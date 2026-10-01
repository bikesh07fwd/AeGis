"""
Focused tests for the agent-loop recursion/iteration safety mechanism.

All graph execution is mocked (no real Gemini API calls, no network, no DB).
Covers:
A. Normal workflow reaching FINISH returns the normal successful response.
B. Workflow hitting the recursion limit is handled gracefully (HTTP 422 with
   a structured payload and trace_id), not an unhandled 500 traceback.
C. The recursion limit is actually passed to the LangGraph invocation.
D. The supervisor FINISH criteria include explicit anti-loop rules.
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from langgraph.errors import GraphRecursionError

from main import app
from api import chat as chat_module
from graph.agents.supervisor import get_supervisor_prompt

client = TestClient(app)

AUTH = {"X-API-KEY": "secret-enterprise-key"}

GENERATE_BODY = {
    "question": "What is the return policy?",
    "conversation_id": "test-conversation",
    "user_id": "test-user",
}


def _successful_result() -> dict:
    """A minimal state snapshot as returned by a workflow that reached FINISH."""
    return {"answer": "The return policy is 30 days.", "next_agent": "FINISH"}


def test_generate_normal_finish_returns_successful_response():
    """A. A normal workflow that reaches FINISH returns the normal response."""
    with patch.object(
        chat_module.graph_app, "ainvoke", new=AsyncMock(return_value=_successful_result())
    ) as mock_ainvoke:
        response = client.post(
            "/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "The return policy is 30 days."
    assert payload["trace_id"]

    # The safety bound must be applied to the graph invocation.
    _, kwargs = mock_ainvoke.call_args
    assert kwargs["config"]["recursion_limit"] == chat_module.RECURSION_LIMIT


def test_generate_recursion_limit_handled_gracefully():
    """B. Recursion exhaustion is a controlled 422, never an unhandled 500."""
    with patch.object(
        chat_module.graph_app, "ainvoke", new=AsyncMock(side_effect=GraphRecursionError("budget exhausted"))
    ):
        response = client.post(
            "/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "recursion_limit_exceeded"
    assert detail["trace_id"]
    assert detail["max_iterations"] == chat_module.RECURSION_LIMIT
    assert "reasoning budget" in detail["message"]

    # Response must not leak a Python traceback.
    body_text = response.text
    assert "Traceback" not in body_text
    assert ".py" not in body_text


def test_generate_recursion_error_not_swallowed_as_success():
    """B (cont). Exhaustion must not be masked as a successful (200) answer."""
    with patch.object(
        chat_module.graph_app, "ainvoke", new=AsyncMock(side_effect=GraphRecursionError("budget exhausted"))
    ):
        response = client.post(
            "/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY
        )

    assert response.status_code != 200
    assert response.status_code != 500
    # An exhausted workflow must never return a fabricated/partial answer payload.
    assert "answer" not in response.json()


def test_stream_recursion_limit_reports_structured_error():
    """B (stream path). SSE stream reports recursion exhaustion as a structured error event."""
    async def _stream_error(initial_state, config=None):
        raise GraphRecursionError("budget exhausted")
        yield  # pragma: no cover - makes this an async generator

    with patch.object(chat_module.graph_app, "astream", new=_stream_error):
        with client.stream(
            "POST", "/api/v1/chat/stream", headers=AUTH, json=GENERATE_BODY
        ) as response:
            assert response.status_code == 200  # SSE transport itself stays healthy
            body = "".join(response.iter_text())

    assert "recursion_limit_exceeded" in body
    assert "trace_id" in body


def test_supervisor_prompt_has_explicit_termination_rules():
    """D. The supervisor prompt contains explicit FINISH / anti-loop criteria."""
    prompt_text = get_supervisor_prompt().format_messages()[0].content
    lowered = prompt_text.lower()

    assert "finish" in lowered
    assert "do not delegate the same task" in lowered
    assert "do not revisit completed work" in lowered
    assert "sufficient information" in lowered


def test_generate_unexpected_error_is_500_not_recursion_path():
    """Regression guard: non-recursion failures keep their distinct 500 path."""
    with patch.object(
        chat_module.graph_app, "ainvoke", new=AsyncMock(side_effect=RuntimeError("boom"))
    ):
        response = client.post(
            "/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "recursion_limit_exceeded" not in str(detail)

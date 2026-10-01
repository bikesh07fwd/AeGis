"""
Focused tests for the deterministic offline Mock LLM provider.

The REAL LangGraph workflow is exercised end-to-end; only the external
boundaries (database sessions, embedding calls) are faked. Zero network
calls, zero Gemini/API usage.

Covers:
A. MockProvider initializes correctly and is selected explicitly.
B. Structured-output compatibility (schema-validated Pydantic results).
C. Tool-binding compatibility.
D. Normal mock scenario: the real graph reaches FINISH (API 200).
E. Loop scenario: the real graph hits the recursion limit
   (GraphRecursionError -> controlled HTTP 422).
F. The API exposes no traceback and no fabricated answer on exhaustion.
"""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from langgraph.errors import GraphRecursionError

from main import app
from api import chat as chat_module
from config.settings import settings
from graph.services.llm_providers import (
    MOCK_LLM_PROVIDER_ENV,
    MOCK_SCENARIO_ENV,
    MockProvider,
)
from graph.services.llm_service import get_llm, get_llm_service
from graph.services.mock_llm import MOCK_ANSWER_PREFIX, MockChatModel
from graph.types import (
    MemoryExtractionResult,
    QueryPlan,
    ReflectionResult,
    RetrievedChunk,
)
from graph.workflow import app as graph_app

client = TestClient(app)

AUTH = {"X-API-KEY": "secret-enterprise-key"}

GENERATE_BODY = {
    "question": "What is the capital of France?",
    "conversation_id": "mock-conversation",
    "user_id": "mock-user",
}

RECURSION_LIMIT = chat_module.RECURSION_LIMIT


def _initial_state() -> dict:
    """Initial state mirroring the /chat/generate endpoint contract."""
    return {
        "conversation_id": GENERATE_BODY["conversation_id"],
        "user_id": GENERATE_BODY["user_id"],
        "question": GENERATE_BODY["question"],
        "trace_id": "mock-trace",
        "query_plan": None,
        "recent_messages": [],
        "semantic_memories": [],
        "retrieved_chunks": [],
        "formatted_context": "",
        "answer": "",
        "extracted_facts": [],
        "messages": [],
        "metadata": {},
        "memory": {},
        "tool_calls": [],
        "errors": [],
        "revision_count": 0,
        "reflection_feedback": None,
        "reflection_status": None,
        "reflection_metrics": None,
        "next_agent": None,
        "node_latencies": {},
        "total_tokens": 0,
        "estimated_cost": 0.0,
    }


async def _fake_retrieve(query: str, db, limit: int = 5):
    """Deterministic in-memory retrieval result (no DB, no embeddings)."""
    return [
        RetrievedChunk(
            id=1,
            text="Paris is the capital of France.",
            document_id=1,
            score=0.0,
            metadata={},
        )
    ]


async def _fake_embedding(text: str) -> list[float]:
    return [0.0] * 768


@contextmanager
def offline_boundaries():
    """Fake only the DB-session and embedding seams used by the real graph.

    Production modules are left untouched; each node module's imported name
    is patched for the duration of the test.
    """

    class _FakeSession:
        def add(self, obj):
            pass

        async def commit(self):
            pass

        async def rollback(self):
            pass

        async def close(self):
            pass

    @asynccontextmanager
    async def fake_session():
        yield _FakeSession()

    with patch("graph.nodes.fetch_memory.async_session_maker", fake_session), patch(
        "graph.nodes.retrieve.async_session_maker", fake_session
    ), patch("graph.nodes.retrieve.retrieve_documents", _fake_retrieve), patch(
        "graph.nodes.store_memory.async_session_maker", fake_session
    ), patch("graph.nodes.store_memory.get_embedding", _fake_embedding):
        yield


# ---------------------------------------------------------------------------
# A. Provider initialization / explicit opt-in
# ---------------------------------------------------------------------------


def test_mock_provider_initializes(monkeypatch):
    """A. AEGIS_LLM_PROVIDER=mock selects the offline mock provider/model."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.delenv(MOCK_SCENARIO_ENV, raising=False)

    service = get_llm_service()
    assert isinstance(service.provider, MockProvider)

    model = service.get_llm("generator")
    assert isinstance(model, MockChatModel)
    assert model.scenario == "normal"

    # get_llm honors the override live, for any role.
    assert isinstance(get_llm("reflection"), MockChatModel)


def test_mock_scenario_selectable_via_env(monkeypatch):
    """A. AEGIS_MOCK_SCENARIO=loop switches the deterministic scenario."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.setenv(MOCK_SCENARIO_ENV, "loop")
    assert get_llm("planner").scenario == "loop"


def test_mock_provider_cannot_activate_in_production(monkeypatch):
    """A. The mock is hard-blocked when environment=production."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(RuntimeError, match="not allowed"):
        get_llm_service()


# ---------------------------------------------------------------------------
# B/C. Structured-output and tool-binding compatibility
# ---------------------------------------------------------------------------


def test_structured_output_returns_schema_valid_results(monkeypatch):
    """B. with_structured_output validates against the requested schema."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    model = get_llm("planner")

    plan = asyncio.run(
        model.with_structured_output(QueryPlan).ainvoke(
            [
                _system("You are an expert Enterprise Query Planner."),
                _human("Question: What is the capital of France?"),
            ]
        )
    )
    assert isinstance(plan, QueryPlan)
    assert plan.search_queries == ["What is the capital of France?"]
    assert plan.memory_policy == "NONE"

    reflection = asyncio.run(
        model.with_structured_output(ReflectionResult).ainvoke(
            [_system("You are a strict Enterprise AI Grader.")]
        )
    )
    assert isinstance(reflection, ReflectionResult)
    assert reflection.overall_status.value == "APPROVED"

    extraction = asyncio.run(
        model.with_structured_output(MemoryExtractionResult).ainvoke(
            [_system("You are an Enterprise Memory Extractor.")]
        )
    )
    assert isinstance(extraction, MemoryExtractionResult)
    assert extraction.facts == []


def test_structured_output_rejects_schema_mismatch(monkeypatch):
    """B. Content that fails the requested schema raises a clear error."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    model = get_llm("planner")
    # Supervisor-mock content is valid JSON, but not a valid QueryPlan.
    with pytest.raises(ValueError, match="QueryPlan validation"):
        asyncio.run(
            model.with_structured_output(QueryPlan).ainvoke(
                [_system("You are a Supervisor Agent. Your job is to delegate tasks.")]
            )
        )


def test_bind_tools_returns_usable_model(monkeypatch):
    """C. bind_tools works and the bound model generates deterministically."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    model = get_llm("generator")
    bound = model.bind_tools([object()])
    assert bound is model  # tool behavior is scenario-driven, binding is a no-op

    response = asyncio.run(
        bound.ainvoke(
            [
                _system("You are a Research Agent. Use your tools to find information."),
                _human("Question: What is the capital of France?"),
            ]
        )
    )
    assert isinstance(response.content, str)
    assert response.content.startswith(MOCK_ANSWER_PREFIX)


# ---------------------------------------------------------------------------
# D. Normal scenario: the REAL graph converges to FINISH
# ---------------------------------------------------------------------------


def test_normal_graph_reaches_finish(monkeypatch):
    """D. Real workflow: planner -> retrieve -> writing agent -> FINISH."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.delenv(MOCK_SCENARIO_ENV, raising=False)
    with offline_boundaries():
        result = asyncio.run(
            graph_app.ainvoke(_initial_state(), config={"recursion_limit": RECURSION_LIMIT})
        )

    assert result["next_agent"] == "FINISH"
    assert result["answer"].startswith(MOCK_ANSWER_PREFIX)
    assert GENERATE_BODY["question"] in result["answer"]
    assert result["reflection_status"] == "APPROVED"
    assert result["errors"] == []


def test_api_mock_generate_success(monkeypatch):
    """D. API: normal mock workflow returns the normal successful response."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.delenv(MOCK_SCENARIO_ENV, raising=False)
    with offline_boundaries():
        response = client.post("/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY)

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith(MOCK_ANSWER_PREFIX)
    assert payload["trace_id"]
    assert "recursion_limit_exceeded" not in response.text


# ---------------------------------------------------------------------------
# E/F. Loop scenario: the REAL graph hits the recursion limit safely
# ---------------------------------------------------------------------------


def test_loop_graph_hits_recursion_limit(monkeypatch):
    """E. Real workflow: endless delegation terminates via recursion_limit."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.setenv(MOCK_SCENARIO_ENV, "loop")
    with offline_boundaries():
        with pytest.raises(GraphRecursionError):
            asyncio.run(
                graph_app.ainvoke(_initial_state(), config={"recursion_limit": RECURSION_LIMIT})
            )


def test_api_mock_recursion_returns_controlled_422(monkeypatch):
    """E/F. API: loop exhaustion is a structured 422, never a 500/200."""
    monkeypatch.setenv(MOCK_LLM_PROVIDER_ENV, "mock")
    monkeypatch.setenv(MOCK_SCENARIO_ENV, "loop")
    with offline_boundaries():
        response = client.post("/api/v1/chat/generate", headers=AUTH, json=GENERATE_BODY)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "recursion_limit_exceeded"
    assert detail["trace_id"]
    assert detail["max_iterations"] == RECURSION_LIMIT

    body_text = response.text
    assert "Traceback" not in body_text  # no traceback exposed
    assert "answer" not in response.json()  # no fabricated successful answer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _system(text: str):
    from langchain_core.messages import SystemMessage

    return SystemMessage(content=text)


def _human(text: str):
    from langchain_core.messages import HumanMessage

    return HumanMessage(content=text)

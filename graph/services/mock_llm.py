"""Deterministic offline chat model for local/test evaluation of the AEGIS graph.

This module is strictly dev/test scoped: it is only reachable through
``MockProvider``, which is selected explicitly via ``AEGIS_LLM_PROVIDER=mock``
(or the existing ``environment=test`` setting). It makes zero network calls,
needs no API key, and returns schema-valid responses so the REAL LangGraph
workflow can be exercised end-to-end without any Gemini/API usage.

Scenarios (``AEGIS_MOCK_SCENARIO``, default ``normal``):
- ``normal``: the supervisor delegates to the writing agent once, approves the
  result, and the graph converges to FINISH with a deterministic answer.
- ``loop``: the supervisor re-delegates the same task forever, which is
  terminated by the configured LangGraph recursion limit (exercises the
  recursion-safety mechanism).
"""

import re

from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.chat_models import ChatGeneration, ChatResult
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import ValidationError

from graph.types import MemoryExtractionResult, QueryPlan, ReflectionResult

MOCK_ANSWER_PREFIX = "[Mock answer]"

_QUESTION_RE = re.compile(r"Question:\s*(.+)")


def _prompt_text(messages: list[BaseMessage]) -> str:
    """Return the first message's text, which carries the caller's role prompt.

    The graph's role prompts arrive as the first message of each call — for
    agents as a SystemMessage, for template-based nodes as a HumanMessage —
    so the role is identified from position rather than message type.
    """
    if not messages:
        return ""
    content = messages[0].content
    return content if isinstance(content, str) else str(content)


def _text(content: object) -> str:
    return content if isinstance(content, str) else str(content)


class _StructuredOutputAdapter:
    """Stands in for LangChain's structured-output runnable for MockChatModel.

    The model always emits JSON for structured-output call sites; this adapter
    simply validates that JSON against the exact schema the caller requested
    (QueryPlan, RouteOption, ReflectionResult, MemoryExtractionResult, ...).
    """

    def __init__(self, model: "MockChatModel", schema: type):
        self.model = model
        self.schema = schema

    async def ainvoke(self, messages, config=None, **kwargs):
        message_list = list(messages)
        chat_result = self.model._generate(message_list)
        raw = chat_result.generations[0].message.content
        try:
            return self.schema.model_validate_json(_text(raw))
        except ValidationError as exc:
            raise ValueError(
                f"Mock model content failed {self.schema.__name__} validation: {raw!r}"
            ) from exc


class MockChatModel(BaseChatModel):
    """Minimal BaseChatModel returning deterministic, schema-valid content.

    Branches are keyed off the caller's system prompt, exactly mirroring the
    roles used by the AEGIS graph (query planner, supervisor, research/math
    agents, writing agent, reflection, memory extraction).
    """

    scenario: str = "normal"
    supervisor_calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "aegis-mock"

    def bind_tools(self, tools: object, **kwargs: object) -> "MockChatModel":
        # Tool-call behavior is scenario driven and does not depend on the
        # bound tools, so binding is a no-op that returns the same model.
        return self

    def with_structured_output(self, schema: type, **kwargs: object) -> _StructuredOutputAdapter:
        return _StructuredOutputAdapter(model=self, schema=schema)

    def _extract_question(self, messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            content = _text(message.content) if not isinstance(message.content, str) else message.content
            match = _QUESTION_RE.search(content)
            if match:
                return match.group(1).strip()
        if messages:
            last = messages[-1].content
            if isinstance(last, str) and last.strip():
                return last.strip()
        return ""

    def _has_mock_answer(self, messages: list[BaseMessage]) -> bool:
        """True once the writing agent's deterministic answer is in history."""
        return any(
            isinstance(message, AIMessage)
            and isinstance(message.content, str)
            and message.content.startswith(MOCK_ANSWER_PREFIX)
            for message in messages
        )

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        prompt_text = _prompt_text(messages)

        if "Query Planner" in prompt_text:
            question = self._extract_question(messages) or "the user question"
            plan = QueryPlan(
                intent="information retrieval",
                search_queries=[question],
                reasoning="Deterministic mock plan for offline workflow evaluation.",
                filters={},
                memory_policy="NONE",
                needs_tools=False,
                confidence=1.0,
            )
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=plan.model_dump_json()))])

        if "Supervisor Agent" in prompt_text:
            self.supervisor_calls += 1
            if self.scenario == "loop":
                # Deliberately keep delegating the same task: the graph can
                # only terminate via the configured recursion limit.
                route_json = '{"next_agent": "research_agent"}'
            elif self._has_mock_answer(messages):
                # The writing agent already produced the final answer.
                route_json = '{"next_agent": "FINISH"}'
            else:
                # First pass: delegate synthesis to the writing agent.
                route_json = '{"next_agent": "writing_agent"}'
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=route_json))])

        if "Enterprise AI Grader" in prompt_text:
            reflection = ReflectionResult(
                groundedness_score=1.0,
                completeness_score=1.0,
                hallucination_score=0.0,
                confidence=1.0,
                overall_status="APPROVED",
                feedback="Deterministic mock approval.",
            )
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reflection.model_dump_json()))])

        if "Memory Extractor" in prompt_text:
            extraction = MemoryExtractionResult(facts=[])
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=extraction.model_dump_json()))])

        if self.scenario == "loop":
            # Non-supervisor roles in the loop scenario: acknowledge without
            # producing a final answer so the delegation cycle continues.
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="[Mock working] step complete."))])

        # Plain generation (writing agent / final synthesis role).
        question = self._extract_question(messages)
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=f"{MOCK_ANSWER_PREFIX} {question}".strip()))]
        )

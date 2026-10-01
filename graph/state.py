from typing import TypedDict, Any, Annotated
from langgraph.graph.message import add_messages
from graph.types import RetrievedChunk, QueryPlan

class GraphState(TypedDict):
    conversation_id: str | None
    user_id: str | None
    question: str
    query_plan: QueryPlan | None
    recent_messages: list[Any]
    semantic_memories: list[Any]
    retrieved_chunks: list[RetrievedChunk]
    formatted_context: str
    answer: str
    extracted_facts: list[Any]
    messages: Annotated[list[Any], add_messages]
    metadata: dict[str, Any]
    memory: dict[str, Any]
    tool_calls: list[Any]
    errors: list[str]
    trace_id: str
    
    revision_count: int
    reflection_feedback: str | None
    reflection_status: str | None
    reflection_metrics: dict[str, Any] | None
    next_agent: str | None
    node_latencies: dict[str, float]
    total_tokens: int
    estimated_cost: float

from pydantic import BaseModel, Field
from typing import Any

class RetrievedChunk(BaseModel):
    id: int
    text: str
    document_id: int
    score: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

class QueryPlan(BaseModel):
    intent: str = Field(description="The perceived intent of the user's question (e.g., 'information retrieval', 'comparison', 'summarization').")
    search_queries: list[str] = Field(description="A list of optimized search queries to execute against the vector database.")
    reasoning: str = Field(description="Explanation of why this plan was chosen.")
    filters: dict[str, Any] = Field(default_factory=dict, description="Any metadata filters to apply to the search.")
    memory_policy: str = Field(default="NONE", description="The memory policy for this query. Must be one of 'NONE', 'RECENT', 'SEMANTIC', 'ALL'.")
    needs_tools: bool = Field(default=False, description="Whether this query requires external tools to answer.")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0.")

class ExtractedFact(BaseModel):
    fact: str = Field(description="A concise statement of a persistent fact to remember.")
    reasoning: str = Field(description="Why this fact is worth remembering long-term.")
    importance_score: float = Field(default=1.0, description="Score 0.0 to 1.0 indicating importance. 1.0 is highest.")

class MemoryExtractionResult(BaseModel):
    facts: list[ExtractedFact] = Field(default_factory=list, description="A list of facts to store in long-term memory.")

from enum import Enum

class ReflectionStatus(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_REVISION = "NEEDS_REVISION"
    NEEDS_MORE_CONTEXT = "NEEDS_MORE_CONTEXT"
    NO_ANSWER_EXISTS = "NO_ANSWER_EXISTS"

class ReflectionResult(BaseModel):
    groundedness_score: float = Field(description="Score 0.0 to 1.0 indicating how well the answer is supported by the context.")
    completeness_score: float = Field(description="Score 0.0 to 1.0 indicating how fully it answers the user's question.")
    hallucination_score: float = Field(description="Score 0.0 to 1.0 indicating likelihood of fabricated information. Higher means more hallucinated.")
    confidence: float = Field(description="Score 0.0 to 1.0 indicating the reviewer's confidence in its own assessment.")
    overall_status: ReflectionStatus = Field(description="The final routing decision based on the scores.")
    feedback: str = Field(description="Constructive critique and instructions for revision, or explanation of the decision.")

class CitationResult(BaseModel):
    is_cited: bool = Field(description="True if all factual statements in the answer are backed by a citation from the context.")
    feedback: str = Field(description="Feedback on missing citations, or 'OK' if all good.")

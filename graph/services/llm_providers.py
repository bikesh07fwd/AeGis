import os

from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

from graph.services.mock_llm import MockChatModel

# Explicit opt-in for the offline mock LLM. Never set in production.
MOCK_LLM_PROVIDER_ENV = "AEGIS_LLM_PROVIDER"
MOCK_SCENARIO_ENV = "AEGIS_MOCK_SCENARIO"

class LLMProvider(ABC):
    @abstractmethod
    def get_model(self, role: str) -> BaseChatModel:
        pass

class VertexAIProvider(LLMProvider):
    def get_model(self, role: str) -> BaseChatModel:
        from langchain_google_vertexai import ChatVertexAI
        # Only the final generation role uses the expensive reasoning model.
        # Planner/supervisor, reflection, and memory extraction all run on flash
        # to cut sequential Vertex AI calls' latency and avoid 429 rate limits.
        model_name = "gemini-2.5-pro" if role == "generator" else "gemini-2.5-flash"
        return ChatVertexAI(
            model_name=model_name,
            temperature=0.0
        )

class GeminiAPIProvider(LLMProvider):
    def get_model(self, role: str) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from config.settings import settings
        
        if not settings.gemini_api_key:
            raise ValueError("gemini_api_key is required for GeminiAPIProvider")
            
        # Local dev (Gemini API): the gemini-2.5 family is blocked for new keys
        # (404) and pro-tier models exceed free-tier quota (429). Default is the
        # best verified flash model; GEMINI_DEV_MODEL overrides it (e.g. to a
        # lite model when the daily free quota of the default is exhausted).
        # Production (VertexAIProvider) keeps its Pro/Flash split.
        import os
        model_name = os.getenv("GEMINI_DEV_MODEL", "gemini-3.6-flash")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.gemini_api_key,
            temperature=0.0
        )

class MockProvider(LLMProvider):
    """Offline, deterministic provider for local/test evaluation only.

    Returns a MockChatModel (zero network, zero API key) that produces
    schema-valid responses so the REAL LangGraph workflow can run
    end-to-end without any Gemini/API calls. Opt-in via
    AEGIS_LLM_PROVIDER=mock; scenario via AEGIS_MOCK_SCENARIO
    ('normal' by default, 'loop' exercises the recursion limit).
    """

    def get_model(self, role: str) -> BaseChatModel:
        scenario = os.getenv(MOCK_SCENARIO_ENV, "normal")
        return MockChatModel(scenario=scenario)

class LLMService:
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
    def get_llm(self, role: str = "generator") -> BaseChatModel:
        return self.provider.get_model(role)

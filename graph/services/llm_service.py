import os

from graph.services.llm_providers import (
    LLMService,
    VertexAIProvider,
    GeminiAPIProvider,
    MockProvider,
    MOCK_LLM_PROVIDER_ENV,
)
from config.settings import settings

def get_llm_service() -> LLMService:
    # Explicit local/test opt-in for the offline mock provider.
    # Guarded so it can never activate in a production environment.
    if os.getenv(MOCK_LLM_PROVIDER_ENV) == "mock":
        if settings.environment == "production":
            raise RuntimeError(
                f"{MOCK_LLM_PROVIDER_ENV}=mock is not allowed when environment=production."
            )
        return LLMService(MockProvider())

    if settings.environment == "production":
        return LLMService(VertexAIProvider())
    elif settings.environment == "test":
        return LLMService(MockProvider())
    else:
        if settings.gemini_api_key:
            return LLMService(GeminiAPIProvider())
        return LLMService(VertexAIProvider())

_service = get_llm_service()

def get_llm(role: str = "generator"):
    """Returns the configured LLM instance for generation."""
    # The mock opt-in is honored live so it takes effect without a process
    # restart (production is still blocked inside get_llm_service).
    if os.getenv(MOCK_LLM_PROVIDER_ENV) == "mock":
        return get_llm_service().get_llm(role)
    return _service.get_llm(role)

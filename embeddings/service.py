import asyncio
from google import genai
from config.settings import settings

def get_client():
    if settings.environment == "production":
        return genai.Client(vertexai=True, project=settings.gcp_project_id)
    
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.gemini_api_key)

def _embedding_model_kwargs(contents: object) -> dict:
    """Build embed_content kwargs per environment.

    Production (Vertex AI) keeps text-embedding-004 unchanged.
    Dev/test (Gemini API): text-embedding-004 is retired there (404), so use
    gemini-embedding-001 truncated to 768 dims to match the Vector(768) schema.
    """
    if settings.environment == "production":
        return {"model": "text-embedding-004", "contents": contents}
    from google.genai import types
    return {
        "model": "gemini-embedding-001",
        "contents": contents,
        "config": types.EmbedContentConfig(output_dimensionality=768),
    }

async def get_embedding(text: str) -> list[float]:
    """Get a single embedding using Gemini."""
    client = get_client()
    
    # We use asyncio.to_thread since genai client might be blocking
    response = await asyncio.to_thread(
        client.models.embed_content,
        **_embedding_model_kwargs(text)
    )
    return response.embeddings[0].values

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts using Gemini."""
    if not texts:
        return []
        
    client = get_client()
        
    response = await asyncio.to_thread(
        client.models.embed_content,
        **_embedding_model_kwargs(texts)
    )
    return [e.values for e in response.embeddings]

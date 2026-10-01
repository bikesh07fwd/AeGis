from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config.settings import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifies the API key for protected routes."""
    # In production, check against database or secrets manager.
    expected_key = getattr(settings, "enterprise_api_key", "secret-enterprise-key")
    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return api_key

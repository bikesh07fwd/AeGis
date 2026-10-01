import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    app_name: str = "Aegis AI"
    environment: str = "development" # "development" or "production"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # GCP Config
    gcp_project_id: str | None = None
    
    # Secrets
    database_url_secret_name: str = "DATABASE_URL"
    database_url: str | None = None
    gemini_api_key: str | None = None
    redis_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Fetch secret from GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def init_settings() -> Settings:
    _settings = Settings()
    
    if _settings.environment == "production":
        logger.info("Initializing in PRODUCTION mode. Fetching secrets from GCP Secret Manager.")
        if not _settings.gcp_project_id:
            raise ValueError("gcp_project_id must be set in production to fetch secrets.")
            
        try:
            # Overwrite local .env values with Secret Manager values
            _settings.database_url = get_secret(_settings.gcp_project_id, _settings.database_url_secret_name)
            # Gemini key is optional if using VertexAI with service accounts, but fetched if needed
            try:
                _settings.gemini_api_key = get_secret(_settings.gcp_project_id, "GEMINI_API_KEY")
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to fetch secrets from Secret Manager: {e}")
            # Fail fast in production!
            raise RuntimeError("CRITICAL: Could not load required secrets from GCP Secret Manager in production.")
    else:
        logger.info("Initializing in DEVELOPMENT mode. Using local .env secrets.")
        
    if not _settings.database_url:
        raise ValueError("DATABASE_URL is missing.")
        
    return _settings

settings = init_settings()
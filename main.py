from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from config.settings import settings
from database.postgres import engine, Base
from api.health import router as health_router
from api.document import router as document_router
from api.chat import router as chat_router
from utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections (Migrations are now handled externally)
    logger.info("Starting up Aegis API...")
    # Just verify connection or setup pools if needed
    yield
    # Shutdown: Close database engine
    logger.info("Shutting down Aegis API...")
    await engine.dispose()

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)

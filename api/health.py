from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.postgres import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint that also verifies database connectivity."""
    try:
        # Attempt a simple query to verify DB connection
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db_status": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail={"status": "error", "db_status": "disconnected", "error": str(e)}
        )

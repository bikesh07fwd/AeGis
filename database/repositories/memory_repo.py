from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import LongTermMemory

async def save_semantic_memory(db: AsyncSession, user_id: str, fact: str, embedding: list[float], tenant_id: int = 1) -> LongTermMemory:
    mem = LongTermMemory(
        tenant_id=tenant_id or 1,
        user_id=user_id,
        fact=fact,
        embedding=embedding
    )
    db.add(mem)
    await db.commit()
    return mem

async def get_semantic_memories(db: AsyncSession, user_id: str, query_embedding: list[float], limit: int = 3) -> list[LongTermMemory]:
    stmt = (
        select(LongTermMemory)
        .where(LongTermMemory.user_id == user_id)
        .order_by(LongTermMemory.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

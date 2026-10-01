from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories import message_repo, memory_repo
from embeddings.service import get_embedding

async def fetch_recent_context(db: AsyncSession, conversation_id: str, limit: int = 5):
    if not conversation_id:
        return []
    messages = await message_repo.get_recent_messages(db, conversation_id, limit)
    return [{"role": msg.role, "content": msg.content} for msg in messages]

async def fetch_semantic_context(db: AsyncSession, user_id: str, query: str, limit: int = 3):
    if not user_id:
        return []
    query_embedding = await get_embedding(query)
    memories = await memory_repo.get_semantic_memories(db, user_id, query_embedding, limit)
    return [mem.fact for mem in memories]

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Chunk
from embeddings.service import get_embedding

async def semantic_search(query: str, db: AsyncSession, limit: int = 5) -> list[Chunk]:
    """
    Perform a semantic search to find chunks related to the query.
    """
    # 1. Convert query to an embedding
    query_embedding = await get_embedding(query)
    
    # 2. Query Postgres using cosine distance (<=> operator in pgvector)
    # The cosine_distance method is provided by pgvector.sqlalchemy
    stmt = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    
    # 3. Execute query and return results
    result = await db.execute(stmt)
    return list(result.scalars().all())

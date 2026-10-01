from sqlalchemy.ext.asyncio import AsyncSession
from graph.types import RetrievedChunk
from retrieval.semantic import semantic_search

async def retrieve_documents(query: str, db: AsyncSession, limit: int = 5) -> list[RetrievedChunk]:
    """Service to fetch documents and wrap them in a RetrievedChunk contract."""
    chunks = await semantic_search(query, db, limit)
    
    return [
        RetrievedChunk(
            id=chunk.id,
            text=chunk.chunk_text,
            document_id=chunk.document_id,
            score=0.0,
            metadata={}
        )
        for chunk in chunks
    ]

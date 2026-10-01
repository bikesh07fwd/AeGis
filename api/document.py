from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import get_db
from database.models import Document, Chunk
from loaders.txt_loader import load_txt
from cleaning.cleaner import clean_text
from metadata.extractor import extract_metadata
from chunking.fixed import chunk_text_fixed

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document, process it (clean, extract metadata, chunk),
    and store it in the database.
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported currently.")
        
    try:
        # 1. Read file
        content_bytes = await file.read()
        raw_text = await load_txt(content_bytes)
        
        # 2. Clean text
        cleaned_text = clean_text(raw_text)
        
        # 3. Extract Metadata
        metadata = extract_metadata(file.filename, file.content_type, file.size)
        
        # 4. Create Document in DB
        db_doc = Document(
            filename=file.filename,
            content=cleaned_text,
            metadata_=metadata
        )
        db.add(db_doc)
        await db.flush()  # To get the document ID before creating chunks
        
        # 5. Chunk text
        chunks = chunk_text_fixed(cleaned_text, chunk_size=1000, chunk_overlap=200)
        
        # 5.5. Generate Embeddings
        from embeddings.service import get_embeddings_batch
        embeddings = await get_embeddings_batch(chunks)
        
        # 6. Create Chunks in DB
        db_chunks = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = Chunk(
                document_id=db_doc.id,
                chunk_text=chunk_text,
                chunk_index=i,
                embedding=embedding
            )
            db_chunks.append(db_chunk)
            
        db.add_all(db_chunks)
        await db.commit()
        await db.refresh(db_doc)
        
        return {
            "status": "success",
            "document_id": db_doc.id,
            "filename": db_doc.filename,
            "chunks_created": len(db_chunks)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

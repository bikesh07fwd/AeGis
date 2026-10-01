def chunk_text_fixed(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Split text into chunks of a fixed size with overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - chunk_overlap
    return chunks

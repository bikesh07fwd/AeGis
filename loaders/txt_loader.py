async def load_txt(content: bytes) -> str:
    """Load and decode a plain text file."""
    return content.decode('utf-8', errors='replace')

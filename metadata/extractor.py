def extract_metadata(filename: str, content_type: str, size: int) -> dict:
    """Extract basic file metadata."""
    return {
        "filename": filename,
        "content_type": content_type,
        "size": size,
    }

import re

def clean_text(text: str) -> str:
    """Clean the text by normalizing whitespace."""
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    return text.strip()

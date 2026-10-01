from langchain_core.prompts import ChatPromptTemplate

def get_memory_extractor_prompt() -> ChatPromptTemplate:
    template = """You are an Enterprise Memory Extractor.
Analyze the user's input and extract any persistent facts that should be stored in long-term memory.
Examples of persistent facts: user preferences, company details, ongoing project goals.
Do NOT store transient information or conversational filler (e.g. "Hi", "Thanks", "Summarize this").

User Input: {question}"""
    return ChatPromptTemplate.from_template(template)

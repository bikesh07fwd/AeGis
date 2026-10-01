from langchain_core.prompts import ChatPromptTemplate

def get_query_planner_prompt() -> ChatPromptTemplate:
    template = """You are an expert Enterprise Query Planner.
Analyze the user's question and determine the best search strategy.

Determine the memory_policy based on what context is needed:
- NONE: standalone questions (e.g. "What is the holiday policy?")
- RECENT: needs recent conversation context (e.g. "Can you summarize what you just said?")
- SEMANTIC: asks about persistent facts or user preferences (e.g. "What database did I decide to use?")
- ALL: needs both recent and semantic memory.

Break the user's question down into one or more highly optimized search queries. 
Focus on core semantic concepts and keywords. If the user asks for a comparison, generate separate search queries for each concept being compared.

Question: {question}"""
    return ChatPromptTemplate.from_template(template)

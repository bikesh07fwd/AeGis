from langchain_core.prompts import ChatPromptTemplate

def get_citation_checker_prompt() -> ChatPromptTemplate:
    template = """You are a strict Enterprise Citation Checker.
Your job is to ensure every factual statement in the generated answer is grounded in the retrieved context.
If any fact is stated without basis in the context, flag it.

Return is_cited=True if the answer is completely safe and grounded.
Return is_cited=False and provide feedback if there are unsupported facts.

Generated Answer:
{answer}

Retrieved Context:
{context}"""
    return ChatPromptTemplate.from_template(template)

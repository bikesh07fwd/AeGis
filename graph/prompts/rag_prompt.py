from langchain_core.prompts import ChatPromptTemplate

def get_rag_prompt() -> ChatPromptTemplate:
    template = """You are a helpful and knowledgeable Enterprise AI Assistant.
Use the following retrieved context to answer the user's question. 
If you don't know the answer based on the context, just say that you don't know. 
Keep the answer concise and strictly grounded in the context.

Recent Conversation History:
{recent_messages}

Long-Term Semantic Facts about User:
{semantic_memories}

Context:
{context}

Previous Critique (If revising):
{reflection_feedback}

Question: {question}

Answer:"""
    return ChatPromptTemplate.from_template(template)

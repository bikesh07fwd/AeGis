from graph.state import GraphState

def build_context_node(state: GraphState) -> dict:
    """Node for building a formatted context string from retrieved chunks."""
    chunks = state.get("retrieved_chunks", [])
    
    formatted_chunks = []
    for i, chunk in enumerate(chunks, 1):
        formatted_chunks.append(f"--- Chunk {i} (Doc ID {chunk.document_id}) ---\n{chunk.text}")
        
    formatted_context = "\n\n".join(formatted_chunks)
    
    from langchain_core.messages import HumanMessage
    msg_content = f"Question: {state.get('question')}\n\nContext:\n{formatted_context}"
    new_message = HumanMessage(content=msg_content)
    
    return {
        "formatted_context": formatted_context,
        "messages": [new_message]
    }

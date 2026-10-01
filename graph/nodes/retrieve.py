from graph.state import GraphState
from graph.services.retriever_service import retrieve_documents
from database.postgres import async_session_maker

async def retrieve_node(state: GraphState, **kwargs) -> dict:
    """Node for retrieving documents based on the QueryPlan."""
    
    queries = []
    if state.get("query_plan") and state["query_plan"].search_queries:
        queries = state["query_plan"].search_queries
    else:
        # Fallback if no plan exists
        queries = [state["question"]]
        
    all_chunks = {}
    
    async with async_session_maker() as db:
        for q in queries:
            chunks = await retrieve_documents(q, db)
            for chunk in chunks:
                # Deduplicate by chunk ID
                if chunk.id not in all_chunks:
                    all_chunks[chunk.id] = chunk
                    
    # Flatten dict to list
    final_chunks = list(all_chunks.values())
    
    return {"retrieved_chunks": final_chunks}

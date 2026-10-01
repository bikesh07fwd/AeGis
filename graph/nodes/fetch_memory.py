from graph.state import GraphState
from database.postgres import async_session_maker
from graph.services import memory_service

async def fetch_memory_node(state: GraphState) -> dict:
    """Node for fetching conversational and semantic memory based on policy."""
    policy = state.get("query_plan").memory_policy if state.get("query_plan") else "NONE"
    
    recent_msgs = []
    semantic_mems = []
    
    async with async_session_maker() as db:
        if policy in ["RECENT", "ALL"] and state.get("conversation_id"):
            recent_msgs = await memory_service.fetch_recent_context(db, state["conversation_id"])
            
        if policy in ["SEMANTIC", "ALL"] and state.get("user_id"):
            semantic_mems = await memory_service.fetch_semantic_context(db, state["user_id"], state["question"])
            
    return {
        "recent_messages": recent_msgs,
        "semantic_memories": semantic_mems
    }

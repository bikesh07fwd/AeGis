from graph.state import GraphState
from database.postgres import async_session_maker
from database.repositories import message_repo, memory_repo
from embeddings.service import get_embedding
import uuid

async def store_memory_node(state: GraphState) -> dict:
    """Node for persisting the conversation and any extracted facts."""
    async with async_session_maker() as db:
        conv_id = state.get("conversation_id")
        user_id = state.get("user_id")
        
        # Save Conversation Messages
        if conv_id:
            await message_repo.save_message(
                db=db,
                conversation_id=conv_id,
                message_id=str(uuid.uuid4()),
                role="user",
                content=state["question"]
            )
            await message_repo.save_message(
                db=db,
                conversation_id=conv_id,
                message_id=str(uuid.uuid4()),
                role="ai",
                content=state["answer"]
            )
            
        # Save Long-Term Memories
        if user_id and state.get("extracted_facts"):
            for fact in state["extracted_facts"]:
                # Generate embedding for the fact
                embedding = await get_embedding(fact.fact)
                await memory_repo.save_semantic_memory(
                    db=db,
                    user_id=user_id,
                    fact=fact.fact,
                    embedding=embedding
                )
                
    return {}

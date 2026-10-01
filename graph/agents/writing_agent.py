from graph.state import GraphState
from graph.services.llm_service import get_llm
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

async def writing_agent_node(state: GraphState) -> dict:
    llm = get_llm(role="generator")
    
    sys_msg = SystemMessage(content="You are a Writing Agent. Synthesize the findings into a final, clear response for the user. Do not call any tools.")
    messages = [sys_msg] + state.get("messages", [])
    
    # Gemini 3.x rejects history ending with an AIMessage (no model prefilling)
    if messages and isinstance(messages[-1], AIMessage):
        messages.append(HumanMessage(content="Continue with your task based on the feedback above."))
    
    response = await llm.ainvoke(messages)
    
    new_revision_count = state.get("revision_count", 0) + 1
    
    return {
        "messages": [response],
        "answer": response.content if response.content else "",
        "revision_count": new_revision_count
    }

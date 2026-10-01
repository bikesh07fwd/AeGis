from graph.state import GraphState
from graph.services.llm_service import get_llm
from graph.tools.registry import search_google_drive, send_email
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

async def research_agent_node(state: GraphState) -> dict:
    llm = get_llm(role="generator")
    llm_with_tools = llm.bind_tools([search_google_drive, send_email])
    
    sys_msg = SystemMessage(content="You are a Research Agent. Use your tools to find information or interact with external systems. Once you have finished your sub-task, summarize your findings.")
    messages = [sys_msg] + state.get("messages", [])
    
    # Gemini 3.x rejects history ending with an AIMessage (no model prefilling)
    if messages and isinstance(messages[-1], AIMessage):
        messages.append(HumanMessage(content="Continue with your task based on the feedback above."))
    
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

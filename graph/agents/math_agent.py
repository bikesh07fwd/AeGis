from graph.state import GraphState
from graph.services.llm_service import get_llm
from graph.tools.registry import calculator
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

async def math_agent_node(state: GraphState) -> dict:
    llm = get_llm(role="generator")
    llm_with_tools = llm.bind_tools([calculator])
    
    sys_msg = SystemMessage(content="You are a Math Agent. Use the calculator tool to compute required numbers. Summarize the calculation when done.")
    messages = [sys_msg] + state.get("messages", [])
    
    # Gemini 3.x rejects history ending with an AIMessage (no model prefilling)
    if messages and isinstance(messages[-1], AIMessage):
        messages.append(HumanMessage(content="Continue with your task based on the feedback above."))
    
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}

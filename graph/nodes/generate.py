from graph.state import GraphState
from graph.services.llm_service import get_llm
from graph.prompts.rag_prompt import get_rag_prompt

from graph.tools.registry import enterprise_tools

async def generate_node(state: GraphState) -> dict:
    """Node for generating the final answer or deciding to call tools."""
    llm = get_llm(role="generator")
    llm_with_tools = llm.bind_tools(enterprise_tools)
    
    prompt = get_rag_prompt()
    
    recent_msgs_str = "\n".join([f"{m['role']}: {m['content']}" for m in state.get("recent_messages", [])])
    semantic_mems_str = "\n".join(state.get("semantic_memories", []))
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        context=state.get("formatted_context", ""),
        recent_messages=recent_msgs_str,
        semantic_memories=semantic_mems_str,
        reflection_feedback=state.get("reflection_feedback", "None"),
        question=state.get("question", "")
    )
    
    messages_to_pass = formatted_prompt + state.get("messages", [])
    
    # Generate answer or tool call
    response = await llm_with_tools.ainvoke(messages_to_pass)
    
    new_revision_count = state.get("revision_count", 0) + 1
    
    return {
        "answer": response.content if response.content else "",
        "messages": [response],
        "revision_count": new_revision_count
    }

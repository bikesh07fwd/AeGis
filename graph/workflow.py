from langgraph.graph import StateGraph, START, END
from graph.state import GraphState
from graph.nodes.query_planner import query_planner_node
from graph.nodes.fetch_memory import fetch_memory_node
from graph.nodes.retrieve import retrieve_node
from graph.nodes.context_builder import build_context_node

from graph.agents.supervisor import supervisor_node
from graph.agents.research_agent import research_agent_node
from graph.agents.math_agent import math_agent_node
from graph.agents.writing_agent import writing_agent_node
from graph.nodes.tool_executor import tool_node

from graph.nodes.reflection import reflection_node
from graph.nodes.citation_checker import citation_checker_node
from graph.nodes.memory_extractor import memory_extractor_node
from graph.nodes.store_memory import store_memory_node
from langchain_core.messages import AIMessage

async def error_handler_node(state: GraphState) -> dict:
    """Handles graceful degradation when a worker crashes."""
    errors = state.get("errors", [])
    last_error = errors[-1] if errors else "Unknown system error."
    
    safe_msg = f"I encountered a temporary system error and could not complete the request. (Internal: {last_error})"
    
    return {
        "answer": safe_msg,
        "next_agent": "FINISH" 
    }

def route_after_supervisor(state: GraphState):
    if state.get("errors"):
        return "error_handler"
    next_agent = state.get("next_agent")
    if next_agent == "FINISH":
        return "reflection"
    return next_agent

def route_after_agent(state: GraphState):
    if state.get("errors"):
        return "error_handler"
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        return "tool_executor"
    return "supervisor"

def route_after_reflection(state: GraphState):
    status = state.get("reflection_status")
    revision_count = state.get("revision_count", 0)
    
    if revision_count >= 3:
        return "citation_checker"
        
    if status == "NEEDS_REVISION":
        return "writing_agent"
    elif status == "NEEDS_MORE_CONTEXT":
        return "research_agent"
    else:
        return "citation_checker"

def build_graph():
    builder = StateGraph(GraphState)
    
    builder.add_node("query_planner", query_planner_node)
    builder.add_node("fetch_memory", fetch_memory_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("build_context", build_context_node)
    
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research_agent", research_agent_node)
    builder.add_node("math_agent", math_agent_node)
    builder.add_node("writing_agent", writing_agent_node)
    builder.add_node("tool_executor", tool_node)
    
    builder.add_node("error_handler", error_handler_node)
    builder.add_node("reflection", reflection_node)
    builder.add_node("citation_checker", citation_checker_node)
    builder.add_node("memory_extractor", memory_extractor_node)
    builder.add_node("store_memory", store_memory_node)
    
    builder.add_edge(START, "query_planner")
    builder.add_edge("query_planner", "fetch_memory")
    builder.add_edge("fetch_memory", "retrieve")
    builder.add_edge("retrieve", "build_context")
    builder.add_edge("build_context", "supervisor")
    
    builder.add_conditional_edges("supervisor", route_after_supervisor, {
        "research_agent": "research_agent",
        "math_agent": "math_agent",
        "writing_agent": "writing_agent",
        "error_handler": "error_handler",
        "reflection": "reflection"
    })
    
    for agent in ["research_agent", "math_agent", "writing_agent"]:
        builder.add_conditional_edges(agent, route_after_agent, {
            "tool_executor": "tool_executor",
            "error_handler": "error_handler",
            "supervisor": "supervisor"
        })
        
    builder.add_edge("tool_executor", "supervisor")
    
    builder.add_edge("error_handler", END)
    
    builder.add_conditional_edges("reflection", route_after_reflection)
    
    builder.add_edge("citation_checker", "memory_extractor")
    builder.add_edge("memory_extractor", "store_memory")
    builder.add_edge("store_memory", END)
    
    return builder.compile()

app = build_graph()

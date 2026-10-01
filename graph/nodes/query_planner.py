from graph.state import GraphState
from graph.types import QueryPlan
from graph.services.llm_service import get_llm
from graph.prompts.query_planner_prompt import get_query_planner_prompt

async def query_planner_node(state: GraphState) -> dict:
    """Node for planning the search queries."""
    llm = get_llm(role="planner")
    prompt = get_query_planner_prompt()
    
    # Enforce structured output using Langchain
    planner_llm = llm.with_structured_output(QueryPlan)
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(question=state["question"])
    
    # Generate the structured plan
    plan: QueryPlan = await planner_llm.ainvoke(formatted_prompt)
    
    return {"query_plan": plan}

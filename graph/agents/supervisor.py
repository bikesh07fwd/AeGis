from pydantic import BaseModel
from graph.state import GraphState
from graph.services.llm_service import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

class RouteOption(BaseModel):
    next_agent: str

def get_supervisor_prompt() -> ChatPromptTemplate:
    template = """You are a Supervisor Agent. Your job is to delegate tasks to specialized worker agents based on the user's request.
The available workers are:
- 'research_agent': Can search documents and drive.
- 'math_agent': Can perform calculations.
- 'writing_agent': Can format the final answer.
- 'FINISH': Call this when the task is fully completed and a final answer has been written.

Termination rules (follow strictly):
- Choose 'FINISH' as soon as sufficient information has been gathered and a final answer has been written.
- Do NOT delegate the same task to the same worker twice unless the previous attempt failed or new work is genuinely required.
- Do NOT revisit completed work without a concrete, specific reason.
- Avoid unnecessary research or reflection cycles; terminate after useful evidence has been gathered.
- An answer that reasonably addresses the question is complete; do not keep iterating for marginal improvements.

Given the current state of messages, who should act next? (Respond with the exact name of the agent or 'FINISH')"""
    return ChatPromptTemplate.from_template(template)

async def supervisor_node(state: GraphState) -> dict:
    llm = get_llm(role="planner")
    prompt = get_supervisor_prompt()
    router = llm.with_structured_output(RouteOption)
    
    # We pass the system prompt followed by all history
    messages_to_pass = prompt.format_messages() + state.get("messages", [])
    
    # Gemini 3.x rejects history ending with an AIMessage (no model prefilling)
    if messages_to_pass and isinstance(messages_to_pass[-1], AIMessage):
        messages_to_pass.append(HumanMessage(content="Who should act next? Respond with the exact agent name or 'FINISH'."))
    
    result = await router.ainvoke(messages_to_pass)
    
    return {"next_agent": result.next_agent}

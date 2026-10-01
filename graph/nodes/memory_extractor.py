from graph.state import GraphState
from graph.types import MemoryExtractionResult
from graph.services.llm_service import get_llm
from graph.prompts.memory_extractor_prompt import get_memory_extractor_prompt

async def memory_extractor_node(state: GraphState) -> dict:
    """Node for extracting persistent facts to long-term memory."""
    llm = get_llm(role="reflection")
    prompt = get_memory_extractor_prompt()
    
    extractor_llm = llm.with_structured_output(MemoryExtractionResult)
    formatted_prompt = prompt.format_messages(question=state["question"])
    
    result: MemoryExtractionResult = await extractor_llm.ainvoke(formatted_prompt)
    
    important_facts = [f for f in result.facts if getattr(f, 'importance_score', 1.0) >= 0.8]
    
    return {"extracted_facts": important_facts}

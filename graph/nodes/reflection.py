from graph.state import GraphState
from graph.types import ReflectionResult
from graph.services.llm_service import get_llm
from graph.prompts.reflection_prompt import get_reflection_prompt

async def reflection_node(state: GraphState) -> dict:
    """Node for evaluating the generated answer."""
    llm = get_llm(role="reflection")
    prompt = get_reflection_prompt()
    
    reflection_llm = llm.with_structured_output(ReflectionResult)
    formatted_prompt = prompt.format_messages(
        question=state["question"],
        context=state.get("formatted_context", ""),
        answer=state.get("answer", "")
    )
    
    result: ReflectionResult = await reflection_llm.ainvoke(formatted_prompt)
    
    metrics = {
        "groundedness": result.groundedness_score,
        "completeness": result.completeness_score,
        "hallucination": result.hallucination_score,
        "confidence": result.confidence
    }
    
    return {
        "reflection_feedback": result.feedback,
        "reflection_status": result.overall_status.value,
        "reflection_metrics": metrics
    }

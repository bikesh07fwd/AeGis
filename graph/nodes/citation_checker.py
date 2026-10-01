from graph.state import GraphState
import re

async def citation_checker_node(state: GraphState) -> dict:
    """Node for checking citations deterministically using string matching."""
    answer = state.get("answer", "")
    context = state.get("formatted_context", "")
    
    # Simple deterministic heuristic: if the answer contains quotes, verify they exist in context
    quotes = re.findall(r'"([^"]*)"', answer)
    
    errors = state.get("errors", [])
    
    for quote in quotes:
        if len(quote) > 10 and quote not in context:
            # If a substantial quote is not in the context, flag it
            errors.append(f"Citation Error: Quoted text '{quote}' not found in retrieved context.")
            
    return {"errors": errors}

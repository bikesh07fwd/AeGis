import time
from functools import wraps

def track_telemetry(func):
    @wraps(func)
    async def wrapper(state: dict, *args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(state, *args, **kwargs)
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            node_name = func.__name__
            
            latencies = state.get("node_latencies", {})
            new_latencies = {**latencies, node_name: latency}
            
            errors = state.get("errors", [])
            new_errors = errors + [f"{node_name} crashed: {str(e)}"]
            
            return {
                "node_latencies": new_latencies,
                "errors": new_errors,
                "next_agent": "error_handler"
            }
            
        end_time = time.time()
        
        latency = end_time - start_time
        node_name = func.__name__
        
        latencies = state.get("node_latencies", {})
        new_latencies = {**latencies, node_name: latency}
        
        if isinstance(result, dict):
            result["node_latencies"] = new_latencies
            
            # Simple token usage extraction
            messages = result.get("messages", [])
            total_tokens_inc = 0
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "response_metadata"):
                    meta = last_msg.response_metadata
                    if 'token_usage' in meta and 'total_tokens' in meta['token_usage']:
                        total_tokens_inc = meta['token_usage']['total_tokens']
            
            new_total = state.get("total_tokens", 0) + total_tokens_inc
            # Roughly $1.25 per 1M tokens for Gemini Pro (blended average)
            new_cost = state.get("estimated_cost", 0.0) + (total_tokens_inc / 1_000_000.0) * 1.25
            
            result["total_tokens"] = new_total
            result["estimated_cost"] = new_cost
        
        return result
    return wrapper

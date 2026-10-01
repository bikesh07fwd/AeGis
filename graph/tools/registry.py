import asyncio
import logging
import time
from langchain_core.tools import tool
from graph.tools.permissions import check_permission, request_human_approval, ToolCategory, ToolPermission
from utils.circuit_breaker import CircuitBreaker, circuit_breaker

logger = logging.getLogger(__name__)

# Shared circuit breaker for external tool APIs
tool_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

async def tool_execution_wrapper(func, tool_name: str, category: ToolCategory, user_role: str, timeout_sec: int, *args, **kwargs):
    """Wrapper that enforces permissions, human approval, timeouts, and auditing."""
    # 1. Audit Log: Attempt
    logger.info(f"[AUDIT] Attempting to execute {tool_name} by role {user_role}. Args: {args} {kwargs}")
    
    # 2. Permission Check
    perm = ToolPermission(category=category, requires_approval=(category in [ToolCategory.WRITE, ToolCategory.DESTRUCTIVE]))
    check_permission(perm, user_role, tool_name)
    
    # 3. Human Approval for destructive/write actions
    if perm.requires_approval:
        # This will raise ApprovalRequiredException
        request_human_approval(tool_name, kwargs)
        
    # 4. Execution with timeout and circuit breaker
    @circuit_breaker(tool_circuit_breaker)
    async def execute_with_timeout():
        # Call the underlying function. If it's sync, wrap in thread. Here we assume async tools.
        return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
        
    try:
        start_t = time.time()
        result = await execute_with_timeout()
        dur = time.time() - start_t
        logger.info(f"[AUDIT] Successfully executed {tool_name} in {dur:.2f}s.")
        return result
    except asyncio.TimeoutError:
        logger.error(f"[AUDIT] Timeout executing {tool_name} after {timeout_sec}s.")
        return f"Error: Tool execution timed out after {timeout_sec} seconds."
    except Exception as e:
        logger.error(f"[AUDIT] Error executing {tool_name}: {str(e)}")
        return f"Error executing tool: {str(e)}"

# Example tools (converted to async to support proper timeouts)

@tool
async def search_google_drive(query: str, user_role: str = "Admin") -> str:
    """Searches Google Drive for documents matching the query."""
    async def _impl(query):
        await asyncio.sleep(0.5) # simulate latency
        return f"[Mock Drive Search] Found 1 document for '{query}': Invoice_August.pdf (Total: $450)"
    return await tool_execution_wrapper(_impl, "search_google_drive", ToolCategory.SEARCH, user_role, 5, query=query)

@tool
async def send_email(to: str, subject: str, body: str, user_role: str = "Admin") -> str:
    """Sends an email to the specified address."""
    async def _impl(to, subject, body):
        await asyncio.sleep(1)
        return f"[Mock Email] Sent email to {to} with subject '{subject}'."
    return await tool_execution_wrapper(_impl, "send_email", ToolCategory.WRITE, user_role, 10, to=to, subject=subject, body=body)

@tool
async def calculator(expression: str, user_role: str = "Admin") -> str:
    """Evaluates a mathematical expression (e.g., '450 * 0.15')."""
    async def _impl(expression):
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    return await tool_execution_wrapper(_impl, "calculator", ToolCategory.READ, user_role, 2, expression=expression)

enterprise_tools = [search_google_drive, send_email, calculator]

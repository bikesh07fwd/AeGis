import logging
from enum import Enum
from pydantic import BaseModel
from typing import Any

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    READ = "READ"
    SEARCH = "SEARCH"
    WRITE = "WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"

class ToolPermission(BaseModel):
    category: ToolCategory
    requires_approval: bool = False

class ApprovalRequiredException(Exception):
    pass

class PermissionDeniedException(Exception):
    pass

def check_permission(tool_permission: ToolPermission, user_role: str, tool_name: str) -> bool:
    """Check if the user has the basic capability to run this tool type."""
    # A simple RBAC mapping
    role_caps = {
        "Admin": [ToolCategory.READ, ToolCategory.SEARCH, ToolCategory.WRITE, ToolCategory.DESTRUCTIVE],
        "Analyst": [ToolCategory.READ, ToolCategory.SEARCH, ToolCategory.WRITE],
        "Viewer": [ToolCategory.READ, ToolCategory.SEARCH]
    }
    
    allowed = role_caps.get(user_role, [])
    if tool_permission.category not in allowed:
        logger.warning(f"Permission denied: Role {user_role} cannot execute {tool_name} ({tool_permission.category.value})")
        raise PermissionDeniedException(f"User role '{user_role}' lacks permission to execute '{tool_name}'.")
    return True

def request_human_approval(tool_name: str, args: dict[str, Any]) -> bool:
    """
    Hook for requesting human approval.
    In LangGraph, you would typically use `interrupt_before` on the tool node.
    Here we raise an exception that the agent must handle, or we simulate a pending state.
    """
    logger.info(f"[APPROVAL REQUIRED] Tool '{tool_name}' requested execution with args: {args}")
    # We raise an exception to stop execution. The agent receives this as an error.
    raise ApprovalRequiredException(f"Tool '{tool_name}' requires human approval. Request submitted.")

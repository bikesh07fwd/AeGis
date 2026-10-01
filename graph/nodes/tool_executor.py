from langgraph.prebuilt import ToolNode
from graph.tools.registry import enterprise_tools

# LangGraph provides a prebuilt ToolNode that handles execution and state updates automatically
tool_node = ToolNode(enterprise_tools)

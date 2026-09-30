from argus.tools.login_history import get_login_history
from argus.tools.ip_reputation import check_ip_reputation
from argus.tools.account_details import get_account_details
from argus.tools.related_incidents import search_related_incidents


TOOL_REGISTRY = {
    "get_login_history": get_login_history,
    "check_ip_reputation": check_ip_reputation,
    "get_account_details": get_account_details,
    "search_related_incidents": search_related_incidents,
}

def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Validate and execute a registered investigation tool."""

    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "tool": tool_name,
            "error": "Unknown or unregistered tool."
        }

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "tool": tool_name,
            "error": "Tool arguments must be a dictionary."
        }

    tool = TOOL_REGISTRY[tool_name]

    try:
        result = tool(**arguments)

        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }

    except TypeError as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Invalid tool arguments: {exc}"
        }

    except Exception as exc:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Tool execution failed: {exc}"
        }
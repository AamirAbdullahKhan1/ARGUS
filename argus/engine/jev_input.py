from argus.engine.investigation_state import InvestigationState


class JevInputFormatter:
    """Format ARGUS investigation data for Jev."""

    @staticmethod
    def build_state(state: InvestigationState) -> dict:
        evidence = []
        failed_tools = []
        tools_with_results = set()

        for item in state.evidence:
            tool_name = item.get("tool")
            result = item.get("result")

            tools_with_results.add(tool_name)

            # Match the success checks used by the investigation engine.
            success = (
                isinstance(result, dict)
                and result.get("success", False)
            )

            if (
                isinstance(result, dict)
                and isinstance(result.get("result"), dict)
                and result["result"].get("success") is False
            ):
                success = False

            if not success:
                failed_tools.append(tool_name)

            evidence.append({
                "tool": tool_name,
                "timestamp": item.get("timestamp"),
                "result": result
            })

        missing_tool_results = [
            tool
            for tool in state.executed_tools
            if tool not in tools_with_results
        ]

        return {
            "incident": state.incident,
            "investigation": {
                "status": state.status,
                "tools_executed": list(state.executed_tools),
                "tool_call_count": state.tool_calls
            },
            "evidence": evidence,
            "evidence_quality": {
                "failed_tools": failed_tools,
                "missing_tool_results": missing_tool_results
            }
        }
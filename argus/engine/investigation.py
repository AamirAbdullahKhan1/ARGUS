from argus.engine.investigation_state import InvestigationState
from argus.tool_executor import execute_tool
from argus.providers.mock_provider import MockDecisionProvider


MAX_TOOL_CALLS = 5


class InvestigationEngine:
    """Coordinates an incident investigation."""

    def __init__(self, decision_provider=None):
        self.decision_provider = (
            decision_provider or MockDecisionProvider()
        )

    def investigate(self, incident: dict) -> InvestigationState:
        """Run an investigation using the configured provider."""

        state = InvestigationState(incident)

        while state.tool_calls < MAX_TOOL_CALLS:
            tool_name = self.decision_provider.select_tool(
                incident,
                state.executed_tools
            )

            if tool_name is None:
                state.complete(
                    "pending_review",
                    "All available investigation tools have been executed."
                )
                return state

            arguments = self._build_arguments(tool_name, incident)

            result = execute_tool(tool_name, arguments)

            state.record_tool_call(tool_name)

            state.add_evidence(tool_name, result)

            if not result.get("success", False):
                state.fail(
                    f"Tool execution failed: {tool_name}"
                )
                return state

        state.fail("Maximum tool call limit reached.")
        return state

    @staticmethod
    def _build_arguments(tool_name: str, incident: dict) -> dict:
        """Build arguments for a tool using incident details."""

        if tool_name == "get_login_history":
            return {
                "username": incident.get("username", ""),
                "source_ip": incident.get("source_ip", "")
            }

        if tool_name == "check_ip_reputation":
            return {
                "ip": incident.get("source_ip", "")
            }

        if tool_name == "get_account_details":
            return {
                "username": incident.get("username", "")
            }

        if tool_name == "search_related_incidents":
            return {
                "username": incident.get("username"),
                "source_ip": incident.get("source_ip"),
                "incident_type": incident.get("event_type")
            }

        return {}
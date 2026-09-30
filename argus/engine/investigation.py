from argus.engine.investigation_state import InvestigationState
from argus.tool_executor import execute_tool
from argus.providers.groq_provider import GroqDecisionProvider


MAX_TOOL_CALLS = 5


class InvestigationEngine:
    """Coordinates an LLM-driven investigation."""

    def __init__(self, decision_provider=None, event_callback=None):
        self.decision_provider = (
            decision_provider or GroqDecisionProvider()
        )
        self.event_callback = event_callback

    def _emit(self, event: str, **details):
        """Send an event to the configured callback."""

        if self.event_callback:
            self.event_callback(event, details)

    def investigate(self, incident: dict) -> InvestigationState:
        """Run an adaptive investigation."""

        state = InvestigationState(incident)

        self._emit(
            "investigation_started",
            incident_id=incident.get("incident_id"),
        )

        while state.tool_calls < MAX_TOOL_CALLS:
            self._emit(
                "decision_started",
                tool_calls=state.tool_calls,
            )

            try:
                decision = self.decision_provider.select_action(
                    incident,
                    state,
                )

            except Exception as exc:
                state.fail(f"Decision provider failed: {exc}")

                self._emit(
                    "investigation_failed",
                    reason=state.reasoning,
                )
                return state

            self._emit(
                "decision_received",
                decision=decision,
            )

            action = decision["action"]

            if action == "complete":
                state.complete(
                    decision["recommendation"],
                    decision["reason"],
                )

                self._emit(
                    "investigation_completed",
                    recommendation=state.recommendation,
                    reasoning=state.reasoning,
                    tool_calls=state.tool_calls,
                )
                return state

            if action == "call_tool":
                tool_name = decision["tool"]

                if tool_name in state.executed_tools:
                    state.fail(
                        f"Repeated tool call: {tool_name}"
                    )

                    self._emit(
                        "investigation_failed",
                        reason=state.reasoning,
                    )
                    return state

                arguments = self._build_arguments(
                    tool_name,
                    incident,
                )

                self._emit(
                    "tool_started",
                    tool=tool_name,
                    arguments=arguments,
                    reason=decision.get("reason", ""),
                )

                result = execute_tool(
                    tool_name,
                    arguments,
                )

                state.record_tool_call(tool_name)
                state.add_evidence(tool_name, result)

                tool_result = result.get("result", {})

                tool_success = result.get("success", False)

                if isinstance(tool_result, dict):
                    if tool_result.get("success") is False:
                        tool_success = False

                self._emit(
                    "tool_completed",
                    tool=tool_name,
                    success=tool_success,
                    result=result,
                )

                if not tool_success:
                    state.fail(
                        f"Tool execution failed: {tool_name}"
                    )

                    self._emit(
                        "investigation_failed",
                        reason=state.reasoning,
                    )
                    return state

        state.fail("Maximum tool call limit reached.")

        self._emit(
            "investigation_failed",
            reason=state.reasoning,
        )
        return state

    @staticmethod
    def _build_arguments(tool_name: str, incident: dict) -> dict:
        """Build tool arguments from the incident."""

        if tool_name == "get_login_history":
            return {
                "username": incident.get("username", ""),
                "source_ip": incident.get("source_ip", ""),
            }

        if tool_name == "check_ip_reputation":
            return {
                "ip": incident.get("source_ip", ""),
            }

        if tool_name == "get_account_details":
            return {
                "username": incident.get("username", ""),
            }

        if tool_name == "search_related_incidents":
            return {
                "username": incident.get("username"),
                "source_ip": incident.get("source_ip"),
                "incident_type": incident.get("event_type"),
            }

        raise ValueError(
            f"Unsupported tool: {tool_name}"
        )
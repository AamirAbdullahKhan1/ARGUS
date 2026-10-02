from argus.engine.investigation_state import InvestigationState
from argus.tool_executor import execute_tool
from argus.providers.groq_provider import GroqDecisionProvider
from argus.reporting.history import save_investigation

MAX_TOOL_CALLS = 5

class InvestigationEngine:
    def __init__(
        self,
        decision_provider=None,
        jev_provider=None,
        event_callback=None,
        provider_name="groq",
    ):
        # Groq always orchestrates the investigation.
        self.decision_provider = (
            decision_provider or GroqDecisionProvider()
        )

        # Jev is used only for final decisions in Jev mode.
        self.jev_provider = jev_provider

        self.event_callback = event_callback
        self.provider_name = provider_name

        if provider_name not in ("groq", "jev"):
            raise ValueError(
                f"Unsupported provider: {provider_name}"
            )

        if provider_name == "jev" and jev_provider is None:
            raise ValueError(
                "JevDecisionProvider is required in Jev mode."
            )

    def _emit(self, event: str, **details):
        if self.event_callback:
            self.event_callback(event, details)

    def _save_state(self, state: InvestigationState):
        """Save the investigation state to persistent history."""
        try:
            save_investigation(state)
            self._emit(
                "history_saved",
                investigation_id=state.investigation_id
            )
        except Exception as exc:
            self._emit(
                "history_save_failed",
                error=str(exc),
                investigation_id=state.investigation_id
            )

    def _complete_with_jev(self, state):
        """Use Jev for the final risk and response decisions."""
        try:
            self._emit("jev_risk_assessment_started")

            risk_response = self.jev_provider.assess_risk(state)

            risk_answer = risk_response["answers"]["risk_assessment"]

            # Jev's score is zero-based for the supplied criteria.
            raw_score = float(risk_answer["score"])
            risk_score = raw_score + 1

            self._emit(
                "jev_risk_assessment_completed",
                risk_score=risk_score,
                confidence=risk_answer.get("confidence"),
            )

            self._emit("jev_response_recommendation_started")

            response = self.jev_provider.recommend_response(
                state,
                risk_response
            )

            response_answer = response[
                "answers"
            ]["response_recommendation"]

            recommendation = response_answer["choice"]

            reasoning = (
                "Response selected by Jev using the investigation "
                "evidence and risk assessment."
            )

            risk_reasoning = (
                "Jev risk assessment. "
                f"Raw score: {raw_score}. "
                f"Confidence: {risk_answer.get('confidence')}."
            )

            state.complete_jev(
                risk_score=risk_score,
                risk_reasoning=risk_reasoning,
                response_recommendation=recommendation,
                response_reasoning=reasoning,
            )

            self._save_state(state)

            self._emit(
                "investigation_completed",
                recommendation=state.recommendation,
                risk_score=state.risk_score,
                reasoning=state.reasoning,
                risk_reasoning=state.risk_reasoning,
                tool_calls=state.tool_calls,
                provider=self.provider_name,
            )

            return state

        except Exception as exc:
            state.fail(f"Jev decision failed: {exc}")
            self._save_state(state)

            self._emit(
                "investigation_failed",
                reason=state.reasoning,
                provider=self.provider_name,
            )

            return state

    def investigate(self, incident: dict) -> InvestigationState:
        state = InvestigationState(
            incident,
            provider=self.provider_name,
        )

        self._emit(
            "investigation_started",
            incident_id=incident.get("incident_id"),
            provider=self.provider_name,
        )

        while state.tool_calls < MAX_TOOL_CALLS:
            self._emit(
                "decision_started",
                tool_calls=state.tool_calls
            )

            try:
                decision = self.decision_provider.select_action(
                    incident, state
                )

            except ValueError as exc:
                if "Tool already executed:" in str(exc):
                    self._emit(
                        "invalid_tool_request",
                        reason=str(exc),
                        tool_calls=state.tool_calls,
                    )

                    # Retry once if Groq requests an already-used tool.
                    try:
                        decision = (
                            self.decision_provider.select_action(
                                incident, state
                            )
                        )

                    except Exception as retry_exc:
                        state.fail(
                            "Decision provider failed after retry: "
                            f"{retry_exc}"
                        )
                        self._save_state(state)
                        self._emit(
                            "investigation_failed",
                            reason=state.reasoning
                        )
                        return state

                else:
                    state.fail(
                        f"Decision provider failed: {exc}"
                    )
                    self._save_state(state)
                    self._emit(
                        "investigation_failed",
                        reason=state.reasoning
                    )
                    return state

            except Exception as exc:
                state.fail(
                    f"Decision provider failed: {exc}"
                )
                self._save_state(state)
                self._emit(
                    "investigation_failed",
                    reason=state.reasoning
                )
                return state

            self._emit("decision_received", decision=decision)

            action = decision["action"]

            if action == "complete":
                if self.provider_name == "jev":
                    return self._complete_with_jev(state)

                # Existing Groq-only completion behavior.
                state.risk_score = decision["risk_score"]
                state.risk_reasoning = decision["risk_reasoning"]

                state.complete(
                    decision["recommendation"],
                    decision["reason"]
                )

                self._save_state(state)

                self._emit(
                    "investigation_completed",
                    recommendation=state.recommendation,
                    risk_score=state.risk_score,
                    reasoning=state.reasoning,
                    risk_reasoning=state.risk_reasoning,
                    tool_calls=state.tool_calls,
                    provider=self.provider_name,
                )
                return state

            if action == "call_tool":
                tool_name = decision["tool"]

                if tool_name in state.executed_tools:
                    state.fail(
                        f"Repeated tool call: {tool_name}"
                    )
                    self._save_state(state)
                    self._emit(
                        "investigation_failed",
                        reason=state.reasoning
                    )
                    return state

                arguments = self._build_arguments(
                    tool_name, incident
                )

                self._emit(
                    "tool_started",
                    tool=tool_name,
                    arguments=arguments,
                    reason=decision.get("reason", "")
                )

                result = execute_tool(tool_name, arguments)

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
                    result=result
                )

                if not tool_success:
                    state.fail(
                        f"Tool execution failed: {tool_name}"
                    )
                    self._save_state(state)
                    self._emit(
                        "investigation_failed",
                        reason=state.reasoning
                    )
                    return state

        state.fail("Maximum tool call limit reached.")
        self._save_state(state)
        self._emit(
            "investigation_failed",
            reason=state.reasoning
        )
        return state

    @staticmethod
    def _build_arguments(tool_name: str, incident: dict) -> dict:
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

        raise ValueError(f"Unsupported tool: {tool_name}")

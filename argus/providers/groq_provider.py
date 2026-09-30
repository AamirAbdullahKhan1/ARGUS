import json

from argus.groq_client import GroqClient


AVAILABLE_TOOLS = {
    "get_login_history",
    "check_ip_reputation",
    "get_account_details",
    "search_related_incidents",
}


class GroqDecisionProvider:
    """Uses Groq to make investigation decisions."""

    def __init__(self, client=None):
        self.client = client or GroqClient()

    def select_action(self, incident: dict, state) -> dict:
        """Ask the LLM to select the next investigation action."""

        system_prompt = """
You are ARGUS, an AI-driven cybersecurity incident
response investigation agent.

Your task is to investigate security incidents using
the available tools and collected evidence.

You must decide whether to:
1. Call an investigation tool.
2. Complete the investigation with a recommendation.

Available tools:
- get_login_history
- check_ip_reputation
- get_account_details
- search_related_incidents

Rules:
- Only select tools from the available list.
- Do not request tools that have already been executed.
- Use the incident and collected evidence to guide decisions.
- Do not invent evidence or claim a tool was executed
  when it was not.
- If evidence is insufficient, investigate further.
- If sufficient evidence is available, complete the
  investigation.
- Recommendations must be one of:
  escalate, monitor, dismiss, pending_review.
- Do not claim to have blocked accounts or changed systems.
- If a tool fails, do not treat its missing results as
  evidence that the incident is harmless.

Return ONLY valid JSON using one of these formats.

To call a tool:
{
    "action": "call_tool",
    "tool": "get_login_history",
    "reason": "Why this tool is needed"
}

To complete the investigation:
{
    "action": "complete",
    "recommendation": "escalate",
    "reason": "Explanation based on collected evidence"
}
"""

        investigation_context = {
            "incident": incident,
            "executed_tools": state.executed_tools,
            "tool_calls": state.tool_calls,
            "evidence": state.evidence,
        }

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": json.dumps(
                    investigation_context,
                    indent=2,
                ),
            },
        ]

        response = self.client.generate(messages)

        try:
            decision = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {exc}"
            ) from exc

        self._validate_decision(decision, state)

        return decision

    @staticmethod
    def _validate_decision(decision: dict, state):
        """Validate the structure and contents of an LLM decision."""

        if not isinstance(decision, dict):
            raise ValueError("Decision must be a JSON object.")

        action = decision.get("action")

        if action == "call_tool":
            tool_name = decision.get("tool")

            if tool_name not in AVAILABLE_TOOLS:
                raise ValueError(
                    f"Unknown tool requested: {tool_name}"
                )

            if tool_name in state.executed_tools:
                raise ValueError(
                    f"Tool already executed: {tool_name}"
                )

            if not isinstance(decision.get("reason"), str):
                raise ValueError("Tool decision requires a reason.")

        elif action == "complete":
            recommendation = decision.get("recommendation")

            allowed_recommendations = {
                "escalate",
                "monitor",
                "dismiss",
                "pending_review",
            }

            if recommendation not in allowed_recommendations:
                raise ValueError(
                    "Invalid final recommendation."
                )

            if not isinstance(decision.get("reason"), str):
                raise ValueError(
                    "Completion decision requires a reason."
                )

        else:
            raise ValueError(
                f"Unsupported action: {action}"
            )
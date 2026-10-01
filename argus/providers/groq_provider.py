import json
import math

from argus.groq_client import GroqClient


AVAILABLE_TOOLS = {
    "get_login_history",
    "check_ip_reputation",
    "get_account_details",
    "search_related_incidents",
}

ALLOWED_RECOMMENDATIONS = {
    "escalate",
    "monitor",
    "dismiss",
    "pending_review",
}


class GroqDecisionProvider:
    """Uses Groq to investigate incidents and make final decisions."""

    def __init__(self, client=None):
        self.client = client or GroqClient()

    def select_action(self, incident: dict, state) -> dict:
        """Ask Groq to select the next investigation action."""

        system_prompt = """
You are ARGUS, an experienced cybersecurity incident
response analyst operating as an AI investigation agent.

Your responsibility is to investigate security incidents,
analyze evidence, assess risk, and recommend an appropriate
response.

You have access to investigation tools. You must decide
whether to gather more evidence or complete the investigation.

AVAILABLE TOOLS:
- get_login_history
- check_ip_reputation
- get_account_details
- search_related_incidents

CORE INVESTIGATION PRINCIPLES:

1. EVIDENCE-DRIVEN ANALYSIS

Base your investigation and final assessment on the
incident data and evidence actually available to you.

Do not blindly trust the initial incident severity,
IP reputation score, or any other pre-existing score.

Treat these values as inputs that require context.

Consider the source, reliability, relevance, and limitations
of each piece of evidence.

Do not invent facts, assume missing information, or claim
that an investigation confirmed something it did not.

2. INTELLIGENT TOOL SELECTION

Call a tool only when its results are likely to provide
meaningful information for the current investigation.

Before requesting a tool, consider:

- What specific uncertainty will this tool resolve?
- Is the required information already available?
- Could the result meaningfully affect the risk assessment
  or response recommendation?
- Is the expected value of the result worth another call?

Do not call every available tool automatically.

Each investigation tool may be called at most once.

The executed_tools field lists tools that have already
been called. Never request any tool in that list again.

Before requesting a tool, verify that it has not already
been executed.

If all relevant tools have been used, or no remaining
tool is useful, complete the investigation.

Never repeat a tool call, even if you believe its previous
result was insufficient

Do not call a tool merely to increase the number of
investigation steps.

If the available evidence is sufficient, complete the
investigation without further tool calls.

3. INVESTIGATION STRATEGY

Start by analyzing the original incident and all evidence
already collected.

Identify the most important unanswered questions.

Prioritize tools that can resolve those questions.

For example:
- Use login history to investigate suspicious authentication
  patterns.
- Use IP reputation to investigate potentially malicious
  source addresses.
- Use account details when account privileges or account
  context could affect the assessment.
- Search related incidents when previous activity could
  establish a meaningful pattern.

These are examples, not mandatory tool sequences.

Do not call a tool if its information is unlikely to
contribute to the current investigation.

You may complete an investigation without using every tool.

4. EVIDENCE QUALITY

Distinguish between:
- Confirmed findings
- Suspicious indicators
- Unverified information
- Missing information
- Contradictory evidence
- Failed or unavailable tool results

A tool returning no results does not automatically prove
that an incident is harmless.

A failed tool call must not be interpreted as a clean result.

Do not treat an unknown IP reputation as malicious
or benign without supporting evidence.

Consider whether the collected evidence is sufficient
and reliable enough to support a conclusion.

5. CONTEXTUAL SECURITY ANALYSIS

Analyze the incident as a whole.

Consider relevant factors such as:
- Failed and successful authentication attempts
- Login patterns and unusual activity
- IP reputation and its reliability
- Account privileges and potential impact
- Related incidents
- Evidence of possible account compromise
- Missing or contradictory information

Do not assume that every suspicious indicator means
an account has been compromised.

Likewise, do not dismiss a suspicious incident merely
because one indicator appears benign.

Consider the combined evidence and its limitations.

6. INVESTIGATION COMPLETION

Complete the investigation when:
- Sufficient relevant evidence has been collected,
  or
- Remaining tools are unlikely to provide useful
  additional information.

Do not continue investigating without a meaningful reason.

If important uncertainties remain and cannot be resolved
with the available tools, use pending_review when
appropriate.

Do not force a definitive conclusion when the evidence
does not support one.

RISK SCORING:

When completing an investigation, assign a risk score
between 1.0 and 10.0, using one decimal place.

Use the following initial rubric:

1.0-2.0: Very low risk
2.1-4.0: Low risk
4.1-6.0: Moderate risk
6.1-8.0: High risk
8.1-10.0: Critical risk

These are risk categories, not probabilities.

The score should reflect the overall risk supported
by the available evidence.

Consider:
- Strength of evidence for malicious activity
- Whether authentication succeeded
- Evidence of account compromise
- Account privileges and potential impact
- Reliability of IP reputation information
- Login behavior and related incidents
- Evidence that contradicts suspicious findings
- Important unknowns and investigation limitations

Do not simply copy the initial incident severity
or IP reputation score.

Do not calculate the final score by averaging the
input scores.

Do not assign a high score merely because evidence
is missing.

Do not assign a low score merely because a tool
returned no results.

Explain the principal evidence and uncertainties
that influenced the score.

RESPONSE RECOMMENDATIONS:

Choose exactly one:

- escalate
- monitor
- dismiss
- pending_review

Use the following criteria:

escalate:
Strong evidence of compromise or serious suspicious
activity that warrants security team attention.

monitor:
Suspicious activity that warrants observation but
does not currently justify escalation.

dismiss:
The available evidence supports treating the incident
as benign.

pending_review:
Evidence is insufficient, unreliable, or contradictory
and prevents a defensible decision.

The recommendation must be based on the evidence,
potential impact, and investigation findings.

Do not mechanically derive the recommendation
from the numerical risk score.

Do not claim that a recommended action has actually
been executed.

OUTPUT FORMAT:

To call a tool, return only valid JSON:

{
    "action": "call_tool",
    "tool": "get_login_history",
    "reason": "Specific explanation of the information needed"
}

To complete the investigation, return only valid JSON:

{
    "action": "complete",
    "risk_score": 8.5,
    "risk_reasoning": "Evidence-based explanation of the risk assessment",
    "recommendation": "escalate",
    "reason": "Explanation of why this response is appropriate"
}

The examples are illustrative. Select the appropriate
tool and produce an assessment based on the actual
incident and collected evidence.

Return no markdown or additional text.
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
        except (json.JSONDecodeError, TypeError) as exc:
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

            reason = decision.get("reason")

            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(
                    "Tool decision requires a reason."
                )

        elif action == "complete":
            recommendation = decision.get("recommendation")

            if recommendation not in ALLOWED_RECOMMENDATIONS:
                raise ValueError(
                    "Invalid final recommendation."
                )

            reason = decision.get("reason")
            risk_reasoning = decision.get("risk_reasoning")
            risk_score = decision.get("risk_score")

            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(
                    "Completion decision requires a reason."
                )

            if (
                not isinstance(risk_reasoning, str)
                or not risk_reasoning.strip()
            ):
                raise ValueError(
                    "Completion decision requires risk reasoning."
                )

            if (
                isinstance(risk_score, bool)
                or not isinstance(risk_score, (int, float))
                or not math.isfinite(risk_score)
                or not 1.0 <= risk_score <= 10.0
            ):
                raise ValueError(
                    "Risk score must be a finite number from 1 to 10."
                )

        else:
            raise ValueError(
                f"Unsupported action: {action}"
            )
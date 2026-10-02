from argus.engine.jev_input import JevInputFormatter
from argus.jev_client import JevClient


class JevDecisionProvider:
    """Make incident response decisions using Jev."""

    RISK_QUESTION = {
        "risk_assessment": {
            "type": "score",
            "instructions": (
                "Assess the security risk of this incident using "
                "the incident details and investigation evidence. "
                "Consider the severity of the activity, the reliability "
                "and completeness of the evidence, and any indicators "
                "of compromise. Do not assume missing evidence indicates "
                "a safe condition. Assign a risk level from 1 to 10."
            ),
            "criteria": [
                "1 - Negligible risk",
                "2 - Very low risk",
                "3 - Low risk",
                "4 - Moderate-low risk",
                "5 - Moderate risk",
                "6 - Moderate-high risk",
                "7 - High risk",
                "8 - Very high risk",
                "9 - Critical risk",
                "10 - Extreme risk",
            ],
        }
    }

    RESPONSE_QUESTION = {
        "response_recommendation": {
            "type": "choice",
            "instructions": (
                "Based on the incident, investigation evidence, "
                "and risk assessment provided, select the most "
                "appropriate incident response action. Consider "
                "the severity of the evidence and the potential "
                "impact of acting incorrectly."
            ),
            "criteria": {
                "monitor": (
                    "Continue monitoring the incident without "
                    "immediate containment."
                ),
                "investigate": (
                    "Collect additional evidence before taking "
                    "a containment action."
                ),
                "escalate": (
                    "Escalate the incident to a human security "
                    "analyst for further investigation."
                ),
                "contain": (
                    "Take an immediate containment action to "
                    "limit potential damage."
                ),
            },
        }
    }

    def __init__(self, client=None):
        self.client = client or JevClient()

    def assess_risk(self, state):
        jev_state = JevInputFormatter.build_state(state)

        response = self.client.generate(
            state=jev_state,
            questions=self.RISK_QUESTION,
        )

        state.jev_responses["risk_assessment"] = response
        return response

    def recommend_response(self, state, risk_assessment):
        jev_state = JevInputFormatter.build_state(state)
        jev_state["risk_assessment"] = risk_assessment

        response = self.client.generate(
            state=jev_state,
            questions=self.RESPONSE_QUESTION,
        )

        state.jev_responses["response_recommendation"] = response
        return response

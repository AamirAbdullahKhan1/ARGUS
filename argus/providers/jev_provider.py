import os
import requests

from argus.engine.jev_input import JevInputFormatter


class JevDecisionProvider:
    """Make incident response decisions using Jev."""

    API_URL = "https://jev-ai.org/api/v1/systemone/"
    MODEL = "jev-1.13"

    RISK_QUESTION = {
    "risk_assessment": {
        "type": "score",
        "instructions": (
            "Assess the security risk of this incident using "
            "the incident details and investigation evidence. "
            "Consider the severity of the activity, the reliability "
            "and completeness of the evidence, and any indicators "
            "of compromise. Do not assume missing evidence indicates "
            "a safe condition. Return a risk score from 1 to 10, "
            "where 1 represents negligible risk and 10 represents "
            "critical risk."
        )
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
                )
            }
        }
    }

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("JEV_API_KEY")

        if not self.api_key:
            raise ValueError("JEV_API_KEY is not configured.")

    def _make_request(self, state, questions):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.MODEL,
            "state": state,
            "questions": questions
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def assess_risk(self, state):
        jev_state = JevInputFormatter.build_state(state)

        response = self._make_request(
            state=jev_state,
            questions=self.RISK_QUESTION
        )

        state.jev_responses["risk_assessment"] = response

        return response

    def recommend_response(self, state, risk_assessment):
        jev_state = JevInputFormatter.build_state(state)

        jev_state["risk_assessment"] = risk_assessment

        response = self._make_request(
            state=jev_state,
            questions=self.RESPONSE_QUESTION
        )

        state.jev_responses["response_recommendation"] = response

        return response
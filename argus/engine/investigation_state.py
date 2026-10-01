from datetime import datetime, timezone
from uuid import uuid4


class InvestigationState:
    def __init__(self, incident: dict, provider: str = "groq"):
        self.investigation_id = str(uuid4())
        self.incident = incident
        self.provider = provider
        self.status = "in_progress"

        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at = None

        self.evidence = []
        self.executed_tools = []
        self.tool_calls = 0

        # Final decision
        self.recommendation = None
        self.reasoning = None

        # Jev risk assessment
        self.risk_score = None
        self.risk_reasoning = None

        # Jev response recommendation
        self.response_recommendation = None
        self.response_reasoning = None

        # Raw Jev API responses
        self.jev_responses = {
            "risk_assessment": None,
            "response_recommendation": None
        }

    def add_evidence(self, tool_name: str, result: dict):
        self.evidence.append({
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def record_tool_call(self, tool_name: str):
        self.executed_tools.append(tool_name)
        self.tool_calls += 1

    def complete(self, recommendation: str, reasoning: str):
        self.status = "completed"
        self.recommendation = recommendation
        self.reasoning = reasoning
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def complete_jev(
        self,
        risk_score,
        risk_reasoning,
        response_recommendation,
        response_reasoning
    ):
        self.status = "completed"

        self.risk_score = risk_score
        self.risk_reasoning = risk_reasoning

        self.response_recommendation = response_recommendation
        self.response_reasoning = response_reasoning

        # Keep the common final-decision fields consistent.
        self.recommendation = response_recommendation
        self.reasoning = response_reasoning

        self.completed_at = datetime.now(timezone.utc).isoformat()

    def fail(self, reason: str):
        self.status = "failed"
        self.reasoning = reason
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "incident": self.incident,
            "provider": self.provider,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "evidence": self.evidence,
            "executed_tools": self.executed_tools,
            "tool_calls": self.tool_calls,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
            "risk_score": self.risk_score,
            "risk_reasoning": self.risk_reasoning,
            "response_recommendation": self.response_recommendation,
            "response_reasoning": self.response_reasoning,
            "jev_responses": self.jev_responses
        }
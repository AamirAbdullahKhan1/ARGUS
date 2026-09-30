from datetime import datetime, timezone
from uuid import uuid4


class InvestigationState:
    def __init__(self, incident: dict):
        self.investigation_id = str(uuid4())
        self.incident = incident
        self.status = "in_progress"

        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at = None

        self.evidence = []
        self.executed_tools = []
        self.tool_calls = 0

        self.recommendation = None
        self.reasoning = None

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

    def fail(self, reason: str):
        self.status = "failed"
        self.reasoning = reason
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "incident": self.incident,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "evidence": self.evidence,
            "executed_tools": self.executed_tools,
            "tool_calls": self.tool_calls,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning
        }
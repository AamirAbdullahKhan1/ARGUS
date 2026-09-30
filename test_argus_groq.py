from argus.engine.investigation import InvestigationEngine
from argus.data_loader import get_incident_by_id


incident = get_incident_by_id("INC-001")

if incident is None:
    raise ValueError("Incident INC-001 not found.")

engine = InvestigationEngine()

state = engine.investigate(incident)

print("\nARGUS INVESTIGATION RESULT")
print("=" * 50)

print("Incident:", incident["incident_id"])
print("Status:", state.status)
print("Tools executed:", state.tool_calls)
print("Executed tools:", state.executed_tools)
print("Recommendation:", state.recommendation)
print("Reasoning:", state.reasoning)

print("\nCOLLECTED EVIDENCE")
print("=" * 50)

for evidence in state.evidence:
    print("\nTool:", evidence["tool"])
    print("Result:", evidence["result"])
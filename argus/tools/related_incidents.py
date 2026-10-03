import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORY_FILE = PROJECT_ROOT / "data" / "previous_incidents.json"


def search_related_incidents(
    username: str | None = None,
    source_ip: str | None = None,
    incident_type: str | None = None,
) -> dict:
    """Search historical incidents using available criteria."""

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Historical incident dataset not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid historical incident JSON."
        }

    incidents = data.get("previous_incidents", [])

    if not isinstance(incidents, list):
        return {
            "success": False,
            "error": "Invalid historical incident dataset structure."
        }

    matches = []

    for incident in incidents:
        if not isinstance(incident, dict):
            continue

        if username and str(
            incident.get("username", "")
        ).casefold() != username.casefold():
            continue

        if source_ip and str(
            incident.get("source_ip", "")
        ) != source_ip:
            continue

        if incident_type and str(
            incident.get("event_type", "")
        ).casefold() != incident_type.casefold():
            continue

        matches.append(incident)

    return {
        "success": True,
        "criteria": {
            "username": username,
            "source_ip": source_ip,
            "incident_type": incident_type
        },
        "total_matches": len(matches),
        "incidents": matches
    }
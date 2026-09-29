import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

INCIDENTS_FILE = DATA_DIR / "incidents.json"
HISTORY_FILE = DATA_DIR / "previous_incidents.json"


def load_json_file(file_path: Path) -> dict:
    """Load and return JSON data from a file."""

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {file_path}: {exc}"
        )


def load_incidents() -> list[dict]:
    """Load current incidents."""

    data = load_json_file(INCIDENTS_FILE)
    incidents = data.get("incidents")

    if not isinstance(incidents, list):
        raise ValueError(
            "Invalid incidents.json: 'incidents' must be a list."
        )

    return incidents


def load_previous_incidents() -> list[dict]:
    """Load historical incidents."""

    data = load_json_file(HISTORY_FILE)
    incidents = data.get("previous_incidents")

    if not isinstance(incidents, list):
        raise ValueError(
            "Invalid previous_incidents.json: "
            "'previous_incidents' must be a list."
        )

    return incidents


def get_incident_by_id(incident_id: str) -> dict | None:
    """Find a current incident by its ID."""

    incidents = load_incidents()

    for incident in incidents:
        if incident.get("id", "").lower() == incident_id.lower():
            return incident

    return None
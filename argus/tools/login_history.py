import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGIN_EVENTS_FILE = PROJECT_ROOT / "data" / "login_events.json"


def get_login_history(username: str, source_ip: str) -> dict:
    """Retrieve login events for a specific user and IP."""

    try:
        with LOGIN_EVENTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Login events dataset not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid login events JSON."
        }

    events = data.get("login_events", [])

    if not isinstance(events, list):
        return {
            "success": False,
            "error": "Invalid login events dataset structure."
        }

    matching_events = [
        event for event in events
        if isinstance(event, dict)
        and str(event.get("username", "")).casefold() == username.casefold()
        and str(event.get("source_ip", "")) == source_ip
    ]

    return {
        "success": False,
        "username": username,
        "source_ip": source_ip,
        "total_events": len(matching_events),
        "events": matching_events
    }
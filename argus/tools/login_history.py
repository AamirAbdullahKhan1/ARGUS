import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGIN_EVENTS_FILE = PROJECT_ROOT / "data" / "login_events.json"


def get_login_history(
    username: str,
    incident_timestamp: str,
    lookback_days: int = 7,
) -> dict:
    """Retrieve a user's login events from the previous N days."""

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

    login_history = data.get("login_history", [])

    if not isinstance(login_history, list):
        return {
            "success": False,
            "error": "Invalid login events dataset structure."
        }

    user_record = next(
        (
            record
            for record in login_history
            if isinstance(record, dict)
            and str(record.get("username", "")).casefold()
            == username.casefold()
        ),
        None,
    )

    if user_record is None:
        return {
            "success": True,
            "username": username,
            "lookback_days": lookback_days,
            "total_events": 0,
            "successful_logins": 0,
            "failed_logins": 0,
            "unique_source_ips": 0,
            "events": [],
        }

    user_events = user_record.get("events", [])

    if not isinstance(user_events, list):
        return {
            "success": False,
            "error": "Invalid event structure for user."
        }

    try:
        incident_time = datetime.fromisoformat(
            incident_timestamp.replace("Z", "+00:00")
        )

    except ValueError:
        return {
            "success": False,
            "error": "Invalid incident timestamp."
        }

    start_time = incident_time - timedelta(days=lookback_days)

    matching_events = []

    for event in user_events:   
        if not isinstance(event, dict):
            continue

        timestamp = event.get("timestamp")

        if not timestamp:
            continue

        try:
            event_time = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

        except ValueError:
            continue

        if start_time <= event_time < incident_time:
            matching_events.append(event)

    successful_logins = sum(
        1
        for event in matching_events
        if event.get("status") == "success"
    )

    failed_logins = sum(
        1
        for event in matching_events
        if event.get("status") == "failed"
    )

    unique_source_ips = len({
        event.get("source_ip")
        for event in matching_events
        if event.get("source_ip")
    })

    result =  {
        "success": True,
        "username": username,
        "lookback_days": lookback_days,
        "incident_timestamp": incident_timestamp,
        "total_events": len(matching_events),
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "unique_source_ips": unique_source_ips,
        "events": matching_events,
    }

    json.dumps(result, indent=2)

    return result
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IP_REPUTATION_FILE = PROJECT_ROOT / "data" / "ip_reputation.json"


def check_ip_reputation(ip: str) -> dict:
    """Retrieve reputation information for an IP address."""

    try:
        with IP_REPUTATION_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "IP reputation dataset not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid IP reputation JSON."
        }

    records = data.get("ip_reputation", [])

    if not isinstance(records, list):
        return {
            "success": False,
            "error": "Invalid IP reputation dataset structure."
        }

    for record in records:
        if (
            isinstance(record, dict)
            and record.get("ip") == ip
        ):
            return {
                "success": True,
                "ip": ip,
                "data": record
            }

    return {
        "success": False,
        "ip": ip,
        "data": None,
        "message": "No reputation data found for this IP."
    }
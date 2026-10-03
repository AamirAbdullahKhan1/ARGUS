import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACCOUNTS_FILE = PROJECT_ROOT / "data" / "accounts.json"


def get_account_details(username: str) -> dict:
    """Retrieve account information for a username."""

    try:
        with ACCOUNTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Account dataset not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid account dataset JSON."
        }

    accounts = data.get("accounts", [])

    if not isinstance(accounts, list):
        return {
            "success": False,
            "error": "Invalid account dataset structure."
        }

    for account in accounts:
        if (
            isinstance(account, dict)
            and str(account.get("username", "")).casefold()
            == username.strip().casefold()
        ):
            return {
                "success": True,
                "username": username,
                "account": account
            }

    return {
        "success": True,
        "username": username,
        "account": None,
        "message": "Account not found."
    }
import json
from pathlib import Path

HISTORY_FILE = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "investigation_history.json"
)


def load_history() -> list[dict]:
    """Load all saved investigation records."""

    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            history = json.load(file)

        if not isinstance(history, list):
            raise ValueError("Investigation history must be a JSON list.")

        return history

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Investigation history contains invalid JSON: {exc}"
        ) from exc


def save_investigation(state) -> dict:
    """Save an investigation state to the history file."""

    record = state.to_dict()

    if not isinstance(record, dict):
        raise TypeError("Investigation state must return a dictionary.")

    if not record.get("investigation_id"):
        raise ValueError("Investigation is missing its ID.")

    history = load_history()

    # Prevent accidentally saving the same investigation twice.
    for existing in history:
        if existing.get("investigation_id") == record["investigation_id"]:
            return existing

    history.append(record)

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, indent=4, ensure_ascii=False)

    return record


def get_investigation(investigation_id: str) -> dict | None:
    """Find an investigation by its unique ID."""

    history = load_history()

    for record in history:
        if record.get("investigation_id") == investigation_id:
            return record

    return None
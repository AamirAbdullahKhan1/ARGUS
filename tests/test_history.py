from argus.reporting import history
from argus.engine.investigation_state import InvestigationState


def test_save_and_load_investigation(tmp_path, monkeypatch):
    # Use a temporary JSON file for testing.
    test_file = tmp_path / "investigation_history.json"
    monkeypatch.setattr(history, "HISTORY_FILE", test_file)

    incident = {
        "incident_id": "INC-TEST-001",
        "event_type": "suspicious_login",
        "username": "test_user",
        "source_ip": "192.168.1.100"
    }

    state = InvestigationState(incident)
    state.complete(
        recommendation="escalate",
        reasoning="Suspicious activity detected."
    )

    history.save_investigation(state)

    saved_history = history.load_history()

    assert len(saved_history) == 1
    assert saved_history[0]["incident"]["incident_id"] == "INC-TEST-001"
    assert saved_history[0]["recommendation"] == "escalate"


def test_get_investigation(tmp_path, monkeypatch):
    test_file = tmp_path / "investigation_history.json"
    monkeypatch.setattr(history, "HISTORY_FILE", test_file)

    incident = {
        "incident_id": "INC-TEST-002",
        "event_type": "suspicious_login"
    }

    state = InvestigationState(incident)
    state.complete("monitor", "Activity requires monitoring.")

    history.save_investigation(state)

    result = history.get_investigation(state.investigation_id)

    assert result is not None
    assert result["recommendation"] == "monitor"


def test_missing_history_file(tmp_path, monkeypatch):
    test_file = tmp_path / "investigation_history.json"
    monkeypatch.setattr(history, "HISTORY_FILE", test_file)

    assert history.load_history() == []
class MockDecisionProvider:
    """Deterministic decision provider for testing ARGUS."""

    def __init__(self):
        self.tool_sequences = {
            "suspicious_login": [
                "get_login_history",
                "check_ip_reputation",
                "get_account_details",
                "search_related_incidents"
            ],
            "unusual_login": [
                "get_login_history",
                "get_account_details",
                "check_ip_reputation",
                "search_related_incidents"
            ]
        }

    def select_tool(self, incident: dict, executed_tools: list) -> str | None:
        """Select the next tool based on the incident type."""

        incident_type = incident.get("event_type", "")

        sequence = self.tool_sequences.get(incident_type, [])

        for tool_name in sequence:
            if tool_name not in executed_tools:
                return tool_name

        return None
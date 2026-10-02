import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH, override=True)


class JevClient:
    """Handles communication with the Jev API."""

    def __init__(self):
        api_key = os.getenv("JEV_API_KEY")

        if not api_key:
            raise ValueError(
                "JEV_API_KEY is missing. "
                "Please configure it in your .env file."
            )

        self.api_key = api_key.strip()
        self.api_url = os.getenv(
            "JEV_API_URL",
            "https://jevtypesafeai.com/api/v1/decide",
        )
        self.model = os.getenv("JEV_MODEL", "jev-1.13.0")

    def generate(self, state: dict, questions: dict) -> dict:
        """Send a state and questions to Jev and return its JSON response."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "state": state,
            "questions": questions,
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"Jev API error {response.status_code}: {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Jev API returned a non-JSON response."
            ) from exc
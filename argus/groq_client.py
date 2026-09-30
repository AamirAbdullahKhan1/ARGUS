import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class GroqClient:
    """Handles communication with the Groq API."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
            "GROQ_API_KEY is missing. "
            "Please configure it in your .env file."
        )

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    def generate(self, messages: list[dict]) -> str:
        """Send messages to Groq and return the response."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return response.choices[0].message.content or ""
from argus.groq_client import GroqClient


client = GroqClient()

messages = [
    {
        "role": "system",
        "content": "You are ARGUS, a cybersecurity incident response assistant."
    },
    {
        "role": "user",
        "content": "Explain what a suspicious login incident is in one sentence."
    }
]

response = client.generate(messages)

print("\nARGUS GROQ RESPONSE")
print("-" * 40)
print(response)
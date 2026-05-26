import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

print("Webhook:", WEBHOOK_URL)

requests.post(
    WEBHOOK_URL,
    json={
        "content": "✅ テスト"
    }
)
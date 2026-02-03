#!/usr/bin/env python3
"""
Manual test script to simulate LINE webhook requests.

Usage:
    python scripts/test_webhook.py "你的測試訊息"
"""

import os
import sys
import hmac
import hashlib
import base64
import json
import httpx
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def create_signature(channel_secret: str, body: str) -> str:
    """Create LINE webhook signature."""
    hash_value = hmac.new(
        channel_secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_value).decode("utf-8")


def main():
    # Get test message from command line or use default
    test_message = sys.argv[1] if len(sys.argv) > 1 else "測試訊息：幫我想三個專案名稱"

    # Get environment variables
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    joey_user_id = os.getenv("JOEY_LINE_USER_ID", "U_test_user_id")
    server_url = os.getenv("TEST_SERVER_URL", "http://localhost:8000")

    if not channel_secret:
        print("Error: Missing LINE_CHANNEL_SECRET in .env")
        sys.exit(1)

    # Create webhook payload
    payload = {
        "destination": "test",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": test_message
                },
                "timestamp": int(datetime.now().timestamp() * 1000),
                "source": {
                    "type": "user",
                    "userId": joey_user_id
                },
                "replyToken": "test_reply_token_" + str(int(datetime.now().timestamp())),
                "mode": "active"
            }
        ]
    }

    body = json.dumps(payload)
    signature = create_signature(channel_secret, body)

    print(f"Testing webhook at {server_url}/webhook/line")
    print(f"Message: {test_message}")
    print("-" * 50)

    try:
        response = httpx.post(
            f"{server_url}/webhook/line",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": signature
            },
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("\n✅ Webhook accepted! Check Notion for results.")
        else:
            print("\n❌ Webhook failed")

    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to {server_url}")
        print("Make sure the server is running: uvicorn src.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

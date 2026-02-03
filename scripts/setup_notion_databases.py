#!/usr/bin/env python3
"""
Script to initialize Notion Memory database with default memories.
Run this once after setting up the Notion databases.

Usage:
    python scripts/setup_notion_databases.py
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from notion_client import Client


def main():
    # Get environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    memory_db_id = os.getenv("NOTION_MEMORY_DB_ID")

    if not notion_api_key or not memory_db_id:
        print("Error: Missing NOTION_API_KEY or NOTION_MEMORY_DB_ID in .env")
        sys.exit(1)

    client = Client(auth=notion_api_key)

    # Initial memories to create
    initial_memories = [
        {
            "title": "Joey 的基本資訊",
            "category": "context",
            "content": "Joey 經營來電司康營收成長顧問公司，服務餐廳、教育機構、電商、NGO 等客戶。偏好簡潔輸出，使用繁體中文，習慣用 Claude Code。",
            "importance": "high"
        },
        {
            "title": "輸出偏好",
            "category": "preference",
            "content": "不要過度格式化，不要太多符號，段落間適當換行，適合在 Line 或即時通訊軟體閱讀。",
            "importance": "high"
        }
    ]

    print("Creating initial memories...")

    for memory in initial_memories:
        try:
            # Check if memory already exists
            existing = client.databases.query(
                database_id=memory_db_id,
                filter={
                    "property": "Title",
                    "title": {"equals": memory["title"]}
                }
            )

            if existing["results"]:
                print(f"  ⏭️  '{memory['title']}' already exists, skipping")
                continue

            # Create memory
            client.pages.create(
                parent={"database_id": memory_db_id},
                properties={
                    "Title": {"title": [{"text": {"content": memory["title"]}}]},
                    "Category": {"select": {"name": memory["category"]}},
                    "Content": {"rich_text": [{"text": {"content": memory["content"]}}]},
                    "Importance": {"select": {"name": memory["importance"]}},
                    "UpdatedAt": {"date": {"start": datetime.now().isoformat()}},
                }
            )
            print(f"  ✅ Created '{memory['title']}'")

        except Exception as e:
            print(f"  ❌ Error creating '{memory['title']}': {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()

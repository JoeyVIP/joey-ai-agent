#!/usr/bin/env python3
"""
Setup Evolution Database - Creates the Notion database for tracking agent evolution

This script creates the Evolution Database in your Notion workspace.
Run this once to set up the database, then add the database ID to your .env file.

Usage:
    python setup_evolution_database.py --parent-page-id <page_id>

The parent page ID is the Notion page where you want to create the database.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion_client import Client
from src.config import settings


def create_evolution_database(client: Client, parent_page_id: str) -> str:
    """Create the Evolution Database in Notion."""

    response = client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Agent Evolution History"}}],
        properties={
            # Basic info
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "pending", "color": "gray"},
                        {"name": "executing", "color": "blue"},
                        {"name": "verifying", "color": "yellow"},
                        {"name": "completed", "color": "green"},
                        {"name": "failed", "color": "red"},
                        {"name": "rolled_back", "color": "orange"},
                    ]
                }
            },
            "Type": {
                "select": {
                    "options": [
                        {"name": "prompt", "color": "purple"},
                        {"name": "code", "color": "blue"},
                        {"name": "frontend", "color": "green"},
                        {"name": "config", "color": "red"},
                    ]
                }
            },
            "Level": {
                "select": {
                    "options": [
                        {"name": "Level 0", "color": "red"},
                        {"name": "Level 1", "color": "orange"},
                        {"name": "Level 2", "color": "yellow"},
                        {"name": "Level 3", "color": "green"},
                    ]
                }
            },

            # Description fields
            "Description": {"rich_text": {}},
            "FilesModified": {"rich_text": {}},
            "VerificationSteps": {"rich_text": {}},

            # Time tracking
            "CreatedAt": {"date": {}},
            "StartedAt": {"date": {}},
            "CompletedAt": {"date": {}},
            "Duration": {"number": {"format": "number"}},

            # Git info
            "GitTagPre": {"rich_text": {}},
            "GitTagPost": {"rich_text": {}},
            "GitCommitHash": {"rich_text": {}},

            # Results
            "VerificationResult": {"rich_text": {}},
            "ErrorMessage": {"rich_text": {}},
            "RollbackReason": {"rich_text": {}},
            "AgentOutput": {"rich_text": {}},
        }
    )

    return response["id"]


def main():
    parser = argparse.ArgumentParser(description="Setup Evolution Database in Notion")
    parser.add_argument("--parent-page-id", required=True, help="Notion page ID where database will be created")

    args = parser.parse_args()

    client = Client(auth=settings.notion_api_key)

    print("Creating Evolution Database...")
    db_id = create_evolution_database(client, args.parent_page_id)

    print(f"\nSuccess! Evolution Database created.")
    print(f"\nDatabase ID: {db_id}")
    print(f"\nAdd this to your .env file:")
    print(f"NOTION_EVOLUTION_DB_ID={db_id}")


if __name__ == "__main__":
    main()

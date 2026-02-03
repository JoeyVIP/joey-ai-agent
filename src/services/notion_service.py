from datetime import datetime
from typing import Optional
from notion_client import Client

from src.config import settings


class NotionService:
    def __init__(self):
        self.client = Client(auth=settings.notion_api_key)
        self.inbox_db_id = settings.notion_inbox_db_id
        self.review_db_id = settings.notion_review_db_id
        self.memory_db_id = settings.notion_memory_db_id

    # ==================== Inbox CRUD ====================

    async def create_inbox_task(
        self,
        title: str,
        raw_input: str,
        source: str = "line"
    ) -> str:
        """Create a new task in Inbox database. Returns the page ID."""
        response = self.client.pages.create(
            parent={"database_id": self.inbox_db_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": "received"}},
                "Source": {"select": {"name": source}},
                "RawInput": {"rich_text": [{"text": {"content": raw_input[:2000]}}]},
                "ReceivedAt": {"date": {"start": datetime.now().isoformat()}},
            }
        )
        return response["id"]

    async def update_inbox_status(self, page_id: str, status: str) -> None:
        """Update the status of an Inbox task."""
        self.client.pages.update(
            page_id=page_id,
            properties={
                "Status": {"select": {"name": status}}
            }
        )

    async def delete_inbox_task(self, page_id: str) -> None:
        """Archive (delete) an Inbox task."""
        self.client.pages.update(
            page_id=page_id,
            archived=True
        )

    # ==================== Review CRUD ====================

    async def create_review_task_simple(
        self,
        title: str,
        summary: str,
        result: str,
        source_task_id: str
    ) -> str:
        """Create a simple review task with direct result."""
        response = self.client.pages.create(
            parent={"database_id": self.review_db_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Difficulty": {"select": {"name": "simple"}},
                "Status": {"select": {"name": "pending_review"}},
                "Summary": {"rich_text": [{"text": {"content": summary[:2000]}}]},
                "Result": {"rich_text": [{"text": {"content": result[:2000]}}]},
                "ProcessedAt": {"date": {"start": datetime.now().isoformat()}},
                "SourceTaskId": {"rich_text": [{"text": {"content": source_task_id}}]},
            }
        )
        return response["id"]

    async def create_review_task_complex(
        self,
        title: str,
        summary: str,
        analysis: str,
        preparation: str,
        prompt_for_claude_code: str,
        estimated_time: str,
        reason: str,
        source_task_id: str
    ) -> str:
        """Create a complex review task with analysis and prompt for Claude Code."""
        response = self.client.pages.create(
            parent={"database_id": self.review_db_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Difficulty": {"select": {"name": "complex"}},
                "Status": {"select": {"name": "pending_review"}},
                "Summary": {"rich_text": [{"text": {"content": summary[:2000]}}]},
                "Analysis": {"rich_text": [{"text": {"content": analysis[:2000]}}]},
                "Preparation": {"rich_text": [{"text": {"content": preparation[:2000]}}]},
                "PromptForClaudeCode": {"rich_text": [{"text": {"content": prompt_for_claude_code[:2000]}}]},
                "EstimatedTime": {"rich_text": [{"text": {"content": estimated_time}}]},
                "Reason": {"rich_text": [{"text": {"content": reason[:2000]}}]},
                "ProcessedAt": {"date": {"start": datetime.now().isoformat()}},
                "SourceTaskId": {"rich_text": [{"text": {"content": source_task_id}}]},
            }
        )
        return response["id"]

    async def update_review_task_status(self, page_id: str, status: str) -> None:
        """Update the status of a Review task."""
        self.client.pages.update(
            page_id=page_id,
            properties={
                "Status": {"select": {"name": status}}
            }
        )

    async def update_review_task_result(
        self,
        page_id: str,
        status: str,
        result: str,
        folder_path: Optional[str] = None
    ) -> None:
        """Update a Review task with execution result."""
        properties = {
            "Status": {"select": {"name": status}},
            "Result": {"rich_text": [{"text": {"content": result[:2000]}}]},
            "CompletedAt": {"date": {"start": datetime.now().isoformat()}}
        }

        if folder_path:
            properties["Folder"] = {"rich_text": [{"text": {"content": folder_path}}]}

        self.client.pages.update(page_id=page_id, properties=properties)

    # ==================== Memory CRUD ====================

    async def get_all_memories(self) -> list[dict]:
        """Fetch all memories from the Memory database."""
        response = self.client.databases.query(
            database_id=self.memory_db_id,
            sorts=[
                {"property": "Importance", "direction": "ascending"},
                {"property": "UpdatedAt", "direction": "descending"}
            ]
        )

        memories = []
        for page in response["results"]:
            props = page["properties"]

            title = ""
            if props.get("Name", {}).get("title"):
                title = props["Name"]["title"][0]["plain_text"]

            category = ""
            if props.get("Category", {}).get("select"):
                category = props["Category"]["select"]["name"]

            content = ""
            if props.get("Content", {}).get("rich_text"):
                content = props["Content"]["rich_text"][0]["plain_text"]

            importance = "medium"
            if props.get("Importance", {}).get("select"):
                importance = props["Importance"]["select"]["name"]

            memories.append({
                "id": page["id"],
                "title": title,
                "category": category,
                "content": content,
                "importance": importance
            })

        return memories

    async def format_memories_for_prompt(self) -> str:
        """Format memories as a string for Claude prompt."""
        memories = await self.get_all_memories()

        if not memories:
            return "目前沒有儲存的記憶。"

        formatted = []
        for mem in memories:
            formatted.append(
                f"【{mem['title']}】({mem['category']}, {mem['importance']})\n{mem['content']}"
            )

        return "\n\n".join(formatted)

    async def update_memory(
        self,
        page_id: str,
        content: Optional[str] = None,
        importance: Optional[str] = None
    ) -> None:
        """Update an existing memory."""
        properties = {
            "UpdatedAt": {"date": {"start": datetime.now().isoformat()}}
        }

        if content is not None:
            properties["Content"] = {"rich_text": [{"text": {"content": content[:2000]}}]}

        if importance is not None:
            properties["Importance"] = {"select": {"name": importance}}

        self.client.pages.update(page_id=page_id, properties=properties)

    async def create_memory(
        self,
        title: str,
        category: str,
        content: str,
        importance: str = "medium"
    ) -> str:
        """Create a new memory entry."""
        response = self.client.pages.create(
            parent={"database_id": self.memory_db_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Category": {"select": {"name": category}},
                "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
                "Importance": {"select": {"name": importance}},
                "UpdatedAt": {"date": {"start": datetime.now().isoformat()}},
            }
        )
        return response["id"]

    async def find_memory_by_title(self, title: str) -> Optional[dict]:
        """Find a memory by title."""
        response = self.client.databases.query(
            database_id=self.memory_db_id,
            filter={
                "property": "Name",
                "title": {"equals": title}
            }
        )

        if response["results"]:
            page = response["results"][0]
            props = page["properties"]
            return {
                "id": page["id"],
                "title": props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "",
                "category": props["Category"]["select"]["name"] if props["Category"]["select"] else "",
                "content": props["Content"]["rich_text"][0]["plain_text"] if props["Content"]["rich_text"] else "",
                "importance": props["Importance"]["select"]["name"] if props["Importance"]["select"] else "medium"
            }
        return None


notion_service = NotionService()

from datetime import datetime
from typing import Optional
from notion_client import Client

from src.config import settings
from src.constants import NOTION_MAX_TEXT_LENGTH


class NotionService:
    def __init__(self):
        self.client = Client(auth=settings.notion_api_key)
        self.inbox_db_id = settings.notion_inbox_db_id
        self.review_db_id = settings.notion_review_db_id
        self.memory_db_id = settings.notion_memory_db_id
        self.evolution_db_id = settings.notion_evolution_db_id

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
                "RawInput": {"rich_text": [{"text": {"content": raw_input[:NOTION_MAX_TEXT_LENGTH]}}]},
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
                "Summary": {"rich_text": [{"text": {"content": summary[:NOTION_MAX_TEXT_LENGTH]}}]},
                "Result": {"rich_text": [{"text": {"content": result[:NOTION_MAX_TEXT_LENGTH]}}]},
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
                "Summary": {"rich_text": [{"text": {"content": summary[:NOTION_MAX_TEXT_LENGTH]}}]},
                "Analysis": {"rich_text": [{"text": {"content": analysis[:NOTION_MAX_TEXT_LENGTH]}}]},
                "Preparation": {"rich_text": [{"text": {"content": preparation[:NOTION_MAX_TEXT_LENGTH]}}]},
                "PromptForClaudeCode": {"rich_text": [{"text": {"content": prompt_for_claude_code[:NOTION_MAX_TEXT_LENGTH]}}]},
                "EstimatedTime": {"rich_text": [{"text": {"content": estimated_time}}]},
                "Reason": {"rich_text": [{"text": {"content": reason[:NOTION_MAX_TEXT_LENGTH]}}]},
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
            "Result": {"rich_text": [{"text": {"content": result[:NOTION_MAX_TEXT_LENGTH]}}]},
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
            properties["Content"] = {"rich_text": [{"text": {"content": content[:NOTION_MAX_TEXT_LENGTH]}}]}

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
                "Content": {"rich_text": [{"text": {"content": content[:NOTION_MAX_TEXT_LENGTH]}}]},
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

    # ==================== Evolution CRUD ====================

    async def create_evolution_task(
        self,
        title: str,
        task_type: str,
        level: str,
        description: str,
        files_modified: str,
        verification_steps: str
    ) -> str:
        """Create a new evolution task in pending status. Returns the page ID."""
        if not self.evolution_db_id:
            raise ValueError("Evolution database ID not configured")

        response = self.client.pages.create(
            parent={"database_id": self.evolution_db_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": "pending"}},
                "Type": {"select": {"name": task_type}},
                "Level": {"select": {"name": level}},
                "Description": {"rich_text": [{"text": {"content": description[:NOTION_MAX_TEXT_LENGTH]}}]},
                "FilesModified": {"rich_text": [{"text": {"content": files_modified[:NOTION_MAX_TEXT_LENGTH]}}]},
                "VerificationSteps": {"rich_text": [{"text": {"content": verification_steps[:NOTION_MAX_TEXT_LENGTH]}}]},
                "CreatedAt": {"date": {"start": datetime.now().isoformat()}},
            }
        )
        return response["id"]

    async def get_pending_evolution_tasks(self) -> list[dict]:
        """Fetch all pending evolution tasks."""
        if not self.evolution_db_id:
            return []

        response = self.client.databases.query(
            database_id=self.evolution_db_id,
            filter={
                "property": "Status",
                "select": {"equals": "pending"}
            },
            sorts=[
                {"property": "CreatedAt", "direction": "ascending"}
            ]
        )

        tasks = []
        for page in response["results"]:
            tasks.append(self._parse_evolution_task(page))
        return tasks

    async def get_evolution_task(self, page_id: str) -> Optional[dict]:
        """Fetch a specific evolution task by ID."""
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            return self._parse_evolution_task(page)
        except Exception:
            return None

    def _parse_evolution_task(self, page: dict) -> dict:
        """Parse a Notion page into an evolution task dict."""
        props = page["properties"]

        def get_text(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            if prop.get("rich_text"):
                return prop["rich_text"][0]["plain_text"] if prop["rich_text"] else ""
            if prop.get("title"):
                return prop["title"][0]["plain_text"] if prop["title"] else ""
            return ""

        def get_select(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            if prop.get("select"):
                return prop["select"]["name"]
            return ""

        def get_date(prop_name: str) -> Optional[str]:
            prop = props.get(prop_name, {})
            if prop.get("date") and prop["date"].get("start"):
                return prop["date"]["start"]
            return None

        def get_number(prop_name: str) -> Optional[int]:
            prop = props.get(prop_name, {})
            if prop.get("number") is not None:
                return prop["number"]
            return None

        return {
            "id": page["id"],
            "title": get_text("Name"),
            "status": get_select("Status"),
            "type": get_select("Type"),
            "level": get_select("Level"),
            "description": get_text("Description"),
            "files_modified": get_text("FilesModified"),
            "verification_steps": get_text("VerificationSteps"),
            "created_at": get_date("CreatedAt"),
            "started_at": get_date("StartedAt"),
            "completed_at": get_date("CompletedAt"),
            "duration": get_number("Duration"),
            "git_tag_pre": get_text("GitTagPre"),
            "git_tag_post": get_text("GitTagPost"),
            "git_commit_hash": get_text("GitCommitHash"),
            "verification_result": get_text("VerificationResult"),
            "error_message": get_text("ErrorMessage"),
            "rollback_reason": get_text("RollbackReason"),
            "agent_output": get_text("AgentOutput"),
        }

    async def update_evolution_task_status(
        self,
        page_id: str,
        status: str,
        **kwargs
    ) -> None:
        """Update evolution task status and optional fields."""
        properties = {
            "Status": {"select": {"name": status}}
        }

        # Handle time tracking
        if status == "executing":
            properties["StartedAt"] = {"date": {"start": datetime.now().isoformat()}}
        elif status in ("completed", "failed", "rolled_back"):
            properties["CompletedAt"] = {"date": {"start": datetime.now().isoformat()}}

        # Handle optional fields
        field_mappings = {
            "git_tag_pre": "GitTagPre",
            "git_tag_post": "GitTagPost",
            "git_commit_hash": "GitCommitHash",
            "verification_result": "VerificationResult",
            "error_message": "ErrorMessage",
            "rollback_reason": "RollbackReason",
            "agent_output": "AgentOutput",
        }

        for kwarg, prop_name in field_mappings.items():
            if kwarg in kwargs and kwargs[kwarg] is not None:
                value = str(kwargs[kwarg])[:NOTION_MAX_TEXT_LENGTH]
                properties[prop_name] = {"rich_text": [{"text": {"content": value}}]}

        if "duration" in kwargs and kwargs["duration"] is not None:
            properties["Duration"] = {"number": kwargs["duration"]}

        self.client.pages.update(page_id=page_id, properties=properties)

    async def get_evolution_history(self, limit: int = 20) -> list[dict]:
        """Fetch recent evolution history."""
        if not self.evolution_db_id:
            return []

        response = self.client.databases.query(
            database_id=self.evolution_db_id,
            sorts=[
                {"property": "CreatedAt", "direction": "descending"}
            ],
            page_size=limit
        )

        return [self._parse_evolution_task(page) for page in response["results"]]


notion_service = NotionService()

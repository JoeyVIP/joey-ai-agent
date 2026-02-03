from datetime import datetime
from typing import Optional
from notion_client import Client

from src.config import settings
from src.constants import NOTION_MAX_TEXT_LENGTH


class NotionService:
    """Notion 資料庫操作服務"""

    def __init__(self):
        self.client = Client(auth=settings.notion_api_key)
        self.inbox_db_id = settings.notion_inbox_db_id
        self.review_db_id = settings.notion_review_db_id
        self.memory_db_id = settings.notion_memory_db_id
        self.evolution_db_id = settings.notion_evolution_db_id

    # ==================== Property 建構輔助方法 ====================

    @staticmethod
    def _build_title(value: str) -> dict:
        """建構 Notion title 屬性"""
        return {"title": [{"text": {"content": value}}]}

    @staticmethod
    def _build_rich_text(value: str, truncate: bool = True) -> dict:
        """建構 Notion rich_text 屬性"""
        text = value[:NOTION_MAX_TEXT_LENGTH] if truncate else value
        return {"rich_text": [{"text": {"content": text}}]}

    @staticmethod
    def _build_select(value: str) -> dict:
        """建構 Notion select 屬性"""
        return {"select": {"name": value}}

    @staticmethod
    def _build_date(value: Optional[datetime] = None) -> dict:
        """建構 Notion date 屬性，預設為現在時間"""
        dt = value or datetime.now()
        return {"date": {"start": dt.isoformat()}}

    @staticmethod
    def _build_number(value: int) -> dict:
        """建構 Notion number 屬性"""
        return {"number": value}

    # ==================== Property 解析輔助方法 ====================

    @staticmethod
    def _parse_title(props: dict, prop_name: str, default: str = "") -> str:
        """解析 Notion title 屬性"""
        prop = props.get(prop_name, {})
        if prop.get("title") and len(prop["title"]) > 0:
            return prop["title"][0]["plain_text"]
        return default

    @staticmethod
    def _parse_rich_text(props: dict, prop_name: str, default: str = "") -> str:
        """解析 Notion rich_text 屬性"""
        prop = props.get(prop_name, {})
        if prop.get("rich_text") and len(prop["rich_text"]) > 0:
            return prop["rich_text"][0]["plain_text"]
        return default

    @staticmethod
    def _parse_select(props: dict, prop_name: str, default: str = "") -> str:
        """解析 Notion select 屬性"""
        prop = props.get(prop_name, {})
        if prop.get("select"):
            return prop["select"]["name"]
        return default

    @staticmethod
    def _parse_date(props: dict, prop_name: str) -> Optional[str]:
        """解析 Notion date 屬性"""
        prop = props.get(prop_name, {})
        if prop.get("date") and prop["date"].get("start"):
            return prop["date"]["start"]
        return None

    @staticmethod
    def _parse_number(props: dict, prop_name: str) -> Optional[int]:
        """解析 Notion number 屬性"""
        prop = props.get(prop_name, {})
        if prop.get("number") is not None:
            return prop["number"]
        return None

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
                "Name": self._build_title(title),
                "Status": self._build_select("received"),
                "Source": self._build_select(source),
                "RawInput": self._build_rich_text(raw_input),
                "ReceivedAt": self._build_date(),
            }
        )
        return response["id"]

    async def update_inbox_status(self, page_id: str, status: str) -> None:
        """Update the status of an Inbox task."""
        self.client.pages.update(
            page_id=page_id,
            properties={"Status": self._build_select(status)}
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
                "Name": self._build_title(title),
                "Difficulty": self._build_select("simple"),
                "Status": self._build_select("pending_review"),
                "Summary": self._build_rich_text(summary),
                "Result": self._build_rich_text(result),
                "ProcessedAt": self._build_date(),
                "SourceTaskId": self._build_rich_text(source_task_id, truncate=False),
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
                "Name": self._build_title(title),
                "Difficulty": self._build_select("complex"),
                "Status": self._build_select("pending_review"),
                "Summary": self._build_rich_text(summary),
                "Analysis": self._build_rich_text(analysis),
                "Preparation": self._build_rich_text(preparation),
                "PromptForClaudeCode": self._build_rich_text(prompt_for_claude_code),
                "EstimatedTime": self._build_rich_text(estimated_time, truncate=False),
                "Reason": self._build_rich_text(reason),
                "ProcessedAt": self._build_date(),
                "SourceTaskId": self._build_rich_text(source_task_id, truncate=False),
            }
        )
        return response["id"]

    async def update_review_task_status(self, page_id: str, status: str) -> None:
        """Update the status of a Review task."""
        self.client.pages.update(
            page_id=page_id,
            properties={"Status": self._build_select(status)}
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
            "Status": self._build_select(status),
            "Result": self._build_rich_text(result),
            "CompletedAt": self._build_date(),
        }

        if folder_path:
            properties["Folder"] = self._build_rich_text(folder_path, truncate=False)

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
            memories.append({
                "id": page["id"],
                "title": self._parse_title(props, "Name"),
                "category": self._parse_select(props, "Category"),
                "content": self._parse_rich_text(props, "Content"),
                "importance": self._parse_select(props, "Importance", default="medium"),
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
        properties = {"UpdatedAt": self._build_date()}

        if content is not None:
            properties["Content"] = self._build_rich_text(content)

        if importance is not None:
            properties["Importance"] = self._build_select(importance)

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
                "Name": self._build_title(title),
                "Category": self._build_select(category),
                "Content": self._build_rich_text(content),
                "Importance": self._build_select(importance),
                "UpdatedAt": self._build_date(),
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
                "title": self._parse_title(props, "Name"),
                "category": self._parse_select(props, "Category"),
                "content": self._parse_rich_text(props, "Content"),
                "importance": self._parse_select(props, "Importance", default="medium"),
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
                "Name": self._build_title(title),
                "Status": self._build_select("pending"),
                "Type": self._build_select(task_type),
                "Level": self._build_select(level),
                "Description": self._build_rich_text(description),
                "FilesModified": self._build_rich_text(files_modified),
                "VerificationSteps": self._build_rich_text(verification_steps),
                "CreatedAt": self._build_date(),
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

        # 輔助函數：解析 title 或 rich_text（兩者都可能包含文字）
        def get_text(prop_name: str) -> str:
            text = self._parse_title(props, prop_name)
            if not text:
                text = self._parse_rich_text(props, prop_name)
            return text

        return {
            "id": page["id"],
            "title": get_text("Name"),
            "status": self._parse_select(props, "Status"),
            "type": self._parse_select(props, "Type"),
            "level": self._parse_select(props, "Level"),
            "description": get_text("Description"),
            "files_modified": get_text("FilesModified"),
            "verification_steps": get_text("VerificationSteps"),
            "created_at": self._parse_date(props, "CreatedAt"),
            "started_at": self._parse_date(props, "StartedAt"),
            "completed_at": self._parse_date(props, "CompletedAt"),
            "duration": self._parse_number(props, "Duration"),
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
        properties = {"Status": self._build_select(status)}

        # Handle time tracking
        if status == "executing":
            properties["StartedAt"] = self._build_date()
        elif status in ("completed", "failed", "rolled_back"):
            properties["CompletedAt"] = self._build_date()

        # Handle optional rich_text fields
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
                properties[prop_name] = self._build_rich_text(str(kwargs[kwarg]))

        if "duration" in kwargs and kwargs["duration"] is not None:
            properties["Duration"] = self._build_number(kwargs["duration"])

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

import logging
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Project, TaskLog, TaskStatus
from src.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)


class WebTaskProcessor:
    """處理 Web 專案任務的執行器"""

    def __init__(self, db: Session):
        self.db = db
        self.claude_service = ClaudeService()

    def _log(self, project_id: int, message: str, log_type: str = "info"):
        """新增任務日誌"""
        log = TaskLog(
            project_id=project_id,
            message=message,
            log_type=log_type
        )
        self.db.add(log)
        self.db.commit()
        logger.info(f"[Project {project_id}] {message}")

    def _update_project_status(self, project_id: int, status: TaskStatus, **kwargs):
        """更新專案狀態"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = status
            for key, value in kwargs.items():
                setattr(project, key, value)
            self.db.commit()

    async def process_task(self, project_id: int):
        """
        執行專案任務
        1. 標記為 RUNNING
        2. 呼叫 Claude API 執行任務
        3. 收集結果
        4. 標記為 COMPLETED/FAILED
        """
        try:
            # Load project
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.error(f"Project {project_id} not found")
                return

            # Mark as running
            self._update_project_status(
                project_id,
                TaskStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            self._log(project_id, f"開始執行任務: {project.name}", "info")

            # Process with Claude
            self._log(project_id, "正在呼叫 Claude API...", "info")

            # TODO: 實際整合 Claude Code Service
            # For now, simulate processing
            await asyncio.sleep(2)
            self._log(project_id, "正在分析需求...", "tool_use")

            await asyncio.sleep(3)
            self._log(project_id, "正在生成程式碼...", "tool_use")

            await asyncio.sleep(2)
            self._log(project_id, "正在執行測試...", "tool_use")

            # Simulate completion
            result_summary = f"成功完成任務: {project.name}\n\n執行結果已儲存。"

            self._update_project_status(
                project_id,
                TaskStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                result_summary=result_summary
            )
            self._log(project_id, "任務執行完成", "success")

        except Exception as e:
            logger.error(f"Task processing failed for project {project_id}: {str(e)}")
            self._update_project_status(
                project_id,
                TaskStatus.FAILED,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
            self._log(project_id, f"任務執行失敗: {str(e)}", "error")

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from src.database.models import TaskStatus


class UserResponse(BaseModel):
    id: int
    github_id: str
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    id: int
    project_id: int
    message: str
    log_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="專案名稱")
    description: Optional[str] = Field(None, description="專案描述")
    task_prompt: str = Field(..., min_length=1, description="任務提示詞")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None


class ProjectResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    status: TaskStatus
    task_prompt: str
    uploaded_files: Optional[str]
    result_summary: Optional[str]
    output_files: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    # Optional: include owner info
    owner: Optional[UserResponse] = None

    # Optional: include logs
    logs: Optional[List[TaskLogResponse]] = None

    class Config:
        from_attributes = True

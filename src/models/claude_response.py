from typing import Optional, Literal
from pydantic import BaseModel, Field


class MemoryUpdate(BaseModel):
    """Memory update instruction from Claude."""
    action: Literal["create", "update"]
    title: str
    category: Optional[str] = None
    content: str
    importance: Optional[str] = None


class SimpleTaskResult(BaseModel):
    """Result for simple tasks that can be completed directly."""
    summary: str = Field(..., description="Brief summary of what was done")
    result: str = Field(..., description="The actual result/answer")


class ComplexTaskResult(BaseModel):
    """Result for complex tasks that need Claude Code."""
    summary: str = Field(..., description="Brief summary of the task")
    analysis: str = Field(..., description="Analysis of the task requirements")
    preparation: str = Field(..., description="What needs to be prepared before execution")
    prompt_for_claude_code: str = Field(..., description="The prompt to use with Claude Code")
    estimated_time: str = Field(..., description="Estimated time to complete")
    reason: str = Field(..., description="Why this is classified as complex")


class ClaudeResponse(BaseModel):
    """Structured response from Claude API."""
    difficulty: Literal["simple", "complex"] = Field(
        ...,
        description="Task difficulty classification"
    )
    title: str = Field(..., description="Task title for Notion")

    # For simple tasks
    simple_result: Optional[SimpleTaskResult] = None

    # For complex tasks
    complex_result: Optional[ComplexTaskResult] = None

    # Memory updates (optional)
    memory_updates: list[MemoryUpdate] = Field(default_factory=list)

    # Message to send to Joey via LINE
    line_message: str = Field(..., description="Message to send via LINE")

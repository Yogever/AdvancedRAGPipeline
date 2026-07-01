from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SessionMode = Literal["query", "agent"]


class ErrorLog(BaseModel):
    error_type: str
    message: str
    raw: str | None = None


class ToolCallLog(BaseModel):
    iteration: int
    tool_name: str
    params: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_content: str | None = None
    result_sources: list[str] = Field(default_factory=list)
    error: ErrorLog | None = None


class MessageLog(BaseModel):
    message_number: int
    mode: SessionMode
    prompt: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answer: str | None = None
    sources: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    error: ErrorLog | None = None


class SessionLog(BaseModel):
    """OperationsDB record — one document per CLI Session, growing via incremental updates."""

    session_id: str
    name: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    message_count: int = 0
    messages: list[MessageLog] = Field(default_factory=list)

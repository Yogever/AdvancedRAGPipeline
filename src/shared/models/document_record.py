from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    PARTIAL = "partial"
    FAILED = "failed"


class DocumentRecord(BaseModel):
    """OperationsDB record — tracks indexing state per Document."""

    source_id: str
    content_hash: str
    status: DocumentStatus = DocumentStatus.PENDING
    chunks_indexed: int = 0
    last_indexed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

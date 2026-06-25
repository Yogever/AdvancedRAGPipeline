from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, computed_field


class VectorRecord(BaseModel):
    """Stage 3 — written to the VectorStore by an EmbeddingWorker."""

    embedding: list[float]
    content: str
    source_id: str
    source_type: str
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_id: str

    @computed_field
    @property
    def record_id(self) -> str:
        return f"{self.source_id}::{self.chunk_index}"

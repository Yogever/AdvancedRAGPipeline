from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field

from shared.models.chunk import Chunk


class EmbeddingJob(BaseModel):
    """Stage 2 — produced by the EmbeddingManager, dispatched to the Job Queue."""

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: int = 0
    chunk: Chunk

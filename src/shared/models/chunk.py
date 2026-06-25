from typing import Any
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Stage 1 — produced by an Adapter from a Document."""

    content: str
    source_id: str
    source_type: str
    chunk_index: int
    total_chunks: int
    metadata: dict[str, Any] = Field(default_factory=dict)

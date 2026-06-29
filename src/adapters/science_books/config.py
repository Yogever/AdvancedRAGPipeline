from pydantic import Field

from shared.config import PipelineConfig


class ScienceBookConfig(PipelineConfig):
    books_path: str = Field(validation_alias="SCIENCE_BOOKS_PATH")
    chunk_max_chars: int = Field(default=2000, validation_alias="SCIENCE_BOOKS_CHUNK_MAX_CHARS")
    chunk_overlap_chars: int = Field(default=200, validation_alias="SCIENCE_BOOKS_CHUNK_OVERLAP_CHARS")

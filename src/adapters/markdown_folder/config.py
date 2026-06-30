from pathlib import Path

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from shared.config import PipelineConfig

_ENV_FILE = Path(__file__).parents[3] / ".env"


class MarkdownFolderConfig(PipelineConfig):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    folder_path: str = Field(validation_alias="SCIENCE_BOOKS_OUTPUT_PATH")
    chunk_max_chars: int = Field(default=2000, validation_alias="MARKDOWN_FOLDER_CHUNK_MAX_CHARS")
    chunk_overlap_chars: int = Field(default=200, validation_alias="MARKDOWN_FOLDER_CHUNK_OVERLAP_CHARS")

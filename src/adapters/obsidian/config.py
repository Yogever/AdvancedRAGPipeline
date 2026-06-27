from pathlib import Path

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from shared.config import PipelineConfig

_ENV_FILE = Path(__file__).parents[3] / ".env"


class ObsidianConfig(PipelineConfig):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    vault_path: str = Field(validation_alias="VAULT_HOST_PATH")
    chunk_max_chars: int = Field(default=1000, validation_alias="OBSIDIAN_CHUNK_MAX_CHARS")
    chunk_overlap_chars: int = Field(default=100, validation_alias="OBSIDIAN_CHUNK_OVERLAP_CHARS")

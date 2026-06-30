from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parents[3] / ".env"


class ScienceBookConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    books_path: str = Field(validation_alias="SCIENCE_BOOKS_PATH")
    output_path: str = Field(validation_alias="SCIENCE_BOOKS_OUTPUT_PATH")

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parents[2] / ".env"


class PipelineConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "rag_pipeline"
    celery_broker_url: str = "redis://localhost:6379/0"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    ollama_base_url: str = "http://localhost:11434"
    embedding_model_id: str = "nomic-embed-text"
    groq_api_key: str = ""
    groq_model_id: str = "llama-3.1-8b-instant"
    qdrant_collection_name: str = "embeddings"

from shared.config import PipelineConfig


class EmbeddingWorkerConfig(PipelineConfig):
    ollama_base_url: str = "http://localhost:11434"
    embedding_model_id: str = "nomic-embed-text"

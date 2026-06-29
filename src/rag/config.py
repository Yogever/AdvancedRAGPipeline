from shared.config import PipelineConfig


class RAGServiceConfig(PipelineConfig):
    top_k: int = 5

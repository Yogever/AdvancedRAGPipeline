from shared.logging_config import configure_logging
import embedding_worker.tasks as _tasks
from embedding_worker.tasks import celery_app

configure_logging()


class _MockEmbeddings:
    """Fixed-vector stub — replace with a real LangChain Embeddings implementation."""

    DIM = 384

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * self.DIM


_tasks._embedding_client = _MockEmbeddings()

celery_app.worker_main(argv=["worker", "-Q", "embed", "--loglevel=INFO"])

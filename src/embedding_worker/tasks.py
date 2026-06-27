import logging

from celery import Celery
from celery.signals import worker_process_init
from langchain_core.embeddings import Embeddings
from pymongo import MongoClient

from embedding_worker.config import EmbeddingWorkerConfig
from shared.models.embedding_job import EmbeddingJob
from shared.models.vector_record import VectorRecord
from shared.repositories.document_record_repository import DocumentRecordRepository
from shared.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_config = EmbeddingWorkerConfig()
celery_app = Celery(broker=_config.celery_broker_url)

_repo: DocumentRecordRepository | None = None
_vectorstore: VectorStore | None = None
_embedding_client: Embeddings | None = None


@worker_process_init.connect
def init_connections(**kwargs):
    global _repo, _vectorstore
    db = MongoClient(_config.mongodb_uri)[_config.mongodb_db_name]
    _repo = DocumentRecordRepository(db)
    _vectorstore = VectorStore(_config.qdrant_host, _config.qdrant_port)
    logger.info("Worker connections initialised")


@celery_app.task(name="embedding_worker.tasks.embed_chunk", bind=True, max_retries=3)
def embed_chunk(self, job_data: dict) -> None:
    job = EmbeddingJob(**job_data)
    chunk = job.chunk

    try:
        vector = _embedding_client.embed_query(chunk.content)

        record = VectorRecord(
            embedding=vector,
            content=chunk.content,
            source_id=chunk.source_id,
            source_type=chunk.source_type,
            chunk_index=chunk.chunk_index,
            metadata=chunk.metadata,
            model_id=_config.embedding_model_id,
        )
        _vectorstore.upsert(record)

        all_done = _repo.increment_and_check_complete(chunk.source_id, chunk.total_chunks)
        if all_done:
            _repo.mark_indexed(chunk.source_id)
            logger.info("Document fully indexed: %s", chunk.source_id)

    except Exception as exc:
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            _repo.mark_partial(chunk.source_id)
            logger.error(
                "Embedding failed after max retries for chunk %d of %s",
                chunk.chunk_index,
                chunk.source_id,
            )

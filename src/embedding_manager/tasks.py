import logging
from datetime import datetime, timezone

from celery import Celery
from celery.signals import worker_process_init
from pymongo import MongoClient

from embedding_manager.config import EmbeddingManagerConfig
from shared.models.chunk import Chunk
from shared.models.embedding_job import EmbeddingJob
from shared.repositories.document_record_repository import DocumentRecordRepository
from shared.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_config = EmbeddingManagerConfig()
celery_app = Celery(broker=_config.celery_broker_url)

_repo: DocumentRecordRepository | None = None
_vectorstore: VectorStore | None = None

_EMBED_TASK = "embedding_worker.tasks.embed_chunk"
_CLEAR_TASK = "embedding_manager.tasks.clear_source"


@worker_process_init.connect
def init_connections(**kwargs):
    global _repo, _vectorstore
    db = MongoClient(_config.mongodb_uri)[_config.mongodb_db_name]
    _repo = DocumentRecordRepository(db)
    _vectorstore = VectorStore(_config.qdrant_host, _config.qdrant_port, _config.qdrant_collection_name)
    logger.info("Worker connections initialised")


@celery_app.task(name="embedding_manager.tasks.clear_source")
def clear_source(source_id: str) -> None:
    if _vectorstore.has_records(source_id):
        _vectorstore.delete_by_source(source_id)
        logger.info("Cleared vectors for empty document: %s", source_id)
    _repo.mark_indexed(source_id)
    logger.info("Empty document marked as indexed: %s", source_id)


@celery_app.task(name="embedding_manager.tasks.ingest_chunk")
def ingest_chunk(chunk_data: dict) -> None:
    chunk = Chunk(**chunk_data)

    if _vectorstore.has_records(chunk.source_id):
        _vectorstore.delete_by_source(chunk.source_id)
        logger.info("Cleared stale records for re-index: %s", chunk.source_id)

    job = EmbeddingJob(chunk=chunk)
    celery_app.send_task(_EMBED_TASK, args=[job.model_dump(mode="json")], queue="embed")
    logger.info("Dispatched %s chunk %d/%d", chunk.source_id, chunk.chunk_index + 1, chunk.total_chunks)

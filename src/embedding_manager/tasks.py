import logging

from celery import Celery
from pymongo import MongoClient

from embedding_manager.config import EmbeddingManagerConfig
from shared.models.chunk import Chunk
from shared.models.embedding_job import EmbeddingJob
from shared.repositories.document_record_repository import DocumentRecordRepository
from shared.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_config = EmbeddingManagerConfig()
celery_app = Celery(broker=_config.celery_broker_url)

_db = MongoClient(_config.mongodb_uri)[_config.mongodb_db_name]
_repo = DocumentRecordRepository(_db)
_vectorstore = VectorStore(_config.chroma_host, _config.chroma_port)

_EMBED_TASK = "embedding_worker.tasks.embed_chunk"


@celery_app.task(name="embedding_manager.tasks.ingest_chunk")
def ingest_chunk(chunk_data: dict) -> None:
    chunk = Chunk(**chunk_data)

    if _vectorstore.has_records(chunk.source_id):
        _vectorstore.delete_by_source(chunk.source_id)
        logger.info("Cleared stale records for re-index: %s", chunk.source_id)

    job = EmbeddingJob(chunk=chunk)
    celery_app.send_task(_EMBED_TASK, args=[job.model_dump(mode="json")], queue="embed")
    logger.info("Dispatched %s chunk %d/%d", chunk.source_id, chunk.chunk_index + 1, chunk.total_chunks)

import hashlib
import logging
from abc import ABC, abstractmethod

from celery import Celery

from shared.models.chunk import Chunk
from shared.models.document_record import DocumentRecord, DocumentStatus
from shared.repositories.document_record_repository import DocumentRecordRepository

logger = logging.getLogger(__name__)

_INGEST_TASK = "embedding_manager.tasks.ingest_chunk"
_CLEAR_TASK = "embedding_manager.tasks.clear_source"


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


class BaseAdapter(ABC):
    def __init__(self, celery_app: Celery, record_repo: DocumentRecordRepository):
        self._celery = celery_app
        self._repo = record_repo

    def _process_document(self, content: str, source_id: str, metadata: dict) -> None:
        content_hash = _hash(content)
        record = self._repo.get(source_id)

        if record and record.content_hash == content_hash and record.status != DocumentStatus.PARTIAL:
            logger.debug("Unchanged, skipping: %s", source_id)
            return

        logger.info("Processing: %s", source_id)
        chunks = self._chunk(content, source_id, metadata)
        logger.info("Chunked into %d piece(s): %s", len(chunks), source_id)

        if not chunks:
            self._repo.save(DocumentRecord(
                source_id=source_id,
                content_hash=content_hash,
                status=DocumentStatus.INDEXING,
            ))
            self._celery.send_task(_CLEAR_TASK, args=[source_id], queue="ingest")
            logger.info("Empty document, dispatched clear: %s", source_id)
            return

        for chunk in chunks:
            self._celery.send_task(_INGEST_TASK, args=[chunk.model_dump(mode="json")], queue="ingest")

        logger.info("Dispatched %d chunk(s) to ingest queue: %s", len(chunks), source_id)

        self._repo.save(DocumentRecord(
            source_id=source_id,
            content_hash=content_hash,
            status=DocumentStatus.INDEXING,
        ))

    @abstractmethod
    def _chunk(self, content: str, source_id: str, metadata: dict) -> list[Chunk]: ...

    @abstractmethod
    def _discover_existing(self) -> None:
        """Process all documents that already exist in the source at startup.
        Called before live watching begins to handle cold starts and offline gaps."""
        ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.database import Database

from shared.models.document_record import DocumentRecord, DocumentStatus


class DocumentRecordRepository:
    COLLECTION = "document_records"

    def __init__(self, db: Database):
        self._col = db[self.COLLECTION]

    def get(self, source_id: str) -> DocumentRecord | None:
        doc = self._col.find_one({"source_id": source_id}, {"_id": 0})
        return DocumentRecord(**doc) if doc else None

    def save(self, record: DocumentRecord) -> None:
        self._col.replace_one(
            {"source_id": record.source_id},
            record.model_dump(mode="json"),
            upsert=True,
        )

    def increment_and_check_complete(self, source_id: str, total_chunks: int) -> bool:
        """Atomically increments chunks_indexed. Returns True if all chunks are now indexed."""
        result = self._col.find_one_and_update(
            {"source_id": source_id},
            {"$inc": {"chunks_indexed": 1}},
            return_document=ReturnDocument.AFTER,
        )
        return result is not None and result["chunks_indexed"] >= total_chunks

    def mark_indexed(self, source_id: str) -> None:
        self._col.update_one(
            {"source_id": source_id},
            {"$set": {
                "status": DocumentStatus.INDEXED,
                "last_indexed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

    def mark_partial(self, source_id: str) -> None:
        self._col.update_one(
            {"source_id": source_id},
            {"$set": {"status": DocumentStatus.PARTIAL}},
        )

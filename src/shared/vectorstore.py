import chromadb
from chromadb import Collection

from shared.models.vector_record import VectorRecord

_COLLECTION_NAME = "embeddings"


class VectorStore:
    def __init__(self, host: str, port: int):
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection: Collection = self._client.get_or_create_collection(_COLLECTION_NAME)

    def has_records(self, source_id: str) -> bool:
        result = self._collection.get(where={"source_id": source_id}, limit=1, include=[])
        return len(result["ids"]) > 0

    def delete_by_source(self, source_id: str) -> None:
        self._collection.delete(where={"source_id": source_id})

    def upsert(self, record: VectorRecord) -> None:
        self._collection.upsert(
            ids=[record.record_id],
            embeddings=[record.embedding],
            documents=[record.content],
            metadatas=[{
                "source_id": record.source_id,
                "source_type": record.source_type,
                "chunk_index": record.chunk_index,
                **record.metadata,
            }],
        )

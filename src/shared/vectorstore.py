from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from shared.models.vector_record import VectorRecord

_VECTOR_DIM = 768


class VectorStore:
    def __init__(self, host: str, port: int, collection_name: str):
        self._client = QdrantClient(host=host, port=port)
        self._collection_name = collection_name
        if not self._client.collection_exists(self._collection_name):
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=_VECTOR_DIM, distance=Distance.COSINE),
            )

    def has_records(self, source_id: str) -> bool:
        result = self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]),
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
        return len(result[0]) > 0

    def delete_by_source(self, source_id: str) -> None:
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=Filter(must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]),
        )

    def upsert(self, record: VectorRecord) -> None:
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=abs(hash(record.record_id)) % (2 ** 63),
                    vector=record.embedding,
                    payload={
                        "content": record.content,
                        "metadata": {
                            "record_id": record.record_id,
                            "source_id": record.source_id,
                            "source_type": record.source_type,
                            "chunk_index": record.chunk_index,
                            **record.metadata,
                        },
                    },
                )
            ],
        )

    def search(self, query: list):
        return self._client.query_points(
            collection_name=self._collection_name,
            query=query
        )
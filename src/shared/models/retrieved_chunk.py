from langchain_core.documents import Document
from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    content: str
    source_id: str
    source_type: str
    path: str
    chunk_index: int
    metadata: dict = {}

    @classmethod
    def from_document(cls, doc: Document) -> "RetrievedChunk":
        # langchain_qdrant puts the entire Qdrant payload (minus the content key)
        # into doc.metadata, so our nested "metadata" dict is one level down.
        inner = doc.metadata
        return cls(
            content=doc.page_content,
            source_id=inner.get("source_id", 'unknown')    ,
            source_type=inner.get("source_type", "unknown"),
            path=inner.get("path", ""),
            chunk_index=inner.get("chunk_index", 0),
            metadata=inner,
        )

    def format_for_prompt(self) -> str:
        vault_name = self.metadata.get("vault_name", "")
        location = f"{vault_name} — {self.source_id}" if vault_name else self.source_id
        header = f"[{self.source_type.upper()} — {location}, chunk {self.chunk_index}]"
        return f"{header}\n{self.content}"

# ADR 0005 — Split read/write abstraction for the VectorStore

**Status:** Accepted

## Context

The pipeline has two distinct access patterns against Qdrant:

- **Write path** (EmbeddingWorker, EmbeddingManager) — upsert vectors, delete by source, check existence. Implemented via a custom `VectorStore` wrapper around the raw `qdrant-client`.
- **Read path** (RAGService) — embed a query at runtime and perform similarity search to retrieve relevant chunks.

Two options were considered for the read path:

1. **Extend the custom `VectorStore`** — add a `search(query_text)` method that calls `OllamaEmbeddings` internally, returns `Document` objects.
2. **Use `langchain-qdrant`'s `QdrantVectorStore`** for the read path — it speaks directly to the existing Qdrant collection, handles query-time embedding natively, and returns LangChain `Document` objects that compose directly into a `RunnableSequence`.

## Decision

Use **`langchain-qdrant`** for the read path. Keep the custom `VectorStore` for the write path unchanged.

## Reasons

- `QdrantVectorStore.as_retriever()` returns a LangChain `BaseRetriever`, which plugs directly into a `RunnableSequence` without any adapter code.
- It handles query-time embedding internally, removing boilerplate from the RAGService.
- The write path has no need for LangChain's `Document` abstraction — extending the custom `VectorStore` to return `Document` objects would be mixing concerns.
- Both paths point at the same Qdrant instance and collection; there is no data duplication.

## Consequences

- Two clients write/read Qdrant: `qdrant-client` (write) and `langchain-qdrant` (read). They share no state beyond the Qdrant server itself.
- The collection name is owned by `PipelineConfig` and passed to both sides — it is the single source of truth.
- A future migration could unify both paths under `langchain-qdrant` (tracked in `thoughts.md`), but this is not required while the write path is stable.

# ADR 0003 — Full re-index on Document change

**Status:** Accepted

## Context

Adapters are live-watch daemons that detect when a Document changes and trigger re-indexing. The question is whether to re-index only the changed Chunks (diff-based) or the entire Document.

A diff-based approach using deterministic IDs (`source_id + chunk_index`) breaks down because `chunk_index` is structural, not stable across Document versions. A Document reduced from 10 Chunks to 1 would leave 9 orphaned records in the VectorStore with no mechanism to identify and clean them up.

## Decision

When a Document changes, delete all VectorStore records with that `source_id` and re-index the entire Document from scratch.

The delete is performed by the **EmbeddingManager**, not the EmbeddingWorker. When the first Chunk of a changed Document arrives, the EmbeddingManager queries the VectorStore directly (`has_records(source_id)`), deletes any existing records, and only then dispatches EmbeddingJobs for the new Chunks.

The EmbeddingManager runs with Celery `concurrency=1`, which serialises ingest tasks so the delete-before-dispatch sequence is guaranteed without distributed locks or Celery chains. After the first Chunk triggers the delete, subsequent Chunks for the same Document find an empty VectorStore and are forwarded directly.

## Reasons

- Chunk structure is not stable across Document versions — chunk count and boundaries can change completely.
- A delete-then-reindex approach eliminates the orphan problem without requiring diff logic.
- Keeping the delete in the EmbeddingManager (rather than dispatching it as a worker task) avoids ordering dependencies between control tasks and embedding tasks on the worker queue.
- `concurrency=1` on the EmbeddingManager is acceptable because the Manager's work is lightweight (a VectorStore read, an optional delete, and a task dispatch) — the expensive work (embedding) happens on the workers.

## Consequences

- `source_id` must be stable across versions of the same Document (e.g. file path). Renaming a file is treated as a new Document — the old records become orphans unless handled explicitly (post-MVP).
- Re-indexing a changed Document always re-processes every Chunk, even unchanged ones. Acceptable at this scale.
- The EmbeddingManager holds read and delete access to the VectorStore. The EmbeddingWorker holds write-only access. VectorStore ownership is split by operation type, not by service boundary.
- Scaling the EmbeddingManager beyond `concurrency=1` would reintroduce a delete race condition and require revisiting this decision (distributed lock or Celery chain approach).

# ADR 0003 — Full re-index on Document change

**Status:** Accepted

## Context

Adapters are live-watch daemons that detect when a Document changes and trigger re-indexing. The question is whether to re-index only the changed Chunks (diff-based) or the entire Document.

A diff-based approach using deterministic IDs (`source_id + chunk_index`) breaks down because `chunk_index` is structural, not stable across Document versions. A Document reduced from 10 Chunks to 1 would leave 9 orphaned records in the VectorStore with no mechanism to identify and clean them up.

## Decision

When a Document changes, delete all VectorStore records with that `source_id` and re-index the entire Document from scratch.

## Reasons

- Chunk structure is not stable across Document versions — chunk count and boundaries can change completely.
- A delete-then-reindex approach eliminates the orphan problem without requiring diff logic.
- Keeps the Adapter and EmbeddingManager simple — no need to compare old and new chunk sets.

## Consequences

- `source_id` must be stable across versions of the same Document (e.g. file path). Renaming a file is treated as a new Document — the old records become orphans unless handled explicitly (post-MVP).
- Re-indexing a changed Document always re-processes every Chunk, even unchanged ones. Acceptable at this scale.
- The EmbeddingManager is responsible for issuing the delete before dispatching new EmbeddingJobs.

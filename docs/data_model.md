# Embedding DataModel

The shared representation of a Chunk as it moves through the pipeline. The model is enriched at each stage — each service adds its own fields without needing to know about fields owned by other stages.

---

## Stage 1 — Adapter Output

Produced by an Adapter from a Document. The thin, content-only version.

| Field | Type | Description |
|---|---|---|
| `content` | `str` | Raw text of the Chunk |
| `source_id` | `str` | Opaque, stable, unique identifier for the parent Document — defined by the Adapter. No prescribed format; each Adapter uses whatever constitutes a stable identity in its source system (e.g. file path for a folder Adapter, message ID for a Slack Adapter). Must not change across Document versions — used as the deletion key when re-indexing. Human-readable location info belongs in `metadata`. |
| `source_type` | `str` | Kind of source: `obsidian`, `pdf`, `code`, etc. |
| `chunk_index` | `int` | Zero-based position of this Chunk within its parent Document |
| `total_chunks` | `int` | Total number of Chunks the parent Document was split into |
| `metadata` | `dict` | Source-specific extras (e.g. PDF page number, Obsidian tags, code language) |

> `chunk_index` + `total_chunks` allow the EmbeddingManager to track Document completion without a separate pagination record.

### OperationsDB Document Record

The Adapter maintains a record per Document in the OperationsDB to support change detection and re-indexing.

| Field | Type | Description |
|---|---|---|
| `source_id` | `str` | Stable Document identifier |
| `content_hash` | `str` | Hash of the Document's raw content at last indexing. Compared on each watch cycle to detect changes. |
| `last_indexed_at` | `datetime` | When the Document was last fully indexed |
| `status` | `str` | `pending`, `indexing`, `indexed`, `failed` |

---

## Stage 2 — EmbeddingJob (EmbeddingManager output)

The EmbeddingManager wraps a Chunk in an EmbeddingJob before dispatching it to the Job Queue. The EmbeddingJob **contains** a Chunk — it does not extend it. Chunk fields and job fields are kept separate so orchestration metadata never leaks into the VectorStore.

| Field | Type | Description |
|---|---|---|
| `job_id` | `str` | Unique identifier for this job — used to track state in Celery and OperationsDB |
| `created_at` | `datetime` | Timestamp when the job was created |
| `priority` | `int` | Queue priority — allows certain sources to be processed first |
| `chunk` | `Chunk` | The Chunk produced by the Adapter (Stage 1) |

---

## Stage 3 — VectorStore Record (EmbeddingWorker output)

What the EmbeddingWorker writes to the VectorStore after embedding a Chunk. Contains the vector, the original content for prompt injection, and enough metadata for the RAGService to cite sources and the system to manage re-indexing.

| Field | Type | Description |
|---|---|---|
| `embedding` | `list[float]` | The vector produced by the embedding model |
| `content` | `str` | Original Chunk text — injected into the RAGService prompt as context |
| `source_id` | `str` | Which Document this came from — used as the deletion key on re-index and for grouping results in the Response |
| `source_type` | `str` | Source kind (`obsidian`, `pdf`, `code`) — used to format citations correctly |
| `chunk_index` | `int` | Position within the parent Document — allows results to be contextualised |
| `metadata` | `dict` | Passed through from the Chunk (PDF page, Obsidian tags, code language, etc.) |
| `embedded_at` | `datetime` | When this Chunk was last indexed |
| `model_id` | `str` | Which embedding model produced this vector — required to detect stale records if the model changes |

> **VectorStore record ID:** `{source_id}::{chunk_index}` — deterministic, human-readable, and directly traceable to the source without a lookup. Safe to use because the full re-index strategy always deletes existing records before inserting new ones (no collision risk).

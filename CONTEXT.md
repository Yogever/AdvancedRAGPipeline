# Domain Glossary

## Document
A source artifact as it exists in the source system — one Obsidian `.md` note, one `.pdf` file, one source code file. A Document is what an Adapter reads; it is never sent over the queue.

## Chunk
A content-type-aware fragment produced by an Adapter from a Document, sized appropriately for embedding. A Chunk is the unit that travels over the queue. A Chunk always belongs to exactly one Document.

## Chunking
The process of splitting a Document into Chunks. Chunking is performed by the Adapter — not the Manager — because the Adapter has knowledge of the content type and can apply the appropriate strategy (e.g. split by heading for Markdown, by page for PDF, by function for code).

## Embedding
The vector representation of a Chunk, produced by calling an embedding model. The artifact stored in the Vector DB. "Embed" (verb) = the act of producing an Embedding from a Chunk.

## Indexing
The act of storing an Embedding in the Vector DB. Distinct from embedding: an EmbeddingWorker first *embeds* a Chunk (produces the vector), then *indexes* it (writes it to the Vector DB).

## VectorStore
The component that stores Embeddings and supports similarity search over them. Backed by Chroma in the current implementation, wrapped behind an interface so swapping to Qdrant is a small change. Named independently from Chroma so the domain term stays stable if the implementation changes.

## OperationsDB
The internal MongoDB instance used for pipeline state that isn't job-queue-level tracking (which belongs to Celery/Redis). Stores: which Documents have been indexed, pagination state for large Documents mid-processing, and operational logs. Not exposed to the user — purely internal to the pipeline.

## Job Queue
The message broker that carries EmbeddingJobs from the EmbeddingManager to EmbeddingWorkers. Each EmbeddingJob is consumed by exactly one EmbeddingWorker (point-to-point, not pub/sub). Implemented with Redis as the broker and Celery as the task queue layer. Not called a "Message Bus" — there is no fanout or publish/subscribe pattern here.

## EmbeddingJob
The queue message dispatched by the EmbeddingManager and consumed by an EmbeddingWorker. Wraps a Chunk with job-level metadata: job ID, source Document reference, retry count, priority, and any other orchestration data. A Chunk is the content; an EmbeddingJob is the envelope that carries it through the pipeline.

## EmbeddingManager
The microservice that orchestrates the embedding pipeline. Responsible for tracking which Documents have been processed, managing pagination for large Documents, dispatching Chunks to the Queue, and monitoring job state. Does not embed anything itself — that is the EmbeddingWorker's job.

## EmbeddingWorker
The microservice that consumes Chunks from the Queue and embeds them by calling the embedding model. Indexing the resulting Embedding into the Vector DB is an implicit final step of the same job. Multiple EmbeddingWorker instances run in parallel to scale throughput. Named for its primary and most expensive responsibility: calling the embedding model.

## Query
A natural language question submitted by the user via the CLI. The input to the RAGService.

## Response
The natural language answer returned by the RAGService after retrieval and LLM generation. The output the CLI displays to the user.

## RAGService
The microservice that handles user queries end to end. Receives a natural language Query from the CLI, retrieves relevant Chunks from the Vector DB, injects them as context into a prompt, calls the LLM via the LLM Wrapper, and returns a natural language Response. Uses a Reranker post-MVP.

## LLMClient
A component that abstracts communication with a language model — sending a prompt and receiving a response. Backed by LangChain in the current implementation. The RAGService calls the LLMClient without knowing which LLM or framework is underneath. Named independently from LangChain so the domain term remains stable if the implementation changes.

## Reranker
_(Post-MVP)_ A sub-component of the RAGService. Takes the initial set of Chunks returned by the vector search and re-orders them by relevance before context injection. Not a separate microservice — lives inside the RAGService. Implementation is swappable (cross-encoder model, LLM-based, etc.).

## Adapter
A service that bridges a specific source system (Obsidian vault, local folder, etc.) into the pipeline. An Adapter watches its source for new or changed Documents, performs Chunking, and puts the resulting Chunks onto the Queue. Runs as a live-watch daemon. Uses content hashing to detect Document changes — not file modification timestamps, which are unreliable under sync tools and editors.

## Source ID
An opaque, stable, unique string that an Adapter assigns to a Document. No system-wide format is prescribed — each Adapter uses whatever constitutes a stable identity in its source system (file path, message ID, thread ID, URL, etc.). Used as the deletion key when re-indexing a changed Document. Must be unique within a source type and stable across Document versions. Human-readable location info belongs in the Chunk's `metadata`, not here.

## Content Hash
A hash of a Document's raw content, stored in the OperationsDB alongside the `source_id`. The Adapter compares the current hash against the stored hash to decide whether a Document needs re-indexing. A changed hash triggers a full re-index of the Document.

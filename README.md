# Advanced RAG Pipeline

A distributed, locally-run Retrieval-Augmented Generation (RAG) system that ingests data from multiple sources, embeds and indexes it, and lets you query your own knowledge base using natural language.

Built as a learning project and personal tool — designed to handle large files, multiple data sources, and continuous indexing without relying on high-level data-layer frameworks like LlamaIndex.

---

## Goal

Index large quantities of personal data (notes, PDFs, code) into a vector store and expose a CLI that answers natural language queries against that data.

---

## Architecture

The system is split into independent microservices communicating via a queue.

```
[Adapters] --> [Queue] --> [Embedding Workers]
                  |               |
           [Embedding Manager]  [Vector DB (Chroma)]
                  |
             [MongoDB]

[CLI] --> [RAG Service] --> [Vector DB + LLM (via LangChain)]
```

### Components

| Service | Responsibility |
|---|---|
| **Adapters** | Watch data sources for new/changed files, fill the Embedding DataModel, push to queue. Run as live-watch daemons. |
| **Queue** | Decouples adapters from workers; enables load balancing across multiple workers. |
| **Embedding Manager** | Orchestrates embedding jobs, handles pagination for large files, tracks which chunks have been indexed. |
| **Embedding Workers** | Consume jobs from the queue, call the embedding API, write vectors to the Vector DB. |
| **Vector DB** | Chroma for MVP. Wrapped behind an interface so swapping to Qdrant later is a small change. |
| **MongoDB** | Internal operations: job state, pagination tracking, logs. |
| **RAG Service** | Accepts user queries, retrieves relevant chunks from the vector store, injects context, calls the LLM, and returns a response. Includes re-ranking (post-MVP). |
| **LLM Wrapper** | LangChain — model abstraction, prompt templates, result parsing. Application-layer only. |
| **CLI** | User-facing interface for submitting queries and displaying results. |

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Vector DB | Chroma | Resource-efficient, free, simple local setup. Interface-wrapped for easy swap to Qdrant. |
| Metadata / Ops DB | MongoDB | Job tracking, pagination state, logs. |
| LLM Framework | LangChain | Application layer only — model wrappers, prompt templates, tool use. |
| Language | Python | — |

---

## MVP Scope

1. Obsidian adapter (live-watch daemon)
2. Local folder adapter for PDFs
3. Embedding Manager — pagination and job orchestration (no data recovery in MVP)
4. Embedding Worker
5. Basic RAG — no re-ranking
6. CLI

---

## Constraints

- Handles very large files via a pagination/chunking mechanism
- Continuous indexing — new files are automatically picked up
- Accurate code and keyword search
- Runs entirely on a local machine (resource-efficient)
- Free or free-tier dependencies only

---

## Project Status

Early development — architecture and data model design phase.

Current work:
- [ ] Embedding DataModel design
- [ ] Adapters (Obsidian + local PDF folder)
- [ ] EmbeddingWorker microservice
- [ ] EmbeddingManager microservice
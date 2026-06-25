# ADR 0001 — Chunking happens in the Adapter

**Status:** Accepted

## Context

Large Documents (PDFs, Obsidian vaults, code files) must be split into Chunks before embedding. The question is where in the pipeline that splitting should occur.

Two alternatives were considered:
1. **Adapter-side chunking** — each Adapter reads the Document, splits it, and puts Chunks on the queue.
2. **Manager-side chunking** — Adapters put whole Documents on the queue; the Manager splits them before dispatching to Workers.

## Decision

Chunking happens in the Adapter.

## Reasons

- The Adapter already knows the content type (it is a `PDFAdapter`, an `ObsidianAdapter`). That knowledge is required to chunk correctly — splitting by heading for Markdown, by page for PDF, by function for code.
- Whole Documents must not travel over the queue. Large files would make queue messages unbounded in size.
- Keeping the Manager free of file content makes it a pure orchestrator — it reasons about jobs and state, never about bytes.

## Consequences

- The queue contract is: **only Chunks travel over the queue, never Documents**.
- Each Adapter is responsible for implementing its own Chunking strategy.
- The Manager never processes raw file content.

# ADR 0004 — Fixed RAG chain, not an agent

**Status:** Accepted

## Context

The RAGService must answer natural language queries by drawing on indexed content from the VectorStore. Two retrieval architectures were considered:

1. **Fixed chain** — every query unconditionally follows: embed query → retrieve top-k chunks → inject as context → call LLM. The LLM never decides whether or how to retrieve.
2. **Agent with retrieval tool** — the LLM receives a retrieval tool and decides at runtime whether to call it, how many times, and with what query rewrite. The LLM is the orchestrator.

## Decision

Use a **fixed chain**.

## Reasons

- The application's sole purpose is to answer questions about indexed personal data. Retrieval is *always* the right action — there is no query type that should skip it.
- Giving the LLM tool-calling control adds latency (at minimum one extra LLM call to decide to retrieve), unpredictability (the model may choose not to retrieve when it should), and failure modes (tool misuse, loop risk) that add no value here.
- A fixed chain is transparent: every query takes the same path, which makes it easy to reason about, debug, and optimise.

## Consequences

- The RAGService always retrieves before generating. There is no "general knowledge" fallback — if the answer is not in the VectorStore, the model says so.
- Query rewriting and multi-hop retrieval (if needed) must be implemented explicitly in the chain, not delegated to the LLM.

## Addendum — `agent` subcommand (2026-06-29)

`AgentRAGService` was added in `src/rag/agent_service.py` and exposed via `python -m cli agent`. It uses `bind_tools` + a manual tool-calling loop (no `AgentExecutor` dependency) with a `search_notes` tool wrapping the same retriever. The fixed chain remains the default (`python -m cli query`); the agent mode is opt-in for queries that benefit from multi-hop retrieval.

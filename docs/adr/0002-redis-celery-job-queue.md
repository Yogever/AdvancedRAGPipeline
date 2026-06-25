# ADR 0002 — Redis + Celery as the Job Queue

**Status:** Accepted

## Context

EmbeddingJobs must travel from the EmbeddingManager to one of potentially many EmbeddingWorkers. The system needs a Job Queue that is resource-efficient (runs locally), free, and minimises the amount of orchestration logic the EmbeddingManager has to implement itself (retry, task state, failure handling).

Alternatives considered:
- **RabbitMQ** — robust and battle-tested, but heavier infra footprint and more operational overhead for a local setup.
- **Redis alone (raw list/stream)** — minimal, but requires hand-rolling retry logic, task state tracking, and worker management.
- **Redis + Celery** — Python-native task queue backed by Redis. Celery provides retry logic, task state, scheduling, and worker management out of the box.

## Decision

Use **Redis** as the broker and **Celery** as the task queue layer.

## Reasons

- Python-native — fits the project's language without adding a separate ecosystem.
- Celery handles retry logic and task state tracking, reducing what the EmbeddingManager needs to implement itself.
- Redis has a minimal local footprint and a free tier on managed services if needed later.
- Point-to-point semantics (each EmbeddingJob consumed by exactly one EmbeddingWorker) map cleanly onto Celery's task model.

## Consequences

- EmbeddingJobs are Celery tasks; the Job Queue is a Redis-backed Celery queue.
- Retry logic and job state are owned by Celery, not the EmbeddingManager.
- Switching brokers later (e.g. to RabbitMQ) is possible with minimal Celery config changes.

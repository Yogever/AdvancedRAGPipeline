#project/AdvancedRAGPipeline #Learning 
 Build a system to index large amounts of big files in a [[Vector DB]] to allow for queries on my data.
this will have to be distributed over multiple [[micro services]] due to the high embedding time.
#### Roadmap
1. write a [[Spec File]] detailing exactly what services will be provided and the use case.
2. desing a general architecture that would fit the bill
3. choose tech stack
4. implement mvp

## MVP
The mvp for this project should include:
1. an obsidian adapter
2. local folder adapter, at first for big PDF's
3. Embbeding manager - pagination and orchistration, no data recovery as of now
4. EmbeddingWorker - for embedding and indexing
5. Basic RAG - no [[Re-rank]] for MVP
6. CLI


## Tasks 2026-06-25
- [ ] Desing DataModel for embedding see [[Embedding DataModel]]
- [ ] Write adapters that collect data, fill the [[Embedding DataModel]] and send to a queue for the manager to read
- [ ] Write EmbeddingWorker [[micro services]] that lreads from a queue, embbeds and indexes
- [ ] Write EmbeddingManager micro services 



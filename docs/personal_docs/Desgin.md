#project/AdvancedRAGPipeline #BEEngineering/desing #micro_services

## Technical Requirements
desing answers to the constraints laid out in [[Spec File]].

1. For indexing very large files, a pagination mechanizem would be implemented. 
2. For performance, a manager-load balancer-worker architecture will be employed to the indexing-embedding part of the system
3. For indexing, a [[Vector DB]],which one is discussed here [[DB discussion]].
4. An extra NoSQL db will be deployed for managing logs, pagination etc..
5. LLM wrapper for communicating with external LLM (either local or Cloud)
6. For increased accuracy and exact results, a re-ranking machanizem for the results of the vector search.
7. For continouity, the adapters will be implemented as Live watch deamons

## Main Components
1. Adapters, for collecting data to be embbeded
2. queue - for load balancing
3. EmbeddingManager [[micro services|micro service]] for orchistrating embbeding tasks and keeping track of the data that was indexed
4. EmbeddingWorker [[micro services|micro service]] that listens on a queue and calls the embedding API to vectorize and index the data shards
5. [[Vector DB]] for storing the vectorized data see [[Vector DB discussion]]
6. [[MongoDB]] for interanl operation and logging
7. RAG microservice to inject context to user queries and perform [[Re-rank]]
8. LLM wrapper - see [[LLM Framework Discussion]]
9. User CLI - for reciving user search prompts and dsipalying results.

## Main Requriements:
1. Resource efficient, it will be ran on a local machine
2. Free / respectable free tier
3. easy to use, out of the box features

a Gemini comarison gave:

|**Database**|**Primary Model**|**Cost Profile**|**Speed & Latency**|**Standout Features**|**Best Use Case**|
|---|---|---|---|---|---|
|**Pinecone**|Managed Cloud Only|Premium (Scales with usage)|Fast, highly optimized (~20ms p99)|Serverless, native hybrid search, zero infra management|Teams without dedicated DevOps wanting fast time-to-market|
|**Qdrant**|Open Source / Cloud|Highly efficient (Low RAM footprint)|Blazing fast (Rust-backed, superior filtered latency)|Advanced "Payload Filtering", high memory efficiency|Performance-critical apps, complex metadata filtering|
|**Milvus / Zilliz**|Open Source / Cloud|Cost-effective at massive scale|High throughput for large batches|Distributed sharding, streaming integration (Kafka)|Billion-scale enterprise datasets, high ingestion workloads|
|**Weaviate**|Open Source / Cloud|Moderate|Fast, balanced|Built-in vectorization modules, Vector Fusion, GraphQL|Multi-tenant B2B SaaS, rich hybrid or multimodal search|
|**pgvector**|Open Source / Free|Lowest (Utilizes existing DB infra)|Excellent up to ~50M vectors|Keeps relational data and vectors side-by-side, ACID compliance|RAG systems where you already run and scale Postgres|
|**Chroma**|Open Source / Free|Zero (Runs locally/in-memory)|High local speed; degrades past ~1M vectors|Dead-simple "plug-and-play" Python API|AI prototyping, local research, small production MVPs|
According to this [[Chroma]] seems like the best option to **start** with. It can be wrraped and decoupled from the rest of the code so that changing it later (Maybe to [[Qdrant]]) will be O(1).
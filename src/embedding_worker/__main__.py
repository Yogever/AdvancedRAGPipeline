import logging

import embedding_worker.tasks as _tasks
from embedding_worker.tasks import celery_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# TODO: replace with a real LangChain Embeddings implementation, e.g.:
#   from langchain_openai import OpenAIEmbeddings
#   _tasks._embedding_client = OpenAIEmbeddings(model="text-embedding-3-small")
# or:
#   from langchain_community.embeddings import SentenceTransformerEmbeddings
#   _tasks._embedding_client = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
raise NotImplementedError(
    "Configure an EmbeddingClient in embedding_worker/__main__.py before starting the worker."
)

celery_app.worker_main(argv=["worker", "-Q", "embed", "--loglevel=INFO"])

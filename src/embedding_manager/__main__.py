import logging

from embedding_manager.tasks import celery_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

celery_app.worker_main(argv=["worker", "--concurrency=1", "-Q", "ingest", "--loglevel=INFO"])

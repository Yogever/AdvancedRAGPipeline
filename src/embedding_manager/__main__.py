from shared.logging_config import configure_logging
from embedding_manager.tasks import celery_app

configure_logging()

celery_app.worker_main(argv=["worker", "--concurrency=1", "-Q", "ingest", "--loglevel=INFO"])

from celery import Celery
from pymongo import MongoClient

from adapters.chunker import ChunkingConfig
from adapters.science_books.adapter import ScienceBookAdapter
from adapters.science_books.config import ScienceBookConfig
from shared.logging_config import configure_logging
from shared.repositories import DocumentRecordRepository

configure_logging()

config = ScienceBookConfig()

celery_app = Celery(broker=config.celery_broker_url)
db = MongoClient(config.mongodb_uri)[config.mongodb_db_name]
repo = DocumentRecordRepository(db)

adapter = ScienceBookAdapter(
    books_path=config.books_path,
    celery_app=celery_app,
    record_repo=repo,
    config=ChunkingConfig(
        chunk_size=config.chunk_max_chars,
        chunk_overlap=config.chunk_overlap_chars,
    ),
)

adapter.start()

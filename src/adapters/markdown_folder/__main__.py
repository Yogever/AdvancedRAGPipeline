from celery import Celery
from pymongo import MongoClient

from adapters.chunker import ChunkingConfig
from adapters.markdown_folder.adapter import MarkdownFolderAdapter
from adapters.markdown_folder.config import MarkdownFolderConfig
from adapters.runner import AdapterRunner
from shared.logging_config import configure_logging
from shared.repositories import DocumentRecordRepository

configure_logging()

config = MarkdownFolderConfig()

celery_app = Celery(broker=config.celery_broker_url)
db = MongoClient(config.mongodb_uri)[config.mongodb_db_name]
repo = DocumentRecordRepository(db)

adapter = MarkdownFolderAdapter(
    folder_path=config.folder_path,
    celery_app=celery_app,
    record_repo=repo,
    config=ChunkingConfig(
        chunk_size=config.chunk_max_chars,
        chunk_overlap=config.chunk_overlap_chars,
    ),
)

AdapterRunner(adapter).run()

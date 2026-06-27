import logging

from celery import Celery
from pymongo import MongoClient

from adapters.obsidian.adapter import ObsidianAdapter
from adapters.obsidian.chunker import ChunkingConfig
from adapters.obsidian.config import ObsidianConfig
from adapters.runner import AdapterRunner
from shared.repositories import DocumentRecordRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

config = ObsidianConfig()

celery_app = Celery(broker=config.celery_broker_url)
db = MongoClient(config.mongodb_uri)[config.mongodb_db_name]
repo = DocumentRecordRepository(db)

adapter = ObsidianAdapter(
    vault_path=config.vault_path,
    celery_app=celery_app,
    record_repo=repo,
    config=ChunkingConfig(
        max_chars=config.chunk_max_chars,
        overlap_chars=config.chunk_overlap_chars,
    ),
)

AdapterRunner(adapter).run()

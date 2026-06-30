from pathlib import Path

from celery import Celery

from adapters.base_markdown_folder import BaseMarkdownFolderAdapter
from adapters.chunker import ChunkingConfig
from shared.repositories.document_record_repository import DocumentRecordRepository


class MarkdownFolderAdapter(BaseMarkdownFolderAdapter):
    """
    Watches a flat markdown folder (e.g. science-books export output) and
    feeds chunks into the ingest pipeline.
    """

    def __init__(
        self,
        folder_path: str | Path,
        celery_app: Celery,
        record_repo: DocumentRecordRepository,
        config: ChunkingConfig | None = None,
    ):
        super().__init__(
            folder_path,
            celery_app,
            record_repo,
            source_type="science_book_md",
            config=config,
        )

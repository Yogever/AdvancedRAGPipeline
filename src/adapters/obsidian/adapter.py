import logging
from pathlib import Path

from celery import Celery

from adapters.base_markdown_folder import BaseMarkdownFolderAdapter
from adapters.chunker import ChunkingConfig
from shared.repositories.document_record_repository import DocumentRecordRepository

logger = logging.getLogger(__name__)


class ObsidianAdapter(BaseMarkdownFolderAdapter):
    def __init__(
        self,
        vault_path: str | Path,
        celery_app: Celery,
        record_repo: DocumentRecordRepository,
        config: ChunkingConfig | None = None,
    ):
        super().__init__(vault_path, celery_app, record_repo, source_type="obsidian", config=config)

    def _make_metadata(self, file_path: Path) -> dict:
        return {
            "filename": file_path.name,
            "path": str(file_path),
            "vault_name": self.folder_root.name,
        }

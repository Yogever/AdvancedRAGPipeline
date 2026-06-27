import logging
from pathlib import Path

from celery import Celery
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from adapters.base import BaseAdapter
from adapters.obsidian.chunker import ChunkingConfig, chunk_markdown
from shared.models.chunk import Chunk
from shared.repositories.document_record_repository import DocumentRecordRepository

logger = logging.getLogger(__name__)


class ObsidianAdapter(BaseAdapter):
    def __init__(
        self,
        vault_path: str | Path,
        celery_app: Celery,
        record_repo: DocumentRecordRepository,
        config: ChunkingConfig | None = None,
    ):
        super().__init__(celery_app, record_repo)
        self.vault_root = Path(vault_path).resolve()
        self.config = config or ChunkingConfig()
        self._observer = Observer()

    def start(self) -> None:
        self._discover_existing()
        handler = _VaultEventHandler(self._process_file)
        self._observer.schedule(handler, str(self.vault_root), recursive=True)
        self._observer.start()
        logger.info("Watching vault: %s", self.vault_root)

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()

    def _chunk(self, content: str, source_id: str, metadata: dict) -> list[Chunk]:
        return chunk_markdown(content, source_id, metadata, self.config)

    def _discover_existing(self) -> None:
        for md_file in self.vault_root.rglob("*.md"):
            self._process_file(md_file)

    def _process_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not read %s — skipping", file_path)
            return

        source_id = str(file_path.relative_to(self.vault_root)).replace("\\", "/")
        metadata = {"filename": file_path.name, "path": str(file_path)}
        self._process_document(content, source_id, metadata)


class _VaultEventHandler(FileSystemEventHandler):
    def __init__(self, process):
        self._process = process

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(Path(event.src_path))

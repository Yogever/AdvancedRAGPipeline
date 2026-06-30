import logging
import threading
from pathlib import Path

from celery import Celery

from adapters.base import BaseAdapter
from adapters.chunker import ChunkingConfig, chunk_markdown
from shared.models.chunk import Chunk
from shared.repositories.document_record_repository import DocumentRecordRepository

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 60


class BaseMarkdownFolderAdapter(BaseAdapter):
    """
    Polls a folder for .md files and dispatches chunks to the ingest queue.
    Subclasses override _make_source_id / _make_metadata to customise per source type.
    """

    def __init__(
        self,
        folder_path: str | Path,
        celery_app: Celery,
        record_repo: DocumentRecordRepository,
        source_type: str,
        config: ChunkingConfig | None = None,
        scan_interval: int = SCAN_INTERVAL_SECONDS,
    ):
        super().__init__(celery_app, record_repo)
        self.folder_root = Path(folder_path).resolve()
        self.source_type = source_type
        self.config = config or ChunkingConfig()
        self._scan_interval = scan_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        logger.info("Scanning folder: %s", self.folder_root)
        self._discover_existing()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Polling folder every %ds: %s", self._scan_interval, self.folder_root)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(timeout=self._scan_interval):
            logger.debug("Running scheduled folder scan")
            self._discover_existing()

    def _discover_existing(self) -> None:
        for md_file in self.folder_root.rglob("*.md"):
            self._process_file(md_file)

    def _process_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not read %s — skipping", file_path)
            return
        source_id = self._make_source_id(file_path)
        metadata = self._make_metadata(file_path)
        self._process_document(content, source_id, metadata)

    def _make_source_id(self, file_path: Path) -> str:
        return str(file_path.relative_to(self.folder_root)).replace("\\", "/")

    def _make_metadata(self, file_path: Path) -> dict:
        return {"filename": file_path.name, "path": str(file_path)}

    def _chunk(self, content: str, source_id: str, metadata: dict) -> list[Chunk]:
        return chunk_markdown(content, source_id, self.source_type, metadata, self.config)

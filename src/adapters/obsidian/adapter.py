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
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        logger.info("Scanning vault: %s", self.vault_root)
        self._discover_existing()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Polling vault every %ds: %s", SCAN_INTERVAL_SECONDS, self.vault_root)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(timeout=SCAN_INTERVAL_SECONDS):
            logger.debug("Running scheduled vault scan")
            self._discover_existing()

    def _chunk(self, content: str, source_id: str, metadata: dict) -> list[Chunk]:
        return chunk_markdown(content, source_id, "obsidian", metadata, self.config)

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
        metadata = {"filename": file_path.name, "path": str(file_path), "vault_name": self.vault_root.name}
        self._process_document(content, source_id, metadata)

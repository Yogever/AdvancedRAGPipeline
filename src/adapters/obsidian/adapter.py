import hashlib
import logging
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from adapters.obsidian.chunker import ChunkingConfig, chunk_markdown
from shared.models.chunk import Chunk
from shared.models.document_record import DocumentRecord, DocumentStatus

logger = logging.getLogger(__name__)


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _source_id(vault_root: Path, file_path: Path) -> str:
    return str(file_path.relative_to(vault_root)).replace("\\", "/")


def _extract_metadata(file_path: Path) -> dict:
    return {"filename": file_path.name, "path": str(file_path)}


class ObsidianAdapter:
    """
    Watches an Obsidian vault for new and changed markdown files.
    Produces Chunks and passes them to the provided on_chunks callback.
    Change detection is done via content hash stored in a DocumentRecord store.
    """

    def __init__(
        self,
        vault_path: str | Path,
        on_chunks: Callable[[list[Chunk]], None],
        get_record: Callable[[str], DocumentRecord | None],
        save_record: Callable[[DocumentRecord], None],
        config: ChunkingConfig | None = None,
    ):
        self.vault_root = Path(vault_path).resolve()
        self.on_chunks = on_chunks
        self.get_record = get_record
        self.save_record = save_record
        self.config = config or ChunkingConfig()
        self._observer = Observer()

    def start(self) -> None:
        self._index_existing()
        handler = _VaultEventHandler(self._process_file)
        self._observer.schedule(handler, str(self.vault_root), recursive=True)
        self._observer.start()
        logger.info("Watching vault: %s", self.vault_root)

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()

    def _index_existing(self) -> None:
        for md_file in self.vault_root.rglob("*.md"):
            self._process_file(md_file)

    def _process_file(self, file_path: Path) -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning("Could not read %s — skipping", file_path)
            return

        source_id = _source_id(self.vault_root, file_path)
        content_hash = _hash(content)
        record = self.get_record(source_id)

        if record and record.content_hash == content_hash:
            return  # unchanged

        chunks = chunk_markdown(content, source_id, _extract_metadata(file_path), self.config)
        self.on_chunks(chunks)

        self.save_record(DocumentRecord(
            source_id=source_id,
            content_hash=content_hash,
            status=DocumentStatus.INDEXING,
        ))
        logger.info("Dispatched %d chunk(s) for %s", len(chunks), source_id)


class _VaultEventHandler(FileSystemEventHandler):
    def __init__(self, process: Callable[[Path], None]):
        self._process = process

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.endswith(".md"):
            self._process(Path(event.src_path))

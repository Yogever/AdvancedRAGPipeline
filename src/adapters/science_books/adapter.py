import logging
from pathlib import Path

from celery import Celery
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

from adapters.base import BaseAdapter
from adapters.chunker import ChunkingConfig, chunk_markdown
from shared.models.chunk import Chunk
from shared.repositories.document_record_repository import DocumentRecordRepository

logger = logging.getLogger(__name__)


class ScienceBookAdapter(BaseAdapter):
    def __init__(
        self,
        books_path: str | Path,
        celery_app: Celery,
        record_repo: DocumentRecordRepository,
        config: ChunkingConfig | None = None,
    ):
        super().__init__(celery_app, record_repo)
        self.books_root = Path(books_path).resolve()
        self.config = config or ChunkingConfig(chunk_size=2000, chunk_overlap=200)

    def start(self) -> None:
        logger.info("Indexing science books: %s", self.books_root)
        self._discover_existing()
        logger.info("Indexing complete.")

    def stop(self) -> None:
        pass

    def _discover_existing(self) -> None:
        for pdf_file in self.books_root.rglob("*.pdf"):
            self._process_file(pdf_file)

    def _process_file(self, file_path: Path) -> None:
        try:
            loader = DoclingLoader(
                file_path=str(file_path),
                export_type=ExportType.MARKDOWN,
            )
            docs = loader.load()
        except Exception:
            logger.warning("Could not load %s — skipping", file_path, exc_info=True)
            return

        if not docs:
            logger.warning("No content extracted from %s — skipping", file_path)
            return

        content = "\n\n".join(doc.page_content for doc in docs)
        source_id = f"science_books/{file_path.name}"
        metadata = {"filename": file_path.name, "path": str(file_path)}
        self._process_document(content, source_id, metadata)

    def _chunk(self, content: str, source_id: str, metadata: dict) -> list[Chunk]:
        return chunk_markdown(content, source_id, "science_book", metadata, self.config)

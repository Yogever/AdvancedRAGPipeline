import gc
import logging
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger(__name__)


class ScienceBookAdapter:
    """
    Standalone export tool: converts PDF files to markdown and writes them to
    output_path. No pipeline dependencies (no Celery, no MongoDB) so it can be
    run separately from the indexing step.

    Uses pymupdf4llm (libmupdf under the hood — no ML models, no image rendering)
    which handles arbitrarily large pages without memory issues.

    The markdown output folder is then indexed by MarkdownFolderAdapter.
    """

    def __init__(self, books_path: str | Path, output_path: str | Path):
        self.books_root = Path(books_path).resolve()
        self.output_path = Path(output_path).resolve()

    def start(self) -> None:
        logger.info("Exporting PDFs: %s → %s", self.books_root, self.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self._discover_existing()
        logger.info("Export complete.")

    def stop(self) -> None:
        pass

    def _discover_existing(self) -> None:
        for pdf_file in self.books_root.rglob("*.pdf"):
            self._export_pdf(pdf_file)

    def _export_pdf(self, file_path: Path) -> None:
        out_file = self.output_path / (file_path.stem + ".md")
        if out_file.exists():
            logger.debug("Already exported, skipping: %s", file_path.name)
            return

        logger.info("Processing: %s", file_path.name)
        try:
            content = pymupdf4llm.to_markdown(str(file_path))
        except Exception:
            logger.warning("Could not convert %s — skipping", file_path, exc_info=True)
            return

        if not content.strip():
            logger.warning("No content extracted from %s — skipping", file_path)
            return

        out_file.write_text(content, encoding="utf-8")
        logger.info("Exported: %s → %s", file_path.name, out_file.name)

        del content
        gc.collect()

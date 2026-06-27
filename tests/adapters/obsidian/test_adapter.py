import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adapters.obsidian.adapter import ObsidianAdapter
from adapters.obsidian.chunker import ChunkingConfig
from shared.models.document_record import DocumentRecord, DocumentStatus
from shared.repositories.document_record_repository import DocumentRecordRepository

CFG = ChunkingConfig(max_chars=500, overlap_chars=0)


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


class FakeDocumentRecordRepository(DocumentRecordRepository):
    """In-memory substitute for tests — no MongoDB needed."""

    def __init__(self):
        self._store: dict[str, DocumentRecord] = {}

    def get(self, source_id: str) -> DocumentRecord | None:
        return self._store.get(source_id)

    def save(self, record: DocumentRecord) -> None:
        self._store[record.source_id] = record


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def celery_app():
    return MagicMock()


def make_adapter(vault: Path, celery_app, repo: FakeDocumentRecordRepository):
    return ObsidianAdapter(
        vault_path=vault,
        celery_app=celery_app,
        record_repo=repo,
        config=CFG,
    )


class TestInitialIndexing:
    def test_indexes_existing_files_on_start(self, vault, celery_app):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        adapter = make_adapter(vault, celery_app, repo)
        adapter._discover_existing()
        celery_app.send_task.assert_called()
        assert celery_app.send_task.call_count == 1

    def test_source_id_is_vault_relative(self, vault, celery_app):
        sub = vault / "folder"
        sub.mkdir()
        (sub / "deep.md").write_text("# Deep\nContent.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        adapter = make_adapter(vault, celery_app, repo)
        adapter._discover_existing()
        chunk_payload = celery_app.send_task.call_args[1]["args"][0]
        assert chunk_payload["source_id"] == "folder/deep.md"

    def test_ignores_non_markdown_files(self, vault, celery_app):
        (vault / "image.png").write_bytes(b"\x89PNG")
        (vault / "note.txt").write_text("plain text")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        celery_app.send_task.assert_not_called()


class TestChangeDetection:
    def test_unchanged_file_is_skipped(self, vault, celery_app):
        content = "# Note\nContent."
        (vault / "note.md").write_text(content, encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        repo.save(DocumentRecord(source_id="note.md", content_hash=_hash(content)))
        make_adapter(vault, celery_app, repo)._discover_existing()
        celery_app.send_task.assert_not_called()

    def test_changed_file_is_reprocessed(self, vault, celery_app):
        (vault / "note.md").write_text("# New\nUpdated.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        repo.save(DocumentRecord(source_id="note.md", content_hash=_hash("old content")))
        make_adapter(vault, celery_app, repo)._discover_existing()
        celery_app.send_task.assert_called()

    def test_new_file_has_no_existing_record(self, vault, celery_app):
        (vault / "new.md").write_text("# New\nBrand new.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        celery_app.send_task.assert_called()

    def test_record_saved_after_processing(self, vault, celery_app):
        content = "# Note\nContent."
        (vault / "note.md").write_text(content, encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        assert "note.md" in repo._store
        assert repo._store["note.md"].status == DocumentStatus.INDEXING
        assert repo._store["note.md"].content_hash == _hash(content)


class TestIngestQueueDispatch:
    def test_one_send_task_call_per_chunk(self, vault, celery_app):
        # Two headings → two chunks
        (vault / "note.md").write_text("# A\nFirst.\n\n# B\nSecond.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        assert celery_app.send_task.call_count == 2

    def test_send_task_uses_correct_task_name(self, vault, celery_app):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        task_name = celery_app.send_task.call_args[0][0]
        assert task_name == "embedding_manager.tasks.ingest_chunk"

    def test_chunk_payload_is_serialized_dict(self, vault, celery_app):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        make_adapter(vault, celery_app, repo)._discover_existing()
        payload = celery_app.send_task.call_args[1]["args"][0]
        assert isinstance(payload, dict)
        assert "content" in payload
        assert "source_id" in payload
        assert "chunk_index" in payload


class TestUnreadableFile:
    def test_unreadable_file_is_skipped(self, vault, celery_app):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        repo = FakeDocumentRecordRepository()
        adapter = make_adapter(vault, celery_app, repo)
        with patch("pathlib.Path.read_text", side_effect=OSError("permission denied")):
            adapter._discover_existing()
        celery_app.send_task.assert_not_called()

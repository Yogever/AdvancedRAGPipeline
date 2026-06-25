import hashlib
from pathlib import Path

import pytest

from adapters.obsidian.adapter import ObsidianAdapter
from adapters.obsidian.chunker import ChunkingConfig
from shared.models.document_record import DocumentRecord, DocumentStatus

CFG = ChunkingConfig(max_chars=500, overlap_chars=0)


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    return tmp_path


def make_adapter(vault: Path, store: dict, collected: list):
    return ObsidianAdapter(
        vault_path=vault,
        on_chunks=lambda chunks: collected.extend(chunks),
        get_record=lambda sid: store.get(sid),
        save_record=lambda rec: store.__setitem__(rec.source_id, rec),
        config=CFG,
    )


class TestInitialIndexing:
    def test_indexes_existing_files_on_start(self, vault):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        collected, store = [], {}
        adapter = make_adapter(vault, store, collected)
        adapter._index_existing()
        assert len(collected) == 1
        assert collected[0].source_id == "note.md"

    def test_source_id_is_vault_relative(self, vault):
        sub = vault / "folder"
        sub.mkdir()
        (sub / "deep.md").write_text("# Deep\nContent.", encoding="utf-8")
        collected, store = [], {}
        make_adapter(vault, store, collected)._index_existing()
        assert collected[0].source_id == "folder/deep.md"

    def test_ignores_non_markdown_files(self, vault):
        (vault / "image.png").write_bytes(b"\x89PNG")
        (vault / "note.txt").write_text("plain text")
        collected, store = [], {}
        make_adapter(vault, store, collected)._index_existing()
        assert collected == []


class TestChangeDetection:
    def test_unchanged_file_is_skipped(self, vault):
        content = "# Note\nContent."
        (vault / "note.md").write_text(content, encoding="utf-8")
        store = {"note.md": DocumentRecord(source_id="note.md", content_hash=_hash(content))}
        collected = []
        make_adapter(vault, store, collected)._index_existing()
        assert collected == []

    def test_changed_file_is_reprocessed(self, vault):
        (vault / "note.md").write_text("# New\nUpdated content.", encoding="utf-8")
        store = {"note.md": DocumentRecord(source_id="note.md", content_hash=_hash("old content"))}
        collected = []
        make_adapter(vault, store, collected)._index_existing()
        assert len(collected) == 1

    def test_new_file_has_no_existing_record(self, vault):
        (vault / "new.md").write_text("# New\nBrand new.", encoding="utf-8")
        collected, store = [], {}
        make_adapter(vault, store, collected)._index_existing()
        assert len(collected) == 1

    def test_record_saved_after_processing(self, vault):
        (vault / "note.md").write_text("# Note\nContent.", encoding="utf-8")
        collected, store = [], {}
        make_adapter(vault, store, collected)._index_existing()
        assert "note.md" in store
        assert store["note.md"].status == DocumentStatus.INDEXING
        assert store["note.md"].content_hash == _hash("# Note\nContent.")


class TestUnreadableFile:
    def test_unreadable_file_is_skipped(self, vault, caplog):
        (vault / "note.md").write_text("# Hello\nWorld.", encoding="utf-8")
        collected, store = [], {}
        adapter = make_adapter(vault, store, collected)

        # Simulate an unreadable file by patching read_text
        from unittest.mock import patch
        with patch("pathlib.Path.read_text", side_effect=OSError("permission denied")):
            adapter._index_existing()

        assert collected == []

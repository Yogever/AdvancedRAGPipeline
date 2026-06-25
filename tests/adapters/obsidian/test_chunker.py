import pytest
from adapters.obsidian.chunker import ChunkingConfig, chunk_markdown

META = {"filename": "test.md", "path": "/vault/test.md"}
SID = "test.md"


def chunks(content: str, max_chars: int = 500, overlap_chars: int = 0) -> list[str]:
    cfg = ChunkingConfig(max_chars=max_chars, overlap_chars=overlap_chars)
    return [c.content for c in chunk_markdown(content, SID, META, cfg)]


class TestHeadingSplit:
    def test_splits_at_headings(self):
        content = "# Intro\nHello.\n\n# Details\nWorld."
        result = chunks(content)
        assert len(result) == 2
        assert result[0].startswith("# Intro")
        assert result[1].startswith("# Details")

    def test_all_heading_levels(self):
        content = "# H1\nA\n## H2\nB\n### H3\nC"
        result = chunks(content)
        assert len(result) == 3

    def test_preamble_before_first_heading(self):
        content = "Some preamble.\n\n# Section\nContent."
        result = chunks(content)
        assert result[0] == "Some preamble."
        assert result[1].startswith("# Section")

    def test_no_headings_returns_single_chunk(self):
        content = "Just a paragraph with no headings."
        result = chunks(content)
        assert len(result) == 1
        assert result[0] == content


class TestFallbackSplitting:
    def test_oversized_section_splits_by_paragraph(self):
        para_a = "a" * 200
        para_b = "b" * 200
        content = f"# Section\n{para_a}\n\n{para_b}"
        result = chunks(content, max_chars=250)
        assert len(result) == 2
        assert all(len(r) <= 250 for r in result)

    def test_oversized_paragraph_splits_by_sentence(self):
        sentences = " ".join(["Short sentence."] * 20)
        result = chunks(sentences, max_chars=100)
        assert len(result) > 1
        assert all(len(r) <= 100 for r in result)

    def test_oversized_sentence_falls_back_to_chars(self):
        # One massive word — no sentence or paragraph boundary
        content = "x" * 300
        result = chunks(content, max_chars=100)
        assert len(result) == 3
        assert all(len(r) <= 100 for r in result)

    def test_all_chunks_within_limit(self):
        content = "\n\n".join([
            "# Big Section",
            "a" * 400,
            "b" * 400,
            "## Sub\n" + "c" * 400,
        ])
        result = chunks(content, max_chars=200)
        assert all(len(r) <= 200 for r in result)


class TestOverlap:
    def test_overlap_prepended_to_next_chunk(self):
        content = "# A\n" + "a" * 80 + "\n\n# B\n" + "b" * 80
        result = chunks(content, max_chars=200, overlap_chars=15)
        assert len(result) == 2
        assert result[1].startswith("a" * 15)

    def test_no_overlap_when_zero(self):
        content = "# A\nFirst.\n\n# B\nSecond."
        result = chunks(content, max_chars=500, overlap_chars=0)
        assert not result[1].startswith("First")

    def test_single_chunk_no_overlap_applied(self):
        content = "Short content."
        result = chunks(content, max_chars=500, overlap_chars=50)
        assert len(result) == 1
        assert result[0] == content


class TestChunkMetadata:
    def test_chunk_index_and_total(self):
        content = "# A\nHello.\n\n# B\nWorld.\n\n# C\nDone."
        cfg = ChunkingConfig(max_chars=500, overlap_chars=0)
        cs = chunk_markdown(content, SID, META, cfg)
        assert [c.chunk_index for c in cs] == [0, 1, 2]
        assert all(c.total_chunks == 3 for c in cs)

    def test_source_fields_propagated(self):
        cfg = ChunkingConfig(max_chars=500, overlap_chars=0)
        cs = chunk_markdown("# A\nHello.", "vault/note.md", META, cfg)
        assert all(c.source_id == "vault/note.md" for c in cs)
        assert all(c.source_type == "obsidian" for c in cs)
        assert all(c.metadata == META for c in cs)

    def test_empty_sections_dropped(self):
        content = "# A\n\n# B\nActual content."
        result = chunks(content)
        assert all(r.strip() for r in result)

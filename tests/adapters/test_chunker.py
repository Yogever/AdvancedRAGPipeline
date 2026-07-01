from adapters.chunker import ChunkingConfig, chunk_markdown

META = {"filename": "test.md", "path": "/vault/test.md"}
SID = "test.md"
SOURCE_TYPE = "obsidian"


def chunks(content: str, chunk_size: int = 500, chunk_overlap: int = 0) -> list[str]:
    cfg = ChunkingConfig(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return [c.content for c in chunk_markdown(content, SID, SOURCE_TYPE, META, cfg)]


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

    def test_no_headings_returns_single_chunk(self):
        content = "Just a paragraph with no headings."
        result = chunks(content)
        assert len(result) == 1
        assert result[0] == content


class TestOversizedSections:
    def test_oversized_section_is_split_further(self):
        content = "# Section\n" + ("a" * 400)
        result = chunks(content, chunk_size=150)
        assert len(result) > 1
        assert all(len(r) <= 150 for r in result)


class TestOverlap:
    def test_overlap_applied_between_chunks(self):
        content = "a" * 300
        result = chunks(content, chunk_size=100, chunk_overlap=20)
        assert len(result) > 1
        assert result[1].startswith(result[0][-20:])

    def test_no_overlap_when_zero(self):
        content = "# A\nFirst.\n\n# B\nSecond."
        result = chunks(content, chunk_size=500, chunk_overlap=0)
        assert not result[1].startswith("First")


class TestChunkMetadata:
    def test_chunk_index_and_total(self):
        content = "# A\nHello.\n\n# B\nWorld.\n\n# C\nDone."
        cfg = ChunkingConfig(chunk_size=500, chunk_overlap=0)
        cs = chunk_markdown(content, SID, SOURCE_TYPE, META, cfg)
        assert [c.chunk_index for c in cs] == [0, 1, 2]
        assert all(c.total_chunks == 3 for c in cs)

    def test_source_fields_propagated(self):
        cfg = ChunkingConfig(chunk_size=500, chunk_overlap=0)
        cs = chunk_markdown("# A\nHello.", "vault/note.md", SOURCE_TYPE, META, cfg)
        assert all(c.source_id == "vault/note.md" for c in cs)
        assert all(c.source_type == SOURCE_TYPE for c in cs)
        for c in cs:
            assert c.metadata["filename"] == META["filename"]
            assert c.metadata["path"] == META["path"]

    def test_heading_text_added_to_metadata(self):
        cfg = ChunkingConfig(chunk_size=500, chunk_overlap=0)
        cs = chunk_markdown("# Section One\nContent.", SID, SOURCE_TYPE, META, cfg)
        assert cs[0].metadata["h1"] == "Section One"

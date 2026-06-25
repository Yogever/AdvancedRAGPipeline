import re
from dataclasses import dataclass

from shared.models.chunk import Chunk

_HEADING_SPLIT_RE = re.compile(r"(?=^#{1,6}\s)", re.MULTILINE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class ChunkingConfig:
    max_chars: int = 1000
    overlap_chars: int = 100


def chunk_markdown(
    content: str,
    source_id: str,
    metadata: dict,
    config: ChunkingConfig,
) -> list[Chunk]:
    sections = _split_by_headings(content)
    pieces: list[str] = []
    for section in sections:
        pieces.extend(_fit_to_limit(section, config.max_chars))
    pieces = _apply_overlap(pieces, config.overlap_chars)

    total = len(pieces)
    return [
        Chunk(
            content=piece,
            source_id=source_id,
            source_type="obsidian",
            chunk_index=i,
            total_chunks=total,
            metadata=metadata,
        )
        for i, piece in enumerate(pieces)
    ]


def _split_by_headings(content: str) -> list[str]:
    parts = _HEADING_SPLIT_RE.split(content)
    return [p.strip() for p in parts if p.strip()]


def _fit_to_limit(text: str, max_chars: int) -> list[str]:
    """Recursively split text until all pieces are within max_chars."""
    if len(text) <= max_chars:
        return [text]

    for splitter in (_split_by_paragraphs, _split_by_sentences, _split_by_chars):
        pieces = splitter(text, max_chars)
        if len(pieces) > 1:
            # Recurse: each piece may still be over the limit
            result = []
            for piece in pieces:
                result.extend(_fit_to_limit(piece, max_chars))
            return result

    return [text]  # unreachable — _split_by_chars always produces pieces <= max_chars


def _split_and_merge(parts: list[str], sep: str, max_chars: int) -> list[str]:
    """Merge adjacent parts greedily until adding the next would exceed max_chars."""
    result: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + sep + part) if current else part
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                result.append(current)
            current = part
    if current:
        result.append(current)
    return result or [sep.join(parts)]


def _split_by_paragraphs(text: str, max_chars: int) -> list[str]:
    return _split_and_merge(text.split("\n\n"), "\n\n", max_chars)


def _split_by_sentences(text: str, max_chars: int) -> list[str]:
    return _split_and_merge(_SENTENCE_SPLIT_RE.split(text), " ", max_chars)


def _split_by_chars(text: str, max_chars: int) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _apply_overlap(pieces: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars == 0 or len(pieces) <= 1:
        return pieces
    result = [pieces[0]]
    for i in range(1, len(pieces)):
        tail = pieces[i - 1][-overlap_chars:]
        result.append(tail + pieces[i])
    return result

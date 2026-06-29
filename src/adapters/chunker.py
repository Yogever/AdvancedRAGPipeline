from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from shared.models.chunk import Chunk

_HEADERS_TO_SPLIT_ON = [("#", "h1"), ("##", "h2"), ("###", "h3")]


@dataclass
class ChunkingConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 100


def chunk_markdown(
    content: str,
    source_id: str,
    source_type: str,
    metadata: dict,
    config: ChunkingConfig,
) -> list[Chunk]:
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    header_docs = header_splitter.split_text(content)
    pieces = char_splitter.split_documents(header_docs)

    total = len(pieces)
    return [
        Chunk(
            content=doc.page_content,
            source_id=source_id,
            source_type=source_type,
            chunk_index=i,
            total_chunks=total,
            metadata={**metadata, **doc.metadata},
        )
        for i, doc in enumerate(pieces)
    ]

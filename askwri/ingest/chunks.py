"""Cut parsed PDF blocks into section-bounded text chunks with stable IDs."""

from collections import Counter
from dataclasses import dataclass

from askwri.ingest.pdf import Block

# About two long paragraphs: small enough for precise search, large enough to stand alone.
MAX_CHUNK_CHARS = 2000
SEPARATOR = " › "


@dataclass(frozen=True)
class Chunk:
    """One citable passage and everything a citation needs."""

    chunk_id: str  # "<doc_id>#p<pdf_page>-<position on page>", identical across reruns
    doc_id: str
    doc_title: str
    pdf_page: int
    section: str  # section path, e.g. "Supply risks › Lithium"
    kind: str
    text: str  # passage text; paragraphs separated by blank lines
    quotable: bool = True  # False when the audit found the words re-ordered against the PDF
    # The document's labels, copied onto every chunk so retrieval can filter on them.
    label_source: str = "no page"  # "wri.org", or "no page" (the citation then cites the PDF)
    link: str | None = None
    year: int | None = None
    topic: str | None = None
    wri_type: str | None = None
    tags: tuple[str, ...] = ()

    @property
    def address(self) -> str:
        """Where the passage sits: document title › section path."""
        return SEPARATOR.join(part for part in (self.doc_title, self.section) if part)

    @property
    def indexed_text(self) -> str:
        """The text sent to the knowledge base: address first, so the passage stands alone."""
        return f"{self.address}\n\n{self.text}"


def build_chunks(doc_id: str, doc_title: str, blocks: list[Block]) -> list[Chunk]:
    """Group body blocks into chunks that never cross a heading or a page break.

    Headings update the section path; a heading repeating the document title is not part of
    it. A chunk closes before it would grow past MAX_CHUNK_CHARS.
    """
    chunks: list[Chunk] = []
    per_page = Counter()
    section_path: list[tuple[int, str]] = []  # (heading level, heading text), outermost first
    paragraphs: list[str] = []
    page = 0

    def close_chunk():
        if not paragraphs:
            return
        per_page[page] += 1
        chunks.append(
            Chunk(
                chunk_id=f"{doc_id}#p{page}-{per_page[page]}",
                doc_id=doc_id,
                doc_title=doc_title,
                pdf_page=page,
                section=SEPARATOR.join(text for _, text in section_path),
                kind="source_text",
                text="\n\n".join(paragraphs),
            )
        )
        paragraphs.clear()

    for block in blocks:
        if block.page != page:
            close_chunk()
            page = block.page
        if block.heading_level:
            close_chunk()
            if block.text.casefold() != doc_title.casefold():
                while section_path and section_path[-1][0] >= block.heading_level:
                    section_path.pop()
                section_path.append((block.heading_level, block.text))
            continue
        if paragraphs and len("\n\n".join([*paragraphs, block.text])) > MAX_CHUNK_CHARS:
            close_chunk()
        paragraphs.append(block.text)
    close_chunk()
    return chunks

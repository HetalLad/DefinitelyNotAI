"""Citation audit: check every chunk against the PDF's own text layer before it is indexed."""

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from askwri.ingest.chunks import Chunk
from askwri.ingest.text import comparable, missing_words


@dataclass(frozen=True)
class AuditResult:
    """Failures block indexing. Unquotable chunks are indexed but may never be quoted verbatim."""

    failures: list[str]
    unquotable: list[str]  # chunk IDs whose words are on the page, but not in this order
    pages_without_text: list[int]

    @property
    def passed(self) -> bool:
        return not self.failures


def audit_chunks(pdf_path: Path, chunks: list[Chunk]) -> AuditResult:
    """Check each chunk against the plain-text layer of the page it claims.

    A chunk fails if it is empty, mostly non-text, or has words that are not on its page.
    A chunk whose words are all on its page, but where some paragraph is not a contiguous run
    of the page's text, is unquotable: the layout model re-ordered it (diagram labels,
    a pull quote overlapping a paragraph), so it may be cited by page but not quoted.
    Matching ignores case, whitespace, punctuation, line-end hyphens and ligatures.
    """
    with pymupdf.open(pdf_path) as doc:
        page_texts = [page.get_text() for page in doc]
    failures, unquotable = [], []
    for chunk in chunks:
        page_text = page_texts[chunk.pdf_page - 1]
        paragraphs = [p for p in chunk.text.split("\n\n") if p.strip()]
        if not paragraphs:
            failures.append(f"{chunk.chunk_id}: empty chunk")
        elif _mostly_non_text(chunk.text):
            failures.append(f"{chunk.chunk_id}: mostly non-text characters")
        elif missing := missing_words(chunk.text, page_text):
            failures.append(
                f"{chunk.chunk_id}: passage not found on page {chunk.pdf_page}; "
                f"missing words: {', '.join(missing[:5])}"
            )
        elif any(comparable(p) not in comparable(page_text) for p in paragraphs):
            unquotable.append(chunk.chunk_id)
    return AuditResult(
        failures=failures,
        unquotable=unquotable,
        pages_without_text=[n for n, text in enumerate(page_texts, start=1) if not text.strip()],
    )


def _mostly_non_text(text: str) -> bool:
    visible = [char for char in text if not char.isspace()]
    return sum(char.isalnum() for char in visible) < len(visible) / 2

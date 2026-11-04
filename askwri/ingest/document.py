"""Ingest one PDF: parse it, cut it into chunks and audit them."""

import dataclasses
import re
from dataclasses import dataclass
from pathlib import Path

from askwri.ingest.audit import AuditResult, audit_chunks
from askwri.ingest.chunks import Chunk, build_chunks
from askwri.ingest.pdf import ParsedPdf, parse_pdf


@dataclass(frozen=True)
class IngestResult:
    """One PDF's chunks, marked quotable or not, and the audit that decides if they're indexed."""

    chunks: list[Chunk]
    audit: AuditResult


def ingest_document(pdf_path: Path) -> IngestResult:
    """Turn one PDF into chunks plus the audit result that decides whether they may be indexed."""
    parsed = parse_pdf(pdf_path)
    chunks = build_chunks(
        doc_id_for(pdf_path), _title(parsed, pdf_path), parsed.blocks, parsed.printed_pages
    )
    audit = audit_chunks(pdf_path, chunks)
    unquotable = set(audit.unquotable)
    chunks = [
        dataclasses.replace(chunk, quotable=False) if chunk.chunk_id in unquotable else chunk
        for chunk in chunks
    ]
    return IngestResult(chunks=chunks, audit=audit)


def doc_id_for(pdf_path: Path) -> str:
    """A readable, stable document ID from the file name, e.g. "critical-minerals-india"."""
    return re.sub(r"[^a-z0-9]+", "-", pdf_path.stem.lower()).strip("-")


def _title(parsed: ParsedPdf, pdf_path: Path) -> str:
    """The PDF's metadata title, else its first top-level heading, else the file name."""
    if parsed.title:
        return parsed.title
    first_page = parsed.blocks[0].page if parsed.blocks else 0
    headings = [b for b in parsed.blocks if b.page == first_page and b.heading_level]
    if headings:
        return min(headings, key=lambda block: block.heading_level).text
    return pdf_path.stem

"""Command line: ingest PDFs and write chunks with Bedrock Knowledge Bases metadata sidecars."""

import argparse
import json
import sys
from pathlib import Path

from askwri.ingest.chunks import Chunk
from askwri.ingest.document import ingest_document


def write_chunks(chunks: list[Chunk], out_dir: Path) -> None:
    """Write each chunk as <doc_id>/<p..>.txt plus the .metadata.json sidecar Bedrock reads."""
    for chunk in chunks:
        doc_dir = out_dir / chunk.doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        path = doc_dir / f"{chunk.chunk_id.split('#')[1]}.txt"
        path.write_text(chunk.indexed_text, encoding="utf-8")
        attributes = {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "doc_title": chunk.doc_title,
            "pdf_page": chunk.pdf_page,
            "pdf_page_end": chunk.pdf_page_end,
            "printed_page": chunk.printed_page,
            "printed_page_end": chunk.printed_page_end,
            "printed_page_fallback": chunk.printed_page_fallback,
            "section": chunk.section,
            "kind": chunk.kind,
            "quotable": chunk.quotable,
        }
        path.with_name(f"{path.name}.metadata.json").write_text(
            json.dumps({"metadataAttributes": attributes}, ensure_ascii=False), encoding="utf-8"
        )


def main() -> int:
    """Ingest each PDF and write its chunks; a PDF that fails the audit writes nothing.

    Returns the exit code: 1 if any PDF failed the audit, else 0.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path, help="PDF files to ingest")
    parser.add_argument("--out", type=Path, required=True, help="folder for chunk files")
    args = parser.parse_args()

    failed = False
    for pdf in args.pdfs:
        result = ingest_document(pdf)
        for page in result.audit.pages_without_text:
            print(f"{pdf.name}: page {page} has no text layer", file=sys.stderr)
        if not result.audit.passed:
            failed = True
            print(f"{pdf.name}: audit failed, nothing written", file=sys.stderr)
            for failure in result.audit.failures:
                print(f"  {failure}", file=sys.stderr)
            continue
        write_chunks(result.chunks, args.out)
        print(
            f"{pdf.name}: {len(result.chunks)} chunks, "
            f"{len(result.audit.unquotable)} not quotable (re-ordered)"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

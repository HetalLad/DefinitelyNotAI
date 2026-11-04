# Ingestion tracer bullet: one text PDF becomes audited text chunks

Owner: jayparmar16
Status: in-review
Issue: #3 (spec: #2)

## Goal

Set up the Python project and the first end-to-end path through the ingestion pipeline:
ingest one text-only PDF with PyMuPDF and cut it into chunks at section headings. Audit
every chunk against the PDF's text layer and write chunks with Knowledge Bases metadata
sidecars to a local folder. Later tickets (#4–#13) build on this path.

## Done when

- [x] Python 3.12 project managed with uv and ruff, `pymupdf` pinned to an exact version,
      test suite runs; README says how to run the tests and the local ingest command.
- [x] Ingesting one document returns chunk records and an audit result; a local command
      writes chunk text files and metadata sidecars to an output folder.
- [x] Text chunks follow section boundaries and start with their address (document title ›
      section path). Each carries `chunk_id`, `doc_id`, `doc_title`, `pdf_page`, `section`,
      `kind` = `source_text`, and the exact text.
- [x] Chunk IDs are deterministic: two runs on the same PDF give identical IDs.
- [x] The audit checks every chunk (without its address prefix) against its claimed page in
      PyMuPDF's plain-text layer, tolerating whitespace, hyphenation and ligature differences.
      A chunk whose words are all on its page but not in that order is kept and marked
      `quotable: false` (decided on this task; see Notes).
- [x] The audit fails loudly, naming document and chunk, for a passage whose words are not on
      its page and for an empty or mostly non-text chunk. It reports pages with no text layer.
- [x] Tests use small synthetic PDFs built in the test suite (two columns, headings, a page
      with no text layer); no corpus files in git.

## Notes

- The spec's strict audit (every paragraph a contiguous run of the page text) blocked 25% of
  documents in a 40-PDF sample. Every failing paragraph had all its words on its page: the
  layout model had re-ordered diagram labels, merged a pull quote into a paragraph, or
  misplaced ligatures ("frst", "tarifs").
- Fix 1: when a region's layout text isn't verbatim but the PDF text layer for that region is,
  use the text layer.
- Fix 2: the audit blocks only chunks whose words aren't on the page; re-ordered chunks are
  indexed but not quotable.
- Result on two 40-PDF samples (3,657 chunks): 0 documents blocked, 99.3% of chunks
  quotable. Moving every chunk to the next page is still caught 99.4% of the time; the misses
  are text that repeats on both pages (address blocks, "Source: Authors.").

## Handoff

None yet.

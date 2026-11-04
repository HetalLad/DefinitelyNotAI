# Ingestion tracer bullet: one text PDF becomes audited text chunks

Owner: jayparmar16
Status: in-progress
Issue: #3 (spec: #2)

## Goal

Set up the Python project and the first end-to-end path through the ingestion pipeline:
ingest one text-only PDF with PyMuPDF and cut it into chunks at section headings. Audit
every chunk against the PDF's text layer and write chunks with Knowledge Bases metadata
sidecars to a local folder. Later tickets (#4–#13) build on this path.

## Done when

- [ ] Python 3.12 project managed with uv and ruff, `pymupdf` pinned to an exact version,
      test suite runs; README says how to run the tests and the local ingest command.
- [ ] Ingesting one document returns chunk records and an audit result; a local command
      writes chunk text files and metadata sidecars to an output folder.
- [ ] Text chunks follow section boundaries and start with their address (document title ›
      section path). Each carries `chunk_id`, `doc_id`, `doc_title`, `pdf_page`, `section`,
      `kind` = `source_text`, and the exact text.
- [ ] Chunk IDs are deterministic: two runs on the same PDF give identical IDs.
- [ ] The audit finds every chunk's text (without its address prefix) on its claimed page in
      PyMuPDF's plain-text layer, tolerating whitespace, hyphenation and ligature differences.
- [ ] The audit fails loudly, naming document and chunk, for a passage not on its page and
      for an empty or mostly non-text chunk. It reports pages with no text layer.
- [ ] Tests use small synthetic PDFs built in the test suite (two columns, headings, a page
      with no text layer); no corpus files in git.

## Handoff

None yet.

# Ingestion 2: printed page numbers, page ranges and running headers/footers

Owner: jayparmar16
Status: in-progress
Issue: #4 (spec: #2)

## Goal

Citations show the page number readers see, not just the position in the file. Chunks that
cross a page break record their page range, and running headers and footers never leak into
chunk text.

## Done when

- [ ] `printed_page` comes from the PDF's page labels where defined, else from the page-header
      or page-footer region, else falls back to `pdf_page` and is flagged.
- [ ] A document with Roman-numeral front matter gives `printed_page` values that differ
      correctly from `pdf_page`.
- [ ] A chunk spanning a page break records both page ranges (PDF and printed), and the audit
      checks it against both pages.
- [ ] Text from page-header and page-footer regions appears in no chunk (checked on synthetic
      and on real PDFs).
- [ ] Covered by tests on synthetic PDFs with page labels and running headers/footers.
- [ ] Chunk IDs stay stable and based on the start page; the 40-PDF regression samples still
      show 0 documents failing.

## Handoff

None yet.

# Ingestion 8: sort the corpus

Owner: jayparmar16
Status: in-progress
Issue: #10 (spec: #2)

## Goal

Only the right documents get ingested. Duplicates and older versions are dropped, non-English
files are dropped while the English twin is kept, and each document is typed. Every dropped
file is reported with its reason.

## Done when

- [ ] Exact duplicates are found by content hash.
- [ ] Version families (version markers such as 2.0 and 2.1, and `_0` suffixes) keep only the
      latest version, and the kept document records which version(s) it replaces.
- [ ] Language is detected from the first pages with a stopword-ratio heuristic (standard
      library only). Non-English files are dropped, and the English twin is kept.
- [ ] Document type is one of: research report, working paper, issue brief, technical note,
      newsletter, RFP, dataset documentation, annual report, other.
- [ ] The result lists kept documents and dropped documents with a reason each.
- [ ] Kept documents have unique `doc_id`s.
- [ ] Tests use synthetic PDFs.
- [ ] A command prints the sorting report for a folder list; run on the full corpus, with the
      numbers in the PR body.

## Handoff

None yet.

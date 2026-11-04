# Document labels from wri.org and the catalog row

Owner: jayparmar16
Status: in-progress
Issue: #8 (spec: #2)

## Goal

Give each document WRI's own labels (topic, type, authors, date, tags) wherever a wri.org
page exists, produce one catalog row per document, and check that the link a citation shows
resolves. Documents with no page cite the stored PDF, and the label source is recorded.

## Done when

- [ ] The document's own WRI DOI (prefix `10.46830`) is taken from its suggested-citation or
      copyright block, not from cited DOIs.
- [ ] The DOI is resolved to its wri.org page. Without a DOI, the PDF title is matched against
      the wri.org sitemap's research and data pages. A page is accepted only when its title
      matches the PDF title.
- [ ] From the page's meta tags the pipeline reads `wri_topic` (main topic), `wri_type`,
      `citation_author`, `citation_publication_date` and `article:tag` (secondary tags).
- [ ] `YYYY-DD-MM` dates are normalised, and ambiguous dates are checked against the PDF.
- [ ] Site topic values map onto the 11 topics (for example `Equity & Governance` becomes
      Equity), and an unmapped value fails loudly.
- [ ] The audit checks that each link resolves; with no page, the citation falls back to the
      stored PDF and the label source is recorded.
- [ ] One catalog row per document is produced, and the filterable fields are added to each
      chunk record (scope update: #12 stores them as database columns).
- [ ] Tests fake the HTTP fetches and cover the cited-DOI, date and topic cases.

## Handoff

None yet.

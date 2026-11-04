# Document labels from wri.org and the catalog row

Owner: jayparmar16
Status: in-review
Issue: #8 (spec: #2)

## Goal

Give each document WRI's own labels (topic, type, authors, date, tags) wherever a wri.org
page exists, produce one catalog row per document, and check that the link a citation shows
resolves. Documents with no page cite the stored PDF, and the label source is recorded.

## Done when

- [x] The document's own WRI DOI (prefix `10.46830`) is taken from its suggested-citation or
      copyright block, not from cited DOIs.
- [x] The DOI is resolved to its wri.org page. Without a DOI, the PDF title is matched against
      the wri.org sitemap's research and data pages. A page is accepted only when its title
      matches the PDF title.
- [x] From the page's meta tags the pipeline reads `wri_topic` (main topic), `wri_type`,
      `citation_author`, `citation_publication_date` and `article:tag` (secondary tags).
- [x] `YYYY-DD-MM` dates are normalised, and ambiguous dates are checked against the PDF.
- [x] Site topic values map onto the 11 topics (for example `Equity & Governance` becomes
      Equity), and an unmapped value fails loudly.
- [x] The audit checks that each link resolves; with no page, the citation falls back to the
      stored PDF and the label source is recorded.
- [x] One catalog row per document is produced, and the filterable fields are added to each
      chunk record (scope update: #12 stores them as database columns).
- [x] Tests fake the HTTP fetches and cover the cited-DOI, date and topic cases.

## Notes

- The link check is the page fetch: `WriSite.find_page` accepts a page only if it answered
  200 on www.wri.org and its title matches, so a link that is stored has been seen to resolve.
  There is no second request. A DOI or sitemap URL that fails the check means "no page"
  (the PDF fallback), not an audit failure.
- `citation_publication_date` was year-day-month on every research page sampled (45 random
  pages plus 14 from DOIs), not "sometimes". Both readings are tried; a day over 12 settles
  it, then the month and year printed in the PDF, then the page's own `wri_published`.
- Some wri.org topics are not among the 11 (an old page has `Africa`). They raise.

## Handoff

None yet.

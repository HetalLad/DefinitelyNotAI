# Fallback labels from the labeler model

Owner: jayparmar16
Status: in-progress
Issue: #9 (spec: #2)

## Goal

Documents with no wri.org page (most RFPs and newsletters), and pages that give no usable
topic, still get labels. The `labeler` model reads the first pages and fills them in, and the
topic can only be one of WRI's 11 topics or `none`.

## Done when

- [ ] When no wri.org page is found, the `labeler` role reads the first pages and returns, as
      structured output: title, date, document type, main topic, countries and a short summary.
- [ ] The main topic must be one of Business, Cities, Climate, Economics, Energy, Equity,
      Finance, Food, Forests, Freshwater, Ocean, or `none`; any other value is rejected.
- [ ] RFPs also get country and deadline.
- [ ] The catalog row records the label source as `model`.
- [ ] Tests use the fake model client.
- [ ] Before falling back to the model, the title in the suggested-citation block is retried
      against the wri.org page found through the DOI (documents whose metadata title is
      unusable, such as "HIGHLIGHTS" or a file name).
- [ ] Documents whose wri.org page gives no usable topic get their topic from the `labeler`,
      which must pick from the 11 topics or `none`.
- [ ] Evidence on about 15 real documents is in the PR body.

## Handoff

None yet.

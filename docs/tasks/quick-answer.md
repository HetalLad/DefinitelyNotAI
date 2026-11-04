# Quick answer: cited answers, claim verification and the decline

Owner: HetalLad
Status: in-progress

## Goal

Issue #38. A Quick answer question returns either a short answer in which every sentence cites
the WRI passages that support it, or a decline that says what was searched and names related
WRI work. Also the verification, decline, finalize and streaming steps that Deep research reuses.

## Done when

### Quick answer flow (`askwri/answer/quick.py`)

- [ ] `quick_draft(request, *, search, client)` yields AgentEvents (C5) and returns a C2 draft.
- [ ] One `labeler` JSON call plans 1 or 2 English queries plus any filter the question states.
      Request filters win over planned ones, key by key.
- [ ] Results merge by `chunk_id` (higher score kept); the 8 best go to the draft. A `step` event
      before each search, a `source-found` event the first time each document appears.
- [ ] If no passage scores at least `ASKWRI_DECLINE_SCORE`, one `labeler` call broadens the query
      and the search runs once more. At most 2 rounds.
- [ ] Retry filters: filters from the request (UI) stay on every search, including the retry.
      Filters inferred from the question are dropped by the retry.
- [ ] One `answerer` JSON call drafts 2 to 6 English sentences in 1 to 3 paragraphs, each with
      `cites`. The prompt allows quotes only from quotable passages, asks for `answerable: false`
      when the passages don't answer, and marks passage text as data.
- [ ] `searched` holds each query and filter as a chip; `seen` holds every passage returned.
- [ ] Steps `plan`, `search-1`, `search-2`, `draft`, `verify` go from `now` to `done` with the
      labels from #38.

### Verification (`askwri/answer/verify.py`)

- [ ] Every sentence in `paragraphs` and `report.key_points` is dropped at the first rule it fails:
      no source, quote not found / quote from a non-quotable passage, number not in source,
      not grounded.
- [ ] Numbers: "2,000" in a sentence matches "2000" in a passage; "3.5" does not match "35".
- [ ] Grounding: one `ApplyGuardrail` call per sentence (4 in parallel) against its cited passages;
      a score below `ASKWRI_GROUNDING_THRESHOLD` (0.69 vs 0.7) drops it. With
      `ASKWRI_GUARDRAIL_ID` / `ASKWRI_GUARDRAIL_VERSION` unset, the check is skipped and the
      answer says `groundingCheck: "skipped"`.
- [ ] Empty paragraphs are removed; dropped sentences are logged with their reason, never shown.

### Decline and answer (`decline.py`, `finalize.py`)

- [ ] `decline_reason` returns `no-results`, `weak-evidence`, `unanswerable` or `unverified`
      (fewer than half the claims verified), first match wins.
- [ ] The decline has a fixed message per reason, `searched`, and up to 3 related documents.
- [ ] Markers are `[1]` to `[k]` in order of first use across paragraphs then key points, and
      `sources` match the markers exactly.
- [ ] `people` (at most 5, most-cited first), `builtFrom` for reports, claim counts,
      `groundingCheck` and `elapsedSeconds` are filled.

### Streaming, entrypoint and CLI

- [ ] `stream_with_pings` sends a `ping` after 15 seconds of silence and turns an exception into
      one `error` event naming the step.
- [ ] `askwri/answer/app.py` validates the payload, answers bad input, `mode: "deep"` and
      `action: "translate"` with one `error` event, and serves SSE on port 8080 locally.
- [ ] Every run ends with exactly one `answer`, `decline` or `error` event.
- [ ] `uv run python -m askwri.answer "question" [--passages FILE]` prints events as JSON lines.
- [ ] README section "Ask a question" documents the command, the local server and every
      `ASKWRI_*` variable read.

### Packaging

- [ ] `askwri/models.py` imports `pymupdf` inside `_red_square_png`.
- [ ] `bedrock-agentcore` and `boto3` are in `[dependency-groups] agent`, which is in
      `[tool.uv] default-groups`.

### Tests and measurements

- [ ] Tests from #38 pass with FakeClaude, a fake search and a fake grounding check, no network.
- [ ] The PR body reports, for 5 real questions: time to answer, claims verified out of total,
      drops per rule, and Guardrails latency.

## Handoff

None yet.

Pending: the `relaxed` field (soft filters dropped by the retry, shown in the answer) is proposed
on #38 to #41 and waits on agreement before it goes into the C2 and C5 contract.

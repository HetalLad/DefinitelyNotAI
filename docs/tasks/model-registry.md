# Model registry and Claude calls on Bedrock

Owner: jayparmar16
Status: in-progress
Issue: #5

## Goal

Every model call goes through one registry by role, so swapping a model is a one-line change.
Claude is reached on Bedrock's `bedrock-runtime` endpoint through the global inference
profiles. A smoke command makes one real call per Claude role, which settles which Anthropic
SDK client signs the requests.

## Done when

- [ ] Registry roles and IDs: `vision` and `answerer` = `global.anthropic.claude-sonnet-5-5`,
      `labeler` = `global.anthropic.claude-haiku-5-5`, `embedder` = `amazon.titan-embed-text-v2:0`,
      `reranker` = `amazon.rerank-v1:0`.
- [ ] Claude is called through the official Anthropic SDK with IAM (SigV4) credentials from the
      AWS profile or task role, in us-west-2. The new dependency's reason goes in the PR.
- [ ] Structured output is supported for label and summary calls, and images can be sent for
      vision calls.
- [ ] Every response's stop reason is checked; a refusal or error raises an error naming the
      document.
- [ ] A fake client can stand in at this seam for tests.
- [ ] A smoke command makes one call per Claude role and reports success. The model IDs, region
      and command are documented in the README.

## Notes

None yet.

## Handoff

None yet.

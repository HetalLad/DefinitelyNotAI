---
name: review
description: Review the current branch's changes against main on four separate axes - Necessity (what can be deleted), Standards (this repo's code rules), Spec (does it do what the task file asked) and Docs. Reports hard findings that block a PR, and judgement calls. Use before opening a PR, when asked to review a branch, diff or PR, or when asked "is this over-engineered" or "what can we delete". Reports only; changes code only if the user asks.
---

Condensed from Matt Pocock's `code-review` (separate Standards and Spec axes) and Ponytail's
`ponytail-review` (hunting over-engineering).

## 1. Pin the inputs

- Diff: `git fetch origin main`, then `git diff origin/main...HEAD` plus uncommitted
  changes (`git diff HEAD`). Commits: `git log origin/main..HEAD --oneline`. If the user
  names another base or a PR number, use that instead (`gh pr diff <number>`).
- If the diff is empty, say so and stop.
- Spec: `docs/tasks/<branch>.md`. Rules: the "Code rules" and "Documentation rules"
  sections of `AGENTS.md`.

## 2. Review each axis on its own

Keep the axes separate, and don't let one axis's findings change another's. For diffs over
roughly 300 lines, run one subagent per axis in parallel if your tool supports it, giving
each the diff command, the inputs it needs and its brief below.

**Necessity.** For every hunk, ask whether the task needs it. Look for:
- code that redoes what the standard library, boto3 or an AWS managed feature already does
  (hand-rolled retries, custom chunking when the Knowledge Base already chunks)
- a new dependency where the standard library or an existing dependency is enough
- abstractions with one implementation or one caller: base classes, factories,
  registries, plugin hooks
- parameters, flags or config nobody sets, dead branches, code "for later"
- handling for states that can't happen; try/except that only re-raises or swallows
- functions that only forward to another function
- the same logic written twice

**Standards.** Breaches of the AGENTS.md code rules. Also flag these smells as judgement
calls (the AGENTS.md rules win if they conflict). Skip anything ruff already enforces.
- *Mysterious name*: the name doesn't say what it does or holds.
- *Feature envy*: a function that mostly works on another module's data.
- *Data clumps*: the same few values keep travelling together and want to be one type.
- *Primitive obsession*: a bare string or dict standing in for a domain concept.
- *Shotgun surgery*: one logical change scattered across many files.
- *Divergent change*: one module edited for unrelated reasons.
- *Message chains*: long `a.b().c().d()` walks that callers shouldn't depend on.

**Spec.** Check against the task file's Goal and Done-when. Quote the line for each finding:
- items missing or only partly done
- behaviour nobody asked for (scope creep)
- items that look done but are implemented wrong

If there's no task file, report "no task file" and skip this axis.

**Docs.** Check against the AGENTS.md documentation rules:
- missing module or public docstrings
- docstrings or comments that no longer match the code
- comments that only restate the code (cut them)
- a new command, env var, AWS resource or setup step not reflected in AGENTS.md or README

## 3. Severity

- **hard**: clearly breaks a written AGENTS.md rule, misses or breaks a Done-when item, or
  leaks a secret. Hard findings block `create-pr`.
- **judgement**: smells, simpler alternatives, matters of taste.

## 4. Report

One line per finding. No praise, no preamble. Don't merge or rerank across axes.

```markdown
## Necessity
- [hard] src/x.py:42 - cut <what> -> <replacement, or "nothing">
## Standards
- [judgement] src/y.py:10 - possible feature envy: <one line>
## Spec
## Docs

**Verdict:** <n> hard, <m> judgement. <Ready for PR | Fix hard findings first>
```

Write "Nothing found." under an empty axis. If the user asks you to fix findings, fix the
hard ones first, then run the review again.

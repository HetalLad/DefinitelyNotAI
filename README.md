# DefinitelyNotAI

AskWRI: a research assistant that answers questions from World Resources Institute
publications, with a citation for every claim. Built on Amazon Bedrock and AgentCore for an
AWS hackathon.

## Get started

1. Install [Claude Code](https://docs.claude.com/en/docs/claude-code) or [Codex](https://developers.openai.com/codex).
   Either works, and teammates can mix them.
2. Clone the repo and open your AI tool in it:

   ```sh
   git clone https://github.com/jayparmar16/DefinitelyNotAI.git
   cd DefinitelyNotAI
   claude        # or: codex
   ```

3. Type **`/setup`** (Claude Code) or **`$setup`** (Codex) and do what it says until
   every line says PASS.

## Every task

| When you want to | Claude Code | Codex |
|---|---|---|
| Start a task | `/claim-task` | `$claim-task` |
| Stop before it's done | `/handoff` | `$handoff` |
| Check your code | `/review` | `$review` |
| Finish and open a PR | `/create-pr` | `$create-pr` |

You can also just say it in plain words, e.g. "claim a task for PDF ingestion" or "open a PR".

## Ingest PDFs locally

The ingestion pipeline (spec: issue #2) turns WRI PDFs into audited, citable chunks.

```sh
uv sync                                   # install Python dependencies
uv run pytest                             # run the tests
uv run python -m askwri.ingest path/to/report.pdf --out chunks/
```

For each PDF the command writes one `.txt` file per chunk, plus the `.metadata.json` sidecar
that Bedrock Knowledge Bases reads, under `chunks/<doc_id>/`. Before anything is written,
the citation audit checks every chunk against the PDF's own text layer:

- **Blocked:** a chunk that is empty, garbled, or has words that aren't on its page. Nothing
  is written for that PDF, and the command exits with an error.
- **Page ranges:** a chunk may run on across a page break when its section continues. It
  records where it starts and ends (`pdf_page`, `pdf_page_end`), and the audit checks that its
  first passage is on the first page and its last on the last.
- **Not quotable:** a chunk whose words are all on its page, but in a different order (for
  example diagram labels). It is written with `quotable: false`, so answers can cite its
  page but never quote it word for word.

Each sidecar carries two kinds of page number. `pdf_page` and `pdf_page_end` are numbers (the
position in the file, for opening the PDF at the right page). `printed_page` and
`printed_page_end` are the numbers printed on the pages, as text because front matter uses
Roman numerals ("iv"). They come from the PDF's page labels where it has them, else from the
page-header or page-footer text (a number counts only when at least two pages agree on the
same offset from the PDF page). When neither exists, `printed_page` is the PDF page and
`printed_page_fallback` is `true`. Page headers and footers never appear in chunk text.

## The rules

- `main` is protected, so every change goes in through a pull request.
- Write only the code the task needs. `review` flags anything extra.
- Commits that contain secrets are blocked.
- Your own AI tool settings stay on your machine (git ignores them).

The full rules for people and agents are in [AGENTS.md](AGENTS.md).

## FAQ

**`/setup` shows FAIL lines.**
Each FAIL line prints its fix. Your AI runs the fixes it can. Logins you have to run
yourself (in Claude Code, type the command with a `!` in front, e.g.
`! gh auth refresh --scopes repo,workflow`). Then run `/setup` again.

**Push fails with "Permission denied" or 403.**
You aren't a collaborator yet. Send your GitHub username to the repo owner (jayparmar16).

**Push to `main` fails with "protected branch".**
That's expected: work goes on a branch. Move your commits to a new branch, then reset your
local `main`:
`git switch -c my-task && git branch -f main origin/main`

**How do I see who's working on what?**
Each open draft PR is a task someone has claimed. Run `gh pr list` or open the Pull
requests tab.

**How do I take over a task someone handed off?**
Run `/claim-task` and name the PR. Their notes are under "Handoff" in
`docs/tasks/<branch>.md`.

**My commit was blocked by "Detect hardcoded secrets".**
Take the secret out of the file. Put it in `.env` (ignored by git) or your AWS profile, then
commit again. If it was already pushed, rotate it. Don't use `--no-verify`.

**My commit failed with "files were modified by this hook".**
ruff fixed the formatting for you. Run `git add` on those files and commit again.

**"check for added large files" failed.**
Documents and data go in S3, not git.

**`/create-pr` stopped because review found "hard" issues.**
Ask your AI to fix them, then run `/create-pr` again. If you think a finding is wrong, say
why and tell it to go ahead.

**`main` changed while I was working.**
`/create-pr` merges the latest `main` into your branch. If there are conflicts, it works
through them with you.

**How does my PR get merged?**
A teammate (or you) reads it on GitHub and clicks Merge. AI agents never merge.

**Can I change my own Claude or Codex settings, MCP servers, or add personal skills?**
Yes. Put them in `CLAUDE.local.md`, `AGENTS.override.md`, `.claude/settings*.json`,
`.mcp.json`, `.codex/`, or your home folder (`~/.claude`, `~/.codex`). Git ignores all of
these. Changes to the shared skills or `AGENTS.md` go through a PR.

**AWS says "Unable to locate credentials" or "ExpiredToken".**
Sandbox credentials expire. Run `aws sso login`, or export fresh sandbox credentials, then
run `/setup` again.

**Bedrock says a model isn't available in my region.**
Use the model's cross-region inference profile ID (it starts with `us.`, `eu.` or
`global.`) instead of the plain model ID.

**I'm on Windows and the skills don't show up in Claude Code.**
`.claude/skills` is a symlink, which Windows only creates if Developer Mode is on. Turn on
Developer Mode, run `git config --global core.symlinks true`, and clone again. Or use WSL.

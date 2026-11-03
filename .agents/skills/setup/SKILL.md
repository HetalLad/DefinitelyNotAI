---
name: setup
description: Check and fix everything this repo needs on this machine - GitHub CLI login with permission to push and to create and edit PRs, git identity, Python 3.12 and uv, AWS CLI credentials with Bedrock access, and pre-commit hooks. Use on first clone, when a teammate joins, or when git, gh, aws, push or PR commands fail with auth or permission errors.
---

1. Run `scripts/setup.sh`. It is safe to re-run. It prints one PASS or FAIL line per check,
   each FAIL with its fix, and exits non-zero if anything failed.
2. Fix each FAIL:
   - **Installs** (`brew install ...`, `uv tool install ...`, `uv python install ...`): run
     them yourself once the user agrees.
   - **Git identity**: ask for name and email, then set them.
   - **Interactive logins** (`gh auth login`, `gh auth refresh`, `aws configure sso`,
     `aws sso login`): the user has to run these. Give the exact command. In Claude Code,
     tell them to type it with a `!` prefix, e.g. `! gh auth refresh --scopes repo,workflow`.
     In Codex, tell them to run it in their terminal.
   - **No write access**: only the repo owner can fix it. Give the user the command from the
     FAIL line, filled in with their GitHub login, to send to the owner.
3. Re-run `scripts/setup.sh` until everything passes, then show the user the final output.

Never write credentials, tokens or account IDs into repo files.

---
name: handoff
description: Record where the current task stands so a teammate or a fresh AI session (Claude or Codex) can pick it up cold - updates the Handoff section of the task file, then commits and pushes the work in progress. Use when stopping before a task is done, switching tasks, ending a session, or passing work to someone else.
---

1. Open `docs/tasks/<current branch>.md`. If it doesn't exist, ask the user to run
   `claim-task` first.
2. Replace the whole `## Handoff` section with the current state. Keep only the latest
   state; git keeps the history.

   ```markdown
   ## Handoff

   _<YYYY-MM-DD HH:MM> by <GitHub login>_

   - **Done:** what works now, and how it was checked
   - **Next:** the very next step, concrete enough to start without asking anyone
   - **Blocked / open questions:** or "none"
   - **Pointers:** files, commands, AWS resource names, gotchas
   ```

   Write for someone with no context. Point to files and commits; don't paste code. No
   secrets, ARNs or account IDs (the repo is public).
3. Set `Status: handed-off`, and tick any done-when items that are now met.
4. Check `git status`. Leave out anything that looks personal or generated, and ask if
   unsure. Commit the rest: `git commit -m "Handoff <slug>: <next step>"`, then `git push`.
   Pre-commit hooks must pass; never use `--no-verify`. Failing tests are fine as long as
   the handoff says so.
5. Tell the user the PR link and that the next person picks it up with `claim-task`
   (or `gh pr checkout <number>`).

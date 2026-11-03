---
name: claim-task
description: Claim a piece of work before starting it - checks nobody else owns it, then creates the branch, a task file in docs/tasks/, and a draft PR that shows the team who is doing what. Also used to pick up a task someone handed off. Use when starting any new task, feature or fix, when resuming someone else's task, or when the user asks what's taken or in progress.
---

Open draft PRs are the team's task board: a task is claimed once its draft PR exists.

## Claim a new task

1. See what's taken: `gh pr list --state open --json number,title,headRefName,author,isDraft`.
2. Agree a short kebab-case slug with the user (e.g. `kb-ingestion`). If an open PR already
   covers this work, stop and tell the user who owns it.
3. If the working tree has uncommitted changes, ask the user what to do with them first.
   Then branch from the latest main: `git fetch origin && git switch -c <slug> origin/main`.
4. Write `docs/tasks/<slug>.md`. Get the goal and done-when items from the user and ask if
   they are vague. `review` checks the code against this file, so keep it concrete.

   ```markdown
   # <Title>

   Owner: <GitHub login, from `gh api user -q .login`>
   Status: in-progress

   ## Goal

   <one to three lines: what this task delivers and why>

   ## Done when

   - [ ] <observable outcome>

   ## Handoff

   None yet.
   ```

5. Commit and push: `git add docs/tasks/<slug>.md && git commit -m "Claim <slug>" && git push -u origin <slug>`.
6. Open the draft PR:
   `gh pr create --draft --base main --title "<Title>" --body "Task: docs/tasks/<slug>.md"`.
7. Give the user the branch name and the PR link.

## Pick up a handed-off task

1. `gh pr checkout <number>`, then read `docs/tasks/<branch>.md`, especially `## Handoff`.
2. Set `Owner` to your login and `Status: in-progress`. Commit, push, and start from the
   handoff's **Next** step.

---
name: create-pr
description: Open or update the pull request for the current branch into main with a short description, after the review skill passes with no hard findings. Turns the task's draft PR into one that's ready for review. Use when work is done, or when the user says "open a PR", "create a PR", "ship it" or "ready for review".
---

1. If you're on `main`, stop and run `claim-task` first. If there are uncommitted changes,
   show the user what they are, then commit them with a clear message.
2. `git fetch origin`. If `origin/main` has moved ahead, run `git merge origin/main` and
   resolve any conflicts with the user. Don't rebase a branch that's already pushed.
3. Run the `review` skill. If it has any hard findings, stop, show them, and fix them only
   if the user asks. Mention judgement findings to the user, but keep them out of the PR.
4. In `docs/tasks/<branch>.md`, set `Status: in-review` and tick the done-when items that
   are met. Commit, then `git push -u origin HEAD`.
5. Write a title (imperative, under 70 characters) and a short body:

   ```markdown
   <1-3 sentences: what changed and why>

   **Task:** docs/tasks/<branch>.md
   **Tested:** <command run and result, or "not tested: <why>">
   **Risk:** <two-way door | one-way door> - <what could break>
   ```

   Add one line naming any new dependency and why it's needed.
6. If the branch already has a PR (`gh pr view --json number,isDraft,url`), update it with
   `gh pr edit --title ... --body ...`, and run `gh pr ready` if it's a draft. Otherwise run
   `gh pr create --base main --title ... --body ...`.
7. Give the user the PR URL.

Never merge the PR and never push to `main`.

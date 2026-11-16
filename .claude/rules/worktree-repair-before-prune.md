---
name: worktree-repair-before-prune
description: After moving or renaming folders that hold git worktrees, run git worktree repair first and list prunable entries before any git worktree prune
metadata:
  type: feedback
---

On 2026-11-03 `git worktree prune` removed the admin records of 6 live demo worktrees (their `.git` files still pointed to the old folder). Nothing was lost (folders and commits intact; records rebuilt from a saved `worktree list --porcelain`), but it was avoidable.

**Why:** prune treats "gitdir points to a missing location" as dead even when the working folder exists at a new path.
**How to apply:** (1) save `git worktree list --porcelain` for every repo first; (2) `git worktree repair <each live path>`; (3) read `git worktree prune -n -v` (dry run) and prune only entries whose folder is really gone and whose HEAD is on a branch or remote (`git branch -a --contains <sha>`); (4) move stray worktrees with `git worktree move`, never by deleting. Related: [[all-work-in-studio-folder]].

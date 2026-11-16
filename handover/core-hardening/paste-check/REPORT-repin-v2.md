# C3b re-pin patch v2 (2026-11-16), written by the lead from the builder's hand-back and evidence-c3e.md
FAILED / OPEN first:
- Not run: PowerShell, wsl.exe, Git Bash, the real n8n scripts. Everything about exit 3 of n8n_kill.py rests on the lead's text (the builder did not read the script).
- The lead must write pastes/P-4b.sh, fill the four placeholder places (final sha full, sha 7, final branch, worktree nlite-fix5 and branch r5; UNVERIFIED 14 and 15).
- Builder's own slip: v1 deleted plan items 12 and 13; v2 restores them.
Result: paste-check/plan-v5-repin-v2.patch replaces plan-v5-repin.patch (never apply both). Apply from the core-hardening folder after plan-v5-fixes.patch. Dry run and real apply rc 0, no fuzz. Syntax checks and stub tests: evidence-c3e.md.
Review state: two fresh reviewers (facts, naive) started; results go to review-repin-v2-*.md.

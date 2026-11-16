# C3b re-pin patch, facts reviewer (egm codebase-details), condensed copy, 2026-11-16
No Blockers, 2 Majors, 6 Nits. Reviewer relied on evidence-c3d.md for dry-runs (rc 0, no fuzz, cmp identical); did not re-run; read gone() by eye.
Checked right: plan lines 2,3,76,120,234,509 match the unpatched plan; patched line numbers (P-2 235, table header 515, intro 513, item 11 561, gone 150-153) consistent; gone() shell is correct (e=$? captured before the echoes; exit 3 test sits before the generic test and returns 1 with GONE-FAIL, so R1 and K5 still match; old test already failed on any non-zero, so no wrong pass); placeholders only at 2,120,235,515, none in a shell span, P-2 STOPs if unfilled; P-4b rationale right (grep -s skips unreadable environ files); 20 rows in strings.txt unchanged.
M1 P-4b (patch l.242): no command and no rule for that case: add "no command supplied = STOP, do not go on to P-5"; P-4b not in the P-3a paste list or section 4 intro l.225; l.428 time estimate (24 min) not updated; says not whether it runs through run.sh as a WSL paste or PowerShell; no result-table row records P-4b pass/fail (K5 covers only GONE-OK).
M2 plan l.19 ("HEAD_PIN stays PROVISIONAL eec6ba4 in all three places") and l.25 (precondition order without P-4b) contradict the patched plan: mark as history or update.
N3 patch l.37 states the cause as fact: word "(per lead: ...)"; 13.1 and 13.3 "on GONE-FAIL use R2": on exit 3 the target n8n may already be gone, R2 is a no-op: add a clause.
N4 RE-PIN line says "three places" but four placeholders (l.515): name the fourth, say cells are filled from regenerated output; diff grep pattern misses `return 3`: add `return`.
N5 nlite-fix5 worktree name is plain text, sourced from old header, not a placeholder: make placeholder or tell lead to confirm.
N6 MUST-NOT list (l.489) names nlite-fix3, fix4 but not fix5: add.
N7 item 11 and header consistent; no leftover old wording.
N8 section 11 final-head cell wording differs ("not re-read here" vs "to be re-read by the lead"): use one.

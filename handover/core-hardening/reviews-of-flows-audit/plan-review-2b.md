# plan-review-2b: egm-implementation-readiness on REVIEW-PLAN v2 (condensed by lead, round 2 of max 3)
Verdict NOT READY. 0 Blocker, 7 Major, 6 Nit. Reviewer read the plan, ORDERS, round 1 files, and TARGET files; ran nothing.
M1 pinned sha 35235ac vs the audit's own snapshot cc449f5: no step says the trees match; no repo/fetch commands named.
M2 reviewers (Read/Grep/Glob only) cannot diff pairs or grep referrers: add an evidence runner (E4) for pair diffs (real-v5 vs film-v5, mf-form vs mf-hook, each CUT-LIST pair) and a referrer grep table.
M3 triggered extension (WRONG adds skipped findings) has no executor, sequence or stop; DRIFT not covered.
M4 E3: no failure branch (F-002 and F-008 both touch build_mainframe.py), no baseline rebuild with no patches, unfilled placeholders, no layout for node/connection diff.
M5 no rule for secrets or personal data copied into evidence (public repo): mask, scan before push.
M6 verdict rubric gaps: 4 DRIFT and 0 WRONG falls in no class; UNVERIFIABLE uncounted; no substance label (HOLDS / DOES NOT HOLD / UNVERIFIED); missed Major effect.
M7 plan breaks its own independence order: take env list taken from FIX-PLAN step 4; build it from A2 + V5-README instead, compare later.
Nits: A2 layout (error output = onError continueErrorOutput / main[1]; save script as evidence-A2-script.py); brief must say EVIDENCE RUNNER, pass citations as a file; FINAL format and stop-rule items (coverage matrix, 13 of 25 plus both Blockers); OPEN is the stated exception to ledger done rule, pipe escaping, UTC and IST; round cap vs security paths; REPORT.md is outside folder (existing practice), scratchpad path may vanish.

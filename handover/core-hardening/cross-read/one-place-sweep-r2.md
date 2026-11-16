# One-place sweep r2 (condensed copy of the sweeper's report), 2026-11-16
Not checked: plan-v10 beyond head and grep hits, v2-v5 READMEs beyond heads, raw logs beyond summary lines, c6 b-e files, steps-edits, v14/v15 sheets. Checklist items must be rechecked after v9 lands.
## Disagreements (failures first)
1. Plan chain has four layers (fixes, repin-v6, gate-rows, then plan-v10 edit list) but LEAD-CHECKLIST:9 and LEAD-FILL:2 name two patches. plan-v10 Edit 2 old text ("Floor about 2 h 51 min clean") is gone after repin-v6 (2 h 52) and gate-rows-v3 (2 h 54); three floor totals (171, 172, 174 min) plus 173 at plan-v10:262. Fix: one PLAN-CHAIN.md (order, plan sha after each step, counts, floor minutes, whether v10 edits go before or after).
2. REPORT.md:5 stale on C3b (board says v8 round 6 clean); C8 "2 majors" (board) vs "4 majors" (REPORT; 2 security + 2 evidence); board cites REPORT-runpy3.md (round 2) as r3 evidence; file-name vs title round numbers are off by one.
3. Board counters: ITEMS_TOTAL 11 vs 14 rows; "7 running" vs 8 rows; C3b evidence column points to v7/r4 files; C13 and C14 have files but no board row.
4. C7b open gaps: REPORT.md:4 says Remove-EC2_x and Remove-S32 "never withheld" as fact; README:67 says "may not match / unchecked"; sources say "described, not fixed". Put full list in v6-extra/DESCRIBE-ONLY-flaky-id-test.md.
5. Superseded results without banner: mutation-lane/REPORT.md ("v2 rerun pending" will never happen), REPORT-runpy3/4 (REPORT-runpy4:3 "not reviewed" but reviews exist), c6-skip-audit/REPORT.md (lane3 "NOT READ" but evidence-lane3-recompute confirmed; REPORT.md:20 old claim without "inside the lease"), patches-ready v2/v3/v4 READMEs and top-level A-01/C-01/G5 patches, paste-check/LEAD-FILL-list.md (v4), old repin and gate-rows patches, plan v5-v9 edit lists, v4/DEAD-MAN-CHECK.md title.
6. run.py S603: REPORT-runpy3:12 "no precedent" vs evidence review "precedent exists"; line numbers drift; cite by function; one dated grep result.
7. Lease/claim wording (plan-v10:458 Text A vs :459 Text B) still undecided; lease seconds 20/30/45/120 across files; "decision 6" means three things (rename claim choice A/B).
8. Port 5690 labelled "take" in repin patches though it is the rehearsal port; take port named nowhere.
9. Backstop 180 vs 189, "13 sends", head de6b574 sourceless.
10. FILL-list:17 skips (b); evidence-c7g section numbers differ (9/13/14); Windows user-name path hard-coded in 14 files.
## Consistent (no action)
Test counts 9418/9413/9491/9514/9391 and arithmetic; C7b patch sha 12e4be6f...; repin-v6 sha 8a83abaa...; plan sha prefix 67a0a195537de875; plan-v10 sha ec922309...; 17 markers on 10 lines and counts 24/10/2/1; flake 1 in about 2,731 runs (ORDERS range 0.015-0.045 percent); kept scope = v5 (G5 + C-01-MINIMAL + dead-man note).
## Q18 question for lead
ANSWER-Q18-lead.md:2 allowed only the rounds already running (run.py r2, C5 v5, C7b fix). run.py r3 and r4 started later; no order found that approves them. Lead to confirm or stop.

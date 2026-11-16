# fix-fixplan60: FIX-PLAN.md, round 60 (fixer; input reviews/fix-plan-reader-r60.md)

Not run: no step of the plan was executed; every new command was only syntax-tested with `bash -n` (all 18 passed). Nothing was committed.

| Item | Status | What changed / why |
|---|---|---|
| B1 command copies | fixed | Steps 0, 3, 3a, 4 (take_check line), 4c, 4d (readiness), 5, 6, 7, 8a, 9 (13 (e)), 14, 17 now point to RUNBOOK with the exact printed pass words (4c: `start-syntax-ok`, not `bash-n-ok`; 4d: `n8n-ready`, not `readiness HTTP 200`). Kept: Step 0a shas.env, the Step 7 alert-address test (RUNBOOK step 10 lacks it: needs lead to copy it) |
| M2 order | fixed | Step 4d and slot paragraph say "RUN FIX-PLAN STEP 5 FIRST"; order is time, not number |
| B3 BLOCKED / self-checking | fixed | one BLOCKED table (item, due UTC/IST, pass word); section Self-checking pass lines (11 items) |
| M4, M5 | fixed | ACCEPTED = 2 (measured by one read-only take_check run on real-v5); per-file node:connection counts 15:14, 15:14, 10:9, 20:26 |
| M6-M9, M11 | fixed | Steps 5, 6, 7, 8a, 17 have self-checking lines |
| M10 | fixed | allowed-hit list written into Step on F-007 (`REPORT.md:49` only after F-004) |
| M12 | fixed | roles table, names are LEAD FILLS / LEAD DECIDES |
| M13 | fixed | 9 + 3 = 12 contacts and the two positive controls reconciled (text, Step 10c) |
| M14 | fixed | one gated Wednesday table with arithmetic (07:48, 09:37, 10:07) |
| M15 | fixed | section of the six time statements |
| M16 | fixed | one three-file list in Step 4c |
| M17 | fixed | interactive vs non-interactive caller rule (Step 0a and slot paragraph) |
| M18 | fixed | step-number rule (rule 3 of "how steps map"); bare numbers prefixed in steps, rules, table cells of lines 181-228 |
| M19 | fixed | "More words" glossary |
| M20 | needs lead | cut-off written as AUDIT PROPOSAL (06:37Z, 12:07 IST, from the Clock block arithmetic); the lead decides |
| Own findings, lines 181-228 | fixed | rows 201/202 (first use vs due), 217 (`decision 4` vs `decision 1`), 220 (meta text removed), bare step numbers |

## Needs lead
- Copy the self-checking lines and the alert-address test into RUNBOOK (RUNBOOK was not touched).
- `IDLOG` and `SUB_ID` need Placeholder-table rows in TAKE-CHECKLIST.md (other fixer's file).
- Human names (roles table); the R3 cut-off; Case B against the 12:00Z recording-ready rule; one rehearsal or two.
- The line "Q31 item 63" pass word `values-loop-ok`, mailbox words `mail-count-ok`, `positive-control-ok`, `row-state-done` are AUDIT PROPOSALS.
- Step 6/7 `placeholder-control-ok` and `filled-greps-clean` are asked of RUNBOOK step 10; no standalone command was written for them.

## Needs clock-block change
None. `sed -n 37,84p FIX-PLAN.md | md5sum` = dfd844ddb7085082534434075814e131; lines 1-36 still 36 lines. The Clock block's "ONCE on Tuesday" wording for the positive control is explained outside the block.

## Checks (last lines)
- check_refs: PASS 5190 references; check_names: PASS 655 rows; check_counts: PASS 52 files / 655 nodes
- check_secrets: FAIL 3 hits, all in reviews-of-core-patches/fix-patchcopies25.md lines 14-16 (64-character strings; a file I did not touch, unchanged by me: not fixed, outside my file); no hit in FIX-PLAN.md
- `ruff format --check .` in handover/flows-audit: 1101 files already formatted (from the repo root it reported 93 files before any change; outside my scope)

# Evidence gates 2 (raw, no judgement)

HEAD at start of run: e99cec5cd87f3b008915a65219687453dc385aa6; HEAD after: e99cec5cd87f3b008915a65219687453dc385aa6.
Note: an earlier `git rev-parse HEAD` a few minutes before the run printed 8a3043a5d70445b5ac0274c1394b96abbb8279ef, so HEAD moved before the run began (not during it). No file under handover/flows-audit changed during the run (find -newer check empty).

| Command | rc | Raw result |
|---|---|---|
| tools/check_refs.py | 0 | PASS 5166 references |
| tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md | 0 | total rows: 185; RESULT: PASS |
| tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md | 0 | paste strings in RW: 136, found word for word in CT: 136, not found 0 |
| tools/count_findings.py | 0 | rows 45 unique 45; Blocker 5, Major 5, Nit 35 |
| reviews-of-core-patches/count_review.py (no args) | 1 | IndexError, needs a path argument |
| count_review.py reviews-of-core-patches/REVIEW.md | 0 | rows 28; Nit 11, Minor 13, Major 4; DECLINE 3, PROPOSE FIX 25 |
| claims-count.py (no args) | 1 | IndexError, needs a path argument |
| claims-count.py CLAIMS-TABLE.md | 0 | total 327, ids 327 unique 327, offenders 0, to-do rows 87 (UNSUPPORTED 27, OVERSTATED 62, SUPPORTED 119, UNTRACED 49, RELAYED-ONLY 70) |
| ruff format --check handover/flows-audit (from repo root) | 0 | 628 files already formatted |
| diff FIX-PLAN.md 14-47 vs TAKE-CHECKLIST.md 8-41 | 0 | no output (identical) |

Counting script for REVIEW.md: /home/user/hadavin-sdk/handover/flows-audit/reviews-of-core-patches/count_review.py

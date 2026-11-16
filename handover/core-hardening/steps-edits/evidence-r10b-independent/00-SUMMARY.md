# Evidence r10b independent (EVIDENCE RUNNER: runs and records, does not judge)
Run 2026-11-16 15:5x UTC (21:2x IST). No existing file edited; no commits; no spend. Scratch copies in the session scratchpad. __pycache__ removed from steps-edits (scripts run with -B -I).

## Failures first
- Failures of EDITS.md found by my own checker: 0 (exit 0, `02-main-run-raw.txt`).
- verify10b.py on a scratch copy: exit 0, "FAILURES 0", its 25 own negative controls caught (`05-verify10b-on-scratch-copy-raw.txt`).
- My first two checker runs failed because of MY parser bugs (headings starting with "## " inside fenced blocks ended a row early; the removed ids E-10/E-35 counted as unknown). Fixed in my script, not in EDITS.md. Final script is the one saved here.
- Differences between my reading and verify10b (not failures of EDITS.md):
  * Naive "apply every NEW block": my script applies 14 HOLD-labelled blocks (13 rows: the 12 Hold rows, with E-13 twice, plus the Hold text N of Apply-now row E-36). The second E-36 block FAILS on a naive run because text W already replaced the OLD text (E-36 W then N: "old count 0"). verify10b counts 53 rows applied because it skips rows with several NEW blocks. So: a script that applies every NEW block WOULD apply the HOLD blocks; the only protection is the label `[HOLD ...: DO NOT APPLY]` and the header status.
  * Lone times: no lone UTC time. Two lone IST times (23:59 IST, "window ends 2026-11-23 23:59 IST"): line 288 is inside E-12's OLD block (a quote of the input), line 306 is E-12's Why quoting it. Not in any NEW block.
- Not checked: whether the NEW texts are good wording or correct in fact; whether the inputs' other lines are right; plan-wp6-resmoke-v5.md is in inputs/ but no row refers to it (0 rows); a stale `mutation-lane/evidence-r10/frozen/__pycache__` exists elsewhere in core-hardening (not mine, left alone).

## Check results (raw files in this folder)
1. sha/lines: before and after `7d4a0e6861eb...c243c`, 886 lines, unchanged (`01-sha-before.txt`, `01-sha-after.txt`). Matches expected.
2. OLD texts (`02-main-run-raw.txt`, lines "OLD ..."): 55 OLD blocks in 54 rows (E-13 has two). All 55 occur exactly once in their input file, at the stated line (or "and" line). Missing 0, repeated 0, overlapping 0. Files: OWNER-STEPS 35 rows, AGENT-SCOPE 15, DECISION-one-store 4.
3. Apply: all 42 non-HOLD NEW blocks apply cleanly in row order to scratch copies (0 failures). Results are byte-identical to the builder's `scratch-apply10b` for all 3 files (`05b-compare-apply-now-with-builder.txt`). No "[HOLD"/"DO NOT APPLY" text in the apply-now copies. Naive apply-all: see above.
4. Times and dates: 42 UTC/IST pairs, all IST = UTC + 5:30 (18:29/23:59, 18:19/23:49, 18:14/23:44, 18:04/23:34). 19 weekday+date strings all correct for 2026 (Mon 16 Nov, Wed 18 Nov, Mon 23 Nov). ISO dates all real. Lone UTC: none. Lone IST: 2 (above).
5. Counts: 54 rows; Apply now 42; Hold 12; ids E-01..E-56 without E-10/E-35, unique, continuous; id lists in the Counts text equal the headers; index table 54 rows matches headers (file, line, status, gate); NOT DECIDED items 1-14 continuous; confirmation letters defined a-j without gaps, used: a, b, c, h (and Cb); gates G1-G5 defined and every gate used in a header/label is defined; per-gate row lists equal headers (G1, G3, G4, G5); E-10/E-35 only mentioned as removed (lines 42, 45, 76), never in a block or the index; 14 HOLD-labelled NEW blocks.
6. Negative controls (`04_negative_controls.py`, `04-negative-controls-summary.txt`, per-case raw in `04-negative-controls-raw/`): baseline exit 0; 26 of 26 mutations make the checker exit 1 (old text changed/repeated/overlapping, stated line changed, UTC time, IST time, gate letter in header, gate definition renamed, HOLD label removed, HOLD gate mismatch, row set to Hold without gate, weekday wrong, impossible ISO date, count texts, duplicate id, confirmation letter gap, ND number, odd fence, index line, secret-shaped sk-/AKIA/personal e-mail (built from parts), banned string (read at run time), lone UTC time, input file changed). Not caught: none.
7. Banned vendor strings (`06-banned-scan-counts.txt`, list read at run time, 10 strings): 600 files scanned in steps-edits (including this folder), 0 files with a hit, 0 occurrences each. Strings not printed.

## Files
check_r10b.py (my checker), 04_negative_controls.py, 06_banned_scan.py, 02-main-run-raw.txt, 04-*, 05-*, 05b-*, 06-*, 01-*.
R-numbers cited: none looked up (evidence runner; no bible lookup done).

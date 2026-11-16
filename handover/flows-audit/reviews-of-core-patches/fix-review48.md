# fix-review48: fixer round 48 for `REVIEW.md` (security path, no round cap)

Static session: nothing was run except the five checks below and `count_review.py`. Only `REVIEW.md` was edited (plus this report and `checkpoint-r48.md`). Backup: `/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/r48/REVIEW.bak`. Edit scripts (unique names, same folder): `edit48a.py` to `edit48e.py` (each edit asserts its old text occurs exactly once; 11 + 4 + 35 + 34 + 3 = 87 edits).

## Gaps first
- Everything new in Z1 part (4A), the nonce rule, the signature record and the working values is a PROPOSAL, nothing built, UNVERIFIED.
- M13 (deselected set, the encoding probe) cannot be closed in a static session. Found while checking: the probe file named in `../heavy-test-lane/SUMMARY.md:9` does not exist in this checkout, so the guards-after-fix run could not have read it. Next step is written in the file: `pytest --collect-only -q` on both trees (an evidence runner; LEAD DECIDES the time, default end of 2026-11-18 UTC / 05:30 IST on 2026-11-19), and one full-suite run on the final head.
- M14: the checks behind "checked and correct" at Z1, Z3, Z7 (batch 43 reads of the batch 42 text) cannot be repeated, the old text is gone. The claims were reworded as "read and judged correct, no saved output, UNVERIFIED as a record"; none was upgraded.
- Reader line numbers were offset by about 4 to 19 lines from the file; every item was matched by its words. Nothing was contested as wrong; two reader claims were checked and CONFIRMED by arithmetic (M1: per-item sum 47 + 26 = 73, total 112).
- Not checked: whether the two new start tests (aa), (ab) fit the login and log designs of the other Z items beyond reading; no reviewer has read part (4A).

## Counts (sums shown in the file, line "COUNT, set in batch 44")
- Z block tests before this round: 73 by the reader and by my recount (Z1 26, Z2 5, Z3 3, Z4 2, Z5 8, Z6 13, Z7 3, Z8 3, Z9 1, Z10 2, Z12 3, Z14 1, Z15 1, Z17 2). Added (aa) and (ab) to Z1: Z1 28, Z block 28+5+3+2+8+13+3+3+1+2+3+1+1+2 = 75, all 39 + 75 = 114. Header "NEGATIVE TESTS (28 ...)": 25 refusals + 3 starts ((l), (aa), (ab)).
- Open questions: 10 YES + 13 NO + 1 MIXED (OL-24) = 24 (old text said 10 and 14; OL-24 now MIXED, honest correction).
- `python3 -I count_review.py REVIEW.md`: rows 28, Major 4 / Minor 13 / Nit 11, PROPOSE FIX 25 / DECLINE 3. Unchanged.
- Lines 5 and 77 hash e6db355c and 7f8da2ce: unchanged.

## Finding to change
| finding | change |
|---|---|
| r47b B1 start sequence | New Z1 part (4A): one table of cases 1 to 7 (L = log counter, H = handed in, S = state file) and who hands in which (B): deployer hands the CURRENT (B) at every start; the PREVIOUS (B) only with a (B) one counter higher; same counter needs no previous file on any host (wiped, lagging or not); lower, equal-with-other-hash or more than one higher refused; lagging host gets the current (B), not the missed files. (4)(a), (4)(c), Z2 compare rule and both Z17 sentences now point to (4A). Tests (aa) wiped host starts, (ab) lagging host starts and older file refused. |
| M1 counts | Recounted with sums; 75 and 114; header 28; History line 789 annotated. Re-run rule made concrete. |
| M2 process kind | Z2 says kind is fixed by pinned code, (B) holds a copy that must equal it; "PROTECT-ONLY" replaced by the Z1 (7) words; word map added; Z3 sentence fixed. |
| M3 release key alone / (A) | Cited Z1 part (9) and the TIGHTENING list (minimum build generation); test idea named; (A) classified (ordinary release, release key alone) with the stolen-key reasoning. |
| M4 alarm fields | Release entry gets a SIGNATURE RECORD (fingerprints, number 1 or 2); Z6 alarm and its test use it; limit (self-reported) stated. |
| M5 second log | Z1 (8) default and Z6 reworded to "no signed pilot note until second log or written acceptance"; LOG OUTAGE LIMIT default 4 hours (LEAD DECIDES, due end of 2026-11-19 UTC). |
| M6 Z11 | One default rule: demos tables stand, pilot/production recommended default; old (4) clause marked superseded; OL-11 and criterion (7) text aligned. |
| M7 met wording | Z13 and O: no criterion is "met" at all before (8) exists; "met (advisory, one person)" only after. |
| M8 defaults | N 15 min, max run 24 h, start-entry limit 26 h, nonce 10 min; all in OL-22 (lead to confirm). |
| M9 nonce | Nonce rule: 128 bits, in memory of the issuing process only, one use, 10 minutes; captured pair refused; test (v) widened. |
| M10 names and counts | Criterion (9) login list points to LOGIN AND IDENTITY COUNT (18 by its own sum), old names mapped, "18" reason withdrawn, `fix-review40.md` described as a log. |
| M11 verifier person dates | One sitting 2026-11-18 12:00 UTC (17:30 IST) in answer order (Q1, 25, 5-K, 7, 29, 26, 27); row 26 trigger and key-table question (3) dated. |
| M12 "Q1" | Meaning fixed (Question Q1 only); key-table questions labelled and mapped to OL-5/6/7; Z16 reworded. |
| M13, M14 | See gaps; claims reworded; "not a defect" and "not evidence of different trees" withdrawn. |
| r47b minors | Re-run rule, Z2 "raised", Z16 builder time, acceptance-note date, trigger list, X-5.1 self-reference, 5-K and Decision 25 due dates and defaults, Decision 9 combinations default, Decision 23b owner/date, "5 scratch-tree failures" defined, OL numbering added in Z4/Z10. |
| r47c B1 | Words defined at the head of the OL list (criterion, hold, chain, true gate, note). |
| r47c M2 to M11 | M2 header/"Closed" bullet; M3 OL-10 machine (LEAD DECIDES); M4 OL-15 time and default; M5 OL-11 default; M6 OL-22 default and plain-word list; M7 OL-3/OL-4 labelled (a)/(b); M8 OL-18 time; M9 OL-7 sitting; M10 OL-19 22:00 UTC / 03:30 IST on 2026-11-17 and OL-21 time; M11 OL-24 first four named, MIXED, overlaps stated. r47c minors: "41 cases" reworded (41 or 42 depending on reading, unverified), glosses for evidence runner, heavy lane, facts reviewer, "directly below", "no cycle" now "by hand". |

## LEAD DECIDES (9 places in the file)
Sitting time (default 2026-11-18 12:00 UTC / 17:30 IST); builder name (default none; 2026-11-16 22:00 UTC / 03:30 IST on 11-17, then 2026-11-17 12:00 UTC); log outage limit (default 4 hours; end of 2026-11-19 UTC); OL-10 machine (default the studio head's signing machine; end of 2026-11-20 UTC); collect-only run time; Decision 23b naming; plus "lead to confirm" values in OL-22.

## Check output (last lines, from handover/flows-audit)
ruff format --check .: `1040 files already formatted` (rc 0)
check_refs.py: `PASS 5193 references` (rc 0)
check_names.py: `PASS 655 rows` (rc 0)
check_secrets.py: `PASS 0 hits in 2915 files` (rc 0)
check_counts.py: `PASS 52 files / 655 nodes` (rc 0)

EGM: this is the fixer step of the sequence; the result review of these edits is the lead's. R-numbers: bible not read in this session (static, owner brief only); rules applied from CLAUDE.md and `.claude/rules`.

# evidence-r3 (EVIDENCE RUNNER, raw output, no judgement), 2026-11-16 UTC (IST = UTC+5:30)

## FAILURES / SURPRISES FIRST
- Mutation (item 4): 20 mutants drawn with seed 20261116; 4 produced a Python syntax error (the "for x in" token swap), so only 16 ran: 13 killed, 3 SURVIVED (mut6 line 608, mut12 line 964, mut16 line 1149; details below). Mutation operators and the sampling are mine (operator swaps on non-docstring code lines), not the fixer's.
- Item 6: raw/pristine-no-baseline.txt was NOT regenerated: mtime 2026-11-16 09:32:15 UTC, 6460 bytes, before the round-3 files (10:11). run_all.sh does not write it (no reference in run_all.sh). Its content reflects an older checker.
- Item 3: round-2 checker = `git show fe7e79696:handover/flows-audit/flow-check/check_flows.py` (09:38 commit; the 10:10 "board" commit 5bd332c67 holds round 3). Result 479 / 59 (matches claim). The 09:36 board commit 49a527801 version gives 410 / 128.
- run_all.sh overwrote files in raw/ and selftest-output/ (its normal behaviour); nothing else touched. No commit.
- No noqa / nosec / type: ignore / pragma in check_flows.py or selftest.py (grep empty). bandit reports 0 skipped; 1 Low issue (below -ll).
- Note: ruff format counted "20 files already formatted" (fix-f8-r3.md says 18; folder now has 2 more .py/.md-free files or the count differs; not investigated).

## (1) bash run_all.sh: exit 0 (4.7 s wall)
Tail (full text: scratchpad runall.txt):
Known open problems: 4
exit=1
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 4
exit=1
[selftest exit=0] SELFTEST: 538 as expected, 0 not as expected, 52 skipped (not applicable)
run_all exit status: 0
placeholder ids: 8 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS: 4 webhook(s) without auth, 4 $env node(s)

real	0m4.741s
user	0m4.092s
sys	0m0.677s

Self-test line: `SELFTEST: 538 as expected, 0 not as expected, 52 skipped (not applicable)` (claim 538/0/52: matches).

## (2) lint (repo root, uv run --all-extras --group test)
All checks passed!
rc=0
20 files already formatted
rc=0
Run started:2026-11-16 10:12:27.772661+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 2838
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 1
		High: 0
Files skipped (0):
rc=0
grep noqa|nosec|type: *ignore|pragma on check_flows.py and selftest.py: no matches.

## (3) round-2 checker (fe7e79696) against the current selftest.py (scratch copy)
SELFTEST: 479 as expected, 59 not as expected, 52 skipped (not applicable)
lines mentioning not-as-expected: 1

## (4) mutation, seed 20261116, 523 candidate lines, 20 sampled; each on a scratch copy (check_flows.py mutated + selftest.py), self-test run with real-v5, /tmp/fc8/g/real, film-v5; KILLED = self-test exit nonzero
candidates=523
mut1 line 120: 'append(' -> 'extend(' : KILLED | SELFTEST: 537 as expected, 1 not as expected, 52 skipped (not applicable) | src: KNOWN.append(f"{where}: {msg}")
mut2 line 169: ' in ' -> ' not in ' : SYNTAXERR-skipped |  | src: for v in o:
mut3 line 233: ' in ' -> ' not in ' : SYNTAXERR-skipped |  | src: for n in nodes:
mut4 line 574: ' == ' -> ' != ' : KILLED | SELFTEST: 527 as expected, 11 not as expected, 52 skipped (not applicable) | src: short == "httpRequest"
mut5 line 606: ' or ' -> ' and ' : KILLED | SELFTEST: 15 as expected, 523 not as expected, 52 skipped (not applicable) | src: for k, v in (cr or {}).items():
mut6 line 608: ' in ' -> ' not in ' : SURVIVED | SELFTEST: 538 as expected, 0 not as expected, 52 skipped (not applicable) | src: if idv and any(p in idv for p in PLACEHOLDERS):
mut7 line 634: ' in ' -> ' not in ' : KILLED | SELFTEST: 15 as expected, 523 not as expected, 52 skipped (not applicable) | src: if au in ("none", None, ""):
mut8 line 712: ' != ' -> ' == ' : KILLED | SELFTEST: 533 as expected, 5 not as expected, 52 skipped (not applicable) | src: and ref != n["name"]
mut9 line 729: ' or ' -> ' and ' : KILLED | SELFTEST: 533 as expected, 5 not as expected, 52 skipped (not applicable) | src: and str((n.get("parameters") or {}).get("method", "GET")).upper() != "GET"
mut10 line 870: ' or ' -> ' and ' : KILLED | SELFTEST: 533 as expected, 5 not as expected, 52 skipped (not applicable) | src: (pr.get("rules") or {}).get("values") or (pr.get("rules") or {}).get("rules") or []
mut11 line 899: 'if not ' -> 'if ' : KILLED | SELFTEST: 33 as expected, 505 not as expected, 52 skipped (not applicable) | src: and [i for i in (0, 1) if not (i < len(bo) and bo[i])] == miss
mut12 line 964: 'if not ' -> 'if ' : SURVIVED | SELFTEST: 538 as expected, 0 not as expected, 52 skipped (not applicable) | src: if not where:
mut13 line 985: ' in ' -> ' not in ' : SYNTAXERR-skipped |  | src: for k in sorted(set(a) | set(b)):
mut14 line 1044: ' != ' -> ' == ' : KILLED | SELFTEST: 537 as expected, 1 not as expected, 52 skipped (not applicable) | src: if d["connections"].get(nm) != want:
mut15 line 1060: ' or ' -> ' and ' : KILLED | SELFTEST: 537 as expected, 1 not as expected, 52 skipped (not applicable) | src: conds = get(d, "KeyOk")["parameters"].get("conditions", {}).get("conditions") or []
mut16 line 1149: 'append(' -> 'extend(' : SURVIVED | SELFTEST: 538 as expected, 0 not as expected, 52 skipped (not applicable) | src: out.append("  node CHANGED {}: {}".format(nm, ", ".join(ch)))
mut17 line 1152: ' or ' -> ' and ' : KILLED | SELFTEST: 537 as expected, 1 not as expected, 52 skipped (not applicable) | src: if pref is None or c.split(" (")[0] not in pref:
mut18 line 1305: ' in ' -> ' not in ' : SYNTAXERR-skipped |  | src: for fn in dfiles:
mut19 line 1311: ' is None' -> ' is not None' : KILLED | SELFTEST: 48 as expected, 490 not as expected, 52 skipped (not applicable) | src: if d is None:
mut20 line 1332: 'if not ' -> 'if ' : KILLED | SELFTEST: 500 as expected, 38 not as expected, 52 skipped (not applicable) | src: if not r:

Script: scratchpad mut.py (operator swaps ==/!=, and/or, comparisons, in/not in, if not, is None, return True/False, append/extend).

## (5) checker on committed real-v5 (pristine, --baseline itself, run_all flags): exit 0
RESULT: 0 FAIL, 18 WARN
OPEN LEAD DECISIONS: 2 webhook(s) without auth, 2 $env node(s)  (exit 0 does NOT mean authentication was checked)
Known open problems: 6
Final line of the run_all.sh run: OPEN LEAD DECISIONS: 4 webhook(s) without auth, 4 $env node(s) (real + film; real alone: 2 and 2).
Folders: handover/demo/n8n-flows-real-v5 and n8n-flows-film-v5 (also handover/flows-audit/tools/scratch/real-v5, not used).

## (6) raw/pristine-no-baseline.txt
mtime 2026-11-16 09:32:15.868109574 +0000 size 6460
raw/pristine.txt mtime 2026-11-16 10:12:19.464252450

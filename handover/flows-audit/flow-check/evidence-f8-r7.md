# evidence-f8-r7 (EVIDENCE RUNNER; raw output in raw-e7/, nothing judged)
Head: files as of 2026-11-16 ~11:10 UTC (check_flows.py 1848 lines). Only new files: this file, raw-e7/, raw-e7b/. Mutants ran on copies in /tmp/e7m (live files untouched). Side effect: selftest.py and run_all.sh rewrite selftest-output/ (generated output) in the live folder when run without FC_OUT; that happened in the py3.11/3.12/3.13 runs.

## Summary (failures first)
SURVIVING MUTANTS (run_all rc=0): M10 (fixer says equivalent), N04 (check_flows.py:1200), N11 (check_flows.py:604).
Ruff version: installed 0.16.9, repo pin ruff==0.17.1 (pyproject.toml:50) -> MISMATCH, results are with 0.16.9 only.
Everything else: see tables.

## Gates (each its own rc)
| command | rc | note |
|---|---|---|
| bash run_all.sh (RUN_ALL_RAW=raw-e7) | 0 | SELFTEST 662 ok, 0 not, 62 skipped; take_check exit=0 none missing; also 2nd run with fixed workdir raw-e7b rc=0 |
| ruff check . (repo config) | 0 | |
| ruff format --check . | 0 | 33 files already formatted (fixer said 32) |
| bandit -ll -c pyproject.toml check_flows.py selftest.py | 0 | 1 Low / Medium-confidence issue listed in totals (below -ll threshold), 0 Medium, 0 High |
| python3 -I selftest.py REAL PATCHED FILM (3.13) | 0 | 662/0/62. First attempt without args gave rc=2 (usage) - needs the 3 folder args |
| selftest py3.11 / py3.12 / py3.13 | 0 / 0 / 0 | all 662 ok, 0 not, 62 skipped |

## Mutants (run_all.sh on /tmp copy; killed = rc!=0)
| id | file:line | change | rc | result | caught by |
|---|---|---|---|---|---|
| M10 | take_check.sh:64 | drop `\|^WARN accept-no-save` alternative | 0 | SURVIVED | (fixer: equivalent, not verified by me) |
| N04 | check_flows.py:1200 | `ncon != expect` -> `ncon < expect` | 0 | SURVIVED | none (more connections than expected not detected) |
| N11 | check_flows.py:604 | `if not blocks or not all(` -> `and` | 0 | SURVIVED | none |
| M2 | check_flows.py:1214 | blanket accept-no-save | 1 | killed | selftest 661/1 |
| M3 | check_flows.py:1214 | accept by prefix mf- | 1 | killed | selftest 661/1 |
| M7 | check_flows.py:1492 | F008 manual check off | 1 | killed | selftest 660/2 |
| M12 | take_check.sh:86 | FINAL always prints 0 | 1 | killed | run_all take lines |
| TCMISS | run_all.sh:76 | TCMISS="" init removed | 1 | killed | "unbound variable" crash seen by nested test |
| N01 | check_flows.py:1835 | return 0 always | 1 | killed | 205/457 |
| N02 | check_flows.py:1835 | exit 1 only if >1 FAIL | 1 | killed | 300/362 |
| N03 | check_flows.py:1198 | node count != -> < | 1 | killed | 657/5 |
| N05 | check_flows.py:1489 | F008 `!= want` -> `==` | 1 | killed | 640/22 |
| N06 | check_flows.py:1492 | `is not want_manual` -> `is` | 1 | killed | 640/22 |
| N07 | check_flows.py:1741 | file-list check off | 1 | killed | 656/6 |
| N08 | check_flows.py:1210 | saveManual `is False` -> `is True` | 1 | killed | 657/5 |
| N09 | check_flows.py:1208 | `== "none"` -> `== "all"` | 1 | killed | 657/5 |
| N10 | check_flows.py:158 | fail() no longer records | 1 | killed | 204/458 |
| N12 | check_flows.py:423 | `miss and not absent` -> `miss and absent` | 1 | killed | 658/4 |
| N13 | check_flows.py:416 | missing-table WARN off | 1 | killed | 660/2 |
| N14 | check_flows.py:231 | SQL checked==0 -> != 0 | 1 | killed | 659/3 |
| N15 | check_flows.py:1162 | duplicate-name check off | 1 | killed | 657/5 |
| N16 | check_flows.py:390 | `nxt != "("` -> `==` | 1 | killed | 657/5 |
Totals: 6 required mutants: 5 killed, 1 survived (M10). 16 new mutants (N01-N16; 15 asked, I ran 16): 14 killed, 2 survived (N04, N11).
Mutant definitions: raw-e7/mutants/mk.py; outputs raw-e7/mutants/*.out.

## Hostile inputs (checker `python3 -I check_flows.py DIR`, and take_check.sh via TAKE_CHECK_FLOWS)
| input | checker rc | traceback | take_check rc |
|---|---|---|---|
| empty folder | 1 | 0 | 1 |
| non-UTF8 flow file | 1 | 0 | 1 |
| 60 MB file | 1 | 0 | not run |
| folder name with spaces | 1 | 0 | 4 |
| take flows missing (only recovery) | 1 | 0 | 1 |
| invalid JSON | 1 | 0 | not run |
| 100000-deep nested list | 1 | 0 | not run |
| nonexistent path | 1 | 0 | 1 |
| no args | 2 (usage) | 0 | - |
| file given as folder | 1 | 0 | - |
Not checked: whether rc=1 is for the right reason in each case (outputs in raw-e7/hostile/). Nothing ran in n8n.

# Round 16 independent evidence (EVIDENCE RUNNER; records, does not judge)
Run: 17:44 to 17:56 UTC = 23:14 to 23:26 IST on Mon 16 Nov 2026. Input: `EDITS.md` (copy: `EDITS.orig.md`, byte-identical to the live file, checked with cmp). No commit, no push, no spend, no secret.

## 1. Failures and deviations first
| # | What | Detail |
|---|---|---|
| D1 | My own checker flags 1 item on the builder's EDITS.md | `mychk16.py` code E1: the Appendix K intro says "...key steps A to K in row E-48". An internal row code sits in a block that is meant for the owner's sheet. Low severity; it is the only FAIL of my checker on the unmutated file (counted as baseline in the mutation runs). |
| D2 | 6 of 14 fresh mutations are caught by NEITHER checker | B03 shred check (2) loses "no space"; B04 appendix K-A says "20 minutes between" instead of 10; B05 step 21 heading changed to a consistent 18:21 UTC = 23:51 IST pair; B08 sentence "The assistant never opens the key file" deleted; B09 D.3 "no reply counts as `more takes`" turned into `no more takes` (changes the safe default); B10 key step K "revoke the key at that time anyway" turned into "wait for the take". B09 and B10 are semantic safety reversals. |
| D3 | Honest limit of my own result | First pass of my checker on the 60-mutation list: 53 caught, 5 caught by neither. I then tuned the checker (frozen counts of key times in E-48, step B list scoped, key step letter range A-Z) and re-ran: 60 of 60. That 60/60 is tuned on that list and is not independent. The batch of 14 fresh mutations (written after the tuning, run once) is the fair comparison: builder 8, mine 5. |
| D4 | Builder's checker misses 15 of the 60 first-batch mutations | See section 4. Nothing it must catch by its own claim is outside the list of its 161 controls, but these are real gaps (for example an absolute path, an `ORD:` code, a missing `not sure` reply option, a dropped "do not shred part (a) while a take runs"). |
| D5 | Not run by me | No click path, no clipboard check, no live take. The builder's `verify16.py` negative controls (161) were run as part of its normal run, not re-planted by me. |

## 2. Builder scripts on copies (task item 1)
| Item | Expected | Observed (raw: `build.log`, `verify.log`) |
|---|---|---|
| `build-r16.py` on a copy of `EDITS.round15.md` | 0 anchor errors | `written 1056 lines`; output cmp-identical to the live EDITS.md |
| `verify16.py` rows | 60 | 60 (`rows parsed 60`) |
| Apply now / Hold | 48 / 12 | 48 / 12 |
| FAILURES | 0 | `FAILURES 0` |
| Negative controls | 161 caught | 161 `NEG` lines, 161 contain "caught", 0 "NOT CAUGHT" |
| `verify16.py` on r15 text (`verify-on-r15.log`) | fails | 45 FAIL lines, exit code 1 |
| Old texts / overlaps | n/a | 61 old texts, 0 overlaps |
| UTC=IST pairs / weekday-date pairs / banned / secret | n/a | 146 / 69 / 0 of 10 / 0 (builder's own numbers; my counts below match 146 and 69) |

## 3. My own independent checker (`mychk16.py`, written without reading verify16's logic; items in task 2)
| Check | Result on EDITS.md |
|---|---|
| UTC = IST + 5:30, with seconds | 146 pairs, 10 with seconds, 0 wrong; also loose forms and an UTC time with no IST partner (new blocks only) |
| Weekday-date pairs (Nov 2026: Mon 16, Wed 18, Sun 22, Mon 23, Wed 25) | 69 pairs, 0 wrong. The sheet text uses Mon 23 (44 times), Wed 18 (20), Mon 16 (5); Sun 22 and Wed 25 do not appear |
| Cross-references | key steps A to K all defined; D.1 to D.5 and G.2 defined; every "appendix K-x" exists (A, C, D, F, G, H, I); "Detail" letter equals its key step; every E-nn named exists (E-10 and E-35 are removed ids); gates and ND numbers in range; card numbered 1 to 7: 0 failures |
| Absolute paths and internal codes in owner text (new blocks of OWNER rows + appendix K) | only D1 above |
| Secret-shaped strings (sk- incl. hyphenated, AKIA other than the example, ghp_, xox, PEM, JWT, long hex/base64, password=, non-example e-mail) | 0 |
| Banned strings (list read at run time from the test file, counts only) | 0 of 10 in EDITS.md and in every r16 script, note and output file (counts per file in the run log) |
| OLD text occurs once in its input file, on the stated line | 0 failures |
| Semantic order and clauses: card order (revoke, shred a/b, items 2/4, item 5, shred c/d, list, item 1), exact-address delete clause in E-04, E-42, E-62, five shred checks in order, 4 cases of D.2, alarms and names, margin 18:00:00 + 1:00 + 14:20 = 18:15:20 UTC = 23:45:20 IST, 3 min 40 s | 0 failures |

## 4. Mutation results (task 3). Caught = the FAIL lines differ from the unmutated baseline
Batch A: 60 planted (`mutate16.py`, `mut-results.json`, `mut-out.txt`). Batch B: 14 planted after tuning (`mutate16B.py`, `mut-results-B.json`, `mut-out-B.txt`).
| | planted | verify16 catches | mychk16 catches | neither |
|---|---|---|---|---|
| Batch A | 60 | 45 | 60 (53 before tuning, see D3) | 0 (5 before tuning) |
| Batch B (fresh) | 14 | 8 | 5 | 6 |
| Total | 74 | 53 | 65 | 6 |

Batch A mutations NOT caught by verify16 (15): 18 appendix ref K-D to K-E; 23 absolute path in owner text; 25 `ORD:` code; 26 `DEC:` code; 34 `key gone, no more decisions` dropped from the step B word list; 37 spending window end moved to 18:19 (pair kept); 40 reply option `not sure` dropped in key step F; 41 "Only `yes` together with `different key`" cut to "Only `yes`"; 43 `please stop looking` dropped from step B; 45 "at least 20 minutes" to "2 minutes"; 48 "do not shred part (a) while a take is running" deleted in key step G; 51 Why line of E-62 removed; 53 UNVERIFIED removed in key step K; 54 "Only your own typed messages count (key step B)" removed; 60 "it is at 18:19" in card item 1 changed to 18:29 (pair kept).
Batch B not caught by mychk16 (9): B02 route B recommended to A; B03; B04; B05; B08; B09; B10; B13 screenshot crop clause dropped; B14 take-folder prefix "followed by `/`" dropped. Of these, B02, B13 and B14 are caught by verify16; B03, B04, B05, B08, B09 and B10 by neither.
Caught by both in both batches: IST swaps (4 kinds), seconds pair, address clause dropped in E-04 and E-62, E-42 address changed, step A and I deadline moved with the pair kept, step A pair broken, card order swap (shred after item 1), key-shaped strings (sk-ant, sk-proj hyphenated, AKIA, ghp_), personal e-mail, banned string, broken key-step reference, broken E-ref, wrong weekday (two), year 2027, shred-rule edits (realpath, take-10, `shred -u --`, link count), alarm 1 time and name, 3:40 margin words, D.5 time, item-1 guard sentence, E-01 status, index line, undefined gate, Phase 0 loose pair, duplicate row id, seconds in K, E-48 OLD altered, card item deleted, G.2 EVERY, E-42 stop rule.

## 5. Word counts (task 4; counted as runs of non-space characters by `mychk16.words`)
| Text | Words |
|---|---|
| E-48 NEW block | 3,643 (builder's note says 3,647; difference 4, method: mine counts non-space runs inside the ~~~~ fences only) |
| Appendix K block (whole `## Appendix K` section) | 928 (matches the builder's 928); 812 without heading and intro paragraphs |
| NEW text of all OWNER-STEPS rows | 16,609 (builder: 16,464 for the OWNER-STEPS rows; difference 145, not investigated) |
| NEW text of all rows, all three files | 18,127 |
| Whole EDITS.md | 52,990 (builder: 52,771; difference 219) |
Not measured by me: the applied-sheet length (builder reports 18,632 words against the 6,300 target, L-LEN open in r16-CHANGES.md; I did not re-run that count).

## 6. Status check (task 5)
- `git status --short` for `inputs/` (core-hardening/inputs), repo `inputs/`, `src/`, `tests/`: 0 lines. EDITS.md cmp-identical to my copy. I wrote only inside `evidence-r16-independent/`.
- Processes: none of mine left. Other agents' jobs are running (a mutation script in `evidence-repin8`, a pytest run under the scratchpad, one long python3 process at 95% CPU); I did not touch them.
- Removed: `__pycache__`, `scratch16`, `mut-tmp.md`. Left on purpose: `a/b/steps-edits` (copies used to run the builder's scripts), `a/b/inputs` and `tests` (symlinks to the real folders, read only).

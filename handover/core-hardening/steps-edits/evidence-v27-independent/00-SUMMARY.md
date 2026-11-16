# Independent evidence run, v27 (EVIDENCE RUNNER: records, does not judge)
Scratch work: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev27/ (orig-copy, rebuild, neg/). Originals: 28 sha256 identical before and after (01-sha-before.txt, 01-sha-after.txt). No spend, no push, no secrets.

## Deviations and things that did not behave as briefed (first)
1. fail-proof count: brief says builder claimed 51 of 55 fail on built v26. Run gives 52 of 55 (3 do not fail: C152, C157, C159); evidence-v27/fail-proof.txt says the same 52/3. The "51" in the brief does not match either file. Reasons for the 3 are given in v27-CHANGES.md item 6.
2. Negative control N12 ("never deletes" replaced by a delete instruction, in LEAD-RELEASE-NOTE-v11-SOURCE.md): check-v27.py exits 1, but ONLY through C19 (pointer list: a new pointer needs a person to read it). No content check looks for that sentence. With ACCEPT_POINTERS=1 on the scratch copy the same edit gives exit 0 and "0 failure(s)" (04-negative-controls-raw/N12b.out.txt). So the guard is the human reading of new pointers, not a check.
3. Negative control N03 (output tokens 10000 -> 11000): build stops on an AssertionError in facts-v27.py (traceback, not a FAIL line); check exits 1 (it also raises). Caught, but by a crash.
4. check-v27.py C07 message says "see v27-CHANGES.md item 3"; in v27-CHANGES.md item 3 is "No independent review", the word-target text is item 1. Wrong pointer inside a check message.
5. Word target (brief 6,300) NOT met: A 7,473, B 7,516. C07 ceiling: v26 check-v26.py = 6500 (v26 sheets 6,435 / 6,434); v27 check-v27.py = 7600 (raised by the builder, +1,100). Headroom over actual: 127 (A), 84 (B).
6. N15 (AKIA-style string with digits, built from parts) was caught by C49 (a stray number), not by the secret pattern; N17 (AKIA + 16 capitals) was caught by C55. Both exit 1.
7. Glossary: see section 5; items below have no explicit definition by pattern search (a person must judge).

## Table
| Check | Exit | One-line raw result | Raw file |
|---|---|---|---|
| (1) build-v27.py on scratch copy | 0 | A 7473, B 7516, note 11067, open-for-lead 6007 words; cmp: all 4 generated files byte-identical to originals; sha256 equal | orig-gen.sha vs rebuild (scratch) |
| (2) check-v27.py on originals | 0 | "check-v27: 0 failure(s)"; C07 info lines 7473 / 7516, target 6300 NOT met | 02-check-originals.txt |
| (2) check-v27.py on scratch rebuild | 0 | identical output to originals (diff empty) | 02-check-scratch-rebuild.txt |
| (3) mut27.py (scratch copy) | 0 | 166 plants: caught 165, missed 0, anchor-not-found 0; NEG1 printed MISSED as required (other check C106 fired); 42 s; output equals evidence-v27/mut27.txt on all CAUGHT/MISSED/TOTAL lines (diff empty) | 03-mut27.txt |
| (3) v27-fail-proof.py | 0 | 55 checks; 52 fail on built v26; no-fail: C152 C157 C159; none fail on v27; equals builder file (only the "rc=0" line differs) | 03-fail-proof.txt |
| (4) negative controls, 17 | see below | all 17 make check-v27.py exit 1 | 04-negative-controls-summary.txt, 04-negative-controls-raw/, 04-neg.py |
| (6) sha256 -c /tmp/claude-0/v26.sha | 0 | 16 lines, all OK (list holds build-v26.py twice) | 06-v26-sha-check.txt |
| (7) banned-vendor scan | 0 | list read at run time (10 entries); 49 files (all *v27*, evidence-v27, this folder): exact-case hits 0, case-insensitive hits 0 | 07-banned-scan-counts.txt |

## (4) Negative controls (each on its own scratch copy; check exit code)
| id | change | build / check exit | first FAIL line |
|---|---|---|---|
| N01 | call ceiling 3 -> 4 (0.27 x 3 = 0.81, 13.21) | 0 / 1 | C03 facts money differs |
| N02 | ledger 1240 -> 1250 (13.21 -> 13.31) | 0 / 1 | C03 facts money differs |
| N03 | output tokens 10000 -> 11000 (price 0.27 -> 0.285) | 1 / 1 | AssertionError (crash, no FAIL line) |
| N04 | one IST time changed (post-by 20:30 -> 20:00) | 0 / 1 | C03 post-by |
| N05 | wrong UTC/IST pair typed in sheet | 0 / 1 | C04 bad pair 09:00 UTC = 15:00 IST |
| N06 | B fourth alarm removed | 0 / 1 | C138 |
| N07 | B 7.11 removed from decline route | 0 / 1 | C137 |
| N08 | minimum think-time slot removed | 0 / 1 | C129 |
| N09 | typed-figure line removed | 0 / 1 | C141 |
| N10 | 5.9 cancel word removed | 0 / 1 | C106 |
| N11 | sk-ant-style string (built from parts) inserted | 0 / 1 | C55 |
| N12 | "never deletes" -> delete instruction (lead note) | 0 / 1 by C19 only; 0 with ACCEPT_POINTERS=1 | C19 pointer not in verified list |
| N13 | wait hard-coded "10 seconds" | 0 / 1 | C140 |
| N14 | think 20 -> 10 in facts | 0 / 1 | C129 |
| N15 | AKIA+digits string inserted | 0 / 1 | C49 (stray number) |
| N16 | wrong weekday (Tue 16 Nov) | 0 / 1 | C04 |
| N17 | AKIA + 16 capitals inserted | 0 / 1 | C55 |

## (5) Independent recount (own scripts, raw numbers in this summary)
- Words (wc -w and Python split agree): A 7,473, B 7,516 (v26: 6,435 / 6,434); note 11,067; open-for-lead 6,007; v27-CHANGES 1,313.
- UTC/IST pairs: A 7, B 15, note 18, open-for-lead 14: 0 arithmetic errors (three note pairs print seconds on the UTC side only, e.g. 17:39:00 UTC = 23:09 IST; sums are right). Lone UTC times without IST: note 3 (18:14 UTC, 18:14:40 UTC, 18:14 UTC), open-for-lead 3 (15:00 UTC, 18:14:40 UTC, 18:14 UTC); each lacks an IST partner on that spot (23:44 IST is given elsewhere). Weekday+date strings: 0 wrong (all 5 files).
- Cross references in A and B: A has sections 1,2,3,5-9 (no section 4; the sheet says so itself); steps A: 5 has 9, 6 has 7, 7 has 10, 8 has 8; B 7 has 11. Every X.Y step reference resolves in its own sheet (the only "unresolved" X.Y patterns were prices 0.27, 0.81, 3.00, 15.00). R1, R4-R10 and L1-L5 all defined. "section 4" appears only in "there is no section 4". Sheet A makes no reference to 7.11.
- Terms used but with no explicit definition found by pattern (A and B identical): look key, run key, per-key limit, think time (only inside the message sample), model settings file, masked / masked accounts, Do-not-disturb (once), last resort (plain, vs defined "Last-resort step"), key-list check 1-3, settings figures, model account pages, film person (named but only described as the person who films), stop rule (heading only). Pattern search is rough; a person must judge each.

## Not run, and why
- No independent judgement of wording quality or of whether any step is safe (runner never judges).
- mut27.py ran once on a scratch copy, not on the originals in place (would modify files). Timing 42 s, one run only.
- Did not run EGM reviewers, ruff, pytest or bandit (not in scope; no python package code touched).
- LEAD-RELEASE-NOTE-v10.md (read by fail-proof) is not covered by /tmp/claude-0/v26.sha.
- No live key, no model call, nothing pushed. Git shows other unrelated modified files (verify10b.py) that I did not touch; my only new folder is evidence-v27-independent/.

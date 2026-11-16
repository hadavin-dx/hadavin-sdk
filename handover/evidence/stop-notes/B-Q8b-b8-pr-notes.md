# Q8b batch 8 builder notes (branch core/q8b-b8 from b7d7cd18; pushed to wip/cloud-q8b-b8)

Round 8, redaction path. Task list: handover/reviews/Q8b/goldfish_review_report-r8.md Issues 1-13.

## Per issue (class / fix / tests / mutants)
1 class: a plural `tokens` glued to a word is a credential flag on the text path but a count on the record walk. Fix: one definition of a count run (`is_count_run`, `_COUNT_BEFORE_TOKENS`) shared by guard/redact.py and k1b/redaction.py. Tests test_b8_1_*. Mutants M116, M117, M118.
2 class: a cookie flag was matched by word part (`--no-cookies` masked the next word). Fix: exact names `cookie`, `set-cookie`, `session-cookie` (and `_`), no plural, no prefix words; curl's `--cookie name=value` stays masked. Tests test_b8_2_*. Mutants M119, M158.
3 class: ordinary word plus one word (`possession_id`) read as a credential key. Fix: look-behind of ordinary words in front of the guarded glued endings, one list for both files. Tests test_b8_3_*. Mutants M120, M121, M132.
4 class: scheme word after `--authorization` / `--bearer`. Fix: two new rules take the scheme word and the token; the generic flag takes a scheme word with its token. Tests test_b8_4_*. Mutants M104, M122, M123.
5 class: bound on words in front of a flag. Fix: six words (was three); timing test on 200,000 characters. Tests test_b8_5_*. Mutants M124, M125.
7 class: Digest header in quotes. Fix: runs to the closing quote; unquoted runs to the end of the line. Tests test_b8_7_*. Mutant M126.
8 class: digits behind a bare credential word. Fix: any number of digits as a flag. Tests test_b8_8_*. Mutants M127, M128.
10 class: `\s+` after a scheme word crossed a line break. Fix: `[ \t]+`, also for Basic (sibling). Tests test_b8_10_*. Mutants M129, M130 (M129 is the Digest line break).
12 class: key with the word cookie and more words readable in text. Fix: `cookie_name=v` etc. masked, as the record walk does. Tests test_b8_12_*. Mutant M131.
6, 9, 11: wording and pins only (CHANGELOG, LIMITS, pins in tests/test_q8b_batch7.py).
13: tests/test_q8b_batch8_lines.py: one line per id (66 ids from the independent run plus 8 new controls), check fails on a missing id (the test deletes a line and expects the check to notice).

## Fail-before
tests/test_q8b_batch8.py copied into a clean detached worktree of b7d7cd18: 16 failed, 8 passed (the 8 are controls and each has a line). Raw: /home/user/build/b8-ev/failbefore-b8-final.txt.
Issue 2 and 12 reproductions on b7d7cd18: /home/user/build/b8-ev/repro-i2-i12-b7d7cd18.txt.

## Evidence files (outside the repo)
/home/user/build/b8-ev/ : probe-head2.json, probe-main.json, cost-B-Q8b-b8.txt, cost-B-Q8b-main.txt, mut-full.txt, and the gate outputs.

## Costs (stated in CHANGELOG and LIMITS)
`--cookies`, `--x-cookie`, `--session_cookies` readable; `--authorization abc file.txt` masks `file.txt`; seven or more prefix words readable; `bypasskey`, `bypasscode` readable; 40 digits behind a key in `key=value` form readable (flag form masks any count); `--apiInputTokens` masked as a flag but read as a count by the record walk (listed).

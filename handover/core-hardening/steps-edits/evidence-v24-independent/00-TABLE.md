# Independent evidence v24 (EVIDENCE RUNNER: runs, does not judge). Run 2026-11-16 ~14:30-14:50 UTC. Scratch copy: scratchpad v24ind/work. Originals unchanged (10-sha-recheck.txt: all OK).

FAILURES AND GAPS FIRST
- Own 25 planted mistakes: check-v24.py caught 10, MISSED 15 (05-own25-plants.txt). Missed: Q01 wrong price per call in the sheet text, Q02 wrong expected total in the sheet text (0.84, build output confirmed to hold it), Q03 wrong output-token count in the sample, Q08 STOP RULE step "(1) if a key is alive, do the card now" deleted, Q09 stray backtick in card gate (a), Q10 card cancel step changed to "press close", Q11 card gate (f) deleted, Q12 R4 auto-reload "off" flipped to "on", Q13 secret-shaped string (built from parts) added to sheet, Q15/Q16 sample give-up and silence minutes changed, Q18 one `@example.com` guard changed to `.org`, Q20 lead note limit 13.21 changed to 13.12, Q22 accepted exit codes widened to "0 or 1", Q24 "five words" changed to "four".
- Gate in the sheets: no fenced shell block exists in A or B (the only fence is the sample numbers message); shell exists only as inline spans (5 per sheet). No python source in the sheets.

| # | Command | rc | Result |
|---|---|---|---|
| 1 | python3 build-v24.py (scratch copy) | 0 | A 6489 words, B 6445, note 9263, open file 4279; built A and B identical (sha256) to the files on disk |
| 1 | python3 check-v24.py | 0 | "0 failure(s)" |
| 1 | word count A / B, limit 6500 | - | wc -w 6489 / 6445; python split() 6489 / 6445; regex \S+ 6489 / 6445; awk NF 6489 / 6445. Margin 11 and 55 words |
| 2 | python3 mut24b.py (scratch) | 0 | 96 plants, caught 96, missed 0, anchor-not-found 0 (19 s) |
| 3 | own25.py (my 25 plants, scripts/own25.py) | 0 | caught 10, missed 15, anchor-not-found 0 |
| 4 | bash -n on 5 inline shell spans per sheet (A, B) | 0 x10 | all clean incl. the key-save line `(set -C; umask 077; read -rs ...)` |
| 4 | bash -n on the one fenced block (sample message, not shell) | 2 x2 | expected: it is plain text, not shell; recorded for completeness |
| 4 | py_compile: no python spans in A/B; compiled build, facts, check, mut24b | 0 x4 | ok |
| 5 | recompute (40000x3+10000x15)/1e6 ; x3 ; 12.40+0.81 ; 860/60 | - | 0.27 ; 0.81 ; 13.21 ; 14.3333 (14.33) |
| 5 | grep values in A, B, note, open file, CHANGES | - | see below |

Arithmetic grep (09b, 09c): A and B hold 0.27 x4 and 0.81 x4 each, no other 0.xx; no 13.21, 14.33 or 860 in the sheets (their only money figures: USD 0.27, 0.81, 15.00 x2, 189.00 x3, 3.00 x2). Lead note: 0.81 x3, 0.27 x1, 12.40 x2, 13.21 x1, 14.33 x3, 860 s x4; also 0.80 (worked example: 3.90 - 3.10 = 0.80, correct), 13.50 and 13.00 (example limits "13.00 is ok, 13.50 is not": both consistent), 15.00 (price out). Open file: 14.33 x4 (min/minutes), 860 s/seconds x2. No 0.28, no 14.4, no other value for the four figures anywhere.

Files: 01-build.txt 02-check.txt 03-word-counts.txt 04-mut24b.txt 05-own25-plants.txt 06-blocks-extract.txt 07-bash-n.txt 08-pycompile.txt 09a/b/c 10-sha-recheck.txt scripts/own25.py
Not checked: whether the 15 misses matter (that is for review); no key-save runtime test; no spend; no banned strings used.

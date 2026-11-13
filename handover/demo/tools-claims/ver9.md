# out-v9: read-only verification of HEAD 36dbb10 and the PR body

Read-only. Edited nothing except this file. Did not run pytest. Only read files, ran `git show/diff/log/rev-parse`, and re-ran the read-only throwaway `/tmp/work/d/check_links.py` on /tmp/am19/c (output identical to the stored f18 log).
Bible lookup (rule 1): the studio bible is not reachable from here, so no R-numbers were cited. EGM: not applicable, verification only.

## (1) Last commit 36dbb10: sentence by sentence

| # | Changed sentence | Verdict | Evidence |
|---|---|---|---|
| 1 | README:20 "If the lead's follow-up email is due and not yet sent, the replay starts it." (was "the repeat") | TRUE | `desk.py:1286-1287`: a replay of `new` sets `drive` only if `_pending_and_due`; `desk.py:1417-1430`: true for a `pending` follow-up with no automatic try yet or whose backoff is over. Test `tests/test_flow.py:114-125` (replay at point B drives the follow-up; `drive_lead_id == lead_id`). Wording is only a synonym change. |
| 2 | README:42 crash-point vs item ids: "the item ids are explained in contract.md, sections 'Other rules' and 'HTTP table' (the GET /review row)" | TRUE, one gap | Both section headings exist (`contract.md:145`, `:197`). `GET /review` row `contract.md:212` lists F, R, D, O and N ids. "Other rules" (`:171`) explains existence rules for F, R, D, O; the N item appears at `:65` and `:70`, which are NOT in "Other rules" (that heading starts at 145). The row alone covers all five id forms, so the pointer holds. Gap: for N nothing in "Other rules" says "N plus a lead id"; only the table row does (and the table row is the cited place). The README's other pointer, "Replies, verdicts and review items" (`contract.md:263`), was removed; that section holds the D item text at `:283` and the 18-digit id rule at `:284`, so removing it loses no claim that is still made. |
| 3 | README:65 and :82 (the two `/counts` comments): "the replayed request is not added to these counts; it only raises attempts in its receipt, and it can start a due follow-up" | TRUE | Counts come from receipts rows (`_COUNTS_SQL`, `desk.py:2417-2420`); a replay hits `ON CONFLICT ... DO UPDATE SET attempts = attempts + 1` (`desk.py:1363`) and adds no row. "Can start a due follow-up": same evidence as row 1. Not pinned by a test that checks counts after a replay (I did not find one); "no test pins this" in README:20 already covers receipt numbers only, not counts. UNPROVEN by test, TRUE by code reading. |
| 4 | `requirements-semgrep.in:8`: "read the first scan result in the job log (docs/tests.md, 'Semgrep': no result is stored; look for the 'Ran N rules on M files' line)" | TRUE | `docs/tests.md:32` heading "Semgrep"; `:36` "Status of the scan: no run result is stored here ... The proof is the log line 'Ran N rules on M files'"; `:34` "findings are printed in the job log only"; `.github/workflows/semgrep.yml:55` has the same line. |

Nothing in HEAD is FALSE. Also checked: the README "ten crash points and an eleventh, N1" sentence was not changed by HEAD, not re-verified.

## (2) /tmp/work/claims-pr-body.md

Placeholders: only `FULL-SUITE-FINAL-PLACEHOLDER` (line 46), as expected. No TODO, XXX, TBD, or other placeholder found by reading all 50 lines.

Numbers against git:

| Claim in body | Command output | Verdict |
|---|---|---|
| "19 commits" | `git log --oneline f3c39cf8..HEAD \| wc -l` = 19 | TRUE |
| "41 files, 602 insertions and 547 deletions" | `git diff f3c39cf8 --shortstat`: 41 files changed, 602 insertions(+), 547 deletions(-) | TRUE |
| 12 docs + 6 workflow/settings + 23 code = 41 | by extension: 12 .md; 4 .yml + .coderabbit.yaml + requirements-semgrep.in = 6; 22 .py + 1 .ps1 = 23 | TRUE |
| head commit 36dbb1060c3c5023e918344449730c5a56960a75 | `git rev-parse HEAD` same | TRUE |
| tree hash 49d3c85938fe5323a3378a49195d3b8da434b3ca | `git rev-parse HEAD^{tree}` same; /tmp/e19-312 (the full-suite clone) has the same tree and HEAD | TRUE |
| "21 of the 22 changed .py files identical, the one different is test_input_edge_cases.py; YAML equal for four workflows and .coderabbit.yaml" | `/tmp/runlogs/f19-proof.log`: 21 AST EQUAL, 1 AST DIFFERENT (that file), 5 YAML EQUAL | TRUE |
| gitleaks 8.30.1, three runs, no leaks, exit 0 | `f19-ci-tools.log`: three runs, "no leaks found", rc=0 each; `gitleaks version` = 8.30.1 | TRUE |
| ruff check exit 0; format "159 files already formatted"; mypy linux and win32 "28 source files each"; check_schema "RESULT ALL PASS" | `f19-ci-tools.log` identical figures | TRUE |
| bandit -ll exit 0 | rc=0 in the log; the log keeps only the last 4 lines, so the severity counts of the report are not in it | TRUE (exit code only) |
| "Link and name check: 7 references reported" | `check_links.py` re-run on tree 19: 356 ok, 7 broken, identical to f18 log. 6 are quoted section names, 1 is `tests/test_name.py` | TRUE; but see fix B |
| "one test-name check reports a deliberate name prefix in docs/limits.md" | `/tmp/runlogs/f18-numbers.md` row `docs/limits.md:60 test_crash_d2_subprocess_with_`: MISMATCH, "no such test function". That log is for tree /tmp/am18/c, not tree 19 | UNPROVEN on the final tree (see fix A) |
| Full suite 3.12: "1 failed, 3878 passed, 4 skipped" | `e8-full-312.log` last line: 1 failed, 3878 passed, 4 skipped in 1557.59s | TRUE |
| ...failure "could not read the clone folder (folder mode 700)" | log shows `test_v1_a_config_below_a_traverse_only_folder_is_refused_with_a_message_as_an_unprivileged_user` failing with `ModuleNotFoundError: No module named 'tools'` when run as the unprivileged user. "Mode 700" is an inference; the log does not print a mode | PARTLY UNPROVEN (cause is inferred) |
| Full suite 3.13: "1 failed, 3713 passed, 169 skipped" | `e8-full-313.log` last line same | TRUE |
| ...failure "a `git commit` that needed network for commit signing" | log: `git commit ... returned non-zero exit status 128` in `test_term_scan_finds_a_planted_term`. Nothing in the log says why; the later run script (`/tmp/work/run19.sh`) sets `commit.gpgsign=false`, which supports the guess but is not a log of the cause | UNPROVEN (cause is inferred) |
| "run before the last round of wording fixes" | e8 logs date 13:47-13:49; HEAD is 14:18; true, but the only full-suite run on the final tree (`f19-full-312.log`) was still running at 14:21 (322 bytes) | TRUE; matches the placeholder |

"Raw logs are in the handover folder": the logs I found are in /tmp/runlogs and /tmp/work; I cannot tell which folder "handover" is. UNPROVEN.

Sentences that say what a process did without a log I could find:
* "a script and readers compared every backticked name... a handful were wrong" (README-level claim in the table, row "Numbers and names"): script output exists (`f18-numbers.md`: 1065 items, 1 MISMATCH) but it is for tree 18 and no log of "readers" exists.
* "the Linux commands named in the docs were run as written": I found no log of this in /tmp/runlogs or /tmp/work/d (not searched exhaustively).
* "every 'no test checks...' was searched against tests/": no log found (the searches may have been interactive).

## Fixes to apply to the PR body

A. Line 45, the name-check clause: it rests on `f18-numbers.md` (tree 18). Either re-run the numbers script on /tmp/am19/c and keep the sentence, or write "(checked on the tree one commit earlier)".
B. Line 45: the log text for the 6 section-name items says "quoted section name: no heading with that name". "Quoted bold lead-in is not a heading" is the author's reading. It checks out for docs/tests.md:40 (a bold lead-in "Run it on your own computer" at tests.md:44); I did not confirm all 6. Say "section names that are in fact bold lead-ins" only if all 6 were checked, else drop the explanation.
C. Line 46: replace "(folder mode 700, a set-up fault of the run, not of the code)" with what the log shows: "the unprivileged-user test could not import `tools` from the clone folder (the log does not print the folder mode)". Replace "needed network for commit signing" with "a `git commit` inside the test exited with status 128; the cause is believed to be commit signing, which was switched off in the later runs; the log does not state the cause".
D. Line 46: when the final full-suite run finishes, replace the placeholder with the exact last line of `/tmp/runlogs/f19-full-312.log`; do not write a count before that. (It had not finished at 14:21.)
E. Line 37: "Raw logs are in the handover folder": name the folder path, or write "in /tmp/runlogs (f19-*.log, e8-*.log)" if that is the folder.
F. Line 42 (bandit): fine as written (exit 0); do not add counts, because the log holds only the last 4 lines.
G. README:42 (HEAD): optional, add "N" explanation: the `N<lead_id>` form is only in the `GET /review` row and in the resolve and retry rules, not in "Other rules" existence list (`contract.md:171`). Low importance; the pointer to the row is correct.

## Not checked
Windows commands; the `ten crash points` count; receipt-number skipping (README:20, unchanged in HEAD); the other 18 commits' sentences; whether CI, CodeQL, SonarCloud or CodeRabbit have run. Tokens: roughly 60k, no sub-agents, no background processes started by me (one pytest process on the machine belongs to the full-suite run, not mine).

Files read: /tmp/am19/c (git show HEAD, contract.md, docs/tests.md, README.md, src/lead_desk/desk.py, tests/test_flow.py), /tmp/work/claims-pr-body.md, /tmp/runlogs/{f19-*,e8-full-*,f18-links.txt,f18-numbers.md}.log. Head SHA verified: 36dbb1060c3c5023e918344449730c5a56960a75.

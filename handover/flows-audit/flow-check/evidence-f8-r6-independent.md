# Evidence F8 round 6, independent run (raw output; evidence runner, no judging)
Date (UTC): 2026-11-16. Hashes cut to 16 hex plus '...': take_check.sh f99407c3a20cee4d..., test_take_check.sh ff9ff309331bcec2... (same as evidence-f8-r6.md). Git status of flow-check was clean before and after (no uncommitted change to the four protected files).
Scratch folder: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/ev-f8 (patched copy in build/g/real; made the way run_all.sh makes it: copy committed real-v5 flows, git apply F-002 then F-008 (both rc 0), build_mainframe.py real (rc 0)).

## 1. Syntax
bash -n take_check.sh rc=0; bash -n test_take_check.sh rc=0; bash -n run_all.sh rc=0

## 2. Test file on the NEW script
`bash test_take_check.sh <patched real-v5> <new scratch>` rc=0
final line: test_take_check: 148 of 148 cases as expected, 0 not as expected
Lines starting with FAIL: 0. (Six "ok" lines contain the word FAIL inside their text, e.g. "B1d: a run with a FAIL writes no pin"; they are passing cases.)

## 3. Same test file on OLD take_check.sh
Old = `git show c79f8074d:handover/flows-audit/flow-check/take_check.sh` (c79f8074d = last commit before 6bdec84e5 that touched the file; 12a356c99 is HEAD). Run in a copy folder with the current test file, pin and checker.
rc=1; final line: test_take_check: 82 of 148 cases as expected, 66 not as expected
Lines starting with FAIL: 66, of which 37 are "f8-r6:" cases (the refused stand-in names exit 4 -> got exit 4 with another or no reviewer-line message, and the accepted names -> got exit 4 instead of 5), the rest are earlier-round cases (pin header/sha256, flows sha256, exit 5 rules, run_all.sh --lock-only/lock cases got exit 127). So c79f8074d is far older than the f8-r6 change; the 6bdec84e5 commit holds several rounds at once. I found no copy of the exact pre-f8-r6 script in git (evidence-f8-r6.md used a local pre-round copy bb3050fe0aae33ae...), so the f8-r6-only delta was not reproduced separately.
Old-run raw lines are in ev-f8/old.txt (scratch).

## 4. Hostile spot checks by hand (TAKE_CHECK_TEST=1, TAKE_CHECK_WARN_PIN=pin whose reviewer line is "<name>, 2026-11-16"; exit codes only)
| reviewer line name | exit |
|---|---|
| Pat O L L M | 4 |
| Pat C L A U D E | 4 |
| Pat Cla.ude | 4 |
| Pat Claudebot | 4 |
| Pat Smith, note "written by Claude" | 4 |
| Pat Smith, note with Cyrillic a (Cl-a-ude) | 4 |
| Pat Smith, note cl4ude | 4 |
| Zed Smith | 5 |
| Mary-Jane O'Neil | 5 |
| Aiden Botha | 5 |
Exit 4 cases 1-7 each print "THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON" (count 1 each). Exit 5 = would-be pass with the pin override (as designed, never 0). In cases 5-7 I wrote the note before the date ("Pat Smith, note X, DATE"); the test file puts the note after the date, so the refusal there is by the same message but the line shape differs from the tests.

## 5. run_all.sh
`RUN_ALL_NESTED=1 RUN_ALL_RAW=<new scratch>/raw bash run_all.sh` rc=0
key lines: "run_all exit status (real-v5 default runs + self-test): 0"; "OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check"; "COMMITTED PIN ... reviewer line ... NOT confirmed by the lead: a bare take_check.sh exits 4".
`git -C /home/user/hadavin-sdk status --short handover/flows-audit/flow-check`: no output (raw/ and selftest-output unchanged; nothing to restore).

## 6. Checks from handover/flows-audit
| command | rc | key line |
|---|---|---|
| python3 -I tools/check_secrets.py | 0 | PASS 0 hits in 1823 files |
| python3 tools/check_refs.py | 0 | PASS 5166 references |
| ruff check . | 0 | All checks passed! |
| ruff format --check . | 0 | 539 files already formatted |
(These counts are higher than evidence-f8-r6.md (1818 / 5162 / 534) because files were added since; this file is itself included in the next run.)

## Summary table
| step | command | exit | key line |
|---|---|---|---|
| 1 | bash -n x3 | 0/0/0 | - |
| 2 | test_take_check.sh on patched copy | 0 | 148 of 148 as expected, 0 FAIL lines |
| 3 | same test on old take_check.sh (c79f8074d) | 1 | 82 of 148; 66 FAIL (37 f8-r6) |
| 4 | 10 hostile names | 4x7, 5x3 | as table |
| 5 | run_all.sh | 0 | git status clean |
| 6 | secrets / refs / ruff check / ruff format | 0/0/0/0 | see table |

Not as stated or not run: step 3 used c79f8074d, not a pre-f8-r6-only copy (none in git). Nothing else was skipped. Nothing committed.

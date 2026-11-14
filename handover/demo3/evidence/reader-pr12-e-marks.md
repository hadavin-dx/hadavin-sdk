# Reader report: the "2 E marks" of the PR #12 run (read-only, facts only)

Paths are relative to /home/user/hadavin-sdk/handover/demo3/ unless stated. I did not run pytest. I ran only read-only counts (a small Python counter over the saved log text).

## 1. Which log, which position

- The run is "A run 2" on PR #12 head 8d65577 (branch followup-ab-v3). Raw log: `evidence/raw/suite-pr12-run2.log` (40 lines, 3239 bytes, written 2026-11-13 10:16). Companion: `suite-pr12-run1.log` (38 lines), `failing-ids-pr12-8d65577-run{1,2}.txt` (57 and 60 lines).
- Recorded numbers: `evidence/summary.md:61-62` (run 1: 2489 / 57 F / 182 s / 0 E; run 2: 2488 / 57 F / 188 s / 2 E; both stopped at 72%, exit 1, 1172 s and 1126 s). `REPORT.md:911` (HEARTBEAT 39) says: "the 2 errors (marks E) in run 2 ... marks only, no traceback saved; the 2 ids by position are in tests/test_fakes_body_before_answer.py, mapping unreliable".
- The progress line positions of any `E` character were never recorded. The position claim "by position ... test_fakes_body_before_answer.py" has no stated line or percent. The log was run with `-q -rs` (summary.md:55, REPORT.md:534), so no test ids are printed in progress lines.
- The log has no pytest summary line and no ERRORS section. It ends with `EXIT_CODE=1 WALL_SECONDS=1126` at about 72% (log line 40). Both logs are cut at the same mark; the cut was later attributed to "git commit / pull --rebase --autostash replaced files pytest was writing" (REPORT.md:909 table row "Logs of A runs", and the proof referred to at heartbeat 40, commit 0af5febd).

## 2. Were the names of the two errored tests ever printed

- No. The log was `-q` without a summary, so no ERROR names exist. `questions-for-lead.md:2` (12:42Z) repeats "no traceback saved. By position they fall in tests/test_fakes_body_before_answer.py (mapping unreliable)". `evidence/summary.md:55` says failing names "are not in these logs".
- The Q10 flake chase (`evidence/flake-chase-fakes.md`, `REPORT.md:530`) never ran on the PR #12 tree ("0 runs (never started)", flake-chase-fakes.md:5; register.md:106).

## 3. What the two "E" marks actually are in the saved log (new finding of this reading)

- Run 2 log lines 13 and 14 each contain the text `Exception occurred during processing of request from` (stderr of Python's socketserver, printed between progress characters). Run 1 has no such text (its line 12 has only a dashed separator `----------------------------------------` between dots).
- I counted the characters `. F s E` in the progress area (text before `EXIT_CODE`, `[ NN%]` suffixes removed):
  - run 1: `.` 2489, `F` 57, `s` 182, `E` 0 (matches summary.md:61 exactly)
  - run 2: `.` 2488, `F` 57, `s` 188, `E` 2 (matches summary.md:62 exactly)
- When I remove the two `Exception occurred during processing of request from` strings from run 2, the counts become 2488 / 57 / 182 / 0 E: the same `s` count as run 1 (182) and zero `E`. The word "Exception" has one capital `E` (2 lines gives 2 E), and "processing of request" has three `s` (2 lines gives 6 s, and 182 + 6 = 188).
- So the recorded "2 E, 188 s" equals the naive count that includes those two stderr text lines. No standalone `E` progress mark exists in the saved log. This is arithmetic on the saved file; whether the counter that produced the table used that same method is not written anywhere (see section 7).
- The same kind of stderr noise is documented elsewhere: `evidence/flake-chase-fakes.md` "What the Exception occurred lines are": present in all 72 main-tree logs of the fakes test file, `BrokenPipeError: [Errno 32]` from demo_only/fake_hubspot.py:224 (an inference about the cause, stated as "not proven" there).
- Run 2 has one fewer `.` (2488 vs 2489) than run 1 with the same 57 F; the difference sits in the lines the stderr text and dashes replaced (run 1 line 12 vs run 2 lines 12-14). Not otherwise explained in the files.

## 4. Was this one of the invalid runs of ORDERS 2026-11-13 12:58Z

- Yes. ORDERS.md:73-74 (12:58Z order item 1): "Your 4 earlier full runs on main/PR #12 are INVALID as pass/fail evidence (basetemp outside TMPDIR: 56 F; logs cut by git)". The run in question is one of those four (main 61ded9e runs 1-2, PR #12 8d65577 runs 1-2). `evidence/summary.md:51` lists it as INVALID: "basetemp OUTSIDE TMPDIR, logs cut by my git operations". REPORT.md:534 table (rows "A (4 early runs)"): "56 / 57 failed (+2 `E` marks in PR #12 run 2) ... invalid, replaced by valid runs"; verified "yes for the 56/57 ... NO for the 2 `E` marks".
- Failure cause for the 57 F: `PathRefused ... path is outside the allowed folders` (REPORT.md:911); same ids pass with basetemp inside TMPDIR (raw/failures-alone-main.log, failures-basetemp-outside-main.log as cited there).

## 5. Later valid runs on the same code (PR #12 head 8d65577)

- None. PR #12 was closed; its content became PR #14 (ORDERS.md:21, ORDER 3: branch followup-final, head d5b4451). No full run on 8d65577 was repeated (flake-chase-fakes.md:5: PR #12 tree 0 runs).
- Later valid full runs are on other heads (main f3c39cf8 stack, PR #14 heads edadd00, 6b1fe49, d5b4451). Summary lines verbatim, from `evidence/raw/`:
  - suite-edadd00.log: `3681 passed, 200 skipped in 1215.22s (0:20:15)`
  - suite-6b1fe49.log: `3683 passed, 200 skipped in 1155.15s (0:19:15)`
  - suite-base.log: `3683 passed, 200 skipped in 1188.75s (0:19:48)`
  - suite-stack.log: `3683 passed, 200 skipped in 1191.99s (0:19:51)`
  - suite-py313-base.log: `3684 passed, 199 skipped in 899.22s (0:14:59)`
  - suite-py313-stack.log: `3684 passed, 199 skipped in 893.23s (0:14:53)`
  - stack-full.log: `3692 passed, 200 skipped in 1140.95s (0:19:00)`
  - e3-fix1-full.log: `3692 passed, 200 skipped in 1347.60s (0:22:27)`; e3-stack-full.log: `3692 passed, 200 skipped in 1357.89s (0:22:37)`
  - hang-c2-full.log: `3407 passed, 198 skipped in 1066.37s (0:17:46)`
  - b9-full-313.log: `3690 passed, 199 skipped, 1 xfailed in 945.14s (0:15:45)`; m4-full.log: `3714 passed, 169 skipped in 923.92s (0:15:23)`; m3-run.log: `30 failed, 3684 passed, 169 skipped in 903.24s (0:15:03)` (30 failures, not errors; its own report is evidence/m3-report.md)
  - None of these lines contains "error". Interrupted logs `fix1-full-run1-interrupted.log` (3196 passed, 184 skipped) and `fix1-full-run3-interrupted.log` (2584 passed, 56 skipped) also show no errors.
- Error counts in other logs (for completeness, different runs and causes):
  - `b5e-full-invalid-run1-basetemp-outside-TMPDIR.log`: `57 failed, 3710 passed, 206 skipped, 13 errors in 1375.15s (0:22:55)`, also marked invalid (basetemp outside TMPDIR); the errors are `ERROR at setup of test_...` in tests/test_smtp_outbox.py (assertion `[] == ['LISTENING', '127.0.0.1']`, test_smtp_outbox.py:63). A different tree (builder b5e) from PR #12.
  - `b5e-smtp-experiment.log`: `54 passed, 13 errors` (twice); `E5-b-test_settings_lane3.log`: `1 error in 0.12s` (collection error). Neither is the PR #12 run.
- Q10 (REPORT.md:530, flake-chase-fakes.md:8-15): 72 runs of tests/test_fakes_body_before_answer.py on main f3c39cf8, all exit 0, "17 passed", 0 errors, 0 failures. REPORT.md:911 also says "0 errors in 10 later full runs".

## 6. Where the item was recorded as unexplained

- First written in HEARTBEAT 39 (REPORT.md:905-925, commit 78ba955f, 2026-11-13 12:38Z); the summary.md row with "2" in the error column was written by commit 15ac7691 (10:25Z, heartbeat 8). questions-for-lead.md:2 (12:42Z); FREEZE.md:24. Marked "stays open (low value: PR closed)" at REPORT.md:543 and 551.

## 7. What the evidence cannot tell

- Whether the heartbeat-8 table was produced by the naive character count (the method that reproduces "2 E / 188 s" from the saved log) or by reading pytest output on screen: no script or note records the method (only `summary.md:55` says counts were "counted from the progress marks").
- Whether pytest really printed any `E` mark during run 2: the log is cut at 72% with no summary, and any `E` in the lost 28% is unknown (the recorded counts only cover the first 72%, and run 1 and 2 have identical F counts and positions).
- Which tests were the "2 ids ... in test_fakes_body_before_answer.py": that mapping was a guess by position, never printed.
- Why run 2 shows the socketserver `Exception occurred` text while run 1 does not (stderr interleaving, timing, or lost text in run 1). Not recorded.
- Whether the PR #12 head 8d65577 would show errors when re-run (never re-run; branch closed).
- I have not looked at the original on-screen output of that run; it is not in the repo, so I cannot confirm or exclude that pytest also printed an `E` that was lost.

# fix-f8-r10c (round 3, review f8-r10b round 2). Failures and gaps first.

## Not done / uncertain
1. The committed `take-warns.pin` still has the flows-audit session line (as ordered). A bare `bash take_check.sh --flows <patched>` therefore exits 4 ("pin not yet confirmed by the lead"; real run: exit 4). Only the lead can make the first exit 0 (replace the one reviewer line; the hash covers the WARN lines only).
2. `run_all.sh` exits 0 although the committed pin is unconfirmed, because its take runs use a copy of the pin with a stand-in reviewer line (otherwise run_all could never judge the files). It prints the committed pin's reviewer line and "NOT confirmed by the lead" in its last lines. Lead decision: whether run_all should also exit non-zero until the pin is confirmed.
3. Q4 part not changed: a tcfail case can still pass when its wanted line is printed for another reason together with exit 4 (each wanted line is specific to its cause; I did not add a stricter match).
4. The unreadable-file case (Q2) is tested with a fake `sha256sum` on PATH (this session runs as root, so chmod 000 cannot be tested); a real permission failure was not run.
5. Not run: Python 3.10 itself (unchanged), n8n (never).
6. Old-script proof for Q3/Q4 used a copy of the OLD run_all.sh in a scratch tree (only the test hook line added for Q3), not the new nested tests.

## Each review point checked against the files
- Q1 confirmed: old take_check.sh rejected only PLACEHOLDER; line 208 printed "a person read and accepted". Now prints `reviewed by (as written in the pin): ...`; a reviewer line with "session" or "lead to confirm" (any case) is exit 4 with `pin not yet confirmed by the lead`; that problem does not block `--write-warn-pin`. Tests: Q1 x4. README, run_all and tests follow (tests use a pin copy with a person's line for exit 0).
- Q2 confirmed: hash was taken after the checker and never compared; a failing sha256sum gave an empty hash. Now `flow_snapshot` hashes the four files and every other *.json in the folder before the checker and after the last read (end of section 4); difference = exit 4 (also over a checker FAIL); unreadable or non-regular file prints MISSING and is exit 4. Tests: change of mf-hook.json, change of an extra json, extra json counted, sha256sum stub failing.
- Q3 confirmed: run_all.sh printed the status, then the OPEN LEAD case could set RC=1. Now RC is final before printing. Nested run with RUN_ALL_DROP_LEAD (new test hook, only with RUN_ALL_NESTED).
- Q4 confirmed: tcfail printed only "want exit 4, got N", guessed "overwritten by another run", inherited TAKE_CHECK_*. Now: first FAIL or !!! line printed, guess dropped, `env -u` for all six variables on every take call (also lines 75, keyok-gone, exit2/3, disabled-send). Nested run exports polluted TAKE_CHECK_* and plants one failing case.
- Q5 confirmed: checker exit >=4 was returned as is; README said --write-warn-pin ALWAYS exits 4. Now >3 is shown and returned as 3; README lists the real codes (4 written, 2 refused, 1 FAIL, 3 checker broke, 4 other problems).
- My own slip: first draft of the Q2 test put an extra json in the mf-hook.json case, so the checker FAIL (exit 1) made it pass by accident; caught by running against the old script; fixed.

## Proof the new tests fail on the OLD scripts (backups in scratchpad/bak-f8r10c/)
- New test_take_check.sh vs OLD take_check.sh + OLD pin: `32 of 44 cases as expected, 12 not as expected` (Q1 x4, Q2 x4, Q5 x4; the Q2 mf-hook case got exit 0). New script: 44 of 44.
- OLD run_all.sh with only the drop-lead hook: printed `run_all exit status ...: 0`, real exit 1 (REAL EXIT=1).
- OLD run_all.sh with TAKE_CHECK_TEST=1 and TAKE_CHECK_DDL exported by the caller: `[take_check.sh exit=4]` and 6 missing lines; new nested run c (polluted env) shows exit=0 and only the planted case.

## Final runs (fresh folders; real exit codes)
- `bash run_all.sh <fresh>`: exit 0; last lines show `[take_check.sh exit=0] missing lines: none`, `run_all exit status ...: 0`, the committed-pin line, OPEN LEAD line. Wall time about 55 s before the two new nested runs, not re-timed after.
- `bash test_take_check.sh <fin/g/real> <fresh>`: exit 0, 44 of 44.
- Bare take on the patched folder with the committed pin: exit 4, reason printed.
- `ruff check`: 0 ("All checks passed!"); `ruff format --check`: 0 (43 files formatted); `bandit -ll -r`: 0, no findings.
- raw/ and selftest-output restored with `git checkout`; two new untracked raw files removed; `git clean -n flow-check` lists only the older untracked flow-check/handover/ (not mine, left alone).
No fill_flows value printed. No commit made (the harness auto-commits edits).

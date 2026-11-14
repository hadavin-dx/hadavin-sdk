# lane3 fix-10 (builder b14): a bad DESK_* value shows a Python traceback in scripts

Base: f3c39cf89ec989f032ea48a23cfd824b88da9c68. Tree: /home/user/work/b14-tree (not committed; `git add -A` at the end).

## What failed first (raw: raw/b14-fails-before.log, raw/b14-sweep-before.log)
- New test file against the unfixed tree: 231 failed, 22 passed (the 22 passes are the two entry points that already
  behaved: `python -m lead_desk.server` and `tests/crash_launcher.py`, for the settings that were already refused).
- Sweep before: `scripts/crash_desk.py`, `scripts/feed.py`, `scripts/reset_check.py`, `scripts/start_all.sh`,
  `scripts/reset.sh` printed a full Python traceback, exit 1, for any refused setting.
- A second bug found by the hostile set (not a traceback, but the same input class): `DESK_NUDGE_TO=a@b@c.test` (two @),
  a 5000 character address and an address with a control character were ACCEPTED by `Config` (PLAIN_ADDRESS allows
  "@" in the domain part and has no length cap). With the old tree `start_all.sh` then started a real desk with that
  address. Fixed in `Config.__post_init__` (see below). The root cause (PLAIN_ADDRESS looseness) lives in identity.py,
  which fix-8 changes; I did NOT touch identity.py, I tightened only the one DESK_NUDGE_TO check.

## Class
An unhandled bad-config value reaches the person as a traceback: a program reads the DESK_* settings by itself,
outside the one place that turns `SettingRefused` into a plain message (`server.main`, exit 4).

## Choke point
`Config.from_env` is the one reader and it is already clean (probe: 19 DESK_ names x 8 hostile values raise only
`SettingRefused`, never another error, never echo the value). The gap was the callers. Fix: ONE new shared function
`lead_desk.config_exit.config_or_exit(env=None)`: catches `SettingRefused`, prints
`the desk refuses a setting: <message>` (one line, cut to 200 characters) on the ERROR stream, exits 4
(`EXIT_DESK_SETTING_REFUSED`, the code the desk already uses; no new code). Error stream, because the shell scripts
read the setting with `$(python -c ...)`, which swallows standard output. `server.main` is unchanged (it prints to the
output stream; kept so that no existing test or habit changes).

## Sweep table (every reader of a DESK_* setting; before / after for DESK_PORT=abc, DESK_FAKES_URL=ftp://..., DESK_NUDGE_TO=two-@)
| Entry point | Before | After |
|---|---|---|
| scripts/crash_desk.py | traceback, exit 1 | one line, exit 4 |
| scripts/feed.py | traceback, exit 1 | one line, exit 4 |
| scripts/reset_check.py | traceback, exit 1 | one line, exit 4 |
| scripts/start_all.sh (3 helper calls) | traceback, exit 1 | one line, exit 4, nothing started or created |
| scripts/reset.sh (1 helper call) | traceback, exit 1 | one line, exit 4, nothing deleted |
| scripts/start_all.ps1, scripts/reset.ps1 | PowerShell error on `.Trim()` of nothing (by reading; NOT RUN) | helper `Read-DeskSetting` passes exit 4 on (NOT RUN: no PowerShell here; text test only) |
| python -m lead_desk.server (server.main) | one line, exit 4 | unchanged |
| tests/crash_launcher.py (calls server.main) | one line, exit 4 | unchanged |
| demo_only/fakes_server.py | does not read DESK_* (uses `Config()` defaults) | unchanged |
| load_tools/check_invariants.py, load_driver.py | read only DESK_QUALIFIER as plain text, cannot fail | unchanged |
| scripts/run_real_check.py | reads a config FILE (not the environment); its own refusal block catches `ValueError` and prints `refused: <Type>: <setting name>` with its own exit code | unchanged (named exception in the guard test) |
| scripts/hubspot_probe.py, n8n_api.py, http_guard.py, run_live_check.py, check_schema.py | no DESK_* reads | unchanged |
Before/after raw: raw/b14-sweep-before.log, raw/b14-sweep-after.log (sweep script: /home/user/work/priv/b14-tmp/sweep.sh).

## Tests (tests/test_bad_setting_entry_points.py, new, 254 cases)
- 5 Python entry points x 14 bad values (empty, whitespace, 5000 characters, control character, non-ASCII digits,
  non-ASCII address, two-@ address, address-like text in a number setting, bad URL, nan): exit 4, ONE line, names the
  setting, no traceback, value and any "@" not in the output, no data folder created.
- 2 shell scripts x the same 14 values.
- Reader class check: 19 DESK_ names x 8 hostile values (incl. NUL, lone surrogate, 100000 characters) give a Config or
  a one-line exit 4 (NUL cannot be put in a real environment, so it is tried in-process).
- Source guard: no scripts/*.py|sh|ps1 may call `Config.from_env(` (only run_real_check.py, named).
- Text check for the two .ps1 files; one-line cut test (long and multi-line message).
- Contract updated (contract.md lines 77 and 131).

## Files and lines touched (for the stack builder who re-cuts)
- NEW src/lead_desk/config_exit.py (29 lines)
- NEW tests/test_bad_setting_entry_points.py
- src/lead_desk/config.py: line 24 (+`EMAIL_MAX,` in the constants import) and lines ~510-516 (the DESK_NUDGE_TO check in
  `__post_init__`: added length cap, exactly one "@", no control character). Nothing else; a fix-2 conflict can only be
  in those two hunks.
- scripts/crash_desk.py lines 12, 17; scripts/feed.py lines 23, 62; scripts/reset_check.py lines 12, 27
- scripts/start_all.sh lines 18-19 and 30; scripts/reset.sh line 14
- scripts/start_all.ps1 lines 10-22 (+ function) and 34; scripts/reset.ps1 lines 15-26 (+ function)
- contract.md lines 77 and 131. identity.py NOT touched.

## Mutation check by hand (raw/b14-mutants.log): 15 mutants of the changed code
14 killed, 1 survived on first run (M3: no one-line cut) and 1 mutant was badly built (M15 replaced only the first of
two names); I added a test for M3 and rebuilt M15; both are killed on the rerun. Final: 15 of 15 killed.
M1 exit code 1; M2 message to stdout; M3 no one-line cut; M4 catch the wrong error; M5 echo the environment; M6/M7/M8 drop
one rule each of the nudge check; M9-M13 put the bare reader back in crash_desk, feed, reset_check, start_all.sh,
reset.sh; M14 start_all.ps1 without the exit-code pass-on; M15 reset.ps1 back to the bare reader.

## NOT DONE / NOT CHECKED
- The two PowerShell scripts were NOT run (no PowerShell on this machine). Only a text test covers them; the
  PowerShell 5.1 error-stream behaviour in `Read-DeskSetting` is reasoned, not observed. Next step: run both with a bad
  DESK_PORT on the Windows CI job or a Windows laptop.
- Windows paths for the new subprocess tests: shell tests are skipped on Windows; the Python ones are not skipped but
  were not run on Windows.
- PLAIN_ADDRESS in identity.py still accepts a second "@" in the domain part for other callers (lead e-mail checks use
  their own stricter `_valid_email`; I did not audit every PLAIN_ADDRESS user). Hand to fix-8.
- Exit 4 in `reset_check.py` already meant "something still answers on a port"; a bad setting now also gives 4 there.
  The one-line message tells them apart; reset.sh never reaches that case (its first helper call fails first).
- An earlier before-run of my own tests (accepted nudge values) started two real desk processes in my tree; I stopped
  exactly those two (checked pid, cwd and DESK_DB_PATH in /proc first) and removed the stray `xy.lock` and `data/` lock
  file my own probing made.

## Checkpoints
- 04:20Z start; 04:47Z fix done, tests green on 3.13 and 3.12 (set of 10 files, 899 passed each), full run started 04:47Z.

## Resume (builder b14b, 05:01Z-05:30Z)
- The earlier full run died at 71% (container restart); its log b14-full-313.log is incomplete and is NOT evidence.
- Full run on the final head (3.13, nothing else): 3968 passed, 169 skipped, 0 failed, 903 s. Raw: raw/b14-full-final.log. Skips are the usual
  ones (no playwright, Windows-only, load measurement); not looked at one by one.
- Re-checked by me from the diff and the tree (not by B14's word): every changed script and the two new files read; grep shows the only
  `Config.from_env(` left in scripts/, demo_only/, load_tools/, tests/crash_launcher.py is scripts/run_real_check.py:884 (named exception);
  demo_only/portal_demo.py and fake_model_server.py contain "DESK_" text but read no environment. NOT re-run by me: the before-the-fix run
  (231 failed, 22 passed, raw/b14-fails-before.log), the 15-mutant run and the sweep tables: those are B14's logs, I read their tails only.
- Patch: evidence/lane3-fix-10.patch against f3c39cf8 (staged with git add -A, not committed). PowerShell scripts still not run.

# Review of the r7b patch (core-fix-on-frozen-r7b.patch), fallback goldfish reviewer

Money and mail path: no round cap. Date 2026-11-13.

## NOT READ / NOT RUN (stated first)
- I did not run the full suite (brief said not to). I ran only the r7b and r7m test files: 100 passed, 2 skipped (the skips are model-only routes).
- PowerShell scripts (start_all.ps1, reset.ps1) were read, never run (no PowerShell here).
- Not fully read: the delta of test_file_call_guard.py, test_hygiene, test_reset_scripts, test_cli_refusals, test_n8n_api_url, test_script_number_limits.
- Not investigated: the RESULTS.md "unexplained" check_invariants 168-vs-161 lines. Not verified: the CHANGELOG count "201 shapes in all".
- No real mail servers; loopback stubs only. Python 3.12 not tried (only 3.13.18); requires-python is >=3.12.
- Slips of mine: (1) one burst probe had stdin redirected from /dev/null, against the brief; all later probes used `input=b''`. (2) `pip download pytest` dropped stray wheels in /home/user/hadavin-sdk; I removed them and `git status` was clean afterwards.
- Frozen tree and every tree I did not create were not edited. Processes I started are finished.

## Verdict
No Blocker. One Major (A): the RecursionError class fixed in r7 N1 is fixed only in the fake servers; the same bug is still live in real-adapter parsers and in two scripts, with a Python traceback on screen. Minors B to I below.

## Major

### A. RecursionError (deeply nested JSON) still escapes in sibling parsers
Spec broken: "never show a traceback ... one line, fixed exit code". Proved with loopback servers returning `'['*30000+']'*30000` (60 KB, under the 64 KiB cap).
- src/lead_desk/live_claude.py:487 (reply parse) catches only ValueError. `LiveQualifier.qualify` raises raw RecursionError.
- scripts/run_live_check.py `run_model` (about line 113) catches only `(LiveError, OSError)`. The traceback escapes after the ledger reserve line is written and with no settle.
- scripts/hubspot_probe.py:152: `--yes-spend-calls 7 --dry-run http://127.0.0.1:PORT` against a stub answering deep JSON prints a full Python traceback, `RecursionError`, rc 1.
- src/lead_desk/crm_hubspot.py:333: `HubspotCrm.put` raises raw RecursionError. The desk's `except Exception` catches it, so the desk is safe; the standalone use is not.
- Same family, no test: adapters.py:74, scripts/run_real_check.py:783 (trusted desk reply, lower risk), portal_api.py:458 and :472, demo_only/fake_model_server.py:110 (control file with deep JSON makes the shield return 400 on every call instead of falling back to the mode), live_claude.py:397 (4096-byte body safe on 3.13, unknown on 3.12).
- Fix: one shared bounded loader in src (use `loads_bounded`'s idea, turning RecursionError into ValueError) used at every site, plus one test per site that fails on the old code.
- docs/settings.md:162-163 ("only three cases can still print a Python error trace") is false until this is fixed.

## Minor

B. tests/support.py `checked_argv` / `popen_program` does not match its own docstring and S603 reason.
- `['git','-ccore.pager=x','log']` and `['git','--config-env=core.pager=X','log']` are accepted (docstring: git `-c` other than `user.*` is refused).
- `popen_program(['true','-c','echo X'], executable='/bin/sh')` ran sh: kwargs `executable` and `shell` are not checked.
- A path-prefixed tool (`/tmp/zz/git`) passes because only the basename is checked.
- `test_no_other_file_of_tests_starts_a_program_by_itself` misses `from subprocess import run`.

C. tests/conftest.py clean-tree guard does hide things; RESULTS.md says it "hides and skips nothing".
- `_SKIP_FOLDERS` skips .git, __pycache__, .pytest_cache, .ruff_cache, .mypy_cache, node_modules. Empty directories are not seen.
- Proved with a probe test: stray file in repo gives rc 1 (good); an empty directory gives rc 0; files in `.git/`, `scripts/__pycache__/`, `node_modules/` give rc 0.
- No test covers the guard itself. The writer of the stray file `a<newline>b` (RESULTS item 1) is still unfound.

D. HeadDeadline `send_error` OSError swallow is untested. Mutant M7 (catch OSError changed to KeyError) survived all 84 slow-sender and bad-request tests; with it a real header drip prints BrokenPipeError tracebacks in server stderr. Add a test asserting no "Traceback" in stderr during a drip.

E. Redundant layers hide each other: M8 (RecursionError removed from BAD_REQUEST_ERRORS) and M3 (`loads_bounded` without the RecursionError catch) survive the deep-body tests. Add a direct unit test for each layer.

F. constants.py comment "one row is at most about 400 bytes" is wrong: a real CRM view row is 794 bytes with max ASCII fields, 2794 with non-ASCII, so a 100,000-lead view can pass the 40 MB cap. Outcome is graceful (refused whole), but the comment and the test premise (150-char note row) are false.

G. scripts/start_all.ps1 is much weaker than start_all.sh and untested: no readiness check and no fail_start (prints "started:" at once); does not refuse pid/log files that are links, pipes or devices; `Test-Path` without `-LiteralPath`; no exit 3. README line 96 ("the .sh and .ps1 end the same way with the same code") holds only for bad DESK_* values. RESULTS says "same in start_all.ps1 (untested)".

H. reset.sh and reset.ps1 pid check is a substring match (`*lead_desk.server*|*demo_only.fakes_server*` anywhere in the args). A reused pid running e.g. `tail -f ...lead_desk.server.log` would be killed. `python` is assumed on PATH (exit 127, not in the fixed code set).

I. CHANGELOG.md in a public repo points to `handover/core/review/` and `out/R7/RESULTS.md` "of the studio notes" (breaks the no-private-pointers rule). The r7b changes (HeadDeadline, RecursionError, burst closed-port exit 3, portal cap 4 MiB to 38 MiB) are missing from it. The "201 shapes" count is unverified.

Nits: fake_model_server `--key-file` pointing at an empty file starts with key "" (auth effectively off). The burst listener probe connects and closes without sending, so the desk sees an empty connection. Burst accepts `localhost` (a name lookup), while the docs say refused addresses are refused "before any name lookup" (true only for refused ones).

## Closure of earlier defects (my own check)
- N1: fixed in fake servers only (see A). N2 HeadDeadline: real drip cut at 20.0 s, no traceback: closed. N3 exit 7 docs: closed. N4 `_message`: closed. N5 `shown` escaping: closed.
- M1 exit 4 for bad paths: closed. M2 cap: closed. M3 replant: 145 of 145: closed. M4, M5, M6 (start_all.sh): closed (ps1 see G).
- Mail F1 to F4, F6, G1: closed. `require_modern_protocol` runs before IMAP login and before the SMTP password; IMAP readline deadline present; `run_real_check.load_env` uses `.strip(" \t")`.
- Burst closed port: exit 3 in about 3 s for `127.0.0.1:1`, `[::1]:1`, `localhost:1`; `:0` gives exit 2.
- Fake servers: 400 or 200, no traceback, depths 500 to 12000.
- CLI fuzz of 20 CLIs (6 to 9 hostile values per option; pipe, directory, empty and deep-JSON files): no traceback, echo, class name or hang.

## Changed old tests (strength check)
ledger_amounts (exit 1 to EXIT_STOPPED 6, same cases), live_claude (CONTROL comments only), process-start conversions to `run_program` with `text_file`, test_mode_safety, crash_points, codeant_demo_only, env_numbers: assertions at least as strong in every row I read.

## Mutation table
Killed: M1 (no timer), M2 (timer not cancelled), M5 (burst check off), M6 (portal cap), M9 (timer x100). Survived: M7 (D), M8 and M3 (E).

## Files
Probes and outputs: /home/user/build/rr6/out/REV7C/probes/ ; checkpoint: /home/user/build/rr6/out/REV7C/checkpoint.md

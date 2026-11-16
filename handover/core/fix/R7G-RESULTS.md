# R7G RESULTS (patch round r7g on r7f, money and mail path). Tree /home/user/build/rr6/tree-R7G. Base frozen 49d3c859.

All numbers are builder-claimed unless a raw file is named. Made-up data, loopback only (test runs inside `unshare -n`), no spend, nothing pushed. This builder RESUMED an earlier one cut off by a container restart; I read tests/test_r7g_findings.py and the full diff vs tree-R7F before relying on it (checkpoint.md). Raw output is in out/R7G/raw/.

## OPEN ITEMS / NOT RUN / NOT DONE (first)

1. **NO full suite** (as instructed; an independent runner does it). I ran the touched-module selector set one file per process (tests/test_*.py listed in sel2.txt, 52 files, plus 5 extra files that mention the changed modules). 96 of 147 files under tests/ were NOT run by me (list: `comm` of tests/ against sel2.txt; none of them mentions load_driver, netconnect, imap_count, connect_bounded, resolve_bounded, desk_listening or STOPPED_EARLY by grep).
2. **Git-dependent tests cannot pass in tree-R7G** (it has no .git by design): test_hygiene (4), test_nosemgrep_form (1), test_raw_bidi_chars (1), test_shell_single_bracket (1) failed there with "not a git repository" (raw/pf-*.log). I re-ran them in a copy with `git init` + one commit (tmp/gitcopy): 298 passed, rc 0 (raw/git-hygiene-final.log; test_hygiene, test_nosemgrep_form, test_file_call_guard, test_raw_bidi_chars, test_shell_single_bracket).
3. **A real slip found by that run and fixed:** the hygiene scan refused literals in my new test file (`127.0.0.2`, `127.0.0.3`, `http://:9`). They are now built from parts. Not seen before because tree-R7G has no .git.
4. test_real_check_dry first run printed "REPOSITORY FOLDER CHANGED BY THE TEST RUN" with rc 1 (79 passed): that was my own edit of tests/test_r7f_findings.py during the run. Re-run needed after the edit was not repeated for that single file; its 79 tests touch scripts/run_real_check.py, which I did not change, but the file is reported as `not clean-run on the final tree`. test_r7g_findings.py (which holds the real-check test) passed after the last edit.
5. NOT RUN: PowerShell, Python 3.13/3.14 (one test skipped for that), real mail/HubSpot/model services, Windows.
6. Slip (mine): I started the selector loop with a `< /dev/null` redirect typed inline, against the preamble rule; it ran and did no harm. I also killed my own too-slow selector run earlier (pids 19606/19613/19615, mine, recorded in checkpoint.md).
7. Machine was heavily loaded; test_clock_steps took 102 s, test_real_check_dry 202 s.
8. Odd-server pattern re-run was done on the code before the last test-only edits; the code did not change after (netconnect, load_driver, imap_count, constants are byte-identical between that run and the patch).

## NEEDED-CHECK v1
- M1 (Exception in helper thread): NEEDED. Same job in two places? Only `resolve_bounded` runs a look-up thread. Core helper? None.
- M1 host check for REAL_IMAP_*_HOST: NEEDED, reuses `smtp_outbox._HOST_NAME` (one regex for both mail hosts, DUPLICATE avoided; the check sits in `ImapSettings.validate`, the one place the settings are made).
- M2 (stop count): NEEDED, ONE function `stopped_count` read by the summary; exit code 3 reads `summary["stopped"]`.
- m1 (per-address time): NEEDED, `CONNECT_PER_ADDRESS_SECONDS` in constants.py.
- m2 docs: NEEDED. n1 socket close: NEEDED.
- load_driver `desk_listening`: NEEDED, routed through `connect_bounded` (a hung look-up could hang the old `socket.create_connection` past its 1 s; test shows it bounded). Removed the now-unused `socket` import and the file-call-guard table row for it.
- scripts/reset_check.py:27: NOT-NEEDED, it connects to the fixed address `127.0.0.1` (no look-up, so no hang class); unchanged, stated in docs/limits.md.

## What changed (7 files in src/load_tools, 4 docs, 2 tests)
- src/lead_desk/netconnect.py: look-up thread never ends with an exception (`contextlib.suppress(BaseException)` around the try; a non-OSError leaves the box empty); caller maps empty box to `OSError(LOOKUP_REFUSED_TEXT)` ("the host name cannot be looked up", no host, no class name). `connect_bounded`: every address except the last gets min(CONNECT_PER_ADDRESS_SECONDS=5, time left); last gets all time left; whole call inside the total deadline; socket closed on ANY exception (BaseException), only OSError moves to the next address.
- src/lead_desk/imap_count.py: `ImapSettings.validate` refuses a host that is not a plain host name (same regex as SMTP, case-insensitive) with ImapSettingRefused; run_real_check ends rc 2 with one line before the Start question (test).
- src/lead_desk/constants.py: CONNECT_PER_ADDRESS_SECONDS.
- load_tools/load_driver.py: `stopped_count` (counts `gave_up == "stopped"`, both kinds); summary and rc 3 read it; STOPPED_EARLY_TEXT now says "never sent or were given up"; `desk_listening` uses `connect_bounded`.
- tests/test_file_call_guard.py: removed the table row for `socket.create_connection` in load_driver (the call no longer exists; the guard test passes, 11 passed).
- docs/limits.md, docs/settings.md, load_tools/README.md, CHANGELOG.md.

## Helper-thread sweep (class: an exception type escaping a helper thread)
Checked by reading every threading.Thread target in src, scripts, load_tools, demo_only:
- Catch BaseException (nothing escapes): `live_claude.py` work(), `crm_hubspot.py` work(), `desk.py` worker work() and `_reaper_loop`, and now `netconnect.py` work().
- load_driver.py worker `run`: catches Exception around each request; a BaseException would end only that worker (not changed; it is KeyboardInterrupt/SystemExit only).
- demo_only/burst.py `one` and portal_demo.py `one`: the only call that can raise is `_post_once`, which catches (OSError, ValueError, HTTPException); UnicodeError is a ValueError. Probe with a 70-char label, `a..b` and a lone surrogate: `fire()` returned `['error','error']` for each, no traceback (command: tmp/burst_probe.py under unshare, run by me).
- server.py `_run`, `serve_forever` threads, run_real_check `_mirror`, demo fakes `_loop/_serve`: they take no host name from a user and loop on sockets they own; not a look-up class. NOT changed; stated, not tested.

## Tests
- New file tests/test_r7g_findings.py: 60 tests. On r7g: 60 passed (raw/new-r7g.log; with test_r7f_findings 139 passed, raw/new-r7g-final.log). On a copy of tree-R7F plus the new test file: 46 failed, 14 passed (raw/new-on-r7f-final.log). The 14 that pass on r7f are controls and the cases that were already right (named CONTROL in their docstrings).
- M1 cases through counts_by_key (mailbox read) and the SMTP path: 70-char label, empty label, lone surrogate, trailing-dot variants give ONE fixed line, empty stderr, no IndexError; run_real_check bad host rc 2 and one line.
- M2 loopback: first real request answered 202 after 2 s, other connections closed, burst:2, 1 worker, 2 threads: rc 3 and the true line (raw/odd-r7g.txt). Odd patterns, r7f vs r7g (raw/odd-r7f.txt, odd-r7g.txt): only202 rc0, only429 rc0, 503-for-3s-then-202 rc0, 503-twice-then-202 rc0, drops-3s-then-answers rc3 ("cannot be reached" line), drops-6-then-answers rc3: all UNCHANGED. burst:8 with first 202 after 3 s: rc3 on both, count now 7 (6 never sent + 1 given up) where r7f said 6. "First answered, then all dropped" burst:4: rc 0 after 62.2 s on both (the per-request limit rule in docs/limits.md, unchanged, stated there).
- **Test changed: tests/test_r7f_findings.py::test_m1_r7e_a_stopped_run_that_the_desk_answers_later_is_not_a_success.** Old assertions: `f"{len(stopped)} of 8 requests were never sent" in err` and `summary["stopped"] == len(stopped)` where stopped = lines with final_status driver:stopped. New: `taken` = lines with gave_up == "stopped"; `len(taken) >= len(stopped)`; `f"{len(taken)} of 8 requests were never sent or were given up" in err`; `summary["stopped"] == len(taken)`. Why not weaker: it still requires rc 3, still requires a stopped line and an answered line, still requires the number in the text to equal the summary, and the count is now taken from the log marker for both kinds (the old count was the bug: it missed the given-up request); the text of the line changed by design (M2 fix).
- No test deleted.

## Mutants (run by me on a copy, tmp/mut, restore checked by sha256; raw/mut-*.txt, raw/mut-summary.txt)
| id | file | mutation (exact text, shortened) | killing tests | result |
|---|---|---|---|---|
| N01 | netconnect.py | `contextlib.suppress(BaseException)` -> `contextlib.suppress(Exception)` | G, -k, whatever_the_lookup_raises | KILLED, restored sha ok |
| N02 | netconnect.py | `result = box[0] if box else None` -> `result = box[0]` | G, -k, empty_box or refuses_gives_one_fixed or whatever_the_lookup_raises | KILLED, restored sha ok |
| N03 | netconnect.py | `    if isinstance(result, OSError): /         raise result / ` -> `    if isinstance(result, OSError): /         raise OSError(LOOKUP_REFUSED_TEXT) / ` | G, -k, gaierror_and_a_lookup | KILLED, restored sha ok |
| N04 | imap_count.py | `if not isinstance(self.host, str) or not _HOST_NAME.fullmatch(self.host.lower()):` -> `if False:` | G, -k, settings_refuse or real_check_refuses | KILLED, restored sha ok |
| N05 | imap_count.py | `_HOST_NAME.fullmatch(self.host.lower())` -> `_HOST_NAME.fullmatch(self.host)` | G, -k, settings_still_take | KILLED, restored sha ok |
| A01 | netconnect.py | `own = left if index == len(addresses) - 1 else min(CONNECT_PER_ADDRESS_SECONDS, left)` -> `own = left` | G, -k, first_address_that_never or total_limit_holds | KILLED, restored sha ok |
| A02 | netconnect.py | `own = left if index == len(addresses) - 1 else min(CONNECT_PER_ADDRESS_SECONDS, left)` -> `own = min(CONNECT_PER_ADDRESS_SECONDS, left)` | G, -k, first_address_that_never or one_address_keeps | KILLED, restored sha ok |
| A03 | netconnect.py | `        if left <= 0: /             raise TimeoutError(LOOKUP_TEXT) /         own` -> `        own` | G, -k, total_limit_holds | KILLED, restored sha ok |
| A04 | netconnect.py | `except BaseException as e:  # closed` -> `except OSError as e:  # closed` | G, -k, closed_on_any_exception | KILLED, restored sha ok |
| A05 | netconnect.py | `raise last or OSError(\"no address for the host name\")` -> `raise OSError(\"no address for the host name\")` | G, -k, refused_on_every_address | KILLED, restored sha ok |
| D01 | load_driver.py | `return sum(1 for d in lines if d.get(\"gave_up\") == \"stopped\")` -> `return sum(1 for d in lines if d.get(\"final_status\") == \"driver:stopped\")` | G, -k, stopped_count or given_up_by_the_stop | KILLED, restored sha ok |
| D02 | load_driver.py | `return sum(1 for d in lines if d.get(\"gave_up\") == \"stopped\")` -> `return sum(1 for d in lines if d.get(\"gave_up\") == \"stopped\" and d.get(\"final_status\` | G, -k, stopped_count | KILLED, restored sha ok |
| D03 | load_driver.py | `    if summary[\"stopped\"]:  # r7f` -> `    if False:  # r7f` | G, -k, given_up_by_the_stop, F, -k, r7e_a_stopped_run | KILLED, restored sha ok |
| D04 | load_driver.py | `requests were never sent or were given up, because` -> `requests were never sent, because` | G, -k, given_up_by_the_stop | KILLED, restored sha ok |
| L01 | load_driver.py | `connect_bounded(parts.hostname or \"\", port, CONNECT_PROBE_SECONDS).close()` -> `__import__(\"socket\").create_connection((parts.hostname or \"\", port), timeout=CONNECT_P` | G, -k, listener_probe_is_bounded | KILLED, restored sha ok |
15 of 15 killed. (Pre-existing mutant sets from r7f were not re-run.)

## Evidence
- ruff 0.17.1 pinned: `check .` rc 0 "All checks passed!"; `format --check .` rc 0 "219 files already formatted" (raw/ruff-check.txt, ruff-format.txt; re-run after the final test edit, same result).
- Suppression counts r7f vs r7g (grep -c over the tree): noqa 175/175, type: ignore 126/126, nosec 8/8, nosemgrep 32/32, S603 7/7. Not grown.
- Selector files (one process each): all passed on r7g except the git-only ones listed in item 2 (re-run green in the git copy). Extra files: test_r7_exit_codes 32, test_r7b_burst_closed_port 3, test_http_guard 6, test_smtp_outbox 67, test_r7c_burst_probe_and_names 8, all passed. Per-file lines: sel-loop.txt and raw/pf-*.log, raw/x-*.log.

## Patches (out/R7G/)
core-fix-on-frozen-r7g.patch (CRLF), core-fix-on-frozen-r7g-lf.patch, core-fix-r7f-to-r7g-delta.patch, sha256-r7g.txt, apply-matrix-r7g.txt (a-crlf, b-crlf, c-lf: git apply --check rc 0 each). build check: BYTE-FOR-BYTE-SAME (frozen + patch = tree) and DELTA-ON-R7F-GIVES-R7G (raw/build-patches.txt).

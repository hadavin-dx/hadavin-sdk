# Review of r7c (core-fix-on-frozen-r7c.patch, delta r7b to r7c), fallback goldfish reviewer

Money and mail path, no round cap. Date 2026-11-14. Made-up data, loopback only, no spend. Scratch copies only (cp -a of tree-R7C); repo2, tree-R7B, tree-R7C untouched.

## NOT CHECKED / NOT RUN (first)
- EV7C evidence had NOT landed when I wrote this (only /home/user/build/rr6/out/EV7C/ partial files exist). If it lands later, it is not reflected here.
- No full suite. I ran: all test_r7c_* files that touch the findings (57 passed on the new tree, Python 3.12.3), test_hygiene with gitleaks on PATH and files staged (24 passed; history scan skipped by the test itself), and fail-before runs on a copy of R7B.
- PowerShell scripts (start_all.ps1, reset.ps1): read only, never run. Python 3.14: not tried (the IMAP reader replaces imaplib's `self.file`; I ran the greeting-drip case only on 3.12 and 3.13.18: 2.0 s against a 2 s limit).
- The stray file "a<newline>b" writer: not found by me either (I did not repeat the 129-file bisect).
- Ctrl-C behaviour (docs/settings.md:164 says it can still print a trace): background SIGINT is ignored in my shell, so inconclusive.

## Verdict
No Blocker. 2 Major (load_driver dead desk; live key not in the pre-Start secret check), 5 Minor. The r7b Major A (RecursionError) is fixed at one choke point. Every other r7b finding is closed except where listed below.

## Major

### M1. load_driver against a dead desk runs for hours (O-1 closed as "no change needed"; it is not)
Scenario: `python -m load_tools.load_driver --base-url http://127.0.0.1:1 --scenario burst:N --log L` (wrong port, desk not started).
Measured: N=3 took 31.7 s (exit 3, one line, good); N=300 took 62 s; N=1000 was still running at my 115 s limit (killed, no output). Every request retries until its own REQUEST_DEADLINE (about 30 s), 256 at a time, so time is about N/256 x 30 s: a 100,000-request burst on a wrong port holds the terminal for about 3 hours before the one refusal line. Spec: no hang on bad input; exit 3 (desk unreachable) quickly. R7C-RESULTS says "checked, no change needed (tests/test_r7b_burst_closed_port.py covers the burst)": that test is for demo_only/burst.py, not load_tools/load_driver.py. No test covers the driver.
Fix (load_tools/load_driver.py, one choke point before workers start): one TCP connect probe to the host and port of --base-url (1 s timeout, nothing sent); refused or timed out gives `ERROR: the desk cannot be reached...` exit 3 at once. Also stop all workers when the first K (for example 2 x threads) requests in a row end in a connection error with no success yet. Test: closed port, burst:100000, asserts exit 3 in under 5 s.

### M2. run_real_check --live-model: the live key file is not read before "Start?" (F-B class incomplete)
scripts/run_real_check.py:656-675 `check_secret_files(hs, pr, inboxes)` covers the HubSpot key, SMTP password and the mailbox passwords only. With `--live-model` the DESK_LIVE_KEY_FILE (config.py:231 only builds a Path) is first read inside the desk after Start?, after HubSpot calls and mails are already allowed. Library level is fine (live key read before the ledger reserve, live_claude.py:429), but the guarantee "bad secret refused BEFORE any connection" does not hold for this script's live path. Read by code; not run.
Fix: in `_run`, after `live = Config.from_env(...).live` (about line 1022) call `read_secret_line(live.key_file, "key", "key")` inside the same `except FileRefused/OSError -> ValueError("DESK_LIVE_KEY_FILE: ...")` shape, still before the question. Test: bad live key file with --live-model, `input` never called, exit 1.

## Minor

### m1. SMTP reply cap is not exact: replies over 64 KiB are still accepted (F-C only partly fixed)
src/lead_desk/smtp_outbox.py:150-162. The total is checked after each CONTINUATION line and for an unfinished buffer, but never for the line that ends the reply. Probe (loopback socketpair): 64,944 bytes of `250-` lines plus a 3,006-byte `250 y...` final line = 67,950 bytes: returns 250 (cap 65,536). A single 68,542-byte final line also returns 250 (same hole existed before). Overshoot is at most one 4096-byte read plus the buffer, so memory is bounded, but the stated guarantee ("over cap refused whole") is false and the new test only uses 4x the cap.
Fix: in the final-line branch (line 151) check `used + end + 2 > _REPLY_MAX_BYTES` and raise `_Closed("reply too long")` before returning; same in the bare-code branch. Tests at cap+1 for multi-line and single-line.

### m2. Tests that pass on the old code are not labelled CONTROL/pin
Reproduced on a copy of R7B (new tests, old src, loopback up): 8 failed, 27 passed. Passing on old: all 3 of test_r7c_mail6_killers.py (D05, D11, D20), test_r7c_burst_probe_and_names.py (all), test_r7c_head_deadline_errors.py (ALL 8; R7C-RESULTS says test_a_real_header_drip_prints_no_trace[hubspot] failed on old: I could not reproduce, so that number is wrong or flaky), test_r7c_invariants_output_size.py (builder admits). None carries the word CONTROL or pin in its docstring. They are not useless: I made mutants D11 (SMTP conn.close removed), D05 (IMAP no-LOGOUT line removed) and M7 (http_guard.py:196 `except OSError` to `except KeyError`): all killed (2/2 and 8/8). Fix: add "CONTROL (passes on r7b; pins behaviour, killed by mutant X)" to each module docstring and say so in the changelog of the round.

### m3. reset.ps1 file removal uses wildcard paths
scripts/reset.ps1:81-83 `Test-Path $f` / `Remove-Item -Force $f` and `Remove-Item $pidFile` (about line 70) without `-LiteralPath`. A database path such as `data\desk[1].db` is read as a pattern: Test-Path says no, nothing is deleted, and `reset done` is printed. The pid-file reads right above already use -LiteralPath, so the two halves disagree. Windows only, not run. Fix: -LiteralPath on all three.

### m4. start_all.ps1: first failure after a program is started leaves it running
scripts/start_all.ps1: `$ErrorActionPreference = 'Stop'` plus an exception in the second `Start-Process` (or a missing `python`) ends the script with a PowerShell error block (not one fixed line) and, for the second case, leaves the demo server and fakes.pid behind. Stop-Start only runs on the polled paths. Fix: wrap both Start-Process calls and Get-DeskSetting's python call in try/catch that routes to Stop-Start or a one-line exit 4. Not run on Windows (README claims parity with .sh; only text tests pin it).

### m5. IMAP total deadline can still be exceeded by the connect and TLS handshake
src/lead_desk/imap_count.py:230: the deadline is set before the connect, but `socket.create_connection` and the TLS handshake run under `timeout_seconds` (default step), not under min(step, time left). A server that accepts TCP and stays silent keeps the call for up to step seconds past the total (and DNS has no bound). Bounded, no secret involved. Fix: pass `timeout=min(s.timeout_seconds, s.total_seconds)` to the constructor.

## Closure of r7b findings (my own checks)
- A (RecursionError siblings): CLOSED. All 40+ parse sites now call `lead_desk.jsonread.loads_bounded` (src, scripts, load_tools, demo_only; grep for json.load/loads, from json import, JSONDecoder, raw_decode, literal_eval, yaml, pickle: only tests/support.py reads fixtures with json.loads). The AST scan test enforces it. Mutant M3 (loader without its catch): killed by 12 tests. Mutant M8 (RecursionError out of BAD_REQUEST_ERRORS): killed by 2 tests (test_r7c_bad_request_layers.py). Both layers now fail alone.
- Mail F-A (IMAP total deadline inside greeting, a line, a literal): CLOSED. `_DeadlineReader` (imap_count.py:97-150) bounds every recv by min(step, time left); fail-before confirmed on old (3 failed); new passes 3/3; also on Python 3.13. send() also bounded. See m5 for connect.
- F-B (secret files before Start): CLOSED for HubSpot, SMTP, IMAP (hostile files: binary, NUL, 5 MB, two lines, directory, FIFO, missing, empty, NUL in path all give the one fixed line naming only the SETTING; a symlink to a good file is accepted, as elsewhere). Open for the live key: M2.
- F-C: PARTLY (m1).
- Hygiene scan: CLOSED. test_hygiene 24 passed with the patch staged; scanner, patterns.txt, exceptions.txt untouched in the delta; failure message no longer cut at 50.
- O-2 (fake_model_server --port=0, empty/pipe/deep key file): CLOSED (rc 4, one line each; probed). Empty key file refusal is new; fail-before 3 failed on old.
- Stray-file guard incl. empty folders: CLOSED for the guard (tests/tree_guard.py compares empty folders, links, sizes, mtimes; only .git insides, .pyc inside __pycache__, three tool caches, coverage files are skipped; 13 tests incl. two session-hook tests that fail on old). The writer is still unfound: it is an open item the builder reported honestly; under the fix-dont-defer rule it needs an owner or a named next step.
- J loads_bounded location: CLOSED (src/lead_desk/jsonread.py; scripts/http_guard.py re-exports it; no duplicate left).
- Portal view size (F): CLOSED as claimed. PORTAL_VIEW_ROW_BYTES = 12 x (200+254+200) + 512; the test builds the worst CRM row through the real fake and asserts both numbers. Real desk record has exactly the six keys used (desk.py:1765). All portal fetches use ?limit=200 (portal_demo.py:350), same first-rows semantics as before.
- O-1: NOT closed (M1). O-3 invariants line count: a pin (passes on old). Burst probe sends nothing and "localhost" accepted: documented decision, pins only; burst.py itself has no diff.
- reset.sh exact command (H): CLOSED for .sh (argv from /proc, exactly `python* -m lead_desk.server` or the 7-word fakes form; matches what start_all.sh starts). reset.ps1 regex read only (m3).

## Changed old tests (strength check)
- test_r7_inputs 6200 rows to 3000: weaker in size (about 2.5 MB to about 1.2 MB body), but the cap it runs against fell from 38 MiB to 200 x 8360 + 4096 bytes by design, and it now asserts the body is under the real cap; the over-cap-refused-whole test is unchanged. Acceptable.
- test_r7b_portal_view_cap: same refusal assertions kept; "30000 rows read whole" became 4000 rows: justified by the limit query (the portal never asks for more). Acceptable.
- test_real_check_dry: stub deadline 0.0 to inf (0.0 only passed because old code ignored it) and real one-line secret files: acceptable; the refusal itself is tested in test_r7c_mail_killers.py (3 fail-before cases on old, all three setting families).
- test_reset_scripts: stand-ins now have the real command shape: same stop and leave-alone assertions. Acceptable.
- test_file_call_guard: one exact ALLOWED_CALLS entry (imap_count.py, super().open) with reason. Acceptable.

## Fail-before table (my runs, copy of R7B with new tests and new support.py)
Fail on old: test_r7c_mail_killers (4: three IMAP deadline cases, secret-file-before-Start), test_r7c_smtp_reply_total_cap (1), test_r7c_model_fake_cli (3, empty key file). test_r7c_one_json_loader cannot import on old (module missing: a collection error, not a behaviour failure; builder says 10 failed, 3 passed on an old copy that had the module path faked).
Pass on old (pins): mail6 killers 3, head_deadline 8, burst_probe/names all, invariants_output_size.

## Mutants I ran (all on copies)
M3 killed, M8 killed, M7 killed, D11 killed, D05 killed. Not run: D20, M-1 mutants of the IMAP reader, anything on the PowerShell scripts.

## Mail/secret guarantee table
Secrets never printed: check_secret_files names the setting only (probed). Bad secret before ledger reserve or connection: yes in the library; script run_real_check yes except the live key (M2). Named CA REPLACES system authorities, CERT_REQUIRED, check_hostname, TLS 1.2 floor before AUTH/LOGIN: no change in r7c to tls_trust; the D05/D11 killers kill the new close/no-LOGOUT lines. IMAP total deadline: yes inside greeting, line, literal; connect: m5. Reply over cap refused whole: IMAP literal yes; SMTP m1; HubSpot and model replies not re-read this round.

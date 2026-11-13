# notes-g2: numbers cross-check (README.md, SECURITY.md, versions.md, docs/limits.md, docs/portal.md)

Studio folder: not present in this container, so the studio rules were not read. No pytest, ruff or network was used. Code was only read (src/lead_desk/constants.py, gate.py, config.py, desk.py, server.py, portal_api.py, portal/portal.js, scripts/, demo_only/, tests/).

## Table (MISMATCH first)

| doc:line | claim | where checked | verdict |
|---|---|---|---|
| docs/limits.md:97 | the fake HubSpot server cuts off a Content-Length above 1 MiB, and "a client that really sends 1 MiB or more" may see a reset | demo_only/fake_hubspot.py:177-200 (MAX_BODY_BYTES 1,048,576; `int(text) <= MAX_BODY_BYTES` is read normally, only a value above it gets the early 400) | MISMATCH (exactly 1 MiB is read, so the reset can only happen above 1 MiB; fixed to "more than 1 MiB") |
| README.md:130 | full test run timed at 16 min 33 s on an earlier set | nothing in this tree (dated run, no log) | CANNOT-TELL (kept as labelled history) |
| README.md:130 | (same sentence, the 33 seconds) | same | CANNOT-TELL |
| docs/limits.md:67 | one byte every 1.9 seconds "was not tested here" | tests/test_slow_sender.py drips every 0.2 s, tests/test_stall_eviction.py every 0.1 s; EVICT_MIN_IDLE_SECONDS = 2.0 (constants.py), so 1.9 s is just under it; the text itself says untested | CANNOT-TELL |
| README.md:42 | reaper waits 1, 2, 4, 8 s, up to 5 automatic tries | gate.py:50-52 SEND_BACKOFF_SECONDS (1,2,4,8), SEND_MAX_ATTEMPTS 5 | OK |
| README.md:60 | loop waits up to 10 s | the loop is 10 rounds of `sleep 1` in the same line | OK |
| README.md:110 | clock jump of 30 s or more | desk.py:409 grace = int(send_timeout 5.0 + 5 x BUSY_WAIT 5.0) = 30; config.py:429 send_timeout default 5.0 | OK |
| versions.md:9 | 92 lines in collection output | `ls tests/test_*.py` gives 92 files; last file test_workflow_run_flags.py; its 10 = 1 + 4 + 4 + 1 with 4 files in .github/workflows | OK (the 3883 total cannot be rechecked without running pytest: CANNOT-TELL, not in the tsv) |
| docs/limits.md:10 | calls cut off after at most 9 s | constants.py MODEL_CALL_BUDGET_SECONDS 9.0, CALL_DEADLINE_MAX_SECONDS 9.0; desk.py:1433 `_call_deadline` = min(send_timeout, 9) | OK |
| docs/limits.md:13 | clock jump 30 s | as README:110 | OK |
| docs/limits.md:32 (x2) | AI budget 9 s; min(send_timeout_seconds, 9 s) | desk.py:1437; constants.py | OK |
| docs/limits.md:49 | waits 10, 60, 180, then 420 s; two earlier failed tries start at 60 s, three at 180 s | constants.py MIRROR_RETRY_WAIT_SECONDS (10,60,180,420); desk.py:825 step_i = (tries_before - 1) + (busy - 1) | OK (x3 rows) |
| docs/limits.md:56 | grace = send timeout + 5 busy waits of 5 s = 30 s | gate.py:46 SENDING_GRACE_BUSY_WAITS 5; constants.py BUSY_WAIT_SECONDS 5.0; desk.py:409 | OK (x3 rows) |
| docs/limits.md:57 | margin 15 s = 10 s write deadline + one wait; 9 + 15 = 24 s < smallest grace 25 s | gate.py:22-24 WRITE_DEADLINE 10; constants.py MODEL_GRACE_MARGIN_SECONDS 15.0; desk.py:115 floor 25; constants.py validate_model_budget (`>=` refused) | OK (x4 rows) |
| docs/limits.md:59 | adapter timeout above 9 s refused, exit code 4 | server.py:1130-1135 DeskSettingRefused -> EXIT_DESK_SETTING_REFUSED (4) | OK |
| docs/limits.md:77 (x3) | stuck for more than 30 s; one pass per second; put back 30 s later | gate.py REAPER_INTERVAL_SECONDS 1.0; desk.py:541-575 `updated_at < older_than` (strict); grace 30 | OK |
| docs/limits.md:81 (x5) | pass 10 s, three calls of at most 9 s, two reads (18 s), 10 + 27 + 18 = 55 s, grace 30 s, stop_background 10 s | gate.py:32-35 (REAPER_PASS_SECONDS 10.0, same 55 s sum); desk.py:639 stop_background timeout = BUSY_WAIT x 2 = 10 | OK |
| docs/limits.md:93 | waiting line 1024 | constants.py LISTEN_QUEUE 1024 | OK |
| docs/limits.md:95 (x4) | first wait 0.1 s, doubles to 1 s, Retry-After honoured up to 1 s, 30 s after the first | constants.py BURST_BACKOFF_SECONDS 0.1, MAX 1.0, DEADLINE 30.0; demo_only/burst.py:55-92 | OK |
| docs/limits.md:97 (first) | Content-Length longer than 7 digits or above 1 MiB gets 400 | fake_hubspot.py:187-200 (len(str(1048576)) = 7) | OK |
| docs/limits.md:98 | 408 10 s after the headers ended | constants.py BODY_READ_DEADLINE_SECONDS 10.0; server.py:613 HTTP_REQUEST_TIMEOUT | OK |
| docs/limits.md:112 | list part at most 3,132,800 bytes, 50 messages | tests/test_later_messages.py:165-166 (50 x (2 x (200+40+200+2000) x 12 + 4096) = 3,132,800); DUPLICATES_MAX 50 | OK |
| docs/limits.md:115 and docs/portal.md:5 | masked value shows for 30 s | src/lead_desk/portal/portal.js:227 REVEAL_MS = 30000 | OK (x2) |
| docs/limits.md:118 | reply write limit 5 s | constants.py REPLY_WRITE_TIMEOUT_SECONDS 5.0 | OK |
| docs/limits.md:119 (x2) | 4 files per thread plus 96; 1024 threads = 4192 | constants.py FDS_PER_HANDLER_THREAD 4, FD_RESERVE 96, MAX_HANDLER_THREADS 1024; server.py:1064 need = 4 x threads + 96 = 4192 | OK |
| docs/limits.md:121 | exit code 4 for timeout above 9 s | server.py:1130-1135 | OK |
| docs/limits.md:122 | about 10 s then SIGKILL | server.py:1093 comment and stop_background default 10 s | OK |
| docs/limits.md:124, 125 | header and body deadlines 10 s each | constants.py HEADER_READ_DEADLINE_SECONDS, BODY_READ_DEADLINE_SECONDS 10.0 | OK (x2 rows) |
| docs/limits.md:126 (x3) | 256 connections; 2 s idle before closing for room; crowd sends a byte every 0.1 s | constants.py MAX_CONNECTIONS 256, EVICT_MIN_IDLE_SECONDS 2.0; tests/test_stall_eviction.py:95,109 | OK |
| docs/limits.md:138 (x3) | waits 10, 60, 180, 420 s; five tries; about 11 minutes | constants.py MIRROR_RETRY_WAIT_SECONDS, MIRROR_MAX_TRIES 5; sum 670 s = 11.2 min | OK |

Row count: 54 rows of g2.tsv. OK 50, MISMATCH 1 (fixed 1), CANNOT-TELL 3.

## Also checked (b), (c), (d)

Exit codes (b):
- README.md:68 start/reset script run with sh: "exit 2": scripts/start_all.sh:12 `exit 2`, reset.sh:12 `exit 2`. OK.
- README.md:90 reset exit codes 2 (path outside data, bad RESET_STOP_WAIT_SECONDS), 3 (process holds database, data folder cannot be looked at, ps missing), 4 (port answers), 5 (did not stop), 6 (pid file names another program): scripts/reset.sh, reset.ps1:11,21,36,40,47, reset_check.py:36-52. OK. RESET_STOP_WAIT_SECONDS 0 to 999, empty means 10: reset.sh `${...:-10}` and the 0|[1-9]|... pattern; reset.ps1 regex. OK.
- docs/limits.md:58 exit 1 for a constant that does not fit (Python error at load): server.py main docstring and constants.py import-time checks. OK.
- docs/limits.md:121-122 exit codes 1, 2, 3, 4, 5: server.py:1107-1213 and constants.py EXIT_*. OK (1 sender unreachable, 2 lock, 3 open-file limit, 4 refused setting, 5 bind).
- docs/limits.md:137 and earlier text: 137 is not stated in my files. n/a.

HTTP status codes (b):
- README 201 for a new lead and for a replay of a new lead, "duplicate" through the other door: desk.py:1276-1299 (new 201, duplicate 200, review 202). OK. limits.md:31 "201=1 and 200=9": test_http.py:54-55. OK.
- README.md:88 404 for unknown address: server.py:552-555, 796, 844. OK.
- limits.md:53 409 `call_still_running`: desk.py:2274. OK.
- limits.md:98, 124, 126 408, 413, 400, 503 with `Retry-After: 1`: server.py:613, 857, 853, 463; constants.py BUSY_RETRY_AFTER_SECONDS 1. OK.
- docs/portal.md 403 for Host/Origin: server.py:761. OK.

Defaults (c):
- Ports 8765 and 8766: config.py:424,427. Python 3.12 or newer: pyproject.toml requires-python. OK.
- send timeout default 5 s behind the 30 s grace: config.py:429. OK.
- Lock file counts in versions.md (19 and 18 pinned lines): `grep` of `==` lines: requirements-dev-win.txt 19, requirements-dev.txt 18. OK.

Limits "at most N / N times" (d):
- 5 automatic tries (README:42, limits:35, 61, 79, 80): SEND_MAX_ATTEMPTS 5; desk.py:555-575. OK.
- "put back five times in a row ends failed": desk.py:555-560 auto_attempts >= SEND_MAX_ATTEMPTS. OK.
- at most 4 AI calls, 8 CRM puts, 8 sends, 4 capability reads: ADAPTER_WORKER_CAPS. OK.
- at most 8 portal requests: PORTAL_MAX_INFLIGHT 8. OK.
- ten crash points plus N1: hooks.py HOOK_POINTS (5) + MORE_HOOK_POINTS (6) = 11. OK.
- real kill at D2 twice (keyed, blind HTTP) and once (SMTP): tests/test_http.py:293 (parametrized), 336. OK.
- test_ten_parallel for 10 and the ten racing claims: test_http.py:43, test_reminder_email.py:113. OK.
- ten crash points, "at most 256 / 1024": constants.py. OK.

Not checked: the 3883 test total (needs pytest), vendor and tool versions in versions.md, "150" and "300" connection figures and "about 11 minutes" real timing (author's runs).

## Edits made

1. docs/limits.md:97: "a client that really sends 1 MiB or more may therefore see a connection reset" -> "a client that really sends more than 1 MiB may therefore see a connection reset". Reason: a body of exactly 1 MiB is read and answered normally (fake_hubspot.py `<= MAX_BODY_BYTES`).

No other file changed.

## CODE-LOOKS-WRONG

None found.

# notes-g1: numbers cross-check of contract.md against the code

Studio folder and bible were not available in this container (not read, no R-numbers cited). Read-only on code; only contract.md edited. No tests, linters, network or agents run, so nothing here is "run"; every verdict is from reading code (and test source).

## Verdict table (MISMATCH first)

| doc:line | claim | where checked | verdict |
|---|---|---|---|
| contract.md:309 | a pass can overrun by "about 55 s at the very worst" | gate.py:29-35 (10 + 27 + 18 = drives plus two capability reads); desk.py:745-758 (after the drives the same pass runs _mirror_pass and _nudge_pass, own clocks MIRROR_PASS_SECONDS 2.5, NUDGE_PASS_SECONDS 2.5, gate.py:38-39) | MISMATCH: 55 s is the drive part only, not the whole pass (fixed) |
| contract.md:155 | server "reads at most one byte more than size_cap_bytes of a body" | server.py:_post_lead (n > cap: 413 before any read), _resolve, _step; contract.md:158 itself says "before any body byte is read" | MISMATCH: no byte of an over-cap body is read; a body is read only when the announced length is at most the cap (fixed) |
| contract.md:137 | the reserve covers "item by item (FD_RESERVE_ITEMS)" and lists 7 items | constants.py FD_RESERVE_ITEMS has 9 items: also lingering refused connections (16) and abandoned adapter workers (ADAPTER_WORKERS_TOTAL = 4+8+8+4 = 24); sum = 66 <= 96 | MISMATCH: list incomplete (fixed) |
| contract.md:173 | refused connect to a closed local port reports after about 2 seconds on Windows | author's own run, no log shipped | CANNOT-TELL (kept as it is) |
| contract.md:138 | "4096 is a common container default" open-file limit | vendor/environment fact | CANNOT-TELL |
| contract.md:27 | 254 characters | constants.py:38 EMAIL_MAX; identity.py:93-94 (len(normalise_email) <= EMAIL_MAX) | OK |
| contract.md:31 | 9 s model budget | constants.py MODEL_CALL_BUDGET_SECONDS 9.0 | OK |
| contract.md:34 | 8 threads at once, at most 4 workers | tests/test_hung_adapter_calls.py:358-398 (parties = 8, MODEL_HUNG_MAX = 4, ADAPTER_WORKER_CAPS model 4) | OK |
| contract.md:35 | 5 s MODEL_BUSY_BACKOFF_SECONDS | gate.py:66 | OK |
| contract.md:38,45,284,312 | grace = send timeout + 5 busy waits = 30 s | desk.py:406-409 int(5.0 + 5*5.0) = 30; gate.py SENDING_GRACE_BUSY_WAITS 5; config.py:429 send_timeout 5.0 | OK |
| contract.md:39 (15 s) | MODEL_GRACE_MARGIN_SECONDS | constants.py 15.0 | OK |
| contract.md:39 (10 s) | write deadline 10 s | gate.py:24 GATE_WAIT 5 + BUSY 5 | OK |
| contract.md:39,45,84,123,157,171,253,256,311,312 (5 s) | busy wait / bind retry / reply write / no-descriptors backoff / in-flight wait / drive wait / "just now" under 5 s | constants.py BUSY_WAIT 5.0, BIND_RETRY 5.0, REPLY_WRITE 5.0; gate.py:61 NO_DESCRIPTORS 5, INFLIGHT_WAIT 5, DRIVE_WAIT 5; portal.js:188 (sec < 5 'just now') | OK |
| contract.md:40 | smallest grace 25 s; 9 + 15 = 24 | desk.py:111-117 (5 * 5.0); validate_model_budget uses >= (equal refused) | OK |
| contract.md:41,131,143 | limit 9 s, 9 accepted, 9.1 refused; AI call budget 9 s | config.py:161, 210 (high=MODEL_CALL_BUDGET_SECONDS); desk checks "above budget" | OK |
| contract.md:104 | host name at most 253 characters, labels 1 to 63 | constants.py HOST_NAME_MAX 253; config.py _LABEL (1 + up to 61 + 1) | OK |
| contract.md:104 | Host port above 65535 refused | constants.py PORT_MAX 65535 | OK |
| contract.md:115,215 | q at most 100 characters | constants.py SEARCH_MAX; portal_api.py:366 | OK |
| contract.md:115,163 (8, 256, 1024) | PORTAL_MAX_INFLIGHT 8; MAX_CONNECTIONS 256; MAX_HANDLER_THREADS 1024; ranges 8..4096 and 8..65536 | constants.py | OK |
| contract.md:135,137,170 | 4 files per handler thread; 8 portal connections x 2 files | constants.py FDS_PER_HANDLER_THREAD 4, FD_RESERVE_ITEMS | OK |
| contract.md:138 | need = 4 x 1024 + 96 = 4192 | server.py:1064 need = FDS*threads + FD_RESERVE; FD_RESERVE 96 | OK |
| contract.md:148 | ACCEPT_PAUSE 0.05 s | constants.py; tests/test_stamp_locks_and_budget.py:414 | OK |
| contract.md:149 (two rows) | reaper join waits up to 10 s | desk.py:639 stop_background timeout BUSY_WAIT*2 = 10; server.py:1093 comment | OK |
| contract.md:155,156 | DRAIN_TOTAL 1 s; HEADER/BODY deadline 10 s | constants.py | OK |
| contract.md:157 (two rows) | REPLY_WRITE 5 s; REQUEST_TIMEOUT 30 s | constants.py | OK |
| contract.md:158,187 | BODY_READ_DEADLINE 10 s | constants.py | OK |
| contract.md:167 | QUIET_DRAIN 0.05 s | constants.py | OK |
| contract.md:163 | EVICT_MIN_IDLE 2 s | constants.py | OK |
| contract.md:215,220,264 | 100 / 18 digits; zero-padded past 18 characters is 400 bad_query / 404 | portal_api.py:125 (len(raw) > MAX_DIGITS, leading zeros counted); desk.py:2184 and server.py:553 (404) | OK |
| contract.md:238 (four rows) | burst waits 0.1 s doubling to 1 s, Retry-After up to 1 s, 30 s deadline | constants.py BURST_*; demo_only/burst.py:57-92 | OK |
| contract.md:248,278 | 3 tries | gate.py DECIDE_FAIL_LIMIT 3 (line 248 is the same count); lockfile.py:24 _LOCK_TRIES 3 | OK |
| contract.md:256,303 | 1, 2, 4, 8 s; 5 tries | gate.py:50-52 SEND_MAX_ATTEMPTS 5, SEND_BACKOFF (1,2,4,8) | OK |
| contract.md:266 | 1 MiB | constants.py REPLY_MAX_BYTES 1_048_576 | OK |
| contract.md:308 | every 30 s OUTBOX_REFRESH | gate.py:51 | OK |
| contract.md:310 (two rows) | WRITE_DEADLINE 10 s; REQUEST_DEADLINE 15 s | gate.py:24-25 | OK |
| contract.md:312 | 9 s + 15 s; 10 s + 5 s | constants.py, gate.py | OK |

(Rows of g1.tsv: 63. OK 61, MISMATCH 1, CANNOT-TELL 1. Rows that share a line and value are merged above. The two extra MISMATCH rows and the 4096 row come from my own reading, not from g1.tsv.)

## (b) Exit codes and HTTP statuses checked

- Exit: 1 EXIT_ADAPTERS_UNREACHABLE (server.py:1169), 2 EXIT_ANOTHER_DESK (1145/1148), 3 EXIT_SETTING_REFUSED (1127, open-file limit only), 4 EXIT_DESK_SETTING_REFUSED (1132..1213), 5 EXIT_PORT_UNAVAILABLE (1186), 137 EXIT_SIMULATED_KILL; a constant out of range gives a traceback (exit 1): all agree with contract.md:131 and :40.
- HTTP: 200/201/202 (desk.py:1281-1295), 400 bad_envelope/bad_decision/bad_step/bad_expected/bad_query/bad_body/bad_request, 403 forbidden_host/forbidden_origin/not_an_approver, 404 not_found/no_state, 405, 408 request_timeout (server.py:613), 409 in_progress/unknown_needs_person/not_retryable/not_actionable/not_unknown/wrong_decision/call_still_running/already_decided/not_to_check, 413 too_large (POST /leads, resolve, step, demo body), 422 refused and 404 no_contact in the fakes (demo_only/fakes_server.py), 500 internal, 501 not_implemented (send_error; tests/test_input_edge_cases.py:51), 503 busy/unavailable (+ reason, Retry-After 1 = BUSY_RETRY_AFTER_SECONDS), 308 redirect (server.py:828): all agree with the prose and tables, including lines 14-20 of contract.md.

## (c) Defaults checked

- send_timeout_seconds 5.0 (config.py:429); port 8765 / fakes port 8766 (config.py); fakes `--crm` default keyed, `--outbox` required (fakes_server.py:242-244); DESK_LATER_MODE default off; DESK_LEADFLOW_FILE unset/empty/off = off; `PRAGMA user_version` 1 (SCHEMA_VERSION); `limit` default 50 (LEADS_LIMIT_DEFAULT) and 100 (LOG_LIMIT_DEFAULT); `offset` 0..100000 inclusive (portal_api.py:370); requirements locks: 18 pinned lines Linux, 19 Windows, the only difference is colorama (checked by diff of name==version lists), Python 3.12 / 3.13 from the lock file headers; 1300 px (leads.css:67 and tests/test_portal_layout.py:76); 1240 px etc. not claimed in prose.

## (d) Limits "at most N / N times" checked

- at most 4 model workers (and crm 8, send 8, refresh 4: "four refresh places" OK); 32 in-flight places and 8 drive places; 16 lingerer sockets; 50 duplicates listed (DUPLICATES_MAX); 128 source_ref (1..128); 5 automatic tries; 3 undecided tries; 18 digits; 9 pinned test cases in test_backfill_classes (nine parameter rows); 8 replays and 20 replays in the cited tests (tests/test_desk_http_edge_cases.py:1490, tests/test_flow.py:87); 20 restarts (RESTARTS = 20); 4301 / 4401 digits (tests use "9" * 4301 and 10 ** 4400); two partial indexes (schema.sql:118, 120); crash points 5 + 5 (+ N1) vs hooks.py:14-19.

## Edits made (contract.md only)

1. Line 137: "... (8 at once, 2 files each) and the reaper's adapter socket; the desk refuses" -> "... (8 at once, 2 files each), the reaper's adapter socket, the refused connections the lingerer keeps open for a moment (16) and the sockets of abandoned adapter calls (24, the sum of the worker caps); the desk refuses".
2. Line 155: "The server reads at most one byte more than `size_cap_bytes` of a body (enough to see that it is over the cap); after an early reply" -> "The server reads a body only when its announced `Content-Length` is at most `size_cap_bytes`; a longer announced body is answered 413 before any body byte is read; after an early reply".
3. Line 309: "so a pass can overrun (about 55 s at the very worst with the defaults, `gate.py` comment); the rows" -> "so the drive part of a pass can overrun (about 55 s at the very worst with the defaults, `gate.py` comment; the CRM copy part and the reminder part that follow in the same pass each have their own 2.5 s clock, checked between calls, and add their own time on top); the rows".

## CODE-LOOKS-WRONG

- src/lead_desk/gate.py:29-35 (comment on REAPER_PASS_SECONDS): says a pass "can overrun ... 10 + 27 + 18 = 55 s at the very worst", but desk.py:754-758 runs _mirror_pass and _nudge_pass in the same reap_once after the drives (clocks MIRROR_PASS_SECONDS 2.5 s and NUDGE_PASS_SECONDS 2.5 s, each can end one bounded call late). Evidence: the order of calls in reap_once. Not edited (code comment); the figure is true for the drive part only. Failing example: a pass with slow drives plus a due CRM copy and a due reminder takes more than 55 s.
- Not wrong, but worth a look: contract.md:138 repeats "or the container's own setting" twice in one sentence (words only, no number; left as it is).

# Signed trigger door: HMAC endpoint, worker, crash helper, n8n template

State of 2026-11-20 after the lead's order 015, steps D and E. This replaces the first version written at about 13:00 UTC.
The coordinator strips every `[path:line]` proof in square brackets before pasting. Paths are repo-relative; `integ:` means the merged tree /home/user/wt/integ (read-only). Sentences are at most 30 words. RECEIVED, WORKING and NEEDS_PERSON are run states: "stored, not started", "loop running" and "a person must look". "The tick" is the scheduled step that ends stuck runs.

No PR template exists in the repo (`.github/` holds only `dependabot.yml` and `workflows/ci.yml`), so this follows the headings of the handover tickets. [.github/workflows/ci.yml:1]

## What it is
A signed HTTP door that starts one agent run per caller key. One worker process serves the endpoint and runs the agent loop.
- `src/hadavin_sdk/triggers/endpoint.py` (pure checks and a WSGI callable), `worker.py` (`Runner`, start-up checks, `main`) and `server.py` (the stdlib server made quiet). [src/hadavin_sdk/triggers/endpoint.py:1-8; src/hadavin_sdk/triggers/worker.py:1-6; src/hadavin_sdk/triggers/server.py:1-8]
- `src/hadavin_sdk/testing/crash.py` (step E): `CrashPoints` stops a test at a named place, in process (`SimulatedCrash`, a BaseException) or as a child exit with code 137. It can be built only inside pytest. [src/hadavin_sdk/testing/crash.py:67-71; src/hadavin_sdk/testing/crash.py:119-131]
- `n8n/hadavin-trigger.json`, `n8n/hadavin-trigger-error.json` and `n8n/README-trigger.md`: a sender template, run once in n8n 2.47.7. [n8n/README-trigger.md:3]
- Start: `python -m hadavin_sdk.triggers.worker --config-dir <dir> [--host H] [--port P] [--allow-non-loopback]`. [src/hadavin_sdk/triggers/worker.py:47]

## What it guarantees
- **Signature.** HMAC "v0", `"v0=" + hex(HMAC_SHA256(secret, "v0:{ts}:" + body))`, within a 300 second window. [src/hadavin_sdk/approvals/hmac_v0.py:19; src/hadavin_sdk/approvals/hmac_v0.py:47] Nothing of the body is parsed before the signature verifies. [src/hadavin_sdk/triggers/endpoint.py:3-5; tests/endpoint_mutants.py:12]
- **One run per key.** It rests on the primary key of the runs table, not on process memory, so it holds across restarts and several processes. [src/hadavin_sdk/triggers/worker.py:12-14]
- **Ack only after the row exists.** A 2xx is sent only after `store.get_run` returned a row for the same agent, principal and `trigger_ref`. 202 means RECEIVED or WORKING; 200 means a later state. [src/hadavin_sdk/triggers/worker.py:1-6; src/hadavin_sdk/triggers/worker.py:549-558]
- **409 and its audit event.** The same key with another document is a 409 and no run is written. [src/hadavin_sdk/triggers/worker.py:549-556] A signed 409 writes one `trigger.conflict` audit event with ids and both document hashes, never the document or the signature. [src/hadavin_sdk/triggers/worker.py:530-545]
- **The event cap is a setting.** At most `triggers.conflict_events_per_minute` events per sender per minute are written; the rest are counted. [src/hadavin_sdk/triggers/worker.py:387-398] The worker reads the number from the configuration only. A settings object without the field is a start error, exit 2. [src/hadavin_sdk/triggers/worker.py:717-721; tests/triggers/test_d_fix24_conflict_setting.py:70]
- **`max_running` is read from the configuration only.** The worker holds no second default; a settings object without the field is a start error, exit 2. [src/hadavin_sdk/triggers/worker.py:103-104; src/hadavin_sdk/triggers/worker.py:714-716; tests/triggers/test_d_fix22_max_running.py:50; tests/triggers/test_d_fix22_max_running.py:73] The default 4 and the bound 64 are core-b's `TriggerSettings`, true only on the merged tree. [integ:src/hadavin_sdk/defaults.py:280-281; integ:src/hadavin_sdk/config.py:395-425]
- **Status codes.** Every refusal has an empty body. 400 is malformed. 401 is a bad signature or timestamp. 404 is another path and 405 another method. 413 is a body over `max_body_bytes`, answered before the body is read. 414 is a request line over 64 KiB. 431 is headers too large. [src/hadavin_sdk/triggers/endpoint.py:345-358; src/hadavin_sdk/triggers/server.py:50-58] A 503 from the endpoint always carries `Retry-After: 1`. The 503 sent when the application itself raised does not. [src/hadavin_sdk/triggers/endpoint.py:407; src/hadavin_sdk/triggers/server.py:177-178]
- **Header cap.** Request line plus headers may be at most 16382 bytes (16384 with the blank line). 16381 and 16382 pass; 16383 and over give 431. [src/hadavin_sdk/triggers/server.py:11; src/hadavin_sdk/triggers/server.py:57-58; tests/triggers/test_d_fix18_door_fixes.py:86-104]
- **HTTP refusal contract.** The server writes its own 400, 414 and 431 in one write, with `Content-Length: 0` and `Connection: close`, and never repeats the request. [src/hadavin_sdk/triggers/server.py:240-256] HTTP 2.0 or higher, an underscore in a header name, two `Content-Length` headers and any `Transfer-Encoding` are answered 400. [src/hadavin_sdk/triggers/server.py:13-21]
- **One write per normal answer**, so a killed worker cannot leave a bare 2xx status line. [src/hadavin_sdk/triggers/server.py:187-200; tests/triggers/test_d_fix13_single_write.py:192]
- **Bounded.** `max_running` pool, at most 128 waiting requests, 256 connection slots and a 30 second absolute read deadline. [src/hadavin_sdk/triggers/worker.py:112; src/hadavin_sdk/triggers/server.py:54; src/hadavin_sdk/triggers/server.py:60]
- **Exit codes 0, 2 and 3.** SIGTERM drains the loops and exits 0; 2 is a refused configuration; 3 is any other start failure. [src/hadavin_sdk/triggers/worker.py:125; src/hadavin_sdk/triggers/worker.py:845-879; src/hadavin_sdk/triggers/worker.py:1169-1177; tests/triggers/test_t5_process.py:176]
- **Degraded start recovers in process.** A store that is down at start is not an exit. The worker answers 503 everywhere but `/health`, retries every 5 seconds and swaps in the real app when the store answers. [src/hadavin_sdk/triggers/worker.py:947-1008; src/hadavin_sdk/triggers/worker.py:1060-1080; tests/triggers/test_d_fix8_e1fix.py:71]
- **`GET /health`.** 200, or 503 with `Retry-After: 1`, with a body of exactly `status` and `store_failures`; no signature is needed. [src/hadavin_sdk/triggers/endpoint.py:120-131; src/hadavin_sdk/triggers/endpoint.py:134-148; tests/triggers/test_d_fix6_e1.py:266]
- **Memory store refused outside the demo stage** (exit 2). [src/hadavin_sdk/triggers/worker.py:669-682; tests/triggers/test_d_fix18_door_fixes.py:116]
- **Spend with parallel runs (true only on the merged tree).** The main model call of a run reserves its worst case before the call and settles after it. The worker warns at start only when `max_running` is above 1 and the limits have no `reserve`. [integ:src/hadavin_sdk/runtime/agent_loop.py:567; src/hadavin_sdk/triggers/worker.py:685-696]
- **Crash matrix.** A worker child is killed at 43 points of the "nothing to do" path on PostgreSQL 16; 39 of them also run on the memory store. It is killed at 171 more points on the read, propose and approve paths, on both stores. At every point there is at most one run row and one approval request per key. No second model call follows a kill when a row exists. A retry gets 200 or 202. [handover/core-a/CRASH-MATRIX.md:7; handover/core-a/CRASH-MATRIX.md:91-93; handover/core-a/CRASH-MATRIX.md:107-109]
- **Crash matrix, money end state (true only on the merged tree).** With core-b's live loop each point also reads the money rows. One open hold stays open until expiry, a restarted run never books again, and the day total equals the sum of the rows. [tests/triggers/crash_money.py:1-20; tests/triggers/crash_launcher.py:60]
- **Mutation testing and fuzzing.** `tests/endpoint_mutants.py` reverts one guard at a time. `tests/triggers/test_fuzz_endpoint.py` runs four seeded properties of 300 cases each. [tests/endpoint_mutants.py:1-8; tests/triggers/test_fuzz_endpoint.py:2-14]

## What it does NOT guarantee
- **A cut-off run is acknowledged, then NEEDS_PERSON, with no notification and no stored document.** The sender must poll the run state. The owner decision is open, called E-door-1 in handover/core-a/ESCALATIONS.md: option A (the sender polls, the default) stands; option B (store the document, notify a person) is not built. [src/hadavin_sdk/triggers/worker.py:36-39; handover/core-a/ESCALATIONS.md:3-8]
- **There is no read address for a run.** The door answers `POST` on its trigger path and `GET /health` only. Polling means sending the same signed key and document again. A 200 does not mean "ended": PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING and VERIFYING also answer 200. [n8n/README-trigger.md:617-626; handover/core-a/CRASH-MATRIX.md:120]
- **A reverse proxy with per-peer connection limits is required.** The server has 256 global slots and no per-peer limit. TLS is the proxy's job. By default it listens on 127.0.0.1 only. [src/hadavin_sdk/triggers/worker.py:42-43; src/hadavin_sdk/triggers/worker.py:47-49]
- **One secret per tenant and per stage.** The tenant is not in the signed string, so a shared secret makes a request for one tenant or stage valid for another within the 300 second window. The same value under two senders is refused at start; reuse on another worker cannot be seen. [src/hadavin_sdk/triggers/worker.py:44-45; src/hadavin_sdk/triggers/endpoint.py:243-266]
- **n8n queue mode is recommended and NOT verified.** It was never run. The caller's 202 is given before anything is stored in Hadavin. In default mode a restart during a 60 second wait lost the run; waits of 70 and 120 seconds survived once each; a restart during a send was not run. [n8n/README-trigger.md:209; n8n/README-trigger.md:883]
- **The tick must run in the deployment**, or a cut-off run never reaches NEEDS_PERSON. [src/hadavin_sdk/triggers/worker.py:36-37]
- **The money crash points do not exercise the real window.** The child's seeding widens `max_day_skew` and `min_expiry_age`, so neither the real day window nor the 3600 second expiry floor is tested there. [tests/triggers/crash_launcher.py:18-26]
- **Not run:** Windows; in n8n the 45 second timeout, 3xx, 502/503/504 with a body, 520 to 524, `Retry-After`, 45 exhausted rounds, states other than NO_ACTION, n8n Cloud and queue mode. [n8n/README-trigger.md:100-110; n8n/README-trigger.md:883]
- **`worker.main` starts only on a tree that has core-b's `Config.triggers` and `App.trigger_secret`.** Elsewhere it exits 2. [src/hadavin_sdk/triggers/worker.py:573-578; src/hadavin_sdk/triggers/worker.py:650-654]

## Tripwires (what to watch)
- Worker exit code: 0 clean stop, 2 configuration error, 3 anything else. [src/hadavin_sdk/triggers/worker.py:125]
- `GET /health` 503, and the WARNING "store re-check failed (class): still degraded", at most every 5 minutes. [src/hadavin_sdk/triggers/endpoint.py:120-131; src/hadavin_sdk/triggers/worker.py:138-140]
- Audit events `trigger.conflict`: a sender reusing a key with another document. [src/hadavin_sdk/triggers/worker.py:530-545]
- Runs in NEEDS_PERSON "interrupted". [src/hadavin_sdk/triggers/worker.py:36-39]
- WARNING "trigger conflict events ... not written so far" when the cap is reached or a write is pending; the connection-cap WARNING at most once a minute. [src/hadavin_sdk/triggers/worker.py:408-415; src/hadavin_sdk/triggers/server.py:70]

## Evidence (each number is quoted from the file named; run 20 is not read yet)
- Merged tree (core-b 463760813, core-a d1ee703ab, core-c bd7f9d978, then the door test support): `tests/triggers` with `HADAVIN_REQUIRE_PG=1` on PostgreSQL 16: 1374 passed, 4 skipped, 0 failed. [handover/core-a/INTEGRATION-DOOR-FIX.md:25-27]
- Mutants: the last full run is in `handover/core-a/evidence/mutants-run19.md` (120 of 120 expected at 5a8c83fd3). See that file and run 20 when it lands. [handover/core-a/evidence/mutants-run19.md:2-3]
- Crash matrix: `handover/core-a/CRASH-MATRIX.md` (Part 1 and Part 2), raw logs `raw/D-crash-matrix-pg16.log` and `raw/D-crash-matrix-paths-pg16.log`. [handover/core-a/CRASH-MATRIX.md:3; handover/core-a/CRASH-MATRIX.md:101]
- Older whole-suite batch on core-a alone, head 6e61005db, `REQUIRE_PG=1 -n 3`: 12 failed, 12366 passed, 458 skipped, 75 xfailed. The 12 are 10 strict-mode tests that need core-b's `TriggerSettings`, the dblink test and the brand-string rule. [handover/core-a/evidence/BATCH10-summary.md:1-20]
- Reviews: `handover/core-a/reviews/D-code-result-review-1..5.md`, `E-result-review-1..6.md`, `n8n-result-review-1.md`. n8n evidence: `handover/core-a/inputs/evidence-n8n-*.md`. Tested-state notes: `handover/core-a/TESTED-D.md`, `TESTED-n8n-E-T4.md`.

## Rollback
Stop the worker and remove the `triggers:` block from `config.yaml`: the worker then refuses to start (exit 2). [src/hadavin_sdk/triggers/worker.py:573-578] Nothing migrates: the door adds no table, role or grant and uses the existing runs table. Runs already written stay as ordinary run rows. The n8n workflows can be deactivated in n8n.

## Test plan
Run from the repo root.
1. `HADAVIN_REQUIRE_PG=1 .venv/bin/python -m pytest tests/triggers tests/test_testing_crash.py tests/test_mutants_anchors.py -n 3`. [tests/triggers/test_t5_strict_mode.py:1-10]
2. With a throwaway PostgreSQL, add `HADAVIN_TEST_PG_DSN=<superuser dsn>` to run the database and kill tests. Without it they skip. [tests/triggers/test_t5_postgres.py:1-12]
3. `.venv/bin/python tests/endpoint_mutants.py` (mutation run, about 4 minutes; it ended with `120 of 120 run are as expected` and exit 0 in run 19). [handover/core-a/evidence/mutants-run19.md:2-3]
4. `ruff check`, `ruff format --check`, `bandit -ll`. [handover/core-a/evidence/BATCH10-summary.md:1-20]

Known state:
- On a checkout WITHOUT core-b's `TriggerSettings`, 10 tests fail by design under `HADAVIN_REQUIRE_PG=1` (they need that class); they pass on the merged tree. Without the switch they skip. [handover/core-a/evidence/BATCH10-summary.md:1-20; tests/triggers/test_t5_strict_mode.py:1-10]
- The crash tables follow the loop: with core-b's `Limits.reserve` they use the reserve and settle calls (`RESERVES` true); on core-a alone they use the older add-spend calls. [tests/triggers/crash_launcher.py:58-60]
- The whole-suite batch also had two failures outside this change: the dblink test (it needs PostgreSQL on the default socket) and the vendor-brand rule on files under `handover/`. [handover/core-a/REPORT.md:7]

Claude-Session: https://claude.ai/code/session_014pRo39MRxnYCnugNxyoaw6

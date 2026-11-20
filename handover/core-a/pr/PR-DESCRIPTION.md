# Signed trigger door: HMAC endpoint, worker, crash helper, n8n template

No PR template exists in the repo (`.github/` holds only `dependabot.yml` and `workflows/ci.yml`), so this follows the headings of the handover tickets.

## What it is
A signed HTTP door that starts one agent run per caller key. One worker process serves the endpoint and runs the agent loop.
- `src/hadavin_sdk/triggers/endpoint.py` (pure checks and a WSGI callable), `worker.py` (`Runner`, start-up checks, `main`), `server.py` (the stdlib server made quiet) [module docstrings of the three files].
- `src/hadavin_sdk/testing/crash.py` (step E): `CrashPoints`, one class that stops a test at a named place, in-process (`SimulatedCrash`, a BaseException) or as a child process exit with code 137; it can be built only inside pytest [tickets/E-test-helpers.md, ticket D section 7 "Needed from step E"].
- `n8n/hadavin-trigger.json`, `n8n/hadavin-trigger-error.json`, `n8n/README-trigger.md`: a sender template. Run once in a real n8n 2.47.7 by the lead [handover/core-a/REPORT.md, "FINAL STATE"; handover/core-a/inputs/evidence-n8n-4.md].
- Start: `python -m hadavin_sdk.triggers.worker --config-dir <dir> [--host H] [--port P] [--allow-non-loopback]` [worker.py docstring].

## What it guarantees
- Signed request: HMAC "v0" (`"v0=" + hex(HMAC_SHA256(secret, "v0:{ts}:" + body))`), 300 second window [src/hadavin_sdk/approvals/hmac_v0.py:3,19 (`MAX_AGE_S = 300`), 28; endpoint.py docstring]. Nothing of the body is parsed before the signature verifies [endpoint.py docstring; mutant G5].
- One run per key, resting on the primary key of the runs table, not on process memory; it holds across restarts and several processes [worker.py docstring; ticket D invariant 6].
- Ack only after the run row exists: a 2xx is sent only after `store.get_run` returned a row for the same agent, principal and `trigger_ref`; 202 = RECEIVED or WORKING, 200 = a later state [worker.py docstring; ticket D invariant 7; mutant G3].
- 409 when the key exists with a different document; no run is written [worker.py docstring; ticket D invariant 7; mutant G2]. A signed 409 writes one audit event `trigger.conflict` (ids and both payload hashes, never the document or signature), at most 10 per sender per minute [worker.py docstring, `CONFLICT_EVENTS_PER_MINUTE = 10`, line 127; ticket D "d-fix6: E1"].
- Status semantics, every refusal with an empty body: 400 malformed request, bad JSON or fields, stalled client; 401 signature or timestamp; 413 body over `max_body_bytes`, before the body is read; 431 headers too large; 404 other path; 405 other method; 503 store unreachable, no row within `ack_wait_s`, or `max_waiting` exceeded, always with `Retry-After: 1` [endpoint.py:66-72, 75, 340-400; server.py docstring; worker.py docstring].
- Header cap: request line plus headers at most 16382 bytes (16384 with the blank line); 16381 and 16382 pass, 16383 and over give 431 [server.py docstring; ticket D d-fix19 N1 and N3; tests/triggers/test_d_fix18_door_fixes.py].
- Bounded: `max_running` pool (default 1 until step F, because spend is charged after the model call), `max_waiting` waiters, 256 connection slots, an absolute read deadline [worker.py docstring; server.py docstring].
- SIGTERM drains and exits 0; exit codes 0 clean stop, 2 config error, 3 anything else [worker.py `EXIT_OK, EXIT_CONFIG, EXIT_FAILED`, line 123, and `main` docstring; REPORT.md "ORDERS 002 to 012, END OF ROUND", Major 2].
- `GET /health`: 200 when the store is up, 503 with a body of exactly `status` and `store_failures`; a worker that starts with the store down logs one WARNING, serves `/health` 503 and recovers by itself [endpoint.py:121-131; worker.py `main` docstring; ticket D e1-fix].
- Memory store refused outside the demo stage (`check_store_stage`, called by `make_app`) [ticket D d-fix18 M4; worker.py lines 666-676].
- One write per answer, so a killed worker cannot leave a bare 2xx status line [ticket D d-fix13; FINDINGS-flake-pg-kill.md].
- Crash matrix: at 43 kill points four invariants held (at most one row, at most one model call, no row left in RECEIVED or WORKING after the tick, a retry gets 200 or 202) [handover/core-a/CRASH-MATRIX.md; raw/D-crash-matrix-pg16.log]. Only the NO_ACTION path is in the matrix [CRASH-MATRIX.md "Not run"].

## What it does NOT guarantee
- Acknowledged, then NEEDS_PERSON with no notification and no stored document; the sender must poll the run state. Owner decision E-door-1 is open: store + notify (option B) or keep this (option A, the default) [ESCALATIONS.md E-door-1; worker.py docstring].
- A reverse proxy with per-peer connection limits is required: the server has 256 global slots and no per-peer limit; TLS is the proxy's job; by default it listens on 127.0.0.1 only [server.py and worker.py docstrings].
- One secret per tenant and per stage; the tenant is not in the signed string, so a shared secret makes a request for one tenant or stage valid for another within the 300 second window. The same value under two senders is refused at start; reuse on another worker cannot be seen [worker.py docstring; ticket D d-fix18 M3].
- "Queue mode required for no event loss" (n8n) is the deployment requirement we ask for, unverified: the caller's 202 is given before anything is stored in Hadavin. Run n8n in queue mode (recommended; NOT VERIFIED here, queue mode was never run). In default mode a restart during a 60 s wait lost the run; waits of 70 s and 120 s survived once each; a restart during a send was not run. [n8n/README-trigger.md lines 209 and 394].
- The tick must run in the deployment, or a cut-off run never reaches NEEDS_PERSON [worker.py docstring; ticket D invariant 12].
- Spend is not safe in the money sense with `max_running` above 1 [worker.py docstring].
- Not verified in n8n: the 45 s timeout, 3xx, 502/503/504 with a body, 520-524, Retry-After, 45 exhausted rounds, other states than NO_ACTION, n8n Cloud, queue mode [n8n/README-trigger.md lines 100-110, 801; REPORT.md FINAL STATE item 3]. Nothing was run on Windows [REPORT.md; WINDOWS-NOTES.md].
- `worker.main` starts only on a tree that has core-b's `Config.triggers` and `App.trigger_secret`; elsewhere it exits 2 [REPORT.md FINAL STATE item 4; worker.py docstring].

## Tripwires (what to watch)
- Worker exit code: 0 clean stop, 2 config error, 3 anything else [worker.py `main` docstring].
- WARNING "trigger worker: store re-check failed (...): still degraded" (class name only) [worker.py:1006].
- `GET /health` 503 [endpoint.py:121-131].
- Audit events `trigger.conflict` (a sender reusing a key with another document) [ticket D d-fix6].
- Runs in NEEDS_PERSON "interrupted" [ESCALATIONS.md E-door-1; CRASH-MATRIX.md].
- WARNING "trigger conflict: audit write failed/did not return in time" [worker.py:419-441]; connection-cap WARNING, at most once a minute [server.py docstring].

## Evidence (see each file for the numbers; those quoted I read in the file named)
- Last independent whole-suite batch, head 6e61005db, `REQUIRE_PG=1 -n 3`: 12 failed, 12366 passed, 458 skipped, 75 xfailed; combined tree 1437 passed, 4 skipped, 0 failed; lint clean, bandit 0 medium/high [handover/core-a/evidence/BATCH10-summary.md; evidence/BATCH10-combined.log].
- d-fix19 test run: 1244 passed, 312 skipped, 1 xfailed [handover/core-a/raw/d-fix19-tests.log; the command is not in the file].
- Mutants: run 18, 109 of 109 as expected (106 killed, 3 crash-accepted) on code before the G33d rename and before G34 [raw/endpoint-mutants-run-18.log]; d-fix19 new mutants G36i and G36j both killed [raw/d-fix19-new-mutants.log]; G36a-h killed [raw/d-fix18-new-mutants.log, ticket D d-fix18]. Run 19 did not start (stale G33d anchor) [raw/endpoint-mutants-run-19.log]. Header: tests/endpoint_mutants.py.
- Crash matrix: raw/D-crash-matrix-pg16.log, raw/D-crash-matrix-paths-pg16.log, handover/core-a/CRASH-MATRIX.md.
- Reviews: handover/core-a/reviews/D-code-result-review-1..5.md, D-tests-result-review-1.md, D-mutants-result-review-1.md, E-result-review-1..6.md, n8n-result-review-1.md, code-D-design-review-1.md.
- n8n: raw/n8n-template-tests-14.log, inputs/evidence-n8n-*.md and inputs/lead-evidence-n8n-1.md.
- Tested-state notes: handover/core-a/TESTED-D.md, TESTED-n8n-E-T4.md.

## Rollback
Stop the worker, remove the `triggers:` block from `config.yaml`, and the worker will not start (exit 2) [ticket D section 7b "New optional block `triggers:`... absent means the worker exits 2"]. Nothing migrates: the door adds no table, role or grant (it uses the existing runs table) [REPORT.md rules used, preamble 11; ticket D invariant 6]. Runs already written stay as ordinary run rows. The n8n workflows can be deactivated in n8n.

## Test plan
Run from the repo root (commands assembled from the variable and file names below; the exact command line of the recorded runs is in the logs only where stated):
1. `HADAVIN_REQUIRE_PG=1 uv run pytest tests/triggers tests/test_testing_crash.py tests/test_mutants_anchors.py -n 3` [strict switch: tests/triggers/conftest.py, test_t5_strict_mode.py; REPORT.md BATCH10 used `REQUIRE_PG=1 -n 3`].
2. With a throwaway PostgreSQL: add `HADAVIN_TEST_PG_DSN=<superuser dsn>` to run the database and kill tests [tests/triggers/test_t5_postgres.py docstring]. Without it they skip.
3. `uv run python tests/endpoint_mutants.py` (mutation run; will exit 2 until the G33d anchor is fixed) [tests/endpoint_mutants.py; raw/endpoint-mutants-run-19.log].
4. `ruff check`, `ruff format --check`, `bandit -ll` [evidence/BATCH10-summary.md section 1].

Known state:
- In a checkout WITHOUT core-b's `TriggerSettings`, 10 tests fail by design under `HADAVIN_REQUIRE_PG=1` (test_worker.py 2, test_t5_main_start.py 7, test_t5_process.py 1); they pass on the combined tree [evidence/BATCH10-summary.md "(a) strict-mode by design"; evidence/BATCH10-combined.log]. Without the switch they skip [tests/triggers/test_t5_strict_mode.py docstring].
- 1 strict xfail, G33d, in `tests/test_mutants_anchors.py`: its anchor (`now - last_warned`) moved in a rename and the line is pending the owner's edit; the day it is fixed the test xpasses and fails [tests/test_mutants_anchors.py lines 15-17].
- PostgreSQL tests are skipped without `HADAVIN_TEST_PG_DSN` [test_t5_postgres.py].
- The whole-suite batch also had 2 failures outside this change: the dblink test (needs PostgreSQL on the default socket) and the vendor-brand rule on `handover/BRIEF-PREAMBLE.md` [REPORT.md UPDATE 11:31 UTC].

Claude-Session: https://claude.ai/code/session_014pRo39MRxnYCnugNxyoaw6

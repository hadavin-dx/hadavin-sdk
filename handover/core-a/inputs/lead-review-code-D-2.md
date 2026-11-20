# review-code-D-2 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# Result review, round 2 of 3: ticket D signed endpoint and worker (branch cloud/core-a), read-only

## Verdict

- **No Blocker.** I found no security hole in the Python path: no acknowledgement without a run row, no body bytes parsed before the signature verifies, and no text leak at the stdlib layer.
- **Two Majors remain, both in the n8n template.** Round-1 Major 4 (tests) is only partly closed.
- **The worker still cannot start through `main`.** `Config.triggers` and `App.trigger_resolve` are not in `config.py`, `app.py`, `registry.py` or `defaults.py` on this branch (grep, no match). That waits on core-b's REQUEST 001.
- **Nothing was run.** Every statement about stdlib behaviour (`http.server`, `wsgiref`, `socketserver`, `signal`, `os.kill` on Windows) is from memory of the stdlib, not from its source.

## What I read

Root: `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-a`. Line counts are as I saw them; the branch may have moved since.

| File | Lines | Coverage |
|---|---|---|
| `src\hadavin_sdk\triggers\endpoint.py` | 316 | full |
| `src\hadavin_sdk\triggers\worker.py` | 444 | full |
| `src\hadavin_sdk\triggers\server.py` | 126 | full |
| `src\hadavin_sdk\testing\crash.py` | 198 | full |
| `tests\endpoint_mutants.py` | 441 | full |
| `tests\triggers\test_t5_wsgiref.py` | 359 | full |
| `tests\triggers\test_t5_process.py` | 199 | full |
| `tests\triggers\test_t5_postgres.py` | 452 | full |
| `tests\triggers\crash_launcher.py` | 254 | full |
| `tests\triggers\test_n8n_template.py` | 443 | full |
| `tests\triggers\test_worker.py` | 871 | lines 1-145, 230-340, 600-871; the rest by test name only |
| `tests\triggers\test_t5_cases.py` | 633 | lines 200-633 |
| `tests\triggers\test_endpoint.py` | about 860 | grep only |
| `tests\triggers\test_t5_nul_document.py` | about 450 | test names only |
| `n8n\hadavin-trigger.json` | 442 | full |
| `n8n\hadavin-trigger-error.json` | 78 | full |
| `n8n\README-trigger.md` | 232 | full |
| `handover\core-a\tickets\D-signed-endpoint.md` | 422 | full |

Also read:
- **Reference documents:** `draft-C-D.md` (ticket D), `review-code-D-1.md` and `evidence-n8n-1.md`, all full.
- **Greps on this branch:** `store\protocol.py:29-38` and `tests\contracts\kinds\store_postgres.py:18-25`.
- **Baseline `sdk-main`:** `approvals\hmac_v0.py:19-51`, by grep.

## Round-1 Majors

1. **Second event during a run: PARTLY.**
   - Code is fixed: the back-off wait is at `worker.py:134-148`, and a waiter takes a freed slot at `:145-147`.
   - README states the throughput at `README-trigger.md:113-136`.
   - The n8n wait-and-sign-again loop is at `hadavin-trigger.json:197-263`.
   - It stays PARTLY because the loop only works once the Set nodes are fixed (new Major A) and it retries only on 503 (new Major B).
2. **SIGTERM strands work: FIXED**, at `worker.py:363-386`.
   - Tests: `test_worker.py:763` (child process), `:788`, and `test_t5_process.py:174` (case D3: the running loop ends, exit 0, port closed).
   - Mutant G12d covers the handler.
   - Residuals are Minors 3, 7 and 9 below.
3. **Missing field becomes the text "undefined": FIXED in the file.**
   - Guard node at `hadavin-trigger.json:21-59`; `String()` now sits behind it at `:71` and `:91`.
   - Shape is pinned by `test_n8n_template.py:239`.
   - The evidence (ITEM 8) confirms the guard on a test copy: nothing was sent in four cases.
4. **Missing crash, database and socket tests: PARTLY.**
   - Done:
     - Socket cases, including the short body (E9): `test_t5_wsgiref.py:281-300`.
     - Child-process kills K2 and K3: `test_t5_postgres.py:325-402`.
     - Two processes on one database (C4): `test_t5_postgres.py:420-451`.
     - Oversize document (E6): `test_t5_postgres.py:294`.
     - Two senders, two rows (N5): `test_t5_postgres.py:257`.
     - The skipped K1 stub is gone (`test_t5_cases.py:606-608`).
   - Not done:
     - Start refusal through `main` with a real config. Only "no triggers block" and "missing folder" exist (`test_t5_process.py:56, 70`).
     - `test_t5_cases.py:628-632` still asserts only that the Postgres kind is registered.
     - K2, K3, C4, E6 and N5 exist only on PostgreSQL, so they skip without the DSN (Minor 8).

## Round-1 Minors

| # | Topic | Status | Where |
|---|---|---|---|
| 1 | Window boundary | FIXED | `endpoint.py:164`; mutant G10 |
| 2 | Unauthenticated resource use | FIXED as recommended (README only) | `README-trigger.md:178-185`; no code limit, see Minor 1 |
| 3 | Stdlib HTML body and Server header | FIXED | `server.py:45-80, 122-125`; socket tests; mutants G8a-d |
| 4 | Refusal without reading the body | PARTLY | Stated at `README-trigger.md:187-190`. Real-socket test only for the no-Content-Length 400 (`test_t5_wsgiref.py:332`, tolerates a reset). No socket test for 413 or 401 with a large unread body. |
| 5 | Secret count and whitespace | FIXED | `endpoint.py:184-194`; `test_endpoint.py:349-388`; mutants G9a/b |
| 6 | Duplicated defaults, silent `getattr` fallbacks | NOT FIXED | `worker.py:305-307, 396-398, 403`; stated at `README-trigger.md:198-200`; waits on REQUEST 001 |
| 7 | IPv6 loopback | FIXED | `worker.py:279-280`; `test_worker.py:840`; mutant G12b |
| 8 | Start-up error text | FIXED | `worker.py:420-434`; `test_worker.py:817` |
| 9 | Cross-protocol secret reuse | PARTLY | README sentence at `:53-56`; no value comparison in code; SECURITY not read |
| 10 | 200 is not "ended" | FIXED | `README-trigger.md:92, 102-111`; `test_n8n_template.py:388` |
| 11 | Stale README default | FIXED | `README-trigger.md:163-166` |
| 12 | NUL in the document | FIXED by tests, per the ticket | `test_t5_nul_document.py` (names only read); `README-trigger.md:196-197` still says "not checked" |
| 13 | Config renames | FIXED | `README-trigger.md:192-195` |
| 14 | The tick is checkable | FIXED | `worker.py:343-360`; `test_worker.py:847`; `README-trigger.md:143-144` still says the worker does not check |

## The n8n evidence against the files

I was not given the ORDER 015 text, so the eight items below are my own reading of what `evidence-n8n-1.md` forces. None of them is in the files yet: all three n8n files are still the pre-evidence outline.

1. **Set nodes typeVersion 3 to 3.4 in the main workflow: NOT IN.** Still 3 at `hadavin-trigger.json:80, 107, 225`. With 3 the nodes add nothing (ITEM 2).
2. **Error workflow Set node 3 to 3.4: NOT IN.** Still 3 at `hadavin-trigger-error.json:19`; the message was null (ITEM 7).
3. **Webhook node needs a `webhookId`: NOT IN** (`hadavin-trigger.json:5-19`). Without it the path registered as `<workflow id>/trigger%20placeholder/<path>` (ITEM 2).
4. **Secret from a Crypto typeVersion 2 credential, not `$env`: NOT IN.** Still typeVersion 1 with `$env` at `:129, 139`. At default settings `$env` is denied (ITEMs 3 and 6).
5. **Option B Code node needs two server settings: NOT IN the note or README.** It needs `NODE_FUNCTION_ALLOW_BUILTIN=crypto` and env access allowed; the return shape is fine. The note at `:158` still says UNVERIFIED.
6. **Status field is `error.status`; `error.httpCode` does not exist: works already** through the fallback at `:209`. The note at `:220` still calls both guesses.
7. **Retry On Fail facts: NOT IN.** It reuses timestamp and signature, made 5 tries when 10 were asked for and waited about 5 s when 10 s were asked for (ITEM 5). The node is correctly off (`:168`), but `README-trigger.md:212-213` still says NOT VERIFIED.
8. **Verified-status wording: NOT IN.**
   - Names still say "outline, not run in n8n" (`:2`).
   - README `:3-5` and the verify list `:207-231` mark all 17 items NOT VERIFIED. The evidence closes most of them (byte-identical body, Content-Length, error workflow must be published, guard, loop). Still open by the evidence's own list: manual retry, duplicate firing against the real endpoint, no answer at all.
   - The top-level `notes` key (`:441`) is dropped by import.

The tests enforce the stale state and must change in the same commit:
- `test_n8n_template.py:29-30, 216, 223` pin the `$env` expression.
- `:36-54, 376-385` pin 17 "NOT VERIFIED" items.
- `:149-151, 162` pin "not run in n8n" and an UNVERIFIED note on every node.

## New findings

### Major

**A. The template as shipped cannot produce a valid request.** `hadavin-trigger.json:80, 107, 129, 139, 225`; `hadavin-trigger-error.json:19`.
- With Set typeVersion 3, the evidence run (execution 51) sent the raw webhook body with no timestamp header and a signature over `v0:undefined:[object Object]`.
- That is a 401 every time. On a default n8n, `$env` fails the execution before that.
- The error workflow's message is null.
- Fix: apply items 1-5 and 8 above and update `test_n8n_template.py` with them.
- Add one test that fails on any Set node below 3.4 and on a webhook node without `webhookId`.

**B. The retry loop treats only 503 as "try again".** `hadavin-trigger.json:209`.
- README `:182-185` requires a reverse proxy in front. When the worker is down or draining, a proxy typically answers 502 or 504. A direct connection is refused or times out.
- All of these go to "Stop: refused or gave up" and a person must resend by hand.
- The new SIGTERM drain makes this routine. `serve` closes the listening socket first (`worker.py:382`). The process then stays alive until the running loop ends, which can be minutes (`worker.py:112-122`, non-daemon pool thread). A supervisor will normally not start the replacement until it exits.
- So every event that arrives during a restart lands in the error workflow. That is the same failure class as round-1 Major 1.
- Retrying is safe by design: same key, new signature.
- Fix: treat 502, 503, 504 and "no HTTP status at all" as busy in "Busy and rounds left?". Keep 400, 401, 409 and 413 as stops.
- The error-item shape for a refused connection or timeout was not run in the evidence (its NOT RUN item 9). It needs one more evidence step.

### Minor

1. **No connection or thread cap; the socket timeout is per receive.** `server.py:117-120`, `worker.py:323`.
   - A client sending one byte just inside each timeout holds a thread through a 64 KB request line, the header block and a body of up to `max_body_bytes`. That is weeks.
   - Each connection can buffer `max_body_bytes` before any signature check.
   - Stated at `README-trigger.md:178-185`. Acceptable on loopback behind a buffering proxy; real exposure with `allow_non_loopback`.
   - Fix if wanted: a bounded semaphore in `QuietServer.process_request` that closes connections above N, and an absolute per-request deadline.
2. **`handle` catches `TimeoutError` from the whole request, not only the read phase.** `server.py:83-86`.
   - A timeout while writing the answer to a client that does not read lands in `_refuse_stalled`.
   - That writes a second `400` head after a partly sent answer and can hold the thread one more timeout.
   - Nothing leaks. Fix: catch `TimeoutError` only around `readline` and `parse_request`.
3. **Drain limits are not written for the operator.** `worker.py:363-386`, `:112-122`.
   - A run in the middle of a model call is not cut; it runs to its end.
   - `close` waits 30 s, then `main` returns 0, but the interpreter still waits for the pool thread.
   - A second SIGTERM is a no-op for up to those 30 s (the handler only calls `shutdown` again). After `:385` restores the old handler it kills the process.
   - If the supervisor's grace is shorter than the run (Docker's default is 10 s), the run is killed and ends NEEDS_PERSON "interrupted", with the key used up.
   - Fix: one README paragraph: set the stop grace longer than the longest run, the port is closed during the drain, and what a second signal does.
4. **A waiter can get 503 although its run started.** `worker.py:142-148`.
   - A waiter that takes a freed slot just before its deadline has `handle` running but gets 503 before the row is read.
   - The retry finds the row, so invariant 11 holds.
   - But `README-trigger.md:119-121, 133` and the Stop message at `hadavin-trigger.json:274` say nothing is stored and the event was not accepted.
   - Fix: reword to "not acknowledged; send again with the same key; it may already be running".
5. **No fairness among waiters.** `worker.py:145-148`.
   - A new request tries the slot at once; an old waiter looks only every up to 1 s. Under steady arrivals an old event can lose every round.
   - Reads per refused request are about 10 in 5 s (pinned at 5-12 by `test_worker.py:713`).
   - A waiter is never acknowledged without a row: every 2xx comes from `_answer(found)` at `:129, 141`.
   - Acceptable at the stated low rate. Fix: one README sentence.
6. **Any `OSError` at start is reported as "store unreachable", exit 4.** `worker.py:429-432` with `store\protocol.py:33`.
   - A port already in use or a bind refusal from `make_server` (`worker.py:404`) therefore tells the operator the database is down.
   - Fix: catch `OSError` around `make_server` and raise the local `ConfigError("cannot listen on the port")`.
7. **Two SIGTERM tests have no Windows guard.** `test_worker.py:763` and `:788`.
   - D3 has the guard (`test_t5_process.py:173`); these two do not.
   - On Windows, `send_signal(SIGTERM)` terminates the child, so `:783` fails.
   - At `:800`, `os.kill(os.getpid(), SIGTERM)` terminates the pytest process itself.
   - The lead's laptop is Windows. Fix: the same `skipif` on both.
   - Mutant G12d's killer is D3, so the mutant script cannot be all-good on Windows.
8. **Database, kill and two-process tests still pass by skipping.**
   - `pg_schema` calls `pytest.skip` when `HADAVIN_TEST_PG_DSN` is unset (`store_postgres.py:22-24`).
   - All of `test_t5_postgres.py` depends on it, and nothing fails when the variable is missing.
   - The kill tests themselves are real: the child dies through `os._exit(137)` at an armed point (`crash.py:142-143`), and the parent asserts exit code, marker and rows by plain SQL (`test_t5_postgres.py:177-181, 78-85`).
   - Fix: a required evidence log listing these test ids as passed, or a strict variable that turns the skip into a failure in the done-run.
   - Delete `test_t5_cases.py:628-632`; it cannot fail usefully.
9. **Drain tests leave three cases open.** No test covers a request waiting for a slot at SIGTERM, a request that arrives between `shutdown` and `server_close`, or a second signal.
10. **Mutant script gaps.** `tests\endpoint_mutants.py`.
    - Ticket section 10 lists mutants that are not in the script: stop trying secrets after the first match; decide 409 from the exception type; read the body before the size check.
    - `server.py` has no mutant for removing the `TimeoutError` branch (`:85-86`), the `handle_error` override (`:122-125`) or the 414 branch (`:93-96`).
    - The drain has only G12d: nothing removes `runner.close()` from `serve` (`worker.py:383`) or `self._closed = True` (`:119`).
    - Secret checks have no mutant for `MAX_SENDERS`, the sender-and-secret line-up (`endpoint.py:240`) or `len(matched) == 1` (`:171`).
11. **Stale README sentences.** `:143-144` and `:201` (tick is now checked at start), `:168-169` ("no test sends such a document"), `:187-190` ("not tested on a real connection"), `:196-197` (NUL "not checked").
12. **Small items in the secret checks.** `endpoint.py:188-201`.
    - `strip()` does not catch a byte-order mark or a zero-width space, so such a secret file still gives a permanent 401.
    - The same value twice for one sender is accepted (one wasted HMAC).
    - Length is counted in characters, so 32 equal characters pass.
    - Equality across senders is exact string equality, which is correct.

## Attack results on the new code

- **Stdlib refusals:** every one I could trace goes through the overridden `send_error` (`server.py:74-80`). That covers a bad request line, bad version, 414, 431 and a stall. The answer is a status line, `Content-Length: 0` and `Connection: close`, with no Server header and no body.
- **Application answers:** these carry a Date header and no Server header (`server.py:48`).
- **Silent closes:** a half-closed or silent socket with no bytes is closed without an answer; an HTTP/0.9 request line is answered with no status line or headers.
- **Server survival:** I found no path that crashes the server or prints. `handle` catches `Exception` at `:87`; `handle_error` is overridden at `:122`.
- **Hangs:** only the slow drip of Minor 1 can hold a thread.
- **SIGTERM handler:** it starts a thread, so there is no self-deadlock. A signal before `serve_forever` begins is not lost (as I recall the stdlib shutdown flag). Exit code is 0.
- **Worker start order:** config, bind check, build, sender and secret checks, tick warning, bind (`worker.py:389-407`). No secret is read before the bind check.

## Not checked

- Nothing was run; no log was opened; `tools\mutation_runner.py` was not read.
- ORDER 015 itself; `ESCALATIONS.md`; `D-review-1.md`; REQUEST 001; SECURITY, CHANGELOG and the repo README.
- `test_endpoint.py` beyond grep; `test_worker.py:146-229, 341-599`; `test_t5_cases.py:1-199`; the bodies of `test_t5_nul_document.py`.
- `store\postgres.py`: commit visibility of `create_run`, and behaviour of the one shared connection under request threads.
- Thread safety of real model clients and the audit chain.
- Duplicate Content-Length or Transfer-Encoding handling behind a real proxy. One request per connection limits the risk.
- Any real n8n behaviour beyond what `evidence-n8n-1.md` records.
- Whether the branch changed after my reads.


# Finding: a 2xx with an EMPTY body in test_pg_kill_at_point[read31-audit.write_outcome-4-after] (BATCH9)
(Written 11:19 UTC by the Elephant. An earlier agent reported writing this file; it did not exist: the d-fix13 ticket paragraph cited a missing file. This is the real one.)

## What was seen
BATCH9 (whole suite, -n 3, REQUIRE_PG=1): the test got `ack_status` 2xx and `ack_data == ""`; `json.loads("")` failed at tests/triggers/test_t5_crash_matrix_paths.py ~822. It passed in BATCH7/BATCH8 and in all builder runs.

## Cause (by reading the stdlib and our server; NOT reproduced by a run)
- The worker child is killed by `os._exit(137)` (testing/crash.py) at the crash point `audit.write_outcome:after`, on the loop thread, while the request thread may be writing the answer.
- `socketserver.StreamRequestHandler.wbufsize = 0`, so `wfile` is unbuffered and `wsgiref` sends a 2xx answer as FOUR separate `sendall` calls: status line, Date line, header block, body (/usr/lib/python3.12/wsgiref/handlers.py: send_preamble, send_headers, write). `QuietWSGIHandler` overrode none of them.
- A kill after the status line leaves the client with `HTTP/1.0 202 Accepted` and EOF. `http.client` treats EOF inside the headers as the end of the headers, reads the body to EOF (no Content-Length) and returns status 202, body empty, NO exception. A kill after the headers gives IncompleteRead; before the status line RemoteDisconnected.
- No empty 2xx exists without a kill: the 200/202 body is always the JSON `{run_id, state}` (endpoint.py BODY_STATUSES, worker.py _answer); empty bodies are only 4xx/5xx.
- The guarantee "a COMPLETE 2xx implies the run row exists" holds in every interleaving: the row is read/created before the answer is written (worker.py _decide / _answered). The defect is wire-level: a client could not tell a truncated 2xx from a complete one.

## Reproduction (A-repro, 11:07-11:10)
- The pg-kill id, 20 runs, one process each: 20 PASS, 0 FAIL (raw/REPRO-pgkill-20.log; the client already had the truncated-answer guard).
- 40-run harness with the OLD client behaviour (returns the status and whatever body arrived): 40 complete answers (HTTP/1.0 202, Content-Length 71, 71 of 71 bytes, run_id matched), 0 truncated, 0 no answer (raw/REPRO-pgkill-incomplete.log).
- So the failure does NOT reproduce serially; it was seen once under whole-suite -n 3 load. Not tried: the harness under CPU load.

## Fix
1. Test client (final-fix, 10:58): `crash_launcher.signed_post` returns (None, b"IncompleteResponse") for a 2xx without Content-Length or with a short body (+4 unit tests, tests/triggers/test_signed_post_truncated.py). The assertion at ~822 is unchanged.
2. Server (d-fix13, 11:15): ONE write per answer: `QuietWSGIHandler._write` buffers, `finish_response` sends the buffer with one `sendall`; 49 tests (tests/triggers/test_d_fix13_single_write.py: exactly one write for 16 answer types, golden bytes equal to the old server: wire equality; 29 of 49 fail on the old code). The pg-kill id after the fix: 20 PASS, 0 FAIL (raw/REPRO-pgkill-after-fix-20.log). Mutant G34 (buffering removed) is killed by test_every_answer_is_one_write[202] (run alone; the full mutant script is blocked by the G33d anchor).
3. Residual: a kill DURING the single sendall of an answer larger than the socket buffer; ours are under 300 bytes.

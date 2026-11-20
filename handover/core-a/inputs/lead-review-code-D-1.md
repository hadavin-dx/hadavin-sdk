# review-code-D-1 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

## Early result review: ticket D signed endpoint + worker (branch cloud/core-a), read-only

**Verdict:** no invariant is BROKEN in the code read, and I found no Blocker in the security path. The work is not complete: the worker cannot start outside tests, and several T5 and crash cases are missing. There are 4 Major and 14 Minor findings.

No review file exists under `handover\core-a\tickets\` (only the D and E tickets), so no prior review was read.

### What I read
Root for the branch: `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-a`

| File | Lines |
|---|---|
| `src\hadavin_sdk\triggers\endpoint.py` | 301 |
| `src\hadavin_sdk\triggers\worker.py` | 391 (see note) |
| `src\hadavin_sdk\triggers\__init__.py` | 1 |
| `src\hadavin_sdk\testing\crash.py` | 198 |
| `tests\triggers\test_endpoint.py` | 795 |
| `tests\triggers\test_t5_cases.py` | 646 |
| `tests\triggers\test_worker.py` | 635 |
| `n8n\hadavin-trigger.json` | 223 |
| `n8n\hadavin-trigger-error.json` | 78 |
| `n8n\README-trigger.md` | 87 |
| `handover\core-a\tickets\D-signed-endpoint.md` | 343 |
| `handover\core-a\tickets\E-test-helpers.md` | 191 |
| `handover\core-a\requests\001-config-triggers.md` | 49 |

- **worker.py changed while I read.** The first read was 379 lines (`_flying` dict, no-slot gave 503 after one re-look). The second read is 391 lines (`_jobs` set, no-slot waits `ack_wait_s`, `check_bind` refuses host names). All findings are against the 391-line version; its lines 1-54 were only grepped for imports the second time.
- **Baseline** (`C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main`): `approvals\hmac_v0.py` (80), `approvals\receiver.py` (66), `runtime\agent_loop.py` 330-400, `runtime\tick.py` 100-150, `store\protocol.py` (161).
- **Spec:** `C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\tickets\draft-C-D.md`, ticket D.
- **Nothing was run.** Of the raw logs I grepped summary lines only: endpoint tests 190 passed / 2 skipped, worker tests 32 passed, guards 233 passed, three endpoint mutants CAUGHT.

### The 12 invariants

| # | Invariant | Status | Where |
|---|---|---|---|
| 1 | Body parsed only after the signature verifies; check order | HELD | `endpoint.py:236-262`. Raw read at 246, `verify_any` at 256, `parse_body` at 260. Path is checked before method (404 wins over 405), which is harmless. |
| 2 | Only a configured secret verifies; sender is the one whose secret verified; start checks | HELD | `endpoint.py:144-165` (all secrets tried, exactly one sender must match), `168-187`, called at `:229` and `worker.py:281`. No sender header is read. Gap: "1 or 2 secrets per sender" is not enforced here (Minor 5). |
| 3 | 300 s window both directions, before any store lookup | HELD | `hmac_v0.py:47` (`abs`), `endpoint.py:256-258` returns 401 before `start`. With a real float clock the boundary is not exact (Minor 1). |
| 4 | run_id derivation, NUL separator, charsets | HELD | `endpoint.py:97-108`. `fullmatch`, so no trailing-newline hole; tenant, sender and key are all in the hash. |
| 5 | trigger_ref carries the payload hash | HELD | `endpoint.py:111-113`. `/` and `#` are outside both charsets, so it is unambiguous. |
| 6 | One row and one loop per key, resting on the primary key | HELD | `worker.py:113-137` with `agent_loop.py:388-393`. The second version dropped the in-process table, which is better. |
| 7 | 2xx only after `get_run` returns a matching row; mismatch 409, nothing written | HELD | `worker.py:116-129`, `182-191`. The answer comes from the row, never from the exception. |
| 8 | Agent and principal from config; start refusal; `trigger_kind` constant | HELD in `make_app` | `endpoint.py:263-267`, `worker.py:212-230` called at `:278`, `:64/:174`. Via `main` and real config: NOT IMPLEMENTED YET. |
| 9 | Run rows never deleted | HELD by absence | Nothing in `triggers\` deletes. No test pins it. |
| 10 | Body only `run_id` and `state`; empty refusals; clean logs | HELD in our code | `endpoint.py:287-290`, logs at `:275, :285, :296`, `worker.py:136, :179` (class names, sender id, run_id only). Not held at the stdlib HTTP layer (Minor 3). |
| 11 | Over capacity or store down gives 503, no ack | HELD | `worker.py:131-137`, `endpoint.py:272-278`. No-slot answers 503 only after `ack_wait_s`, not at once (Major 1). |
| 12 | The tick must run | Log line only | `worker.py:376-379`. Nothing checks it (Minor 14). |

### Attack results
- **Bytes before verify:** none are parsed or logged. The stdlib request log is silenced (`worker.py:307-309`).
- **Timing:** `compare_digest` at `hmac_v0.py:51`; no early stop across secrets (`endpoint.py:160-163`). Early returns happen only on header shape or window, the same for every secret.
- **Unsigned request and the store:** no read or write is possible; 401 returns before `start`. `test_t5_cases.py:320-335` spies `get_run`.
- **Two senders:** no confusion found. A value shared across senders is refused at start, and `verify_any` also returns None on two matches. An extra `X-Hadavin-Sender` header is ignored (`test_endpoint.py:415`).
- **Same key, different document:** 409 from the row. In a parallel race the loser's `create_run` fails before any write.
- **Ack before the row:** not possible in `Runner.start`.
- **Header case and duplicates:** WSGI folds header names, so any case works. As I recall wsgiref (not checked here), duplicate headers are comma-joined, which fails `isdigit` and gives 401.
- **Content-Length:**
  - missing, signed, spaced, non-ASCII or zero: 400 (`endpoint.py:202-206, 241`).
  - over 12 digits or over the cap: 413 unread (`:243`).
  - smaller than the body: the truncated bytes fail the signature, 401.
  - larger than the body: the read blocks until the socket timeout, then 400 (`:247`). There is no socket test of this (E9).
  - chunked without a length: 400, on the same assumption that wsgiref sets no `CONTENT_LENGTH` then.
- **Leaks in exceptions:** `BadRequest` text never quotes the body. The catch-alls log the class name only.
- **Hard-coded values:** no secret. Loopback and port 8081 are literals (Minor 6). The n8n URL is `example.invalid`.

### Findings

**Major**

1. **A second event that arrives during a run ends in the n8n error workflow.** `worker.py:58, 122-133` with `n8n\hadavin-trigger.json:106-108`.
   - `max_running` defaults to 1, and a no-slot request polls for `ack_wait_s` (5 s) before its 503.
   - The template retries 3 times with 5 s waits, so the retry span is about 20-40 s. A run can last minutes (`tick.py:100-109`).
   - Each refused request also costs about 100 `get_run` reads on the one locked store connection the running loop uses.
   - Fix: state the throughput (one run at a time) in the README. Answer no-slot 503 at once when no other worker process exists, or back the poll off. Add an n8n outer loop (Wait node, then re-sign) for 503 instead of relying on Retry On Fail.

2. **A routine restart permanently strands in-flight work.** `worker.py:380-386`.
   - Only `KeyboardInterrupt` is handled. A SIGTERM from a supervisor or container stop kills the process with no drain.
   - The document lives only in memory, and the key is a hash of the business id, so the client cannot resubmit: the same key answers 200 NEEDS_PERSON forever.
   - Fix: a SIGTERM handler that calls `server.shutdown()` then `runner.close()`. Add a README line on what a client does with NEEDS_PERSON "interrupted".

3. **The n8n template silently merges events when a field is missing.** `n8n\hadavin-trigger.json:31, 56`.
   - `String($json.body.record_id)` turns a missing field into the text "undefined", so every such event shares one key.
   - The first one runs; later ones get 409, or dedupe silently if the document is identical. A missing text field sends the document "undefined".
   - Fix: an IF or Stop-and-Error node before hashing that fails on an empty or undefined id or text.

4. **The tests do not prove everything the ticket claims.**
   - `test_t5_cases.py:606` is skipped. The crash case exists only in-process on the memory store (`test_worker.py:484`).
   - Missing: subprocess kill cases K2 and K3, two processes on one database (C4), and the short-body socket case (E9).
   - Missing: start refusal through `main` (H8), an oversize document giving NEEDS_PERSON (E6), and two senders giving two rows at store level (N5).
   - `test_t5_cases.py:641-645` asserts only that the Postgres kind is registered. Every Postgres run skips silently without the DSN, and I saw no D log for Postgres (only `E-tests-pg16.log`).
   - The T5 file drives the app in-process, not over wsgiref as the ticket names it. There is one socket test (`test_worker.py:603`).
   - Fix: add the missing cases, and require a Postgres log with test ids before "done".

**Minor**

1. **Window boundary.** `hmac_v0.py:47` with `endpoint.py:256`: the real clock is a float, so a timestamp exactly 300 s old is refused once the fraction is above zero. The tests pass only with an integer clock (`test_endpoint.py:521`). Fix: `int(clock())`, or drop the "exactly 300" claim.

2. **Unauthenticated resource use.** `worker.py:301-317`.
   - One thread per connection with no cap; the socket timeout applies per receive, not per request, so a slow drip holds a thread indefinitely.
   - Each connection may buffer up to `max_body_bytes`.
   - A fresh timestamp buys up to 16 HMACs over the full body.
   - Acceptable on loopback behind a buffering proxy. With `allow_non_loopback` it is exposed. Fix: say in the README that the proxy must buffer requests and limit connections.

3. **Stdlib HTTP layer breaks "empty refusal".** A malformed request line or oversize header is answered by `http.server` with an HTML body that echoes caller text, plus a `Server:` header naming the Python version. Fix: override `send_error`, `server_version` and `sys_version` in `_QuietHandler`. This is from memory of the stdlib, not checked here.

4. **Refusal without reading the body.** For 413, 400 and 401 on a real socket, closing with unread bytes can reset the connection, so the client may see a reset instead of the status. Untested.

5. **Secret count per sender.** `worker.py:239-245` accepts any number of secret names, so the "16 HMACs" bound rests on config that does not exist yet. Fix: `check_secrets` refuses more than 2 values. Also refuse leading or trailing whitespace in a value (a trailing newline from a secret file means a permanent 401).

6. **Duplicated defaults.** `worker.py:57-63` and `endpoint.py:36-37` against R1b `defaults.py`. The `getattr(settings, ..., default)` calls at `worker.py:285-287, 341-343` silently hide a misnamed config field. Fix: delete the fallbacks when REQUEST 001 lands.

7. **IPv6 loopback.** `worker.py:253-265` accepts `::1`, but `WSGIServer` is IPv4, so the bind fails with exit 3. Fix: refuse it or set the address family.

8. **Start-up error text.** `worker.py:365, 368` print the full text of `StoreUnavailable` and `ConfigError`. Line 370's own comment says such text "could hold a value". Whether those messages can carry a DSN was not checked (`postgres.py` not read).

9. **Cross-protocol secret reuse.** The header prefix is not in the signed text (`hmac_v0.py:27`). If a trigger secret equals the approvals channel secret, whoever holds the trigger secret can forge approval clicks. Fix: one SECURITY sentence, and a value comparison in core-b's wiring if it is cheap.

10. **200 is not "ended".** `worker.py:65, 191` answers 200 for PLAN_READY, WAITING_FOR_APPROVAL, EXECUTING and VERIFYING. `README-trigger.md:61` says 200 means the run has ended.

11. **README default is stale.** `README-trigger.md:65` says 262144 bytes; ticket section 7b sets 2 x MAX_DOCUMENT_BYTES.

12. **NUL in the document.** `document` may contain `\u0000` (`test_endpoint.py:214` accepts it). Whether the redaction map and Postgres text paths tolerate it was not checked.

13. **Config renames.** Renaming the tenant or a sender id changes every run id, so old keys run again. Changing a sender's agent or principal makes every old key 409. Neither is documented.

14. **The tick is checkable.** `Store.get_tick_state(step)` exists (`protocol.py:117`). The worker could warn at start when no recent "stuck" tick is recorded, instead of "cannot check it". I did not read the `TickState` fields.

### n8n outline
- **HMAC over the bytes sent:** correct by construction. One string `body` is signed as `'v0:' + ts + ':' + body` (`:75`) and the same field is sent raw (`:126-128`). UTF-8 is used on both sides.
- **Unproven, as the README itself lists:** that the HTTP Request node sends the string byte-identical.
- **Not on the verify list, should be:**
  - n8n sends `Content-Length`, not chunked (chunked gets 400).
  - `$env` is readable in expressions. I believe n8n 2.x blocks it by default; that is from memory.
  - The option B return shape: `return $json` is probably wrong for per-item mode.
- **Retry inside the window:** yes. Retry On Fail is on the HTTP node only and reuses `ts`; the worst case is about 3 x 10 s + 2 x 5 s = 40 s, well under 300 s. A manual or `retryOf` retry is the open item, and it is listed.
- **Clock skew** over 300 s between the hosts gives a permanent 401; the README mentions it.

### Not implemented yet
- **REQUEST 001** (core-b, status DRAFT 2): `Config.triggers`, the defaults, `App.trigger_resolve`, and the registry check. `main` therefore always exits 2 today (`test_worker.py:537`). I inferred this from the request file and tests; I did not open `config.py`, `app.py` or `registry.py`.
- **Config rules the request should add:** `host` must be an IP literal or `localhost`, to match `check_bind`.
- **The `crash=` hook points** of ticket section 7 (`verified`, `submitted`, `row_seen`) are absent from `Runner`, `make_app` and `main`.
- **Logging:** "3 connectivity errors then exit 4" (open question 5) and the reason code, body length and duration fields of ticket invariant 10 are absent.
- **Wording:** R3 README, SECURITY and CHANGELOG text.
- **Tests:** the cases listed in Major 4.

### Not checked
- Whether `postgres.py` commits `create_run` before `get_run` can see it.
- Thread safety of the real model clients and the audit chain.
- `testing\mutation.py` and `testing\__init__.py` (not new files).
- The mutant logs beyond their verdict lines.
- `atlas-n8n.md` and the other `inputs\` files.
- Any real n8n behaviour.

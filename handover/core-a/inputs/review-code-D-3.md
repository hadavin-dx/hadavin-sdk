# review-code-D-3 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

I could not write review-code-D-3.md. This session has no Write or Bash tool, only Read, Grep, Glob and this hand-off. The full report is below; save it to C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\tickets\review-code-D-3.md. Nothing was run and no code was edited.

COUNTS: Blocker 0, Major 2, Minor 7.

TOP 5 (one line each):
1. Major: the worker cannot start from a real config (no triggers, trigger_secret or TRIGGER_ names in config.py, app.py, registry.py or defaults.py), and test_t5_main_start.py skips whole-module, so start refusal through main stays unproven.
2. Major: there is no cap on connection threads or on work before the signature check (server.py:167-170); a fresh timestamp alone buys up to 16 HMACs over a body of up to 8 x MAX_DOCUMENT_BYTES.
3. Minor: the qualification loop is copied (worker.py:439-450 versus cli.py:288-299, with agent_loop.py:207 a third caller of assert_qualified), and sender_list duplicates _sender_map.
4. Minor: the HADAVIN_REQUIRE_PG switch fails only skips whose reason names the DSN or psycopg, so the "config not on this branch" and win32 skips pass green.
5. Minor: any exception becomes the same 503 (worker.py:211-217, endpoint.py:310-314), so a permanent fault looks like an outage to n8n. Also: weak "status < 500 or == 503" asserts in the crash-matrix tests, a 32-equal-character secret passes, SIGTERM is unverified on Windows, and root logging.basicConfig(INFO).

# review-code-D-3 (fresh result reviewer, 2026-11-20, read-only)

Target: worktree cloud-core-a, branch cloud/core-a.
- Source read: src\hadavin_sdk\triggers\endpoint.py (343 lines), worker.py (554), server.py (176), approvals\hmac_v0.py, and cli.py:280-305.
- Tests read in part: tests\triggers\conftest.py, test_t5_main_start.py (first 70 lines), the end of test_t5_cases.py, and the matching lines of test_t5_crash_matrix.py and test_t5_crash_matrix_paths.py.
- Spec: plan-v4-final.md, review-code-D-1 and review-code-D-2.

## Verdict
No Blocker. The signing, window, run_id, 409 and ack-after-row logic is sound. The worker still cannot start from a real config, and the tests meant to prove that skip silently.

## Verified in the code (not re-reported)
- **HMAC v0 (hmac_v0.py):**
  - The signed text is "v0:" + ts + ":" + body (:26-28).
  - The compare is hmac.compare_digest (:51).
  - The timestamp must be ASCII digits, at most 12 long, and within 300 s in both directions (:47).
  - endpoint.py:175 cuts the clock to whole seconds, so the D-1 Minor 1 boundary is fixed.
- **verify_any (endpoint.py:177-182):** it tries every secret and never stops early. Two matching senders give None, which is a 401.
- **Order of checks (endpoint.py:274-300):**
  - The order is path, method, Content-Length, size cap, read, verify, then parse.
  - A 413 does not read the body.
  - A 401 comes before start, so the store is not touched.
  - Nothing is parsed or looked up before the signature verifies.
- **run_id (endpoint.py:110-121):** tenant, sender and key are in a NUL-separated hash, with fullmatch on all three, so NUL and newline tricks cannot collide. trigger_ref carries the SHA-256 of the document (:124-126).
- **409 and ack (worker.py:185-277):**
  - Every 2xx comes from _answer(found), a stored row.
  - 409 is decided from the row's agent, principal and trigger_ref, never from an exception.
  - Runner.close sets _closed under the same lock that guards submit, so no job is submitted to a shut pool.
- **Parsing (endpoint.py:136-154):** duplicate JSON members, a lone surrogate, a deep nest, a huge number and a BOM are all mapped to 400.
- **Round-2 fixes, verified in code:**
  - SIGTERM drain (worker.py:473-496).
  - IPv6 host refused (:349).
  - A port in use becomes ConfigError (:431-434).
  - Start-up error text is class name only (:530-544).
  - Tick checked at start (:453-470).
  - Secret rules and count (endpoint.py:185-221).
  - The stdlib body and Server header are removed, and HTTP/2 maps to 400 (server.py:76-100).
- **Logging:** only class names, status, sender id and run_id are logged. Unverified refusals are DEBUG. I found no path in these three files that logs a body, key, header or secret.
- **Duplicate signature or timestamp headers:** from memory of the stdlib, wsgiref joins them with commas, which fails the digit test and gives 401. I did not run this.

## Major

### 1. The worker cannot start from a real config, and the tests that should prove it skip silently
- **Where:** worker.py:402-411 and 506-508, worker.py:362, test_t5_main_start.py:30-31 and 47-49, conftest.py:44.
  - worker.py:402-411 and 506-508 use getattr fallbacks for max_running, ack_wait_s, poll_s, max_waiting, host, port and allow_non_loopback.
  - worker.py:362 depends on App.trigger_secret.
- **What is missing:** a grep of config.py, app.py, registry.py and defaults.py finds no "triggers", "trigger_secret" or "TRIGGER_". Config.triggers, App.trigger_secret and the defaults of REQUEST 001 are not in this tree.
- **Failure scenario 1:** main() always exits 2 on a real install.
- **Failure scenario 2:** if REQUEST 001 lands with a differently spelled field, for example ack_wait_seconds, getattr silently uses the local default and no test fails.
- **Why the tests do not catch it:**
  - test_t5_main_start.py skips its whole module when hadavin_sdk.config has no TriggerSettings, and also skips on win32.
  - The HADAVIN_REQUIRE_PG strict switch turns a skip into a failure only when the skip reason contains "HADAVIN_TEST_PG_DSN" or "psycopg".
  - So a green run with every main-start case skipped is accepted. Start refusal through main (D-1 H8, D-2 Major 4 remainder) is still unproven.
- **Fix:**
  - Do not call this step done until the evidence run shows the test_t5_main_start tests as passed, not skipped.
  - Extend the strict switch to also fail the "trigger config not on this branch" skip.
  - Delete the getattr fallbacks when REQUEST 001 lands.

### 2. No cap on connection threads or on work before the signature check
- **Where:** server.py:167-170 (ThreadingMixIn, one thread per connection, no limit), worker.py:68-82 and endpoint.py:278-294.
- **What is capped:**
  - Waiters inside start (128, then 503). They are counted only once the request is verified and inside Runner.start.
  - Run slots (max_running 1).
  - Ack wait (30 s ceiling).
  - Body size (8 x MAX_DOCUMENT_BYTES ceiling).
  - Senders (8) and secrets per sender (2).
- **What is not capped:**
  - The number of connections and threads.
  - The total time of a request. The socket timeout is per receive.
  - Before any signature check, a caller can hold a thread while sending a body of up to max_body_bytes.
  - Then, with only a fresh timestamp and no secret, each request costs one HMAC per configured secret (up to 16) over the whole body.
- **Failure scenario:** a few thousand slow connections exhaust memory or threads of the process that also runs the agent loop. The loop and the legitimate n8n calls stall. With allow_non_loopback this is reachable by anyone who reaches the port. Behind loopback it needs a proxy that does not buffer.
- **Why Major:** D-2 Minor 1 and the README accepted this as "put a buffering proxy in front". The brief asks for thread caps, and a bounded semaphore in QuietServer.process_request plus an absolute per-request deadline is a few lines. If the plan's M2 and M3 only require what is already capped, downgrade this to Minor.

## Minor
1. **Duplicate code, qualification loop.**
   - worker.py:439-450 (_qualified_agents) repeats cli.py:288-299 (_tick) except for the output channel (logging.warning versus print to stderr). agent_loop.py:207 is a third caller of assert_qualified.
   - Failure scenario: a change to what "qualified" means in one place does not reach the others. One shared helper removes the copy.
2. **Duplicate code, sender maps and constants.**
   - worker.py:288-295 (sender_list) and endpoint.py:224-233 (_sender_map) both turn a config list or mapping into id to sender.
   - worker.py:404 and endpoint.py:267 both call check_secrets.
   - worker.py:73-87 repeats constants that REQUEST 001 should own (NEEDED-CHECK: one place per job).
3. **A permanent failure looks like an outage.**
   - worker.py:211-217 and endpoint.py:310-314 answer 503 for any exception, including an internal bug or a refusal that will never succeed. The ERROR log line is the only difference.
   - n8n retries and then gives up into its error workflow with no hint. This is safe by design (no ack), but say it in the README.
4. **Secret strength.** endpoint.py:206 checks length 32 only, so 32 equal characters pass (D-2 Minor 12, still open). There is no entropy check, and nothing stops a trigger secret equal to the approvals secret (D-2 Minor 9, README sentence only).
5. **Weak lines in tests.**
   - test_t5_crash_matrix.py:432 and 578, and test_t5_crash_matrix_paths.py:826 and 948, assert "status < 500 or == 503". That accepts 400, 401 and 409.
   - Each is followed by a stricter assert, so the test can still fail, but the first line is dead and misleading. Delete it.
   - The crash matrix, all Postgres tests and fuzz layer 3 pass by skipping without HADAVIN_TEST_PG_DSN unless HADAVIN_REQUIRE_PG=1 is set. The evidence log must show it was set.
6. **The drain is unproven on the owner's platform.**
   - The SIGTERM tests (test_worker.py:764 and 790, test_t5_process.py:173, all of test_t5_main_start.py) skip on Windows, and on Windows SIGTERM is not delivered to a Python handler.
   - Only Ctrl-C works there (worker.py:489). The README should say the worker is for Linux or containers.
7. **Root logger side effect.** worker.py:527 calls logging.basicConfig(level=INFO) on the root logger, so every other library that logs at INFO (HTTP clients may log URLs) now writes to stderr. Set the level on the hadavin_sdk loggers only.

## What I did not check
- **Plan M2 and M3:** I could not find them as thread and wait caps. plan-v4-final.md has only B1 to B5 and no section D, so I judged the caps from the brief text. The ticket file D-signed-endpoint.md was not opened.
- **Nothing was run:** no tests, no mutants, no sockets, and no evidence-*.md file was opened. Stdlib behaviour (wsgiref header joining, socketserver shutdown) is from memory.
- **n8n and testing:** the n8n templates and test_n8n_template.py were not opened, so the status of D-2 Majors A and B (n8n template) here is unknown. I looked for the testing helpers only by listing the triggers folder.
- **Not read:** test_endpoint.py, test_worker.py, test_t5_wsgiref.py, test_t5_postgres.py and test_t5_fuzz*.py (greps only), crash.py, store\postgres.py (commit visibility of create_run), and the internals of Runtime.handle (thread safety of real model clients and the audit chain).
- **Branch:** it may have moved since my reads. Line numbers are from this session.
- **Rules:** I used STUDIO-PREAMBLE items 5, 6, 20, 22 and 25. I did not grep the bible R-numbers.

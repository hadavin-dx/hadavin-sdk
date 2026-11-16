**Package Q8a-2, head c19d87dc0588a27be7af234f2577c1b73eacf205, round 5, persona: design critic (focus: the item 2 deviation)**

Verdict: the try/finally design with ERROR logged before the answer and the `_Reported` flag is correct for all four properties you asked about. I found no Blocker or Major. I read the code and tests only; I did not run them. There are two Nits.

Paths below are in `/home/user/build/snap/q8a2b4-c19d87dc/files/`.

### [N1] Nit - the `reported.flag = False` reset in `setup()` cannot be tested, and it is not a per-request reset
Where: `src/hadavin_sdk/approvals/receiver.py:173`, with `:47-50` and `:168`
What: The flag is a `threading.local` created once per `serve()` call and reset in `Handler.setup()`, which runs once per connection, not once per request. `ThreadingHTTPServer` starts a fresh thread for every connection, so the thread-local already starts at `False`, and the reset line is dead today. No test can fail if it is deleted.
Why it matters (concrete input -> wrong output): Nothing breaks now. The handler does not set `protocol_version`, so it stays HTTP/1.0 with one request per connection. If someone later sets HTTP/1.1 keep-alive, or moves to a thread pool, then:
- a first request on a connection fails and sets the flag;
- a second request on that connection hangs up, and `handle_error` sees the stale flag and logs only DEBUG.
Suggested fix: Either reset the flag at the top of `do_POST` (that is per request and costs nothing), or add a comment that the design relies on one thread and one request per connection. Do not leave the line looking like a guarantee.

### [N2] Nit - the write-timeout test replaces `_answer` instead of failing a real write
Where: `tests/test_q8a2_callback.py:687-718`
What: The test swaps `_answer` for a function that raises `TimeoutError`. That proves the ERROR is written before the answer, and stdlib's swallow of `TimeoutError` in `handle_one_request` is then exercised, because the exception does escape `do_POST`. The test does not exercise the real `settimeout`, `send_response` or `wfile.write` path. The docstring says a real peer cannot be made to stop the write, which I accept.
Why it matters: A later reorder that puts the answer back before the log would still be caught, because the raise comes before any log. So the test can fail on the property that matters, and I am not asking for a change.
Suggested fix: None required.

### Judgment of the design

1. **Exactly one ERROR per failed request: holds.**
   - `do_POST` (`receiver.py:198-206`) sets `failed` to `True` first and clears it only after `handle_action` returns. Any exception, including `BaseException`, reaches the `finally` with `failed` true.
   - The `finally` sets the flag, then logs ERROR once with `_kinds(sys.exception())`. `sys.exception()` returns the in-flight exception inside a `finally` entered by an exception.
   - If `_answer` then raises (BrokenPipe, reset, or anything else), the error escapes `do_POST` with the handler failure as its `__context__`. `handle_error` (`:243-248`) sees `already_logged` and writes DEBUG only.
   - If the handler succeeded and only the write fails, the flag is `False`. `hung_up` then decides: a bare `ConnectionError` gives DEBUG, anything else gives ERROR, once.
   - The non-handler paths are 404, 400, 413 and the body read. They never set the flag, so they keep the old hang-up or timeout rules.
   - Tests cover all of this: `test_q8a2_callback.py:627-651`, `:667-684` (six error kinds, including `ConnectionRefusedError`) and `:823-843` (failure plus hang-up in one request).

2. **None lost on write timeout: holds.** The ERROR is written before `_answer` runs (`:205-206`), so stdlib swallowing `TimeoutError` as DEBUG `Request timed out` (`handle_one_request`, which never calls `handle_error`) cannot drop it. The test at `:691-718` checks this: exactly one ERROR, and `RuntimeError` is the only kind named.

3. **No message text logged: holds.**
   - `_kinds` (`:53-65`) takes only `type(exc).__name__`, is bounded at five kinds with a seen-set against `__context__` cycles, and appends `...` when the chain is longer.
   - No `exc_info` is passed anywhere.
   - `log_message` (`:221`) replaces exception arguments with their class names.
   - The tests assert that "secret text" and "store is down" are absent and that no record carries `exc_info` (`:649-652`, `:684`, `:719`).
   - `_LOG.info("channel action: %s", reason)` at `:106` logs the existing `reason` string. It is not new in this change.

4. **Flag cannot leak between requests on a reused thread: holds today, with the caveat in N1.**
   - `ThreadingMixIn.process_request` starts a new thread per connection, and `handle_error` runs in that same thread.
   - The thread-local is per server, because it is created inside `serve()`, so two servers do not share it.
   - The class default is `False`, and `setup()` resets it as well.

5. **Dropping catch-and-re-raise for try/finally is sound.** `finally` runs for every exception without a broad `except`, so BLE001 does not apply, and the original exception still propagates unchanged to stdlib and `handle_error`. The ordering log, then answer, is what makes the write-timeout case safe. A re-raise would not have changed that.

### Checked and found fine
- `receiver.py:198-206`: `failed` is true until `handle_action` returns, so `BaseException` is also logged.
- `receiver.py:243-248`: the DEBUG-or-ERROR choice is decided by state (`already_logged`) first, then by `exc.__context__ is None` for a bare hang-up.
- The r4 items now present at head:
  - m1 is fixed: ConnectionRefusedError from the store is logged at ERROR.
  - m2 is fixed: the ERROR is not lost when the write times out.
  - m4 is fixed: `_kinds` is bounded with a seen-set.
  - n1 is fixed: the docstring sentence at `:95-96` reads correctly.
  - m3: `\x7f`, U+2029, bidi characters and U+200B are present in the log-forgery test string at `tests/test_q8a2_callback.py:978`.
- `_answer` sets `settimeout`, so the write has the same bound as the read.
- The path is compared on `requestline.split()[1:2]` before any other work, so 404s are cheap.
- `callback_path` fails closed with a sanitised, length-bounded channel name in the `ConfigError` message.
- `body_length` rejects multiple Content-Length lines and non-digits, and caps long digit strings without `int()`.

### Not checked
- I did not run any tests, ruff or bandit.
- I did not review `channel.py`, `slack_channel.py`, `hmac_v0.py`, the guard file, the CHANGELOG, or the rename and guard parts of the ticket. This round was scoped to the `do_POST` and `handle_error` design.
- I did not verify the mutant list for the new `_Reported` behaviour.
- I did not check stdlib behaviour on a Python version other than the 3.11+ implied by `sys.exception()`.
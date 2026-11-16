<!-- full hand-back report of sub-agent a21ecf6d, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8a-2 round 4 delta review, head 3210f93a. I read the code and tests only and ran nothing.

VERDICT: READY by reading. 0 Blocker, 0 Major, 4 minor, 3 nits.
- No evidence exists for this head yet. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/ holds only scripts, initdb.log, full-meta.txt and full-outer.log. There is no EVIDENCE-REPORT.md or RESULTS.md.
- Every "fails if removed" statement below comes from tracing the test against the code, not from a run.
- Clearance should wait for the runner's mutant and full-suite results.

Paths below are under /home/user/build/snap/q8a2-3210f93a/. Test line numbers are in tests/test_q8a2_callback.py.

## Round 3 findings

**The round 3 Major (handle_error untested) is closed.** The tests are:
- `_handle_error_records` (:707-726) calls the real `Server.handle_error` inside nested `except` blocks. That gives a genuine `__context__` chain.
- :730 `test_a_hang_up_alone_is_debug`
- :738 `test_a_hang_up_after_a_failed_handler_is_error_and_names_both_kinds`
- :750 `test_any_other_error_is_error_with_its_kind_only`
- :627, :655 and :684 test it through a real socket, with a bounded `_wait_for` instead of a sleep-then-negative check.

**Round 3 m1 (the reset test never reached the `_answer` write path) is closed.** The test at :684 uses `_Slow`, which pauses in `receive` while the client resets, so the answer write fails. The body-read reset test has its docstring corrected (:569-571).

**Round 3 m3 (the 12-digit guard written twice) is closed.**
- `hmac_v0.MAX_HEADER_DIGITS` and `is_plain_digits` are used by `verify` (hmac_v0.py:57) and `body_length` (receiver.py:91, 93).
- :830-845 asserts identity with `is`.
- These are the only two header-number paths in src. The other hits for `isdigit` and `int(` are unrelated (redact.py's 18-digit suffix, migration_numbers).

**Round 3 m4 (unverified retry claim) is closed.** The wording is now "a sender that retries on 5xx" (receiver.py:126).

**Round 3 m5 (timing ceilings) is closed.** The ceilings are now 4 s (:520, :558).

I did not re-check round 3 m6 to m8 or the nits.

## Mutants, by tracing

| Mutant | Result | Killed by |
|---|---|---|
| `hung_up` never true | killed | :730, which expects DEBUG for a lone hang-up, and :655 |
| no `len(kinds)==1` | killed | :738, which expects ERROR with "ConnectionResetError while handling RuntimeError" |
| `str(exc)` added to the line | killed | "store is down", "secret text" and "request text" must be absent from `caplog.text` (:650, :735, :747, :755). Exact-message equality also fails. |
| ERROR to DEBUG, or the reverse | killed | Levels are asserted exactly in :738, :750 and :627 |
| raw log text (`_LOG.debug(format, *args)`) | killed | :792 expects `??` and `?[31m` |
| no cut | killed | :793 (`len(third) == 200`) and :774 (`len(shown) == 200`) |
| bool accepted | killed | `True` and `False` are in the bad list (:807-808). `type() in (int, float)` is what rejects them. |
| no max bound | killed | `10**10`, `3601` and `inf` are refused; `3600` and `3600.0` are accepted |
| zero, negative, nan or inf accepted | killed | all are in the bad list |

## Checks asked about

**`_plain` (receiver.py:34-37) is sound.**
- `str.isprintable` is False for categories Cc, Cf, Zl, Zp, Cs, Co and Cn, and for every space except ASCII space.
- So C0, `\x7f`, C1 (including `\x85`), U+2028 and U+2029, the bidi overrides and isolates (U+202A-E, U+2066-9, U+200E and U+200F) and zero-width characters all become `?`.
- The cut happens first, so the cost is bounded.
- The request line is decoded latin-1, so no surrogates appear.
- Printable look-alike letters still pass. That is expected.

**`log_message` and `handle_error` cannot leak a request value or secret by themselves.**
- `handle_error` logs only the class names (`type(exc).__name__`). It has no `exc_info` and no message.
- `log_message` logs the request line, at DEBUG only. Headers, body and client address are never logged.
- The request line can carry a query string, but only at DEBUG. That is documented in the serve docstring (:127-128).

**`format % args` raising inside `log_message`:**
- TypeError and ValueError are caught and the raw `format` is logged. That is safe because the format is a stdlib constant. The ValueError path is tested (`"100%"`, :785-787).
- Other exceptions, such as OverflowError from `%c` with a huge int, are not caught. No stdlib call site can produce them: the stdlib's own `log_request` and `log_error` calls pass str, int and HTTPStatus.
- If one escaped, it would propagate out of `handle_one_request` into `handle_error` and be logged as one ERROR line with the kind only. There would be no crash and no traceback.

**Digit guard use (`MAX_HEADER_DIGITS`, `is_plain_digits`):** see round 3 m3 above.

## New findings

**m1 (Minor). A handler failure that is a builtin `ConnectionError` is logged only at DEBUG.**
- Where: receiver.py:198, `hung_up = isinstance(sys.exception(), ConnectionError) and len(kinds) == 1`.
- Scenario:
  - `handle_action` raises `ConnectionRefusedError` or `RemoteDisconnected` (a `ConnectionResetError` subclass) from a store or channel.
  - The `finally` answers 500 and the original exception propagates with an empty context.
  - `kinds == ["ConnectionRefusedError"]`, so the line is DEBUG. An operator at the default level sees nothing about a store outage.
- Most stores wrap such errors, which is why this is Minor. No test covers it.
- Fix: decide from state, not from the exception type. For example, set `self._handled = True` in `do_POST` once the body has been read, or wrap the `handle_action` failure in a marker. Then add a test where `_Recording` raises `ConnectionRefusedError` and expects ERROR.

**m2 (Minor). A write timeout in `_answer` after a handler failure loses the ERROR line.**
- Where: receiver.py:165-166 and the stdlib `handle_one_request`.
- The `TimeoutError` raised by the `finally` answer carries the `RuntimeError` as its context. The stdlib's `except TimeoutError` catches it and logs "Request timed out" at DEBUG, so `handle_error` never runs.
- This needs a peer that stops reading a few bytes. It is rare, but the failure is silent.
- Fix: log the handler failure at ERROR inside `do_POST` (for example `except Exception` with a kind-only line, then re-raise). Otherwise note it in the docstring.

**m3 (Minor). `_plain` tests do not pin every claimed class.**
- Where: :784 covers `\r`, `\n`, `\x1b`, `\x85` and U+2028. It has no `\x7f`, U+2029, bidi (U+202E, U+2066) or U+200B.
- A mutant that replaces `isprintable()` with a hand-written control range would pass if it kept the listed characters.
- Fix: add those characters to the :784 string. They would be `?`.

**m4 (Minor). The error-kind chain is unbounded.**
- Where: receiver.py:195-197.
- A hand-built `__context__` cycle loops forever. A very long chain makes a very long line.
- Fix: stop after about 5 kinds, or after a seen-set hit, and append `...`.

**Nits**
- n1: receiver.py:67-68, the `handle_action` docstring says "the outcome is audited and the outcome is audited". It is a doubled phrase from an edit.
- n2: receiver.py:121, the docstring line is over-long and was left unwrapped by the edit.
- n3: `log_message` drops the client address that the stdlib line carried. At DEBUG this makes hang-up lines hard to correlate. Optionally add `self.address_string()`, passed through `_plain`.

## Not checked
- Anything that needs a run, including the timing tests under load.
- The guard tests in tests/test_lockin_guard.py, which are unchanged from round 3 as far as I was asked.
- CHANGELOG wording against the final code. :758 only greps two phrases.

Files read:
- src/hadavin_sdk/approvals/receiver.py
- src/hadavin_sdk/approvals/hmac_v0.py
- tests/test_q8a2_callback.py (lines 480-850 and grep hits)
- Round 3 reports: /home/user/hadavin-sdk/handover/reviews/Q8a-2/result-r3-design-full.md and result-r3-codebase-full.md

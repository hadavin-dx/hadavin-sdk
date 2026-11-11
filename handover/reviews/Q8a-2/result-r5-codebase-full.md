Package Q8a-2, head c19d87dc0588a27be7af234f2577c1b73eacf205, round 5, persona codebase details. Review by reading only; nothing was run.

Verdict: 0 Blocker, 0 Major, 2 Minor, 1 Nit. All r4 fixes are in the code. The CHANGELOG error-line claim holds against the code. The held-connection cause is plausible but has no evidence on this head.

Paths are under /home/user/build/snap/q8a2b4-c19d87dc/files/ (rcv = src/hadavin_sdk/approvals/receiver.py, test = tests/test_q8a2_callback.py).

## r4 fixes, checked at the lines

- **m1 (a store ConnectionError was logged at DEBUG): fixed.**
  - rcv:198-206: `do_POST` sets `reported.flag = True` and logs ERROR from `sys.exception()` in the `finally`, before `_answer`. The class of the error is not consulted.
  - rcv:242-249: `handle_error` logs DEBUG when `already_logged` or when the hang-up has no context (`exc.__context__ is None`). Otherwise it logs ERROR.
  - test:667-683 runs six failure kinds, including `ConnectionRefusedError`, through a real socket and expects exactly one ERROR with the kind only and no `exc_info`.
- **m2 (a write timeout swallowed the ERROR line): fixed.**
  - The ERROR is written before `_answer`.
  - test:691-719 replaces `_answer` with a raising `TimeoutError` and expects one ERROR.
  - Replacing `_answer` is justified in the docstring, because a few answer bytes cannot fill a socket buffer.
  - test:823-843 covers a failure plus a reset (`_SlowFailure`) and expects exactly one ERROR.
- **m3 (`_plain` characters): fixed.** test:978 now includes `\x7f`, U+2029, U+202E, U+2066 and U+200B. The expected output at test:989 has 7 `?`, which matches the 7 characters after `[31m`.
- **m4 (unbounded error chain): fixed.**
  - rcv:53-65 uses a seen-set (by `id`) and a cap of 5, and appends `...`.
  - Tests cover 10 errors, exactly 5, a two-error loop, and a self-context.
  - I traced the expected strings at test:897, :909, :919 and :937 against the loop, and they match.
- **n1 (doubled docstring phrase): fixed.** rcv:95-96 now reads "the outcome is audited, and tick updates the channel message".
- **n2 (over-long docstring line): fixed.** rcv:110-115 is wrapped.
- **n3 (client address not logged): declined, and the reason is consistent.** `log_message` at rcv:216-226 still logs no address. I found nothing that contradicts it.

## The five items you asked about

### 1. Server backlog setting: correct and effective
- defaults.py:134 sets `RECEIVER_BACKLOG = 128`, with a comment that matches the mechanism: the read bound starts at accept.
- rcv:228-231 sets `request_queue_size` on the `Server` class, which is defined before it is constructed.
- stdlib `TCPServer.__init__` calls `server_activate`, which does `listen(self.request_queue_size)`. The class attribute is therefore what listen receives.
- The kernel may cap 128 at `net.core.somaxconn`. That does not matter here.

### 2. Is the deterministic backlog test enough? Mostly yes, with one gap and one flake risk
- **The deterministic test (test:755-760).**
  - It asserts `server.request_queue_size == defaults.RECEIVER_BACKLOG > 5`.
  - It fails if the setting is removed or lowered to 5, and that is the only regression that matters.
  - It checks the attribute, not the value that reached `listen()`. A later override of `server_activate` or `server_bind`, or a socket created elsewhere, would pass it.
  - A stronger check would wrap `socket.socket.listen` to record its argument during `serve(port=0)` and assert it equals `RECEIVER_BACKLOG`.
- **The burst test (test:722-752).**
  - Your premise holds: the builder says it does not fail reliably on old code, and I found nothing in the snapshot that proves otherwise. It cannot discriminate.
  - The test docstring and the CHANGELOG quote measurements of 8 to 25 of 50 over the bound (CHANGELOG line 265, test:726). Those are for 50 connections and a 2 s bound.
  - The test itself uses 150 connections and a 1.0 s bound. I found no measurement of that configuration on old code.
  - Its failure mode is a client-side recv waiting up to 20 s (the `settimeout(20)` at test:735), which makes it slow when it does fail.
  - The 150 client threads and the server run in the same process, so GIL contention can push the lifetime past `bound + margin`. The margin is only 1.5 s, and the lead notes the CPU is shared through heavy.sh. That makes it a flake risk on good code. Round 4 flagged the same class of risk for timing ceilings.
  - Recommendation: keep it only as an integration smoke test, rename or caveat it as non-discriminating, and widen the margin or mark it as timing-sensitive. Do not count it as proof of the fix.

#### [Q5-1] Minor - the backlog test checks the attribute, not what reaches listen
Where: test:755-760, rcv:228-231.
What: it asserts `server.request_queue_size`, not the argument passed to `listen()`.
Why it matters (concrete input -> wrong output): a later `server_activate` override, or a `Server` built another way, calls `listen(5)` while `request_queue_size` still reads 128. The test stays green and the held-connection bug returns.
Suggested fix: record the `listen` argument by wrapping `socket.socket.listen` during `serve(port=0)`, or add that assertion to the existing test.

#### [Q5-2] Minor - the burst test cannot tell old code from new and its margin is tight
Where: test:722-752.
What: see item 2.
Why it matters (concrete input -> wrong output): on a loaded CI host a correct build can exceed 2.5 s from connect start and fail. A reader who sees the test pass may believe it proves the fix, when it would also pass on a backlog of 5.
Suggested fix: as in item 2. Also say in the docstring that the 150/1.0 s configuration was not measured on old code.

### 3. CHANGELOG error-line claim against the code: matches
- CHANGELOG line 265 is the item that carries all four claims below.
- **"A failed request gets exactly one error level line."** True for a handler failure, with or without a failing answer write (rcv:198-206 with 242-249; tests above). I found no path in `do_POST` where a handler failure logs two ERROR lines.
- **"A store that refuses the connection (`ConnectionRefusedError`) is logged at error level."** True (rcv:205, test:667).
- **"Logged even when the answer cannot be written because the caller stopped reading."** True (test:691).
- **"A caller that hangs up after that adds only a debug line."** True, because `reported.flag` forces DEBUG (rcv:243-246).
- **Chain claims.** "At most five at a time, joined by `while handling`, `...`, stops at the first repeat" matches rcv:53-65.
- **No-traceback and message claims.** Neither the message nor a traceback is logged (rcv:205, 245-249).
- **`test_the_error_line_is_what_the_changelog_says_it_is` (test:949-953)** only greps four phrases, and all four are present. The behaviour is held by the other tests, not by this grep.
- **Measurement wording.** The CHANGELOG says "measured with 50 silent connections and a 2 s bound ... 8 to 25 of 50 ... some for 30 s". That is a statement about the old code from the builder's measurement. I cannot confirm it from the snapshot.

#### [Q5-3] Nit - a CHANGELOG measurement has no evidence on file
Where: CHANGELOG.md:265, test:726.
What: "8 to 25 of 50 ... some for 30 s" has no evidence file I could find under handover/evidence/Q8a-2. The nearest evidence, 3210f93/EVIDENCE-REPORT.md:9, shows 45/50 and 47/50 closed on the previous head.
Why it matters: a CHANGELOG number with no recorded run.
Suggested fix: cite the run, or soften the wording.

### 4. Held connections (earlier evidence: 45/50 and 47/50 closed)
- **What the earlier evidence shows.** The 3210f93 evidence report (EVIDENCE-REPORT.md:9) says that after the 10 s bound plus 2 s, 45 of 50 silent and 47 of 50 short-body connections were seen closed. Partial-first-line was 50 of 50, and the previous report had 50 of 50 in all three. The runner wrote "I did not investigate".
- **Is the backlog change the right cause?**
  - It is plausible. Parallel opening of 50 clients against a backlog of 5 makes some connects wait on SYN retransmit, and the server bound only starts at accept. A counted miss then comes from a connection whose lifetime from its own connect exceeded the bound.
  - It is not proven. The earlier evidence did not measure when each connection was accepted.
  - Variant A, serial opening, was already known to inflate times (f6c2a3d/EVIDENCE-REPORT.md:21), which supports that accept timing, not the bound, drove those numbers.
  - A second contributor is possible and unmeasured: the evidence script and the server share one process, so GIL contention could delay the check. The script's own check time is not known from the snapshot.
- **No evidence exists for c19d87dc.** The only evidence dirs are 02068eb, 5f94f59, f6c2a3d and 3210f93. The held-connection step needs a re-run on this head before it is called closed. It should print each connection's own lifetime, not a count at one instant, so a repeat of 45/50 shows whether the cause was queueing or the bound itself.
- **Read bound is correct in the code.** `_DeadlineReader` uses a fixed monotonic end set at construction (rcv:124-139). Each read waits only for the time left, and it raises `TimeoutError` at the end. The stdlib then closes the connection without an answer. A silent client is therefore dropped at accept time plus `read_timeout_s`.

## Checked and found fine
- `body_length` and the 12-digit guard are shared with `hmac_v0` (rcv:22-23, :110-121).
- `_plain` uses `isprintable` and cuts first (rcv:41-44). `log_message` and `handle_error` log kinds only, with no message, address or traceback (rcv:216-249).
- The path is compared on the raw request line before any other work (rcv:184).
- `serve()` validates `read_timeout_s` by exact type, so a bool is refused (rcv:159-166).
- The refusal message names the channel safely (`_shown_name`, rcv:68-75) and states the grammar and length (rcv:84-88).
- The `reported` thread-local is reset in `setup`, and the stdlib handler serves one request per connection thread.
- `handle_action` is unchanged in behaviour: 413, 401, and 200 for an unknown approval (rcv:92-107).
- The module docstring states that `serve` does not limit open connections (rcv:6-8). The CHANGELOG repeats it.
- The CHANGELOG upgrade bullets match the code on the rename, the removed `PATH`, the doubled-slash behaviour change and the `callback_path` grammar.

## Not checked
- The Slack kind over a real socket, and a run of any test, timing or burst.
- tests/test_lockin_guard.py, tests/contracts/test_capabilities.py, tests/test_p7_tick.py, channel.py, gate.py and the renames. This round was scoped to the receiver, the backlog and the CHANGELOG error line.
- The long lock-in guard CHANGELOG bullet (line 266) against the guard code.
- Whether `net.core.somaxconn` on a given host limits the backlog below 128.
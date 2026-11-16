<!-- full hand-back report of sub-agent a3dab418, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: no Blocker and no Major found by reading. Counts: 0 Blocker, 0 Major, 6 Minor, 4 Nit. Everything that needs a run is UNPROVEN, because the independent evidence folder does not exist: /home/user/hadavin-sdk/handover/evidence/Q8a-2/f6c2a3d/ was empty or missing when I looked. Do not treat this as a merge clearance until RESULTS.md arrives. This is a security path with no round cap, so I would not close it on reading alone.

## Are the earlier Majors really closed? (checked in the f6c2a3d code, not in notes)

- **Round 2 design M1, string boundary built from a hand-picked list: closed.**
  - tests/test_lockin_guard.py:851 now uses lookarounds: `(?<![A-Za-z0-9])(?:{_W_SPLIT})(?![A-Za-z0-9])`.
  - Any character that is not an ASCII letter or digit is a boundary. That includes `|`, quotes, brackets, braces, `=`, and `:` on both sides.
  - By reading, `"^(slack|teams)$"`, `"kind = 'slack'"`, `"{aws_region}"`, `"[slack]"` and `"channel:slack"` all match now.
  - The two PATTERNS entries (:854 and :872) are complementary. The second excludes via `\A(?!(?:W)(?::|$))`, which is the first entry's text, so one string gives one line.
  - The three gate hits are exact `WORD_IN_OK` entries (:701-725). Their line counts are pinned in `_WORD_IN_OK_LINES` (:1986) and each has a removal test.
- **Round 2 codebase F1, `from x import slack as chat`: closed.**
  - :1095 emits both `a.name` and `a.asname` for `from` imports.
  - Relative `from . import slack` is covered too, since the name is emitted even when the module is empty.
- **Round 2 m2, names that are only read: closed.** `_scanned_names` now returns Name and Attribute reads, marked "plain read" (:1083-1086). The docstring no longer claims they are exempt. Only reads of the pinned table names inside `backends.table` are skipped (:1140).
- **Round 2 m1 (two-part words), m7 (chat vendors), m6 (async skip):** closed by reading.
  - `TWO_PART_WORDS` covers the two-part words.
  - Seven chat and paging vendors were added.
  - The async skip was reverted (:893).
- **Round 1 Majors:** I could not re-read them in this review. The gcs prefix, import path and one-checker items look present in the code.
- **Round 2 codebase F2 (`Content-Length` of 4301 digits raised in `int()` before the path check):** closed in `body_length` (receiver.py:71-81). Length is capped at 12 digits before `int()`, and the path is judged first (:130).
- **Round 2 codebase F5 (unchecked fallback class name in the error text):** closed. `_shown_name` (:30-36) applies one check to whichever name was chosen: cut to 64 characters, then non-printables become `?`. It uses `str.__str__`, so a str subclass cannot bring its own text. This is pinned by a test.

## Read-bound and timeout logic (traced against the standard library's `handle_one_request`)

- **A slow client cannot hold a thread past the deadline.**
  - `_DeadlineReader` fixes one end time at `setup()`. Each `readinto` sets the socket timeout to the time left, so dripping one byte at a time does not extend it.
  - The first line, the headers and the body all read through it, so one bound covers the whole request.
  - The server uses HTTP/1.0 with no keep-alive, so the deadline cannot be re-armed by a second request on the same connection.
  - `TimeoutError` raised inside `do_POST` or inside `parse_request` is caught by the library's `except TimeoutError` in `handle_one_request`. It is logged at debug and the connection closes with no answer. The body read happens before the 500 `try`, so a timeout does not produce a 500.
- **One slow client cannot starve a signed request.** `ThreadingHTTPServer` gives each connection its own thread, and the accept loop never reads from a client. This holds by reading only.
- **The write side is bounded.** `_answer` resets the timeout to `read_timeout_s` before writing. `sendall` treats the timeout as a total deadline, and the answer is a few bytes. The worst case is about 3 × `read_timeout_s`. This relies on CPython behaviour I know but did not read in the installed library.
- **Handler time after the read is not bounded here.** A hung store holds the thread, but that is outside this change.

## Findings

**m1 (Minor). The concurrency count is unbounded.**
- Where: receiver.py:174 (`Server(ThreadingHTTPServer)`), docstring :111-114.
- Scenario: the bound limits how long one connection lives, not how many exist. Many connections opened in a loop can use up threads or file descriptors, and a signed click then waits or fails to connect. This costs about N/10 s of attacker effort per N connections.
- Fix: the cheapest option is a docstring sentence saying `serve` is a demo and local stage server with no limit on concurrent connections, and that production hosting (S11) must limit them.

**m2 (Minor). Control characters in `log_message`.**
- Where: receiver.py:154-155.
- Scenario:
  - The override passes the stdlib's format and args straight to `_LOG.debug`. `log_request` puts the raw request line in the args.
  - A request line can hold `\r`, `\x1b` terminal escapes, `\x85` and similar characters.
  - Newer standard library versions escape control characters in their own `log_message`. This override drops that protection (from my knowledge of CPython, not checked in the installed library).
  - It is reachable without a signature, on any path, with any method.
  - It only shows when the logger is at DEBUG, but then it forges or hides log lines.
- No test covers this, and `_shown_name` shows the project already knows the fix.
- Fix: build the text first, `text = format % args`, then cut it to about 200 characters and replace each non-printable character with `?`. Log with `_LOG.debug("%s", text)`. Add one test with `\r` and `\x1b` in a request line at DEBUG.
- Not run, so this is by reading only. The same gap was noted in round 2 and left open.

**m3 (Minor). `read_timeout_s` is not checked at start.**
- Where: receiver.py:102-107, :89 and :98.
- Scenario by reading:
  - `0` or a negative value makes every request time out and be dropped silently.
  - `None` fails with a TypeError per request, caught by `handle_error`.
  - `nan` and `inf` make `settimeout` raise per request.
  - `True` is accepted as 1.
  - None of these are caught by a ConfigError at `serve()`. The module already validates `callback_path` at start, so this is inconsistent.
- Fix: in `serve()`, raise `ConfigError` unless `type(x) in (int, float)` and `0 < x < inf` (or finite). Add a test.

**m4 (Minor). The vendor word list is still a hand-kept subset.**
- Where: tests/test_lockin_guard.py:793-828.
- Scenario: `/datadog/hook`, `jira`, `servicenow`, `okta`, `splunk`, `snowflake`, `mattermost` and `sendgrid` pass both scans and the receiver whole-text test. The limit is stated ("any word that is not in VENDOR_WORDS", :17, pinned).
- Fix: none required by this ticket. Say in the PR text that the list is open-ended.
- Opposite risk: a few listed words are also English (`oracle`, `zoom`, `teams`, `discord`, `foundry`, `google`). A future error message in neutral code that uses one of them as plain prose will fail CI and need an exact allow entry. The allow mechanism handles that, so it is friction, not a hole.

**m5 (Minor). CHANGELOG bullet 8 is too dense for a non-technical reader.**
- Where: CHANGELOG.md:8.
- It is one 250-word paragraph using "second word of that line", "reverse proxy", "plain `str`" and "percent-encoding" unexplained. The first bullet does explain what the receiver is.
- Fix: split it into "what changed for a deployment" and "what a custom channel author must do". Explain "reverse proxy" in words (a gateway in front of the receiver).
- The guard docstring's "[pinned]" is also unexplained for someone outside the team. Add "(a test fixes it)" once.

**m6 (Minor). Process gap.**
- No evidence for f6c2a3d: the fail-on-main runs, the six removal probes, the HTTP matrix, the hostile-path list, the new hit counts (+0 for words and +3 for the pipe) and ruff/bandit are all unproven here.

**Nits**
- **n1:** `Content-Length: 5 ` with trailing white space gets 400, because the `email` header parser keeps trailing spaces and `isdigit()` fails. This is fail-closed and stricter than HTTP. Say so in the docstring or strip ASCII spaces and tabs.
- **n2:** `handle_error` logs only exception type names. That is deliberate (no request data) and good. An operator with a store outage sees "OperationalError" at ERROR and nothing else. A one-line pointer such as "enable debug for detail" would help.
- **n3:** A `WORD_IN_OK` entry with an empty assignment name `""` would cover every string that is not inside an assignment in that module (`assigned.get(id(n), "")`, :991). No such entry exists. A test that refuses empty-name keys would close it.
- **n4:** A name allowance is keyed by (module, name) and covers every kind of binding of that name. This is stated at :726-731 and the places are pinned by count.

## Other questions asked

- **Content-Length rules (receiver.py:71-81, :130-137), by reading:**
  - The path is judged first (404), then length (400/413), then the body.
  - A missing header gives 0. Two or more lines, an empty value, a sign, a space, a non-ASCII digit or a comma give 400.
  - More than 12 digits gives 413 without `int()`.
  - A 13-digit value with leading zeros is also 413 (pinned).
  - I found no `int()` overflow path.
- **Path judging (:130):**
  - `requestline.split()[1:2] != [path]` takes the second white-space word before the stdlib's `//` rewrite.
  - The new accept set is a subset of main's: only a leading `//` is newly refused, and the CHANGELOG says so.
  - `\xa0` and other splitter characters are still accepted as on main (pinned test). A path-filtering proxy in front could read such a line differently. Not new, but state it when hosting is decided.
  - The path is held in a closure and read once. `valid_callback_path` requires `type(value) is str`, so a str subclass cannot supply its own `__eq__`.
  - The grammar has no ReDoS risk: every repetition needs a mandatory joiner.
- **500 path (:138-144):**
  - `finally` answers 500, then the exception goes on to `handle_error`.
  - If the write also fails (BrokenPipe), the chain shows as two types and logs at ERROR.
  - A bare hang-up logs at DEBUG.
  - Idempotence on retry rests on `Approvals.decide` returning "not_pending" for a recorded decision. I read that at requests.py:146-180 and it looks consistent, but `receive` is outside this diff.
- **Least privilege and dependencies:**
  - The server binds 127.0.0.1 by default.
  - The only new imports are stdlib (`io`, `socket`, `sys`, `time`), plus the project's own `defaults` and `errors`.
  - No dependency was added. The vendor path literal lives only in `slack_channel.py:35`. `receiver.py` carries no vendor word in code, comments or docstrings, and a test holds it to that.
  - The `channel` capability still has one production kind, covered by an existing exception. This change does not touch that.
- **Guard false negatives (by reading the patterns):**
  - Caught: strings (including f-strings, `+` joins and bytes), names, import paths and aliases, SQL inside Python strings, `"x.slack.y"` module strings, and constant folding such as `f"{'slack'}"`.
  - Not caught, and listed in the docstring: camel case glued inside a string, runtime-built strings, comments, docstrings, non-Python files, look-alike scripts, and words not on the list.
  - I found no unlisted gap among the vendor-word forms asked about.
- **False positives:**
  - `awsome`, `laws` and `teamster` are safe by equality or boundary rules.
  - `team_s` and `open_ai` are intentional over-matches (pinned).
  - `s32_bucket` is handled by the digit-strip loop.
- **Allowance lists:**
  - All 13 `LITERAL_OK`, 4 `WORD_IN_OK` and 6 `IDENTIFIER_OK` entries are exact.
  - Each has a count-pinned removal test, and a completeness test (:2006-2009) ties each pinned table to its live dictionary.
  - A second occurrence of an allowed literal in the same module would fail the removal test, so allowances do not widen silently.
- **Rename coverage:** by grep, `_SLACK`, `TICK_SLACK_S`, `K8S_LOG_SLACK_BYTES` and `handle_slack_action` no longer occur in the snapshot, other than as intended text in a test plant.

## What I did not check
- Anything that needs a run: pytest, ruff, bandit, fail-on-main, the removal probes, the HTTP matrix, the 4301-digit request, the timing tests on a slow runner, and the merge with Q8a-1.
- The installed CPython's `http.server`. My reading of `handle_one_request`, `parse_request`, the log-escaping history and `sendall` timeout semantics comes from my knowledge of the library, not from the installed file.
- `Approvals.decide` and `parse_decision` beyond `receive` and `decide`, `approvals/slack.py` and `slack_channel.py` beyond the one attribute line, `tests/contracts/conftest.py` (whether the suite builds the Slack kind), `tests/test_p7_tick.py` edits, docs and CI.
- The hit lists measured in the PR notes (I was told not to read them), and the module-name and import-path plants in the guard tests, which I only sampled (about lines 1250-1950 unread).
- Whether `from tests.test_http_metadata import VENDOR_WORDS` imports under the repo's pytest setup. The regex at :1211 does fit the pattern shape at test_http_metadata.py:114-118.

Files read, all under /home/user/build/snap/q8a2-f6c2a3d/:
- src/hadavin_sdk/approvals/receiver.py
- src/hadavin_sdk/approvals/channel.py
- src/hadavin_sdk/defaults.py
- tests/test_lockin_guard.py
- tests/test_q8a2_callback.py
- tests/contracts/test_capabilities.py
- CHANGELOG.md

Main comparison: /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/approvals/receiver.py

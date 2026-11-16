<!-- full hand-back report of sub-agent ac5c317b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8a-2 result review, round 3, head f6c2a3d (snapshot /home/user/build/snap/q8a2-f6c2a3d). Code-and-docs review only; I ran nothing.

VERDICT: NOT CLEAN by reading, but close. 0 Blocker, 1 Major, 8 Minor, 3 nits.
- Every finding from rounds 1 and 2 that I could trace is closed in the code (list at the end).
- Receiver: do_POST, `_DeadlineReader`, `body_length`, `handle_error` and `_shown_name` behave as their comments say.
- Guard: I traced `_scanned_names` and `identifier_problems`; they match their docstrings.
- The evidence file for f6c2a3d (/home/user/hadavin-sdk/handover/evidence/Q8a-2/f6c2a3d/RESULTS.md) does not exist yet. Nothing below is backed by a run.

MAJOR

M1. `Server.handle_error` is untested, and the CHANGELOG states its behaviour.
- Where: /home/user/build/snap/q8a2-f6c2a3d/src/hadavin_sdk/approvals/receiver.py:158-172; CHANGELOG.md:263 items (3) and (4).
- What is claimed: a caller who hangs up logs one DEBUG line. A handler failure logs one ERROR line naming the exception kinds, chained with "while handling", with no request text and no message. This is on the security path.
- What the tests do: grep of tests/ for "ended with an error", `caplog` and "while handling" finds nothing in test_q8a2_callback.py. The tests only check that stderr has no "Traceback" after `time.sleep(0.2)`.
- Failure scenario: the level could change (DEBUG to ERROR or the reverse), the `hung_up` rule could break, or `str(exc)` could be added to the line. Every test would stay green. The sleep-then-negative check can also pass before a slow handler thread has printed anything.
- Smallest fix: one test with `caplog.at_level(logging.DEBUG, logger="hadavin_sdk.receiver")`.
  - Use the existing 500 test (`_Recording(..., RuntimeError("store is down"))`). Assert one ERROR record whose message is "a request ended with an error: RuntimeError" and that "store is down" is not in `caplog.text`.
  - Use the existing reset test. Assert that its record is DEBUG and that there is no ERROR record.

MINOR

m1. The comment in the reset test is wrong.
- Where: tests/test_q8a2_callback.py:543-557, especially the comment at line 550 and the docstring at line 544.
- Why: with Content-Length 100 and 9 bytes sent, the server is blocked in `self.rfile.read`. The RST therefore raises `ConnectionResetError` in `_DeadlineReader.readinto`, not in `_answer`.
- Effect: the `_answer` write-failure path (`ConnectionError` with `len(kinds)==1`, the debug case) is never exercised.
- Fix: correct the wording. Add a case that sends a complete request and resets before the answer, or a unit call of `handle_error` with a `BrokenPipeError`.

m2. `handle_action`'s docstring says "the channel message updated".
- Where: receiver.py:56-57.
- Why: `handle_action` calls `receive(..., record_only=True)`. The receiver does not update the message; tick reconcile does (requests.py:174-177).
- Note: main had the same text, and the ticket's E2 asked for this exact wording.
- Fix: "the outcome is audited; tick updates the channel message".

m3. The 12-digit guard is duplicated.
- Where: receiver.py:75 and 81 against approvals/hmac_v0.py:46-47. The docstring says "the same guard as `hmac_v0.verify`".
- Why: it is the same rule written twice with a literal 12, not shared. redact.py:887 has a third copy with 18.
- Fix: one named constant or helper in core (for example `MAX_DIGITS_UNIX_S` / a `plain_digits(s, max_len)` helper) used by both, or drop the "same guard" claim.

m4. "So the sender delivers it again" is unverified.
- Where: receiver.py:113 and CHANGELOG.md:263 (4).
- Why: it holds only for a sender that retries on 5xx. I could not verify that Slack retries interactive callbacks; I believe it does not.
- Also not checked: that a redelivery after a half-done `decide` is safe.
- Fix: write "a sender that retries on 5xx delivers it again".

m5. Timing bounds can flake under load.
- Where: tests/test_q8a2_callback.py:505 (`taken < 2.5` against a 0.5 s bound) and :539 (`< 2.5` against a 0.6 s bound with 0.2 s drip sleeps).
- Margin: about 2 s. A loaded CI runner can exceed it, and so can sleep overshoot in the drip loop.
- Fix: keep the bounds small but raise the ceilings to about 4 s. Both tests are already bounded above by their own 4 s and 5 s socket waits.

m6. A test depends on the draw order of the seeded generator.
- Where: tests/test_q8a2_callback.py:376-382, `test_the_generated_paths_cover_every_length_and_both_joiners`.
- Why: it needs 500 seeded draws to hit all 63 lengths. By my estimate that is about a 98% chance, and it holds only for this seed and this draw order. Any change to `_valid_path` (an extra `below()` call) can make it fail spuriously.
- Fix: build lengths explicitly (`for length in range(2, 65)`) for the coverage tests.

m7. The module docstring summary of rule c is stale.
- Where: tests/test_lockin_guard.py:6-8.
- Why: it says "names it gives to modules, functions…". The scan now also covers reads, imports (module path, original name and alias) and call-site keywords.
- Fix: one clause.

m8. Test-only hedges for running on main stay in place after merge.
- Where: `_served` (`inspect.signature` check at test_q8a2_callback.py:47-51) and `_path_before_and_after` (the `getattr(..., VENDOR)` fallback at :78-80).
- Effect: a lost `read_timeout_s` parameter or a lost `callback_path` attribute would be hidden by the fallback rather than failing. Other tests catch the `callback_path` case, and the timeout tests fail on their own bound.
- Fix: drop the hedges, or keep them with a one-line note that they exist for the fail-on-main proof.

NITS
- tests/test_q8a2_callback.py:464: the comment "bytes of an Arabic-Indic five" is wrong. The server decodes headers as latin-1, so this case is not a non-ASCII digit. Only `\xb2` tests that.
- tests/test_lockin_guard.py:1169: `sql_problems` hard-codes "bare vendor name" while `_BARE` is defined later at :1325.
- A pattern compiled with IGNORECASE folds U+017F and U+212A to s and k, so "ſlack" counts as a vendor word. Harmless over-detection; not stated or pinned.

CHECKED AND CORRECT (traced by reading)
- do_POST path check:
  - `self.requestline.split()[1:2] != [path]` is sound, and the comment about `//` rewriting is true for the required Python 3.12 or later.
  - It is the same split `parse_request` uses, so the pinned white-space test holds.
  - The absolute-form request target gets 404, as on main.
- Timeout behaviour:
  - `_DeadlineReader` raises `TimeoutError`, which is the same as `socket.timeout`. `handle_one_request` catches it around the read, the header parse and the method call.
  - Closing the original `rfile` leaves the socket open (SocketIO refcount), so the comment holds.
  - A timeout during `handle_one_request` is logged at debug and ends without an answer, as stated.
- `body_length`:
  - Behaviour matches its docstring, including the 13-or-more-digit rule (so `0000000000005` gets 413).
  - CHANGELOG lines 8-9 and 263 match main's receiver (empty header read as 0, first of two used, the ValueError past 4300 digits).
- `_shown_name`:
  - `str.__str__` returns an exact str for a subclass.
  - The 64-character cut and the `?` replacement work as claimed.
  - It applies to both the `name` and the class-name fallback.
- `valid_callback_path`: `type(value) is str`, the length limit and `fullmatch` are one checker used by receiver and contract test. The `$`-versus-`/a\n` comment is correct.
- Guard, AST scan (`_scanned_names`):
  - Reads, attributes and decorators are scanned (they are `ast.Name` and `ast.Attribute` nodes under `ast.walk`).
  - Both `asname` and the original name are scanned for `import` and `from … import`.
  - Relative imports are scanned: `from . import slack` (module None) and `from .slack import X`. `_path_segments` drops only a leading `hadavin_sdk`.
  - `global` and `nonlocal` names are scanned, with the statement's line.
  - `async def` is in `_NAMED`, and it is not skipped in the table module (matches the string scan).
  - f-string `FormattedValue` names are `ast.Name` nodes, so they are scanned. Literal parts go to the string scan.
  - Also covered: keyword names, `except … as`, match captures and rest, class-pattern `kwd_attrs`, and type parameters (`ast.TypeVar` and friends exist on the required 3.12 or later).
  - Not scanned: string annotations. This is the stated glued-string limit.
- Guard, patterns and names:
  - Exactly-one-line holds: the `\A(?!(W)(:|$))` lookahead excludes whatever the bare entry matches.
  - `name_parts` and `_CAMEL` give the documented results for GitHub, OpenAI, S3, AWSClient and AWSclient.
  - `vendor_words_in` digit stripping never strips a listed word (`s3`).
  - Counts: 33 words, nine two-part words ("PagerDuty, OpenAI and seven more" is right), 17 pinned table names.
- Sources adapter and exception entry:
  - The real Kubernetes kind has `build.__module__ == hadavin_sdk.sources.kinds`, whose docstring has "Neutral protocol:", so `neutral` is True.
  - The plant tests cover no-line, vendor settings and vendor build.
  - The registry import is inside a function.
- `tests/test_p7_tick.py`: the only changes are the import (line 18), the four renames (259-273) and the path at line 290. The assertions are unchanged and :537 is untouched.
- Contract test: `test_channel_names_its_callback_path` uses `getattr(channel_module, "valid_callback_path", None)` and asserts it is not None, so it fails cleanly on main.
- CHANGELOG: word counts, the 17 pinned names, and the four pre-existing receiver faults (all on main) are accurate. I found no `noqa`, `random` or `type: ignore` in the two new or edited test files.

EARLIER FINDINGS CONFIRMED CLOSED IN CODE
- Round 1:
  - The `gcs` prefix is not added to `_TABLE_VENDOR_NAME`. `GcsRetentionLockSettings` has exact name and literal entries, and the plant test at test_lockin_guard.py:1528 keeps its strings scanned.
  - Import module paths are scanned.
  - Snake-case two-part words are seen.
  - The boundary rule is a rule, not a list of characters.
  - One checker holds grammar and length.
  - Read-once at start is tested (:238).
  - Both `noqa: S311` suppressions are gone.
  - 404 probes send no body.
  - The near-miss list has percent-encoding, a doubled slash and the absolute form.
  - A completeness test exists for the removal tests (:2006).
  - The module key is by position.
  - The channel name is checked before it goes into the error text.
  - The registry import is lazy.
  - The sources adapter checks the build module too.
- Round 2:
  - An import alias no longer drops the original name (:1720-1727).
  - `|` is a boundary (:1381-1392).
  - A Content-Length of more than 12 digits gives 413 with no `int()` call, and the path is judged first.
  - The CHANGELOG names the signed `//` behaviour change.
  - The async-def difference is stated.
  - The [pinned] markers have tests.

NOT CHECKED
- No execution at all: no pytest, ruff, ruff format, bandit or `stage_mutants`. I could not confirm the green results, the guard hit lists, or the exact "places" counts in `_IDENTIFIER_OK_WORDS` (:1992-1999).
- The 500-answer-on-failure and 12-digit-guard hardening goes beyond the ticket's "asks for neither" receiver change. I judged it only on technical accuracy, not on scope.
- Main's guard test file is not in the export (src only). I could not diff it for weakened existing tests; the claim "56 tests unchanged" and the old `TABLE`-prefix skip behaviour are unverified.
- The merge with Q8a-1 was not checked.
- The `tests.test_http_metadata` word-list subset test: I confirmed its regex shape matches `VENDOR_WORDS` there (:114-116) by reading only, and the guard list is a superset.
- Slack's real retry behaviour for interactive callbacks (m4).
- Whether `sql_problems` plus the new word entry gives zero hits on the real migrations (evidence not available).

Files: /home/user/build/snap/q8a2-f6c2a3d/src/hadavin_sdk/approvals/receiver.py, /home/user/build/snap/q8a2-f6c2a3d/src/hadavin_sdk/approvals/channel.py, /home/user/build/snap/q8a2-f6c2a3d/tests/test_q8a2_callback.py, /home/user/build/snap/q8a2-f6c2a3d/tests/test_lockin_guard.py, /home/user/build/snap/q8a2-f6c2a3d/CHANGELOG.md.

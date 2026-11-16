<!-- full hand-back report of sub-agent acecc94a, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8a-2 fix batch 3: every item is fixed and the full suite is green. New head 3210f93acfcde2eb388a2b9b4f2fbdee641f5b04, pushed fast-forward (f6c2a3d9..3210f93a) to core/q8a-2-neutral-callback-and-guard. No PR, no merge.

**Slips and things to read first**
- Two process slips, both cleaned. I ran `pip download` in /home/user/hadavin-sdk and left 7 wheel files there; I removed exactly those. I also started my full suite twice through heavy.sh and killed the duplicate waiter, so only one run happened.
- The one-line ruff-driven edit on the new test failed on the first try (BLE001) and a vendor word-allowance test assertion was wrong; both were fixed before the commit.
- Bandit is not in the project venv (`uv run bandit` fails with "Failed to spawn"). I ran it from a throwaway venv in the scratchpad: `bandit -ll -r src tools` exit 0, "No issues identified".
- The new log tests (500 test, hang-up tests) pass on the OLD code, because the behaviour already existed; M1 was missing tests, not a code fault. I proved they bite with 8 mutants on handle_error, log_message and serve (see Fail-before). 20 of the new tests fail on the old code.
- I did not run the perf-marked tests (the suite excludes `live` and `perf`), the merge against the Q8a-1 branch, or CI, CodeQL, SonarCloud and CodeRabbit.
- Not verified: real Slack retry behaviour. I only reworded the claim to "a sender that retries on 5xx delivers it again".
- Machine was shared, so timings are not quiet-machine numbers.

**What changed** (files: src/hadavin_sdk/approvals/receiver.py, hmac_v0.py, src/hadavin_sdk/defaults.py, tests/test_q8a2_callback.py, tests/test_lockin_guard.py, CHANGELOG.md)
- **M1, handle_error tested with caplog** (logger hadavin_sdk.receiver at DEBUG).
  - The 500 test asserts exactly one ERROR line "a request ended with an error: RuntimeError" and that "store is down" is not in caplog.text. It waits on the record instead of sleeping and checking stderr.
  - A hang-up while the body is read is DEBUG only, with no ERROR.
  - A complete request followed by a reset, so the answer write fails, is DEBUG only (this covers the answer-write path).
  - Unit calls of handle_error cover BrokenPipe, ConnectionReset and ConnectionAborted alone (DEBUG), and ValueError (ERROR, no exc_info).
  - Decision: a reset after a handler failure stays ERROR and names both kinds ("ConnectionResetError while handling RuntimeError"). Pinned by a test and stated in the CHANGELOG.
- **log_message** builds `format % args`, cuts to 200 characters, replaces each non-printable with `?`, and logs with "%s". One shared helper `_plain` also serves `_shown_name`. Tested with `\r`, `\n`, `\x1b`, `\x85` and ` ` by a unit call, and end to end with an escape in the path over a real socket.
- **serve() validates read_timeout_s**: ConfigError unless the type is exactly int or float (bool refused), finite, > 0 and at most `defaults.RECEIVER_READ_TIMEOUT_MAX_S` = 3600.
  - I added the upper bound myself, because a socket timeout of 1e10 raises OverflowError on every request (measured).
  - 16 refuse cases and 7 accept cases are tested.
- **Shared digit guard**: `hmac_v0.MAX_HEADER_DIGITS` (12) and `hmac_v0.is_plain_digits`, used by `hmac_v0.verify` and `receiver.body_length`. A test pins that both use the same objects.
- **Docstrings and wording**:
  - serve has no connection limit and production hosting (S11) must limit them.
  - handle_action says "outcome is audited; tick updates the channel message".
  - "so the sender delivers it again" is now "a sender that retries on 5xx delivers it again", in receiver.py and the CHANGELOG.
  - Trailing space in Content-Length is documented as fail closed, 400. This is stricter than HTTP, and a test already covers it.
  - "Enable debug level on hadavin_sdk.receiver for detail" is in the serve docs and the CHANGELOG.
- **Tests**:
  - Timing ceilings raised to 4 s.
  - The generated-path coverage test is explicit over range(2, 65), no longer dependent on draw order.
  - Comments fixed: the "Arabic-Indic" comment, the reset-test docstring, and a note on the two fail-on-main hedges (`_served`, `_path_before_and_after`). I kept the hedges, each with a one-line note.
  - The guard module docstring, rule c, is updated.
  - New test refuses an empty-name WORD_IN_OK key: `literal_problems` now reports it as a problem line.
- **CHANGELOG**:
  - The path-serving bullet is split into "What changes for a deployment" and "What a custom channel author must do". It explains reverse proxy as a gateway in front of the receiver.
  - "[pinned]" is explained as "a test that fixes it" in the guard docstring.
  - The vendor word list is stated as open-ended, with named examples.
  - The four unscanned plants (`# slack`, a docstring naming Slack, `-- slack`, `/* slack */`) are stated as a design decision, not a gap. A vendor word in a comment, docstring or SQL comment cannot change behaviour. Pinned by existing tests; approvals/receiver.py stays checked as whole text.
  - The same text is appended to /home/user/build/B-Q8a2-pr-notes.md.

**Evidence** (raw files in /home/user/build/q8a2-fb3/)
- **Targeted run**: tests/test_q8a2_callback.py + tests/test_lockin_guard.py + tests/test_p7_tick.py + tests/contracts gave 564 passed, 31 skipped. The callback file alone ran 3 times, 106 passed each time.
- **Fail-before**: the new test files over f6c2a3d9's src gave exit 1, 20 failed, 312 passed (fail-before.log). Failures: log_message cut and cleanup, 16 read_timeout_s refuse cases, plus the shared-digit-check test.
- **Mutants on handle_error, log_message and serve** (mut.py): hung_up never, hang-up check without `len(kinds)==1`, adding `str(exc)` to the line, ERROR changed to DEBUG, raw log text, no cut, bool accepted, no max bound. All 8 killed.
- **stage_mutants**: `37 of 37 good; problems: []`, exit 0 (g-mutants.txt).
- **Full suite**: one run through heavy.sh on head 3210f93a, with my own Postgres 16 on port 56082 started with PGHOST and PGPORT in the server's environment. Result: exit 0, `10830 passed, 1 skipped in 354.65s` (full-pytest.log, .rc, .head). Excluded marks: live, perf.
- **Gates**:
  - ruff check exit 0
  - ruff format --check exit 0, "323 files already formatted"
  - bandit exit 0
  - tools/scan_repo.py exit 0, no output
  - gitleaks on f6c2a3d9..HEAD and origin/main..HEAD: no leaks, exit 0
  - 0 added noqa, nosec or type: ignore in the diff
- **Hygiene**: Postgres 56082 stopped and its data dir deleted. The temporary worktree is removed. No processes of mine remain, and I stopped no process I did not start. Checkpoint notes are in /home/user/build/B-Q8a2-checkpoint.md.

**Rules cited**: fix-dont-defer-be-honest, class-level-fixes, no-single-dependency, least-privilege-hard-rule, verify-tests-and-evals, wording-clear-for-everyone, long-jobs-run-detached.

<!-- full hand-back report of sub-agent a6c1cd5e, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 19, PR 89, head b95b0ca7. Mode: REVIEW. Verdict: NOT READY (1 Blocker gate, 4 Major, 13 Minor).

All findings are by reading only; I ran nothing. Line numbers are in `/home/user/build/snap/p89-b95b0ca/tools/mutation_runner.py` unless another file is named.

## What failed or is unproven, first

- **No evidence exists for this head.** `/home/user/hadavin-sdk/handover/evidence/PR89/` holds only `b7a6b07888771e76aa38e023ac112be81717e4a4/` and `db0d9eb/`. There is no `b95b0ca/RESULTS.md`, so every "passes", "fails on the old runner" and "162 mutants good" is unproven.
- **The projection is not what the docs say it is.** It still shows child-chosen text in two slots, and the fuzz test does not check the encoded forms it lists.
- **The address check accepts by pattern** (any unix socket folder, or no host at all), and the caller cannot narrow that away.
- **The test-only switch certifies a behaviour production now refuses** (a passed name set to empty text).

## Blocker

**B1 (gate). No evidence run at b95b0ca.**
- Scope: whole pull request.
- Unproven: full suite, ruff, bandit, the 162 keyword mutants, the 7 new mutants (`tests/mutation_runner_mutants.py:496-502`), the new tests against the old runner, the sha256 pins.
- Fix: an EVIDENCE RUNNER on b95b0ca before the next result review. It should run the full suite, `python tests/mutation_runner_mutants.py`, and the round-18 tests against db0d9eb's runner with the reason for each failure recorded (see M1c).

## Major

**M1. The "class name" slot and the test-id slot are free child text; only plain 4-character pieces of the value are denied.**
- Where: `_shown_line` 736-755, `_shown_id` 758-766, `_baseline_failure` 1222-1224.
- (a) Wrong outcome, encoded forms:
  - The secret is the URL password `Zq9xK4mTw`. A test, or a mutant's code, raises `type("wTm4Kx9qZ", (Exception,), {})("x")`.
  - `first_lines` and the baseline failure message then show `wTm4Kx9qZ`, the password reversed. No 4-character piece matches, so nothing hides it.
  - The same holds for a base64 copy that starts with a letter or `_`, rot13, or any identifier-shaped encoding.
  - Hex is hidden only by luck: the hex of printable ASCII starts with a digit, so it is not an identifier. `"x" + hex` is shown.
  - A file path or function name in the JUnit `classname` / `name` behaves the same way (a conftest hook can set them).
- (b) Wrong outcome, slices: any slice of 3 characters or fewer is shown by design. A child can emit the secret three characters per row across mutants; a 5-character password loses 60% in one class name.
- (c) The fuzz test does not prove what the CHANGELOG implies.
  - `tests/test_mutation_runner_keywords.py:3195-3239` builds base64, hex and reversed child text, but asserts only that no plain 4-character piece of the value is in the output.
  - Inside that test, a base64 copy of a secret piece that begins with a letter is itself shown as the class name, and the test passes.
  - "It fails on the old runner" is true for the wrong reason: the test calls `mr._baseline_failure`, `mr._shown_line` and `mr._shown_id`, which the old runner does not have, so it fails with `AttributeError` before any assertion.
- (d) Claims that exceed the code:
  - Docstring 77-78 and the CHANGELOG "what is shown" bullet say "The child's text is not shown at all ... because a list of the forms of a secret ... can never be complete".
  - The class slot is exactly such a denylist: an identifier minus plain 4-character pieces.
- Realism: an honest test puts a real exception class first, so this needs a hostile or exotic child. This is the redaction path and the stated design principle is "no denylist", so I rate it Major.
- Proposed fix (also removes M2):
  - Class slot: show a name only when it is on an allowlist. That is the exception names in `builtins`, plus the `crash_type` values of the mutants in this call, plus an optional caller keyword such as `shown_classes=(...)`. Otherwise `CLASS_HIDDEN`.
  - Test id: show the file part only when it equals one of the caller's `tests` entries (print the caller's string, not the child's). Show the function name only when `def <name>` is literally in the snapshot copy of that file, or it equals `m.only_test` or the function part of `m.pinned`. Otherwise `ID_HIDDEN`.
  - Drop `_shows_a_piece` and `PROJECTION_MIN`.
  - Make the fuzz assert that every shown class is on the allowlist and that every shown id is caller text.
  - Prove failure on the old code by a leak assertion, not a missing attribute.

**M2. The 4-character rule shreds legitimate ids for the CI address, which holds no secret.**
- Where: `_shown_id` 766, `_refuse_skips_in_baseline` 1208, `_row` 1262.
- Input: `postgresql://postgres@localhost:5432/postgres`. Its pieces include `post`, `ostg`, `gres`, `esql`, `sql:`, `loca`, `ocal`, `host`, `ost:`, `5432`, `/pos`.
- Because an id is `tests/<file>::<function>`, the pieces `sql:` and `ost:` match across the `::`.
- Ids that become `[test id not shown]` as a whole:
  - `tests/test_postgres_store::test_x`
  - `tests/test_store_sql::test_x` (`sql:`)
  - `tests/test_host::...`, `tests/test_cost::...` (`ost:`)
  - any function with `progress` or `regression` (`gres`), `allocation` or `local` (`loca`), `post` or `host`
  - anything under `tests/pos.../`
- Class names hidden: `PostgresError`, `PostgresSyntaxError`, `LocalProtocolError`, `UnknownHostError`.
- What a developer still sees: the mutant name, the verdict, the good flag, a safe class name, `[expect found]` or `[expect not found]`, and their own `expect`.
- What is lost:
  - The actual failure line. A WRONG_REASON row cannot be diagnosed from the output.
  - For Postgres-named test files, which test failed on an OTHER_TEST row.
  - Which tests skipped. With `forbid_skips` now implied, a developer whose database is down gets `the unmutated copy skipped 3 selected test(s): ['[test id not shown]', ...]`.
- Verdicts stay correct, because `judge`, `pinned` and `crash_type` read the raw text.
- Fix: the M1 allowlist (ids from the caller's own `tests` list and snapshot source are caller text, shown as given like `expect`). Until then the CHANGELOG cost line understates this: it names only `test_postgres_...`.

**M3. Least privilege: socket folders and "no host" are accepted by pattern and cannot be excluded.**
- Where: `_SOCKET_DIR` 498, `_address_fields` 530-537, `_refuse_unsafe_address` 572, `_checked_throwaway_hosts` 548.
- Input and wrong outcome:
  - `throwaway_hosts=("db",)` with `HADAVIN_TEST_PG_DSN="dbname=prod"` is accepted.
  - So is `host=/var/run/postgresql dbname=prod` and `host=/var/run/pgbouncer dbname=app`.
  - With no host, libpq uses the machine's default cluster, and the OS user logs in by peer authentication. On a database host that user is often the superuser. Every mutant's tests then write there.
- The docs say "There is no pattern and no override keyword" (docstring 70, CHANGELOG step 3). `/[A-Za-z0-9_./-]*` is a pattern.
- The test at `tests/test_mutation_runner_keywords.py:3380-3394` says "the default is replaced, not widened" but never checks that a socket or a host-less address is refused once the list is narrowed.
- Fix:
  - A socket folder must be an exact member of `throwaway_hosts` (allow absolute paths in `_checked_throwaway_hosts`).
  - Refuse a key=value address with neither `host` nor `hostaddr`, or require an explicit named member for "default socket".
  - Decide whether the default list holds a socket folder at all (CI does not need one).
  - Add negative tests: narrowed list refuses a socket; narrowed list refuses no host.

**M4. The test-only switch is fail-open and certifies behaviour that production refuses.**
- Where: `tests/test_mutation_runner_keywords.py:83-96`.
- Reachable in production: no. The runner has no keyword, environment variable or flag for it; it is a monkeypatch of a module attribute. Confirmed by reading `_run_mutants` 1300-1332.
- Does it hide regressions: yes.
  - The check is off for every test whose name does not start with one of three prefixes. A new address test with another name silently runs unchecked.
  - `test_no_name_that_is_not_set_is_checked` (3473) runs with the check replaced, despite its name.
  - `test_a_passed_name_set_to_an_empty_text_still_gets_the_canary` (908) and its mutant (`tests/mutation_runner_mutants.py:375`) pass only because the check is off. In production `_address_fields("")` returns `None` (518-525) and line 1319 raises "not in a shape"; the suite's own refused list includes `""` (3340).
  - The CHANGELOG still says the canary "runs whenever a passed name is set, also when its value is empty text", and the comment at 1326 says the same. That cannot happen through `run_mutants`.
  - Most end-to-end tests of the hiding use `db.invalid`, key=value password words, a sentinel or a file path as the value. Production refuses all of these before anything runs. Under real settings, the pipeline check, then lock, then projection is run by only a handful of tests.
- Fix:
  - Invert the switch: an explicit marker or fixture on the tests that need a fake address, not a name-prefix exemption.
  - Better: pass `throwaway_hosts=("db.invalid",)` through `_run` and use addresses the grammar accepts.
  - Delete or rewrite tests of inputs that are now refused.
  - Decide the empty-value behaviour, then make docs, test and mutant agree.

## Minor

**m1. Lock folder: the "cannot plant" claim is wider than the code.**
- Where: `_lock_dir` 793-819; docstring 109-111; CHANGELOG lock bullet.
- Another user of a sticky `/tmp` can pre-create `hadavin_mutation_locks_<victim uid>` (the name is predictable). The victim then gets `RuntimeError` on every run until they set `TMPDIR`. The denial of service moved from file to folder.
- The design is otherwise sound: `mkdir` 0700, `lstat`, owner, no group or other bits, link refused.
- Residual: between the `lstat` and the `os.open` at 887 the path is used by name. That is safe only when the temp folder is sticky.
- Fix: say that a planted folder is refused, not prevented. Or prefer `XDG_RUNTIME_DIR` or a folder under the user's home, with the temp folder as fallback. Open the folder with `O_DIRECTORY|O_NOFOLLOW`, `fstat` it, and create the lock with `dir_fd`.
- No test takes a real lock inside the real folder: the autouse `_own_lock_folder` replaces `_lock_dir` everywhere, and the four real-folder tests only call `_lock_dir()`.
- The Windows claim "private to the account" is unverified; it is false when `TEMP` is a shared folder.

**m2. Lock name for socket addresses ignores port and database.**
- Where: `_address_parts` 492 calls `_address_fields(value)` without `sockets=True`.
- `host=/var/run/postgresql dbname=a` and `... dbname=b` both hash as `unparsed`. The second run is refused as "the same passed database address", which is a wrong message and an over-refusal.
- This is now the only reachable `unparsed` case. The other cases in docstrings 113, 487-491, 870-871 and in the CHANGELOG lock bullet are refused earlier by the address check.
- Fix: `sockets=True` in `_address_parts`; correct the texts.

**m3. `forbid_skips`: one word, two meanings.**
- Where: 1320-1323.
- The code switches it on when a name is listed (`bool(env_names)`). The docs say "Setting a passed name" (60) and "on when a `pass_env` name is set" (CHANGELOG). The canary uses "present in the environment" (1324).
- Callers broken: none found. `/home/user/hadavin-sdk` outside `tests/` and `handover/` has no `pass_env` or `run_mutants(` caller in the checkout I could read. The snapshot's 40 `pass_env=` uses are all in the keyword test file; whether they pass is unproven (B1).
- Behaviour change to state plainly: a caller who lists the name unconditionally, with tests that skip when the variable is unset or with any platform `skipif` or `xfail` in the file, now gets a baseline `RuntimeError`. The only way out is `forbid_skips=False`, which removes the protection for the whole run.

**m4. Two `# type: ignore` remain; both are removable.**
- Where: 967 and 1103. Rule: no suppressions.
- 967: pass `creationflags=` and `start_new_session=` as explicit keywords chosen by `_IS_WINDOWS` instead of `**own`.
- 1103: type `previous` with the handler type that `signal.signal` returns instead of `object`.
- The builder's deviation is not justified by need.

**m5. Mutant gaps on the new security code.**
- Where: `tests/mutation_runner_mutants.py:496-502`.
- No mutant for:
  - the call at 1317-1319
  - `key not in keys` and `key in found` (527)
  - the `..` socket check (534)
  - `.strip("[]").lower()` (571)
  - `_shows_a_piece` inside `_shown_id` (766)
  - the `any(secrets)` branch of `_baseline_failure` (1222)
  - the owner and is-a-folder checks of `_lock_dir` (812-813)
- No negative tests for trailing dot (`localhost.`), decimal, hex or short IPv4 (`2130706433`, `0x7f.1`, `127.1`), `[::ffff:127.0.0.1]`, `passfile=`, `sslkey=`, `target_session_attrs=`.
- By reading, exact membership refuses all of them. A property test "any host not in the tuple is refused" would pin that.

**m6. "No repeated key" is true only for four keys.**
- Where: 527. `found` stores only `host`, `hostaddr`, `port`, `dbname`.
- `user=a user=b` and `sslrootcert=x sslrootcert=y` are accepted. Harmless for routing, but the claim (docstring 68, error text 567, CHANGELOG step 2) is wider than the code.
- Fix: track every key seen.

**m7. Allowlisted keys carry no written reason per key.**
- Where: `ADDRESS_KEYS_ALLOWED` 501-503. Rule: least-privilege point 5.
- `sslrootcert` (any path, `..` allowed) and `application_name` are not needed for a loopback or socket throwaway database, nor for CI.
- Fix: remove them until a caller needs them, or add one line of reason per key and a negative test per refused sibling.

**m8. No guard test that libpq's own variables stay out of the child.**
- By reading, the child environment is built from `CHILD_ENV` only (936-941). `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGSERVICE`, `PGSERVICEFILE`, `PGPASSFILE`, `PGOPTIONS`, `PGDATABASE` are not inherited, so they cannot redirect the checked address.
- No test pins this. Fix: assert that no `CHILD_ENV` name starts with `PG`.
- Stated limit, not a redirect: `HOME` is inherited, so `~/.pgpass` and `~/.postgresql/` client certificates are used by the child. Docstring line 3 ("no other DSN, token or secret of the caller") is true for environment variables only.

**m9. The "in order" list is not the code order.**
- Docstring 62-75 and CHANGELOG steps 1-5 put the 300-text count fourth. The code does it inside `_secret_values` (1316), before the grammar and host checks (1319).

**m10. Stale or missing wording.**
- The comment at 1317 says "a local, marked throwaway database"; there is no marker.
- The `run_mutants` docstring (1123-1134) does not name `throwaway_hosts` or the address `ValueError`, and still says `first_lines` is "masked".
- The module docstring at 126 still says `COLLECTION ERROR` comes "with pytest's message" (round-18 readiness item 5).

**m11. `throwaway_hosts` is validated only when the variable is set and the grammar passed.**
- Where: 569. A bad list such as `("*",)` is silent on a machine without the variable.
- Fix: validate at the top of `_run_mutants`.

**m12. Unreachable code and tests.**
- The key=value password-word path, `PASSWORD_PIECE_MIN`, and the every-`@` logic of `_url_passwords` cannot be reached through `run_mutants` with a set value. The address check refuses those shapes first.
- Consequence to state: a key=value address with a password, or a URL password holding `@ / ? #`, can no longer be used at all. The plan's D-002 logged "refuse any password-bearing address" as rejected and needing the owner; half of it has shipped through "fail closed on unparsed".
- Next step: an owner decision. Either accept this and delete the dead paths and their tests, or let the grammar read a password word.

**m13. Commits not split (builder's deviation from plan item 4 / P7).**
- I cannot verify this from the snapshot, which holds one diff.
- Consequence if true: the security change cannot be reverted or bisected apart from the minor fixes. Not blocking on its own.

## Answers to the brief, where not covered above

- **`expect` echo.** It can equal part of the secret: the test at keywords 469 uses `expect="postgresql"` and it is shown. That is the caller's own text and is documented as not covered. A whole secret used as `expect` is still masked by `_masked`. `[expect found]` is a yes/no probe of the child line for the caller, who already knows the value. No finding.
- **Short secrets.**
  - A secret under 4 characters gives no pieces. Only the exact-match masker covers it, which is sound for whole occurrences.
  - A 1 or 2 character password garbles the fixed words too (`Ass[REDACTED]rtionError`); this is documented.
- **Other output paths I found clean.** `SETUP FAILED`, `JUNIT REFUSED`, `JUNIT MISSING`, `TIMEOUT`, `EXIT CODE n`, the canary reasons (1470-1476), `CanaryFailed.rows` (already-projected rows), the lock messages, the refusal messages (never the value), and child stdout and stderr (sent to DEVNULL).
- **Grammar bypasses.** By reading, all of these are refused, by exact membership or by the fullmatch grammar: host case (lowered first), trailing dot, IPv4-mapped, numeric IPv4 forms, several hosts, percent-encoding in host or database name, any query, `service`, `passfile`, `options`.
- **Refusal before side effects.** Refusals come before the lock folder, the lock and any temp folder (1306-1319 against 1374-1379). The only earlier effects are `first_lines.clear()` and the signal handlers, which are restored.

## Round-18 findings: resolved, partly, or not (by reading; all "resolved" still need B1)

| Source | Id | Status | Note |
|---|---|---|---|
| codebase | m1 `judge_report` and contract text | resolved | |
| codebase | m2 `OSError` in `_row` | resolved | `_UNUSABLE_JUNIT`, test at 2947 |
| codebase | m3 labels, empty `first_lines` entries | resolved | |
| codebase | m4 baseline message | resolved | class only, per P7 |
| codebase | n5 stray "(canary)" | resolved | not found in head |
| design | M1 mutants never executed | not resolved | no evidence at this head |
| design | M2 denylist | partly | see M1, M2 above |
| design | M3 throwaway check | partly | see M3 above |
| design | M4 regressions, full suite | not proven | no evidence at this head |
| design | m5 ladder line | resolved | |
| design | m6 wording, weak assertion | partly | bullets split; assertion not checked |
| design | m7 lock folder | partly | see m1 above |
| design | m8 wall-clock bounds, `__wrapped__` | not checked | `__wrapped__` not found by search; bounds not read |
| design | m9 canary opt-out, implied `forbid_skips` | partly | `forbid_skips` done; no canary opt-out, no stated reason |
| readiness | 1 CI address | resolved | test reads `ci.yml`, skips if absent |
| readiness | 2 `type: ignore` | partly | two remain (m4) |
| readiness | 3 literal password URL | resolved | built from parts; `12/45` remains only in a docstring at 384 |
| readiness | 4 duplicate-name guard | resolved | `tests/test_mutation_runner_meta.py:111` |
| readiness | 5 wording | partly | see m10 |
| readiness | 6 one giant bullet | resolved | split; still dense |
| readiness | 7 Windows note | resolved | |
| zoom-out | P1 no name marker | resolved | |
| zoom-out | P2 exact allowlist | resolved | apart from sockets, M3 |
| zoom-out | P3 strict grammar, fail closed | resolved | m6 nit |
| zoom-out | P4 projection | partly | M1 |
| zoom-out | P5 shredding | n/a as written | 4-character form remains, M2 |
| zoom-out | P6 evidence first | not resolved | |
| zoom-out | P7 baseline class only; split batch | partly | baseline part resolved; split not done |
| zoom-out | P8 ladder, no reuse of core redactor | resolved | |

## What I did not check

- Any run: tests, lint, bandit, mutants.
- The sha256 pins: I had no way to hash.
- Most of the 3,495-line keyword test file. I read lines 1-130, 425-484, 904-929 and 2900-3495; the rest only by search.
- `tests/test_mutation_runner.py` and `tests/conftest.py`.
- `DIFF-vs-main.patch` beyond its file list, and `DIFF-r18.patch` beyond line 203. I read the head files instead.
- `.github/workflows/ci.yml` itself.
- Windows and macOS behaviour.
- libpq and driver parsing: stated from knowledge, not tested.
- Whether the commits were split.

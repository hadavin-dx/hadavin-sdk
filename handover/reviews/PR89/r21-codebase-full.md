<!-- full hand-back report of sub-agent abd93594, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 21, pull request 89, head 7a2eb4cc. Read-only, by reading only; nothing was run.

# Verdict: NOT CLEAN

Blocker 0, Major 1, Minor 12.

Gate, not counted: `/home/user/hadavin-sdk/handover/evidence/PR89/7a2eb4c/RESULTS.md` does not exist (the folder holds only `b7a6b078...`, `db0d9eb` and `b95b0ca`). Every run-dependent claim for this head is unproven. If your gate needs evidence per head, as round 19 B1 did, that is a Blocker.

Files (all under `/home/user/build/snap/p89-7a2eb4c/`):
- MR = `tools/mutation_runner.py`
- MU = `src/hadavin_sdk/testing/mutation.py`
- KW = `tests/test_mutation_runner_keywords.py`
- MM = `tests/mutation_runner_mutants.py`
- META = `tests/test_mutation_runner_meta.py`
- CL = `CHANGELOG.md`

Names in the brief that no longer exist at this head: `_pieces`, `_shows_a_piece`, `PROJECTION_MIN`. They were removed with the 4-character rule. `_canary_refusal` and `_masked` remain.

## Major

**M1. The second layer splices `[REDACTED]` into text the reader already knows, so the mask position gives the password away.** MR:897, MR:924, `_masked` at MR:769-805.

- After the allowlist, the whole shown text goes through `_masked`. That text is a Python class name, the runner's fixed words, the caller's file and function names, and `expect`.
- The child's text is already gone at that point. Any hit is therefore in text the reader has: Python's exception names, the repository's file names, the runner's own words.
- Input 1: `HADAVIN_TEST_PG_DSN=postgresql://postgres:postgres@localhost:5432/postgres`, tests `["tests/test_postgres_store.py"]`. The password `postgres` is a secret via `_url_passwords` (MR:460-467).
  - Expected: `tests/test_postgres_store::test_x`.
  - Actual by reading: `tests/test_[REDACTED]_store::test_x`. A reader with the repository reads the password off the file name.
- Input 2: password `Error`. `_shown_line("E   KeyError: x", shown)` gives `Key[REDACTED]`.
- Input 3: password `test`. Every row id becomes `[REDACTED]s/[REDACTED]_core::[REDACTED]_a`.
- Input 4: password `class`. The runner's own replacement text becomes `[[REDACTED] not shown]`.
- Without the second layer none of these outputs would say anything about the password.
- Condition: the password, or one of its decoded or encoded forms, must be a substring of caller, Python or runner text. That means a weak password, but `postgres` and `test` are the usual ones on a throwaway database.
- Same symptom class as round 19 M2/M3 (ordinary ids shredded). KW:3394 pins only the passwordless CI address.
- Only the garbling by a 1 or 2 character secret is stated, and only in the `_masked` docstring.
- Smallest fix at the choke point (MR:897, MR:924):
  - never run `_masked` over Python names or the runner's fixed words;
  - for a caller-owned field (id, class from `shown_classes`, `expect`), if any secret occurs in it, replace the WHOLE field with the fixed text (`ID_HIDDEN`, `CLASS_HIDDEN`, a fixed word for `expect`).
- Siblings: MR:1421 and MR:1494, both through `_shown_id`.
- Add a test with `postgres:postgres` and one with a password equal to a function name. KW:3464-3475 asserts only `_PW not in ...`, which the splice satisfies.

## Minor

**m1. One raised error keeps a child-text exception in `__context__`.** MR:1415-1418.
- `raise RuntimeError(...) from None` inside the `except` hides the context from display but leaves `__context__` set.
- `UnicodeDecodeError`: its args, and so its `repr`, hold the whole bytes of the JUnit file.
- `ET.ParseError`: its message can hold up to 100 bytes of file text (`undefined entity &...;`).
- Sequence: a baseline or canary test writes a `base.xml` or `again.xml` with a bad byte; the caller logs `repr(exc.__context__)`.
- An honest pytest writes neither; only a hostile or broken test does.
- Fix: take `type(exc).__name__` in the `except` and raise after it, as `_baseline_failure` (MR:1430-1434) already does.
- Siblings checked clean: MR:1432, MR:1477, MR:1449 (uses `str(exc)` only, raised outside the `except`).
- MR:994, 1101, 1113, 1116 and 1689 hold `OSError` contexts with paths only.

**m2. Fail-open default on the choke point.** MR:1410, MR:1425, `_Shown` at MR:831.
- `shown: _Shown | None = None`, then `shown or _Shown()`, means "replace nothing".
- A future call site that forgets the argument shows child text. The mutant at DIFF-r20:281 is exactly that edit.
- Fix: make `shown` required at both sites; tests pass `mr._Shown()` explicitly.

**m3. Unstated limit: tracebacks hold the address.**
- Every exception leaving `_run_mutants` carries frames whose locals are `environ`, `secrets` and `value` (MR:649, MR:1550-1551).
- A printer of locals (pytest `--showlocals`, rich, an error tracker) prints the address with its password.
- MR:137 and CL:57 say "every text the runner returns or raises".
- Fix: state the limit.

**m4. `HOME` gives the child more than `~/.pgpass`.** MR:310-313, MR:1137-1141.
- Exact code: `env = {k: source[k] for k in CHILD_ENV if k in source}`, plus the checked `pass_env` names, plus `PYTHONNOUSERSITE=1`, plus `PYTHONPATH` set by the runner.
- No `PG*`, proxy or cloud variable passes.
- `HOME` and `USERPROFILE` do pass. So `~/.aws/credentials`, `~/.netrc`, `~/.config/gcloud` and `~/.postgresql/` (client certificate and key, `root.crt`) are reachable.
- MR:6-7 says "no other database address, token or secret of the caller", unqualified. MR:118-120 and CL:45 name only `~/.pgpass`.
- Fix: qualify the sentence.

**m5. The runner folds case where the database library does not.** MR:544 (`(?i:postgres(?:ql)?)`), MR:603 (`key.lower()`).
- From my knowledge of libpq, not checked here: it compares the scheme and the keys with exact case.
- `POSTGRESQL://u@localhost/db` and `HOST=localhost dbname=x` pass the check and take the lock, then fail at connect, so the baseline fails or skips.
- I found no input that reaches an unlisted host this way: no white space is allowed in a URL, and repeats are compared after folding.
- The docstring at MR:585 says `postgres://` or `postgresql://`.
- Fix: drop `(?i:` and `.lower()` on the key.

**m6. Lock folder residue.** MR:955-1011.
- The parent folder is never checked for owner or sticky bit. In a shared temp folder without the sticky bit another user can rename the folder away, and the next runner makes a new one, so the lock is missed. Unstated.
- `_own_private_dir` checks `XDG_RUNTIME_DIR` with `lstat`; the folder is then used by path (check, then use). `O_NOFOLLOW` covers only the last path part.
- An `OSError` from `os.fstat` at MR:997 leaks `fd` and is not the documented `RuntimeError`.
- A signal between MR:1088 and MR:1089 leaks the folder descriptor.
- Found correct: `O_DIRECTORY|O_NOFOLLOW`; uid; mode `& 0o077`; `dir_fd` on the only later open; close in `finally`; refusal also for root.
- Unreachable on Linux and so untested: MR:347-348, MR:1014-1020 (`msvcrt` lock), and the real Windows path of MR:1092 and MR:1096.

**m7. Tests that cannot fail, or branches never proven.**
- KW:3875-3881: the loop uses `pytest.raises(ValueError)` without `match`. All three values raise a `ValueError` even if the host-list validation is removed ("host is not one of", or "names no host"). Only KW:3882 tests the rule.
- KW:3820: the sibling `options=-cport=1` is refused by the token shape (`=` is not in `_PAIR`), not by the key allowlist.
- KW:3726-3737: the fuzz control proves only the "line" and "id" branches of `_check_one_output`. The "failure", "skip" and "canary" branches (KW:3669-3682) are never shown able to fail.
- MR:1432: no test and no mutant for a failed baseline with an unusable JUnit file.
- MR:975-977: the `XDG_RUNTIME_DIR` choice has no mutant, and the link case of `_own_private_dir` has no test (KW:3309-3328 covers private, open, relative and other user).

**m8. The order test pins 9 of the 13 documented steps.** KW:4400-4410.
- Missing: step 1 (paths), step 5 (`conftest`), step 8 (over 300 texts), step 12 (`test_file`).
- CL:78 says "Others pin the order of the refusals".

**m9. A mutants header sentence is wrong.** MM:52-54: "the table rows with password keys stay and are killed through the mutant of the key allowlist".
- That mutant's killer is `test_every_allowed_key_has_a_reason_and_a_refused_sibling`, run alone (`only_test`, MM:101-104).
- `_REFUSED_SIBLING` (KW:3817-3825) holds no password key.
- The password row (KW:3809) lives in a test that no mutant of the key rule runs.
- Fix: add a password key to the sibling table, or correct the sentence.

**m10. Wrong or unprovable statements in CHANGELOG and docstrings.**
- MR:82-83: "Each is a `ValueError` ... A message names the variable and the reason". A bare string gives a `TypeError` (MR:407, 634, 840). Steps 1 to 5, 12 and 13 name no variable.
- CL:32: "Each refusal is an error that names the variable". The lock message (MR:1114) names none.
- MR:142 and CL:60: `expect` is printed "as given". It goes through `_masked` (MR:897); KW:3473 proves the opposite for a whole secret.
- CL:36 "Changed in this round ... no longer accepted"; CL:47 "the earlier rule ... is gone"; CL:62 "an older copy of this tool"; CL:65 "(before, every socket address shared one name)"; CL:79 "in this round". These describe states between review rounds that `main` never had (`pass_env` and the lock are new against `main`). They also use process words in a release note.
- CL:78 "300 seeded random hosts": a set of 300 draws; the test itself asserts only 290 or more (KW:4078).
- CL:78 "on the previous version of the runner that test fails" and KW:3531-3532: run-dependent, unproven.
- CL:38 and MR:102 "exact member": names are folded to lower case first (MR:614, MR:640).
- MR:985: "`RuntimeError` when the folder cannot be made or opened" does not hold for an `fstat` error.

**m11. A made-up password stands as one literal.** KW:3068 and KW:3083 write `"Zq9xK4mTw"` whole. The file's own rule (KW:156-158) is "in parts".

**m12. Unreachable from `run_mutants`.**
- The `"unparsed"` lock name (MR:624-625): the address check refuses first.
- The password-word reading in `_password_texts` (MR:415, MR:482-500). It is kept on purpose and the docstring says so.
- Round 19 design m12 is therefore only partly closed.

## Checked and found correct, by reading

**Allowlist (brief item 1).**
- `_shown_class` (MR:878-881): exact, case-sensitive membership of the parsed leading name.
- `_IDENTIFIER` is used with `fullmatch` on `shown_classes`.
- `_shown_id` (MR:900-925) rebuilds the id from the caller's `tests` text plus names equal to a `def` or `class` name of the snapshot file or to the mutant's own names. The bracket part is always replaced.
- An empty allowlist hides everything.
- A listed class that holds only a piece of the secret is shown as the caller wrote it. The whole secret inside one is M1.
- Derived forms (reversed, case-changed, base64, percent) never match the allowlist.
- No `print` or log call exists in MR.

**Call sites traced.**
- `_row` (MR:1469-1515): timeout, reaped, unusable JUnit including `OSError`, JUnit missing, collection, fixture, skipped, judged row.
- `_baseline_failure`, `_refuse_skips_in_baseline`, `_canary_refusal`, `SETUP FAILED`, the lock messages.
- `judge_report` returns a verdict only.
- No raw child text reaches a row, `first_lines`, `on_result`, `CanaryFailed.rows` or a message, apart from m1.

**Grammar (brief item 2).**
- Both shapes are matched whole (`fullmatch`).
- Refused: an empty value, an empty token, quotes and backslashes (earlier, by `_refuse_odd`), repeated keys (after folding), several hosts, a query, percent codes in host or database name, a database name that is itself an address, `host=[::1]`, a URL IPv6 host without brackets, `host=@name`, a `..` socket part.
- A socket folder is compared as written: no normalising, a trailing slash is refused, links are not resolved.
- `throwaway_hosts` is checked on every call (MR:1542). Bytes, an int, `""`, `*` and brackets give `ValueError`; a bare string gives `TypeError`; `None` gives a raw `TypeError`.
- `%40`: the password is searched as written, decoded to a fixed point, and re-encoded in three forms with upper and lower hex.
- Lock name: the four fields cannot hold a newline or NUL, so two different field sets cannot share a text. One address gives one name. The name holds no password or host text, only 16 hex digits of a hash, inside a 0700 folder.

**The removed password-word check: every input it refused is still refused.**
- Old code (DIFF-r20:2723): `_PASSWORD_KEY.search(pair.group(1))`, on the key of a key=value word only.
- New code (MR:603-605): the lower-cased key must be one of `host`, `hostaddr`, `port`, `dbname`, `user`, `sslmode`, `connect_timeout`.
- None of the seven holds `password`, `passwd` or `pwd`.
- Result: `ValueError` from the check, `"unparsed"` for the lock name.
- The four removed mutants leave no rule without a test, but see m9.

**Tests (brief item 5).**
- `_must_raise` (KW:109-118) is right now: the `else` raises outside the `try`, and the message is asserted after it. With the default `match=""` the message is not checked.
- The two "ends quietly" tests (KW:920-936, KW:4167-4196) do fail when the refusal is missing: `_must_raise` raises "nothing was raised". `forbid_skips=False` only keeps a different error from coming first.
- Fuzz: fixed seeds (`_Det`, 60), 8 forms, 13 outputs asserted per iteration. Every field is checked by membership in a set built from the caller's side.
- Wall-clock bounds: KW:727 (30 s); KW:2179, 2908, 2928, 2938 (60 s).
- `conftest.py`: an autouse, function-scope fixture for the whole suite. It only fails a test that writes the variable directly. It is unchanged this round.
- Pins: the values in CL:465-468 and the manifest are identical. The hashes themselves were not recomputed.

**Mutants (brief item 6).** For each of the 38 below, `old` occurs exactly once in the head file, and the killer exists (a count of 36 killer definitions was confirmed by search).
- Re-pointed:
  - b2 refused junit
  - names not checked before start
  - baseline that skips
  - baseline skip message
  - FIXTURE ERROR keeps no message
  - SKIPPED TESTS message
  - first_lines shows value
  - row id shows value
  - database check ignored
  - canary skip accepted
  - baseline without usable JUnit
  - ERROR row names none
  - bare string
  - lock file cannot be opened
  - lock file open to others
  - canary skip message
  - database of a URL
  - values that are no address
  - URL host case
  - key=value host shape
  - hostaddr shape
  - lock folder others can enter
- Added:
  - empty text not checked
  - class not on allowlist
  - parameters shown
  - file part not the caller's
  - function not in snapshot
  - test class not in snapshot
  - crash_type not on allowlist
  - shown_classes not on allowlist
  - class not masked
  - id not masked
  - baseline failure shows child line
  - shown_classes not checked
  - address check not called
  - host list checked only with a variable
  - socket dot-dot
  - key not on allowlist
  - key twice
  - socket unlisted
  - no host
  - host keeps case
  - socket lower case
  - listed host keeps case
  - absent variable and skip check
  - judge_report
  - exit code label
  - unreadable JUnit (`PermissionError`)
  - lock folder of another user
  - not a folder
  - folder flags
  - opened by path
  - folder descriptor leaks
- Counts: META pins 248 (224 + 28 - 4), MU 13, conftest 4. The Windows list at MM:18-32 names 26, which matches CL:21.

**Suppressions (brief item 7).**
- None added in round 20.
- Whole pull request: `noqa: S314` with `nosec B314` (MU:124, reasoned in the comment above it) and `noqa: S603` (KW:2249).
- No `type: ignore` and no `pragma: no cover` at the head.

## Round-19 checklist

| Item | State | Where verified |
|---|---|---|
| Design B1: no evidence run | Not resolved | no folder for 7a2eb4c |
| Design M1 / codebase M2: child text in the class and id slots | Resolved | MR:881, MR:900-925 |
| Design M2 / codebase M3: 4-character rule | Resolved for a passwordless address; the same symptom remains through the second layer | M1 |
| Design M3: sockets and no host | Resolved | MR:661, MR:669; KW:3945-3983 |
| Design M4 / codebase M1: test-only switch | Resolved | DIFF-r20:375-388; KW:920 |
| Codebase m1: baseline second layer | Resolved | MR:1434 |
| Codebase m3 / design m6: repeated key | Resolved | MR:606 |
| Codebase m4: IPv6 in key=value | Resolved | MR:554; KW:3778 |
| Codebase m6 / design m11: host list checked late | Resolved | MR:1542 |
| Codebase m7 / design m1: lock folder | Resolved for `dir_fd` and wording; residue | m6 |
| Design m2: socket lock name | Resolved | one grammar |
| Design m4: `type: ignore` | Resolved | none at head |
| Design m5: mutant gaps | Partly | m7 |
| Design m7: reason per key | Resolved | MR:562-570 |
| Design m8: `PG*` guard test | Resolved | KW:4271 |
| Design m9: order | Partly | m8 |
| Design m12: unreachable code | Partly | m12 |
| Codebase m12: `lru_cache` of secrets | Resolved | removed |
| Codebase m10/m11: fuzz and weak tests | Mostly | m7 |
| Comprehension M1 to M9 | Resolved | MR:17, CL:7, CL:463; the CL:26-30 table; CL:42; CL:62; CL:21 |
| Comprehension m1, m2, m6 to m9 | Resolved by the rewrite, as far as read | CL:6-79 |
| Comprehension m3 (internal codes), m5 (sentence length) | Not re-checked | |
| Comprehension m4 (non-steps under "Upgrade steps") | Partly | the background entry is still in that section (CL:71) |
| Design m3, m10, m13; codebase m2, m5, m8, m9 | Not re-checked | texts not opened |

## Not checked

- Nothing was executed: no tests, no mutant run, no hash computed. All "passes", "kills", "fails on the old runner", "248 good" and "186 in the keyword file" are unproven.
- `DIFF-r20.patch` was not read hunk by hunk. I read the CHANGELOG, manifest, mutants and meta hunks, and the grammar hunk of the tool. For the rest of the tool I read the whole head file, not the removed lines.
- Of KW I read only 36-177, 912-951, 1756-1786, 2990-3100 and 3168-4468. The older tests (lock file, masking, signals, conftest inner runs) were not opened.
- `DIFF-vs-main.patch` was only searched, not read. `tests/test_mutation_runner.py` was not read.
- libpq behaviour (m5; home-folder files in m4) is from memory, not a run.
- Windows behaviour was not checked.
- Whether other test files of the repository write `HADAVIN_TEST_PG_DSN` directly was not checked; they are outside the snapshot.

<!-- full hand-back report of sub-agent a3278730, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 19, pull request 89, head b95b0ca7. Read-only, snapshot only, nothing executed.

Verdict: NOT READY by reading. No Blocker. 3 Major, 12 Minor.

Evidence file: `/home/user/hadavin-sdk/handover/evidence/PR89/b95b0ca/RESULTS.md` is NOT present (the folder `b95b0ca` does not exist). Every finding below is from reading; none is confirmed by a run.

Abbreviations: MR = `/home/user/build/snap/p89-b95b0ca/tools/mutation_runner.py`, MU = `/home/user/build/snap/p89-b95b0ca/src/hadavin_sdk/testing/mutation.py`, KW = `/home/user/build/snap/p89-b95b0ca/tests/test_mutation_runner_keywords.py`, MUT = `/home/user/build/snap/p89-b95b0ca/tests/mutation_runner_mutants.py`, META = `/home/user/build/snap/p89-b95b0ca/tests/test_mutation_runner_meta.py`, CL = `/home/user/build/snap/p89-b95b0ca/CHANGELOG.md`.

## MAJOR

**M1. A test "proves" behaviour the real runner no longer has; the autouse fixture hides it; the docs state both.**
- Where: KW:908-917 (`test_a_passed_name_set_to_an_empty_text_still_gets_the_canary`), KW:90-96 (autouse fixture), MR:1317-1319, MR:522-539, CL "pass_env and the shared database" bullet, MR:579-581 and MR:1324-1326.
- Sequence: set `HADAVIN_TEST_PG_DSN=""` and call `run_mutants(..., pass_env=("HADAVIN_TEST_PG_DSN",))`. Real code: `_address_fields("")` returns None (`"".split(" ")` is `[""]`, `_PAIR.fullmatch("")` fails), so `_refuse_unsafe_address` raises "not in a shape" before anything runs. KW's own refusal list has `("", "not in a shape")`.
- The test at KW:908 still passes, only because the fixture replaces `_refuse_unsafe_address` with a no-op for every test whose name lacks one of three prefixes.
- CL and the MR docstring still say the canary "runs whenever a passed name is set, also when its value is empty text". That contradicts the code.
- Wider effect: the fixture is opt-out. About 150 older tests (canary, lock, skip, masking) run `run_mutants` with addresses the real runner refuses (`str(tmp_path / "state.flag")`, `db.invalid`, key=value with a password word). Only the two `test_run_mutants_refuses_an_address_*` tests run the real entry path.
- Scope of the fixture: module-level in KW with `monkeypatch`, so it cannot leak to other test files. `raising=False` means a rename of `_refuse_unsafe_address` would go unnoticed by it.
- Fix: delete or invert the empty-value test and correct the three doc places. Make the switch-off opt-in (a marker on the tests that need a fake address) or move the fakes to accepted addresses (`host=localhost dbname=<unique>`). Drop `raising=False`.

**M2. The projection still shows child-chosen text, filtered by a denylist; the stated guarantee and the fuzz claim are wider than the code.**
- Where: MR:736-755 (`_shown_line`), MR:758-766 (`_shown_id`), MR:728-733, MR:77-78 and CL "what is shown" ("The child's text is not shown at all ... a base64 or hex copy ... can never be complete"), KW fuzz (DIFF-r18.patch:922-987).
- Repro, with secrets from `postgresql://svc:Zq9xK4mTw@localhost/app`:
  - `mr._shown_line("E   wTm4Kx9qZ: x", secrets)` returns `"wTm4Kx9qZ"` (the password reversed). It shares no forward 4-character piece.
  - `mr._shown_line("E   WnE5eEs0bVR3: x", secrets)` returns `"WnE5eEs0bVR3"` (base64 of the password, a valid identifier).
  - `mr._shown_id("tests/test_core::test_WnE5eEs0bVR3[p]", secrets)` returns that base plus `[parameters hidden]`. The base is never checked to be path plus identifier.
- Hex is stopped only by accident: hex of printable ASCII starts with a digit, so `_IDENTIFIER` fails.
- The fuzz generates exactly these forms (reversed, and base64 stripped to alphanumerics as the class in its third template). It passes because it asserts only "no plain 4-character piece", so the changelog's list of forms reads as covered when it is not.
- Realism: this needs a test that encodes the value on purpose. A plain accident (a slice, any letter case) is caught.
- Fix, either:
  - (a) Show the class only when it is a builtin exception name, `Failed`, or the mutant's `crash_type`; show the id only when it fullmatches `<one of the caller's tests paths>(/Class)*::identifier`.
  - (b) Keep the code and correct the docs and CL to say the class name and id base are child text under a 4-character plain-piece filter, and make the fuzz assert what it claims.

**M3. The 4-character pieces come from the whole value, including key names and the scheme, so ordinary rows lose their class and test id (not a leak; the verdict is unchanged).**
- Where: MR:718-733, MR:746, MR:766; CL "cost" names only `test_postgres_...`.
- Repro 1: DSN `host=localhost dbname=app application_name=mut`. The pieces include `tion` (from "application"). `AssertionError` contains `tion`, so every kill shows `[class not shown] [expect found] ...`.
- Repro 2: DSN `postgresql://postgres@localhost:5432/test` (or any database or user with `test` in it). The pieces include `test`, every id contains `tests/test_`, so every row's id is `[test id not shown]`.
- Repro 3: any key=value address gives the pieces `host`, `port`, `name`, `user`, so `test_username`, `test_rename` and `test_host_*` are hidden.
- A caller that builds `Mutant.pinned` from the id column cannot do so from a `pass_env` run.
- Fix: build the pieces from the password forms and the field VALUES the grammar read (host, dbname, user), not from key names, the scheme or the whole value. Otherwise state the real cost in the CL and add a test with a `*test*` database name.

## MINOR

**m1. `_baseline_failure` skips the second layer that the docs promise.** MR:1222-1224 duplicates the class filter and never calls `_masked`; MR:91-95 says the projection "is then passed through `_masked`" and lists the baseline failure message. Repro (contrived): password `abc` (under 4 characters, so no pieces); a baseline test with `pytest.fail("E   abc", pytrace=False)` gives `...(exit code 1): abc`. Fix: `return f"{message}: {_shown_line(first, secrets)}"`.

**m2. `forbid_skips` default is keyed on the names listed, not on a variable being set.** MR:1320-1323 is `bool(env_names)`; `canary` at MR:1324 uses "name in environ". The CL uses "a pass_env name is set" for both. Repro: variable unset, `pass_env=(DSN,)`, a test that skips without a database: now `RuntimeError` "skipped", while the canary, lock, address check and projection are all off. No test covers "listed, not set" (`test_no_name_that_is_not_set_is_checked` uses a test that does not skip). Fix: decide, say it in one phrase, add the test.

**m3. "No repeated key" holds only for the four address keys.** MR:527 tests `key in found`, but `found` stores only `host`, `hostaddr`, `port`, `dbname` (MR:529-538). Repro: `mr._address_fields("dbname=app user=a user=b", sockets=True, keys=mr.ADDRESS_KEYS_ALLOWED)` returns `{"dbname": "app"}`, not None. Fix: keep a separate `seen` set.

**m4. IPv6 in key=value form is the wrong way round.** MR:465, 473. `host=::1 dbname=app` (the libpq spelling, and `::1` is in the default allowlist) is refused "not in a shape". `host=[::1] dbname=app` (brackets are URL-only in libpq) is accepted. `hostaddr=::1` works. No key=value IPv6 case in `_OK_ADDRESSES`. Fix: a key=value host grammar without brackets and with `[0-9A-Fa-f:.]+`.

**m5. A unix-socket address gets the lock name `unparsed`.** MR:492 calls `_address_fields(value)` without `sockets=True`. Repro: run A `host=/var/run/postgresql dbname=a` and run B `host=/var/run/postgresql dbname=b` refuse each other. MR:66 says "the same grammar that names the lock"; it is not the same. After the address check, sockets are the only values that reach `unparsed`, so the CL line "values outside the grammar share the name unparsed" misleads. Also `user=svc` alone is refused (`found or None`, MR:539) although the docs say "no host at all is the local socket".

**m6. `throwaway_hosts` is validated late.** MR:569 runs only when the variable is set and the grammar passed. Repro: `throwaway_hosts="localhost"` or `("*",)` with the variable unset runs fine on a laptop and raises `TypeError` or `ValueError` on CI. Fix: call `_checked_throwaway_hosts` at the top of `_run_mutants`. Bytes and non-str members give `ValueError` (correct); `_address_fields(b"...")` gives a raw `TypeError` (direct calls only).

**m7. Lock folder (MR:793-819).**
- (a) Check then use by path: `lstat`, then `os.open(path / name)`; `O_NOFOLLOW` covers the last part only. In a temp folder without the sticky bit the folder can be swapped for a link in between. Fix: open the folder with `O_DIRECTORY | O_NOFOLLOW`, `fstat` it, open the file with `dir_fd`.
- (b) `os.lstat` at MR:810 can raise `FileNotFoundError` (folder removed after `mkdir`). It is not wrapped, so a raw `OSError` leaves `run_mutants`.
- (c) The CL says another user can no longer "plant a file under one to stop a run". Another user can still stop a run: `mkdir /tmp/hadavin_mutation_locks_<victim uid>` first; the victim is refused every time and cannot remove it in a sticky folder. Fail closed, with a `TMPDIR` way out, but the claim is too wide.
- (d) Windows: "private to the account" holds for the default `%TEMP%` only.
- (e) Not stated: a demo with the old byte copy (lock in the temp folder) and one with the new copy (lock in the sub-folder) no longer see each other.
- Checked as correct: the mode test `& 0o077`, the owner test, the symlink refusal by `lstat`, behaviour as root.

**m8. Doc and code drift in MR and CL.**
- Order of refusals: code runs 1, 4, then 2/3, then 5 (`_secret_values` at MR:1316 holds the 300 count, before the address check). MR:62-75 and CL say "in order" 1 to 5.
- MR:62 "BEFORE any test runs, except step 5": the lock is also taken before any test.
- MR:1317 comment says "marked throwaway database"; there is no marker.
- MR:122 "two changes of result and one new label" vs CL "three results change".
- The `run_mutants` docstring (MR:1123-1134) names neither `throwaway_hosts` nor the address refusal nor the lock-folder refusal.

**m9. Mutant coverage gaps in the new code** (the tests exist, no mutant registered): the `judge_report` branch `rc == 1 and (fixture_failed or collection_failed)` (MU:97-101; the META count for MU stays 12); the label split `NO_TEST_NAMED if rc == 1 else EXIT CODE` (MR:1276); `OSError` inside `_UNUSABLE_JUNIT` (MR:267-270); `.lower()` and `PROJECTION_MIN` in `_pieces` / `_shows_a_piece`; the `ID_HIDDEN` branch; the key allowlist, repeat and socket `..` branches (MR:527-535); the class filter in `_baseline_failure`.

**m10. Fuzz test (DIFF-r18.patch:943-987).**
- The seed is fixed (`_Det(20261111)`). Forms: plain, percent, base64, hex, upper, reversed.
- It does NOT assert on every output field. Covered: row id, `first_lines`, `_baseline_failure`, `_shown_line`, `_shown_id`. Not exercised: the `SKIPPED TESTS`, `COLLECTION ERROR` and `FIXTURE ERROR` branches of `_row`, `_refuse_skips_in_baseline`, the canary message. The "skip message" is imitated by a join of `_shown_id`, although the docstring claims it.
- Always `rc=1`, `forbid_skips=False`, a `<failure>` element.
- The assertion also compares the runner's own fixed words (`[test id not shown]`, "the unmutated copy does not pass its tests") with pieces of the random value, so it holds for this seed and prefix by luck; a seed change can fail it for no real reason.
- `assert checked >= 900` where 5,400 iterations are expected.
- I could not check that it fails on the old runner.

**m11. Weak or blind tests.**
- `test_no_name_that_is_not_set_is_checked` runs with the check patched out, so it could not see a check of `""` for an unset name.
- `test_run_mutants_refuses_an_address_before_any_folder_or_run` watches only `mkdtemp` and `_pytest`, with `_lock_dir` replaced, so a lock taken before the address check would pass.
- No test runs `run_mutants` through the real `_lock_dir`; the four lock-folder tests call `mr._lock_dir()` alone.
- The `_real_lock_dir` fixture calls `monkeypatch.undo()` mid-setup (it undoes every earlier patch of that test, a fragile order dependence). It patches the process-wide `tempfile.gettempdir`, and one test patches the process-wide `os.getuid`. Both are scoped and undone.
- Root: handled (`os.access` skip; the other-uid case works as root). Temp state: all use `tmp_path`.
- `_inner_pytest` needs `hadavin_sdk` importable by a fresh interpreter from another folder (it inherits `os.environ`); if the suite relies on a pytest `pythonpath` setting instead of `PYTHONPATH` or an install, it fails loudly, not silently.
- Wall-clock: new `timeout=180` for each inner run and `baseline_timeout=1` (robust: the child sleeps 30 s). The older 30 s / 60 s bounds at KW:715, 2148, 2859, 2879, 2889 are unchanged.

**m12. `_pieces` keeps secrets after the call.** MR:718 `lru_cache(maxsize=16)` is keyed by the tuple of secrets (the whole address and the password forms), kept for the life of the process. Fix: compute once per call and pass it down, or `cache_clear()` in the `finally` of `_run_mutants`.

## Checked and found correct (by reading)

- **Round-18 suppressions.** The three `# type: ignore` lines are gone (DIFF-r18.patch:1461, 1669, 1686).
  - `msvcrt` is now loaded with `importlib.import_module("msvcrt")` (MR:901-903). That hides the same thing from the type checker without a comment marker; decide whether it counts.
  - New this round: one `# noqa: S603` in KW `_inner_pytest` (DIFF-r18.patch:487). No new `nosec`, `type: ignore` or `pragma: no cover`.
  - Whole pull request against main: only that `noqa`, plus the moved line `# noqa: S314  # nosec B314` in MU:124.
  - MR:967 (`type: ignore[call-overload]`) and MR:1103 (`type: ignore[arg-type]`) remain; they do not appear as added lines in DIFF-vs-main.patch.
- **Mutant search strings.** Each `old` of the 7 new and the 11 re-pointed mutants occurs exactly once in head MR.
  - The class-filter string also appears in `_baseline_failure` (MR:1224), but there it lacks the leading 8 spaces and the trailing newline.
  - `0o077` is distinct from `0o177` in `_check_lock_file`.
  - The other grammar mutants (MUT:462-492) still match.
- **Killers.** Each named killer has a first assertion that the mutant breaks and that holds the `expect` text. Two are narrower than their names:
  - "a class name that shares a piece with a secret is shown" (MUT:501): the killer's input holds the WHOLE password, which the second layer also hides, so the 4-piece rule itself is not what kills.
  - "the parameters of a test id are shown" (MUT:502): killed because the parameter holds the secret (the mutant output becomes `[test id not shown]`), not because parameters are shown.
- **Counts.** 217 to 224 and 155 to 162 agree with the 7 additions.
- **Error labels** (MR:1276-1282): `rc == 1` gives `NO FAILING TEST NAMED`; any other code gives `EXIT CODE n`, negatives included; exit 0 and 5 give an empty id; an id that is present wins.
- **`judge_report`** (MU:78-101): correct. Its fixture/collection branch is redundant for `_row`, which returns earlier.
- **`_row` paths.** Timeout, reaped, unusable JUnit (`OSError`, `ValueError`, `SyntaxError`, and `UnicodeDecodeError` as a `ValueError`), JUnit missing, canary and baseline skip all emit fixed text, class names or `_shown_id` only. No raw child text reaches a row, `first_lines`, `on_result`, `CanaryFailed.rows` or an exception message, apart from M2 and m1.
- **`_shows_a_piece`.** Case is folded on both sides, all overlapping windows are taken, decoded and encoded password forms are included (they are in `secrets`). A secret under 4 characters gives no pieces and relies on `_masked` alone.
- **Address grammar.** URL regex is anchored by `fullmatch`; login and host cannot hold `@`; multi-host commas, port lists, `?host=`, `service`, `options`, percent-encoded hosts and `dbname=<url>` are all refused; the host is lower-cased; the `..` socket rule works.
- **Duplicate-name guard** (META:111-116): reads top-level `def`s only, which is enough.
- **Conftest guard tests.** They now use a real inner pytest with a quiet control.
- **Pins.** The two new sha256 values are identical in the CL and in `tests/fixtures/mutation_manifest.json`.

## Not checked

- Nothing was run: no test, no mutant run, no lint, no type check. "Fails on the old runner" is unverified.
- The sha256 pins against the file bytes (no hashing tool available to me).
- `.github/workflows/ci.yml` (not in the snapshot), so the CI address claim is unverified.
- Most of KW outside the round-18 hunks and the helpers; `tests/test_mutation_runner.py` except one test; `DIFF-vs-main.patch` beyond a search for suppressions; CL bullets outside the mutation runner.
- Windows behaviour; libpq behaviour (from knowledge, not from a run); pytest's JUnit wording for `pytrace=False` (from memory of the source).

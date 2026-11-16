<!-- full hand-back report of sub-agent a309e5a8, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PR89 round 22 is finished and pushed: head c2f98f49 on core/mutation-runner-keywords. It is a fast-forward from 7a2eb4cc and is one squashed commit, so the stopped builder's WIP commit 3b2dc9c1 is gone from that branch. I did not open or merge a PR. No EGM review was run (builder only), and the "answers findings" table below rests on my own tests plus the lead's evidence folder, not on a fresh reviewer.

**Not run, uncertain, or weaker than it looks (read first)**
- **Full suite, first run (on fa0f7f34): 1 failure.** `tests/demo_askdata/test_validate_harm.py[dblink-connect]` failed because I started my Postgres without PGHOST/PGPORT in the server's own environment, so dblink looked for the default socket. That is my setup slip, not a code fault. I restarted the server with those variables and that file passed (253 passed, `evidence/rerun-harm.log`).
- **Two mutants were not good on the first mutant run: 259 of 261.** Both were "the environment is read again" (each mutant run, canary run), `WRONG_REASON`.
  - **Cause:** the killer test used an unlisted host in its changed address. The new address guard in `_pytest` refused it with a `ValueError` before the child ran.
  - **Fix:** the changed address now uses the listed host `db.invalid`, so only the value tells the two apart. The same two mutants then gave 2 of 2 good.
  - **Then I amended the commit, so the first suite and mutant runs are not on the final head.** On c2f98f49 I re-ran the full suite once and the whole mutant list once.
- **Two new tests pass on the old code** (7a2eb4cc), so they do not prove a fix. They are `test_a_failed_baseline_with_an_unusable_result_file_says_only_how_the_run_ended` and `test_a_link_to_a_private_folder_is_no_runtime_folder_for_the_lock`. Each has a mutant (both killed in the 261/261 run), but the tests alone are not fail-before proof.
- **Open owner question, unchanged:** a password together with `sslmode` or `connect_timeout` cannot be written, because the URL shape takes nothing after the database name and the words shape takes no password key. The CHANGELOG and docstring say so plainly.
- **Huge port accepted.** A URL port such as `99999999999` is accepted (independent evidence, address row 93). I left it: the host is still checked, and the database library refuses such a port.
- **Not verified:**
  - Windows and macOS were not run. The texts say so.
  - The perf-marked tests were not run (the suite ran `-m "not live and not perf"`).
  - I did not independently check the Windows-survivor mutants. The count "26" is dropped from the texts and replaced by "some, names in the header".
  - I did not re-run the leak, address and lock probes of the independent evidence on the new head.
- **Suppressions:** against 7a2eb4cc this round adds 0. Against origin/main the diff has 2 (`noqa: S314 # nosec B314` on `ET.fromstring`, which is an existing line that moved, and `noqa: S603` on a `subprocess.run` in a test). I left both as they are.

**Commands and results, final head c2f98f49** (logs in `/home/user/build/B-PR89-r22b-ev/`)

| check | result |
|---|---|
| Full suite via heavy.sh, `-m "not live and not perf"` (`full2.log`) | exit 0, 10777 passed, 1 skipped (a bedrock stub case), 28 deselected |
| Whole mutant list via heavy.sh (`mutants2.log`) | exit 0, 261 of 261 good, 0 BAD |
| ruff check `src tests demos tools` | exit 0 |
| ruff format --check | exit 0 |
| bandit -ll on `src demos tools` | exit 0 |
| `tools/scan_repo.py` | exit 0, no findings |
| gitleaks on `origin/main..HEAD` | exit 0, no leaks |
| Pins recomputed after the last change | no diff |

- **Runner test files:** step 8 of the order test passed after the fix. The four runner test files passed (329 passed, exit 0) before the CHANGELOG and docstring edits. The suite above covers them again on the final head.
- **mypy:** `--platform win32` on `tools/mutation_runner.py` gives 13 errors at this head. 12 are POSIX-only attributes (`getuid`, `O_DIRECTORY`, `O_NOFOLLOW`, the `waitid` constants, `killpg`, `SIGKILL`) and 1 is the untyped import of `hadavin_sdk.testing.mutation`, the same single error Linux shows. The count is now stated in the CHANGELOG and the module docstring.
- **Fail-before** on a clean worktree of 7a2eb4cc with the new keywords, meta and mutants test files overlaid: 42 failed, 276 passed (`/home/user/build/B-PR89-r22b-fail-before.txt`, copy in the evidence folder). That worktree has been removed.

**Findings answered**

| finding | fix | test or proof |
|---|---|---|
| Step-8 value (stopped builder's red test) | the made-up address is now a password in 901 percent-encoded layers (more than 300 texts, under 2,000 characters); an assert checks it stays under the length limit; the limit is untouched | `test_the_refusals_come_in_the_order_the_docstring_gives` passes |
| Wording Majors M1 to M4 (CHANGELOG) | rewritten from the docstring. `[expect found]` scripts now test the fixed words, with real example rows. Environment variables only, `HOME`, run under an account with no real credentials. The condition for `throwaway_hosts` comes first and the list REPLACES the defaults. Windows and macOS: not run, mypy win32 count given. "use the runner as it is" is removed. | reading; mutant list covers the code the texts describe |
| Review-history words, counts, Minors 4, 5, 6, 8, 10, 12, 13, 14 and 15 | "in this round" and "older copy" are gone. 248 became 261. Row shape explained once. The two red-list cases JUNIT MISSING and lock refusal are added. Lock file name and temp-folder access are stated. Windows lock sentence made clear. | text only |
| Codebase m10 statements | `TypeError` for a bare string, refusals named as they are, "exact member" now says whole name without regard to case, "300 seeded draws", no run-dependent "fails on the previous version" claim. | text only |
| `run_mutants` docstring, `mutation.py` docstring, Minor 16 | the long `RuntimeError` sentence is now a list. The `mutation.py` docstring is a list of verdicts with plain explanations. The older "re-copy it in every repository" bullet now points to all four files. | text only |
| Evidence folded in | a test can forge its own result file; the lock folder falls back to `tempfile.gettempdir()` when TMPDIR is not writable. Both are added to the module docstring and the CHANGELOG. The leak table showed 0 of 498 shown, and the halves case ("test_" and "probe") came from the old cutting code, now replaced by whole-slot replacement. | not re-probed on the new head |

**Files and paths**
- Worktree: `/home/user/build/B-PR89-r20`. Pins script: `/home/user/build/B-PR89-r22-pins.sh`.
- Changed: `CHANGELOG.md`, `tools/mutation_runner.py`, `src/hadavin_sdk/testing/mutation.py`, `tests/test_mutation_runner_keywords.py`, `tests/test_mutation_runner_meta.py`, `tests/mutation_runner_mutants.py`, `tests/fixtures/mutation_manifest.json`.
- Checkpoint: `/home/user/build/checkpoints/B-PR89-r22b.md`. Evidence folder: `/home/user/build/B-PR89-r22b-ev/`.

**Hygiene:** my Postgres (port 56822) is stopped and its folder removed. No sub-agents were started and I killed nothing. Leftover `mutants_*` and `mutant_ini_*` folders in `/tmp` are not mine to remove: I did not check whether they belong to other sessions' runs.

**Time and tokens:** about 50 minutes of real clock (16:23 to about 17:15 UTC). I did not measure my own token use.

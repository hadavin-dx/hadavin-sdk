**What:** Semgrep is a code scanner that looks for known risky code patterns. This PR adds a CI job (`.github/workflows/semgrep.yml`) that runs the open-source Semgrep, version 1.185.0, on every pull request to main and every push to main.
**Why:** it adds a second opinion next to the checks we already run (ruff, mypy, bandit, gitleaks, CodeQL).
**What it does not do:** it does not scan `tests/` or `demo_only/` and does not look for secrets. It reports only Semgrep's highest severity level, called ERROR. It is intended not to be a required check.

**Code touched:** this PR changes no code under `src/` and no core module. It adds or changes 9 files: `.codeant/configuration.json`, `.github/workflows/semgrep.yml`, `.gitleaks.toml`, `docs/tests.md`, `exceptions.txt`, `requirements-semgrep.in`, `requirements-semgrep.txt`, `tests/test_gitleaks_semgrep_lock.py`, `tests/test_nosemgrep_form.py`. **No suppression comment is added on any code line:** 0 added lines contain `noqa`, `nosec`, `NOSONAR` or `type: ignore` (measured with `git diff`). The word `nosemgrep` does appear in 64 added lines (the docs, test data, and one message in the workflow); none of them suppresses a finding of a real file. The new tests start programs (`git`, the gitleaks program, and `bash`) through the helper `_run` that already exists in `tests/test_hygiene.py` and already carries that file's one existing `noqa` comment; no new helper and no new comment were added. Two of the commands are fixed words (`git ...`, gitleaks). The third is `bash -e -c <text>`, where the text is the `run:` block of the scan step, read from `.github/workflows/semgrep.yml` in this repository: bash does run a shell script there, with a stand-in `semgrep` in front on the path. No text from a scanned file or from a user reaches a command line.

**Commits named below:** `0841f36` is the commit that was scanned with Semgrep. It was a commit of the branch `pr-3-tests` and is not in the history of main, because the earlier pull requests #2 to #4 were merged into main as one squash commit. `61ded9e` is the commit this PR is cut from: the head of main, which is that squash commit. Its message names `3598120` as the head of the squashed branch, and `61ded9e` and `3598120` have the same file tree (compared). `61ded9e` already holds the `sonar.yml` fix, the `tests/` folder and the test file `tests/test_workflow_files_parse.py`.

The diff of this PR is the patch with sha256 `b59f5bd9cb776f3dcf4985beaa6577d869b5d66f045f3b23950835264aae9d73`.

## What this PR does NOT prove

- **No run of this workflow on GitHub has been seen.** Every result below comes from a local copy, not from GitHub.
- **Semgrep was not run with the registry packs for this PR.** The rules of `p/python` and `p/javascript` were not downloaded for any check in this version. The only run with those packs is the project lead's earlier run on `0841f36` (see "Scan result").
- All Semgrep runs listed under "Tests run" used a made-up local rule, not the registry packs. Only one of them ran on `61ded9e` (the five scanned folders); the others ran on earlier trees.
- The full test suite was not run on `61ded9e`.
- **In a client copy of the repository (without `demo_only/`), both new test files are skipped as a whole** (they import `support`, which needs `demo_only/`), so the checks of the workflow, the suppression form and the gitleaks exceptions do not run there at all.
- **The workflow tests do not show that the workflow is safe.** They pin the particular changes listed under "Tests run"; a change that is not on that list can still pass them. Eighteen made-up changes were tried and all are caught; that is a sample, not a proof.

## What the job checks

- It installs Semgrep 1.185.0 from a lock file (`requirements-semgrep.txt`). A lock file lists every package with its exact version and a checksum (a hash). This lock holds 67 packages in 1130 lines.
- It checks the install (`pip check` and `semgrep --version`). A broken install is then reported as an install problem, not as a finding.
- It scans the folders `src`, `scripts`, `load_tools`, `tools` and `n8n`.
- It uses two rule packs from the public Semgrep registry (Semgrep's online rule library): `p/python` and `p/javascript`. No other packs.
- It fails the job only on a finding of severity ERROR. Findings print in the job log only. Nothing is uploaded to GitHub code scanning.
- Options: `--metrics=off` sends no usage data to Semgrep. `--disable-version-check` makes no call to check for a newer Semgrep. With `--strict`, a broken rule, or a file that cannot be fully read, stops the run instead of being skipped.
- If Semgrep exits with code 2 (registry or network failure, or a folder that does not exist), the job tries again. It makes up to 3 tries, 20 seconds apart. Findings (exit code 1) are never retried.
- **The job fails when Semgrep exits with code 3.** Under `--strict`, some files that cannot be fully read make Semgrep exit 3; not every syntax error does. Measured with the real Semgrep 1.185.0 and a made-up rule, offline, on this PR (saved output `evidence-11`): a Python or JavaScript file with an unclosed call bracket (`print("hit"` or `eval("hit"`) gave exit 3 with `--strict` and exit 0 without it. The two earlier test folders whose cause was not described both hold a broken JavaScript file: `function f( {` followed by an unclosed `eval("hit"` (with or without a clean Python file next to it); they gave exit 3 with about 100 percent of lines read. But `def f(:` followed by `  pass`, `def f(` followed by `  pass`, and `function f( {` followed by `}` gave exit 0 even with `--strict` (about 100 percent read). The share of lines read does not predict the exit code. The job reports exit 3 as a tool error and prints "NOT findings". It then fails and does not retry.
- The four number tests in the scan step use `[[ ]]` instead of `[ ]`. That is the form SonarCloud's shell rule S7688 asks for ("Use '[[' instead of '['"). The behaviour is unchanged: with a stand-in program in place of Semgrep, the exit status, the number of tries and the printed messages are the same as before for every exit code tried, under both ways GitHub can start bash. `lint.yml` on main uses the same `[[ ]]` form. This compares the step's own logic only; the real Semgrep was not used for it.

## What the job does NOT check

- `tests/` and `demo_only/` are not scanned. `tests/` holds planted fake secrets and deliberately unsafe code that other checks must catch. `demo_only/` holds fake services and a demo page. **This was decided without a scan result.** Nobody has scanned these two folders with Semgrep.
- `n8n` is in the list but only in name. It holds 3 JSON files, and no rule pack reads JSON. JavaScript inside an n8n Code node is not read either.
- Only severity ERROR. Findings at lower levels (WARNING, INFO) are not reported and were not looked at.
- No rule packs other than `p/python` and `p/javascript`.
- No secrets scan. Looking for secrets stays the job of gitleaks in `lint.yml`.
- **The rules change over time.** The registry rules are downloaded fresh at every run and cannot be pinned to a version. So the result can change between two runs with no change in this repository.
- **It is intended not to be a required check.** The workflow comments say to keep it out of the required checks. Whether GitHub's branch settings agree was not checked. Only the repository owner can make it required.

## Scan result, exactly as measured

- **ERROR-level clean on commit 0841f36 of the branch `pr-3-tests`, as of the lead's run.** That commit is an earlier commit of the branch whose pull requests were squashed into main's `61ded9e`. The project lead ran that scan, and Semgrep reported no finding at level ERROR.
- That run used Semgrep 1.185.0 (container image `semgrep/semgrep:1.185.0`), the packs `p/python` and `p/javascript`, severity ERROR, and the same five folders. It ended with exit code 0 and no finding.
- That run differs from the workflow in three ways. It did not use `--strict`. It did not use `--disable-version-check`. It put the options in a different order.
- It also used `--quiet`. So its output does not show that both packs were really downloaded.
- This PR is cut from main's `61ded9e`. Since 0841f36, 25 files in the scanned folders changed (912 lines added, 118 removed; measured as `git diff --shortstat 0841f36 3598120 -- src scripts load_tools tools n8n`, where `3598120` has the same tree as `61ded9e`). Two of those files are new modules: `src/lead_desk/urls.py` and `tools/pathconfine.py`. **The scan was not repeated on 61ded9e.**
- **No run of this workflow on GitHub has been seen yet.** The first live CI run on this PR is the real check. The job log prints the Semgrep version and the pack names at the start.
- The first run may fail on a finding that already exists in the code. Then the plan is to fix the code, or to suppress that one finding by its rule id, in a separate change.

## Licence of the rules

- The Semgrep program (the engine) is open source under LGPL-2.1. The registry rules have a separate licence, the Semgrep Rules License v1.0. **The text of that licence was not downloaded or read for this PR.**
- The repository owner has given a yes to using `p/python` and `p/javascript` only, for this repository only. No other pack is covered. This yes is also written in the "Semgrep" section of `docs/tests.md` in this PR.
- This repository is public, so the job log is public. The log prints the rule id and rule message of every finding. That is accepted under the owner's yes.
- No copy of any rule is stored in this repository.

## Overlapping runs

- Runs that share a group name cancel each other. Each branch or pull request gets its own name: `semgrep-${{ github.ref }}`.
- In a pull request, a newer push cancels the older Semgrep run that is still running.
- A push to main does not cancel a run that is already running on main: cancelling is switched on only for pull request runs. **Not measured:** from the GitHub documentation as remembered (not read again for this PR), GitHub may still replace a run of the same group that is only waiting to start (pending) with a newer one, even with cancelling off. So with several pushes to main in quick succession, a waiting run could be dropped. Semgrep results on main are not a gate, so this only costs a missing result.
- This is safe only while `github.ref` stays in the group name. A test (`test_semgrep_workflow_does_not_cancel_a_running_push_to_main`) pins this whole block and fails if it changes.

## How the lock file was made

- `pip-compile` and `uv` are two Python tools that write lock files. The header of each lock file names the tool that made it: `pip-compile` made `requirements-dev.txt`; `uv` made `requirements-dev-win.txt`, `requirements-coverage.txt` and the two browser locks. The Semgrep lock was made with `uv` 0.13.8 (the command in `requirements-semgrep.in`). The uv version is written down only for the coverage lock (0.11.32, in `requirements-coverage.in`) and the Semgrep lock.
- The Semgrep lock was made a second time with uv 0.13.8 and the same arguments. A byte-by-byte file comparison (`cmp`) found the new file identical to the committed one: same sha256, starting `a791abb7e447`, and 1130 lines. The saved output of that check (the uv version, the command, the `cmp` result and both checksums) is in the project's handover notes. That check ran on an earlier tree; the lock file in this PR has the same sha256 on `61ded9e`.
- That second run used uv installed from PyPI under Python 3.13. The docker command written in `requirements-semgrep.in` was not run.

## Supply chain and permissions

- The install is `python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt`.
- Every package must match its checksum. Only ready-made packages are installed, so nothing is built from source. Nothing outside the lock file is pulled in.
- `pip check` then confirms that no package is missing or in conflict.
- The job uses two GitHub Actions (reusable workflow steps): checkout and setup-python. Both are pinned to a full commit id. Checkout keeps no credentials (`persist-credentials: false`).
- Permissions: `contents: read` only. The job uses no repository secret and no token. No Semgrep account is used.
- Timeout: 20 minutes. This is an upper limit, not a measurement: no GitHub run has been timed. Installing from the lock took 17 seconds in one local test (earlier tree, not re-run on `61ded9e`).

## Other files in this PR

- `tests/test_nosemgrep_form.py`: every Semgrep suppression comment (`nosemgrep`, or the short form `nosem`) must name a dotted rule id, for example `# nosemgrep: python.lang.x.y <reason>`. A bare `nosemgrep` would hide every finding on that line.
- The test also refuses other spellings that Semgrep 1.185.0 was seen to treat as a bare suppression: any upper or lower case, extra letters after the word, and the long s `ſ`.
- `tests/test_gitleaks_semgrep_lock.py`: gitleaks is the secrets scanner in `lint.yml`. The lock file is full of checksums that look like secrets to it. This PR adds an exception telling gitleaks not to report the checksum lines. The test runs the real gitleaks and checks that this exception is exact. A second part widens the exception on purpose and fails if the widening goes unnoticed.
- `.gitleaks.toml` and `exceptions.txt`: three exceptions in all. (1) the checksum lines of the lock file (gitleaks; and `exceptions.txt` line 32, for the literal-text scan of `lint.yml`); (2) the file name `requirements-semgrep.in` (gitleaks mistakes the `.in` ending for a web address; `exceptions.txt` line 33); (3) `exceptions.txt` line 34, `^requirements-semgrep\.txt:[0-9]+:(opentelemetry-[a-z-]+)(==[0-9]+)?$`: the literal-text scan reports any run of 40 or more letters, digits or dashes, and some OpenTelemetry package names in the lock are that long, so those names, in the lock file in the repository root only, are let through. A new test (`test_otel_name_exception_is_narrow` in `tests/test_gitleaks_semgrep_lock.py`) plants the same name in other files and another long name in the lock: all are still reported; it also widens the line three ways and checks that the bad cases then slip through.
- `tests/test_nosemgrep_form.py` also holds the workflow tests described under "Tests run".
- `.codeant/configuration.json`: CodeAnt (a review service) skips the lock file.
- `docs/tests.md`: a new "Semgrep" section (status of the scan, licence, what is scanned, exit codes, how to run it, how to suppress a finding, how to update Semgrep).

## Trade-offs and known gaps

- The gitleaks exception for checksum lines applies only to the file `requirements-semgrep.txt` in the repository root (`^requirements-semgrep\.txt$`). A copy of that file in a sub-folder gets no exception. This was tightened from an earlier, looser pattern.
- CodeAnt skips the lock file, so CodeAnt does not check those 67 packages.
- Dependabot (GitHub's update bot) is set up for GitHub Actions only. It covers none of the lock files, this one included. So nothing checks the 67 Semgrep packages for updates automatically. The repository owner checks by hand, when a Semgrep security advisory appears or about once a quarter.
- The Semgrep lock fits Linux x86_64 and Python 3.12 only (the CI runner).
- The retry and exit-code logic of the scan step is now run by a test (`test_scan_step_retries_only_exit_2`, 8 cases) with a stand-in `semgrep`, under `bash -e`, on Linux only; it is skipped on other systems and in a copy without `demo_only/`. It does not use the real Semgrep. The test waits 0 seconds between tries (the pause is set to 0), so the 20-second pause is not tested.

## Tests run for this PR

On a clean copy of commit `61ded9e` with this PR's changes, unless a line says "not re-run on 61ded9e". Re-measured on `61ded9e`: the focused tests, `git apply --check`, gitleaks, ruff, mypy, bandit, the stand-in check of the scan step, the two overlapping-runs breakages, and one real Semgrep run with a made-up rule over the five folders. In a copy of the repository without `demo_only/` (the way a client copy is made), ruff and mypy are clean, but 6 of the 8 test files named in this section are skipped as a whole by `tests/conftest.py` (they import `support`, which needs `demo_only/`), including both files of this PR (the v9 run of 5 of the files skipped 3, among them both of this PR's). Only `test_workflow_files_parse.py` and `test_workflow_run_flags.py` ran there: 15 tests passed. The saved outputs are in the project's handover notes.

- Focused tests (v9 patch, clean `61ded9e` with the patch applied, no extra git refs): 333 passed in 78 s in the eight files `tests/test_hygiene.py` (24), `tests/test_nosemgrep_form.py` (93; the retry test is 8 of them and the workflow-change checks are 1 + 21 mutant cases), `tests/test_gitleaks_semgrep_lock.py` (4, one new), `tests/test_gitleaks_exceptions.py` (44), `tests/test_workflow_files_parse.py` (5), `tests/test_workflow_run_flags.py` (10), `tests/test_shell_single_bracket.py` (146) and `tests/test_codeant_hygiene.py` (7). (In the v9 build, a first run failed `test_hygiene_scan_public` because three strings with `\n` after a colon looked like a Windows path to the literal-text scan; they were rewritten and the run above is the second.)
- These ran with the real gitleaks (version 8.30.1) and with the setting that makes the hygiene test fail, instead of skip, when gitleaks is missing. A header line that the person running the tests wrote into the saved output names both; the test output itself does not show them.
- Deliberate breakages of the real workflow file (mutants), run on the v9 tree (`evidence-6`; the workflow file was restored byte-identical with `cmp` after each of the 18). Each was run against the v8 test file and the v9 test file. Changes that the v8 tests did NOT catch (v8 file: all 81 passed) and the v9 tests catch: `--no-deps` removed (2 fail), `continue-on-error: true` on the scan step (1) and on the job (1), an extra pack `p/ci` (2), `runs-on: self-hosted` (4), `--metrics=off` removed (2), the folder `tools` dropped from the scan command (2), a job-level `permissions: id-token: write` (1), `timeout-minutes: 360` (2). Caught by both: persist-credentials true, event/head_ref/ref_name/base_ref text inside a `run:` step, `--strict` removed, severity WARNING, retry also on exit 1, a `secrets.` reference in an env block. (For the `ref_name` and `base_ref` cases the v8 file failed only because the stand-in test could not run the broken block, not because its hazard check saw them.) These are 18 changes I thought of; other changes may still pass. The earlier two (`cancel-in-progress: true`, a constant group) are caught by the older concurrency test; they were last re-run on the v7 tree. The unbroken v9 file: 93 passed.
- Deliberate breakages of the gitleaks exceptions (left anchor removed, line rule widened, path widened, file-name rule widened): each made the lock test fail. Earlier version of this PR, not re-run on 61ded9e. The test that checks the exceptions is unchanged in substance, but this file now starts programs through `tests/run_cmd.py`; its in-test widening checks pass, the manual breakages were not repeated.
- 24 comment shapes were tried, one by one, against the old and the new suppression test. They are mostly the short spelling `nosem` and upper-case forms, and real Semgrep 1.185.0 reads most of them as "hide findings". The old test missed 23 of the 24; the new test refuses all 24. Earlier version of this PR, not re-run on 61ded9e.
- `git apply --check` on a clean copy of `61ded9e`: OK.
- gitleaks on a clean copy with this PR's changes committed: no leaks, in the files and in the history.
- ruff check and ruff format: clean. mypy for Linux and for Windows: no issues in 28 source files.
- bandit (`-ll`, medium and high severity) on `src`, `tools`, `scripts`, `load_tools`: exit 0, no issue reported.
- The scan step with a stand-in program in place of Semgrep: exit codes 0, 1, 2, 3 and 7, "2 then 0", "2, 2, 0", "2, 2, 2" and "2 then 1" give the same exit status, number of tries and messages as before the `[[ ]]` change. Exit 2 gives 3 tries; exit 3 gives 1 try and the "NOT findings" message. The old-versus-new comparison was measured on `db54e13` (the workflow file is byte-identical here); on `61ded9e` only the new block was run, under both bash forms, with the results just listed.
- Semgrep exit codes 0, 1, 2 and 7 were seen locally with the pinned version on a made-up rule (earlier tree, not re-run on 61ded9e; not with the registry packs).
- Files with a syntax error, tested with the pinned Semgrep 1.185.0 and a made-up local rule, offline, re-run for v8 (saved output `evidence-11`): unclosed-bracket files (`print("hit"`, or `eval("hit"`, or a broken `def`/`function` line before it) gave exit 3 with `--strict` and exit 0 without it, at about 0, 50, 75 or 100 percent of lines read. `def f(:` + `  pass`, `def f(` + `  pass` and `function f( {` + `}` gave exit 0 with `--strict`, at about 100 percent. A real finding next to a syntax error gave exit 1 either way (the fresh reviewer's run on the v7 tree, not re-run for v8). With `--verbose`, the broken JavaScript file printed a "Syntax error" warning with its file name; the `def f(:` file printed none.
- The real scanned folders of `61ded9e` with this PR's changes (the v7 patch; the v8 patch changes no scanned folder, so the run was not repeated), with the same made-up local rule (not the registry packs), Semgrep 1.185.0. Semgrep read 47 files (30 in `src`, 9 in `scripts`, 4 in `load_tools`, 4 in `tools`, none in `n8n`), reported about 100% of lines parsed, and exited 0 with and without `--strict`. So today's files do not trigger exit 3 with that rule. Whether the registry packs read them the same way is not tested. (An earlier measurement on `2db3926` read 45 files with the same result; the five folders are not identical on `61ded9e`: 16 files differ from `db54e13`.)

## Tests NOT run

- The full test suite on this PR at 61ded9e. (An earlier version of this PR, on 0841f36, ran the full suite: 2426 passed, 115 skipped.)
- Any real GitHub CI run of this workflow.
- Windows and PowerShell.
- Windows and Python 3.13 for the new tests (the retry test is skipped off Linux).
- The real Semgrep with the registry packs on the v8 patch; any GitHub run (so whether Sonar flags the helper or the new tests is unknown).
- Python 3.13: only the lock regeneration ran on 3.13, not the tests.
- Semgrep with the registry packs on `tests/`, on `demo_only/`, or on 61ded9e. Semgrep at WARNING level.

## Measured vs not

"Re-measured on 61ded9e" means the check was run again on `61ded9e` with this PR's changes. "Not re-run on 61ded9e" means the result comes from an earlier tree or an earlier version of this PR.

| Claim | Status |
|---|---|
| Patch applies to `61ded9e` (`git apply --check`) | Re-measured on 61ded9e |
| Focused tests: 333 passed in 8 files (24 + 93 + 4 + 44 + 5 + 10 + 146 + 7) | Re-measured on 61ded9e (v9 patch) |
| ruff, mypy (28 files, Linux and Windows), bandit `-ll` | Re-measured on 61ded9e |
| gitleaks: no leaks in files and history | Re-measured on 61ded9e |
| Lock file: 67 packages, 1130 lines, sha256 `a791abb7e447...` | Re-measured on 61ded9e |
| 25 files, 912 lines added, 118 removed in the scanned folders since 0841f36 | Re-measured on 61ded9e (via `3598120`, same tree) |
| Scan step logic unchanged by `[[ ]]` (stand-in program, not Semgrep) | Old-versus-new on db54e13; new block only on 61ded9e |
| ERROR-level clean with the registry packs | Only on 0841f36 (lead's run); not re-run on 61ded9e |
| Overlapping-runs mutants (2 breakages, each caught) | v7 tree; not re-run on v8 |
| 18 made-up workflow changes: the v8 tests missed 8 of them, the v9 tests catch all 18 (this pins those 18 only; it does not show the workflow is safe) | Re-measured on 61ded9e (v9 patch) |
| 0 noqa/nosec/NOSONAR/type: ignore added; the word nosemgrep is in 64 added lines (docs, test data, workflow message), none suppresses a finding; ruff, mypy, bandit clean | Re-measured on 61ded9e (v9 patch) |
| GitHub may replace a pending run in the same group | NOT measured (documentation as remembered) |
| gitleaks-exception mutants (4 breakages, each caught) | Not re-run on 61ded9e |
| 24 comment shapes (old test missed 23, new test refuses 24) | Not re-run on 61ded9e |
| Real Semgrep exit codes 0, 1, 2, 7 (made-up rule) | Not re-run on 61ded9e; not with the registry packs |
| Real Semgrep exit 3 for some unclosed-bracket files; exit 0 for `def f(:` (made-up rule) | Re-measured for v8 on small made-up folders (not on 61ded9e's folders); not with the registry packs |
| 47 files read, about 100% parsed, exit 0 with and without `--strict` (made-up rule) | Re-measured on 61ded9e |
| Lock file rebuilt and identical (`cmp`) | Earlier tree; same sha256 on 61ded9e |
| Install time 17 seconds | Earlier tree, one local test |
| Full test suite: 2426 passed, 115 skipped | On 0841f36 only (earlier version of this PR) |
| Any run on GitHub | Not seen |
| Registry rules downloaded for this PR | No |
| Text of the Semgrep Rules License v1.0 | Not read |

## What a reviewer should look at first

- The overlapping-runs block and the scan command in `.github/workflows/semgrep.yml`: does it cancel only pull request runs, and does it scan exactly what is listed above?
- The two new blocks in `.gitleaks.toml`: are they as narrow as `tests/test_gitleaks_semgrep_lock.py` claims?
- The choice to leave `tests/` and `demo_only/` unscanned, made without a scan result: is that acceptable for now?

## If the job goes red

- **Exit 1** (findings): the log lists each finding with its rule id. Fix the code, or suppress that one finding with `# nosemgrep: <rule-id> <reason>` (see `docs/tests.md`, "Semgrep"). Never use a bare `nosemgrep` without the rule id: it hides every finding on the line, and a test refuses it.
- **Exit 2** (registry or network failure, or a missing folder): re-run the job later, and check that the five folders exist.
- **Exit 3** (for example, a file could not be fully read): this is not a finding. Run the scan locally with `--verbose` added. For some syntax errors, the log shows a "Syntax error" warning with the file name; for other causes it may not. Fix the syntax error in that file. Not every syntax error gives exit 3.
- If the file is valid and Semgrep still cannot read it, report it as a Semgrep problem. Decide in a separate change whether to leave that file out.
- Do not remove `--strict` to turn the job green: that would hide files Semgrep cannot read.
- **Any other exit code** (other than 0, 1, 2 and 3): a tool error. Read the job log.

## How to run it on your own computer

You need network access to the Semgrep registry, because the rules are downloaded at run time. Docker is not needed. From the repository root, in a Python 3.12 virtual environment on Linux x86_64:

```
python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt
python -m pip check
semgrep scan --metrics=off --disable-version-check --strict --error --severity ERROR --config p/python --config p/javascript src scripts load_tools tools n8n
```

On another system or Python version the lock file does not fit. There, use `pip install semgrep==1.185.0` (no checksums), then the same `semgrep scan` command. What the exit code means:

- 0: no ERROR finding.
- 1: findings.
- 2: the registry could not be reached, or a folder is missing.
- 3: for example, a file could not be fully read.

## Order of merging

This PR is cut from main (`61ded9e`) and has no merge-order dependency. The earlier pull requests #2 to #4 are already on main as one squash commit, so both things this PR needs are there. First, the five scanned folders exist (Semgrep fails if one is missing). Second, `tests/test_hygiene.py` already has the `cwd=target` change (line 200 on `61ded9e`) that makes gitleaks scan from the repository root, which the new gitleaks exception needs. Whether this pull request's base branch on GitHub is main was not checked.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

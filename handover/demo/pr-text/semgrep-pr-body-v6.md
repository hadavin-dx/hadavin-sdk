**What:** Semgrep is a code scanner that looks for known risky code patterns. This PR adds a CI job (`.github/workflows/semgrep.yml`) that runs the open-source Semgrep, version 1.185.0, on every pull request to main and every push to main.
**Why:** it adds a second opinion next to the checks we already run (ruff, mypy, bandit, gitleaks, CodeQL).
**What it does not do:** it does not scan `tests/` or `demo_only/` and does not look for secrets. It reports only Semgrep's highest severity level, called ERROR. It is intended not to be a required check.

**Code touched:** this PR changes no code under `src/` and no core module. It adds or changes 9 files: `.codeant/configuration.json`, `.github/workflows/semgrep.yml`, `.gitleaks.toml`, `docs/tests.md`, `exceptions.txt`, `requirements-semgrep.in`, `requirements-semgrep.txt`, `tests/test_gitleaks_semgrep_lock.py`, `tests/test_nosemgrep_form.py`.

**Commits named below:** `0841f36` is the commit that was scanned with Semgrep. `db54e13` is the commit this PR is cut from: the head of the branch `pr-3-tests`. That branch is the head of pull request #4, the last of the earlier pull requests #2 to #4. `db54e13` already holds the `sonar.yml` fix and the test file `tests/test_workflow_files_parse.py`.

The diff of this PR is the patch with sha256 `fac20b0311503b8724adc1ae20bb4fa6d33a3b5c75bc98ef5783388bc03aac37`.

## What this PR does NOT prove

- **No run of this workflow on GitHub has been seen.** Every result below comes from a local copy, not from GitHub.
- **Semgrep was not run with the registry packs for this PR.** The rules of `p/python` and `p/javascript` were not downloaded for any check in this version. The only run with those packs is the project lead's earlier run on `0841f36` (see "Scan result").
- All Semgrep runs listed under "Tests run" used a made-up local rule, not the registry packs, and none of them ran on `db54e13`.
- The full test suite was not run on `db54e13`.

## What the job checks

- It installs Semgrep 1.185.0 from a lock file (`requirements-semgrep.txt`). A lock file lists every package with its exact version and a checksum (a hash). This lock holds 67 packages in 1130 lines.
- It checks the install (`pip check` and `semgrep --version`). A broken install is then reported as an install problem, not as a finding.
- It scans the folders `src`, `scripts`, `load_tools`, `tools` and `n8n`.
- It uses two rule packs from the public Semgrep registry (Semgrep's online rule library): `p/python` and `p/javascript`. No other packs.
- It fails the job only on a finding of severity ERROR. Findings print in the job log only. Nothing is uploaded to GitHub code scanning.
- Options: `--metrics=off` sends no usage data to Semgrep. `--disable-version-check` makes no call to check for a newer Semgrep. With `--strict`, a broken rule, or a file that cannot be fully read, stops the run instead of being skipped.
- If Semgrep exits with code 2 (registry or network failure, or a folder that does not exist), the job tries again. It makes up to 3 tries, 20 seconds apart. Findings (exit code 1) are never retried.
- **The job fails when Semgrep exits with code 3.** Under `--strict`, a file that cannot be fully read, for example a Python or JavaScript file with a syntax error, gives exit 3 (seen with the real Semgrep on an earlier tree, not re-run on `db54e13`). Exit 3 was also seen in two other made-up tests whose cause the saved test does not describe. The job reports exit 3 as a tool error and prints "NOT findings". It then fails and does not retry.
- The four number tests in the scan step use `[[ ]]` instead of `[ ]`. That is the form SonarCloud's shell rule S7688 asks for ("Use '[[' instead of '['"). The behaviour is unchanged: with a stand-in program in place of Semgrep, the exit status, the number of tries and the printed messages are the same as before for every exit code tried, under both ways GitHub can start bash. This compares the step's own logic only; the real Semgrep was not used for it.

## What the job does NOT check

- `tests/` and `demo_only/` are not scanned. `tests/` holds planted fake secrets and deliberately unsafe code that other checks must catch. `demo_only/` holds fake services and a demo page. **This was decided without a scan result.** Nobody has scanned these two folders with Semgrep.
- `n8n` is in the list but only in name. It holds 3 JSON files, and no rule pack reads JSON. JavaScript inside an n8n Code node is not read either.
- Only severity ERROR. Findings at lower levels (WARNING, INFO) are not reported and were not looked at.
- No rule packs other than `p/python` and `p/javascript`.
- No secrets scan. Looking for secrets stays the job of gitleaks in `lint.yml`.
- **The rules change over time.** The registry rules are downloaded fresh at every run and cannot be pinned to a version. So the result can change between two runs with no change in this repository.
- **It is intended not to be a required check.** The workflow comments say to keep it out of the required checks. Whether GitHub's branch settings agree was not checked. Only the repository owner can make it required.

## Scan result, exactly as measured

- **ERROR-level clean on commit 0841f36 of the branch `pr-3-tests`, as of the lead's run.** That commit is an earlier commit of the branch this PR is based on. The project lead ran that scan, and Semgrep reported no finding at level ERROR.
- That run used Semgrep 1.185.0 (container image `semgrep/semgrep:1.185.0`), the packs `p/python` and `p/javascript`, severity ERROR, and the same five folders. It ended with exit code 0 and no finding.
- That run differs from the workflow in three ways. It did not use `--strict`. It did not use `--disable-version-check`. It put the options in a different order.
- It also used `--quiet`. So its output does not show that both packs were really downloaded.
- This PR is cut from a later commit of that branch, `db54e13`. Since 0841f36, 13 files in the scanned folders changed (405 lines added, 60 removed). **The scan was not repeated on db54e13.**
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
- A run started by a push to main is never cancelled: cancelling is switched on only for pull request runs.
- This is safe only while `github.ref` stays in the group name. A test (`test_semgrep_workflow_never_cancels_a_push_to_main`) pins this whole block and fails if it changes.

## How the lock file was made

- `pip-compile` and `uv` are two Python tools that write lock files. The header of each lock file names the tool that made it: `pip-compile` made `requirements-dev.txt`; `uv` made `requirements-dev-win.txt`, `requirements-coverage.txt` and the two browser locks. The Semgrep lock was made with `uv` 0.13.8 (the command in `requirements-semgrep.in`). The uv version is written down only for the coverage lock (0.11.32, in `requirements-coverage.in`) and the Semgrep lock.
- The Semgrep lock was made a second time with uv 0.13.8 and the same arguments. A byte-by-byte file comparison (`cmp`) found the new file identical to the committed one: same sha256, starting `a791abb7e447`, and 1130 lines. The saved output of that check (the uv version, the command, the `cmp` result and both checksums) is in the project's handover notes. That check ran on an earlier tree; the lock file in this PR has the same sha256 on `db54e13`.
- That second run used uv installed from PyPI under Python 3.13. The docker command written in `requirements-semgrep.in` was not run.

## Supply chain and permissions

- The install is `python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt`.
- Every package must match its checksum. Only ready-made packages are installed, so nothing is built from source. Nothing outside the lock file is pulled in.
- `pip check` then confirms that no package is missing or in conflict.
- The job uses two GitHub Actions (reusable workflow steps): checkout and setup-python. Both are pinned to a full commit id. Checkout keeps no credentials (`persist-credentials: false`).
- Permissions: `contents: read` only. The job uses no repository secret and no token. No Semgrep account is used.
- Timeout: 20 minutes. This is an upper limit, not a measurement: no GitHub run has been timed. Installing from the lock took 17 seconds in one local test (earlier tree, not re-run on `db54e13`).

## Other files in this PR

- `tests/test_nosemgrep_form.py`: every Semgrep suppression comment (`nosemgrep`, or the short form `nosem`) must name a dotted rule id, for example `# nosemgrep: python.lang.x.y <reason>`. A bare `nosemgrep` would hide every finding on that line.
- The test also refuses other spellings that Semgrep 1.185.0 was seen to treat as a bare suppression: any upper or lower case, extra letters after the word, and the long s `ſ`.
- `tests/test_gitleaks_semgrep_lock.py`: gitleaks is the secrets scanner in `lint.yml`. The lock file is full of checksums that look like secrets to it. This PR adds an exception telling gitleaks not to report the checksum lines. The test runs the real gitleaks and checks that this exception is exact. A second part widens the exception on purpose and fails if the widening goes unnoticed.
- `.gitleaks.toml` and `exceptions.txt`: that exception for the checksum lines, and one for the file name `requirements-semgrep.in` (gitleaks mistakes the `.in` ending for a web address).
- `.codeant/configuration.json`: CodeAnt (a review service) skips the lock file.
- `docs/tests.md`: a new "Semgrep" section (status of the scan, licence, what is scanned, exit codes, how to run it, how to suppress a finding, how to update Semgrep).

## Trade-offs and known gaps

- The gitleaks exception for checksum lines applies only to the file `requirements-semgrep.txt` in the repository root (`^requirements-semgrep\.txt$`). A copy of that file in a sub-folder gets no exception. This was tightened from an earlier, looser pattern.
- CodeAnt skips the lock file, so CodeAnt does not check those 67 packages.
- Dependabot (GitHub's update bot) is set up for GitHub Actions only. It covers none of the lock files, this one included. So nothing checks the 67 Semgrep packages for updates automatically. The repository owner checks by hand, when a Semgrep security advisory appears or about once a quarter.
- The Semgrep lock fits Linux x86_64 and Python 3.12 only (the CI runner).
- No test in this repository checks the retry and exit-code logic of the scan step. It was checked only with a stand-in program outside the repository.

## Tests run for this PR

On a clean copy of commit `db54e13` with this PR's changes, unless a line says "not re-run on db54e13". Re-measured on `db54e13`: the focused tests, `git apply --check`, gitleaks, ruff, mypy, bandit and the stand-in check of the scan step. The saved outputs are in the project's handover notes.

- Focused tests: 130 passed in total. `tests/test_hygiene.py` 15 passed, `tests/test_nosemgrep_form.py` 63 passed, `tests/test_gitleaks_semgrep_lock.py` 3 passed, `tests/test_gitleaks_exceptions.py` 44 passed, `tests/test_workflow_files_parse.py` 5 passed.
- These ran with the real gitleaks (version 8.30.1) and with the setting that makes the hygiene test fail, instead of skip, when gitleaks is missing. A header line that the person running the tests wrote into the saved output names both; the test output itself does not show them.
- Deliberate breakages of the real workflow file (mutants): `cancel-in-progress: true` made 1 test fail (62 passed). A constant `group: semgrep` made 1 test fail (62 passed). Not re-run on db54e13; the overlapping-runs block is byte-identical in this version.
- Deliberate breakages of the gitleaks exceptions (left anchor removed, line rule widened, path widened, file-name rule widened): each made the lock test fail. Earlier version of this PR, not re-run on db54e13. The lock test has not changed in substance since; only one comment in it changed.
- 24 comment shapes were tried, one by one, against the old and the new suppression test. They are mostly the short spelling `nosem` and upper-case forms, and real Semgrep 1.185.0 reads most of them as "hide findings". The old test missed 23 of the 24; the new test refuses all 24. Earlier version of this PR, not re-run on db54e13.
- `git apply --check` on a clean copy of `db54e13`: OK.
- gitleaks on a clean copy with this PR's changes committed: no leaks, in the files and in the history.
- ruff check and ruff format: clean. mypy for Linux and for Windows: no issues in 26 source files.
- bandit (`-ll`, medium and high severity) on `src`, `tools`, `scripts`, `load_tools`: exit 0, no issue reported.
- The scan step with a stand-in program in place of Semgrep: exit codes 0, 1, 2, 3 and 7, "2 then 0", "2, 2, 0", "2, 2, 2" and "2 then 1" give the same exit status, number of tries and messages as before the `[[ ]]` change. Exit 2 gives 3 tries; exit 3 gives 1 try and the "NOT findings" message.
- Semgrep exit codes 0, 1, 2 and 7 were seen locally with the pinned version on a made-up rule (earlier tree, not re-run on db54e13; not with the registry packs).
- Files with a syntax error, tested with the pinned Semgrep and a made-up local rule (earlier tree, not re-run on db54e13). A Python file and a JavaScript file with a syntax error each gave exit 3 with `--strict` and exit 0 without it. Two more made-up test folders also gave exit 3 with `--strict`, with about 100% of lines parsed; the saved test does not say what was in them. Without `--strict`, Semgrep only printed a short note about skipped lines. A real finding in the same folder gave exit 1 either way.
- The real scanned folders of `2db3926` with this PR's changes, with the same made-up local rule (not the registry packs). Semgrep read 45 files, reported about 100% of lines parsed, and exited 0 with and without `--strict`. Not re-run on db54e13, but the five folders are identical on `db54e13`: the difference between `2db3926` and `db54e13` in them is empty. So today's files do not trigger exit 3 with that rule. Whether the registry packs read them the same way is not tested.

## Tests NOT run

- The full test suite on this PR at db54e13. (An earlier version of this PR, on 0841f36, ran the full suite: 2426 passed, 115 skipped.)
- Any real GitHub CI run of this workflow.
- Windows and PowerShell.
- Python 3.13: only the lock regeneration ran on 3.13, not the tests.
- Semgrep with the registry packs on `tests/`, on `demo_only/`, or on db54e13. Semgrep at WARNING level.

## Measured vs not

"Re-measured on db54e13" means the check was run again on `db54e13` with this PR's changes. "Not re-run on db54e13" means the result comes from an earlier tree or an earlier version of this PR.

| Claim | Status |
|---|---|
| Patch applies to `db54e13` (`git apply --check`) | Re-measured on db54e13 |
| Focused tests: 130 passed (15 + 63 + 3 + 44 + 5) | Re-measured on db54e13 |
| ruff, mypy (26 files, Linux and Windows), bandit `-ll` | Re-measured on db54e13 |
| gitleaks: no leaks in files and history | Re-measured on db54e13 |
| Lock file: 67 packages, 1130 lines, sha256 `a791abb7e447...` | Re-measured on db54e13 |
| 13 files, 405 lines added, 60 removed in the scanned folders since 0841f36 | Re-measured on db54e13 |
| Scan step logic unchanged by `[[ ]]` (stand-in program, not Semgrep) | Re-measured on db54e13 |
| ERROR-level clean with the registry packs | Only on 0841f36 (lead's run); not re-run on db54e13 |
| Overlapping-runs mutants (2 breakages, each caught) | Not re-run on db54e13 |
| gitleaks-exception mutants (4 breakages, each caught) | Not re-run on db54e13 |
| 24 comment shapes (old test missed 23, new test refuses 24) | Not re-run on db54e13 |
| Real Semgrep exit codes 0, 1, 2, 7 (made-up rule) | Not re-run on db54e13; not with the registry packs |
| Real Semgrep exit 3 for unreadable files (made-up rule) | Not re-run on db54e13; not with the registry packs |
| 45 files read, about 100% parsed, exit 0 with `--strict` (made-up rule) | On 2db3926 only; the folders are identical on db54e13 |
| Lock file rebuilt and identical (`cmp`) | Earlier tree; same sha256 on db54e13 |
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
- **Exit 3** (for example, a file could not be fully read): this is not a finding. Run the scan locally with `--verbose` added. For a syntax error, the log shows a "Syntax error" warning with the file name; for other causes it may not. Fix the syntax error in that file.
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

This PR stays its own PR. It is meant to be merged after PRs #2 to #4, the earlier code and test changes this PR is based on. Among other things, they bring the `tests/` folder to main, where it does not exist yet.

This PR needs them in two ways. First, Semgrep fails if any of the five scanned folders is missing. Second, the gitleaks exception only works with the `cwd=target` change in `tests/test_hygiene.py` from those PRs: it makes gitleaks scan from the repository root.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

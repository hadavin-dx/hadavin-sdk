**What:** a new CI job (`.github/workflows/semgrep.yml`) runs the open-source Semgrep scanner, version 1.185.0, on every pull request to main and every push to main.
**Why:** Semgrep is a code scanner that looks for known risky code patterns; this adds a second opinion next to the checks we already run (ruff, mypy, bandit, gitleaks, CodeQL).
**What it does not do:** it does not scan `tests/` or `demo_only/`, does not look for secrets, reports only the most serious level (ERROR), and is not a required check.

## What the job checks

- It installs Semgrep 1.185.0 from a lock file (`requirements-semgrep.txt`). A lock file lists every package with its exact version and a checksum (a hash). The lock holds 67 packages in 1130 lines.
- It checks the install (`pip check` and `semgrep --version`), so that a broken install is reported as an install problem and not as a finding.
- It scans the folders `src`, `scripts`, `load_tools`, `tools` and `n8n`.
- It uses two rule packs from the public Semgrep registry (the online rule library): `p/python` and `p/javascript`. No other packs.
- It fails the job only on a finding of severity ERROR (the highest level). Findings print in the job log only; nothing is uploaded to GitHub code scanning.
- Options: `--metrics=off` (no usage data sent to Semgrep), `--disable-version-check` (no call to check for a newer Semgrep), `--strict` (a broken rule stops the run instead of being skipped).
- If Semgrep exits with code 2 (registry or network failure, or a folder that does not exist), the job tries again, up to 3 tries, 20 seconds apart. Findings (exit code 1) are never retried.

## What the job does NOT check

- `tests/` and `demo_only/` are not scanned. `tests/` holds planted fake secrets and deliberately unsafe code that other checks must catch. `demo_only/` is fake services and a demo page. **This was decided without a scan result.** Nobody has scanned these two folders with Semgrep.
- `n8n` is in the list but is only nominal. It holds 3 JSON files, no rule pack reads JSON, and JavaScript inside an n8n Code node is not parsed.
- Only severity ERROR. Findings of lower levels (WARNING, INFO) are not reported and were not looked at.
- No other rule packs than `p/python` and `p/javascript`.
- No secrets scan. Secrets stay with gitleaks in `lint.yml`.
- A Python file that Semgrep cannot parse does not fail the job (exit 0 was observed even with `--strict`).
- **The rules change over time.** The registry rules are downloaded fresh at every run and cannot be pinned to a version. So the result can change between two runs with no change in this repository.
- **It is not a required check.** A red Semgrep job does not block a merge, unless the repository owner chooses to make it a required check in the GitHub settings.

## Scan result, exactly as measured

- **ERROR-level clean on the stack head at 0841f36 as of the lead's run.** That run used Semgrep 1.185.0 (container image `semgrep/semgrep:1.185.0`), the packs `p/python` and `p/javascript`, severity ERROR, and the same five folders. It ended with exit code 0 and no finding.
- That run differs from the workflow in three ways. It did not use `--strict` or `--disable-version-check`, and it put the `--config` options in another order. It also used `--quiet`, so the log does not show that both packs were really fetched.
- This PR applies on a later head, `2db3926`. Since 0841f36, 13 files in the scanned folders changed (405 lines added, 60 removed). **The scan was not repeated on 2db3926.**
- **No run of this workflow on GitHub has been seen yet.** The first live CI run on this PR is the real check. The job log prints the Semgrep version and the pack names at the start.
- If the first run fails on a finding that already exists in the code, the plan is: fix the code, or suppress that one finding with its rule id, in a separate change.

## Licence of the rules

- The Semgrep engine is open source (LGPL-2.1). The registry rules are under a separate licence, the Semgrep Rules License v1.0.
- The repository owner gave a written yes for using `p/python` and `p/javascript`, for this repository only. No other pack is covered.
- This repository is public, so the job log is public. The log prints the rule id and rule message of every finding. That is accepted under the owner's yes.
- No copy of any rule is stored in this repository. The licence text itself was not fetched or read for this PR.

## Concurrency (what happens when runs overlap)

- Each branch or pull request has its own group: `semgrep-${{ github.ref }}`.
- In a pull request, a newer push cancels the older, still running Semgrep run.
- A run on a push to main is never cancelled: `cancel-in-progress` is true only for `pull_request` events.
- This is safe only while `github.ref` stays in the group name. A test (`test_semgrep_workflow_never_cancels_a_push_to_main`) pins the whole block and fails if it changes.

## How the lock file was made

- Three tools made the lock files of this repository. `pip-compile` made the dev locks. `uv` 0.11.32 made the coverage lock and the two browser locks. `uv` 0.13.8 made the Semgrep lock.
- The Semgrep lock was made again with uv 0.13.8 and the same arguments. `cmp` found the new file byte-identical to the committed one (same sha256, starting `a791abb7e447`, 1130 lines). Evidence: `semgrep/evidence-sg-17-uv-lock-identical.txt`.
- That re-run used uv installed from PyPI under Python 3.13. The docker command written in `requirements-semgrep.in` was not run.

## Supply chain and permissions

- The install is `python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt`. Every package must match its checksum. Only ready-made wheels are installed (nothing is built from source). Nothing outside the lock is pulled in.
- `pip check` then confirms that no package is missing or in conflict.
- Both Actions (checkout, setup-python) are pinned to a full commit SHA. Checkout keeps no credentials (`persist-credentials: false`).
- Permissions: `contents: read` only. The job uses no repository secret and no token. No Semgrep account is used.
- Timeout: 20 minutes. This is a ceiling, not a measurement: no GitHub run has been timed. Installing from the lock took 17 seconds in one local test.

## Other files in this PR

- `tests/test_nosemgrep_form.py`: every Semgrep suppression comment (`nosemgrep` or the short form `nosem`) must name a dotted rule id, for example `# nosemgrep: python.lang.x.y <reason>`. A bare `nosemgrep` would hide every finding on that line. The test also refuses spellings that Semgrep 1.185.0 was seen to accept as a bare suppression (any case, extra letters, the long s `ſ`).
- `tests/test_gitleaks_semgrep_lock.py`: runs the real gitleaks (the secrets scanner) and checks that the new gitleaks allowance for the lock file is exact. A second part widens each allowance on purpose and fails if the widening goes unnoticed.
- `.gitleaks.toml` and `exceptions.txt`: allowances for the checksum lines of the lock and for the file name `requirements-semgrep.in` (which ends like a host name).
- `.codeant/configuration.json`: CodeAnt (a review service) skips the lock file.
- `docs/tests.md`: a new "Semgrep" section (status of the scan, licence, what is scanned, exit codes, how to run it, how to suppress, how to bump).

## Trade-offs and known gaps

- The gitleaks allowance for checksum lines applies only to the file `requirements-semgrep.txt` in the repository root (`^requirements-semgrep\.txt$`). A copy of that file in a sub-folder is still reported. This was tightened from an earlier, looser pattern.
- CodeAnt skips the lock file, so CodeAnt does not check those 67 packages.
- Dependabot (GitHub's update bot) is set up for GitHub Actions only. It covers none of the lock files, this one included. So nothing checks the 67 Semgrep packages for updates automatically. The repository owner checks by hand, when a Semgrep security advisory appears or about once a quarter.
- The Semgrep lock is for Linux x86_64 and Python 3.12 only (the CI runner).

## Tests run for this PR

- Focused tests on a 2db3926 tree with this patch: **125 passed** (`test_hygiene` with the real gitleaks, `test_nosemgrep_form`, `test_gitleaks_semgrep_lock`, the gitleaks exceptions test).
- Mutants (deliberate breakages) of the real workflow file: `cancel-in-progress: true` made 1 test fail (62 passed); a constant `group: semgrep` made 1 test fail (62 passed).
- Mutants of the gitleaks allowances (left anchor removed, line rule widened, path widened, host-name rule widened): each made the lock test fail. These ran on an earlier version of the patch; the lock test file is unchanged since.
- The old suppression test, run against the new refused shapes, missed 23 of 24 of them. The new test refuses them.
- `git apply --check` on a clean clone of `2db3926`: OK (this PR changes 9 files).
- gitleaks `dir` and `git` scans: no leaks. ruff check and ruff format: clean. mypy (linux and win32): clean, as reported by the builder.
- Semgrep exit codes 0, 1, 2 and 7 were seen locally with the pinned version on a made-up rule.

## Tests NOT run

- The full test suite on this PR at 2db3926. (An earlier version of this patch, on 0841f36, ran the full suite: 2426 passed, 115 skipped.)
- Any real GitHub CI run of this workflow.
- Windows and PowerShell.
- Python 3.13.
- bandit on this version of the patch (no clean bandit output is saved for it).
- Semgrep on `tests/`, `demo_only/`, on 2db3926, or at WARNING level.

## What a reviewer should look at first

- The `concurrency:` block and the scan command in `.github/workflows/semgrep.yml`: does it cancel only pull-request runs, and does it scan exactly what is listed above?
- The two new blocks in `.gitleaks.toml`: are they as narrow as `tests/test_gitleaks_semgrep_lock.py` claims?
- The decision to leave `tests/` and `demo_only/` unscanned, made without a scan result: is that acceptable for now?

## How to run it on your own computer

You need network access to the Semgrep registry, because the rules are downloaded at run time. Docker is not needed. From the repository root, in a Python 3.12 virtual environment on Linux x86_64:

```
python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt
python -m pip check
semgrep scan --metrics=off --disable-version-check --strict --error --severity ERROR --config p/python --config p/javascript src scripts load_tools tools n8n
```

On another system or Python version the lock does not fit. There, use `pip install semgrep==1.185.0` (no checksums), then the same `semgrep scan` command. Exit code 0 means no ERROR finding, 1 means findings, 2 means the registry could not be reached or a folder is missing.

This PR stays its own PR. It is meant to be merged after PRs #2 to #4.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

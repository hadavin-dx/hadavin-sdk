**What:** Semgrep is a code scanner that looks for known risky code patterns. This PR adds a CI job, `.github/workflows/semgrep.yml`, that runs the open-source Semgrep 1.185.0 on every pull request to main and every push to main. It adds a second opinion next to ruff, mypy, bandit, gitleaks and CodeQL.

**What it scans:** the folders `src`, `scripts`, `load_tools`, `tools` and `n8n`, with the registry rule packs `p/python` and `p/javascript`. It fails only on findings of Semgrep's highest level, ERROR. It does not scan `tests/` or `demo_only/` (decided without a scan result) and does not look for secrets (gitleaks does). `n8n` holds only JSON, which no pack reads. It is intended not to be a required check; whether the branch settings agree was not checked.

**Files (9, none under `src/`):** `.codeant/configuration.json`, `.github/workflows/semgrep.yml`, `.gitleaks.toml`, `docs/tests.md`, `exceptions.txt`, `requirements-semgrep.in`, `requirements-semgrep.txt`, `tests/test_gitleaks_semgrep_lock.py`, `tests/test_nosemgrep_form.py`. The diff is the patch with sha256 `7e944af38fa6d5400fd84da34a3ea30ec81e5b147547749495d37635078c0bfb`, cut from main `61ded9e`; `git apply --check` on a clean `61ded9e` is OK.

**How the job works**
- Install from a hash-checked lock file (67 packages, wheels only, no dependencies pulled in), then `pip check` and `semgrep --version`.
- Scan with `--metrics=off --disable-version-check --strict --error --severity ERROR`. Findings print in the job log only; nothing is uploaded.
- Only Semgrep exit code 2 (registry or network trouble, or a missing folder) is retried: up to 3 tries, 20 seconds apart. Findings (exit 1) are never retried. Any other non-zero code fails the job with a "NOT findings" message.
- Permissions: `contents: read` only; no secret or token. Both Actions are pinned to the same full commit ids as `lint.yml`; checkout keeps no credentials. Timeout 20 minutes (a ceiling, not measured).
- A push to main does not cancel a run already running on main; only pull-request runs are cancelled by a newer push. GitHub may still replace a run that is only waiting to start (pending) in the same group. This is from documentation as remembered, NOT measured.

**Other files**
- `tests/test_nosemgrep_form.py`: (1) every Semgrep suppression comment (`nosemgrep` or `nosem`) must name a dotted rule id, because a bare one hides every finding on its line; (2) the workflow is compared with an exact whitelist (triggers, permissions, concurrency, one job on `ubuntu-24.04` with at most 20 minutes, exactly five steps with exactly the expected keys, the two Actions pinned as in `lint.yml`, the install command and the scan command word for word); an expression such as `github.event.` or `github.ref_name` inside a `run:` step and any secret or token reference are refused; (3) the scan step's own `run:` block is executed with a stand-in `semgrep` (8 cases: only exit 2 is retried).
- `tests/test_gitleaks_semgrep_lock.py`: runs the real gitleaks to check that its exceptions for the lock file are narrow, plus a check that the `exceptions.txt` line for OpenTelemetry package names is narrow.
- `.gitleaks.toml` and `exceptions.txt`: three exceptions, all for the lock file or its name: the checksum lines; the file name `requirements-semgrep.in`; and package names that start with `opentelemetry-` (the literal-text scan reports any run of 40 or more letters, digits and dashes).
- `.codeant/configuration.json`: CodeAnt skips the lock file. `docs/tests.md`: a "Semgrep" section (status, licence, scope, exit codes, how to run, how to suppress, how to update).
- The new tests start `git`, gitleaks and `bash` through the existing `_run` helper in `tests/test_hygiene.py`. `bash -e -c` runs the text of the scan step, read from the workflow file in this repository; no text from a scanned file or a user reaches a command line. **No suppression comment was added:** 0 added lines contain `noqa`, `nosec`, `NOSONAR`, `type: ignore`, `pragma`, `pylint: disable` or `fmt: off/skip` (grep of the diff). The word `nosemgrep` appears in 64 added lines (docs, test data, one workflow message); none suppresses a finding.

**Tests run (this PR's own tests only)**
- `tests/test_nosemgrep_form.py`, `tests/test_gitleaks_semgrep_lock.py`, `tests/test_workflow_files_parse.py`, `tests/test_workflow_run_flags.py`: 133 passed, with the real gitleaks 8.30.1 on the path and `DPLD_REQUIRE_SCAN=1`.
- Mutants of the real workflow file: 39 deliberate breakages, each run against the new test file and the previous (blacklist) version of it, the workflow restored `cmp`-identical after each one. All 39 are caught by the new tests. The previous version missed 18 of them: a step-level `if`, a job-level `if: false`, an extra action step, `defaults.run.shell`, a step `shell: sh`, a matrix, `cache: pip`, Python 3.9, a job `env`, a push trigger to another branch, a pull-request trigger to no branch, `install || true`, a step timeout of 1 minute, a `container:`, a `workflow_dispatch` trigger, and others; the full list and per-mutant results are in `evidence-6-workflow-mutants.txt`. The 39 are the changes I and two reviewers thought of: the whitelist catches any change to the checked shape, but it is not a proof that the workflow is safe.
- Syntax errors under `--strict` (real Semgrep 1.185.0, made-up rule, offline): an unclosed call bracket such as `print("hit"` or `eval("hit"` gave exit 3 with `--strict` and exit 0 without; `def f(:` followed by `  pass`, and `function f( {` followed by `}`, gave exit 0 even with `--strict`. So only some syntax errors make the job fail with exit 3. The two older test folders whose cause was unclear both hold a broken `.js` file (`function f( {` plus an unclosed `eval("hit"`).
- A run of Semgrep with a made-up local rule over the five folders of `61ded9e` plus this change: 47 files read, about 100% of lines parsed, exit 0 with and without `--strict`.

**What this PR does NOT prove**
- No run of this workflow on GitHub has been seen. The first live run is the real check. The job log prints the Semgrep version and pack names at the start.
- Semgrep was not run with the registry packs for this PR. The only run with them is the project lead's earlier run on `0841f36` (an earlier commit of the branch, not in main's history because #2 to #4 were squashed into `61ded9e`): no ERROR finding, without `--strict` and with `--quiet`. 25 files in the scanned folders have changed since (912 lines added, 118 removed); the scan was not repeated. If the first run finds something, fix the code or suppress that one finding by rule id in a separate change.
- The registry rules are fetched live and cannot be pinned, so the result can change with no change here.
- The full test suite, Windows and Python 3.13 were not run. The retry test runs only on Linux.
- In a copy of the repository without `demo_only/`, both new test files are skipped as a whole (they import `support`), so none of these checks run there.
- Lint, type, secret-scan and hygiene tools were not run for v10 (GitHub CI runs them on the PR); they were clean on the v9 patch only.
- The licence text of the registry rules (Semgrep Rules License v1.0) was not read. The repository owner has said yes to `p/python` and `p/javascript` for this repository only. The job log of a public repository is public.
- The lock file was rebuilt with uv 0.13.8 and compared byte for byte in an earlier version; not repeated for v10.

**If the job goes red:** exit 1 = findings (fix them, or `# nosemgrep: <rule-id> <reason>`, never a bare `nosemgrep`); exit 2 = re-run later and check the five folders exist; exit 3 = a file Semgrep could not fully read, run locally with `--verbose` (not every syntax error causes it); do not remove `--strict` to turn the job green.

**Run locally** (network needed, Python 3.12, Linux x86_64): `python -m pip install --require-hashes --only-binary=:all: --no-deps -r requirements-semgrep.txt`, then `semgrep scan --metrics=off --disable-version-check --strict --error --severity ERROR --config p/python --config p/javascript src scripts load_tools tools n8n`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36uYfYwuEDby9epxu8

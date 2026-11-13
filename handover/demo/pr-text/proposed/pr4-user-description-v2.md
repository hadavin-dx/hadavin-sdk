## **User description**

### What this part is
This is part 3 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part adds the tests. It also carries every fix made after the three pull requests were opened on 2026-11-12 at 17:37 UTC. Those fixes change files of parts 1 and 2, but they sit on this branch only.

Base: part 2 (`pr-2-demo-folder`). This pull request changes 142 files: 93 under `tests/` and 49 elsewhere.

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. #2 (`pr-1-code`) goes into `main`, #3 into #2's branch, and this one into #3's branch.

The code was split in three to keep each part small for the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically). This third part grew past the planned size because the later fixes were added to it.

The final tree of the stack (this branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: settings that came from `main`, and the fixes below.

Merge as a stack: #2, then #3, then #4. The other way is to retarget a pull request to `main` after the one before it is merged.

Checks, inferred from the workflow files:
* The lint and CodeQL checks are set to run only for pull requests whose base is `main`. So for this pull request GitHub should start only the SonarQube check.
* This branch passes the secret scan and has the tests. Parts 1 and 2 alone fail the secret scan and have no tests; this branch fixes both.

### Changed since this pull request was opened
Opened at 17:37 UTC on 2026-11-12. Times are commit times in UTC.
1. 19:47 and 20:11: two merges bring `main`'s settings down the stack. These are the SonarQube, CodeAnt AI and DeepSource settings and the SonarQube key allowance.
2. Batch 1 (2ce1f98, 20:50): documentation fixes, small portal script fixes, error-handling clean-up in the retry paths, demo-only cosmetics, and a narrower allowance list for gitleaks. Gitleaks is a scanner that looks for passwords and keys in code.
3. Batch 2a (0841f36, 20:53): SonarQube now gets test coverage. `sonar.yml` installs a new lock file and runs the whole test suite with coverage before the scan. A lock file pins exact package versions with checksums.
4. Batch 2 (5947364, 22:20): security fixes suggested by CodeAnt AI, the browser lock file and layout fixes.
5. 22:25 (40d5668): the test stand-in servers for `scripts/n8n_api.py` read the request body before they answer. Stand-in servers are small fake web servers inside the tests. A late body caused a flaky reset on Windows.
6. 22:42 (f5fe824): small security fixes to the export scrubber and to `scripts/n8n_api.py`.
7. Batch 3 (2db3926, 00:41 on 2026-11-13): eight fixes suggested by CodeAnt AI, a stop guard for the tests and hygiene tests for the gitleaks allowance. Hygiene tests check that the allowance stays narrow.

Files by kind (outside `tests/`):
* Core desk code: 16 files under `src/`. See "Core code touched" below.
* Security: `tools/scrub_n8n_export.py` (cleans exported n8n workflows of addresses and keys), `scripts/n8n_api.py`, `scripts/http_guard.py`, `scripts/reset.ps1`, `n8n/proof.json`.
* Secret-scan settings: `.gitleaks.toml` and `exceptions.txt`. The SonarQube project key is now allowed by its exact text. The path rules start at the repository root.
* New lock files `requirements-browser.in`, `requirements-browser.txt` and `requirements-browser-win.txt`. They pin Playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1 and typing-extensions 4.16.0. Playwright is a package that drives a real web browser for tests.
* New lock files `requirements-coverage.in` and `requirements-coverage.txt`. They pin coverage 7.17.2 and pytest-cov 7.1.0, and only the SonarQube job uses them.
* Browser tests no longer need the image library Pillow.
* Workflow `sonar.yml`: it runs on `ubuntu-24.04`, its time limit goes from 20 to 60 minutes, and it runs the tests with coverage. `lint.yml` and `codeql.yml` are unchanged.
* In `sonar.yml` the tests and the scan run in one job. The `SONAR_TOKEN` secret is set only on the scan step. Splitting them into two jobs is an open decision for the owner.
* Settings: `pyproject.toml` (coverage settings and `faulthandler_timeout = 300`), `sonar-project.properties` (coverage report path), `.gitignore`, `.codeant/configuration.json`.
* Demo-only fakes: `demo_only/fake_hubspot.py`, `fake_imap.py`, `fake_model_server.py`, `fake_smtp_tls.py`, `portal_demo.py`, `portal_demo.css`, `portal_demo.js`. The fake CRM now reads a request body before it answers.
* Load tools: `load_tools/catcher.py`, `load_tools/load_driver.py`.
* Documents: `contract.md`, `docs/limits.md`, `docs/n8n-recipe.md`, `docs/portal.md`, `docs/settings.md`, `docs/tests.md`, `versions.md`.

The stop guard is a time limit on stopping each test server. It is a safety net for the tests, not a fix of a hang: no hang was ever shown to come from the desk code. A server that does not stop in 20 seconds (60 for the desk and the fakes) makes its test end in an error. The error prints every thread's stack.

### Core code touched
These change shared desk code under `src/` (16 files) and `contract.md`. The descriptions come from reading the diff against #1.

* `server.py`, step route: when the body is too large (413), the desk now reads and drops it before closing. A body left unread can reset the reply.
* `server.py`, error replies: after an error reply sent once the headers were read, such as 501 for an unknown method, the desk also reads and drops the body.
* `server.py` and `desk.py`: the desk refuses to start with the lead-book name `:memory:` (exit code 4). It refuses before it makes the folder or the lock file.
* The check is a module-level function `book_problem` in `desk.py`, and `Desk` repeats it. `main` calls it through the module, so a test that replaces `server.Desk` cannot remove the check.
* `loader.py`: a new optional interface `KnowsBoundAddress`. When a demo extension has `set_bound_address`, `server.py` now hands it the real address and port after binding. Only `demo_only/portal_demo.py` has it.
* `desk.py`, CRM stage copy: while this lead's earlier copy call is still running, the desk waits before trying again. The wait is about 10, 60, 180 and at most 420 seconds, depending on earlier tries. Such a refusal does not count as a try.
* `desk.py`, CRM stage copy: this call is now exclusive for every CRM, keyed or not. Exclusive means a second call for the same lead does not start while the first one runs.
* `desk.py`: the copy call binds its values with `functools.partial` instead of a `lambda`. A worker that runs late then sends its own row's values.
* `config.py`, `crm_hubspot.py`, `live_claude.py`, `smtp_outbox.py`, `smtp_provider.py`: `except` lists drop types that another listed type already covers. For example `UnicodeError` is a `ValueError`. The new test `tests/test_except_clause_hierarchy.py` checks these error types.
* `portal_api.py`: unused names in one function are renamed.
* `portal/portal.js` and `pages/overview.js`: variables are declared before the functions that read them, and one loop no longer creates a function.
* `pages/log.js`: after "Load more", the log keeps rows that new requests pushed off page one. No row falls between pages.
* Portal styles `app.css`, `pages/leads.css`, `pages/needs.css`, `pages/overview.css`: long names wrap or end in "…". At phone width nothing widens the page.
* These styles use CSS range queries, which are screen-width rules written like `(width > 860px)`. A reviewer's estimate of the minimum browsers is Chrome 104, Firefox 63 and Safari 16.4. This is not in the repository docs, and only Chromium was tested.
* `contract.md`: line 71 names the browser lock files; lines 143 and 277 describe the `:memory:` refusal and when it runs.

### Tests run and not run
All runs were on Linux with Python 3.12, in our own container, on this head (2db3926). None of them is a GitHub check.
* Whole test suite in 10 separate parts (one process per part): 3138 passed, 3 skipped, 0 failed, 0 errors. State shared across test files is not tested this way.
* Whole test suite in one process: [FILL: single-process result]
* ruff (check and format), mypy (Linux and Windows modes) and bandit: no problems. Gitleaks on the files and on the history: no findings.
* The hygiene and gitleaks tests: 59 passed. One restart test, run 5 times: passed each time.
* Browser tests ran with Playwright 1.63.0 and Chromium only.
* Earlier heads of this branch were also run in full, with 0 failures.

The 3 skipped: a file-permission test (the tests ran as root), a load measurement that runs only on request, and a Windows-only reset test.

Not run:
* GitHub's own checks (lint, CodeQL, SonarQube, CodeRabbit) on this head.
* The whole suite on Windows, and the PowerShell scripts.
* Python 3.13 (the Windows lock file targets it).
* A real n8n server, a real CRM or a real mail service.
* Firefox and Safari.
* The SonarQube coverage job (it needs the repository's token).
* Semgrep: it comes in its own pull request after this stack.

On GitHub the lint workflow installs no Playwright, so the browser tests skip there.

### What to look at first
1. The core code touched: `server.py`, `desk.py`, `loader.py`, `contract.md` and the four CSS files.
2. Then `sonar.yml`, the two new lock files and `.gitleaks.toml` with `exceptions.txt`.
3. Then the new tests for each fix, for example `tests/test_codeant_desk.py`, `tests/test_server_stop_guard.py` and `tests/test_gitleaks_exceptions.py`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

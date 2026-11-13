## **User description**

### What this is
This pull request holds the whole demo of a lead desk and replaces #2 and #3. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. It copies leads into a CRM (the customer database of the sales team) and works with n8n (a workflow tool). All data in it is made up.

Branch `pr-3-tests` (2db3926) into `main`: 226 files.

### What is in it, by part
* Desk code (`src/`, 38 files): the desk itself, its web server, the database layer, the CRM, mail and AI adapters, and the portal (the desk's web pages).
* Scripts (`scripts/`, 14 files): start and reset scripts for Linux and Windows, a test feeder, crash and real-service check tools, and `n8n_api.py`.
* Tools (`tools/`, 3 files): the hygiene scan and `scrub_n8n_export.py`, which cleans exported n8n workflows of addresses and keys.
* Load tools (`load_tools/`, 5 files) and n8n workflow files (`n8n/`, 3 files).
* Documents: `contract.md` (the desk's rules in plain text), `versions.md` and 8 files under `docs/`.
* Workflows (`.github/workflows/`): `lint.yml`, `codeql.yml` and `sonar.yml`. SonarQube and CodeQL are two code-quality and code-security scanners that run on GitHub.
* Demo-only fakes (`demo_only/`, 15 files): fake mail, CRM and AI services and the demo controls page. The desk loads them only when it runs with the demo settings.
* Tests (`tests/`, 117 files), including 24 saved sample answers of the desk that the portal tests use.
* Project files: `pyproject.toml`, lock files, and the settings for gitleaks, SonarQube, CodeAnt AI and CodeRabbit. A lock file pins exact package versions with checksums. Gitleaks is a scanner that looks for passwords and keys in code. CodeAnt AI and CodeRabbit are services that review pull requests automatically.

The workflow files set lint and CodeQL to run for pull requests into `main`, and SonarQube for every pull request.

### Fixes added after the first three pull requests
The demo first went up as #2, #3 and #4 on 2026-11-12 at 17:37 UTC. These fixes came after, in commit order (UTC):
* 2ce1f98 (20:50): documentation fixes, small portal script fixes, error-handling clean-up in the retry paths, demo-only cosmetics and a narrower gitleaks allowance list.
* 0841f36 (20:53): SonarQube gets test coverage. `sonar.yml` installs `requirements-coverage.txt` (coverage 7.17.2, pytest-cov 7.1.0) and runs the whole test suite with coverage before the scan.
* 5947364 (22:20): security fixes suggested by CodeAnt AI, layout fixes and the browser lock files. They pin Playwright 1.63.0, a package that drives a real web browser for tests; Pillow is no longer needed.
* 40d5668 (22:25): the test stand-in servers for `scripts/n8n_api.py` read the request body before they answer. Stand-in servers are small fake web servers inside the tests.
* f5fe824 (22:42): small security fixes to the export scrubber and to `scripts/n8n_api.py`.
* 2db3926 (00:41 on 2026-11-13): eight fixes suggested by CodeAnt AI, a stop guard for the tests and hygiene tests that check the gitleaks allowance stays narrow.

The stop guard is a time limit on stopping each test server. A server that does not stop in 20 seconds (60 for the desk and the fakes) makes its test end in an error that prints every thread's stack.

In `sonar.yml` the tests and the scan run in one job. The `SONAR_TOKEN` secret is set only on the scan step. Splitting them into two jobs is still an open owner decision.

### Core code touched
Compared with the first version of this code (pull request #1, branch `initial-code`, closed without merging), 16 files under `src/` and `contract.md` changed. The descriptions come from reading that diff.

* `server.py`, step route: when the body is too large (413), the desk now reads and drops it before closing. The reason given in the code: a close with the body unread can reset the reply.
* `server.py`, error replies: after an error reply sent once the headers were read, such as 501 for an unknown method, the desk also reads and drops the body.
* `server.py` and `desk.py`: the desk refuses to start with the database name `:memory:` (exit code 4). That name would give each thread its own empty database. It refuses before it makes the folder or the lock file.
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
All runs below were on this head (2db3926). None of them is a GitHub check.

On Linux with Python 3.12, in our own container:
* Whole test suite in 10 separate parts (one process per part): 3138 passed, 3 skipped, 0 failed, 0 errors. State shared across test files is not tested this way.
* Whole test suite in one process: 3138 passed, 3 skipped, 0 failed in 20 min 18 s.
* ruff (check and format), mypy (Linux and Windows modes) and bandit: no problems. Gitleaks on the files and on the history: no findings.
* The hygiene and gitleaks tests: 59 passed. One restart test, run 5 times: passed each time.
* Browser tests ran with Playwright 1.63.0 and Chromium only.

The 3 skipped on Linux: a file-permission test (the tests ran as root), a load measurement that runs only on request, and a Windows-only reset test.

On Windows: The whole suite was run once on Windows by the maintainer on pr-3-tests 2db3926: 3096 passed, 45 skipped, 0 failed (22 min 30 s). The skips: 24 gitleaks-exception tests and 4 hygiene tests (no gitleaks program on that machine), 3 reset-script tests, 2 each in test_portal_demo (symbolic-link privilege error), test_portal_api, test_model_stamp_and_reaper, test_desk_http_edge_cases and test_desk_edge_cases, and 1 each in test_server_hardening (a measurement run), test_reset_ps1_links, test_n8n_api_url and test_mode_safety.

Not run in the runs above:
* GitHub's own checks (lint, CodeQL, SonarQube, and CodeRabbit, an automatic code-review tool) on this head.
* A real n8n server, a real CRM or a real mail service.
* Firefox and Safari.
* The SonarQube coverage job (it needs the repository's token).
* Semgrep (a code scanner).

On GitHub the lint workflow installs no Playwright, so the browser tests skip there.

### What to look at first
1. The core code changes above: `server.py`, `desk.py`, `loader.py`, `contract.md` and the four CSS files.
2. Then `sonar.yml`, the lock files and `.gitleaks.toml` with `exceptions.txt`.
3. Then the tests for each fix, for example `tests/test_codeant_desk.py`, `tests/test_server_stop_guard.py` and `tests/test_gitleaks_exceptions.py`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

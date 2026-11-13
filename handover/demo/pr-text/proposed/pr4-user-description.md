<!-- D-PR proposal for PR #4 (head pr-3-tests 2db3926, base pr-2-demo-folder). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stays. Every fact is in VERIFY.md. [UNVERIFIED] = the lead resolves or removes it. [IN PROGRESS] = the lead updates it when the run ends. -->
## **User description**

### What this part is
This is part 3 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part adds the tests. It also carries every fix made after the three pull requests were opened on 2026-11-12 at 17:37 UTC. Those fixes change files of parts 1 and 2, but they sit on this branch only.

Base: part 2 (`pr-2-demo-folder`). This pull request now changes 142 files: 93 under `tests/` and 49 elsewhere.

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. #2 (`pr-1-code`) goes into `main`, #3 into #2's branch, and this one into #3's branch.

The code was split in three because of a limit of the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically). Part 3 has since grown to 142 files. Whether CodeAnt AI still reviews all of them: [UNVERIFIED].

The final tree of the stack (this branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: the quality-tool settings that came from `main`, and the fixes listed below.

Which checks GitHub starts, read from the workflow files:
* The lint and CodeQL checks run only for pull requests whose base is `main`. This pull request's base is part 2, so GitHub starts only the SonarQube check here.
* Run alone on my computer, parts 1 and 2 fail the secret scan and have no tests. These are local results, not GitHub's. This branch passes both.

Questions for the owner before any merge (I did not check these):
* Does `main` have branch protection, and which checks must pass? [UNVERIFIED]
* After #2 is merged, will #3 and #4 be retargeted to `main`? Does lint then start without a new push? [UNVERIFIED]

### Changed since this pull request was opened
Opened at 17:37 UTC on 2026-11-12. Commit times are in UTC.
1. 19:47 and 20:11: two merges bring `main`'s quality-tool settings down the stack (SonarQube, CodeAnt AI and DeepSource settings, and the SonarQube key allowance for the secret scan).
2. Batch 1 (2ce1f98, 20:50): documentation fixes, small portal script fixes, error-handling clean-up in the retry paths, demo-only cosmetics, and a narrower allowance list for gitleaks. Gitleaks is a scanner that looks for passwords and keys in code.
3. Batch 2a (0841f36, 20:53): SonarQube now gets test coverage. `sonar.yml` installs a new lock file and runs the whole test suite with coverage before the scan. A lock file pins exact package versions with checksums.
4. Batch 2 (5947364, 22:20): the CodeAnt AI security set and the browser lock. Details are under "Files by kind" below.
5. 22:25 (40d5668): the test stand-in servers for `scripts/n8n_api.py` read the request body before they answer. A late body caused a flaky reset on Windows.
6. 22:42 (f5fe824): small security fixes to the export scrubber and to `scripts/n8n_api.py`.
7. Batch 3 (2db3926, 00:41 on 2026-11-13): the CodeAnt AI runtime set (eight patches), a test-side stop guard and hygiene tests for the gitleaks allowance.

Files by kind (outside `tests/`):
* Core desk code under `src/`: see "Core code touched" below.
* Security: `tools/scrub_n8n_export.py` (cleans exported n8n workflows of addresses and keys), `scripts/n8n_api.py`, `scripts/http_guard.py`, `scripts/reset.ps1`, `n8n/proof.json`.
* Secret-scan settings: `.gitleaks.toml` and `exceptions.txt`. The SonarQube project key is now allowed by its exact text. The path rules start at the repository root.
* New lock files: `requirements-browser.in`, `requirements-browser.txt` and `requirements-browser-win.txt` pin Playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1 and typing-extensions 4.16.0. Playwright is a package that drives a real web browser for tests.
* New lock files: `requirements-coverage.in` and `requirements-coverage.txt` pin coverage 7.17.2 and pytest-cov 7.1.0. They are used only by the SonarQube job.
* Browser tests no longer need the image library Pillow.
* Workflow: `sonar.yml` runs on `ubuntu-24.04`, its time limit goes from 20 to 60 minutes, and it runs the tests with coverage. `lint.yml` and `codeql.yml` are unchanged.
* Settings: `pyproject.toml` (coverage settings; `faulthandler_timeout = 300`), `sonar-project.properties` (coverage report path), `.gitignore`, `.codeant/configuration.json`.
* Demo-only fakes: `demo_only/fake_hubspot.py`, `fake_imap.py`, `fake_model_server.py`, `fake_smtp_tls.py`, `portal_demo.py`, `portal_demo.css`, `portal_demo.js`. The fake CRM now reads a request body before it answers.
* Load tools: `load_tools/catcher.py`, `load_tools/load_driver.py`.
* Documents: `contract.md`, `docs/limits.md`, `docs/n8n-recipe.md`, `docs/portal.md`, `docs/settings.md`, `docs/tests.md`, `versions.md`.

The stop guard is a safety net for the tests, not a fix of a hang. No hang was ever shown to come from the desk code. A test server that does not stop within 20 seconds (60 for the desk and the fakes) is reported as an error of that test, with every thread's stack printed.

### Core code touched
These change shared desk code under `src/` and `contract.md`. Each sentence comes from the diff against #1.

Approved by the project lead on condition it is named here:
* `src/lead_desk/server.py`: the desk now reads and drops the request body after two refusals. One is 413 (body too large) on the step route. The other is an error reply sent after the headers were read, such as 501 for an unknown method. A body left unread can reset the reply.
* `src/lead_desk/server.py` and `src/lead_desk/desk.py`: the desk refuses to start with the lead-book name `:memory:` (exit code 4). It refuses before it makes the folder or the lock file. The check is a module-level function `book_problem` in `desk.py`. `main` calls it by the module, so a test that replaces `server.Desk` cannot remove the check. `Desk` repeats the check.
* `src/lead_desk/loader.py`: a new optional interface `KnowsBoundAddress`. This is not behaviour-free: when a demo extension has `set_bound_address`, `server.py` now hands it the real address and port after binding. Only `demo_only/portal_demo.py` has it.
* `contract.md` lines 143 and 277: they describe the `:memory:` refusal and when it runs.
* Portal styles `src/lead_desk/portal/app.css`, `pages/leads.css`, `pages/needs.css`, `pages/overview.css`: long names wrap or are cut with "…", and at phone width nothing widens the page.
* These styles use CSS range queries such as `(width > 860px)`. The recommended minimum browsers for them are Chrome 104, Firefox 63 and Safari 16.4. Only Chromium was tested.

Applied by the project lead after review, but not on the lead's list of approved core touches. Lead: please confirm or approve each one. [UNVERIFIED: approval]
* `src/lead_desk/desk.py`: when this lead's earlier CRM copy call is still running, the desk now waits 10, 60, 180, then 420 seconds, longer after each refusal. Such a refusal does not count as a try. The copy call is now always exclusive.
* `src/lead_desk/desk.py`: the CRM copy call binds its values with `functools.partial` instead of a `lambda`. A late worker then sends its own row's values.
* `config.py`, `crm_hubspot.py`, `live_claude.py`, `smtp_outbox.py`, `smtp_provider.py`: `except` lists drop types already covered by another listed type, for example `UnicodeError`, which is a `ValueError`. The intent is no behaviour change. A new test, `tests/test_except_clause_hierarchy.py`, checks the error hierarchy (49 cases).
* `portal_api.py`: unused names in one function are renamed. Nothing else changes.
* `portal/portal.js` and `pages/overview.js`: variables are declared before the functions that read them, and one loop no longer creates a function.
* `pages/log.js`: after "Load more", the log keeps rows that new requests pushed off page one, so no row falls between pages.
* `contract.md` line 71: it names the new browser lock files.

### Tests run and not run
All runs below were on Linux with Python 3.12, in our own container. None of them is a GitHub check.
* On this head (2db3926), run by me: ruff 0.17.4 (check and format), mypy 2.4.1 (Linux and Windows modes), bandit and gitleaks 8.30.1 (files and history) all report no problems.
* Full test suite on this head, in 10 separate parts (separate processes): 3138 passed, 3 skipped, 0 failed. State shared across test files was not exercised.
* One full run of this head in a single process, which the lead asked for: [IN PROGRESS] not done at the time of writing.
* On f5fe824, the head before Batch 3: 2988 passed, 6 skipped, 0 failed in one process. 3 gitleaks tests were skipped because the scanner was not installed for that run.
* On f5fe824 plus the Batch 3 patches except the hygiene tests: 3094 passed, 3 skipped, 0 failed, in 10 separate parts. State shared across test files was not exercised.
* The lead's own run on Windows after Batch 3: "252 passed / 29 skipped on Windows (skips: POSIX signal and gitleaks-binary tests)". This is part of the suite, not all of it.
* Browser tests ran in the parts above with Playwright 1.63.0 and Chromium only.

Not run:
* GitHub's own checks (lint, CodeQL, SonarQube, CodeRabbit) on these heads; the lead reads them on GitHub.
* The whole suite on Windows, and the PowerShell scripts.
* Python 3.13 (the Windows lock file targets it).
* A real n8n server, a real CRM or a real mail service.
* Firefox and Safari.
* The SonarQube coverage job (it needs the repository's token).
* The Semgrep check: it comes in its own pull request after this stack.

Skips on Linux: one file-permission test (we run as root), the load measurement (runs only when asked) and one Windows-only reset test. The lint workflow installs no Playwright, so on GitHub the browser tests skip.

### What to look at first
1. The core code touched: `server.py`, `desk.py`, `loader.py`, `contract.md` and the four CSS files.
2. Then `sonar.yml`, the two new lock files and `.gitleaks.toml` with `exceptions.txt`.
3. Then the new tests for each fix, for example `tests/test_codeant_desk.py`, `tests/test_server_stop_guard.py` and `tests/test_gitleaks_exceptions.py`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

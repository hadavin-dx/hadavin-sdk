## **User description**

### What this part is
This is part 2 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part holds the `demo_only/` folder: fake mail, CRM and AI services and the demo controls page. It also holds the portal fixtures: 24 saved sample answers of the desk (JSON files) that the portal tests use. It changes 39 files. Base: part 1 (`pr-1-code`).

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. #2 (`pr-1-code`) goes into `main`, this one (#3) into #2's branch, and #4 (`pr-3-tests`) into this branch.

The code was split in three to keep each part small for the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically). The third part later grew past the planned size, because the later fixes were added to it.

The final tree of the stack (#4's branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: settings that came from `main`, and the fixes listed in #4.

Merge as a stack: #2, then #3, then #4. The other way is to retarget a pull request to `main` after the one before it is merged.

Checks, inferred from the workflow files:
* The lint and CodeQL checks are set to run only for pull requests whose base is `main`. This pull request's base is part 1, so GitHub should start only the SonarQube check here.

Local results for this branch alone (our own container, not GitHub):
* The secret scan fails. Gitleaks, a scanner that looks for passwords and keys in code, finds 1 item in the files: the SonarQube project key, a public name, not a secret. #4 fixes the rule that allows it.
* On the history, gitleaks finds 325 items. The scan reads every branch of the clone. With this branch's older settings it flags the checksum lines of lock files added later in #4, some file names that look like host names, and the SonarQube key.
* `tests/` holds only the portal fixtures here, so the test step finds no tests. The tests arrive in #4.

### Changed since this pull request was opened
Opened at 17:37 UTC on 2026-11-12. The files this pull request shows have not changed since then. Two merges (19:47 and 20:11 UTC) brought part 1's changes into this branch.

Every later fix to files of this part sits on #4's branch, not here. The files of this part that #4 changes:
* `demo_only/fake_hubspot.py` (the fake CRM now reads a request body before it answers), `fake_imap.py`, `fake_model_server.py`, `fake_smtp_tls.py`.
* `demo_only/portal_demo.py`, `portal_demo.css`, `portal_demo.js` (the demo controls page).

### Core code touched
This pull request has no file under `src/`, the core desk code. #4 touches `src/`; each change is named there.

### Tests run and not run
* On this head (f31e261): gitleaks results as above. ruff and mypy pass. There are no test files here.
* The full test results are on #4's branch, where the tests are.

Not run here: GitHub's own checks, Windows and PowerShell, Python 3.13, a real n8n server.

### What to look at first
1. `demo_only/fakes_server.py` and the fake services it starts.
2. `demo_only/portal_demo.py`: the demo controls page.
3. That `demo_only/` stays out of the core: the desk loads it only when it runs with the demo settings.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

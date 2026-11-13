<!-- D-PR proposal for PR #3 (head pr-2-demo-folder f31e261, base pr-1-code). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stays. Every fact is in VERIFY.md. [UNVERIFIED] = the lead resolves or removes it. -->
## **User description**

### What this part is
This is part 2 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part holds the `demo_only/` folder: fake mail, CRM and AI services and the demo controls page. It also holds the portal fixtures: 24 saved sample answers of the desk (JSON files) that the portal tests use. It changes 39 files. Base: part 1 (`pr-1-code`).

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. #2 (`pr-1-code`) goes into `main`, this one (#3) into #2's branch, and #4 (`pr-3-tests`) into this branch.

The code was split in three because of a limit of the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically).

The final tree of the stack (#4's branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: the quality-tool settings that came from `main`, and the fixes listed in #4.

Which checks GitHub starts, read from the workflow files:
* The lint and CodeQL checks run only for pull requests whose base is `main`. This pull request's base is part 1, so GitHub starts only the SonarQube check here.
* Run alone on my computer, this branch fails the secret scan. Gitleaks (a scanner that looks for passwords and keys in code) finds 1 item in the files and 325 in the history. These are local results, not GitHub's.
* The 1 item is the SonarQube project key in `sonar-project.properties`, a public name, not a secret. #4 fixes the allowance rule for it.
* `tests/` holds only the portal fixtures here, so the test step finds no tests. The tests arrive in #4.

Questions for the owner before any merge (I did not check these):
* Does `main` have branch protection, and which checks must pass? [UNVERIFIED]
* After #2 is merged, will this pull request be retargeted to `main`? Does lint then start without a new push? [UNVERIFIED]

### Changed since this pull request was opened
Opened at 17:37 UTC on 2026-11-12. The files this pull request shows have not changed since then. Two merges (19:47 and 20:11 UTC) brought part 1's changes into this branch.

Every later fix to files of this part sits on #4's branch, not here. See #4 for the full list. The files of this part that #4 changes:
* `demo_only/fake_hubspot.py` (the fake CRM now reads a request body before it answers), `fake_imap.py`, `fake_model_server.py`, `fake_smtp_tls.py`.
* `demo_only/portal_demo.py`, `portal_demo.css`, `portal_demo.js` (the demo controls page).

### Core code touched
None in this pull request: `demo_only/` is demo code, not the core desk. The core changes made later are in #4, each named there.

### Tests run and not run
* On this head (f31e261), run by me on Linux: gitleaks 8.30.1 reports 1 finding in the files and 325 in the history. There are no test files here.
* An earlier run on this head, in our own container: ruff and mypy pass.
* The full test results are on #4's branch, where the tests are. They are listed in #4.

Not run here: GitHub's own checks (the lead reads them on GitHub), Windows and PowerShell, Python 3.13, a real n8n server.

### What to look at first
1. `demo_only/fakes_server.py` and the fake services it starts.
2. `demo_only/portal_demo.py`: the demo controls page.
3. That `demo_only/` stays out of the core: the desk loads it only when it runs with the demo settings.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

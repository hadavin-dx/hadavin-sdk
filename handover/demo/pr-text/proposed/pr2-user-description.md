<!-- D-PR proposal for PR #2 (head pr-1-code d23cf8f, base main). Replaces ONLY the "User description" section; the CodeAnt-AI section below it stays. Every fact is in VERIFY.md. [UNVERIFIED] = the lead resolves or removes it. -->
## **User description**

### What this part is
This is part 1 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part holds the desk code (`src/`), the scripts, the documents, the workflows and the project files. It changes 86 files. Base: `main`.

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. This one (#2, `pr-1-code`) goes into `main`. #3 (`pr-2-demo-folder`) goes into this branch, and #4 (`pr-3-tests`) into #3's branch.

The code was split in three because of a limit of the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically).

The final tree of the stack (#4's branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: the quality-tool settings that came from `main`, and the fixes listed in #4.

Which checks GitHub starts, read from the workflow files:
* The lint and CodeQL checks run only for pull requests whose base is `main`. This is the only one of the three with base `main`, so it starts lint, CodeQL and SonarQube. #3 and #4 start only SonarQube.
* Run alone on my computer, this branch fails the secret scan. Gitleaks (a scanner that looks for passwords and keys in code) finds 1 item in the files and 325 in the history. These are local results, not GitHub's.
* The 1 item is the SonarQube project key in `sonar-project.properties`. It is a public name, not a secret. This branch's allowance rule for it does not match; #4 fixes the rule.
* This branch has no `tests/` folder, so the test step finds no tests. The tests arrive in #4.

Questions for the owner before any merge (I did not check these):
* Does `main` have branch protection, and which checks must pass? [UNVERIFIED]
* If GitHub's lint check on #2 fails like my local run, how should the stack be merged? One option is to retarget #4 to `main`. [UNVERIFIED]

### Changed since this pull request was opened
Opened at 17:36 UTC on 2026-11-12. Between 19:46 and 20:11 UTC, three files of this pull request changed: `.gitleaks.toml`, `exceptions.txt` and `docs/tests.md`. They allow the SonarQube project key and describe it. `main`'s quality-tool settings were also merged in.

Every later fix to files of this part sits on #4's branch, not here. See #4 for the full list. The files of this part that #4 changes:
* Desk code: `src/lead_desk/server.py`, `desk.py`, `loader.py`, `config.py`, `crm_hubspot.py`, `live_claude.py`, `portal_api.py`, `smtp_outbox.py`, `smtp_provider.py`.
* Portal: `src/lead_desk/portal/app.css`, `portal.js`, `pages/leads.css`, `pages/needs.css`, `pages/overview.css`, `pages/overview.js`, `pages/log.js`.
* Security and scripts: `tools/scrub_n8n_export.py`, `scripts/n8n_api.py`, `scripts/http_guard.py`, `scripts/reset.ps1`, `n8n/proof.json`.
* Load tools: `load_tools/catcher.py`, `load_tools/load_driver.py`.
* Settings: `.gitleaks.toml`, `exceptions.txt`, `pyproject.toml`, `.gitignore`.
* Documents: `contract.md`, `docs/limits.md`, `docs/n8n-recipe.md`, `docs/portal.md`, `docs/settings.md`, `docs/tests.md`, `versions.md`.

### Core code touched
This pull request is the core desk code itself. The later changes to it are in #4, each named there in one sentence.

### Tests run and not run
* On this head (d23cf8f), run by me on Linux: gitleaks 8.30.1 reports 1 finding in the files and 325 in the history. There are no test files here.
* An earlier run on this head, in our own container: ruff and mypy pass.
* The full test results are on #4's branch, where the tests are. They are listed in #4.

Not run here: GitHub's own checks (the lead reads them on GitHub), Windows and PowerShell, Python 3.13, a real n8n server.

### What to look at first
1. The desk code in `src/lead_desk/`, mainly `desk.py` and `server.py`.
2. `contract.md`: the desk's rules in plain text.
3. The workflows in `.github/workflows/` and `.gitleaks.toml`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

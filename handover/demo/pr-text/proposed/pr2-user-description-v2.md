## **User description**

### What this part is
This is part 1 of 3 of the demo of a lead desk. A lead desk is a small program that receives sales leads, stops duplicate leads and sends follow-up mail. All data in it is made up.

This part holds the desk code (`src/`), the scripts, the documents, the workflows and the project files. It changes 86 files. Base: `main`.

### The stack and merge order
The three pull requests are a stack: each branch is built on the one before. This one (#2, `pr-1-code`) goes into `main`. #3 (`pr-2-demo-folder`) goes into this branch, and #4 (`pr-3-tests`) into #3's branch.

The code was split in three to keep each part small for the free code-review tool, CodeAnt AI (a service that reviews pull requests automatically). The third part later grew past the planned size, because the later fixes were added to it.

The final tree of the stack (#4's branch, 2db3926) is no longer the tree of the earlier pull request #1. #1 (branch `initial-code`, 43110e7) was closed without merging. The two trees differ in 95 files: settings that came from `main`, and the fixes listed in #4.

Merge as a stack: #2, then #3, then #4. The other way is to retarget a pull request to `main` after the one before it is merged.

Checks, inferred from the workflow files:
* The lint and CodeQL checks are set to run only for pull requests whose base is `main`. This is the only one of the three with base `main`, so it should start lint, CodeQL and SonarQube.

Local results for this branch alone (our own container, not GitHub):
* The secret scan fails. Gitleaks, a scanner that looks for passwords and keys in code, finds 1 item in the files.
* The 1 item is the SonarQube project key in `sonar-project.properties`. It is a public name, not a secret. This branch's rule that allows it does not match; #4 fixes the rule.
* On the history, gitleaks finds 325 items. The scan reads every branch of the clone. With this branch's older settings it flags the checksum lines of lock files added later in #4, some file names that look like host names, and the SonarQube key.
* There is no `tests/` folder, so the test step finds no tests. The tests arrive in #4.

### Changed since this pull request was opened
Opened at 17:36 UTC on 2026-11-12. Between 19:46 and 20:11 UTC, three files of this pull request changed: `.gitleaks.toml`, `exceptions.txt` and `docs/tests.md`. They allow and describe the SonarQube project key. `main`'s settings were also merged in.

Every later fix to files of this part sits on #4's branch, not here. #4 changes 16 desk files under `src/`, the security scripts, the load tools, the scan settings and seven documents of this part. #4 lists them all, with a sentence for each change to the desk code.

### Core code touched
This pull request is the core desk code itself. The later changes to it are in #4.

### Tests run and not run
* On this head (d23cf8f): gitleaks results as above. ruff and mypy pass. There are no test files here.
* The full test results are on #4's branch, where the tests are.

Not run here: GitHub's own checks, Windows and PowerShell, Python 3.13, a real n8n server.

### What to look at first
1. The desk code in `src/lead_desk/`, mainly `desk.py` and `server.py`.
2. `contract.md`: the desk's rules in plain text.
3. The workflows in `.github/workflows/` and `.gitleaks.toml`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

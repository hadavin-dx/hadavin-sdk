# PR stack decision: A (one pull request) or B (merge the stack in order)

Repository: hadavin-dx/duplicate-proof-lead-desk-n8n (public). Read-only work: nothing was pushed, commented, edited or merged.
Data fetched 2026-11-13 from the public GitHub API (no token: the session's GH_TOKEN is invalid) and a read-only clone at /tmp/work/ab-base.
Labels: **MEASURED** = read from the API, a git command or a file (evidence file named); **INFERRED** = my reading, not checked on GitHub.
Draft by a drafter, not an EGM review: the EGM review of this paper is still to be done by the lead (rule 13). The studio bible (RULES.md) is not on this machine, so no R-numbers are cited.

The two options:
- **A**: change the base branch of #4 (`pr-3-tests`, which holds the whole tree) to `main`, and close #2 and #3 as replaced by #4.
- **B**: keep the stack: merge #2 into `main`, then point #3 and then #4 at `main` and merge each.

## 0. Read first: one blocker that applies to both options (MEASURED)

**The SonarQube workflow file in the final tree is broken YAML, so SonarQube has not run on #4 since commit 0841f36.**
`.github/workflows/sonar.yml` on `pr-3-tests` line 45 is `run: python -m pip install --require-hashes --only-binary=:all: -r ...`; the unquoted `: ` after `:all:` makes the YAML parser stop ("mapping values are not allowed here", line 45 column 71). The same file on `main` parses. (evidence-ab-sonar-yaml.txt)
On GitHub this shows as 5 failed runs named `.github/workflows/sonar.yml` with **0 jobs** for the pushes 0841f36, 5947364, 40d5668, f5fe824 and 2db3926, and no SonarQube pull request run after 2ce1f98; the SonarQube check suite on 2db3926 is `queued`, with 0 check runs (evidence-ab-checks.txt, evidence-ab-sonar-run.txt).
So the statement "SonarQube runs for every PR" is false for #4 today. Under A, the retargeted #4 would have no SonarQube check; under A or B, the merge would put the broken file on `main` and stop the SonarQube push scan there too.
The local green runs do not test workflow files, so they could not catch this. The fix is to put that one `run:` line in quotes, or write it as a block (`run: |`). It needs a push to `pr-3-tests`, and that is the lead's call. I did not push.

## 1. What GitHub would show

| | A: #4 against `main` | B: #2, then #3, then #4 |
|---|---|---|
| Files and lines (MEASURED, evidence-ab-diffstat.txt) | `git diff --stat origin/main...origin/pr-3-tests`: **226 files, +58211 / -4**, 17 commits | #2: 86 files +19298. #3 against `main` after #2 is merged: 39 files (its API count). #4: **142 files** +34370 / -164 |
| File limit of the review bots (MEASURED, from bot comments) | CodeRabbit (free plan): "**limit of 100**" files (comment 6830154982 on #1, which had 198 files). CodeAnt: "this PR changes more than 100 files" → **skips by default**, can be forced with `@codeant-ai : review` (comment 6837514351 on #4). The PR bodies say "100 files or fewer (a limit of the free code-review tool)" and do not name the tool. 226 is over both limits. | #2 (86) and #3 (39) are under 100. **#4 (142) is already over 100**: CodeAnt reviewed #4 at b29bb1f and 2ce1f98, then skipped it at 22:20 (comment 6837514351). So the split no longer gets #4 a bot review either. |
| CodeRabbit | It skipped all 4 PRs (check run `skipped` on every head). On #2 (base `main`) its reason: "fewer than 10 stars"; on #3 and #4: base is not `main` (`.coderabbit.yaml` `base_branches: [main]`). It would skip 226 files anyway. | Same: no CodeRabbit review on any part. |
| Workflows that start (MEASURED: file text; event behaviour INFERRED) | lint.yml and codeql.yml: `pull_request: branches: [main]`, no `types:` → they would apply once #4's base is `main`. sonar.yml: `types: [opened, synchronize, reopened]`, any base, skipped for forks and Dependabot (`if:` line 185); **broken file, see 0**. INFERRED, from GitHub's documentation and not checked here: a base-branch change is an `edited` event, which neither list includes, so **a new push (or closing and reopening) may be needed** before lint and CodeQL run. The sonar.yml fix push would do it. | Lint and CodeQL run on whichever part currently has base `main`. Same `edited` question at each retarget. |
| Does the whole tree pass? | **Measured locally only** (lead's figures): chunked full run on 2db3926: 3138 passed, 3 skipped, 0 failed; the maintainer's Windows run without chunks: 3096 passed, 45 skipped, 0 failed; a single-process Linux run had not finished when I wrote this. **Not measured: real GitHub CI on 2db3926** (lint has never run on it). Nearest real run: lint passed on the earlier full tree 43110e7 (#1), tests step **958 s** on ubuntu-24.04 (run 43269123651); that tree differs from 2db3926 in 95 files. | #2 on GitHub (MEASURED, run 43297870133): lint **failed at the gitleaks step**, and every later step was skipped, tests included. SonarQube quality gate on #2: failed (0.0% coverage on new code). DeepSource grade C. Locally (MERGE-READINESS-2-4.md lines 7 and 43): gitleaks finds 1 problem in the files and 325 in the history, and pytest exits 5 because #2 has no tests. #3 is the same, and red as well. |

## 2. What A loses, and how to carry it over

Counts (MEASURED, evidence-ab-api-counts.txt, evidence-ab-api-summary.txt, evidence-ab-findings-breakdown.txt):

| PR | inline review comments | reviews | conversation comments | humans |
|---|---|---|---|---|
| #1 (closed) | 2 (CodeQL) | 2 | 5 | 2 conversation comments by the maintainer (a CodeRabbit command and the "split into three" note); no human review |
| #2 | 22: CodeAnt 12 (3 Critical, 9 Major), DeepSource 9 (3 major, 6 minor), CodeQL 1 | 11 | 5 (Sonar gate failed, DeepSource C) | none |
| #3 | 21: CodeAnt 2 (1 Critical, 1 Major), DeepSource 19 (8 major, 11 minor) | 2 | 6, including CodeAnt "Nitpicks" with **14** suggestions | none |
| #4 | 216: CodeAnt 3 Major, DeepSource 213 (42 critical, 94 major, 77 minor) | 12 | 7, including CodeAnt Nitpicks with **16** suggestions | none |

- **No human review thread exists on any of the four pull requests.** Every inline comment is from a bot, and every comment is a thread starter (0 replies).
- Resolved or not: **not readable**. The REST API does not report it; the GraphQL API needs a token. "Outdated" (position null): **0** on every PR.
- Under A, **#4 keeps its own 216 comments**: it is the same pull request, only its base changes (INFERRED: comments on lines still in the diff stay attached; not tested). **What A really loses is #2 and #3**: 43 inline findings, 14 nitpicks, plus 11 conversation comments. Closed pull requests stay readable.
- Are those 43 still in the final tree 2db3926? I compared the exact line text at the commit the bot reviewed (MEASURED, evidence-ab-checklist-stats.txt). #2: 10 at the same line, 3 moved, 9 changed. #3: 9 at the same line, 11 moved, 1 changed. Of the 4 CodeAnt Critical findings, 3 still have their line text in the final tree (n8n_api.py:32 is now at 131, desk.py:397 at 416, portal_demo.py:414 at 423), and 1 is changed (reset.ps1:20). A line that is still there does not prove the finding is still open: the fix may sit elsewhere. A "moved" match on a common line can also be a false match.

How to carry each kind over:

| Kind | Way |
|---|---|
| CodeAnt (inline and nitpicks) on #2 and #3 | Copy them into #4's description as a checklist that links to the closed PRs; that list is **CARRY-OVER-CHECKLIST.md** (291 rows, one per inline comment plus 30 nitpicks). A fresh CodeAnt review of 226 files needs the `@codeant-ai : review` command (posting it is the lead's call; its own warning is that reviews this large give duplicate findings). |
| DeepSource | It reviewed #4 at 142 files, so it is expected to review again after the retarget. Whether it handles 226 files was not measured. Its findings on #2 and #3 are in the checklist as well. |
| SonarQube | It re-analyses the pull request on its own once sonar.yml is fixed (see 0). Nothing to copy: its #2 and #3 comments are only gate summaries. |
| CodeQL | Its 2 alerts (#1) and 1 alert (#2) are code-scanning alerts in the Security tab, which belong to the repository, not to a pull request. CodeQL re-runs on #4 once its base is `main`. |
| CodeRabbit | Nothing to carry: it reviewed nothing. The paid plan is the only route at 226 files (spend: owner's decision). |
| Human threads | None exist. |

## 3. What B costs (MEASURED unless marked)

- **`main` would hold code that fails its own checks.** On GitHub, lint on #2 fails at gitleaks and never reaches the tests (run 43297870133). After the merge, the push run on `main` would fail the same way (INFERRED: same tree, same file). `main` stays red until #4 lands.
- Branch protection: `GET /branches/main` returns `protected: false`, and both `GET /rulesets` and `GET /rules/branches/main` return `[]`. These are unauthenticated reads: settings that only an admin token can see were not read.
- #3 against `main` would be red as well (gitleaks 1 finding, no tests). #4 at 142 files gets no CodeAnt or CodeRabbit review, so B's last step gets no bot review either (see 1).
- Each retarget may need a new push before lint and CodeQL run (INFERRED, not verified).
- History: 3 merges against 1. With merge commits, `main` gets 3 merge commits plus the 17 branch commits; with squash, 3 commits against 1.
- B's only extra benefit: #2's and #3's 43 findings stay attached to merged pull requests. That is worth little, because no human thread exists.

## 4. Should CI install Playwright, Chromium and gitleaks? (facts, then a recommendation)

Facts (MEASURED, from the files): lint.yml installs only `requirements-dev.txt` (line 105). It installs gitleaks, checks its checksum and sets `DPLD_REQUIRE_SCAN=1`, so the tests fail if gitleaks is missing (lines 90 to 102 and 149). sonar.yml installs the dev and coverage locks. It installs no gitleaks and sets no `DPLD_REQUIRE_SCAN` (lines 194 to 203).
So the **166 browser tests are skipped in both jobs**, and the **27 gitleaks and hygiene tests are skipped in the Sonar job** (skips/SKIP-TABLE.md lines 24 and 33). Neither job installs Node; the Node tests (36) run only if the runner has Node (INFERRED).
The browser lock exists: `requirements-browser.txt` holds Playwright 1.63.0 and 3 packages it needs, with hashes (91 hash lines). It needs Chromium build 1243, fetched with `playwright install chromium` (docs/tests.md lines 36 to 40 and 58).
Cost, partly measured: on GitHub the tests step took 958 s without a browser (earlier tree). Locally, a serial run with the browser took 993 s for 2516 tests (docs/tests.md line 61). **Not measured: the time to install Chromium on a runner**, and whether the runner needs Chromium's system libraries (`--with-deps`).

**Recommendation** (mine, from this evidence): add a **separate browser job** that runs on pull requests to `main`. It installs both locks, then `playwright install chromium`, and runs only the browser test files. The reason: the portal masking promise P10 rests on these tests (docs/tests.md line 34), and today no CI job runs them. A separate job keeps the lint time as it is. Set its time limit after the first real run. In the Sonar job, gitleaks matters only for the coverage figure, because lint already enforces the scan. Add it there (the same 4-line install step) only if the owner wants the coverage figure to include the hygiene tests. Lower priority.

## 5. Recommendation table

| Option | What the reviewer sees | CI coverage | Risk | Effort | Carry-over work |
|---|---|---|---|---|---|
| A | One PR, 226 files, 17 commits; bots: DeepSource expected, CodeAnt only on command, CodeRabbit none | lint + CodeQL + Sonar on the whole tree, **after** the sonar.yml fix and a push; real CI never run on 2db3926 | First real CI run may find something local runs did not | 1 file fix + push, retarget, close 2 PRs | Paste the checklist (43 inline + 14 nitpicks from #2/#3) into #4 |
| B | 3 PRs; #4 (142 files) already gets no CodeAnt or CodeRabbit review | lint red on #2 and #3 by design; `main` red between merges | `main` holds code that fails its own checks for a while; 3 retargets, each may need a push | 3 merges + 2 retargets + the same sonar.yml fix | None (threads stay where they are) |

**Testing the lead's preference for A against the evidence:** the evidence **supports A**. The reason for the split (a bot review for each part under 100 files) no longer holds, because #4 is at 142 files and CodeRabbit reviewed nothing. There are no human threads to lose. B would put code on `main` that fails its own checks.
**Where the evidence does not support "A as planned":**
(1) A alone does not give the whole tree SonarQube: sonar.yml is broken and must be fixed first (the same is true for B).
(2) Retargeting alone may not start lint or CodeQL; plan one push after it (not verified).
(3) A gives up a bot line-by-line review of the whole tree unless someone posts the CodeAnt command.
(4) "Green" is local only: the first real GitHub CI run of 2db3926 is still ahead.

## Evidence appendix (all in /tmp/demo-push/handover/demo/pr-stack/)

- evidence-ab-api-counts.txt: number of comments and reviews per PR, every page fetched
- evidence-ab-api-summary.txt: state, base, head, file counts, authors
- evidence-ab-findings-breakdown.txt: severities, DeepSource themes, Sonar gates, DeepSource grades
- evidence-ab-checklist-stats.txt: final-tree line check per PR and per bot
- evidence-ab-diffstat.txt: `git diff --stat` for both options, commit list, file tree of `main`
- evidence-ab-workflows.txt: the workflow files, `.coderabbit.yaml` and the CodeAnt config, as on `pr-3-tests` and `main`
- evidence-ab-sonar-yaml.txt, evidence-ab-sonar-run.txt: the YAML error and the 0-job runs
- evidence-ab-checks.txt: check runs and statuses per head, workflow runs, branch protection and rulesets
- evidence-ab-ci-durations.txt: real run times and step results of lint, CodeQL and Sonar
- evidence-ab-ancestry-browser.txt: branch ancestry, the browser lock, the docs lines
- raw-*.json: raw API answers. CARRY-OVER-CHECKLIST.md is built from them by `checklist.py` in this folder (no network).

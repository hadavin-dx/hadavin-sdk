# VERIFY: facts in pr2/pr3/pr4-user-description.md (drafter+verifier D-PR, queue Q3)
Clone: /tmp/work/dpr-base (fresh `git clone` of the public repo, all branches tracked, 2026-11-13 ~01:25Z). Heads: main a0b97a4, pr-1-code d23cf8f, pr-2-demo-folder f31e261, pr-3-tests 2db3926, initial-code 43110e7. Read-only on GitHub (one `gh api .../pulls?state=all` read). Commit times from `git log --date=iso-strict` (+05:30 author dates) converted to UTC by me; they are not push times.
EGM skipped for this file: a read-only verification table. The three PR texts still need the lead's EGM review of the result (R13); I could not run EGM agents (no sub-agents allowed).

## Corrections to the brief and to REVIEW-pr2-4.md (read first)
1. The PRs were OPENED at 17:36:53Z (#2), 17:37:03Z (#3), 17:37:11Z (#4) on 2026-11-12, not at 20:16Z. 20:16Z is the last `updated_at` of #2/#3. The texts use the opening times.
2. #4 now changes 142 files, so the current body's "each pull request has 100 files or fewer" is FALSE for #4. The new text says so; whether CodeAnt AI still reviews all of it is [UNVERIFIED].
3. The core touches are MORE than the reviewer listed. Batch 1 (2ce1f98: triage/py-retry + js-portal, reviewed clean, applied by the lead) changed config.py, crm_hubspot.py, live_claude.py, portal_api.py, smtp_outbox.py, smtp_provider.py, desk.py (functools.partial), portal.js, overview.js, log.js. Batch 3's desk.py ALSO holds the CRM-copy busy-wait change (`_mirror_busy`, `exclusive=True`), not only `book_problem`; Batch 3 also changed log.js. None of these is on the lead's approval lists (ORDERS.md L100, L117, L120, L110). #4's text lists them under "[UNVERIFIED: approval]" for the lead.
4. `KnowsBoundAddress` is NOT behaviour-free: `server.make_server` now calls `demo.set_bound_address(...)` when the demo extension has it (only demo_only/portal_demo.py has it). The text says so.
5. The reviewer's "mypy, bandit clean on 2db3926" was not in SCAN-TABLE (that ran gitleaks, ruff 0.16.9 and test_hygiene only). I ran ruff 0.17.4, mypy, bandit and gitleaks on 2db3926 myself: clean (rows 23-26).
6. triage/SUMMARY-codeant3-rt.md L8 says the refusal "also refuses `file:` names"; the final code does NOT (desk.py docstring: "A `file:` name is NOT refused"). The text follows the code.
7. #2's own gitleaks allowance for the SonarQube key does not take effect (its `regexTarget = "line"`; #4's .gitleaks.toml comment explains why). Measured: 1 finding with #2's own config.
8. skips/ has no SKIP-TABLE.md (Q5 not finished): only two evidence files, one marked INVALID. Not cited.
9. Chunked run on 2db3926 finished during my work: 3138 passed, 3 skipped, 0 failed (row 50). The single-process run the lead asked for is not done.

## Table
| # | statement (as used in the texts) | how verified | result |
|---|---|---|---|
| 1 | #2/#3/#4 opened 17:36:53Z / 17:37:03Z / 17:37:11Z | `gh api repos/hadavin-dx/duplicate-proof-lead-desk-n8n/pulls?state=all` | verified |
| 2 | #1 = branch initial-code 43110e7, closed, not merged | same call (state closed, merged_at empty) | verified |
| 3 | #2 changes 86 files, base main | `git diff --name-only main...pr-1-code \| wc -l` | 86 |
| 4 | #3 changes 39 files: 15 demo_only, 24 tests/portal_fixtures, all .json | `git diff --name-only pr-1-code...pr-2-demo-folder`, dirname count, `grep -vc '\.json$'` = 0 | verified |
| 5 | #4 changes 142 files: 93 tests/, 49 elsewhere | `git diff --name-only pr-2-demo-folder...pr-3-tests` + top-dir count (tests 93, src 16, root 12, demo_only 7, docs 5, scripts 3, load_tools 2, .codeant/.github/n8n/tools 1 each) | verified |
| 6 | at opening #4 had 73 files; 92 files of today's #4 view differ from bee6fff | `git diff --name-only 1ca303a bee6fff \| wc -l`; blob compare per file | 73; 92 |
| 7 | final tree differs from #1 in 95 files | `git diff --stat initial-code pr-3-tests` | "95 files changed, 5513 insertions(+), 271 deletions(-)" |
| 8 | the 95 = 9 quality-tool files from main + the batches | `git diff --name-status initial-code 558d37f` (9 files before any batch: .codeant x2, .deepsource.toml, sonar.yml, sonar-project.properties, .sonarcloud.properties deleted, .gitleaks.toml, exceptions.txt, docs/tests.md) | verified |
| 9 | 19:47Z and 20:11Z merges bring main's settings down the stack | `git log --graph --all` (b29bb1f 01:17:37+05:30, 558d37f 01:41:28+05:30) | verified |
| 10 | #2 view: since opening only .gitleaks.toml, exceptions.txt, docs/tests.md changed, 19:46-20:11Z | blob compare of each `main...pr-1-code` file vs ca6edf0; commits ac93153, d71284f, 177b8b7, d23cf8f | verified |
| 11 | #3 view: no file changed since opening | blob compare vs 1ca303a: none; file list identical | verified |
| 12 | pr-1-code / pr-2-demo-folder unchanged since 20:11:28Z | heads d23cf8f, f31e261 dated 01:41:28+05:30 | verified |
| 13 | Batch 1 2ce1f98 20:50Z; 2a 0841f36 20:53Z; 2 5947364 22:20Z; 40d5668 22:25Z; f5fe824 22:42Z; Batch 3 2db3926 00:41Z (13 Nov) | `git log --date=iso-strict pr-2-demo-folder..pr-3-tests` | verified (author dates) |
| 14 | what each batch touched | `git diff --name-status <c>~1 <c>` per batch | verified |
| 15 | batch files in #2's part (34 names listed in #2's text), in #3's part (7 demo_only names) | `grep -Fxf` of the batch file list against each PR's list | verified |
| 16 | lint.yml and codeql.yml: pull_request only for `branches: [main]` | merge-ready/evidence-m3-5-workflow-triggers.txt (git show on all three heads); unchanged since: `git diff --stat pr-2-demo-folder pr-3-tests -- .github` = sonar.yml only | verified |
| 17 | sonar.yml: pull_request opened/synchronize/reopened, no branch filter, same-repo PRs only | same file + `git show pr-3-tests:.github/workflows/sonar.yml` (`if:` line) | verified |
| 18 | so #2 starts lint, CodeQL, SonarQube; #3 and #4 only SonarQube | inference from 16-17 and the PR bases | inference from the files; GitHub's real check list NOT read (the lead reads it) |
| 19 | pr-1-code alone: gitleaks dir 1 finding (generic-api-key, sonar-project.properties:4), git 325 | gitleaks 8.30.1 on `git archive pr-1-code` and on a detached worktree, branch's own .gitleaks.toml, `--redact --ignore-gitleaks-allow`, `-f json` | exit 1 / 1; exit 1 / 325 (matches SCAN-TABLE) |
| 20 | pr-2-demo-folder alone: same | same commands | exit 1 / 1; exit 1 / 325 |
| 21 | no tests on pr-1-code; only tests/portal_fixtures on pr-2; pytest exit 5 | `git ls-tree` (0 test_*.py on both); exit 5 from merge-ready/MERGE-READINESS-2-4.md | ls-tree verified; exit 5 from that file, not re-run |
| 22 | ruff and mypy pass on d23cf8f and f31e261 ("an earlier run by the studio") | MERGE-READINESS-2-4.md branch table | from file, not re-run |
| 23 | 2db3926: ruff 0.17.4 "All checks passed!", "145 files already formatted" | my run, /tmp/work/int2-venv/bin/ruff in /tmp/work/dpr-base | verified |
| 24 | 2db3926: mypy 2.4.1 linux and win32 "no issues found in 26 source files" | `mypy --platform linux` / `--platform win32` | verified |
| 25 | 2db3926: bandit -ll no issues | `bandit -ll -q -r src tools scripts -c pyproject.toml`: exit 0, no issue lines | verified |
| 26 | 2db3926: gitleaks dir and git "no leaks found" | gitleaks 8.30.1 on `git archive` and on the clone, `--config .gitleaks.toml --redact --ignore-gitleaks-allow` | exit 0 / exit 0 |
| 27 | server.py drops the body after 413 on the step route and after an error reply once headers were read (501 unknown method) | `git diff initial-code pr-3-tests -- src/lead_desk/server.py` (hunks in `_step` and `send_error`) | verified |
| 28 | `:memory:` refused, exit 4, before folder and lock; module-level `book_problem`; main calls `desk_module.book_problem`; Desk repeats it | diff of server.py `main`, desk.py `book_problem` and `Desk.__init__`; contract.md :143 | verified |
| 29 | loader.py `KnowsBoundAddress`; make_server calls set_bound_address; only demo_only/portal_demo.py implements it | diff + `git grep -n set_bound_address pr-3-tests -- demo_only src` (3 hits) | verified: NOT behaviour-free (demo mode only) |
| 30 | contract.md 143 and 277 describe the refusal; line 71 names the browser locks | `git diff -U0` per batch: 143 (Batch 1, 3), 277 (Batch 3), 71 (Batch 2) | verified |
| 31 | CSS: app.css, leads.css, needs.css, overview.css: long names wrap or end in an ellipsis; phone-width rules | `git diff initial-code pr-3-tests -- '*.css'` | verified |
| 32 | range queries need Chrome 104 / Firefox 63 / Safari 16.4, "recommended minimum" | layout/REVIEW-3.md L4 (reviewer); lead approval ORDERS.md L110; NOT in the repo (`git grep` chrome/safari/firefox in docs, README, versions.md, contract.md: 0 hits) | reviewer note + lead approval; not documented in the repo |
| 33 | only Chromium tested | layout/REVIEW-3.md L10; docs/tests.md browser section (Chromium only) | verified (files) |
| 34 | desk.py CRM copy busy wait 10/60/180/420 s, refusal not a try, exclusive=True | Batch 3 desk.py diff; triage SUMMARY L11; docs/limits.md L137 | verified |
| 35 | desk.py functools.partial instead of lambda | Batch 1 desk.py diff | verified |
| 36 | except clean-ups in 5 files; test_except_clause_hierarchy.py 49 cases | diffs; docs/tests.md L61 ("49 in the new file") | diff verified; 49 from docs, not counted by me |
| 37 | "the intent is no behaviour change" | comments in the diff ("UnicodeError is a ValueError", "a CrmError is none of these: it passes through") | intent from comments; equivalence read, not proven |
| 38 | portal_api.py: only renames of unused names | diff (one hunk) | verified |
| 39 | portal.js/overview.js declarations moved, loop without a function; log.js keeps rows on Load more | Batch 1 and Batch 3 diffs | verified |
| 40 | approved core touches: drain, KnowsBoundAddress, contract.md 143/277 (ORDERS L100); main refusal + book_problem (L117; module form L120); CSS + browser minimum (L110) | /tmp/demo-push/handover/demo/ORDERS.md | verified (file) |
| 41 | rows 34-39 and contract.md 71 are not on those lists | ORDERS.md; APPLY-LIST.md (Batch 1 "reviewed clean", no core-touch condition) | absence verified; marked [UNVERIFIED: approval] |
| 42 | requirements-browser.in `playwright==1.63.0`; .txt/-win.txt pin greenlet 3.5.6, playwright 1.63.0, pyee 13.0.1, typing-extensions 4.16.0, with hashes | `git show pr-3-tests:<file>` | verified |
| 43 | requirements-coverage.in = pytest-cov; .txt pins coverage 7.17.2, pytest-cov 7.1.0 (+ pytest 9.2.0 etc. constrained by the dev lock); only sonar.yml uses it | `git show`; sonar.yml install line | verified |
| 44 | browser tests need no Pillow | docs/tests.md L36; no pillow in requirements-browser.in | verified (files) |
| 45 | sonar.yml: ubuntu-latest -> ubuntu-24.04, timeout 20 -> 60, setup-python, dev + coverage locks, `pytest -q --cov` | `git diff main pr-3-tests -- .github/workflows/sonar.yml` | verified |
| 46 | pyproject `faulthandler_timeout = 300` and `[tool.coverage.run]`; sonar-project.properties coverage path | diffs | verified |
| 47 | stop guard: 20 s, 60 s for desk/fakes (2 x 30 s), stack dump, reported as an error of the test | tests/support.py L442-484, tests/conftest.py L80-93, constants.py L192; APPLY-LIST nit "reports ERROR at teardown" | verified |
| 48 | no hang was ever shown to come from the desk code | APPLY-LIST.md 23:25Z ("no hang was ever reproduced"); INT-2b.md (buffering misread) | from files |
| 49 | fake CRM reads the body before answering | Batch 3 subject; APPLY-LIST L69 (speed/fake-hubspot-read-body-before-answer.patch); diff stat | from files + stat, body not read line by line |
| 50 | 2db3926 in 10 separate parts: 3138 passed, 3 skipped, 0 failed | /tmp/work/h3chunk-0..9.txt and .exit (all 10 `exit=0`; summed summary lines; no FAILED/ERROR lines); driver /tmp/work/h3chunks.sh (Playwright + Chromium + GITLEAKS_BIN + DPLD_REQUIRE_SCAN=1); chunk 5 was rerun after a killed first attempt | verified (finished 01:38:25Z) |
| 51 | f5fe824 run A: 2988 passed, 6 skipped, 0 failed, one process; 3 gitleaks tests skipped | integration/INT-2b.md | from file |
| 52 | run C2: f5fe824 + Batch 3 patches except the hygiene tests: 3094 passed, 3 skipped, 0 failed, 10 parts | INT-2b.md (C2 stack has no hygiene-v3; ORDERS L129: v3 applied last) | from file |
| 53 | lead's Windows quote "252 passed / 29 skipped on Windows (skips: POSIX signal and gitleaks-binary tests)" | ORDERS.md L129 | quoted; "part of the suite" is my inference (281 tests vs 3141) |
| 54 | Linux skips: file permission as root, load measurement, Windows-only reset | my chunk run: SKIPPED lines in tests/test_n8n_api_url.py:510, tests/test_server_hardening.py:224, tests/test_stall_eviction.py:526 | verified |
| 55 | browser tests skip in GitHub's lint (no Playwright there) | docs/tests.md L34 | verified (file) |
| 56 | browser tests ran in the chunked runs with Chromium | drivers export PLAYWRIGHT_BROWSERS_PATH; 16 `test_portal_browser.py ... PASSED` lines in h3chunk-6.txt | verified |
| 57 | "because of a limit of the free code-review tool" (no number) | kept; no source for "100" in repo or handover | number [UNVERIFIED], not used |
| 58 | CodeAnt AI reviews all 142 files of #4? | none | [UNVERIFIED] |
| 59 | branch protection on main; lint starting after retarget without a new push | none (MERGE-READINESS round 3: a reviewer's reading, not verified) | [UNVERIFIED] (owner questions) |
| 60 | demo_only loads only with the demo settings | loader.py `load_demo_portal` docstring on pr-3-tests | verified (file) |
| 61 | not run: GitHub checks, full Windows/PowerShell, Python 3.13, real n8n/CRM/mail, Firefox/Safari, SonarQube coverage job, Semgrep, single-process run of 2db3926 | MERGE-READINESS items 2-4; INT-2b "Not run"; my runs include none of these | verified as not run in the evidence (except the lead's partial Windows run) |

## Cleanup
Mine: /tmp/work/dpr-base (kept for re-checks), /tmp/work/dpr-*.txt and .json; the two worktrees and the archive folders are removed. I did not touch /tmp/work/h3; I only read its output files. No process left running.

## v2 update (after the second review)
Files: pr2/pr3/pr4-user-description-v2.md (v1 kept), QUESTIONS-FOR-LEAD.md (internal items). No internal markers in the v2 bodies except [FILL: single-process result]; no [UNVERIFIED] lines, no handover file names, no first person, no "lead"; every sentence under 35 words (script check). The rows above still hold; new or changed rows:
| # | statement | how verified | result |
|---|---|---|---|
| 62 | src/ files in #4: 16 | `git diff --name-only initial-code pr-3-tests -- src` and `pr-2-demo-folder...pr-3-tests -- src` | 16 (9 py, 4 css, 3 js) |
| 63 | wait "about 10, 60, 180 and at most 420 s, depending on earlier tries" | desk.py L824-825 on pr-3-tests; constants.py L159 `(10.0, 60.0, 180.0, 420.0)` | verified |
| 64 | `exclusive=True` on the stage-copy call for every CRM (before: no exclusive argument, default False) | desk.py L806-809 (pr-3-tests) vs initial-code L779-785; other CRM calls L1582 | verified; only this call |
| 65 | 2db3926 post steps: ruff, format (145 files), mypy linux+win32, bandit exit 0, hygiene+gitleaks tests 59 passed, gitleaks dir+git no leaks, restart test 5 x 1 passed | /tmp/work/h3post-1..9*.txt/.exit | verified (all exit=0) |
| 66 | single-process run of 2db3926 | /tmp/work/full2db-b.txt (at 01:43Z: running, ~2%) | not finished: [FILL] in #4 |
| 67 | 325 history findings: scan reads every branch; #2's older settings flag lock files added in #4 (313 long-hex-token), 10 hostname-like, 2 SonarQube key | gitleaks 8.30.1 `git` on a pr-1-code worktree of the full clone, `-f json`, grouped by rule/file/commit (commits 0841f36, 5947364, 7ec367b, a0b97a4) | verified; the reviewer's stated reason was wrong |
| 68 | "earlier heads of this branch were also run in full, with 0 failures" | INT-2b run A (f5fe824: 0 failed); APPLY-LIST INT-1 (Batch 1 tree: 2400 passed, 0 failed) | from files |
| 69 | sonar.yml: one job; SONAR_TOKEN only on the scan step; split is open | `git show pr-3-tests:.github/workflows/sonar.yml` comment lines 7-12 and the `env:` of the scan step | verified |
| 70 | "should start" (lint/CodeQL/SonarQube) | inference from workflow files (row 16-18) | wording now says inferred |
| 71 | browser minimum = a reviewer's estimate, not in the repo docs | row 32 | wording fixed |
| 72 | Windows 252/29 figure | dropped from v2 (QUESTIONS item 5) | n/a |
| 73 | INT-3-2db3926.md | not present in /tmp/demo-push (find) | not read; same figures verified from raw files |

## v3 update (after the third review)
Files: pr2/pr3/pr4-user-description-v3.md (v1 and v2 kept). Changes: merge order rewritten as two ways A/B without a recommendation (QUESTIONS item 10); terms defined once (CRM, n8n, SonarQube, CodeQL, CodeAnt AI, repository owner); ":memory:" now "database name" with the reason (desk.py MEMORY_BOOK_PROBLEM text); "Batch" labels replaced by commit ids; CodeAnt split rationale dropped; one [FILL: single-process result: the whole suite in one pytest process] marker, chunked result on the line before it with its limit. Script check: no sentence of 35 words or more; no "Batch", "lead's", first person or handover file names.
| # | statement | how verified | result |
|---|---|---|---|
| 74 | 19:46 vs 19:47: both are right, for different branches. ac93153 (main into pr-1-code) 01:16:24+05:30 = 19:46:24Z, used in #2. 51abd28 (into pr-2) 19:47:36Z and b29bb1f (into pr-3) 19:47:37Z, used in #3/#4 | `git log --date=iso-strict` (row 9) | consistent per branch |
| 75 | way A/B: lint and CodeQL only for base main, SonarQube for every PR | rows 16-17 | verified (files); what GitHub allows for each merge step is not claimed |
| 76 | GitHub may retarget a PR when its base branch is deleted after merging | GitHub's documented behaviour, not tested on this repo | worded "may" |

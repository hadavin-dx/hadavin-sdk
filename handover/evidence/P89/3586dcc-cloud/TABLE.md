# EVIDENCE RUNNER table: core/mutation-runner-keywords
Head: 3586dcc34647fa66dded9a4250be6b52e845c5ba (git rev-parse printed at the top of each log). Git tree of HEAD: 6fa785565bc526c20021db7cf61a74540b76f6ab (equals the expected tree).
Merge-base of origin/main and head: 2742c1bfe510bfb13cfac5d3424bac3d8d6324c5.
Cloud variables unset (AWS_*, ANTHROPIC_*, AZURE_*, GOOGLE_*, GCP_*, VAULT_*, OPENAI_*, GEMINI_*, CLOUDSDK_*) by clean.sh around every command; the full-suite logs list "still set:" lines (none printed).
Postgres: own cluster ev-p89-3586dcc, 127.0.0.1:55893, trust, UTF8; HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55893/postgres (printed before and after in 02 logs). Cluster stopped with pgstop.sh.
Worktrees: wt (full suite), wt-mut (steps 3,4,6), wt-base (step 5), nr/wt (non-root clone). Both full-suite runs shared one cluster and ran at the same time.

| # | Command | Python | Counts | Exit | Log |
|---|---|---|---|---|---|
| 1a | ruff check src tests demos tools | 3.13 | All checks passed | 0 | 01-lint.log |
| 1b | ruff format --check src tests demos tools | 3.13 | 318 files already formatted | 0 | 01-lint.log |
| 1c | bandit -q -r src demos tools -ll | 3.13 | no findings (bandit is not in the uv test group, so run with uvx bandit; warnings about nosec comments only) | 0 | 01b-bandit.log |
| 1d | python tools/scan_repo.py | 3.13 | no output | 0 | 01-lint.log |
| 2a | full pytest -m "not live and not perf", no deselect | 3.12 | 10584 passed, 1 skipped, 28 deselected (marker) | 0 | 02-full-py3.12.log |
| 2b | same | 3.13 | 10584 passed, 1 skipped, 28 deselected (marker) | 0 | 02-full-py3.13.log |
| 3a | 3 mutation runner test files (keywords, meta, runner), DSN set | 3.12 | 164 passed | 0 | 03-three-py3.12.log |
| 3b | same | 3.13 | 164 passed | 0 | 03-three-py3.13.log |
| 4a | python tests/mutation_runner_mutants.py (alone), root | 3.13 | 162 of 162 good; git status clean after | 0 | 04-mutants-root.log(.full) |
| 4b | same as uid 65534 via setpriv, own clone nr/wt (HEAD and tree verified in log) | 3.13 | 162 of 162 good; git status clean after | 0 | 04-nonroot.log, 04-nonroot-mutants.full |
| 4c | step-3 files as uid 65534, DSN set | 3.13 | 164 passed; git status clean | 0 | 04-nonroot.log |
| 5a | head keywords+meta tests copied onto merge-base, no shim | 3.13 | keywords: collection ERROR (ImportError PASS_ENV_ALLOWED); meta run alone: 3 failed, 3 passed | 2 / 1 | 05-failbefore-collect.log, 05-failbefore-meta-collect.log |
| 5b | same with no-behaviour stub plugin (names missing on old code stubbed to raise NotImplementedError) | 3.13 | 97 failed, 8 passed of 105 | 1 | 05-failbefore-shim.log/.xml, 05-failbefore-results.txt (per test PASS/FAIL), 05-conftest_shim_plugin.py |
| 6 | the 3 test files, 3 repeats (in addition to 3b) | 3.13 | 164 passed each time (3 of 3) | 0 | 06-repeats-py3.13.log |

## Not run / caveats
- bandit run with uvx (not in the uv group). The shared cluster was used by 2a and 2b concurrently; no failures resulted.
- Step 5: the meta test file on the old code uses the old mutants list (62 mutants), as only the two test files were copied, as instructed. The 8 passes in 5b are listed in 05-failbefore-results.txt; stubs may make some of them pass or fail for reasons other than the missing behaviour.
- Step 6 read as 3 repeats of the three files; step 3b is a further run.
- No Windows run. No coverage run. No live or perf tests (marker excluded: 28 deselected).
- First non-root attempt used a wrong checkout; kept as 04-nonroot-attempt1-wrong-checkout.log, redone correctly.

Note by the cloud lead: the two full-suite junit files (02-full-py3.12.log.xml and 02-full-py3.13.log.xml) are not committed because they contain made-up key-shaped test strings that the repository secret scan could flag; the pytest summary lines are in the .log files. Evidence belongs to head 3586dcc (tree 6fa785565bc526c20021db7cf61a74540b76f6ab); round 8 will produce a new head.

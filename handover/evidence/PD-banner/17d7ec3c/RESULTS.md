Evidence for wip/cloud-pd-banner head 17d7ec3c434083f357fcba1aee5abb06b19a3d45 (records only)
NOT RUN: gitleaks (binary not installed; download from github.com was denied by the permission classifier; not worked around).
Full pytest first run: 1 failed, 10621 passed, 1 skipped, 28 deselected (rc=1): tests/demo_askdata/test_validate_harm.py[dblink-connect]; cause: my Postgres server's own default socket/port differ (environment). Re-run with server started with PGPORT=54399 PGHOST=/tmp: 253 passed (6c log).
1 targeted: 283 passed rc=0. 2 stage_mutants 37/37 good rc=0; banner_mutants 79/79 good rc=0; git status clean after each.
3 ruff check rc=0; ruff format --check rc=0 (325 files); bandit -ll rc=0 (no issues; nosec warnings only); scan_repo rc=0.
4 yaml.safe_load: only ci.yml exists under .github/workflows, OK.
5 fail-before (2cf0f742 ci.yml + head test): 2 failed (parse + unquoted colon, line 87), 2 passed, rc=1; file restored.

## Lead addendum (not the runner)
- gitleaks (runner could not install it): lead ran `gitleaks git --log-opts origin/main..17d7ec3c` rc=0 and `gitleaks dir` on the raw evidence rc=0.
- Single-run full pytest NOT proven: 1 failure was the runner Postgres setup (fixed socket), not the branch; the rerun of that file passed.
- The ci.yml swap overlapped the stage-mutants run, so its 37/37 may be affected; rerun at the batch-4 head.
- Head is stale once batch 4 (a43a4fca) pushes; a delta run is owed at the new head.

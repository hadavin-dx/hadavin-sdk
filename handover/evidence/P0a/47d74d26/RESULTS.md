# Evidence: PR 71 (core/P0a) merged head 47d74d264a39a932bd90519cc3e71ea2e3cfb78e (EVIDENCE RUNNER, no judgement)

Head = normal merge of origin/main e5aa9457 into core/P0a 04cfa501 (no conflicts). Clean detached worktree, `git status` clean before and after. Own Postgres 16.15, UTF8, PGHOST/PGPORT in the server env. Raw logs: `/home/user/build/evidence-raw/p0a-merge/` (outside the repo).

## Not run / notes (first)
- Failures: none. The one skip in the full run is tests/contracts/test_llm.py:95 (Stubber). Vault tests did not appear as skips because they are deselected or absent in this head's marker set; real Vault server not available here.
- Heavy-slot priority was set by a name match ("Q8c1-prio1"), not an official setting.
- The timing wrapper rc 143 is the runner's own `wait` on killed busy loops; every pytest run inside exited 0.
- The timing flake did NOT appear in 7 runs (alone x5, one busy loop, four busy loops). That does not prove it is fixed: PR 71's `check` still depends on the timing fix PR.

## Results
| Item | Exit | Last line |
|---|---|---|
| Full pytest (-m "not live and not perf") | 0 | 10805 passed, 1 skipped, 28 deselected in 273.81s |
| ruff check src tests demos tools | 0 | All checks passed! |
| ruff format --check | 0 | 322 files already formatted |
| bandit -ll | 0 | only the B102 nosec warnings, no findings |
| tools/scan_repo.py | 0 | no problems |
| gitleaks origin/main..HEAD | 0 | 9 commits scanned, no leaks |
| CI step "stale gitleaks ignore entries" (shell from ci.yml, run as CI does) | 0 | no output; .gitleaksignore 21 entries |
| check-no-handover-files.sh core/P0a 47d74d26 | 0 | no output |
| tests/test_ci_gitleaks_scope.py + tests/test_ci_guard_wip_lanes.py | 0 | 149 passed |
| tests/test_timing_fixture.py alone x5 / 1 busy loop / 4 busy loops | 0 | 10 passed each |
| diffstat origin/main...HEAD | - | 1 file changed, 675 insertions |

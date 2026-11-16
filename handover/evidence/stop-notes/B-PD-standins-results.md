Head 9c831f700f62dcee50316394239599c6b463e5e9 (pushed to wip/cloud-pd-standins). Merge base: 9f688fdc (is_loopback_host, from wip/cloud-pd-bind) on 2a8c2aac.
ruff check, ruff format --check (src tests demos tools), bandit -ll -r src, tools/scan_repo.py: rc=0 (B-PD-standins-lint.log)
Full pytest via heavy.sh (-m "not live and not perf"): 10167 passed, 457 skipped, 28 deselected, rc=0 (B-PD-standins-suite.log)
tests/stage_mutants.py: 37 of 37 good (B-PD-standins-stagemut.log)
tests/standin_mutants.py: 13 of 13 good (B-PD-standins-mut2.log)
Old code 2a8c2aac: both new test files fail at collection (B-PD-standins-old-code.log); probe shows stand-in on example.test accepted (B-PD-standins-old-probe.log)

# EVIDENCE RUNNER results: PD-bind, head 06e762bc2bf99375ec58f3e8b52c20b59b3c389b (origin/wip/cloud-pd-bind), base origin/main a8b4d8e8
Recorded only, nothing judged or fixed. Interpreter: CPython 3.13.18. Tree clean (0 changed files) at the start and after every mutant run.
Raw logs: /home/user/build/evidence-raw/pdbind-06e762bc/ (outside the repo).

## Failures and things not run (first)
- `uv sync --locked --no-build --all-extras --group test` (the exact command of the brief) FAILED, exit 2: "hadavin-sdk==0.1.0 @ editable+. ... marked as --no-build but has no binary distribution". I ran `uv sync --locked --all-extras --group test` (no --no-build), exit 0, and used that venv for everything. Log: sync.log, sync2.log.
- Item 9: `test_the_timing_harness_flags_a_quadratic_stand_in`, alone, 3 runs each: head FAILED 3 of 3 ("a quadratic function must be flagged"); origin/main failed 1 of 3 (run 1 failed, runs 2 and 3 passed). (Run with PYTHONPATH pointing at each worktree's src.)
- Fail-before (item 7), main: 3 of the 4 changed test files cannot be collected on old code (ImportError for `bindguard` and `netguard`), so their tests never ran there; see below.
- IPv6 real socket and Python 3.12: IMPOSSIBLE-NOW here, not tried. Full suite had 2 skips, one of them "this machine has no IPv6 loopback" (tests/test_bindguard.py:468).
- Probe slip of mine: in probes.out line f4 I built the approvals and the config from two separate build calls, so it refused for "not that config" (not the case intended); f5 is the intended case.
- Not run: perf step of ci.yml (`pytest -m perf`; the ticket names no perf item), Semgrep, zizmor, pip-audit, Trivy, CodeQL (not available / not part of the items).

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 | `git diff --name-only origin/main...HEAD` | 0 | 24 files (list in item1.txt: 19 under src/ plus ci.yml, CHANGELOG.md and 5 test files: tests/bind_mutants.py, test_bindguard.py, test_loopback_sites.py, test_netguard.py, test_p7_tick.py) |
| 2a | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | `ruff format --check src tests demos tools` | 0 | 325 files already formatted |
| 3 | `bandit -q -r src demos tools -ll` | 0 | only WARNING "nosec encountered (B102)" at src/hadavin_sdk/tools.py:389; no issues |
| 4a | `python tools/scan_repo.py` | 0 | (empty output) |
| 4b | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks git, log-opts origin/main..HEAD | 0 | no leaks found |
| 5 | full pytest `-p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 0 | 10726 passed, 2 skipped, 28 deselected in 257.92s (0:04:17) |
| 6a | `python tests/bind_mutants.py` (ci.yml step added by this branch) | 0 | 52 of 52 good; problems: [] (48 KILLED, 4 CRASH lines, each marked ok) |
| 6b | `python tests/stage_mutants.py` | 0 | 37 of 37 good (same as 4b) |
| 7a | the 4 changed test files copied onto detached origin/main (src from main) | 1 | 1 failed, 40 passed, 3 errors |
| 7b | same 4 files against src of 6e6ae211 | 1 | 118 passed, 1 error |
| 8 | probes (probes.out) | see below | |
| 9 | flaky timing test alone x3 | see above | |

Postgres 16.15 own server (port 56711, PGHOST and PGPORT in the server and test environment, HADAVIN_TEST_PG_DSN pointed at it); stopped and its folder deleted. The heavy.sh queue wait before item 5 was about 0 to 4 minutes (start 21:32:54 UTC, end 21:39:05 UTC including the 4:17 run).

## Item 7 detail
7a origin/main src + head's test files (bind_mutants.py is a script, copied too):
- collection errors (not run): tests/test_bindguard.py, tests/test_loopback_sites.py, tests/test_netguard.py (ImportError: cannot import name 'bindguard' / 'netguard', ModuleNotFoundError hadavin_sdk.netguard).
- tests/test_p7_tick.py: 40 passed, 1 failed (`test_the_approvals_server_answers_over_http`).
- the 40 passing tests in test_p7_tick.py pass on old code (list in failbefore-main.txt).
7b src of 6e6ae211 (the round 2 head) + head's test files: tests/test_bindguard.py cannot be collected (ImportError: cannot import name 'is_stand_in_object' from hadavin_sdk.bindguard). Passed: test_loopback_sites.py 67, test_netguard.py 10, test_p7_tick.py 41 (list in failbefore-r2head.txt). No test of test_bindguard.py ran against 6e6ae211.

## Item 8 probes (exact output in probes.out)
| Probe | Exit | Result |
|---|---|---|
| a real subclass of FakeChannel in build(); stand-in-only config; host 0.0.0.0 | 0 | BindRefused naming `held channel: RealChan` |
| b hand-built Approvals, no config; public host and loopback host | 0 | BindRefused "built by hand with no config" (both hosts) |
| c approvals.config = other; approvals.overrides = {} | 0 | AttributeError "property ... has no setter" (both); overrides['x']=1: TypeError (mappingproxy) |
| d approvals.channel replaced after build (an object not a stand-in; also a real subclass), host 0.0.0.0 | 0 | BindRefused `held channel: LooksReal` / `held channel: RealChan` |
| e detector AnyOf of stand-ins only | 0 | accepted (None); AnyOf with one real detector: BindRefused `held detector: AnyOf` |
| f tools={} | 0 | accepted (None); tools={"x": object()}: BindRefused `held tools`; build(tools={"x": fn}) then serve public: BindRefused `held tools` |
| g reason 9 chars / 10 chars | 0 | 9: "must say why, in at least 10 characters" (also when padded with spaces); 10: accepted (None); serve public with 10 chars: server created and a WARNING logged, with 9: BindRefused |
| h `::ffff:127.0.0.1`, `::ffff:7f00:1` | 0 | is_loopback_host True; serve on it: OSError 97 (no IPv6 on this machine, after the guard passed) |
| h `::ffff:8.8.8.8`, `::ffff:0808:0808` | 0 | is_loopback_host False; serve: BindRefused |
Also: `0.0.0.0` False, `::` False, `127.0.0.2` True, `LOCALHOST` True, `0177.0.0.1` False.
Each probe ran in one script, exit 0 for the script; each line states the exception or result.

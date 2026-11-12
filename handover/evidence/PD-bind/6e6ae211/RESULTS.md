# EVIDENCE RUNNER results: wip/cloud-pd-bind head 6e6ae21124f5b77231c6dd1a99a11b4c4bfb1ee3 (2026-11-12)

I ran commands and recorded raw output. I do not judge. Raw logs: /home/user/build/evidence-raw/pdbind-6e6ae211/ (outside the repo). Worktree: /home/user/build/EV-pd-bind (detached at the head). Linux, Postgres 16 started by me as the postgres OS user on private port 55437, stopped at the end.

## Not run / deviations
- FAILED once, then re-run narrowly: full pytest ended `1 failed, 10698 passed, 2 skipped, 28 deselected in 257.02s`. The one failure is `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: "could not establish connection ... socket /var/run/postgresql/.s.PGSQL.5432". Cause seen in the log: the Postgres SERVER process (dblink runs inside it) had no PGHOST/PGPORT in its own environment (I had set them only for pytest). I restarted my private Postgres with PGHOST/PGPORT/PGUSER in the server environment and re-ran that one file alone: `253 passed in 23.01s`. The whole suite was NOT re-run after the fix (same practice as the dd5c7242 ledger row). So no single full-suite run is green on this head.
- 2 skipped in the full run: not itemised. In tests/test_bindguard.py one test is skipped by design: "this machine has no IPv6 loopback" (tests/test_bindguard.py:438). So IPv6 `::1` binding was never exercised on this machine (Errno 97).
- Fail-before: test_s6_approvals.py passes 12/12 on old code (it does not fail before). The other four fail on old code (see table).
- Hostile inputs: a valid public-bind reason with a real public host (0.0.0.0) was NOT run, because that would open a wildcard socket (brief says loopback only). Valid reasons were run on 127.0.0.1 only; invalid reasons on 0.0.0.0 (refused before any socket). Stand-in config with 0.0.0.0, '::', '', 8.8.8.8 and the odd spellings was not run for the same reason.
- No hostname lookup or traffic was sent. No tree_hash column value for the ledger beyond the git tree of the head (given below).
- The fixture config has zero real services; the hostile run added egress host `example.invalid` to make a "real service" config.
- Not run: tests marked live and perf (excluded by the flag).

## Table
| item | command | exit | counts | seconds |
|---|---|---|---|---|
| full pytest | `heavy.sh uv run --all-extras --group test pytest -m "not live and not perf" -q` (HADAVIN_TEST_PG_DSN=own PG 55437, PGHOST/PGPORT client side only) | 1 | 1 failed, 10698 passed, 2 skipped, 28 deselected | 520 incl. queue wait (257 test time) |
| dblink file rerun (server env PGHOST/PGPORT) | `pytest tests/demo_askdata/test_validate_harm.py -q` | 0 | 253 passed | 24 |
| stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good, problems [] | 92 |
| bind mutants | `python tests/bind_mutants.py` | 0 | 39 of 39 good, problems []: 36 KILLED by a named test, 3 CRASH (B6, B22, B30 killed by crash in the named test) | 26 |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed | 0 |
| ruff format | `ruff format --check src tests demos tools` | 0 | 324 files already formatted | 0 |
| bandit | `bandit -q -r src demos tools -ll` | 0 | no findings printed (2 warnings: nosec B102 at src/hadavin_sdk/tools.py:389 without a finding; comment "bytes") | 1 |
| scan_repo | `python tools/scan_repo.py` | 0 | no output | 1 |
| gitleaks | `gitleaks git --config .gitleaks.toml --redact --log-opts origin/main..HEAD` | 0 | 4 commits scanned, no leaks | 0 |

## Fail-before (head's 5 test files copied into a detached worktree of origin/main a8b4d8e83f9fb29c09079417505682fd8b5464be, old src, own venv)
| file | old code | head |
|---|---|---|
| tests/test_bindguard.py | exit 2: 1 error, ImportError cannot import name 'bindguard' | 99 passed, 1 skipped (no IPv6) |
| tests/test_netguard.py | exit 2: 1 error (module missing) | 9 passed |
| tests/test_p7_tick.py | exit 1: 1 failed, 40 passed (`serve() got an unexpected keyword argument 'config'`) | 41 passed |
| tests/test_loopback_sites.py | exit 2: 1 error (module missing) | 67 passed |
| tests/test_s6_approvals.py | exit 0: 12 passed | 12 passed |

Note: three of the four "fail" on old code are import errors (the new module does not exist), not assertion failures.

## Hostile inputs against bindguard.listen (script /home/user/build/evidence-raw/pdbind-6e6ae211/hostile.py, output hostile.out; port 0, no traffic)
Machine has no IPv6 loopback (`::1`, `[::1]`, `::ffff:127.0.0.1` bind -> OSError Errno 97 on both configs, not BindRefused).
Config "real" = a service configured (egress example.invalid):
| host | outcome |
|---|---|
| '0.0.0.0', '::', '' | BindRefused |
| 'localhost', 'LOCALHOST', '127.0.0.1' | bound 127.0.0.1 |
| '127.1', '0x7f.0.0.1', '017700000001', '127.000.000.001' | BindRefused (treated as public) |
| '::ffff:0.0.0.0' | BindRefused |
| 'example.com', 'public-name.example', '8.8.8.8' | BindRefused (no lookup) |
| '::1', '[::1]', '::ffff:127.0.0.1' | OSError Errno 97 (no IPv6 here) |
Config "stand-in only": 'localhost', 'LOCALHOST', '127.0.0.1' bound; 'example.com', 'public-name.example' BindRefused ("not an IP address written out").
Reasons (real config): public host 0.0.0.0 with reason of 0 chars, 201 chars, bell character, newline, spaces only: BindRefused with the reason message; None: BindRefused with the bind message. On 127.0.0.1: 0 chars refused; 1 char and 200 chars bound; 201 chars, newline, escape sequence refused (an invalid reason is refused even when not needed).

Head tree hash: a49770b106a9bac3e7d5e18d6b107240e6e31017.

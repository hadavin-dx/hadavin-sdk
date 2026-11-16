# Q8a-1 independent evidence, tag Q8a1r8, head 18741c8cfdfc67e073139ad4e5df0f744d96b495
Run 2026-11-12 00:20-00:30 UTC by an EVIDENCE RUNNER (records only, judges nothing, fixes nothing). The builder's evidence folder was not read.
Head confirmed with `git rev-parse HEAD`; tree clean (`git status --short` empty) after all runs. Raw logs: /home/user/build/evidence-raw/Q8a1r8-18741c8c/.

## Not run or different from the brief (first)
- Timing test (item 9): not run (the lead said not required).
- CI steps pip-audit, semgrep, zizmor, trivy: not run (not named by the package ticket). Full-history gitleaks of CI: replaced by gitleaks on origin/main..HEAD.
- `uv sync --locked --no-build` fails for this repo ("hadavin-sdk editable can't be installed because it is marked --no-build"); the sync was run without `--no-build` (exit 0).
- Fail-before: tests/stage_mutants.py is a script, not a test file; it was not part of the fail-before copy (it is covered by item b).
- Perf marked tests (-m perf): not run (ticket names no perf item).

## Results
| item | command | exit | last line |
|---|---|---|---|
| head and tree | git rev-parse HEAD; git status --short | 0 | 18741c8c..., 0 changed files |
| (1) diff names | git diff --name-only origin/main...HEAD (main = 2a8c2aac) | 0 | 55 files (diff-names.txt) |
| (2) ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| (2) ruff format | ruff format --check src tests demos tools | 0 | 321 files already formatted |
| (3) bandit | uv run --with bandit bandit -q -r src demos tools -ll | 0 | only a warning: nosec B102 with no failed test at src/hadavin_sdk/tools.py:403 |
| (4) scan | python tools/scan_repo.py | 0 | no output besides a uv deprecation warning |
| (4) stage mutants | python tests/stage_mutants.py (own worktree, heavy.sh) | 0 | 160 of 160 good; problems: [] |
| (4) gitleaks | gitleaks git --log-opts=origin/main..HEAD | 0 | no leaks found |
| (5) full pytest | pytest -p no:cacheprovider -q -m "not live and not perf" -rs, via heavy.sh, own Postgres 16 (PGHOST/PGPORT/HADAVIN_TEST_PG_DSN set) | 0 | 11024 passed, 1 skipped, 28 deselected in 288.06s; the one skip: tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape) |
| (7a) fail-before at a1869655 | the 9 changed test files of `git diff --name-only a1869655 18741c8c -- tests` (stage_mutants.py excluded) on src of a1869655 | 1 | 51 failed, 610 passed |
| (7a) fail-before at origin/main 2a8c2aac | same files on src of origin/main | 1 | 283 failed, 378 passed |
| (8) ticket probes | own script /home/user/build/ev-q8a1r8-scripts/probe.py | 0 | see below |

Delta test files: tests/contracts/test_secrets.py, test_k5_tools.py, test_p2_postgres.py, test_p3b_neutral_audit.py, test_p4b_secrets.py, test_p7_store.py, test_s3_gate.py, test_stage_names.py, tests/warden_port/test_audit_chain.py (and tests/stage_mutants.py).

## Fail-before lists
- Failed lists: fb-prev-failed.txt (51) and fb-main-failed.txt (283) in this folder.
- Tests whose id exists at head but not in the test files of a1869655 (40 ids): 37 fail and 3 pass on a1869655 src; 38 fail and 2 pass on origin/main src. The ones that pass on old src are listed in new-passing-on-prev.txt (3) and new-passing-on-main.txt (2): the secret-shaped-id messages [hex64] and [upper], the guard-sees-a-name test, and the empty-tools-manifest test.
- 14 tests that already existed (same id at a1869655) fail on a1869655 src with the delta test file.
- Parametrized id collection can shift ids; the id comparison is by exact text.

## Ticket probes (probe.log; own script typed from the ticket tables, no builder tests used)
- Six overrides (secrets, channel, detector, llm, clock, timeout_s) x stages pilot, prod, staging, dev, test, Demo, DEMO, "demo " (trailing space), "" and "pilot ": all 60 refused with ConfigError and the ticket's message (secrets/channel/detector/llm: "<name>= is for tests; configure backends.<name> in pilot and prod"; clock and timeout_s: "<name>= is for tests; it is refused in pilot and prod").
- Falsy objects in pilot (falsy channel and secrets objects, detector 0, llm "", timeout_s 0, 0.0, False, clock 0, sources {}, tools {}): all refused.
- Several overrides at once: the first in order secrets, channel, detector, llm, clock, timeout_s is named (secrets).
- hold_run_ids= in pilot: not refused by the override check (the build went on to the next error: secret pg-dsn cannot be read, since the probe has no secrets).
- Vault: for `vault` (secrets) and `vault_transit` (signer), pilot and prod, auth omitted and `auth: token`: load_config accepts, build refuses with "environment <stage>: refused: <capability>: <kind> auth token (the default; set auth: kubernetes (recommended) or auth: approle)". With auth kubernetes and approle the build was not refused by that rule (it stopped at a missing secret).
- Demo: channel, detector, llm, clock, timeout_s and secrets (with the secret present) accepted (App returned). In demo timeout_s of 0, -1, inf, nan, True, 3601, 0.0005 and "5" is refused with "timeout_s= must be an int or float between 0.001 and 3600".
- Probe artifact to note: the first demo line `[demo] secrets=` used a secrets object without the needed secret, so it stopped at "secret fixture-token cannot be read"; the later line with the secret present returned an App.

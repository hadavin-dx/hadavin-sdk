## Safe reset for demos (promoted from the public demo)

promoted from the public demo repo duplicate-proof-lead-desk-n8n at 43110e7 (its `scripts/reset.sh`, `reset.ps1`, `reset_check.py`).

### What it does, in plain words
A demo leaves files behind (a database, its lock file, logs, process-id files). `hadavin_sdk.safe_reset` deletes exactly the files one config file names, and only after every check passed. Without `--apply` it is a dry run. It deletes only files, never folders, and never stops a program.
Refuses (nothing deleted): a path that does not resolve (symbolic links and `..` followed) to a place inside the data folder (exit 2); a data folder that is a filesystem root, the home folder or above it (2); a process listed in a process-id file that is still running or a process-id file that does not hold one number (6); a lock file held by another process or one that cannot be tested (3); a loopback port that still answers (4); any stage except `demo` (7; `pilot` and `prod` are never reset; any non-stage value, including the old name `dev`, is a config error, 2).
Wrappers: `tools/reset.sh`, `tools/reset.ps1` (thin; all logic is in Python).

### Rung table
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| safe reset | wipe demo working files safely | 2/4: exists in the public demo, promote (core has no equivalent; checked in handover/core/REPORT.md ORDER 254 step (a)) | demo scripts at 43110e7 | refusal rules that protect pilot and prod data | KEEP-CODE (generalised) |
| path confinement | stay inside data folder | reuse `config.confined` | existing core function | none | reused; one bug fixed |

### Demo names removed
lead_desk, lead_desk.server, demo_only.fakes_server, desk.pid, fakes.pid, DESK_DB_PATH, DESK_PORT, DESK_FAKES_PORT, the hard-coded `data/` folder, RESET_STOP_WAIT_SECONDS. Names, folders, pid files, lock files and ports now come from one validated config. The demo stopped processes; core refuses instead (least privilege, per the brief).

### Bug fixed at the shared choke point
`config.confined` crashed with `ValueError` on a NUL character (callers catch `ConfigError` only). Now `ConfigError`. Sibling search: all `confined` callers go through it.

### Tests that fail on old code
Old code = origin/main 2a8c2aac in a clean detached worktree. `tests/test_safe_reset.py` fails at collection (module missing; trivially). The `confined` NUL test fails for real: `ValueError: embedded null character`. Raw: evidence-pd-reset/old-code-run.txt, old-code-confined.txt (in /home/user/build).

### Measured results (head: see below)
- tests/test_safe_reset.py: 56 passed (includes a seeded fuzz of 300 path entries, seed 20261112).
- tests/reset_mutants.py: 19 of 19 good (17 killed, 2 crash by design); new CI step added.
- ruff check, ruff format --check: clean. bandit -ll: exit 0, 0 issues. tools/scan_repo.py: exit 0.
- Full pytest at head 89ef13c9: 10150 passed, 458 skipped, 1 failed = the known flaky test_the_timing_harness_flags_a_quadratic_stand_in (not touched). An earlier run failed test_the_old_stage_word_is_gone because the config key was called `stage`; renamed to `environment` (no exemption added).
- stage_mutants.py: see /home/user/build/evidence-pd-reset/stage-mutants.txt (was still running).
- Config key is `environment: demo|pilot|prod`.

### Not verified
PowerShell wrapper never run (no PowerShell here; text-checked only; run once on Windows). Windows liveness and lock code untested. Anchor-root check is equivalent to the parents-of-home check on POSIX (cannot be mutated there).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac

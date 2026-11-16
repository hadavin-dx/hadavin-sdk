# bd-peel report: run_id on Runtime.handle (ORDER 174 q382(1)), head 84abdf6, PR 87 (draft)

## NOT done / uncertain (first)
- No EGM plan review, evidence runner or egm:* result review was run by me (lead runs them). EGM-GATE steps (b), (e), (f), (g) are open. I wrote the ticket and built; I did not review my own work.
- Postgres not run: 454 tests skipped (HADAVIN_TEST_PG_DSN not set, CI has the service). The same-id refusal in `store/postgres.py` is read from the ticket's cite, not exercised here; the peel's tests use MemoryStore only.
- GitHub CI (CodeQL, SonarCloud, CodeRabbit) not seen: no check output read after the push.
- bandit: run with `uvx bandit` (latest, not the pinned 1.9.4), `-q -r src demos tools -ll`, exit 0; the pinned version was not run (not in the venv).
- The duplicate case raises `StaleState` only. The "return the existing run if agent/principal/trigger_ref match" step (AK-G2 D2/D2b/D2c) is NOT here (ledger BL-core-peel-002, stays in AK-G2-a).
- Side finding `trigger_kind="webhook"` NOT fixed: AK-G2 item 6 uses "event" and says the run shape needs no change. Ledger BL-core-peel-001 (lead decision).
- `tools/mutation_runner.py` could not be used (it runs `--noconftest`; the tests need `tests/conftest.py`: baseline failed "the unmutated copy does not pass its tests"). Used `handover/tools/peel_mutants.py` (same per-mutant temp copy, real conftest). Ledger BL-core-peel-003.
- Brief said draft PR, preamble rule 9 says ready PR: I followed the brief (draft).
- Draft PR is on origin; handover files (ticket, ledger rows, evidence, tools, this report) are in /home/user/hadavin-sdk/handover on branch core/cloud-handover, NOT committed by me, and not in the PR (handover/ does not exist on main).

## What changed (PR: 3 files, +156/-1)
- `models.py`: `RUN_ID_PATTERN = run-[0-9a-f]{32}` next to `new_id`.
- `agent_loop.py`: `InvalidRunId(ValueError)`, `_checked_run_id`, `handle(..., *, run_id=None)`; the id goes to `Run(...)`; `create_run` (first write) refuses a repeat with `StaleState`. Diff in `handle` is 3 lines plus docstring (hot-file care for P5c / P4c-2).
- `tests/test_peel_run_id.py`: 26 tests (T1-T8): given id used; repeat refused with model calls and audit notes unchanged; default ids well formed; 19 hostile ids (non-strings, newline, NUL, unicode digit, upper case, ...); exhaustive one-character damage of a valid id (about 1,000 cases); AK-G2 36-character shape accepted; keyword-only; independent oracle regex (the test does not judge the pattern with itself).

## Evidence (raw files in handover/evidence/PEEL-run-id/)
- Fail-before on base 0dabf1f (src stashed): `fail-before-base-0dabf1f.txt`: 25 failed (new-name tests fail by TypeError/DID NOT RAISE, no collection error; T8 passes only because it compares the shimmed fallback to itself, so 25 of 26 fail).
- Mutants: `mutants-final.txt`: 9/9 killed for the stated reason (ignored id, validation removed, length loosened, match for fullmatch, upper-case hex, repeat swallowed, non-string accepted, positional keyword, default id shape). A first run showed MP3 SURVIVED because the test used the pattern under test as its own oracle; fixed (independent oracle) and re-run.
- ruff check: All checks passed; ruff format --check: 283 files already formatted.
- Full suite at head 84abdf6 via heavy.sh: `full-suite.log`: `9970 passed, 454 skipped, 28 deselected in 249.92s`, `exit=0` (CI marker filter `not live and not perf`). No truncation (summary present).

## Ledger: BL-core-peel-001 (MAJOR, lead decision), -002 (MAJOR, AK-G2-a), -003 (MINOR).
R-numbers: R448 (rung table in ticket), R368 (no double-applied), R449 (no stage names used). No spend, no live call, no secret. Processes: all background jobs finished; none left. Tokens: not measured.

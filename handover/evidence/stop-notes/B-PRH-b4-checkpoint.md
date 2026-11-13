# B-PRH-b4 checkpoint 1 (23:34 UTC)
Worktree /home/user/build/B-PRH-b4 (branch wip/prh-b4-local from e852b577), venv B-PRH-b4-venv, runner PRH-b4-run.sh.
DONE: Issues 1 and 2 REPRODUCED by running (both leak; main leaks too, so not a regression): scratch/repro-before.txt, repro-main.txt.
Code (uncommitted): hidden.readings() shared helper; runmap consuming pair views with own rule _consuming_wins; decodes()/undo(consume);
entity control refs kept as characters; tools._scrub uses readings + per-secret rule for char/consuming readings, _decoded_readings;
pass counter (_Work, MAX_REDACT_PASSES=24, measured worst 17). Contract: oracle consuming reading, 232 cases promoted.
NEXT: fixture rows + unit + tools rows, mutants (46 + new, expect fragments, pin 44), NOT_PROMISED converse/pins, docs, Cf CI, perf shapes, evidence, full pytest once.
BLOCKERS: none. Commit: none yet.

## Checkpoint 2 (about 23:55 UTC 2026-11-11)
Committed 0561c618 (not pushed). Done: Issues 1-9 in code/tests/docs. ruff check/format, bandit -ll, scan_repo exit 0 (logs /home/user/build/B-PRH-b4-logs/). Fail-before on e852b577 src: 58 new test ids, 49 fail, 3 pass (count test, converse test, clean control row), 6 perf ids not run in that pass.
Running via heavy.sh: full pytest (own Postgres 56347), prh_mutants, stage_mutants. Next: perf alone (G4 + sgr0 shapes + large colourised log), results into /home/user/hadavin-sdk/handover/evidence/PRH/b4/, gitleaks, push, notes.

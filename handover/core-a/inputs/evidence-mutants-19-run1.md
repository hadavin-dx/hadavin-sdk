# evidence-mutants-19 (facts only)
Tree: _local\scratch\wt\lead-mut19 (detached 04886e739 + one-line edit in tests/endpoint_mutants.py, G33d). Copied (no .git, no .venv) to WSL Ubuntu ~/hvmut19. No PostgreSQL needed (no REQUIRE_PG in tests/conftest.py; script docstring: no database); no container created.
WSL had uv 0.10.2; `uv run` fetched CPython 3.13.12 and built .venv in the copy (normal sources). Nothing else installed.

Command: `uv run python tests/endpoint_mutants.py G33d` (step 1). Duration 3.8 s.
Result: the script stopped before running any mutant with an uncaught ValueError; the exit code printed by `echo $?` after the command was 0 (python_exit=0, see raw/g33d-exit.txt; odd next to a traceback, reported as observed).
Last lines of the log (raw/g33d.log):
  File "/home/rakesh/hvmut19/tools/mutation_runner.py", line 454, in _run_mutants
    raise ValueError(
ValueError: mutant 'G34 QuietWSGIHandler._write sends at once (the answer is four writes again)': test_file 'tests/triggers/test_d_fix13_single_write.py' is not one of the copied tests

Cause visible in the file: tests/endpoint_mutants.py line 211 `TESTS = [TE, TC, TS, TP, TW, T6, T8, T9]` has no T13 (line 129 defines T13; mutant G34 at ~1290 uses it). The runner checks every mutant's test_file against TESTS before the `only` filter, so the check fails for G33d too and for the full run.
Step 2 (full run): not run (same check fails before anything runs). No mutants run: 0 killed, 0 crash-accepted, 0 survivors; no "N of N run are as expected" line produced. No ERROR anchor line.
Cleanup: no container made; hvmut19 check `docker ps -a --filter name=hvmut19` showed none; WSL copy and temp files removed.
Files created: this file, raw/g33d.log, raw/g33d-exit.txt (this folder).

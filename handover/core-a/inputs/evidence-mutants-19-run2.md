# evidence-mutants-19-run2 (facts only)
Tree: lead-mut19 with 2 one-line edits (G33d anchor, TESTS now `[TE, TC, TS, TP, TW, T6, T8, T9, T13]`, line 211). Copied to WSL ~/hvmut19. WSL python: CPython 3.13.12 (uv), linux.
Command: `uv run python tests/endpoint_mutants.py G33d > log 2>&1; echo EXIT=$?` -> `EXIT=0` (same line, no pipe). grep -c Traceback = 1.
Log ends: `RuntimeError: the unmutated copy does not pass its tests` (tools/mutation_runner.py line 527; baseline pytest of TESTS returned nonzero). No mutant ran. Full script: not run (same baseline check precedes every mutant).
Baseline reproduced by hand in the copy (pytest -q --noconftest -x, TE + T13): `1 failed, 309 passed, 2 skipped`; failure tests/triggers/test_d_fix13_single_write.py::test_every_answer_is_one_write[400-garbage]: `AssertionError: []  assert 0 == 1` (len(writes)==0).
T13 file alone, 3 repeats: each `3 failed, 46 passed`: test_every_answer_is_one_write[400-garbage], test_the_one_write_holds_status_line_headers_and_the_whole_body[400-garbage], test_the_bytes_on_the_wire_are_those_of_the_stdlib_writes[400-garbage]. Same each time.
Counts: 0 killed, 0 crash-accepted, 0 survivors, no summary lines. Exit code of python reported as 0 despite the traceback (as in run 1).
Cleanup: no container made; WSL copy and temp files removed.
Files: evidence-mutants-19-run2.md, raw/run2-g33d-and-t13-baseline.log

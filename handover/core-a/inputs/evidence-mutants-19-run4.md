# evidence-mutants-19-run4 (facts only)
Tree: lead-mut19c (core-a ef976f98a + G33d anchor edit). TESTS = [TE, TC, TS, TP, TW, T6, T8, T9, T13, T14]. WSL Ubuntu.
1. test_t5_wsgiref.py + test_d_fix13_single_write.py + test_d_fix14_single_write_edges.py (pytest -q --noconftest, runner-style ini): CPython 3.13.12: `104 passed in 8.44s`; system CPython 3.12.3: `104 passed in 8.63s`.
2. `python tests/endpoint_mutants.py G33d > log 2>&1; echo EXIT=$?` run from a script file: EXIT=2; grep -c Traceback = 0. Log ends with 3 ERROR anchor lines (occurs 0 times in src/hadavin_sdk/triggers/server.py, must be 1):
   - G8c send_error is the standard library's again (an HTML page as the refusal)
   - G16a an HTTP version of 2.0 or higher is answered 505 again
   - G16b a request line with no version is not closed quietly
   server.py sha256 d0178d6e... differs from earlier runs (d-fix16 rewrote send_error). No mutant ran; full script not run.
CORRECTION to runs 1-3: exit codes there ("EXIT=0") were read through `wsl bash -lc '...$?'` typed on the command line, which does not pass `$?` through (a control `sys.exit(3)` also showed 0/empty). Those exit values are NOT reliable. Run 4 used a script file: control sys.exit(3) -> CTRL_EXIT=3, script -> EXIT=2.
Counts: 0 killed, 0 crash-accepted, 0 survivors.
Cleanup: no container; WSL copy, ~/venv312, ~/g33d4.log, /tmp/e.ini removed.
Files: evidence-mutants-19-run4.md, raw/run4-g33d.log (plus scratchpad g.sh, outside repo).

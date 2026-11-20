# evidence-mutants-19-run3 (facts only)
Tree: lead-mut19b (core-a ecabe6ab0 + G33d anchor edit). TESTS = [TE, TC, TS, TP, TW, T6, T8, T9, T13, T14]. WSL Ubuntu, CPython 3.13.12 (uv); also system 3.12.3 (venv ~/venv312 via uv with --python /usr/bin/python3, removed).
1. T13 `-k garbage` (3 tests) on 3.13.12: `3 passed, 46 deselected`.
2. `uv run python tests/endpoint_mutants.py G33d` ; echo EXIT=$? -> EXIT=0; grep -c Traceback = 1; last line `RuntimeError: the unmutated copy does not pass its tests`. No mutant ran. Full script not run.
3. Baseline by hand (runner's pytest line, -x): first failure tests/triggers/test_t5_wsgiref.py::test_garbage_instead_of_a_request_line_is_400_empty, `Seen(raw=b'', end='closed')`, log line `trigger status=400 sender=- (refused before the endpoint)`; `1 failed, 411 passed, 4 skipped, 1 deselected`.
4. test_t5_wsgiref.py alone, 3.13.12: `6 failed, 42 passed` (repeatable): test_garbage_instead_of_a_request_line_is_400_empty; test_f1_http_version_2_or_higher_is_400_empty_never_a_5xx[HTTP/2.0, /3.0, /9.9, /10.1]; test_n10_refusals_before_the_signature_are_debug_and_a_verified_request_is_info. Single garbage test x3: failed each time.
5. Same wsgiref file on system 3.12.3: also fails (raw=b'' for garbage and HTTP/2.0.. cases; see raw/run3.log for counts).
Counts: 0 killed, 0 crash-accepted, 0 survivors. Not run: full script.
Files: evidence-mutants-19-run3.md, raw/run3.log.

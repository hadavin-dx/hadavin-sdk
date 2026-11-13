# NEEDS CODE and NEEDS DOCS (for the demo session; core lane made no code change)
Sources: standing/C1, C3, C5, C7, C8, C10 (agent reports; items marked "reproduced" I ran myself).
1. scripts/run_real_check.py uses a stock argparse parser: a secret or address typed on the command line is echoed in the error (`invalid int value: '<key>'`, `unrecognized arguments: <address>`). REPRODUCED with a fake key built from parts. run_live_check.py (RefusingParser, line 134) and hubspot_probe.py (_Quiet) do not echo. Class: one parser per script. Next step: give run_real_check.py the same refusing parser; add a test that no argv text appears in any usage error.
2. scripts/feed.py raw tracebacks: `--index 0` / `9999` (ValueError), desk not running (URLError). REPRODUCED. Next step: catch, one plain line, exit 2, test.
3. run_real_check.py `--dry-port-base 99999` -> "(OverflowError)" text blames a file or folder (C1 row 10, C7 #21). Next step: range check 1..65535.
4. run_live_check.py: --price-date, --effort, duplicate --model with different prices unvalidated (C1, C7 #82). Next step: validate and refuse.
5. read_approvers / read_leadflow / read_secret_file on a FIFO block (C7 #137, 30 s timeout); scripts refuse FIFOs. Next step: special-file check in the library readers.
6. C5: docs/tests.md:26 crash_desk PYTHONPATH (src vs src:.; NOT reproduced by me), stale test count 2516 vs 3982, README "about 20 minutes".
7. C8 (REPRODUCED): versions.md:9 and docs/tests.md:79 describe `pytest --collect-only -q` as one line per file; it prints one line per test (3885 lines); only -qq gives per-file lines.
8. Docs items already in standing/C10/docs-fix-v1.patch (not applied).

# fix-f8-r2 (round 2, last), checkpoint at ~14 min, 2026-11-16 (UTC)

## NOT DONE / NOT YET VERIFIED (first)
- Final run_all.sh after the last self-test additions (two patch-only cases) is still running; its result is not yet recorded here.
- Re-run of three mutants that survived the first mutation pass (files_names, f002_links, f002_conn_struct) against the new cases: still running.
- Three mutants survive by design and are NOT fixable by a test: cross_try (the try around cross_file is now unreachable because cross_file itself guards every shape), arg_missing_value (Python raises the same IndexError anyway), expect_json_object (update() raises the same error anyway). They are equivalent mutants.
- REPORT.md: final counts (self-test, mutation) and refreshed old-checker self-test numbers (raw/selftest-oldchecker.txt is stale) still to be written.
- Not checked: a real n8n import; secret values of 5 characters or fewer; credential kind of web address passwords (only presence of a credentials block).

## DONE
- check_flows.py: plain-words header at top of output (verdict, exit 0/1/2, WARN/FAIL, 6 vs 8 known open problems, 3 decisions); every header line starts with `#`.
- REPORT.md: "Start here: what you must decide" box (import NOT KNOWN, $env, webhook password, StuckRow/AlertRow, M1/M3), terms defined before use, M1-not-rerun caveat kept, unverified list extended.
- 7 false-pass Majors: settings and webhook shape (clean FAIL), cross_file guarded and file handle closed, `--files all` on empty folder FAIL, unknown `--patch-checks`/`--allow` exit 2, more $env forms (`$env["X"]`, `process.env`) and literal inside `{{ }}` expression, webhook/form authentication without credentials FAIL, credential kind check and `--expect-credential` name check (run_all passes both real names), usage errors exit 2, duplicate JSON keys FAIL, sticky note text not read as expressions.
- selftest.py: new cases for each of the above plus F-002 content, F-008 settings, node_diff (added, removed, changed, settings, top level), WARN no-retry, WARN write after swallowed error, secret list, argument errors, and a "no Traceback" guard on every case; skipped cases listed by name.
- Result before the last two cases: run_all exit 0; self-test 467 as expected, 0 not, 32 skipped; checker output on real flows unchanged (8 known open problems patched, 6 pristine; strict 4 FAIL).
- Own mutation pass (remove one check at a time, 42 mutants): 35 killed in the first pass; 7 survived (3 equivalent above, 3 being re-run, 1 cross_try counted in the 3).

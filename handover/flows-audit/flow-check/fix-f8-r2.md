# fix-f8-r2 (round 2, last), checkpoint at ~14 min, 2026-11-16 (UTC)

## NOT DONE / NOT VERIFIED (first)
- Real n8n import never tried; secret values of 5 characters or fewer pass; web address password credential checked only for presence of a credentials block.
- 3 of 42 own mutants survive: cross_try, arg_missing_value, expect_json_object. All three are equivalent (unreachable or same error raised by Python anyway); no test can catch them.
- Mutation run was by me, not independent.

## DONE
- check_flows.py: plain-words header at top of output (verdict, exit 0/1/2, WARN/FAIL, 6 vs 8 known open problems, 3 decisions); every header line starts with `#`.
- REPORT.md: "Start here: what you must decide" box (import NOT KNOWN, $env, webhook password, StuckRow/AlertRow, M1/M3), terms defined before use, M1-not-rerun caveat kept, unverified list extended.
- 7 false-pass Majors: settings and webhook shape (clean FAIL), cross_file guarded and file handle closed, `--files all` on empty folder FAIL, unknown `--patch-checks`/`--allow` exit 2, more $env forms (`$env["X"]`, `process.env`) and literal inside `{{ }}` expression, webhook/form authentication without credentials FAIL, credential kind check and `--expect-credential` name check (run_all passes both real names), usage errors exit 2, duplicate JSON keys FAIL, sticky note text not read as expressions.
- selftest.py: new cases for each of the above plus F-002 content, F-008 settings, node_diff (added, removed, changed, settings, top level), WARN no-retry, WARN write after swallowed error, secret list, argument errors, and a "no Traceback" guard on every case; skipped cases listed by name.
- FINAL: run_all exit 0; self-test 469 as expected, 0 not, 32 skipped (was 368/0/20; 101 new cases, 12 new skips by case name listed in raw/selftest-new.txt); old checker on new cases 91 as expected, 378 not; checker output on real flows unchanged (8 known open problems patched, 6 pristine; strict 4 FAIL).
- Own mutation pass (remove one check at a time, 42 mutants): 39 caught after two extra cases (3 caught only after adding patchonly_ cases without the diff); 3 equivalent survive.

FAILED/UNCLEAR: nothing failed. Unclear/not run: Windows not run (read-only review only); R20 "swallowed" has no pre-made mutant, I made two own variants (env={} and not-caught) plus the existing v5 "old wording" mutant. My 6th mutant row (K6+K10) was only a repeat of K6 (mislabelled, only K6 applied); K6+K10 together not run.
Tree-C4 head 61ded9e (+patches). Mutants planted only in a copy (tmp-C4/mut, since removed). tree-C4 untouched except possibly nothing (PYTHONDONTWRITEBYTECODE=1 set from run 2; run 1 may have written __pycache__).

| test | right reason? | 20-run passes | TMPDIR-dependent? | Windows risk |
|---|---|---|---|---|
| R20 test_a_config_file_whose_read_fails_is_refused_with_one_fixed_line | yes, 3 mutants killed at the line-42 equality (swallow: prints missing-names list; old wording: "refused: FileNotFoundError"; not caught: "refused: the settings: ... (PermissionError)") | 20/20 | no (3 passed with TMPDIR inside copy, /dev/shm, outside, and nonexistent dir) | low: Path.read_text patched by name, PermissionError is an OSError on all OS; print newline via capsys is "\n"; a_terminal fixture is the cross-platform one |
| K6 test_a_flag_that_only_the_format_fold_can_read_is_found | yes, mutant K6 gives ([], 0) != (['test_a'], 1); other test still passes | 20/20 (also alone 20/20) | no | low: sources in docstring so CRLF checkout is normalised by the compiler; breaks under python -OO (__doc__ None, KeyError) |
| K10 test_a_flag_split_by_a_format_field_is_found_by_the_glued_pieces | yes, mutant K10 gives ([], 0) != (['test_a'], 1); other test still passes | 20/20 (also alone 20/20) | no | same as K6 |
Unmutated: 3 passed (run01 log). Both files together 20/20; start_prompt file 129 passed.
Logs: out/C4/61ded9e-run01-unmutated.log, 61ded9e-flaky-*-N.log, 61ded9e-mutants.log
Test files not run: everything else (task scope = these 2 files; also test_start_prompt_hardening and -k keep of test_take_script_refusals as side checks).

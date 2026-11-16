# PD Part 6 round 13, design reviewer (egm:egm-design), head 63996217 (condensed by lead; read-only review, nothing run)

Blockers: 0. Majors: 1 (unconfirmed). Minors: 7. Nits: 2.

M1 tools/fixed_run.py:30 `subprocess.run([exe, *argv[1:]], ...)` non-literal list: ruff S603 expected (builder confirms it fires). Waivers removed, none added, so the line needs a restructure. CHANGELOG claim "needs no waiver anywhere else" is wrong while it fires. (Lead ruling pending.)

m1 tests/test_mode_banner.py:1587 comment "refuses in prod for being dev-only" = old stage word in a test (lead rule: none anywhere, tests included). CHANGELOG.md:204 "outside `dev`" is old history text.
m2 test_mode_banner.py:3768 `getattr(mb,"READ_ERRORS",None) or mb._READ_ERRORS`: dead compatibility code; use mb.READ_ERRORS.
m3 fixed_run.py:24 refuses only shell=True; executable=, cwd=, preexec_fn= pass through (executable can override the looked-up program). Allow an explicit kwarg set; test pins only shell refusal (R13A9).
m4 demo_only_guard.py:81-97 runs a sibling file via exec_module; a run_fixed returning a fake CompletedProcess makes the guard pass with an empty file list; guard does not check non-empty list. Consider keeping the single git call inside the guard. A foreign installed `tools` package could be picked up when not run with -I (CI runs without -I).
m5 scan_repo.py:17-20 falls back to bare `from fixed_run import`; inconsistent with the guard's path fallback; traceback under -I (fails closed).
m6 prod banner tag "LIVE" and prose "pilot or live": confirm "live" is an intended display word (old stage word is "dev").
m7 pre-existing suppressions in touched files (backends/table.py:257,259; config.py:52,443,485; several tests) are not added by the diff; "no suppressions anywhere" is not true of the tree.
Nits: test_banner_mutant_table.py fail-before comment says 332 rows while ROW_COUNT is 333; odd wraps at demo_only_guard.py:360-362.

Checks: all broad catches named (app.py:273,301,320,479; mode_banner.py:184,742,775); surprise errors propagate, no banner returned; no masker row shows more than main; no suppression added; no fail-open found beyond m3-m5.

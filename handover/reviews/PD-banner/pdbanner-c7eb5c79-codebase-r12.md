# PD Part 6 round 12, codebase reviewer (egm-codebase-details), head c7eb5c79

Read-only, snapshot /home/user/build/snap/pdbanner-c7eb5c79/. Condensed by the lead session from the inline report. Result: 0 Blocker, 3 Major, 8 Nit. No fail-open path found. Nothing was run. No SonarCloud claim.

Suppressions on added lines of DIFF.patch: noqa 0, type: ignore 0, fmt: skip 0, pragma: no cover 0. Waivers: pyproject.toml:78-90 per-file BLE001 (app.py, mode_banner.py) and S603 (tests/fixed_run.py, tools/demo_only_guard.py, tools/scan_repo.py). Five broad except sites: app.py:295, :312, :471; mode_banner.py:731, :759.

M1 pyproject.toml:86-90 and tools/scan_repo.py:73-74: the S603 comment says "found on the PATH and run by its full path ... at those places only"; scan_repo.py calls subprocess.run(["git","-C",...]) directly with no which and no single entry point; waiver is file-wide; two near-identical helpers (fixed_run.run, demo_only_guard._run) pass **kwargs through so shell=True is not refused; scan_repo could reuse _run.
M2 pyproject.toml:80-85: BLE001 comment says "four sites" and "owner decision pending"; app.py:471 (post_card) is a fifth with no reason written; any new broad catch passes silently. _READ_ERRORS (mode_banner.py ~104) is fail-closed.
M3 test_mode_banner.py:3638-3639: test_each_unreadable_shape_seals... is a non-pin whose dd827d79 failure is only the missing name _UNREADABLE (does not count); also setattr(..., raising=False) on _services_in; needs tolerant getattr. Related: test_every_equivalent_mutation_has_a_reason (test_banner_mutant_table.py:447-455) rests on the new bm.EQUIVALENT name; unclear whether its old-code failure is behaviour.

Holding: _given tolerance (test_mode_banner.py:2217-2223); stage seal (app.py:236-244, :261-266, :292-293) and test :3593-3602; rows R12B1/R12C1/R12C2 by reading; EQUIVALENT entry reasoning; 320 rows counted = ROW_COUNT = CHANGELOG; test_pin_* headers say PASSES; @needs_node; once-test asserts len==1; CHANGELOG deepcopy, 3.14 label, derived listing count, decision text.

Nits: 1 expectation_nowhere_in_killer (test_banner_mutant_table.py:377-406) still loose (m.expect in p accepts any string constant; p in m.expect accepts invented text; startswith 4 chars; shadowing by last same-named function); real guard is the blocking mutant run. 2 CHANGELOG still lists masker pass "address" (code: URL, demo_only_guard.py:271, 282). 3 "logged once" is true for _warn_once only; banner_or_unconfirmed (mode_banner.py:732) logs every call. 4 "build does NOT fail" wider than code (_SEAL_ERRORS has five types). 5 _SEAL_ERRORS (app.py:81) and _READ_ERRORS duplicate: one definition. 6 stale 3-tuple fixture test_mode_banner.py:2742 (seal now 4 slots). 7 long lines (E501 not selected). 8 shutil.which searches cwd on Windows only. No row for the _stage non-str raise (app.py:242-243).

Not checked: any run; dd827d79 or 06ed4b4c claims; cast(BannerWords) typing; S607 on scan_repo.py cmd; DELTA lines 523-2599 beyond grep.

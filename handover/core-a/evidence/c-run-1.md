# c-run-1 evidence
Command: cd /tmp/ca-c-run && uptime > /tmp/ca-c-run1.load0; (uv run --all-extras --group test pytest -q -n 3 --no-header -p no:cacheprovider -rfE -m "not perf and not live" 2>&1 | tee /tmp/ca-c-run1.log | tail -40); uptime
(note: -rfE added; output redirected to log, run in background)
core-c sha: 9072e701f
Load start: 13:12:55 load average: 1.08, 0.87, 0.65
Load end:   13:19:01 load average: 4.26, 3.31, 1.86
Wall time: 366s (pytest reported 363.80s, 0:06:03)
Last 5 lines:
FAILED tests/test_b64_scan.py::test_no_run_no_extra_work - AssertionError: TB...
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
FAILED tests/test_runmap_enforce_map.py::test_e5b_a_conflict_puts_every_secret_entry_first_also_for_other_originals
4 failed, 15754 passed, 561 skipped, 76 xfailed in 363.80s (0:06:03)
(line 1 of 5, preceding the above: FAILED tests/test_b64_scan.py::test_tie_break_keeps_the_order_of_different_originals)
Counts: 15754 passed, 4 failed, 0 errors, 561 skipped, 76 xfailed
Failures (first error line):
- tests/test_b64_scan.py::test_tie_break_keeps_the_order_of_different_originals: AssertionError: TB-2.8 map 1; assert 'x <SECRET_1><TENANT_1> y' == 'x ab-<TENANT_1> y'
- tests/test_b64_scan.py::test_no_run_no_extra_work: AssertionError: TB-3.4 the work of a text with no run is not the base commit's; At index 9 diff: (1, 160) != (1, 154)
- tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked: AssertionError: vendor brand strings ... handover/BRIEF-PREAMBLE.md: 'Port.io'; handover/core-c/evidence/G4-build-notes.md: 'Port.io'
- tests/test_runmap_enforce_map.py::test_e5b_a_conflict_puts_every_secret_entry_first_also_for_other_originals: AssertionError: TB-2.11 E5b the secret entries were not put first; assert 'x <SECRET_1><TENANT_1> y' == 'x <SECRET_1>-ef y'
Known failures present: no_reference_material (yes), TB-2.8 (yes), TB-2.11 (yes), TB-3.4 (yes). Other failures: none.
Full log: /home/user/hadavin-sdk/handover/core-a/raw/c-run-1.log

# c-run-4 evidence
sha: e5d469a5fca6a8615607517166da0742c6181439 (/tmp/ca-c-p4)
cmd: cd /tmp/ca-c-p4 && uptime && (time uv run --all-extras --group test pytest -q -n 3 -rfE --no-header -p no:cacheprovider -m "not perf and not live" > /tmp/ca-c-run4.log 2>&1); tail -30 /tmp/ca-c-run4.log; uptime
load start: 13:19:52 load average: 2.46, 2.96, 1.82
load end:   13:26:26 load average: 3.58, 3.97, 2.74
wall: real 6m33.627s (pytest 391.07s)
last lines: 
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
FAILED tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice
2 failed, 15265 passed, 561 skipped, 15 xfailed in 391.07s (0:06:31)
counts: 2 failed, 15265 passed, 561 skipped, 15 xfailed
failing:
1. tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked -- AssertionError: vendor brand strings or unscannable files in the repo: handover/BRIEF-PREAMBLE.md: 'Port.io'
2. tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice -- AssertionError: SHOWN: 'db-7.corp.internal': 'www.evil.digitaldocs.example.com(anna.m@example.org_9例-_db-7.corp.internal_é例' -> '...(<EMAIL_1>_9例-_db-7[.]corp[.]internal_é例'
vs expected: 2 failed matches; 15265 passed matches; 561 skipped matches; 15 xfailed matches; both failing ids match.
mutants: globs tests/*host*mut* and tests/*g4*mut* matched NOTHING. No file contains 'host mutants'. Closest, run once: tests/p1d_a_mutants.py -> tail shows per-mutant tuples only (no '13 of 13' line): last 3 lines:
('A16', KILLED, 'tests/test_p1d_a_rows::test_row_H36a_card', True)
('A44', KILLED, ...K41_model, True)
('A45', KILLED, ...K41q_model, True)
'13 of 13 host mutants killed': not observed (no such script).

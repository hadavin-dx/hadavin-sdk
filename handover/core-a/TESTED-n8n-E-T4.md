# Tested state of the three items, 2026-11-20T09:07Z
Code and files are in earlier board snapshots; this commit records the tested state.
- T5 n8n template (retry fix, evidence-n8n-1/2/3): tests/triggers/test_n8n_template.py 91 passed (raw/n8n-template-tests-11.log, run by me), ruff clean; also inside the combined-tree run 1294 passed 0 failed (evidence/BATCH6-combined.log); 3+1 fresh review rounds, last round's Majors fixed; NOT run in n8n beyond the lead's evidence runs.
- Step E crash helper (src/hadavin_sdk/testing/crash.py): tests/test_testing_crash.py inside 1342 passed, 5 skipped (raw/D-fix5-tests.log, -n 3), mutants 16 of 16 (raw/E-evidence-3-mutants.log), 4 review rounds (round 4 extra pass: 0 Blocker/Major, nits fixed in d-fix5).
- T4 store/meter/gate contract tests (tests/contracts/*, tests/test_trigger_config.py, tests/test_redact_idempotence_property.py): core-b a11ab5132 head 696 passed 20 skipped; core-c 613611e25 head 354+201 passed, 8 xfailed (raw/MAINT-evidence-2.log, MAINT-core-c-2.log).
- failing test ids now: none in my files; the 10 strict-mode ones fail by design in the checkout with HADAVIN_REQUIRE_PG=1 and pass on the combined tree. batch7 (whole suite) running.

## Update 09:23Z: drift fixes and tests E5/E11
- tests/triggers/test_endpoint.py + test_t5_cases.py (new E5/E11 tests, stand-ins updated): 429 passed, 2 skipped (raw/D-fix6-tests.log); each new test fails when its guard is broken (scratch copies).
- n8n README follows the code (drift N1-N7): 91 template tests pass (raw/n8n-template-tests-12.log).
- Documents (ticket D/E, CRASH-MATRIX, WINDOWS-NOTES) follow the code: DRIFT-REPORT.md fix log.
- Independent evidence BATCH7 (evidence/BATCH7-summary.md): whole suite 12 failed (10 strict-mode by design, brand string in the lead's BRIEF-PREAMBLE.md, dblink env) / 12256 passed; combined tree 1327 passed 0 failed; mutants 90 of 90. The E5/E11 tests and README edits came after BATCH7 (their own runs above).

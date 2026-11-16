# Heavy lane evidence (scratch copy of hadavin-sdk at b4cce5b, not a real clone; raw logs in /tmp/sm-heavy-*.pytest.log, last line rc=)
Command: uv run --all-extras --group test pytest -q -p no:cacheprovider (timeout 2400).
| run | result | time |
|---|---|---|
| baseline 2 (no patch) | 2 failed, 9389 passed, 455 skipped, rc=1 | 290.61 s |
| patch A-02 | 2 failed, 9389 passed, 455 skipped, rc=1 | 293.86 s |
| patch B-01 | 2 failed, 9389 passed, 455 skipped, rc=1 | 299.79 s |
The same 2 tests fail in all three: tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked and tests/test_repo_rules.py::test_licences_are_proprietary. Both are probably caused by the scratch copy (handover/ content, no git repo) and are NOT confirmed in a real clone. Result: A-02 and B-01 add no failures in this copy. Not tested: n8n behaviour, any live service.

## Added 2026-11-16 (same copy, same command)
| run | result | time |
|---|---|---|
| patch C-01 | 2 failed, 9389 passed, 455 skipped, rc=1 | 291.57 s |
| patch D2-01 | 2 failed, 9389 passed, 455 skipped, rc=1 | 286.13 s |
Same two tests fail as in the baseline. Patches C-01 and D2-01 add no failure in this copy. The numbers of passed tests are identical to the baseline, so these runs show no new test was added or broken by the patches in this copy; they do not show the patches' own behaviour works (that needs the patches' own tests, which the patches may not add).

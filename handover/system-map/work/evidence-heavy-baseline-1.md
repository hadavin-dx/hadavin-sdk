# EVIDENCE (heavy lane): baseline run 1 of hadavin-sdk b4cce5b on a scratch copy (not a git repository), 2026-11-16 ~09:14 UTC
Command: uv run --all-extras --group test pytest -q -x -p no:cacheprovider (in /tmp/sm-heavy). Log: /tmp/sm-heavy-baseline.log (not kept in repo).
Result: rc=1, 8400 passed, 1 failed, 443 skipped, stopped after the first failure (-x), 255.99 s.
Failed: tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked: handover/BRIEF-PREAMBLE-studio-2026-11-06.md contains a vendor word; handover/reviews/P1a-idempotence-probe.txt is not UTF-8; also a file under handover/demo/portal (name cut off in the log). These are files under handover/ copied into the scratch, not source code. Note: the scratch has no git, so the test's own tracked-file list may differ from the real checkout; NOT verified in a real clone.
Not checked: the tests after the failure (run 2 without -x is running: /tmp/sm-heavy-baseline2.log).

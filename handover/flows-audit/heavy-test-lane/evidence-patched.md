# Evidence: patched run (EVIDENCE RUNNER, no judgement)
Worktree /tmp/heavy-patched at b4cce5b (full repo). Patches from origin/cloud/core-hardening (fetched; tip bf5f18383), handover/core-hardening/patches-ready/.
Run with uv (available). AWS_* env vars were present in the shell; unset for the full run and the lint/format steps (the first new-tests run had them set; it uses fakes).

## Patches (order C-01, A-01, G5-wording)
- `git apply --check` rc=0 and `git apply` rc=0 for all three. Modified: approvals/gate.py, audit/chain.py, audit/local_dir.py, config.py, defaults.py, guard/redact.py, runtime/tick.py, tests/test_p7_tick.py, tests/warden_port/test_gate.py. New: tests/test_a01_audit_reconcile.py, tests/test_c01_route_limits.py.

## New/changed tests on their own (log /tmp/heavy-new.log)
pytest tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py tests/test_p7_tick.py tests/warden_port/test_gate.py -> rc=0, 70 passed in 17.87s (a01: 5, c01: 10, p7_tick: 41, gate: 14).

## Gate
- `uv run --all-extras --group test ruff check` rc=0 "All checks passed!"
- `ruff format --check` rc=0 "301 files already formatted"
- `bandit -ll`: `uv run ... bandit` failed to spawn (not in uv env, rc=2); used /tmp/core-venv/bin/bandit. `bandit -q -r src demos -ll` (the ci.yml command) rc=0, 0 issues.
- Full `uv run --all-extras --group test pytest` (log /tmp/heavy-patched.log), PYTEST_RC=1:
  `2 failed, 9404 passed, 455 skipped in 282.03s`
  FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
    (handover/BRIEF-PREAMBLE-studio-2026-11-06.md 'Port.io'; handover/reviews/P1a-idempotence-probe.txt not UTF-8; handover/demo/portal/portal-design-v2.md 'Port.io')
  FAILED tests/test_repo_rules.py::test_licences_are_proprietary
    (10 items, first: handover/promotion-inputs/apexc/LICENSE not the proprietary licence text)
  Both failures name only files under handover/, none touched by the patches. Not checked here: whether the unpatched baseline fails the same two (compare with baseline evidence).

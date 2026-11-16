# Evidence baseline, commit b4cce5b (full worktree /tmp/heavy-base, 2026-11-16)
Runner: uv (network worked). AWS_* env vars were present in the shell; unset for pytest.
- uv run ... ruff check: rc=0 "All checks passed!"
- uv run ... ruff format --check: rc=0 "299 files already formatted"
- uv run ... pytest (log /tmp/heavy-base.log): rc=1; 2 failed, 9389 passed, 455 skipped in 280s
  - FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked ('[vendor-brand-string]' in handover/BRIEF-PREAMBLE-studio-2026-11-06.md and handover/demo/portal/portal-design-v2.md; handover/reviews/P1a-idempotence-probe.txt not UTF-8)
  - FAILED tests/test_repo_rules.py::test_licences_are_proprietary (10 extra items, first: handover/promotion-inputs/apexc/LICENSE not the proprietary licence text)
- bandit -ll -r src (/tmp/core-venv/bin/bandit; uv has no bandit): rc=0, 0 medium/high issues
Tail: 2 failed, 9389 passed, 455 skipped in 280.12s (0:04:40)
Earlier 5 scratch failures (README, CHANGELOG, .gitleaks.toml, docs manifest, .git): none appear in the full worktree.

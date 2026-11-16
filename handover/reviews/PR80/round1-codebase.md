# PR 80 (P5b1) round 1, egm-codebase-details, head 4003672 (condensed). Partial; ran nothing. Ticket read from pulse-clone (outside snapshot; snapshots now carry handover/tickets).
Blocker none in code read.
M1 evidence is for b2a65ea, incomplete (no R14 by id, fail-before, 45/45 mutants, class sweep, lock-in/import, library versions).
M2 full suite not green: 1 failed (Postgres socket, env) unnamed; re-run with Postgres.
M3 skipped rows count as failed evidence: test_provider_facts.py:163 (UsageMissing/UnpricedUsage not on branch, needs core/P4a) and contracts/test_llm.py:95; no dated record + next step; pickle path unexercised.
M4 PR diff far wider than ticket file list: also guard/textnorm.py, _confusables.py, _scripts.py, guard/diagnostic.py (~600 lines), app.py, defaults.py, textnorm_* tests, test_diagnostic*.py, diagnostic_mutants.py, third_party_notices.json, neverraise.py, tests/demo_askdata/test_validate_harm.py. Either diff base is not the P5a merge or the branch carries unrelated work (breaks ONE PR and BN-5 fail-before base). Lead: PR 80 base check needed.
Nits: neverraise import/scope; tests/test_diagnostics_hostile.py vs test_diagnostic_hostile.py names; R7 anthropic.py allow-list not checked.

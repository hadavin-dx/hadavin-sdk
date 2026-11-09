# PR 83 (P0t-followup) round 1, egm-design, head 7f24178 (condensed). Read-only.
Blocker none. M1 evidence is for 72389db not 7f24178 (mutants M1-M11 only; T1-T28 id mutants absent); new code (STAGE_WORDS, fold_name, check_id, commonwords.py, 5 id types in config.py:65-73) has no evidence or independent review. Need evidence runner on 7f24178 (3.12+3.13, ruff, bandit, fail-before, T1-T28 + M1-M11).
M2 "tenant named Pilot" leak: id check protects no live field (test_tenant_ids.py:18 no id stored); bare "Pilot"/"Demo" free text readable (redact.py:1188): redaction trade-off needs a recorded lead/owner decision or add id type where an id is first stored.
M3 quoted-list stage regexes (test_stage_names.py:478-493) traced by hand only; need run.
Minors: prose false positives for bare "test" in docs; config.py:387 casefold/strip vs ticket exact `dev` (wording); Literal duplicates STAGES (pin test not found); ID_NAME matches "tenant" anywhere; scope (about 600 test lines + leaf module) beyond tiny P0t, orders 126/132 not supplied.
OK: is_live != "demo" fail closed at app.py:83, deferred.py:48, registry.py:322, config.py:411; shared COMMON_WORDS pinned by identity.

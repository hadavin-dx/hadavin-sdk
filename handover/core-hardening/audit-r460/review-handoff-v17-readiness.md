# Hand-off v17 readiness review, round 4 (egm-implementation-readiness, condensed copy of the inline report), 2026-11-16
Target: CORE-PR-HANDOFF-v17.md (551 lines), -other-tracks, v17-CHANGES.md, v17-OPEN-FOR-LEAD.md, resolve-handoff-v17.md. Read-only; nothing run, no sha256 computed. Verdict: NOT YET "build without asking", close. 0 blockers, 3 majors, 7 minors. All 8 v16 majors closed in substance (two left residue, now V17-Ma1 and Ma3); v14 findings closed.

## MAJOR
- V17-Ma1 E0-S2-2 (line 435, last clause) still needs DB-1's held file applied, but 5.4 item 4 (line 256) and 5.6 item 1(c) (line 301) say the S-2a test applies two inline ALTER TABLE statements and does not read DB-1's file. S-2a is merge order 2, DB-1 order 4 (the migrate seam does not exist yet). Fix: replace "DB-1's file applied" with "the two inline ALTER statements applied".
- V17-Ma2 Lines 299-300 (5.6 items 1(a), 1(b)) give the DB-2 file at `evidence-handoff-v16/held-sql/spend_decrease_log.sql` but quote the v17 hash b4dfdf3a...1ec9; the v16 file (hash 4c37aea8...) has no lock_timeout. Item 1(k) (line 310) sends the upgrade hash to sha256-v16.txt (harmless, stale). Fix: cite evidence-handoff-v17/held-sql/ for all five files and sha256-v17.txt for all hashes.
- V17-Ma3 Build-order snippet (line 188) gives ALLOWED["llm"] = {"routes","gate"} and ALLOWED["detector"] = {"llm","gate"} and passes only gate=gate; 5.7 (line 324) and the 7.1 S-1 row say Deps.spend and "spend" in ALLOWED; app.py snippet never passes spend=. GuardrailPrice.from_settings(deps.spend) has no source (the v16 major, reopened by the old 5.3 text). Fix: put spend=cfg.spend and the "spend" entries in the line 188 snippet.

## MINOR
- Pass rule achievable but not mechanical: baseline real (raw-gate4-base-pytest.txt: 2 failed, 9364 passed, rc=1; the two failing tests scan handover/: test_no_reference_material.py and test_repo_rules.py::test_licences_are_proprietary). gate4_v17.sh runs pytest with -rs which replaces -rfE, so no FAILED lines print; "no new failing test id" cannot be read; script marks any non-zero rc bad; an id-based rule would pass a new offending file in handover/. Fix: use -rfs and compare ids plus the failure message to the baseline.
- 7.1 table rows omit pieces the prose assigns (S-2a row: Breaker, ChainReserver, ProcessCap, test_call_gate(), chain_status; S-1 row: chain_status, breaker settings).
- ChainReserver Ticket "carries both inner tickets" but Ticket(agent_id, day, worst, daily, monthly) (line 137) has no field for them.
- test_call_gate() (line 193) starts with test_: pytest would collect it when imported; rename.
- 5.6 item 1(j) (line 309) ambiguous: say port secdef_guard_v17.py into tests/test_secdef_guard.py.
- Conditional test table (line 451) covers L7, L10, L11 only; add L9, L18, L21, L22 effects on E0-DB-2, upgrade test, E0-DB-4, E0-S1-x.
- Stale: section 9 (line 515) names the v16 other-tracks file; line 188 cites app.py:162-167 (real 162-166); CI steps not run by gate4 omit semgrep and zizmor at line 427 (line 482 lists them).

## Prior findings
v16 Ma1 half closed (V17-Ma1); Ma2 closed; Ma3 closed (per-kind timeout exception classes left to the S-2a builder: lookup); Ma4 closed but contradicted by line 188; Ma5 closed (Ticket field minor); Ma6 closed (test_ name minor); Ma7 rule achievable (see minor); Ma8 closed (+0.049/+0.061 ms v16, +0.071/+0.099 ms v17, spread admitted). v14: layering closed; R2 closed; Limits source closed; start-up checks owned by S-2b; conditionals present; retry/release wording closed (one frozenset, defaults.RELEASE_EXTRA_STATUSES).

## Cites spot-checked (about 55 against src/hadavin_sdk, all located; 1 drift: app.py 162-166 vs 162-167)
store/migrate.py, llm/retry.py, llm/common.py, runtime/agent_loop.py, guard/injection.py, guard/bedrock_guardrail.py, config.py, store/postgres.py, llm kinds, limits.py, app.py, k1b/loop.py, backends/table.py, guard/redact.py:1162 (`"dev"` in _COMMON; plan keeps it and adds "demo"), cli.py, errors.py, ci.yml, tests/.

## A builder can do without asking
S-1 (except the line 188 snippet), S-2a (after fixing V17-Ma1; treat the 7.1 row as incomplete), S-2b, DB-1 (use the v17 path), DB-2 (gated by L9, PG 14 or newer), DB-3 (blocked by L22, L23 and the unwritten store code).

## Not checked
sha256 values; SQL held files, pg_v17.py, raw Postgres outputs, INVENTORY content ("49 of 49", "175 of 175" taken on trust); section 8.1, section 6, parts of 5.9 and 5.7, lines 364-380; vendor facts, PG 14 and 17 behaviour; other-tracks file beyond a few cites; .sonarcloud.properties:6, models.py:23-24, the 5-site tests/...:608 cites.

# Hand-off v16 readiness review, round 4 (egm-implementation-readiness, condensed copy), 2026-11-16T17:01:45Z
Read-only, nothing run. NOT READY. 0 blockers, 8 majors, 9 minors.
## MAJOR
- Ma1 B1 cases in E0-S2-2 and 5.4 item 4 (line 252) still need DB-1's held file; inline ALTER only in the "no held file" clause; G-4(i) test test_store_emits_update_for_negative_deltas has no definition or owner.
- Ma2 spend_nonneg_upgrade.sql, test_upgrade_fails_on_nan_and_rolls_back and its HELD pin have no owning PR; E0-DB-3 kill-switch/append-only tests need DB-2 SQL but sit in the DB-1 test file.
- Ma3 circuit breaker unowned and unspecified: settings not in the "exactly these" list (line 90), circuit_open not in codes/end-state table/_REASON_TEXT, no PR row, no place in admit order, no failure classification.
- Ma4 GuardrailPrice has no source: make(settings, deps) and ALLOWED["detector"] do not carry cfg.spend.
- Ma5 no composite Reserver for ProcessCap + Limits for the command line (5.8): order and rollback missing.
- Ma6 test seam contradicts S-1/S-2a: line 189 requires CallGate on injected NetworkLLM, S-1 has only WindowOnlyGate; S-2a refuses paid kind with WindowOnlyGate so 14+ test sites break; nobody owns re-pointing; S-1 protocol test cannot check CallGate.
- Ma7 "five rc=0" cannot pass: baseline pytest rc=1 (2 failed; L20 has no default); L19, L4, L13 no real default; L18 default only in OPEN-FOR-LEAD.
- Ma8 5.6(b) still has v15 timing (+0.075, +0.040); raw v16 files give +0.049 / +0.061; CHANGES claim "two sets" not true. 175 of 175 confirmed.
## MINOR
Mi1 RELEASE_EXTRA_STATUSES three descriptions; Mi2 census owner C6 vs C1,C2,C5; Mi3 spend_scope/KeptTotal wiring; Mi4 Ticket.daily/monthly meaning, route=None; Mi5 cli_* required vs guardrail-paid/llm-fake; Mi6 gate4 path v14/v15/v16 mix; Mi7 stale "Round: 8"; Mi8 O1 owner vs lead lists, L2,L3,L5,L6,L8 missing, "v15 holds"; Mi9 Grant(audit_read=), migrate(audit_reader_role=), reader_problems only prototype-specified.
v14 M1-M7: M2,M3,M5,M7 fixed; M1 stale numbers; M4 mostly; M6 half. 
Not checked: other-tracks beyond count, held SQL contents, ~400 cites, vendor facts.

# Hand-off v20 readiness review, round 7 (egm-implementation-readiness, condensed copy of the inline report), 2026-11-16
Target: CORE-PR-HANDOFF-v20.md, -other-tracks, v20-OPEN-FOR-LEAD.md, v20-CHANGES.md, INVENTORY.md, sha256-v20.txt. Read-only; no command run (hashes compared as text only). Verdict: NOT READY. 2 blockers, 8 majors, 6 minors. v19 majors: M1, M6 closed; M2, M3, M4 partly; M5 not closed. v20 added new sections and left the v19 text with wrong numbers, hashes, paths.

## BLOCKERS
- B1 Line 325 (5.6 item 1(o)) still names the v19 DB-3 file (evidence-handoff-v19/held-sql/spend_guarded_writes.sql, sha 40d8b345...) and the old design (NOT VALID, NFC/blank agent-id rules, "120 checks / 24 controls"). v20 file is evidence-handoff-v20/held-sql/..., sha 3aa7ed70...10cc (5.6c item 2, section 8, sha256-v20.txt). Lines 308-309 give v19 paths for DB-1/DB-2 (byte-equal copies, confusing).
- B2 DB-3 grants contradict: 5.6c item 6 (line 350) gives runtime role reserve+settle and operator role engage+release; line 325, v20-OPEN-FOR-LEAD line 8, L22 (line 594), L22/L23 row and secdef_audit_v20.py FUNCTION_POLICY give runtime engage+reserve+settle, operator release only. Two mechanisms named: `Grant` kind "function" in GRANTS (5.6(o), 7.1 row 5b) vs `migrate(function_grants=Mapping)` (5.6c item 6).

## MAJOR
- M1 Start-up query: three signatures (5.5b `secdef_problems(db, roles, owner)`; 5.6c `(connection, policy, roles)`; prototype `(db, *, roles, owner, policy)`); owner = pg_database.datdba (5.6c) vs migration role (5.5b/prototype); prototype raises KeyError when spend.operator_role is empty; "applied files" detection unspecified; spend.operator_role not in the 5.1 field list or S-2b row or E0-S1-2; store/secdef.py not in S-2b hot-file list; test file name differs (test_secdef_startup.py vs test_startup_secdef.py).
- M2 L19: check runs "when decrease record exists or audit-reader role exists" but detection is only to_regclass('spend_decrease_log'); role detection unspecified; 5.6(h) says active only when the log exists; 5.6(g2) ties it to gate G-4(v).
- M3 `limits status --check`: no source for "kill switch on longer than N minutes" (kill_switch.ts vs kill_switch_log, DB-2 not applied case); L24 default "alert only on decreases not made by spend_settle" cannot be built (decrease log has no function column; who = session_user); no alert channel/format; E0-L13 has no fixtures.
- M4 E0-F5 and L-2 store code have no owner PR; 5.10 row L-2 still says spend_add vs 5.10b spend_reserve/spend_settle; G-5(e) needs L-2 store code before DB-3 but L-2 is written after L22.
- M5 Conditional test table lacks L24 and L25 rows; L18 row names v19 scripts; L22 row refers to the conflicting per-role list.
- M6 Section 7.2 mixes v19, v14, v16, v20 names (header gate4_v19.sh; E0-S1-1 starts gate4_v20.sh and ends "gate4_v19.sh NOT run"; E0-DB-4 names pg_v19.py).
- M7 S-2b has too much for "one session" (60 minutes); no split.
- M8 Other-tracks file uses gate4.sh v14 with "all five rc=0" pass rule that the spend file says is impossible at baseline (two failing guard tests, L20); compare_gate4.py not applied to nine other-track PRs.

## MINOR
m1 lines 3 and 5 still say v19 / round 5; section 0 is still v19 text. m2 section 8 Files paragraph, section 9, section 10 head, 5.6(j),(p), 7.1 row 5b list v19 files/counts. m3 5.6(b) old v16 cost paragraph not retired (5.6c says 135 bytes). m4 hash abbreviations acceptable. m5 discovery left to the builder (flagged UNVERIFIED): breaker error classes, audit event fields, PostgresSettings signatures, detector reason codes, plan at cards.py:79, wheel packaging. m6 other-tracks keeps v10-v20 history sentences; "13 PR ids" vs 14; test_g4_parity.py not stated to exist.

## Checked, no finding
Files on disk (v20, v19, v16, v14 folders); five held hashes match as text across OPEN-FOR-LEAD, section 8, sha256-v20.txt (not computed). Held files are in audit-r460/evidence-handoff-v20/held-sql/, not audit-r460/held-sql/. 5.3, 5.7, 5.8, 5.9, 6 complete; v14 M2, M3, M6, M7 closed; v19 M1, M6 closed.

## Not checked
5 held SQL files (one REVOKE grep), allow_v20.py, raw outputs, pg_v20.py, src/ cites, test counts (177/27/3, 197, 30), lines after 596. No hash, script or command run.

# Hand-off v21 readiness review, round 1 (egm-implementation-readiness, condensed copy of the inline report), 2026-11-16
Target: CORE-PR-HANDOFF-v21.md (not read: 5.3, 5.4, 5.5, 5.7-5.9, lines 130-298 and 395-419), other-tracks (lines 1-30, 168-214 only), v21-CHANGES, v21-OPEN-FOR-LEAD, INVENTORY. Nothing run, no hash computed. Verdict: NOT READY. 1 blocker, 8 majors, 8 minors.
## BLOCKER
B1 The hash-pinned DB-3 file (held-sql/spend_guarded_writes.sql) contradicts the grant table: its lines 20-22 and 39 say the runtime role gets EXECUTE on kill_switch_engage and the operator role release only, while 5.6c item 5 says engage is operator only (L22b); line 41 says the store does not call these functions for a pseudo id while 5.6c item 8 says that default cannot work; lines 22 and 36 cite "5.6 item 1(o2)" and "(o3)" that do not exist. A comment edit changes the sha256, so the pin and OPEN-FOR-LEAD hash change too; or say in (o) that the header is superseded.
## MAJOR
- M1 5.5b item (3b) keeps the old signature secdef_problems(db, roles, owner); 5.6c item 4 says (db, *, roles, policy=None, owner=None) with owner = pg_database.datdba; L26 says the owner stays the migration role; the doc never says the migration role must equal datdba.
- M2 L19 stated three ways (5.6c item 4 record OR role; 5.6(h) only when log exists; 5.5b only to_regclass); E0-L19 has no case for record without role.
- M3 S-2b-1/S-2b-2 split incoherent: items 1, 2, 5, 6 vs startup_checks and idle check under S-2b-2; statement_timeout_ms in prose only; base `limits status` line in neither; hot-file column lacks store/secdef.py, config.py, tests/; merge-order text still says seven sessions (now eight); spend.operator_role and spend.kill_switch_alert_minutes missing from the 5.1 "exactly these" field list.
- M4 startup_checks(self, environment) has no config: operator role name, runtime role name source, policy, alert minutes have no carrier.
- M5 `limits status --check` not fully buildable: empty operator_role gives a false FAIL on `limits reset`; E0-L13 lacks fixtures for on-too-long, released-by-other, row-count WARN, audit-reader write probe; section 10 says the operator runs it weekly by hand while item 7 says nothing runs it.
- M6 E0-F5 tests code that does not exist at S-2b-2 (store calls to spend_reserve/spend_settle arrive only in the DB-3 move PR, row 5b).
- M7 Other-tracks row E0-O1 still says `sh evidence-handoff-v14/gate4.sh` and "all five rc=0", which cannot hold at the two-failure baseline; output folder and line 184 disagree with the new gate block.
- M8 L23 row in 7.2 says operator gets release only; table says engage and release; L22 row points to 5.6 item 1(o), which no longer exists.
## MINOR
m1 wrong cross-reference "item 5" for `limits status --check` (item 7) in 7.1 row 3, E0-L13, v21-CHANGES. m2 stale v19 names and raw-file cites (lines 267, 319, 324, 522, 629). m3 "secdef_guard_v21.py" should say v20. m4 L26 says three DB-3 functions; there are four. m5 section 10 first paragraph has v16-era text. m6 tests/test_g4_parity.py both "exists today" and "PLANNED". m7 discovery left to the builder (flagged UNVERIFIED). m8 v21-CHANGES says it folds things the text still carries.
## Per PR
Builder can build without asking: S-1 (apart from M3 fields), S-2a (as far as read), DB-1, DB-2. Cannot: S-2b-1, S-2b-2, DB-3 (OWNER-OPEN anyway), other tracks gate.

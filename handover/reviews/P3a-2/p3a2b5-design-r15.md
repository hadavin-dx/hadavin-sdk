# p3a2b5-design-r15: P3a-2 batch 5, head 989c02a3, round 15, persona design

Source: hand-back of the design reviewer (agent aa9f67fca92147e2d), saved by the lead (condensed). SECURITY / least-privilege path (no round cap). Read-only; evidence file did not exist when read, so every number and kill is the builder's claim. 0 Blocker, 2 Major, 4 Minor, 2 Nit, plus 1 escalation (O8). Snapshot /home/user/build/snap/p3a2-5-989c02a3.

## Major
- **Major A** O17 is not empty by logic (tests/test_migration_matrix.py:878, CHANGELOG.md:29): reason "this default right names no schema"; the effect is written `ALTER DEFAULT PRIVILEGES GRANT USAGE ON SEQUENCES TO PUBLIC` (:722) but PostgreSQL accepts `ALTER DEFAULT PRIVILEGES IN SCHEMA {o} GRANT USAGE ON SEQUENCES TO PUBLIC`: the PUBLIC twin of the O16 cell just built. Same false-reason class as r15-report Issue 4; CHANGELOG states "cannot exist by logic". Build O17 under C10 with the IN SCHEMA form (kind default_for_everyone) or list NOT BUILT with a true reason; then fix the 32 and the 548.
- **Major B** O13-O15 claimed unable to be extension members, false (tests/test_migration_matrix.py:1660-1671 C8_EMPTY_BY_LOGIC): a schema can be an extension member (ALTER EXTENSION x ADD SCHEMA s). C8 exists to test the evasion "make the object an extension member so verify skips it"; V106 shows verify has such a skip for extension rows; CREATE on the run schema with the schema made a member is that evasion, unbuilt behind a false reason. Build O13-O15 x C8 or give the true reason with a measured result; the r15 fix touched C8's table (explicit sets) but did not re-examine its reasons.

## Minor
- postgres.py:147-151 and CHANGELOG sentence: the connect() hole is stated, not closed, and its outcome unstated: migrate.py:1485 and :1637 call connect(...) as the `with` expression outside the inner try/except psycopg.Error (:1620), so a driver error from `SET TIME ZONE` surfaces raw (probably the exit-3 crash the CHANGELOG says "never" happens for the check); at step 8 (:1637) it is inside a try, for the first connect it is not. Say plainly what happens or wrap it.
- tests/test_migration_verify.py ~1409-1431: the one-statement pin is mock-level (monkeypatches pg.psycopg.connect, counts conn.execute); misses conn.cursor(), connection options/-c, the IAM branch; V112 plants only the visible form.
- tests/test_migration_verify_pg.py ~958-966: the 25P04 assertion accepts "25P04", "TransactionTimeout" or "OperationalError" (broad: connect loss also matches); must be narrowed after the first PG17 observation; say so in open items.
- BUILDER-notes.md:3-5: the questions-for-lead.md reword (r15 Issue 2) not done (file says "built and tested but OFF", "Safe default: keep it OFF" at handover/questions-for-lead.md:1831); the lead must apply the builder's replacement text before merge; carry it into the ledger.

## Nits
- tests/test_migration_rules.py ~1250-1256: the O8-wording guard accepts any "must be owned" sentence containing "during the run"; the PG17-claim test is one literal regex (`runs in CI on PostgreSQL 17`).
- matrix ~801-805 comment stale ("Only the effects of objects outside the map exist there"; O13-O16 now exist there too).
- Weak: `len(why) > 40` and `len(set(values)) > 1` check that reasons exist, not that they are true.

## Escalation (OWNER/LEAD, q-p3a2-o8-schema-owner; not a builder defect)
O8 default OFF is a real least-privilege gap: a non-superuser role outside the family that owns the run schema can drop or alter the package's tables and the run returns. OFF is acceptable only as a recorded owner-visible deviation; do not merge as "O8 done". The stated reason for OFF (ON would refuse the printed PLAIN_MIGRATION_ROLE_SQL setup) points at the setup: the least-privilege fix is to change the printed setup so the migration role owns the schema, then turn ON. Middle option: refuse only when the outside owner is not a superuser. Ticket line edit and the flip are owner-only. Stated honestly in migrate.py:1271-1278, CHANGELOG, and real-server ON and OFF cells.

## Held up (by reading)
O13-O16 x C10 are built by real-server cells (matrix:1405-1427, schema `<schema>_o`, real_connect); 15 of 16 empty-by-logic pairs are true and distinct; PG17 tests are visible skips and the PG16 fact lives in a test that runs on every server; CHANGELOG no longer claims a PG17 run; V104 quote of f"{schema}.runs" fixed.

## Not checked
Anything needing the evidence file (totals, gates, kills of V104-V112, old-code list); that V104-V111 `old` strings exist once in migration_verify.py (not in the snapshot); cleanup after the O16 cell; ci.yml PG17.10 claim; long CHANGELOG lines beyond 15, 29-32, 58; DIFF.patch; whether verify judges an IN SCHEMA PUBLIC default in another schema; whether an extension-member schema is skipped by verify; the "schema owned by a third role X" shape of O13-O16 is not built.

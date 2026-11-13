# P3a-2 batch 3e: PR notes (builder, 2026-11-12)

Branch core/p3a2-3e (from 7bc65cdc), pushed to wip/cloud-p3a2-3e. Security path (migration refusals and database rights): no round cap. The lead runs the EGM step (evidence runner, egm:* reviewers, resolve, drift report); the builder did none of it and says so.

## Rung statement (tool ladder, CODE-LAST)
- Rung 1, reuse: the existing matrix (tests/test_migration_matrix.py), mutant runner (tests/migrate_mutants.py) and oracle (tests/fixtures/oracle.py) are extended, nothing replaced.
- Rung 7, custom code: only the migrate refusal logic (src/hadavin_sdk/store/migrate.py, step "a driver error before the commit is a refusal, not a crash").
- No no-code tool and no MCP server applies: this is a database-rights safety guarantee, which stays in our tested code.

## Decisions that need the lead or the owner (read first)
1. B5 (the 8 pre-existing-state cells with no role argument): the brief said migrate must refuse all of them. Measured on this head (probe log /home/user/build/B-P3a2-3e-probe-b5.log): X17, X18, X19, X31, X32, X33, X36 return normally in the no-roles variant; X28 (a named role owns a table) is already refused. I made NO product change and pinned the measured behaviour. Reason: with no role argument the promise covers "everyone" (PUBLIC) only; a right held by one specific other role (a third role no argument names) is not promised, and refusing it would mean judging every role of the cluster. The "everyone" forms (X17e, X18e, X36e) and X28 are refused in both variants and are tested. If the owner wants the stronger promise (a refusal for any role of the cluster) that is a product decision with a cost (it would refuse databases that other applications share); say yes or no.
2. New "not promised" findings, pinned as returning normally in both variants (tests X01t, X11, X12, and C10 O24): a right of a third role on a table outside the map; a function made by an administrator and callable by everyone, not of this package; a SECURITY DEFINER function not of this package. The same wording applies to C13 (a right for a third role on a moved table is not promised; the cells use the named role or everyone).
3. K8 of the ticket ("a file hands a map table to a group the migration role belongs to, allowed since O5 is struck") cannot end in outcome (iii) on this head. Three forms measured and pinned (test_control_k8_cannot_end_in_iii...): written in the open, the text rule refuses it at step 0; by dynamic SQL the server refuses it (42501, no CREATE on the schema for the new owner); after an administrator gave the group CREATE, the run is refused before any file ran (that CREATE is itself an excess right). The ticket line is out of date: Issue 7 below.
4. B7 (C6, deferred trigger, repairable effect with role arguments): option (i) is right. The ticket says (i) for C6; the trigger fires at the COMMIT-time check after step 4 repaired the grant, so step 6 sees the excess and refuses. Pinned by the rule "repaired and carrier != C6 -> (iii) else (i)" and mutant V78.
5. Issue 7 of goldfish_review_report-3d.md is a ticket edit for the owner: the ticket's wording must change (K8 above; the 24-row state table; the count). Nothing built.

## Items
- Issues 1-6 and 8 of the 3d report: see the report. Issue 1 whole-form check of the CHANGELOG sentences (planted fault killed by V84); Issue 2 `_driver_error_before_commit` (a connection lost at any step before the commit gives exit 2, nothing kept; a bug stays loud; a file's own error stays its own); Issue 3 recorded grantor; Issue 4 wording; Issue 5 `sql_words` docstring and odd-argument-name test (V83); Issue 6 test fixes; Issue 8 the four mutant batches.
- B1 matrix: 27 effects x 10 generated carriers x 2 variants minus the 18 map-table effects under C10 = 504 cells; C6b 54; 36 pre-existing states x 2 = 72; C8 2, C9 2, C13 4, controls (K1, K2, K3-K12 including K8 as three refusals) in the count test; the three written tables (server-refused effects, empty by logic, not promised) in test_the_matrix_has_exactly_the_planned_cells. No carrier or control is listed as "not built".
- B2 controls K2-K12: built (K2, K5-K8, K10 are own tests, the rest generated).
- B3 carriers C3, C5, C6b, C8, C9, C10, C11, C13: built.
- B4: direction 2 of 7.7 judges every schema, every foreign server and wrapper, large objects and the database-level rights (`Oracle.can_everywhere`). It has a mutant now (V86).
- B6: "No file ran." added to the pre-flight ownership refusal; X28 removed from X_WORDING_GAP (now empty). Fail-before: only the two X28 cells fail on the old head.
- B8: measured 35 of 200 seeded compositions were stopped at step 0 by the text rules; after the fix 200 of 200 reach the data checks (log B-P3a2-3e-b8-after.log).
- B9: only PG16 is on this machine. The PG17 branch of test_a_role_saved_transaction_timeout_gives_exit_2_wherever_it_strikes is UNRUN here. The CI PG17 step was read twice (see report); it is not claimed to have passed.

## Not-run and open
- PG17 branches: UNRUN (no server available here). The CI run is the first run.
- Fail-before proof paths: /home/user/build/B-P3a2-3e-failbefore-issue2.log (Issue 2: 10 failed, 7 passed on the old head; the 7 are tests of behaviour the old head already has, covered by mutants V82 and V83) and /home/user/build/B-P3a2-3e-failbefore-matrix-b.log (the X28 cells fail on the old head). New matrix cells for B5 pins and B4 are new coverage that passes on the old head (no product change): stated reason, with mutants V86 and V87 as the proof of sensitivity.
- Mutant runner results: see the final report.

## Results (head f1ec83a8)
- gitleaks origin/main..HEAD: exit 0, no leaks. Plain push to wip/cloud-p3a2-3e done.
- ruff check 0; ruff format --check (src tests demos tools) 0; bandit -ll (src demos tools, from the shared bandit venv, not in the test group) 0; tools/scan_repo.py 0; stage_mutants 37 of 37; migration_numbers_mutants 40 of 40.
- migrate_mutants batches 1-4: 87/87, 88/88, 98/98, 97/97 killed (370), plus V86 and V87 (2 of 2): all killed. Batch 2 first stopped with "baseline not green" when three batches ran at once against the same Postgres (one test saw rights made by a concurrent run); run alone it is green. Do not run batches in parallel on one server.
- Issue 8: all 29 retired ids exist at 4d328e3d and none is in the list at HEAD (/home/user/build/B-P3a2-3e-issue8-retired.log).
- Fail-before sample on the old head (/home/user/build/B-P3a2-3e-failbefore-matrix-c.log): 80 tests, 2 failed (X28 wording), 78 passed (new coverage with no product change; sensitivity shown by mutants).
- Full pytest run 1: 1 failed, 12126 passed, 1 skipped; the one failure (demo_askdata dblink-connect) was the builder's slip: the scratch Postgres had been started without PGHOST/PGPORT/PGUSER in the server's own environment. After restarting it correctly the file passes (253 passed). Run 2 of the full suite: see the final report.
- Full pytest run 2 (scratch Postgres restarted with PGHOST/PGPORT/PGUSER in its own environment), same head f1ec83a8: exit code 0 taken from pytest itself, "12127 passed, 1 skipped, 29 deselected in 549.08s" (/home/user/build/B-P3a2-3e-final-pytest2.log, .rc).

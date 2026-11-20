# H3 / F8 hostile review 1 (merge 7a6d74f2f, F8 ef465c3fd c665dcc49)

Ran tests/test_money_start_check_pg.py on own DB: 33 passed.

## Blocker
none.

## Major
1. NOINHERIT false negative. src/hadavin_sdk/store/postgres.py:355-370 (own_money_rights_problems; same in own_stop_rights_problems ~300).
   Scenario: runtime login `CREATE ROLE l LOGIN NOINHERIT IN ROLE g`, g holds UPDATE on hadavin_caps / spend. has_table_privilege(oid,'UPDATE') returns f (checked on this DB), so build() starts, but the login can `SET ROLE g` and write the money tables (or, if g also owns, it is exempt). Same for PG16 per-grant INHERIT FALSE / SET TRUE. No test covers NOINHERIT.
   Fix: judge rights as the union over roles it can reach: for each role r with pg_has_role(current_user, r, 'MEMBER') (pg_roles, rolsuper false) evaluate has_table_privilege(r, ...) / has_any_column_privilege(r, ...) / has_function_privilege(r, ...), not only current_user; add a NOINHERIT test.

## Minor
1. Views not covered: postgres.py ~349 relkind IN ('r','p'). A (auto-updatable) view over spend/hadavin_caps in the schema that the login can write, owned by the owner, is a write path as the view owner. Fix: also scan relkind 'v','m','f' in the schema and flag write rights on any whose definition references money tables, or simply flag any INSERT/UPDATE/DELETE the login holds on any non-GRANTS relation of the schema.
2. Owner exemption is all-or-nothing and silent: `any(owns)` (postgres.py ~352) skips the whole check if the login is a member (even NOINHERIT / via a group) of the owner of ANY one money table. Managed setups where the app role is a member of the owner role by convention are therefore not refused, and not warned. Fix: log one WARNING "money-rights self-check skipped: login is a member of the owner role" and document it as the single escape hatch.
3. Escape hatch / docs: for a legitimate false positive (app role in a group role holding write rights via default privileges) the only remedy is the error text (migrate --runtime-role resets only the named role's grants, not the group's). No documented opt-out; no mention found in docs/ or the runbook (only the ticket and DECISIONS). Fix: runbook line: revoke from the group, or run as non-member; state the owner/superuser exemption (rds_superuser is not rolsuper, so only the owner-membership exemption applies).
4. Function check is conditional on EXECUTE on reserve (postgres.py ~391). Marker is code-only (PrivateAttr table.py:146, set to "reset" only in cli.py:346/360/812; not reachable from config), so a config cannot start a runtime login as reset. A purge-marked/ purge-DSN login that ALSO holds reserve is checked (good, refused). Residual: a runtime-store login that holds set_cap but NOT reserve passes; harmless (cannot book) but it is a cap writer started as a runtime store. cli.py:360 (`limits reset` with no reset ref) lets the configured login skip all checks by design; fine, mention in docs.
5. Cost: ~60 round trips at every build() (per table x right, two checks per column right, plus the stop check), postgres.py ~358-372. Fix: one query using has_table_privilege over a VALUES/CROSS JOIN of rights.
6. Clock hint (limits.py hunk of e750160ec): `"p_day" in str(exc)` is a substring test, so any exception message containing p_day (e.g. StaleState f"spend reservation exists: {reservation_id}" with a caller-chosen id, or a ValueError for p_day on the 1970/9999 bounds) logs the clock hint. Cannot leak (fixed string, the store passes only a token; tested) but can be forged into a misleading hint by a chosen reservation id. Fix: key on `isinstance(exc, ValueError)` as well.
7. tests/test_money_h1_pg.py check_m1_add_spend_window: the comment line "the message names the argument..." is duplicated.

## Checks that held
- (1) add_spend window: 0011_money_definer.sql:405-409 equals reserve's; widening_add_spend (money_caps_seed.py:127) widens only tests without no_cap_seed; test_money_h1_pg.py check_m1_add_spend_window runs with no_cap_seed (module marker, line 28) at the real window (+-1 day ok, +-2 days / +73y refused, 22023, no rows), skew 0, missing row HD004, and three mutants (M-m1a/b/c, using rpartition `_last`) are killed in test_money_caps_mutants.py. A production regression is NOT hidden by the wrapper.
- (4) F8 lowering_attacks (tests/test_money_guard_pg.py:100-106): CheckViolation is counted as went_through (not refused), so it cannot mark a mutant killed; it makes the harness stricter. Only InsufficientPrivilege counts as refused. No wrong-reason acceptance. test_audit_chain.py: non-ASCII moved from the charset-limited `result` to `source`, still exercises the unicode canonicalisation path; fine.

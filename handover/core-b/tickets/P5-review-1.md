# P5 review 1 (hostile reviewer) - wip/cloud-core-b/draft-upgrade

Ran tests/test_migrations_draft_upgrade_pg.py + tests/test_migrations_checksum.py on own DB: 34 passed.
Verdict: not clean. 1 Major, 4 Minor, 2 notes.

## Major

**MAJ-1 NULL checksum on 0010/0011 is trusted silently with roles named (the pre-M6 draft DB).**
src/hadavin_sdk/store/migrate.py `_verify_applied`, the `if old is None:` branch runs BEFORE the `elif strict and
path.stem in MONEY_WALL_DRAFTS` branch. A draft DB migrated before checksums existed has NULL for 0010/0011: with all
roles named it logs one warning, records the current file's hash and goes on; the refusal never fires, and from then on
the DB looks healthy. Any older body with a SIGNATURE that is still mapped (e.g. an old 6-arg `hadavin_reserve_spend`
body that took caps from the caller but kept today's argument list, old `hadavin_settle_spend`, old guard trigger body)
keeps running. Only an overload with a different signature is caught (by the unmapped check). The test file itself
sets checksum NULL as "trusted on first use" (test_the_unmapped_old_overload_refuses...), so the hole is known and
unasserted.
Scenario: DB from the first money-draft, never re-migrated since M6; operator deploys with roles: passes.
Fix: with `strict` and `path.stem in MONEY_WALL_DRAFTS`, a NULL checksum is the same ConfigError (remedies reset /
accept; accept is already handled earlier via `continue`). Released-only DBs cannot have NULL on 0010/0011 (those files
never shipped released), so no false positive. Add a test: NULL checksum + named roles -> ConfigError; + --no-roles ->
warning.

## Minor

**MIN-1 `_drop_unmapped_functions` builds DDL from `oidvectortypes` text through `sql.SQL(types)` (migrate.py,
`_drop_unmapped_functions`).** `oidvectortypes` does not quote or schema-qualify: a type with a mixed-case or odd name
(`"MyType"`, a type outside the search path, a name containing `)`/`;`) gives a broken or injectable statement. Reach
is small (the function must be owned by the migrating login and be named hadavin_*), but the old code already had the
right primitive. Fix: take `p.oid::regprocedure::text` (quotes and qualifies) and run `DROP FUNCTION` with that
via `sql.SQL`, or use the oid-to-text from `pg_identify_object_as_address`; the function name and schema are properly
quoted by `sql.Identifier` already. Same for the DROP statements printed in `_unmapped_message`: f-string with plain
`"{name}"` does not double an embedded quote; use `.replace('"','""')` or the regprocedure text, so the operator's
copy-paste is correct.

**MIN-2 `--reset-draft` drops with no CASCADE and no pre-check: a dependent object ends as a raw psycopg
DependentObjectsStillExist, not a ConfigError.** A stale unmapped function that a trigger or default uses fails the
reset mid-transaction (rolled back, safe) with an unhelpful message. Fix: catch `psycopg.errors.DependentObjectsStillExist`
and raise ConfigError naming the function and the dependent. Do NOT add CASCADE.

**MIN-3 Docs recipe is incomplete for 0010.** docs/migration-checksums.md "Recipe" says for 0010 "reset also 0011", but
0010 creates `spend_money_guard`, `spend_month_money_guard`, `spend_reservations_money_guard` with plain
`CREATE TRIGGER` (0010 lines 88-92): `--reset-draft 0010_money_guard` fails with "trigger already exists" unless the
operator also runs `DROP TRIGGER ... ON spend / spend_month / spend_reservations`. The error text in migrate.py
mentions "guard triggers of the draft" but names none. Fix: list the three DROP TRIGGER statements in the recipe (and
`hadavin_money_guard()` is replaced by CREATE OR REPLACE; fine).

**MIN-4 Docs name `AUDIT_FUNCTIONS`, which does not exist on this branch.** docs/migration-checksums.md says
"no longer in `MONEY_FUNCTIONS` or `AUDIT_FUNCTIONS`"; the code compares with FUNCTION_GRANTS + EXCLUDED_FUNCTIONS
(migrate.py `_unmapped_rows`). Fix: say FUNCTION_GRANTS / EXCLUDED_FUNCTIONS. Also the docs say the shipped test is
the proof; the runbook claims "Afterwards run limits sync-caps (cap table recreated empty)": true, but see (3) below.

## Answers to the questions asked

1. False negatives: (a) NULL rows: NOT handled, MAJ-1. (b) The unmapped-function check is unconditional (not gated by
`named`, runs after files are applied, same transaction, so it also covers --no-roles); it only knows
FUNCTION_GRANTS + EXCLUDED_FUNCTIONS, so a mapped-signature stale body or a name outside the hadavin_ prefix is not
seen. AUDIT_FUNCTIONS (0012, audit-rights branch, note only): when that branch merges, its functions must be added to
FUNCTION_GRANTS/EXCLUDED_FUNCTIONS or this check refuses every migrate (and `--reset-draft` would DROP them if owned
by the login before re-applying, since they are "unmapped" until mapped: reset ordering is drop-then-apply, so for a
DB that already has 0012 and a reset of 0011, the 0012 functions get dropped and not re-applied (0012 stays in the
ledger)). Fix at that merge: map them; and make `_drop_unmapped_functions` only drop functions whose signature is not
created by ANY shipped file (regex over migration texts, as check_grants does). (c) Right checksum but hand-edited
body: undetected by design; residual. A cheap detector: record a md5 of `prosrc` per money function in the shipped
file set at test time and compare at start-check; not required for this ticket, document as residual.
2. False positives: none found. Fresh DB, DB from released 0001-0007, and re-run on a healthy DB all give [] (tests
`w.migrate() == []` after reset; 0001-0007 have no hadavin_* functions beyond mapped/excluded; strict only fires on a
recorded checksum that differs). One operational note: because 0011 is still being edited under review, every
persistent staging DB with named roles now hard-fails after each 0011 edit until reset; intended, but say so in the
CHANGELOG so deploy pipelines are not surprised.
3. `--reset-draft` drops: ownership (`proowner = current_user`), prefix (LIKE 'hadavin\_%'), schema
(current_schema) are enforced; names via sql.Identifier are safe; types are not (MIN-1). A dropped function mid
transaction: DROP takes a lock, concurrent runtime calls wait for the commit; the re-applied file recreates the mapped
ones, only unmapped ones are gone, so the runtime loses nothing it needed. Danger: it runs even if the reset version
is 0011 but the unmapped function belongs to 0012 (see above). On the recipe (operator drops hadavin_caps,
hadavin_limits, two *_usd_range constraints): the data loss is real (caps are re-entered by `limits sync-caps`, and
until then the runtime reads no cap: fail closed, but a failed migrate after the DROP leaves the DB uncapped-closed
and the caps gone). Recommendation: do NOT make --reset-draft drop tables. Make 0011 idempotent for those objects,
since 0011 is unreleased and being rewritten anyway: `CREATE TABLE IF NOT EXISTS hadavin_limits/hadavin_caps (...)`
and a `DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'spend_usd_range' AND conrelid =
'spend'::regclass) THEN ALTER TABLE ... END IF; END $$` for the two constraints. Then the reset recipe is only
`--reset-draft`, the caps data survives, and the failed-migrate window disappears. Caveat: with IF NOT EXISTS, a
draft table with a different column set is kept silently: add a column check (or keep `check_ledger` style assertion)
or keep the manual drop for DBs whose caps schema differs. Until then, at minimum tell the operator to
`CREATE TABLE hadavin_caps_backup AS SELECT * FROM hadavin_caps` first (docs currently do not).
4. Mutants: the three monkeypatch "mutants" assert only that the refusal disappears (`== []`, or the old refusal
remains); they kill nothing in themselves and depend on the paired positive tests: strict-off and wall-empty are
killed by test_named_roles_refuse..., no-drop by test_reset_draft_drops.... They are honest as documentation, but add
mutants that matter: (i) NULL checksum with roles (fails today: MAJ-1); (ii) `_drop_unmapped_functions` without the
proowner check (the foreign-owner test is a direct call, fine, but not through `migrate(reset_draft=...)`); (iii) drop
filter without `hadavin_` prefix (not_ours covered); (iv) a mixed-case type function (MIN-1). Missing positive tests:
NULL + roles; 0010 reset recipe end-to-end; reset-draft via migrate() on a DB whose unmapped function has a dependent.
5. Docs: accurate on strict/--no-roles/0008-0009 and on accept-changed-draft being the operator's call; the
inaccuracies are MIN-3, MIN-4 and the missing backup step; the "NULL checksum on an unreleased file is trusted once"
line at the end of migration-checksums.md must be amended with MAJ-1 (it is exactly the case being protected).
Runbook upgrade section is consistent with code.

# P0e memo 4: migration numbers, collisions, renumber order, and whether any database ever ran a branch-numbered migration

Author: research agent (read-only), 2026-11-05. Evidence: `git ls-tree -r --name-only <ref>`, `git diff --name-status origin/main...<ref>`, `git show origin/main:src/hadavin_sdk/store/migrate.py`. Base `origin/main` = ce70eb5. Nothing executed. Lead: run `egm:egm-review-loop`.

## 1. Migration files per ref (folder `src/hadavin_sdk/store/migrations/`)
| Ref | merge-base with main | Files present | Added by this ref (vs main) |
|---|---|---|---|
| `origin/main` (ce70eb5) | - | 0001_core, 0002_audit_chain, 0003_approvals_tick, 0004_audit_checkpoint_meta, **0005_evidence** (K5-core, merged) | - |
| `origin/pr/41` (K6 measurement) | 308558a (13 ahead) | 0001-0004, **0005_measure** | `0005_measure.sql` (labels, level_events, reports, seen_actions, announcements, 3 views) |
| `origin/pr/43` (ask-your-data gaps) | 6608146 (22 ahead) | 0001-0004 | none |
| `origin/pr/47` (ask-your-data export) | 6608146 (7 ahead) | 0001-0004 | none |
| `origin/pr/48` (hardening) | 6608146 (21 ahead) | 0001-0004 | none (but it edits `migrate.py` GRANTS for `spend`/`spend_month`, adds a `maintenance` role; no SQL file) |
| `origin/pr/49` (promoted refunds) | 6608146 (6 ahead) | 0001-0004, **0005_reservations** | `0005_reservations.sql` (table `reservations`, 2 indexes) |
| `origin/pr/50` (promoted apexc) | ce70eb5 (28 ahead) | 0001-0004, 0005_evidence | none |
| `handover-src/pr50-local-748849c` | ce70eb5 (34 ahead) | same as pr/50 | none |
| `handover-src/c1a-8460813` | 6608146 (10 ahead) | 0001-0004 | none |

(Branches `pr/43`, `pr/47`, `pr/48`, `pr/49`, `c1a` are based on 6608146, which is BEFORE K5-core's `0005_evidence` landed on main, so they do not show it. They will meet it on rebase.)

## 2. Collisions
* **Number 0005 has three claimants**: `0005_evidence` (main, already merged), `0005_measure` (PR #41), `0005_reservations` (PR #49). Because main already holds 0005, BOTH PR #41 and PR #49 now collide with main, not only with each other. The plan text (inventory.md line 11: "migration number 0005 collides") is correct; the earlier two-way collision (#41 vs #49) became a three-way one when K5-core merged.
* No other numbers collide: PR #43, #47, #48, #50, C1a add no migration file.
* `pr/41` `migrate.py` also adds `GRANTS` rows (`labels`, `level_events`, `reports`, `seen_actions`, `announcements`, `labels_seq_seq`, `level_events_seq_seq`, 3 `v_*` views) and `pr/49` adds a `reservations` GRANTS row; both edit the same dict, so besides the file number the two PRs textually conflict in `migrate.py` (s0-merge-probe shows conflict in `tests/test_k2_migrations.py`; `migrate.py` also changed by pr/48).

## 3. How `store/migrate.py` orders and checks numbers today (main)
* File pattern `_FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql")` (line ~64); files are `sorted(folder.glob("*.sql"))` (`_migration_files`), i.e. by name.
* `check_ledger(paths)` (lines ~91-104): refuses a name not matching the pattern, **refuses two files with the same number** ("two migrations are numbered 0005") and **refuses a gap** ("migration 0003 is missing"); the numbers must run 1..max. It runs inside `migrate()` before any connection (`if problems := check_ledger(files) + check_grants(files): raise ConfigError`) and as repo tests: `tests/test_k2_migrations.py:29` (real folder), `:36` duplicate number caught, `:41` gap caught, `:46` first file not 0001 caught, `:50` bad name caught.
* The applied set is the table `schema_migrations(version TEXT PRIMARY KEY)` holding the file STEM (number + name). `migrate()` applies every file whose stem is not recorded, in name order, in ONE transaction under `pg_advisory_xact_lock` (line ~219). If the database holds a stem with no file in this release it raises ("applied migrations have no file in this release", test `test_migrate_refuses_when_an_applied_migration_has_no_file`, `test_k2_migrations.py:387`).
* What is NOT checked (this is the real gap P3a must close):
  1. **Out-of-order insertion**: stems are the key, so a new file numbered LOWER than an applied one (for example a renumbered `0005_reservations` arriving after a database already applied `0006_x`) is not a duplicate in the folder and is simply applied late, after the higher one, with no error. Today this is impossible only because no database has more than one migration beyond what the folder shows. P3a's rule "fails on out-of-order numbers" needs a database-side check: every unapplied file must be numbered above the highest applied number, else refuse.
  2. **Renumbered-but-same-content file** (rename 0005_measure to 0006_measure): the old stem is in `schema_migrations`, the new file has a new stem, so `gone` triggers (loud, good) with the hand-fix text in the error. P3a should keep that behaviour and test it.
  3. **Forward-only downgrade read**: nothing tests old code reading a newer schema (plan-v3 P3a adds it).
  4. **Branch-vs-main collision** (two open PRs both adding 0006): the folder check catches it only after both are merged (CI on main), or when one PR rebases on the other. A pre-merge CI step that compares the PR's new migration numbers with `origin/main` would catch it at PR time; the plan says "CI fails on duplicate or out-of-order numbers". Note `.github/workflows` is lead-only (plan-v3 rule 9(d)).
* `check_grants` (same file) additionally fails a migration that creates a table/view/sequence not in `GRANTS`; any renumbered migration keeps passing it only if the `GRANTS` rows move with it.

## 4. Proposed renumber order (following plan-v3 section 7 and rule 10)
Rule used: the number is assigned at merge time in merge order (P3a's rule), not at branch time. Merge order from section 7: P3a/P1 -> P2a, P4d -> P4a, P2d, P5a -> P4b -> ... ; v1.1 packages later.
| Order | Package | Migration needed? | Number |
|---|---|---|---|
| (already merged) | K5-core | `0005_evidence` | 0005 |
| 1 | P3a, P4d, P4a, P2a, P2d, P5a-P5b5, P5c, P6a, P6b | none expected (P3a adds a rule and tests only; P4d is tests/refactor; P4a is `Usage`/price code; P5c redactor uses the existing `redaction_maps` table) | none |
| 2 | **P4b** (meter) | **depends on the money decision.** If the winner keeps `spend`/`spend_month` tables as PR #48 does: none (only GRANTS edits). If it needs an integer column or a `reservations` table: that is the first new number | **0006** (name chosen by the builder) |
| 3 | P3b (PR #49 rebase; v1.1; reservations only if refunds is the first client, plan-v3 section 11 default "no") | `0005_reservations.sql` renamed | next free number after step 2 (0006 if P4b added none, else 0007) |
| 4 | P3c (PR #41 K6; v1.1; trigger "first pilot") | `0005_measure.sql` renamed | next free number after step 3 (0006, 0007 or 0008) |
So the answer to "who gets 0006": whoever merges first. With the plan's order: P4b if it needs a migration, else P3b if triggered, else P3c. Each rename also moves: the `GRANTS` rows in `migrate.py`, the `Grant` comments, `tests/test_k2_migrations.py` expectations, the CHANGELOG entry, and any text that quotes the file name (PR #41's migration comment block names "version 0005"; PR #49's header says "version 0005").
The lead should record the assignment in the ledger when it happens, and each renamed PR needs its rebase review (plan-v3 rule 11: range-diff plus full evidence rerun).

## 5. Could any demo or pilot database have run a branch-numbered migration?
Evidence:
* Demos do not use the core migrations at all. Grep of `projects/hadavin-demo-{apexc,dealdesk,intake,refunds}`, `projects/jagrat` and `projects/hadavin-portal-kit` (py/md/toml/json/yml/sql, excluding venvs and scratch) for `schema_migrations`, `hadavin-sdk migrate`, `hadavin_sdk.store`, `store/migrat`, `0005_`, `migrate(`, `HADAVIN_*DSN`, `pg-dsn` found only: `hadavin-portal-kit/hadavin_kit/versioning.py` (an unrelated JSON export `migrate(doc)`, lines 19 and 159). So no demo imports `hadavin_sdk.store`.
* Demo core pins: apexc and refunds and intake `core_commit` = `660814674ece8ad578293e5412633d796eddb96f` (= 6608146, pre-0005); dealdesk `6608146`. Their core copies are listed in `core_copies.json` and cover guard/runtime/testing files only (apexc: `_confusables`, `egress_text`, `textnorm`, `config_view`, `rowstore`, `stop_gate`, `testing/mutation`; dealdesk: `signed`, `_confusables`, `egress_text`, `textnorm`; intake: `safe_text`, `_confusables`, `textnorm`; refunds: `_confusables`, `textnorm`). None is a store or migration file. Their own persistence is local (dealdesk/Intake use SQLite files in their own code: `dealdesk/inbox.py` `SqliteLedger`, Intake `workqueue.py`), not Postgres through the core.
* The only Postgres use in the core repo's demo is `demos/ask-your-data` (a read-only login against a user-supplied target DB; no `migrate`).
* The core CLI `migrate` reads `HADAVIN_MIGRATE_DSN` (`cli.py:322`). The only automatic runs are the test fixtures, which create a fresh schema per test and drop it (`tests/contracts/kinds/store_postgres.py` lines 29-80: `CREATE SCHEMA`, `migrate(scoped)`, `DROP SCHEMA ... CASCADE`). CI runs those against a throw-away service Postgres.
* There is no client, no pilot and no production database yet (CLAUDE.md "first client" gap; handoff/lead-state-2026-11-05-limit-stop.md; nothing in `memory\` records a deployed core database). I found no note recording a migrate run against a persistent database.
* What I could NOT verify: (a) the owner's laptop or any scratch database may have been migrated by hand from a branch checkout (for example while building K6 on `pr/41`); there is no log of that in the repo or the studio notes I grepped (I did not search `_local\` or shell history). (b) Any database on a cloud account. (c) Whether `egm\hadavin-sdk\k6-egm-review-2026-11-01.md` records a live-Postgres run (I did not open it). Cheap check for the lead before P3a is merged: ask the owner "did you ever run `hadavin-sdk migrate` against a database that you keep?"; and if yes, run `SELECT version FROM schema_migrations` there (masked output).
Conclusion: on the evidence in the repos, no demo and no pilot database can have applied `0005_measure` or `0005_reservations` through the core, so renaming them breaks no stored data. The only databases that may have done so are throw-away test schemas and possibly a developer scratch database, which can be dropped. This supports the plan's choice "renumber, forward-only, no compatibility shim". The residual risk (an unlogged developer database) is closed by the owner question above.

## 6. Risks and asks
* Out-of-order insertion (section 3, gap 1) is a real silent failure mode once any persistent database exists; make it the first P3a fail-before test.
* PR #41 and PR #49 both change `migrate.py` GRANTS and `tests/test_k2_migrations.py`; whoever merges second must rebase those files and renumber, with `check_grants` as the safety net (it fails if a table has no GRANTS row).
* Plan-v3 says "includes a test that the previous release code reads the new schema or fails loudly": the code to read is `migrate.py` + `postgres.py`; what "the previous release" is has to be pinned (for example the ce70eb5 tag) and checked out in a throwaway worktree.

R-numbers cited: none. Files changed: this file only. Head SHA read: origin/main = ce70eb5.

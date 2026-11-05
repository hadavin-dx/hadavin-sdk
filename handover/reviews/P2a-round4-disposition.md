# P2a round 4 disposition (ticket revision 6)

Author: P2a ticket author, 2026-11-05 (UTC; IST = UTC+5:30). Inputs: `P2a-round4-resolve.md`, `P2a-round4-adversarial.md` (ADV-A1..A12), `P2a-round4-correctness.md` (COR-C1..C14). Target: `tickets/P2a.md` revision 6. Nothing committed or pushed.

Database evidence: `handover/evidence/P2a-sql.md` (throwaway PostgreSQL 16.15 on port 54329, tests S1-S28, a hand-written SQL model in a non-`public` schema, not the migration file; nothing stopped, my database and roles dropped). Every database claim in the ticket cites an S-number or is marked UNVERIFIED. Not run: PostgreSQL 17, the Python `migrate()`, the Store methods, the true core `ce70eb5` code.

Summary: 26 rows (12 adversarial, 14 correctness): applied 24 (ADV-A2 and ADV-A6 narrowed as the resolve says; ADV-A5 with its premise narrowed), applied in part and contested in part 1 (ADV-A4: G2 dropped, G3 kept), declined 1 (ADV-A12). Mutant counts: 41 / 14 / 82 / 53 = 190 (was 179). If the lead also drops G3: 81 / 189.

| id | decision | ticket location (revision 6) | note |
|---|---|---|---|
| ADV-A1 | applied | Security > Trigger (final function text), Packaging; mutant row "re-issue hard-codes public"; Tests > Guard and migrate; evidence S1, S26, S27 | Schema is an identifier built by `migrate()`. S27 shows the `public.` version raising 42P01 in another schema. The scanner cite `migrate.py:80-90` is the reviewer's (UNVERIFIED by me). |
| ADV-A2 | applied, narrowed (as the resolve says) | Security > Probe (reconciliation), Breakglass | No new tick step or table: the existing `stop_guard_probe` step reconciles `kill_switch_resets` against audit rows and writes `reset_out_of_band`; the alarm keys on `login_label = 'breakglass'` (S10). The audit field carrying the version is UNVERIFIED. 2 mutant rows. Owner of the alarm stays PENDING LEAD 10. |
| ADV-A3 | applied | Security > Probe ("WHEN"); Tests > Guard and migrate; 2 L mutant rows | Stop first, probe after, time-capped, never changes the stop exit code. Evidence S21 (the lock case). |
| ADV-A4 | applied in part (G2 dropped), contested in part (G3 kept) | Mutation plan > "The 77 new rows" and the count bullet | G2 (`ENABLE ALWAYS` inside the static file) is hidden by the Python re-assert: dropped. G3 (the Python re-assert removed) is NOT equivalent: the static file runs once, so a test that disables the trigger and then runs `migrate` kills it (S13, S14 show the states). I disagree with dropping G3; if the lead insists the counts are 81 / 189. |
| ADV-A5 | applied (premise narrowed, as the resolve says) | Interface > `Limits.stop` and CLI exit codes | Exit 7 and `except AuditUnavailable` removed because `write_outcome` never raises (cite from COR-C5, UNVERIFIED by me). The reconciliation repairs a missing outcome row. |
| ADV-A6 | applied, narrowed | Interface > Missing row; DURABLE MARKER (`restore(True)`); Missing-row recipe; 1c mutant row | `restore(True)` without a version reads `status().version`; the recipe says restart gates. S24 shows the re-seed and reset. |
| ADV-A7 | applied | Security > Trigger (`NEW."by" := lbl`); mutant row; test | S8 shows the label stored in `kill_switch.by`. |
| ADV-A8 | applied | Interface > Store methods (`guard_dry_run`); Probe; 2 P mutant rows | First UPDATE must succeed and the second must raise 42501 with the fixed message. S17, S18. The placeholder's own message is UNVERIFIED (not run). |
| ADV-A9 | applied | Interface > `clear_kill_switch_if`; Security > Timeouts; S-mutant rows | `str(ms)`; S20 shows the integer argument raising 42883. |
| ADV-A10 | applied | Security > Packaging (hand-applied guard file); Depends on / PENDING LEAD 2 (P3a late-file text); Rollback | "After a hand-applied guard file run `migrate`." Not run (Python). |
| ADV-A11 | applied | Interface > `PostgresStore.set_kill_switch` and `Limits.stop`; contract test; S-mutant row | `-> KillSwitch`, `UPDATE ... RETURNING`; memory returns its record. |
| ADV-A12 | declined | none (ledger only) | One-row table; autovacuum covers the dead tuples. |
| COR-C1 | applied | same as ADV-A11 | merged. |
| COR-C2 | applied | same as ADV-A1 | merged. |
| COR-C3 | applied | `handover/evidence/P2a-sql.md`; ticket header rule; Security and Rollback cites; Evidence step 5 | About 15 claims now cite S-numbers. Claims without a run are marked UNVERIFIED: the rollback against true core code, `pg_terminate_backend`, PostgreSQL 17, the weak-row run and the earlier Linux runs (no saved output). Rev 5 had called the rollback "tested against true core code": corrected to SQL level only. |
| COR-C4 | applied | Interface > `Limits(...)` (`environment` required), Files (app, cli), existing-tests (j); mutant row | Cites `DEV_ONLY` (`table.py:593`, `config.py:366-369`; the reviewer's cite). L11 is killed only by a directly built `Limits`. Test: no `environment` gives TypeError. |
| COR-C5 | applied | same as ADV-A5 | merged. L16 removed. |
| COR-C6 | applied | Files P2a-1 > existing tests (h), (i) | Audit sequence `reset_attempted` then `reset`; `ADD COLUMN IF NOT EXISTS` form. |
| COR-C7 | applied | Tests > FAIL-BEFORE (2); Evidence step 4 | Re-worded per head; (4) now says it runs at `748849c`. |
| COR-C8 | applied | same as ADV-A9, plus both writers through `@_writes` | `clear_kill_switch_if` has no retry. |
| COR-C9 | applied (a lead action) | Depends on (sibling tickets bullet); PENDING LEAD 2 | Line numbers of the sibling tickets are the reviewer's. |
| COR-C10 | applied | same as ADV-A3 | merged. |
| COR-C11 | applied | Login labels (Retention); PENDING LEAD 14; Rollback | Table kept; a purge is a written recipe with sign-off. |
| COR-C12 | applied | Files P2a-1 (runbook file, CHANGELOG upgrade steps, `app.py` environment, repo-rules note) | Runbook name and docs folder UNVERIFIED. |
| COR-C13 | applied | Depends on > Coupling with P4d-b | P2a-1 changes the single P4d read; "without more code" removed. |
| COR-C14 | applied | Interface > Masking; PENDING LEAD 4 and 13 | New item 13: allow-list of system principals, recommended yes. |

New PENDING LEAD items: 13 (system-principal allow-list), 14 (`kill_switch_resets` kept). Carried unchanged: 1, 3-12.

Counts check: baseline 103; P2a-1 new rows 77 (25 G + 13 S + 12 P + 27 L), 1c new rows 10; 41 + 14 + (5 + 77) + (25 + 18 + 10) = 190 = 103 + 77 + 10.

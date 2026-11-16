# Hand-off v15 readiness review, round 4 (egm-implementation-readiness, condensed copy of the inline report), 2026-11-16
Target: CORE-PR-HANDOFF-v15.md, -other-tracks, v15-CHANGES, v15-OPEN-FOR-LEAD. Read-only; nothing run. Verdict: NOT YET READY for "build without asking". 0 blockers, 5 majors. All 7 v14 majors fixed or mostly fixed.

## MAJOR
- M1 Gate type differs between S-1 (`WindowOnlyGate`) and S-2a (`CallGate`) with different settle/keep/release signatures (`ticket: None` vs `Ticket`); no shared Protocol; the test-seam rule needs a `CallGate` that does not exist at S-1 head; `Reply.booked_usd` is added in S-2a but `NetworkLLM.chat` text sets it with `model_copy` in S-1. Fix: one named gate Protocol in `llm/spend.py`, seam check against it, say what S-1 `chat` does about `booked_usd`.
- M2 Audit-reader role code unowned: `Grant(audit_read=)`, `migrate(audit_reader_role=)`, `check_grants` / `effective_problems` handling and the setting name are "not yet code"; DB-2 tests E0-DB-2 cannot run without it; `audit_reader_role` is not in `SpendSettings`, `PostgresSettings` or the CLI. Name the PR and the setting.
- M3 S-2a test still depends on DB-1 (E0-S2-2, 5.4 item 4 say "DB-1's file applied"); 5.6 item 1(c) says inline ALTER TABLE but E0-S2-2 and 5.4 do not, and the constraint name `spend_month_usd_ok` appears only in the held SQL file. G-4(i) check names a sentence ("store emits UPDATE for negative deltas") not a pytest id.
- M4 Hot-file lists incomplete: S-2b row lacks `config.py` (also edited by K1, H-0, H-1, S-1) and `store/postgres.py`/`make()`/`startup_checks`; DB-1 row lacks `tests/test_lockin_guard.py` and the `migrate()` lambda tests; S-2a row lacks `llm/anthropic.py`, `llm/gemini.py` (v13 R4 still partly open).
- M5 S-1 pass rule rests on untested `gate4.sh` (v14 N7 still open); E0-S1-5 runs `import_graph_v14.py ... --table CORE-PR-HANDOFF-v14.md` but the planned-edge table now lives in v15 section 8.1; S-1 scope very large for two 60-minute sessions (unmeasured).

## MINOR
1 `status_of` text says retry.status reads the cause chain; real `status()` reads one exception, chain walker is private `_chain` (retry.py:43). 2 `_retry` snippet calls `spend.definite_client_error(status)` without `extra`, so the 429-release test cannot work. 3 `k1b/loop.py:115` already defines a local `worst_case_usd` with a different signature; wrapper or replace not stated. 4 5.4 heading says S-2a but item 2 is S-1-owned. 5 `Limits.charge` still uses `now()` (limits.py:18). 6 5.9 table row 7 extra cell. 7 other-tracks line 174 says "all 13 PR ids", v15 says 14. 8 `NetworkLLM.__init__` keyword-only `gate` without default breaks direct constructions (covered by E0-S1-1). 9 PostgresStore signature consistent.

## v14 majors status
1 FIXED; 2 FIXED; 3 FIXED (`Limits(store, audit, registry, clock=models.now, *, window=None, spend=None)`); 4 MOSTLY FIXED (audit-reader code unowned: M2); 5 FIXED (two held files, default is exactly `CHECK (usd >= 0)` plus the spend_month constraint); 6 PARTLY FIXED (M3); 7 FIXED with one slip (minor 2).

## UNVERIFIED items without a stated way to settle
Lowest supported Postgres version (variant and DB-2 need 14+; CI 17.10); whether any vendor bills 400/401/403/404/422 (invoice comparison, POST-DEMO); vendor facts in 5.9; `.gitattributes eol=lf` on a Windows checkout (sha256 pins); 32 MOVED citations unread and 142 planned-name labels assigned by rule; Postgres 17.10 runs.

## Checked against src (matches)
`Limits.charge/blocked` limits.py:17-30; `with_retry` re-raise retry.py:95-96; `retry.status`; `NetworkLLM` common.py:200-241; the four kinds call `self._retry(`; `ALLOWED` table; `Deps`/`make()`; `app.build` order; `injection_check` 3 params; `agent_loop.py` and `k1b/loop.py` line cites; `store/migrate.py` `_migration_files`, `check_ledger`, `GRANTS`, `_SAFE_CREATE`; `PostgresStore.__init__(self, conn)` store/postgres.py:195; held SQL files and evidence helpers exist. Merge order S-1, S-2a, S-2b, DB-1, DB-2 coherent; GRANTS/migrate ordering sound.

## Not checked
Other-tracks content beyond the PR table and E0 table; raw Postgres outputs; ORDERS.md Q24/Q28/Q33/Q34; resolve-handoff-v15.md, checkpoint, planned-names; about 400 cites line by line; `.sonarcloud.properties`, ci.yml line numbers; anything needing a run.

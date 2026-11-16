# fix-review12: round 12 of REVIEW.md (security and money path, no round cap)

Backup: scratchpad bak-rev12.md. Not committed.

## Unverified or not done (first)
- Nothing was run. The approval guard trigger, the column-level UPDATE grants, BEFORE UPDATE on the upsert DO UPDATE branch, the foreign key and the new constraints are Postgres behaviour I did not test. Patches and patched tree are not on disk.
- Not built: no source was edited. All new designs (guard, build profile, audit-writer function, moving ALLOW-class execution to the tick) are proposals in the rows.
- Not opened fully: `tests/contracts/test_store.py:237`; whether `approval_requests.summary` is changed anywhere; SQL column names of `approval_decisions`.
- Not decided (lead choices, listed in the file): audit-writer identity; ALLOW-class execution to the tick; FK second guard.

## Reviewer claims confirmed against src
- Design B1 (retarget, reset and replay, upsert over APPROVED): `models.py:182-190` (decision has no run_id), `tick.py:88-95`, `agent_loop.py:776-797`, `postgres.py:311` and `:204-218`, `requests.py:107`. All confirmed; guard in X-6 rebuilt.
- Design M1: `agent_loop.py:768` executes ALLOW plans, hooks at `:886-909`. Confirmed; identity table corrected.
- Design M2: `migrate.py:5`, `:320-326`; `chain.py:312`, `:315-317`. Confirmed; rollback now = snapshot, ON CONFLICT change one release before 0009, NOT VALID or pre-check.
- Design M3: `app.py:144-145`, `161-162`, `170-174`. Confirmed; build profile added.
- Design M4 (column-level UPDATE), M5 (FK weakness, tests `test_p2_postgres.py:289,296,299`), M6 (spend trigger not a guarantee), M7 (audit writer). Confirmed or reasoned from the grants; recorded.
- Design minor: fixture breakage list `test_store.py:103,114,166,237`; I found no direct DB hit in `test_p7_tick.py` (reviewer count differs; stated in the row).
- Codebase M1 (C-7 not live; producers `anthropic.py:142`, `openai_compat.py:142`, `bedrock.py:176`, `fake.py:54`): confirmed; row relabelled, fix is "negative = missing" with `ge=0` backstop (`common.py:164-165`, `:171`).
- Codebase M2 (headline: 6 price cases + 5 A-01 + 2 ceiling; evidence-13.md:43-58, :99): confirmed; evidence bullet and Short answer restated.
- Codebase N1 (count_review.py robustness): done. N3 (`tick.py:91-92`, `postgres.py:389-397`): hedge narrowed. N5-N7 cites fixed: `app.py:151-160`, `tick.py:59-60`, `chain.py:184-186`, `evalcli.py:154-157`, `0004:6-7`. N6 (verify flags unparseable JSON via `chain.py:397-400`) is true; reads still fail.
- Contested: none.

## Changes
REVIEW.md: Short answer rewritten in plain words; X-6 guard, identity table, rollback, migration numbers, build profile, audit writes, spend wording; C-7 relabel and fix; X-5(f) FK note; effective-Major paragraph (live X-4, X-5, X-6; C-7 apart; arithmetic 3+1+1+1+1+5=12); evidence headline; cites; Not checked; header status. count_review.py: decision cell found by pattern in cells 3 or 4. Counts unchanged (26 rows; Major 12, Minor 4, Nit 10; PROPOSE FIX 23, DECLINE 3).

## Checks
See the final report for exit codes (run from handover/flows-audit).

# Round 13 (review-design-r13.md and review-codebase-r13.md; log appended here as the brief said)

Backup: scratchpad bak-rev13.md. Not committed. Nothing was run against Postgres or the patches; every SQL statement is a proposal.

## Unverified or not done (first)
- All Postgres behaviour in the new text (temporary schema lookup, `TG_TABLE_SCHEMA` with `EXECUTE`, `REVOKE TEMPORARY`, `ENABLE ALWAYS`, `session_replication_role`, SECURITY DEFINER with a pinned search path) is the design reviewer's knowledge, not checked by me. No source or test was edited.
- Not designed: the receiver recomputing the approval summary (lead choice (5)(b)); the SQL version of the hash (byte-equality with Python's `json.dumps`).

## Findings, each opened in src
- Design B1 (temporary table bypass): CONFIRMED for the source part: `migrate.py:210-212` checks CREATE on `current_schema()` only; a grep of `src/hadavin_sdk` for TEMP, search_path, SECURITY DEFINER, ENABLE ALWAYS and session_replication_role finds nothing relevant. X-6 row: the false claim is withdrawn, three-part fix and negative tests (f) added, verdict "do not build the guard as written" in the Short answer and the row. Severity: row stays Major (scale note in Counts; the Blocker is a flaw in a proposed fix, not in today's code or the three patches); flagged to the lead as choice (5)(c).
- Design M1 (audit-writer function): confirmed as reasoning; minimum rules written in AUDIT WRITES. `migrate.py:80-85` accepts only `CREATE OR REPLACE FUNCTION`: confirmed.
- Design M2 (INSERT rule): CONFIRMED: `requests.py:97-107`, `agent_loop.py:747` and `:762-763` (gate decision and WAITING state come before the request, so the INSERT checks are feasible), `_recheck` `:776-797` never reads the approval. Added to the guard.
- Design M3 (frozen columns): CONFIRMED; `summary` has no update path (`requests.py:124,166,198,207` change other columns), `step_expires_at` changes only in the escalation (`requests.py:196-201`); clock-skew allowance added (`tick.py:81`).
- Design M4: CONFIRMED in src (`0002_audit_chain.sql:28-35` plain triggers; `migrate.py:219` compares owner name only; `migrate.py:285-288` optional roles). PARTLY CONTESTED: "like app.py:86-89" - that line checks only a purge secret name; the app cannot see how `migrate` was called, so the refusal is written as a start-up `effective_problems` check, a new piece of code.
- Design M5: CONFIRMED: `migrate.py:256` excuses only SELECT columns.
- Design Nits 1-4 added to the guard (shared Python transition function; `save_approval_decision` has no src caller, only `test_store.py:131,132,135`; second trigger on `approval_decisions`, which breaks `test_store.py:131-135`; race: reviewer found none, I did not look independently). Nit 5: `:114` was already in the breakage list.
- Codebase M1: line 106 said four live choices; fixed to two (matches line 23). M2: `agent_loop.py:742` sets `restored_hash` on every `gate.decide`; `:845-866` stops with `restored_unbound` for every plan; qualifier fixed, conclusion unchanged.
- Codebase Nits: 1 (`chain.py:397-400`, `_body_event_id` `:406-410`) added; 2 (migrate callers) list completed incl. `cli.py:330`; 3 (`test_p2_postgres.py:290`, `test_store.py:237` rationale) fixed; 4 (`model_copy` has many src hits, none a Route) fixed; 5 (22 collection errors) fixed; 6 (`askdata/config.py:61-70` - the reviewer's `config.py:61-69` is the demo's file, not `src`; `_migrate` `cli.py:312`, call `:330-339`; `checkpoint()` `:295-320`) fixed.
- Contested: none outright; one partial (M4 wording above). The reviewer said "Row counts 26, Major 12..." true and unchanged.

## Changes
REVIEW.md only (header, Short answer, counts line, evidence bullet, C-4, X-5 (c)(iii) and (i), X-6, single-dependency outline, Counts reading and effective-Major paragraph, Not checked, Open for the studio head). Counts unchanged: 26 rows; 0 Blocker, 12 Major, 4 Minor, 10 Nit; 23 PROPOSE FIX, 3 DECLINE. count_review.py not changed (the row parser needed nothing).

# Round 14 (review-design-r14.md and review-codebase-r14.md; log appended here)

Backup: scratchpad bak-rev14b.md. Not committed. Nothing was run against Postgres or the patches; every SQL statement is a proposal.

## Unverified or not done (first)
- All Postgres behaviour in the new text (function and operator lookup through the temporary schema, `session_replication_role` grant, BEFORE UPDATE on the upsert branch, `TG_TABLE_SCHEMA` with `EXECUTE format()`, `ENABLE ALWAYS TRIGGER` through the scanner, a changed `schema_version` failing `model_validate`, hash parity of SQL and Python JSON text) is the design reviewer's knowledge, not checked by me. No source or test was edited; nothing was built.
- Not opened: how the plan hash is built (design point 3 says it covers placeholders; reviewer words); the other `runs` columns (point 2 names only `cost_usd`); the patched copies (still not on disk).
- Round 13 log above, Findings, Design B1 line, still says the search "finds nothing relevant"; that wording is wrong (see below) and is corrected only in REVIEW.md, because this log is append-only history.

## Findings, each opened in src
- Design Major 1 (functions and operators): CONFIRMED in src for the part that can be read: `migrate.py:210-212` checks CREATE only on `current_schema()`. Written into X-6 fix (1) (now "and", with `SET search_path = pg_catalog, <schema>, pg_temp`), (3) (every schema on the search path) and test (f).
- Design Major 2 (spend): CONFIRMED: key columns `0001_core.sql:87-91`, `0003_approvals_tick.sql:15-19`; grants `migrate.py:53-54`, `:47`; `postgres.py:433-442`; `limits.py:24-29`; `agent_loop.py:256-257`. Freeze keys, no decrease, monotonic `runs.cost_usd`, tests. Full `runs` column list not written.
- Design Major 3 (approval binding): CONFIRMED in src: `agent_loop.py:845-867`, `:273-278`, `:292`; `migrate.py:57`, `:65`. Plan-hash coverage not opened. X-6 point 3 and the AUDIT WRITES choice (1) now say it is a bypass, not harmless; studio head choice (5)(g).
- Design Major 4 (release A): CONFIRMED: `migrate.py:51`, `requests.py:97-107`. Written into X-6 point 4 and the CHANGELOG note.
- Design Major 5 (INSERT and UPDATE rules): CONFIRMED with one correction: the update builders SET every column except `approval_id` (`postgres.py:316-326`, `:349-355`), so the reviewer's "written by update builders" is true for `schema_version` only; `approval_id` is the WHERE key. The denylist point stands. `requests.py:103` confirms the agent writes `step_expires_at`.
- Minors 6 to 9: CONFIRMED in src (`requests.py:171`, `:211`; `chain.py:68-72`, `:397-410`; `postgres.py:349-355`; ENABLE ALWAYS needs a new migration because 0002 is released). Written as X-6 points 6 to 9.
- Wrong-claim note: CONFIRMED: hits at `migrate.py:126`, `migration_numbers.py:12-14`, `:251`; `refused_statements` `:633-639`. REVIEW.md B1 wording now says migration-time only and that `REVOKE TEMPORARY` is an operator deployment step.
- Codebase cites 1 to 7: all CONFIRMED and fixed: X-2 `record_decision` at `:337`; X-5 callers (`test_k5_fixes2.py:302`, `test_p3b_neutral_audit.py:324`, `test_k2_migrations.py:115,120,125`, `test_p2_postgres.py:78`; "completes" withdrawn); B1 wording; C-4 `tools.py:494`; G-2 `gate.py:59` (also `:42` found by me); C-3 `config.py:80-94`; X-6 (4) `agent_loop.py:809` loads, `:814` rechecks.
- Contested: none outright; the one partial is the `approval_id` point above.

## Changes
REVIEW.md only: header status, round log sentence, Short answer (X-6 round 14), X-2, X-5, X-6 (status, B1 wording, fix (1) and (3), test (f), point (4) wording, AUDIT WRITES choice (1), new ROUND 14 block), C-3, C-4, G-2, Not checked, Open for the studio head (sub-choices (d) to (g)). Severity of X-6 kept Major: no defect in today's source or the three patches beyond what the row records. Counts unchanged: 26 rows; 0 Blocker, 12 Major, 4 Minor, 10 Nit; 23 PROPOSE FIX, 3 DECLINE.

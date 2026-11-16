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

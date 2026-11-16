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

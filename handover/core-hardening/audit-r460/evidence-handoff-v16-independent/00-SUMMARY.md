# EVIDENCE RUNNER summary: independent run on CORE-PR-HANDOFF-v16.md (spend track) and evidence-handoff-v16/
Date 2026-11-16, started 17:01 UTC (22:31 IST), PostgreSQL 16.15 only. This file records; it does not judge. No existing file was edited, nothing committed or pushed, no spend, no secrets (all role passwords were random per run and never printed).

## 1. Failures and deviations (first)

**F1. DB-2 file has no `lock_timeout`, although the document says it has.** (my check `LOCK[decreaselog]`, raw-ind16-main.txt)
- `held-sql/spend_decrease_log.sql` contains 0 lines with `lock_timeout` (`grep -c`: DB-2 = 0; the other three files = 2, 1, 1).
- The document says otherwise in two places: 5.6(b) ("v16 adds ... the `lock_timeout` line") and 5.6(n) ("Each held file starts with `SET LOCAL lock_timeout = '5s'`"). `INVENTORY.md` also lists `lock_timeout` for this file.
- Test: another session held ROW EXCLUSIVE on `spend`, then the real `migrate()` applied DB-2 as 0006. The three DB-1 files failed with 55P03 after about 5 s and rolled back (3 of 3 PASS). DB-2 did not fail with 55P03: it waited until my own 14 s `statement_timeout` cancelled it (57014 after 14.0 s). Without my cap it would keep waiting (CREATE TRIGGER needs SHARE ROW EXCLUSIVE, which conflicts with a writer). The ledger row was not written (rolled back).
- The builder's own `pg_v16.py` has a lock check only for the default file (D1), so its 175 of 175 does not cover this.

**F2. Hash text in the document.** Section 8 of the document contains no sha256 for the held files; the hashes are in 5.6 (a) and (b) and in `sha256-v16.txt`. The upgrade file's hash (`fafa71fa...`) is only in `sha256-v16.txt`, not in the document text. Section 8 line 458 still prints v15's DB-2 hash `c7e1213d...` (labelled "carried from v15"), which is not the v16 file's hash (`4c37aea8...`). Not wrong if read as carried, but two different DB-2 hashes appear in one section.

**F3. Cite sample (step 5) is only partly machine-checkable.** See section 4: heuristic result 20 HIT, 4 MOVED, 16 MISSING, 20 RANGE-ONLY; my manual reading of the 40 non-HIT cites found 1 that I could not confirm (`guard/redact.py:1162`, the line is `"dev",` in a list of environment names; the document says it read this line and that it "holds what the sentence says", but I could not find the sentence it supports). The two caveats are in section 4.

**F4. Items I did not run:** Postgres 14 and 17.10 (only 16.15 is installed; no network install attempted), concurrency under parallel load, the product tests (none exist), Windows line endings, `ruff`/`pytest`/`bandit` gate (not asked).

No other failure. Control runs of every unmutated file through my harness: 0 failures.

## 2. What passed (raw files named)
| Step | Result | Raw file |
|---|---|---|
| 1. sha256 of every held file and builder script against `sha256-v16.txt` | 7 of 7 OK; 3 of the 4 held-file hashes also appear in the document text, 1 does not (F2) | raw-sha256-check.txt, raw-sha256-own.txt, raw-sha256-vs-doc.txt |
| 2. My own Postgres checks, own cluster (scram-sha-256, no trust line, 5 of 5 role secrets SCRAM, non-superuser migration role that owns the database, real `migrate()` over real migrations 0001-0005, then the held file as 0006/0007) | 222 of 223 pass; the one FAIL is F1 | raw-ind16-main.txt, raw-ind16-pg-version-main.txt |
| 3. Builder's `pg_run_v16.sh` unchanged on a copy (`bash pg_run_v16.sh <out> <python> <src> 1`) | `175 of 175 checks passed`, rc=0, 0 FAIL lines, PostgreSQL 16.15 | raw-builder-rerun-run1.txt, raw-builder-rerun-version.txt |
| 4. Mutations on scratch copies | 47 planted, 47 caught, 0 missed, 0 invalid (details section 3) | raw-ind16-mutations.txt |
| 5. 60 seeded cites | section 4 | raw-cites-sample60.txt |
| 6. Banned-string scan (BANNED read from `tests/test_no_reference_material.py` at run time; counts only) | 10 strings, 50 files with "v16" in a path part (includes this folder), 0 hits case-sensitive, 0 case-insensitive, 0 non-UTF-8 | raw-banned-count.txt |

What my step-2 checks cover (all through the runtime role `rt` unless named):
- DB-1 default, variant, and upgrade file: constraint text on both tables; INSERT and UPDATE of -0.01, -Infinity, NaN, Infinity, 0, -0, 0.00 and a 22-digit number on both tables (default accepts NaN and Infinity, refuses -0.01 and -Infinity; variant and upgrade refuse all four); INSERT ... ON CONFLICT with a negative delta refused 23514; plain UPDATE give-back works and below zero refused; applying default and variant together fails 42710; upgrade over a table holding a NaN row fails 23514, keeps the old rule on both tables, and leaves no 0007 ledger row.
- DB-2 (alone, on top of default, on top of variant): both SECURITY DEFINER functions owned by the non-superuser migration role with `search_path=pg_catalog, pg_temp`, PUBLIC and `rt` have no EXECUTE, direct call by `rt` refused 42501; the two non-definer functions carry the same search_path; both indexes exist; lowering of `spend` and `spend_month` each logs one row with agent, period, scope, old, new, login role `rt` and a current time; raise and same-value update log nothing; NaN and Infinity transitions logged, NaN to NaN not; kill switch on/off logged with old_by/new_by, a change of only `by` not logged; `rt` and `portal` get 42501 on SELECT, INSERT, UPDATE, DELETE and TRUNCATE of both logs; audit reader (my own SELECT-only grant) can SELECT and gets 42501 on the four writes, and cannot write `spend` or `kill_switch`; temporary-table attack (temp tables with the logs' names, `search_path = pg_temp, ...`) leaves the real logs +2 and +1 rows and the temp tables empty; a temp function named `clock_timestamp` does not change `at`; `rt` cannot CREATE SCHEMA, create `public.spend_decrease_log`, or SET ROLE mig; key-column updates on both tables refused 42501 with the trigger's text, usd-only update works; UPDATE, DELETE and TRUNCATE on both logs refused 42501 for the owner and for a superuser; owner INSERT works; with the log renamed, a lowering fails and the total is unchanged (fail closed); running `migrate()` again applies nothing.
- NaN, Infinity and negative at both tables: covered under DB-1 above (both tables, INSERT and UPDATE, three file kinds) and under DB-2 alone (lowering to -5 then to -Infinity logs two rows, `L7`).
- INFO only (not pass/fail, matches the document's own statement): the owner can DISABLE a trigger and a superuser with `session_replication_role=replica` can bypass the triggers.

## 3. Mutations (step 4): 47 planted, all on scratch copies in the scratchpad (`.../scratchpad/ind/`), held files untouched (sha256 re-checked after)
- 36 on `spend_decrease_log.sql` (M01-M36), 11 on the three DB-1 files (M40-M50). Each mutant ran the matching suite on a fresh database; "caught" means at least one check failed or the real `migrate()` refused the file.
- 47 caught, 0 missed. Each CAUGHT line names the first failing check (raw-ind16-mutations.txt). Controls (unmutated file through the same harness): 0 failures.
- Caveat on how they were caught: M03, M31, M32, M33 (search_path edits that do not change behaviour because the function already names its table with the schema) were caught only by my catalog check on the `search_path` setting, not by a behavioural failure. M29 and M30 (indexes) are caught only by an index-exists check. The lock-timeout mutants M44, M45, M50 are caught by the timing check (55P03 within 4-9 s). The count of 47 is by my oracle, which I wrote knowing these files; it says nothing about mutations I did not think of.

## 4. Cite sample (step 5)
Method (`cites16.py`, seed 16016): 312 file:line cites found by regex (231 distinct path and range); 60 drawn at random. HIT = file resolves, range inside the file, and an identifier in backticks just before the cite occurs inside the range plus or minus 1 line. MOVED = the identifier is only elsewhere in the file. MISSING = file not found, range outside file, or identifier not in the file. RANGE-ONLY = no identifier to match.
- Automatic: **20 HIT, 4 MOVED, 16 MISSING, 20 RANGE-ONLY** (60).
- The automatic MISSING and MOVED labels are unreliable here: the identifier in the sentence before a cite often names a test or planned item, not the cited line, and a follow-up cite (`, :355`) can belong to a different file than my parser assigns. So I read the code line and the sentence for all 40 non-HIT entries (printed in the raw file as CODE and CLAIM). Manual reading: 39 of the 40 have a code line that matches what the sentence says (for example `limits.py:17-18` is `charge`, `agent_loop.py:425-427` is the `.chat(` call, `bedrock_guardrail.py:101` is `apply_guardrail`, `migrate.py:93-94` is `_migration_files`, `pipeline.py:147` is `reserve`, `ci.yml` lines are the cited steps). 1 I could not confirm: `guard/redact.py:1162` (`"dev",`; see F3). Manual reading is my judgement and is not a program result.
- Nothing was MISSING by file: every cited file exists (`ci.yml` is under `.github/workflows/`; `pipeline.py` is a demo file).
- Cites in the document marked as planned files (`llm/spend.py`, `owner_gates.py`, `fileguard.py`) do not exist yet, as the document says. `near-miss-v14.txt` is in `evidence-handoff-v14-independent/`, not in the v14 folder.

## 5. Not run, and cleanup
- Not run: PostgreSQL 14 (lowest supported version unknown, L18), PostgreSQL 17.10 (the CI version), real parallel load, anything on a Windows checkout, the product tests (none written), `ruff`/`pytest`/`bandit` gate, any EGM skill.
- Scratch clusters: `/var/lib/postgresql/hv16ind_main`, `hv16ind_mut` and the builder script's `hadavin_v16_exp1`, all removed by their traps; `ls /var/lib/postgresql` shows only `16`; 0 `postgres` processes remain. Scratch folders under the session scratchpad (`ind/`, `copy16/`, `rerun/`) hold only temporary copies. No `__pycache__` created (`python -B -I`).
- Edits to existing files: none. New files: only in this folder.

## 6. Files in this folder
`run_ind16.sh` (cluster runner), `ind16.py` (my Postgres checks and mutation list), `cites16.py`, `banned16.py`, `checkpoint.md`, `raw-*.txt` as named above.
Re-run: `bash run_ind16.sh <out_dir> <python> <src_dir> ../evidence-handoff-v16/held-sql <scratch_dir> main|mut`.

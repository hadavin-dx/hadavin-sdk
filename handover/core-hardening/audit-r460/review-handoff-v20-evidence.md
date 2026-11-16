# Hand-off v20 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: evidence-handoff-v20-independent/00-TABLE.md. PostgreSQL 16.15 only. Recorded, not judged.
## Failures first
- B1 GUARD BYPASS: the guard does not pin the text of the ALTER TABLE ... ADD CONSTRAINT ... CHECK lines in spend_guarded_writes.sql. 4 of 78 file spellings judged CLEAN (H67, H68, H75, H76), all apply through migrate(). H75 puts CHECK (true) in place of the agent-id rule on both tables; H76 raises the ceiling to 1e30 on both; the runtime login then gets an id with a space, a newline id and a reserve of 1e20 accepted (genuine file refuses with 23514, cases D08, D11, D42). H67/H68 weaken only the spend table (spend_month still refuses). 74 others FLAGGED. Whether CHECK text is the guard's job is the lead's call.
- G1 the v20 python files are never linted: ruff 481 errors, format 31 files, bandit 12 High 7 Medium (B608, B102 exec in the spell30 guards); repo config excludes handover/.
- G2 pytest on 17 existing test files: 2 failed (the known brand-string and licence tests), 634 passed, 12 skipped (Postgres tests skipped, no DSN). 23 named test files do not exist, NOT RUN.
- G3 PostgreSQL 14 and 17 NOT RUN (apt 403 via proxy; L18 stays open).
- G4 run_secrets_v20.sh failed 10 of 12 until pydantic packages were copied in; its pre-check does not test for them.
- G6 silent no-ops in spend_settle on the genuine file (NULL or negative actual or worst, NULL day, missing day or month row): empty or unchanged result, no error; reservation stays open (safe direction) but the text says an empty result must be an error.
- G7 R13 (LOCK outside a transaction) tests nothing (25P01 first); inside a transaction ACCESS EXCLUSIVE and FOR UPDATE give 42501, ROW EXCLUSIVE and ACCESS SHARE allowed on SELECT-only.
- G5 runner slips: 16 min 31 s slot wait, own script bugs, two short smoke runs outside the slot (not evidence). G8 12 banned-string hits in raw/12-pytest.txt masked.
## Author commands re-run (PASS)
sha256 97 of 97 OK (CORE-PR-HANDOFF-v20.md not in list); pg_v20.py 177/177, 27/27 controls, 3/3 exploits; pg_v16_regress 175/175; secdef_mutants_v20 197 checks 0 failed; spell30_guard_v20 30/30; chk.py clean; run_secrets_v20.sh 12/12 after dependency fix.
## New hostile: 172 cases
78 file spellings (74 FLAGGED, 4 CLEAN; 58 applied, 20 refused); 72 data cases (all forbidden ids/amounts 23514; 0 invariant rows; cutover with open reservation refused); 22 runtime-login cases all 42501 or harmless.
## Scans
Banned 0 (100 and 103 files); secret-shape 0 real.
## Not run
PostgreSQL 14/17; gate4_v20.sh as one script; CodeQL, SonarCloud, CodeRabbit, pip-audit, Semgrep, zizmor, gitleaks; 23 absent test files; src/ mutation run; Postgres/vault repo tests.

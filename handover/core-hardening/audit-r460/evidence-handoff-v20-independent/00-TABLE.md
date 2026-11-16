# 00-TABLE: independent evidence run of hand-off v20 (EVIDENCE RUNNER: records, never judges)

Date 2026-11-16, run 19:01 to 19:36 UTC (00:31 to 01:06 IST on 2026-11-17). Machine: 4 cores, PostgreSQL 16.15 only. Nothing in v1 to v20, `src/` or `tests/` was edited. No commit, no push, no spend.

## 1. FAILURES, BYPASSES AND GAPS FIRST

| # | What | Exact command or file | Result |
|---|---|---|---|
| B1 | **GUARD BYPASS (guard says CLEAN, server accepts the weaker file).** The v20 guard does not pin the text of `ALTER TABLE ... ADD CONSTRAINT ... CHECK (...)` lines. A copy of the real DB-3 file in which the agent-id rule is `CHECK (true)` on both tables (H75) or the ceiling is `1e30` on both tables (H76) is judged CLEAN, applies through `migrate()`, and the runtime login then gets what the genuine file refuses: `spend_reserve('a b', ...)` and a newline id are accepted (genuine file: 23514, cases D08, D11), and `spend_reserve('big', ..., 1e20)` is accepted (genuine file: 23514, case D42). | `hostile_v20_indep.py` cases H75, H76 (and H67, H68, which weaken one table only: guard CLEAN, the other table still refuses, so nothing leaks through `spend_reserve`) | guard verdict CLEAN in run 1 and run 2; server applied; probe accepted; rows left in section 3. Scope note for the lead: whether CHECK text is meant to be inside the guard's job is the lead's call (the file header says the reviewer reads the file text); the guard has `EXTRA_BY_FILE` pins for one-off statements but none for the `ADD CONSTRAINT` lines of DB-3. |
| G1 | `ruff check` on the v20 python files as the brief asked (explicit file paths): **481 errors**, rc=1. `ruff format --check`: **31 files would be reformatted**, rc=1. `bandit -ll` on the same files: **12 High, 7 Medium**, rc=1 (47 B608 SQL-string findings, 2 B102 `exec` findings in `spell30_guard_v19.py` and `spell30_guard_v20.py`). | `raw/09-ruff-check-v20files.txt`, `raw/09-ruff-format-v20files.txt`, `raw/09-bandit-v20files.txt` | The repo's own ruff config excludes `handover/` (`extend-exclude`), so with `--force-exclude` ruff reports `All checks passed` (rc=0, "No Python files found"). The author's gate (`src tests demos`) therefore never looks at these files. Recorded, not judged. |
| G2 | `pytest` on the 17 test files the v20 text names that exist in `tests/`: **2 failed, 634 passed, 12 skipped** (rc=1). The 23 other test files the text names (for example `test_secdef_guard.py`, `test_guarded_writes_pg.py`) do **not exist** in `tests/` yet, so they were NOT RUN. | `raw/12-pytest.txt` | The two failures are `test_no_vendor_brand_string_is_tracked` and `test_licences_are_proprietary`: the same two the author's baseline lists (`evidence-handoff-v20/baseline/raw-gate4-base-pytest.txt`). Database tests skipped (no `HADAVIN_TEST_PG_DSN`, by the repo rule). |
| G3 | **PostgreSQL 14 and 17: NOT RUN.** `apt.postgresql.org` is refused by the egress proxy (curl: `CONNECT tunnel failed, response 403`); the Ubuntu noble archive here has no 14 or 17 server package. Floor question L18 stays open. | `apt-cache policy postgresql-14 postgresql-17` empty; `curl` 403 | not run, no workaround attempted |
| G4 | `run_secrets_v20.sh` failed 10 of 12 on my first try: the copied tree held `hadavin_sdk` but not its third-party imports (`pydantic`, `pydantic_settings` ...), so the probe printed a Traceback. After copying those packages next to it, 12 of 12 passed. The script's pre-check tests folder access only, not that the probe can import. | `raw/07-secrets.txt` (second try) | minor documentation gap in the author's instructions (INVENTORY and L18 say "installed packages" without naming them) |
| G5 | Slot waits: first hostile run waited **16 min 31 s** for a slot (asked 19:10:52, taken 19:27:23); all other heavy jobs waited 0 to 110 s. That run then stopped on a bug in MY script (a Postgres expression call on a stored query body), so it produced no evidence; later runs are in section 3. A second harness error (NUL byte in an agent id queried client side) was also mine; both runs kept as `raw/raw-hostile-run0-harness-error-NUL.txt`. | `raw/08-slot.txt` | my errors, fixed in `hostile_v20_indep.py`; final runs 1 and 2 are identical (diff empty) |
| G6 | Silent no-ops in `spend_settle` (observation, genuine v20 file): a settle with `p_actual` NULL, `p_worst` NULL, `p_worst` negative or `p_actual` negative, or with a NULL day, returns the unchanged totals with NO error and changes nothing (D55 to D58, D62). The reservation then stays open (safe direction), but a caller that treats "no error" as "settled" would keep it open for ever. The file text says an empty result must be an error; these cases return a row, or no row (D62, D63, D65, D66). | cases D55 to D58, D62, D63, D65, D66 | recorded |
| G7 | `LOCK TABLE ... ACCESS EXCLUSIVE` outside a transaction returned 25P01 before any privilege check (R13), so R13 does not test the right; R21 and R22 repeat it inside a transaction: refused 42501 for ACCESS EXCLUSIVE and for `FOR UPDATE`, allowed for ACCESS SHARE and ROW EXCLUSIVE locks on SELECT-only privilege (`ok`). | R13, R21, R22 | recorded |

Nothing else failed. Items that passed are in section 2.

## 2. Author's commands re-run (counts)

| Step | Command (from `evidence-handoff-v20/`) | Result | Raw file |
|---|---|---|---|
| 1 sha256 | `sha256sum -c sha256-v20.txt` | 97 of 97 lines `OK`, rc=0. `CORE-PR-HANDOFF-v20.md` (in the parent folder, not in the list): sha256 `c76f3ada7461b86ffc12b7fc68a1ec87f8466905b39a6774cdedc221d629672f`. | `raw/01-sha256-check.txt` |
| 2a | `pg_v20.py` through `run_pg_v20.sh` (my copy of the runner puts the cluster under `/tmp`, otherwise identical; PostgreSQL 16.15) | 177 of 177 safety checks PASS, 27 of 27 controls, 3 of 3 stated exploits shown, 0 FAIL, rc=0. Slot 1 taken 19:03:43, load average 5.3 at request. | `raw/raw-pg-v20-indep.txt`, `raw/raw-pg-version-raw-pg-v20-indep.txt` |
| 2b | `pg_v16_regress.py` through the same runner | `175 of 175 checks passed`, rc=0. Slot 1 taken 19:06:37. | `raw/raw-pg-v16-regress-indep.txt` |
| 2c | `secdef_mutants_v20.py held-sql <src>/hadavin_sdk/store/migrations` | `197 checks passed, 0 failed`; v19 guard misses 37, v18 86, v17 122, v16 150; rc=0 | `raw/04-secdef-mutants.txt` |
| 2d | `spell30_guard_v20.py` | `30 of 30 spellings flagged by v20`, rc=0 | `raw/05-spell30.txt` |
| 2e | `chk.py` (guard on the 5 held files and the 5 product migrations) | all ten `[]` (clean), rc=0 | `raw/06-chk.txt` |
| 2f | `run_secrets_v20.sh <python> <src>` (copy under `/tmp`, OS user `nobody`) | `SUMMARY failures=0`, 12 of 12 PASS on the second try (first try: see G4) | `raw/07-secrets.txt` |
| 4a | `ruff check`, `ruff format --check`, `bandit -ll` on the v20 python files | see G1 | `raw/09-*.txt` |
| 4b | `pytest` on the existing files the v20 text names | see G2 | `raw/12-pytest.txt` |
| 5a | banned-string scan: `evidence-handoff-v20/banned_count_v20.py` (author) and my `scan_indep.py` (NFKC and zero-width removal before matching), both read `BANNED` at run time from `tests/test_no_reference_material.py` | author: 100 files, 10 strings, 0 hits. Mine: 103 files (v20 folder, hand-off, other-tracks note, checkpoint, resolve note), 10 strings, **0 hits**; my own folder 45 files, 0 hits. The pytest output of the repo's own brand test printed the vendor strings of OTHER folders into `raw/12-pytest.txt`: 12 occurrences replaced by `[BANNED-STRING-MASKED]` (the only edit of a raw file; failure names and counts untouched) | `raw/10-*.txt`, `raw/15-scan-own-folder.txt` |
| 5b | secret-shaped scan (AWS key shape except the one allowed literal, private-key block, GitHub, `sk-`, Slack, Google key, URL with password, e-mail address, password literal) | 0 hits in every category. Two shape rules matched only non-secrets: 64-character hex (205 hits, all SHA-256 values) and 12-digit runs (`999999999999` amounts and digit runs inside SHA-256 values) | `raw/10-scan-v20.txt`, `raw/10-scan-v20-classify.txt` |

## 3. New hostile spellings, two identical runs

Script `hostile_v20_indep.py` (my own, none of the author's spellings), run through `run_pg_ind.sh` (a private cluster under `/tmp`, scram-sha-256, unix socket only, removed by trap). Raw: `raw/raw-hostile-run1.txt` and `raw-hostile-run2.txt` (diff of all result lines: empty); machine-readable `raw/hostile-rows-run1.json`. Counts: **78 file spellings, 72 data cases, 22 runtime-login cases = 172 cases.** Guard verdicts: 74 FLAGGED, 4 CLEAN (H67, H68, H75, H76: see B1). Server: 58 applied through the real `migrate()`, 20 refused (server error or `migrate()`'s own check).

Reading the columns. **Guard**: `allow_v20.check(secdef_guard_v20, <file name>, <text>)`; the file name selects the pins. **Server**: the changed file applied by the real `migrate()` on a fresh database (real 0001 to 0005 first, DB-2 genuine first, runtime role SELECT-only on the three tables, function grants as the author's `apply_function_grants`). **Probe**: what the runtime login then ran. **Effect**: `data CHANGED` means spend, month or kill-switch rows differ after the probe; for a probe that calls a genuine function a normal reserve also changes rows, so read it with the guard column. **Structure**: differences of triggers, functions, constraints, relations against the genuine files. BYPASS-CANDIDATE is a mechanical mark (guard CLEAN and a data change, leak or structure difference).


### 3.1 File spellings (H01 to H78)

| id | family | spelling | guard | server | probe, data, leak, structure | rows left (usd) | mark |
|---|---|---|---|---|---|---|---|
| H01 | RETURN body | SQL-standard RETURN expr, definer, leaks a table the runtime cannot read via query_to_xml | FLAGGED(5) | ok | probe ok; data unchanged; leak YES; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H02 | RETURN body | RETURN calls a second definer plpgsql helper that deletes spend | FLAGGED(13) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[] killsw_on=[True] |  |
| H03 | RETURN body | RETURN set_config('session_replication_role','replica',true) in a definer | FLAGGED(5) | ok | probe 42501,ok; data unchanged; leak no; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H04 | RETURN body | RETURN (data-modifying CTE) is not legal SQL: server must refuse | FLAGGED(7) | REJECTED by server 0A000: WITH clause containing a data-modifying statement must be at the top l | n/a (not applied) | n/a |  |
| H05 | RETURN body | invoker RETURN body with lower-case 'return' and quoted type, no attribute at all (control-like: plain function) | FLAGGED(2) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H06 | EXECUTE format | EXECUTE format('DELETE FROM %I.spend', 'public') in a plpgsql definer | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H07 | EXECUTE format | EXECUTE format('UPDATE %s SET usd = %L', 'public.spend', 0) | FLAGGED(8) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('seed', '0')] month=[('seed', '100')] killsw_on=[True] |  |
| H08 | EXECUTE format | EXECUTE 'DELETE FROM ' \|\| quote_ident('public') \|\| '.' \|\| quote_ident('spend') | FLAGGED(7) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H09 | EXECUTE format | positional %1$I.%2$I with USING-free format | FLAGGED(9) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H10 | EXECUTE format | EXECUTE of an E-string with escaped quote | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H11 | EXECUTE format | EXECUTE of a U&'' unicode-escape string | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H12 | EXECUTE format | PERFORM + EXECUTE built by array_to_string (no literal SQL word in the text) | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H13 | EXECUTE format | EXECUTE via chr() codes only (no keyword in text): TRUNCATE | FLAGGED(13) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H14 | dollar quote | body inside $a$ with an inner $b$ string holding the DELETE | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H15 | dollar quote | DO block builds a definer function from doubled quotes | FLAGGED(1) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE FU | n/a (not applied) | n/a |  |
| H16 | dollar quote | tag with a digit-free unicode tag $é$ | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H17 | dollar quote | single-quoted body with a '' inside a string that contains the word DELETE | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H18 | dollar quote | comment-looking text inside a quoted identifier hides the attribute | FLAGGED(7) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H19 | dollar quote | nested block comment around the keyword that the server also skips, then a live statement | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H20 | case/quoted | mixed-case keywords sEcUrItY dEfInEr | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H21 | case/quoted | quoted upper-case twin "Spend_Reserve" of a pinned name, evil body | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H22 | case/quoted | overload spend_reserve(varchar,date,numeric) with evil body (an overload picked by a typed call) | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H23 | case/quoted | pinned function re-created with the same signature and an added DELETE in the body (fingerprint pin) | FLAGGED(2) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('a', '1')] month=[('a', '1'), ('seed', '100')] killsw_on=[True] |  |
| H24 | case/quoted | pinned spend_settle with the month guard EXISTS removed (semantic weakening, same statement kinds and tables) | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H25 | case/quoted | pinned kill_switch_release without the `AND "on" = true` and without session_user (changed by-column) | FLAGGED(1) | ok | probe 42501; data unchanged; leak no; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H26 | schema/search_path | definer function in schema public, qualified name public.h26 | FLAGGED(7) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H27 | schema/search_path | search_path lists public AFTER pg_temp | FLAGGED(7) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H28 | schema/search_path | search_path TO form, correct value, but a function not on the list | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H29 | schema/search_path | ALTER FUNCTION of a pinned function to search_path public | FLAGGED(1) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('a', '1'), ('seed', '100')] month=[('a', '1'), ('seed', '100')] killsw_on=[True] |  |
| H30 | schema/search_path | ALTER ROUTINE ... SECURITY INVOKER-> DEFINER on a DB-1 style helper (ALTER ROUTINE spelling) | FLAGGED(1) | REJECTED by server 42501: must be able to SET ROLE "op17" | n/a (not applied) | n/a |  |
| H31 | schema/search_path | CREATE SCHEMA + shadow function + ALTER ROLE rt17 SET search_path | FLAGGED(8) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE SC | n/a (not applied) | n/a |  |
| H32 | schema/search_path | SET search_path at file level (session setting, not LOCAL) | FLAGGED(1) | REJECTED by migrate() ConfigError: the runtime role holds more than the grant map: rt17: can CREATE in schema pg_temp_28 | n/a (not applied) | n/a |  |
| H33 | DML on spend | BEGIN ATOMIC with a data-modifying CTE that deletes spend | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H34 | DML on spend | BEGIN ATOMIC DELETE ... USING spend_month | FLAGGED(4) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H35 | DML on spend | BEGIN ATOMIC UPDATE ... FROM ... RETURNING (lowers usd) | FLAGGED(4) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('seed', '0')] month=[('seed', '100')] killsw_on=[True] |  |
| H36 | DML on spend | BEGIN ATOMIC INSERT ... ON CONFLICT DO UPDATE SET usd = 0 | FLAGGED(4) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('seed', '0')] month=[('seed', '100')] killsw_on=[True] |  |
| H37 | DML on spend | MERGE ... WHEN MATCHED THEN DELETE in plpgsql definer | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H38 | DML on spend | TRUNCATE ONLY in plpgsql definer | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H39 | DML on spend | TRUNCATE TABLE ... spend_month, spend CASCADE in BEGIN ATOMIC is illegal; plpgsql form | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[] killsw_on=[True] |  |
| H40 | DML on spend | WITH u AS (UPDATE ... RETURNING) inside EXECUTE in plpgsql definer | FLAGGED(5) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[('seed', '0')] month=[('seed', '100')] killsw_on=[True] |  |
| H41 | trigger | ALTER TABLE spend DISABLE TRIGGER spend_keep_keys | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H42 | trigger | ALTER TABLE spend DISABLE TRIGGER USER / ALL | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H43 | trigger | DROP TRIGGER without IF EXISTS | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H44 | trigger | DROP TRIGGER IF EXISTS of a pinned trigger, never re-created | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H45 | trigger | ALTER TABLE ... ENABLE REPLICA TRIGGER spend_keep_keys (it then does not fire in a normal session) | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H46 | trigger | compound ALTER: ADD CONSTRAINT then DISABLE TRIGGER in one statement | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H47 | trigger | ALTER TABLE spend ADD COLUMN, ALTER COLUMN usd SET DEFAULT / DROP NOT NULL | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: same | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H48 | trigger | ALTER TABLE ONLY public.spend (qualified) DROP CONSTRAINT | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H49 | trigger | new trigger on spend that runs a definer function (AFTER UPDATE) set up as a pinned-name trigger lookalike | FLAGGED(6) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers,functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H50 | view/policy/rule | CREATE RULE ... DO INSTEAD NOTHING on spend UPDATE | FLAGGED(1) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE RU | n/a (not applied) | n/a |  |
| H51 | view/policy/rule | CREATE RULE ... DO ALSO UPDATE spend_month SET usd = 0 | FLAGGED(1) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE RU | n/a (not applied) | n/a |  |
| H52 | view/policy/rule | CREATE VIEW over a table the runtime cannot read, then GRANT SELECT to rt17 | FLAGGED(2) | REJECTED by migrate() ConfigError: migrations are inconsistent: h52 (view) is created by a migration but is not in GRANTS | n/a (not applied) | n/a |  |
| H53 | view/policy/rule | ENABLE ROW LEVEL SECURITY + CREATE POLICY USING (false) on spend | FLAGGED(2) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE PO | n/a (not applied) | n/a |  |
| H54 | view/policy/rule | CREATE MATERIALIZED VIEW / CREATE TABLE AS shadow of spend | FLAGGED(1) | REJECTED by migrate() ConfigError: migrations are inconsistent: spend_shadow (table) is created by a migration but is not in  | n/a (not applied) | n/a |  |
| H55 | role/set_config | top-level SET ROLE rt17 (file continues as another role) | FLAGGED(1) | REJECTED by server 42501: permission denied to set role "rt17" | n/a (not applied) | n/a |  |
| H56 | role/set_config | SET SESSION AUTHORIZATION rt17 / RESET ROLE | FLAGGED(2) | REJECTED by server 42501: permission denied to set session authorization "rt17" | n/a (not applied) | n/a |  |
| H57 | role/set_config | SELECT set_config('role','op17',false) at file level | FLAGGED(1) | REJECTED by server 42501: permission denied to set role "rt17" | n/a (not applied) | n/a |  |
| H58 | role/set_config | SET LOCAL "ROLE" quoted upper | FLAGGED(1) | REJECTED by server 42501: permission denied to set role "rt17" | n/a (not applied) | n/a |  |
| H59 | role/set_config | GRANT migr17-owned function EXECUTE with grant option to rt17 | FLAGGED(1) | ok | probe 42501; data unchanged; leak no; structure vs genuine: same | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H60 | role/set_config | GRANT op17 TO rt17 (role membership) | FLAGGED(1) | REJECTED by server 42501: permission denied to grant role "op17" | n/a (not applied) | n/a |  |
| H61 | unicode | function name spend_reserve with Greek nu (U+03BD) in place of v, evil body | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H62 | unicode | unquoted function name with a zero-width space inside (spend_res<ZWSP>erve) | FLAGGED(6) | ok | probe ok; data CHANGED; leak no; structure vs genuine: functions | spend=[] month=[('seed', '100')] killsw_on=[True] |  |
| H63 | unicode | NBSP (U+00A0) between SECURITY and DEFINER | FLAGGED(2) | REJECTED by server 42601: syntax error at or near "SECURITY DEFINER" | n/a (not applied) | n/a |  |
| H64 | unicode | zero-width joiner inside the word DEFINER (DEF<ZWJ>INER) | FLAGGED(2) | REJECTED by server 42601: syntax error at or near "DEF‍INER" | n/a (not applied) | n/a |  |
| H65 | unicode | full-width quotation / semicolon characters around a statement | FLAGGED(6) | REJECTED by server 42601: syntax error at or near "；" | n/a (not applied) | n/a |  |
| H66 | unicode | table name lookalike: Cyrillic a in spend_month (spend_month with U+0430) used as a shadow target | FLAGGED(1) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE TA | n/a (not applied) | n/a |  |
| H67 | weakened check | agent-id CHECK replaced by CHECK (true) (same constraint name, ADD form) | CLEAN | ok | probe 23514; data unchanged; leak no; structure vs genuine: constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] | BYPASS-CANDIDATE |
| H68 | weakened check | ceiling 1e12 changed to 1e30 in spend_guarded_ok | CLEAN | ok | probe 23514; data unchanged; leak no; structure vs genuine: constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] | BYPASS-CANDIDATE |
| H69 | weakened check | CHECK that calls a user function (volatile helper) in the expression | FLAGGED(4) | REJECTED by migrate() ConfigError: migrations are inconsistent: 0007_guard.sql: statement the guard does not read: 'CREATE FU | n/a (not applied) | n/a |  |
| H70 | DB-2 file | spend_log_decrease body gets an extra DELETE of the log through EXECUTE | FLAGGED(2) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H71 | DB-2 file | kill_switch_log_change handler swallows errors also when the switch goes OFF (no RAISE) | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H72 | DB-2 file | the append-only trigger on the log is disabled inside the file | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: triggers,functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H73 | DB-2 file | WHEN condition of the decrease trigger widened to never fire (NEW.usd < OLD.usd removed) | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H74 | DB-2 file | spend_log_decrease made SECURITY INVOKER-looking: attribute order moved after the body (plpgsql, search_path first) | FLAGGED(2) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H75 | weakened check | agent-id CHECK replaced by CHECK (true) on BOTH spend and spend_month (so a reserve with a space in the id works) | CLEAN | ok | probe ok,ok; data CHANGED; leak no; structure vs genuine: constraints | spend=[('a\nb', '1'), ('a b', '1'), ('seed', '100')] month=[('a\nb', '1'), ('a b', '1'), ('seed', '100')] killsw_on=[True] | BYPASS-CANDIDATE |
| H76 | weakened check | ceiling 1e12 raised to 1e30 on BOTH tables (a reserve of 1e20 is accepted) | CLEAN | ok | probe ok; data CHANGED; leak no; structure vs genuine: constraints | spend=[('big', '100000000000000000000'), ('seed', '100')] month=[('big', '100000000000000000000'), ('seed', '100')] killsw_on=[True] | BYPASS-CANDIDATE |
| H77 | DB-2 file | audit_log_append_only made a no-op (RETURN NULL) so the logs can be edited | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions,constraints | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |
| H78 | pinned semantic | kill_switch_engage turned around: sets "on" = false (same kinds, same table, same signature) | FLAGGED(1) | ok | probe ok; data unchanged; leak no; structure vs genuine: functions | spend=[('seed', '100')] month=[('seed', '100')] killsw_on=[True] |  |

### 3.2 Hostile data given to the GENUINE v20 functions (D01 to D70b), guard column not applicable (the genuine file is CLEAN)

| id | family | case | server result | rows left for that agent |
|---|---|---|---|---|
| D01 | agent id | 0 characters '' (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D02 | agent id | 1 character 'a' (expected by the file's rule: accept) | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D03 | agent id | 200 characters (expected by the file's rule: accept) | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D04 | agent id | 201 characters (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D05 | agent id | first char '.' (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D06 | agent id | first char '_' (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D07 | agent id | first char '-' (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D08 | agent id | inner space 'a b' (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D09 | agent id | leading space (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D10 | agent id | trailing space (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D11 | agent id | trailing newline (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D12 | agent id | inner tab (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D13 | agent id | carriage return (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D14 | agent id | single quote (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D15 | agent id | double quote (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D16 | agent id | backslash (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D17 | agent id | percent (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D18 | agent id | dollar (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D19 | agent id | semicolon (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D20 | agent id | star (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D21 | agent id | equals (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D22 | agent id | DEL 0x7f (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D23 | agent id | zero-width space inside (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D24 | agent id | RTL override U+202E (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D25 | agent id | BOM U+FEFF at end (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D26 | agent id | Cyrillic a (U+0430) first (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D27 | agent id | full-width a (U+FF41) (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D28 | agent id | NFD e + combining acute (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D29 | agent id | NFC e-acute (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D30 | agent id | emoji (expected by the file's rule: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D31 | agent id | NUL byte (client side) (expected by the file's rule: refuse) | error None | no row can exist (NUL cannot be stored in text) |
| D32 | agent id | allowed set all together (expected by the file's rule: accept) | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D33 | agent id | case twin 'A' vs 'a' (stated: separate budgets) (expected by the file's rule: accept) | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D34 | agent id | NULL agent id (expected by the file's rule: no row) | error 23502 |  |
| D35 | amount | reserve 0 (expected: no row) | ok [] | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D36 | amount | reserve -1 (expected: no row) | ok [] | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D37 | amount | reserve NULL (expected: no row) | ok [] | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D38 | amount | reserve 0.0000001 (expected: accept) | ok [['1E-7', '1E-7']] | day rows=1 usd=1E-7 open=1E-7; month rows=1 usd=1E-7 open=1E-7 |
| D39 | amount | reserve 999999999999.99 (expected: accept) | ok [['999999999999.99', '999999999999.99']] | day rows=1 usd=999999999999.99 open=999999999999.99; month rows=1 usd=999999999999.99 open=999999999999.99 |
| D40 | amount | reserve 1e12 exactly (expected: 23514) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D41 | amount | reserve 1e12 - 0.0000001 (boundary under) (expected: accept) | ok [['999999999999.9999999', '999999999999.9999999']] | day rows=1 usd=999999999999.9999999 open=999999999999.9999999; month rows=1 usd=999999999999.9999999 open=999999999999.9999999 |
| D42 | amount | reserve 1e20 (expected: 23514) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D43 | amount | reserve NaN (expected: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D44 | amount | reserve Infinity (expected: refuse) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D45 | amount | reserve -Infinity (expected: no row) | ok [] | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D46 | amount | reserve 1e131072 (numeric max digits) (expected: 23514 or 22003) | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D47 | day | reserve with day 2019-12-31 | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D48 | day | reserve with day 2020-01-01 | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D49 | day | reserve with day 2099-12-31 | ok [['1', '1']] | day rows=1 usd=1 open=1; month rows=1 usd=1 open=1 |
| D50 | day | reserve with day 2100-01-01 | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D51 | day | reserve with day infinity | error 23514 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D52 | day | reserve with day NULL | error 23502 | day rows=0 usd=0 open=0; month rows=0 usd=0 open=0 |
| D53 | settle | settle worst=10 actual=0 after reserve 10 (give back) | ok [['0', '0']] | day rows=1 usd=0 open=0; month rows=1 usd=0 open=0 |
| D54 | settle | settle worst=11 (more than open 10) | error 23514 | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D55 | settle | settle actual NULL | ok [['10', '10']] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D56 | settle | settle worst NULL | ok [['10', '10']] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D57 | settle | settle worst negative -5, actual 0 (try to raise open) | ok [['10', '10']] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D58 | settle | settle actual negative -1 | ok [['10', '10']] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D59 | settle | settle actual 1e12 (above ceiling) | error 23514 | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D60 | settle | settle actual NaN | error 23514 | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D61 | settle | settle actual 50 above worst 10 (stated safe direction) | ok [['50', '50']] | day rows=1 usd=50 open=0; month rows=1 usd=50 open=0 |
| D62 | settle | settle day NULL | ok [] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D63 | settle | settle for another day (no row for that day) | ok [] | day rows=1 usd=10 open=10; month rows=1 usd=10 open=10 |
| D64 | settle | settle twice: second give-back of the same 10 | ok [['0', '0']] | day rows=1 usd=0 open=0; month rows=1 usd=0 open=0 |
| D64b | settle | (second call of the line above) | error 23514 | day rows=1 usd=0 open=0; month rows=1 usd=0 open=0 |
| D65 | settle | settle where the month row is MISSING (day row only, open 7) | ok [] | day rows=1 usd=7 open=7; month rows=0 usd=0 open=0 |
| D66 | settle | settle where the DAY row is MISSING (month row only, open 7) | ok [] | day rows=0 usd=0 open=0; month rows=1 usd=7 open=7 |
| D67 | reserve | reserve 1 when only the day row exists (month row created?) | ok [['4', '1']] | day rows=1 usd=4 open=4; month rows=1 usd=1 open=1 |
| D68 | cutover | reservation of 5 open at the moment DB-3 is applied (old-style row), then give-back 5 -> 0 | error 23514 | day usd/open=('5', '0') month usd/open=('5', '0') |
| D69 | cutover | DB-3 applied over an old row whose agent id has a space | refused 23514 | spend rows=1; functions installed=0 |
| D70 | invariant | after every case above: rows with usd<0 or open<0 or open>usd in spend (day) table | 0 rows |  |
| D70b | invariant | same for spend_month | 0 rows |  |

### 3.3 Runtime login on its own (R01 to R22), genuine v20 database

| id | what | results in order | check query | table state after (usd) |
|---|---|---|---|---|
| R01 | CREATE TEMP TABLE spend, then spend_reserve (does the definer write the real table?) | ok ; ok:[(Decimal('1'), Decimal('1'))] ; ok:[(0,)] | [(1,)] | spend=[('seed', '100'), ('tmpa', '1')] killsw_on=[True] |
| R02 | CREATE TEMP TABLE spend_month + kill_switch, then kill_switch_engage | ok ; ok ; ok:[(None,)] | [(1,)] | spend=[('seed', '100'), ('tmpa', '1')] killsw_on=[True] |
| R03 | CREATE TEMP TABLE spend with a trigger (own temp table) and call spend_reserve | ok ; ok ; ok ; ok:[(Decimal('1'), Decimal('1'))] | [(1,)] | spend=[('seed', '100'), ('tmpa', '1'), ('tmpb', '1')] killsw_on=[True] |
| R04 | CREATE TRIGGER on the real spend table | ok ; 42501 |  | spend=[('seed', '100'), ('tmpa', '1'), ('tmpb', '1')] killsw_on=[True] |
| R05 | SET search_path = pg_temp, public then call the functions | ok ; ok:[(Decimal('1'), Decimal('1'))] | [(1,)] | spend=[('seed', '100'), ('sp1', '1'), ('tmpa', '1'), ('tmpb', '1')] killsw_on=[True] |
| R06 | CREATE TEMP VIEW spend then reserve | ok ; ok:[(Decimal('1'), Decimal('1'))] | [(1,)] | spend=[('seed', '100'), ('sp1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R07 | CREATE FUNCTION in public (shadow spend_reserve) | 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R08 | CREATE FUNCTION pg_temp.spend_reserve then call unqualified | ok ; ok:[(Decimal('1'), Decimal('1'))] | [(1,)] | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R09 | SET ROLE migr17 / set_config role / SET SESSION AUTHORIZATION | 42501 ; 42501 ; 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R10 | COPY spend TO PROGRAM / COPY FROM PROGRAM | 42501 ; 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R11 | ALTER TABLE spend DISABLE TRIGGER ALL; TRUNCATE spend; DROP TABLE spend | 42501 ; 42501 ; 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R12 | DROP FUNCTION spend_settle; CREATE OR REPLACE spend_reserve; ALTER FUNCTION ... SET search_path | 42501 ; 42501 ; 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R13 | set_config('session_replication_role','replica'); LOCK TABLE spend ACCESS EXCLUSIVE | 42501 ; 25P01 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R14 | CREATE RULE / POLICY / VIEW on spend | 42501 ; 42501 ; 42501 |  | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R15 | kill_switch_release as runtime; direct UPDATE kill_switch; direct UPDATE/DELETE spend | 42501 ; 42501 ; 42501 ; 42501 | [(True,)] | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('vw1', '1')] killsw_on=[True] |
| R16 | settle ANOTHER agent's open reservation (stated limit (b) of the file) | ok:[(Decimal('40'), Decimal('40'))] ; ok:[(Decimal('0'), Decimal('0'))] | [(Decimal('0'), Decimal('0'))] | spend=[('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R17 | reserve to the ceiling then settle at 0 (stated limit (a) of the file) | ok:[(Decimal('999999999999'), Decimal('999999999999') ; ok:[(Decimal('0'), Decimal('0'))] | [(Decimal('0'), Decimal('0'))] | spend=[('gamer', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R18 | create a temp table named spend_decrease_log / audit_entries then lower a total (settle)  | ok ; ok:[(Decimal('5'), Decimal('5'))] ; ok:[(Decimal('0'), Decimal('0'))] | [(2,)] | spend=[('gamer', '0'), ('lg', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R19 | SET LOCAL statement_timeout / lock_timeout then reserve inside a transaction block, ROLLBACK after reserve | ok ; ok:[(Decimal('9'), Decimal('9'))] ; ok | [(0,)] | spend=[('gamer', '0'), ('lg', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R20 | CREATE TABLE in public, CREATE SCHEMA, CREATE EXTENSION | 42501 ; 42501 ; 42501 |  | spend=[('gamer', '0'), ('lg', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R21 | LOCK TABLE spend ACCESS EXCLUSIVE inside a transaction (R13 hit 25P01 before any privilege check) | ok ; 42501 ; ok |  | spend=[('gamer', '0'), ('lg', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |
| R22 | SELECT ... FOR UPDATE on spend; LOCK ROW EXCLUSIVE; inside a transaction | ok ; 42501 ; ok ; ok ; 42501 ; ok |  | spend=[('gamer', '0'), ('lg', '0'), ('seed', '100'), ('sp1', '1'), ('tf1', '1'), ('tmpa', '1'), ('tmpb', '1'), ('victim', '0'), ('vw1', '1')] killsw_on=[True] |

## 4. Not run, not checked

- PostgreSQL 14 and 17 (G3). Behaviour of the held files on other minor versions of 16 is untested.
- `gate4_v20.sh` as one script (the author says it was not run as one script either); CodeQL, SonarCloud, CodeRabbit, pip-audit, Semgrep, zizmor, gitleaks; the 23 test files named in the v20 text that do not exist yet; the database and vault tests of the repo (no DSN, by rule); `perf` tests.
- Mutation run of `src/` (not asked). Only the guard's own mutants (197) and spellings (30) were run.
- Spellings in sections 3.1 to 3.3 are 172 cases of my own choosing; absence of a bypass in them is not proof of absence.
- `spell30_runner_v18_copy.py` was run only through the author's wrapper.

## 5. Housekeeping

Scratch clusters: one per run, under `/tmp/hv20ind-pg-<pid>`, removed by the runner's trap (`ls /tmp | grep hv20` empty at the end). The secrets copy under `/tmp/hv20ind-sec.*` was removed by its trap. `__pycache__` folders under `src/`, `tests/`, `demos/` and the v20 folders were deleted. Helper files of mine in this folder: `hostile_v20_indep.py`, `scan_indep.py`, `run_pg_v20_tmp.sh`, `run_pg_ind.sh`, `chain.sh`. Agents and processes started by me: none left running. Tokens: not measured here.

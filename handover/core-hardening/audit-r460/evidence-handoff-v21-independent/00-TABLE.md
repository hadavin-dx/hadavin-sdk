# EVIDENCE RUNNER, independent run of hand-off v21 (records only, no judging)

Runner: independent evidence runner for hand-off v21. Date 2026-11-16 (UTC). Folder: `handover/core-hardening/audit-r460/evidence-handoff-v21-independent/` (copy of `evidence-handoff-v21/`; the four v21 documents are copied to `docs/`; raw output in `run/`, gate output in `ind-gate4-*.txt`). No commit, no push, no spend, no live model call. Server: PostgreSQL 16.15 (the only version run). Python 3.13.18 venv with the pins of `pyproject.toml` (pydantic 2.14.1, pydantic-settings 2.16.1, psycopg 3.3.6) in `/tmp/hv21ind/venv`.

## 1. Failures, deviations and things NOT run (first)

1. **PostgreSQL 14 and 17: NOT RUN.** No apt package lists exist and `apt-get update` would write under `/var`, so I did not run it (`apt-cache policy postgresql-14` / `-17`: "Unable to locate package"). I then downloaded the Ubuntu archive `.deb` files for 14.24 (jammy) from `archive.ubuntu.com` (HTTP 200) and unpacked them under `/tmp/hv21ind` with `dpkg -x` (no system write). `ldd` showed the 14 binary needs `libldap-2.5.so.0`, `libicui18n.so.70`, `libicuuc.so.70`. When I tried to fetch those two libraries and run the unpacked `postgres --version`, the permission classifier DENIED the command ("Unauthorized Access"). I did not retry or work around it; the downloaded files were deleted. Next step for the lead: allow running downloaded server binaries from the Ubuntu archive in a throwaway folder, or provide PostgreSQL 14 and 17 on the machine. Every claim in this run is therefore about 16.15 only. Consequence for the held files: DB-3 and DB-1b/1c use `BEGIN ATOMIC` and `'Infinity'::numeric`, which need 14; that is untested here.
2. **Slot starvation, three jobs refused first time (exit 75).** `pg_v21.py`, `pg_v16_regress.py` and `hostile2_ind_v21.py` each waited 25 minutes with no free slot (other sessions held all three) and printed `heavy-slot: no free slot after 25 minutes, command NOT run` (kept as `run/slot-pg21-attempt1-exit75.log`, `slot-pg16-attempt1-exit75.log`, `slot-hostile2-attempt1-exit75.log`). I resubmitted each; all three then ran and finished with rc=0. The first Postgres runs therefore started at 20:12 and 20:16 UTC, not 19:46.
3. **The hostile spellings found guard gaps (facts, section 3).** The guard (`secdef_guard_v21` with `allow_v21.check`) returns CLEAN for a DB-3 file from which whole `ADD CONSTRAINT` lines were DELETED. The server applies such a file through the real `migrate()` and the runtime login then accepts a space or newline agent id (R01, R08), and with all eight lines deleted also a 1e20 reserve and a 1999 day (R04). ADD_PINS_BY_FILE is behaving as a list of statements that MAY appear, not statements that MUST appear (observed, not judged). The same holds for DB-1 files: deleting a month-table statement is CLEAN (Q02, Q03, Q05, Q07, O04, O16).
4. **My own slips.** (a) Data case "pre-existing spend_month row `-unattributed:x`" in the first hostile run inserted a month that is not the first of a month, so the row could not be inserted (23514); I re-ran the six month-table data cases as `hostile3_ind_v21.py` (section 5). (b) My first "no packages" negative test for `run_secrets_v21.sh` used the venv python that itself holds pydantic, so the pre-check did not fire; re-done with `/usr/local/bin/python3` (section 4, rc=3 as designed). (c) The first-run DB-1 probe tested only `spend`, not `spend_month`; the Q-series in run 2 tests both.
5. **Gate: 2 test failures, same as the author's baseline** (`test_no_vendor_brand_string_is_tracked`, `test_licences_are_proprietary`): the first lists banned-string hits in other sessions' scratch folders under `handover/core-hardening/steps-edits/`, the second lists LICENSE files under `handover/promotion-inputs/`; my folder is not among them (0 path matches). The gate sets no `HADAVIN_TEST_PG_DSN`, so 454 tests (database and vault) are skipped, as the script's header says. `uv run` used the repository's existing `.venv` folder.
6. **Banned scan.** The raw gate file `ind-gate4-pytest.txt` first held 16 banned-string hits (they come from echoing the failing test's message); I masked 12 occurrences with `<masked>` using the list read at run time. After masking: files scanned 186, strings checked 10, hits 0 (folder, the four v21 documents). No banned string is written in any script of mine.
7. **Secrets script ran from a copy**, because `/home/user` is mode 750 root and the OS user `nobody` cannot enter it (the script's own pre-check). I copied the folder and the source tree plus the venv packages to `/tmp/hv21ind/sec` (mode a+rX, my folder only, deleted afterwards). Nothing outside my folders and `/tmp/hv21ind` was changed; no chmod outside them; restore of modes not needed.
8. **Not run / not covered:** a catalog comparison of constraint text (the author lists it as impossible without 14 and 17); the full mutation run of the repository (not part of this brief); `HADAVIN_TEST_PG_DSN` tests; CodeQL, SonarCloud, CodeRabbit.

## 2. Standard runs (all PostgreSQL 16.15)

| step | command (wrapper) | result | raw |
|---|---|---|---|
| sha256 check, author's folder | `sha256sum -c sha256-v21.txt` in `evidence-handoff-v21/` | 0 lines not OK (all files and the four v21 documents OK) | |
| sha256 check, my copy | same in `evidence-handoff-v21-independent/` | 0 lines not OK | |
| Postgres script | `run_pg_v21.sh ... pg_v21.py` (slot, second attempt) | `SUMMARY safety checks 220 of 220 passed; controls 31 of 31 showed the old behaviour; stated exploits shown 3 of 3`, rc=0; 220 PASS lines, 0 FAIL, 0 CONTROL-FAIL, 0 STATED-NOT-SHOWN; lines identical to the author's `raw-pg-v21-run6.txt` after cutting the bracketed details | `run/ind-pg-v21.txt` |
| v16 regress | `run_pg_v21.sh ... pg_v16_regress.py` (slot, second attempt) | `INFO 175 of 175 checks passed`, rc=0, 0 FAIL | `run/ind-pg-v16-regress.txt` |
| secdef mutants | `secdef_mutants_v21.py held-sql <migrations>` | `235 checks passed, 0 failed`, rc=0 | `run/ind-mutants.txt` |
| spell30 guard | `spell30_guard_v21.py` | `SUMMARY 30 of 30 spellings flagged by v21`, rc=0 | `run/ind-spell30.txt` |
| chk.py | `chk.py` | every held file and every product migration prints `[]` (no problems), rc=0 | `run/ind-chk.txt` |
| secrets (12 checks) | `run_secrets_v21.sh <venv python> <src copy>` as root, agent = `nobody` | 12 PASS, `SUMMARY failures=0`, rc=0 | `run/ind-secrets.txt` |
| secrets pre-check negative | same, system python, source copy without packages | `PRECHECK FAILED ... nothing was tested`, rc=3 | `run/ind-secrets-nopkg.txt` |
| gate script | `heavy-slot.sh sh gate4_v21.sh ind-gate4` (slot 1, 20:05:20Z) | ruff rc=0; format rc=0; perf rc=0; bandit rc=0; pytest `2 failed, 9364 passed, 454 skipped, 26 deselected in 188.32s`, rc=1; compare: "failing names in baseline: 2; in this run: 2; new ones: 0", script rc=0 | `ind-gate4-*.txt` |
| banned scan | `banned_count_v21.py` (list read at run time) | after masking: files 186, strings 10, hits 0 | |

Scratch Postgres clusters: all created by `run_pg_v21.sh` under `/var/lib/postgresql/hadavin_v21_<pid>` (the wrapper's own trap stops and removes each); after the runs `/var/lib/postgresql` holds only the pre-existing `16` folder and no postgres process of mine is running.

## 3. Hostile spellings (real `migrate()` on 16.15)

Method: template databases (base migrations 0001-0005; plus DB-2 applied; plus DB-1 default applied), one fresh database copy per spelling, the spelling written as the next migration file and applied by `hadavin_sdk.store.migrate.migrate(runtime_role=...)` with the grant map select-only (`_RW` for the DB-2 cases), then `secdef_audit_v21.apply_function_grants` (as `pg_v21.py` does). Guard verdict = `allow_v21.check(secdef_guard_v21, <real file name>, text)`. Runtime probes = the runtime login calls `spend_reserve` with agent `a b` (space), ` a` (leading space), `a<newline>b`, a 1e20 amount, day 1999-01-01, and a control (`okagent`, amount 1); `ACC` = the call succeeded, `23514` = refused by a check. Owner-role probes = the migration role inserts directly. Counts: 142 server applications = 140 case ids (78 H + 28 R + 27 O + 7 Q, of which Q01, Q04 and Q06 are unmodified-file controls, so 137 hostile spellings) + the control C00 once in each of the two runs; the guard has no part in `migrate()` (it is a separate test), so "guard flags + server APPLIED" is expected and not a finding.

Summary lines printed by the scripts:
- run 1: `total=106 guard_clean=14 applied=95 weakened=30 CLEAN+APPLIED+WEAKENED=1 ['H23']`
- run 2: `total=36 guard_clean=18 applied=31 weakened=15 CLEAN+APPLIED+WEAKENED=8 ['R01','R02','R03','R04','R08','Q02','Q03','Q05']`

Guard CLEAN, server applied, and a probe shows a weaker table than the unmodified file (observed):
- **R01** both agent-rule lines deleted: runtime login accepts space, leading space and newline agent ids (1e20 refused by the open-amount ceiling, day 1999 refused by the window).
- **R04** all eight `ADD CONSTRAINT` lines deleted: runtime login accepts space, newline, 1e20 and day 1999.
- **R08** agent rule and usd ceiling deleted on both tables: runtime accepts space, leading space, newline; 1e20 reserve refused (the `open_usd` ceiling stays); owner role accepts 1e20 and a negative total.
- **R02** both usd ceilings deleted: owner role accepts 1e20 and a negative total; runtime 1e20 reserve refused (open-amount ceiling). **R03** both window lines deleted: runtime accepts day 1999-01-01. **R05** both open-amount ceilings deleted: no probe changes.
- **H23** (only the `spend` agent rule deleted): owner role accepts space and newline; runtime refused (the `spend_month` rule remains). **H29** month window deleted: no probe changes.
- DB-1 files: **Q02** (default, month rule deleted; O04 is the same file probed on `spend` only): the month table accepts a negative total; **Q03** (spend rule deleted): spend accepts a negative total; **Q05** (finite variant, month statement deleted): month accepts negative, NaN and Infinity; **Q07**/**O16** (upgrade, month statement deleted): month keeps the default rule (accepts NaN and Infinity).
- Guard CLEAN, no probe difference (same meaning or extra statements): H36 (comment inside the statement), H37 (block comment), H38 (tab/newline), H42 (comment only), R10 (order swapped), R18 (`COMMENT ON TABLE`), O08 and O27 (`lock_timeout` line removed; presence is checked elsewhere), O20 and O26 (extra `ADD CONSTRAINT` appended to DB-2; `ADD_PINS_BY_FILE` has no entry for `spend_decrease_log.sql`; O26 adds a CHECK that cannot loosen anything), O12 (same-meaning comment), R09 (duplicate line: server refused 42710), R15 (`\v`/`\f` between tokens: guard CLEAN, server refused 42601 on 16.15; PostgreSQL 17 not run).
- Guard flagged and server applied with a weaker table (the guard test is what stops these; the script counted weakened=30 in run 1, of which 1 guard-clean (H23), and weakened=15 in run 2, of which 8 guard-clean; the 7 guard-flagged ones of run 2 are R06, R07, R11, R12, R13, R25, R28): R11 to R13 are the hidden-DROP tricks (identifier `x$$`, E-string ending in two backslashes, plain string ending in a backslash) and the guard flagged all three; R25 replaces the `spend_reserve` body (runtime accepts everything).
- Server refused or errored (no table change): H26 (0A000), H48 (0A000), H55, H59, H63, H70, H73 (42501), H65 (42883), O21 (42501), R09 (42710), R15, R16 (42601), H54, H57, R17, R27 (migrate's own ConfigError: unknown statement shape or grant above the map).
- Owner/grant/search_path spellings (H55-H67): all flagged by the guard; the ones that applied did not change any probe (H55, H59, H63 were refused by the server 42501). DB-2 spellings (O18-O27 on `spend_decrease_log.sql`): O18 (`DISABLE TRIGGER ALL` on spend: a decrease wrote 0 log rows, a key change by the runtime login succeeded), O19 (append-only trigger of the log disabled: the owner role can delete log rows), O23 (`DROP TRIGGER spend_log_decrease`: a decrease wrote 0 log rows), O24 (`SECURITY INVOKER`: the runtime decrease is refused 42501, 0 log rows) were flagged by the guard; O20, O26, O27 are guard CLEAN and changed nothing observable.

### 3a. Run 1 (DB-3 spellings H01-H78, DB-1/DB-2 spellings O01-O27), raw lines in `run/ind-hostile.txt`
| id | guard verdict | server (real migrate) | runtime login probes (via spend_reserve) | owner-role direct probes | spelling |
|---|---|---|---|---|---|
| C00 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | CONTROL: the unmodified DB-3 file |
| H01 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | ceiling 1e12 -> 1e30 on spend.usd |
| H02 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ceiling -> 1e20 on spend.open_usd |
| H03 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | ceiling written as 1e12*1e9 (arithmetic) |
| H04 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | ceiling replaced by 'Infinity'::numeric |
| H05 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=ACC] | usd >= 0 -> usd >= -1e30 (negative totals allowed) |
| H06 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | month table ceiling -> 1e30 |
| H07 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | CHECK ... OR open_usd > 0 appended (bypass by a second column) |
| H08 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=ACC] | CHECK (true) |
| H09 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | CHECK (usd IS NULL OR usd >= 0) and no ceiling |
| H10 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | ceiling comparison flipped: usd < 1e12 -> usd > -1e12 |
| H11 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=23514 1e20=23514 neg=23514] | agent regex allows a space: [A-Za-z0-9._:@/+ -] |
| H12 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=ACC 1e20=23514 neg=23514] | agent regex allows newline via \n in the class |
| H13 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent regex start anchor removed (unanchored) |
| H14 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent regex end anchor removed |
| H15 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent operator ~ -> ~* (case-insensitive: harmless) |
| H16 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=23514] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent operator ~ -> !~ (inverted) |
| H17 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent rule NOT VALID |
| H18 | 1 problems | APPLIED | fn=4 rt[space=2201B lead=2201B nl=2201B 1e20=2201B day1999=2201B ok=2201B] | owner[space=2201B nl=2201B 1e20=2201B neg=2201B] | agent rule: length {0,199} -> {0,99999} |
| H19 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent rule E-string spelling (same meaning) |
| H20 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent rule dollar-quoted regex (same meaning) |
| H21 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent rule OR whitespace alternative |
| H22 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent rule on spend_month only weakened (space allowed) |
| H23 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent rule dropped from spend (line deleted) |
| H24 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent rule replaced by CHECK (agent_id <> '') |
| H25 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent rule: char_length(agent_id) BETWEEN 1 AND 200 only |
| H26 | 1 problems | REFUSED 0A000 | - | - | agent rule: IN (SELECT ...) is refused by server; test the guard text only |
| H27 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | day window upper bound -> 9999-01-01 |
| H28 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | day window lower bound -> 0001-01-01 (year 1) |
| H29 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | month window removed |
| H30 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | lowercase keywords: alter table ... add constraint ... check |
| H31 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER TABLE ONLY spend ADD ... (agent rule) |
| H32 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER TABLE IF EXISTS spend ADD ... (agent rule) |
| H33 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | schema-qualified public.spend (agent rule) |
| H34 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | constraint renamed (agent rule): spend_agent_len -> spend_agent_len2 |
| H35 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=23514] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | two ADD CONSTRAINT actions in ONE statement (comma) |
| H36 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | comment inside the statement (-- comment line) |
| H37 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | block comment inside the CHECK expression |
| H38 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | tab and newline whitespace between tokens (same meaning) |
| H39 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | NO INHERIT added (same meaning on a plain table) |
| H40 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | NOT   VALID with extra spaces and lowercase |
| H41 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | Cyrillic a in the constraint name (lookalike) |
| H42 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | fullwidth parenthesis lookalike inside a comment-only statement appended |
| H43 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | DROP CONSTRAINT spend_agent_len appended |
| H44 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=ACC] | DROP CONSTRAINT IF EXISTS spend_guarded_ok appended |
| H45 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | DROP CONSTRAINT spend_month_window appended (lowercase) |
| H46 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | DROP + ADD in one statement with a weaker CHECK (the upgrade shape) |
| H47 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | DISABLE TRIGGER ALL on spend |
| H48 | 1 problems | REFUSED 0A000 | - | - | ALTER COLUMN usd TYPE real (loses the numeric ceiling meaning) |
| H49 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER COLUMN usd DROP NOT NULL |
| H50 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ADD COLUMN open_usd DEFAULT 1e20 (default over the ceiling) |
| H51 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ADD COLUMN IF NOT EXISTS open_usd (same meaning) |
| H52 | 3 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | RENAME CONSTRAINT spend_agent_len TO old_len + new weak one |
| H53 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | DISABLE ROW LEVEL SECURITY / no-op policy |
| H54 | 1 problems | ERROR ConfigError:migrations are inconsi | - | - | CREATE RULE ... DO INSTEAD NOTHING on spend |
| H55 | 1 problems | REFUSED 42501 | - | - | ALTER TABLE spend OWNER TO rt17 |
| H56 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | GRANT INSERT, UPDATE ON spend TO rt17 |
| H57 | 1 problems | ERROR ConfigError:the runtime role holds | - | - | GRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC |
| H58 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | GRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17 |
| H59 | 1 problems | REFUSED 42501 | - | - | ALTER FUNCTION spend_reserve OWNER TO rt17 |
| H60 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER FUNCTION spend_reserve SET search_path = public |
| H61 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER FUNCTION spend_settle SECURITY INVOKER |
| H62 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER FUNCTION ... RESET ALL (drops pinned search_path) |
| H63 | 1 problems | REFUSED 42501 | - | - | ALTER ROLE rt17 SET search_path = public (role-level setting) |
| H64 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | SET search_path = public at the top of the file |
| H65 | 1 problems | REFUSED 42883 | - | - | SET LOCAL search_path = pg_temp, public after lock_timeout |
| H66 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | set_config('search_path', ..., true) via SELECT |
| H67 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER DATABASE ... SET search_path via DO/EXECUTE |
| H68 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | DO block that drops a constraint via EXECUTE |
| H69 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | PREPARE + EXECUTE of a DROP CONSTRAINT |
| H70 | 1 problems | REFUSED 42501 | - | - | UPDATE pg_constraint SET convalidated = false (needs a superuser) |
| H71 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | lock_timeout 5s -> 0 (no timeout) |
| H72 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | statement_timeout 60s -> 0 |
| H73 | 1 problems | REFUSED 42501 | - | - | SET LOCAL role rt17 mid-file (identity change; later statements run as rt17) |
| H74 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | reserve: guard p_worst > 0 -> p_worst <> 0 (negative reserve) |
| H75 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | settle: drop the p_actual >= 0 guard on the first UPDATE |
| H76 | 2 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | agent id lower() inside reserve (changes budget identity) |
| H77 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | REVOKE line for kill_switch_release removed |
| H78 | 6 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | extra SELECT-only function with a SECURITY DEFINER body (data leak shape) |
| O01 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=ACC nan=ACC inf=ACC ok=ACC] | DB-1 default: CHECK (usd >= -5) |
| O02 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC ok=ACC] | DB-1 default: NOT VALID |
| O03 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=ACC nan=ACC inf=ACC ok=ACC] | DB-1 default: CHECK (usd >= 0 OR true) |
| O04 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC ok=ACC] | DB-1 default: month rule dropped |
| O05 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC ok=ACC] | DB-1 default: lowercase + ONLY |
| O06 | 1 problems | APPLIED | cons=[] | owner[neg=ACC nan=ACC inf=ACC ok=ACC] | DB-1 default: DROP CONSTRAINT appended |
| O07 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=ACC nan=ACC inf=ACC ok=ACC] | DB-1 default: second statement ADD CONSTRAINT other name CHECK (true) plus DROP of first via comma |
| O08 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC ok=ACC] | DB-1 default: lock_timeout removed |
| O09 | 2 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=ACC ok=ACC] | DB-1 finite: 'Infinity' -> 'NaN'::numeric bound |
| O10 | 2 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 finite: bound 'Infinity' -> 1e300 (finite but huge) |
| O11 | 2 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 finite: `OR usd IS NULL` |
| O12 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 finite: block comment hides weaker bound |
| O13 | 1 problems | APPLIED | cons=[] | owner[neg=ACC nan=ACC inf=ACC ok=ACC] | DB-1 upgrade: ADD part removed (constraint only dropped) |
| O14 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 upgrade: re-added as CHECK (usd >= -1) |
| O15 | 1 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 upgrade: DROP CONSTRAINT IF EXISTS + ADD ... NOT VALID |
| O16 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 upgrade: month statement removed |
| O17 | 2 problems | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 ok=ACC] | DB-1 upgrade: ceiling 1e12 instead of Infinity (stricter, harmless: control of a legit change) |
| O18 | 1 problems | APPLIED | log_rows 0->0 | decrease=None keychange=None rt_delete_log=42501 owner_delete_log=None | DB-2: ALTER TABLE spend DISABLE TRIGGER ALL appended |
| O19 | 1 problems | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=None | DB-2: ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only appended |
| O20 | CLEAN | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=42501 | DB-2: ADD CONSTRAINT CHECK (true) on spend_decrease_log appended |
| O21 | 1 problems | REFUSED 42501 | - | - | DB-2: ALTER TABLE spend_decrease_log OWNER TO rt17 |
| O22 | 1 problems | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=42501 | DB-2: GRANT DELETE ON spend_decrease_log TO rt17 |
| O23 | 1 problems | APPLIED | log_rows 0->0 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=None | DB-2: DROP TRIGGER spend_log_decrease ON spend |
| O24 | 1 problems | APPLIED | log_rows 0->0 | decrease=42501 keychange=42501 rt_delete_log=42501 owner_delete_log=None | DB-2: ALTER FUNCTION spend_log_decrease() SECURITY INVOKER |
| O25 | 1 problems | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=42501 | DB-2: ALTER FUNCTION spend_log_decrease() SET search_path = public |
| O26 | CLEAN | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=42501 | DB-2: ALTER TABLE spend ADD CONSTRAINT stray CHECK (usd >= -1e30) (unrelated ADD in DB-2) |
| O27 | CLEAN | APPLIED | log_rows 0->1 | decrease=None keychange=42501 rt_delete_log=42501 owner_delete_log=42501 | DB-2: lock_timeout removed |

### 3b. Run 2 (combined and hidden-statement spellings R01-R28, DB-1 month probes Q01-Q07), raw lines in `run/ind-hostile2.txt`
| id | guard verdict | server (real migrate) | runtime login probes (via spend_reserve) | owner-role direct probes | spelling |
|---|---|---|---|---|---|
| C00 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | CONTROL: the unmodified DB-3 file |
| R01 | CLEAN | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | delete BOTH agent-rule lines (spend and spend_month) |
| R02 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=ACC] | delete BOTH usd ceiling lines |
| R03 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=ACC ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | delete BOTH day/month window lines |
| R04 | CLEAN | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=ACC day1999=ACC ok=ACC] | owner[space=ACC nl=ACC 1e20=ACC neg=ACC] | delete ALL eight ADD CONSTRAINT lines (columns kept) |
| R05 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | delete BOTH open_usd ceiling lines |
| R06 | 2 problems | APPLIED | fn=4 rt[space=ACC lead=23514 nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | BOTH agent regexes allow space and newline |
| R07 | 2 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=ACC neg=23514] | BOTH usd ceilings -> 1e30 |
| R08 | CLEAN | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=ACC neg=ACC] | delete agent rule AND ceiling on BOTH tables (four lines) |
| R09 | CLEAN | REFUSED 42710 | - | - | duplicate statement (agent rule twice): server must refuse |
| R10 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | statement order swapped (day window before agent rule): same set of statements |
| R11 | 4 problems | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | dollar inside an identifier (x$$) hides two DROP CONSTRAINT statements from a naive dollar-quote scanner |
| R12 | 4 problems | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | E-string ending in backslash-backslash hides both DROPs (naive scanner sees \' as an escaped quote) |
| R13 | 4 problems | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | standard string with a trailing backslash ('\') hides both DROPs |
| R14 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | nested block comment around a DROP (server: all comment) |
| R15 | CLEAN | REFUSED 42601 | - | - | vertical tab and form feed between tokens of a pinned ADD |
| R16 | 1 problems | REFUSED 42601 | - | - | non-breaking space between tokens of a pinned ADD (server: syntax error) |
| R17 | 6 problems | ERROR ConfigError:migrations are inconsi | - | - | plpgsql function that drops the agent rules, called by SELECT |
| R18 | CLEAN | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | COMMENT ON TABLE spend (harmless) |
| R19 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=23514] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ADD CONSTRAINT CHECK (false) appended (fail closed: spend unwritable) |
| R20 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | TRUNCATE spend appended |
| R21 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | UPDATE spend SET usd = 0 appended (erase totals) |
| R22 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | UPDATE kill_switch SET on = false appended (release in a migration) |
| R23 | 1 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER TABLE kill_switch DISABLE TRIGGER ALL appended |
| R24 | 1 problems | APPLIED | fn=3 grants:UndefinedFunction rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | DROP FUNCTION spend_settle(text,date,numeric,numeric) appended |
| R25 | 3 problems | APPLIED | fn=4 rt[space=ACC lead=ACC nl=ACC 1e20=ACC day1999=ACC ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | second CREATE OR REPLACE of spend_reserve with no ceiling guard (shape-equal, body different) |
| R26 | 2 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=23514 nl=23514 1e20=23514 neg=23514] | ALTER TABLE spend ADD CONSTRAINT with the ceiling spelled 10^12 via power() |
| R27 | 6 problems | ERROR ConfigError:migrations are inconsi | - | - | ceiling as an unqualified call to a user function in public (binding: search_path of the migration) |
| R28 | 2 problems | APPLIED | fn=4 rt[space=23514 lead=23514 nl=23514 1e20=23514 day1999=23514 ok=ACC] | owner[space=ACC nl=ACC 1e20=23514 neg=23514] | agent rule through a domain-free regex function: ~ replaced by textregexeq(agent_id, '.*') |
| Q01 | CLEAN | APPLIED | cons=['spend_month_usd_ok', 'spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC | month neg=23514 nan=ACC inf=ACC] |
| Q02 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=ACC inf=ACC | month neg=ACC nan=ACC inf=ACC] |
| Q03 | CLEAN | APPLIED | cons=['spend_month_usd_ok'] | owner[neg=ACC nan=ACC inf=ACC | month neg=23514 nan=ACC inf=ACC] |
| Q04 | CLEAN | APPLIED | cons=['spend_month_usd_ok', 'spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 | month neg=23514 nan=23514 inf=23514] |
| Q05 | CLEAN | APPLIED | cons=['spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 | month neg=ACC nan=ACC inf=ACC] |
| Q06 | CLEAN | APPLIED | cons=['spend_month_usd_ok', 'spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 | month neg=23514 nan=23514 inf=23514] |
| Q07 | CLEAN | APPLIED | cons=['spend_month_usd_ok', 'spend_usd_ok'] | owner[neg=23514 nan=23514 inf=23514 | month neg=23514 nan=ACC inf=ACC] |

## 4. Data cases (unmodified DB-3 file, real `migrate()`, runtime login through the functions)

Raw lines: `run/ind-hostile.txt` (lines starting `DATA`) and `run/ind-hostile3.txt`. Key observations (the full list is in the raw files):
- Pseudo agent ids: reserve with `-cli`, `-unattributed:foo`, `-` all refused 23514, no state change. A spend row `-cli` that exists before the file makes the apply REFUSED 23514 with no `open_usd` column and the ledger unchanged (5 rows). Month-table rows `-unattributed:x`, `-cli`, a newline agent, 2e12 and month 1999-01-01 each make the apply REFUSED 23514 (`run/ind-hostile3.txt`); a clean month row applies (control). Also refused at apply: spend rows with a trailing-space agent, 2e12, day 1999, NaN.
- Agent ids: 200 characters accepted, 201 refused, the e-acute, Cyrillic lookalike, trailing newline, leading/trailing/inner space, tab, zero-width space, fullwidth letter and empty string all refused 23514; NULL agent or NULL day refused 23502.
- Reserve amounts: NaN, Infinity, 1e12, 1e20, 1e30 refused 23514; 999999999999.99 accepted; two reserves of 6e11 for one agent: the second refused (cumulative ceiling). NULL, -1, 0 and -Infinity return NO row and no error and change nothing.
- Settle: NULL agent, NULL day, NULL worst, NULL actual, worst -1, actual -1, unknown agent, day without a row, month row missing (deleted by the owner role) and day row missing all return NO row, no error, no state change. Worst larger than open, NaN, Infinity, actual 1e20, actual 1e12: refused 23514. Settling agent `sb`'s own reservation as agent `sb` from the one runtime login succeeded (the file's stated item (b)). A second identical settle (nothing open) refused 23514. Settle with worst 0 and actual 3 raised the total by 3 with no reservation.
- Cutover with an open reservation: rows `usd=5` existing before the file get `open_usd=0`; settle worst 5 actual 0 is refused 23514 and nothing changes; a new reserve 3 then settle 3 works; a second settle 3 is refused. Final rows `usd=5, open_usd=0`.
- Roles: runtime login calling `kill_switch_engage()` and `kill_switch_release()` gets 42501; operator login calls both without error; runtime direct INSERT, UPDATE, DELETE, TRUNCATE on spend and UPDATE on kill_switch all 42501.

## 5. Not judged

No verdicts are given here. The lines in section 3 marked guard CLEAN with a weaker table, and the PostgreSQL 14/17 gap, are for the reviewers to weigh. Files in this folder written by me: `hostile_ind_v21.py`, `hostile2_ind_v21.py`, `hostile3_ind_v21.py`, `00-TABLE.md`, `run/`, `ind-gate4-*.txt`, `docs/`. Everything else is a byte copy of `evidence-handoff-v21/`.

Cleanup state at the end: no process started by me is running (the wrapper traps stopped every scratch server), `/var/lib/postgresql` holds only its pre-existing `16` folder, `/tmp/hv21ind/sec` deleted, `/tmp/hv21ind/venv` kept (my own Python environment, re-run needs it). Sub-agents started by me: 0. Background shell jobs started by me: all finished (checked with `ps`).

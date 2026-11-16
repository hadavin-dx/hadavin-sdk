# P3a round 7 correctness review (egm:egm-codebase-details), ticket rev 8. Verbatim reviewer report, saved by the lead; reviewer read-only, ran nothing.

Round 7 CORRECTNESS review of handover/tickets/P3a.md (revision 8). Verdict: not clean. 4 Major, 6 Minor, 2 Nit. I read the persona, the ticket (all 177 lines), LEAD-ORDERS, the template, and the core files cited below. I ran nothing. I could not read the git head, so "branch core/cloud-handover head dc3d6e5" is unchecked.

## Findings

| id | severity | where (ticket line) | problem | fix |
|---|---|---|---|---|
| COR-R7-1 | Major | 3, 33, 41 | The ticket says the commands and raw output of the revision-8 probes are in `handover/reviews/P3a-round6-disposition.md`. They are not. That file (lines 38-43) holds only summaries and says "Raw outputs ... were seen in my session, not saved". The probes with no record are: `U&"set\005fconfig"` returns `q`; FF and CR are whitespace while VT is not; `\g` mid-line and `\!` run under `psql -f`; `:'DBNAME'` is replaced; `x[1:n]` is left alone. Line 33 and line 41 cite the disposition as the raw-output home for these. `evidence/P3a-abort-commit-probe.md` has output only: it names `/tmp/r67.sql` but does not contain the SQL, so nobody can re-run it. `evidence/P3a-comment-cr-probe.md` does support the CR probe and the quoted and spaced `set_config` spellings. | Either save the raw commands and output under `handover/evidence/`, or reword the claims as "drafter's report, no record" and make evidence command 7c the proof. Add the probe SQL to the abort-probe file. |
| COR-R7-2 | Major | 100 (M26(d)), 83 | The killer for "no `E'` backslash rule" does not kill it. The test plants `E'a\'b'; COMMIT;` and expects it "refused". Under the mutant the string closes at `\'`, then `'; COMMIT;` opens a string that never closes. That returns "string not closed", so the file is still refused and the mutant survives. This is the same class as round 6 ADV-R6-5. | Add an exact-output case for `E'a\'b'`. Add a case that must NOT be refused: `SELECT E'\' ; COMMIT; --'`. The mutant would refuse it, because it would see a live `COMMIT`. |
| COR-R7-3 | Major | 101 (M27), 93 | Three M27 sub-mutants have no killer that fails on that mutant alone. (a) "Column set" names `DROP COLUMN state`. That statement is not in the planted list at line 93; it appears only in M27 and in the layer-2 negative control. It would also drop `runs_state_check` and `runs_by_state_age` and change the seeded rows, so other comparers would still fail and the mutant survives. (b) "Row count" is killed by `DELETE FROM spend` and `TRUNCATE`. Both also change the row values, so the values comparer still fails. (c) "Relation existence" is killed by `DROP VIEW`, which the view comparer also sees. The same-sentence claim "killed = the named test fails; every mutant killed" is unproven. | Add one isolating plant per sub-mutant. For column set, drop a column with no dependents, such as `runs.reason_code` or `tool_calls.attempt`. For count, add an extra row with `INSERT`. For relation existence, define what it compares apart from the view and table comparers. Put each plant in the line-93 list. |
| COR-R7-4 | Major | 32 (`hand_recipe`) | The recipe puts "the SQL text itself followed by" the ledger `INSERT` with no separator. The lexer accepts a file that ends in a `--` comment with no final newline. Then `-- done INSERT INTO schema_migrations ...` is one comment. `COMMIT` keeps the file's changes and no ledger row is written. The file is then still "late" and a second hand run applies it twice. A last statement with no `;` fails safely (a syntax error rolls back). The silent-comment case is a data-safety hole on the path whose purpose is data safety. No test or mutant covers it. | `hand_recipe` writes a newline before each `INSERT`. It refuses, or terminates with `;`, a text whose last statement is unterminated (the lexer can report this). Add a test with a trailing comment and no newline, and a mutant for it. |
| COR-R7-5 | Minor | 91 | The rule says "A must equal U on every kind" and "U must equal F", and "seeded rows" is one of the kinds. A and F have no seeds, and `kill_switch` is UPDATEd in U. By construction the rows differ, so H2 and `test_upgraded_equals_fresh` would fail. | State that the rows kind is checked only for U against the seed values. Structural kinds are compared A, U, F. |
| COR-R7-6 | Minor | 91, 93 | The trigger comparison names `pg_trigger` but not `tgenabled`. P2a-1 relies on `ENABLE ALWAYS`, and P2a says `CREATE OR REPLACE TRIGGER` resets `tgenabled` (P2a.md S14). The planted list has `DROP TRIGGER` but no `ALTER TABLE audit_entries DISABLE TRIGGER audit_entries_append_only`. A migration that disables the audit append-only trigger is not refused by the list or by the comparer as written. | Compare `tgenabled`. Plant a DISABLE case and add a mutant. |
| COR-R7-7 | Minor | 41, 83, 100 (M58) | The `U&"` rule and its test are written in upper case only. PostgreSQL's scanner start is `[uU]&"`, from memory and unchecked. `u&"set\005fconfig"(...)` is not covered. | Make the rule case-insensitive. Plant a lower-case spelling and make M58 cover it. |
| COR-R7-8 | Minor | 11, 92 | Cites into other tickets are stale. The tickets named below are at the current checkout. `P2a.md` line 10 is cited as the order list, which is now at line 15. `P2a.md` line 14 states that P3a's cites of its lines 10, 41, 75 and 118 are stale. `P2a.md` line 50 says the `ACCEPTED_CHANGES` key format is "defined by P3a", but P3a gives only "object, reason, package, named test". `P4b2.md` line 167 is cited for the `Grant` fields, which are at line 170. The header says these were "read this round". | Cite by item name, as P4d does. Define the `ACCEPTED_CHANGES` key shape. |
| COR-R7-9 | Minor | 11, 153 | Line 11 says "One builder, P3a's; P4d-b reuses it". `P4d.md` line 53 gives P4d-a1 the "behind schema builder" in `tests/contracts/kinds/store_postgres.py`. No ticket other than P3a names `tests/migration_schemas.py` (grep). There are two builders on two tickets. | Add this to the coupling table as a conflict the lead must settle. Do not state it as agreed. |
| COR-R7-10 | Minor | 148-155 | The coupling table misses four couplings. (1) `P4c.md` line 117 relies on "P3a's downgrade-read test (old code on the new schema keeps working)". P3a ships a structure comparer (layer 1) and a manual layer 2 only for ALTER-only migrations, and P4c-1 adds a table. (2) `P4c.md` lines 20-21 order `tests/test_k2_migrations.py` as "P4d, P2a-1a, then P4c-1" with no P3a, although P3a edits line 392. (3) `P4b2.md` line 164 lists `cli.py: P3a, ...`, but P3a does not touch `cli.py` (line 11). (4) `P5a.md` line 55 names `MigrationNumberError` (it inherits `config_invalid`). | Add P4c and P5a rows and a P4b2 correction to the table. |
| COR-R7-11 | Nit | 32 | `hand_recipe` does not check that each stem matches `STEM` before it puts the stem inside quotes in the `INSERT`. It is a public pure function. psql variable names also allow digits and non-ASCII bytes, and PostgreSQL 15 and later add `:{?name}`; the rule lists only letter, `_`, `'` and `"`. Unset names are left alone, so the effect is small. | Validate the stem. Say which psql name characters are in scope. |
| COR-R7-12 | Nit | 56, 11 | `test_k2_migrations.py:30-34` should be 29-33; the test starts at line 29. The ticket also says "UNVERIFIED whether P4b1 edits `migrate.py`", while `P4d.md` line 15 says "neither P4a nor P4b1 edits it". | Correct the cite. Resolve or cite the P4d statement. |

## Verified
Everything below is from reading the files only.

- **All 17 template fields** are present: package id, path class, depends on, problem, source, target, interface, neutral default, files, reused code, security, tests, mutation plan, evidence, reviewers, done, rollback.
- **Code cites into `migrate.py` all match:** 71 (`_FILE`), 97-107, 131, 132, 305, 308, 312, 316-317, 319-332, 320, 330, 331, 360. `errors.py:4`, `cli.py:70-83`, `pyproject.toml:52` (pglast), `test_lockin_guard.py:69`, `ci.yml:38-49`, 40, 82-83, 84-88, 104, and `demo_askdata/conftest.py:89-96` (S603 noqa at 93, PGPASSWORD at 92) also match.
- **Test cites all match:**
  - `test_k2_migrations.py`: 31, 36-55, 108, 357-371, 387-394, 390, 392.
  - `check_grants(files)` call lines 33, 63, 66, 73, 80, 86, 90, 96, 321, 327, 333, 345, 405, 410.
  - `test_k5_fixes1.py:181-186` and `test_k5_fixes2.py:282-309` (the `_migration_files` patch at 300, the assert at 304).
  - `test_p2_postgres.py`: 28, 78, 157, 277-290, with the hard-coded list at 290.
  - `test_k5_round10_postgres.py:137-142`.
- **Grep of `tests/`, `demos/` and `src/`:** exactly one `check_grants` patch (`:392`, a one-argument lambda). Other patches are `_migration_files` stubs taking no argument, which still fit the new `migrate()`.
- **The `:392` edit** is needed: `check_grants(files, texts=texts)` raises `TypeError` on the old stub. After the edit the test is green. The orphan `0005_evidence` has no same-text file and 5 is above 4, so case 2 prints and the phrase `no file in this release` stays.
- **`test_k5_fixes2.py:282` stays green.** The orphan `0005_evidence` matches the folder file `0006_evidence`, so case 1 prints. Case 1 contains "by hand" and does not print `0006_evidence`.
- **`test_plant_badly_named_file_is_caught` and the other `check_ledger` tests** keep their exact messages.
- **No other test breaks.** Other existing tests that run `migrate()` for real or with a patched `connect` (`test_p3b_neutral_audit.py:298-325`, `test_p2_postgres.py:276-290`, `warden_port/test_audit_chain.py:652`) are unaffected.
- **Migration files, counts and cites match:**
  - Statement counts 12, 9, 8, 2, 3 (34 in all).
  - 15 tables from 8, 3, 2, 0, 2 `CREATE TABLE`s.
  - `BIGSERIAL` at `0001_core.sql:64` and `:78`.
  - The `$f$` tag at `0002_audit_chain.sql:26` and the `$` in a string at `0003_approvals_tick.sql:31` are the only `$` characters.
  - Apostrophes in comments at `0004` lines 3-4 and `0005` lines 1 and 19.
  - `0003_approvals_tick.sql:10` is a `DELETE`.
  - The real files contain no backslash, and `::date` is the only colon use.
  - The real files trigger none of the new refusals (`DO` appears only inside `ON CONFLICT DO NOTHING`; `EXECUTE` only mid-statement).
- **The lock-key value** `3760701656253510835` is correct (I computed `int.from_bytes(b"hadvnmig","big") >> 1` by hand).
- **Mutant arithmetic is consistent:** 10 + 14 + 6 + 25 + 13 + 21 + 7 = 96; 90 - 3 + 9 = 96; M25 15 + 1 + 6 + 3 = 25; M27 lists 19; the 13-kinds arithmetic gives 19.
- **Mutant killers checked and sound:**
  - M26(i) is killed by the 0005 statement count.
  - M26(a), (c), (e), (f) and (g) are killed.
  - M9, M11-M19, M23, M24, M32-M36, M38-M43, M51, M55-M57 and M59 are killed.
  - The FAIL-BEFORE 1-7 reasoning holds on `ce70eb5`.
- **The H7a, H7b, H7c, H8 and H9a-c** `gone_message` case assignments follow the stated rules.
- **CHANGELOG lines 11, 38, 45, 52 are the only `0006` hits; line 10 is correct.** The `migrations/` folder holds only the five `.sql` files, so the CI stray-entry check will pass on the real folder.
- **The lock-in guard** scans `src/` only. `literal_problems` does not match the recipe words, and the lock number has 19 digits, not 12. The new module imports no database library.
- **Evidence files exist as cited.** `P3a-comment-cr-probe.md` supports the CR comment end and the quoted and spaced `set_config` spellings. `P3a-abort-commit-probe.md` output supports "ledger rows 0, table absent". The earlier-round review and disposition files exist.
- **The header arithmetic** holds: 16 ids, 14 rows, UTC to IST.

## Could not check
- The git head, branch and `git diff --stat ce70eb5 HEAD`.
- Any PostgreSQL or psql behaviour on 16.15 or 17.10, including VT and FF as whitespace, `U&"`, psql variable and backslash handling, the exit code 3, and the non-ASCII dollar tag rule.
- That `Path.glob` lists a dangling symlink (the ticket marks this UNVERIFIED).
- The `psycopg` multi-statement `execute` for H1 (existing `migrate` relies on it, so likely fine).
- Whether `test_no_hardcoded_values.py` accepts the new messages.
- Whether the evidence runner can get Postgres 17.
- The contents of `P2a.md` lines 41, 75 and 118, and the `P4b1.md`, `P6b1.md`, `P5a.md` and `P0c.md` bodies beyond the P3a mentions. The memo claims in line 21 were not checked.
- That the builder's lexer, seeds and tests will match the specification: nothing is built.
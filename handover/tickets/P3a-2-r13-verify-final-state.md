# Ticket P3a-2 round 13 (rev 1, DRAFT for plan review): judge the final state of the database with one check called `verify`, and say honestly what it can and cannot promise

Source: decision D-020 (handover/AUTONOMOUS-DECISIONS.md), which amends D-019 and replaces the scope sentence of D-009; the design review with addendum (handover/reviews/P3a-2/r13-design-zoomout-full.md); the two round-12 reviews (r12-design-full.md, r12-codebase-full.md); evidence in handover/evidence/P3a-2/4d328e3/ (route-probes.txt, design-probes*.txt, run by a separate EVIDENCE RUNNER); the ticket author's own probes in /home/user/build/p3a2-r13-author/ (p1..p6.sql and .out, v1.sql and v1.out, mut.py, tst.py).
Branch: continue `core/P3a-2-clean` from 4d328e3d, fast-forward only (no rebase, no force push). `core/P3a-2` and `core/P3a-2-rewritten` stay untouched. The builder never merges.
Path class: security (rights and least privilege). No round cap on result reviews.
Code references: `MIG` = src/hadavin_sdk/store/migrate.py, `MN` = src/hadavin_sdk/store/migration_numbers.py, `CL` = CHANGELOG.md, `TPG` = tests/test_migration_postgres.py, `TCMP` = tests/test_migration_compare.py, `TW` = tests/test_migration_wiring.py, `MUT` = tests/migrate_mutants.py. All line numbers are for the snapshot /home/user/build/snap/p3a2-r12-4d328e3/ (head 4d328e3d).
Status: written by a ticket author. Nothing is built. Fresh plan reviewers judge this ticket before any build. Times: written 2026-11-11 about 16:00 to 16:40 UTC (21:30 to 22:10 IST).

## Read first: what is not established

1. Every PostgreSQL fact below was run on PostgreSQL 16.15 only. Versions 17 (the version CI uses) and 18 were not run by anyone. The design has one built-in guard for that (the self-check in section 3.6), and the acceptance list makes the CI run on 17 a required evidence item.
2. The SQL in section 3 ran on the author's throwaway cluster against a small made-up setup (5 tables, 4 functions, 6 roles). It was not run on a large catalog. Its cost on a database with tens of thousands of objects is not measured (acceptance item 21 measures it).
3. Three things in this ticket go beyond the words of D-020 or correct the design review. They are marked AUTHOR ADDITION or CORRECTION where they appear and are collected in section 10.3 so the lead can accept or strike each one.
4. Facts taken from memory and not run by anyone are marked "from memory, unverified" in section 2. None of them carries the design alone.
5. OPEN CONFLICT between two runs, to be settled before the build (one command, shown in fact 14): the evidence runner's RESULTS.md (Step 9, row F3) says a trusted extension installed by a plain role "is owned by `postgres`", so the migration role "can never own `citext`". The author's run on the same server version shows the opposite, with output: the installing role owns the extension (`citext|r13_mig`), only the 47 functions inside it are owned by `postgres`, and the role could then add its own table and its own SECURITY DEFINER function to the extension. route-probes.txt ends at the heading of that precondition probe (line 92) and holds no output for it. The design does not depend on who is right: rule O6 has no condition (section 3.3).
5b. The evidence runner's RESULTS.md (sections "Step 5", "Step 6", "Step 9", "Addendum 2"), route-probes.txt, design-probes*.txt and the table of probe 6c were read and are used. The round-12 design finding 6 (rights that already existed before the run) has no row of its own in Step 9; two rows of probe 6c show the same class (facts 27 and 28).
5c. The mutant list: RESULTS.md says 280 mutants; importing the list object of `tests/migrate_mutants.py` at 4d328e3d gives 288 entries with 288 different names (author run, mut.py). The difference was not resolved. Section 5.5 uses the 288.
6. Not read by the author: the lexer body of `MN` (only lines 28-40 and 655-740), most test bodies (names, helpers and the lines cited in the reviews were read), DIFF-main-to-head.patch, TICKET-P3a.md, BUILDER-ticket-notes.md, cli.py beyond `_migrate` and the exit-code lines.

## 1. What this is about, in plain words

### 1.1 The problem

The package keeps its data in a PostgreSQL database. A small program called `migrate` sets that database up: it runs our SQL files (the "migration files") in order, and then gives three application logins exactly the rights they need. In PostgreSQL such a login or group is called a *role*. The three are the *runtime role* (the running application), the *portal role* (the read-only web portal) and the *purge role* (deletes old evidence). What each of them may do on each table is written down in one list in the code, the *grant map*. `migrate` itself connects as a fourth role, the *migration role*, which owns the tables.

After the files ran, `migrate` must make sure that the three roles can do what the grant map says and nothing more. Twelve rounds of work tried to do that by comparing the database before and after the files ("what changed during this run?"). Each round a fresh reviewer found another way to slip a right past that comparison: code that runs at the very end, kinds of object the comparison never read, rights that were already there before the run, and so on.

### 1.2 The decision

We stop asking "what changed?" and ask "what is true now?". One check, called `verify`, reads who can do what in the database and compares it with the grant map. It runs three times: before the first file, as the last thing before the changes are made permanent, and once more afterwards on a new connection. The before-and-after comparison is deleted.

We also stop promising what no check of this kind can deliver. A migration file runs as the owner of every table. Nothing that runs as that same owner can stop the owner from doing what an owner may do. So the promise is split by who wrote the file.

### 1.3 The promise table (decided in D-020; this exact table goes first in the module text and in the CHANGELOG)

"Stopped" means: the run is refused and everything it did is undone. "Detected" means: the run reports it loudly, but the change is already in the database and a person must act. "Lasting right" means a right that is still there when the check looks.

| Who wrote the file | What `migrate` does | Word |
|---|---|---|
| 1. We did, and made an honest mistake | When the file leaves a named role, or everyone, with a right outside the grant map, the run is refused and undone. The same mistake is caught before release, because the build server runs the shipped files on an empty database and tests what each role can really do. | STOPPED |
| 2. Someone careless, or a file copied from elsewhere | The same, for lasting rights only. Nothing is promised about lost data, and nothing about code the file leaves behind to run later. | STOPPED, for lasting rights only |
| 3. Someone who wants to do harm | NOT stopped. Lasting excess rights that exist when the check after the commit runs are reported, with the statements that remove them. | DETECTED, not stopped |

Why row 3 cannot be better: the file runs as the owner of every table. The real protections against a harmful file are elsewhere: a person reviews every file, each released file's fingerprint is recorded and checked (both exist today), and a separate read-only login that only checks (a new ticket, see 10.2 A).

### 1.4 What can never be noticed from inside the migration role, in any number of rounds

- A change that a file makes and takes back before it ends.
- A file that reads data or changes data.
- Code a file leaves behind (in a trigger, a rule, a column default, a view or a function) that runs later, as whoever touches the table next. That can be an administrator.
- A right that someone gives again one second after the check.
- Anything a file does outside its transaction (for example through a second connection).
- What the server reports when the reader itself is the one being cheated: the check after the commit still connects as the migration role. Only a separate checking login closes that (10.2 A).

A clean run therefore means "no excess right was there when we looked", not "the database is safe from now on".

### 1.5 Sentences in today's texts that claim more, and what happens to each

Quoted from the snapshot. "Delete" means the sentence goes and the promise table stands in its place.

| Where | Sentence today | Action |
|---|---|---|
| MIG:36-37 | "so a file cannot leave the migration role with what the first check refused" | Replace: "so a mistake in a file that changes the migration role's own rights is refused" |
| MIG:38-41 | "It compares the database before and after the files of THIS run ... so it finds an object that a file made or changed in any schema, by any statement, also by dynamic SQL" | Delete (item 5 of the docstring is rewritten around `verify` and the promise table) |
| MIG:45-48 | "Only what is the migration role's is compared ... An owner change made by dynamic SQL is found for these three kinds of object only" | Delete |
| MIG:56-57 | "any default right for a role other than the migration role itself (a named role included)" | Replace with the rule of section 3.3 D1-D3 (it names the two exemptions the code has) |
| MIG:296-301 | `effective_problems`: "What the role can REALLY do, however it got it" | Delete with the function body (replaced by `verify`; the new text says "read from the access lists and the memberships; see the promise table") |
| MIG:747-748 | "a file can create no type or domain: the guard refuses `CREATE TYPE` and `CREATE DOMAIN`" | Replace: "a statement the scan can read cannot create a type or a domain; dynamic SQL can, and `verify` judges the result" |
| MIG:1081-1087 | "Found by what the files left behind, so an object made or changed by dynamic SQL ... is found ... `_refuse_foreign_owned` looked at that before" | Delete with `_changed_since` |
| MIG:1240 | "Nothing was changed. The whole run is undone." | Replace by the three wordings of section 4.2 (one per call of `verify`; none says "nothing was changed" where that can be false) |
| MIG:1241-1244 | "a named role gets the rights of the grant map and nothing on any other table, view, sequence or function" | Replace by the baseline of section 3.4, in the same words as the CHANGELOG |
| MIG:1247-1249 | "or another session changed an object of the migration role while this run was open (the run compares the database before and after its files ...)" | Delete |
| MN:680-683 (comment on `_GRANT_TARGET`) | "is refused: the read-back after the file does not look at those places" | Replace: "is refused early, as a plain message for an accident. This rule carries no security claim: `verify` judges the result whatever the text says" |
| MN:722-723 (`refused_statements`) | "A quick check that catches accidents, not a sandbox: the read-back after each file is the guard." | Replace the last clause: "... not a sandbox, and not the guard: `verify` judges the final state. A way around a text rule is not a defect of this module." |
| CL:12 | "`migrate` refuses to run when that role could reach beyond this package's own objects, or could not change them" | Replace: "`migrate` refuses to run when that role holds one of the powers listed below, or could not change this package's objects". (No sandbox claim.) |
| CL:15 | "the old default of the `public` schema on PostgreSQL 14 and earlier; fix with ..." and "Not looked at by this check: rights in other schemas, `EXECUTE` on functions, and `REFERENCES` on one column." | Delete both (below 16 is refused; the three "not looked at" are now looked at) |
| CL:17 (whole item, about 900 words) | among others: "in ANY schema of the database, whatever way the file did it"; "`_refuse_foreign_owned` looked at it first"; "gets no right at all on a table, view, sequence or column that is not in the grant map, in any schema, and no right on a function"; "on PostgreSQL 14 and earlier the default of the `public` schema lets everyone create" | Delete the item. New item: the promise table, the baseline (3.4), the three calls (4), the after-commit message (4.2) |
| CL:18 | "because the read-back does not look at those places"; "a table, a type or a column that is called `rename` does not make an owner change pass"; "a file cannot create a type or a domain, the text scan refuses `CREATE TYPE` and `CREATE DOMAIN`"; "found by the read-back for a table, view, ... and for no other kind of object" | Delete the four sentences. New sentence: "These text rules refuse common accidents early with a plain message. They are not the guard; dynamic SQL passes them, and `verify` judges what is in the database afterwards." |
| CL:34 | "PostgreSQL 16 is the lowest version this check is written for" | Replace: "PostgreSQL 16 is the lowest version `migrate` runs on; an older server is refused with a plain message before anything is read or changed" |

The builder also runs `grep -n -i "however it got it\|whatever way\|by any statement\|cannot leave\|no right at all\|Nothing was changed"` over src, CHANGELOG.md and tests after the edit and pastes the output; each remaining hit is either inside a test of the old wording that was retired, or justified in one line.

## 2. Facts the design rests on

Status words: "author run" = verified by the ticket author's run on PostgreSQL 16.15 (own cluster, port 56190, files in /home/user/build/p3a2-r13-author/); "evidence runner" = in handover/evidence/P3a-2/4d328e3/; "memory" = from memory, unverified.

| # | Fact | Status and output |
|---|---|---|
| 1 | A temporary table named like a catalog table (for example `pg_class`) is read instead of the real one by an unqualified name, as long as the search path does not list `pg_catalog` before `pg_temp`. After `SET search_path = pg_catalog, pg_temp` the unqualified name reads the real catalog again. | author run (p1.out: `unqualified 0`, `qualified t`, `regclass_literal_same f`, after the pin `unqualified_after_pin t`); evidence runner, design-probes.txt F8/P1, same result |
| 2 | A temporary function does not shadow a built-in function. | evidence runner only (design-probes.txt P1) |
| 3 | `SET CONSTRAINTS ALL IMMEDIATE` runs the deferred triggers that are already waiting, and triggers queued later in the same transaction run at once. | author run (p2.out: `NOTICE: LATE FIRED` printed at the SET; access list changed before commit); evidence runner P2, same |
| 4 | CORRECTION. It is NOT true that no file code runs at COMMIT after that statement. A trigger function can run `SET CONSTRAINTS ALL DEFERRED` itself and queue new work, which then runs at COMMIT. | author run (p3.out: after the SET the access list of `app.audit_entries` is unchanged; `NOTICE: LATE2 fired, i=2` is printed at COMMIT; after COMMIT the list holds `=arwdDxt/r13_mig`). The evidence runner's P3 (RESULTS.md Addendum 2) says "no user trigger code observed at COMMIT in an already-immediate transaction"; that is true for what it tried (a trigger created later, and a temporary table dropped at commit) and it did not try a trigger that defers again. Both observations stand; the conclusion "nothing can run at COMMIT" does not. Consequence: the check before commit is never called the sound one. |
| 5 | A deferred trigger with no `SET CONSTRAINTS` runs at COMMIT and its grant is committed (round-12 design finding 1 in plain SQL). | author run (p2.out, "after commit"); evidence runner route-probes.txt F1: `migrate` returned "applied" and `audit_entries` is open to everyone afterwards |
| 6 | A membership granted `WITH INHERIT FALSE` is not counted by `has_table_privilege` (`f`), while `pg_has_role(..., 'MEMBER')` is `t`; the member can switch to the role and then read. | author run (p1.out: `has_priv f, member t, usage f, can_set t`; after `SET ROLE` the read works); evidence runner P4, same |
| 7 | Memberships are rows of `pg_catalog.pg_auth_members` with three options on 16: `admin_option`, `inherit_option`, `set_option`. A recursive query over that table gives every role a named role belongs to, whatever the options (section 3.2, Q1). Any role can read the table. | author run (v1.out Q1, Q1b, run as the plain role `r13_mig`) |
| 8 | The owner of the current database is treated by the server as a member of the built-in role `pg_database_owner`, and that membership is NOT a row of `pg_auth_members`. | author run (p4.out: `grp_is_db_owner_member t`, `auth_members_rows_for_pg_database_owner 0`) |
| 9 | The closed list of catalog columns that hold an access list (type `aclitem[]`) on 16.15, 14 columns: `pg_attribute.attacl`, `pg_class.relacl`, `pg_database.datacl`, `pg_default_acl.defaclacl`, `pg_foreign_data_wrapper.fdwacl`, `pg_foreign_server.srvacl`, `pg_init_privs.initprivs`, `pg_language.lanacl`, `pg_largeobject_metadata.lomacl`, `pg_namespace.nspacl`, `pg_parameter_acl.paracl`, `pg_proc.proacl`, `pg_tablespace.spcacl`, `pg_type.typacl`. | author run (p1.out and v1.out Q0, as a plain role); evidence runner P6, same 14. Note: the design review said "14 kinds" for the GRANT table; the count that matters here is 13 live access-list columns plus `pg_init_privs.initprivs`, which is a record of the rights objects had when the server or an extension was installed and gives nobody a right. |
| 10 | What everyone (PUBLIC) holds by default, per kind (`acldefault`): function `=X` (EXECUTE), type and domain `=U` (USAGE), language `=U`, database `=Tc` (TEMPORARY, CONNECT). Nothing for everyone on: table, view, sequence, column, schema, large object, foreign-data wrapper, foreign server, tablespace, parameter. | author run (p1.out, 13 rows of `acldefault`); evidence runner P7 by behaviour (new role: CONNECT t, TEMPORARY t, CREATE f; new function EXECUTE t; new type USAGE t; `plpgsql` and `sql` USAGE t) |
| 11 | An access-list column that is NULL means "the default of fact 10". `coalesce(acl, acldefault(kind, owner))` makes it readable in one query. The row type that every table gets has a NULL list, so everyone has USAGE on it by default; a grant on a row type is possible. | author run (p2.out: `typacl` empty for `audit_entries`, set for `runs` after a GRANT; v1.out shows `(everyone) USAGE` on the row types) |
| 12 | `pg_shdepend` holds a row of type `o` for every object a role owns (seen for table, function, database, and for a live temporary table) and a row of type `a` for every object whose access list names the role (seen for table, column with `objsubid` = column number, schema, database, type, large object as `pg_largeobject`, parameter, function, default rights). Rows for the database itself, and for parameters, have `dbid` 0. Memberships are not in it. | author run (p2.out P5, p3.out, v1.out Q3); evidence runner P5, same, including "`dbid = 0` rows are missed by a `current_database()` filter" |
| 13 | A role may change its own saved settings (`ALTER ROLE <itself> SET search_path = evil, pg_catalog`); a new session then starts with that path. A connection option (`options=-c search_path=...`) wins over the saved setting, and an explicit `SET` as a statement wins too. A plain role may not set `session_preload_libraries` for itself (the server answers "permission denied to set parameter"; when a superuser sets a bad value the role cannot connect at all). | author run (p1.out, p3 "P8": `pg_catalog`, then `evil, pg_catalog`, then `pg_catalog, pg_temp`); evidence runner P7-session and P8, same. The `session_preload_libraries` half: author run for the superuser case only; the refusal text for a plain role is from memory. |
| 14 | How a plain role comes to own an extension: it holds CREATE on the database (for example because it owns the database, which D-020 allows) and installs a trusted extension (21 are available on this machine, `citext` among them). It then owns the extension, while the objects inside are owned by the superuser. It can make its own table and its own SECURITY DEFINER function members of the extension (`ALTER EXTENSION citext ADD ...`; the `pg_depend` rows of type `e` appear). Without CREATE on the database it cannot install one ("permission denied for database"). | author run, as `r13_mig` with `current_user = session_user = r13_mig`: `CREATE EXTENSION`; `select extname, pg_get_userbyid(extowner)` gives `citext|r13_mig`; owner of the 47 member functions `postgres`; `ALTER EXTENSION` twice; `member|2`. CONTRADICTS the evidence runner's sentence in RESULTS.md Step 9 row F3 (which has no raw output; see "Read first" item 5). Command to settle it: as a plain role with CREATE on the database, `CREATE EXTENSION citext; SELECT pg_catalog.pg_get_userbyid(extowner) FROM pg_catalog.pg_extension WHERE extname = 'citext';` |
| 15 | `SET LOCAL search_path` inside a savepoint is undone by `ROLLBACK TO SAVEPOINT`. | author run (p4.out: `pg_catalog, pg_temp`, then `app`) |
| 16 | `REVOKE ALL ON TABLE t FROM r` also removes r's rights on single columns of t and r's grant options. | author run (after p5: list is `{owner..., r13_po=r/...}` and no column list is left) |
| 17 | CORRECTION. The join that the round-12 code review proposed for "which prepared transaction holds the lock" (`pg_locks.virtualtransaction = '-1/' || transaction`) returns no row on 16.15: the lock row of a prepared transaction keeps the virtual id of the session that prepared it (`4/129`). The working join goes through the prepared transaction's own lock on its transaction id (section 6.1). | author run with `max_prepared_transactions = 10` (p2.out: wrong join 0 rows; p3.out: corrected join returns `r13-holder` and not `r13-bystander`; also works as a plain role) |
| 18 | CORRECTION for the test design. From a superuser session, `SET ROLE x` after `SET ROLE y` is always allowed (the server checks the login, not the current role). To test "may this role switch to that role" the oracle must use `SET SESSION AUTHORIZATION <role>` first; then `SET ROLE` is refused with code 42501 where it should be. | author run (p6.out: three `SET` with no error under `SET LOCAL ROLE`; `ERROR: 42501: permission denied to set role "r13_boss"` under `SET SESSION AUTHORIZATION r13_po`) |
| 19 | A refused attempt has the error code 42501 for a table, a schema, a sequence (`nextval`) and a function. `EXPLAIN SELECT f()` is refused with 42501 without running the function; calling a trigger function directly gives 42501 without EXECUTE and 0A000 with it. | author run (p4.out, p6.out) |
| 20 | Server errors for effects a plain migration role cannot produce (they become "cannot be built on a plain role" cells in section 7.4): tablespace "permission denied for tablespace pg_default"; parameter "permission denied for parameter work_mem"; wrapper "permission denied to create foreign-data wrapper"; language "must be superuser to create custom procedural language" and `GRANT USAGE ON LANGUAGE plpgsql` gives "WARNING: no privileges were granted"; role flag "permission denied to alter role"; membership "permission denied to grant role" (also for the role itself: a role cannot grant itself to another); database right without owning it "WARNING: no privileges were granted for ..."; owner handover to a role it is not a member of "must be able to SET ROLE"; `CREATE SCHEMA` without CREATE on the database "permission denied for database"; default rights for another role "permission denied to change default privileges". | author run (p5.sql output) |
| 21 | On a fresh server the only roles named in an access list of a system object (schemas `pg_catalog`, `information_schema`), apart from everyone and the owner, are built-in `pg_*` roles (`pg_monitor`, `pg_read_all_stats`). | author run (p3.out, "SYS explicit grantees") |
| 22 | The name prefix `pg_` cannot be used for a new schema ("unacceptable schema name ... The prefix "pg_" is reserved for system schemas"). | author run (p2.out) |
| 23 | The server writes its own default (`=X` for functions, `=U` for types) into a default-rights entry for all schemas as soon as any default right is set there. | author run (v1.out Q4: row `f, (all schemas), r13_mig, (everyone), EXECUTE`); the snapshot comment MIG:1009-1014 says the same |
| 24 | Round-12 design findings reproduced through `migrate` on the round-12 head: 1 (deferred trigger), 2 (trigger on the ledger disables the audit triggers, plain and split-word), 4 (large object opened to everyone; the database half was not run), 5 (named role in a superuser group without inheritance, in `pg_execute_server_program`, in `pg_read_server_files`), 7 (login switches role): each run returned "applied". Finding 3 was NOT reproduced as written: the file with a plain `CREATE EXTENSION` is refused by a text rule, and the precondition (the migration role owns an extension) was not built by the evidence runner. Fact 14 shows the precondition can exist; the route through `migrate` itself (extension made beforehand or by dynamic SQL, then `ALTER EXTENSION ... ADD` in a file) has been run by nobody and is generator carrier C8. | verified by the evidence runner (RESULTS.md Step 9; route-probes.txt, files step9-f1f4 and step9-f5f7-v2) |
| 27 | Accepted by the round-12 head today: a SECURITY DEFINER function in ANOTHER schema that existed before the run, owned by the migration role (case C04p) or by a role the migration role belongs to (case C03o). | verified by the evidence runner (RESULTS.md Step 6 table). New design: rule S7 refuses it at the check before the first file whenever a named role, a role it belongs to, or everyone may call it (everyone may, by default), unless it is a member of an extension that the migration role family does not own. When nobody but its owner may call it, it gives the named roles nothing and passes. |
| 28 | Accepted by the round-12 head today: a function whose only change is a new saved setting (`ALTER FUNCTION ... SET search_path = public`, case C05); the same change on the package's own trigger function is refused by the read-back. Also accepted: `GRANT ... ON audit_entries TO <named role> WITH GRANT OPTION` in a file, and a large object opened by dynamic SQL. | verified by the evidence runner (RESULTS.md Step 6 table). New design: the saved setting of a function is not a right, so `verify` does not judge it (stated under 1.4, "code a file leaves behind"); the read-back keeps refusing it for trigger functions, at step 3 and again at step 6; a function of the family in the schema of the run can be called only by its owner after rule O2, and a SECURITY DEFINER one is refused whatever its settings. The grant option: with role arguments step 4 resets the role's rights and the option is gone (fact 16), and what is left is judged by S6; without role arguments rule O1 refuses the role. The large object: rules S5 and O2 (fact 9 column `pg_largeobject_metadata.lomacl`). |
| 29 | With `max_prepared_transactions = 0` the real-server test of the prepared-transaction message is reported as passed without calling `migrate`. | verified by the evidence runner (RESULTS.md Step 5: "mpt=0: 9 passed ... handles the mpt=0 default internally"); read in code by the author (TPG:4520) |
| 25 | PostgreSQL 17 has the same 14 columns; PostgreSQL 18 adds a default-rights kind for large objects. | memory, unverified. The self-check of 3.6 and the unknown-kind rule of 3.3 D4 make the design safe if this is wrong. |
| 26 | Operator lookup can be captured by a user-defined operator in a schema on the search path. | NOT shown: the author's probe (p4.out, a user-defined `=(name, text)`) did not change the result. The path is pinned anyway (it costs one statement). |

## 3. Design of `verify`

### 3.1 Signature and shape

New module `src/hadavin_sdk/store/migration_verify.py` (only `psycopg.sql` from the database library, as `store/migrate.py` uses it today; it imports `Grant` and `GRANTS` types from `migrate` only for type hints, or the two move here: builder's choice, stated in the notes).

```python
@dataclass(frozen=True)
class Problem:
    kind: str     # one of PROBLEM_KINDS (a closed tuple of words, one per clause of section 3.3)
    schema: str   # "" for an object that lives in no schema (database, large object, parameter, ...)
    obj: str      # the object's name; "" when the problem is about a role alone
    detail: str   # the column, the argument list, or the membership path; "" otherwise
    role: str     # the role that holds it; everyone is written "everyone (PUBLIC)"
    right: str    # the right, the flag, "OWNER", or "MEMBER"
    fix: str      # one SQL statement that removes it, or "" when a name is not plain (a person writes it by hand)
    repaired_by_run: bool = False  # true only for the two cases of section 4.1 step 2

    def line(self) -> str: ...


def verify(
    db,
    migration_role: str,
    named_roles: Mapping[str, Literal["runtime", "portal", "purge"]],
    grant_map: Mapping[str, Grant],
    *,
    schema: str,
    login_role: str | None = None,
    managed_functions: Sequence[str] = (),
    reviewed_definers: frozenset[tuple[str, str, str]] = REVIEWED_DEFINER_FUNCTIONS,
) -> list[Problem]:
```

- `migration_role` is the current user that `migrate` read once in step 1; `login_role` is the session user when it differs (a login that switches role). Both are plain strings passed in. `verify` never reads `current_user`, `session_user` or `current_schema()`; `schema` is the schema of the run, read once in step 1 (with the path pinned, `current_schema()` would answer `pg_catalog`).
- `named_roles` maps each role name given on the command line to the column of the grant map it gets. With no role arguments it is empty, and the subject side still judges everyone.
- `verify` only reads. It returns every problem (the caller cuts the printed list with `_shown`, the decision is taken on the full list).
- `verify` has two layers, so that tests can pin each: `_read(db, ...)` runs the queries of 3.2 and returns plain rows; `_judge(rows, ...)` is a pure function that turns rows into `Problem`s. All rules of 3.3 live in `_judge`.
- How it runs: inside `with db.transaction():` (a savepoint when a transaction is open, a transaction on the fresh connection). First statement inside: `SET LOCAL search_path = pg_catalog, pg_temp`. Then the version check (3.5), the self-check (3.6), the queries. The block always ends by rolling back (psycopg `Rollback`), which restores the search path (fact 15) and keeps nothing.
- Every catalog table, view, function and type in every query is written with `pg_catalog.` in front. No `::regclass` or `::regrole` from a bare text literal; `'pg_catalog.pg_class'::pg_catalog.regclass` is the allowed form.

A problem line (what `Problem.line()` returns), fixed order kind of object, schema.name, detail, role, right, what to do:

```
table app.audit_entries: everyone (PUBLIC) has SELECT. To remove: REVOKE SELECT ON TABLE "app"."audit_entries" FROM PUBLIC;
table other.secret: r13_rt can use it through the role r13_grp (a membership that does not pass rights on by itself, but r13_rt may switch to r13_grp), SELECT. To remove: REVOKE "r13_grp" FROM "r13_rt";
role r13_po: is a member of the built-in server role pg_read_server_files. To remove: REVOKE "pg_read_server_files" FROM "r13_po";
function app.door(q text): runs with the rights of its owner r13_mig (SECURITY DEFINER) and is not on the reviewed list. To remove: ALTER FUNCTION "app"."door"(q text) SECURITY INVOKER;  (or drop it)
```

Every name that comes from the database goes through the existing `_label` helper (MIG:1364) in the readable part. The `fix` statement is printed only when every name in it is plain (`escape_name(x) == x`, the rule `_refuse_foreign_owned` already uses at MIG:780); otherwise `fix` is empty and the line ends "a person must write the statement by hand (a name holds a character that is not copied into a printed line)". Statements are built with `sql.Identifier`, never by string formatting. This also closes the raw names at MIG:316, 324, 339, 353, 365; MIG:1314 (`usename`) gets `_label` in section 6.

### 3.2 The queries (each ran on the author's cluster as the plain role; result shapes pasted)

Parameters: `%(named)s` text array, `%(family)s` text array (`migration_role` and `login_role`), `%(schema)s` text. In the sketches the arrays are written as literals.

**Q0, self-check input** (section 3.6):

```sql
SELECT c.relname || '.' || a.attname
  FROM pg_catalog.pg_attribute a
  JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
  JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
 WHERE n.nspname = 'pg_catalog' AND c.relkind IN ('r','v') AND tn.nspname = 'pg_catalog'
   AND t.typname = '_aclitem' AND a.attnum > 0 AND NOT a.attisdropped ORDER BY 1;
```
Result on 16.15: the 14 rows of fact 9.

**Q1, the subjects.** A subject is a role whose rights count as a named role's rights: the named role itself and every role it belongs to, directly or through other roles, whatever the options. Everyone (PUBLIC) is always a subject too.

```sql
WITH RECURSIVE named AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])),
closure(root, role, at_once, depth) AS (
  SELECT n.oid, n.oid, true, 0 FROM named n
  UNION ALL
  SELECT c.root, m.roleid, c.at_once AND m.inherit_option, c.depth + 1
    FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member = c.role)
SELECT pg_catalog.pg_get_userbyid(c.root) AS named_role, r.rolname AS subject, min(c.depth) AS depth,
       bool_or(c.at_once) AS uses_rights_at_once, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls,
       r.rolreplication, (r.rolname ~ '^pg_') AS built_in
  FROM closure c JOIN pg_catalog.pg_roles r ON r.oid = c.role
 GROUP BY 1, 2, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication ORDER BY 1, 3, 2;
```
Result shape (v1.out):
```
 named_role |       subject        | depth | uses_rights_at_once | rolsuper | rolcreaterole | ... | built_in
 r13_po     | r13_po               |     0 | t                   | f        | f             |     | f
 r13_po     | pg_read_server_files |     1 | t                   | f        | f             |     | t
 r13_po     | r13_boss             |     1 | t                   | f        | t             |     | f
 r13_rt     | r13_rt               |     0 | t                   | f        | f             |     | f
 r13_rt     | r13_grp              |     1 | f                   | f        | f             |     | f
```
Q1b (same file) returns the direct membership rows with the three options, for the words of the message. The same recursion started from `%(family)s` gives the *migration role family*: the migration role, the login when it differs, and every role either belongs to. One more row is added in Python to both sets when it applies: a set that contains the owner of the current database also contains `pg_database_owner` (fact 8; Q2 returns the database owner).

**Q2, every access-list item that matters, one query over the 13 live columns.** Shape: one inner `UNION ALL` that brings each kind of object to the same columns `(kind, schema, name, sub, owner, definer, ext, acl)` with `coalesce(acl, pg_catalog.acldefault(<kind letter>, owner))`, then one `aclexplode`. The full text that ran is in /home/user/build/p3a2-r13-author/v1.sql (71 result rows on the made-up setup, no error, run as the plain role). Its branches: `pg_class` (relkind `r p v m S f`; letter `s` for a sequence, `r` otherwise), `pg_attribute.attacl` (only where not NULL), `pg_proc` (all `prokind`), `pg_namespace`, `pg_type` (array types left out: they follow their element type), `pg_database` (the current database only), `pg_foreign_data_wrapper`, `pg_foreign_server`, `pg_language`, `pg_largeobject_metadata`, `pg_parameter_acl`, `pg_tablespace`. Outer part:

```sql
SELECT o.kind, o.schema, o.name, o.sub, pg_catalog.pg_get_userbyid(o.owner) AS owner,
       (o.owner IN (SELECT role FROM fam)) AS family_owned, o.definer, o.ext,
       CASE a.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(a.grantee) END AS grantee,
       (a.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, (a.grantee = o.owner) AS owner_item,
       a.privilege_type, a.is_grantable, pg_catalog.pg_get_userbyid(a.grantor) AS grantor
  FROM obj o CROSS JOIN LATERAL pg_catalog.aclexplode(o.acl) a
 WHERE a.grantee IN (SELECT role FROM subj)                                   -- a subject is named
    OR (a.grantee = 0 AND (o.kind NOT IN ('function','procedure','aggregate','type','domain','language')
                           OR o.owner IN (SELECT role FROM fam) OR o.definer))  -- everyone, where it is judged
    OR (o.schema = %(schema)s AND (o.owner IN (SELECT role FROM fam) OR o.kind = 'schema'));  -- object side
```
Result shape (v1.out, cut):
```
     kind     | schema |     name      | sub  |   owner   | f | d | e |  grantee   | s | o | privilege_type | g | grantor
 database     |        | r13db         |      | postgres  | f | f | f | (everyone) | f | f | TEMPORARY      | f | postgres
 database     |        | r13db         |      | postgres  | f | f | f | r13_rt     | t | f | CREATE         | f | postgres
 function     | app    | door          | q text | r13_mig | t | t | f | (everyone) | f | f | EXECUTE        | f | r13_mig
 function     | other  | sd            |      | r13_other | f | t | f | (everyone) | f | f | EXECUTE        | f | r13_other
 large object |        | 424242        |      | r13_mig   | t | f | f | r13_rt     | t | f | SELECT         | f | r13_mig
 parameter    |        | work_mem      |      | unknown (OID=0) | f | f | f | r13_rt | t | f | SET          | f | postgres
 sequence     | app    | audit_entries_seq_seq | | r13_mig | t | f | f | r13_other | f | f | USAGE        | f | r13_mig
 table        | app    | audit_entries |      | r13_mig   | t | f | f | r13_rt     | t | f | INSERT         | t | r13_mig
 table        | other  | secret        |      | r13_other | f | f | f | (everyone) | f | f | SELECT         | f | r13_other
 table        | other  | secret        |      | r13_other | f | f | f | r13_grp    | t | f | SELECT         | f | r13_other
 type         | app    | runs          |      | r13_mig   | t | f | f | r13_rt     | t | f | USAGE          | f | r13_mig
```
Changes the builder makes to the sketch, each with a test: (a) the two system schemas are read as well, but only for items whose grantee is a subject role (never for everyone); other schemas whose name starts with `pg_` (temporary and toast schemas of sessions) stay out; (b) the `ext` column is computed for every kind that can be an extension member, not only relations and functions; (c) the extension's owner is returned next to `ext` (needed for rule S7); (d) the relkind is returned so that an access list on a relation kind outside `r p v m S f` becomes a problem line of its own ("a kind of relation this version does not read") instead of being skipped.

**Q3, what a subject or a family role owns, and where a subject is named** (`pg_shdepend`, all kinds in one query; fact 12):

```sql
SELECT d.deptype, d.classid::pg_catalog.regclass::text AS catalog, d.objid, d.objsubid,
       pg_catalog.pg_get_userbyid(d.refobjid) AS role,
       pg_catalog.pg_describe_object(d.classid, d.objid, d.objsubid) AS described
  FROM pg_catalog.pg_shdepend d
 WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass AND d.refobjid IN (SELECT role FROM subj)
   AND d.dbid IN (0, (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database()));
```
Result shape (v1.out, grouped there): `a | pg_class | table app.runs | r13_po`, `a | pg_default_acl | default privileges on new relations belonging to role r13_mig in schema app | r13_rt`, `a | pg_largeobject | large object 424242 | r13_rt`, `a | pg_parameter_acl | parameter work_mem | r13_rt`, `o | pg_class | table other.owned_by_grp | r13_grp`, `o | pg_database | database r13db | r13_grp`. The builder adds: rows with `dbid = 0` and `classid = pg_database` count only for the current database; an owned relation in a session's temporary schema is not a problem (fact 12: a live temporary table of a named role shows up here; TEMPORARY is part of the stated baseline).

**Q4, default rights, selected by who receives them** (not by who set them):

```sql
SELECT d.defaclobjtype::text AS kind, n.nspname AS schema, pg_catalog.pg_get_userbyid(d.defaclrole) AS set_for,
       (d.defaclrole IN (SELECT role FROM fam)) AS set_for_family,
       CASE a.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(a.grantee) END AS grantee,
       a.privilege_type, a.is_grantable
  FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
 CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
 WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam);
```
Result shape (v1.out): `f | (all) | r13_mig | r13_po | EXECUTE`, `f | (all) | r13_mig | (everyone) | EXECUTE` (the server's own entry, fact 23), `r | app | r13_mig | r13_rt | SELECT`, `r | other | r13_other | r13_rt | SELECT` (set by another role: the round-12 code never read this row).

No query is sent per role, per relation or per right: `verify` sends Q0, the version read, Q1 twice (subjects, family), Q1b, Q2, Q3, Q4 = 8 statements whatever the size of the database. `has_*_privilege` is not used (fact 6).

### 3.3 The rules (`_judge`); each lettered clause gets one `Problem.kind` and one mutant

**Subject side. For each named role and every role it belongs to:**

- S1 flags: none of the five flags (`SUPERUSER`, `CREATEROLE`, `CREATEDB`, `BYPASSRLS`, `REPLICATION`) on the named role or on any role in its closure.
- S2 built-in roles: no role in the closure has a name starting with `pg_` (this includes `pg_database_owner` added through fact 8).
- S3 family: no role in the closure is in the migration role family (a named role that can act as the owner of the tables). The existing rule "named roles are not members of each other" (`_members_of_each_other`, MIG:1471) stays and is asked through the same closure.
- S4 owns nothing: no subject role owns any object in this database or the database itself (Q3 type `o`), temporary objects apart.
- S5 rights: every item of Q2 whose grantee is a subject role, or everyone, must be allowed by the grant map for the named role it reaches, or by the baseline (3.4). The map is matched by (schema of the run, name, kind): `runs` in another schema is not the grant-map table, and a view called like a grant-map table is not it. Rights on one column count like the map's column list. A right that reaches the named role only through a role it must switch to (fact 6) is judged exactly like a direct one; the line says through which role.
- S6 no grant option for a subject role on anything (`is_grantable`), the grant map included.
- S7 SECURITY DEFINER through everyone: a function outside the system schemas that is SECURITY DEFINER and that a subject, or everyone, may execute is refused, unless it is a member of an extension whose owner is not in the migration role family.
- S8 named where nothing is read: every Q3 row of type `a` for a subject role must belong to a catalog that Q2 or Q4 reads (`pg_class`, `pg_proc`, `pg_namespace`, `pg_type`, `pg_database`, `pg_foreign_data_wrapper`, `pg_foreign_server`, `pg_language`, `pg_largeobject`, `pg_parameter_acl`, `pg_tablespace`, `pg_default_acl`). Any other catalog is a problem line "named in the access list of a kind of object this version does not read". This is the second, independent closure next to the self-check.

**Object side. For each object in the schema of the run that a role of the migration role family owns, and for the schema of the run itself whoever owns it:**

- O1 allowed grantees: the owner, the migration role itself (also on an object a group owns: this is the round-12 false refusal), and the named roles as far as the grant map gives it. Any other role is a problem. This rule is what protects a run with no role arguments.
- O2 nothing for everyone, with the one exception of 3.4 line 3 (row types).
- O3 no grant option for anyone but the owner and the migration role (the migration role may hold `USAGE ... WITH GRANT OPTION` on a schema it does not own; that is how the printed role of MIG:597-601 works).
- O4 SECURITY DEFINER only on the reviewed list. `REVIEWED_DEFINER_FUNCTIONS` becomes `frozenset[tuple[str, str, str]]` of (schema, name, identity arguments as `pg_get_function_identity_arguments` prints them); an entry whose schema is the constant `RUN_SCHEMA = ""` means the schema of the run. It stays empty. One unit test pins the key: same name in another schema, and an overload, are not excused.
- O5 AUTHOR ADDITION, group owner: when the owner of such an object is not the migration role itself but a group it belongs to, every other member of that group (read downward through `pg_auth_members`, any option) can act as owner. Each such member must be an allowed grantee with all rights, which a named role never is, so each is a problem line "can act as the owner of ... through the role ...". A group whose only member is the migration role passes (the supported case "database first built under a group role"). This replaces "an owner a file handed an object to" (which needed the before-state) by a rule about the state.
- O6 extension membership is no excuse: an object the family owns is judged the same whether or not it is a member of an extension. The rule has no condition in the code (there is simply no extension filter on family-owned objects), so it holds whoever is right in the open conflict of "Read first" item 5. It matters in practice only for a migration role that owns an extension; fact 14 says how such a role can exist (CREATE on the database plus a trusted extension), and an administrator can also create the situation by installing an extension while switched to the migration role.
- O7 schema of the run: any right other than USAGE for a role that is not the owner and not the migration role is a problem (today's rule, MIG:1217-1225, unchanged in meaning).

**Default rights (Q4):**

- D1 no default right for a subject role, whoever set it.
- D2 no default right for everyone on tables, sequences and schemas, whoever set it; on functions and types only the server's own entry for all schemas is accepted (`_BUILT_IN_DEFAULT`, MIG:1015, kept), an entry for one schema is refused.
- D3 for defaults set for a role of the migration role family: no grantee but that role and the migration role (today's rule, MIG:1004-1005).
- D4 a default-rights kind the code does not know (anything but `r S f T n`) is a problem line that names the letter and prints no guessed statement (this replaces `_DEFAULT_WORDS.get(kind, 'TABLES')`, MIG:1234).

### 3.4 The baseline: what everyone holds on every PostgreSQL server and how it is judged (printed in the CHANGELOG in these four lines)

1. System objects (schemas `pg_catalog` and `information_schema`): what everyone holds there is the server as shipped and is not judged. AUTHOR ADDITION: a grant there that names a subject role is judged (fact 21 shows a fresh server has none outside built-in roles, which S2 refuses anyway). D-020 says "not judged" without this exception; see 10.3.
2. Kinds where everyone holds nothing by default (table, view, sequence, column, schema rights beyond what an administrator gave, CREATE on the database, large object, foreign server, foreign-data wrapper, tablespace, parameter): judged everywhere in the database. Any right there for a named role, for a role it belongs to, or for everyone, that the grant map does not give, is refused. USAGE on a schema is allowed (it only lets a role look a name up).
3. Kinds where everyone holds a right by default (EXECUTE on a function, USAGE on a type, a domain or a language):
   - on an object of the migration role family in the schema of the run, everyone gets nothing; `migrate` removes the default from the functions its files name, anything else is refused with the REVOKE statement printed. CORRECTION to D-020's wording: the row type that every table carries is left out of this line (fact 11: every table of every database would be refused otherwise, and USAGE on a row type gives no access to the rows). A grant on a row type that names a subject role is still refused.
   - a grant that names a subject role, anywhere, is refused;
   - everyone's default on other owners' objects is not judged, except rule S7 (SECURITY DEFINER).
4. On the database: CONNECT is expected. TEMPORARY for everyone is the server default; it is stated here and not judged (the owner may tighten this later). CREATE on the database is refused for a subject role and for everyone. An explicit TEMPORARY grant that names a subject role is refused (it is outside the map and removing it changes nothing while everyone has it).

### 3.5 Refusal below PostgreSQL 16

First read inside `verify`, and also in `migrate` right after the lock: `SELECT pg_catalog.current_setting('server_version_num')::int`. Below 160000: `ConfigError("this database server is PostgreSQL <version as the server prints it>; migrate needs PostgreSQL 16 or later (it reads who is a member of which role in the form that version 16 introduced). Nothing was changed. Run migrate against a server of version 16 or later.")`. The version text goes through `_label`. Placed before the first query that needs 16 (`inherit_option`, `set_option`).

### 3.6 The run-time self-check of the access-list columns

`KNOWN_ACL_COLUMNS` in the new module: the 13 live columns of fact 9, each mapped to the branch of Q2 or Q4 that reads it, plus `pg_init_privs.initprivs` mapped to the reason "a record of the rights at install time; gives nobody a right". `verify` runs Q0 and compares sets:

- a column on the server that is not in `KNOWN_ACL_COLUMNS`: `ConfigError("this PostgreSQL version keeps access rights in a place this version of the package does not read (<column>). migrate cannot say that the roles hold only what the grant map gives. Nothing was changed. Use a PostgreSQL version this release names as supported, or a newer release of the package.")`;
- a known column missing on the server: the same error with "does not have (<column>)" (the queries would fail anyway; this gives the plain message).

How each of the 14 is treated (the exact list of fact 9, verified by the author and by the evidence runner):

| Column | Treated as |
|---|---|
| `pg_class.relacl`, `pg_attribute.attacl`, `pg_proc.proacl`, `pg_namespace.nspacl`, `pg_type.typacl` | read by Q2 for every object outside the system schemas (and inside them for items that name a subject role); judged by S5-S7 and O1-O7 |
| `pg_database.datacl` | read by Q2 for the current database only (other databases of the server are not checked: section 10.1); judged by baseline line 4. Its `pg_shdepend` rows have `dbid` 0, so Q3 reads `dbid IN (0, current)` and keeps a `pg_database` row only when it is the current database |
| `pg_largeobject_metadata.lomacl` | read by Q2, every large object of the database; judged by S5 and O2 (in `pg_shdepend` the catalog name is `pg_largeobject`) |
| `pg_foreign_data_wrapper.fdwacl`, `pg_foreign_server.srvacl`, `pg_language.lanacl` | read by Q2, every row; a grant that names a subject role is refused; everyone's default on a language is baseline line 3 |
| `pg_parameter_acl.paracl` | a list for the whole server (not per database); read by Q2, every row; any item that names a subject role or everyone is refused. (The existing check of the migration role's own parameter rights, MIG:616-627, stays.) |
| `pg_tablespace.spcacl` | a list for the whole server; read by Q2, every row; any item for a subject role or everyone is refused |
| `pg_default_acl.defaclacl` | read by Q4; rules D1-D4 |
| `pg_init_privs.initprivs` | known and NOT judged: a record of the rights objects had when the server or an extension was installed (used by `pg_dump`); it gives nobody a right. Listed so that the self-check knows it |

A repository test asserts that every live key of `KNOWN_ACL_COLUMNS` appears, with its `pg_catalog.` prefix, in the text of Q2 or Q4, so the list and the queries cannot drift apart.

## 4. New order of `migrate`

### 4.1 The eight steps

| Step | What happens | On failure: message, error class, exit code of `hadavin-sdk migrate`, what is kept |
|---|---|---|
| 0 (unchanged, before connecting) | Argument checks, file names, ledger order, released-file fingerprints, `check_grants` with the new duplicate rule (6.4) | `ConfigError` or `MigrationNumberError`, exit 2. Nothing touched. |
| 1 | Connect, open the transaction, take the lock (6.1-6.2), version refusal (3.5), the two time limits, `_refuse_privileged_role`, `_refuse_foreign_owned`, read `current_user`, `session_user` and `current_schema()` once into Python values, create the ledger table if missing, read the ledger, late-file checks. Unchanged except the version refusal and the three values. | `ConfigError`, exit 2. Rolled back; nothing kept. |
| 2 | `verify` before the first file. Problems with `repaired_by_run` are dropped here only. Those are exactly: (i) a right that names a named role directly on a relation of the grant map in the schema of the run (step 4 resets it with `REVOKE ALL` and grants the map again, fact 16); (ii) EXECUTE for everyone on a function in the schema of the run that the family owns and whose name the files create (step 4 removes it). Everything else stops the run. | `ConfigError` starting "before any migration file ran, this database already holds rights that the grant map does not give: ... Nothing was changed. No file ran. What to do: a database administrator runs the statements printed with each line (or removes the cause named there), then run migrate again." Exit 2. Nothing kept. |
| 3 | Each pending file, then the existing read-back after the file (`_check_read_back`, `_recheck_roles`), then the ledger row. Unchanged. The read-back stays because it names the file, which a state check cannot. | As today: `ConfigError` naming the file, exit 2, rolled back (with the existing sentence about a hidden COMMIT). |
| 4 | All writes of the runner itself: `_apply_grants` per named role; `REVOKE ALL ON ROUTINE ... FROM PUBLIC` for each function in the schema of the run that the family owns, whose name is in `_managed_names(...)[1]` and on which everyone has EXECUTE (read with one qualified query; this replaces "functions that changed"). No runner write comes after this step. | A server error here (for example the lock limit on a busy table) is reported as today (`_limit_error`), exit 2, rolled back. |
| 5 | `SET CONSTRAINTS ALL IMMEDIATE`. Triggers that waited for the commit run now. | An error raised by such a trigger is wrapped: `ConfigError("a trigger that was set to run at the end of the transaction failed when migrate ran it early: <server message through _label>. Nothing was kept.")`, exit 2, rolled back. |
| 6 | Last statements before the commit: the read-back once more (session values, triggers of the schema, memberships, saved settings; so a trigger on the ledger that disabled the audit triggers is refused as a mistake), `_recheck_roles`, then `verify` in full (nothing dropped), then the existing "each named role can use the schema" check moved into `verify` as a missing-right line (the only "too little" it reports). Nothing reads a user table. | `ConfigError` starting "after the migration files and the grants, rights that the grant map does not give are in place: ... The whole run is rolled back; the database is as it was before this run, unless a file ended the transaction itself (that is reported separately above). What to do: (1) if a migration file made it, remove that statement from the file; (2) if no file did, a database administrator runs the statement printed with the line; (3) run migrate again." Exit 2. |
| 7 | COMMIT (leaving the `with` blocks). | A server error at COMMIT: raised as it is, exit 3; the server has rolled back. |
| 8 | A NEW connection through the same `connect(...)` with one extra connection option `options="-c search_path=pg_catalog,pg_temp"` (fact 13), `verify` in full with the values of step 1. The first statement `verify` sends is the `SET LOCAL search_path` of 3.1; the one statement `connect` itself sends before (`SET TIME ZONE 'UTC'`, store/postgres.py:148) looks no name up. Runs also when no file was pending: running `migrate` again is the way to re-check. | See 4.2. |

Step 8 cannot connect (network, login): `AppliedNotVerifiedError` with the "could not be checked" wording of 4.2. It never returns "applied".

### 4.2 The failure after the commit

New class in `hadavin_sdk.errors`: `class AppliedNotVerifiedError(Exception)` with the attributes `applied: list[str]`, `problems: list[Problem]`, `statements: list[str]`. It is deliberately NOT a `ConfigError`: a `ConfigError` means "refused, nothing happened" everywhere in this package (cli.py:19, exit 2). `cli._migrate` catches it, prints the message to standard error, prints no "applied" line, and returns exit code 5 (the builder confirms by `grep -n "return 5\|exit 5" src/hadavin_sdk/cli.py` that 5 is unused; 0 to 4 are taken) and adds the code to the usage text at cli.py:9.

Exact wording (the three bracketed parts are filled in; the first sentence is fixed):

```
The files are applied and committed; the database is over-privileged now; run these statements; run migrate again to re-check.
Applied in this run: <versions, or "no file (nothing was pending)">.
What is wrong (<n> things): <problem lines, at most 20, then "and N more">.
Statements for a database administrator, in this order (every one is printed, not only the first 20):
<one REVOKE / ALTER ... per line, each ending with ";">
<when a fix is empty:> For <n> of them no statement is printed, because a name holds a character that is not copied into a printed line: a person writes those by hand.
migrate did not remove anything itself. Until a person has run the statements, the roles named above can do more than the grant map allows.
This check ran after the commit, on a new connection, as the migration role. A file written to do harm can also cheat this check; see "What migrate promises" in CHANGELOG.md.
```

When step 8 could not run at all: first sentence "The files are applied and committed, but the check after the commit could not run (<reason through _label>), so nobody has confirmed that the roles hold only what the grant map gives; run migrate again to check."

How the statements are printed: `Problem.fix` values, de-duplicated, in a fixed order (memberships first, then default rights, then object rights, then owner and SECURITY DEFINER changes), each built with `sql.Identifier` and `sql.SQL` and rendered with `as_string`. Forms: `REVOKE <right> ON <KIND> <schema.name> FROM <role or PUBLIC>;`, column rights `REVOKE <right> (<column>) ON TABLE ...`, `REVOKE GRANT OPTION FOR ...`, `REVOKE <group> FROM <member>;`, `ALTER DEFAULT PRIVILEGES FOR ROLE <r> [IN SCHEMA <s>] REVOKE <right> ON <KINDS> FROM <grantee>;`, `ALTER ROLE <r> NO<FLAG>;`, `ALTER FUNCTION <schema.name>(<identity arguments>) SECURITY INVOKER;`. For an owner problem no statement is guessed: the line says "hand it to the migration role or drop it" and counts as "by hand". A test executes every printed statement as a superuser on the test server and then asserts that `verify` returns nothing (the statements are right and complete).

### 4.3 Why there is no automatic repair

- The check before the commit already undoes everything a mistake can do. A failure after the commit therefore means code that ran at commit time on purpose, or another session; both need a person to look.
- An automatic REVOKE would be new write logic with the owner's rights, run in a state nobody understands yet, and the same actor could undo it a second later.
- "Applied" is a fact about the ledger. "Verified" is a fact about the database now. Mixing them into a new ledger state would make every later run depend on a flag a harmful file can also write.
- Decided in D-020: no automatic REVOKE, no new ledger state, no switch.

## 5. Keep, change, delete

### 5.1 Keep (no change in behaviour)

`MN` as a whole (names, ledger, released list, lexer, text rules; only the two comments of 1.5 and the duplicate rule of 6.4 touch it). In `MIG`: `Grant`, `GRANTS` (118-163), `_scan` and `check_grants` (203-257, plus 6.4), `_apply_grants` (260-280), `_released_manifest` (384-400), the read-back (`_READBACK_*`, `_Saved`, `_read_back`, `_check_read_back`, 403-592 and 1369-1468), `_trigger_changes` (507-567), `PLAIN_MIGRATION_ROLE_SQL` and `_refuse_privileged_role` (597-656), `_refuse_foreign_owned` and `_managed_names` (659-818), `_BUILT_IN_DEFAULT`, `_DEFAULT_KINDS` (1007-1015), `_shown` (1019-1023), the lock handling and limits (1257-1325 with the changes of section 6, 1492-1509), `_refuse_unusual_strings`, `_where`, `_membership_words`, `_label`, `_members_of_each_other`, `_recheck_roles` (1328-1489), the mutant runner.

### 5.2 Change

| What | Where | Change |
|---|---|---|
| `effective_problems` | MIG:283-366 | Body replaced by the subject side of `verify`. The name stays exported as a thin wrapper `effective_problems(db, role, expected_table, expected_cols=None) -> list[str]` only if a caller outside `migrate` exists on the branch (`grep -rn effective_problems src tests`); otherwise it is removed and its tests re-pointed. Main's version (main migrate.py:193-262) is the reuse base: same idea (what the role can do against the map), now all schemas, all kinds, memberships, 8 statements instead of one per role x relation x right x column. |
| Access-list queries | MIG:909-1006 | `_ACL_RELATION_SQL`, `_ACL_FUNCTION_SQL`, `_ACL_OWNER_SQL`, `_ACL_SCHEMA_SQL`, `_ACL_DEFAULT_SQL` are replaced by Q2-Q4. They lose the inputs `changed_*`, `kept_*` and `judged`; default rights are selected by grantee. |
| `_refuse_unlisted_grantees` | MIG:1098-1254 | Its loops become `_judge`; the REVOKE of everyone's EXECUTE moves to step 4; the function is removed. |
| `REVIEWED_DEFINER_FUNCTIONS` | MIG:821-824 | Key (schema, name, identity arguments), rule O4. |
| `_routine_name` | MIG:1101-1106 | Replaced by `sql.Identifier(schema, name)` plus the argument text, the form MIG:784 already uses. |
| Order of `migrate` | MIG:1579-1672 | Section 4. Lines 1607 and 1662-1663 go; 1624-1661 shrink to the three `_apply_grants` calls. |
| Catalog names | every query that stays in MIG (304-365 goes; 432-477, 609-627, 669-684, 1257-1271) | `pg_catalog.` in front of every catalog table and function, no bare `'pg_class'::regclass`. A repository test greps the SQL constants of `MIG` and the new module for a catalog name without the prefix. |
| Module docstring, `migrate` docstring, CHANGELOG | MIG:1-78, 1524-1554, CL:6-34 | Promise table first; section 1.5; section 9.3. |

### 5.3 Delete, with the written reason

Deleted: `_NOT_SYSTEM_PARTS` entries `@ME@`, `@MINE@`, `@ITEM@` and `_sql` (MIG:826-848, as far as nothing kept uses them), `_IN_SCOPE`, `_OWNER`, `_FUNCTION_FIELDS`, `_FUNCTION_STATE_SQL`, `_RELATION_FIELDS`, `_RELATION_STATE_SQL`, `_SCHEMA_FIELDS`, `_SCHEMA_STATE_SQL` (MIG:851-908), `_Objects`, `_objects`, `_Changed`, `_changed_ids`, `_kept_owner_ids`, `_changed_since` (MIG:1026-1095), `_NO_RIGHT_OUTSIDE` (MIG:1098), the calls at MIG:1607 and 1662.

Reason (rule "improve before replace": a replacement needs the written reason why the gaps cannot be fixed in place). The comparison answers "what did this run change?". Every excess right a change can produce is present in the final state, so the comparison finds nothing that the state check does not find. The gaps it has cannot be fixed inside it, because they come from the question itself:
1. It cannot see what was already there before the run (round-12 design finding 6, code finding 1 inputs A and B).
2. It must decide whose changes count, and so needs a scope ("objects of the migration role"). That scope is defined through the current user (design finding 7), needs an exception for extension members (design finding 3, code finding 2), and an exception per kind of object (design finding 4). Each exception was a route.
3. Its key is the object id, so a moved or renamed table is "unchanged" (code finding 1 input C).
4. It takes another session's change for a file's change, or misses it, depending on the scope (round-11 Majors 1 and 4).
5. It reads every function and relation of the database twice per run.
Twelve rounds patched these one by one; both round-12 reviewers proposed a thirteenth field for the state tuples. The parts of rounds 1 to 12 that are not this comparison are kept (5.1).

### 5.4 Retired tests (by name) and what replaces each

`TCMP` (16 tests): retired with the code they test:
- `test_the_field_names_match_the_rows_the_state_queries_return`
- `test_a_difference_in_any_one_field_of_an_object_in_scope_makes_it_changed`
- `test_an_object_that_is_out_of_scope_before_and_after_is_never_changed`
- `test_an_object_in_scope_only_before_or_only_after_is_compared`
- `test_the_ids_that_kept_their_owner_are_one_set_per_catalog`
- `test_nothing_found_means_no_refusal_and_the_queries_get_one_set_of_ids_per_catalog`

Rewritten against `_judge` (pure function, made-up rows; they pin the words of a line, not a decision the real-server tests do not also take): `test_the_relation_loop_refuses_each_kind_of_right_with_its_own_words`, `test_the_owner_loop_says_what_the_object_is_and_names_it_with_its_schema`, `test_the_function_loop_refuses_rights_and_security_definer_and_removes_the_default_for_everyone`, `test_the_schema_loop_lets_any_role_look_a_name_up_and_refuses_everything_else`, `test_the_default_right_loop_skips_only_the_servers_own_default_for_every_schema`, `test_a_long_list_is_cut_with_a_count_of_what_was_left_out`, `test_a_function_is_written_for_the_revoke_with_quoted_names`. Kept as they are: `test_the_ownership_check_before_the_files_gets_the_relation_names_and_the_function_names_apart`, the two lock-message tests (changed per section 6).

`TPG`, retired (they pin the comparison or a gap of it):
- `test_a_function_of_another_application_owned_by_the_migration_role_is_left_alone` (pins the gap of design finding 6; under 3.4 line 3 such a function is refused until everyone's EXECUTE is revoked)
- `test_a_function_that_kept_a_foreign_owner_is_not_refused_for_that_owner` (replaced by a test of rule O5: a group with one member passes, a group with a second member is refused)
- `test_a_schema_that_a_file_changed_and_that_kept_its_owner_is_not_taken_for_handed_over` (same)
- `test_a_function_whose_body_a_file_replaced_is_treated_as_changed`
- `test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function`
- `test_what_another_session_commits_during_the_run_does_not_stop_the_run` (replaced: another application's objects that give the named roles and everyone nothing do not stop the run; ones that do, stop it)
- `test_a_change_by_another_session_to_a_table_of_the_migration_role_is_refused_and_the_message_names_that_cause` (replaced by the after-commit test of 7.6)
- `test_a_security_definer_function_that_is_not_the_migration_roles_or_not_in_the_run_schema_is_left_alone` (replaced by a test of rule S7 in both directions)

`TPG`, kept with the same intent and re-pointed at the new message and, where it applies, the new place of refusal (the builder lists old name -> new name in the notes): `test_a_right_given_on_a_table_that_existed_before_the_run_is_refused`, `test_a_second_right_on_a_column_that_already_had_one_is_refused`, `test_a_right_given_on_a_table_of_another_schema_is_refused`, `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind`, `test_an_owner_handed_over_in_the_run_schema_is_refused`, `test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is`, `test_a_foreign_table_that_a_file_opens_to_everyone_is_refused`, `test_a_right_that_a_named_role_may_pass_on_is_refused_on_a_table_of_the_grant_map`, `test_a_named_role_that_may_pass_the_schema_right_on_is_refused`, `test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map`, `test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to`, `test_a_named_role_that_may_pass_a_function_right_on_is_refused`, `test_the_database_owner_pseudo_role_is_refused_on_a_schema_it_does_not_own`, `test_a_named_role_with_the_replication_flag_is_refused`, `test_a_security_definer_function_of_the_migration_role_that_no_file_made_is_refused`, `test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers`, `test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types`, `test_a_named_role_gets_no_right_on_a_function`, `test_a_function_that_is_called_like_a_table_of_the_grant_map_is_not_this_packages`, `test_a_named_role_that_can_read_a_foreign_table_in_the_run_schema_is_refused`, `test_the_portal_role_is_refused_what_the_other_roles_are_refused`, the three `test_with_the_printed_role_...` / `test_the_printed_role_runs_...` tests.

`TW`: `test_the_maintain_privilege_is_asked_about_from_postgresql_17_only`, `test_a_maintain_grant_is_a_problem_on_postgresql_17`, `test_the_portal_role_is_asked_about_every_table_privilege_the_other_roles_are` answer `effective_problems` by exact query text with a faked server. They are retired: `verify` reads the access lists, where MAINTAIN on 17 is one more item with no version branch (`_MAINTAIN_FROM`, `_table_privs`, MIG:283-292, are deleted). The CI run on 17 (acceptance 19) replaces the faked version. `test_migrate_refuses_a_changed_released_file_before_it_connects` only mentions `changed_rel` in a helper: re-point. The stale md5 wording at TW:192 and 208 goes with its helper.

### 5.5 Retired and re-pointed mutants (ids from `MUT` at 4d328e3d; 288 mutants in the list, 100 of them sit in code this ticket changes; produced by /home/user/build/p3a2-r13-author/mut.py)

Retired (the planted line is in deleted code and the rule it guarded no longer exists as a rule): SD3, SD4, SD5, RN6, OW3, OW4, OW7, OW8, RA1, RA1b, FB1, FB2, FB3, SO1, SO2, SO3, CS1, CS2, CS4, CS5, KC1, KC2, KC3, SC10, SC11, SD9, WD1 (27 ids).

Re-pointed (the rule lives on in `verify`; the mutant gets a new planted line in the new module and a real-server killer): AC1, AC2, AC3, AC4, AC5, SD1, SD2, SD6, SD7, SD8, DP1, DP2, DP3, DP4, DP5, DP6, DP7, DP8, DP9, SC8, SC9, SC12, SC13, SC14, GO4, GO5, GO6, RO1, RO3, RO4, RO5, RA2, RA4, IM1, RK1, RK2, RF5, OW5, OW6, OW9, MC2, PDO2, PC1, PT1, GO2 (45 ids). RA2 and RA4 change meaning from "only the schema of the run" to "only the schema of the run is read on the SUBJECT side" and must now be killed by a right in another schema.

Unchanged: the 18 in `migrate()` wiring that do not touch the comparison (M61, M64, M67, M95, MW2-MW6, N15, T13, S1, O1, R6, RC1, LV1-LV4, LW4), the lock mutants (MW8, LW1-LW3, LW5-LW8; LW7 and LW8 get the new join as planted text), and the 188 outside the changed regions. The builder's notes carry the final table id -> retired / re-pointed (new killer) / unchanged, and `problems_with_the_list()` (MUT:2997-3016) is changed to check the parametrised id of a killer as well (today it strips it).

### 5.6 What happens to each round-12 finding

Design review (r12-design-full.md):

| Finding | Result |
|---|---|
| F1 deferred trigger at commit | Usual case: stopped at step 5/6 (rows 1 and 2 of the promise table). A trigger that defers itself again (fact 4): detected at step 8 (row 3). Covered by generator carriers C6 and C6b. |
| F2 trigger on the ledger | Privilege variant: falls away by order (all runner writes come before the last check). Variant that disables the audit triggers: refused by the read-back at step 6 as a mistake; against a harmful file not promised (1.4, code left behind); "required audit triggers present" is split ticket B. |
| F3 extension member | Not reproduced as written by the evidence runner (fact 24); its precondition can exist (fact 14, author run, in conflict with the evidence runner's sentence). Falls away by construction either way (rule O6; no extension filter on family-owned objects; S7 for the named roles). Carrier C8 is the first run of this route through `migrate`. |
| F4 kinds never read | Falls away by construction (Q2 reads all 13 columns; self-check 3.6; rule S8). |
| F5 existing memberships | Falls away by construction (Q1 closure; S1, S2, S3). |
| F6 rights that existed before | Falls away by construction (state, not change; reported at step 2 before any file). |
| F7 login switches role | Falls away on the subject side (no current user in scope); `login_role` joins the family for the object side. |
| F8 (design review) temp table shadows the catalog | Fixed by item 3.1 (pinned path inside `verify`, qualified names) for all three calls; the fresh connection of step 8 is the sound one. |
| m1 function fields | Falls away (no state tuple). A SECURITY DEFINER function moved to another schema: S7 judges it where it is. |
| m2 column REFERENCES | Falls away (column lists are read as they are, every right). |
| m3 row security, views | Split ticket E. Not promised in this round; said in the CHANGELOG. |
| m4 lowest version | Fixed by 3.5. |
| m5 default kind `L` | Fixed by D4. |
| m6 reviewed list by name | Fixed by O4. |
| m7 messages | Fixed by the line shape of 3.1 (kind, schema, what to do in every line). |
| m8 false refusal | Fixed by O1 (the migration role itself is allowed). |
| m9 hand recipe, between runs | Pre-flight (step 2) and "run migrate again re-checks" cover the state at the next run; continuous checking is split ticket A. |
| m10 test wording | Fixed with the retirements of 5.4. |
| m11 docstring | Fixed by 1.5. |

Code review (r12-codebase-full.md, prefixed C):

| Finding | Result |
|---|---|
| C-F1 inputs A, B (standing rights) | Fall away by construction (S5). |
| C-F1 input C (move and recreate) | Falls away by construction (map matched by schema, name, kind; the moved table is a table outside the map on which the role holds rights). Plus item 6.4. Carrier C13. |
| C-F2 extension filter | Falls away (O6). Carrier C8, with and without role arguments. |
| C-F3 `ALTER TABLE ONLY rename OWNER TO` | Split ticket C (text-rule cleanup). Not a finding under D-020 (a way around a text rule); the false CHANGELOG sentence is deleted now (1.5, CL:18). |
| C-F4 two false "cannot" sentences | Fixed by 1.5 (MIG:747-748, CL:18; MIG:1084-1086 deleted with the code). |
| C-F5 prepared transaction | Fixed by items 6.1-6.3 (in scope of this round). |
| C-F6 raw names | Fixed by 3.1 (`_label` everywhere) and 6.2 (MIG:1314). |
| C-F7 rules without mutant | Grantor clauses and function state fields: deleted code. `l.pid IS NULL`, the `is_managed` column half: new mutants (7.7). Param ids checked: 5.5. |
| C-F8 version 13 crash | Fixed by 3.5 (and `pg_get_function_sqlbody` is gone). |
| C-F9 reviewed list by bare name | Fixed by O4. |
| C-F10 wording, `_DEFAULT_WORDS`, false refusal | Fixed by 1.5, D4, O1. "Names, not OIDs" (MIG:455): the comment is corrected to say the grantor stays an id inside the JSON. |
| C-F11 test hygiene | Fixed for surviving tests by item 6.5. |
| C-F12 reuse nits | `_routine_name`: fixed here (5.2). Three caps of 20: split ticket F. |

## 6. In-scope extras

### 6.1 The prepared-transaction message names the transaction that really holds the lock

A *prepared transaction* is a transaction that a session set aside to finish later; it keeps its locks and has no session. Today the message lists the five oldest of the database and says "finish the one that holds the lock" (MIG:1301-1312). An administrator who rolls back the wrong one loses another system's work.

New query replacing `_PREPARED_SQL` (ran on the author's cluster with `max_prepared_transactions = 10`, two prepared transactions, one holding the lock; result: only `r13-holder`; also as a plain role; fact 17):

```sql
SELECT x.gid, x.owner, x.prepared
  FROM pg_catalog.pg_locks l
  JOIN pg_catalog.pg_locks t ON t.locktype = 'transactionid' AND t.pid IS NULL AND t.granted
                            AND t.virtualtransaction = l.virtualtransaction
  JOIN pg_catalog.pg_prepared_xacts x ON x.transaction = t.transactionid
                                     AND x.database = pg_catalog.current_database()
 WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 AND l.pid IS NULL
   AND l.database = (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database())
   AND ((l.classid::bigint << 32) | l.objid::bigint) = %s
 ORDER BY x.prepared;
```
Message: exactly one row: "the prepared transaction '<gid>' (owner <owner>, prepared <time>) holds it ... A database administrator finishes THAT one (ROLLBACK PREPARED '<gid>' or COMMIT PREPARED '<gid>'); do not finish any other." More than one row (two prepared transactions can carry the same virtual id; not seen, possible by reading): all are named and the message says "one of these holds it; the server does not tell them apart for this login; ask the owners before finishing any". No row although the lock row exists: "a prepared transaction holds it, and this login cannot see which one". No `LIMIT`; `_shown` cuts the list and counts the rest.

### 6.2 An unreadable view becomes a plain configuration error

Any `psycopg.Error` raised by the two queries inside the `except LockNotAvailable` handler (MIG:1298-1325) is caught and turned into `ConfigError("migrate waited <n> seconds for the migration lock and gave up; it could not read who holds it (<server message through _label>). Nothing was changed. ...")`. `_seen(row[1])` at MIG:1314 becomes `_label(_seen(row[1]))`, and the same for the application name.

### 6.3 The real-server test runs or skips visibly

`test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one` (TPG:4499) returns early at TPG:4520 when `max_prepared_transactions` is 0, and is reported as passed. New behaviour: `pytest.skip("this server has max_prepared_transactions = 0; the prepared-transaction test did not run")` on a developer machine, and a failure when the environment variable `CI` is set (the same pattern the existing `tests/fixtures/dsn_skip.py` uses for a missing server; the builder reuses that helper). The CI service gets `max_prepared_transactions` above 0: `.github/workflows/ci.yml` lines 40-47 and 110-117 start `postgres:17.10@sha256:7958...` with default settings; the builder adds the server option in the smallest way the workflow allows (the image accepts `-c max_prepared_transactions=10` as the container command; GitHub service containers take no command, so the working form is an `options:` entry or an `ALTER SYSTEM` plus restart step: the builder tries, pastes the CI log line `max_prepared_transactions = 10`, and states which form worked). The test gains a second prepared transaction that does not hold the lock and asserts it is NOT named. The other early return, TPG:242 in `_plain_role_may_set`, is a helper and is checked by the repository test of 7.8.

### 6.4 `_scan` refuses a second CREATE of a grant-map name

In `_scan` (MIG:232-237): when `name` is already in `found`, append `f"{path.name}: {name} is created a second time (the first time in {first_file}); a table of the grant map is created once"`. Applies to every relation name the scan reads, across files and inside one file. `CREATE OR REPLACE VIEW` of the same view in a later file is the one form that may repeat (the scan knows the form). This is a text rule for accidents; it carries no security claim.

### 6.5 Test hygiene for surviving tests

Every surviving real-server test that creates a role creates it inside the `try` whose `finally` drops it (the three tests the code review names: `test_with_the_printed_role_an_owner_handed_over_is_the_one_cause_of_the_refusal`, `test_with_the_printed_role_the_schema_and_default_right_checks_hold`, and the replacement of `test_what_another_session_commits...`). The new generator uses one fixture that owns all roles, schemas, large objects and prepared transactions of a case and removes them in `finally`; a session-end check asserts that no role with the test prefix is left.

## 7. Test design (real server only for every decision; pure-function tests only pin message words)

### 7.1 The closed property

For every generated case, exactly one of these holds, and the test asserts which:
- (i) REFUSED: `migrate` raised `ConfigError` before the commit, and the oracle's answers after the run equal its answers before the run;
- (ii) NOT VERIFIED: `migrate` raised `AppliedNotVerifiedError`, and every excess the oracle finds is named in its problem lines;
- (iii) APPLIED: `migrate` returned, and the oracle finds no excess for any named role and for a fresh role that stands for everyone.

Forbidden, and the reason the suite exists: `migrate` returned and the oracle finds an excess.

### 7.2 The oracle

A separate connection as the test server's superuser. It shares no query and no helper with `src/` (a repository test asserts that the oracle module imports nothing from `hadavin_sdk.store` and contains none of the words `aclexplode`, `acl`, `has_table_privilege`, `has_` + `_privilege`, `pg_auth_members`, `pg_shdepend`, `pg_default_acl`). It reads no access list. It lists objects by name only (`pg_class`, `pg_proc`, `pg_namespace`, `pg_largeobject_metadata`, `pg_roles` for names and kinds) and then TRIES each operation:

- It becomes the role with `SET SESSION AUTHORIZATION <role>` (fact 18: `SET ROLE` from a superuser session would allow every later role switch and make the membership tests blind).
- Each attempt runs inside its own savepoint, which is rolled back whatever happens. The result is classed by the error code: 42501 = not allowed; no error, or any other code (a not-null violation, "trigger functions can only be called as triggers") = allowed.
- Attempts per relation of every non-system schema: `SELECT ... LIMIT 0`, `INSERT ... DEFAULT VALUES`, `UPDATE ... WHERE false` on the first column, `DELETE ... WHERE false`, `TRUNCATE`, `LOCK TABLE ... IN ACCESS EXCLUSIVE MODE` (owner or MAINTAIN on 17), per column `SELECT <col> ... LIMIT 0`; per sequence `nextval`, `currval` after it, `setval`; per function `EXPLAIN SELECT f(NULL, ...)` (refused without running the body, fact 19; the generator's functions are VOLATILE so nothing is evaluated while planning); per schema `CREATE TABLE <schema>.<unique>(i int)`; in the database `CREATE SCHEMA <unique>`; per large object `SELECT lo_get(<oid>)` and `lo_put`; per other role `SET ROLE <that role>`; and for each role it can switch to, the whole list again as that role (one level is enough: the generator makes no deeper chain; a deeper chain in a case fails the case as "oracle too shallow").
- "Everyone" is tested as a role created fresh by the oracle with no grant and no membership.
- Expected set per named role: built from the grant map by an independent, hand-written table in the test file (table, right) -> allowed, not from `GRANTS` through the code under test (one test asserts the hand table equals `GRANTS`, so a map change must touch both).

**Sensitivity control (mandatory, never skipped).** Each effect is also applied raw, as a superuser or as the migration role, without `migrate`; the oracle must then report exactly that excess. An effect the oracle cannot see fails the suite; it does not count as covered.

A second, coarser oracle for outcome (i): `pg_dump --schema-only` of the database and `pg_dumpall --roles-only --no-role-passwords`, text-equal before and after the refused run (the tests already shell out to the PostgreSQL client; ci.yml line 85 checks it is present). Test aid only.

### 7.3 Effects (each is "a role ends up able to do X"); grantee variants in brackets

| # | Effect | # | Effect |
|---|---|---|---|
| E01 | SELECT on a table outside the map, schema of the run [named, everyone, third role] | E20 | USAGE on a type or domain of the family [named] |
| E02 | a right beyond the map on a map table, e.g. DELETE on `runs` [named directly, everyone, through a group] | E21 | USAGE on a language [named] |
| E03 | TRUNCATE, REFERENCES or TRIGGER on a map table [everyone] | E22 | SELECT or UPDATE on a large object [everyone, named] |
| E04 | SELECT on one column of a map table [everyone] | E23 | USAGE on a foreign server or wrapper [named] |
| E05 | UPDATE on one column [third role] | E24 | CREATE on a tablespace [everyone] |
| E06 | USAGE on a sequence outside the map [named] | E25 | SET on a parameter [named] |
| E07 | UPDATE (setval) on a map sequence [everyone] | E26 | grant option on a map right [named] |
| E08 | SELECT on a view or materialized view outside the map [everyone] | E27 | a map table owned by a group that has another member |
| E09 | SELECT on a foreign table [everyone] | E28 | a named role owns a table, a function or a schema |
| E10 | EXECUTE on a function, explicit [named] | E29 | named role in a group with rights, inheriting |
| E11 | a function of the family left callable by everyone, made by dynamic SQL | E30 | the same with INHERIT FALSE, SET TRUE |
| E12 | SECURITY DEFINER function of the family in the schema of the run | E31 | named role in a built-in `pg_*` role |
| E13 | SECURITY DEFINER function of another owner in another schema, callable by everyone | E32 | named role in a role that holds a flag |
| E14 | EXECUTE on a procedure [named] | E33 | a flag on the named role itself |
| E15 | CREATE on the schema of the run [named, everyone] | E34 | default right for a named role, one schema, set by the migration role |
| E16 | USAGE on the schema WITH GRANT OPTION [named] | E35 | default right for everyone on sequences, all schemas, set by the migration role |
| E17 | CREATE on another schema [named] | E36 | default right for a named role set by another role |
| E18 | CREATE on the database [named, everyone] | E37 | any right for a third role on a map table |
| E19 | TEMPORARY on the database, explicit [named] | | |

37 effects. Expected outcome is written per effect in the test table (for example E02 "named directly" with role arguments is outcome (iii): the runner repairs it; without role arguments the role is a third role and the outcome is (i)).

### 7.4 Carriers (how the effect gets into the database)

| # | Carrier | Expected class when the effect is an excess |
|---|---|---|
| C1 | plain statement in a file (many are refused by a text rule first: still outcome (i)) | (i) |
| C2 | dynamic SQL with a split word (`'GR' || 'ANT ...'`) in a function the file calls | (i) |
| C3 | a string-bodied SQL function the file calls | (i) |
| C4 | AFTER INSERT trigger on the ledger table `schema_migrations` | (i) |
| C5 | trigger on a grant-map table, fired by a later file | (i) |
| C6 | deferred constraint trigger on the ledger | (i) |
| C6b | deferred constraint trigger that defers itself again (fact 4) | (ii) |
| C7 | a rule, and a column default, on the ledger table that call a function | (i) |
| C8 | the object is made a member of an extension the migration role owns, then the effect | (i) |
| C9 | role switch: the login differs from the role (`options=-c role=M`), the effect is done under the login | (i) |
| C10 | the object lives in another schema that the migration role owns | (i) |
| C11 | a temporary table named like a catalog table is created first, then the effect | (i) |
| C12 | the state exists before the run, there is no file (an administrator did it) | (i), with "No file ran" in the message |
| C13 | move and recreate: `ALTER TABLE <map table> SET SCHEMA other; CREATE TABLE <same name> (...)`; also a plain rename | (i) |

Every case runs twice: with the three role arguments and with none.

Cells that cannot be built with a plain migration role as the actor (the server refuses; fact 20). They are listed by name in the test file with the server's error text, built by the superuser instead under carrier C12 only, and counted separately; none is silently dropped: E09 and E23 (foreign-data wrapper), E21, E24, E25, E31, E32, E33, E36, E18 and E19 unless the migration role owns the database (one variant of the fixture does), E17 and E28-schema unless it holds CREATE on the database, C8 unless a trusted extension is available and the role holds CREATE on the database (fact 14; the evidence file states per server whether `citext` is available).

Minimum counts, asserted by a test that counts the collected ids: every buildable effect x every carrier x 2 (role arguments) is present, at least 600 cases; the 37 effects as pre-existing state x 2 = 74; 200 seeded compositions of two or three effects with different carriers (fixed seed, the seed is printed); at least 10 clean controls that must end in (iii) (the shipped files alone; another application's schema with tables that give nobody anything; a named role with a live temporary table; a group-owned database where the migration role is the only member; no pending file).

### 7.5 One mutant per clause of `verify`

New ids `V*` in `MUT`, each with a real-server killer from the generator (the id of the parametrised case is part of the killer and is checked): S1 to S8, O1 to O7, D1 to D4 (19); the map key by schema, by name, by kind (3); the row-type exception of 3.4 line 3 widened to all types (1); the system-schema rule of 3.4 line 1 (1); `repaired_by_run` set for every problem (1) and never dropped at step 6 (1); the closure follows only inheriting memberships (1); `pg_database_owner` not added (1); the temporary-object exception widened to all objects (1); the pinned path removed (killer: carrier C11) (1); the version refusal removed (1, killed by a test that runs `verify` against a faked version read: the one fake allowed, because no server below 16 is available) ; the self-check removed and each of its two directions (3); step 5 removed (killer: C6) (1); step 8 removed (killer: C6b) (1); `AppliedNotVerifiedError` raised as `ConfigError` (1); the "applied" return kept on a step-8 failure (1); the pre-flight removed (killer: C12 must say "No file ran") (1); the new lock join replaced by the old listing (killer: the bystander is named) (1); `l.pid IS NULL` removed (1); the duplicate-CREATE rule removed (1). About 44 new mutants; with 5.5 the list goes from 288 to about 305.

### 7.6 Dedicated tests outside the matrix

- After-commit: a test wraps `connect` so that, just before the step-8 connection is returned, a superuser grants `SELECT ON <map table> TO PUBLIC`. Asserts: `AppliedNotVerifiedError`, exit code 5 through `cli.main`, the first sentence word for word, no line starting "applied", the ledger holds the files, and running every printed statement as a superuser makes the next `migrate` return normally.
- Step 8 cannot connect: the wrapped `connect` raises; asserts the "could not be checked" wording and exit code 5.
- Message safety: one object name, one role name and one column name with a newline and an ESC character; asserts the printed text holds neither and that no statement is printed for them.
- Version: fact-based test that the running server is 16 or later and `verify` accepts it; the faked read below 160000 gives the 3.5 message.
- Self-check: on the running server Q0 equals `KNOWN_ACL_COLUMNS` (this is the test that fails first on a new PostgreSQL version).
- Upgrade from main: a database built by main's `migrate` (main 2a8c2aa, where the trigger function keeps everyone's EXECUTE) is accepted by the new pre-flight and repaired by step 4.
- Cost: `verify` on a database with 5,000 made-up tables of another application; the time of one call is printed and asserted under a generous bound (30 seconds), so a per-object query cannot come back unnoticed.

### 7.7 The CI test of the shipped files (promise table row 1)

One test, run in CI on every pull request: empty database, plain migration role as the printed SQL makes it, `migrate` with the three role arguments on the five shipped files; then the oracle shows, for each of the three roles and for the fresh "everyone" role, that it can do every operation the hand-written expected table lists (direction 1: nothing is missing) and is refused every other operation the oracle tries on every object of the database (direction 2: nothing extra). A second run with no pending file must give the same answers.

### 7.8 Repository check: no real-server test returns before calling `migrate`

Extend the existing `test_no_migration_test_skips_silently` (tests/test_migration_rules.py): parse TPG and the new generator file with `ast`; in every `test_*` function a bare `return` (or `return None`) that comes before the first call whose name is `migrate`, `_run_plant` or the generator's runner is a failure, unless the line carries the marker comment `# visible: pytest.skip above`. Helpers are checked for a bare `return` that follows a server-setting read (the TPG:242 pattern) by the same walk. The test must fail on the round-12 head because of TPG:4520.

### 7.9 Which tests must FAIL on the round-12 head, and the proof

Must fail on 4d328e3d (the builder checks out 4d328e3d into a scratch worktree, copies only the new test files and the oracle onto it, with a thin adapter that maps the old return and error to outcomes (i) and (iii), runs each id, and pastes the failing lines; exit code taken from pytest, never from a pipe):
- generator cases for E22 x C2 (large object), E29/E30/E31/E32 x C12 (memberships), E01 x C12 in another schema, E10 x C12 (standing EXECUTE), any effect x C6 (deferred trigger), x C8 (extension), x C9 (role switch), x C13 (move), E36 (default right set by another role): each returns "applied" with an excess the oracle sees;
- the prepared-transaction test with the bystander (the old message names it);
- the repository check of 7.8;
- the version refusal test; the self-check test (the names do not exist);
- the message-safety test for `effective_problems` lines.

Regression guards expected to PASS on the round-12 head where they can run there (exempt from the proof, listed as such): effects x C1 that a text rule refuses, the clean controls, the CI test of 7.7 direction 1.

### 7.10 Run time and batching

Not measured (nothing is built). Estimate from the existing suite: one `migrate` of the five files on a scratch schema takes well under a second on an idle machine; about 900 cases with two oracle passes each should stay under 15 minutes on one heavy slot. The builder measures the first 50 cases, writes the number in the checkpoint note, and reports if the whole matrix would exceed 20 minutes instead of cutting cells. While building: only the affected ids. On the final head, once each: the full suite (`python tools/heavy_slot.py --slots 3 --timeout 2400 -- ...` where that tool exists on the machine), the migrate mutant list (the header of `MUT` says about 10 minutes today; estimate 15 after this ticket), alone, not in parallel with the suite and never while a gate runs.

## 8. Tool ladder, single dependency, least privilege

RUNG TABLE (CODE-LAST v1):

| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| `verify` | compare who can do what with the grant map, at run time, as a plain role, on any PostgreSQL including managed ones | own core, extended: `effective_problems` on main (migrate.py:193-262) is the base | read 2026-11-11; Q0-Q4 run on 16.15 | least privilege of the shipped roles is a safety guarantee of the product | KEEP-CODE (one module, 8 statements) |
| pg_permissions (server extension with a desired-state table and a difference view) | same | ready-made tool | from memory, UNVERIFIED (not researched live for this ticket): needs a server-side install, which managed databases may not allow; said not to cover memberships | - | not at run time; an idea source only |
| pgTAP (`table_privs_are`, `is_member_of`, ...) | same | ready-made tool | from memory, UNVERIFIED: asserts named objects, not "nothing else anywhere"; needs an extension | - | test aid at most; not used |
| `pg_dump` / `pg_dumpall` text comparison | "nothing changed" after a refused run | ready-made tool, already on the test machines (ci.yml:85) | used by today's tests | - | second test oracle only (7.2); never at run time (needs a matching client binary) |
| declarative grant tools (ldap2pg, infrastructure-as-code providers), event triggers | keep rights in a declared state; log grants | client's own tool | from memory, UNVERIFIED | - | the client's choice; named in the hardening guide (split ticket D) |
| the behavioural oracle | an independent judge for the tests | new test code | fact 18, 19 | independence from the code under test | KEEP-CODE (tests only) |

Ladder line: own core module extended (reuse of `effective_problems`, `_label`, `_shown`, `_managed_names`, `_apply_grants`, the mutant runner); no no-code tool, connector or model feature applies to a catalog check inside a database transaction. No external tool is needed at run time, so no licence question arises for what ships; licences of the test aids are those of the PostgreSQL client already in use.

Single-dependency line: PostgreSQL stays behind the store kind; `psycopg` stays inside `store/`; no new library. Versions: 16.15 run here by the author and the evidence runner; CI runs `postgres:17.10@sha256:7958605b474b3d264a969cb3a123d6aa00ad1e1fe9da8a69984dabb704d93317` (.github/workflows/ci.yml lines 41 and 111 on the branch); 18 is not run by anyone and is not claimed; below 16 is refused. The self-check (3.6) is the guard for a version nobody ran.

Least-privilege lines: this ticket creates no new identity and gives no identity a new right. `verify` reads catalogs every role may read (run as a plain role, v1.out) and writes nothing. The migration role, runtime role, portal role and purge role keep their rights: migration role = owner of the package's objects, no flag, no built-in role; runtime, portal, purge = exactly the grant map plus USAGE on the schema; the per-right reasons are the comments of `GRANTS` (MIG:135-163), unchanged. Negative test: 7.7 direction 2. Over-breadth review: the result review of this round. The separate checking identity (connect-only, reads catalogs, no right on any table) is split ticket A and is not built here.

## 9. Acceptance, gates, branch, CHANGELOG

### 9.1 Acceptance checklist (each item is checked by an evidence runner with the command; "paste" means raw output in the evidence file)

1. `git -C <repo> merge-base --is-ancestor 4d328e3d HEAD; echo $?` prints 0; `git log --oneline 4d328e3d..HEAD` shows the commit split of 9.3.
2. `grep -n "_changed_since\|_Objects\|_objects(\|_Changed\|_kept_owner_ids\|_changed_ids\|_STATE_SQL\|@MINE@\|@ME@" -r src tests` prints nothing.
3. `grep -n "current_user\|session_user\|current_schema" src/hadavin_sdk/store/migration_verify.py` prints nothing.
4. The repository test "every catalog name is qualified" passes, and fails when one `pg_catalog.` is removed from Q2 (mutant).
5. `grep -c "has_table_privilege\|has_column_privilege\|has_sequence_privilege" src/hadavin_sdk/store/migrate.py src/hadavin_sdk/store/migration_verify.py` prints 0 for both.
6. The promise table of 1.3 is the first thing after the title line in the `MIG` docstring and in the CHANGELOG item; a test compares the two texts with each other.
7. The grep of 1.5 is pasted with one line of reason per remaining hit.
8. Generator: the count test passes; the collected numbers (cases, pre-existing, compositions, controls, not-buildable cells with their server errors) are pasted.
9. Sensitivity control: for every effect the raw application is reported by the oracle (paste the per-effect table).
10. No case ends "applied with excess" (paste the summary line by outcome class).
11. 7.9: each must-fail id pasted failing on 4d328e3d and passing on the head, with pytest's own exit codes.
12. Mutants: `uv run python tests/migrate_mutants.py` on the final head ends with `N of N killed`; the table retired / re-pointed / new is in the builder notes; every `V*` mutant has a real-server killer.
13. After-commit tests of 7.6 pass; the pasted message starts with the exact first sentence of 4.2; exit code 5 shown through `hadavin-sdk migrate`.
14. Every printed fix statement runs as a superuser and the next `verify` returns nothing (7.6, paste).
15. Prepared transaction: evidence states `SHOW max_prepared_transactions` of the server used (above 0), the test ran (not skipped), the bystander is not named.
16. `ConfigError` for an unreadable lock view (6.2): test pasted.
17. Duplicate CREATE (6.4): test pasted; `check_grants` on the shipped files still returns no problem.
18. 7.8 repository check passes on the head and is shown failing on 4d328e3d.
19. CI on PostgreSQL 17.10 is green for the whole suite, including 7.7 and the self-check; the CI log line with the server version is pasted. A local 16.15 run of the same is pasted.
20. Version refusal and self-check messages pasted.
21. Cost test of 7.6 pasted with the measured time.
22. Upgrade-from-main test of 7.6 pasted.
23. Gates, each with its own exit code (never through a pipe), on the final head with no cloud configuration in the environment:
    `uv run --all-extras --group test ruff check`; `uv run --all-extras --group test ruff format --check`; `uv run --all-extras --group test pytest > log 2>&1; rc=$?; tail -n 1 log; echo $rc`; `bandit -ll -r src`; the repository guard tests (`scan_repo` and `stage_mutants` as `.github/workflows/ci.yml` on the branch runs them: the builder copies the two command lines from the workflow into the evidence); the migrate mutant list (item 12) and `tests/migration_numbers_mutants.py`; `gitleaks` as the workflow runs it. CodeQL, SonarCloud and CodeRabbit green on the pull request; threads resolved after fixing; no suppression, no weakened or deleted test outside the lists of 5.4.

### 9.2 Stop rule

Security path: result-review rounds repeat until a fresh round finds no Blocker and no Major. Classing rule for every finding from now on (D-020): it is either a bug in a numbered clause of section 3.3 or 3.4 (fix it and add the generator cell), or it is inside a stated non-promise of 1.3/1.4 (no fix; check that the text says so), or it is a way around a text rule (not a finding).

### 9.3 Commits and CHANGELOG

Commit split, in this order, each one leaving ruff and the affected tests green:
1. Deletion: the comparison code, its tests (5.4 "retired") and mutants (5.5 "retired"). The suite is green with the old final check reduced to the kept loops.
2. `verify`: the new module, `_judge` unit tests, version refusal, self-check.
3. Order: section 4, `AppliedNotVerifiedError`, cli exit code 5, removal of `effective_problems` and `_refuse_unlisted_grantees`.
4. Extras: section 6 (lock message, unreadable view, duplicate CREATE, CI server setting).
5. Tests: oracle, generator, dedicated tests, repository checks, re-pointed and new mutants.
6. Texts: docstrings, CHANGELOG.

Commit messages end with the attribution lines the session reminder gives. Draft pull request stays the existing one for `core/P3a-2-clean` if there is one; otherwise the lead opens it.

CHANGELOG ("Unreleased", "Upgrade steps", replacing CL:15, 17, 18 and correcting CL:12 and 34):
- First the promise table of 1.3 under the heading "What migrate promises", then 1.4 as "What it cannot notice".
- The baseline of 3.4 in its four lines.
- The three calls and the exit codes (2 refused and nothing kept; 5 applied and committed but not verified).
- Upgrade note, in these words or plainer: "A setup with rights beyond the grant map is now refused before any file runs. Earlier versions only refused rights that changed during the run, so a database that passed before can be refused now. `migrate` prints one line per right with the statement that removes it. A database administrator runs those statements (they are REVOKE statements and membership removals; none of them changes data), then runs `migrate` again. Typical cases: a table of another application that everyone may read; a login used as runtime role that is also a member of a group; a function in the same schema, owned by the migration role, that everyone may call; a default right set long ago with `ALTER DEFAULT PRIVILEGES`. Two things `migrate` repairs by itself and does not refuse: rights of the named roles on the package's own tables (they are reset to the grant map as before), and the right of everyone to call the package's own functions (removed as before). If the listed object belongs to another application that needs the right as it is, do not remove it: give this package a database or a schema of its own, with roles that are not shared."
- The minimum version, and that PostgreSQL 18 has not been run.
- No sentence may say more than the promise table; reviewers check the CHANGELOG against 1.3 line by line.

## 10. Not to build, split tickets, open questions, what was not verified

### 10.1 Not to build (D-020)

More text rules or spellings; a SQL parser used for security; detectors per route (for example refusing a deferrable trigger by reading its flags); before-and-after snapshots of the catalog, and no further field on the old state tuples; automatic REVOKE or any other repair; a new ledger column or an "applied but not verified" state in the ledger; any switch, argument, environment variable or per-deployment exception list that relaxes `verify`; anything that needs a superuser from the runner (event triggers, extension installs); a run-time dependency on `pg_dump`, pg_permissions, pgTAP or any external tool; support below PostgreSQL 16; checks of other databases of the same server; a path for client-written files through this role; a sandbox for files.

### 10.2 Split tickets (one line each; the lead files them in the ledger)

- A. A read-only `verify` command for a separate checking login that may only connect, plus a scheduled re-check: the real control against a harmful file and against drift between runs.
- B. "The required audit triggers are present and enabled" as a state check in the audit package.
- C. Text-rule cleanup: remove the reason "the read-back does not look there" from `_GRANT_TARGET`, decide on the `_RENAME_OWNER` exemption (the `ALTER TABLE ONLY rename OWNER TO` case), merge duplicates.
- D. Client hardening guide: a migration role that does not own the database, a database of its own per application, an event trigger that logs grants, login rules.
- E. Row-level security, policies and view options as part of the judged state, when the first one enters the grant map.
- F. Surviving minors: one constant for the three caps of 20, message polish not covered here.
- G. The prepared-transaction message: pulled INTO this round as item 6.1-6.3 (operator safety); listed here only so the ledger shows where it went.

### 10.3 Open questions, with the safe default this ticket takes

1. AUTHOR ADDITION, baseline line 1: a grant on a system object that names a subject role is judged. D-020 says system objects are not judged. Default taken: judged (stricter; fact 21 shows no false refusal on a fresh server). The lead may strike it.
2. CORRECTION, baseline line 3: row types of tables are left out of "everyone gets nothing on family objects". Without this every database is refused (fact 11). No alternative offered.
3. AUTHOR ADDITION, rule O5 (other members of a group that owns a package object). Default taken: refused. Alternative: accept any family owner as today and state it as a limit; weaker.
4. AUTHOR ADDITION, the pre-flight ignores exactly the two things the run repairs itself (4.1 step 2). Without it every upgrade from main is refused before any file (main never removed everyone's EXECUTE from the trigger function). Alternative: no exception and a hand step for every upgrade; safe but a worse upgrade.
5. A function or type of another application that the migration role owns in the schema of the run and that everyone may use is refused at the pre-flight (3.4 line 3), where round 12 left it alone. Default taken: refused, with the REVOKE printed. Owner question: is sharing the schema and the owner with another application a supported setup at all? (D-020: the package does not require a schema of its own.)
6. TEMPORARY for everyone on the database: stated baseline, not judged (D-020). An explicit TEMPORARY grant naming a subject role: refused (default taken here).
7. A migration role that owns the database or holds CREATE on it: allowed (D-020), named in the hardening guide. Fact 14 shows what it enables; `verify` judges the result.
8. Exit code 5 and a new error class outside `ConfigError`: default taken. Alternative: a subclass of `ConfigError` with exit 2; rejected because exit 2 means "refused, nothing happened" in this command line.
9. `effective_problems` as a public name: removed unless a caller outside `migrate` exists on the branch (the builder greps and states the result).
10. Whether the CI service container can be started with `max_prepared_transactions` above 0 without a custom image was not tried (6.3). Safe default: the test FAILS in CI when the setting is 0, so a vacuous pass is impossible either way.

### 10.4 What I did not verify

- Anything on PostgreSQL 17 or 18 (fact 25 is from memory).
- The cost of Q2 and Q3 on a large catalog.
- That `psycopg`'s `connect(..., options=...)` passes through the wrapper `store/postgres.connect` unchanged (its `**extra` at postgres.py:146 was read in a 28-line window only).
- That `REVOKE ALL ON ROUTINE` and the printed fix statements are right for every kind (aggregates with `*`, procedures): section 7.6 tests it; nothing here ran it.
- The behaviour of Q3 for objects of kinds I did not create (operators, collations, text-search objects, publications, event triggers): rule S4 reads them through `pg_shdepend` whatever the kind, by fact 12 for the kinds seen.
- Whether two prepared transactions can really share one virtual transaction id (6.1 handles it either way).
- Who is right about the owner of a trusted extension installed by a plain role ("Read first" item 5): my run says the installing role; the evidence runner's report says the superuser. I did not see the evidence runner's raw output for it.
- The difference between 280 mutants (evidence runner) and 288 entries in the list object (my import).
- The plain-role refusal text for `session_preload_libraries` (fact 13, second half).
- The descriptions of external tools in section 8.
- The line numbers of `ci.yml` beyond the grep output (lines 37-47, 85, 110-117 were seen), and how the workflow calls `scan_repo`, `stage_mutants` and gitleaks (acceptance 23 makes the builder copy the commands).
- TICKET-P3a.md and BUILDER-ticket-notes.md were not read; if they fix a format or a promise that this ticket contradicts, the plan reviewers will see it before I do.
- No test, lint or mutant of the repository was run by the author.

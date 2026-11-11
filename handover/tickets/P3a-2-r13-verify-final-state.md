# Ticket P3a-2 round 13 (rev 3, the LAST plan round; after it the lead freezes the plan with errata and one builder starts): judge the final state of the database with one check called `verify`, and say honestly what it can and cannot promise

## Rev 3 status, written 2026-11-11 16:59-17:5x UTC (22:29-23:2x IST) by the ticket author

### What rev 3 still does not settle (read this first)

1. Nothing in this ticket ran on PostgreSQL 17 or 18. Every probe of rev 1, rev 2 and rev 3 ran on 16.15. The first run on 17.10 is the CI run of the built branch (acceptance 19).
2. The test oracle as a whole has still not been built or run. Rev 3 probed every attempt the round-2 reviews doubted (facts 41-47), and changed the attempt table to what the probes show, but the attempts for TRIGGER on a view, INSERT/UPDATE/DELETE on a partitioned table and on a partition, `CALL` of a procedure, a large object, a foreign server or wrapper, a tablespace and a parameter were not re-probed in rev 3. The sensitivity control (7.2) stays the guard that finds a wrong attempt at build time, in commit 2.
3. Five owner decisions are open (questions-for-lead.md, block "P3a-2 rev 3"). This ticket takes the stricter default for each and builds that; a different answer changes the named rules and tests only (10.3).
4. The rung-table rows for pg_permissions, pgTAP and ldap2pg were NOT researched live. Rev 3 rewrites them as "not evaluated" and rests KEEP-CODE on the stated constraints only (section 8). Nothing in the build order depends on them.
5. Time estimates for the builder sessions, the mutant batches and the matrix are still guesses; the first builder measures them (9.4).
6. The mutant re-check list of 5.5 is computed by a script from planned line ranges (fact 50). A builder edit outside those ranges is caught by the per-commit rule of 5.5, not by the list.
7. The rev 3 author ran PostgreSQL and psycopg probes and one script over the mutant lists of the 4d328e3d tree. No test, lint or mutant of the repository was run.

### Changes since rev 2 (every round-2 finding and the section that answers it)

Inputs: plan review round 2, design (handover/reviews/P3a-2/plan-r2-design-full.md, ids F1-F12 and Nit) and implementation readiness (plan-r2-readiness-full.md, ids M1-M8 and m1-m14, n1-n3). Rev 3 probes: handover/evidence/P3a-2/plan-r3/ (scripts in scripts/, outputs p3.out, p3b.out, p3c.out, affected_mutants.out, affected_vs_rev2_lists.out), facts 41-50 below.

| id | answer (decision, definition, number or test) | section |
|---|---|---|
| F1 oracle attempts | Probed: a temporary referencing table gives 42P16 before any rights check (fact 41), so E03-REFERENCES uses a permanent table the oracle makes in its scratch schema; E19-E21 attempts no longer need TEMPORARY (fact 42; `SELECT NULL::type` does NOT test USAGE, so the reviewer's suggested attempt is not used); INSERT/UPDATE/DELETE/TRUNCATE/REINDEX are chosen per relation kind from the measured codes (facts 43, 44); every object attempt gets USAGE on the object's schema as scaffolding inside the savepoint, and schema USAGE has its own attempt (fact 45) | 7.2 |
| F2 not green per commit | Every test has a commit (table "test -> commit"); the AST, rights-table, rewritten-TCMP, promise-table and problem-kind tests move to the commit that makes them true | 9.3 |
| F3 commit 3 too big | Split into 3a, 3b, 3c, each green; one side-branch squash rule for a step that spans sessions | 9.3, 9.4 |
| F4 rung rows from memory | Rows rewritten as "not evaluated"; KEEP-CODE rests on the stated constraints only | 8 |
| F5 COMMIT classification | Exit 2 only for an allowlist of SQLSTATEs on an open connection whose status is IDLE; everything else exit 5. Probed: `pg_terminate_backend` at COMMIT gives 57P01, connection closed, status UNKNOWN (fact 46) | 4.1 step 7 |
| F6 refusals dropped on purpose | Column "refusal dropped on purpose; lead signs off" in 5.4 | 5.4 |
| F7 limits first, PG17 `transaction_timeout` | `pinned_read` sets the limits first; measured: both orders 100 of 100 (fact 47), so this is defence, not a measured fix; `transaction_timeout` (17 and later) is NOT neutralised (no version branch, not runnable here): a saved role value can stop the check, which then ends in exit 5 "could not run", never in "applied"; the claim in 3.1 and the CHANGELOG is narrowed to the two limits that are set | 3.1, 9.5 |
| F8 6.4 is a text rule | Moved to split ticket C; its mutant and test leave this ticket (count 313) | 6.4, 10.2 |
| F9 `pg_database_owner`; grant option from two grantors | No statement removes `pg_database_owner` (probed, fact 48): by-hand line "hand the database to another role". Grant option: `SET ROLE <grantor>; REVOKE GRANT OPTION FOR ... CASCADE; RESET ROLE;` per grantor (probed, fact 49) | 3.3 S2, 4.2 |
| F10 cluster-wide leftovers | Session-start and session-end guard over tablespaces, parameter rights and roles with the test prefix; a leftover fails the session with the clean-up statements | 7.2 |
| F11 printed REVOKE on another application's object | Each such line and statement is marked "NOT THIS PACKAGE'S OBJECT"; statements go to a second block that the message tells the administrator not to run blindly | 4.2 |
| F12 extension-owned objects | Probed with `pg_stat_statements`: 2 views readable by everyone; `ALTER EXTENSION ... UPDATE` re-grants after a REVOKE (fact 50). Default taken: refused (D-020, no exception list), with an extension mark and no statement printed; OWNER QUESTION | 3.3 E1, 10.3 item 13 |
| Design Nit and wording | Glossary added | Glossary |
| M1 test -> commit | Table in 9.3 for every test of 7.6, 7.7, 7.8, 5.4 and 5.4b; `MIGRATION_TEST_FILES` in commit 1 for the two files that exist then, commit 2 for the matrix file; `problems_with_the_list()` change in commit 5 | 9.3 |
| M2 runnable commands | "How to run here" block: initdb, start, DSN form, `uv` offline check, heavy.sh form, time bounds; `DSN=...` replaced by `HADAVIN_TEST_PG_DSN=...` | 9.0, 9.1 |
| M3 commit 3, red WIP, B2 after C1, "parallel" | 3a/3b/3c; side-branch squash rule; B2 depends on C1; "parallel" defined (two worktrees, disjoint files, cherry-pick of an unpushed commit by the lead) | 9.3, 9.4 |
| M4 heavy.sh | Every heavy command is `/home/user/build/heavy.sh timeout <s> <argv>` here, `python tools/heavy_slot.py ...` on the studio machine; bounds given | 7.10, 9.0 |
| M5 interfaces | `_read` returns a `Rows` record of named tuples; `_judge` signature; `Problem` gains `owner`, `grantor_is_owner`, `outside_package`, `extension`, `order`; `Problem.line()` for all 21 kinds (the review counted 25; the rev 2 table lists 21); S5 for a group reached by two named roles; statement builder `statements_for(problems)`; exit-2 cap stated; `KNOWN_ACL_COLUMNS` value format; `RUN_SCHEMA` handled in `migrate`, not in `verify` | 3.1a, 3.3, 3.6, 4.2 |
| M6 matrix cells, C10 | Attempt per effect per relation kind; scaffolds; C10 cells E10, E11, E20, E21 decided (named roles: (i); everyone on family functions and types in another schema: "not promised"); the three tables filled as far as the probes allow; clean controls numbered to 12 | 7.2, 7.4 |
| M7 mutant lists not closed | Computed list (fact 50): 106 mutants overlap a planned edit; 30 of them were in no rev 2 list (28 named only as "unchanged", plus M102 and P8); the 10 CHANGELOG-planted ids outside the rewritten lines are re-checked at commit 6. The `pg_catalog.` prefix edit of kept MIG queries is DROPPED (they all run inside `pinned_read`), so no mutant moves for it. Batch-2 ids live in a constant `BATCH_2_IDS` in `tests/migrate_mutants.py` from commit 3a | 5.5, 3.1 |
| M8 Q0/version unbacked; qualified-names rule | Q0 and the version read run (fact 48 output G1, G2); the version read now also returns the database owner (m1, probed, p3c.out); the qualification rule is defined for relation names in the new module only (functions and types are not looked up in `pg_temp`) | 3.1, 3.2, 3.5 |
| m1 | Database owner read by the version statement (V2); probed: with everyone's database rights revoked Q2 returns no database row | 3.2, 3.5 |
| m2 | Review ids in the body are kept as history only; the glossary and the rules carry the meaning | Glossary |
| m3 | Line citations unconfirmable by reviewers: the builder confirms each with `git show 4d328e3d:<file> | sed -n` in the builder notes | 9.3 |
| m4 | Promise-table comparison strips leading whitespace of each line and blank lines | 9.1 item 6 |
| m5 | Item 2b: no comment or docstring in `migrate.py` may contain `current_schema()` other than the one read | 9.1 item 2b |
| m6 | `from __future__ import annotations` plus `if TYPE_CHECKING: from hadavin_sdk.store.migrate import Grant` | 3.1 |
| m7 | The fake `_Db` gets a `transaction()` context manager that records "SAVEPOINT"/"ROLLBACK TO" lines (commit 3b) | 9.3 |
| m8 | The one-database-per-case fixture builds its own login DSN by replacing `dbname` in the result of `login_dsn` with `psycopg.conninfo.make_conninfo` | 7.2 |
| m9 | Statement-timeout test uses the measured setting: 1 ms (fact 47), sensitivity first | 7.6 |
| m10 | Probed: the lost-connection path gives `AdminShutdown` 57P01, closed, UNKNOWN (fact 46); the test asserts exit 5 and that the classifier saw 57P01 | 7.6 |
| m11 | `problems_with_the_list()` change in commit 5 | 9.3 |
| m12 | The exit-code line goes after the `migrate` usage line (cli.py:9-10) | 4.2 |
| m13, m14 | Kept as written (both reviewers agreed); 7.9 now says the matrix file imports `verify` only inside functions | 6.3, 7.9 |
| n1 | "applied" means "in the ledger and committed"; "committed" is used only for the COMMIT statement | Glossary |

### Glossary (10 lines)

- **family** (migration role family): the migration role, the login when it differs, and every role either of them is a member of.
- **named role**: one of the three roles given on the command line (runtime, portal, purge). **subject**: a named role or any role it is a member of, directly or through others.
- **everyone**: PostgreSQL's PUBLIC, the rights every role has.
- **excess**: a right a named role or everyone holds that the grant map and the baseline (3.4) do not give.
- **effect** (E01-E39): one kind of excess a test builds, for example "SELECT for everyone on a table outside the map".
- **carrier** (C1-C13): the way a test brings the effect into the database, for example "dynamic SQL in a function the file calls".
- **cell**: one effect brought by one carrier, run with and without the role arguments.
- **outcome (i), (ii), (iii)**: refused and nothing kept; applied but reported as not verified (exit 5); applied and clean (7.1).
- **hidden COMMIT**: a migration file that ends the transaction itself, so what came before it is kept even if the run is refused later.
- **oracle**: test code that finds out what a role can do by trying it as that role, never by reading access lists.

## Changes in rev 2 (errata to rev 1, written 2026-11-11 16:24-16:53 UTC, 21:54-22:23 IST)

Inputs: plan review round 1, implementation readiness (handover/reviews/P3a-2/plan-r1-readiness-full.md, prefix R: B1, B2, M1-M9, Mn1-Mn11, citation list A) and design (plan-r1-design-full.md, prefix D: M1-M8, m1-m12). New probes on PostgreSQL 16.15: handover/evidence/P3a-2/plan-r2/ (README.md there lists them). The sections below are rewritten in place; this list says where. Every finding is answered in the table of section 11.

1. Commit order rebuilt so every commit is green (9.3), with the work split into packages of at most 60 minutes of builder time (9.4). R-B1, R-M5.
2. Everyone may hold USAGE on the schema of the run; rules O2 and O7 say so; a test runs `migrate` in a `public` schema with the server's own access list (3.3, 7.6). R-B2.
3. Step 8 sends no extra connection option; every failure in step 8 becomes "applied, not verified" (exit 5); step 8 has its own time limits; a COMMIT whose outcome is unknown also ends in exit 5 (4.1, 4.2). R-M1, D-M2, D-M3, D-M8.
4. The test oracle: superuser login required (a failure, not a skip), one database per case, a table "effect -> attempt that shows it" for all 37 effects, a whole-word ban list (7.2). R-M2, D-M1.
5. Named lists of every test and mutant this ticket touches beyond rev 1's lists, with the mutant count corrected to 288 = 279 + 9 (5.4, 5.5). R-M3, R-A, Mn10.
6. A test id for every acceptance item (9.1). R-M4.
7. Mutant runs in four batches (7.10). R-M5.
8. Module layout decided: no import from `migrate` into the new module; `_label` moves to `migration_numbers`; the reviewed list is passed at call time (3.1). R-M6.
9. Full query texts, the step-4 query, the schema-USAGE rule, `PROBLEM_KINDS` and the rights per role kind are in the ticket (3.2, 3.3). R-M7.
10. Old-head proof must fail on the assertion, not on an import (7.9). R-M8. Upgrade test emulates main's state and claims no more (7.6). R-M9.
11. Object side stays limited to the schema of the run, now stated as an AUTHOR ADDITION that narrows D-020 (3.3, 10.3). D-M6.
12. Rule O5 struck (3.3, 1.4). D-M7.
13. A right that reaches a named role only through a built-in `pg_*` role is one membership line; no statement is ever printed against a system schema (3.3, 4.2). D-M4.
14. `Problem` carries the grantor; printed statements use the form the probes show works (`SET ROLE <grantor>` for object rights, `GRANTED BY` for memberships); step 2 drops only what step 4 really removes (3.1, 4.1, 4.2). D-M5, D-m5.
15. All Minors of both reviews (section 11).
16. Two gaps found by the rev 2 author while answering the reviews: rule O8 (a package object in the schema of the run handed to a third role, which rev 1 had stopped refusing) and the `current_schema()` reads that a pinned path would break (3.1, 3.3, section 11).
17. Rev 1's open conflict about the owner of a trusted extension is settled by a run ("Read first" item 5).

Not changed in rev 2: the promise table's three rows and words (1.3), the decision to delete the before-and-after comparison (5.3), the split tickets (10.2), the stop rule (9.2).

Source: decision D-020 (handover/AUTONOMOUS-DECISIONS.md), which amends D-019 and replaces the scope sentence of D-009; the design review with addendum (handover/reviews/P3a-2/r13-design-zoomout-full.md); the two round-12 reviews (r12-design-full.md, r12-codebase-full.md); evidence in handover/evidence/P3a-2/4d328e3/ (route-probes.txt, design-probes*.txt, run by a separate EVIDENCE RUNNER); the ticket author's own probes in /home/user/build/p3a2-r13-author/ (p1..p6.sql and .out, v1.sql and v1.out, mut.py, tst.py).
Branch: continue `core/P3a-2-clean` from 4d328e3d, fast-forward only (no rebase, no force push). `core/P3a-2` and `core/P3a-2-rewritten` stay untouched. The builder never merges.
Path class: security (rights and least privilege). No round cap on result reviews.
Code references: `MIG` = src/hadavin_sdk/store/migrate.py, `MN` = src/hadavin_sdk/store/migration_numbers.py, `CL` = CHANGELOG.md, `TPG` = tests/test_migration_postgres.py, `TCMP` = tests/test_migration_compare.py, `TW` = tests/test_migration_wiring.py, `MUT` = tests/migrate_mutants.py. All line numbers are for the snapshot /home/user/build/snap/p3a2-r12-4d328e3/ (head 4d328e3d).
Status: written by ticket authors (rev 1 and rev 2). Nothing is built. Fresh plan reviewers judge this ticket before any build. Times: rev 1 written 2026-11-11 about 16:00 to 16:40 UTC (21:30 to 22:10 IST); rev 2 16:24 to 16:53 UTC (21:54 to 22:23 IST).

## Read first: what is not established

1. Every PostgreSQL fact below was run on PostgreSQL 16.15 only. Versions 17 (the version CI uses) and 18 were not run by anyone. The design has one built-in guard for that (the self-check in section 3.6), and the acceptance list makes the CI run on 17 a required evidence item.
2. The SQL in section 3 ran on the author's throwaway cluster against a small made-up setup (5 tables, 4 functions, 6 roles). It was not run on a large catalog. Its cost on a database with tens of thousands of objects is not measured (acceptance item 21 measures it). Rev 2's final texts ran on a slightly larger setup (fact 40), still small.
3. Three things in this ticket go beyond the words of D-020 or correct the design review. They are marked AUTHOR ADDITION or CORRECTION where they appear and are collected in section 10.3 so the lead can accept or strike each one.
4. Facts taken from memory and not run by anyone are marked "from memory, unverified" in section 2. None of them carries the design alone.
5. SETTLED in rev 2 (was an open conflict between two runs). A plain role with CREATE on the database that installs the trusted extension `citext` OWNS the extension (`citext | xmig`, run with `current_user = session_user = xmig`, `rolsuper = f`), and the 47 functions inside it are owned by `postgres` (handover/evidence/P3a-2/plan-r2/x-extension-owner.out). Rev 1's run was right; the evidence runner's sentence in RESULTS.md Step 9 row F3 ("is owned by `postgres`", no raw output) is wrong for the extension and right only for its member functions. The design never depended on it: rule O6 has no condition (section 3.3).
5b. The evidence runner's RESULTS.md (sections "Step 5", "Step 6", "Step 9", "Addendum 2"), route-probes.txt, design-probes*.txt and the table of probe 6c were read and are used. The round-12 design finding 6 (rights that already existed before the run) has no row of its own in Step 9; two rows of probe 6c show the same class (facts 27 and 28).
5c. The mutant list has 288 entries with 288 different names at 4d328e3d: 279 written as `Mutant(...)` in the list plus 9 made by the helper `cmp_mutant` (rev 2 author run, mutclass.out; `grep -c "^    Mutant("` = 279, 9 calls of `cmp_mutant(`). The 280 in RESULTS.md is a miscount. Settled.
5d. Rev 2 probes (handover/evidence/P3a-2/plan-r2/) are facts 30 to 40 in section 2. They confirm every PostgreSQL claim of the two plan reviews that was checked, with one correction: `GRANTED BY` works for memberships only; for object rights PostgreSQL answers "grantor must be current user" (fact 30).
6. Not read by the author: the lexer body of `MN` (only lines 28-40 and 655-740), most test bodies (names, helpers and the lines cited in the reviews were read), DIFF-main-to-head.patch, TICKET-P3a.md, BUILDER-ticket-notes.md, cli.py beyond `_migrate` and the exit-code lines.

## 1. What this is about, in plain words

### 1.1 The problem

The package keeps its data in a PostgreSQL database. A small program called `migrate` sets that database up: it runs our SQL files (the "migration files") in order, and then gives three application logins exactly the rights they need. In PostgreSQL such a login or group is called a *role*. The three are the *runtime role* (the running application), the *portal role* (the read-only web portal) and the *purge role* (deletes old evidence). What each of them may do on each table is written down in one list in the code, the *grant map*. `migrate` itself connects as a fourth role, the *migration role*, which owns the tables.

After the files ran, `migrate` must make sure that the three roles can do what the grant map says and nothing more. Twelve rounds of work tried to do that by comparing the database before and after the files ("what changed during this run?"). Each round a fresh reviewer found another way to slip a right past that comparison: code that runs at the very end, kinds of object the comparison never read, rights that were already there before the run, and so on.

### 1.2 The decision

We stop asking "what changed?" and ask "what is true now?". One check, called `verify`, reads who can do what in the database and compares it with the grant map. It runs three times: before the first file, as the last thing before the changes are made permanent, and once more afterwards on a new connection. The before-and-after comparison is deleted.

We also stop promising what no check of this kind can deliver. A migration file runs as the owner of every table. Nothing that runs as that same owner can stop the owner from doing what an owner may do. So the promise is split by who wrote the file.

### 1.3 The promise table (decided in D-020; this exact table goes first in the module text and in the CHANGELOG)

"Stopped" means: the run is refused and everything it did is undone, unless a file ended the transaction itself (a hidden COMMIT); that case is reported separately with its own message, as today. "Detected" means: the run reports it loudly, but the change is already in the database and a person must act. "Lasting right" means a right that is still there when the check looks.

| Who wrote the file | What `migrate` does | Word |
|---|---|---|
| 1. We did, and made an honest mistake | When the file leaves a named role, or everyone, with a right outside the grant map, the run is refused and undone. The same mistake is caught before release, because the build server runs the shipped files on an empty database and tests what each role can really do. | STOPPED |
| 2. Someone careless, or a file copied from elsewhere | The same, for lasting rights only. Nothing is promised about lost data, and nothing about code the file leaves behind to run later. | STOPPED, for lasting rights only |
| 3. Someone who wants to do harm | NOT stopped. Lasting excess rights that exist when the check after the commit runs are reported, with the statements that remove them. Such a file can also cheat the check after the commit, or make it fail to run; a check that cannot run ends in the same loud "applied, not verified" result, never in "applied". | DETECTED, not stopped |

Why row 3 cannot be better: the file runs as the owner of every table. The real protections against a harmful file are elsewhere: a person reviews every file, each released file's fingerprint is recorded and checked (both exist today), and a separate read-only login that only checks (a new ticket, see 10.2 A).

### 1.4 What can never be noticed from inside the migration role, in any number of rounds

- A change that a file makes and takes back before it ends.
- A file that reads data or changes data.
- Code a file leaves behind (in a trigger, a rule, a column default, a view or a function) that runs later, as whoever touches the table next. That can be an administrator.
- A right that someone gives again one second after the check.
- Anything a file does outside its transaction (for example through a second connection).
- What the server reports when the reader itself is the one being cheated: the check after the commit still connects as the migration role. Only a separate checking login closes that (10.2 A).
- Who else can act as owner: when the package's tables are owned by a group role, every other member of that group can act as their owner. `migrate` does not judge the members of an owning group (rev 1's rule O5 is struck; section 3.3).
- A table in the schema of the run that is not one of the package's tables and that a file hands to a third role: once handed over it is no longer the family's, and only the named roles' and everyone's rights on it are judged (rev 3; the package's own tables and functions, and the schema itself, are covered by rule O8).
- Rights for a role that is neither a named role nor everyone, on an object the migration role owns OUTSIDE the schema of the run (the object side reads only the schema of the run; section 3.3, AUTHOR ADDITION 10.3 item 11).
- A grant made by another session between the last check before the commit and the check after it: the check after the commit reports it like any other excess ("this run, or another session since the commit").

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
| MN:677-679 (comment above `_GRANT_TARGET`, which starts at MN:680; rev 1 said 680-683) | "is refused: the read-back after the file does not look at those places" | Replace: "is refused early, as a plain message for an accident. This rule carries no security claim: `verify` judges the result whatever the text says" |
| MN:722-723 (`refused_statements`) | "A quick check that catches accidents, not a sandbox: the read-back after each file is the guard." | Replace the last clause: "... not a sandbox, and not the guard: `verify` judges the final state. A way around a text rule is not a defect of this module." |
| CL:11 (rev 1 said CL:12, which is the "powerful flags" bullet) | "`migrate` refuses to run when that role could reach beyond this package's own objects, or could not change them" | Replace: "`migrate` refuses to run when that role holds one of the powers listed below, or could not change this package's objects". (No sandbox claim.) |
| CL:15 | "the old default of the `public` schema on PostgreSQL 14 and earlier; fix with ..." and "Not looked at by this check: rights in other schemas, `EXECUTE` on functions, and `REFERENCES` on one column." | Delete both (below 16 is refused; the three "not looked at" are now looked at) |
| CL:17 (whole item, about 900 words) | among others: "in ANY schema of the database, whatever way the file did it"; "`_refuse_foreign_owned` looked at it first"; "gets no right at all on a table, view, sequence or column that is not in the grant map, in any schema, and no right on a function"; "on PostgreSQL 14 and earlier the default of the `public` schema lets everyone create" | Delete the item. New item: the promise table, the baseline (3.4), the three calls (4), the after-commit message (4.2) |
| CL:18 | "because the read-back does not look at those places"; "a table, a type or a column that is called `rename` does not make an owner change pass"; "a file cannot create a type or a domain, the text scan refuses `CREATE TYPE` and `CREATE DOMAIN`"; "found by the read-back for a table, view, ... and for no other kind of object" | Delete the four sentences. New sentence: "These text rules refuse common accidents early with a plain message. They are not the guard; dynamic SQL passes them, and `verify` judges what is in the database afterwards." |
| CL:34 | "PostgreSQL 16 is the lowest version this check is written for" | Replace: "PostgreSQL 16 is the lowest version `migrate` runs on; an older server is refused with a plain message before anything is read or changed" |
| CL:34 and CL:15 (MAINTAIN) | "Not yet run on PostgreSQL 17.10 ... the `MAINTAIN` check is covered only by tests that fake the server version"; "asks for `MAINTAIN` only from 17, because 16 rejects that name"; "On PostgreSQL 17 and later ... MAINTAIN is also counted" | Delete all three. New sentence: "On PostgreSQL 17 the right MAINTAIN is one more right in the access lists that `verify` reads; there is no version branch for it. The whole suite runs in CI on PostgreSQL 17.10." |

The builder also runs `grep -n -i --include='*.py' --include='*.md' -r "however it got it\|whatever way\|by any statement\|cannot leave\|no right at all\|Nothing was changed" src CHANGELOG.md tests` after the edit and pastes the output; each remaining hit is either inside a test of the old wording that was retired, or justified in one line.

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
| 14 | How a plain role comes to own an extension: it holds CREATE on the database (for example because it owns the database, which D-020 allows) and installs a trusted extension (21 are available on this machine, `citext` among them). It then owns the extension, while the objects inside are owned by the superuser. It can make its own table and its own SECURITY DEFINER function members of the extension (`ALTER EXTENSION citext ADD ...`; the `pg_depend` rows of type `e` appear). Without CREATE on the database it cannot install one ("permission denied for database"). | author run, as `r13_mig` with `current_user = session_user = r13_mig`: `CREATE EXTENSION`; `select extname, pg_get_userbyid(extowner)` gives `citext|r13_mig`; owner of the 47 member functions `postgres`; `ALTER EXTENSION` twice; `member|2`. Re-run in rev 2 with a fresh role and only CREATE on the database: same result (plan-r2/x-extension-owner.out). Settled; see "Read first" item 5. |
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
| 26 | CORRECTION (rev 2). Operator and function lookup CAN be captured by a user-defined operator or function with a matching signature in a schema that the search path lists before `pg_catalog` (the documented class behind CVE-2018-1058). Rev 1's probe (p4.out, `=(name, text)`) did not show it, which is no evidence of safety (its signature did not beat the built-in one). | from the PostgreSQL documentation and the CVE, not probed in rev 2. Consequence: every catalog read of the runner, not only `verify`, runs with the path pinned to `pg_catalog, pg_temp` (3.1, "Pinned reads"); `pg_temp` is never searched for functions or operators. |
| 30 | `REVOKE` removes only the entries whose grantor is the role the statement acts as. A superuser, and the owner, act as the owner: `REVOKE SELECT ON app.t FROM rt` leaves `rt=r/boss` (granted by `boss` through its grant option). `REVOKE ... GRANTED BY boss` on an object right is refused: "grantor must be current user". What works: `SET ROLE boss; REVOKE SELECT ON TABLE app.t FROM rt; RESET ROLE;`, run by a superuser, or `REVOKE SELECT ON app.t FROM boss CASCADE`, which also takes boss's own right. A plain `REVOKE ... FROM boss` while a dependent entry exists fails: "dependent privileges exist". A right granted by a superuser that is not the owner is recorded with the owner as grantor (`rt=w/mig`). `REVOKE GRANT OPTION FOR SELECT ON TABLE ... FROM boss CASCADE` removed boss's table-level dependents but left boss's column-level grant `secret: rt=r/boss` in place; it went only with the later `REVOKE SELECT ... FROM boss CASCADE`. | rev 2 run (plan-r2/a-revoke-grantors.out a1-a7, a11-a12; a2-orphan-column.out a13-a16) |
| 31 | Step 4's `REVOKE ALL ON TABLE app.t FROM rt`, run by the migration role (the owner), removes the entries it granted and leaves `rt=r/boss` and the column grant `secret: rt=r/boss`; `rt` can still read. | rev 2 run (a-revoke-grantors.out a2: `{mig=arwdDxt/mig,boss=r*/mig,rt=r/boss}`; the `SELECT` as `rt` then ran without error: `rt_can_still_read` = 0 rows of an empty table) |
| 32 | Memberships on 16: `GRANT grp TO rt` run by a CREATEROLE role `cr` records `cr` as grantor. The superuser's plain `REVOKE grp FROM rt` then does nothing and prints "WARNING: role "rt" has not been granted membership in role "grp" by role "postgres"". `REVOKE grp FROM rt GRANTED BY cr` removes it. Two grants of the same membership by two grantors are two rows; one plain REVOKE leaves the other. `REVOKE ... GRANTED BY <the bootstrap superuser>` also works for the superuser's own grant. | rev 2 run (a-revoke-grantors.out a8-a10) |
| 33 | Row types on 16: tables, partitioned tables, partitions, views, materialized views and foreign tables each have one (`typtype = 'c'`, `typrelid` set, the relation's `relkind` is `r p v m f`). A sequence has NONE (`reltype = 0`; `GRANT USAGE ON TYPE app.seq` fails "type does not exist"). A standalone composite type has `typtype = 'c'` with a relation of `relkind = 'c'`. Every type (base, composite, domain, enum, range, multirange, array) with a NULL `typacl` defaults to `=U/<owner>`. A GRANT on a row type or a standalone composite type writes `=U/<owner>` next to the grantee. | rev 2 run (b-row-types.out b1-b6) |
| 34 | The `public` schema of a new database on 16 is owned by `pg_database_owner` with `{pg_database_owner=UC/pg_database_owner,=U/pg_database_owner}`: everyone may look names up, nobody else may create. The owner of the database (a plain role) is a member of `pg_database_owner` and may create in `public`; a new plain role may use it but not create in it. A schema with a NULL access list gives everyone nothing (`acldefault('n', ...)` has no `=` entry). | rev 2 run (c-public-schema.out c1-c5) |
| 35 | psycopg 3.3.6: a keyword `options=` REPLACES an `options=` inside the DSN (the merged conninfo keeps only the keyword's value). With the DSN alone (`options='-c role=drole'`) the session runs as `drole`; with the keyword added it runs as the login `dlogin`, so the role switch is lost. Also: `store/postgres.connect` at 4d328e3d takes only `dsn, iam_auth, region, sslmode, sslrootcert`, so rev 1's call with `options=` would raise `TypeError`. | rev 2 run (dfg.out d1-d3); signature read at store/postgres.py:125-132 |
| 36 | A role may run `ALTER ROLE <itself> SET statement_timeout = 1`. A fresh session then starts with `1ms`; 100 of 100 fresh connections that ran a catalog read shaped like Q2 were cancelled (57014). With `SET LOCAL statement_timeout = '60s'; SET LOCAL lock_timeout = '5s'` as the first statements of the transaction, 100 of 100 ran (the `SET TIME ZONE 'UTC'` that `connect` sends ran under the 1 ms limit and passed 100 of 100, which is luck, not a guarantee). | rev 2 run (dfg.out g1-g3) |
| 37 | COMMIT failures, as psycopg reports them: (a) the server refuses the COMMIT (a deferred foreign key checked at COMMIT): `ForeignKeyViolation`, SQLSTATE 23503, the connection stays open, transaction status IDLE; nothing was committed. (b) the connection is cut after the COMMIT message reached the server (a TCP relay that forwarded COMMIT and dropped the reply): `OperationalError`, SQLSTATE None, "consuming input failed: server closed the connection unexpectedly", status UNKNOWN, connection closed, AND the row IS in the table when read on a new connection: the commit happened although the client got an error. | rev 2 run (f2.out f1, f2; dfg.out holds a first run whose relay cut too late and is not used) |
| 38 | A named role that is a member of `pg_monitor` reaches `pg_monitor`, `pg_read_all_settings`, `pg_read_all_stats` and `pg_stat_scan_tables`. Rev 1's rules would print 12 problem lines and 12 REVOKE statements against `pg_catalog` functions and views (for example `REVOKE EXECUTE ON FUNCTION pg_catalog.pg_ls_archive_statusdir(...) FROM pg_monitor;`), which would strip monitoring from the whole server. The one right statement is `REVOKE pg_monitor FROM hrt GRANTED BY postgres;`. | rev 2 run (h-pg-monitor.out h1-h4) |
| 39 | The re-defer route of fact 4 confirmed as the plain migration role with no superuser: the pre-commit read of the access list is empty, the trigger fires a second time at COMMIT, and afterwards the list is `{emig=arwdDxt/emig,=r/emig}`. Promise table row 3 is right to say "detected, not stopped". | rev 2 run (e-redefer.out) |
| 41 | (rev 3) A referencing TEMPORARY table cannot show REFERENCES: `CREATE TEMP TABLE u (x int REFERENCES app.t (id))` gives 42P16 "constraints on temporary tables may reference only temporary tables" whether or not the role holds REFERENCES. A permanent table owned by the probed role does show it: `ALTER TABLE scratch.u ADD FOREIGN KEY (x) REFERENCES app.t (id)` is allowed with REFERENCES (table level or on column `id` only) and 42501 "permission denied for table t" without. | rev 3 run (plan-r3/p3.out A1-A5) |
| 42 | (rev 3) With everyone's TEMPORARY revoked, every attempt that makes a temporary object fails with 42501 "permission denied to create temporary tables" before the type or language is checked (B0, B1, B10). `SELECT NULL::app.typ` is allowed WITHOUT USAGE on the type (B2): USAGE on a type only controls making objects that depend on it. Attempts that show USAGE without TEMPORARY: `CREATE TABLE scratch.u (x app.typ)` in a scratch schema where the role may create (allowed with USAGE, 42501 "permission denied for type app.typ" without); `DO $$BEGIN END$$ LANGUAGE plpgsql` (allowed with USAGE, 42501 "permission denied for language plpgsql" without). | rev 3 run (p3.out B0-B10) |
| 43 | (rev 3) Codes per relation kind, role with ALL / with nothing. Table: INSERT, UPDATE, DELETE, TRUNCATE, SELECT allowed / 42501; REINDEX 42501 "must be owner" in both (16). Auto-updatable view: INSERT, UPDATE, DELETE, SELECT allowed / 42501; TRUNCATE and REINDEX 42809 in both. View that is not auto-updatable: INSERT, UPDATE, DELETE 55000 in both (no rights check reached); SELECT allowed / 42501. Materialized view: INSERT, UPDATE, DELETE 42809 "cannot change materialized view" WITH the right and 42501 without (the rights check comes first); TRUNCATE 42809 in both; REINDEX and REFRESH 42501 "must be owner" in both. Sequence: SELECT allowed / 42501; UPDATE statement 42809 with ALL; INSERT, DELETE 42501 in both (a sequence has no such right); TRUNCATE, REINDEX 42809 in both. `UPDATE app.t SET c = NULL WHERE false` with UPDATE and no SELECT: allowed. | rev 3 run (p3.out section C) |
| 44 | (rev 3) Foreign table (`file_fdw`, available here as contrib): SELECT allowed / 42501; INSERT, UPDATE, DELETE 0A000 "cannot insert into foreign table" WITH the right and 42501 without; TRUNCATE 0A000 in both. | rev 3 run (p3b.out J) |
| 45 | (rev 3) Schema USAGE confounds object attempts: SELECT on `other.ot` WITH the table right and without USAGE on `other` gives 42501 "permission denied for schema other", the same code as no table right. `DROP TABLE IF EXISTS other.<name that does not exist>` is allowed (a notice only) with USAGE, directly or through everyone, and 42501 "permission denied for schema other" without it: an attempt that shows schema USAGE alone. | rev 3 run (p3.out D1-D4, p3b.out K1-K3) |
| 46 | (rev 3) COMMIT failures, psycopg 3.3.6 on an autocommit connection with a `transaction()` block (the shape `store/postgres.connect` gives): `pg_terminate_backend` while a commit-time trigger runs gives `psycopg.errors.AdminShutdown`, SQLSTATE 57P01, `closed=True`, status UNKNOWN, and the row was NOT committed; `pg_cancel_backend` at the same point gives `QueryCanceled` 57014, connection open, status IDLE, row not committed. With fact 37: a cut connection can also leave a committed row with the same "closed" signs, so "closed" never means "nothing kept". Also: `isolation_level = REPEATABLE_READ` and `read_only = True` set on an autocommit connection ARE carried by the BEGIN of `transaction()` (`repeatable read`, `on`), also inside a nested savepoint; after `psycopg.Rollback` of the savepoint the search path is the session's again. | rev 3 run (p3.out E1-E4, F1, F2) |
| 47 | (rev 3) Order of the limits: a role with a saved `statement_timeout = 1`: 0 of 100 fresh connections failed with the path set first, 0 of 100 with the limits set first; without the limits 20 of 20 Q2 runs were cancelled. The order does not matter measurably here; limits first is kept as the safer order. | rev 3 run (p3b.out N) |
| 48 | (rev 3) Q0 as the plain login returns the 14 columns of fact 9; the version read returns 160015. `REVOKE pg_database_owner FROM r3_mig` (with or without `GRANTED BY postgres`), where `r3_mig` owns the database, does nothing and warns "has not been granted membership in role "pg_database_owner" by role "postgres""; only a change of the database owner removes it. With everyone's rights on the database revoked (a common hardening step), Q2 returns NO database row, so the database owner must be read on its own: `SELECT pg_catalog.current_setting('server_version_num')::int, pg_catalog.pg_get_userbyid(d.datdba) FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()` returned `(160015, 'r3_mig')`. Q1, Q1b, Q2, Q3, Q4 and the step-4 query run without error with an EMPTY named array and roles array (Q1 0 rows, Q2 69 rows, Q3 0, Q4 0) and with a two-entry family (`r3_mig` plus the login `r3_login`, run after `SET ROLE r3_mig`). | rev 3 run (p3.out G, H; p3b.out L; p3c.out) |
| 49 | (rev 3) A grant option held from two grantors: `r3_boss=r*/r3_mig` and `r3_boss=r*/r3_boss2`, and `r3_rt=r/r3_boss`. The superuser's `REVOKE GRANT OPTION FOR SELECT ON app.g FROM r3_boss CASCADE` leaves `r3_boss=r*/r3_boss2` AND `r3_rt=r/r3_boss`. `SET ROLE r3_boss2; REVOKE GRANT OPTION FOR SELECT ON app.g FROM r3_boss CASCADE; RESET ROLE;` then removes both. | rev 3 run (p3b.out M1-M3) |
| 50 | (rev 3) Extension-owned objects: `CREATE EXTENSION pg_stat_statements` (contrib, superuser) leaves the views `public.pg_stat_statements` and `public.pg_stat_statements_info` readable by everyone (`=r/postgres`); Q2 returns them as 2 rows with `extension = pg_stat_statements`, `extension_family_owned = false`, grantee everyone, SELECT. After `REVOKE SELECT ... FROM PUBLIC`, `ALTER EXTENSION pg_stat_statements UPDATE` (1.9 to 1.10) writes `=r/postgres` back. Mutant lists of 4d328e3d (288 in `migrate_mutants.py`, 40 in `migration_numbers_mutants.py`; every `old` text occurs exactly once): 106 overlap a line range rev 3 plans to edit; 30 of those were in no rev 2 list. | rev 3 run (p3b.out I1-I4); affected_mutants.out, affected_vs_rev2_lists.out (the extra id "by" in the second file is a regex artefact of the reading script, not a mutant) |
| 40 | The final query texts of section 3.2 (Q1, Q1b, Q2, Q3, Q4, the step-4 query) run without error as a plain login on 16.15 against a made-up setup that holds a grant-option chain, a `pg_monitor` member, a membership with INHERIT FALSE, a default right and a 25-level "diamond" of groups (each level two roles, each a member of both roles of the next level). Q1 took 1.9 ms; the rev 1 shape (`UNION ALL` with a depth column) was cancelled by a 10 s limit on the same roles. Q2 returned no `pg_catalog` item for the `pg_monitor` member. | rev 2 run (queries.py, run_queries.out) |

## 3. Design of `verify`

### 3.1 Signature and shape

New module `src/hadavin_sdk/store/migration_verify.py`. Module layout (decided in rev 2, R-M6):
- It imports from the database library only `psycopg` (for `psycopg.Rollback`) and `psycopg.sql`, and from the package only `hadavin_sdk.errors` and `hadavin_sdk.store.migration_numbers`. It never imports `hadavin_sdk.store.migrate` at run time; `Grant` is imported for type hints only, under `if TYPE_CHECKING:`. So `migrate` imports `migration_verify` and there is no import cycle.
- `_label` moves from `migrate.py` (MIG:1364-1366) into `migration_numbers.py`, next to `escape_name`, which it calls. `migrate.py` imports it back under the same name, so `mig._label` keeps working for tests. No mutant is planted inside `_label` (checked: its body text appears in no `old` of `MUT`).
- `Grant`, `GRANTS`, `REVIEWED_DEFINER_FUNCTIONS`, `RUN_SCHEMA` and `_shown` stay in `migrate.py`. `verify` receives the grant map and the reviewed list as arguments with NO default value, and `migrate()` passes `REVIEWED_DEFINER_FUNCTIONS` by reading the module global at call time, so `monkeypatch.setattr(mig, "REVIEWED_DEFINER_FUNCTIONS", ...)` (TPG:2804) still reaches `verify`. TPG:2804's patched value becomes `frozenset({(mig.RUN_SCHEMA, "hadavin_test_definer", "")})` (the new key of rule O4).

```python
@dataclass(frozen=True)
class Problem:
    kind: str     # one of PROBLEM_KINDS (section 3.3, the closed tuple)
    schema: str   # "" for an object that lives in no schema (database, large object, parameter, ...)
    obj: str      # the object's name; "" when the problem is about a role alone
    detail: str   # the column, the argument list, or the membership path; "" otherwise
    role: str     # the role that holds it; everyone is written "everyone (PUBLIC)"
    right: str    # the right, the flag, "OWNER", or "MEMBER"
    grantor: str  # the role recorded as grantor of the item ("" for flags and ownership)
    fix: str      # the statement(s) that remove it (section 4.2 forms), or "" (a person writes it by hand)
    by_hand: str = ""  # why no statement is printed: "name" (a name is not plain) or "system" (a server object)
    repaired_by_run: bool = False  # true only for the two cases of section 4.1 step 2

    def line(self) -> str: ...


def verify(
    db,
    *,
    migration_role: str,
    login_role: str | None,
    named_roles: Mapping[str, Literal["runtime", "portal", "purge"]],
    grant_map: Mapping[str, Grant],
    schema: str,
    managed_relations: Sequence[str],  # the grant-map relations and schema_migrations (_managed_names(...)[0])
    managed_functions: Sequence[str],  # the functions the files create (_managed_names(...)[1])
    reviewed_definers: frozenset[tuple[str, str, str]],
    limits: Sequence[str],          # the two lines of RECIPE_TIMEOUTS, run as statements
) -> list[Problem]:
```

**Pinned reads (rev 2, D-m1 and fact 26; order changed in rev 3, F7).** One helper in the new module, `pinned_read(db, limits)`, a context manager: `with db.transaction():` (a savepoint inside the run's transaction, a transaction on a fresh connection), first the lines of `limits` (`SET LOCAL statement_timeout ...`, `SET LOCAL lock_timeout ...`), then `SET LOCAL search_path = pg_catalog, pg_temp`, then the caller's reads, and on the way out it raises `psycopg.Rollback`, so the path and the limits are restored (fact 15, fact 46 E3) and nothing is kept. Fact 47 measured no difference between the two orders; limits first is kept because a statement that runs before the limits is the only one a saved role setting can cancel. `verify` runs all its statements inside one `pinned_read`. The runner's other catalog reads use it too: `_refuse_privileged_role`, the reads of `_refuse_foreign_owned`, `_read_back` and `_check_read_back` (steps 1, 3 and 6), `_recheck_roles`, `_members_of_each_other` and the step-4 query. Rev 3 (closes the re-indent risk of M7): the `with pinned_read(db, RECIPE_TIMEOUTS):` blocks sit at the CALL SITES inside `migrate()`, which is rewritten anyway; the bodies of these kept functions are not edited or re-indented, so no mutant planted in them moves. `test_every_runner_catalog_read_is_pinned` (commit 3b) checks with `ast` that every call of these seven names inside `migrate()` is lexically inside a `with` whose context expression is a call of `pinned_read`.

**Qualified names, defined (rev 3, M8).** Rule: inside the query constants of the NEW module (`Q0`, `Q1`, `Q1B`, `Q2`, `Q3`, `Q4`, `STEP4_SQL`, `V2_SQL`), every name of a relation of `pg_catalog` (the token list is the `relname` of every table and view in `pg_catalog`, read by the test from the server, or, without a server, the fixed list of the 25 catalog relations the constants use) is written `pg_catalog.<name>`. Functions, casts and types (`bool_or`, `::text[]`, `::"char"`, `::int`) are NOT required to be prefixed: the path is pinned to `pg_catalog, pg_temp`, and PostgreSQL never looks functions, operators or types up in `pg_temp` unless named with `pg_temp.` (the documented rule behind fact 2; a temporary table, by contrast, CAN shadow an unqualified relation, fact 1). The kept queries of `migrate.py` are NOT prefixed in this ticket (rev 2 asked for it; dropped in rev 3): they all run inside `pinned_read`, where an unqualified catalog name reads `pg_catalog` (fact 1), and prefixing them would move about 30 mutants for no added protection. `test_every_catalog_name_in_the_queries_is_qualified` scans the new module's constants only, by the regular expression `(?<![\w.])(pg_[a-z_]+)\b(?!\s*\()` restricted to the relation list (so `pg_catalog.pg_get_userbyid(` and `pg_catalog` itself never match).

**Imports (m6).** The new module starts with `from __future__ import annotations` and imports `Grant` only under `if TYPE_CHECKING: from hadavin_sdk.store.migrate import Grant`. Every kept read that names the schema through `current_schema()` gets the schema read at step 1 as a parameter instead, because with the path pinned `current_schema()` answers `pg_catalog`: `_READBACK_TRIGGERS_SQL` (MIG:476), `_FOREIGN_OWNED_SQL` (MIG:671, 680) and the read in `_refuse_foreign_owned` (MIG:770); the one read of step 1 (MIG:1603) stays and is the only `current_schema()` left in `migrate.py` (acceptance item 2b). Writes are never inside it: the step-4 statements are qualified with the schema read at step 1 (`_apply_grants` gets a `schema` argument instead of reading `current_schema()` itself, MIG:263).

- `migration_role` is the current user that `migrate` read once in step 1; `login_role` is the session user when it differs (a login that switches role). Both are plain strings passed in. `verify` never reads `current_user`, `session_user` or `current_schema()`; `schema` is the schema of the run, read once in step 1 (with the path pinned, `current_schema()` would answer `pg_catalog`).
- `named_roles` maps each role name given on the command line to the column of the grant map it gets. With no role arguments it is empty, and the subject side still judges everyone.
- `verify` only reads. It returns every problem (the caller cuts the printed list with `_shown`, the decision is taken on the full list).
- `verify` has two layers, so that tests can pin each: `_read(db, ...)` runs the queries of 3.2 and returns plain rows; `_judge(rows, ...)` is a pure function that turns rows into `Problem`s. All rules of 3.3 live in `_judge`.
- How it runs: inside `pinned_read(db, limits)`: first the two lines of `limits` (the `RECIPE_TIMEOUTS` constant, passed in, never written a second time: TR `test_no_source_or_test_file_writes_the_timeout_values_a_second_time`), then the path, so every call has a 60 s limit per statement and a 5 s lock limit, also on the fresh connection of step 8 where a saved role setting could hold anything (fact 36). Then the version-and-owner read `V2_SQL` (3.5), the self-check (3.6), the queries. The block always ends by rolling back, which restores the search path and the limits and keeps nothing. Not neutralised: `transaction_timeout` (PostgreSQL 17 and later). A saved role value of it can stop the check; that ends in "could not run", exit 5 at step 8 or exit 2 before the commit, never in "applied" (F7). The CHANGELOG says "a saved `statement_timeout` or `lock_timeout` of the migration role cannot stop the check", nothing broader.
- `RUN_SCHEMA` (rev 3, M5): `verify` never sees `RUN_SCHEMA`. `migrate()` turns the reviewed list into concrete keys before the call: `{(schema if s == RUN_SCHEMA else s, name, args) for (s, name, args) in REVIEWED_DEFINER_FUNCTIONS}`, read at call time, so the monkeypatch of TPG:2804 still reaches it. `verify(reviewed_definers=...)` receives only real schema names.

### 3.1a Interfaces a builder must not invent (rev 3, M5)

```python
class Rows(NamedTuple):            # what _read returns; each field is a tuple of psycopg rows made with row_factory=namedtuple_row,
    version: int                   # so fields are read by the column NAMES of the queries in 3.2 (r.grantee, r.privilege_type, ...)
    database_owner: str            # from V2_SQL (3.5), not from Q2 (fact 48)
    acl_columns: tuple[str, ...]   # Q0, "relname.attname"
    subjects: tuple                # Q1 from the named roles: start_role, member_of, uses_rights_at_once, rolsuper, ...
    family: tuple                  # Q1 from the family
    memberships: tuple             # Q1b from the named roles
    items: tuple                   # Q2
    owned_or_named: tuple          # Q3
    defaults: tuple                # Q4

def _read(db, *, named: Sequence[str], family: Sequence[str], schema: str, managed_functions: Sequence[str]) -> Rows: ...
def _judge(rows: Rows, *, named_roles: Mapping[str, str], family: Sequence[str], grant_map: Mapping[str, Grant], schema: str,
           managed_relations: Sequence[str], managed_functions: Sequence[str], reviewed_definers: frozenset[tuple[str, str, str]]) -> list[Problem]: ...
def statements_for(problems: Sequence[Problem]) -> list[str]: ...   # 4.2: ordered, de-duplicated, rendered with as_string(db)
```

`verify` = version refusal (3.5) and self-check (3.6) on `rows`, then `_judge`. Pure tests build `Rows` by hand with `collections.namedtuple` rows whose field names are the column names of 3.2; a repository test asserts that the field names used by `_judge` (collected with `ast` from attribute reads on row variables) are a subset of the column names of the query texts.

`Problem` (frozen dataclass), rev 3 fields, in this order: `kind`, `schema`, `obj`, `detail`, `role`, `right`, `grantor`, `owner` (the object's owner, "" for role-only problems), `grantor_is_owner: bool`, `outside_package: bool` (true when the object is outside the schema of the run, or its owner is not in the family; 4.2 F11), `extension: str` ("" or the extension the object is a member of), `fix`, `by_hand` ("" / "name" / "system" / "database_owner" / "extension" / "owner"), `repaired_by_run`, and the property `order` = index of the statement group of 4.2 (0 memberships, 1 default rights, 2 object rights granted by another role, 3 object rights granted by the owner, 4 grant options, 5 flags, 6 SECURITY DEFINER, 7 by hand). Problems are sorted by `(order, kind, schema, obj, detail, role, right, grantor)` before printing, so output is stable.

`Problem.line()`: `<object words> <schema.name or name><detail>: <role words> <what>. <ending>`; `<ending>` is "To remove: <fix>" when `fix` is set, else the by-hand sentence of `by_hand`, and lines with `outside_package` start with "NOT THIS PACKAGE'S OBJECT: " (4.2). The `<what>` per kind (role names through `_label`; "everyone (PUBLIC)" for PUBLIC):

| kind | `<what>` after "<object>: <role>" | statement form (4.2) or by hand |
|---|---|---|
| flag | "has the flag <FLAG> (directly or through <role path>)" | `ALTER ROLE <r> NO<FLAG>;` |
| built_in_role | "is a member of the built-in server role <pg_x> (through <path>)" | `REVOKE <group> FROM <member> GRANTED BY <grantor>;` on the first membership of the path; `pg_database_owner`: by hand "this role owns the database <db>; hand the database to another role (ALTER DATABASE ... OWNER TO ...)" |
| can_act_as_family | "can act as the migration role <m> (member of it through <path>)" | membership statement |
| named_roles_overlap | today's sentence (MIG:1471) unchanged | membership statement |
| owns | "owns this object" | by hand: "hand it to the migration role or drop it" |
| right | "has <RIGHT>" or "can use it through the role <g> (...), <RIGHT>" | object-right form |
| grant_option | "may pass <RIGHT> on to others" | grant-option form |
| definer_callable | "may call it, and it runs with the rights of its owner <o> (SECURITY DEFINER)" | `ALTER FUNCTION ... SECURITY INVOKER;` |
| unread_catalog | "is named in the access list of a kind of object this version does not read (<catalog>)" | by hand |
| unread_relation_kind | "has <RIGHT> on a relation of a kind this version does not read (relkind <c>)" | by hand |
| foreign_owner | "is owned by <owner>, which is not the migration role or a role it belongs to" | by hand "owner" |
| other_grantee | "has <RIGHT>; only the owner, the migration role and the grant map's roles may hold rights here" | object-right form |
| everyone | "everyone (PUBLIC) has <RIGHT>" | object-right form |
| object_grant_option | "may pass <RIGHT> on to others" | grant-option form |
| definer_unreviewed | "runs with the rights of its owner (SECURITY DEFINER) and is not on the reviewed list" | `ALTER FUNCTION ... SECURITY INVOKER;` |
| schema_right | "has <RIGHT> on the schema of the run; only USAGE is allowed" | object-right form |
| default_for_named | "gets <RIGHT> on every new <kind> that <set_for> makes<in schema>" | default-right form |
| default_for_everyone | same words with "everyone (PUBLIC)" | default-right form |
| default_for_other | same words | default-right form |
| default_unknown_kind | "a default right of a kind this version does not know (<letter>)" | by hand |
| missing_schema_usage | today's message text (MIG:1665-1671) | none (it is "too little", not excess) |

The table is 21 kinds: the closed tuple of 3.3. `test_every_problem_kind_has_a_line_form` (commit 1) builds one `Problem` per kind and asserts that `line()` contains the kind's fixed words and no raw control character.
- Snapshots: at steps 2 and 6 the statements run inside the run's READ COMMITTED transaction, so each sees its own snapshot (another session can commit between two of them; the check after the commit catches what lands). At step 8 the fresh connection's transaction is opened `ISOLATION LEVEL REPEATABLE READ, READ ONLY` (psycopg: `db.isolation_level` and `db.read_only` set before `pinned_read`), so all statements of the check after the commit read one snapshot. Said in the CHANGELOG.
- Every catalog relation in the new module's queries is written with `pg_catalog.` in front (rule and test defined above, "Qualified names, defined"; rev 3 narrowed it from "every table, view, function and type", which the pasted Q1 text itself did not meet). No `::regclass` or `::regrole` from a bare text literal; `'pg_catalog.pg_class'::pg_catalog.regclass` is the allowed form.

A problem line (what `Problem.line()` returns), fixed order kind of object, schema.name, detail, role, right, what to do:

```
table app.audit_entries: everyone (PUBLIC) has SELECT. To remove: REVOKE SELECT ON TABLE "app"."audit_entries" FROM PUBLIC;
table other.secret: r13_rt can use it through the role r13_grp (a membership that does not pass rights on by itself, but r13_rt may switch to r13_grp), SELECT. To remove: REVOKE "r13_grp" FROM "r13_rt";
role r13_po: is a member of the built-in server role pg_read_server_files. To remove: REVOKE "pg_read_server_files" FROM "r13_po";
function app.door(q text): runs with the rights of its owner r13_mig (SECURITY DEFINER) and is not on the reviewed list. To remove: ALTER FUNCTION "app"."door"(q text) SECURITY INVOKER;  (or drop it)
```

Every name that comes from the database goes through the existing `_label` helper (moved to `migration_numbers`, see above) in the readable part. The `fix` statement is printed only when every text in it is plain (`escape_name(x) == x`, the rule `_refuse_foreign_owned` already uses at MIG:780), and that includes the whole argument list of a function (`pg_get_function_identity_arguments` prints argument NAMES, which can hold control characters) and the grantor; otherwise `fix` is empty, `by_hand = "name"`, and the line ends "a person must write the statement by hand (a name holds a character that is not copied into a printed line)". For an object in `pg_catalog` or `information_schema` no statement is ever printed (`by_hand = "system"`), and the line ends "this is an object of the server itself; a database administrator decides; no statement is printed". Statements are built with `sql.Identifier`, never by string formatting. This also closes the raw names at MIG:316, 324, 339, 353, 365; MIG:1314 (`usename`) gets `_label` in section 6.

### 3.2 The queries (final texts, rev 2; each ran without error as a plain login on 16.15, fact 40; the same text is in handover/evidence/P3a-2/plan-r2/queries.py)

The builder copies these texts into the module as constants, without rewording them; a change needs a new run on a server, pasted in the builder notes. Parameters are bound by psycopg with `db.execute(TEXT, params)`: `%(named)s` text array of the named roles, `%(family)s` text array (`migration_role`, plus `login_role` when it differs), `%(roles)s` text array (the roles a closure starts from), `%(schema)s` the schema of the run, `%(managed)s` text array of the function names the files create (`_managed_names(...)[1]`). The two closures (`subj`, `fam`) use `UNION`, not `UNION ALL`: a role graph where groups belong to several groups gives an exponential number of paths otherwise (fact 40: 25-level diamond, 1.9 ms against a cancelled run). No statement is sent per role, per relation or per right: `verify` sends Q0, the version read, Q1 twice (from the named roles and from the family), Q1b, Q2, Q3 and Q4, 8 statements whatever the size of the database. `has_*_privilege` and `pg_has_role` are not used anywhere in the new module (fact 6).

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

**Q1, the closure.** Run twice: with `%(roles)s` = the named roles (the *subjects* of each named role: the role itself and every role it belongs to, directly or through other roles, whatever the options) and with `%(roles)s` = the family (the *migration role family*). `uses_rights_at_once` is false when every path to that role passes a membership with INHERIT FALSE (fact 6). Whether a role is built in is decided in Python by the prefix `pg_` (a new role cannot take that prefix: "role name ... is reserved"). One row is added in Python when it applies: a closure that contains the owner of the current database (read by `V2_SQL`, 3.5; rev 2 read it from Q2's database branch, which can be empty, fact 48) also contains `pg_database_owner` (fact 8). The same applies to the family closure: when the family contains the database owner, `_judge` treats objects owned by `pg_database_owner` (the `public` schema, fact 34) as family-owned, although Q2's `family_owned` column is false for them (F9).

```sql
WITH RECURSIVE closure(root, role, at_once) AS (
  SELECT r.oid, r.oid, true FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[])
  UNION
  SELECT c.root, m.roleid, c.at_once AND m.inherit_option
    FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member = c.role)
SELECT pg_catalog.pg_get_userbyid(c.root) AS start_role, r.rolname AS member_of, bool_or(c.at_once) AS uses_rights_at_once,
       r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
  FROM closure c JOIN pg_catalog.pg_roles r ON r.oid = c.role
 GROUP BY c.root, r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolbypassrls, r.rolreplication
 ORDER BY 1, 2;
```

**Q1b, the direct membership rows** (for the words of a line and for the printed statement, which needs the grantor, fact 32):

```sql
SELECT pg_catalog.pg_get_userbyid(m.member) AS member, pg_catalog.pg_get_userbyid(m.roleid) AS role_name,
       pg_catalog.pg_get_userbyid(m.grantor) AS grantor, m.admin_option, m.inherit_option, m.set_option
  FROM pg_catalog.pg_auth_members m
 WHERE m.member IN (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(roles)s::text[]))
 ORDER BY 1, 2, 3;
```

**Q2, every access-list item that matters, one query over the 13 live columns.** Rev 1's changes (a)-(d) are built in: (a) `pg_catalog` and `information_schema` are read (column `system`), but in them only items whose grantee is a named role itself, or a subject role whose name does not start with `pg_`, are returned (D-M4, fact 38); the schemas of other sessions (`pg_temp_N`, `pg_toast`, `pg_toast_temp_N`) are left out by `!~ '^pg_(toast|temp_)'`; (b) extension membership is computed for every kind except columns, through one join on `pg_depend` type `e`; (c) the extension's owner and whether it is in the family are returned; (d) a relation of a kind outside `r p v m S f` that carries an access list is returned with the kind word "relation of an unread kind" and becomes a problem line of its own. Third clause of the WHERE (rev 2, after the first run): every item of every object in the schema of the run, whoever owns it, so rule O8 sees an object a file handed to a third role (re-run on a fresh 16.15 cluster: 49 rows, 25.6 ms, the third-role table returned; plan-r2/run_queries_r2.out). Also returned: `row_type` (fact 33: `typtype = 'c' AND typrelid <> 0 AND relkind <> 'c'`; a standalone composite type is NOT a row type), the grantor and whether the grantor is the owner (facts 30, 31).

```sql
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role),
fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role),
named(role) AS (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])),
obj(kind, relkind, cls, oid, schema, name, sub, owner, definer, row_type, acl) AS (
  SELECT CASE c.relkind WHEN 'S' THEN 'sequence' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view'
                        WHEN 'f' THEN 'foreign table' WHEN 'r' THEN 'table' WHEN 'p' THEN 'table'
                        ELSE 'relation of an unread kind' END,
         c.relkind::text, 'pg_catalog.pg_class'::pg_catalog.regclass, c.oid, n.nspname, c.relname, '', c.relowner, false, false,
         coalesce(c.relacl, pg_catalog.acldefault(CASE c.relkind WHEN 'S' THEN 's' ELSE 'r' END::"char", c.relowner))
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname !~ '^pg_(toast|temp_)' AND (c.relkind IN ('r','p','v','m','S','f') OR c.relacl IS NOT NULL)
  UNION ALL
  SELECT 'column', c.relkind::text, 'pg_catalog.pg_class'::pg_catalog.regclass, c.oid, n.nspname, c.relname, a.attname, c.relowner, false, false, a.attacl
    FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid = a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE a.attacl IS NOT NULL AND NOT a.attisdropped AND n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT CASE p.prokind WHEN 'p' THEN 'procedure' WHEN 'a' THEN 'aggregate' ELSE 'function' END, '',
         'pg_catalog.pg_proc'::pg_catalog.regclass, p.oid, n.nspname, p.proname,
         pg_catalog.pg_get_function_identity_arguments(p.oid), p.proowner, p.prosecdef, false,
         coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT 'schema', '', 'pg_catalog.pg_namespace'::pg_catalog.regclass, n.oid, n.nspname, '', '', n.nspowner, false, false,
         coalesce(n.nspacl, pg_catalog.acldefault('n', n.nspowner))
    FROM pg_catalog.pg_namespace n WHERE n.nspname !~ '^pg_(toast|temp_)'
  UNION ALL
  SELECT CASE t.typtype WHEN 'd' THEN 'domain' ELSE 'type' END, coalesce(rc.relkind::text, ''),
         'pg_catalog.pg_type'::pg_catalog.regclass, t.oid, n.nspname, t.typname, '', t.typowner, false,
         (t.typtype = 'c' AND t.typrelid <> 0 AND rc.relkind <> 'c'),
         coalesce(t.typacl, pg_catalog.acldefault('T', t.typowner))
    FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    LEFT JOIN pg_catalog.pg_class rc ON rc.oid = t.typrelid
   WHERE n.nspname !~ '^pg_(toast|temp_)' AND NOT (t.typelem <> 0 AND t.typcategory = 'A')
  UNION ALL
  SELECT 'database', '', 'pg_catalog.pg_database'::pg_catalog.regclass, d.oid, '', d.datname, '', d.datdba, false, false,
         coalesce(d.datacl, pg_catalog.acldefault('d', d.datdba))
    FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()
  UNION ALL
  SELECT 'foreign-data wrapper', '', 'pg_catalog.pg_foreign_data_wrapper'::pg_catalog.regclass, w.oid, '', w.fdwname, '', w.fdwowner, false, false,
         coalesce(w.fdwacl, pg_catalog.acldefault('F', w.fdwowner)) FROM pg_catalog.pg_foreign_data_wrapper w
  UNION ALL
  SELECT 'foreign server', '', 'pg_catalog.pg_foreign_server'::pg_catalog.regclass, s.oid, '', s.srvname, '', s.srvowner, false, false,
         coalesce(s.srvacl, pg_catalog.acldefault('S', s.srvowner)) FROM pg_catalog.pg_foreign_server s
  UNION ALL
  SELECT 'language', '', 'pg_catalog.pg_language'::pg_catalog.regclass, l.oid, '', l.lanname, '', l.lanowner, false, false,
         coalesce(l.lanacl, pg_catalog.acldefault('l', l.lanowner)) FROM pg_catalog.pg_language l
  UNION ALL
  SELECT 'large object', '', 'pg_catalog.pg_largeobject'::pg_catalog.regclass, m.oid, '', m.oid::text, '', m.lomowner, false, false,
         coalesce(m.lomacl, pg_catalog.acldefault('L', m.lomowner)) FROM pg_catalog.pg_largeobject_metadata m
  UNION ALL
  SELECT 'parameter', '', 'pg_catalog.pg_parameter_acl'::pg_catalog.regclass, a.oid, '', a.parname, '', 0::pg_catalog.oid, false, false, a.paracl
    FROM pg_catalog.pg_parameter_acl a WHERE a.paracl IS NOT NULL
  UNION ALL
  SELECT 'tablespace', '', 'pg_catalog.pg_tablespace'::pg_catalog.regclass, s.oid, '', s.spcname, '', s.spcowner, false, false,
         coalesce(s.spcacl, pg_catalog.acldefault('t', s.spcowner)) FROM pg_catalog.pg_tablespace s),
items AS (
  SELECT o.*, (o.schema IN ('pg_catalog', 'information_schema')) AS system, a.grantee, a.grantor, a.privilege_type, a.is_grantable
    FROM obj o CROSS JOIN LATERAL pg_catalog.aclexplode(o.acl) a)
SELECT i.kind, i.relkind, i.schema, i.system, i.name, i.sub, pg_catalog.pg_get_userbyid(i.owner) AS owner,
       (i.owner IN (SELECT role FROM fam)) AS family_owned, i.definer, i.row_type,
       xe.extname AS extension, pg_catalog.pg_get_userbyid(xe.extowner) AS extension_owner,
       (xe.extowner IN (SELECT role FROM fam)) AS extension_family_owned,
       CASE i.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(i.grantee) END AS grantee,
       (i.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, (i.grantee IN (SELECT role FROM named)) AS grantee_is_named,
       (i.grantee = i.owner) AS owner_item, i.privilege_type, i.is_grantable,
       pg_catalog.pg_get_userbyid(i.grantor) AS grantor, (i.grantor = i.owner) AS grantor_is_owner
  FROM items i
  LEFT JOIN pg_catalog.pg_depend xd ON xd.classid = i.cls AND xd.objid = i.oid AND xd.objsubid = 0 AND xd.deptype = 'e'
       AND i.kind <> 'column'
  LEFT JOIN pg_catalog.pg_extension xe ON xe.oid = xd.refobjid
 WHERE (i.grantee IN (SELECT role FROM subj)
        AND (NOT i.system OR (i.grantee IN (SELECT role FROM named)
                               OR pg_catalog.pg_get_userbyid(i.grantee) !~ '^pg_')))
    OR (NOT i.system AND i.grantee = 0
        AND (i.kind NOT IN ('function', 'procedure', 'aggregate', 'type', 'domain', 'language')
             OR i.owner IN (SELECT role FROM fam) OR i.definer))
    OR (NOT i.system AND i.schema = %(schema)s)
 ORDER BY 1, 3, 5, 6, 14, 18;
```

**Q3, what a subject owns, and where a subject is named** (`pg_shdepend`, all kinds in one query, fact 12). Database rows and parameter rows have `dbid` 0; a database row counts only for the current database. `temporary` marks a relation in a session's temporary schema, which is not a problem (TEMPORARY is in the stated baseline).

```sql
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role)
SELECT d.deptype::text, d.classid::pg_catalog.regclass::text AS catalog, d.objid, d.objsubid,
       pg_catalog.pg_get_userbyid(d.refobjid) AS role,
       pg_catalog.pg_describe_object(d.classid, d.objid, d.objsubid) AS described,
       (d.classid = 'pg_catalog.pg_class'::pg_catalog.regclass AND EXISTS (
          SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
           WHERE c.oid = d.objid AND n.nspname ~ '^pg_(toast_)?temp_')) AS temporary
  FROM pg_catalog.pg_shdepend d
 WHERE d.refclassid = 'pg_catalog.pg_authid'::pg_catalog.regclass AND d.refobjid IN (SELECT role FROM subj)
   AND (d.dbid = (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database())
        OR (d.dbid = 0 AND (d.classid <> 'pg_catalog.pg_database'::pg_catalog.regclass
                             OR d.objid = (SELECT oid FROM pg_catalog.pg_database WHERE datname = pg_catalog.current_database()))))
 ORDER BY 5, 1, 2, 6;
```

**Q4, default rights, selected by who receives them** (not by who set them):

```sql
WITH RECURSIVE subj(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(named)s::text[])
  UNION
  SELECT m.roleid FROM subj s JOIN pg_catalog.pg_auth_members m ON m.member = s.role),
fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role)
SELECT d.defaclobjtype::text AS kind, n.nspname AS schema, pg_catalog.pg_get_userbyid(d.defaclrole) AS set_for,
       (d.defaclrole IN (SELECT role FROM fam)) AS set_for_family,
       CASE a.grantee WHEN 0 THEN NULL ELSE pg_catalog.pg_get_userbyid(a.grantee) END AS grantee,
       (a.grantee IN (SELECT role FROM subj)) AS grantee_is_subject, a.privilege_type, a.is_grantable
  FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
 CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
 WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)
 ORDER BY 1, 2, 3, 5, 7;
```

**Step-4 query: the functions whose default EXECUTE for everyone the run removes** (replaces "functions that changed"; run inside `pinned_read`; each row becomes `REVOKE ALL ON ROUTINE <schema.name>(<identity arguments>) FROM PUBLIC`, built with `sql.Identifier` for the schema and the name and `sql.SQL` for the argument text, the form MIG:784 uses; a row whose texts are not plain is not revoked by the run and stays a problem line for step 6):

```sql
WITH RECURSIVE fam(role) AS (
  SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = ANY(%(family)s::text[])
  UNION
  SELECT m.roleid FROM fam f JOIN pg_catalog.pg_auth_members m ON m.member = f.role)
SELECT p.oid::pg_catalog.regprocedure::text AS shown, n.nspname, p.proname,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS args, p.prokind::text
  FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = %(schema)s AND p.proowner IN (SELECT role FROM fam) AND p.proname = ANY(%(managed)s::text[])
   AND EXISTS (SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))) a
                WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')
 ORDER BY 2, 3, 4;
```

**The "named role can use the schema" check without `has_schema_privilege`** (moved into `verify` from MIG:1662-1671; `_SCHEMA_USAGE_SQL` is deleted). From Q2's rows for the schema of the run (Q2 returns every item of that schema, third clause of its WHERE): a named role can use the schema when one item gives USAGE to (i) the named role itself, (ii) a subject role reached with `uses_rights_at_once` true in Q1, or (iii) everyone (`grantee` NULL, the `public` default, fact 34). A USAGE that reaches the role only through a role it must switch to does not count (the application never switches role; fact 6). Otherwise one problem of kind `missing_schema_usage` with today's message text (MIG:1665-1671), the only "too little" `verify` reports.

**The rights each named role may hold** (R-M7; read today only from the lambdas at MIG:1630-1654; `_judge` takes them from this table, and a unit test asserts the table equals what `_apply_grants` is called with):

| named role kind | on a relation of the grant map (matched by schema of the run, name and kind: `table` = relkind `r` or `p`, `view` = `v`, `sequence` = `S`) | on the schema of the run | anywhere else |
|---|---|---|---|
| runtime | exactly the comma-separated words of `Grant.runtime`, table level, no grant option | USAGE (required) | nothing beyond the baseline (3.4) |
| portal | SELECT when `Grant.portal` is true, table level (a sequence too); nothing otherwise | USAGE (required) | nothing beyond the baseline |
| purge | exactly the words of `Grant.purge`, table level, plus SELECT on exactly the columns `Grant.purge_cols` (column level) | USAGE (required) | nothing beyond the baseline |

A view of the map is granted with `GRANT ... ON TABLE` (MIG:268) and its access list uses the table letters; MAINTAIN (PostgreSQL 17) is not in any `Grant` and so is never allowed.

### 3.3 The rules (`_judge`); each lettered clause has one `Problem.kind` and at least one mutant

`PROBLEM_KINDS` (a closed tuple in the new module, in this order; a repository test asserts every kind is produced by at least one `_judge` unit test and named in the CHANGELOG list of what is refused):

| kind | clause | kind | clause |
|---|---|---|---|
| `flag` | S1 | `other_grantee` | O1 |
| `built_in_role` | S2 | `everyone` | O2 |
| `can_act_as_family` | S3 | `object_grant_option` | O3 |
| `named_roles_overlap` | S3 (existing rule of MIG:1471) | `definer_unreviewed` | O4 |
| `owns` | S4 | `schema_right` | O7 |
| `right` | S5 | `default_for_named` | D1 |
| `grant_option` | S6 | `default_for_everyone` | D2 |
| `definer_callable` | S7 | `default_for_other` | D3 |
| `unread_catalog` | S8 | `default_unknown_kind` | D4 |
| `unread_relation_kind` | Q2 change (d) | `missing_schema_usage` | 3.2, last part |
| `foreign_owner` | O8 (rev 2) | | |

**Subject side. For each named role and every role it belongs to:**

- S1 flags: none of the five flags (`SUPERUSER`, `CREATEROLE`, `CREATEDB`, `BYPASSRLS`, `REPLICATION`) on the named role or on any role in its closure.
- S2 built-in roles: no role in the closure has a name starting with `pg_` (this includes `pg_database_owner` added through fact 8). Every `pg_*` role is refused, also the harmless ones (consistent with D-020; said in the CHANGELOG). The line names the membership and the fix is the membership statement with its grantor (4.2). A right that reaches the named role THROUGH a `pg_*` role produces no line of its own: the S2 line covers it (D-M4, fact 38). That is enforced twice: Q2 does not return such items in the system schemas, and `_judge` drops an S5 or S6 item whose grantee is a built-in role in any schema.
- S3 family: no role in the closure is in the migration role family (a named role that can act as the owner of the tables), kind `can_act_as_family`. The existing rule "named roles are not members of each other" (`_members_of_each_other`, MIG:1471) stays and is asked through the same closure, kind `named_roles_overlap`.
- S4 owns nothing: no subject role owns any object in this database or the database itself (Q3 type `o`), temporary objects apart (Q3 column `temporary`).
- S5 rights: every Q2 item whose grantee is a subject role that is not built in, or everyone, must be allowed by the table "rights each named role may hold" (3.2) for the named role it reaches, or by the baseline (3.4). The map is matched by (schema of the run, name, kind): `runs` in another schema is not the grant-map table, and a view called like a grant-map table is not it. Rights on one column count like the map's column list. A right that reaches the named role only through a role it must switch to (fact 6) is judged exactly like a direct one; the line says through which role. Items of the system schemas are judged only when the grantee is the named role itself or a subject role that is not built in; no statement is printed for them (3.1).
  - Rev 3 (M5), a group role reached by two or more named roles: the item is judged once per named role that reaches it, against that named role's column of the rights table. It is allowed only when it is allowed for EVERY named role that reaches the group (a right reaches each of them). Example: `grp` is a member path of both runtime and portal and holds INSERT on `runs`; runtime's map allows INSERT, portal's does not: one problem line for portal ("can use it through the role grp, INSERT"); no line for runtime. A pure test pins this (`test_a_group_reached_by_two_named_roles_is_judged_for_each`, commit 1).
- S6 no grant option for a subject role that is not built in, on anything (`is_grantable`), the grant map included.
- S7 SECURITY DEFINER through everyone: a function outside the system schemas that is SECURITY DEFINER and that a subject, or everyone, may execute is refused, unless it is a member of an extension whose owner is not in the migration role family. A SECURITY DEFINER function of the family in another schema that only its owner may call passes (the old comparison refused it when it changed; said in the CHANGELOG).
- S8 named where nothing is read: every Q3 row of type `a` for a subject role must belong to a catalog that Q2 or Q4 reads (`pg_class`, `pg_proc`, `pg_namespace`, `pg_type`, `pg_database`, `pg_foreign_data_wrapper`, `pg_foreign_server`, `pg_language`, `pg_largeobject`, `pg_parameter_acl`, `pg_tablespace`, `pg_default_acl`). Any other catalog is a problem line "named in the access list of a kind of object this version does not read". This is the second, independent closure next to the self-check.

**Object side. For each object in the schema of the run that a role of the migration role family owns, and for the schema of the run itself whoever owns it.** AUTHOR ADDITION (rev 2, D-M6; 10.3 item 11): D-020 says "the objects the migration role family owns" without a schema limit; this ticket limits the object side to the schema of the run, option (b) of the design review. Reason: the promise table promises the named roles and everyone; on objects outside the schema of the run those two are judged in every schema by the subject side (S5-S7, D1-D2). What the limit leaves out is a right for a THIRD role (neither a named role nor everyone) on a family object in another schema, and an owner change to such a role there. Option (a), reading the object side in every schema, costs no extra statement (only the third clause of Q2's WHERE changes), but it would refuse every setup where the migration role also owns another application's schema whose own roles hold rights there, and whether that setup is supported is an owner question (10.3 item 5); with the default EXECUTE and USAGE for everyone it would also refuse every family function and type in every schema. Rev 2 does not take (a) without that answer. The generator cells C10 x E37 (third role) and C10 x "owner handed to a third role" are marked "not promised" (7.4), and the CHANGELOG says: "On objects outside the schema of the run, `migrate` judges what the three named roles and everyone can do, not what other roles can do."

- O1 allowed grantees: the owner, the migration role itself (also on an object a group owns: this is the round-12 false refusal), and the named roles as far as the table of 3.2 gives it. Any other role is a problem, kind `other_grantee`, built-in roles included. This rule is what protects a run with no role arguments.
- O2 nothing for everyone, with exactly two exceptions: USAGE on the schema of the run (the PostgreSQL 15 and later default of the `public` schema, `=U/pg_database_owner`, fact 34; it only lets a role look a name up), and USAGE on a row type (3.4 line 3, key of fact 33). CREATE or any other schema right for everyone is a problem (it falls under O7, which covers everyone, see below). R-B2.
- O3 no grant option for anyone but the owner and the migration role (the migration role may hold `USAGE ... WITH GRANT OPTION` on a schema it does not own; that is how the printed role of MIG:597-601 works).
- O4 SECURITY DEFINER only on the reviewed list. `REVIEWED_DEFINER_FUNCTIONS` becomes `frozenset[tuple[str, str, str]]` of (schema, name, identity arguments as `pg_get_function_identity_arguments` prints them); an entry whose schema is the constant `RUN_SCHEMA = ""` means the schema of the run. It stays empty. A unit test pins the key, and a real-server test (C-F9) shows that the same name in another schema, and an overload, are not excused.
- O5 STRUCK in rev 2 (D-M7). Rev 1 refused every other member of a group that owns a package object. That refuses a normal setup (`CREATE ROLE app_owner; CREATE ROLE mig LOGIN IN ROLE app_owner; CREATE ROLE alice IN ROLE app_owner;`) with no way out but removing colleagues from the group, and a named role in that group is already refused by S3. Other members of an owning group are not judged; 1.4 says so.
- O6 extension membership is no excuse: an object the family owns is judged the same whether or not it is a member of an extension. The rule has no condition in the code (there is simply no extension filter on family-owned objects), so it held whoever was right in the conflict of "Read first" item 5, which rev 2 settled (the installing role owns the extension). It matters in practice only for a migration role that owns an extension; fact 14 says how such a role can exist (CREATE on the database plus a trusted extension), and an administrator can also create the situation by installing an extension while switched to the migration role.
- O8 (rev 2, author finding while answering D-M6) owner of the package's objects: an object in the schema of the run whose name is a relation of the grant map or `schema_migrations` (`managed_relations`) or a function the files create (`managed_functions`) must be owned by a role of the migration role family, and (rev 3) so must the schema of the run itself, where `pg_database_owner` counts as family when the family owns the database (fact 34, F9); otherwise kind `foreign_owner`, no statement printed ("hand it back to the migration role, or drop it"), no extension excuse (O6). Without it, rev 1 lost the old refusal of a table that a file hands to a third role in the schema of the run (the object is no longer family-owned, so O1-O4 skip it, and the third role is not a subject). The kept step-1 check `_refuse_foreign_owned` says the same thing before any file with today's message; O8 makes it hold at all three calls. Handing an object to a group the migration role belongs to stays allowed (O5 struck; 1.4).
- O7 schema of the run: any right other than USAGE for a role that is not the owner and not the migration role is a problem, and "role" includes everyone (`CREATE` for everyone on `public`, the PostgreSQL 14 default, is refused). Same meaning as today's rule (MIG:1217-1225).

**Default rights (Q4):**

- D1 no default right for a subject role, whoever set it.
- D2 no default right for everyone on tables, sequences and schemas, whoever set it; on functions and types only the server's own entry for all schemas is accepted (`_BUILT_IN_DEFAULT`, MIG:1015, kept), an entry for one schema is refused.
- D3 for defaults set for a role of the migration role family: no grantee but that role and the migration role (today's rule, MIG:1004-1005).
- D4 a default-rights kind the code does not know (anything but `r S f T n`) is a problem line that names the letter and prints no guessed statement (this replaces `_DEFAULT_WORDS.get(kind, 'TABLES')`, MIG:1234).

**Extension members (rev 3, F12; owner question 10.3 item 13).** Fact 50: `pg_stat_statements` leaves two views readable by everyone, and an extension update writes the right back after a REVOKE. Rule E1, default taken (the stricter one, D-020 "no exception list"): an object that is a member of an extension the family does not own is judged like any other object (baseline line 2 refuses everyone's SELECT on such a view), but the problem gets `extension = <name>` and `by_hand = "extension"`: NO statement is printed, and the line ends "belongs to the extension <x> (owner <o>), not to this package; a REVOKE is undone by the next ALTER EXTENSION ... UPDATE; a database administrator decides (for example a database of its own for this package)". Alternative waiting for the owner (option b): such members are judged for the named roles only, not for everyone; it would cost one condition in `_judge`, its mutant and two tests. A clean control does NOT exist for (b) in this ticket; a cell "pg_stat_statements installed, shipped files" is in the expected-refusal list (7.4, control list note) so the default is pinned by a test (`test_an_extension_view_readable_by_everyone_is_refused_without_a_statement`, commit 3b). When `CREATE EXTENSION pg_stat_statements` is not possible on a test server, the test FAILS with the server's error (not a skip); it is available on 16.15 here and is part of the PostgreSQL contrib package of the CI image (the CI image claim is from the PostgreSQL docker image's documented contents, UNVERIFIED until the CI run).

**Grantor (rev 2, D-M5).** Every problem built from a Q2, Q1b or Q4 row carries the grantor. It decides the printed statement (4.2) and `repaired_by_run` (4.1 step 2). It never decides whether something is a problem: a right is judged the same whoever granted it.

### 3.4 The baseline: what everyone holds on every PostgreSQL server and how it is judged (printed in the CHANGELOG in these four lines)

1. System objects (schemas `pg_catalog` and `information_schema`): what everyone holds there is the server as shipped and is not judged. AUTHOR ADDITION: a grant there that names a named role itself, or a subject role that is not built in, is judged (fact 21 shows a fresh server has none outside built-in roles). A grant there to a built-in `pg_*` role is never its own line: the membership in that role is one S2 line (fact 38). No statement is ever printed against a system object (3.1). D-020 says "not judged" without this exception; see 10.3.
2. Kinds where everyone holds nothing by default (table, view, sequence, column, schema rights beyond what an administrator gave, CREATE on the database, large object, foreign server, foreign-data wrapper, tablespace, parameter): judged everywhere in the database. Any right there for a named role, for a role it belongs to, or for everyone, that the grant map does not give, is refused. USAGE on a schema is allowed (it only lets a role look a name up).
3. Kinds where everyone holds a right by default (EXECUTE on a function, USAGE on a type, a domain or a language):
   - on an object of the migration role family in the schema of the run, everyone gets nothing; `migrate` removes the default from the functions its files name, anything else is refused with the REVOKE statement printed. CORRECTION to D-020's wording: the row type that a relation carries is left out of this line (fact 11: every table of every database would be refused otherwise, and USAGE on a row type gives no access to the rows). Exact key (fact 33, D-m9, R-Mn5): `typtype = 'c' AND typrelid <> 0` and the relation's `relkind` is one of `r p v m f` (table, partitioned table and partition, view, materialized view, foreign table), which is Q2's column `row_type`. A sequence has no row type on 16. A standalone composite type (`CREATE TYPE x AS (...)`, relation `relkind = 'c'`), an enum, a range, a multirange, a domain and a base type are NOT row types and stay refused. A grant on a row type that names a subject role is still refused; the test makes that grant first, so the access list is written (`=U/owner` appears next to the grantee, fact 33) and the exception must still hold for everyone's entry.
   - a grant that names a subject role, anywhere, is refused;
   - everyone's default on other owners' objects is not judged, except rule S7 (SECURITY DEFINER).
4. On the database: CONNECT is expected. TEMPORARY for everyone is the server default; it is stated here and not judged (the owner may tighten this later). CREATE on the database is refused for a subject role and for everyone. An explicit TEMPORARY grant that names a subject role is refused (it is outside the map and removing it changes nothing while everyone has it).

### 3.5 Refusal below PostgreSQL 16

First read inside `verify`, and also in `migrate` right after the lock. Rev 3 (m1, M8; ran on 16.15, fact 48, p3c.out) reads the database owner in the same statement, `V2_SQL`: `SELECT pg_catalog.current_setting('server_version_num')::int, pg_catalog.pg_get_userbyid(d.datdba) FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()`. The owner from this read (never from Q2, which returns no database row when everyone's database rights were revoked) decides which closure gets `pg_database_owner` (Q1 note) and whether the `public` schema owned by `pg_database_owner` counts as family-owned (F9). The statement count of `verify` stays 8 (V2 replaces the version read). Below 160000: `ConfigError("this database server is PostgreSQL <version as the server prints it>; migrate needs PostgreSQL 16 or later (it reads who is a member of which role in the form that version 16 introduced). Nothing was changed. Run migrate against a server of version 16 or later.")`. The version text goes through `_label`. Placed before the first query that needs 16 (`inherit_option`, `set_option`).

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

Format (rev 3, M5): `KNOWN_ACL_COLUMNS: Mapping[str, tuple[str, str]]`, key `"<catalog>.<column>"` exactly as Q0 returns it (no prefix, for example `"pg_class.relacl"`), value `(query, fragment)` where `query` is `"Q2"`, `"Q4"` or `"none"` and `fragment` is a text that must occur in that query's constant: for `pg_class.relacl` the value is `("Q2", "c.relacl")`, for `pg_attribute.attacl` `("Q2", "a.attacl")`, for `pg_default_acl.defaclacl` `("Q4", "d.defaclacl")`, for `pg_init_privs.initprivs` `("none", "a record of the rights at install time; gives nobody a right")`. `test_every_live_acl_column_is_read_by_a_query` (commit 1) asserts, for each value whose query is not "none", that the fragment occurs in that constant AND that the catalog occurs there as `pg_catalog.<catalog>`; it replaces rev 2's "key with its prefix in the text", which could not match.

## 4. New order of `migrate`

### 4.1 The eight steps

| Step | What happens | On failure: message, error class, exit code of `hadavin-sdk migrate`, what is kept |
|---|---|---|
| 0 (unchanged, before connecting) | Argument checks, file names, ledger order, released-file fingerprints, `check_grants` with the new duplicate rule (6.4) | `ConfigError` or `MigrationNumberError`, exit 2. Nothing touched. |
| 1 | Connect, open the transaction, take the lock (6.1-6.2), the two time limits of `RECIPE_TIMEOUTS`, version refusal (3.5), `_refuse_privileged_role`, `_refuse_foreign_owned`, read `current_user`, `session_user` and `current_schema()` once into Python values (this one statement stays outside `pinned_read`, because `current_schema()` must see the run's own search path, as today at MIG:1603; it names no catalog table), create the ledger table if missing, read the ledger, late-file checks. Unchanged except the version refusal, the three values and the pinned reads (3.1). | `ConfigError`, exit 2. Rolled back; nothing kept. |
| 2 | `verify` before the first file. Problems with `repaired_by_run` are dropped here only. Those are exactly: (i) a right on a relation of the grant map in the schema of the run whose grantee is a named role itself AND whose grantor is the migration role (step 4's `REVOKE ALL` removes only what the migration role granted, fact 31; a right granted by anyone else is NOT repaired and stops the run here, D-m5); (ii) EXECUTE for everyone on a function that the step-4 query of 3.2 returns (step 4 removes it). Everything else stops the run. | `ConfigError` starting "before any migration file ran, this database already holds rights that the grant map does not give: ... Nothing was changed. No file ran. What to do: a database administrator runs the statements printed with each line (or removes the cause named there), then run migrate again." Exit 2. Nothing kept. |
| 3 | Each pending file, then the existing read-back after the file (`_check_read_back`, `_recheck_roles`), then the ledger row. Unchanged. The read-back stays because it names the file, which a state check cannot. | As today: `ConfigError` naming the file, exit 2, rolled back (with the existing sentence about a hidden COMMIT). |
| 4 | All writes of the runner itself: `_apply_grants(db, schema, role, ...)` per named role (schema from step 1); `REVOKE ALL ON ROUTINE ... FROM PUBLIC` for each row of the step-4 query (3.2). No runner write comes after this step. | A server error here (for example the lock limit on a busy table) is reported as today (`_limit_error`), exit 2, rolled back. |
| 5 | `step[0] = "running the deferred checks and triggers early"`, then `SET CONSTRAINTS ALL IMMEDIATE`. Checks and triggers that waited for the commit run now. | A lock or statement limit (55P03, 57014) goes to `_limit_error` as today (R-Mn7: the limit wins, the step name says where). Any other `psycopg.Error` is wrapped: `ConfigError("a deferred check or trigger failed when migrate ran it before the commit: <server message through _label>. Nothing was kept.")` (D-m4: it can be a foreign key, unique or exclusion check as well as a trigger), exit 2, rolled back. |
| 6 | Last statements before the commit: the read-back once more (session values, triggers of the schema, memberships, saved settings; so a trigger on the ledger that disabled the audit triggers is refused as a mistake), called as `_check_read_back(db, saved, END_OF_RUN, frozenset(), named)` with the constant `END_OF_RUN = "(after the last file and the grants)"` in the place of the file name (R-Mn6), `_recheck_roles(db, named, END_OF_RUN)`, then `verify` in full (nothing dropped), including the schema-USAGE check of 3.2. Nothing reads a user table. | `ConfigError` starting "after the migration files and the grants, rights that the grant map does not give are in place: ... The whole run is rolled back; the database is as it was before this run, unless a file ended the transaction itself (that is reported separately above). What to do: (1) if a migration file made it, remove that statement from the file; (2) if no file did, a database administrator runs the statement printed with the line; (3) run migrate again." Exit 2. |
| 7 | COMMIT (leaving the `with` blocks), wrapped (D-M3, fact 37; rule rewritten in rev 3, F5, fact 46). One pure function `_commit_outcome(exc, db) -> Literal["refused", "unknown"]` in `migrate.py` decides. | (a) "refused" ONLY when all four hold: the error has an SQLSTATE; `db.closed` is false; `db.info.transaction_status` is `IDLE`; and the SQLSTATE is in the allowlist `_COMMIT_REFUSED_STATES` = every code of the classes `22`, `23`, `40`, `42`, `44`, `P0` and the codes `55P03`, `55000`, `55006`, `57014` (errors a commit-time check or trigger raises while the server keeps the session; probed: 23503 fact 37a, 57014 fact 46 F2). Then the server rolled back. `ConfigError("the database server refused the commit (<SQLSTATE>: <message through _label>). Nothing was kept; run migrate again.")`, exit 2. (b) Everything else is "unknown": no SQLSTATE (fact 37b), any `08`, `57P0x`, `53`, `58`, `XX` code, any code outside the allowlist, a closed connection, or a status other than IDLE (probed: `pg_terminate_backend` gives 57P01, closed, UNKNOWN, fact 46 F1; a cut gives no SQLSTATE and the row WAS committed, fact 37b). `AppliedNotVerifiedError` with `commit_unknown = True` and the wording of 4.2, exit 5. Step 8 is not run in case (b). The allowlist errs towards "unknown": a refused commit outside it is reported as "may or may not have happened", which costs one more run of `migrate`, never a false "nothing was kept". Unit test `test_commit_outcome_classes` (commit 3a) pins every class above with faked exceptions; the real-server tests of 7.6 pin 23503, 57014 and 57P01. |
| 8 | A NEW connection through the same `connect(dsn, iam_auth=..., region=..., sslmode=..., sslrootcert=...)` with NO extra argument (D-M8, R-M1, fact 35: an `options=` keyword would replace a role switch inside the DSN, and `store/postgres.connect` does not take one); `db.isolation_level = REPEATABLE_READ`, `db.read_only = True`; then `verify` in full with the values of step 1 (its first statements pin the path and set the two limits, 3.1). The one statement `connect` itself sends before (`SET TIME ZONE 'UTC'`, store/postgres.py:148) looks no name up. Runs also when no file was pending: running `migrate` again is the way to re-check. Step 8 has no lock (D-m12): what another session grants after the commit is reported like any other excess. | ALL of step 8 sits in one `try`, outside the `try` that feeds `_limit_error` (MIG:1673-1676): ANY exception (a failed connect, a `QueryCanceled` from a role-level limit, the version or self-check `ConfigError`, a `psycopg.Error` such as an object dropped between two reads) becomes `AppliedNotVerifiedError` with the "could not run" wording of 4.2, exit 5, chained with `raise ... from e`. Problems found: `AppliedNotVerifiedError` with the list, exit 5. It never returns "applied" unless `verify` ran to the end and returned nothing. |

### 4.2 The failure after the commit

New class in `hadavin_sdk.errors`: `class AppliedNotVerifiedError(Exception)` with the attributes `applied: list[str]`, `problems: list[Problem]`, `statements: list[str]`, `could_not_run: str` ("" when the check ran) and `commit_unknown: bool`. It is deliberately NOT a `ConfigError`: a `ConfigError` means "refused, nothing happened" everywhere in this package (cli.py:19, exit 2). `cli._migrate` catches it, prints the message to standard error, prints every statement to standard output (one per line, nothing else on standard output, so `hadavin-sdk migrate ... > fix.sql` captures them; D-m3), prints no "applied" line, and returns exit code 5 (checked: no `return 5` in cli.py at 4d328e3d; 0 to 4 are taken). The module docstring of cli.py gets one line for `migrate` in the style of the other commands (R-Mn8), placed directly after the two-line `migrate` usage entry (cli.py:9-10 at 4d328e3d), indented like the `tick` exit-code line (rev 3, m12): `hadavin-sdk migrate ...   exit 0 applied and checked, 2 refused (nothing kept), 3 failure, 5 applied and committed but not verified (or the commit's outcome is unknown)`.

Exact wording on standard error (the bracketed parts are filled in; the first sentence is fixed):

```
The files are applied and committed; the database is over-privileged now; run these statements; run migrate again to re-check.
Applied in this run: <versions, or "no file (nothing was pending)">.
What is wrong (<n> things): <problem lines, at most 20, then "and N more">.
The <m> statements that remove them are printed on standard output, in the order to run them (all of them, not only the first 20).
<when some have no statement:> For <k> of them no statement is printed: <j> because a name holds a character that is not copied into a printed line, <i> because the object belongs to the server itself; a person decides those by hand.
migrate did not remove anything itself. Until a person has run the statements, the roles named above can do more than the grant map allows.
This check ran after the commit, on a new connection, as the migration role; what it found was made by this run or by another session since the commit. A file written to do harm can also cheat this check; see "What migrate promises" in CHANGELOG.md.
```

When step 8 could not run at all: first sentence "The files are applied and committed, but the check after the commit could not run (<reason through _label>), so nobody has confirmed that the roles hold only what the grant map gives; run migrate again to check."

When the COMMIT's outcome is unknown (step 7 b): first sentence "The connection was lost while the files were being committed, so the commit may or may not have happened, and nothing was checked afterwards; run migrate again: it applies the files that are not in the ledger and checks the database either way." `applied` lists the versions this run tried to commit, under the words "Tried to commit:".

How the statements are built (rev 3, M5): `statements_for(problems)` in the new module; each `Problem.fix` is built with `sql.Identifier` and `sql.SQL` and rendered with `as_string`; duplicates removed; order by `Problem.order` (3.1a; fact 30: a grant-option holder's dependents must go first): memberships, then default rights, then object rights granted by someone other than the owner (`grantor_is_owner` false), then object rights granted by the owner, then grant options, then flags, then SECURITY DEFINER changes. `migrate()` builds the message from `[p.line() for p in problems]` cut by `_shown`, and `statements_for(problems)` uncut.

Which statements are printed where (rev 3, M5 last point): at exit 5 every statement goes to standard output, all of them. At exit 2 (steps 2 and 6, a `ConfigError`) there is no standard-output block: the message holds at most 20 problem lines, each with its own statement, then "and N more lines; run the statements above, then run migrate again to see the rest". The rev 2 words "all of them, not only the first 20" apply to exit 5 only.

Statements for objects that are not this package's (rev 3, F11). A problem with `outside_package` true (the object is outside the schema of the run, or its owner is not in the family) starts its line with "NOT THIS PACKAGE'S OBJECT: " and ends "confirm with the owner of <schema.name> (<owner>) before running the statement; another application may need this right". At exit 5 its statement is printed in a SECOND block on standard output, after a comment line `-- NOT THIS PACKAGE'S OBJECTS: confirm each with its owner before running`; the first block holds only statements on the package's own objects and on the named roles' memberships and flags. The standard-error text says how many statements are in each block. `test_a_right_on_another_applications_table_is_marked_and_printed_apart` (commit 3b) pins both the line and the two blocks. An extension member (rule E1) prints no statement at all.

Forms, each checked against facts 30-32 and 48-49:
- object right, grantor is the owner: `REVOKE <right> ON <KIND> <schema.name> FROM <role or PUBLIC>;` (a superuser acts as the owner); column right `REVOKE <right> (<column>) ON TABLE <schema.name> FROM ...;`
- object right, grantor is another role G: `SET ROLE <G>; REVOKE <right> ON <KIND> <schema.name> FROM <role>; RESET ROLE;` on one line (fact 30, a16). `REVOKE ... GRANTED BY` is NOT used for objects ("grantor must be current user").
- a grant option: one statement PER GRANTOR of the option (Q2 returns one row per grantor): grantor is the owner: `REVOKE GRANT OPTION FOR <right> ON <KIND> <schema.name> FROM <role> CASCADE;`; grantor is another role G: `SET ROLE <G>; REVOKE GRANT OPTION FOR <right> ON <KIND> <schema.name> FROM <role> CASCADE; RESET ROLE;` (rev 3, F9, fact 49: the superuser's plain form leaves the option from G and its dependents). Printed after the dependents above, so CASCADE removes nothing that was not already listed; the line says "also removes what <role> passed on".
- `pg_database_owner`: no statement (fact 48: REVOKE does nothing and only warns); by hand "this role owns the database; hand the database to another role".
- membership: `REVOKE <group> FROM <member> GRANTED BY <grantor>;`, always with `GRANTED BY` (fact 32: without it a superuser's REVOKE of a membership granted by a CREATEROLE role does nothing and only warns).
- default right: `ALTER DEFAULT PRIVILEGES FOR ROLE <set_for> [IN SCHEMA <s>] REVOKE <right> ON <KINDS> FROM <grantee>;`
- flag: `ALTER ROLE <r> NO<FLAG>;`
- SECURITY DEFINER: `ALTER FUNCTION <schema.name>(<identity arguments>) SECURITY INVOKER;` (the word is `PROCEDURE` for a procedure).
- owner problem: no statement is guessed; the line says "hand it to the migration role or drop it" and counts as by hand.
- an object of `pg_catalog` or `information_schema`: never a statement (3.1).

A test executes every printed statement as a superuser on the test server and then asserts that `verify` returns nothing (the statements are right and complete). The test cases include grantor = owner, grantor = a grant-option holder (table and column), a grant option held from two grantors (fact 49), and a membership granted by a CREATEROLE role (facts 30-32). Problems that are by hand (name, system, database owner, extension, owner) are excluded from "returns nothing" and listed by the test.

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
| `effective_problems` | MIG:295-372 (`_TABLE_PRIVS` starts at 283, `_no_duplicate_names` at 374) | REMOVED (decided in rev 2, R-Mn1: its only callers outside `migrate()` are the three TW tests retired in 5.4). The subject side of `verify` replaces it. Main's version (main migrate.py:193-262) is the reuse base of the idea (what the role can do against the map), now all schemas, all kinds, memberships, 8 statements instead of one per role x relation x right x column. |
| Access-list queries | MIG:909-1006 | `_ACL_RELATION_SQL`, `_ACL_FUNCTION_SQL`, `_ACL_OWNER_SQL`, `_ACL_SCHEMA_SQL`, `_ACL_DEFAULT_SQL` are replaced by Q2-Q4. They lose the inputs `changed_*`, `kept_*` and `judged`; default rights are selected by grantee. |
| `_refuse_unlisted_grantees` | MIG:1098-1254 | Its loops become `_judge`; the REVOKE of everyone's EXECUTE moves to step 4; the function is removed. |
| `REVIEWED_DEFINER_FUNCTIONS` | MIG:821-824 | Key (schema, name, identity arguments), rule O4. |
| `_apply_grants` | MIG:260-280 | Takes `schema` as an argument (read once at step 1) instead of `SELECT current_schema()` at MIG:263. |
| `_label` | MIG:1364-1366 | Moves to `migration_numbers.py`; `migrate.py` imports it back (3.1). |
| `_routine_name` | MIG:1101-1106 | Replaced by `sql.Identifier(schema, name)` plus the argument text, the form MIG:784 already uses. |
| Order of `migrate` | MIG:1579-1672 | Section 4. Lines 1607 and 1662-1663 go; 1624-1661 shrink to the three `_apply_grants` calls. |
| Catalog names | every query that stays in MIG (304-365 goes; 432-477, 609-627, 669-684, 1257-1271) | `pg_catalog.` in front of every catalog table and function, no bare `'pg_class'::regclass`. A repository test greps the SQL constants of `MIG` and the new module for a catalog name without the prefix. |
| Module docstring, `migrate` docstring, CHANGELOG | MIG:1-78, 1524-1554, CL:6-34 | Promise table first; section 1.5; section 9.3. |

### 5.3 Delete, with the written reason

Deleted: `_TABLE_PRIVS`, `_SERVER_VERSION_SQL`, `_MAINTAIN_FROM`, `_table_privs` and `effective_problems` (MIG:283-372), `_SCHEMA_USAGE_SQL` (MIG:694, its only use MIG:1665 moves into `verify`), `_NOT_SYSTEM_PARTS` entries `@ME@`, `@MINE@`, `@ITEM@` and `_sql` (MIG:826-848, as far as nothing kept uses them), `_IN_SCOPE`, `_OWNER`, `_FUNCTION_FIELDS`, `_FUNCTION_STATE_SQL`, `_RELATION_FIELDS`, `_RELATION_STATE_SQL`, `_SCHEMA_FIELDS`, `_SCHEMA_STATE_SQL` (MIG:851-908), `_Objects`, `_objects`, `_Changed`, `_changed_ids`, `_kept_owner_ids`, `_changed_since` (MIG:1026-1095), `_NO_RIGHT_OUTSIDE` (MIG:1098), the calls at MIG:1607 and 1662.

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
- `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind` (rev 2: it hands objects of a SECOND schema to a group the migration role belongs to; that is outside the object side (3.3, D-M6) and is a group owner, which rev 2 allows (O5 struck); its run-schema form lives on in the re-pointed `test_an_owner_handed_over_in_the_run_schema_is_refused`)
- `test_with_the_printed_role_an_owner_handed_over_is_the_one_cause_of_the_refusal` (rev 2: it hands a table to a group the migration role belongs to; allowed after O5 is struck; its wording pin moves to the third-role form below)
- `test_a_function_that_kept_a_foreign_owner_is_not_refused_for_that_owner` (replaced by two clean controls of 7.4: a group-owned database where the migration role is the only member, and E27, a group with a second member; both must end in (iii), because rule O5 is struck in rev 2)
- `test_a_schema_that_a_file_changed_and_that_kept_its_owner_is_not_taken_for_handed_over` (same)
- `test_a_function_whose_body_a_file_replaced_is_treated_as_changed`
- `test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function`
- `test_what_another_session_commits_during_the_run_does_not_stop_the_run` (replaced: another application's objects that give the named roles and everyone nothing do not stop the run; ones that do, stop it)
- `test_a_change_by_another_session_to_a_table_of_the_migration_role_is_refused_and_the_message_names_that_cause` (replaced by the after-commit test of 7.6)
- `test_a_security_definer_function_that_is_not_the_migration_roles_or_not_in_the_run_schema_is_left_alone` (replaced by a test of rule S7 in both directions)

Rev 3 (F6): why each retired TPG test goes. "Code gone" = the code it tested is deleted and the rule lives on elsewhere; "refusal dropped on purpose" = it pinned a REFUSAL that the new design ALLOWS; the lead signs each of those off in handover/AUTONOMOUS-DECISIONS.md before commit 3b is pushed, and 9.1 item 24 counts them as deliberate, not as weakened tests.

| retired test | why | tied to |
|---|---|---|
| `test_a_function_of_another_application_owned_by_the_migration_role_is_left_alone` | code gone; the new design is STRICTER here (refused) | 3.4 line 3 |
| `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind` | refusal dropped on purpose (group the migration role belongs to; other schema) | 10.3 items 3 and 11 |
| `test_with_the_printed_role_an_owner_handed_over_is_the_one_cause_of_the_refusal` | refusal dropped on purpose (group handover allowed) | 10.3 item 3 |
| `test_a_function_that_kept_a_foreign_owner_is_not_refused_for_that_owner` | code gone; replaced by two clean controls | 10.3 item 3 |
| `test_a_schema_that_a_file_changed_and_that_kept_its_owner_is_not_taken_for_handed_over` | code gone | - |
| `test_a_function_whose_body_a_file_replaced_is_treated_as_changed`, `test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function` | code gone (no change comparison); a function's settings are not rights (1.4) | 1.4 |
| `test_what_another_session_commits_during_the_run_does_not_stop_the_run`, `test_a_change_by_another_session_to_a_table_of_the_migration_role_is_refused_and_the_message_names_that_cause` | code gone; replaced (state is judged whoever made it) | 7.6 |
| `test_a_security_definer_function_that_is_not_the_migration_roles_or_not_in_the_run_schema_is_left_alone` | refusal dropped on purpose for one case (a family SECURITY DEFINER function in another schema that only its owner may call passes), STRICTER for the rest (S7) | 3.3 S7, 9.5 |

Rev 3 also notes: a schema of the run handed to a third role is NOT covered by O8 (O8 matches managed relation and function names). Rev 3 adds it to O8: the schema of the run itself must be owned by a role of the family or by `pg_database_owner` when the family owns the database; otherwise kind `foreign_owner` (design review round 2, section (5)). An unmanaged table a file creates and hands to a third role in the schema of the run is judged by O1 only if the family still owns it; once handed over it is NOT judged: added to 1.4 as a non-promise.

`TPG`, kept with the same intent and re-pointed at the new message and, where it applies, the new place of refusal (the builder lists old name -> new name in the notes): `test_a_right_given_on_a_table_that_existed_before_the_run_is_refused`, `test_a_second_right_on_a_column_that_already_had_one_is_refused`, `test_a_right_given_on_a_table_of_another_schema_is_refused`, `test_an_owner_handed_over_in_the_run_schema_is_refused` (rev 2: the new owner becomes a THIRD role that the migration role does not belong to, parametrised over table, view, sequence and function, refused by O8; killer of OW5, OW6), `test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is`, `test_a_foreign_table_that_a_file_opens_to_everyone_is_refused`, `test_a_right_that_a_named_role_may_pass_on_is_refused_on_a_table_of_the_grant_map`, `test_a_named_role_that_may_pass_the_schema_right_on_is_refused`, `test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map`, `test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to`, `test_a_named_role_that_may_pass_a_function_right_on_is_refused`, `test_the_database_owner_pseudo_role_is_refused_on_a_schema_it_does_not_own`, `test_a_named_role_with_the_replication_flag_is_refused`, `test_a_security_definer_function_of_the_migration_role_that_no_file_made_is_refused`, `test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers`, `test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types`, `test_a_named_role_gets_no_right_on_a_function`, `test_a_function_that_is_called_like_a_table_of_the_grant_map_is_not_this_packages`, `test_a_named_role_that_can_read_a_foreign_table_in_the_run_schema_is_refused`, `test_the_portal_role_is_refused_what_the_other_roles_are_refused`, the two remaining `test_with_the_printed_role_...` / `test_the_printed_role_runs_...` tests (the third is retired above).

`TW`: `test_the_maintain_privilege_is_asked_about_from_postgresql_17_only`, `test_a_maintain_grant_is_a_problem_on_postgresql_17`, `test_the_portal_role_is_asked_about_every_table_privilege_the_other_roles_are` (TW:1196-1235; TW:1227 reads `_TABLE_PRIVS`) answer `effective_problems` by exact query text with a faked server. They are retired: `verify` reads the access lists, where MAINTAIN on 17 is one more item with no version branch. The CI run on 17 (acceptance 19) replaces the faked version. CORRECTIONS to rev 1 (citation list A of the readiness review): `test_migrate_refuses_a_changed_released_file_before_it_connects` (TW:1244) does not mention `changed_rel` and needs no re-pointing; TW:192 and TW:208 sit in the helper of `_READBACK_TRIGGERS_SQL`, which is kept, so nothing there goes.

### 5.4b Tests outside rev 1's lists (rev 2, R-M3), each named

1. **Fake-database wiring tests in TW that drive `migrate()` with scripted answers.** Through the helpers `_run` (TW:163), `_refused_by` (TW:884) and `_run_raising` (TW:1355), or directly: `test_migrate_executes_the_text_it_scanned`, `test_a_privileged_migration_role_is_refused_before_any_file_runs`, `test_a_role_that_is_a_member_of_a_privileged_role_is_refused_before_any_file_runs`, `test_a_privileged_session_user_is_refused_even_when_the_current_user_is_plain`, `test_a_parameter_grant_is_refused_before_any_file_runs`, `test_a_server_without_parameter_grants_is_not_asked_about_them`, `test_the_refusal_says_how_to_make_a_plain_migration_role`, `test_the_roles_are_asked_again_after_every_file`, `test_the_replication_flag_is_read_again_after_every_file`, `test_the_named_roles_are_checked_against_each_other_after_every_file`, and the four released-list tests `test_migrate_refuses_when_the_released_list_is_unreadable_or_wrong`, `test_the_released_check_looks_at_the_files_migrate_runs_not_at_the_folder`, `test_a_bad_hash_in_the_released_list_is_a_config_error_not_a_changed_file`, `test_a_json_name_written_twice_in_the_released_list_is_refused` (these four and `test_directory_named_like_a_migration_is_refused`, `test_commit_in_a_file_is_refused_before_connecting` stop before connecting; they are listed so the builder confirms they still pass unchanged). Rule: the fake `_Db` gets one shared answer helper that answers the new statements (the savepoint and `SET LOCAL` lines of `pinned_read`, Q0 to Q4, the version read, the step-4 query) by the constants imported from `migration_verify`, with the answers of a clean database; a test that wants a problem overrides one answer. Each listed test keeps its assertion word for word; only scripted answers change. Every mutant that these tests kill (MW1, S2, S3, S4, S5, B1, SU1, PA1, RC2, RF1, R7, and the users of `READS_BEFORE` and `WIRING_VAL`) must still be killed (5.5 group "re-checked").
2. **tests/test_k2_migrations.py** (13 tests, 12 call `migrate`, 2 patch `connect`): all keep their assertions except `test_migrate_refuses_a_portal_role_that_inherits_write_rights` (killer of PC1, PT1), whose expected message words change from "the portal role has privileges outside the portal grant map" to the new problem line of kind `right` ("... can use it through the role ..."). The two `connect` patches must answer a second call (step 8 opens a new connection). `test_migrate_refuses_roles_that_are_members_of_each_other` keeps today's sentence: the kind `named_roles_overlap` prints "the runtime, portal and purge roles must not be members of each other" unchanged. `test_cli_migrate_passes_the_portal_role` (killer of CL1, CL2) is unchanged.
3. **CHANGELOG and docstring pins in tests/test_migration_rules.py**, rewritten in the texts commit (9.3 commit 6), each named: `test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim` (TR:672-715: the asserts on the MAINTAIN sentences and on "Refused: rights for any other role, owners a file handed over, ..." are replaced by asserts on the new sentences; the asserts on the released file, REPLICATION, "CREATE has no grant option", "an existing trigger left disabled", "`REVIEWED_DEFINER_FUNCTIONS`", `session_user`, `WITH GRANT OPTION`, `pg_parameter_acl`, "PostgreSQL 16 is the lowest version", "the role memberships", "inside a function body" stay, with the new text written to keep them true; mutant R23 is re-pointed with it), `test_the_scope_the_order_and_the_file_own_limits_are_written_down`, `test_every_timeout_value_written_in_the_docs_is_the_constants`, `test_case_f_says_migrate_has_the_same_limits_as_the_hand_file`. Docstring phrases that MUST survive the rewrite of 1.5 and 9.3: `RECIPE_TIMEOUTS` and `pg_auth_members` (module docstring and `migrate` docstring), "so a run with no pending file is covered too", "sets the limits BEFORE the advisory lock", "AFTER it, on purpose", "A migration file may not change either limit". `_upgrade_bullet()` (TR:666) cuts from "- **Migrations: stricter checks" to the next top-level bullet: the new "What migrate promises" text is a NESTED part of that bullet (indented two spaces), never a new top-level bullet, so the cut still covers it.
4. **The skip rule.** `test_no_migration_test_skips_silently` (TR:158, rule at TR:87-130) allows `pytest.skip` only under `if not DSN:`. Rev 1's 6.3 would have broken it; 6.3 is changed (a failure, no skip). The new test files are added to `MIGRATION_TEST_FILES` (TR:28).
5. TPG:2804's patched value of `REVIEWED_DEFINER_FUNCTIONS` changes to the tuple key (3.1); TR:704 keeps finding the name `REVIEWED_DEFINER_FUNCTIONS` in the CHANGELOG.

### 5.5 Retired, re-pointed and re-checked mutants (ids from `MUT` at 4d328e3d: 288 entries, 279 written as `Mutant(...)` plus 9 made by `cmp_mutant`; the rev 2 mapping is in handover/evidence/P3a-2/plan-r2/mutclass.out)

Retired (the planted line is in deleted code and the rule it guarded no longer exists as a rule): SD3, SD4, SD5, RN6, OW3, OW4, OW7, OW8, RA1, RA1b, FB1, FB2, FB3, SO1, SO2, SO3, CS1, CS2, CS4, CS5, KC1, KC2, KC3, SC10, SC11, SD9, WD1, and (rev 2) MT1 and MT2 (MUT:1210-1225, planted in `_MAINTAIN_FROM` and `_table_privs`, killer `test_the_maintain_privilege_is_asked_about_from_postgresql_17_only` retired). 29 ids.

Re-pointed (the rule lives on; the mutant gets a new planted line, in the new module or the rewritten text, and a killer that exists in the same commit): AC1, AC2, AC3, AC4, AC5, SD1, SD2, SD6, SD7, SD8, DP1, DP2, DP3, DP4, DP5, DP6, DP7, DP8, DP9, SC8, SC9, SC12, SC13, SC14, GO4, GO5, GO6, RO1, RO3, RO4, RO5, RA2, RA4, IM1, RK1, RK2, RF5, OW5, OW6, OW9, MC2, PDO2, PC1, PT1, GO2 (45 ids from rev 1), plus (rev 2) R23 (planted in CL:10, which is rewritten; killer the rewritten TR test) and SH1 (planted in `_shown`, kept; its killer `test_a_long_list_is_cut_with_a_count_of_what_was_left_out` is rewritten against `_judge`, so the killer name is re-checked). 47 ids. RA2 and RA4 change meaning from "only the schema of the run" to "only the schema of the run is read on the SUBJECT side" and must now be killed by a right in another schema.

Re-checked, no edit to the mutant (its killer is a test whose scripted answers or expected words change in 5.4b): MW1, S2, S3, S4, S5, B1, SU1, PA1, RC2, RF1, R7, CL1, CL2, GM1, MC1, OA4. 16 ids. Each must still be KILLED after commit 3.

Unchanged: the rev 1 list (M61, M64, M67, M95, MW2-MW6, N15, T13, S1, O1, R6, RC1, LV1-LV4, LW4; the lock mutants MW8, LW1-LW3, LW5-LW8, where LW7 and LW8 get the new join as planted text) and every other id. Rule for the builder: every mutant whose planted text sits inside `migrate()` (MIG:1512-1677) is checked by `problems_with_the_list()` at every commit (it is part of the per-commit green command); one whose text no longer exists exactly once is re-pointed with the same intent in that commit and added to the builder notes table.

`problems_with_the_list()` (MUT:2997-3016) is changed to check the parametrised id of a killer as well (today it strips it at `split("[")[0]`). Commit 5 (rev 3, M1/m11).

**Rev 3 closure of the lists (M7, fact 50).** The script handover/evidence/P3a-2/plan-r3/scripts/affected_mutants.py read both mutant lists of the 4d328e3d tree (288 + 40, every `old` text exactly once) and intersected each planted text's line span with the line ranges rev 3 plans to edit (the ranges are written in the script, one per row of 5.2, 5.3, 6.1-6.2, 1.5 and the cli change, each with its commit). Result (affected_mutants.out): 106 overlap; the per-commit list is in that file. Classification, closed:
- Retired: the 29 of rev 2 (all 29 are in the overlap; unchanged).
- Re-pointed: the 47 of rev 2.
- Re-checked, rev 2: the 16 (they overlap nothing; their killers change).
- Re-checked, NEW in rev 3 (in the overlap, in no rev 2 list): at commit 3a M102 (MIG:476, `current_schema()` becomes a parameter); at commit 3b LV1, LV2, LV3, LV4, LW4, N15, MW2, MW3, MW4, MW5, MW6, M61, M64, M67, M95, T13, RC1, S1, O1, R6 (all inside `migrate()`, MIG:1550-1621); at commit 4 LW1, LW2, LW3, LW5, LW6, MW8, and LW7, LW8 re-planted on the new join; at commit 6 P8 (MIG:26, module docstring). 30 ids. For each: if its `old` text still occurs exactly once after the commit, it is run and must be KILLED in that commit; if not, it is re-pointed with the same intent in that commit and listed in the builder notes.
- Re-checked at commit 6 because the CHANGELOG is rewritten around them (planted outside the rewritten lines, but the new nested text could repeat a planted text): N16, N17, N18, N19, P1, P2, P3, P5, P6, P7 (10 ids, plus R23 re-pointed).
- `tests/migration_numbers_mutants.py` (40): none overlaps the two comment edits of 1.5 (MN:677-679, 722-723); `_label` is inserted, not edited. Rule below still applies.
- The `pg_catalog.` prefix edit of kept MIG queries is dropped (3.1), so M102's neighbours T2-T5, R4, SC1, SC2, NR2, NS1, NS2, NM1, R2, PS1, SC5, PA2-PA4 and the FO/OW mutants of MIG:669-684 do not move, except where a range above covers them.

**Rule that closes the list for edits the plan did not foresee (per commit, part of G).** Before each commit the builder runs `affected_mutants.py` adapted to `git diff -U0 <parent>` (the script takes ranges; the builder notes paste the ranges from the diff hunks of every changed file under `src/`, `CHANGELOG.md` and `tests/` files named in `MUT` or `migration_numbers_mutants.py`). Every id it lists that is not retired is run in that commit (`python tests/migrate_mutants.py <ids>` or `python tests/migration_numbers_mutants.py <ids>`) and must be KILLED; `test_every_migrate_mutant_still_applies_to_the_source` covers "old text exactly once" for all ids.

**Where batch 2 lives (M7).** From commit 3a: a constant `BATCH_2_IDS: frozenset[str]` in `tests/migrate_mutants.py` = the 47 re-pointed + the 16 + the 30 rev 3 re-checked (minus retired) + LW7, LW8 (as they exist at each commit; ids not yet re-planted are skipped by the runner with a printed line, never silently). `--list-batch` (commit 5) uses it; a unit test asserts the four batches are disjoint and cover the list.

Count after this ticket: 288 - 29 retired + 54 new (7.5; the duplicate-CREATE mutant left with 6.4, rev 3) = 313.

### 5.6 What happens to each round-12 finding

Design review (r12-design-full.md):

| Finding | Result |
|---|---|
| F1 deferred trigger at commit | Usual case: stopped at step 5/6 (rows 1 and 2 of the promise table). A trigger that defers itself again (fact 4): detected at step 8 (row 3). Covered by generator carriers C6 and C6b. |
| F2 trigger on the ledger | Privilege variant: falls away by order (all runner writes come before the last check). Variant that disables the audit triggers: refused by the read-back at step 6 as a mistake, pinned by the dedicated test `test_a_ledger_trigger_that_disables_the_audit_triggers_is_refused_at_the_end_of_the_run` (7.6, D-m11); against a harmful file not promised (1.4, code left behind); "required audit triggers present" is split ticket B. |
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
| C-F9 reviewed list by bare name | Fixed by O4; a unit test pins the key and the real-server test `test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments` (7.6, D-m11) shows that the same name in another schema and an overload are refused. |
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

### 6.3 The real-server test runs or fails visibly (rev 2: no skip)

`test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one` (TPG:4499) returns early at TPG:4520 when `max_prepared_transactions` is 0, and is reported as passed. New behaviour: when `HADAVIN_TEST_PG_DSN` is set and the server says `max_prepared_transactions = 0`, the test FAILS with `pytest.fail("this server has max_prepared_transactions = 0; the prepared-transaction test cannot run. Start the test server with -c max_prepared_transactions=10.", pytrace=False)`, on a developer machine and in CI alike. Rev 1 proposed a `pytest.skip` outside CI; that breaks the repository rule `test_no_migration_test_skips_silently` (TR:87-130 allows a skip only under `if not DSN:`), so rev 2 takes the stricter form (R-M3 item 4). The test gains a second prepared transaction that does not hold the lock and asserts it is NOT named.

CI (R-Mn4): `.github/workflows/ci.yml` lines 40-47 and 110-117 start `postgres:17.10@sha256:7958...` as a GitHub service container, which takes no command, and `options:` passes flags to `docker create`, not to postgres. First route to try: one workflow step right after the services are up, in both jobs: `docker exec ${{ job.services.postgres.id }} psql -U postgres -c "ALTER SYSTEM SET max_prepared_transactions = 10"`, then `docker restart ${{ job.services.postgres.id }}`, then wait until `pg_isready` answers (bounded: at most 30 tries, 2 s apart), then `psql ... -Atc "SHOW max_prepared_transactions"` printed to the log. Second route if the first fails: replace the service by a `docker run -d ... postgres:17.10@sha256:... -c max_prepared_transactions=10` step with the same image digest. The builder pastes the CI log line with `10` and states which route worked. The other early return the rev 1 text named, TPG:242, is NOT such a case: it is the plain `return` after `yield` in the context manager `_plain_role_may_set` (citation list A, item 3); nothing changes there.

### 6.4 MOVED OUT in rev 3 (F8): `_scan` refusing a second CREATE of a grant-map name goes to split ticket C

Reason: it is a text rule for accidents, which 10.1 says not to build in this round; `verify` already judges a moved-and-recreated table by construction (map matched by schema, name and kind; carrier C13). Leaves this ticket with it: its mutant (7.5, count 313), `test_a_grant_map_name_created_twice_is_refused`, the `_scan` half of acceptance 17, the 6.4 entry of step 0. The rev 2 text stays below for split ticket C, struck:

~~In `_scan` (MIG:232-237): when `name` is already in `found`, append `f"{path.name}: {name} is created a second time (the first time in {first_file}); a table of the grant map is created once"`. Applies to every relation name the scan reads, across files and inside one file. `CREATE OR REPLACE VIEW` of the same view in a later file is the one form that may repeat (the scan knows the form). This is a text rule for accidents; it carries no security claim. Data shape (R-Mn3): `_scan` keeps its dict `found: name -> kind` exactly as it is (`check_grants` iterates `created.items()` as `(name, kind)`), and tracks the first file in a second dict `first_file: name -> file name` used only for the message.~~

### 6.5 Test hygiene for surviving tests

Every surviving real-server test that creates a role creates it inside the `try` whose `finally` drops it (the three tests the code review names: `test_with_the_printed_role_the_schema_and_default_right_checks_hold` (the first of the three the code review named is retired in rev 2, 5.4), and the replacement of `test_what_another_session_commits...`). The new generator uses one fixture that owns all roles, schemas, large objects and prepared transactions of a case and removes them in `finally`; a session-end check asserts that no role with the test prefix is left.

## 7. Test design (real server only for every decision; pure-function tests only pin message words)

Test files (rev 2 names, R-M4): `tests/test_migration_verify.py` (pure `_judge` tests and repository checks, no server), `tests/test_migration_verify_pg.py` (dedicated real-server tests of 7.6), `tests/test_migration_matrix.py` (oracle, sensitivity controls, generator), `tests/fixtures/oracle.py` (the oracle). The three test files are added to `MIGRATION_TEST_FILES` (TR:28), so the skip rule and the early-return rule (7.8) cover them.

### 7.1 The closed property

For every generated case, exactly one of these holds, and the test asserts which:
- (i) REFUSED: `migrate` raised `ConfigError` before the commit, and the oracle's answers after the run equal its answers before the run;
- (ii) NOT VERIFIED: `migrate` raised `AppliedNotVerifiedError`, and every excess the oracle finds is named in its problem lines, with the problem kind the effect table (7.3) gives for that effect;
- (iii) APPLIED: `migrate` returned, and the oracle finds no excess for any named role, for a fresh role that stands for everyone, and (in the schema of the run only, rule O1) for any other role the case created.

Forbidden, and the reason the suite exists: `migrate` returned and the oracle finds an excess. The assertion message for that case starts with the fixed words "applied with excess:" (7.9 greps for them).

### 7.2 The oracle (rev 2: environment decided, D-M1, R-M2)

**What it may read.** A separate connection as the test server's superuser. It shares no query and no helper with `src/`. It lists objects by name and kind only: `pg_class` (name, `relkind`), `pg_attribute` (column names), `pg_proc` (name, argument types through `pg_catalog.format_type`, `prokind`, `prosecdef`), `pg_namespace`, `pg_type` (name, `typtype`), `pg_largeobject_metadata` (oids), `pg_roles` (names and the five flags). It reads no access list and no membership table. Repository test `test_the_oracle_shares_nothing_with_the_code_under_test` (in test_migration_matrix.py) asserts that `tests/fixtures/oracle.py` imports nothing from `hadavin_sdk` and that this whole-word pattern finds nothing in its text: `\b(acl|aclexplode|aclitem|acldefault|relacl|attacl|proacl|nspacl|typacl|datacl|fdwacl|srvacl|lanacl|lomacl|paracl|spcacl|defaclacl|initprivs|pg_auth_members|pg_shdepend|pg_default_acl|pg_has_role|has_\w+_privilege)\b` (whole words, so "oracle" does not match).

**Superuser or failure.** The fixture `oracle_db` connects with `HADAVIN_TEST_PG_DSN` (autocommit) and reads `rolsuper` of `session_user`. Not a superuser: `pytest.fail("the oracle needs a superuser login in HADAVIN_TEST_PG_DSN (SET SESSION AUTHORIZATION needs it); this is a failure, not a skip", pytrace=False)`. DSN not set: the module carries `pytestmark = pytest.mark.skipif(not DSN, reason="HADAVIN_TEST_PG_DSN is not set")`, the one form the skip rule allows.

**Scope: one database per case.** Every generated case and every dedicated real-server test that judges the whole database runs in its own database, `hadavin_test_m<pid>_<n>`, made by the fixture with `CREATE DATABASE ... TEMPLATE template0` and dropped in `finally` with `DROP DATABASE ... WITH (FORCE)` (measured on 16.15, idle: median 24 ms for create plus drop, handover/evidence/P3a-2/plan-r2/createdb_cost.out). So other tests' scratch schemas, other processes' plain roles and a parallel mutant run cannot change what `verify` or the oracle sees in that database. Roles are server-wide: every case's roles carry the prefix `hadavin_test_m<pid>_<n>_`, are dropped in `finally`, and a session-end check asserts that none with the test prefix is left. Only roles reached from the case's own named roles count, so another test's roles cannot enter a case. Two kinds of object are server-wide, not per database: parameter rights (`pg_parameter_acl`) and tablespaces. Every case takes `pg_advisory_lock_shared(K)` on the `postgres` database for its whole run; the cells of E24 and E25 take `pg_advisory_lock(K)` (exclusive), so no other case runs while they hold a server-wide right.

**Fixture variants** (rev 1 named them without defining them): (P) plain: the database is owned by the DSN superuser and the case's migration role owns only the schema of the run (as `plain_role_connect` does today); (O) the migration role owns the database (`CREATE DATABASE ... OWNER <migration role>`); (C) the migration role holds CREATE on the database (`GRANT CREATE ON DATABASE ... TO <migration role>`); (T) like (P), and the fixture has run `REVOKE TEMPORARY ON DATABASE ... FROM PUBLIC`, so that E19 becomes visible by behaviour; (U) (rev 3) like (P), and the fixture revokes everyone's USAGE on `plpgsql` and on the case's own types, so that E20 and E21 become visible; (T) no longer revokes the type or language right, and (U) keeps TEMPORARY (design review round 2, F1). The case's migration role is a LOGIN made with the existing helpers `create_login_role` and `login_dsn` (tests/fixtures/migration_role.py; a password built at run time, never written in the source); the tests carry the marker `real_connect`, so the autouse swap of tests/conftest.py:94-108 does not apply.

**How an attempt is made and classed.** The oracle becomes the role with `SET SESSION AUTHORIZATION <role>` (fact 18) and runs `RESET SESSION AUTHORIZATION` before the next role. Each attempt runs inside its own savepoint, rolled back whatever happens (the shape probed in rev 3, scripts/p3.py `attempt`). Classes: no error = allowed; 42501 = refused; one of these codes, which PostgreSQL raises only AFTER the privilege check = allowed: 23502, 23503, 23505, 23514; 0A000 with "trigger functions can only be called as triggers", "cannot truncate a table referenced in a foreign key constraint", or "cannot insert into / update / delete from foreign table" (fact 44: 42501 comes first without the right); 42809 with "cannot change materialized view" (fact 43: 42501 comes first without the right); a GRANT attempt that ends with the warning "no privileges were granted" = refused (E16, E26). The oracle sets `lc_messages = 'C'` on its superuser connection so the message texts are the English ones above. ANY other code (42809 wrong object type, 42P16, 55000 view not updatable, 42725 ambiguous function, 42830 no unique constraint, ...) = INCONCLUSIVE: the case fails with "the oracle cannot see this attempt: <code> <message>"; it is never classed allowed. Attempts that the measured codes show can never reach the rights check are not made at all (rev 3, F1, facts 41-44): they are in the table "rights the oracle cannot see by behaviour" below, and the generator does not use them as effects.

**Scaffolding inside the attempt's savepoint (rev 3, F1, facts 41, 42, 45).** Before switching to the probed role, still as the superuser and inside the same savepoint (so it is rolled back with the attempt):
- (S-a) schema USAGE: `GRANT USAGE ON SCHEMA <the object's schema> TO <probed role>` for every attempt on an object in a schema, so a 42501 is about the object and never about the schema (fact 45). Schema USAGE itself is shown by its own attempt without this scaffold (E-schema row below).
- (S-b) a place to create: the database has one scratch schema `hadavin_oracle_scratch` owned by the superuser, made by the case fixture; attempts that must create an object get `GRANT USAGE, CREATE ON SCHEMA hadavin_oracle_scratch TO <probed role>` (fact 42 B4, B5, B8, B9). `verify` never sees this schema: it is created after `migrate` returned and dropped before the case ends, and the run-schema rules do not cover it.
- (S-c) a referencing table: for REFERENCES, `CREATE TABLE hadavin_oracle_scratch.<u> (x <type of the column>)`, `ALTER TABLE ... OWNER TO <probed role>` (fact 41 A3-A5).
- For "everyone", the probed role is the case's fresh role, which the scaffolding grants like any other probed role; the scaffold never grants anything to PUBLIC. One level of role switching: for each role the probed role can `SET ROLE` to (tried for every role of the case and every `pg_*` role), the whole list again as that role; a deeper chain in a case fails it as "oracle too shallow".

**Effect -> the attempt that shows it** (every column is tried, not only the first; functions are called with typed NULLs `NULL::<type>` built from `format_type`, so an overload is never ambiguous; the generator makes every function VOLATILE and every procedure body empty):

| Effect | Attempt as the probed role | Fixture variant, extra step |
|---|---|---|
| E01, E08, E09 SELECT on a table, view, materialized view, foreign table | `SELECT * FROM s.t LIMIT 0`, and per column `SELECT <col> FROM s.t LIMIT 0` | E09: the foreign table uses `file_fdw` (PostgreSQL contrib) with `filename '/dev/null'`, made by the superuser; a server without `file_fdw` makes E09 "not buildable here", with the error text |
| E02 INSERT, UPDATE, DELETE beyond the map | per column `INSERT INTO s.t (<col>) SELECT NULL WHERE false`; per column `UPDATE s.t SET <col> = NULL WHERE false` (no column on the right, so SELECT is not needed, D-M1; probed allowed with UPDATE only, fact 43); `DELETE FROM s.t WHERE false`. By relation kind (rev 3, fact 43, 44): table, partitioned table, auto-updatable view: all three; materialized view: all three (42809 "cannot change" = allowed); foreign table: all three (0A000 "cannot ... foreign table" = allowed); sequence: UPDATE only as `setval` (E07), never INSERT/DELETE (no such right); a view that is not auto-updatable: none (55000 before the check; table "cannot see") | S-a |
| E03 TRUNCATE, REFERENCES, TRIGGER | `TRUNCATE s.t` (table and partitioned table only; 42809 on views, matviews, sequences and 0A000 on foreign tables in both directions, facts 43, 44); REFERENCES per unique column: `ALTER TABLE hadavin_oracle_scratch.<u> ADD FOREIGN KEY (x) REFERENCES s.t (<col>)` on the scaffold table S-c (rev 3: a TEMP table gives 42P16 before the check, fact 41; table-level and column-level REFERENCES both show, A3, A5); `CREATE TRIGGER <u> BEFORE UPDATE ON s.t FOR EACH ROW EXECUTE FUNCTION pg_catalog.suppress_redundant_updates_trigger()` (tables only; on views TRIGGER is in the "cannot see" table, not probed) | S-a, S-c |
| MAINTAIN (17) and owner-only upkeep (direction 2 of 7.7) | `REINDEX TABLE s.t` on tables, partitioned tables and materialized views only (42809 on views and sequences in both directions, fact 43); a materialized view also `REFRESH MATERIALIZED VIEW s.m`. On 16 both answer 42501 "must be owner" even with ALL (fact 43), so on 16 they only confirm "not owner" | S-a |
| E04, E05 column SELECT, column UPDATE | the per-column attempts of E01 and E02, on every column | - |
| E06, E07 sequence USAGE, UPDATE | `SELECT pg_catalog.nextval('s.q')` (USAGE or UPDATE), `SELECT pg_catalog.setval('s.q', 1)` (UPDATE), `SELECT last_value FROM s.q` (SELECT) | - |
| E10, E11, E12, E13 EXECUTE on a function (explicit, left to everyone, SECURITY DEFINER of the family, SECURITY DEFINER of another owner) | `EXPLAIN SELECT s.f(<typed NULLs>)` (refused with 42501 without running the body, fact 19); aggregates: `EXPLAIN SELECT s.a(<typed NULL>) FROM (VALUES (1)) v(x)`; whether it is SECURITY DEFINER comes from `prosecdef` | - |
| E14 EXECUTE on a procedure | `CALL s.p(<typed NULLs>)` (the body is empty; `EXPLAIN` does not apply to procedures, D-M2) | - |
| E15, E17 CREATE on the schema of the run, on another schema | `CREATE TABLE s.<u> (i int)` | S-a; E17 needs a second schema: (C) or (O) |
| E-schema USAGE on a schema (rev 3, F1) | `DROP TABLE IF EXISTS s.hadavin_oracle_no_such_name` (allowed with USAGE, directly or through everyone; 42501 "permission denied for schema" without; fact 45 K1-K3) | no S-a scaffold |
| E16, E26 grant option on the schema, on a map right | `GRANT USAGE ON SCHEMA s TO <helper>`; `GRANT SELECT ON s.t TO <helper>`; `<helper>` is a fresh role of the case; the warning "no privileges were granted" = refused | - |
| E18 CREATE on the database | `CREATE SCHEMA <u>` | (O) or (C) for the migration role as actor |
| E19 TEMPORARY, explicit | `CREATE TEMP TABLE <u> (i int)` (42501 "permission denied to create temporary tables" without, fact 42 B0) | (T): visible only once everyone's TEMPORARY is revoked |
| E20 USAGE on a type or domain | `CREATE TABLE hadavin_oracle_scratch.<u> (c s.typ)` (rev 3: no TEMPORARY needed; allowed with USAGE, 42501 "permission denied for type" without, fact 42 B4, B5; `SELECT NULL::s.typ` is NOT used, it passes without USAGE, B2) | S-a, S-b; variant (U): the fixture revokes everyone's USAGE on the case's own types, nothing else |
| E21 USAGE on a language | `DO $$BEGIN END$$ LANGUAGE plpgsql` (rev 3: allowed with USAGE, 42501 "permission denied for language" without, fact 42 B6, B7; the temp-function attempt failed on TEMPORARY first, B10) | variant (U): the fixture revokes everyone's USAGE on `plpgsql`, nothing else |
| E22 large object SELECT, UPDATE | `SELECT pg_catalog.lo_get(<oid>)`; `SELECT pg_catalog.lo_put(<oid>, 0, '\x00')` | - |
| E23 USAGE on a foreign server, on a wrapper | `CREATE USER MAPPING FOR CURRENT_USER SERVER <srv>` (needs USAGE on the server); `CREATE SERVER <u> FOREIGN DATA WRAPPER <w>` (needs USAGE on the wrapper) | superuser builds the wrapper and server |
| E24 CREATE on a tablespace | `CREATE TEMP TABLE <u> (i int) TABLESPACE <ts>` | superuser makes `<ts>` with `SET allow_in_place_tablespaces = on; CREATE TABLESPACE <ts> LOCATION ''` (a developer option of 15 and later, so no directory is needed in the CI container); exclusive lock |
| E25 SET on a parameter | `SET LOCAL log_statement = 'none'` (a superuser-only parameter) | exclusive lock |
| E27 a map table owned by a group with another member | NOT a promise after rev 2 (O5 struck): a clean control that must end in (iii) and documents the non-promise | - |
| E28 a named role owns a table, function, schema | `COMMENT ON <KIND> <object> IS NULL` (owner only, every kind) | - |
| E29, E30 membership in a group with rights, inheriting / INHERIT FALSE SET TRUE | the group's rights show up directly (E29) or after `SET ROLE <group>` (E30) | - |
| E31 membership in a built-in `pg_*` role | `SET ROLE <pg_* role>` for every built-in role; for a membership with SET FALSE, one attempt per role for these six: `pg_read_all_data` `SELECT * FROM <a table with no grant> LIMIT 0`, `pg_write_all_data` `DELETE FROM <that table> WHERE false`, `pg_read_server_files` `SELECT pg_catalog.pg_stat_file('PG_VERSION')`, `pg_write_server_files` `COPY (SELECT 1) TO '/dev/null'`, `pg_execute_server_program` `COPY (SELECT 1) TO PROGRAM 'true'`, `pg_monitor` `SELECT * FROM pg_catalog.pg_ls_waldir() LIMIT 0`; the generator uses only memberships with SET TRUE or one of these six | superuser builds it (C12) |
| E32, E33 a flag on a role in the closure, on the named role | the five flags from `pg_roles` for the role and for each role it can `SET ROLE` to (flags are attributes, not access lists); for CREATEROLE also `CREATE ROLE <u>` | superuser builds it (C12) |
| E34, E35, E36 default rights | after the run, the oracle, as the migration role AND as every role the case created (the generator knows who set the default; the oracle reads no default-rights catalog), creates one fresh table, sequence, function, type and schema (schema only where that role may) in the schema of the run and in the case's second schema, then probes every named role and the fresh role on those objects with the attempts above | (C) for a second schema |
| E37 any right for a third role on a map table | the oracle also probes every role the case created on the objects of the schema of the run | - |
| E38 (rev 2) a named role's right on a map table granted by a grant-option holder (D-M5, D-m5) | as E02 | C12 only: superuser grants `WITH GRANT OPTION` to a third role, which grants to the named role |
| E39 (rev 2) a membership of a named role granted by a CREATEROLE role | as E29 | C12 only |

**Expected set for everyone** (D-m8; rev 3 M6): the fresh role may hold exactly the 3.4 baseline: CONNECT and TEMPORARY on the database, USAGE on the schema `public` when it carries the server's default list, EXECUTE on functions of other owners that are not SECURITY DEFINER, USAGE on types of other owners and on languages, USAGE on row types, and EXECUTE/USAGE on family functions and types OUTSIDE the schema of the run that are not SECURITY DEFINER (3.4 line 3 does not judge them there; C10 row). Expected set per named role: built from the grant map by an independent, hand-written table in the test file, (table, right) -> allowed, not from `GRANTS` through the code under test; `test_the_hand_written_map_equals_grants` asserts that the hand table equals `GRANTS`, so a map change must touch both.

**Sensitivity control (mandatory, never skipped).** Each effect is also applied raw, as a superuser or as the migration role, without `migrate`; the oracle must then report exactly that excess (test `test_the_oracle_sees_every_effect_applied_raw`, one parametrised id per effect and variant). An effect the oracle cannot see fails the suite; it does not count as covered.

**Rights the oracle cannot see by behaviour (rev 3, F1, M6; measured, facts 41-44).** `verify` judges them (they are access-list items like any other); the oracle cannot confirm them, so no generated effect uses them, and the property's "applied with excess" can never fire for them. Precision for them rests on the `_judge` unit tests and on direction 2 of 7.7 not trying them. Table in the test file, one row each with the measured code: INSERT, UPDATE, DELETE on a view that is not auto-updatable (55000); TRUNCATE on a view, materialized view, sequence (42809) and on a foreign table (0A000); REINDEX on a view or sequence (42809); REFERENCES on anything but a table with a unique column; INSERT and DELETE on a sequence (no such right; the GRANT is refused or ignored by the server); TRIGGER on a view (not probed in rev 3: listed as "not attempted" until the builder's first run shows a code; if it is allowed/42501 cleanly, it moves into the attempt table in the same commit 2). The oracle is also conservative on purpose for memberships: it only tries `SET ROLE`, so it never confirms that a refused ADMIN-only or INHERIT-FALSE membership was needed (design review round 2, (3)).

**Cluster-wide leftover guard (rev 3, F10).** Tablespaces and parameter rights are server-wide and outlive a killed run. The session fixture of `tests/test_migration_matrix.py` and `tests/test_migration_verify_pg.py` checks at session START and at session END, as the superuser: no tablespace whose name starts with `hadavin_test_`, no `pg_parameter_acl` row whose access list names PUBLIC or a role with the test prefix, no role with the test prefix, no database with the prefix `hadavin_test_m`. A leftover at start FAILS the session (not a skip) with the exact clean-up statements (`DROP TABLESPACE ...`, `REVOKE SET ON PARAMETER ... FROM PUBLIC`, `DROP DATABASE ... WITH (FORCE)`, `DROP ROLE ...`) in the failure text, so a poisoned developer cluster is never silently reused; a leftover at end fails the session the same way.

**DSN of a case database (rev 3, m8).** The fixture builds the migration role's DSN for the case database with `psycopg.conninfo.make_conninfo(login_dsn(...), dbname=<case database>)`, the documented psycopg helper that replaces one keyword of a conninfo string; `login_dsn` itself is not changed.

A second, coarser oracle for outcome (i): `pg_dump --schema-only` of the case database and `pg_dumpall --roles-only --no-role-passwords`, text-equal before and after the refused run (the tests already shell out to the PostgreSQL client; ci.yml line 85 checks it is present). Test aid only.

### 7.3 Effects

E01 to E37 as in the table of rev 1 (kept below), plus E38 and E39 of 7.2. Rev 2 changes: E19, E20, E21 run on variant (T); E27 is a control for a non-promise; E38 and E39 are the grantor cells.

| # | Effect | # | Effect |
|---|---|---|---|
| E01 | SELECT on a table outside the map, schema of the run [named, everyone, third role] | E20 | USAGE on a type or domain of the family [named] |
| E02 | a right beyond the map on a map table, e.g. DELETE on `runs` [named directly, everyone, through a group] | E21 | USAGE on a language [named] |
| E03 | TRUNCATE, REFERENCES or TRIGGER on a map table [everyone] | E22 | SELECT or UPDATE on a large object [everyone, named] |
| E04 | SELECT on one column of a map table [everyone] | E23 | USAGE on a foreign server or wrapper [named] |
| E05 | UPDATE on one column [third role] | E24 | CREATE on a tablespace [everyone] |
| E06 | USAGE on a sequence outside the map [named] | E25 | SET on a parameter [named] |
| E07 | UPDATE (setval) on a map sequence [everyone] | E26 | grant option on a map right [named] |
| E08 | SELECT on a view or materialized view outside the map [everyone] | E27 | a map table owned by a group that has another member (control, not a promise) |
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
| E19 | TEMPORARY on the database, explicit [named] | E38, E39 | grantor cells (7.2) |

Each effect row in the test file carries: the expected outcome per role-argument variant (for example E02 "named directly" with role arguments is outcome (iii): the runner repairs it, IF the migration role granted it; E38 is the same right granted by someone else and is outcome (i) with "No file ran"), and the problem kind(s) that must name it in outcome (ii) (D-m11), from `PROBLEM_KINDS`.

### 7.4 Carriers

| # | Carrier | Expected class when the effect is an excess |
|---|---|---|
| C1 | plain statement in a file (many are refused by a text rule first: still outcome (i)) | (i) |
| C2 | dynamic SQL with a split word (`'GR' || 'ANT ...'`) in a function the file calls | (i) |
| C3 | a string-bodied SQL function the file calls | (i) |
| C4 | AFTER INSERT trigger on the ledger table `schema_migrations` | (i) |
| C5 | trigger on a grant-map table, fired by a later file | (i) |
| C6 | deferred constraint trigger on the ledger | (i) |
| C6b | deferred constraint trigger that defers itself again (facts 4, 39) | (ii) |
| C7 | a rule, and a column default, on the ledger table that call a function | (i) |
| C8 | the object is made a member of an extension the migration role owns, then the effect | (i) |
| C9 | role switch: the login differs from the role (`options=-c role=M` in the DSN), the effect is done under the login | (i) |
| C10 | the object lives in another schema that the migration role owns (fixture grants the named roles and the fresh role USAGE on it, so the subject-side rules are tested, not schema USAGE) | Decided per effect (rev 3, M6): (i) for named roles on every effect (S5-S7, D1-D2 judge every schema); (i) for everyone on kinds where everyone holds nothing by default (E01, E04, E07, E08, E09, E22, E03, E15/E17); NOT PROMISED for everyone on family functions, types and languages in that schema (E11, everyone's half of E10, E20, E21: baseline 3.4 line 3 judges everyone's default only in the schema of the run, so `verify` returns nothing and the oracle's everyone-expectation includes them; the oracle's expected set for everyone gains "EXECUTE and USAGE on family functions and types outside the schema of the run"); NOT PROMISED for a third role (E05 third role, E37, an owner handed to a third role: rev 2, 3.3 object side) |
| C11 | a temporary table named like a catalog table is created first, then the effect | (i) |
| C12 | the state exists before the run, there is no file (an administrator did it) | (i), with "No file ran" in the message |
| C13 | move and recreate: `ALTER TABLE <map table> SET SCHEMA other; CREATE TABLE <same name> (...)`; also a plain rename | (i) |

Every case runs twice: with the three role arguments and with none.

**Counting (rev 2, D-m11).** The test file holds three written tables: (1) cells the server refuses to a plain migration role, with the server's error text (fact 20: E09 and E23 wrapper creation, E21, E24, E25, E31, E32, E33, E36, E18 and E19 unless variant (O), E17 and E28-schema unless (C) or (O), C8 unless a trusted extension is available and the role holds CREATE on the database; these are built by the superuser under C12 only); (2) pairs that are empty by logic, each with a one-line reason (for example C6 x E33: a trigger runs as the migration role, which cannot set a flag; C13 x E22: a large object has no schema to move it to; E38, E39 x anything but C12); (3) the cells that are not promised (C10 third-role cells, E27). The count test `test_the_matrix_has_exactly_the_planned_cells` computes the expected numbers from the effect, carrier and three exclusion tables and asserts equality (not a minimum), and prints: cases, pre-existing (every effect x C12 x 2), 200 seeded compositions of two or three effects with different carriers (fixed seed, printed), and the clean controls. Clean controls (rev 3: exactly 12, numbered, each must end in (iii)): K1 the shipped files alone; K2 the shipped files in a database whose schema of the run is `public` with the server's own access list; K3 another application's schema with tables, a function and a type that give the named roles nothing (D-m8); K4 a named role with a live temporary table; K5 a database owned by the migration role (O); K6 a group-owned database where the migration role is the only member; K7 E27 (group with a second member); K8 a file that hands a map table to a group the migration role belongs to (allowed since O5 is struck; documents the non-promise of 1.4); K9 no pending file; K10 every relation kind with its row type (fact 33); K11 a family SECURITY DEFINER function in another schema that only its owner may call (3.3 S7); K12 a family function in another schema left callable by everyone (C10 decision above). Rev 2's E27 / group-owned-database overlap is resolved: K6 has no second member, K7 has one.

**How a carrier performs an effect (rev 3, M6).** Every effect row carries one `make` SQL text (the same text the sensitivity control runs raw) and, where needed, a `setup` text the superuser runs before the run. A carrier is a pure function `carry(make) -> list of migration file texts`: C1 the text itself; C2 `CREATE FUNCTION s.f_<u>() ... EXECUTE <make split into 'GR' || 'ANT'...>` plus `SELECT s.f_<u>()`; C3 a `LANGUAGE sql` function whose body is `make`; C4/C5/C6/C6b a trigger function whose body is `EXECUTE <make>` on the named table with the named timing; C7 a rule and a column default that call that function; C8 the object made, `ALTER EXTENSION <ext> ADD ...`, then `make`; C9 the same files with a DSN that switches role; C10 `make` with the schema replaced by the second schema; C11 a `CREATE TEMP TABLE pg_class (...)` file first, then `make`; C12 `make` run by the superuser before the run, no file; C13 the move-and-recreate file, then `make` on the moved table. The expected outcome of a cell comes ONLY from this rule, never from the code under test: (i) for every pair, except: C6b gives (ii); E02 "named directly" granted by the migration role, with role arguments, gives (iii) (step 4 repairs it); E38/E39 exist under C12 only; the not-promised cells are excluded; the empty-by-logic and server-refused cells are excluded.

**The three exclusion tables, filled as far as the probes allow (rev 3, M6).**
- Server-refused to a plain migration role (fact 20; built by the superuser under C12 only): E09 wrapper creation and E23 wrapper and server creation; E21 language creation; E24 tablespace; E25 parameter; E31 built-in membership; E32, E33 flags; E36 default right set by another role; E18 and E19 unless variant (O); E17 and E28-schema unless (C) or (O); C8 unless the role holds CREATE on the database and a trusted extension is available (fact 14: `citext` is; variant (C)).
- Empty by logic (one line each): C6, C6b, C4, C5, C7 (trigger, rule or default runs as the migration role) x E31, E32, E33, E36, E39 (a plain role cannot do these: server-refused already); C13 x E22, E23, E24, E25, E18, E19, E29-E33 (nothing to move: no schema-bound map table involved); C10 x E18, E19, E22, E24, E25, E29-E33 (no schema); C11 x E29-E33 (a temporary table cannot change a membership); E38, E39 x every carrier but C12; E27 x every carrier (control).
- Not promised: C10 x {E05 third role, E37, owner handed to a third role}; C10 x everyone's half of {E10, E11, E20, E21}; E27 (control K7); the "cannot see by behaviour" rights above.
The count test computes cells = effects x carriers x 2 role-argument variants minus the three tables, plus the C12 pre-existing set, the 200 compositions and the 12 controls, and prints each table with its size. Rev 3 does not state the final number (it depends on the builder's encoding of the effect rows); acceptance 8 pastes it.

Q2's second WHERE clause also returns family-owned function, type and language items for everyone in every schema (design review round 2, readiness M6); `_judge` uses only the ones in the schema of the run. The query text is frozen (3.2) and the extra rows are a few per family function; the clause is not narrowed in this round.

### 7.5 New mutants, one per clause and per decision (ids `V*` in `MUT`; each killer is a real-server test, and the id of a parametrised killer is part of the killer and is checked)

From rev 1, corrected (O5 struck): S1 to S8 (8), O1, O2, O3, O4, O6 (planted as "family objects that are extension members are skipped"; killer C8), O7, O8 (7), D1 to D4 (4); the map key by schema, by name, by kind (3); the row-type exception widened to all types (1); the system-schema rule of 3.4 line 1 (1); `repaired_by_run` set for every problem (1) and never dropped at step 6 (1); the closure follows only inheriting memberships (1); `pg_database_owner` not added (1); the temporary-object exception widened to all objects (1); the pinned path removed from `verify` (killer: carrier C11) (1); the version refusal removed (1, killed by the one allowed fake: a faked version read below 160000); the self-check removed and each of its two directions (3); step 5 removed (killer: C6) (1); step 8 removed (killer: C6b) (1); `AppliedNotVerifiedError` raised as `ConfigError` (1); the "applied" return kept on a step-8 failure (1); the pre-flight removed (killer: C12 must say "No file ran") (1); the new lock join replaced by the old listing (killer: the bystander is named) (1); `l.pid IS NULL` removed (1); ~~the duplicate-CREATE rule removed (1)~~ (rev 3: left with 6.4). That is 41 (rev 1's 42, minus O5, plus O8, minus the duplicate-CREATE rule). The two lock mutants (new join replaced by the old listing; `l.pid IS NULL` removed) are planted in commit 4 with the lock code, not in commit 5.

New in rev 2 (13): O2's schema-USAGE exception removed (killer `test_the_public_schema_with_the_server_default_passes`); the built-in-grantee filter removed from S5 (killer `test_a_named_role_in_pg_monitor_prints_exactly_one_statement`); a fix printed for a system object (same killer); the object-right fix ignores the grantor (killer `test_printed_statements_remove_every_problem_for_every_grantor_form`); the membership fix without `GRANTED BY` (same killer); `repaired_by_run` ignores the grantor (killer `test_a_right_granted_by_a_grant_option_holder_is_not_dropped_at_step_2`); the step-8 `try` narrowed to connection errors (killer `test_any_error_inside_step_8_gives_exit_5_not_exit_2`); the two limits not run inside `verify` (killer `test_step_8_with_a_saved_statement_timeout_still_checks`); a server-refused COMMIT classed as unknown (killer `test_a_commit_refused_by_the_server_gives_exit_2_and_keeps_nothing`); a lost connection at COMMIT classed as refused (killer `test_a_lost_connection_at_commit_gives_exit_5`); step 8 not REPEATABLE READ (killer `test_step_8_reads_one_snapshot`); the row-type key widened to standalone composite types (killer `test_row_types_of_six_relation_kinds_pass_and_a_standalone_composite_type_does_not`); Q1's `UNION` turned into `UNION ALL` (killer `test_verify_cost_on_a_large_catalog`, the diamond part).

54 new mutants (41 + 13); with 5.5 the list goes from 288 to 313. Ids: `V01`-`V54` in the order of this section (first paragraph in its order, then the 13); the builder notes table holds id, clause, planted file and text, killer node id, commit. Rev 3 (M7): a killer named "C<n> x E<m>" in this section is the parametrised node id `tests/test_migration_matrix.py::test_cell[<E>-<C>-roles]`, checked with its parameter (5.5).

### 7.6 Dedicated tests outside the matrix (in tests/test_migration_verify_pg.py unless said otherwise; each name is the acceptance id of 9.1)

- `test_after_commit_a_grant_gives_exit_5_and_the_statements_repair_it`: a test wraps `connect` so that, just before the step-8 connection is returned, a superuser grants `SELECT ON <map table> TO PUBLIC`. Asserts: `AppliedNotVerifiedError`, exit code 5 through `cli.main(["migrate", ...])`, the first sentence word for word, no line starting "applied", the statements on standard output only, the ledger holds the files, and running every printed statement as a superuser makes the next `migrate` return normally.
- `test_step_8_that_cannot_connect_gives_exit_5`: the wrapped `connect` raises on its second call; asserts the "could not run" wording and exit code 5.
- `test_any_error_inside_step_8_gives_exit_5_not_exit_2`: parametrised: (a) the step-8 connection raises `QueryCanceled` on its third statement, (b) its version read answers 150000 (the version `ConfigError`), (c) it raises a plain `psycopg.Error`. Each: exit 5, "could not run", never exit 2, never "Nothing was changed".
- `test_step_8_with_a_saved_statement_timeout_still_checks` (D-M2): in a case database, `ALTER ROLE <migration role> SET statement_timeout = 1` (rev 3, m9: the value measured in facts 36 and 47; 20 of 20 Q2 runs cancelled without the limits). Sensitivity first: on a fresh connection of that role, Q2 alone is cancelled (57014), so the setting really bites on this machine (fact 36); if it does not, the test FAILS with that finding. Then `migrate` on the shipped files returns normally (exit 0) and the oracle is clean, because `verify` runs the two limits first. The role setting is reset in `finally`.
- `test_step_8_keeps_a_role_switch_in_the_dsn` (D-M8, carrier C9): the DSN carries `options=-c role=<M>`; a wrapper records `current_user` on the step-8 connection; asserts it is `<M>`.
- `test_step_8_reads_one_snapshot`: a wrapper records `transaction_isolation` and `transaction_read_only` inside step 8: `repeatable read`, `on`.
- `test_a_commit_refused_by_the_server_gives_exit_2_and_keeps_nothing` (D-M3): a file with a deferred trigger that defers itself again (fact 4) and whose second firing raises an error at COMMIT. Asserts exit 2, the "the database server refused the commit" wording, the ledger without the file.
- `test_a_lost_connection_at_commit_gives_exit_5` (D-M3): the same shape, but the second firing runs `pg_sleep(5)`; the test's second thread waits (bounded, 10 s) until `pg_stat_activity` shows that sleep, then runs `pg_terminate_backend` on it. Asserts exit 5, the "may or may not have happened" wording, and (rev 3, m10) that `_commit_outcome` received `AdminShutdown` with SQLSTATE 57P01 on a closed connection (fact 46 F1: here the commit did not happen; fact 37b shows a cut where it did). `test_a_cancel_at_commit_gives_exit_2` (rev 3) is its sibling with `pg_cancel_backend`: 57014, open, IDLE, exit 2, ledger without the file (fact 46 F2).
- `test_message_safety_names_with_newline_and_escape`: one object name, one role name, one column name and one function ARGUMENT name with a newline and an ESC character; asserts the printed text holds neither and that no statement is printed for them (`by_hand = "name"`).
- `test_the_running_server_is_16_or_later_and_accepted`, `test_a_server_below_16_is_refused_with_the_plain_message` (the one allowed fake: the version read answers 150000).
- `test_the_self_check_matches_the_running_server`: Q0 equals `KNOWN_ACL_COLUMNS` (the test that fails first on a new PostgreSQL version).
- `test_upgrade_from_mains_state_is_repaired` (R-M9): EMULATES the state main's `migrate` (main 2a8c2aa) leaves; it does not run main's code. In a case database: the five shipped files applied as the migration role in one transaction, the ledger table with the five versions, the three named roles granted exactly the grant map with the migration role as grantor, and the default EXECUTE for everyone left on the package's trigger function (main never removed it). Then the new `migrate` with no pending file: returns normally, the oracle is clean. The claim is exactly this emulated state, nothing more.
- `test_verify_cost_on_a_large_catalog` (marker `perf`, so CI runs it in its perf step, ci.yml line 100; D-m10): one case database with 5,000 tables of another application (each with a column grant to a third role), 20,000 functions, 2,000 large objects, 500 roles with memberships, and the 25-level diamond of fact 40 under one named role. Asserts one `verify` call under 30 s and prints the time of each of its 8 statements. The statement limit inside `verify` is 60 s per statement (`RECIPE_TIMEOUTS`, migration_numbers.py:68), so the bound of 30 s for the whole call is below it.
- `test_the_public_schema_with_the_server_default_passes` (R-B2): a case database whose schema of the run is `public` with its own access list (fact 34); `migrate` with the three role arguments on the shipped files returns normally. `test_create_for_everyone_on_public_is_refused` is its sensitivity control: `GRANT CREATE ON SCHEMA public TO PUBLIC` first; refused at step 2 with "No file ran", kind `schema_right`.
- `test_an_extension_view_readable_by_everyone_is_refused_without_a_statement` (rev 3, F12 default, fact 50): `CREATE EXTENSION pg_stat_statements` in the case database; `migrate` refused at step 2, two lines with the extension mark, no statement printed for them.
- `test_a_right_on_another_applications_table_is_marked_and_printed_apart` (rev 3, F11): a grant after the commit on a table of another schema owned by a third role; exit 5; the line starts "NOT THIS PACKAGE'S OBJECT"; its statement is in the second block only.
- `test_a_grant_option_from_two_grantors_is_removed_by_the_printed_statements` (rev 3, F9, fact 49).
- `test_the_database_owner_membership_is_a_by_hand_line` (rev 3, F9, fact 48): a named role owns the case database; one `built_in_role` line, `by_hand = "database_owner"`, no statement.
- `test_a_named_role_in_pg_monitor_prints_exactly_one_statement` (D-M4, fact 38): the runtime role is a member of `pg_monitor`; refused at step 2 with exactly one problem line (kind `built_in_role`) and exactly one statement, `REVOKE "pg_monitor" FROM "<runtime role>" GRANTED BY "<grantor>";`.
- `test_printed_statements_remove_every_problem_for_every_grantor_form` (D-M5, facts 30-32): a right on a table of another schema granted by the owner, the same granted by a grant-option holder (table and column), a membership granted by a CREATEROLE role, a default right; all printed statements run as a superuser; `verify` then returns nothing.
- `test_a_right_granted_by_a_grant_option_holder_is_not_dropped_at_step_2` (D-m5, effect E38): refused at step 2 with "No file ran"; the run does not reach step 6.
- `test_row_types_of_six_relation_kinds_pass_and_a_standalone_composite_type_does_not` (D-m9, fact 33).
- `test_a_ledger_trigger_that_disables_the_audit_triggers_is_refused_at_the_end_of_the_run` (D-m11, round-12 F2 variant).
- `test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments` (C-F9).
- `test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one` (TPG, changed by 6.3), `test_an_unreadable_lock_view_is_a_plain_config_error` (6.2), `test_a_grant_map_name_created_twice_is_refused` (6.4).
- In tests/test_migration_verify.py (no server): `test_every_catalog_name_in_the_queries_is_qualified` (acceptance 4), `test_every_live_acl_column_is_read_by_a_query` (3.6), `test_every_runner_catalog_read_is_pinned` (an AST check that `_refuse_privileged_role`, `_refuse_foreign_owned`, `_read_back`, `_check_read_back`, `_recheck_roles`, `_members_of_each_other` and the step-4 query run only inside `pinned_read`), `test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog` (markers of 9.3), `test_every_problem_kind_is_produced_and_named` (3.3), `test_the_rights_table_equals_what_apply_grants_is_called_with` (3.2), the rewritten TCMP tests of 5.4.

### 7.7 The CI test of the shipped files (promise table row 1)

`test_the_shipped_files_give_each_role_exactly_the_map` (tests/test_migration_matrix.py), run in CI on every pull request: a case database, plain migration role as the printed SQL makes it, `migrate` with the three role arguments on the five shipped files; then the oracle shows, for each of the three roles and for the fresh "everyone" role, that it can do every operation the hand-written expected table lists (direction 1: nothing is missing) and is refused every other operation the oracle tries on every object of the database (direction 2: nothing extra, the baseline of 3.4 apart). A second run with no pending file must give the same answers.

### 7.8 Repository check: no real-server test returns before calling `migrate`

Extend tests/test_migration_rules.py with `test_no_real_server_test_returns_before_it_runs_migrate`: parse TPG, test_migration_verify_pg.py and test_migration_matrix.py with `ast`; in every `test_*` function, a `return` (bare, or `return None`) that comes before the first call whose name is `migrate`, `_run_plant`, `run_case` or `main` is a failure, unless the line carries the marker comment `# visible: pytest.fail above`. Functions that contain `yield` are not checked (rev 1 named TPG:242, which is the plain `return` after `yield` in the context manager `_plain_role_may_set`; it is legitimate, citation list A item 3). Helpers are not checked (rev 1's helper rule is dropped: it had no exact definition). The test must fail on the round-12 head because of TPG:4520.

### 7.9 Which tests must FAIL on the round-12 head, and the proof (rev 2, R-M8)

How: the builder checks out 4d328e3d into a scratch worktree, copies onto it ONLY tests/fixtures/oracle.py, tests/test_migration_matrix.py, the dedicated test of 6.1 and the repository check of 7.8, plus a 20-line adapter `tests/_old_head_adapter.py` that defines `AppliedNotVerifiedError` as a class nothing raises and maps the old results: `migrate` returned = outcome (iii), `ConfigError` = outcome (i). The new test files must not import `hadavin_sdk.store.migration_verify` at module level (they import `AppliedNotVerifiedError` with `getattr(hadavin_sdk.errors, "AppliedNotVerifiedError", None) or adapter class`, and import `hadavin_sdk.store.migration_verify` only inside the test functions that call `verify` directly, none of which is copied; rev 3, m14), so collection succeeds on the old head. A failure counts ONLY when it is the assertion "applied with excess:" (7.1) or, for the lock test and the repository check, their own assertion; an import error, a collection error or an INCONCLUSIVE attempt does not count, and the evidence shows the failing line for each id. Exit codes from pytest itself, never through a pipe.

Must fail on 4d328e3d:
- generator cases for E22 x C2 (large object), E29/E30/E31/E32 x C12 (memberships), E01 x C12 in another schema, E10 x C12 (standing EXECUTE), any effect x C6 (deferred trigger), x C8 (extension), x C9 (role switch), x C13 (move), E36 (default right set by another role): each returns "applied" with an excess the oracle sees;
- the prepared-transaction test with the bystander (the old message names it);
- the repository check of 7.8.

Not part of the old-head proof (rev 2 correction): the version refusal test, the self-check test and the message-safety test of `effective_problems` lines; they test names that do not exist on the old head and could only fail on import.

Regression guards expected to PASS on the round-12 head where they can run there (exempt from the proof, listed as such): effects x C1 that a text rule refuses, the clean controls, the CI test of 7.7 direction 1.

### 7.10 Run time, batching and heavy jobs (rev 2, R-M5)

Measured or cited numbers: the migrate mutant list takes 30 minutes or more for 288 mutants (about 6-7 s each; the readiness review's studio figure, not measured by this author; the header of `MUT` still says "about 10 minutes" and is corrected in the texts commit). The new V* killers use the matrix (migrate plus oracle), estimated 10-20 s each (not measured). One case database costs about 24 ms (measured, 7.2).

`tools/heavy_slot.py` does not exist in this repository (checked at 4d328e3d and on core/cloud-handover: `ls tools/heavy_slot.py` fails; rev 3 re-checked `git show 4d328e3d:tools/heavy_slot.py`: exit 128). Rule (rev 3, M4): in this cloud container every heavy job (full suite, matrix, a mutant batch, the perf test) runs as `/home/user/build/heavy.sh timeout <seconds> <argv...>`: `heavy.sh` takes a slot (at most 3 machine-wide, flock on /tmp/heavy-slot-N.lock) and runs its arguments without a shell, so `timeout` is INSIDE the slot and bounds the job itself; environment variables are set before `heavy.sh` (`HADAVIN_TEST_PG_DSN=... /home/user/build/heavy.sh timeout 3000 uv run --offline ...`). On the studio machine the same argv runs after `python tools/heavy_slot.py --slots 3 --timeout 3000 --`. Bounds: a mutant batch 3000 s; the matrix 2400 s; the whole suite 2400 s; the perf test 600 s. The mutant runner calls each killer by its node id; `-m perf` tests are NOT deselected inside a killer run, so the perf test as a killer (the `UNION ALL` mutant) runs its fixture once per mutant run, measured by the builder in batch 1 and written in the checkpoint note.

Mutants: the runner gets `--list-batch N` (N = 1 to 4), a pure function with a unit test that the four batches are disjoint and cover the whole list: batch 1 = the 55 new V* (estimate 9-18 min); batch 2 = the 47 re-pointed, the 16 re-checked and LW7, LW8 (about 65, estimate 8-10 min); batches 3 and 4 = the rest in id order, split in half (about 97 each, estimate 10-12 min each). Command per batch (rev 3, M4; `ids` first, because heavy.sh runs no shell): `uv run --offline --all-extras --group test python tests/migrate_mutants.py --list-batch N > /home/user/build/batchN.ids`, then `HADAVIN_TEST_PG_DSN="$DSN" /home/user/build/heavy.sh timeout 3000 uv run --offline --all-extras --group test python tests/migrate_mutants.py $(cat /home/user/build/batchN.ids) > /home/user/build/batchN.log 2>&1; echo $?` (the `$(cat ...)` is expanded by the calling shell before heavy.sh starts). While building: only the ids the commit touches. On the final head: the four batches once, one after another, alone. If a batch hits the time limit: the evidence runner records the last finished id, runs `git status --short` and restores any planted file with `git checkout -- <file>` (rule long-jobs-run-detached), splits the unfinished ids in two and runs each half once; the time-out is written in the evidence, not hidden.

Generator: about 1,000 cases (exact number from the count test) with one database each; estimate 15-25 minutes on one heavy slot. The builder measures the first 50 cases and writes the number in the checkpoint note. The matrix runs in CI on every pull request (it is the promise of row 1); if the measured whole matrix exceeds 20 minutes, the builder reports the number to the lead instead of cutting cells (the lead decides between a separate CI job and a nightly run; cutting cells is not allowed).

## 8. Tool ladder, single dependency, least privilege

RUNG TABLE (CODE-LAST v1):

| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| `verify` | compare who can do what with the grant map, at run time, as a plain role, on any PostgreSQL including managed ones | own core, extended: `effective_problems` on main (migrate.py:193-262) is the base | read 2026-11-11; Q0-Q4 run on 16.15 | constraints (1)-(3) under this table: inside the run's transaction, as the plain role, against the Python grant map | KEEP-CODE (one module, 8 statements) |
| pg_permissions (server extension) | same | ready-made tool | NOT EVALUATED (rev 3, F4): not researched live; no claim about its features, version or licence is made | - | does not decide anything below |
| pgTAP | same | ready-made tool | NOT EVALUATED (rev 3, F4): no claim about its features is made | - | does not decide anything below |

Rev 3 (F4): the KEEP-CODE verdict for `verify` rests ONLY on these stated constraints, each checkable without knowing any outside tool: (1) the check must run inside `migrate`'s own transaction, before the commit, so that a refusal undoes the run (section 4.1 steps 2 and 6); a tool outside the transaction cannot undo it; (2) it must run as the plain migration role with no server-side install, because the package runs on managed databases where the migration role may not install extensions (10.1, "anything that needs a superuser from the runner"); (3) it must judge the package's own grant map, which lives in the Python code (`GRANTS`). Any outside tool that meets (1)-(3) at 80 percent or more would need a new ticket and the owner's yes (rule 20); none is named here because none was researched. The build order does not depend on these rows. A live comparison of pg_permissions, pgTAP and ldap2pg is listed for split ticket D (hardening guide), where they may be offered to a client.
| `pg_dump` / `pg_dumpall` text comparison | "nothing changed" after a refused run | ready-made tool, already on the test machines (ci.yml:85) | used by today's tests | - | second test oracle only (7.2); never at run time (needs a matching client binary) |
| declarative grant tools (ldap2pg, infrastructure-as-code providers), event triggers | keep rights in a declared state; log grants | client's own tool | NOT EVALUATED (rev 3, F4) | - | the client's choice; to be researched live in split ticket D |
| the behavioural oracle | an independent judge for the tests | new test code | fact 18, 19 | independence from the code under test | KEEP-CODE (tests only) |
| `file_fdw` (PostgreSQL contrib) and `allow_in_place_tablespaces` (developer option, 15 and later) | a foreign table and a tablespace the oracle can probe in a container | ready-made, ships with PostgreSQL | from the PostgreSQL documentation, not run in rev 2 (the builder's first run states per server whether each is available; a missing one makes its cells "not buildable here" with the error) | - | test aid only, never at run time |

Ladder line: own core module extended (reuse of `effective_problems`, `_label`, `_shown`, `_managed_names`, `_apply_grants`, the mutant runner); no no-code tool, connector or model feature applies to a catalog check inside a database transaction. No external tool is needed at run time, so no licence question arises for what ships; licences of the test aids are those of the PostgreSQL client already in use.

Single-dependency line: PostgreSQL stays behind the store kind; `psycopg` stays inside `store/`; no new library. Versions: 16.15 run here by the author and the evidence runner; CI runs `postgres:17.10@sha256:7958605b474b3d264a969cb3a123d6aa00ad1e1fe9da8a69984dabb704d93317` (.github/workflows/ci.yml lines 41 and 111 on the branch); 18 is not run by anyone and is not claimed; below 16 is refused. The self-check (3.6) is the guard for a version nobody ran.

Least-privilege lines: this ticket creates no new identity and gives no identity a new right. `verify` reads catalogs every role may read (run as a plain role, v1.out) and writes nothing. The migration role, runtime role, portal role and purge role keep their rights: migration role = owner of the package's objects, no flag, no built-in role; runtime, portal, purge = exactly the grant map plus USAGE on the schema; the per-right reasons are the comments of `GRANTS` (MIG:135-163), unchanged. Negative test: 7.7 direction 2. Over-breadth review: the result review of this round. The separate checking identity (connect-only, reads catalogs, no right on any table) is split ticket A and is not built here.

## 9. Acceptance, gates, branch, CHANGELOG

### 9.0 How to run here (rev 3, M2, M4; every line ran in rev 3 on this container unless marked)

```sh
# 1. Your own PostgreSQL 16.15 (installed at /usr/lib/postgresql/16/bin). The container runs as root; initdb refuses root, so run as the postgres OS user.
P=/usr/lib/postgresql/16/bin; D=/home/user/build/pg-<you>; S=/home/user/build/pg-<you>-sock; PORT=<free port in 56000-56999>
mkdir -p $D $S && chown postgres:postgres $D $S
runuser -u postgres -- $P/initdb -D $D -E UTF8 --locale=C.UTF-8 -U postgres > /home/user/build/pg-<you>-initdb.log 2>&1; echo $?   # 0
runuser -u postgres -- $P/pg_ctl -D $D -l $D/server.log -o "-p $PORT -k $S -c listen_addresses='' -c max_prepared_transactions=10" -w start; echo $?   # 0
runuser -u postgres -- $P/psql -h $S -p $PORT -U postgres -Atc "SHOW server_version; SHOW max_prepared_transactions"   # 16.15 ..., 10
# (the log must live inside $D or another postgres-writable place: rev 3's first start failed with "Permission denied" for a log in /home/user/build)
# 2. The DSN (superuser over the local socket; trust authentication is initdb's default for local connections; no password exists or is written):
DSN="host=$S port=$PORT user=postgres dbname=postgres"
# 3. Python environment: pre-synced in this container; always pass --offline (no downloads):
T="uv run --offline --all-extras --group test"
$T python -c "import psycopg, pytest; print(psycopg.__version__, pytest.__version__)"   # rev 3: 3.3.6 9.1.1, exit 0 (on core/cloud-handover; re-run on core/P3a-2-clean first)
uvx --offline bandit --version                                                          # rev 3: exit 0 (bandit is not in the test group; uvx has it cached)
# gitleaks is NOT installed here (rev 3: `which gitleaks` prints nothing); it runs in CI only (ci.yml gitleaks step). State it in the evidence.
# 4. A quick (non-heavy) test run, exit code from pytest itself:
HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify.py -q > /home/user/build/v.log 2>&1; echo $?
# 5. A heavy run (full suite, matrix, mutant batch, perf): through the slot wrapper, time bound inside the slot:
HADAVIN_TEST_PG_DSN="$DSN" /home/user/build/heavy.sh timeout 2400 uv run --offline --all-extras --group test pytest -q > /home/user/build/full.log 2>&1; echo $?
# 6. At the end: stop YOUR server.
runuser -u postgres -- $P/pg_ctl -D $D -m fast stop
```

Time bounds: per-commit G command 600 s (`timeout 600` in front of each pytest, not through heavy.sh); full suite, matrix 2400 s; mutant batch 3000 s; perf test 600 s; a builder session 60 minutes (9.4). CI on PostgreSQL 17.10 (item 19) needs a push and a pull request: the builder never pushes; the LEAD pushes the branch and opens or updates the draft pull request, then the builder (or an evidence runner) reads the CI logs with `gh run view --log` and pastes the lines.

### 9.1 Acceptance checklist (rev 2: each item names its test id or command, R-M4; an evidence runner runs each and pastes raw output; `T="uv run --offline --all-extras --group test"`; `HADAVIN_TEST_PG_DSN="$DSN"` with `$DSN` from 9.0, a superuser login of a scratch server with `max_prepared_transactions` above 0; every pytest exit code is taken from pytest itself, never through a pipe; heavy items (10, 12, 21, 24 full suite) run through heavy.sh as in 9.0)

The builder notes also carry a table "item -> exact command as run -> exit code", a Blocker-level deliverable: an item without its row is not done.

1. `git merge-base --is-ancestor 4d328e3d HEAD; echo $?` prints 0; `git log --oneline 4d328e3d..HEAD` shows the commits of 9.3 in that order.
2. `grep -rn --include='*.py' "_changed_since\|_Objects\|_objects(\|_Changed\|_kept_owner_ids\|_changed_ids\|_STATE_SQL\|@MINE@\|@ME@\|effective_problems\|_MAINTAIN_FROM\|_SCHEMA_USAGE_SQL\|_TABLE_PRIVS" src tests` prints nothing (`--include` keeps committed `.pyc` files out).
2b. `grep -n "current_schema()" src/hadavin_sdk/store/migrate.py` prints exactly one line, the read of step 1. No comment or docstring of `migrate.py` may contain `current_schema()` (write "the schema of the run"; rev 3, m5).
3. `grep -n "current_user\|session_user\|current_schema" src/hadavin_sdk/store/migration_verify.py` prints nothing. The new module must not contain these words anywhere, comments and docstrings included (write "the role that runs migrate" instead).
4. `$T pytest tests/test_migration_verify.py::test_every_catalog_name_in_the_queries_is_qualified tests/test_migration_verify.py::test_the_qualified_name_check_catches_a_missing_prefix` passes (the second feeds the check a copy of Q2 with one `pg_catalog.` removed and asserts it is caught).
5. `grep -c "has_table_privilege\|has_column_privilege\|has_sequence_privilege\|has_schema_privilege\|pg_has_role" src/hadavin_sdk/store/migration_verify.py` prints 0, and `grep -c "has_table_privilege\|has_column_privilege\|has_sequence_privilege\|has_schema_privilege" src/hadavin_sdk/store/migrate.py` prints 0. (`pg_has_role` and `has_parameter_privilege` stay in the kept step-1 checks and read-back of `migrate.py`, MIG:438-461, 607-625, 661-681, 1474; they are not part of `verify`.)
6. `$T pytest tests/test_migration_verify.py::test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog` passes. Markers (R-Mn9): the promise table sits between a line `[promise table]` and a line `[end of promise table]` in the `migrate.py` module docstring and in the CHANGELOG item; the test compares the text between the markers after removing leading whitespace from each line and dropping blank lines (rev 3, m4: the docstring is not indented, the CHANGELOG copy is nested two spaces).
7. The grep of 1.5 (with `--include`) is pasted with one line of reason per remaining hit.
8. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_matrix.py::test_the_matrix_has_exactly_the_planned_cells -s` passes; its printed numbers are pasted (cases, pre-existing, compositions with the seed, controls, server-refused cells with their errors, empty-by-logic pairs, not-promised cells).
9. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_matrix.py -k test_the_oracle_sees_every_effect_applied_raw -rA` passes; the per-effect table it prints is pasted.
10. `HADAVIN_TEST_PG_DSN="$DSN" /home/user/build/heavy.sh timeout 2400 uv run --offline --all-extras --group test pytest tests/test_migration_matrix.py -q -rA > /home/user/build/m.log 2>&1; echo $?` is 0, and the outcome summary the module prints at session end (counts of (i), (ii), (iii), and "applied with excess: 0") is pasted.
11. 7.9: each must-fail id pasted failing on 4d328e3d with the "applied with excess:" line (or the lock test's or the repository check's own assertion), and passing on the head.
12. Mutants: the four batches of 7.10 on the final head, one after another, through heavy.sh, each with the runner's own summary line pasted (rev 3: the builder pastes the line the runner really prints at 4d328e3d, read from `tests/migrate_mutants.py`, not the words `N of N killed`), total 313; the table retired / re-pointed / re-checked / new is in the builder notes; `$T pytest tests/test_migration_rules.py::test_every_migrate_mutant_still_applies_to_the_source` passes.
13. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py -k "after_commit or step_8 or any_error_inside_step_8 or commit_refused or lost_connection_at_commit" -rA` passes; the message of `test_after_commit_a_grant_gives_exit_5_and_the_statements_repair_it` is pasted and starts with the exact first sentence of 4.2; exit code 5 is shown through `cli.main`.
14. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form tests/test_migration_verify_pg.py::test_a_named_role_in_pg_monitor_prints_exactly_one_statement -rA` passes; the printed statements are pasted.
15. Prepared transaction: `SHOW max_prepared_transactions` of the server used (above 0) pasted; `HADAVIN_TEST_PG_DSN="$DSN" $T pytest "tests/test_migration_postgres.py::test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one" -rA` passes, not skipped.
16. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py::test_an_unreadable_lock_view_is_a_plain_config_error` passes.
17. (rev 3: the duplicate-CREATE test left with 6.4) `$T python -c "from pathlib import Path; from hadavin_sdk.store import migrate as m; print(m.check_grants(sorted(Path('src/hadavin_sdk/store/migrations').glob('*.sql'))))"` prints `[]`.
18. `$T pytest tests/test_migration_rules.py::test_no_real_server_test_returns_before_it_runs_migrate` passes on the head and fails on 4d328e3d (TPG:4520).
19. CI on PostgreSQL 17.10 is green for the whole suite, including 7.7 and the self-check; the CI log line with the server version and the line `max_prepared_transactions` = 10 are pasted. A local 16.15 run of the same suite is pasted.
20. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py -k "running_server_is_16 or below_16 or self_check" -rA` passes; both messages pasted.
21. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest -m perf tests/test_migration_verify_pg.py::test_verify_cost_on_a_large_catalog -s` passes; the measured times pasted.
22. `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py::test_upgrade_from_mains_state_is_repaired` passes.
23. Rev 2 items: `HADAVIN_TEST_PG_DSN="$DSN" $T pytest tests/test_migration_verify_pg.py -k "public_schema or create_for_everyone_on_public or grant_option_holder_is_not_dropped or row_types_of_six or audit_triggers or reviewed_definer_is_excused or message_safety" -rA` passes.
24. Gates, each with its own exit code, on the final head with no cloud configuration in the environment: `$T ruff check`; `$T ruff format --check`; `HADAVIN_TEST_PG_DSN="$DSN" $T pytest > log 2>&1; rc=$?; tail -n 1 log; echo $rc`; `uvx --offline bandit -q -r src demos -ll` (the form of ci.yml line 119); the repository guard steps as `.github/workflows/ci.yml` at the branch head runs them (line 84 `python tools/scan_repo.py`, line 94 `python tests/stage_mutants.py`; the builder copies the lines from the workflow at the final head into the evidence); the migrate mutant batches (item 12) and `HADAVIN_TEST_PG_DSN="$DSN" /home/user/build/heavy.sh timeout 3000 uv run --offline --all-extras --group test python tests/migration_numbers_mutants.py` (rev 3: the builder confirms the argument form against the file's header and pastes it); `gitleaks` as the workflow runs it (CI only: not installed in this container, 9.0). CodeQL, SonarCloud and CodeRabbit green on the pull request; threads resolved after fixing; no suppression, no weakened or deleted test outside the lists of 5.4 and 5.4b.

### 9.2 Stop rule

Security path: result-review rounds repeat until a fresh round finds no Blocker and no Major. Classing rule for every finding from now on (D-020): it is either a bug in a numbered clause of section 3.3 or 3.4 (fix it and add the generator cell), or it is inside a stated non-promise of 1.3/1.4 (no fix; check that the text says so), or it is a way around a text rule (not a finding). When the builder or the lead and a reviewer disagree on the class of a finding, the lead decides and writes the decision in handover/AUTONOMOUS-DECISIONS.md before the next round (R-readiness D, stop rule).

### 9.3 Commits (rev 2, R-B1): one buildable order, each commit green on its own

The per-commit green command (G): `$T ruff check && $T ruff format --check && HADAVIN_TEST_PG_DSN="$DSN" $T pytest <the affected test files of that commit> tests/test_migration_rules.py::test_every_migrate_mutant_still_applies_to_the_source`, each exit code taken from pytest. A mutant that a commit's code change moves (re-pointed) or removes (retired) is changed IN THAT COMMIT, so `test_every_migrate_mutant_still_applies_to_the_source` is green at every commit.

1. **verify beside the old code** (nothing calls it yet): `migration_verify.py` (queries, `_judge`, `Problem`, `PROBLEM_KINDS`, `KNOWN_ACL_COLUMNS`, version refusal, self-check, `pinned_read`), `_label` moved to `migration_numbers.py` with the import back in `migrate.py`, `tests/test_migration_verify.py`, and the parts of `tests/test_migration_verify_pg.py` that call `verify` directly on a database the test prepares (version, self-check, and the `verify` half of the public-schema, pg_monitor, grantor-form, row-type and cost tests); their `migrate` halves land in commit 3. Old code untouched, so every old test and mutant still holds. G affected files: tests/test_migration_verify.py, tests/test_migration_verify_pg.py, tests/test_migration_rules.py.
2. **oracle** (no product code): `tests/fixtures/oracle.py`, the sensitivity-control test and the oracle's repository test in `tests/test_migration_matrix.py`. G affected: tests/test_migration_matrix.py -k "oracle".
3. **the switch** (one commit, because the deletion and the new order depend on each other): `migrate()` takes the order of 4.1; `AppliedNotVerifiedError`; cli exit 5 and its docstring line; COMMIT handling; step 8; deletion of the comparison code, `effective_problems`, `_refuse_unlisted_grantees` and the other names of 5.3; retired tests of 5.4 removed; kept tests of 5.4 re-pointed; the fake-database answers of 5.4b; `test_k2_migrations.py` change of 5.4b; the 29 retired mutants removed and the 45 re-pointed mutants re-planted (with killers that exist in this commit); the 16 re-checked mutants confirmed killed (run them: batch 2 ids that exist at this commit); the step-8 and COMMIT tests of 7.6. G affected: tests/test_migration_wiring.py, tests/test_migration_postgres.py, tests/test_migration_compare.py, tests/test_k2_migrations.py, tests/test_migration_verify*.py, tests/test_migration_rules.py.
4. **extras** (section 6): lock message and join, unreadable view, duplicate CREATE, CI server setting, the prepared-transaction test change, mutants LW7 and LW8 re-planted. G affected: tests/test_migration_postgres.py, tests/test_migration_verify_pg.py, tests/test_migration_rules.py.
5. **the matrix**: generator, controls, count test, 7.7, 7.8, the 55 V* mutants with their killers, `--list-batch`. G affected: tests/test_migration_matrix.py, tests/test_migration_rules.py, plus the V* ids run once.
6. **texts**: module docstring (its numbered list "What `migrate` does, in order" rewritten to the eight steps of 4.1, R-Mn11), `migrate` docstring (promise table first between the markers, then the eight steps, then 1.4 as "What it cannot notice", keeping the phrases listed in 5.4b item 3), the CHANGELOG item, the MUT header ("about 10 minutes" replaced by the measured time), the TR pins of 5.4b item 3 and mutant R23 re-pointed in the same commit. G affected: tests/test_migration_rules.py, tests/test_migration_verify.py.

Commit messages end with the attribution lines the session reminder gives. The draft pull request stays the existing one for `core/P3a-2-clean` if there is one; otherwise the lead opens it.

### 9.4 Work packages, each within one 60-minute builder session (rev 2, R-M5)

A session writes a checkpoint note every 30 minutes (done / next / blockers / commit SHA) and stops at 60 minutes with a commit; a fresh builder resumes from the note. A package may take more than one session; the estimates are guesses, not measurements.

| Package | Commits | Depends on | Can run in parallel with | Estimate |
|---|---|---|---|---|
| A1 | 1 | nothing | B1 | 1-2 sessions |
| B1 | 2 | nothing (the oracle uses no product code) | A1 | 1 session |
| A2 | 3 | A1 | B1 (if not done) | 2 sessions (the largest: deletion, order, 5.4b test edits) |
| C1 | 4 | A2 | B2 | 1 session |
| B2 | 5 | A2, B1 | C1 | 2 sessions |
| C2 | 6 | A2, B2 | - | 1 session |

Critical path: A1 -> A2 -> B2 -> C2, about 6 sessions; with B1 and C1 beside it, about 8 sessions in all. Heavy jobs: one full suite, the four mutant batches and one matrix run, once each on the final head (7.10).

### 9.5 CHANGELOG

CHANGELOG ("Unreleased", "Upgrade steps", replacing CL:15, 17, 18, correcting CL:11 and 34). Everything below is NESTED inside the existing first bullet "- **Migrations: stricter checks ...**" (indented two spaces), never a new top-level bullet, so `_upgrade_bullet()` (TR:666) still covers it:
- First the promise table of 1.3 under the heading "What migrate promises", between the markers of 9.1 item 6, then 1.4 as "What it cannot notice".
- The baseline of 3.4 in its four lines, plus: "Every built-in `pg_*` role is refused for the three roles, also the harmless ones."
- The three calls and the exit codes (2 refused and nothing kept; 5 applied and committed but not verified, or the commit's outcome unknown); that the statements go to standard output.
- "Before the commit the eight reads may each see the database at a slightly different moment; the check after the commit reads one consistent picture."
- "On objects outside the schema of the run, `migrate` judges what the three named roles and everyone can do, not what other roles can do."
- "A SECURITY DEFINER function of the migration role in another schema that only its owner may call is no longer refused."
- Upgrade note, in these words or plainer: "A setup with rights beyond the grant map is now refused before any file runs. Earlier versions only refused rights that changed during the run, so a database that passed before can be refused now. `migrate` prints one line per right and, on standard output, the statements that remove them. A database administrator runs those statements (they are REVOKE statements and membership removals; none of them changes data), then runs `migrate` again. Typical cases: a table of another application that everyone may read; a login used as runtime role that is also a member of a group; a function in the same schema, owned by the migration role, that everyone may call; a default right set long ago with `ALTER DEFAULT PRIVILEGES`. Two things `migrate` repairs by itself and does not refuse: rights the migration role itself gave the named roles on the package's own tables (they are reset to the grant map as before), and the right of everyone to call the package's own functions (removed as before). In a shared database, the check covers the whole database: any table of another application that everyone may read is refused, whatever schema it is in. If such an object belongs to another application that needs the right as it is, do not remove it: give this package a database of its own, or roles that no other application uses. A schema of its own is not enough." (D-m6)
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

1. AUTHOR ADDITION, baseline line 1: a grant on a system object that names a named role itself, or a subject role that is not built in, is judged (rev 2: rights through a built-in `pg_*` role are one membership line, no statement against a system object). D-020 says system objects are not judged. Default taken: judged (stricter; fact 21 shows no false refusal on a fresh server). The lead may strike it.
2. CORRECTION, baseline line 3: row types are left out of "everyone gets nothing on family objects", with the exact key of fact 33. Without this every database is refused (fact 11). No alternative offered.
3. STRUCK in rev 2: rule O5 (other members of a group that owns a package object). Plan review D-M7 showed a false refusal on a normal setup with no way out; S3 already refuses a named role in that group. Stated as a non-promise in 1.4.
4. AUTHOR ADDITION, the pre-flight ignores exactly the two things the run repairs itself (4.1 step 2), and since rev 2 only when the migration role is the grantor (fact 31). Without it every upgrade from main is refused before any file (main never removed everyone's EXECUTE from the trigger function). Alternative: no exception and a hand step for every upgrade; safe but a worse upgrade.
5. A function or type of another application that the migration role owns in the schema of the run and that everyone may use is refused at the pre-flight (3.4 line 3), where round 12 left it alone. Default taken: refused, with the REVOKE printed. OWNER QUESTION (in handover/questions-for-lead.md): is sharing the migration role, or the schema, with another application a supported setup at all? (D-020: the package does not require a schema of its own.) The answer also decides item 11.
6. TEMPORARY for everyone on the database: stated baseline, not judged (D-020). An explicit TEMPORARY grant naming a subject role: refused (default taken here); the oracle sees it only on fixture variant (T).
7. A migration role that owns the database or holds CREATE on it: allowed (D-020), named in the hardening guide. Fact 14 shows what it enables (now settled, "Read first" item 5); `verify` judges the result.
8. Exit code 5 and a new error class outside `ConfigError`: default taken. Alternative: a subclass of `ConfigError` with exit 2; rejected because exit 2 means "refused, nothing happened" in this command line. Rev 2 adds the unknown COMMIT outcome to exit 5 and a server-refused COMMIT to exit 2.
9. DECIDED in rev 2: `effective_problems` is removed (its only outside callers are retired tests).
10. The CI route for `max_prepared_transactions` above 0 is still untried (6.3 names the first and second route). Safe default: the test FAILS when the setting is 0, on every machine, so a vacuous pass is impossible.
11. AUTHOR ADDITION (rev 2, D-M6): the object side reads only the schema of the run, which narrows D-020's "objects the migration role family owns". Option (b) of the design review, taken because option (a) would refuse a migration role shared with another application, which is the owner question of item 5. If the owner answers "not supported", option (a) costs one changed WHERE clause in Q2, the C10 third-role cells become promised, and its own mutant and tests are added; that would be a new ticket revision.
12. Statements on standard output, problem lines on standard error (4.2, D-m3). Alternative: a file written by `migrate`; rejected because a library that writes files where it was not asked to is a surprise for the caller.

### 10.4 What I did not verify (rev 2)

- Anything on PostgreSQL 17 or 18 (fact 25 is from memory). The rev 2 probes ran on 16.15 only.
- The cost of the final Q2 and Q3 on a large catalog: fact 40 is a small setup (Q2 16.8 ms). Acceptance 21 measures it.
- That the printed statement forms work for every kind (aggregates with `*`, procedures, large objects, parameters, tablespaces, default rights with `IN SCHEMA`): facts 30-32 cover table, column and membership forms only. `test_printed_statements_remove_every_problem_for_every_grantor_form` tests the rest.
- Whether a role-level `statement_timeout` of 5 ms reliably cancels Q2 on the CI runner (fact 36 used 1 ms on an idle laptop-class machine); the dedicated test checks this itself first and fails loudly if not.
- `file_fdw` and `allow_in_place_tablespaces` in the CI image `postgres:17.10`: from the PostgreSQL documentation, not run.
- That `REVOKE GRANT OPTION FOR ... CASCADE` printed AFTER the dependents (4.2 order) leaves nothing behind for column grants (fact 30 shows a column grant can survive a table-level CASCADE; the order prints the column REVOKE first, and the statements test checks the end state).
- How `pg_terminate_backend` during a commit-time trigger is reported by psycopg 3.3 (SQLSTATE 57P01 with the connection closed is expected from reading; `test_a_lost_connection_at_commit_gives_exit_5` will show it).
- The behaviour of Q3 for objects of kinds I did not create (operators, collations, text-search objects, publications, event triggers): rule S4 reads them through `pg_shdepend` whatever the kind, by fact 12 for the kinds seen.
- Whether two prepared transactions can really share one virtual transaction id (6.1 handles it either way).
- The plain-role refusal text for `session_preload_libraries` (fact 13, second half).
- The descriptions of external tools in section 8 (pg_permissions, pgTAP, ldap2pg) are from memory, not researched live.
- The run time of the mutant list (30+ minutes is the readiness reviewer's studio figure) and of the matrix: not measured.
- The CI workflow steps beyond the lines grepped (40-47, 84, 92-94, 100, 110-117, 153, gitleaks block 163-209).
- TICKET-P3a.md and BUILDER-ticket-notes.md were not read by either author.
- No test, lint or mutant of the repository was run by the rev 2 author. The rev 2 author ran PostgreSQL and psycopg probes only.


## 11. Every plan-review finding of round 1, with its answer (rev 2)

Prefix R = implementation-readiness review (plan-r1-readiness-full.md), D = design review (plan-r1-design-full.md). "Fixed" means the ticket text now says it; nothing is built.

| finding id | answer | where in the ticket |
|---|---|---|
| R-B1 commit order not buildable | Rebuilt: verify beside the old code, oracle, then ONE switch commit (deletion + new order + test and mutant changes together), extras, matrix, texts; per-commit green command includes `test_every_migrate_mutant_still_applies_to_the_source`; mutants change in the same commit as their code | 9.3 |
| R-B2 O2 refuses the `public` default | Everyone's USAGE on the schema of the run allowed; O7 covers everyone (CREATE for everyone refused); `public` test plus sensitivity control (fact 34) | 3.3 O2, O7; 7.6; 9.1 item 23 |
| R-M1 step-8 option breaks fixtures; wrap step 8 | Option dropped (also not accepted by `connect`, fact 35); all of step 8 in one `try`, any exception -> exit 5 | 4.1 step 8; 4.2; fact 35 |
| R-M2 oracle environment | Superuser required (failure, not skip); one database per case (24 ms, measured); variants P, O, C, T defined; `CALL` for procedures; typed NULLs; `RESET SESSION AUTHORIZATION`; unknown codes INCONCLUSIVE; whole-word ban list | 7.2 |
| R-M3 tests and mutants outside the lists | Named: fake-db wiring tests, test_k2_migrations.py, CHANGELOG and docstring pins, phrases that must survive, nesting for `_upgrade_bullet()`, MT1/MT2, R23, SH1, 16 re-checked | 5.4b, 5.5, 9.5 |
| R-M4 acceptance commands | Every item names a test id or command; `--include='*.py'`; item 3 covers comments; DSN and batching in item 12; `migration_numbers_mutants.py` command; builder-notes table is Blocker-level | 9.1 |
| R-M5 run time, heavy jobs, time box | Four mutant batches with `--list-batch`, `timeout 3000`, heavy_slot where it exists (it does not in this repository), time-out procedure; work packages A1, B1, A2, C1, B2, C2 of at most 60-minute sessions | 7.10, 9.4 |
| R-M6 circular import, default binding | New module never imports `migrate`; `_label` moves to `migration_numbers`; reviewed list passed at call time with no default; TPG:2804 patch value updated | 3.1 |
| R-M7 missing definitions | Rights per role kind table; schema-USAGE rule without `has_*`; step-4 query; `PROBLEM_KINDS`; full Q2 with changes (a)-(d) and the temp/toast filter, run as a plain role | 3.2, 3.3; fact 40 |
| R-M8 old-head proof | Adapter defined; only the "applied with excess:" assertion counts; no module-level import of the new module; version/self-check/message tests removed from the proof | 7.9 |
| R-M9 upgrade-from-main test | Emulates main's state (files, ledger, map grants, PUBLIC EXECUTE on the trigger function); claims exactly that | 7.6 |
| R-Mn1 `effective_problems` | Removed | 5.2, 10.3 item 9 |
| R-Mn2 other stale CL:34/CL:15 MAINTAIN sentences | Deleted, one new sentence | 1.5 |
| R-Mn3 `_scan` data shape | `found` dict unchanged; second dict for the first file | 6.4 |
| R-Mn4 CI route | First: `docker exec ... ALTER SYSTEM` + `docker restart` + bounded `pg_isready`; second: `docker run` step | 6.3 |
| R-Mn5 row-type key | `typtype='c' AND typrelid<>0 AND relkind<>'c'` (fact 33) | 3.4 line 3, Q2 |
| R-Mn6 `file_name` at step 6 | Constant `END_OF_RUN` | 4.1 step 6 |
| R-Mn7 step 5 versus `_limit_error` | `_limit_error` wins for 55P03/57014 with its own step name; other errors wrapped | 4.1 step 5 |
| R-Mn8 cli docstring | One `migrate` line with exit codes 0, 2, 3, 5 | 4.2 |
| R-Mn9 promise-table marker | `[promise table]` ... `[end of promise table]` in both texts | 9.1 item 6, 9.5 |
| R-Mn10 mutant count | 288 - 29 + 55 = 314 (rev 1's 7.5 list counted 42; minus O5, plus O8, plus 13 new) | 5.5, 7.5 |
| R-Mn11 docstring rewrite vague | Module list "What migrate does, in order" rewritten to the eight steps; phrases that must survive listed | 9.3 commit 6, 5.4b item 3 |
| R-A1..A8 stale citations | CL:12->CL:11; MN:680-683->677-679; TPG:242 is a context manager exit (7.8 exempts functions with `yield`); TW:192/208 claim struck; TW:1244 needs no re-point; MIG:283-366->283-372/295-372; MUT time 30+ min; 280/288 resolved (279+9) | 1.5, 5.2, 5.4, 6.3, 7.8, 7.10, Read first 5c |
| R-B list (deleted names, callers) | `_TABLE_PRIVS`, `_SERVER_VERSION_SQL`, `_MAINTAIN_FROM`, `_table_privs`, `_SCHEMA_USAGE_SQL` added to the delete list; MT1/MT2 retired; R23 re-pointed; `REVIEWED_DEFINER_FUNCTIONS` type change handled | 5.3, 5.5, 3.1 |
| D-M1 oracle cannot see half the effects | Effect -> attempt table for all 37 plus E38/E39; default rights via fresh objects created as the migration role and every case role; every column; UPDATE without SELECT | 7.2 |
| D-M2 step-8 failures become exit 2 | All of step 8 wrapped (exit 5); limits set inside `verify`; test with a role-level `statement_timeout` (fact 36) | 3.1, 4.1, 7.6 |
| D-M3 COMMIT outcome | Server-refused (SQLSTATE, connection open) -> exit 2; anything else -> exit 5 "may or may not" (fact 37); two tests | 4.1 step 7, 4.2, 7.6 |
| D-M4 fix against built-in role damages the server | Rights through `pg_*` roles are one S2 membership line; never a statement against a system object; test prints exactly one statement (fact 38) | 3.1, 3.3 S2/S5, 3.4 line 1, 7.6 |
| D-M5 grantor ignored | `Problem.grantor`; `SET ROLE <grantor>` form for objects (GRANTED BY refused for objects, fact 30); `GRANTED BY` for memberships (fact 32); order dependents first; generator cells E38, E39 | 3.1, 3.3, 4.2, 7.2 |
| D-M6 object side limited to the run schema | Option (b), stated as AUTHOR ADDITION narrowing D-020; C10 third-role cells "not promised"; CHANGELOG sentence; option (a) cost and its blocker (owner question) written | 3.3, 7.4, 9.5, 10.3 items 5 and 11 |
| D-M7 rule O5 false refusal | O5 struck; non-promise in 1.4; E27 becomes a control | 1.4, 3.3, 7.2, 10.3 item 3 |
| D-M8 `options` at step 8 | Dropped; test with a role switch in the DSN (fact 35) | 4.1 step 8, 7.6 |
| D-m1 operator capture | Fact 26 corrected; every runner catalog read pinned through `pinned_read`; AST test | facts 26; 3.1; 7.6 |
| D-m2 exponential closure | `UNION` closures; 25-level diamond: 1.9 ms against a cancelled old shape (fact 40); cost cell and mutant | 3.2, 7.5, 7.6 |
| D-m3 uncapped statement printing | Statements on standard output (redirectable), problem lines capped at 20 on standard error | 4.2, 10.3 item 12 |
| D-m4 step 5 wording | "a deferred check or trigger" | 4.1 step 5 |
| D-m5 `repaired_by_run` and grantor | Only when the migration role is the grantor (fact 31); test and cell E38 | 4.1 step 2, 7.6 |
| D-m6 upgrade note "schema of its own" | Reworded: a database of its own or unshared roles; "a schema of its own is not enough" | 9.5 |
| D-m7 promise table and hidden COMMIT | "unless a file ended the transaction itself" in 1.3 and step 6 | 1.3, 4.1 step 6 |
| D-m8 oracle expectation for everyone | Expected set holds the baseline; controls include another application's function and type | 7.2, 7.4 |
| D-m9 row-type carve-out | Exact key; six relation kinds plus standalone composite; sequences have none (fact 33); test after the GRANT materialises the list | 3.4 line 3, 7.6 |
| D-m10 cost fixture, limits, snapshots | Larger fixture (functions, column grants, large objects, roles, diamond); statement limit is 60 s per statement (the reviewer's "30 s above the limit" was a misreading: `RECIPE_TIMEOUTS` says 60 s); one snapshot at step 8 (REPEATABLE READ), stated in the CHANGELOG | 3.1, 7.6, 9.5 |
| D-m11 coverage gaps | F2 audit-trigger test; C-F9 real-server test; exact counts with empty-by-logic table; problem kind per effect for outcome (ii) | 5.6, 7.3, 7.4, 7.6 |
| D-m12 step 8 has no lock | Kept without a lock; message says "this run or another session since the commit"; non-promise in 1.4 | 1.4, 4.1 step 8, 4.2 |
| D small point: argument names in fixes | The "plain" test covers the whole argument list; message-safety test has an argument name | 3.1, 7.6 |
| D small point: S2 refuses benign `pg_*` roles | Stated in the CHANGELOG | 3.3 S2, 9.5 |
| D small point: 288 versus 280 | Resolved: 279 + 9 | Read first 5c |
| D question (4) item 3: family SECURITY DEFINER in another schema only its owner may call | Passes now; CHANGELOG sentence | 3.3 S7, 9.5 |
| D question (5): expected table must know MAINTAIN on 17 | MAINTAIN is in no `Grant`, so it is never expected; the oracle tries `REINDEX TABLE` on every relation (MAINTAIN on 17) and it must be refused for every named role and everyone | 3.2 (last line), 7.2 |
| D-020 points the design review called incomplete | Object-side scope (D-M6), row 2 up to the commit and hidden COMMIT (D-m7), failing check after commit (D-M2/M3): each answered above | 1.3, 3.3, 4.1 |
| Rev 2 author finding: rev 1 dropped the refusal of a package table handed to a third role in the schema of the run (found while answering D-M6; the old comparison refused it) | Rule O8 in `verify` (all three calls), Q2's third clause widened and re-run; two family-group handover tests retired, the run-schema test re-pointed to a third role | 3.2, 3.3 O8, 5.4, 7.5 |
| Rev 2 author finding: with the path pinned, `current_schema()` answers `pg_catalog`, which would break the kept reads that use it | Those reads take the step-1 schema as a parameter; acceptance 2b | 3.1, 9.1 item 2b |
| Rev 1 open conflict: extension owner | Settled by a rev 2 run: the installing role owns it | Read first 5, fact 14 |

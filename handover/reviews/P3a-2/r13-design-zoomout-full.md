<!-- full hand-back reports (main report, then addendum) of sub-agent a26d1a15, saved verbatim by the lead's script; model output, nothing in it was run -->

ZOOM-OUT PLAN REVIEW: P3a-2, decision D-019, before round 13. Mode: REVIEW. Read-only; nothing was run.

Every PostgreSQL fact below is from memory unless marked "read in code". Facts marked (M) carry the design and need a probe before a ticket relies on them. They are collected as P1-P8 near the end.

## 1. Recommendation

Choose option B, but narrower and differently scoped than D-019 words it. D-019 is not ready to become a ticket as written (2 Blockers, 5 Majors below).

The round-13 design in one paragraph: one catalog-only function, `verify`, judges the final state against the grant map. It reads from the side of the subjects (each named role plus every role it is a member of, and PUBLIC) and from the side of the objects the migration role family owns. It never asks "what changed" and never uses `current_user` to define scope. It is called three times:
- before the first file (existing excess: refuse, nothing changed);
- as the last statements before COMMIT, after all of the runner's own writes and `SET CONSTRAINTS ALL IMMEDIATE` (refuse and roll back);
- after COMMIT on a fresh connection (loud failure, no automatic repair).

The before/after change comparison is deleted. Text rules stay as refusals but carry no security claim.

Three strongest reasons:

1. **A hostile file is not a coherent adversary for this runner, so twelve rounds chased a promise nobody can keep.**
   - The files ship inside the package and are pinned by SHA-256 in `migrations_released.json` (read in code). Whoever can land a hostile file can equally edit `GRANTS` or `migrate.py`.
   - The file runs as the owner of every table. It can read or change all data, do something and undo it, or leave code that fires later. No privilege check sees any of that.
   - The five shipped files contain one plain trigger function and four triggers: no grant, no SECURITY DEFINER, no extension (grep of main's folder).
   - The honest promise is: mistakes and careless files are stopped; persistent privilege excess is detected whatever caused it; a hostile file is not stopped.

2. **A state check read from the subject side is closed; "everything the migration role can reach" is not.**
   - F3, F5, F6 and F7 are all scope holes of the `@MINE@` / `changed_*` construction (migrate.py:838-839, 926-927, 950-955).
   - "For each named role and PUBLIC: every right it holds in this database must be in the allow-list" has no `current_user`, no extension exclusion, no "changed in this run" and no session-user question.
   - The seed already exists on main: `effective_problems` (main migrate.py:193-262).

3. **A check in the same session can be lied to; I found an eighth route by reading.**
   - Every catalog read in migrate.py uses unqualified names (`FROM pg_class c JOIN pg_namespace n`, `'pg_class'::regclass`, `pg_roles`; migrate.py:304, 318, 433, 834-907).
   - (M) `pg_temp` is searched before `pg_catalog` for relation and type names when it is not listed in `search_path`.
   - So `EXECUTE 'CREATE TEMP TABLE pg_class AS SELECT * FROM pg_catalog.pg_class WHERE false'` in a function body may blind every state query of the same session.
   - The read-back does not see it: `search_path` is unchanged and the trigger read-back only reads `current_schema()`.
   - Not reproduced. Give it to the evidence runner as F8.
   - It shows that "nothing file-reachable after the last check" is another open list. Only a fresh session after commit, with qualified names and a pinned search path, is sound by construction.

## 2. Findings on D-019 as written

**Blocker 1. The threat model is posed as a question while the chosen design already promises against the hostile case.**
- Scope: D-019 "Options (B)" and "Root".
- Rationale: "nothing file-reachable afterwards" and "whatever happened and whenever it happened" are hostile-file promises. If the ticket inherits them, round 13 is another route hunt: F8 above, the leftovers under answer (2), and the unbounded "code that fires later" class.
- Fix: the ticket states a three-row promise table (answer 1) before any design text.

**Blocker 2. The scope "everything the migration role can reach" is the wrong axis.**
- Scope: D-019 "Root (c)"; D-009 "comparison scoped to objects the migration role owns or granted".
- Rationale: it is defined through `current_user` (F7). It excludes rights a named role got from someone else (F5, F6). It needs carve-outs for extension members (F3) and for object kinds (F4).
- An over-privileged runtime role is over-privileged whoever granted the right.
- Fix: D-019 must supersede the D-009 scope sentence explicitly.

**Major 1. "The last possible moment before commit" is not closed.**
- Scope: D-019 option B, "constraints made immediate, nothing file-reachable afterwards".
- Rationale: besides deferred triggers, file code can sit in: a rule on the ledger, a column default on `schema_migrations.applied_at`, an expression index, a check constraint, a forced row-security policy on a table the runner touches, session state, or temp objects (F8).
- Keep the pre-commit check for its rollback. Do not claim it is the sound one; the post-commit fresh-session check is.

**Major 2. The outcome of a failed post-commit check is undecided.**
- Scope: D-019 names "a compensating action or loud failure" only in the question.
- Rationale: an automatic REVOKE in an unknown state is new privileged write logic, and can be undone by the same actor. See answer (3) for the simple rule.

**Major 3. PUBLIC's default rights make "equals the allow-list" unachievable as worded.**
- Scope: D-019 "compare it with a written allow-list".
- Rationale: (M) PUBLIC has by default EXECUTE on every function, USAGE on types and languages, CONNECT and TEMPORARY on the database.
- CHANGELOG.md:17 "no right on a function" can never be literally true. A written baseline is required (answer 2).

**Major 4. "Text rules only as warnings" would remove two rules the runner's own guarantee needs.**
- Scope: D-019 option B, last clause.
- Rationale: the transaction-control and `SET`/`RESET` refusals protect the one-transaction rollback. The hidden-character and lexer refusals protect the scan. They must stay refusals.
- What changes is their claim ("catches accidents early"), plus a process rule: a bypass of a text rule is no longer a finding.

**Major 5. A state judgement refuses setups that pass today, and D-019 has no pre-flight.**
- Scope: missing from D-019.
- Rationale: without a check before the first file, an existing excess would fail the run after the files ran, or after commit. The pre-flight call makes that "refused, nothing changed" and needs an upgrade note.
- Also missing: the real control for mistakes in our own files is a CI run of the shipped files on a clean server with an independent oracle. The files are static and hashed, so their effect is decidable before release.

**Nit 1.** D-019 says "final state of everything". The check is about privileges, owners, memberships and default rights. Trigger integrity (F2's example disables the audit triggers) is a different property and should not be folded in.

**Nit 2.** The docstring (78 lines) and CHANGELOG.md:17 (one paragraph of about 900 words) describe routes. A promise table replaces them, and each round's findings are then classed against the table.

**Nit 3.** "No builder until the reproductions are in" is right. Add F8 and probes P1-P8 to that gate.

## 3. Answers

### (1) Threat model

Who writes files: the studio's builders, into `src/hadavin_sdk/store/migrations/`, reviewed and hashed. I found no mechanism for a client to add files to that folder, and none should be built. A client's engineers who need migrations get their own migration role and their own schema. Role separation is the control there, not this runner.

| Adversary | What a runner connected as the owner can guarantee | Honest word |
|---|---|---|
| (a) honest mistake in our file | Refusal with rollback of any persistent privilege excess in the final state; and it is caught before release by the CI run | stops |
| (b) careless or copied file | The same, for persistent privilege state only. Nothing about data loss (`DROP`, `DELETE`): that is the snapshot and the column-safety check. Nothing about code left to fire later | stops privilege excess; nothing else |
| (c) deliberately hostile file | Prevention: none. Detection: persistent privilege excess present at the moment of the post-commit check, and only as far as the checker's reads cannot be faked | detects; does not stop |

Never detectable from inside the same role, in any number of rounds:
- a change made and undone;
- reading or altering data;
- code left behind in a trigger, rule, default, view or function body that runs later as whoever touches the table (including a superuser administrator);
- a re-grant after the check;
- effects outside the transaction (dblink, sequences).

The real controls for (c) are elsewhere:
- code review plus the released-file hash (exists);
- a separate verifier identity with CONNECT only, reading the catalog after commit and on a schedule. (M) The privilege-inquiry functions and the catalog ACL columns are readable by any role;
- a migration role that does not own the database and has no CREATE on it. Note the snapshot allows `pg_database_owner` at migrate.py:611;
- an event trigger installed by a superuser that logs GRANTs ((M) superuser-only, so it is the client's administrator's choice);
- a database of its own per application;
- for audit rows, the hash chain (`audit verify`), not the trigger.

Promises in the current texts that no number of rounds can keep:
- **migrate.py:38-41 and CHANGELOG.md:17**: "finds an object that a file made or changed in any schema, by any statement, also by dynamic SQL" and "whatever way the file did it".
- **migrate.py:36-37**: "so a file cannot leave the migration role with what the first check refused".
- **migrate.py:296**: `effective_problems` "what the role can REALLY do, however it got it". (M) A membership that does not inherit is not counted by `has_*_privilege`.
- **migrate.py:1240**: "Nothing was changed. The whole run is undone." This is false after a hidden commit or a second connection, which the same docstring admits at lines 32-33.
- **CHANGELOG.md:17**: a named role "gets no right at all ... in any schema, and no right on a function". False through the PUBLIC baseline. CHANGELOG.md:15 contradicts it, as F6 noted.
- **CHANGELOG.md:12**: "could reach beyond this package's own objects" reads as a sandbox claim.
- **Any wording implying a clean run means a clean database later.** Another session can grant one second after the check; the advisory lock is cooperative.

### (2) Design, worked through on F1-F7

Reading from the named roles' side is the simpler and closed formulation, yes. It needs a second, small object-side rule, because rights of third roles on our tables and runs with no role arguments are invisible from the named roles' side.

**Subject side.** Subjects are each named role, every role it is a member of (transitive, any option), and PUBLIC. For each subject:
- none of the five flags, on the whole membership closure;
- no membership in a `pg_*` role;
- owns nothing in this database;
- effective rights on every non-system object are a subset of the allow-list;
- no default right in its favour, from any role's `pg_default_acl` row, selected by grantee and not by `defaclrole`.

**Object side.** For each object in the run schema owned by the migration role or a role it belongs to (the migration role is passed as a parameter, not taken from `current_user`):
- grantees are a subset of {owner, named roles per the map};
- no grant option;
- nothing for PUBLIC;
- no SECURITY DEFINER unless on the reviewed list;
- extension membership is not an excuse.

**What the state query must cover.** The closed list is the privilege table of the PostgreSQL GRANT documentation ((M) 14 kinds): table-like relations, columns, sequences, databases, domains, types, functions and procedures, foreign-data wrappers, foreign servers, languages, large objects, parameters, schemas, tablespaces. Plus default ACLs, memberships, role flags, owners.

Two catalog features make it closed instead of hand-listed:
- (M) the set of catalog columns of type `aclitem[]` can be derived from `pg_attribute`. One self-check query at run time compares that set with the set the code reads, and refuses a server that has an ACL column this version does not read. That closes F4 and round-11's "PostgreSQL 18 kind L" by construction.
- (M) `pg_shdepend` records every object that a role owns or is named in the ACL of, for any object kind. One query gives "this named role owns nothing and is named nowhere unexpected".

`session_user` versus `current_user` matters only for the migration-role checks that already exist (`_refuse_privileged_role`); `verify` uses neither.

**F1-F7:**

| Finding | Result under this design |
|---|---|
| F1 deferred trigger at commit | `SET CONSTRAINTS ALL IMMEDIATE` fires it before the pre-commit check, so the usual case rolls back. Anything else at commit is seen by the post-commit check (PUBLIC on `audit_entries` is an object-side hit). Falls away. |
| F2 trigger on the ledger | The privilege variant falls away by order (all runner writes before the check). The variant that disables the audit triggers is not a privilege: run the existing `_check_read_back` once more at the final point, and say it protects against mistakes. Remains as a stated limit against a hostile file. |
| F3 extension member | Falls away. Scope is by owner, and the named roles' EXECUTE on `door` through PUBLIC is a subject-side hit. |
| F4 kinds never read | Falls away through the derived ACL-column list. (b) is also `has_database_privilege(role, db, 'CREATE')`. |
| F5 existing memberships | Falls away through the membership closure. |
| F6 rights that existed before | Falls away. Nothing is "changed"; the pre-flight reports it before any file runs. |
| F7 login switches role | Falls away. `other.l_table` readable through PUBLIC is a subject-side hit whoever owns or granted it. |
| F8 temp table shadows the catalog (new, unreproduced) | Closed only by a fresh connection, `pg_catalog.`-qualified names, and `SET search_path = pg_catalog, pg_temp` as its first statement. |

**PUBLIC's baseline, handled honestly.** Write it down as four lines and print it in the docs:
1. Objects in `pg_catalog` and `information_schema`: not judged (the server as shipped).
2. Kinds with no PUBLIC default (relations, columns, sequences, CREATE on a schema or the database, large objects, servers, wrappers, tablespaces, parameters): judged everywhere, effective rights, refused. Any hit is a real non-default grant.
3. Kinds with a PUBLIC default (functions, types, languages):
   - on objects of the migration role family, PUBLIC gets nothing (the runner already revokes, migrate.py:1253);
   - a direct grant to a named role anywhere is refused;
   - PUBLIC's default on other owners' objects is not judged, with one exception: a SECURITY DEFINER function outside the system schemas that a named role can execute is refused unless it belongs to an extension the family does not own.
4. CONNECT is expected. TEMPORARY through PUBLIC is stated as baseline. This is an owner question; the stricter choice is to refuse.

### (3) Order, and what a failed post-commit check does

Smallest sound order:
1. Existing role checks, lock and limits (unchanged).
2. `verify` pre-flight, excess only. Refuse; nothing changed.
3. Files, with the existing per-file read-back. It names the file, which a state check cannot.
4. All runner writes: ledger rows, grants, PUBLIC revokes.
5. `SET CONSTRAINTS ALL IMMEDIATE`.
6. Final read-back and `verify`: catalog-only, qualified, touching no user relation. Refuse and roll back.
7. COMMIT.
8. New connection, `verify` again.

If step 8 fails:
- Raise a distinct error and exit code.
- Say plainly: the files are applied and committed; the database is over-privileged now.
- Print the exact REVOKE statements.
- Do not print "applied" as success.
- No automatic REVOKE, and no new ledger state.

Reasons:
- Step 6 already rolls back everything a mistake can do. So a step-8 failure means deliberate commit-time code or another session, and both need a person.
- "Applied" is true of the ledger. "Verified" is a property of the database now, and running `migrate` again with nothing pending re-checks it.

Is this acceptable under "mistakes cannot cause damage"? Yes for mistakes. For hostility the honest sentence is "detected and reported, not prevented", and the texts must say so.

### (4) Improve before replace

**Keep:**
- all of `migration_numbers.py` (names, ledger, released list, lexer);
- the lock handling and time limits;
- `_refuse_privileged_role`, `_refuse_foreign_owned`, `_apply_grants`;
- `effective_problems`, as the core of the subject side;
- the reading of `_ACL_DEFAULT_SQL` and `_BUILT_IN_DEFAULT`, `_ACL_SCHEMA_SQL`;
- the SECURITY DEFINER rule and the PUBLIC revoke;
- `_check_read_back` (session values, hidden-commit detection, triggers, memberships);
- `_shown`, `_label`, and the mutant runner and list.

**Change:**
- `effective_problems`: all non-system schemas, all kinds, the membership closure, and set-based queries. Today it sends one statement per role, relation, right and column.
- The ACL queries lose the `changed_*`, `kept_*` and `judged` inputs, and select default rights by grantee.
- The order of `migrate` (answer 3).
- Qualified catalog names.
- A plain refusal below PostgreSQL 16 (m4).
- The texts.

**Delete:**
- `_Objects`, `_objects`, `_Changed`, `_changed_ids`, `_kept_owner_ids`, `_changed_since`;
- `_FUNCTION_STATE_SQL`, `_RELATION_STATE_SQL`, `_SCHEMA_STATE_SQL`;
- `@ME@` and `@MINE@` as scope.

Written reason for the deletion: every excess a change can produce is present in the final state, so the comparison detects nothing the state judgement does not. Meanwhile it cannot see what existed before (F6), it confuses other sessions with files (round-11 M1/M4), it needs the scope carve-outs behind F3 and F7, and it reads every function and relation of the database twice per run.

**Text rules:**
- Delete none in round 13 (churn in tests and mutants, no safety gain).
- Reword `refused_statements` and `_GRANT_TARGET` to "early, plain refusal for accidents".
- Cleanup candidates for a later ticket: `_GRANT_TARGET` (its stated reason, "the read-back does not look there", disappears) and the `_RENAME_OWNER` exemption.

### (5) Scope

See section 5 below.

### (6) Tests so that round 14 is not a route hunt

**Property.** For every generated case, exactly one of:
- (i) refused before commit, and the oracle's snapshot equals the pre-run snapshot;
- (ii) the not-verified error was raised;
- (iii) returned "applied", and the oracle finds no excess for any named role or PUBLIC.

Forbidden: "applied" with excess.

**Oracle.** A separate superuser connection that shares no query with the implementation and does not read ACLs at all. It switches to each named role (`SET ROLE`) and attempts the operation inside a savepoint: each table right, `nextval`, calling a function, CREATE in a schema, CREATE SCHEMA, reading a large object, switching to each role. It classes the result by error code 42501 or not. This is the negative test least-privilege rule item 5 asks for. A second oracle for (i): `pg_dump --schema-only` and `pg_dumpall --roles-only --no-role-passwords`, text-equal before and after.

**Sensitivity control (mandatory).** Each generated route is also applied raw, without `migrate`, and the oracle must then report the excess. A cell that cannot be made live on a plain role is listed by name with the server's error, never silently counted.

**Generator.** Enumerated, not random:
- effects: about 30 (one per privilege kind of the GRANT table, grant option, owner handover, membership with and without inherit, default rights by kind and scope, SECURITY DEFINER flag; grantee named, PUBLIC or third role);
- carriers: about 12 (plain statement; split-word dynamic SQL in a called function; string-bodied SQL function; trigger on the ledger; trigger on a grant-map table; deferred constraint trigger; rule or default on the ledger; extension membership; role switch with login different from role; other schema; temp catalog shadow; already present before the run with no file).

**Minimum counts:**
- every effect with every carrier once (about 360 cases);
- every effect as pre-existing state (30);
- 200 seeded compositions of two or three routes;
- clean-file controls that must return "applied".

**Other requirements:**
- real server only;
- PostgreSQL 16 (stated floor), 17 (CI) and 18; check live whether a newer major is released on the build day;
- the ACL-column self-check runs on each version;
- one mutant per clause of `verify`;
- the retired change-comparison tests and mutants are listed by id.

"Round 14 not needed" cannot be promised. What changes is that a new finding is either inside a stated non-promise or a bug in a 14-row table.

### (7) Existing tools (all from memory; check live before quoting)

- **pg_permissions (extension):** views of all rights plus a desired-state table and a diff function. Closest in idea. It needs a server-side install, which a managed database may not offer. (M) It covers neither memberships nor all kinds. Not a runtime dependency; an idea source.
- **pgTAP:** `table_privs_are`, `function_privs_are`, `is_member_of` and similar. It asserts named objects, not "nothing else anywhere", and needs an extension. Possible as a test aid only.
- **ldap2pg, Terraform postgresql provider, Ansible:** declarative grants with drift reporting for declared objects. An external binary and the client's choice. Document as an option, not in the runner.
- **Event triggers:** installing one needs superuser, so not from the runner. A client hardening option.
- **`pg_dump` / `pg_dumpall` diff:** the broadest state check (it also sees triggers, rules, defaults). But it needs a matching client binary, a golden text per major version, and normalised role names. Use it as the second test oracle and in the CI run of the shipped files, not at run time.
- **In the repository:** `effective_problems` on main is the reuse. The tick step `reprobe_sources` (runtime/tick.py:221) is the existing pattern for "probe the scope again and fail loudly if it widened"; the later verifier ticket should follow it. `pglast` is in the test group and should stay out of this.

Conclusion: no tool removes our one verify module. Two PostgreSQL features (the derived ACL-column list and `pg_shdepend`) make it closed.

## 4. Risks of this recommendation, one SQL example each

1. **Refusals caused by another application's state.**
   - Example: `GRANT SELECT ON other_app.prices TO PUBLIC;`
   - The pre-flight refuses, and the operator cannot fix it alone. Intended (fail closed), but needs the upgrade note and a message naming the owner.

2. **The baseline hides a door.**
   - Example: `CREATE FUNCTION other_app.run(q text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$BEGIN EXECUTE q; END$$;` (PUBLIC may call it by default.)
   - Covered only if baseline line 3's SECURITY DEFINER exception is built.

3. **A committed, open database between step 8 and a person's REVOKE.**
   - Example: an administrator's `GRANT ALL ON audit_entries TO PUBLIC;` committed between steps 6 and 7.
   - Detected, not prevented.

4. **The fresh session is still the migration role.**
   - Example: `ALTER ROLE migration_role SET search_path = evil, pg_catalog;` with a table `evil.pg_class`. (M) A role may set its own defaults.
   - Mitigation: qualified names and a pinned path as the first statement. The full fix is the separate verifier identity.

5. **A membership the inquiry functions do not count.**
   - Example: `GRANT boss TO runtime_role WITH INHERIT FALSE;`
   - Covered only if the closure query is right. The generator has this cell.

6. **Cost on a large catalog.**
   - Example: 20,000 partitions of another application in the same database.
   - `verify` runs three times and must be set-based. Measure once.

7. **A catalog assumption is wrong on some version.**
   - Example: `ALTER DEFAULT PRIVILEGES FOR ROLE x GRANT SELECT ON TABLES TO runtime_role;` not showing in `pg_shdepend`.
   - This is why default rights are also read directly by grantee, and why P1-P8 run first.

## 5. Proposed round-13 scope

0. **Gate.** Reproductions of F1-F7 and F8, and probes P1-P8 on 16, 17 and 18, are saved. D-019 is amended with the promise table and supersedes the D-009 scope sentence.
1. **Promise table** (stops / detects / not promised) in the module docstring and CHANGELOG. Remove the over-claims listed in answer (1).
2. **`verify(db, migration_role, named roles, grant map)`** returning problems: subject side and object side as in answer (2), the four-line baseline, catalog-only, qualified names, pinned search path, set-based, no use of `current_user` for scope.
3. **Run-time self-check** of the ACL-column set, and a refusal below PostgreSQL 16.
4. **New order of `migrate`** (answer 3, steps 1-8), including the fresh-connection check and the distinct error with printed REVOKE statements.
5. **Delete the change comparison** (answer 4) and retire its tests and mutants with a written list.
6. **Reword the text-rule docstrings.** Process rule in the ticket: a text-rule bypass is not a finding.
7. **Tests** as in answer (6).
8. **One CI test:** the shipped files on a clean server; the behavioural oracle shows each named role can do exactly the map, in both directions.

Split into separate tickets, with reasons:
- **(A) Read-only verify command for a CONNECT-only verifier identity, plus a scheduled re-check.** New command-line surface, a new identity, and `cli.py` is a hot file. This is the real control for hostility and for drift between runs, and it covers m9 (the hand recipe).
- **(B) "Required audit guards present" as a state check.** A different property; it belongs to the audit package.
- **(C) Text-rule cleanup.** Churn only.
- **(D) Client hardening guide** (migration role not the database owner, own database, event trigger, pg_hba). Documentation; the client decides.
- **(E) Row security, policies, view options (m3).** When the first one enters the grant map.
- **(F) Surviving minors** (m6, m7, m8, m10).

Owner questions:
- TEMPORARY through PUBLIC: baseline or refusal?
- May the package require its own schema?

## 6. What should not be built

- More text rules or spellings, or a SQL parser used for security.
- Per-route detectors (for example reading `tgdeferrable` to refuse).
- Before/after catalog snapshots.
- Automatic REVOKE or any other compensation.
- A ledger column or an "applied but not verified" state.
- A switch or a per-deployment exception list.
- Anything that needs superuser from the runner (event triggers, extension installs).
- A run-time dependency on `pg_dump`, pg_permissions or pgTAP.
- Support below PostgreSQL 16.
- Checks of other databases in the cluster.
- Any path for client-written files through this role.
- A sandbox for files.

## 7. What I did not check

**Nothing was executed.** No SQL, test, mutant or probe.

**Probes the design depends on (all from memory):**
- P1: `pg_temp` is searched before `pg_catalog` for relations and types (F8).
- P2: `SET CONSTRAINTS ALL IMMEDIATE` fires queued deferred triggers and covers constraints created later in the transaction.
- P3: no user code runs at COMMIT for a non-superuser after P2.
- P4: `has_*_privilege` ignores non-inherited memberships.
- P5: `pg_shdepend` holds owner and ACL rows for every kind, including default ACL grantees.
- P6: the `aclitem[]` column list per version.
- P7: PUBLIC's default rights by kind, and that a role may `ALTER ROLE ... SET` its own defaults.
- P8: startup-option and first-statement precedence over role and database settings.

**Not read or only partly read:**
- TICKET-P3a.md: lines 1-51 of 287 only.
- CHANGELOG.md: lines 1-70 only (not the repair runbook).
- `migration_numbers.py`: symbol list and lines 640-768 only (not the lexer body).
- Test files: counted only (418 test functions in 7 files), bodies not read.
- `tests/migrate_mutants.py`: header only.
- Not read at all: both DIFF patches, ROUND11-findings-design.md, the earlier round summaries (review-1, round-w2, BN, merge-fix1, r11 summaries, evidence.md beyond its first lines).
- `/home/user/hadavin-sdk/CLAUDE.md`: read by search only (the least-privilege line).
- Main's `migrate.py`: lines 190-349 and its symbol list.

**Other unverified statements:**
- The descriptions of external tools (pg_permissions, pgTAP, ldap2pg) and which PostgreSQL major is newest today.
- Whether any deployment today shares its database or schema with another application. That decides how often risk 1 bites.
- The cost of three `verify` calls on a large catalog.

**Files relied on:**
- /home/user/hadavin-sdk/handover/AUTONOMOUS-DECISIONS.md (D-009, D-019)
- /home/user/build/snap/p3a2-r12-4d328e3/src/hadavin_sdk/store/migrate.py (read in full)
- /home/user/build/snap/p3a2-r12-4d328e3/src/hadavin_sdk/store/migration_numbers.py
- /home/user/build/snap/p3a2-r12-4d328e3/CHANGELOG.md
- /home/user/build/snap/p3a2-r12-4d328e3/BUILDER-ticket-notes.md
- /home/user/hadavin-sdk/handover/reviews/P3a-2/r12-design-full.md
- /home/user/hadavin-sdk/handover/reviews/P3a-2/r11-design-full.md
- /home/user/hadavin-sdk/handover/reviews/P3a-2/r11-codebase-full.md
- /home/user/hadavin-sdk/handover/decisions/P3a2-history-memo.md
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/store/migrate.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/runtime/tick.py
- the eight rule files under /home/user/hadavin-sdk/.claude/rules/
- /root/.claude/plugins/cache/egm/egm/0.1.1/agents/zoom_out.md
- /root/.claude/plugins/cache/egm/egm/0.1.1/resources/document_standards/zoom-out-standard.md

---

ADDENDUM to my zoom-out review of D-019 (P3a-2), after reading /home/user/hadavin-sdk/handover/reviews/P3a-2/r12-codebase-full.md in full. Nothing was run; PostgreSQL facts are from memory.

The second review does not change the recommendation; it strengthens it. Its two Majors are the same two classes the design review found (standing rights judged only when changed; the extension filter hiding the package's own objects), reached independently. Both are artefacts of the change comparison and its scope carve-outs, which my recommendation deletes. Changes to answers (2), (5) and (6) follow.

## Answer (2), additions

Mapping of the code-details findings (prefixed C to keep them apart from the design review's F1-F7):

| Finding | Result under the recommended design |
|---|---|
| C-F1 inputs A and B: standing right in another schema, standing EXECUTE on an untouched function | Falls away. Same class as design F6: the subject-side check reads every right a named role holds, with no "changed in this run" and no "run schema only". |
| C-F1 input C: `ALTER TABLE audit_entries SET SCHEMA other; CREATE TABLE audit_entries (...)` | Falls away, and without the reviewer's fix of adding name and schema to the state tuple. There is no state tuple and no oid key any more. The moved table is a relation in `other` on which the runtime role still has SELECT/INSERT; it is not in the grant map at (run schema, name), so the subject side refuses it. |
| C-F2: `ALTER EXTENSION citext ADD TABLE audit_entries`, then `GRANT ALL ... TO PUBLIC` | Falls away. Same class as design F3. Scope is by owner, and extension membership is never an excuse for an object the migration role family owns. This must hold with NO role arguments too, which is why the object side and PUBLIC-as-a-subject are both required. |
| C-F4 second half: "`_refuse_foreign_owned` looked at it first" is false for unmanaged objects | Disappears with `_changed_since` and the `kept_*` sets: the sentence and the logic it excuses are deleted. |
| C-F7: no mutant on the grantor half of the scope, on `prolang`/`probin` | Disappears: the grantor clauses and the function state fields are deleted code. |
| C-F10 false refusal (migration role's own right on a group-owned object reported as a stranger's) | Must be carried into `verify` as a rule: the allowed grantees on a family-owned object are the owner, the migration role itself, and the named roles per the map. |

Two points the second review adds to what `verify` must do, which my first report did not state:

1. **The grant map must be matched by (schema of the run, name, kind), never by bare name.** C-F1 input C and C-F9 (`REVIEWED_DEFINER_FUNCTIONS` matched by bare name) are the same class: an allow-list entry that also excuses a same-named object elsewhere. The reviewed-definer list is keyed by (run schema, name, identity arguments).
2. **A duplicate `CREATE` of a grant-map name in the files is refused by `_scan`** (C-F1 sibling, MIG:232-234). It is a text rule for accidents, cheap, and it removes the one honest way input C arises.

One more route class confirmed by the second reviewer's "sound by reading" section: a named role that is a NOINHERIT member of a group with rights is not seen by `has_*_privilege`. That is my probe P4 and risk 5; the membership closure rule stands.

Also supporting the precondition in design F3 / C-F2: both reviewers note that the migration role may own the database or hold CREATE on it, and that `_refuse_privileged_role` (MIG:630-656) does not look at it. Under the recommended design this no longer opens a hole in the privilege check, but it belongs in the hardening guide (split ticket D), and the owner may want it refused outright. Add it to the owner questions.

## Answer (5), changes to the round-13 scope list

Amend item 2 (`verify`): add "allow-list entries matched by (run schema, name, kind); reviewed-definer entries by (run schema, name, identity arguments); the migration role's own right on a family-owned object is allowed".

Amend item 3: the minimum-version refusal is now confirmed by two reviewers (design m4, C-F8). State it as: a plain `ConfigError` from `server_version_num` below 160000, placed before the first catalog query that needs a newer server; write the floor in the CHANGELOG and remove the sentences that describe "PostgreSQL 14 and earlier" as a running case (CHANGELOG lines 15 and 17). Note that after the deletion of `_FUNCTION_STATE_SQL` the `pg_get_function_sqlbody` crash on 13 disappears by itself, but the refusal is still needed because the membership read relies on 16.

Add item 9: **`_scan` refuses a second `CREATE` of a grant-map name.**

Add item 10: **every name from the database goes through `_label` in every message of the kept code** (C-F6: `effective_problems` at MIG:316, 324, 339, 353, 365 and `usename` at MIG:1314 print raw names; a name with a newline or ESC reaches the log). `effective_problems` is rewritten set-based in item 2 anyway, so this costs nothing there; it is one line at MIG:1314.

Add item 11: **texts.** C-F4 first half (a file "cannot create a type or a domain" is false through dynamic SQL) and C-F10 wording go away with the promise table of item 1; the ticket should name these lines so the builder removes them rather than rewords them.

Split out, in addition to my list:
- **(G) Prepared-transaction message (C-F5).** Reasons: it is lock handling, which the redesign keeps unchanged; it is a correctness and operator-safety fix (naming five transactions and saying "finish the one that holds the lock" can lead to a wrong `ROLLBACK PREPARED` of another system's work); it has its own test problem (the real-server test is vacuous when `max_prepared_transactions = 0`, the server default, and reports as passed). Fix by joining the lock row to the holder, turn an unreadable `pg_prepared_xacts` into a `ConfigError`, and make the test skip visibly or run on a server configured above 0. It can ride in the same pull request if the lead prefers one batch, but it should be a separate ticket item with its own evidence line stating the server's `max_prepared_transactions`.
- **(H) Text-rule minor C-F3** (`ALTER TABLE ONLY rename OWNER TO r` passes the text rule). Under the process rule in item 6 a text-rule bypass is not a finding, and the owner state check catches it. The false CHANGELOG sentence ("a table ... called `rename` does not make an owner change pass") must still be removed in item 1. The regex fix goes to the cleanup ticket (C), where I would rather delete the `_RENAME_OWNER` exemption than patch it a third time (it was round-11 minor 1, round-12 fix, and now C-F3).
- **(I) Reuse nits C-F12** (`_routine_name` versus `sql.Identifier`; three caps of 20): fold into the cleanup ticket.
- **C-F11 test hygiene** (roles created before the `try`): fix in round 13 only for tests that survive; most of the named tests belong to the change comparison and are retired.

Not to build, in addition: do not add name, schema, extension-membership or any further field to the state tuples (the fix both reviewers propose for the move and the extension route). It is the thirteenth patch to the mechanism that is being removed.

## Answer (6), additions to the test design

New generator cells (carriers), each with the sensitivity control:
- **move and recreate:** `ALTER TABLE <grant-map table> SET SCHEMA other; CREATE TABLE <same name> (...)`; also a plain rename. Oracle expectation: the named role must not be able to read or write the moved table.
- **extension membership of a grant-map object** (table and function), followed by a grant to PUBLIC; run both with and without role arguments.
- **standing right, no file:** in another schema, on an untouched function in the run schema, and granted by a role other than the migration role (the grantor half that C-F7 says no test covers today).
- **same-named object elsewhere:** a function with a reviewed-definer name in another schema, and an overload, once that list is non-empty; today one unit case on the key shape is enough.
- **every case is run twice: with the three role arguments and with none.** C-F2 shows the no-arguments path is where the object side is the only guard.

Evidence requirements the second review shows are needed:
- The evidence file states, per server: version, `max_prepared_transactions`, and whether an extension the migration role can create or owns is available. A cell that cannot run on that server is listed as "not run here", not passed.
- A test that returns early on an unmet server condition must skip visibly, never report as passed (C-F5 (c)). Add a repository check, in the style of the existing `test_no_migration_test_skips_silently`, that no real-server test returns before calling `migrate`.
- Mutants: one per clause of `verify`, including the allow-list key (schema, name, kind), the "extension membership is no excuse" clause, the "migration role's own right is allowed" clause and the version refusal. The mutant list check should verify the parametrised id of a killer, which today it strips (C-F7).
- Message tests include one object name with a control character, so the `_label` rule of item 10 is pinned.

## What I did not check (addendum)

- Nothing was run; the second review's server claims (trusted extension creation with CREATE on the database, `ALTER EXTENSION ... ADD` ownership rule, the `pg_locks`/`pg_prepared_xacts` join, `pg_get_function_sqlbody` from 14) are its author's memory and mine.
- I did not open the test or mutant lines the second review cites (TPG:4497-4530, TCMP:444-465, MUT:2997-3016); I rely on its reading for C-F5 (c), C-F7 and C-F11.
- Whether the lead wants the prepared-transaction fix in the same pull request is a batching choice I leave open.

File read for this addendum: /home/user/hadavin-sdk/handover/reviews/P3a-2/r12-codebase-full.md

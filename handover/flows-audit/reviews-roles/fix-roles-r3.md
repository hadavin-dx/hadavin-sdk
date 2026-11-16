# Fix report: ROLES-PROPOSAL.md, round-3 doc findings M1-M8, N1-N10

Edited only `handover/flows-audit/ROLES-PROPOSAL.md` (now Version 4). Not touched: `roles-coverage-check/`. Nothing committed. EGM skipped for this report itself: it is a fix pass on a doc whose independent review is the lead's next step (the doc says so in section 10).

## Failed, uncertain, not checked (first)

- **Nothing was run.** No Postgres, no psql, no n8n here. Every SQL line, guard and SQLSTATE in the file is still UNVERIFIED. The section 4 SQL was rewritten heavily (three guarded parts, each one transaction), so it is MORE untested text than version 3, and it needs the lead's fourth review.
- **I could not fetch the Postgres manual.** Tried again with curl to `www.postgresql.org`: the proxy refused (CONNECT 403). So the facts for M3, M4, M5, N5, N10 are written as "rule I rely on (UNVERIFIED)" with the manual page named. N10's two UNVERIFIED lines (138, 288) are NOT closed; they are narrowed to one named manual sentence each, closable by reading the REVOKE page.
- New guard syntax (`\if`, `\gset`, `:'var'`, `pg_control_system()` for the fingerprint) is my own design and is the least certain part. If the login cannot call `pg_control_system()`, section 8 names a fallback fingerprint.
- Not checked: that film-v5 and real-v5 statements are identical (still not re-compared; section 11 question 8 asks for a scripted diff); how n8n really resolves credentials and re-imports (I read the flow files, not n8n docs).
- Not done (belongs to the other agent): M9 / S1-S7 script findings. I only added their list and a pointer to section 10 and section 2.

## Finding by finding

| Id | Verdict on the reviewer | What I changed |
|---|---|---|
| M1 | Right: one guard at the top, Part B (days later) had none | Section 4 is now Part A, Part B, Part C, each with its own guard, `ON_ERROR_STOP`, and own transaction; each meant as its own file (question 1 asks the lead to split them; my brief limited me to one file) |
| M2 | Right: `SET mf.throwaway` is typeable and says nothing about which server | Guard now compares `current_database()` and the server's `system_identifier` against values passed with `psql -v`, written down per server beforehand; throwaway mode also requires the name to start `mf_throwaway`. Honest limit stated: stops a wrong-window paste, not a deliberate administrator |
| M3 | Right | `BEGIN`/`COMMIT` per part; Part A starts by refusing if any `mf_` login already exists; database name asserted; `GRANT CONNECT` / `REVOKE` on the database now use the asserted name, not a placeholder. Transactional-DDL rule added to section 8 with a throwaway test |
| M4 | Right on both points | Part B step B1 now first grants `USAGE, CREATE` on schema public to mf_tableowner; section 8 ownership row corrected (the CREATE right is needed by the NEW owner, not the person running it); new test C9; new row in "Reason for each grant" |
| M5 | Right (ALTER OWNER moves only the old owner's entries) | C5 rewritten as an exact ACL diff both ways (table ACL and every column ACL against the list generated from group MX); the same check sits at the end of Part B and rolls it back on any difference; Part B has a line for revoking each other grantee that group L lists |
| M6 | Right, and I checked the files: all Postgres nodes in real-v5 carry the id `PG_CREDENTIAL_ID` and name `n8n-publish-pg`; `SUB_WORKFLOW_ID` is also a placeholder; the builder takes one id | Section 3 cost text rewritten: bind by id, node-name to credential table, four placeholder ids, builder must take four, re-import and sub-workflow id behaviour (UNVERIFIED), "exactly one active copy" check. Step 5 rewritten; step 6 rollback says "by id"; FW tests must also record which login ran (section 8) |
| M7 | Right that it is unproven | New C6b (hard kill, restart, one and two n8n processes); pool rule "processes x pool max + 1 <= limit" in section 8; C8 extended with the silent-stop check and an early-warning query on `rolvaliduntil`; C7 notes process count. I did NOT add `idle_session_timeout` or change the limits: question 5 recommends waiting for C6b |
| M8 | Right | New C10: wrong-password `28P01`, `password_encryption` and `SCRAM-SHA-256$` prefix (first 14 characters only, no hash), `pg_hba_file_rules` with no `trust`; also added to group L; warning that the Docker image default may fail it |
| N1 | Right | Pass rule rewritten: a positive control per action, named for each denied action; no control means the denial is not counted |
| N2 | Right (`pg_class` is readable by everyone) | C1 now uses a made-up table `mf_other`; catalog readability listed in WS |
| N3 | Right in substance | C4 expects `28P01` first (password is checked before the LOGIN attribute; part C sets the password NULL); `28000` would mean authentication was skipped and is a C10 failure. UNVERIFIED |
| N4 | Partly right: group L line 204 already used `pg_attribute`; the one using `information_schema.columns` (line 208) was the weak one | Replaced line 208 with `pg_attribute` (attnum > 0, not dropped); added `pg_db_role_setting` |
| N5 | Right (tables have no default PUBLIC rights, so the line did nothing) | B3 line removed and explained; pg_default_acl rows from group L are decided with the owner, none assumed. Section 8 row added |
| N6 | Right | Rollback block rewritten: new password and new n8n credential needed after Part C; credential `n8n-publish-pg` is disabled, not deleted, until step 9 plus a day; owner "no" at step 7 means B and C are not run (stated in step 7 and question 6) |
| N7 | Right (the guard used no `\if`) | New guards do use `\if`/`\gset`; section 8 row rewritten to match and says to test a wrong and a missing value |
| N8 | Right (`state` has a CHECK with six values, `mf_leads.sql` line 8 of the v4 file) | Section 9 item 1 now says "any state the table allows" and lists the six |
| N9 | Right | Part B precondition stops if the old login is a superuser; Part C has a path B (change password, remove from n8n, it stays the administrator's login); owner question 3 and a line in "What I need from the owner" |
| N10 | Reviewer right that the facts are plausible | Both rows kept UNVERIFIED but narrowed to the manual sentence relied on; line 138 belt-and-braces column revokes kept in Parts B and C (harmless if the rule holds) |

## Where I partly disagree

- N4: the claim that group L did not use `pg_attribute` is half wrong (it did, in the column-ACL query). The `information_schema` problem was real and is fixed.
- N10: I cannot close the two UNVERIFIED facts without the manual, so I did not mark them verified.
- M1: "two .sql files" is done as three labelled parts inside the one allowed file, because my brief forbids other files.

## Questions raised (section 11 of the file, each with a recommendation)

1 split into three .sql files; 2 who records the fingerprint pair; 3 is the old login a superuser, administrator or Docker default; 4 expiry policy; 5 connection limits wait for C6b; 6 owner says no to retiring; 7 CREATE on schema for mf_tableowner; 8 scripted diff of film and real folders.

## Rules cited

Studio preamble 3 (no secrets: placeholders and `-v` values only, no password in file), 5 (fix, do not defer; the three exceptions stated), 11 (least privilege: negative tests C9/C10 added, mf_tableowner's extra right justified), 6 (honesty). Bible R-numbers not available in this repository (grep of the preamble's bible path not present); none cited.

Files changed: `/home/user/hadavin-sdk/handover/flows-audit/ROLES-PROPOSAL.md`, `/home/user/hadavin-sdk/handover/flows-audit/reviews-roles/fix-roles-r3.md`. No commit, no head SHA. No agents, shells or containers started.

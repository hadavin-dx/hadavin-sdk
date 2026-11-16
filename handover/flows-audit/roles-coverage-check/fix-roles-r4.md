# Round 4: roles coverage check (fix report)

## What failed first
- Independent rerun (`evidence-rerun.md`): 5 of 22 planted faults SURVIVED (exit code 0): SQL text in a Code node (F6a), a MySQL-type node (F6b), a postgresTool node (F6c), SQL text in a Set node (F6d), and one flow file with no Postgres node while the other files kept theirs (I4c).
- Security review R3 (`../reviews-roles/review-r3-security.md`, item M9, S1 to S7), checked against the script as it stood. Already fixed in round 3, so no new code: S6 (grants are parsed from section 4 of ROLES-PROPOSAL.md; test `test_script_and_document_cannot_differ`) and S7 (unused-grant report; test `test_g7b_extra_column_grant`). Those two tests pass on the old script too, so they cannot show a before/after; I did not claim they do. Still open before this round: S1 (partly), S2, S3, S4 (partly), S5.

## What changed (all in `check_grants_cover_queries.py`)
- F6a-d: every node that is not the checked Postgres node is now inspected. FAIL if its type name contains a database word (postgres, mysql, mssql, sql, mongo, redis, ...) or if any text in its parameters or notes looks like SQL (select..from, insert into, update..set, delete from, drop/alter/create, truncate, grant..to) or names `mf_leads`. On the two real folders no such node exists (I listed all 41 non-Postgres nodes per folder first: no hit).
- I4c: each flow file must hold at least one Postgres node (message names the file).
- S1: each folder must hold exactly the 4 flow files and 14 Postgres nodes; no folder given, wrong folder, missing file, or a different count exits 1.
- S2: a Postgres node whose operation is not `executeQuery` (or is missing) fails; a query starting with `=` (n8n expression) fails (before, the `=` was silently stripped).
- S3: a node with no Postgres credential fails. New option `--require-new-credentials`: each node's credential must equal the name the document's login table gives for its login (read from the document, not copied), and `n8n-publish-pg` (the old shared one) fails.
- S4: also refused now: `SELECT *`, `RETURNING *`, `INSERT` without a column list, `UPDATE ... FROM` (a subquery in parentheses is still allowed), any `WITH` (CTE). DELETE, TRUNCATE, COPY and other tables were already refused.
- S5: column matching ignores case (before, `EMAIL` or `Name` was missed or split into wrong pieces); any double-quoted name fails.

## Evidence
- New file state: `python3 -m unittest test_check_grants`: Ran 44 tests, OK (19 old plus 25 new).
- Real folders: `python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5`: rc=0, 14 postgres nodes each, TOTAL PROBLEMS: 0.
- Same tests against the old script (copy saved before editing, run via `SCRIPT=`): 22 of the 25 new tests FAIL, as required. Two new tests pass on the old script by design: `test_f6e_innocent_node_text_not_flagged` (a no-false-alarm control) and `test_s1_no_folder_given` (the old script already refused no folder).

## Not checked / honest limits
- S3 is OFF by default. Reason: today's flow files still use the old shared credential `n8n-publish-pg` (the re-pointing is step 5 of the rollout in ROLES-PROPOSAL.md and needs the full re-test), so turning it on by default would break the required baseline rc=0. Run with `--require-new-credentials` after step 5; on today's files it reports 14 failures per folder (verified for the real folder). Owner or lead decision: switch the default on at step 5.
- The SQL-text rule is a text match: a flow built to hide SQL (split strings, encoded text, an HTTP call to another service) can still pass. A normal word match such as "update" alone does not trigger it. The database tests remain the real proof.
- The count constants (4 files, 14 nodes) must be edited in the script when a flow legitimately gains or loses a Postgres node.
- Credential names are matched by name only, not by credential id; I did not check what the real n8n instance holds.
- Not run: any database, any n8n instance. Not committed (the lead commits). No other folder touched.
- EGM: the review of this result by the egm reviewer agents and the evidence runner are not done by me (I cannot invoke them from here); the lead runs that step. No token or agent helpers were started.

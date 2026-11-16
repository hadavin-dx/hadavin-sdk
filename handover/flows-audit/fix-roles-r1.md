# fix-roles-r1: fixes to ROLES-PROPOSAL.md for review-r1

Failed or unverified first: no Postgres fact could be verified (manual fetch returned HTTP 403; no Postgres exists; nothing ran). All SQL stays UNTESTED. This version has had no second review. R-numbers: the bible is not in this repository, so none cited. EGM: not run by me (the lead runs the review). Head SHA: not a git repository.

Checked myself against the real flows: extracted all `query` fields of `n8n-nodes-base.postgres` nodes in `n8n-flows-real-v5` and `n8n-flows-film-v5` with a script: 14 nodes each, text identical (script comparison, replaces "by eye"); no DELETE/TRUNCATE/DROP/ALTER/CREATE/COPY/GRANT/REVOKE/SET ROLE; only table `mf_leads`. A coverage script derived reads/writes per statement and compared them with the grants: new grants 0 uncovered; old grants fail on S10 (claim_token) in both folders, so B1 is real. `mf_leads.sql` (v4) has 15 columns incl. alert columns; the older file has 11, as the proposal said.

| Finding | Fix | Where |
|---|---|---|
| B1 claim_token missing for recovery | Added to SELECT grant, reason table, statement table (S10 RETURNING lead_key, email, claim_token), rights table; coverage script proves it | s2, s4 |
| M1 owner/old role | mf_tableowner NOLOGIN (decided), ALTER TABLE OWNER, old-login retirement steps (revoke, NOLOGIN, password null, delete n8n credential, stop-if-superuser), rollback order, tests T4/T5 | s3, s4, s7 |
| M2 deny by default | REVOKE ALL on database/schema/table/columns from PUBLIC; R0 replaced by group R (aclexplode, attacl, pg_auth_members, relowner, has_column_privilege, datacl); disputed table-vs-column REVOKE behaviour stated, tested by T5 | s4, s5, s8 |
| M3 Option B | removed from proposal; kept as a marked rule exception needing owner yes, exact extra rights listed | s3 |
| M4 test matrix | full 15 columns x 4 logins x 3 actions (180 cells) plus DELETE/TRUNCATE/ON CONFLICT DO UPDATE/SELECT *, SQLSTATE 42501 and positive control required, TEMP/other-database/old login/limit/wide-spot tests; X depends on F-011 | s5 |
| M5 throwaway | separate server, never CREATE ROLE on the take's server, no filming overlap, TEMPLATE note | s6 |
| M6 connection limits | limits 6/6/3/3, pool maximums one lower, burst test T7; n8n pooling marked UNVERIFIED | s8, s5 |
| N1 passwords | VALID UNTIL, rotation drill T8, stated exception | s4, s8 |
| N2 "own claim" | wording corrected | s4 |
| N3 "two roles" | now "four plus one table-owner login" | s3 |
| N4/N5 wording | glossary first; ids explained; mf_ prefix said unknown; owner clash resolved (table owner) | s0 |
| Naive Blocker 1 | 4-line top incl. real reason for "nothing before the video" | top |
| Naive Blocker 2 | glossary before first use | s0 |
| Naive Majors/Nits | "by eye" removed; "none deletes" scoped to the searched text; "not granted" reworded to intent plus tests; "per the manual" replaced by from-memory plus page names; "Is the split cheap" retitled; R/W legend vs test ids renamed S1-S14; DO NOT PASTE banner on SQL; take and laptop defined | various |

Not fixable now: Postgres facts (impossible now: manual blocked), old login's rights, other users of `n8n-publish-pg`, wide-spot trigger decision, other-database revokes (all need the owner); independent review (needs the lead). Listed with next steps in section 10 of the proposal.

Rights of identities proposed: listed in section 4 of the proposal (masked, no passwords or ids). Token use: not measured.

# plan-v6-real-v5-edits.md round 1, readiness review (egm reviewer A, condensed copy), 2026-11-16
Read-only; nothing run. Verdict: not ready for a lead who has never seen it. 0 Blocker, 8 Major, 7 Nit. The 28 edits apply mechanically (dry run 28/28 once, in order; 558 to 605 lines); arithmetic holds (S2 14, 153 steps, 173 min = 2 h 53, 21 rows); label spelled identically in edits 1, 4, 20.
Major:
1 Section 10b steps 2 and 4 (lines 325-331): database guard is by-eye; TRUNCATE may run in another session; take database name never stated (UNVERIFIED 15); no connection command. Fix: one psql -d <take_db> call with current_database() check (\gset/\if or DO block) and a lead fill-in for the expected name.
2 Steps 3-4: a row sent between export and TRUNCATE is deleted but not listed, orphaning its HubSpot contact (breaks decision 2); recovery flow runs every 30 s. Fix: n8n stopped or flows inactive between 3 and 4, or one transaction, or recount after TRUNCATE.
3 Step 6: "highest in version 3 is step 18" is wrong; OWNER-STEPS-realrun-v3.md has steps 19-23.
4 Wording: "lead" means the Claude session, the made-up sales record and the person contacted. Use "made-up lead record"; keep "the lead" for the Claude session (edits 25, 28 item 16 too).
5 Line 313 (edit 25): "table key cannot be empty so insert fails" is false for an empty string (lead_key text PRIMARY KEY rejects NULL, accepts '').
6 Line 162 (edit 13): recipe prints CrmUpsert parameters from the film file, but edits 6 and 9 stop archiving the film folder; give git -C $HD show 5fdc659d1:... and name the swapped file.
7 Lines 162-179, 359: nothing says what the stand-in answers or that CrmIdOk accepts it; if not, every lead in A, B, C fails. Add checked fact or UNVERIFIED.
8 Line 155 and REPORT-real-v5-edits-v6.md:4: claim "swap negative run fires the assertion" has no output in swap-test.txt (positive run only). Add output or drop claim. (Builder's hand-back said a negative run was done; the file on disk does not show it.)
Nit: crm_id empty after lost ack (cases C, E) missing from export; step 5 does not name where rehearsal ids are; label claim vs paraphrases in edits 15, 21; which hash line is first in INDEX.md; "plan line 271/129" are original-plan numbers; startswith http://127.0.0.1: accepts userinfo trick, use exact match; hash difference by eye, file counts (76/70) omit 2.1b.sh.
Could not check: real-v5 flow files (mf-form.json:27/97, mf-recovery.json:26, M3 line 258, byte-identity claim), crm_stub.py and CrmIdOk, glue, n8n 2.46.6 import, $HD, V5-README.md.
Section 10b vs "take never deletes contacts": no step deletes a HubSpot contact; only TRUNCATE of lead rows is destructive, guarded by by-eye check; consistent with decision 2.

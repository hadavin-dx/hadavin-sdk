# Fixlog: STATIC-PASS-real-v5.md to STATIC-PASS-real-v5-v2.md (2026-11-16)
Input: verify-static-pass.md (4 majors, 1 minor, 1 nit) and paste-check/REPORT-real-v5-edits.md.
1. Major 1 (cite): the count read is plan:289 (P-C2), not :288. Plan:288 is the denied-write tests N1-N10; now said in answer 3. FIXED, plan lines re-read.
2. Major 2 (framing): removed "does not run real-v5" as an undisclosed failure. Now states plan:493 already discloses it; the real gap is that same-id-twice evidence comes from film-v5. FIXED.
3. Major 2 add-on: added the film-v5 versus real-v5 diff facts (mf-form and mf-hook byte-identical; lease 45 s; recovery 30 s; Claim at mf-form.json:97; CrmUpsert is the HubSpot node at mf-sub-crm-mail.json:94-95). Marked as builder-report facts, not re-run. FIXED.
4. Major 3 (v3 cites): all owner-sheet cites now point at v9 (:19, :22, :26, :29, :35, :36, :121, :143, :200, :237, :335, :405). Old :97 became :36/:19; old :23/:92 became :22/:143; old :121 stays :121 (step I.5). FIXED, lines re-read.
5. Major 4 (overreach): "holds by construction" removed. Report now says the insert was read, and lists recovery, MailClaim, the stage journal and the CRM upsert as unrun. FIXED.
6. Minor 5: drive.py and fill_flows.py described as run-time glue copies (plan:223, :248), not repo files; "not found" is no longer a defect. FIXED.
7. Nit 6: dropped "only a new take id is required"; now says the marker guards the tag, and nothing read says mf_leads is cleared. FIXED.
8. Every claim now carries "read", "run" or "not found"; no "VERIFIED". Nothing is marked run because nothing was run.
9. Re-read from origin/cloud/flows-audit this pass: mf-form.json:27,97,293; mf-hook.json:27; mf-recovery.json:26,102; mf-sub-crm-mail.json:28,94-95,159; V5-README.md:1. Other flow cites are carried from the first pass and said so.
10. NOT done: the "20" in "20/45/120" still unexplained; film-v5 whole-flow diff is taken from the builder report, not run by me; glue files not read; v9 cite for the clean-up of mf_leads rows does not exist (nothing says it).
11. Open for the lead: where is same-id-twice tested in the real run; whether to adopt edit R8 (step 2.1b) and R15/R17 (clean-start row).
12. Only files under cross-read/ were written. Nothing committed, no processes started.

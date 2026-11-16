# CORRECTIONS to the flows-audit, round 2 (target: branch cloud/flows-audit, folder handover/flows-audit, content of head 53079836). Owner of every entry: the lead (owner of the audit). I did not change the target. Evidence: REVIEW.md, review-design-r2.md, review-codebase-r2.md, evidence-r2-*. Round-1 corrections (CORRECTIONS-r1.md) still stand unless an entry here replaces them.
Each entry: where, change, why.
## Ratings (FINDINGS.md)
C-1 F-018 row: rate Major or merge into F-029 and say so; move "HubSpot answer shape" into its own row (see C-13). Why: same mechanism and impact as F-029 (DESK_ALERT_TO unset fails every alert, mf-recovery.json:178). [D1]
C-2 F-028 row: write what is wrong in the row (not "see lanes/L3.findings.md"); if the stale numbers are in filmed files, rate like F-003. [D2]
C-3 F-012 row: delete "the batch is usually one lead" or cite evidence; rate Major until the rehearsal counts the leads in flight at the kill (add that count to the rehearsal); keep the real HubSpot node's missing timeout versus the film node's DESK_TIMEOUT_MS in a row of its own. [D3]
C-4 F-037 row: rate Major by the one rule; keep Blocker only as "the lead's order" in the table header (like F-002). Why: default UNVERIFIED, repo start paths set the variable, failure shows at the first rehearsal (Qualify error output). [D4]
C-5 F-002 (and F-007, F-031) cell: remove "(until T19 and T20 pass)"; the cell holds the rating by the rule, the lead's order sits in the header. Count by the rule: 5 Blockers (F-001, F-003, F-005, F-006, F-037 if kept). [D5]
C-5b F-009 and F-036: make the "take" column agree or cite where the loopback binding is written. [D6]
## Coverage of round-1 items (FINDINGS.md, FIX-PLAN.md)
C-6 F-002 text: say the first keyless lead is never processed and never alerted (StuckRow mf-recovery.json:69, AlertRow :167). T20: add missing field, null, array, number, 65 characters, whitespace, and one positive case (L plus 16 hex passes). [M1]
C-7 FIX-PLAN item 3 (gate): add the real-v5 versus film-v5 swap, a check that all four flows are active, where the grep runs (files before import or an export), and the exact variable list per flow set (DESK_URL, MF_STAGE_URL, MF_CRM_URL, DESK_ALERT_TO, DESK_TIMEOUT_MS). [M2]
C-8 F-037/F-021: name the owner and file of the take start script (not in the repository). [M3]
C-9 Add a T-test that the first alert arrives with the database down and a heartbeat or activation check for mf-recovery (BEFORE or state why AFTER). [M4]
C-10 F-014: one sentence linking the alert flood to F-009 and F-036. [M5]
C-11 New row: SendMail has no timeout (mf-sub-crm-mail.json:278) against the 45 s lease (false alert, no second mail); and a row that the film rehearsal cannot show real HubSpot behaviour (keying on e-mail only). [M6]
C-12 F-002: a [text] step to put the sender contract (422 final, 503 resend with the same key) into a live document and a named person to confirm the sender's behaviour and its resend window against a longer outage. [M7]
C-13 New BEFORE step: one call to the real HubSpot trial to measure the answer shape that CrmIdOk requires (^[0-9]+$ on id or vid, mf-sub-crm-mail.json:146); until done real-v5 is not ready. [NEW-1]
C-14 FIX-PLAN order: apply F-001, F-002, F-008 and the text patches, rebuild once, import, gate, then T19-T21 and one end-to-end run; item 8 before the tests when the video says "one database". [NEW-2]
C-15 F-007, F-003: name who supplies the lane3 report and by when, or caption the numbers "relayed". [NEW-3]
C-16 F-002 fallback: state exactly what the IF checks and run it in T21. [NEW-4]
## Patches
C-17 F-002 row and FIX-PLAN item 2: mark UNVERIFIED that a failed Postgres write goes to output 1 with pairedItem intact (no other Postgres node in the generator uses it); T21 is the gate; F-002 is not closed by T19 and T20 alone. [K1]
C-18 F-002 row: mark UNVERIFIED that the node (version 2.5) emits one item when INSERT ... ON CONFLICT DO NOTHING inserts nothing (support is a comment at build_mainframe.py:114); T19 and the fallback cover it. [K2]
C-19 F-002 / T20: state that a non-text key may fail in the Set node before KeyOk (bare 500), or add the types to T20 and drop "each junk key gets 422". [K3]
C-20 patches/F-003: also patch run sheet lines 85 and 90 (scene-4 captions), or state in the F-003 row that the patched sheet is not releasable until both are fixed. [K6]
C-21 patches/F-004: move the process notes ("read: ... occurs 3 times", "Never write ...") out of the quoted claim into the Tag line; say the three-leases claim has two relayed figures. [K7]
C-22 F-008: add the two documents (N8N-START.md l.15-27, DESIGN-A-README.md:23) to the patch or keep them as BEFORE item 4 text steps; say saved runs hold node inputs and outputs and give the pruning age. [K8]
## Plan and wording
C-23 FIX-PLAN: drop the padded item 9 (real list 8, required 7); give the estimate a breakdown or say "not estimated"; add the blockers not listed (C-7, C-8, C-13, clean-up method, heartbeat); justify or drop T19's 10 s limit, add a concurrent-request case; run T17/T18 before the take or say why not. [Q5]
C-24 F-030: add to item 7 the sentence "alerts do not survive a mail outage". [Q5]
C-25 Wording: say "studio lead" for the person and "enquiry" or "sales lead" for the other meaning; move "Words used in this file" above the short answer or drop ids from it; define take-day gate, T-ENV, T19-T21, CrmIdOk, ClaimStuck, stand-in, scene 10 and P/T/O at first use in FIX-PLAN; header "17 rows in 7 items". [W1-W7]

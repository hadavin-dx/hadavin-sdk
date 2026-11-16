# Difference list: OWNER-STEPS v3 to v4 (lead-facing; E-xx = row in EDITS.md)

v3 = inputs/OWNER-STEPS-realrun-v3.md (193 lines). v4 = steps-edits/OWNER-STEPS-realrun-v4.md. Step letters in v4 are new (A to J); v3 numbers are not kept because v3 jumped from 9 to 16.

| v3 section / line | Result | v4 place | Reason in plain words |
|---|---|---|---|
| 1 title | changed | title | version 4 |
| 3 history, sources, "worktree", review-round wording | removed | none | Owner does not need branch names or builder history. E-01, E-02 and E-23 (branch and round wording) therefore have no target; they stay valid for the lead's own file |
| 5 "lead does everything else" | changed | intro, "The rehearsal" | Added the rehearsal at US$0 before any real take (E-03) |
| 7 UNVERIFIED legend | changed | "Not checked" in plain words | Wording rule: explain, no bare label |
| 9-16 words used | changed | Words used | Removed done items (app password, company address, token); added rehearsal; one gloss for "archive" = delete (E-05) |
| 18-26 rules 1, 3, 4, 5, 6 | kept (reworded) | Rules 1 to 5 | Still owner-only. Old rule 2 (you type secrets) removed: the secrets are already saved |
| 27 Phase 0 heading and 1 to 7, 9 | removed | none | Owner statement 2026-11-16 and the facts file: mailboxes, 2-step, app passwords, HubSpot test account and keys are done (E-37, which only added a status note, is replaced by this full cut) |
| 29-32 step 1 old password check | removed | none | Done: the old app password was revoked |
| 34-38 step 2 two Gmail accounts | removed | none | Done |
| 40-44 step 3 "Send mail as" | removed | not checked item | Facts file says Gmail settings done; whether Send-mail-as was among them is not stated, so it is kept only as a "not yet shown" line |
| 46-54 step 4 filter and label | removed, check kept | step C.1 | Facts file says settings done, but an empty label on take day is still owner-checked |
| 56-61 step 5 app passwords | removed | none (revoke kept in step I) | Done |
| 63-72 steps 6, 7 HubSpot property and apps | removed | none (app deletion kept in step I) | Done |
| 74-80 step 8 n8n credentials | changed | step C.2 | n8n account and credential store are done; only a fresh-n8n first visit may need the owner. Proposal text (E-10) and "database login" wording (E-09) kept, marked as the lead's to decide. Port wording (E-06) as a lead-decision line. E-07 stays held: "not yet checked" |
| 82-83 step 9 sentences | removed | none | Reported items are done; "label and inbox empty" moved to the take-day row |
| 85-87 Phase 1 lead checks | changed | step A lead-decision line | Two kinds of rehearsal; order not decided (E-11) |
| 91-92 step 16 yes with numbers | kept, changed | step A | Added "rehearsal passed, no pass no take" (E-12) |
| 94-100 step 17 `y` and challenge | kept, changed | step D | Owner-only typing. "archived" gloss (E-05); marker-file text kept; the proof screen is a lead-decision line |
| 102-104 step 18 `end` | kept, changed | step E | Owner-only. Added open point: read-only key cannot delete (E-04) |
| 106-109 step 19 filming | kept, changed | step F | Owner-only. Item 4 and 5 changed for saved runs ON and no chosen proof screen (E-14, E-15); the v3 sentence allowing detail panes to be filmed is removed |
| 111-112 step 20 failed take | kept | step G | Owner-only |
| 116-117 step 21 watch | kept | step H | Owner-only |
| 119-128 step 22 retirement | changed | step I | Item 1 (lead's) kept only as a one-line order note; E-16 applied by not describing how saved runs go. Revokes, screenshots, retire check, secret-file deletion kept. HubSpot-app deletion kept with a lead-decision line |
| 130-131 step 23 post | changed | step J | Narrow claim kept; "own credentials" replaced (E-36); must-not-say list extended: portal, approval, audit trail, egress, crash-safe, independent login (E-17, E-18); exact wording lead's |
| 133-138 three owner decisions | removed | none | All answered or approved (narrow claim in force, throwaway mailboxes done, build-time rule closed) |
| 140-147 what to send | changed | table | Dates and done items removed |
| 149-166 status and test counts | removed, summarised | "What is not proven yet" | Old counts are on old heads and belong to the lead's own file. Kept plain-word statements (E-19 to E-22) |
| 168-172 refusals, deadline, exit codes | kept (shortened) | Refusals section | The owner meets these at the prompt. Time converted to IST |
| 174-176 optional name in take config | removed | none | Lead-only setting |
| 178-193 UNVERIFIED list (14 items) | changed | "What is not proven yet" | Items about done accounts removed; E-24 and E-25 numbering has no target because the list became plain bullets; new lines on Postgres, saved runs, egress, crash added (E-25 items 15 to 18) |
| new | new | step B, step C.2, intro | Take-day laptop settings as an explicit step; fresh-n8n check; records note (one database, stage.journal exception) |

## Rows of EDITS.md not applied, and why
- E-04, E-06, E-07, E-08, E-09, E-10, E-11, E-14, E-15 are applied only as plain-words "To be decided by the lead" lines (items 1, 3, 4, 5, 6, 7, 8, 11 of NOT DECIDED). E-07 and E-08 are held: v4 says "not yet checked".
- E-01, E-02, E-13, E-19, E-23: the v3 passages they edit are removed from the owner file (history, round wording, test counts), so nothing to change; E-13 (second edit pass after the rehearsal) is still needed: lines about "by hand" in step D must be rechecked after the rehearsal.
- E-26 to E-35 edit AGENT-SCOPE, not this file; not touched.
- E-37 replaced by the full cut (NOT DECIDED item 12 taken as the queue order C4b).

## Decisions applied
One database (take's Postgres; `stage.journal` the one exception); saved runs ON on made-up data, deleted at clean-up; no portal, approval or audit-trail claim; narrow claim only; n8n outgoing traffic switched off by setting names and only observed; US$0 rehearsal before any real take; take branches local only (no branch text in the owner file).

## Revision after review C4b (2026-11-16, review-c4b-v4.md)
- Added: order of the day; take date line (the plan sets none; only last start 18:14 UTC = 23:44 IST and window end 18:29 UTC = 23:59 IST on Mon 23 Nov); "Who is who" (studio lead / contact; "lead" only in the quoted claim); "removed for good" with one note that "archive" means the same; fuller Words used (take id with the honest note that no pattern exists in the plan, take config, window end, secret files, exit code with `echo $?`, hook door, Postgres, retire check, crash-safe, proof screen, rehearsal, loopback); money section (no fixed dollar ceiling enforced, as v3 line 23 says); bold warning before step E; exit codes next to step D; rule 5 never use the real company mailbox.
- Changed: C.2 reworded for the new empty database (D-M1); proof screen is the owner's choice (D-M2); HubSpot app question goes to the owner (D-M3); personal name in the path replaced by a placeholder; browser profile moved into step C.3 (old step F keeps the filming rules and is now "What the film may show"); table "What to send" extended; "real take" renamed "recorded take".
- Moved: all lead-only technical points into the box "For the studio lead", each with the owner default "do nothing until the studio lead says".
- Not verified: the take id pattern and take date do not exist in the plan; the file says so.

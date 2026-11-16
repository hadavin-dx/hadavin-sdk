# Rows for OWNER-STEPS version 4 (the lead pastes these)

> STATUS: UNVERIFIED. Nothing ran. Every fact about files, line numbers, mailbox addresses and the take folder below was read from text, not run. Nothing here is a yes to act on until the lead writes "re-check done" with the date and time (UTC and IST) at the top of this sheet. Until then the owner does nothing from this sheet.

## For the owner (read only this part)
You are the owner. Only two things on this sheet are yours: Step A and Step D, both inside "Row 4" below. Everything else is the lead's work. OWNER: stop reading after Step A and Step D.

What you do not do: you type no folder path, no mailbox address and no password into any message to the lead. Never paste a password, key or app password (a 16-letter Google password for one program) into a chat message or a file.

Step A (your yes, before anything real is sent). The lead sends you a message that holds one number: the cost in US dollars of sending one made-up person through the real HubSpot trial account. Cost line (the lead's answer Q21, ORDERS.md line 132; the heading of that answer is line 131): up to 3 live model calls under the owner's standing credits yes; no US$0 claim. Only the number in the lead's message counts.
- If the lead's message holds a number and you accept it, reply in the same chat: "yes, US$X" with X being that exact number.
- If the lead's message holds no number, or you do not accept it, reply "no". A reply without a number is a no.
- Where to write it: as a reply in the chat where the lead's message arrived. Nothing is written into a file.
- Until your "yes, US$X" arrives, the lead sends nothing.

Step D (after the take: delete the made-up contact in HubSpot, by hand). The lead sends you one message with the made-up e-mail address and the HubSpot contact number. Then:
1. In HubSpot open Contacts and search by the e-mail address (not by the name). The menu names are UNVERIFIED: the lead checks them at the re-check.
2. Delete only a contact whose e-mail address is exactly the made-up address in the lead's message, letter for letter.
3. If the search finds more than one contact, or the address is even one letter different, stop. Delete nothing and tell the lead.
4. After the delete, search again by the same address. Expect no result.
5. Reply "deleted" in the chat. If the second search still finds the contact, reply "not deleted" instead.
Why you delete by hand: the take must never delete contacts (decision of 2026-11-16, kept in the file inputs/DECISIONS-2026-11-16.md), so the take's login holds no delete right.

When it worked: the lead tells you in one message that all four checks of Step C passed. If you hear nothing, it did not finish; do nothing.

## For the lead (the owner skips this part)
Words used here (one word, one meaning):
- "the lead" = the Claude session that prepares and runs the demo take.
- "the take" = one recorded run.
- "the take folder" = the working folder built for the take, written below as TAKE_FOLDER. The lead creates it inside the studio folder (the lead's own working area, kept outside the hadavin-sdk repository; its place is UNVERIFIED and is confirmed at the re-check). The owner never types a path.
- "a made-up person" = one invented person who fills in the form. It is the only word used for a test person in this sheet. Its rows in the database are called leads in the file names.
- "the incoming-people table" = the Postgres table named mf_leads.
- "the flow files" = the four files mf-form.json, mf-hook.json, mf-recovery.json and mf-sub-crm-mail.json in handover/demo/n8n-flows-real-v5.
- "the table file" = handover/demo/n8n-flows-v4/mf_leads.sql. It sits in a folder named v4 while the flow files sit in a folder named v5: two different folders. All paths start at the top folder of the hadavin-sdk repository.
- "practice run" = the run of the flows against a local stand-in, not the real services (in earlier notes this was called the loopback re-smoke).
- "rehearsal" = the first full laptop run of the changed flows, done by the lead right after the practice run passes (decision 12 of 2026-11-16, in inputs/DECISIONS-2026-11-16.md).
- "stuck-mail alert" = the mail the recovery flow sends when a made-up person stays unprocessed. "Alert" is used for nothing else in this sheet: the four database columns are called "stuck-mail columns" (their real names are alert_sent, alert_token, alert_until and alert_attempts).

Order of the lead's work (L1 to L6), then Row 4 (real HubSpot test, then rehearsal):
- L1 copy the table file; L2 create the database from it; L3 import the flow files into n8n; L4 fill the placeholder words and the literal values with fill_flows; L5 run the tool's own check on the filled copy, then the column check; L6 the first send ("first send" = the first made-up person sent into the flows).
- Row 4 happens after the practice run passes, after the owner's "yes, US$X", and before the rehearsal.

L1. Copy the table file (before the database is created and before the flow files are imported). The take uses handover/demo/n8n-flows-v4/mf_leads.sql. It has four extra stuck-mail columns. The older file handover/demo/n8n-flows/mf_leads.sql has none (the word "alert" occurs 0 times in it, counted by search). Reason: the recovery flow handover/demo/n8n-flows-real-v5/mf-recovery.json uses all four columns (lines 124, 204 and 228). That flow runs every 30 seconds (lines 9 and 10) and its alert-claim step carries on after an error (line 141, onError continueRegularOutput). What would happen on the older table is NOT KNOWN: nothing was run. It may fail every 30 seconds without stopping the flow, in which case no stuck-mail alert is sent; this is a guess from reading the files. The take does not check the stuck-mail alert by itself (OWNER-STEPS version 3, line 166). The lead verifies, at the re-check of the take scripts against this audit (not done yet; the audit has not seen those scripts), that the copied file is the v4 one. Note on the file's own first line: line 1 of handover/demo/n8n-flows-v4/mf_leads.sql says "v3 table", although the file sits in the folder v4 and holds the four stuck-mail columns (alert_sent, alert_token, alert_until, alert_attempts; lines checked by search). The comment is old wording; the folder name and the columns are what count. The lead confirms at the re-check that this is the file copied.

L2. Create the database from the copied table file. The lead verifies the database is the take's own database and no other. L3. Import the flow files into n8n. Nothing else to write here.

L4. Fill the placeholder words and literal values with the fill program. First the two address words in the mail steps. FROM_ADDRESS_PLACEHOLDER appears in mf-recovery.json (line 177) and in mf-sub-crm-mail.json (line 256); it is the address shown as "From" on the mail. By OWNER-STEPS version 3 (step 3, line 40 of inputs/OWNER-STEPS-realrun-v3.md; step 1 is about the old practice mailbox password and does not name this address) that is the company address, shown through the Gmail setting "Send mail as" (a Gmail setting that lets one mailbox send mail that shows another address as "From"). INTAKE_ADDRESS_PLACEHOLDER appears once, in mf-sub-crm-mail.json (line 257), as the "To" of the thank-you mail. The file does not say which mailbox that is. The receiving mailbox (the throwaway mailbox that only receives the demo mails) is a plausible reading but UNCONFIRMED: the names "intake mailbox", "receiving mailbox" and "throwaway mailbox" may or may not be the same mailbox, and Row 4 does not run until the lead has shown, from the take's own settings, which mailbox is meant. The lead fills both words with the fill program handover/flows-audit/fill_flows/fill_flows.py (it replaces both words in the flow files). Nobody types the two addresses into the lead. The fill program reads the two addresses from the take program's own settings; the names of those settings are UNVERIFIED and are confirmed at the re-check. The take program's startup check is said to have already checked the mailboxes; also UNVERIFIED.
The fill program handles six placeholder words, per handover/flows-audit/fill_flows/README.md lines 9 to 11 and the list PLACEHOLDERS in handover/flows-audit/fill_flows/fill_flows.py (lines 65 to 72): PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID, HS_CRED_PLACEHOLDER, FROM_ADDRESS_PLACEHOLDER and INTAKE_ADDRESS_PLACEHOLDER. All six are written as literal values into a COPY of the flow files; the original files are not changed. SUB_WORKFLOW_ID is known only after the sub-flow is imported (README lines 115 to 141, the walk-through, give the order); the lead verifies that order at the re-check. Whether every one of the six occurs in the four real flow files is UNVERIFIED (an earlier note, evidence-f3-r7.md, warns that some are "not used by any node" in some folders); the check below reports what is really left.
Mail login (separate from the two address words): OWNER-STEPS version 3, step 8, says the owner types the sending mailbox address and its app password into n8n himself, inside n8n only, never in a message. This is UNCONFIRMED. Do not ask the owner to do it until the lead has confirmed step 8 at the re-check; if it is not confirmed, this paragraph is deleted.
Third address: mf-recovery.json line 178 uses DESK_ALERT_TO. "Desk" is the studio's own name for the person or mailbox that receives the stuck-mail alert. The lead's statement (the lead verifies; it replaces the earlier wording "read from an n8n setting"): the take blocks environment access inside n8n nodes (handover/flows-audit/ORDERS.md line 81), so DESK_ALERT_TO is NOT read from an n8n setting; it is a literal value that the fill program writes into the copy. The fill program README line 32 lists DESK_ALERT_TO, DESK_URL and DESK_TIMEOUT_MS as keys for the folder n8n-flows-real-v5, so the same fill step also fills DESK_URL and DESK_TIMEOUT_MS. The route is the fill program's literal values (the program is frozen; no n8n setting is changed), per the lead's answer Q21 (ORDERS.md line 132, under the heading on line 131); the check afterwards is that no flow node reads $env. The value comes from the same values file; where the lead keeps it is UNVERIFIED (the lead checks the take's start script).

L5. After L4, run the fill program's own check command on the filled copy, not a hand search: `python3 -I "$TOOL" check <filled folder>` (README lines 78 to 99 say it must report `0 problem(s)` before anything is imported; the lead verifies the exact command line at the re-check). That check covers the six placeholder words and the leftover environment markers; it also refuses a copy marked NOT READY. A hand search is not a substitute. Then, before the first send, run the column check (one psql command; psql is the Postgres command-line program) against the take's own Postgres database, never against another database:
   psql -h <HOST> -U <DB_USER> -d <DB_NAME> -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'mf_leads' AND column_name LIKE 'alert_%' ORDER BY column_name;"
(The three words in angle brackets are the take's own database host, user and name; they are not written here.)
Expected output: exactly four rows (the four stuck-mail columns), in this order: alert_attempts, alert_sent, alert_token, alert_until. If a column is missing or the number of rows differs, the lead stops, sends nothing, and tells the owner in one plain sentence which column is missing. The owner does nothing in that case; the lead repairs it. The psql command itself was not run and its validity is UNVERIFIED.

L6. First send: the lead sends the first made-up person only after L1 to L5 are done.
Port (decision 6 of 2026-11-16, inputs/DECISIONS-2026-11-16.md line 7): the rehearsal runs on port 5690, named here once and nowhere else in this sheet. The real take uses its own free port, which the lead names in the plan; ports 5678 and 5679 are the owner's own n8n and the take never uses them. The lead verifies this at the re-check.

Lead-only note on the older sheet: line 103 of inputs/OWNER-STEPS-realrun-v3.md says the script archives contacts when `end` is typed (line 104 adds that leftover contacts are deleted by the owner by hand). Decision 2 of 2026-11-16 (inputs/DECISIONS-2026-11-16.md line 3) replaces them: the take is read-only, deletes and archives no contacts, and the owner deletes leftover made-up contacts by hand (Step D). The lead verifies at the re-check that the take scripts match decision 2. The owner does not read this note.

## Take-day lead list (lead's answer Q22, ORDERS.md lines 134 and 135, 11:30Z)
One list. Every row has the owner column "lead": the owner does none of these rows. The owner's part stays Step A and Step D only. Nothing here ran; every check is a plan the lead carries out.

| # | Owner | When | Step |
|---|-------|------|------|
| T1 | lead | take prep, before scene 2 | Use a lead id and an e-mail address (both made up) that were never used before: not in the practice run, not in the rehearsal, not in the Row 4 test. Check that the table mf_leads has 0 rows for that lead_key (the lead's column name for the lead id; the lead verifies the name in the table file). Empty the receiving mailbox or filter it so older mails cannot be counted as the take's mail (how to empty or filter: UNVERIFIED, the lead decides at re-pin). |
| T2 | lead | during and after the take | Proof of "processed once" is all three together: exactly 1 mail in the receiving mailbox, plus the mf_leads row for that lead_key, plus the reply to the second POST (the second send of the same lead id) arriving in under 10 seconds. The count of CRM rows (HubSpot contacts) alone is NOT proof, because the CRM row is keyed on the e-mail address only. The claims table must say the same; it is a different file, so the lead or another fixer changes it (see the log). |
| T3 | lead | scene 4 | The lead stops and starts n8n with the take scripts (decision 7 of 2026-11-16). The owner never does it. The stopwatch is the owner's phone clock, not a tool. If no takeover (the work being picked up again after n8n restarts) shows within 2 minutes, scene 4 is cut. The takeover line is spoken only after a rehearsal has shown it. |
| T4 | lead | before the take | If check P4a of handover/flows-audit/CLAIMS-TABLE.md (line 30: what the real CRM answers with for a contact's number) fails, the take is postponed. Failed rows are never filmed. |
| T5 | lead | at re-pin (re-pin = moving the demo to the new core version) | The re-pin happens after r20, r21 and r22 are merged, reviewed and have final evidence. It does not happen before about 6 hours after 11:30Z (11:30 UTC = 17:00 IST). The lead sets the time then. Date and time: TBD. No date is written here. |
| T6 | lead | at re-pin | The port of the real take and the check of n8n_api.py (scripts\n8n_api.py, decision 7): lead, at re-pin, time TBD. |
| T7 | lead | take prep | Made-up sender and receiver addresses are chosen and checked before filming. Only made-up addresses appear on screen. |
| T8 | lead | during filming | Screens that are shown and not opened: credential pages, Settings, any node output that holds environment values. They are not opened on camera. |
| T9 | lead | after filming | The lead watches the whole recording once, start to end, before anything is published. |
| T10 | lead | during and after each take | Any extra mail in the mailbox means: stop and retake. It is not explained away. |
| T11 | lead | any time a check fails | Abort-and-retake rule: the lead calls the abort. Clean check with new keys (a new lead id and a new e-mail address), then film again. |

Wording note: two proposed steps in the fifth rewrite of this sheet were labelled P1 and P2; those labels clash with the check names P1 and P2 of the claims table, so they are now T1 and T2 and are no longer proposals. The source text for the checks is handover/flows-audit/reviews/adversarial-takeday-r1.md items 1 and 2 (a reviewer's text read, not run); the sources for T7 to T11 are the review gaps named in the lead's order of this round.

## Row 4: one made-up person through the real HubSpot trial account (lead's part)
This is the owner's decision of 2026-11-16: one made-up person goes through the real flows into the real HubSpot trial account, replacing a larger set of real-account checks (decision 8 in inputs/DECISIONS-2026-11-16.md; item 5 of the lead's answer Q17 in handover/flows-audit/ORDERS.md line 117; the Q14 answer holds no decision 5). Why one and not more: it keeps the real-account use and the cost as small as possible.
Row 4 comes before the take; on the take day the rows T1 to T11 apply. Do not run Row 4 until: (i) the practice run passed, (ii) the mailbox names are confirmed (L4), (iii) the owner's "yes, US$X" has arrived (Step A).
Step B (the lead): sends ONE made-up person (made-up name, made-up e-mail address) through the real flows into the real HubSpot trial account.
Step C (the lead checks four things, called "the four checks"):
 (a) the contact number HubSpot sends back is all digits. The flow reads the field "id" first and, if there is none, the field "vid" (an older name HubSpot may use for the same number; whether it is always the same number as "id" is not verified), see mf-sub-crm-mail.json lines 117 and 146. The lead reads the number the flow actually stores in the column crm_id. In this sheet "contact number" always means that HubSpot number.
 (b) the incoming-people table has exactly one row for that made-up person, and in its column state the value is done (the flow sets state='done', mf-sub-crm-mail.json line 284; the allowed values are in the table file).
 (c) exactly one mail arrived, in the receiving mailbox (not confirmed, see L4). The lead looks at it; the owner does not.
 (d) exactly one contact for that made-up person exists in HubSpot.
 If any of the four checks is not as written, the lead stops, does not start the rehearsal, and tells the owner in one sentence. If all four pass, the lead tells the owner so in one message and goes on to the Step D message.
Step D (the lead's part): the contact stays in HubSpot, because the take never deletes contacts. The lead sends the owner one message holding the made-up name, the made-up e-mail address and the contact number, then waits for the owner's "deleted" (see "For the owner").

The checks above were read from files, not run. The lead verifies, at the lead's re-check of the take scripts against this audit (not yet done), all rows, all line numbers and every item marked UNVERIFIED.

---
Footer: version history
- Third rewrite (lead answer to question 20, 11:20Z): every fact about the take folder and mailbox addresses written as "the lead verifies at the re-check"; none stated as fact.
- Second rewrite: after the stranger re-read. Text only; nothing was run. Made-up data only.
- Fifth rewrite (round 5): applied reviews/crossread-demo-r1.md items 2, 3 and 4 and reviews/adversarial-takeday-r1.md items 1 and 2 (proposed); change log in handover/flows-audit/fix-ownersteps-r5.md.
- Fourth rewrite (round 4, this file): applied the stranger review of question 20 (handover/flows-audit/reviews/stranger-ownersteps-q20.md); change log in handover/flows-audit/fix-ownersteps-r4.md.
- Sixth rewrite (round 6): applied the citation mismatches of reviews/citations-ownersteps-r5.md, the lead's answer Q22, and the review gaps T7 to T11; change log in handover/flows-audit/fix-ownersteps-r6.md.

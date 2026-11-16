# Rows for OWNER-STEPS version 4 (the lead pastes these)

> STATUS: UNVERIFIED. Nothing ran. Every fact about files, line numbers, mailbox addresses and the take folder below was read from text, not run. Nothing here is a yes to act on until the lead writes "re-check done" with the date and time (UTC and IST) at the top of this sheet. Until then the owner does nothing from this sheet.

## For the owner (read only this part)
You are the owner. Only two things on this sheet are yours: Step A and Step D, both inside "Row 4" below. Everything else is the lead's work. OWNER: stop reading after Step A and Step D.

What you do not do: you type no folder path, no mailbox address and no password into any message to the lead. Never paste a password, key or app password (a 16-letter Google password for one program) into a chat message or a file.

Step A (your yes, before anything real is sent). The lead sends you a message that holds one number: the cost in US dollars of sending one made-up person through the real HubSpot trial account. The sheet's expectation is US$0 (one made-up person, one mail, no paid AI call), but only the number in the lead's message counts.
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
- L1 copy the table file; L2 create the database from it; L3 import the flow files into n8n; L4 fill the two address words; L5 check no placeholder word is left in the four flow files, then run the column check; L6 the first send ("first send" = the first made-up person sent into the flows).
- Row 4 happens after the practice run passes, after the owner's "yes, US$X", and before the rehearsal.

L1. Copy the table file (before the database is created and before the flow files are imported). The take uses handover/demo/n8n-flows-v4/mf_leads.sql. It has four extra stuck-mail columns. The older file handover/demo/n8n-flows/mf_leads.sql has none (the word "alert" occurs 0 times in it, counted by search). Reason: the recovery flow handover/demo/n8n-flows-real-v5/mf-recovery.json uses all four columns (lines 124, 204 and 228). That flow runs every 30 seconds (lines 9 and 10) and its alert-claim step carries on after an error (line 141, onError continueRegularOutput). What would happen on the older table is NOT KNOWN: nothing was run. It may fail every 30 seconds without stopping the flow, in which case no stuck-mail alert is sent; this is a guess from reading the files. The take does not check the stuck-mail alert by itself (OWNER-STEPS version 3, line 166). The lead verifies, at the re-check of the take scripts against this audit (not done yet; the audit has not seen those scripts), that the copied file is the v4 one.

L2. Create the database from the copied table file. The lead verifies the database is the take's own database and no other. L3. Import the flow files into n8n. Nothing else to write here.

L4. Fill the two address words in the mail steps. FROM_ADDRESS_PLACEHOLDER appears in mf-recovery.json (line 177) and in mf-sub-crm-mail.json (line 256); it is the address shown as "From" on the mail. By OWNER-STEPS version 3 (steps 1 and 3) that is the company address, shown through the Gmail setting "Send mail as" (a Gmail setting that lets one mailbox send mail that shows another address as "From"). INTAKE_ADDRESS_PLACEHOLDER appears once, in mf-sub-crm-mail.json (line 257), as the "To" of the thank-you mail. The file does not say which mailbox that is. The receiving mailbox (the throwaway mailbox that only receives the demo mails) is a plausible reading but UNCONFIRMED: the names "intake mailbox", "receiving mailbox" and "throwaway mailbox" may or may not be the same mailbox, and Row 4 does not run until the lead has shown, from the take's own settings, which mailbox is meant. The lead fills both words with the fill program handover/flows-audit/fill_flows/fill_flows.py (it replaces both words in the flow files). Nobody types the two addresses into the lead. The fill program reads the two addresses from the take program's own settings; the names of those settings are UNVERIFIED and are confirmed at the re-check. The take program's startup check is said to have already checked the mailboxes; also UNVERIFIED.
Mail login (separate from the two address words): OWNER-STEPS version 3, step 8, says the owner types the sending mailbox address and its app password into n8n himself, inside n8n only, never in a message. This is UNCONFIRMED. Do not ask the owner to do it until the lead has confirmed step 8 at the re-check; if it is not confirmed, this paragraph is deleted.
Third address: mf-recovery.json line 178 reads DESK_ALERT_TO from an n8n setting. "Desk" is the studio's own name for the person or mailbox that receives the stuck-mail alert; where DESK_ALERT_TO is set is UNVERIFIED (the lead checks the take's start script).

L5. After L4, check that no placeholder word is left in the four flow files (search for the two words above and DESK_ALERT_TO); this is also verified at the re-check. Then, before the first send, run the column check (one psql command; psql is the Postgres command-line program) against the take's own Postgres database, never against another database:
   psql -h <HOST> -U <DB_USER> -d <DB_NAME> -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'mf_leads' AND column_name LIKE 'alert_%' ORDER BY column_name;"
(The three words in angle brackets are the take's own database host, user and name; they are not written here.)
Expected output: exactly four rows (the four stuck-mail columns), in this order: alert_attempts, alert_sent, alert_token, alert_until. If a column is missing or the number of rows differs, the lead stops, sends nothing, and tells the owner in one plain sentence which column is missing. The owner does nothing in that case; the lead repairs it. The psql command itself was not run and its validity is UNVERIFIED.

L6. First send: the lead sends the first made-up person only after L1 to L5 are done.

## Row 4: one made-up person through the real HubSpot trial account (lead's part)
This is the owner's decision of 2026-11-16: one made-up person goes through the real flows into the real HubSpot trial account, replacing a larger set of real-account checks (decision 8 in inputs/DECISIONS-2026-11-16.md; decision 5 of the lead's answer to questions 14 and 17 in handover/flows-audit/ORDERS.md, not re-read for this edit). Why one and not more: it keeps the real-account use and the cost as small as possible.
Do not run Row 4 until: (i) the practice run passed, (ii) the mailbox names are confirmed (L4), (iii) the owner's "yes, US$X" has arrived (Step A).
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
- Fourth rewrite (round 4, this file): applied the stranger review of question 20 (handover/flows-audit/reviews/stranger-ownersteps-q20.md); change log in handover/flows-audit/fix-ownersteps-r4.md.

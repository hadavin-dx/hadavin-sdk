# Page statements V4: alerts and recovery (rewrite of section C for the v4 flows)

Written 2026-11-14 by the cloud demo session. Replaces section C of PAGE-STATEMENTS-DRAFT and the v4 additions draft. Nothing in this file was run by me. Plain words only.

## Tag legend
- MEASURED-ON-LAPTOP: the lead read the raw result files from the laptop run and relayed the numbers. I did not open those files. Laptop-local, not pushed. These runs used the v3 flows, lease 20 s, made-up data, one machine, stand-in SMTP, CRM and stage.
- RELAYED-INDEPENDENT: the lead told me the lane3 harness (a separate harness) printed this. I did not read the raw files. The lead did not name the lane3 flows version, the harness or the raw file names to me, so every such claim says "raw file: not named to me, ask lead".
- READ-ONLY: read from the flows or the SQL, never run.
- NOT RUN: no run exists, or none was given to me.

## Lane3 report check
I looked for the lane3 report under handover/demo3 and found nothing. The only report file in this checkout is handover/demo/REPORT.md, which is a different file and was not used. Nothing from lane3 is invented here: every lane3 claim below is the lead's relay only.

## Hard rules applied
- No claim "within 60 s" anywhere. The recovery sentence is statement 12.
- "Exactly one alert" is never said for a hold longer than 720 s (statement 7).
- The word "fixed" does not appear as a claim, because no named raw file with n has reached me.
- v3 can give two alerts. v4 gave one alert in 3 of 3 lane3 runs (n=3, one setup).

## Statements

1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow."
   Tag: READ-ONLY for the design. Backing runs are on v3 only (statements 2 and 3).
   Test: none for the design sentence.
   Raw file: none.

2. "On the v3 flows, a lead that failed before any mail step started ended in state failed with exactly 1 alert, no mail, no CRM write. Two failure kinds were run, 3 runs each (n=3 and n=3, one machine, made-up data)."
   Tag: MEASURED-ON-LAPTOP (lead-read).
   Test: T8 (model stage refuses, errors or times out; 0 CRM writes, 0 model calls in the table) and T15 (CRM answers an error from the start; 0 mails, 0 CRM rows, 27 CRM calls refused).
   Raw file: V7-v3 folder, mf_result_T8.json and mf_result_T15.json, laptop-local.
   Note: the seconds to the final state were 88.4, 116.9 and 42.5 for T8, and 91.2, 88.3 and 110.1 for T15 (limit 210). Alert timing inside those runs is not stated to me beyond "1 alert each".

3. "The same failure cases (T8, T15) were not run on the v4 flows."
   Tag: NOT RUN (no v4 result for them was given to me).
   Test: T8, T15 on v4.
   Raw file: none.

4. "On the v3 flows, when n8n was killed after the mail step began, every lead ended unknown, none was lost and none was re-mailed: 20 of 20 for the kill after delivery and 20 of 20 for the kill after the mail was marked sent but before it was delivered. Time from kill to final state was 28.5 to 30.5 s and 28.4 to 31.0 s."
   Tag: MEASURED-ON-LAPTOP (lead-read).
   Test: K3 (kill after the mail was delivered, before the table update; 1 intake mail per lead) and K3B (kill after mail_sent was set, mail not yet delivered; 0 intake mails per lead). n=20 each, lease 20 s.
   Raw file: V7-v3 folder, mf_result_K3.json and mf_result_K3B.json, laptop-local.
   OPEN CONFLICT for the lead: the first V7 table lists 1 alert per lead for K3 and K3B, but the runner's final caveat says those result files have no per-lead alert count. Until the lead settles this, this page must NOT say "1 alert each" for K3 and K3B. It may say "unknown, counted 20 of 20".

5. "With the alert send alone refused by the mail server, the first alert did not come at once: in one run it arrived at 272.1 s, and there was no alert at 20 s. Do not write 'within 30 seconds' for this fault."
   Tag: MEASURED-ON-LAPTOP (lead-read), n=1, v3 flows.
   Test: AF1 (alert-only mail refusal, two refusals). Result: state unknown unchanged, 1 alert, 1 intake mail, 0 lost, 0 doubled.
   Raw file: V7-v3 folder, mf_result_AF1.json, laptop-local.

6. "On the normal path an alert goes out within about 30 seconds of the state change (one recovery tick)."
   Tag: READ-ONLY. No timing for the normal path was given to me.
   Test: none.
   Raw file: none.

7. "On v3 a lead can get two alert e-mails when the mail server holds its answer for 90 seconds, because the first claim lasts 60 seconds. On v4 the alert claim window is 720 seconds, and the same 90 second hold gave exactly 1 alert in 3 of 3 lane3 runs (n=3, one setup, first alert at about 120 s). That is all that was run. For a hold longer than 720 seconds nothing was run: a second alert is possible and untested."
   Tag, v4 hold of 90 s: RELAYED-INDEPENDENT. Raw file: not named to me, ask lead.
   Tag, v3 two alerts: RELAYED-INDEPENDENT. Raw file: not named to me, ask lead.
   Tag, hold beyond 720 s: NOT RUN.
   Test: lane3 B90 (answer held 90 s), v3 build and v4 build.
   OPEN CONFLICT for the lead: my earlier draft says the v3 result was n=1 (2 alerts at about 120 s); the lead note says 3 of 3 on v3; the earlier lead note said v4 n=2 while the latest relay says v4 n=3. I use n=3 for v4 as relayed last. For v3 write "in at least one lane3 run" until the lead gives n and the file.

8. "In two other lane3 cases the first alert came at about 270 s (case A, n=2) and at about 750 s (case C, n=1)."
   Tag: RELAYED-INDEPENDENT. Raw file: not named to me, ask lead.
   Test: lane3 case A and case C. I do not know what these cases do or which flows version they ran on; do not map them to a page sentence until the lead says. Do not use this as support for any "alert time" promise.

9. "On v4 the alert claim window is 720 seconds, and after a failed alert send the next try waits 60 seconds times the attempt count, capped at 5 (60, 120, 180, 240, 300 s)."
   Tag: READ-ONLY (v4 flow build and SQL).
   Test: none.
   Raw file: none.

10. "On v4 a duplicate alert is still possible if the table update fails after a successful send, or if a send outlasts 720 seconds. A duplicate, never a loss, is the design."
    Tag: READ-ONLY design limit.
    Test: none; the 720 second case is NOT RUN (see 7).
    Raw file: none.

11. "There is no limit on alert retries (the attempt counter only counts). The only alert channel is e-mail through the same mail server that sends the lead mail. While that server is down nobody is notified, and there is no second channel. A person would see the unsent alerts only by looking at the table."
    Tag: READ-ONLY. A dead mail server for 10 minutes: NOT RUN. A Slack alert: NOT BUILT.
    Test: none.
    Raw file: none.

12. "In my runs the slowest recovery was 59.6 s against a 60 s target, margin 0.4 s, n=20 per kill point, one machine." Detail: kill point K1 (kill after the claim, before the CRM write) slowest 59.6 s, median 29.65 s, fastest 18.0 s; kill point K2 (kill after the CRM write, before the mail step) slowest 59.4 s, median 29.5 s, fastest 17.3 s, margin 0.6 s. Every lead in both was completed, none lost, none doubled. v3 flows, lease 20 s, made-up data.
    Tag: MEASURED-ON-LAPTOP (lead-read).
    Test: K1 and K2, n=20 each.
    Raw file: V7-v3 folder, mf_result_K1.json and mf_result_K2.json, laptop-local.
    Note: the margin is thin; one slower run would pass the target. Never shorten this to "within 60 s".

13. "No mail was sent twice for one lead id in the four kill points K1, K2, K3 and K3B: 80 kills, 0 doubled, 0 lost (v3 flows, lease 20 s). This is not a claim about all faults."
    Tag: MEASURED-ON-LAPTOP (lead-read).
    Test: K1, K2, K3, K3B, n=20 each.
    Raw file: V7-v3 folder, mf_result_K1.json, K2, K3, K3B, laptop-local.
    Caveat from the runner: the doubled count folds in the alert count and was not separately verified for these four.

14. "The kill series (K1, K2, K3, K3B), the recovery times and the no-double result were not run on the v4 flows, so on v4 they are not measured."
    Tag: NOT RUN (no v4 kill series result given to me).
    Test: K1, K2, K3, K3B on v4.
    Raw file: none.

15. "A lead that used up its three tries after the mail step started is called unknown, not failed."
    Tag: READ-ONLY (the failure-marking SQL). The kills in K3 and K3B end in unknown by a different branch. The cap-after-mail branch itself: NOT RUN.
    Test: none.
    Raw file: none.

16. "How long the n8n Send Email node waits for a silent mail server is not measured. From the mail library inside n8n 2.46.6 it is up to 2 minutes to connect, 30 seconds for the greeting and 10 minutes of silence after that; the node has no timeout setting."
    Tag: library values READ-ONLY; the node's real wait NOT RUN.
    Test: AF2, not run.
    Raw file: none.

17. "Only lease 20 s was measured. Recovery times at lease 45 s and 120 s (the v4 flows ship with 120) were not run, so no recovery time is stated for them."
    Tag: NOT RUN for 45 s and 120 s.
    Test: lease table, not run.
    Raw file: none.

18. "With the four n8n settings turned off (success data, error data, progress data, manual execution data), n8n still keeps the lead's name and e-mail from the incoming request in its own database until its pruning removes the run; the pruning age is not measured. Secrets were not found in the scan. Do not put a secret in a lead form field."
    Tag: carried over unchanged from the old section C, not re-checked here. Earlier tags: laptop V5 T7b relayed pass; lane3 HB171 RELAYED-INDEPENDENT.
    Test: T7b, HB171.
    Raw file: not named to me, ask lead.

Total: 18 statements.
NOT RUN statements: 3, 14, 17. Part NOT RUN: 7 (hold beyond 720 s), 11 (dead mail server 10 minutes; Slack NOT BUILT), 15 (cap-after-mail branch), 16 (node wait).

## Honest limits (what is not measured)
- The Send Email node timeout (AF2 not run); only library values were read.
- AF2, K4, K5, T10, T11, T13: not in the claims above. T10, T11 and T13 numbers exist in the lead's V7 file, but I am not using them here; T13 was never re-read by the lead.
- Lease 45 s and 120 s: no recovery table.
- Any v4 run by the demo harness: none given to me (T8, T15, K1 to K3B, AF1 on v4 not run).
- A hold of the alert answer beyond 720 s: not run.
- A real mailbox, a real HubSpot account, a Slack alert: none.
- Lane3 claims are second-hand: no raw file name, no flows version, no harness name reached me. Cases A and C are unmapped.
- One machine, made-up data, stand-in services, n small (n=3 for the lane3 hold, n=1 for the 272.1 s alert).
- The n8n alert count for K3 and K3B conflicts between two lead notes (statement 4).

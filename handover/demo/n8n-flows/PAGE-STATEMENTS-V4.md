# Page statements V4: alerts and recovery (rewrite of section C for the v4 flows)

Changelog (2026-11-14 audit fixes; statement 19 added after lane3 HB189):
1. Fixed: 4, 7, 12, 13, 14, 17 now use the settled numbers (K3 and K3B 1 alert each, v3 B90 n=3, v4 B90 n=3 plus 1 laptop run, lane3 K1 144.3 s at lease 120 s); 12 lost "in my runs" and "would pass".
2. Moved to UNBACKED (do not publish until backed): the 30 s alert timing (6), lane3 cases A and C (8), library timeouts (16), the scan claim (18). Statements 1, 2, 3, 5 got small wording fixes.
3. Added: two different K3 names, the new tag RELAYED-LEAD, and one recovery rule of thumb (statement 17).

Written 2026-11-14 by the cloud demo session. Replaces section C of PAGE-STATEMENTS-DRAFT and the v4 additions draft. Nothing in this file was run by the cloud session. Plain words only.

## Tag legend
- MEASURED-ON-LAPTOP: the lead read the raw result files from the laptop runs and relayed the numbers. The cloud session did not open those files. Laptop-local, not pushed. These runs used the v3 flows, lease 20 s, made-up data, one machine, stand-in SMTP, CRM and stage. Written as "in the laptop runs (lead-read)".
- RELAYED-INDEPENDENT: the lead relayed what the lane3 harness (a separate harness) printed. Raw lane3 reports HB180 and HB186 are named but were not found in the handover tree, so they could not be checked.
- RELAYED-LEAD: the lead relayed a pass from the laptop V4-par run; the result file was not read.
- READ-ONLY: read from the flows or the SQL, never run.
- NOT RUN: no run exists, or none was given to the cloud session.
- UNBACKED: a statement with no run, no definition or no named file. Do not publish until backed.

## Two different K3 tests (never mix them)
- demo K3 (n8n killed after the mail was delivered): the laptop harness test, statements 4 and 13.
- lane3 K3 (killed after the CRM write, closest to demo K2): the lane3 test, relayed only. No lane3 K3 figure is used on this page.

## Lane3 report check
No lane3 report was found under handover/demo3. HB180 and HB186 are absent from the handover tree. The only report file in this checkout is handover/demo/REPORT.md, a different file, not used. Every lane3 number below is a lead relay only.

## Hard rules applied
- No claim "within 60 s" anywhere without the 20 s test lease. The recovery wording is statements 12 and 17.
- "Exactly one alert" is never said for a hold longer than 720 s (statement 7).
- The word "fixed" does not appear as a claim, because no named raw file with n has reached the cloud session.
- v3 gave two alerts in 3 of 3 lane3 B90 runs. v4 gave exactly 1 alert in 3 of 3 lane3 B90 runs, and 1 on the laptop V4-par run.

## Statements

1. "A lead whose mail outcome is unknown, or that could not be finished, is noted in the lead table and an alert e-mail is sent to the owner address by the recovery flow."
   Tag: READ-ONLY for the design. Backing runs: v3 runs (statements 2 and 3 area) plus v4 B90 (statement 7).
   Test: none for the design sentence.
   Raw file: none.

2. "On the v3 flows, a lead that failed before any mail step started ended in state failed with exactly 1 alert, no mail, no CRM write. T8: three failure kinds, one run each. T15: three runs. One machine, made-up data."
   Tag: MEASURED-ON-LAPTOP (lead-read).
   Test: T8 (model stage refuses, errors or times out; 0 CRM rows, 0 mails, 0 model calls) and T15 (CRM answers an error from the start; alerts 1, 1, 1; 0 mails; 0 CRM rows; 27 CRM calls refused).
   Raw file: V7-v3 folder, mf_result_T8.json and mf_result_T15.json, laptop-local.
   Note: seconds to the final state for T8 by kind: refuse 88.4, error 116.9, timeout 42.5. For T15 (three runs): 91.2, 88.3 and 110.1 (limit 210). Alert timing inside those runs is not stated beyond "1 alert each".

3. "The same failure cases (T8, T15) were not run on the v4 flows."
   Tag: NOT RUN (no v4 result for them was given). Re-check against the laptop V4-par result before publishing, because that runner may have produced v4 numbers since.
   Test: T8, T15 on v4.
   Raw file: none.

4. "On the v3 flows, in the laptop runs (lead-read), when n8n was killed after the mail step began, every lead ended unknown, none was lost and none was re-mailed, with 1 alert each: 20 of 20 for demo K3 (n8n killed after the mail was delivered) and 20 of 20 for K3B (killed after the mail was marked sent but before it was delivered). Time from kill to final state was 28.5 to 30.5 s and 28.4 to 31.0 s."
   Tag: MEASURED-ON-LAPTOP (lead-read).
   Test: demo K3 (1 intake mail per lead) and K3B (0 intake mails per lead). n=20 each, lease 20 s. Alerts: 1 each, read from the per_lead alerts field. K1 = 0 alerts and K2 = 0 alerts in the same series.
   Raw file: V7-v3 folder, mf_result_K3.json and mf_result_K3B.json, laptop-local.

5. "On the v3 flows, with the alert send alone refused by the mail server, the first alert did not come at once: in one run it arrived at 272.1 s, and there was no alert at 20 s. Do not write 'within 30 seconds' for this fault."
   Tag: MEASURED-ON-LAPTOP (lead-read), n=1, v3 flows.
   Test: AF1 (alert-only mail refusal, two refusals). Result: state unknown unchanged, 1 alert, 1 intake mail, 0 lost, 0 doubled.
   Raw file: V7-v3 folder, mf_result_AF1.json, laptop-local.

6. "On the normal path an alert goes out on the next recovery tick; the flow runs that tick every 30 s."
   Tag: READ-ONLY for the 30 s tick in the flow.
   Test: none.
   Raw file: none.
   UNBACKED (do not publish until backed): any promise such as "within about 30 seconds of the state change". No run timed the normal-path alert. NOT RUN.

7. "On v3 a lead got two alert e-mails when the mail server held its answer for 90 seconds, because the first claim lasts 60 seconds: 2 alerts in 3 of 3 lane3 runs (B90, n=3). On v4 the alert claim window is 720 seconds, and the same 90 second hold gave exactly 1 alert in 3 of 3 lane3 runs (B90, n=3, first alert at about 120 s), plus 1 of 1 on the laptop V4-par run (pass). That is two setups. For a hold longer than 720 seconds nothing was run: a second alert is possible and untested."
   Tag, v3 B90 (HB180): RELAYED-INDEPENDENT. Raw report HB180 not found in handover.
   Tag, v4 B90 on lane3 (HB186): RELAYED-INDEPENDENT. Raw report HB186 not found in handover.
   Tag, v4 B90 on the laptop V4-par: RELAYED-LEAD (result file not read).
   Tag, hold beyond 720 s: NOT RUN.
   Test: B90 (answer held 90 s), v3 build and v4 build.
   Note: "exactly 1 alert" applies to the 90 s hold only.

8. UNBACKED (do not publish until backed). Relayed only: in two other lane3 cases the first alert came at about 270 s (case A, n=2) and at about 750 s (case C, n=1).
   Tag: UNBACKED, RELAYED-INDEPENDENT. Cases A and C have no definition, no flows version and no file. Case C at 750 s is near the 720 s window and could be misread. Do not use for any alert-time sentence.
   Test: lane3 case A and case C. NOT RUN by the cloud session.
   Raw file: none named.

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

12. "At a test lease of 20 s, in the laptop runs (lead-read), the slowest recovery was 59.6 s (K1) and 59.4 s (K2), n=20 per kill point, one machine, v3 flows. This is a 20 s lease result only; it does not carry over to the 45 s film lease or the 120 s shipped lease."
    Detail: K1 (kill after the claim, before the CRM write) slowest 59.6 s, median 29.65 s, fastest 18.0 s, margin 0.4 s. K2 (kill after the CRM write, before the mail step) slowest 59.4 s, median 29.5 s, fastest 17.3 s, margin 0.6 s. Every lead in both was completed, none lost, none doubled. Alerts: 0 each.
    Tag: MEASURED-ON-LAPTOP (lead-read).
    Test: K1 and K2, n=20 each.
    Raw file: V7-v3 folder, mf_result_K1.json and mf_result_K2.json, laptop-local.
    Note: the margin is thin; one slower run would miss 60 s. Never shorten this to "within 60 s".

13. "In the laptop runs (lead-read), no mail was sent twice for one lead id in the four kill points K1, K2, demo K3 and K3B: 80 kills, 0 doubled, 0 lost (v3 flows, lease 20 s). Alerts per lead were read: demo K3 1, K3B 1, K1 0, K2 0. This is not a claim about all faults."
    Tag: MEASURED-ON-LAPTOP (lead-read).
    Test: K1, K2, demo K3, K3B, n=20 each.
    Raw file: V7-v3 folder, mf_result_K1.json, K2, K3, K3B, laptop-local.

14. "On the demo harness the kill series (K1, K2, demo K3, K3B) was not run on the v4 flows. The only v4 recovery figure is a lane3 relay: K1 recovered in 144.3 s at its lease of 120 s (n=1, v4 K1). The raw lane3 report was not seen."
    Tag: NOT RUN for the demo harness on v4. The lane3 figure: RELAYED-INDEPENDENT.
    Test: K1, K2, demo K3, K3B on v4 (harness); lane3 v4 K1.
    Raw file: none for the harness; lane3 report not found in handover.

15. "A lead that used up its three tries after the mail step started is called unknown, not failed."
    Tag: READ-ONLY (the failure-marking SQL). The kills in demo K3 and K3B end in unknown by a different branch. The cap-after-mail branch itself: NOT RUN.
    Test: none.
    Raw file: none.

16. UNBACKED (do not publish until backed). "How long the n8n Send Email node waits for a silent mail server is not measured." Library values (2 minutes to connect, 30 seconds for the greeting, 10 minutes of silence, version 2.46.6, node has no timeout setting) are library defaults with the source file not named; the node wait was not measured.
    Tag: UNBACKED. The node's real wait NOT RUN.
    Test: AF2, not run.
    Raw file: none named.

17. "Recovery within 60 s was measured only at the 20 s test lease (max 59.6 s, margin 0.4 s, n=20 per kill point, one machine); at the shipped 120 s lease lane3 measured 144.3 s once (n=1, v4 K1); at the 45 s film lease nothing is measured. Rough rule from lane3: about the lease plus 25 s; the 20 s data is lease + 40 s so treat the rule as rough."
    Tag: 20 s figure MEASURED-ON-LAPTOP (lead-read). 120 s figure RELAYED-INDEPENDENT (one figure, report not seen). 45 s: NOT RUN.
    Test: lease table, not run.
    Raw file: V7-v3 folder for the 20 s figure; none for the others.

18. UNBACKED (do not publish until backed). Carried over from the old section C, not re-checked: with the four n8n settings turned off (success data, error data, progress data, manual execution data), n8n may still keep the lead's name and e-mail from the incoming request in its own database until pruning removes the run; the pruning age is not measured. "Secrets were not found in the scan" has no raw file. Do not put a secret in a lead form field.
    Tag: UNBACKED. If kept later, tag RELAYED-INDEPENDENT and name the files (T7b, HB171; HB171 is not in handover).
    Test: T7b, HB171. NOT RUN by the cloud session.
    Raw file: none named.

Total: 18 statements.
UNBACKED (do not publish until backed): 8, 16, 18, and the 30 s timing promise in 6.
NOT RUN statements: 3, 14 (demo harness on v4). Part NOT RUN: 6 (normal-path alert time), 7 (hold beyond 720 s), 11 (dead mail server 10 minutes; Slack NOT BUILT), 15 (cap-after-mail branch), 16 (node wait), 17 (lease 45 s).

19. "An alert can arrive up to about 13 minutes late if n8n itself dies while it is sending the alert; it is not lost." [RELAYED-INDEPENDENT, lane3 HB189 v4 kill series, n8n killed 10 s into the alert send: exactly 1 alert, not lost, 780 s late because the killed send holds the 12 minute claim until it runs out; n=not given to me, raw file not named to me, ask lead. The cause is the 720 s claim window (statement 1) read from the v4 flow. NOT run by me.] Plain meaning: v4 trades v3's possible second alert for a possible late alert, and only when n8n dies during the alert send. Not an engineering change (the lead's RIGHT-SIZE call): the main flow and the doubtful-case scene are unaffected. Must NOT be shortened to "alerts always arrive within minutes" or to "exactly one alert" without this delay.

## Honest limits (what is not measured)
- The Send Email node timeout (AF2 not run).
- AF2, K4, K5, T10, T11, T13: not in the claims above. T13 was never re-read by the lead.
- Lease 45 s: nothing measured. Lease 120 s: one lane3 figure only.
- Any v4 run by the demo harness: none given (T8, T15, K1 to K3B, AF1 on v4 not run).
- A hold of the alert answer beyond 720 s: not run.
- A real mailbox, a real HubSpot account, a Slack alert: none.
- Lane3 claims are second-hand: HB180 and HB186 are named but absent from the handover tree. Cases A and C are undefined.
- Alert delay: up to about 13 minutes if n8n dies during the alert send (statement 19); n and raw file not given to me.
- One machine, made-up data, stand-in services, n small (n=3 for each lane3 hold, n=1 for the laptop V4-par run, n=1 for the 272.1 s alert, n=1 for the 144.3 s figure).
- Stale source note: the V7 numbers file still says v4 B90 n=2; the settled value is n=3 on lane3 plus 1 on the laptop. Fix it at its source (not done here).

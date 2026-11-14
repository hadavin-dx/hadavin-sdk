# Audit of PAGE-STATEMENTS-V4 (read-only, 2026-11-14)

Checked against: the V7 numbers file (with the lead correction of 16:50Z: K3 = 1 alert each, K3B = 1 each, K1 = 0, K2 = 0), the settled facts from the lead, and, for the READ-ONLY statements, the v4 recovery flow and the v4 table SQL (read, not run). I ran nothing.

Lane3 report HB186: ABSENT. A search of the whole handover tree for HB186 found no file. HB180 is also absent. So every lane3 number (B90 v3 3 of 3, B90 v4 n=3, K1 144.3 s at lease 120) is a lead relay that I could not check against a report. Nothing was invented.

## Counts
18 statements. OK 8. WRONG 1. UNBACKED 4. OUTDATED 5.

## WRONG and UNBACKED first
- 12 WRONG: voice, a false sentence, and the lease 20 s condition is not in the headline.
- 6 UNBACKED: "within about 30 seconds" for the normal path has no timing.
- 8 UNBACKED: lane3 cases A and C have no definition, version or file.
- 16 UNBACKED: the mail library values and the version number cite no file.
- 18 UNBACKED: carried over, not re-checked, no raw file.

## Table, every statement
| No. | Verdict | Why (quote the number or raw name it must match) | Fix |
|---|---|---|---|
| 1 | OK | Design sentence matches the v4 recovery flow (states unknown and failed get an alert; K1 and K2 per_lead alerts = 0 fits). The note "Backing runs are on v3 only" is stale: v4 B90 now exists (lane3 n=3, laptop V4-par 1). | Change the note to "v3 runs plus v4 B90 (statement 7)". |
| 2 | OK | T8 n=3 (0 CRM rows, 0 mails, 0 model calls, 1 alert); T15 n=3 (alerts 1,1,1; 0 mails; 0 CRM rows; 27 CRM calls refused). Seconds 88.4, 116.9, 42.5 and 91.2, 88.3, 110.1 match. Caution: the V7 header calls the T8 seconds min/median/max but lists them as refuse, error, timeout, so T8 is three failure kinds, one run each. | Say "T8: three failure kinds, one run each; T15: three runs" and label the three T8 seconds by kind. |
| 3 | OK | Absence claim; nothing in the V7 numbers covers v4 T8 and T15. The V4-par runner was still running v4 at the time of the V7 file, so it can go stale. | Re-check against the V4-par result before publishing. |
| 4 | OUTDATED | Says K3 and K3B must NOT say "1 alert each" (open conflict). The lead correction settles it: K3 per_lead alerts = 1 each, K3B = 1 each. Other numbers match: 20 of 20, 28.5 to 30.5 s, 28.4 to 31.0 s, intake mails 1 and 0. | Delete the conflict note, add "1 alert each (per_lead alerts field, n=20 each, lease 20 s)". Name K3 "killed after mail delivered" and keep it apart from lane3's K3 (see naming below). |
| 5 | OK | AF1 n=1: first alert 272.1 s, none at 20 s, 1 alert, 1 intake mail, 0 lost, 0 doubled, unknown 1. The quoted sentence does not say v3. | Add "on the v3 flows" inside the quoted sentence, not only in the tag. |
| 6 | UNBACKED | The flow has a 30 s recovery tick (read), but no run times the normal-path alert. "Within about 30 seconds" is a timing promise; a state change can wait a tick, then the node run. AF1 (272.1 s) shows alert time can differ widely. | Replace with "on the next recovery tick (every 30 s in the flow); the normal-path time was not measured". |
| 7 | OUTDATED | Says v3 "in at least one lane3 run"; settled: v3 B90 n=3 (HB180, 2 alerts in 3 of 3). Says v4 "3 of 3, one setup" and "That is all that was run"; settled: v4 B90 n=3 on lane3 (HB186, exactly 1 alert at about 120 s) PLUS 1 on the laptop V4-par (pass), so two setups and n=4 in total. The 720 s window is confirmed in the flow. The tag text "raw file: not named" is stale: HB180 and HB186 are named (but absent from handover). The 1 laptop run is relayed only, not read by the lead, so it needs its own tag. | Rewrite: "v3 B90: 2 alerts in 3 of 3 (lane3 HB180). v4 B90: exactly 1 alert in 3 of 3 (lane3 HB186, first alert about 120 s) and 1 of 1 on the laptop V4-par (pass, result file not read). Hold over 720 s: NOT RUN." Keep "exactly one alert" tied to the 90 s hold only. |
| 8 | UNBACKED | Cases A (about 270 s, n=2) and C (about 750 s, n=1) have no definition, flows version or file; the statement itself says not to map them. A statement that supports no sentence should not be on the page. Case C at 750 s sits near the 720 s window and could be misread. | Remove from the page until the lead defines A and C and gives the report id; keep in the lead notes only. |
| 9 | OK | Flow: AlertClaim interval 720 seconds; AlertBackoff = 60 seconds times LEAST(alert_attempts, 5), so 60, 120, 180, 240, 300 s. READ-ONLY tag justified. | None. |
| 10 | OK | AlertMark only matches the claim token, so a failed mark after a send, or a send longer than 720 s, lets the row be claimed again. READ-ONLY justified; the 720 s case is NOT RUN and says so. | None. |
| 11 | OK | AlertClaim has no cap on alert_attempts; AlertSend is the only channel (e-mail). Dead server 10 minutes: NOT RUN, Slack NOT BUILT, both stated. | None. |
| 12 | WRONG | (a) "In my runs" is false: the cloud session ran nothing; the lead read the raw files. (b) Headline "59.6 s against a 60 s target" carries no lease; it is true only at test lease 20 s, and the shipped lease 120 s recovers in about lease + 25 s (lane3 v4 K1 = 144.3 s at ITS lease 120 s, not a demo-harness figure). (c) Note says "one slower run would pass the target"; it would MISS it. Numbers match V7: K1 18.0 / 29.65 / 59.6, K2 17.3 / 29.5 / 59.4, margins 0.4 and 0.6 s, n=20 each. | Rewrite: "At a test lease of 20 s the slowest recovery was 59.6 s (K1) and 59.4 s (K2), n=20 each, v3 flows. This is a lease 20 s result only; it does not carry over to lease 45 s or 120 s." Fix "pass" to "miss". |
| 13 | OUTDATED | 4 x 20 = 80 kills, 0 doubled, 0 lost matches V7; intake mails 1, 1, 1, 0 per lead, so no second mail. But the closing caveat ("no per-lead alert count, doubled not separately verified") rests on the runner caveat that the lead has shown WRONG for K1, K2, K3, K3B. | Drop the caveat; say alerts per lead were read: K3 1, K3B 1, K1 0, K2 0. |
| 14 | OUTDATED | Says no v4 kill and recovery result exists. Settled: lane3 ran a v4 K1 recovery of 144.3 s at its lease 120 s. The demo harness has none, which is true; "not measured" is not. | Say "demo harness: not run on v4; lane3 relay: K1 144.3 s at lease 120 s, raw report not seen". |
| 15 | OK | MarkFailed: state is unknown when mail_sent is true, failed otherwise, once attempts reach 3. READ-ONLY justified; cap-after-mail branch NOT RUN stated. | None. |
| 16 | UNBACKED | The values (2 minutes connect, 30 s greeting, 10 minutes silence, version 2.46.6) cite no file in the handover; the version appears in readmes but the library timeouts appear nowhere in the tree. The AF2 NOT RUN tag is right. | Name the file that was read, or write "library defaults, source not named; node wait not measured". |
| 17 | OUTDATED | Says no recovery time is stated for lease 120 s. Settled: lane3 v4 K1 = 144.3 s at lease 120 s (about lease + 25 s). Flow check: v4 ships lease 120, film v4 flows use 45 s (confirmed), film lease 45 s is unmeasured. Caution: lease + 25 s rests on one figure; at test lease 20 s the max was lease + 39.6 s, so do not present it as a formula. | State the figure "144.3 s at lease 120 s (lane3, one figure)", then "lease 45 s: not measured", and no formula. |
| 18 | UNBACKED | Carried over, not re-checked; no raw file; tags T7b and HB171 are named only as relayed. HB171 is also not in handover. | Cut it from this page or re-check; if kept, tag RELAYED-INDEPENDENT and name the files. |

## Tag check
- MEASURED-ON-LAPTOP on 2, 4, 5, 12, 13: justified (the lead read the raw files for these; AF1, T8, T15 in the first V7 table, K1 to K3B re-read). Each carries v3, lease 20 s, laptop-local.
- RELAYED-INDEPENDENT on 7, 8, 18: justified as a tag, but the raw file is now NAMED for 7 (HB180, HB186), so the text "not named to me" is stale; and no report exists in handover to check.
- The laptop V4-par single run in 7 has no tag that fits (lead relay of "pass"); it needs "RELAYED, laptop V4-par, result file not read".
- READ-ONLY on 1, 9, 10, 11, 15: justified, checked against the flow. READ-ONLY on 6 is justified only for the 30 s tick, not for the promised time. READ-ONLY on 16 has no named file.
- NOT RUN on 3, 14, 17 and parts of 7, 11, 15, 16: correct, except that 14 and 17 are missing the lane3 v4 K1 figure.

## Rule check
- "Within 60 s" without lease 20 s: no literal use, but statement 12 gives the 60 s comparison without the lease in its headline, and statement 17 leaves 120 s unmeasured when it is relayed as 144.3 s.
- "Exactly one alert" for a hold over 720 s: none found. Statement 7 ties it to the 90 s hold.
- "Fixed" without a named raw file with n: the word is not used as a claim. Good.

## Naming problem the page must resolve
Lane3's test called K3 means "killed after the CRM write". The demo harness K3 means "killed after the mail was delivered". Harness K2 is the nearer match to lane3's K3 (after CRM write, before the mail step). Statements 4, 13 and 14 use the harness meaning. Any lane3 figure on the page needs its own name, such as "lane3 kill after CRM write".

## Stale source note
The V7 numbers file, line "Reading (lead)", still says v4 B90 n=2; the settled value is n=3 on lane3 plus 1 on the laptop. It should be corrected at its source.

## Top 5 problems
1. Statement 12: false voice ("my runs"), "would pass" should be "miss", and the 59.6 s headline has no lease 20 s condition; shipped lease 120 s is about lease + 25 s.
2. Statement 17 (and 14): says lease 120 s and v4 kills are unmeasured; lane3 v4 K1 = 144.3 s at lease 120 s exists as a relay. Only lease 45 s remains unmeasured.
3. Statement 7: v3 shown as "at least one run" (settled: 3 of 3, HB180); v4 shown as one setup (settled: lane3 n=3 HB186 plus 1 on the laptop V4-par); HB186 and HB180 are not in handover.
4. Statement 4 (and 13): the "do not say 1 alert each" conflict is resolved by the lead correction; the page still blocks a true figure and keeps a stale runner caveat.
5. Statements 6, 8, 16, 18: timing promise "within about 30 seconds" with no run; cases A and C undefined; library values and carried-over scan claim with no named file. Also K3 needs separate names for the harness and lane3.

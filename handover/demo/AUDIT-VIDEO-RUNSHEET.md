# Audit of the video run sheet (read-only, made-up data, no new measurements)

Inputs read in full: the run sheet and the V7 numbers file (lead-read, with the 16:50Z correction that per_lead rows carry alerts: K3 = 1 each, K3B = 1 each, K1 = 0, K2 = 0).
Lane3 report HB186: grep over the handover folder found NO file containing it. It is absent, so the v4 claims (B90 n=3, exactly 1 alert at about 120 s, plus 1 on the laptop V4-par) rest on the settled facts given to me, not on a document I could open. The V7 file still says "B90 n=2" for v4; that line is stale against the settled n=3.

Settled facts used as the yardstick:
- v3 B90: n=3, 2 alerts in 3 of 3 runs (lane3 HB180).
- v4 B90: n=3 lane3, exactly 1 alert at about 120 s, plus 1 on the laptop V4-par.
- lane3 v4 K1 recovery 144.3 s at its lease of 120 s.
- V7 recovery max 59.6 s (K1) and 59.4 s (K2) at TEST lease 20 s. So "within 60 s" holds only at lease 20 s. Shipped lease 120 s recovers in about lease + 25 s. Film lease 45 s is unmeasured.
- lane3 K3 = "killed after CRM write". Demo harness K3 = "killed after mail delivered". Same label, different fault.

## Part 1: scene by scene

| Scene | Verdict | Why |
|---|---|---|
| 1 Stack at rest | OK | T14 idle 120 s: all zero. Caption matches the row. T14 has no n in the table (shown as a dash): say "one idle run". |
| 2 One lead in | OK | Carries no number, and says so. Speed words are limited to the owner's live observation. Fine. |
| 3 Same lead again | UNBACKED | The only number is T13 (n=13), which the lead has NOT re-read. The backup rows K1, K2, K3, K3B are kill tests, not duplicate-send tests, so they do not back "sent again, nothing doubled". T13 is also three at once plus a database kill, while the scene is one sequential resend. |
| 4 Kill n8n, recovery | OUTDATED | Caption numbers match K1 and K2. But the "must not" cell says recovery at lease 120 s is not measured: lane3 measured 144.3 s at 120 s. Also the film lease is undecided, and 59.6 s is a 20 s-lease number. The lease + 25 s rule does not even fit the 20 s data (max 59.6 s is about lease + 40), so do not extrapolate it to 45 s. |
| 5 CRM refuses forever | OK | T15 n=3 backs 88 to 110 s, state failed, alerts 1,1,1, 0 mails, 0 CRM rows. The 2-alert flaw is correctly fenced. Real wait of 90 to 110 s is a lease 20 s figure; it changes if the lease changes. |
| 6 Doubtful: lead goes in | OK | No number, none claimed. |
| 7 Doubtful: mail may have gone | WRONG | The caption "the mail server took the mail, the answer never came back" describes option A. Under option B (harness K3) n8n is killed after delivery; no mail-server answer was lost. One caption cannot serve both options. Option A has no v3 number (T12 not run). A hand kill landing in the window between delivery and table update is not credible without a slowed stand-in step. |
| 8 Answer says unknown | UNBACKED | Reply text never checked on v3. Worse, under option B n8n is killed mid-request, so the caller may get no reply at all; "reads the reply aloud" may be impossible. This is my inference from how a kill works, not something I verified in the flow. |
| 9 One alert, no second mail | OUTDATED | Timings K3 28.5 / 29.45 / 30.5 s and K3B 28.4 / 29.45 / 31.0 s match. But the sheet still says the per-lead alert count is not verified; the lead correction (K3 = 1 each, K3B = 1 each) backs "1 alert each" for the kill variants. Update the must-not cell and risk 4. Still not backed for the stand-in drop variant. |
| 10 Table row | UNBACKED | Table screen never run. V7 has no alert_sent column; it has a per-lead alerts count. K3B sets mail_sent true while 0 mails reached the inbox, so the row "mail_sent true" next to an empty intake list will look like a contradiction without a caption. |
| 11 Dead alert server (optional) | OK | AF1 n=1: first alert 272.1 s, no alert at 20 s, 1 alert, state unknown. Sheet says n=1. Wording flaw: the fault is "451 refusal twice", not a dead server; the title overstates. Valid only at lease 20 s. |
| 12 Closing card | OK | K1, K2, K3, K3B n=20 each, 0 lost, 0 doubled, 80 kills: matches. Gaps to fix: 40 of the 80 ended as UNKNOWN by design (K3, K3B), not completed; the card does not state the v3 two-alert flaw, the 20 s versus shipped 120 s lease gap, or the recovery time at 120 s (144.3 s lane3). |

Counts: OK 6 (scenes 1, 2, 5, 6, 11, 12), WRONG 1 (scene 7), UNBACKED 3 (scenes 3, 8, 10), OUTDATED 2 (scenes 4, 9). Total 12.

Arithmetic check: the running time total of 330 s (355 s with scene 11) adds up correctly.

Correction rows to quote:
- Scene 4 caption: V7 FINAL K1 "20 / 0 / 0 / 0 / 18.0 / 29.65 / 59.6" and K2 "20 / 0 / 0 / 0 / 17.3 / 29.5 / 59.4", both at lease 20 s.
- Scene 7 option B caption: V7 first table K3 "n8n killed after the mail was delivered, before the table update ... UNKNOWN counted, 1 alert each, not re-mailed".
- Scene 9: V7 first table K3 "1 / 1 / 1 / 1" and K3B "1 / 0 / 1 / 1" (CRM / intake / alerts / model) with the 16:50Z correction.
- Scene 3, if kept: V7 FINAL T13 "13 / 0 / 0 / 0 / 0.3 / 5.8 / 7.7", labelled runner report, raw not re-read.

## Part 2: the 7 open decisions

| Decision | Options | Cost | Recommendation |
|---|---|---|---|
| 1 Step-2 fault | A stand-in drop; B kill after delivery | A: no v3 number, 5 rehearsal runs, minutes unknown; unrun on v3 so the film could show a surprise (second alert, mail count). B: backed by K3 n=20, but the hand kill is unlikely to land, the caption is wrong, and scene 8 may have no reply. | B, with a slowed stand-in step so the kill lands and the caption rewritten to say n8n was stopped after delivery. Only B has a number. Check scene 8 first; if no reply exists, drop scene 8 or go to A with no number. |
| 2 Table screen | Run it; or fallback screenshot or editor preview | Run: owner import plus first-open rehearsal, effort unknown, risk of a live failure and a name or address column leaking. Fallback: a few minutes of owner effort, zero risk to the claim. | Fallback screenshot of the safe columns. Try the screen once in rehearsal and keep it only if it works first time. |
| 3 Lease | 20 s; 45 s; shipped 120 s | 20 s: free, matches V7. 45 s: unmeasured; K1 plus K2 n=20 each is roughly 15 to 20 runner minutes per series by my extrapolation (V7 took 90 calendar minutes for 11 tests), unknown really. 120 s: lane3 has one 144.3 s K1 figure; no demo-harness table. | Film at 20 s, label it "test lease 20 s", and put the shipped 120 s figure (lane3 K1 144.3 s, about lease + 25 s) on the closing card separately. Do not film at 45 s: it has no number at all. |
| 4 Scene 11 | Keep; cut | Keep: 25 s of screen, n=1, title overstates ("dead"). Cut: saves 25 s, loses the only slow-alert evidence. | Cut. One run, one retry pattern, and it invites "alerts always arrive" misreading. Move to the closing card as one line only if wanted. |
| 5 Scene 3 number | Quote T13; K rows only | Re-reading the T13 raw file on the laptop: owner minutes, unknown but small. K rows only: the scene then has no matching evidence. | Re-read T13 raw, then quote it as "3 at once, plus a database kill". If not re-read, show no number in scene 3. |
| 6 v4 or v3 in the take | Film v4; stay on v3 | v4: not in the V7 file, so every caption number is void until K1, K2, K3, K3B are rerun; a full 80-kill rerun is likely over an hour of runner time (my guess, not measured) and the laptop V4-par has only 1 run. v3: the two-alert flaw must be named. | Stay on v3 and name the flaw on the closing card (v3 B90: 2 alerts in 3 of 3 when the alert send is slow). Switch only if V4-par delivers a full table before the take. |
| 7 Retention line | Yes; no | Cost near zero. Omitting risks a privacy overclaim (request body stays in n8n data, age not measured). | Yes, one line, no time. |

## Top 5 problems

1. Scene 7 caption is wrong for option B, and the sheet recommends B for the number. The harness K3 is a kill after delivery; the caption describes a dropped mail-server answer. The lane3 K3 (killed after CRM write) is a third meaning; never cite it for this scene.
2. Scene 8 may be impossible under option B: killing n8n mid-request leaves the caller without a reply (my inference, unverified), and the reply text was never checked on v3.
3. Stale text: the sheet says recovery at lease 120 s is unmeasured and the per-lead alert count is unverified. Lane3 gave 144.3 s at 120 s, and the lead correction backs K3 = 1 and K3B = 1 alerts each.
4. The film lease problem: all recovery numbers (59.6 s, 59.4 s, 88 to 110 s, 272.1 s) are lease 20 s; "within 60 s" is true only there; the shipped lease is 120 s and the 45 s candidate has no measurement.
5. Scene 3 and scene 10 rest on a number or a screen nobody has verified: T13 raw not re-read, and the table screen never run; the closing card also reads as 80 clean completions when 40 ended UNKNOWN by design.

# QUEUE for system-map (lead, 2026-11-16). Ordered backlog that runs WITHOUT waiting for the lead.
Times: UTC first, IST (= UTC + 5:30) second, for example 12:00 UTC / 17:30 IST. A bare "Z" in an older line means UTC.

## Words used on this page (one line each)
1. lead = the Claude session on the owner's laptop that gives the orders. owner = the one person who runs the studio. system-map = this session (the one that reads this file).
2. take = the single recorded real run of the lead-handling workflow, on made-up data, that becomes the video. The program that runs it is `scripts/run_real_check_n8n.py` in the take repo (not in your checkout).
3. real-v5 = the set of n8n workflows (n8n is the automation tool) used for the take, patched copy (lead answer of 16 Nov 10:20 UTC / 15:50 IST). film-v5 = a second set for scenes 5 to 11 of the run sheet; it is out of this video (lead decision 1).
4. N-lite = the short one-video plan (scenes 1 to 4 only). Its one claim: "the same lead id sent twice is processed once".
5. board = each session's status file; board beat = the 5-minute update of that file (see ORDERS.md, orders 015 and 021).
6. STATE FINAL = the last line you write on the board when every item below is DONE or BLOCKED with the exact missing input.
7. ring = a round of fresh independent readers over a finished file (item M10); log in rings/RING-LOG.md.
8. ORDER 021 etc. = a numbered order from the lead, in ORDERS.md (same folder). "Decision N" = the numbered lead decision in inputs/DECISIONS-2026-11-16.md.
9. drift = two files saying different things about the same fact; drift/REPORT.md lists each one, row 101 of its table is the open list of 8 Blocker rows for the lead.
10. HubSpot = the contact system the take writes to. M-numbers (M1 to M20) are the items below.

## Percent legend (digest 382)
A percentage on a row = the share of that row's acceptance checks that have a command and output on file. It is not confidence.

## Rules of the queue
Owner HARD rule 2026-11-16: complete the video work by Wed 18 Nov (the lead names the time in UTC and IST), and no session sits idle.
1. Always keep at least 6 agents running, up to 8 (orders 021, 022, 027, 028; the container has 4 cores, about 15 GB, 3 heavy test slots; light reading and review agents are not limited by cores). Start the next item the moment a lane frees; never wait for the lead between items.
2. Take items in order; independent items run in parallel. For each item: two independent EGM reviewers on the result, and an evidence runner for anything that runs.
3. Report each finished item in REPORT.md and on the board (item state table). Only questions that only the lead or owner can answer go to QUESTIONS.md; continue with the next item meanwhile.
4. Write STATE FINAL only when EVERY item is DONE or BLOCKED with the exact missing input. The lead refills this file every tick: re-read it on every board beat (git pull) and add new items to your own list.
5. If the queue is empty and nothing waits on the lead: take the next unreviewed area from your own "not checked" list (architecture audit rule R460) and say so on the board.
6. Inputs copied for you (read-only, made-up data): handover/system-map/inputs/.
7. MUST-NOT: no real keys, mailboxes or client data; no pushes outside cloud/system-map; no edits outside handover/system-map/; no secrets; do not touch other sessions' folders (read via git show).

## Decisions in force (who decided: the lead, 16 Nov 2026; the owner may veto any line)
1. Decision 1: one video, real-v5 only (scenes 1 to 4); no flow-set switch.
2. Decision 2 (corrected by the lead's batch 3 answer, 16 Nov 16:50 UTC / 22:20 IST; replaces the 16:41 UTC wording): the take's HubSpot key stays read-only. "The take's HubSpot key cannot archive or delete. After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list." Because the key is read-only, the expected case is that all three contacts are on the printed list. UNVERIFIED until the lead's loopback re-smoke (whether the refusal prints cleanly; whether HubSpot's filtered list shows archived contacts). The older wording "never deletes" is withdrawn.
3. Decision 4: core patch A-01 deferred, C-01 extras cut.
4. Decision 5: security items S9-5, S9-12 and S9-3 applied as text; S9-2 kept with an honest sentence.
5. Decision 7: the owner's n8n first-visit setup is already done; the lead imports and activates the flows; the owner only types y, the challenge and end.
6. Decision 11: licence copies under handover/promotion-inputs are never overwritten or re-licensed.
7. Storage (decision 10 and DECISION-one-store.md): one Postgres server with two databases (n8n's own and the take's), holding n8n state and claim rows; the file stage.journal is the one stated exception.
8. Executions are saved ON (made-up data only) and deleted at clean-up; the video makes no portal, approval or audit-trail claims.
9. Narrow claim: "the same lead id sent twice is processed once".
10. n8n outgoing network access is switched off by environment names and observed (not enforced).
11. The loopback re-smoke (a free local test run, US$0, before any real take) comes first; the lead runs it, Tue 17 or Wed 18 Nov. Facts it proves are UNVERIFIED until then.
12. Take branches are local only, never in your branch.
13. Builders r37, r38, r39 (laptop lead agents, not a named person) finish about 17:15, 18:10 and 18:40 UTC (22:45, 23:40 and 00:10 IST); then reviews and the merge chain; re-pin target Tue 17 Nov 08:00 UTC / 13:30 IST. Dollar limit: the API credits (US$189 prepaid, with an in-code backstop below it), window to Mon 23 Nov 18:29 UTC / 23:59 IST. Estimate: about 2 days of agent time to the take. Video: recorded earlier on Wed 18 Nov, posted Wed 18 Nov 15:00 UTC / 20:30 IST. Crash test (DM): required.

## Items
Fixed order on each row: STATE | date | owner | due | percent | open items. Detail is on the line below. Owner means the person or session that must act; "system-map" is this session.

M1 [DONE (read-only check) | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: the changed flows have NOT been run in n8n]
  Third read of the flows-audit top 10 findings against the real flow JSON; flow-graph check of the patched flows.
M2 [REVIEWED, fixes applied | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: none stated]
  FINAL-CROSSCHECK.md of all three audits with the combined cut list for the owner.
M3 [REVIEWED, fixes PARTLY applied | 2026-11-16 | system-map | no due | 92% | open: 8 Blocker rows for the lead in drift/REPORT.md row 101]
  Drift check of the take documents (critical path): inputs/ OWNER-STEPS, AGENT-SCOPE, DECISION-one-store, plan v5. Every number, file name, port, step id and claim that appears in two documents must agree; list each disagreement with both quotes and line numbers; one place per job. Output drift/REPORT.md with an exact fix list. Two EGM reviewers. Tag reconciled to the board 16 Nov 10:40 UTC / 16:10 IST.
M4 [REVIEWED round 1, fixes applied; round 2 started, result not seen | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] (earlier figure: 90%) | open: round 2 result]
  MASTER-MAP refresh: add this session's new files (board duty files, queues, fill_flows when it lands, paste-check, steps-edits) to MASTER-MAP.md and ONE-PLACE-TABLE.md; mark duplicates. Tag reconciled 16 Nov 10:40 UTC / 16:10 IST.
M5 [round 3 fixes applied; round 2 naive-reader running | 2026-11-16 | system-map | due Tue 17 Nov 12:00 UTC / 17:30 IST | percent [LEAD FILLS at refill from the live state] | open: naive-reader result; the clean-up sentence in M17 (expected case: all three contacts are printed for you to archive or delete by hand) is UNVERIFIED until the loopback re-smoke]
  OWNER VIEW: one page, plain words: what is done, what runs, what is still the owner's (the written yes, typing y, the challenge and end, archiving or deleting by hand the made-up contacts on the list the program prints after the take (expected: all three, because the take's HubSpot key is read-only; UNVERIFIED until the re-smoke), revoking the model key at clean-up). Accounts and n8n setup are already done (decisions 2 and 7). Built from the board and REPORT files of all three sessions (read others via git show).
M6 [R460 review DONE (work/review-r460-tools.md); B1, B2 and B4 fixed | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] (earlier figure: 90%) | open: B3 (a tool's check results are matched to table rows by row number, so a moved row would get another row's result)]
  Idle fallback: architecture audit rule R460 on the next unreviewed area of your own audit. Tag reconciled 16 Nov 10:40 UTC / 16:10 IST.
M7 [APPLIED | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: none]
  Read inputs/FACTS-ALREADY-DONE.md. M3 flags every document that still lists a done item as an open owner step (OWNER-STEPS v3, handoff, orders); M5 lists only still-owner-only items.
M8 [DRAFT written (ARCHIVE-CUT-LIST.md); fact review running | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: fact review result]
  Structure and size audit of the whole studio repo from your checkout (largest folders, duplicated documents, stale handoff-like files, files over 1 MB tracked in git) with an archive cut list (archive, never delete).
M9 [PARTLY DONE via M7 section 6 | 2026-11-16 | system-map | no due | 90% (same as M7 minus 5) | open: remaining documents that still show a done item as open]
  Re-check every finding of FACTS-DIGEST (reading origin/main through git show is not available: use inputs/ files); flag which of your own documents still contain an owner-open item that is already done.

### REFILL at 09:42 UTC / 15:12 IST (lead): start these now, in parallel (then 1 agent and 3 free cores; now 8 agents; target 70 to 85 percent)
M10 [PARTLY DONE, fresh round running | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: fresh ring round; log in rings/RING-LOG.md]
  SECOND-READER RING: for each finished deliverable (owner view, drift report, master map, ONE-PLACE-TABLE, cut list) start a fresh naive reader (egm-comprehension) AND a facts-and-cites checker (egm-codebase-details) in parallel; log in rings/.
M11 [DONE | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: none; results in drift/REPORT.md section 11]
  FACTS-ALREADY-DONE SWEEP: grep every document in the repo and in the other two sessions' pushed files (git show origin/cloud/<name>:...) for owner-step lists that ask the owner for accounts, keys, mailboxes, Docker, HubSpot accounts; list each place with line number and exact fix.
M12 [DONE | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: none; drift/REPORT.md section 11]
  VIDEO-DATE SWEEP: every place that states a take date, post date or first slot (the queue says Wed 18 Nov morning IST; no owner-steps file gives a take date; deadline Wed 25 Nov 20:30 IST): list place, quote, fix.
M13 [DONE | 2026-11-16 | system-map | no due | percent [LEAD FILLS at refill from the live state] | open: none; drift/REPORT.md section 12]
  THREE-WAY CONSISTENCY: ports, folder names, file names, step ids in OWNER-STEPS v4, plan v5 and the run sheet: table of disagreements.
M14 [RUNNING | 2026-11-16 | core-hardening owns the fix | no due | percent not stated | open: 1 real failure (the licence-files test)]
  HEAVY LANE: re-run the core test suite in a FRESH git clone of the cloud/core-hardening head (not a scratch copy) with 3 slots; record the two baseline failures exactly (vendor-word test, licence-files test) and whether they exist in a clean clone. Earlier clone 14d8fe46d; re-run on head 60338533: 1 failed (licence files), 9390 passed. "Licence files" = the copies of other holders' Apache-2.0 licence text under handover/promotion-inputs; the test checks them, and the fix must not edit them (decision 11).
M15 [PARTLY DONE | 2026-11-16 | system-map | no due | 80% (board) | open: the one list to sign is not built]
  Cut list (archive, never delete) for repo files not used by the take: next area under R460. A reconciliation note is in ARCHIVE-CUT-LIST.md.
Keep at least 6 agents running, up to 8; when one finishes, start the next in the same turn.

### REFILL at 09:45 UTC / 15:15 IST (lead)
M16 [CLOSED by lead decision 1 | 2026-11-16 | lead | no due | percent not stated | open: archive the flowset report, never delete]
  FLOW-SET QUESTION (history): the take scripts contain no code that switches the n8n flow set from real-v5 (scenes 1 to 4) to film-v5 (scenes 5 to 11). Decision 1: the one video is real-v5 only, so there is no flow-set switch. Output was to be flowset/REPORT.md.

### REFILL 3 at 17:30 UTC / 23:00 IST (lead, batch 3 answer 7) items
M17 [NOT STARTED | 2026-11-16 | lead (applies the text to v5, the run-day card, the program notice, TAKE-BLOCKERS; program notice and prompt text are edited by the fix builders, the lead approves) | due Tue 17 Nov 12:00 UTC / 17:30 IST | 70% | open: whole item]
  Replacement text file for item 1 (what end does to contacts): "The take's HubSpot key cannot archive or delete. After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list." Expected case: the key is read-only, so all three contacts are on the printed list. UNVERIFIED until the lead's loopback re-smoke (whether the refusal prints cleanly; whether HubSpot's filtered list shows archived contacts). The earlier wordings "never deletes" and "the program archives them" are withdrawn. The key gets no archive right (decision 2). Targets: v5, run-day card, program notice, TAKE-BLOCKERS; old/new lines.
M18 [CLOSED, settled by decisions 4 and 5 | 2026-11-16 | lead | was due Tue 17 Nov 12:00 UTC / 17:30 IST | 90% | open: archive the draft decisions/D04-D05.md, never delete]
  decisions/D04-D05.md (one page): was written, awaiting the lead.
M19 [round 2 cold reads done | 2026-11-16 | system-map | due Tue 17 Nov 12:00 UTC / 17:30 IST | 60% | open: further rounds]
  Independent reader pass over the final owner-steps page (stranger test, 10 minutes of steps, no jargon).
M20 [BLOCKED | 2026-11-16 | lead | due Tue 17 Nov 12:00 UTC / 17:30 IST | percent [LEAD FILLS at refill from the live state] | open: SESSION-HANDOFF must be pasted into inputs/ by that time, or M20 is dropped from the take]
  Re-verify every number and date in SESSION-HANDOFF live state against files (claims check); list mismatches.

M16 is CLOSED by decision 1: the flowset report is moved to the archive folder, not deleted (a repo file, not a HubSpot contact).

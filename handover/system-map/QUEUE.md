# QUEUE for system-map (lead, 2026-11-16). Ordered backlog that runs WITHOUT waiting for the lead.
RULES OF THE QUEUE (owner HARD rule 2026-11-16: complete the video work by Wed 18 Nov morning; no idle session):
1. Always keep at least 6 agents running, up to 8 (ORDER 021, 022, 027, 028; the container has 4 cores, about 15 GB, 3 heavy test slots; light reading and review agents are not core-limited). Start the next queue item the moment a lane frees; never wait for the lead between items.
2. Take items in order; independent items run in parallel (several at once). EGM sequence per item: your own egm reviewers (two independent) on the result; evidence runner for anything that runs.
3. Report each finished item in REPORT.md and the board (item state table); only the questions that only the lead or owner can answer go to QUESTIONS.md, and you continue with the next item meanwhile.
4. Write STATE FINAL only when EVERY item below is done or marked BLOCKED with the exact missing input; the lead refills this file every tick, so re-read it on every board beat (git pull) and append new items to your own list when it grows.
5. If the queue is empty and nothing waits on the lead: take the next unreviewed area from your own 'not checked' list (architecture audit rule R460) and say so in the board.
6. Inputs copied for you (read-only, made-up data): handover/system-map/inputs/. Decisions in force: one Postgres server with two databases (n8n's own and the take's) (n8n state + claim rows), stage.journal file the one stated exception; executions saved ON on made-up data and deleted at clean-up; no portal, approval or audit-trail claims in the video; narrow claim 'the same lead id sent twice is processed once'; n8n egress switched off by env names and observed (not enforced); loopback re-smoke US$0 before any real take; take branches are local only (never in your branch).
7. MUST-NOT: no real keys, mailboxes or client data; no pushes outside cloud/system-map; no edits outside handover/system-map/; no secrets; do not touch other sessions' folders (read via git show).
ITEMS (mark each DONE / RUNNING / BLOCKED with date in this file; the lead reads it):
M1 [DONE 2026-11-16] Third read of flows-audit top 10 findings against the real flow JSON; flow-graph check of the patched flows.
M2 [REVIEWED 2026-11-16, fixes applied] FINAL-CROSSCHECK.md of all three audits with the combined cut list for the owner.
M3 [REVIEWED; fixes PARTLY applied; 8 Blockers open for the lead (drift/REPORT.md row 101); 92%; tag reconciled 16 Nov 10:40Z to the board] DRIFT CHECK of the take documents (critical path): inputs/ OWNER-STEPS, AGENT-SCOPE, DECISION-one-store, plan v5: every number, file name, port, step id and claim that appears in two documents must agree (list each disagreement with both quotes and line numbers; one place per job). Output handover/system-map/drift/REPORT.md with an exact fix list. Two egm reviewers.
M4 [REVIEWED round 1, fixes applied; round 2 started, result not seen; 90%; tag reconciled 16 Nov 10:40Z to the board] MASTER-MAP refresh: add the new artefacts from this session (board duty files, queues, fill_flows when it lands, paste-check, steps-edits) to MASTER-MAP.md and ONE-PLACE-TABLE.md; mark duplicates.
M5 [round 3 fixes applied; round 2 naive-reader running] OWNER VIEW: one-page plain-words status for the owner (what is done, what runs, what he must do by when for a take on Wed 18 Nov: accounts, Docker running, the written yes), built from the board and REPORT files of all three sessions (read others via git show).
M6 [R460 review DONE (work/review-r460-tools.md); B1, B2 and B4 fixed, B3 row-number keying OPEN; 90%; tag reconciled 16 Nov 10:40Z to the board] Idle fallback: architecture audit rule R460 on the next unreviewed area of your own audit.

M7 [APPLIED 2026-11-16] Read inputs/FACTS-ALREADY-DONE.md: M3 drift check must flag every document that still lists a done item as an open owner step (OWNER-STEPS v3, handoff, orders); M5 OWNER VIEW lists only the still-owner-only items.

M8 [DRAFT cut list written (ARCHIVE-CUT-LIST.md); fact review running 2026-11-16] Lane: structure and size audit of the whole studio repo from your checkout (largest folders, duplicated documents, stale handoff-like files, files over 1 MB tracked in git) with an archive cut list (archive, never delete).
M9 [DONE via M7 section 6, 2026-11-16] Re-check every finding of FACTS-DIGEST (read via git show origin/main is not available: use inputs/ files): flag which of your own documents still contain an owner-open item that is already done.

## REFILL 09:42Z (lead): start these NOW, in parallel, you have 1 agent and 3 free cores (target 70-85 percent)
M10 [PARTLY DONE 2026-11-16, ring log in rings/RING-LOG.md; fresh round running] SECOND-READER RING: for each deliverable already written (owner view, drift report, master map, ONE-PLACE-TABLE, cut list) start a FRESH naive reader (egm-comprehension) AND a facts-and-cites checker (egm-codebase-details) in parallel; log results in handover/system-map/rings/.
M11 [DONE 2026-11-16, results in drift/REPORT.md section 11] FACTS-ALREADY-DONE SWEEP: grep every document in the repo and in the other two sessions' pushed files (git show origin/cloud/<name>:...) for owner-step lists that ask the owner for accounts, keys, mailboxes, Docker, HubSpot accounts; list each place with line number and exact fix (one place per job).
M12 [DONE 2026-11-16, drift/REPORT.md section 11] VIDEO-DATE SWEEP: every place that states a take date, post date or first slot (queue says Wed 18 morning IST, no owner-steps file gives a take date, deadline Wed 25 Nov 20:30 IST): list place, quote, fix.
M13 [DONE 2026-11-16, drift/REPORT.md section 12] THREE-WAY CONSISTENCY: ports, folder names, file names, step ids that appear in OWNER-STEPS v4, plan v5 and the run sheet: table of disagreements.
M14 [DONE 2026-11-16 earlier clone 14d8fe46d; re-run on new head 60338533: 1 failed (licence files), 9390 passed] HEAVY LANE: re-run the core test suite in a FRESH git clone of cloud/core-hardening head (not a scratch copy) with 3 slots, record the two baseline failures exactly (vendor-word, licence) and whether they exist in a clean clone.
M15 [DONE: reconciliation note in ARCHIVE-CUT-LIST.md] Cut list (archive, never delete) for repo files not used by the take: next area under R460.
Keep at least 6 agents running, up to 8; when one finishes start the next in the same turn.

## REFILL 09:45Z (lead)
M16 [CLOSED by lead decision 1 of 16 Nov 2026: the one video is real-v5 only (scenes 1-4); film-v5 (scenes 5-11) is out, so there is no flow-set switch; the text below is history] FLOW-SET QUESTION (was critical path, take day): local check says the take scripts contain NO code that switches the n8n flow set from real-v5 (scenes 1-4) to film-v5 (scenes 5-11); `scripts/n8n_api.py` can import/activate/deactivate but nothing calls it; the lead imports real-v5 by hand (WP6-RUNBOOK line 16). Decide from the run sheet, owner steps and the 'simple video' decisions which scenes the ONE N-lite video really contains and whether film-v5 scenes are in it at all. Output handover/system-map/flowset/REPORT.md: scene list, flow set each needs, exact manual switch steps (n8n_api.py commands, who runs them, how long) or 'film-v5 not in this video'. Two reviewers.

## REFILL (lead): items
M17. Replacement text file for item 1 (end never deletes): v5, run-day card, program notice, TAKE-BLOCKERS; old/new lines.
M18. decisions/D04-D05.md (one page).
M19. Independent reader pass over the final owner-steps page (stranger test, 10 minutes of steps, no jargon).
M20. Re-verify every number and date in SESSION-HANDOFF live state against files (claims check), list mismatches.

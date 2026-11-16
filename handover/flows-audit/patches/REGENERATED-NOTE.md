# F-003 and F-004 regenerated (F-001 dropped, see the last bullet of round 3) a third time (2026-11-16, round 3 after review r2)

This note is for the lead and the owner. The internal codes and the decision cites that the reviews wanted out of the reader text live here, not in the run sheet.

Decisions used: inputs/DECISIONS-2026-11-16.md item 1 (one video, real-v5, scenes 1 to 4, no recovery number) and the lead's answer to Q15 (ANSWER-Q15-lead.md, 10:31Z: closing card is ONE line, "a lead sent twice is processed once", no recovery number). Static work: nothing ran in n8n, a CRM or a mail server. Review words are unverified until checked (patches/review-r2-patches.md). Backup of the round-2 patches: scratchpad patches-r3/ (copy); older ones in archive-pre-decision1/.

Check (copy of the repo files, not the real tree): lanes7/evidence-patches-r4.txt. check_patches.sh PASS, rc 0 (at that time 5 patches; now 4 after F-001 was archived); all 5 patches together apply, rc 0. This proves only that the patches apply; it does not judge wording. No new review runs after this round (as ordered); the lead runs the drift report.

## What changed in round 3
F-003 (VIDEO-RUNSHEET.md)
- Card (lead decision needed, item 1 below): the line now reads "A lead sent twice is processed once in this recording." The bound stays on one line, so it went into the card cell as ordered; the Must-NOT cell keeps the same bound. The lead may keep or drop "in this recording".
- Scene 4: voice says "at least 45 seconds, a setting we chose"; the mail window is named (a stop after the CRM write, around the mail send, can end unknown with one alert mail instead of done; caption only if the row reaches done). Must-NOT says the lead does not always end done. Rehearsal item 4 records the final state, the alert and the real wait of each try. Scene 3 and rehearsal item 2 note that a repeat sent while the first is still processing replies "processing".
- Producer note: the 30 s sentence is labelled "read from the flow files, not run"; the n8n restart time is added (not measured).
- Scene 2: one short sentence defines "lead"; a voice line introduces lead, lead table row, CRM and receiving mailbox. Scene 1 explains the lead table and the execution list in plain words.
- On-screen caption no longer says "Scenes 1 to 4". Closing card is no longer numbered 12. "lead decision ... item" cites, internal codes (T13, T14, K1 to K5, V7 history, WP5/WP6, plan-4, LOOPBACK) are gone from the scene cells, risks, rehearsal and open decisions. The older numbers are in one owner-only producer note.
- Execution list: "planned, HELD" in risk 3, rehearsal 7 and open decision 1.
- Scene 5-11 residue outside the moved block: the 17:08Z update, the 17:40Z note, the scene 5 caption and the table screen note are moved under "Residue notes moved here (NOT FOR THIS VIDEO)"; the owner crop list stays (item 5 marked later video). Risk 10, open decision 2 and the K3 tag bullet are labelled NOT FOR THIS VIDEO.
- Stale changelog lines are rewritten (no "moved to the closing card", no superseded notes). "example.com" is marked UNVERIFIED (read only from the older owner steps; the newer ones were not read).
F-004 (PAGE-STATEMENTS-V4.md)
- Statement 17 public sentence: no "the one video", no cross-reference, "run" is defined, the 30 s check interval (read, not run) and the n8n restart are named. Tag: "one source for the 20 s figures"; the 144.3 s figure is marked relayed, not measured by us (also in statement 14, honest limits and changelog bullets 1 and 3). The "lead decision item 1" cite in the struck statement 20 is reworded.
F-001: DROPPED by the lead (Q17-3, 2026-11-16, ORDERS.md 10:58Z): the take uses demo/n8n-flows-v4/mf_leads.sql as is (Q16). The patch file is moved to patches/archive/F-001-one-ddl.patch (not deleted, not applied). check_patches.sh now reports PASS 4 patches (lanes7/evidence-q14-q17.txt).

## Still needs the lead or the owner
1. Card wording: "A lead sent twice is processed once in this recording." The bound was added because it stays on one line. It is a general promise next to the state word "processing"; the lead may reword (for example "handled once").
2. Rows 5 to 11 are moved, not deleted; the lead may delete them or move them to a separate file.
3. PAGE-STATEMENTS-V4.md other lines are untouched: statement 12 still says "Detail ... 59.6 s"; statement 19 and the honest limits still name 13 minutes. True for their own text, not in the video.
4. build_mainframe.py lines 13-14 still carry example.test (not for the take).
5. Not checked: the real HubSpot answer, raw V7 and lane3 files, the take script, whether the take addresses are example.com (the v4 owner steps were not read: UNVERIFIED).
6. Wording rows still held in RUNSHEET-WORDING.md were not pasted.
7. The 30 s check interval and the claim that a mail-window stop ends unknown come from reading the flow files (review r2 facts); nothing was run.
8. The execution list stays HELD until the save-runs patch (F-008) is applied and the flows are rebuilt.

## F-008 changed (2026-11-16, lead answer Q18)
- Manual runs ("Test workflow") are now saved too: `saveManualExecutions` is True in the shared settings of the two entry flows and the sub-workflow. Reason is in the patch comment line (a Python comment, so the format allowed it). The recovery flow keeps saving "none" and manual False (unchanged).
- The lead's reason (the take's evidence reads n8n's run list, "system-map checks it") is the lead's statement; I did not verify it.
- Checker: new option `--accept-no-save FILE`; the recovery flow is printed as "ACCEPTED: recovery flow not part of the take (decision 4)". `--patch-checks F008` now also requires manual True (False for recovery). Evidence: flow-check/fix-q18.md.

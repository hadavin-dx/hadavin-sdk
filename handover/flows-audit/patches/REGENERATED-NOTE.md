# F-001, F-003 and F-004 regenerated again (2026-11-16, round 2 after review r1)

Decisions used: inputs/DECISIONS-2026-11-16.md item 1 (one video, real-v5, scenes 1 to 4) and the lead's answer to Q15 (ANSWER-Q15-lead.md: the closing card is ONE line, "a lead sent twice is processed once", no recovery number). Static work: nothing ran in n8n, a CRM or a mail server. Review words are unverified until checked (patches/review-r1-patches.md). Backup of the round-1 patches: scratchpad patches-r2/ (copy), older ones in archive-pre-decision1/.

Check (copy of the repo files, not the real tree): lanes7/evidence-patches-r3.txt. Check script and all 5 patches applied together: rc 0. The check only proves the patches apply; it does not judge wording. No EGM review of this round was run (the lead runs it).

## What changed against round 1
F-003 (VIDEO-RUNSHEET.md)
- Title and a banner: READ ONLY SCENES 1-4 AND THE CLOSING CARD. Rows 5 to 11 are MOVED (not deleted, text unchanged) to a last section "LATER VIDEO (not for the take)". Old totals 355/380 s, the lines about scenes 5 to 11, the stand-in CRM scene and the 60.1 to 61.9 s caption no longer stand in the part to read.
- Closing card: one line (Q15). Time 10 s; total 160 s. The not-tested list, retention and invalid-e-mail points moved to a new "Producer notes" section (plain words, not read aloud).
- B1: retention wording is "we found no step in the flows that deletes a row" (read from flow files, not run), plus "n8n may keep a copy of each incoming request until its own clean-up removes it; we did not measure when". No "no expiry".
- B2: the 30 s sentence is now in producer notes (and the first check must also come after n8n is back up). Scene 4 voice says "The stopwatch shows the real wait". n8n, run and lease are explained; a caption bounded to "in this recording" (use only if the row reaches done).
- Scene 1: execution list marked HELD (as built the 4 real-v5 flows save no runs; the shot is empty unless the save-runs patch F-008 is applied and the flows rebuilt). Scene 3: voice and caption added in the edit only after the recording shows 1 CRM row and 1 e-mail message. Names: lead ID, receiving mailbox, start-marker row.
- example.test replaced by "made-up take addresses (example.com, as in the owner steps)" in lines 8, 31, 55, 68, 85 and in the risks.
- Reader-text codes removed (D1, D2, coordinator, RUNSHEET-WORDING.md, lead decision item cite). Risk 8: card names no lease. Risks 1, 5, 10 and rehearsal items 1, 3, 5, 6 marked NOT FOR THIS VIDEO. Open decisions 3 and 6 answered. New rehearsal item 11.
F-004 (PAGE-STATEMENTS-V4.md)
- Statement 17 now has no recovery figure at all: the 20 s numbers stay only in statement 12 (one source, MEASURED-ON-LAPTOP lead-read, consistent with statements 4 and 13); the 120 s figure is dropped; "Never write within 60 s" removed from the public text; the "another test session" wording is gone. Tag says HELD until runs at 45 s exist.
- Total line: 19 statements in force, 17 HELD, 20 struck. Statement 20 is struck (8 of its 18 runs ended unknown, so "finished about a minute after" is false; all its numbers, caption rule and the 60.8/61.9/60.9/61.2/52.9-54.9 lines removed). Changelog bullet 4 added.
F-001: line 7 no longer names film-v5 (it names n8n-flows-real-v5 and the older v3 and v4 flows).

## Still needs the lead (not fixed by these patches)
1. The card line "a lead sent twice is processed once" is the lead's wording (Q15). It is a general promise and uses "processed" next to the state word "processing"; the reviews (M6, A-016e) wanted "handled once" / "in this recording". I kept the lead's words and added a limit (show the card only if scene 3 showed 1 row and 1 mail). Lead may reword.
2. Rows 5 to 11 are moved, not deleted; the lead may delete them or move them to a separate file.
3. PAGE-STATEMENTS-V4.md other lines are untouched: statement 12 (20 s numbers) still says "Detail ... 59.6 s"; statements 19 and the honest-limits lines still name 13 minutes and "lease 120 s: one lane3 figure only". They are true for their own text but are not in the video.
4. build_mainframe.py lines 13-14 still carry example.test (film-path addresses; the real take uses the placeholder). Not touched (F-002/F-008 target; not for the take).
5. Not checked: the real HubSpot answer (P4a: all-digit id), raw V7 and lane3 files, the take script, and whether the take addresses are example.com (read only from OWNER-STEPS v3 line 107; v4 not read). Statement 12's clock start is not stated in V7.
6. Wording rows still held in RUNSHEET-WORDING.md (A-007 and others) were not pasted; scene 1 uses a HELD note instead of the spoken A-007 sentence.
7. No fresh review of this wording has run: the lead must run the EGM result review and the drift report.

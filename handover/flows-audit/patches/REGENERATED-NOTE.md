# F-003 and F-004 regenerated (F-001 dropped, see the last bullet of round 3) a third time (2026-11-16, round 3 after review r2)

This note is for the lead and the owner. The internal codes and the decision cites that the reviews wanted out of the reader text live here, not in the run sheet.

Decisions used: inputs/DECISIONS-2026-11-16.md item 1 (one video, real-v5, scenes 1 to 4, no recovery number) and the lead's answer to Q15 (ANSWER-Q15-lead.md, 10:31Z: closing card is ONE line, "a lead sent twice is processed once", no recovery number). Static work: nothing ran in n8n, a CRM or a mail server. Review words are unverified until checked (patches/review-r2-patches.md). Backup of the round-2 patches: scratchpad patches-r3/ (copy); older ones in archive-pre-decision1/.

Check (copy of the repo files, not the real tree): lanes7/evidence-patches-r4.txt. check_patches.sh PASS, rc 0 (at that time 5 patches; now 4 after F-001 was archived); all 5 patches together apply, rc 0. This proves only that the patches apply; it does not judge wording. No new review runs after this round (as ordered); the lead runs the drift report.

## What changed in round 3
F-003 (VIDEO-RUNSHEET.md)
- Card: SUPERSEDED by the lead answers Q25-2 and Q28-1. The card now carries the scoped sentence "In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox." The broad sentence "A lead sent twice is processed once in this recording." is not used. Text of this round-3 line is kept in git history.
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
1. Card wording: ANSWERED (lead, Q25-2 and Q28-1): the scoped sentence above goes on screen and on the card. Nothing is open here.
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

## F-002 changed (2026-11-16, fix round r2 after patch-review2-r1.md; static, nothing ran in n8n)
- Open item first: UNVERIFIED whether the repeat-key reply works. F-002 sets Claim to always=False (no extra empty item). The repeat request is answered only if the Postgres node emits one item (for example {success: true}) for an INSERT that hits ON CONFLICT and returns no row. The builder comment (build_mainframe.py:114) says it does, read from n8n source by an earlier session, not re-checked. The recovery flow already relies on the same behaviour. I could not judge the alternative (keep alwaysOutputData with the error output) from files: it would also depend on unverified n8n behaviour and risks a false "stored repeat" reply for a lead never stored (the reason the patch changed it, FINDINGS F-002 row). Shape left unchanged; the risk is written into the patch comment.
- ReplyStoreFail now reads $('Valid').first().json.lead_key (Valid emits one item per request; no paired-item lookup on an error item). Hunk regenerated by editing the patch in place; same line counts.
- The key comment and the 422 reply text now say "1 to 64 characters from A-Z, a-z, 0-9, - or _ (ASCII only)" instead of "letters".
- T19 line: if the repeat request gets no reply, F-002 fails and this node shape (always=False) is the cause. Fallback unchanged: alwaysOutputData on plus onError continueRegularOutput plus an IF on $json.error.
- T20 hostile inputs added (all must give 422 and no row): lead_key as a number (123), as an array (["a"]), as an object, as null, key missing, key empty, key with a space or a non-ASCII letter, key of 65 characters. Valid turns the value into text with String(), so an array ["a"] becomes "a" and PASSES the shape check: expected 200 path, not 422; record what the real node does (UNVERIFIED). A number 123 becomes "123" and also passes. These two are accepted shapes, not rejected; the test only checks that nothing crashes and that the stored key is the text form.
- Checks: check_patches.sh PASS 4 patches; F-002 then F-008 apply in sequence on a temp copy. Backup: scratchpad bak-patch2/.

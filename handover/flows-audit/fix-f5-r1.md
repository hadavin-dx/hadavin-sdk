# fix-f5-r1: F5 fixer round 1 (of max 2), change log for RUNSHEET-WORDING.md, 2026-11-16
Static reading only; nothing ran. Findings checked against the flow JSON and the sources first. No reviewer has seen the rework yet.
W-01 fixed: new "Goes where" column (SCREEN, VOICE, CARD, PAGE, LEAD) plus flow set and scene per row; "Paste this" split from "Note to lead".
W-02 fixed (blocker, confirmed): AlertClaim 720 s hold, AlertMark only after a good send, AlertBackoff, no cap, so the alert can repeat. Spoken text has no count; written text says "normally one; it can repeat". Rows A-021, A-057, A-076, A-077, B-077, N-4.
W-03 fixed (blocker, confirmed): scene 9 shows the mail in the stand-in list. New wording: n8n got no confirmation, so it cannot know whether the mail arrived. Rows A-021, A-033, A-035, A-077.
W-04 fixed: "took" replaced by "received" (A-030).
W-05 fixed: "went" replaced by "arrived"; the cut connection is described (A-033, A-035).
W-06 fixed: viewer line has no K1, lane3 or film-v4; D1 default is no number, alternative given; sources only in lead column (A-017, A-019, A-051, A-081).
W-07 fixed: lease explained before the label; row N-5 and the words list.
W-08 fixed: "mail" = e-mail message, "e-mail address" always says address; words list; A-010, A-053, B-010.
W-09 fixed: plain sentence on what n8n may keep and what the lead table keeps (A-010, A-053).
W-10 fixed: "six columns, none holds a name or e-mail address"; "capture one screenshot" (A-040, A-042).
W-11 fixed partly: spoken line added; the built alert text "A person decides." stays on screen because I may not edit the flow (FIX-PLAN item 7 has no patch). Needs lead decision D3.
W-12 fixed: review row sentence in N-3 and A-057, A-091 (only marked, no alert, someone must check the table).
W-13 fixed: scene 5 pane tag is "Stand-in CRM: a test copy of the customer list, not a real CRM" (lead answer kept, jargon glossed).
W-14 fixed: mail pane resolved by address evidence (example.test cannot be a real mailbox) with its own tag; C2 closed unless the lead overrules.
W-15 fixed, differs from claims table: the card no longer holds "say on screen" (note about the video); reason stated at the top of the file.
W-16 fixed: A-005 plain words, same string as the claims table.
W-17 fixed: A-016 result spoken only after it is read off the take.
W-18 fixed: one numbers rule; no pooled range; per-stop-point figures only (A-073, A-076, A-081, A-019).
W-19 fixed: T8, harness, lane3, K3=K3B moved to lead column; page text is plain (A-059, A-073, A-076, A-077).
W-20 fixed: "not lost in those 2 runs" (A-023, A-075, A-088).
W-21 fixed: page statements marked PAGE (public reader) vs LEAD; unknown-audience problem removed.
W-22 fixed: "capture one screenshot", "take" kept only for a filming run.
W-23 fixed: one name per column, with the on-screen name once in the words list.
W-24 fixed: double quotes outside, single quotes inside.
W-25 fixed: "claim window" explained in A-098; "claim" and "window" no longer used loosely.
Disputed: none. Unverified: all relayed numbers, P1, P2, P3, D1 to D3, what program is the stand-in mail server, T8/T15 meaning.
ORDER 019 addition: fixed. Row N-8 in RUNSHEET-WORDING.md section 1 gives the flow-set switch between scenes 4 and 5 (deactivate all four real-v5 flows including recovery, activate film-v5, clean leftover lead rows). UNCHECKED: whether the take scripts do this switch; the lead checks.

## Round 2 (of max 2), 2026-11-16 about 09:40 UTC (15:10 IST)
Static reading only; nothing ran. Findings checked first against: film-v5 mf-recovery.json (AlertSend text, AlertClaim 720 s, ClaimStuck), film-v5 sub-workflow (MF_STAGE_URL, MF_CRM_URL), and the copies of VIDEO-RUNSHEET.md and PAGE-STATEMENTS-V4.md under tools/scratch/rp/c/b. Not checked: the rest of the files the facts review listed as unchecked. Round 2 fixes are not reviewed.
- Reader B1 fixed: new section 0 numbered list with the N-8 flow-set switch as step 8.
- Reader B2 fixed: every "Paste this" cell is one clean string; labels, conditions, DEFAULT/IF D1 variants and instructions moved to the last column or into lettered rows (A-016a-d, A-017a/b, A-033a/b, A-036a/b, A-051a/b, A-019a/b, N-4a-c, N-5a/b). NO PASTE and DELETE are defined.
- Reader B3 fixed: A-036 reworded per facts M1 (A-036b); A-050 now run counts "relayed, not re-measured here" (A-050a); A-017b gives numbers and "relayed"; `<key>` placeholder removed (A-036a is NO PASTE, the note describes the built text).
- Reader B4 fixed: section 3 and 4 have a Type column (PAGE TEXT, LEAD NOTE, VIEWER TEXT); section 4 states it has no viewer sentence.
- Reader M5 fixed: glossary "Words and ids" before first use (D1-D3, P1-P3, W/F/Q/A/B/N/X/V/P/S5 ids, HB189, V7, AF1/AF2, K1-K3B, RELAYED, UNTRACED, flow set, real-v5, film-v5, take, stand-in, claim, door, lane3, T-tests, mf.py, OwnsClaim1); two meanings of "owner" separated.
- Reader M6 fixed: A-033 names "stand-in mail server"; A-021 "We stopped n8n on purpose"; "mail sent" label note (A-044a); "review" explained as a word in the state column; "normally one" removed from all viewer and page text; A-076 split into three short sentences.
- Reader M7 fixed: A-016b is a post-edit insert with a stated stop rule. M8: scene 5 lower third shortened (A-026a, section 2). M9: RELAYED and UNTRACED defined. M10: duplicate ids removed (A-075, A-077, A-040/041, B-085, A-042/097/N-2 split; P rows moved to section 3).
- Facts M1 fixed (A-036b, A-050b, N-1). M2 fixed (S5-voice has no "only"; checked MF_STAGE_URL). M3 fixed (N-8 check lists processing, unknown, failed with alert sent false; verified in ClaimStuck and AlertClaim queries).
- Facts M4 fixed: rows added for VIDEO-RUNSHEET.md:41 line 4 (V-41), :11 (V-11), :57 (V-57), P:153 (A-077b) and P:155 (P-155); A-073 now gives stop point and run counts; 144.3 s is one run (the "144.2 to 144.4" range has no run count, dropped); A-008 promise "marked in each scene" removed because scenes 8, 10 and 11 carry no tag.
- Facts nits: "self-check" rule 2 now says where the words appear; "lead ID" and "lead key" defined as one meaning; "this recording" used for the video being made, "take" only for a filming run; dates carry UTC and IST; A-004 wording no longer says "fake model".
- Unverified: all relayed numbers, D1-D3, P1-P3, which program the stand-in mail server is, whether the take scripts do the N-8 switch, real-v5 files (not re-read), the K1 stop point of the 59.6 s figure (A-073a), the meaning of T8/T15.
- Coverage: section 7 recount by script: 117 rows, claims rows 1 to 69 all present by number; this does not prove the wording is right.

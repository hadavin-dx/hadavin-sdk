# Claims table r5, stranger read of lines 1-260 (egm-comprehension af6b5d33; saved by flows-audit, condensed, all findings kept)
Not checked: no cited source opened; lines 261-end not read; claims-count.py not run; whether LIVE/OUT tags are right for the video.
BLOCKERS
B1 (lines 5-16, 144) never says what scenes 1-4 contain; stranger cannot see why rows 6,8,9,16,22,32 are LIVE and 10-15 not. Fix: 4 lines in scope box (scene, on screen, real services).
B2 (54, 66-70, 33, row 33 needs-cell) gating rule says edit only after decision/check in "needs"; row 33 (LIVE, before take) needs P4c, which runs after the take (70, 104); row 33 note says safe text is the default now; row 48 same; rows 1 and 4 needs cell says Q6 but note says wait for P4a and two owner steps.
B3 (line 10 vs 11, rows 33/48/16) line 10 says Table 2 incl. row 48 is out; line 11 lists P4c (rows 33 and 48) as live; line 11 "P2 (rows 6 and 16)" but row 16 no longer depends on P2.
MAJOR
M1 line 12 lists rows 2,5,32 as "live, text only" but tags are plain [LIVE]; "TEXT ONLY" never defined; row 16 TEXT ONLY carries a P2 note.
M2 tag position: lines 10 and 144 say start of note cell; rows 1,3,4,21,33,36 have it at end or middle. Give the tag its own column.
M3 Table 1 heading and line 85 say "42 to change before the take" but 24 of 42 are OUT, 18 live (rows 1-9, 16, 17, 21, 22, 32, 33, 36, 39, 79); live count never stated.
M4 line 28 "replacement text exists for 90 of 327" counts DELETE and "keep; do not add" rows; line 33 "except the few" vs line 85 14 added-on-purpose rows.
M5 line 122: lane A 7 UNTRACED + lane B 63 = 70, totals say 69.
M6 "Decision" three meanings (Decision 1,2,5,9 numbered items; D1-D3; "lead decision item 2"); D1 vs decision 1 conflict; rows 9 and 22 "needs D1" but replacement DELETE; "S9-3" undefined.
M7 "lead" alone still used (lines 5, 6, 12, 36, 104, row 8) against line 18 "never".
M8 "check", "claim", "window", "done", "table" carry several meanings.
M9 "v4" and "v3" mean both documents and flow sets.
M10 row 2 replace cell contains instructions (belong in note column).
M11 row 6 replacement promises "we delete the saved runs afterwards", not in the owner's actions; row 16 says data stays in n8n's database.
M12 row 33 / line 36 replacement states as fact what the file says is unproven (script archive step); label "intended, not checked" like row 39.
M13 line 14 "not in this file" vs checks defined at 99-104; two orders of work (line 11 vs 68); P1 in order of work but P1 rows OUT; line 101 "8 flow files" vs line 24 "4 real-v5 files".
M14 row 21 tagged LIVE, TEXT ONLY but describes the table picture (row 13/line 7 OUT, decision 9); row 5 predicts cropped footage.
M15 row 3 and row 17 (LIVE) lean on OUT rows / recovery numbers; row 17 "were tested" says more than "numbers were relayed"; "no recovery number on screen" vs D1 "scene 4 shows the stopwatch".
M16 scope items 3-4 undefined words (take identity, settings-file figures, model key, "both typed answers"= y and 6-digit challenge, contacts = HubSpot); P4a, P2, A-012, mf-recovery, stand-in, film-v5 used before defined.
NIT N1 empty "Start here" heading; N2 line 22 "T2 nowhere" meaningless; N3 line 21 broken clause, 17:05Z no IST; N4 line 19 "second n8n flow" vs four flows, alert case never reaches done; N5 F-008/F-001/F-01 confusable, T1 two meanings; N6 round history in lines 85, 144; N7 bare file names, paths only in index; N8 which round reviewed which rows unreadable; N9 two kinds of OUT tag, only one explained.
Stranger can: find the file (yes), the line (yes, lines may move), which rows apply (mostly), before which step (only "before the take"; order given twice inconsistently).

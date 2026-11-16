# fix-rswording13 (fixer, static; nothing run except the four read-only checkers; nothing committed)
Files edited: RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT) only. Line numbers are from the files after the edit; strings found by exact text.

## Not fixed, needs the lead (inputs)
1. Person at the keyboard (Q-A, scenes 1 to 3), and the channel for "tell the lead" (Q-I), Q-D, Q-G, Q-J: no Q31 item exists. RW now says "no Q31 item, see fix log" (RW 21, 67, 143, 451). Lead: add Q31 items or answer in ORDERS.md.
2. The made-up e-mail address that lands in the intake mailbox and the name of its setting: in no file; RW 27 says unknown, lead verifies at re-pin (Q27 item 2).
3. The minimum wait and the expected attempts value: unset until rehearsal (Q31 items 25, 45). RW 29 says no minimum is invented.
4. QUESTIONS.md (a lead file, not edited) still asks who types y, the challenge and end (Q31 items 39 (a) and 43) and says the owner has Step D only in places; ORDERS.md lines 156 and 166 say the owner types them. Lead corrects.
5. Q31 index counts in QUESTIONS.md are untouched.

## Reader r6 (rw-r6-reader.md), 11 Majors
1. Contact count / "message": RW 23, 89, 144, 401: Step D now = deletes the contacts the lead lists after each of the lead's two delete requests (a chat message, not an e-mail message); at least 2 contacts (2 lead IDs); more after practice run and rehearsal (ORDER 037 item 3, ORDERS.md line 177).
2. Typed answers: RW 21, 23, 28, 89, 137, 401 now say the owner types y, challenge, end on camera plus S9-2, S9-3 (ORDERS.md line 156 Q27 item 10; line 166 Q28 item 4).
3. "unknown: lead answers" without Q31 item: replaced by "no Q31 item, see fix log" (RW 21, 67, 143, 451). B-045, B-046, A-004 now cite item 73 (RW 323, 324, 451).
4. Proof read in THIS take, in frame, after the wait and the recount (Q28 item 2, line 166; Q29 item 2, line 167); stale RWQ-9 sentence rewritten (RW 143).
5. RW 29: expected attempts value for two sends of the same lead ID; wait has no invented minimum; Q29 items 1 and 2 added (positive control, recount); POST 2 and the 10 s line defined (10 s line: ORDERS.md line 141 Q24 item 2).
6. RW 25, 27, 139, 220: Gmail filter defined; how a message reaches the intake mailbox explained, example.com/.test cannot receive; A-012 now cites step 10 for the filter.
7. Re-pin latest: RW 65, 88, 134, 385, 398 (and CT 20, 60, 86): NO-GO path Mon 23 Nov 07:00Z = 12:30 IST (ORDERS.md line 156 Q27 item 6).
8. Step 5 (RW 138): card A-008a only when no longer HELD.
9. RW 138 to 140, 161: prepared screen set, send note, stop note, take scripts defined; "take id" replaced by "lead ID of this take".
10. Edit steps 7, 10, 11 (RW 140, 143, 144): the studio owner edits and posts (Q27 item 3, line 156); RW 23 fixed.
11. N-5a (RW 233 and CT 664, same words): no "the lead", "a lead that stopped", "regular check", "run".

## Citation r17 and r16
B-045, B-046, A-004 cite item 73; N-4c cites R:38, N-5c R:34 and R:38, N-8 R:33 and R:34; A-085 dropped "(22:49 IST)".

## claims-r5-design.md, 7 Majors (cites re-grepped in CT)
M1 B-003 now OVERSTATED (flow path SUPPORTED as second verdict, not counted); A-002, A-015, A-049, B-219 already OVERSTATED.
M2 A-012 OVERSTATED; A-014, A-018, B-051 UNTRACED (mailbox-count outcome, no recording); A-013 keeps SUPPORTED with caveat "T19 not run; patch F-002 not applied"; A-014 carries the caveat. Verdict lists rows 7 and 39 updated.
M3 B-219 verdict cell, to-do row 79 and A-099 scope (now includes ONS:131).
M4 new lane rows A-100 (RW A-016b, UNTRACED) and A-101 (RW A-016g, SUPPORTED read only). Id count rises 328 to 330 (the id pattern A-016b would not be counted by claims-count.py, so the new ids are A-100, A-101).
M5 rule (six columns, no name or e-mail) copied into row 7b; rows 13, 18, 21 tags now say the rule is LIVE for the in-frame preview.
M6 B-195 and row 72: "reported by another test session, raw files not seen".
M7 RW line 30 and CT count text: 330; SUPPORTED 115, RELAYED-ONLY 70, OVERSTATED 64, UNSUPPORTED 27, UNTRACED 54; flagged ids 88, UNTRACED A/B 53.

## Checker outputs (run from flows-audit)
- check_rw_ct_pairs.py: paste strings in RW: 136 | found word for word in CT: 136 | not found: 0
- check_runsheet_paste.py: flagged ids 88, with no row here: []; UNTRACED 53; RESULT: PASS
- check_refs.py: PASS 5166 references
- claims-count.py: SUPPORTED 115, OVERSTATED 64, UNTRACED 54, UNSUPPORTED 27, RELAYED-ONLY 70, total 330; A 100, B 226, X 4; offenders: 0; ids 330 unique
Not checked: the other lines of CT outside the edited rows, section counts in RW 414 (row total 185 unchanged; no RW row added).

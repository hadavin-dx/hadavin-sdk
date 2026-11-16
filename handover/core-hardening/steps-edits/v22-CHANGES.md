# v22 changes (sheet v21 -> v22, note v5 -> v6)

Not fixed or only partly fixed (first, as the rules require)
- Length: the sheet is LONGER, not shorter. v21 118 lines / 7,943 words; v22 146 lines / 9,267 words (+1,324). Cause: the card is a full in-order script, new steps 7.7-7.10 and 8.4-8.5 were added. The stranger review wanted a shorter, simpler sheet; this is not met.
- Long bullets: the "Deadline" bullet is still over 100 words. Other long bullets were split. Partly fixed.
- Everything about vendor pages, buttons, the cancelled state word, HubSpot app names, the -I start line and need_seconds is UNVERIFIED. Needs the lead (v22-OPEN-FOR-LEAD.md rows 51-61).
- ORDER 034 (outside reader can follow it) is not shown as met. See Open 51.
- Not run by me: EGM result review, egm-resolve, egm-drift-report. These are the lead's steps.
- The frozen pointer map in evidence-v22/pointer-golden-v22.json was generated from my own v22 text. It only proves pointers did not change after freezing, not that they were right at the start.

Fixed (finding group -> where)
- Stranger blockers 1-5 and majors 6-14: one in-order card in sheet section 2 (Parts 1-4, steps 1-6) is the single source of the cancel rule. R1-R4, 6.5, 7.7/7.8, 8.1 and the set-phrase list point to it. One trigger list (a)-(h). "Unsure" has one meaning (STOP RULE). 7.7 split into 7.7-7.10. R10 `echo $?` pointer fixed.
- Stranger nits 15-24: wording and term order fixes, checked by glossary-order test in check-v22.py. Bullet length only partly (see above).
- Security majors 1-7: gates G39 (-I start line) and G40 (separate Y, RL, FP lines, RL >= need_seconds/60); G41 cancelled state word given by the lead, no "differs" fallback; G32 aligned with R2(b) with "unknown" defined; step 8.4 revokes HubSpot app secrets (phrase "HubSpot apps revoked") with a STILL WORKS branch, gate G42; step 7.8 states the end-first decision with the reason (cancel race G34 unknown); section 1 line 7 marked UNVERIFIED.
- Security nits 8-12: run-name prefix rule; key-file path must not start with /mnt/; mail delete checks (subject start and sender, delete means Trash; phrase "demo mails deleted <number>"); "one lower per key cancelled"; cross-refs and release-note ordering (items 7/8, G16, G37 vs step 9).
- Independent F1 (R10 pointer), F2 (note item 6 now "Open 2 and 31"), F3 (note section 0 numbered 1-10 in order), F4 (v16 citation now names its words part and appendix), F5 (R8 charset now allows . _ / - : = @ + , and the set phrases were reworded to fit; R8 has five lead words), F6 (one placeholder spelling <its name>), F7 (every quoted phrase is in the list; checker enforces it), F8 (sample dates all on Wed 18 Nov), F9 (Open 30 now 6,638 words for v20 by wc), F10 (checker catches both classes).
- Timing sample: run 15 min (need >= 860 s = 14.4 min), total 30 min; latest start 11:30 UTC = 17:00 IST; alarm 12:00 UTC = 17:30 IST; cancel-by 12:10 UTC = 17:40 IST. Mon 23 Nov latest start 17:39:00 UTC (deadline - 50 min). Arithmetic in evidence-v22/arith-v22.txt.
- Note v6: gates G39-G42 added; template range G1-G15, G17-G24, G31-G42; items 9 (ORDER 034) and 10 (end-then-cancel decision) added.

Evidence (evidence-v22/)
- check-v22-raw.txt: exit 0, TOTAL PROBLEMS 0, 73 pointer lines.
- mutation-v22-raw.txt: 22 runs; baseline M0 passes; 21 planted mistakes all caught, including an unlisted set phrase and a changed pointer target.
- arith-v22.txt, counts-banned-v22.txt (all counts 0).

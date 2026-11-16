# fix-ownersteps13 (owner part of OWNER-STEPS-q16-rows.md; static, nothing ran)
Source: reviews/round-12z-findings.md, "OWNER-STEPS owner part stranger read r11". Backup: scratchpad bak-os13/. Owner part now ends before "## For the lead" (old line 106, new line 108); that part and everything after is byte-identical to the backup (cmp rc 0). All 1 Blocker, 6 Majors and the Nit were real against the file.
- B1 New paragraph "Cancelled chases" before the table: four things cancel every Wednesday "missing:" chase (no-recording message, no item 6 answer by 08:30 UTC / 14:00 IST, a slip, a stopped take); the lead names new times; messages already received are still answered. Pointer added to rows 1a, 2a, 3, 2b, 1b, 5, 7, 4, to items 1 to 7, to the Wednesday-morning rule, the slip bullet and the chase list.
- M2 row 6: no answer by 08:30Z counts as treating the day as no recording; write nothing more.
- M3 "missing: credits answer" now at the later of 17:00Z (22:30 IST) and the lead's answer deadline (row 4, item 4, chase list); lead writes 17:30Z or 30 minutes after you.
- M4 double "missing: clean-up message": at 17:00 write nothing more if already due at 14:00 or if "retake yes" answered.
- M5 one post rule only in row 5; retake entry, item 5 and line 73 now point to it.
- M6 fixed two-facts question added to "What you type".
- M7 delete-message 1-hour deadline now has about-times (08:30Z / 14:00 IST for message 1, 12:00Z / 17:30 IST for message 2) and "the lead's message gives the clock time".
- Nit: line 9 names rehearsal and challenge; "rehearsal" in the run entry says "each explained below".
All new times are marked "planned by the audit, lead to confirm".
Consistency script (scratchpad os13/extract.py) output: counts per "missing:" word, table / items / chase. Chase counts above 1 for take-prep, clean-up and safety test come from explanatory mentions, not extra rules; every time and word matches.
{'table': 13, 'items': 7, 'chase': 1}
missing: GO or NO-GO {'table': 2, 'items': 0, 'chase': 1}
missing: clean-up message {'table': 3, 'items': 2, 'chase': 2}
missing: credits answer {'table': 1, 'items': 1, 'chase': 1}
missing: delete message 1 {'table': 1, 'items': 1, 'chase': 1}
missing: delete message 2 {'table': 1, 'items': 1, 'chase': 1}
missing: item 3 message {'table': 1, 'items': 1, 'chase': 1}
missing: re-check done {'table': 1, 'items': 0, 'chase': 1}
missing: re-check time {'table': 1, 'items': 0, 'chase': 0}
missing: recording-ready message {'table': 1, 'items': 1, 'chase': 1}
missing: reply words {'table': 0, 'items': 1, 'chase': 0}
missing: safety test result {'table': 3, 'items': 1, 'chase': 2}
missing: take-prep message {'table': 1, 'items': 0, 'chase': 2}
missing: typing message {'table': 1, 'items': 1, 'chase': 1}
missing: what y confirms {'table': 1, 'items': 1, 'chase': 0}
missing: where to look {'table': 1, 'items': 1, 'chase': 0}
table missing: credits answer => , only if you asked the two facts and either is still unanswered, do not revoke and write "missing: credits answer" (this covers both facts); the lead

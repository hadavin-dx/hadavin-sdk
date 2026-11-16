# Fix log, OWNER-STEPS-q16-rows.md, round 4 (applies stranger-ownersteps-q20.md)
Nothing ran. Only text was edited. Source read: the review, the sheet, inputs/DECISIONS-2026-11-16.md (read). ORDERS.md and the flow files were NOT re-read, so every line number is carried over unchanged from the old sheet and stays UNVERIFIED.

Applied
- B1 Step A: owner replies "yes, US$X" only if the lead's message holds the number; no number = no; says where (reply in the chat of the lead's message).
- B2 Step D: search by e-mail, delete only the exact made-up address, stop if more than one hit or one letter off, search again after, expect none, reply "deleted" (or "not deleted").
- M3: owner-types-nothing wording split: no paths, addresses, passwords in messages; v3 step 8 login marked UNCONFIRMED, not asked until confirmed; app password never pasted.
- M4: owner part moved to top with "OWNER: stop reading" line; lead text separated.
- M5: status box at top: UNVERIFIED, nothing ran, no action until "re-check done" with date.
- M6: owner told what success looks like (one message: all four checks passed; silence = not finished).
- M7: "alert" limited to one meaning (stuck-mail alert; columns called stuck-mail columns); "desk" explained as the studio's name for the alert receiver, location UNVERIFIED.
- M8: decision numbers replaced by the rule in words; numbers kept only as pointers to DECISIONS-2026-11-16.md (decisions 2, 8, 12 checked against that file and match). The "decision 5 ... ORDERS.md" pointer could not be checked: not re-read.
- M9: "most likely fail" now "not known, a guess".
- M10: psql must run against the take's own database; stated.
- M11: owner does nothing when a column is missing; stated.
- M12: mailbox names flagged unconfirmed; Row 4 blocked until shown.
- M13: lead steps renamed L1-L6; placeholder check added as L5 after L4.
- M14: order stated (practice run, owner yes, real HubSpot test, rehearsal); "loopback re-smoke" explained as "practice run".
- N15 one name "contact number"; N16 one name "made-up person"; N17 studio folder described, its place marked UNVERIFIED; N18 version history moved to footer; N19 "four columns/rows" vs "four checks" separated; N20 reason for no delete (take holds no delete right) added.

Not fixed / limits
- Nothing in the file can be confirmed here: line numbers, file names, setting names, HubSpot menu names, psql validity, mailbox identity all need the lead's re-check. Missing input: the take scripts and settings (the audit has not seen them).
- Finding 12 "mailbox names unconfirmed": applied as flagged, not resolved; needs the take's own settings.
- Reviewer findings found wrong: none. Finding 3 was partly a wording clash (typing different things); fixed by wording, not by removing the row.
- The "cost US$0" expectation is kept only as an expectation; the lead's number decides.

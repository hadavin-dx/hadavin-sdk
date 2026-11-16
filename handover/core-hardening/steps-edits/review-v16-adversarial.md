# Owner sheet v16 adversarial review (implementation readiness), condensed copy, 2026-11-16
Read only; nothing run. NOT ready: 3 Blockers, 11 Majors, 5 Nits. S = OWNER-SHEET-v16.md line.
B1 flow checksums (S:171, 219, 288, 298): E.0 tells owner to sha256sum each flow file and compare; appendix 3 says the compared form is an API export after activation, not the repo file; owner has no command for that form. Tick can never pass or owner improvises. Fix: exclude flow lines from the E.0 tick (lead states the match, go item 5(b)) or print a command.
B2 (S:100 vs 110, 68, 35): A.0b "cancel a listed run- key if you recognise it as yours" vs I.0 "only run-<run name>, never any other". CHANGES marks it FIXED; it is not.
B3 (S:94-95): 0.6 erases the result file first, then step 4 says read the "delete" line; if 0.5 hit a filter or 0.4 failed the owner cannot know if a step 0 contact exists. Fix: always search the exact step 0 address in HubSpot and delete if found, independent of the file.
M1 owner role far beyond decision 7 (S:7, 87-107, 389-395, 120-126): split steps into required by owner-safety rules vs could be done by the lead.
M2 step 0 vs decisions 8 and 2 (S:56, 87-96): default should be "not run"; a skipped step 0 can fail the paid take on camera.
M3 probe app and key creation is not a step (S:38, 88, 95, 405); no end deadline if stopped at 0.1; a cancelled step 0 never triggers 0.6.
M4 card cannot be complete when DO THIS FIRST needs it (S:10, 178-189, 200): rows sourced from step A message are blank when the card is sent.
M5 A.0b old-key / kept-key decisions have no criterion; OI-24 "highest balance" who sets it.
M6 informational-only ceiling and lag leave money rule without a decision (S:66, 71, 98).
M7 stop-word order puts cancelling run-<run name> below recording-off (S:32-40); say cancelling is always allowed whichever word wins; Key exposed says "Then Freeze" while Freeze says close nothing.
M8 F.5 missing from closing checklist and gates (S:248, 342, 240); contact ids vs addresses.
M9 lease sentence order (Q21.2) not carried: sheet bans every lease sentence, candidate S:352 lacks the "gap longer than the lease is not claimed" text. M10 candidate reads as a promise ("whatever the lease"). M11 film cannot show which mail belongs to person A; if printed result does not say it, state a plain no-go for the claim.
Scenarios: skipped step 0 (M2, M3); step A late (no minimum gap before E.0, formula omits A.0-A.6 time and lag wait: add "step A needs N minutes" line); wrong A.6 numbers (nothing checks typed vs message); wrong `end` word costs the film; lost key (two keys may carry same name, E.0 tick ambiguous; no fallback if key page unreachable); take late past money stop (covered by Time); leftover contact (B3, M8).
Nits: S:142 stamp line multi-value; lowercase "stop" at S:370, 391; sheet 418 lines; DECISION-one-store:14 still says ONE database (input, lead); ban list ok.
v16-CHANGES audit: SE-M3, CI-1, AD-1 (B2), SE-M1/AD-19 (B1), AD-4 (B3), AD-2 (M9), ST-B2, CI-4 marked FIXED but are not; NOT FIXED rows honest (ST-n2, ST-G, AD-3, AD-12, AD-37, AD-5/29 contact ids).
Not checked: v16-OPEN, check-v16.py, any program/flow/script, ORDERS beyond Q15-Q21.

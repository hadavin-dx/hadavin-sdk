# Owner sheet v31 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: steps-edits/evidence-v31-independent/ (00-TABLE.md first). Recorded, not judged.
## Failures and deviations first
1. check-v31.py does NOT end at 0 failures: 9 failures, all C19 ("pointer not in the verified list") in v31-CHANGES.md (pointers-v31.txt written 17:33Z, v31-CHANGES.md edited 17:46Z). A person must read the new pointers and run ACCEPT_POINTERS=1. v31-CHANGES.md says "Baseline failures 0": does not match.
2. mut31.py: 230 plants, 228 caught, 0 missed, 1 anchor-not-found (M48, text no longer in v31-CHANGES.md), negative control ok. CHANGES says "229 caught, 0 anchor-not-found": does not match.
3. check-v31.py misses these hostile mutations (source edit then rebuild): H09 warning beside default A removed from lead note; H18 absolute path in an owner sheet; H20 `ORD:` and H21 `DEC:` in an owner sheet; H25 "one letter only" rule shortened; H33 7-day date computed from 160 h not 168 h (page shows 18:30 UTC = 00:00 IST, pair and weekday consistent); H37 label L5 renamed L4; H38 UNVERIFIED removed from a heading; H50 film pause 10 to 12 in one place; H51 call ceiling 3 to 4 in one place; H53 run length 15 to 12 in one place; H54 new wording of the old H06 idea ("the lead sends you cancel the older key"). Biggest class: a number typed once in a source and not tied to the facts file (H50, H51, H53): neither checker catches those.
4. v30 evidence named 3 misses (H06, H09, H15): H06 exact text now caught (C213) but variant H54 not (H55 caught); H09 caught (C224); H15 caught (C225). 18:00 UTC = 23:30 IST is on no v31 page; 18:29=23:59, 18:19=23:49, 18:09=23:39 are on owner pages; 18:04=23:34 only in appendix and lead note.
5. Runner's P05, H43, H46, P12 had anchor problems (P05 not counted; the others re-run).
6. Other agents' heavy jobs shared the machine.
## Results
build-v31.py rc 0, 44 files identical before and after. v31-fail-proof.py rc 0: 17 of 18 Part 8 checks (C210-C227) fail on built v30; C224 cannot fail on v30; none fail on v31. Independent checker indep31.py (no shared code): 0 findings on built v31. Words: sheet A 6287 (cap 6300), B 6087, card A 1959, B 1876, appendix A 4458, B 4389, film page 519, lead note 13032, open list 7679. Weekdays Mon 16, Wed 18, Sun 22, Mon 23, Wed 25 correct.
## Mutations
69 applied. Source edits rebuilt 57: check-v31 caught 45, indep31 39, both missed 6 (H33, H37, H38, H50, H51, H53). Built-page edits 12: check-v31 12 (5 only via C01 rebuild comparison), indep31 7, 0 missed. indep31 catches H09, H18, H20, H21, H25, H54 that check-v31 misses; check-v31 catches 12 that indep31 misses.
## Status
inputs/src/tests 0 changes; no processes left; base/ kept.
## Not checked
Whether sheets are understandable or correct for a person; UNVERIFIED claims; other text; CI gates; whether the rules are right.

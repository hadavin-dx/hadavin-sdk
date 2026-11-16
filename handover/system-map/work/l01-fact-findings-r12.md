# L-01 round 12 fact reader findings (security path; saved from the hand-back of af8ac853614ad42a9)

Result: 0 Blockers, 1 Major, 6 Nits. Stamp 2026-11-16 21:15 UTC / 2026-11-17 02:45 IST identical on all three pages; 11 shared blocks once per page; approve/refusal lines identical on L01 and OV (checked by regex, not full character diff). md5 not checked by this reader.

## MAJOR
1. Reply list item 5 ("Everything else ... and any question") precedes item 6 (other yes/no questions judged only against their own sentence) under "first match wins", so item 6 is unreachable (L01 87, OV 147, LP 133). Outcome is safe (neither is an approve/refusal) but wording conflicts. Fix: item 5 starts "Everything else that is a reply to this request", or move item 6 before 5. Shared block change = NEW STAMP.

## NITS
1. L01 line 9 card item 4 writes `new deadline agreed: <date>`; tables write `<date and time>`. Use `<date and time>` (outside stamp).
2. L01 line 11 card item 6: "any other reply (a bare yes, ...) counts as nothing" lacks the exception "except a bare no right after the request".
3. LP line 117: STAMP line sits after LP-4, before LP-5 (119); Stamp rule says it stands in LP-5.
4. OV line 75 cites "(lead answer 7)" for post time; it is Batch 3 item 7 (LEAD-ANSWERS line 67).
5. OV row 7 (114) and LP 111 cite "first section, item 1b with item 8 update"; that is under Batch 2 (LEAD-ANSWERS line 57).
6. LP 103 gives run-day card steps "17 to 22" for step F while 105 puts step 22 under after-run work.

Not checked: md5 values; full character diff of every block; cites to ORDERS/QUESTIONS/decisions/TAKE-BLOCKERS/OS lines/FINAL-CROSSCHECK/flowcheck.

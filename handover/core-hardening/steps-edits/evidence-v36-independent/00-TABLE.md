# Evidence v36 independent (EVIDENCE RUNNER, no judging) - run 2026-11-16 ~20:40 UTC
Raw outputs: 01-rebuild.out, 01-diff.txt, 02-check-v36.out, 03-wordcount.out (wc.py), 04-times.out (times.py), 05-plants.out (plants.py; scratch copies outside repo), 06-scan.out (scan.py).

## Deviations first
- D1 (plant P08 NOT caught): renaming the set phrase "contacts deleted <number>" to "contacts removed <number>" in facts-v36.py, consistently everywhere, gives check-v36.py 0 failures. No check holds the literal. ("run started" has a literal in newchecks-v36.py; "contacts deleted" and "app passwords revoked" have none in check-v36.py/newchecks-v36.py by grep.)
- D2: v36-OPEN-FOR-LEAD.md has one IST time with no UTC pair: "one phone alarm at 08:00 IST the next day" (table row near line 134). Not a mismatch, no pair to check.
- D3: P10 and P15 were stopped by asserts inside facts-v36.py (reported as C00), not by a content check.

## Results
| Step | Result |
|---|---|
| 1 rebuild from source to temp, diff vs built files | build rc=0; all 10 built files byte-identical (cmp); 0 differences |
| 2 check-v36.py | rc=0, "check-v36: 0 failure(s)" |
| 3 words (own counter: runs of non-space; also explicit whitespace-set counter; also wc -w) | A: sheet 6270, card 2238, appendix 5658, film 589, helper 956, total 15711. B: sheet 6097, card 2191, appendix 5515, total 15348. Claim 6270 / 15711 / 15348: match. Caps 6286 and 15715: sheet A 16 under, total A 4 under. Five-page total for B 15348 |
| 4 UTC/IST pairs and weekdays (11 files) | 198 pairs, 141 weekday-dates, 0 mismatches; 16 Nov 2026 = Mon confirmed |
| 5 hostile plants (20, applied in source/facts, rebuilt so C01 is clean, then check-v36.py) | 17 caught by a content check, 2 stopped by facts asserts (C00), 1 not caught (P08). Table below |
| 6 banned brand strings (list of 10 read at run time) | 0 hits in 25 v36/lead files. Secret-shaped: 0 real hits; 1 pattern hit = alphabet string at check-v36.py line 284. Literal AKIAIOSFODNN7EXAMPLE count 0 |

### Plants (id: change -> checks that failed)
P01 Recording "switch it OFF yourself at once" -> "leave it as it is": C14
P02 "No word of the lead resumes" -> "Any word ... resumes": C23
P03 "Never Select all, never empty Trash" weakened: C14, C23
P04 "card first" -> "card second": C19, C23
P05 balance sentence replaced: C23
P06 four alarms -> three: C138, C14, C172, C25
P07 "never use rotate" -> "use rotate if you like": C14, C44
P08 set phrase "contacts deleted" -> "contacts removed" (facts, consistent): NONE
P09 set phrase "run started" -> "run starts" (facts): C105, C21
P10 deadline 18:29 -> 18:39 (facts): C00 (facts assert)
P11 earliest key time 10:30 -> 10:45: C18, C235
P12 broken IST pair in text (11:30 UTC = 16:30 IST): C04, C239
P13 wrong weekday "Tue 23 Nov 2026": C04, C239, C96
P14 call ceiling 3 -> 4: C03, C04, C17, C236, C48
P15 output price 1500 -> 1600: C00 (facts assert)
P16 balance 189.00 -> 199.00: C04, C48
P17 backtick rule reversed: C14
P18 key-save prompt "Enter:" -> "Return:": C14
P19 open-list row number 1 -> 2: C16, C19
P20 secret-shaped string (built from parts, AKIA+...) added: C55

## Not run
- No full mutation run (mut36.py, pid 22677 not touched), no pytest/ruff/bandit, no heavy-slot jobs (none needed).
- Plants were applied only in source/facts (not directly in built files; direct edits would be caught by C01 by construction, not tried).
- Only 20 plants; no fuzzing. Word count compared token runs only; no check of what a "word" means to a reader.
- Weekday/time scan covers the formats my regexes match (HH:MM UTC = HH:MM IST; "Mon 23 Nov [2026]"; "Mon Nov 23"; "23 Nov (Mon"; "Mon 2026-11-23"); other phrasings would be missed.
- Scratch copies under the session scratchpad plant/ (P01..P20, base); evidence-v36-independent/rebuild/ holds the rebuilt files. No commit, no push, no chmod, no helper processes left running.

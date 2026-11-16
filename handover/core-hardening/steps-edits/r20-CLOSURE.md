# r20 closure table: every finding id of the r18 and r19 reviews, one row each

Status words: CLOSED (text changed and a check in `verify20.py` fails on r19 and passes on r20), PARTLY, LEAD-DECISION, UNVERIFIED, THIRD-PARTY. "Check" names the label in `verify20.py` (section "round 20 checks") or the older check that already guards it. Nothing here is reviewed by anyone but the builder; the lead's reviewers judge.

| id | finding in one line | status | evidence (check label, or the reason and next step) |
|---|---|---|---|
| r18 security M1 | identification rule can stop item 1 from starting | PARTLY | r19 closed the dead end with `web revokes not done`; r20 adds M2 item 5 checks and the M3 rotate-first rule; whether an owner can tell what his own n8n holds is UNVERIFIED (needs a real run) |
| r18 security M2 | no last resort for the key after 18:29, no alarm for Tue 24 | CLOSED | checks `M1 key has no date`, `M5 five alarms`, `M5 alarm 5 unconditional`; the Tue 24 date itself is lead decision ND18 |
| r18 security M3 | day page lacks the steps it points to | CLOSED | checks `MA day sheet holds key step B`, `MA day sheet holds D.1 to D.4`, `MA day sheet says it is not everything` |
| r18 security M4 | L-LEN not met | LEAD-DECISION | ND20 with a plain recommendation question (check `m9 ND20 recommendation question`); the choice is the lead's |
| r18 security m1 | alarms 1 and 3 are exceptions to waiting | CLOSED | check `M4 exceptions list` (alarm 1, 3, 4, 5, emergency, last time to revoke) |
| r18 security m2 | key gone word used in conflicting cases | CLOSED | check `M4 one rule for key gone (B)` and `m2 route B warning in the prompt` |
| r18 security m3 | 18:25 late or breach | CLOSED | r19 sentence kept; check `min plain words` and `min card step 1 time` |
| r18 security m4 | which item needs which check | CLOSED | closed in r19 per the r19 reviewer; r19-pins guard it (pins rebuilt, `r20-pins.txt`) |
| r18 security m5 | open at r19 review | PARTLY | the r19 reviewer marked it OPEN; I could not tie it to a sentence from the condensed review; UNVERIFIED, the lead names the original finding text |
| r18 security m6 | click path check, K-G | PARTLY | check `m4 app password page shows only a name`; whether the Google and HubSpot pages show name and day is UNVERIFIED (third party pages) |
| r18 stranger B1 | key and the 10 minutes | CLOSED | r19 closed; r20 keeps it with check `min plain words` |
| r18 stranger B2 | "10 minutes" two meanings | CLOSED | r19 closed; guarded by pins `r20-pins.txt` |
| r18 stranger B3 | day sheet not usable alone | CLOSED | checks `MA day sheet holds key step B`, `MA day sheet holds D.1 to D.4`; day sheet 6256 words, check `r20 day sheet longer than 6300 words` |
| r18 stranger M1 | L-LEN cannot be decided | LEAD-DECISION | ND20 and section L-LEN in `r20-CHANGES.md` |
| r18 stranger M2 | route cost hidden in appendix | CLOSED | r19 closed (route A price at D.1 and D.3); kept by pins |
| r18 stranger M3 | `no more takes` vs `yes, no more takes` | CLOSED | checks `m7 ND15 option B`, `MB K-D`, `MB old route B time` |
| r18 stranger M4 | one word, one event broken | CLOSED | checks `M4 one rule for key gone (B)`, `MG exact typing`, `MG replies of key step F in the table` |
| r18 stranger M5 | stale labels, Tue 24 shown as fact | CLOSED | checks `MD hedge replaced by a rule`, `MD hedge`, `m7 ND15 stale`, round line order check |
| r18 stranger m1 | card step 1 "instead of both" | CLOSED | check `min card step 1 time` |
| r18 stranger m2 | "last" has four meanings | PARTLY | not changed in r20 beyond r19; UNVERIFIED whether a stranger now reads it right |
| r18 stranger m3 | "key" many meanings | PARTLY | reviewer r19 said not fixed; I did not rewrite every use of "key"; I explain it in the day sheet words list only; next step: a lead call on a glossary line |
| r18 stranger m4 | item, step, part overloaded; Phase 0 note undefined | PARTLY | check `MF day sheet defines take and cut`; Phase 0 note pointer on the day sheet is UNVERIFIED |
| r18 stranger m5 | retire check unexplained on the day sheet | CLOSED | r19 closed; day sheet has the identification check section (check `r20 day sheet lacks`) |
| r18 stranger m6 | alarm 1 30-minute rule confusing | PARTLY | the alarm paragraph is split into five alarms (check `M5 five alarms`); readability UNVERIFIED |
| r18 stranger m7 | item 3 no pointer to last-day exception | CLOSED | r19 closed per the reviewer; kept by pins |
| r18 stranger m8 | stale counts text | CLOSED | r19 closed per the reviewer; facts lines machine-checked in `r20-CHANGES.md` |
| r18 stranger m9 | "question for the studio lead" in owner text | PARTLY | check `MD hedge on the day sheet`; a full scan of every owner row for lead-facing phrases was not done (UNVERIFIED) |
| r19 security M1 | key deferrable with a date | CLOSED | checks `M1 key has no date (D.5, I)`, `M1 G.2 no later date`, `M1 old handoff date for the key`, `M1 later date` |
| r19 security M2 | item 5 dead end | CLOSED | checks `M2 item 5 counts as done (G.2)` and `(E-59)` |
| r19 security M3 | app 2 and app password stay alive | CLOSED | checks `M3 rotate first`, `M3 two n8n told apart`, `M3 take-only word`, `M3 app 2 goes to the take n8n`; owner ability to tell is UNVERIFIED |
| r19 security M4 | no emergency early revoke | CLOSED | check `M4 emergency revoke` |
| r19 security M5 | first reminder 11 h 41 min late, alarm 4 conditional | CLOSED | checks `M5 alarm 4 at 18:24`, `M5 alarm 5 unconditional`, `M5 alarm 5 not conditional`; alarm 2 time is lead decision ND18 |
| r19 security m1 | alarm words conflict | CLOSED | check `m1 alarm word` |
| r19 security m2 | prompt after `key revoked` lacks route B warning | CLOSED | check `m2 route B warning in the prompt` |
| r19 security m3 | "In short" garbled | CLOSED | check `m3 In short repaired` and `m3 double space` (the double space and the missing "Then you" were real; fails on r19) |
| r19 security m4 | identification compares name and date, point (5) names only | CLOSED | check `m4 app password page shows only a name` |
| r19 security m5 | paper lists have no typed gate | LEAD-DECISION | ND19 (`lists written`), check `m5 ND19 lists written` |
| r19 security m6 | day sheet item 2 lacks click path | PARTLY | check `m6 item 2 click path` adds it with the words "this click path is not checked"; correctness UNVERIFIED |
| r19 security m7 | ND15 option B stale | CLOSED | checks `m7 ND15 option B`, `m7 ND15 stale` |
| r19 security m8 | shred rule: line break, hand list | CLOSED | checks `m8 no line break`, `m8 own list is the only check for (b) and (d)` |
| r19 security m9 | L-LEN undecided | LEAD-DECISION | ND20, check `m9 ND20 recommendation question` |
| r19 stranger M-A | day sheet lacks key step B and D.1 to D.4 | CLOSED | checks `MA day sheet holds key step B`, `MA day sheet holds D.1 to D.4`, `MA old claim` |
| r19 stranger M-B | real latest time in route B is alarm 1 | CLOSED | checks `MB step 21 heading`, `MB real latest time`, `MB K-D`, `MB old route B time` |
| r19 stranger M-C | G.2 undated; no way to show times | CLOSED | checks `MC G.2 dated Monday`, `MC how to show times`, `MC other days`, `MC old clock rule` |
| r19 stranger M-D | "studio lead" hedges, no rule if no answer | CLOSED | checks `MD hedge replaced by a rule`, `MD second person rule`, `MD second person open`, `MD hedge`, `MD hedge on the day sheet`; the underlying decisions stay with the lead (ND18) |
| r19 stranger M-E | identification likely always ends `used` | PARTLY | r20 answers with rotate first (check `M3 rotate first`) so `used` no longer leaves a key alive; whether an owner can tell is UNVERIFIED |
| r19 stranger M-F | take, cut, routes undefined on the day sheet | CLOSED | checks `MF day sheet defines take and cut`, `MF day sheet defines routes` |
| r19 stranger M-G | typed-word conflicts, no typing rule | CLOSED | checks `MG exact typing`, `MG replies of key step F in the table`, `M4 one rule for key gone (B)` |

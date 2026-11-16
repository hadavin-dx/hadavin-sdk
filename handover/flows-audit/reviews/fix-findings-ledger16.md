# fix-findings-ledger16 (round 16; one fixer; edited only FINDINGS.md and LEDGER-ROWS.md; nothing committed; nothing run in n8n)

## FAILURES, UNCERTAINTY AND WHAT WAS NOT DONE (first)
1. ITEM 3 CONTESTED IN PART (checkable evidence): the reviewer says a lead who answers Q31 item 59 as written leaves REPO a placeholder. FIX-PLAN.md Step 0a (2) sets `REPO="$(git rev-parse --show-toplevel)"` and step (4) writes it into shas.env with `sed "s|^REPO=.*|REPO=...|"`. So REPO needs no question if Step 0a is followed. What IS wrong, and is fixed: "(one value, asked in Q31 item 59)" (READ-FIRST) and inputs row 3 ("the pairing is the audit's reading"). I still wrote the NEW QUESTION text as ordered (REPO as eighth value of item 59, due Tue 17 Nov 03:30Z (09:00 IST)) inside the F-003 fix cell, part (4a), but with a NOTE saying it is a safeguard and the lead may drop it. Lead decides.
2. ITEM 4: TAKE-CHECKLIST.md and QUESTIONS.md were NOT edited (other sessions). The two files still differ until check 13 is changed; FINDINGS (F-007, F-031) now says its pass line governs. Changes needed are listed below.
3. ITEM 6: "Row 4" was NOT renamed: RUNBOOK (18 uses), QUESTIONS (43), TAKE-CHECKLIST (11), FIX-PLAN (9), ORDERS (3) use it; renaming in two files would split them. Instead its description lost the word "first" in FINDINGS (READ-FIRST, inputs row 9, Words x2, WEDNESDAY CLOCK). The reviewer's "T19-T21 and the probe run before Row 4" is itself contested: FIX-PLAN step 10b says the probe IS Row 4 (the audit's reading, UNVERIFIED), F-018 says it is a separate step before. Whether T19-T21 and the probe reach HubSpot: the files do say something (RUNBOOK table 'One filled flow set...' lines 246-259: re-smoke leaves 1 contact, T19 and T21 leave contacts, T20 none, Row 4 1, step 19a 2; RUNBOOK I17: "the first live send is step 16 on Tuesday"), but it is the RUNBOOK author's reading ("the lead confirms in I43"), so I recorded it as that and wrote "NOT WRITTEN: LEAD FILLS" for the confirmation, the probe/Row 4 identity and the address question (new inputs row 11, pointer in the F-018 cell).
4. Not done (stated, not hidden): NOT COVERED item 28 still says "time TBD" (not in the reviewer's list; I did not check RUNBOOK for its time). Reviewer's unread parts (F-029, F-041, F-028, F-001, F-012-F-046, LEDGER 12-47, Q31 items 17, 19, ...) were not re-read by me beyond the edits below. No fresh reviewer has read these edits yet.
5. The "one plain sentence" gloss for the ten rows is my wording from the ledger summaries; the row text is the authority.

## FINDING TO RESULT
| # | finding (r15) | checked against | result |
|---|---|---|---|
| 1 | FINDINGS 16-18 unreadable | text: line 18 was one 3686-char paragraph; READ-FIRST had no ids | DONE. New 10-row table (n, id, severity, plain sentence, GO row 6 flag) after the READ-FIRST list; "downgrade route", "minimum set", T7b explained under it; old line 18 split into 7 numbered points (minimum set as sub-bullets); the time-ordered list deleted and replaced by a pointer to the decision table (checked: the table has every item of the old list plus item 32; no other file quotes the list: grep). Table rows start with `\| n \| F-nnn`, not `\| F-`, so count and compare scripts do not see them. |
| 2 | "$REPO first used at step 4a" wrong | RUNBOOK 205 step 1: `need_set REPO PATCH_BRANCH BRANCH FINAL_SHA` and `git -C "$REPO"` | CONFIRMED and DONE. Inputs row 3 and F-003 part (4) (both files) now say first used at step 1 (04:00Z, or 03:31Z), by a patch at 4a. Row 3 rows list now F-003, F-004, F-007, F-011, F-028, F-031, F-041, F-042, F-043 (all nine have `cd "$REPO"`; reviewer named two, I counted by grep). |
| 3 | $REPO has no question | RUNBOOK 93, QUESTIONS 523 (seven values), FIX-PLAN Step 0a | PARTLY CONFIRMED (see failure 1). READ-FIRST line, inputs row 3, decision row 59, WHO DOES IT line fixed; NEW QUESTION text in F-003 (4a), both files. |
| 4 | two pass definitions | FINDINGS F-007/F-031 vs TAKE-CHECKLIST 361 | CONFIRMED. F-007 and F-031 cells (both files) say their pass line governs; one allowed-hit sentence (after the F-004 patch only REPORT.md:49; :150/:153 only until F-004 is applied). TAKE-CHECKLIST changes below. |
| 5 | minimum set omits second reader | F-011 row (4b) | CONFIRMED and DONE: "(2b)" in the minimum set; decision table row 18 and inputs row 4 name 07:00Z. The time-order 07:00Z entries no longer exist (list deleted). |
| 6 | Row 4 "first" untrue | READ-FIRST 8, Words, WEDNESDAY CLOCK, RUNBOOK I17 and table | CONFIRMED the word "first"; not renamed (failure 3); inputs row 11 added with the question and the facts. |
| b1 | F-002 (4) hour LEAD FILLS | RUNBOOK 268: step 2 04:03, step 3 04:08 | DONE (both files): 04:03Z (09:33 IST), 04:08Z (09:38 IST); 03:34Z (09:04 IST), 03:39Z (09:09 IST) on the 03:31Z start (shift by the difference, as RUNBOOK says). |
| b2 | F-003 and inputs row 10 times are no-wait | RUNBOOK 269 | DONE: "NO-WAIT times", late 4a input moves apply to 04:46Z-04:56Z (10:16-10:26 IST), end at most 08:59Z (14:29 IST); item 51 caps the wait. |
| b3 | Verdict: UNVERIFIABLE, code-last rule, the brain, T13 | Words line, mf.py 337-338 | DONE in FINDINGS: 7x UNVERIFIABLE -> UNVERIFIED; "code-last rule" and "brain" explained in row 8; T13 added to the Tests word line. |
| b4 | NOT COVERED 22-24 "time TBD" | RUNBOOK steps 16, 19, 21, 24 | DONE with RUNBOOK times (08:29Z (13:59 IST) no-wait re-smoke; 07:00Z (12:30 IST); 07:44Z (13:14 IST), first send 07:48Z (13:18 IST)). |
| b5 | LEDGER header one 2000-word line, no compare result for round 14 | | DONE: header split into a title, 6 rule bullets and one history bullet per round; round 14 bullet now carries "45 45 differences: 0" (from fix-findings-ledger14.md line 31); round 16 bullet added. |
| b6 | F-004 no owner / WHAT CLOSED PROVES | | DONE (both files): proposed applier, artifact, date, what closed proves. |

## NEW QUESTIONS FOR THE LEAD TO ADD TO QUESTIONS.md (texts are inside the cells)
- REPO as an eighth value of Q31 item 59, due Tue 17 Nov 03:30Z (09:00 IST): FINDINGS/LEDGER F-003 fix cell, part (4a). Optional (see failure 1).
- WHICH SENDS REACH HUBSPOT (re-smoke, T19, T20, T21, probe, Row 4, step 19a; probe = Row 4 or separate; different made-up addresses; what counts against "up to 3 sends"), proposed due Tue 17 Nov 08:29Z (13:59 IST): FINDINGS inputs table row 11 (summarised in the F-018 fix cell).

## TAKE-CHECKLIST.md CHANGES NEEDED (check 13, line 361; owner: plan-files session)
1. Add part (0): `test -d "$REPO/handover/demo" && echo FOLDER-OK` prints FOLDER-OK.
2. Add F-007 part (2) and (2b): `grep -c -F "Kill case names (one table)"` on PAGE-STATEMENTS-V4.md and VIDEO-RUNSHEET.md prints path:1 each; and the two greps for `K3B (this table) = n8n killed after` and `K3 (this table) = n8n killed after` print path:1 each (strings as in the F-007 cell).
3. F-031: replace "at least one line found" by: the sentence stands BEFORE the heading `## Total running time` (the two-pattern grep lists the sentence first).
4. Replace the allowed-hit list by the FINDINGS sentence: after the F-004 patch the only allowed hit is handover/demo/REPORT.md:49; PAGE-STATEMENTS-V4.md:150 and :153 only until F-004 is applied; delete "may stay only until the lead gives the new wording, then the lead EDITS them".
Also for the lead: QUESTIONS.md line 212 ("Row 4 (first real HubSpot send)") still says "first".

## RAW OUTPUTS (run from flows-audit after the edits)
PASS 5175 references
PASS 655 rows
PASS 0 hits in 2698 files
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
846 files already formatted
45 45 differences: 0

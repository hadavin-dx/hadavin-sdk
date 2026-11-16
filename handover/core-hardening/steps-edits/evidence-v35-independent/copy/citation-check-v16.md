# v16 citation check (citation checker, read-only; nothing in any sheet was run), 2026-11-16

Checked: OWNER-SHEET-v16.md (S, 418 lines, 88,872 bytes), v16-CHANGES.md (CH, 101 rows), v16-OPEN-FOR-LEAD.md (OP) against review-v15-security.md, review-v15-stranger.md, citation-check-v15.md, cross-read/adversarial-contradiction-v15.md, inputs/, ORDERS.md, paste-check/plan-v10-real-v5-edits.md, and the sheet itself. I re-ran `python3 check-v16.py` (exit 0, "TOTAL PROBLEMS 0") and diffed it with v16-check-output.txt.

Result: 0 Blockers, 0 Majors, 6 Minors (all wrong numbers or pointers in the change notes; the sheet text itself held up). Banned-word count was taken by the script only (0); I did not print or write any banned word.

## Failures first (cite | claimed | actual | WRONG)
| # | Cite | Claimed | Actual | Sev |
|---|---|---|---|---|
| 1 | CH "Size, honestly"; OP B.1 | Part 1 is 36,315 bytes | 36,317 (check-v16.py and its own output file print 36317; I recomputed with the script's split at "\n# Part 2.") | WRONG, Minor |
| 2 | CH "Size, honestly" | whole file 88,870 bytes | 88,872 (`wc -c` and check output). The claim "about 430 bytes over v15" still holds (36,317 - 35,882 = 435) | WRONG, Minor |
| 3 | v16-check-output.txt line 3 | v16-CHANGES.md bytes=13831 | CH is 13,825 bytes now (`wc -c`; a re-run of check-v16.py prints 13825, the only diff line). The output file is stale: CH was edited after it was written (both files 11:41). Output file must be regenerated | WRONG (stale), Minor |
| 4 | CH "Size, honestly": "adds ... eight open items" | eight new open items | nine: OI-30 to OI-38 (OP intro "OI-30 to OI-38 are new"; OP B.8; S appendix 18 "New in v16"). Three new secrets rows is correct (v15 had 6, v16 has 9) | WRONG, Minor |
| 5 | CH row ST-n8: "step I intro and appendix 14: you film nothing for the proof screen" | text is in step I intro | "film nothing" occurs in S line 11 (DO THIS FIRST 2) and S line 385 (appendix 14 item 4). The step I intro (S 119 to 126) does not say it | WRONG (pointer), Minor |
| 6 | S line 50: "D (Part 2, first section)" | D is in Part 2's first section | Part 2's first section is "The values" (card table). D is in the second section, "Run day: preparation" (S 202 to 206) | WRONG (pointer), Minor |
| 7 | CH row SE-M2: "B20 equivalent OI-35" vs CH header "v15 blank B-n = v16 OI-n (same numbers)" | one numbering rule | v15 B20 = "where the probe key comes from" = OI-20 (OP). OI-35 is a new item (exact contact address and probe app name). The row mixes two numbering rules; no content is lost, but "B20 equivalent OI-35" reads as a renumbering | Unclear, Minor |
| 8 | CH id "CI-13" and CI-1..CI-12 | ids exist in citation-check-v15.md | The file numbers its failures 1 to 12 (no "CI-" prefix) and uses "CI-2" and "CI-U4" as ids of its spot-check table, where "CI-2" means the PASS/FAIL/SKIPPED row, not failure 2. CH CI-2 (four markers) = failure 2; CH CI-13 = the file's "CI-U4". Content maps one to one, but the ids are not literal and CH CI-2 collides with the file's own CI-2 | Unclear, Minor |
| 9 | CH row CI-4 "card lines hold one value each" | true | Not provable by check-v16.py (CH admits it). Card lines 177 (page, amount), 190 (a number plus the printed result it covers), 171 (list lines added as needed) can still hold more than one value | Weakly OK, noted |
| 10 | OP OI-13 and S appendix 7 "plan-v10 lines 456 to 459 (Text B)" | file named plan-v10 | no file `plan-v10.md`; the lines are in `paste-check/plan-v10-real-v5-edits.md` lines 456 to 459 (Text B is there; "up to three tries" is there). Content OK, path imprecise | OK (path loose) |

## Everything else (cite | claimed | actual | OK/WRONG)
| Cite | Claimed | Actual | Result |
|---|---|---|---|
| CH status counts | 91 FIXED / 3 BLANK / 2 MOVED / 5 NOT FIXED | by first word: FIXED 91, BLANK 3 (SE-M5, SE-M6, ST-17), MOVED 2 (SE-N6, ST-n3), NOT FIXED 5 (ST-n2, ST-G, AD-3, AD-12, AD-37); total 101 | OK. Note: several FIXED rows also hold a BLANK or NOT FIXED part (SE-M1, SE-M7, AD-5, AD-29, AD-16), so the counts are by first word only |
| CH row count | 101 rows | 101 (script: expected 101, rows 101, missing none) | OK |
| Finding ids vs v15 reviews | SE-M1..M7, SE-N1..N8 | review-v15-security.md: "7 Majors, 8 Nits", M1..M7 and N1..N8 present | OK |
| ST-B1..B5, ST-6..17 | exist | review-v15-stranger.md: Blockers 1 to 5, Majors 6 to 17 | OK |
| ST-n1..n8, ST-U1..U7, ST-G | exist | stranger nits list has 8 items (n1 markers, n2 8x8, n3 App.17, n4 "program", n5 `~`, n6 S:44, n7 `<B28>`, n8 proof screen) all matched by CH text; "Did not understand" has 7 items, matched to U1..U7; "Still needs a second person" = ST-G | OK |
| CI-1..CI-12 | exist | failures 1 to 12 of citation-check-v15.md, content matches each CH row (CI-13 see failure 8) | OK except id literalness |
| AD-1..AD-40 | exist | adversarial-contradiction-v15.md items 1 to 40 numbered as claimed (spot-checked: 2 lease, 4 step 0 leftover, 6 read-only line, 14 rounding, 22 key vs money stop, 26 key exposed, 33 "C unknown", 38 filter) | OK |
| OP OI-1..OI-38 | complete, unique | 38 rows `| OI-n |`, no duplicates (`uniq -d` empty); each also in S appendix 18 | OK |
| OP B.1..B.10 | complete, unique | numbered 1 to 10, one each; B.2, B.3, B.4, B.6, B.7 cited from CH and OI-5 exist | OK |
| Every OI-n cited in S, CH, OP | exists | all <= 38 (script) and every OI is used outside the list (script) | OK |
| Proposals | OI-16 to 19, 21 to 23, 28 | S list [16,17,18,19,21,22,23,28], OP "Proposal" rows the same set | OK |
| v16-check-output.txt vs re-run | same | identical except CH bytes (failure 3); all other lines identical, exit 0 | OK except failure 3 |
| Byte sizes: v15 sheet 35,882 | 35,882 | `wc -c` OWNER-STEPS-realrun-v15.md = 35,882 | OK |
| v15 three files 80,446 | 80,446 | 35,882 + 12,537 (card) + 32,027 (appendix) = 80,446 | OK |
| Card underline lines | 57 | S lines 142 to 198 inclusive = 57; script 57; each has exactly one underline and a source | OK |
| Appendix sections | 18 | headings `## 1.` to `## 18.` = 18; the intro list at S 252 names all 18 correctly | OK |
| Value list rows | 23 | rows 1 to 23, rows 8 and 9 "not used" | OK |
| Go items / money items / rules / ban list / submissions | 9 / 6 / 15 / 13 / 13 | go list 1 to 9, money rule 1 to 6, rules 1 to 15, ban items 1 to 13, submissions 2 + 10 + 1 = 13; checksum "8 groups of 8" = 64 characters | OK |
| Stop words | five, order 1 to 5 | Key exposed, Emergency cancel, Time, Freeze, Stop; "LOWER order number wins" present once in the table heading and card | OK |
| Dates | Mon 16, Wed 18, Mon 23, Wed 25 Nov 2026 | computed weekdays: Mon, Wed, Mon, Wed | OK |
| 18:29 UTC | = 23:59 IST (23 Nov) | 18:29 + 5:30 = 23:59 same day | OK |
| 15:00 UTC | = 20:30 IST (25 Nov) | 15:00 + 5:30 = 20:30 | OK |
| Worked example S 262 | 0.27 per call, 0.81, 13.21, rise 0.80 ok, 0.90 over | (40,000 x 3 + 10,000 x 15) / 1,000,000 = 0.27; 3 x 0.27 = 0.81; 12.40 + 0.81 = 13.21; 3.90 - 3.10 = 0.80; 4.00 - 3.10 = 0.90; Decimal calculator printed 0.27 | OK |
| OI-19 "860 s" | v3 line 171 | inputs/OWNER-STEPS-realrun-v3.md line 171 says "about 860 s (about 14 minutes ...)"; proposal 15 minutes is at least 860 s (14.3 minutes) | OK |
| OI-13 / Q21.2 | ORDERS Q21.2: no takeover after lease unless file says | ORDERS.md line 151 says so; Text B (plan-v10 456 to 459) says re-claim up to three tries: the contradiction is real | OK |
| OP B.3 / DECISION-one-store line 14 | still says "ONE database" | inputs/DECISION-one-store.md line 14 starts "ONE database for everything we own" | OK |
| OP B.4 US$180 vs 189 | sources disagree | FACTS "US$180 of 189 in-code backstop"; AGENT-SCOPE "backstop setting, US$180 of 189"; neither is in S (grep "US$18" in S = 0) | OK |
| OP B.6 / Q20.3 | take key read-only line | ORDERS line 147 Q20.3 | OK |
| CH CI-12 / Q18(3) | one sheet | ANSWER-Q18-lead.md (3) "YES: collapse ... ONE who-types-what sheet" | OK |
| CH SE-N5, ST-11, ST-13, ST-14, AD-9, AD-19, AD-22, AD-27, AD-28 | text present | S line 40 (cancel text), 237 (card F.2 sentence), 85 (`TZ=UTC`), 263 (Decimal), 238 ("0 is the usual sign of success"), 58 ("not a public claim"), 154 + 112 (key deadline at or before money stop), 105 ("do not click show token"), 240 and 355 (cap of four, shape check) | OK |
| CH "ledger code" and "retake count" removed from owner text | removed | grep in S = 0 (only CH mentions them) | OK |
| S cross references | appendix 1 to 18, rows 1 to 23, rule 1 to 15, step refs A.0 to I.7 | check-v16.py section 7 passes; I also read each by hand in S 1 to 417: all point to existing sections | OK |

## What I did not check
- Any command, click path, screen, program, flow or take script (none exist in this checkout; the sheet marks them UNVERIFIED).
- AD-36 ("already closed in v15"), AD-18, AD-37 against the v15 files: only the CH wording was read.
- The check-v16.py logic itself (forbidden-pattern list, regexes) beyond running it and reading it once; the claim "no invented numbers" rests on its regex list.
- Whether the 38 OP rows repeat the sheet's text word for word (I compared meaning for OI-1, 3, 5, 10, 13, 19, 22, 23, 28 only; the script checks only that each row exists).
- Any bible R-number (the bible is not in this checkout).
- Files other than the four review inputs: ORDERS.md and inputs/ were read only at the lines cited above.

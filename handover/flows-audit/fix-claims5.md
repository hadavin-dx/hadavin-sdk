# fix-claims5.md: claims table round 5 fixer log (2026-11-16)

Role: FIXER, static edits only, nothing run against n8n, Postgres, HubSpot or the network. Only CLAIMS-TABLE.md edited (backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-claims5.md). Round 5, non-security path: Blockers and Majors only.

Finding: both review files quote line numbers and wording of an older copy of the table. I opened each cited source and checked the current table; about half of the Majors were already fixed in the current text.

## Counts (python3 claims-count.py CLAIMS-TABLE.md)
- Before: SUPPORTED 124, RELAYED-ONLY 69, OVERSTATED 54, UNSUPPORTED 29, UNTRACED 51 = 327; lanes A 97, B 226, X 4; to-do rows 87; offenders 0; ids 327 unique 327.
- After: SUPPORTED 123, RELAYED-ONLY 72, OVERSTATED 55, UNSUPPORTED 29, UNTRACED 48 = 327; same lanes, 87 rows, 0 offenders, 327 unique.
- Cause: A-010, A-045, A-074 UNTRACED -> RELAYED-ONLY (3); A-039 SUPPORTED -> OVERSTATED (1). All count sentences updated (top, "What this file is", "What failed", "Count", lane A verdict counts 33/27/13/20/4, "Before filming" lists and "7 + 44 = 51" -> "4 + 44 = 48", the 80/50 script note -> 81/47, 95 -> 96 claims in the tables, 232 -> 231 without a row). Lane B counts (90/45/16/35/44) recomputed and unchanged.

## Facts review (3 Majors)
1. Row 33 (contacts): partly untrue as quoted. The text "does not remove ... unless F-01 has landed" is not in the current table (grep: 0 hits); the replacement already follows decision 2 and Q13 (read-only, never deletes, "statement by the lead, lead verifies at re-pin"). TRUE part fixed: the claim "only ORDERS.md:82 says they stay" was wrong in two places (row 33 why cell, "What failed" paragraph): ORDERS.md:82 says they stay only unless the F-01 fix lands; decision 2 (DECISIONS-2026-11-16.md item 2) and Q13 (ORDERS.md:110) say it without condition. Added a hedged other-branch text to row 33 for the case the re-pin check finds the take script does remove contacts. B-215 cite narrowed to ONS:103 (:112 only says the owner deletes leftovers). Checked OWNER-STEPS-realrun-v3.md :103, :104, :111-112 myself.
2. Rows 2 and 5, example.test vs example.com: true. Source: OWNER-STEPS-realrun-v3.md:107 says the take uses example.com ("not example.test"); VIDEO-RUNSHEET.md :8, :31, :55, :68, :87 and the film flows (B-154, PLAN:126) use example.test; the take program is absent, so unchecked. Row 2 note told the agent to paste example.com while also saying RUNSHEET-WORDING names no domain: fixed, no replacement names a domain now; row 2 "why" hedged; row 5 note points to row 2; B-216 carries the reconciliation.
3. Row 21 and OWNER-STEPS:107 item (5): true that no lane row covers it (B-216 is :108). Row 21 now lists :107 item (5) in the claim-ids cell as covered here (no lane row), quotes its own wording ("the table screen: lead keys only"), and says both files are wrong the same way (n8n-table-screen-v2/README.md:14 reads six columns). No new row added (counts stay 87 rows).

## Reader review (14 Majors, reader opened no sources)
1. Same claim, different verdicts: "lease plus 25 to 30 s" is already UNSUPPORTED in A-017, A-051, B-032, B-056 (all four checked); B-183 and B-189 both UNSUPPORTED; stale in the review. TRUE and fixed: "n8n keeps the request" was UNTRACED (A-010, A-045, A-074) against RELAYED-ONLY (B-086, B-126, B-140), all from the same relayed T7b/HB171 number; the three A rows now RELAYED-ONLY with the F-008 two-states note; glossary sentence and the A-053 cross-reference updated.
2. Row 16 vs B-137/B-140/row 6: true as a gap. Row 16's replacement already says "may keep"; added to the note that it holds with saving on or off (B-137, B-140, relayed) and that row 6 only concerns the run list on screen.
3. Row 33: see facts 1 (the quoted "unless F-01" text is not in the current table).
4. Row 2 "example.test": the quoted replacement is stale (current replacement names no domain); real conflict fixed, see facts 2.
5. B-219 is already OVERSTATED with the three untraced clauses named; the "Rule break" labels on B-027 and B-203 do not exist in the current table (grep 0). Rejected as stale.
6. Lane vs table wording: the file already said "Tables 1 and 2 win" at both verbatim lane headers; strengthened to cover verdicts and RUNSHEET-WORDING.md strings. A-039 was SUPPORTED while its own cell said "one alert" can be two (B-077 OVERSTATED): now OVERSTATED, added to row 11 (new replacement "No second lead mail in this run."; the scene 9 title at VIDEO-RUNSHEET.md:38, which the reader and an older note call scene 8, is scene 9). B-102 cell now says the relayed count only and that "exactly 1 alert" as a rule is OVERSTATED. Rows 30, 62, 71 already say the alert can come again (no "normally one"). A-051/row 15 and A-025/A-026/row 20 differ in sentence, not in verdict; covered by the Tables-win sentence.
7. Row 25 "144.2 to 144.4 s without n": no such text in the current row (it says one run, 144.3 s). Stale.
8. Rows 44, 45, 36, 37 rewrite requirements: current notes already say "this row says what the flows really do; if the lead wants the requirement kept, the flow is changed instead (lead decides)". Stale.
9. K3B/K3 tied to P1 without explanation: row 23 note explained it; A-021 did not. Added the explanation to A-021 (P1 = stand-in mail drop = the same event as K3B/K3).
10. Double-meaning words: all were defined, but spread over "Quick words" and the glossary. Added one short plain-word block at the top ("Short glossary of words that have two meanings ...": the lead, v3 to v5 and the two v4 leases, F-001/F-008 vs F-01, lane3, P/R keys vs P1 to P4c vs R1 to R3, claim/check/tick/test, stage vs OutStage, scene numbers and FINAL scene 4). R1 to R3 checked at lane B part 4.
11. Roles: same block names cloud session, demo session, builder, reviewers, folder reviews-f1, queue items F1 and C4. Row 43 current words really read "stated by the lead" in n8n-owns-vs-desk-owns.md:4 (checked); no change needed. The claim that no row is marked reviewed or not stays true and is now in the block.
12. Row 36 not in claim form: it has quoted current words, a plain replacement and the instruction in the note cell. Rejected.
13. Undefined references: "17:05Z", WP1/WP3b/WP4, hot/warm/cold, PUB, KS n=2, OwnsClaim1 are in the new block (they were also in Quick words).
14. Rows 72 to 77: row 72 current text already carries the noun; Table 2 intro already says the verdict is the first word of the "why" cell for rows 72 to 77 and in the lane row for 41 to 71. TRUE part: row 74 "0 of 15" with "no effect" undefined; added the file's own wording (n8n-published-numbers.md:20: "kill rows where no client lost its connection", 0 of 15 for a, c, d; b 0 of 13 valid) to the row note.

## Nits skipped (round 5 rule)
Reader 15 to 25 (row 48 listing, row 3 D1/D2, "checks every sentence" wording, line 37 cites of UNTRACED rows, "Verified" wording, B-168 cite, STALE word, round history in note cells, plan-future rows rated as present tense, row 36 :23/:26, row 17 leases untested) and facts Nits 4 to 7 except: Nit 7 (ORDERS.md ambiguity) was fixed on the way (the "flows-audit/ORDERS.md" path is stated in the new text). Not listed as fixed: facts Nit 5 (B-214 UNTRACED), Nit 6 (A-021 label).

## Gates (from handover/flows-audit)
- python3 -I tools/check_secrets.py: exit 0 (PASS 0 hits in 1848 files)
- python3 tools/check_refs.py: exit 0 (PASS 5168 references)
- ruff check .: exit 0
- ruff format --check .: exit 0 (564 files already formatted)

## Not checked
Take scripts (absent), the flow JSON, relayed numbers, the whole of lane B beyond rows named, the Index by file after the A-039 move into row 11 (row 11 was already listed under VIDEO-RUNSHEET.md). No run of anything. Nothing committed.

## Needs the lead
- Confirm A-010/A-045/A-074 as RELAYED-ONLY (it moves 3 claims; the alternative is to put B-086/B-126/B-140 to UNTRACED).
- Re-pin check of the take scripts (contacts: removed or left) still outstanding; row 33 now has a hedge for the bad case.
- Which domain the take uses (example.com per ONS:107 against example.test in film flows) is open until the take config is read.
EOF

# Claims table, reader review r5, lines 134-759 (egm-comprehension style stranger read; agent a0659b2b)
Saved by flows-audit, condensed; every finding kept. Reviewer words are unverified until checked. Reviewer opened NO source files: it checked internal consistency only. Lines 1-133 read for context only.

Not checked by reviewer: source files cited by rows; any quote, line number or verdict against its source; count scripts; the "15 added on purpose" list; Index by file (spot check matched); relayed numbers; correctness of SUPPORTED rows. Lane totals A 97 + B 230 = 327 agree by arithmetic.

Is the second half a stale duplicate? No: "LANE A (verbatim)" (line 212) and "LANE B (verbatim)" (line 376) are the first-pass source tables the A-/B-/X- ids point to. They are not marked as older. Suggested fix: one sentence at line 212: "pasted first-pass lane reports; where wording differs, Tables 1 and 2 win."

## Major
1. Same claim, different verdicts: "lease plus 25 to 30 s" UNSUPPORTED in A-017/A-051 but OVERSTATED in B-032/B-056 (lines 266, 300, 450, 474); the definition (lines 53, 230) says UNSUPPORTED = files contradict it; A-097 was moved to OVERSTATED for that reason. B-183 UNSUPPORTED vs sibling B-189 UNTRACED. "n8n keeps the request": A-010/A-045/A-074 UNTRACED, B-086/B-126/B-140 RELAYED.
2. Row 16 (line 139) says say nothing more about what n8n keeps, but B-140/B-136/B-137 (lines 582-586) say name and e-mail reach n8n's database even with saving off; B-125 rates it UNTRACED; row 6 says run list would be empty.
3. Row 33 (line 156) asserts "script does not remove the take's made-up contacts unless F-01 has landed" while line 13 says unknown; cite conflict with B-215 (:103/:112 vs :104/:112); replacement not hedged.
4. Row 2 (line 125) replacement "All leads are made-up people on example.test" contradicted by B-216 (line 686): OWNER-STEPS:108 names take-<id>-a/b/c@example.com.
5. B-219 (line 689) rated SUPPORTED but three clauses are UNTRACED ("caps the spend", "asks the model once per lead", "counts ... on its own credentials"); public post text; no to-do row. B-027 and B-203 labelled "Rule break" (lines 445, 713) with no row.
6. Lane wording vs table wording disagree and the file never says which wins: A-051 (line 300) median 60.8 s max 61.9 s vs row 15 "no estimate is quoted"; A-025/A-026 vs row 20 (lines 274, 275, 143); A-039 "One alert mail" SUPPORTED vs rows 30/62/71 "normally one alert"; scene 8 title R:38 "one alert, no second mail" no row; line 720 RUN-ON-LAPTOP:63 "exactly 1 alert" OVERSTATED vs B-102 RELAYED, no row.
7. Row 25 (line 148) "lease 120 s, 144.2 to 144.4 s" with no n; A-020/A-070/B-035 say n=1; a range cannot come from n=1.
8. Rows 44-45 (lines 175-176) rewrite requirements (AGENT-SCOPE:6 "capped at 3" -> "no cap on tries"; "MUST NOT process the same lead key twice" -> "send the mail twice") in coordinator decision files; row does not say whether the flow should be fixed instead. Rows 36/37 same kind.
9. Row 23 and A-021 (lines 146, 270) tie kill case K3B/K3 to check P1 (stand-in mail drop, line 77) without explaining the link.
10. Words with two meanings: "the lead" (coordinator / sales lead / lead record), row 43 puts "stated by the coordinator" in the current-words cell though the real file says "the lead" (B-182); "v4" (120 s vs 45 s lease); F-01 vs F-001; "lane3"; P (page-statements key) vs P1-P4c; R run-sheet key vs rules R1-R3; claim (sentence / database step / row / 720 s window); check; tick; stage vs OutStage; scene numbering (row 22 "FINAL scene 4"; row 1 "scenes 5 to 11", scene 11 undescribed).
11. Roles undefined: "cloud session", "demo session", "builder", "reviewers", "folder reviews-f1", "queue item F1/C4". Line 15 says verdicts not named in review notes are first-pass readings, notes not in file; no row marked reviewed or not.
12. Row 36 (line 159) not in claim form: unquoted current words; replacement mixes text with an instruction.
13. Undefined references: "17:05Z" (authority for rows 9, 15, 22, 25; no date or file); WP1/WP3b/WP4; hot/warm/cold; PUB and n8n-published-numbers.md; "KS n=2"; "OwnsClaim1".
14. Rows 72-77 (lines 203-208) not understandable alone: row 72 drops the noun (B-185: bursts clean at one CRM row and one email); row 74 "0 of 15" does not say good or bad; Table 2 gives no verdict for rows 41-71.

## Nit / Minor
15. Line 120 lists row 48 among Table 1 rows; it is in Table 2 (line 179).
16. Row 3 needs only D2 (line 126) vs line 72 rows 3, 25, 27, 28 need D1 and D2; line 22 omits row 3 from D1 list.
17. Line 5 "checks every sentence" vs line 403 skips stage directions etc.; B-109..B-120, B-221..B-223 inflate the "69 RELAYED-ONLY" headline (line 9).
18. Line 37 states what the 6-digit challenge blocks, citing B-205/B-212 (lines 675, 682) which are UNTRACED.
19. A-004/B-071 UNTRACED yet line 14 uses them (hedged correctly). Line 232 ends "Verified", A-096 (line 344) says "verified", nothing ran.
20. Line 758 cites B-168 for "lease plus 25 to 30 s" but B-168 is "about 30 s" latency; B-032 is the lease row.
21. Part 5b (lines 730-742) uses "STALE" as a verdict, not in either verdict list (lines 53, 402); B-093..B-095, B-130 use UNSUPPORTED with "Stale".
22. Rows 11-13, 18 carry round history in the "note" cell (line 141: "Round 4: line numbers crossed"); line 62 long count history. Note column is defined as an instruction (line 69).
23. Lane B rates plan-future sentences (B-015..B-025 UNTRACED, B-054 UNSUPPORTED) as present-tense claims (header line 416 admits); row 52 (line 183) turns a planned test into "not yet run".
24. Row 36 says only :26 calls the decision an aim (line 159); line 702 cites :23 and :26.
25. Row 17 (line 140): "leases other than 20, 45 and 120 s" not tested; those three rest on relayed numbers (row 25), row does not say so.

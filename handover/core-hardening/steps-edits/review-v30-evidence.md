# Owner sheet v30 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: evidence-v30-independent/ (00-TABLE.md, out-*.txt, hashes-*.txt, indep30.py, hostile30.py). Recorded, not judged.

## Failures and deviations first
1. Mutation H06 NOT caught: adding `the lead sends the owner the words "cancel the older key now"` to the lead-note source: check-v30.py rc 0. C188 matches only the exact old text; other wording passes (the exact old wording, H13, is caught).
2. Mutation H09 NOT caught: one of the five `[LEAD FILLS at re-pin: ...]` placeholders changed to `[LEAD FILLS: ...]`; checks only test that the spelling exists somewhere.
3. H15 missed but not a checker gap: fact `ls_t` is used in no source, so the mutation changed no page.
4. The pair 18:00 UTC = 23:30 IST appears on no v30 page (v30 uses 18:04 for the 23 Nov latest start); 18:19 = 23:49 and 18:04 = 23:34 are in lead pages only, not in any owner page (matches security M1). 18:29 = 23:59 is in the owner pages.
5. Secret scan: 2 email-shaped hits, both a masked example (`de...1@...` at OWNER-APPENDIX-v30-A line 71, B line 69). `sk-ant-api03-` shape built from parts: 0 hits; all other patterns 0.
6. Another process (the stop-hook wip commits) committed the evidence folder; evidence-r15-runner files changed by another agent, not this runner.
7. The runner's first pass had 6 false FAIL lines (searched owner pages only; flagged explanatory placeholder text); fixed in its script.

## Results
- build-v30.py rc 0 (9 files), hashes identical before and after; check-v30.py rc 0 "0 failure(s)".
- mut30.py: 209 plants, 208 caught, 0 missed, 0 anchors not found (the control prints MISSED as it must). v30-fail-proof.py: Part 7 (C185 to C209, 23 checks) fails on built v29 in 23 of 23, on v30 in none.
- Words: sheet A 6,285, B 6,097; card A 1,777, B 1,711; appendix A 3,950, B 3,881; film page 442; lead note 12,837; open list 7,527.
- 117 UTC/IST pairs, 0 wrong, 0 unpaired; 65 weekday-date mentions, 0 wrong. Both placeholder spellings present in A and B (4 and 5 each). "cancel the older key" in lead pages: 3 mentions, descriptive (crude heuristic; see I05 in out-indep30.txt). All 10 distinct appendix pointers resolve in A (36 mentions) and B (34). Rebuild into temp folder: all 9 files byte-equal. Banned scan 0 hits over 20 files.
- 15 hostile mutations: 12 caught, 3 missed (H06, H09, H15), 0 anchors missing.

## Not checked
Whether the sheets are understandable or correct for a real person; vendor claims (UNVERIFIED in the sheets); text outside the 9 pages and listed scripts; ruff, pytest, bandit.

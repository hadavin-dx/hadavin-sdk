# Fresh read of r38 rows P98-P114 (RUNBOOK-V4.3-PATCH.md lines 287-311) vs inputs/lead-reviews/LANE-D-13v.md. No Blocker, 3 Major.
Quoted strings identical to the lane file: P98-P103 (items 2-5), P105-P109 (clean-up item 1, contact line), P111, P113. P110, P114 paraphrased and correct. Items 1-5, X-1, X-2, X-3, N1, N2 all covered.
MAJOR
1. P104, P112, P109 say "cut off in the lane file". It is not cut off. Lane file never gives the item-6 masks sentence (item 3 only says "masks sentence (see X-3)"); P112: only the words "(an estimate)" exist; P109: "..." after "N contact(s):" is a list placeholder, and the row contradicts itself. Reword all three: "the lane file does not give this text".
2. "lead" has two meanings in P102 and P113 (notice: made-up sales enquiry; elsewhere: project lead). Use "made-up contact" / "test contact" in notice text candidates where the lane text allows, and where the text is a quote, add a note "lead here = made-up sales enquiry". Notice also mixes people/leads/persons.
3. P102: "at most 3 calls" beside "does not limit the model calls" reads as contradictory and never says who limits. Row says it "replaces what rows P96 and P113 offer" but P113 is not replaced: P96, P102, P113 are three CANDIDATE texts for notice item 1. Say so plainly.
MINOR
4. P112: the string `...the take needs about 49 minutes before it (estimate)` is our construction, not a lane string; do not put it in backticks beside exact strings.
5. P113: label "LEAD-SUGGESTED" is wrong; lane D suggested it (X-2). "the lead has not accepted it" is unverifiable: remove.
6. P100: "Same text as in row P10" -> "same as P10, plus the 'refused: ' prefix" (P10 has no prefix).
7. P101: "A twice, B ten times at once, C once" does not define A, B, C; "take id" / <tag> / TAKE_TAG are three names for one thing (say so once); "type it, a space and the take id" is ambiguous.
8. P99: lists "an existing file" under "result.json was not written" (exit 3) while P100/X-5 say an existing result.json is refused earlier with exit 2. Say which case applies when.
9. P103 item 2: "you delete them by hand" vs master sentence "by a filtered list": add pointer to P109's filter.
10. P96 quoted limit sentence differs from P102/P113 wording: note it (P96 pending r37).
11. P82 and P109: owner has two filter texts (email contains <KEY_PREFIX> and take-<tag>-a/-b/-c); add a line that they must find the same contacts (UNVERIFIED).
NITS
12. Undefined words for owner: hard links, /mnt, tag marker, spent, in flight, "(example.com)", "the HubSpot screen": add a plain gloss in the row note (not inside quotes).
13. P98: "(worst case)" overstated (X-1); "49 minutes before it" does not say before the window end. P98 formula/arithmetic OK (2900 s = 48.33 min, up 49).
14. P114: "BURST_N=10 is a lead decision against validated config" ambiguous: write "versus". Mark "DO NOT WRITE any new number" as OUR inference, not lane text. N1 is an owner question, not an instruction to the owner.
CONFLICT (Major) 15. P63, P64, P65, P45 START DEFINITION say the program accepts a start up to 17:40Z and "start" is after the typed answers. P98 says the 49-minute check runs twice (config phase before the y prompt, and again after confirmation). If typing takes ~5 min, a 17:40Z launch fails the second check. Add a note to P63-P65 and P45: "accepts a start up to 17:40Z" is true only for the first check; re-pin when r41/lane D confirm. UNVERIFIED.

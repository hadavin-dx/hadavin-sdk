# v25 changes (builder, Mon 16 Nov 2026). Failures and gaps first.

## NOT fixed, not shown, or not decided
1. Nothing here was run on real vendor pages, buttons, Windows, WSL, PowerShell or n8n. All of it stays UNVERIFIED. The only things run are the build, the checker, the planting test, `bash -n` and the arithmetic (evidence-v25/).
2. No independent review of v25 has happened. The builder cannot start the EGM review or the evidence runner from this role: the lead runs both on the built files. The v24 reviews were read, not repeated.
3. Word limit: met, but thin. Sheet A has 6,495 words and B 6,467 (limit 6,500; check C07 fails above it). The fixes added about 750 words; wording was cut to pay for them. Nothing was moved to the lead note to make room. Cut items are listed under Cut in v25 below.
4. Decisions that stay with the lead and the owner: sheet A or B (Open 71), the 7 day rule of A (Open 78), B always cancels the older key (Open 79), a smaller balance (Open 77), a short phone walk-through because the sheet is not a one-person job (Open 80), M2 and M3 (Open 72 and 73). ORDER 034 is not shown as met.
5. Stranger blocker 6 (the whole balance is the exposure) is flagged, not changed: decision Q24 keeps it (Open 77).
6. The checker tests listed properties, never meaning. The 15 plants of the independent run are now caught (C48 to C60 and C61), but a different wrong figure in a place no check watches would still pass. Pointer check C19 compares each pointer with pointers-v26.txt; I read the new pointers (about 90) in their sentences, nobody else did.

## Independent run of v24: the 15 plants check-v24 missed
check-v24 caught 10 of 25 plants. For each of the 15 missed ones there is now a check, and mut26.py plants it again against v25 (Q01 to Q24 in evidence-v25/20-mut26-first.txt: 15 of 15 caught, each by its own new check).
| Plant | What it changed | Check now | Fails on |
|---|---|---|---|
| Q01, Q02 | wrong price per call, wrong total 0.84 | C48 allow-list of amounts in the sheets | the plant |
| Q03 | sample output tokens | C49 allow-list of numbers with four or more digits | the plant |
| Q08 | STOP RULE step 1 deleted | C50 exact STOP RULE order | the plant |
| Q09 | stray backtick | C51 even backticks on every line | the plant |
| Q10 | card cancel step changed | C52 exact card step 3 | the plant |
| Q11 | card trigger (f) deleted | C53 triggers (a) to (i) all present, in order, (f) exact | the plant (and v24, which lacks (i)) |
| Q12 | auto-reload off flipped to on | C54 exact R4 sentence, and no auto-reload on | the plant (and v24) |
| Q13 | secret-shaped text | C55 patterns for key-shaped and long random text | the plant |
| Q15, Q16 | sample give-up and silence minutes | C56 exact sample line | the plant |
| Q18 | one delete domain changed | C57 exactly 3 `@example.com`, no other example domain | the plant |
| Q20 | note limit 13.12 | C58 note sum literal and 13.xx allow-list | the plant |
| Q22 | exit codes widened | C59 exact sentence | the plant |
| Q24 | R8 four words, five listed | C60 count of listed words equals the number said | the plant |

## Findings of the v24b reviews: finding, fix, check that fails on v24
Checks C26 to C47, C61 to C63 live in newchecks-v26.py. evidence-v25/10-v24-fail-proof.txt runs them on the v24 built files: C26 to C48, C53, C54 and C61 to C63 fail there (the exact list is in that file); C49 to C52 and C55 to C60 pass on v24 because they guard against new mistakes (their plants are in mut26.py).
| Finding | Fix | Check |
|---|---|---|
| Security major 1: lead text typed into WSL unchecked | R6 shape check: start line starts with fixed words, paths only letters, digits and `/ . _ -`, a path starts with `/home/`, none of the listed characters or a backtick | C26 |
| Security major 2: B lets a valid key outlive the deadline | B always cancels the older key in 8.6; R4, card (b) and the yes say the card does not stop it | C27, C61 |
| Security major 3: older key text on screen, no-key path | card trigger (i); card step 2 says N is the count now and K is 1 for the older key; sheet 8.2 no-key path cancels nothing the owner did not make, it only describes such a key | C28, C63 |
| Security minor 2: key list time zone | blank on the card, sample line, compared at 6.3 | C29 |
| Security minor 3: key text pasted as a name | describe only that it is a long random text | C30 |
| Security minor 4: B proof for the older key | 8.6 uses the card steps 2 to 4 (row gone also passes) | C31 |
| Security minor 6, stranger secret on screen | 5.7 grep cut to 60 characters, `clear`, close that window, then FREEZE | C32 |
| Security minor 7: Gmail conversation view | R7 asks for list view with Conversation view off | C33 |
| Security minor 8: stale and rotate wording | note and open list rewritten (items 6, 8.4 template, rows 2, 31, 62); sheet 8.4 never rotate | C44 |
| Stranger B1, B2: the sheet depends on a message the owner cannot get | glossary Model account; set phrase asking for the numbers message at 5.1; other channel; People, Recording tool, Posting place, Model settings file in the sample | C34, C37, C39 |
| Stranger B4: tell has three meanings | Send and Describe defined once; no tell anywhere | C35, C36, C43 |
| Stranger B3: 5.7 path undefined | model settings file slot in the numbers message sample | C39 |
| Stranger B5: older key irreversible in A | A refuses when the key was used in the last 7 days (the last-used time is in the yes) | C62 |
| Stranger majors: UNVERIFIED rule, FREEZE resume, card used before defined, give-up and latest start defined late | glossary and card words reworked; tolerated items; the run ends after the card when a key was alive | C35, C40, C42 |
| Stranger minors: Gmail roles, 5.3 pass test, exit code first used in R10 | receiver and sender roles; the Windows page shows the values; R10 now points to 7.9, where the exit code is explained | C38, C41 |
| Mid-task order of the coordinator | checks for the 15 plants | C48 to C60 |

## Cut in v25 (to pay for about 750 added words; no safety step was dropped, explanation was)
The sample notice line; the sentence that a paid key left alive costs money (the STOP RULE says it); the sentence on the only copying the owner does (6.4 says it); the pointer to check 1 of section 3 from the glossary; the phrase that figures never change after the start; several shortened glossary and row sentences; the lead-side sentence in section 9 about when the lead says post. If the lead wants any of them back, one must be cut elsewhere (Open 75).

## Lead note and open list
The note is now version 9: a new section Added in v9; items 6 and the clean-up template fixed; section 4 and 8 describe both older key routes. The open list has rows 77 to 81 and rows 2, 31, 62, 70 and 75 corrected.

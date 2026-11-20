# Root docs style review 3 (fresh, style, read only): NOT clean. 0 Blocker, 8 Major
1. SECURITY ~11 vs 13-22: note says "secret finder" here and "redactor" in README/CHANGELOG, then Part 1 says "redactor" five times: use "secret finder" in 13-22.
2. SECURITY ~60 "Single breaks were run by hand (2.9)": 2.9 says nothing of it (dangling): reword (no result line on file) or delete.
3. CHANGELOG ~108 "(see the correction below)": no correction exists: replace with a pointer to SECURITY K46/K84.
4. SECURITY ~37 labels a stated decision NONE (NONE = no evidence named): use STATED with the source.
5. SECURITY ~515-519 (2.7) lead-in "Shown by tests:" above UNVERIFIED bullets (milder in 2.3 ~244-248): "Not shown by recorded tests:" / "Shown by tests, and what is not:".
6. Internal artifacts in shipped text: SECURITY ~40 "status board", ~298 "evidence file and a ticket of the text and masking team", ~39/472/564 "working notes ... not shipped"; CHANGELOG ~217/219/233 `k1b`, ~203 "Phase 4": name the source by kind and date only; K35 "the team calls this accepted; no written order found (UNVERIFIED)"; `k1b` in prose -> "the replay settings" (explain once if it is a real config key).
7. Brand strings: CHANGELOG ~23 bedrock_guardrail, ~24 slack (also ~291, 293, 304, 362, 368, 381, 411): describe by role in new text; if they are real config values state the exception once (as SECURITY ~42).
8. Sentences over 30 words: CHANGELOG ~15 (four steps in one sentence), ~29 (~120 words), ~17-20; SECURITY ~50, 110, 382, 582.
9. CHANGELOG ~5 defines only TESTED/MEASURED/UNVERIFIED/NOT RUN but ~30 "(a test pins this)" is unlabelled, ~46 and ~129 use OPEN/"Pinned" undefined: label and add PINNED/OPEN to the list.
Nits: capitalised REFUSED looks like a label (SECURITY ~70, CHANGELOG 30, 114); second "(OPEN)" on K70/K74/K36/K84, K82 PINNED with UNVERIFIED parts, K85 lower-case pinned vs status OPEN; Part 1 ~24 STATED but K84 is OPEN; SECURITY ~302 "28 of 44 ... 7 of 44 ... 19 pinned as closed" does not add up: explain the 19; README Python section (~19, 34) unlabelled; CHANGELOG 32-34 repeats METADATA_ENDPOINTS text at ~45; ~77 "TID251", ~31 "merge commit, not from a branch", no blank line before "### Upgrade steps" (~125-126); CHANGELOG ~110 "more than 256 values" vs K64 old limit gone: add a pointer.
Consistent: numbers (6 s, 4.5-5.4 s, 262,144/256 KiB, 524,288, 786,432, 2,000, 12-char base64, depth 3), the 2026-11-23 12:00 UTC default, 14 unused functions, anchor #words-used-here, batch arithmetic 6+2+1+1=10, CHANGELOG "Pin" entry.
Not read: CHANGELOG ~229-807 except grep.

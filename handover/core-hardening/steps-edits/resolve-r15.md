# Round 15 resolve note (EDITS round 15, one batched fix)

Failures and open items first.
- Not run by me: the EGM review of this result. The studio lead must run it (no EGM skill in this sub-agent run).
- Not measured: the 860 s figure is a reading of the take program, not a timing. No click path was run. No program of the take was run. The rules are text; nothing enforces them.
- Long key steps remain (word counts, E-48 new block): A 177, B 172, C 332, D 613, E 186, F 166, G 590, H 272, I 318, J 140, K 281. D and G are long; a naive reader may still find them heavy. I did not split them further.
- Studio lead must answer confirmations h, o and p in EDITS.md (the 18:00 UTC = 23:30 IST latest start moves 4 minutes earlier than the lead's 18:04 UTC = 23:34 IST).

Fixed (all findings of review-r14-security, review-r14-naive, review-r14-evidence): security M1 (only the owner's own typed message counts), M2 (shred targets, link rule with trailing `/`), M3 (latest start 18:00 UTC = 23:30 IST, margin 280 s by script), m1-m5; naive M1-M9 and minors (alarms, two HubSpot keys, `shred done` scope and silence, "Are you sure?" step, E-12 five short numbered replies, no placeholder wording, key steps A to K, no brand name, E-09 e two names); evidence: bare times given UTC and IST pairs, verify script uses paths relative to its own folder.
Also found and fixed by me in this batch: item 6 (E-59) said to delete after `shred done`, but `shred done` includes item 6's files (circular); now item 6 only needs the check, and `shred done` includes them.

Rows: 59 (new E-59, E-60, E-61); Apply now 47.
Checks: see resolve-r15-check-output.txt. New checks fail on round 14 (r15 failure count in that file). chk15.py is adapted from chk14.py with relative paths.

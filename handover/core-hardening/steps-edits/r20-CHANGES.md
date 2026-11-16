# EDITS round 20: what changed (builder report, EDITS.md rebuilt from EDITS.round19.md)

## Failures, gaps and what was NOT run (first)
- Not run: any EGM review, any independent evidence runner (the studio lead's steps), any real take, any provider click path, any spend. Nothing here is "reviewed".
- The full run of `verify20.py` with its negative controls: see `resolve-r20-check-output.txt`. If that file does not say `FAILURES 0`, this round is not clean. The run takes about 30 minutes in one piece; I report the exact runs in the handback.
- UNVERIFIED: the Google app-password page and the HubSpot private-apps page show what the identification check needs (a name and a day); I did not open them. The click path added to day-sheet item 2 is marked "not checked" in the text.
- UNVERIFIED: whether an owner who cannot tell what a credential in his own n8n holds can follow the rotate-first rule (M3); it needs a real reader.
- UNVERIFIED: the lead-facing phrases in owner text were fixed where the two reviews named them (the "studio lead" hedges, "the builder believes"); I did not scan every one of the Hold and non-key rows.
- Not changed on purpose: r18 stranger m2 ("last"), m3 ("key") and m4 (item, step, part) are only partly closed; see `r20-CLOSURE.md`.
- Slips of mine found and fixed this round: the r19 "In short" line had a double space and a missing "Then you" (found because my own check failed on it); two of my first plants did not change the text and were caught as `plant anchor missing`.

## Facts (machine-checked by `verify20.py`)
- EDITS.md lines (wc -l): 1104
- applied sheet words (wc -w): 24367
- day sheet words (wc -w): 6256
- appendix words (wc -w): 1357
- Parts of the applied sheet (wc -w): key step C (the alarms) 575 words, key step D.5 630 words, the table of typed words 606 words, the card with one-liners 752 words, key step I 408 words, key step G with G.2 1076 words, the identification check 542 words.

## What changed, by finding (the row-by-row table is `r20-CLOSURE.md`)
1. Security M1: the live key never gets a date or a later date. One sentence, copied in D.5, key step I, G.2, E-58, the day sheet.
2. Security M2: item 5 counts as done for a login with `web revokes not done`; item 1 does not wait for it.
3. Security M3: rotate first, then delete, for an item marked `used`; the sheet names the take's n8n and your own n8n as two different things; `take-only` is defined; app 2 goes into the take's n8n only.
4. Security M4 and stranger M-G: one emergency early-revoke sentence; one rule for `key gone, no more decisions` (key step B); the exceptions list names alarms 1, 3, 4, 5, the emergency and the last time to revoke; one rule for typing words exactly.
5. Security M5: five alarms. Alarm 4 at 18:24 UTC = 23:54 IST on Mon 23 Nov 2026; alarm 5 at 00:30 UTC = 06:00 IST on Tue 24 Nov 2026, always set; alarm 2 at a fixed 06:30 UTC = 12:00 IST (proposal, ND18).
6. Stranger M-A: the day sheet now holds key step B and D.1 to D.4, and says in plain words that it is not the whole retirement.
7. Stranger M-B: the real latest time to confirm in route B is alarm 1 (17:49 UTC = 23:19 IST); step 21, E-57 and K-D say it once.
8. Stranger M-C: G.2 is dated Mon 23 Nov 2026 and says how to show message times. M-D: hedges replaced by a rule (the date stands if the assistant names no other before the first take). M-F: take, cut and routes defined on the day sheet.
9. Minors: card step 1 time, E-37 count of questions, route B warning in the prompt, "In short" repaired, no line break rule, hand-written list limits, ND15 option B, round line order.
10. Lead-facing: ND18 (alarm 2 time and the Tue 24 date), ND19 (`lists written`, exact typing), ND20 (L-LEN), header count 20.

## L-LEN in plain words (section L-LEN)
ORDERS.md says: ONE sheet of at most 6,300 words, detail in an appendix, nothing deleted. The applied sheet has 24367 words, so it is 18067 words over. The day sheet has 6256 words, which is 44 under 6,300; the appendix has 1357 words.
- Option 1: cut the applied sheet itself to 6,300 words by moving 18067 words into linked appendix files. Needs row-by-row moves and the exact-copy pins rebuilt.
- Option 2: name the day sheet as the one sheet; the applied sheet stays as the detail file it links to. Needs the lead's written reading of the order.
- The question for the studio lead: "Is the day sheet, together with its appendix, the one sheet that the order means?" My recommendation: yes (option 2), because the owner acts from the day sheet and the day sheet now holds everything he types. I do not decide.

## Class fix and proof
- Class: a fix was checked only by the old pins; a new sentence had no check that fails on the old text. Fix at the choke point: `r20-section.py` lists each new phrase (need) and each removed phrase (absent) with the place it must appear; every entry is also planted (removed or added in memory) and must be caught by its own label.
- Proof that the checks fail on r19: `v20-on-r19-output.txt` (run with `EDITS_PATH=EDITS.round19.md`).

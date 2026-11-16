# v19 changes (builder, Mon 16 Nov 2026; one batched fix pass for all v18 review findings; failures first)

## 0. Failures first: what v19 does NOT settle
1. **Nothing was run or seen.** The only program I ran is check-v19.py, which checks form (ids, counts, order of terms, arithmetic of the invented examples, weekdays, UTC = IST pairs, banned words). It cannot show that a statement is true. Output: v19-check-output.txt (0 problems). I also planted four mistakes in a scratch copy (a wrong alarm time, a balance above the highest balance, a repeated rule phrase, a renamed gate); the checker flagged all four (counts 3, 2, 2, 3); the copy was deleted.
2. **The sheet is not shorter.** 102 lines against 98, about 5,250 words against about 4,250 (`wc -w`). I cut the "What you do, in this order" bullet (the order table says the same) but every other addition answers a finding (list in v19-MAP.md). Open 30 names what the lead could cut. Not fixed, only justified.
3. **Only the lead can fill:** the second way to reach the lead (Open 26), the shut-down timer (Open 27), what the take program does after an early key cancel (Open 28), the older-key statement (Open 31). With their safe defaults a run does not start.
4. **Still open from v18 and unchanged:** the take program deletes contacts today (Open 1, G1 NO); UNVERIFIED items remain (SM5 is only improved: the numbers message lists items the lead has since seen).
5. **A real example numbers message** is still invented. Its numbers are consistent (checked by the form checker): balance 189.00 is between run total 0.81 and highest balance 200; program limit 13.21 = 12.40 + 0.81; times 11:30 + 25 min = 11:55, + 10 = 12:05; IST pairs correct. The real wording of the notice, the printed result and the page words still comes from the lead (Note G17).
6. I did not read the BR-a..s lettered list file, the take scripts, the flows or the model program (not in this checkout). I did not re-verify every v18 citation; I checked the three post-by sources by line (ORDERS.md 150, OWNER-STEPS-realrun-v3.md 130, QUESTIONS.md 55) and the FACTS and AGENT-SCOPE quotes.

## 1. What changed in the sheet (OWNER-SHEET-v19.md; v18 untouched)
- Intro: "unsure" rule split before and after the paid key exists; precedence line (R2, R3, R1, R10).
- Section 1: message place (the chat where the sheet was received), second way, HubSpot, version id, fingerprint, person id, exit code, key list, key file, balance, highest balance, program limit; "Backstop" and "Credit" gone; lead "could read any file you can read".
- R2: any key made today after starting section 6, whatever its name; older key only if name and date match and the message says nothing uses it. R3: cancelled word or key gone from the list; type nothing in the take window at the alarm; lead-side shut-down. R4: whole balance is the exposure; key check at 5.6, after 6.2, at 7.1; cannot lower a balance. R6: one list of everything typed in WSL. R7: demo mails of 5.4 and the take-prep contact. R8: four words that start or end steps; charset for shell values and other values; odd message goes to the second way. R9: film only, items (a) to (f), the From column honestly. R10: only `date -u` and `ls -l` in a freeze.
- Section 3: full sample message (balance, highest balance, program limit, times with the owner's y minutes, expected counts, second way), "Reading the counts", check 6, minutes are the lead's figures. Alarm = latest start + 5 + 10 + 10.
- Section 4: "NOT safe" rows. Section 5: write down settings, anchored grep, yes line with the balance and older key. Section 6: Recall page, bash, paste once, clipboard replaced right after `exit 0`, failed save needs a new message with new times. Section 7: `end` then R3 at once, split 7.7 and 7.8, "(wanted here)", "run started" goes to the lead. Section 8: one line per key, restore the written-down values. Section 9: no UNVERIFIED label on the post-by time.

## 2. Lead note (LEAD-RELEASE-NOTE-v3.md), open items, map
- New gates G30 (shut-down at the alarm and by 18:29 UTC), G31 (second way), G32 (older key); G14 balance; G10 and Note 2 formula with Y; money words defined once; quotes fixed (FACTS line 3, AGENT-SCOPE line 15, decision 1 wording, post-by sources, DECISION-one-store CORRECTIONS).
- v19-OPEN-FOR-LEAD.md: 31 items (v18 had 25). v19-MAP.md: every v18 finding with where it is fixed, failures first; its RC-5 row no longer points to a wrong item.

## 3. Recomputed figures (by the checker and by hand)
Price (40,000 x 3 + 10,000 x 15) / 1,000,000 = 0.27; 3 x 0.27 = 0.81; 12.40 + 0.81 = 13.21. Window end - 35 min = 17:54:00; 11:30 + 25 = 11:55 = 17:25 IST; + 10 = 12:05 = 17:35 IST; on 23 Nov 17:54:00 + 25 = 18:19:00 = 23:49 IST, + 10 = 18:29:00 = 23:59 IST; 18:29:00 - 860 s = 18:14:40 = 23:44:40 IST; Mon 23 Nov, Wed 18 Nov, Wed 25 Nov 2026 weekdays right.

## 4. Not claimed
Nothing here is reviewed. EGM steps after the build (evidence runner, reviewers, resolve, drift report) are the lead's.

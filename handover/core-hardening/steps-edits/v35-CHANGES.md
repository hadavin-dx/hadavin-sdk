# v35 changes (round 7, builder evidence only)

Builder evidence only. An independent evidence runner and fresh egm reviewers must still run; nothing here is verified by anyone but me. Round 2 for the owner sheet, security uncapped.

## 1. Failures and open items first

1. NOT fixed, lead decision: stranger blocker B1 (the sheet cannot be followed alone; the five pages are still mandatory; about 15,000 words in one sitting). No page split was built. Next step: you decide the L-LEN split (open list rows 112 and 124). No word cap was raised; the five-page total fell from 15,715 to 15,577 (A) and the sheet from 6,277 to 6,274 (A).
2. NOT fixed, lead decision (open list rows): 125 exit code rule (stranger M6), 126 the day clock (a key made near the latest start; I invented no number), 127 the length of the typed yes (about 450 words), 128 next-morning alarm (security m4, recommendation only), 129 helper minutes (m5), 130 revoke-name read-back on another channel (m6).
3. NOT fixed, lead or owner: stranger B4 (three statements the owner cannot check: n8n credentials scoped, spend lock set, no model key outside the model program). The sheet already says an unchecked statement means no run; who verifies them is open list row 122. Security M3 (the film person sees the screen while a key is alive): three options are written in row 123 and I did not pick one.
4. Design choice to confirm (row 121): from alarm 5 (Sunday) the owner cancels a still valid older key at once, with no 7-day check and no wait for the lead. It is the one place a key last used within 7 days is cancelled without the lead; the sheet says so in one sentence (5.1a, 6.7, L2, the yes, appendix 10).
5. UNVERIFIED and third party: whether the model account offers a cancel-only role and whether that role can do the last-resort step (row 131); how the lead starts and stops the model program; every vendor page path and word. None was checked.
6. Stranger minors NOT touched: the 55-minute window is not checked against a real run; the "describe" template; the Gmail filter wording; 13 typed submissions against a call ceiling of 3 (the readers' judgement, not a fact I can fix in the text). Each needs the owner's dry reading of the sheet; next step: the independent stranger round.
7. Own slips: my first cut of the appendix words list removed the definition of "run name" (check C14g failed, restored); I used "tell" in the helper and film pages (check C36 failed, now "call the owner"); I put brackets inside the typed yes (check C13/C24 failed, removed); an unbalanced bracket in appendix 10 (C199, fixed). The new meaning checks found two more of my slips that no exact-sentence pin had: the old words "deadline reminders" and "live word" were still in the lead note and open list (C277, fixed).
8. Heavy runs: mut35.py and v35-fail-proof.py waited in heavy-slot.sh because the three machine slots were held by other jobs; see section 5 for what ran and its exit codes.

## 2. Reading load (wc -w, split on spaces; check C07 and C273 print the same)

| Page | v34 A | v35 A | v35 B |
|---|---|---|---|
| Sheet | 6,277 | 6,274 | 6,071 |
| Card | 2,211 | 2,256 | 2,154 |
| Appendix | 5,753 | 5,454 | 5,375 |
| Film page | 577 | 608 | 608 |
| Helper page | 897 | 985 | 985 |
| Total, five pages | 15,715 | 15,577 | 15,193 |

Caps: C07 and C273 now require the five-page total below 15,715 (was 15,722); the sheet cap 6,286 for A is unchanged. Nothing was raised.

## 3. Findings and fixes

| Finding | Fix | Check |
|---|---|---|
| Stranger B1 boundary at exactly 5 minutes | one rule: the Enter-by time = latest start minus 5 minutes (sample 11:25 UTC = 16:55 IST); Enter at or before it; used in the card words, W5, 6.2, 6.6, 7.3 | C274 (reads the facts and the structure) |
| Check 2 on Sunday | the older-key time must be before alarm 5 (18:09 UTC = 23:39 IST) | C275 |
| Sunday reminder wording, deadline reminders | alarm 5 (Sunday) and alarm 6 (Monday); the backstop time is ten minutes after either | C277, C187, C210, C232 |
| W1 and W2 normal steps shown as danger signs | planned moments P1 and P2; danger signs W3 to W9; the card says nothing is missing | C276, C237, C53 |
| Security M2: 7-day rule against 7.11 | one sentence: the rule only decides whether sheet A may cancel the older key at 6.7; it never stops 7.11 | C261, C182 |
| Security M1: helper standing access | the helper calls the owner back on the paper's number; acts only on a key the owner names that is on the paper; the paper may say none for the last-resort step; the owner removes the cancel-only role and voids the paper at 8.7 | C278, C230, C249, C267 |
| Security M3: film person exposure | options only, not picked (row 123); the film page defines the editor and says to check microphone and sound are OFF | C279, row 123 |
| One word, one meaning (deadline, key, valid, card, none/never, live) | defined once; "live word" is "current state word"; none/never/unknown defined once | C277 |
| Pointers: R8, appendix 7, check 2 sum 30 | R8 now carries the typing list; the sum is written inline (30 = 5 + 15 + 10) | C19, C236 |
| Lead note title and stale line | title v19; section titles re-numbered; helper row added to the secrets table | C248 |
| Section 9 and 10 loop | section 9 carries the posting rule itself; section 10 is the film rule only | C279 |

## 4. UNVERIFIED (kept from earlier rounds, nothing new checked)

Every vendor fact (the model account key list, roles, prepaid page, the cancel confirmation box, the clipboard behaviour of the terminal, the phone alarm behaviour) is UNVERIFIED. The lead statements on row 122 are UNVERIFIED by me.

## 5. Evidence (builder's own; the independent run is the lead's)

See evidence-v35/ for the raw output files and the commands:
- python3 check-v35.py: 0 failures after the edits (C01 to C280). After the source edits and before I updated the pins it printed 267 FAIL lines (stale pins, ledgers and the new content), which I fixed or re-pointed one class at a time.
- mut35.py (308 plants, 32 of them re-pointed to reworded anchors, 8 new plants AC01 to AC08 for C274 to C280), v35-fail-proof.py and gap-proof-v35.py: results in section 6 below, written after they ran.

## 6. Heavy-run results

(filled in after the runs; if a run did not get a slot this says so)

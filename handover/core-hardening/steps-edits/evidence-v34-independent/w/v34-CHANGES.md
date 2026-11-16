# v34 changes (round 6, builder evidence only)

Builder evidence only. An independent evidence runner and fresh egm reviewers follow; nothing here is verified by anyone but me.

## 1. Failures and open items first

1. NOT fixed: stranger blocker B1 (the sheet cannot be followed alone; about 45 pointers; the five pages are mandatory). It needs the L-LEN split (open list rows 112 and 120); I did not build it. The five pages are lower than v33 (see section 2), but they are still long: the five pages hold 15,715 words on sheet A.
2. NOT fixed, lead decisions (open list rows): 116 exit code rule (stranger M6), 118 the day clock (stranger M2: a key made near the latest start cannot reach Enter in time; I invented no number), 120 yes length, tolerated-items placement and reading load (M5, M8, M9). Stranger minors not touched: letter row mismatch, words with several meanings, Gmail filter wording, 13 submissions against call ceiling 3, allowed typed characters, the film person while the key is alive, 7.6 tab budget, alarm 4 position.
3. Design choices I made that the owner or lead must confirm (row 119, row 117): the helper holds the last-resort step on its paper (or none) and acts on it after a second failed cancel; the helper paper has two blanks at hand-over (cancel button word, cancelled word) that the owner phones after 5.9, and until both are written the helper acts only on the owner's call or at a backstop time; a missing Recall page is no longer a stop (UNVERIFIED that no page means no Recall).
4. UNVERIFIED and still open: whether the model account offers a cancel-only role and whether that role can do the last-resort step; how the lead starts and stops the model program; the vendor page paths. Nothing was run on a real service. No commit, no push, no spend.
5. Own slips: my first edit of the lead note pointed to a section number the pointer ledger did not know (caught by C19, fixed); my first helper-page text broke the "exactly four triggers" check C230 (caught, reworded); two plants (P30, M28) lost their anchor because I removed the text they changed (re-pointed, see section 3).
6. A person (me) read each pointer and fact-use diff before accepting the ledgers: 7 new pointers all name steps and rules that exist (5.1, 5.6, 5.9, 7.6, 7.9, 7.11, R8); fact-use rows changed for ek, last_day, ph_cf and rv22 because of the edits.

## 2. Reading load (wc -w, split on spaces; the checks print the same)

| Page | v33 A | v34 A | v34 B |
|---|---|---|---|
| Sheet | 6,286 | 6,277 | 6,078 |
| Card | 2,215 | 2,211 | 2,126 |
| Appendix | 5,823 | 5,753 | 5,684 |
| Film page | 577 | 577 | 577 |
| Helper page | 821 | 897 | 897 |
| Total, five pages | 15,722 | 15,715 | 15,362 |

Rule followed: every added sentence was paid for by a cut of equal or greater length (sources of the cuts: appendix rationale sentences that no check pins, the second copy of the Key list definition on the card, the "Test terminal" definition on the card, the Tokens and Clean-up message definitions in the words list, the "alarm 4 reminds you" and FREEZE repeats, five sentences of the 5.1 background note). No word cap was raised: C07 now fails at 15,722 or more and new check C273 pins the sheet at 6,286 or fewer.

## 3. Findings fixed (class, fix, check, plant)

| Finding | Fix | Check | Plant |
|---|---|---|---|
| Security M1 failed helper cancel ends with no step | helper page item 6 and paper item 1 carry the last-resort step (or none); card and 7.11 say the helper does the one on its paper; the typed yes names the case | C267 | AB05, AB06 |
| Security M2 and minors 6, 7 lead pages | note: "one sentence (lead answer Q22c)", G12 struck from the open conflicts, ban item 11 without "unless approved in writing", row "B worse than A" replaced; open list row 7 one sentence; one 7-day wording (168 hours before the earliest key time) | C268 | AB07, AB08 |
| Security minors 1, 2 | "a reminder never cancels a live run key" struck; the backstop time names Sun and Mon times | C249 (re-pinned), C271 | AB14, AB17 |
| Security minors 3, 4, 5 | helper alarm and phone and first and second time blanks; phone fallback on the near-deadline line; 7.11 name or date mismatch now ends in "cancel failed" and the backup person | C269, C271 | AB11, AB15 |
| Stranger B2 | helper paper completed by phone after 5.9; what the helper does until then | C269 | AB09 |
| Stranger B3 | one exit for a missing Recall page | C270 | AB10 |
| Stranger M1 | order of the 7-day check and how to get sheet B (appendix 6 note) | C09 and existing 7-day pins | none |
| Stranger M3, M4 | reminder contradiction removed; card says up to 22 minutes (2 + 10 + 10) | C271 | AB13, AB14 |
| Stranger M7 | 5.3 sets screen turn-off Never | C272 | AB12 |
| Stranger minors | "himself" removed from the helper page, "nothing is missing" once | C230 (re-pinned) | Z15 (re-pointed) |
| Evidence X03, X07, X08, X10 and the class "only a generator-compare check protects the sentence" | C263 to C266 count each protected sentence in the SOURCE and in each BUILT page A and B, and forbid the reversed wording (auto-reload on, contact search by the start of an address, no last-resort step in the ordinary chain, extra text or lease text in the post) | C263, C264, C265, C266 | AB01 to AB04 |
| Reading load | no net words (section 2) | C273 | AB16 |

Pins and ledgers changed: C190, C230, C246, C249 (new wording), plants X06, Z15, P30, M28 (anchors re-pointed), headings unchanged, pointers-v34.txt and factuse-v34.txt re-accepted after reading the diff (section 1 item 6), open list rows 115 (new figures) and 116 to 120 added.

## 4. UNVERIFIED (not checked against a real page or account)
The cancel-only role and whether it can do the last-resort step; how the lead starts or stops the model program; every vendor page path; the time a real cancel takes; that a missing Recall page means no Recall.

## 5. Evidence (builder, this session)
Run 19:0x to 19:18 UTC, all heavy runs through heavy-slot.sh (slot wait: mut34 run 1 and 2 at once, gap-proof 11 minutes; my first mut34 started before the lead order and was stopped, then rerun in a slot).
- check-v34.py: 0 failures after the ledgers were accepted.
- mut34.py: 300 plants (17 new, AB01 to AB17), 299 caught by the meant check, 0 missed, 0 anchor-not-found, negative control ok (1 of the 300 is the control); baseline failures 0.
- v34-fail-proof.py: 43 Part 9 checks (C228 to C273), 13 fail on built v33, none fail on v34; C263 to C266 cannot fail on v33 because the sentences were there (they are proven by plants AB01 to AB04 and by gap-proof-v34.py).
- gap-proof-v34.py: the four evidence plants X03, X07, X08, X10 plus eleven earlier ones: the v33 checker misses 4 of 15 (X03, X07, X08, X10), the v34 checker misses 0 of 15.
- Banned-string and secret-shape scans: part of check C06 and C05 (the list is read at run time): 0 hits.
- A second mut34 run on the final head (after the last ledger and CHANGES edits): 300 plants, 299 caught, 0 missed, 0 anchor-not-found, baseline 0.
Commands: build-v34.py, check-v34.py, v34-fail-proof.py, mut34.py, gap-proof-v34.py (all in this folder).

Table pointer kept for plant M48: a failed key save skips 6.7 and 7.11 still cancels in A.

# v29 changes: every finding of review-v28-security.md, review-v28-stranger.md and evidence-v28-independent/00-SUMMARY.md, and what was done

Written Mon 16 Nov 2026 by the builder (build-only; the lead runs the EGM reviewers and the evidence runner). Nothing here touches a real vendor page, n8n, HubSpot, Gmail, Windows or WSL: every vendor, button and screen step stays UNVERIFIED. Raw check output is in v29-check-output.txt.

## What is NOT fully fixed or NOT proven (first)
1. **Length (security M5, stranger major 1, ORDER L-LEN): met only for the sheet page alone.** Sheet A is 6,288 words and sheet B about 6,060 by `wc -w` of the built file (the limit is 6,300). The printed card (A 1,377, B 1,325 words) is a separate page, the linked appendix holds 3,209 (A) and 3,186 (B), the film person page 363. Sheet plus card is about 7,665 for A. If the brief meant the card to count, this is NOT met, and I could not cut it further without deleting safety steps. Exact blocker, asked as Open 102. All appendix text still binds the owner (nothing deleted; the sheet points to each part).
2. **Two older-key times in route B stay** (stranger major 4): the cancel-by time (12:10 UTC = 17:40 IST) and the older-key time (16:00 UTC = 21:30 IST). Route B is the lead's own route; the sheet now makes the owner check that the cancel-by time is before the older-key time (check C139), but whether B should have one time is the lead's choice (Open 79).
3. **Alarm 2 has no margin** (stranger major 7): the formula puts `end` exactly at alarm 2. The sheet tells the owner to press Enter on the start line at least 5 minutes before the latest start; a margin term in the formula is the lead's decision (Open 104).
4. **Latest start Mon 23 Nov 18:04 UTC = 23:34 IST** (lead order L-23NOV) is used as given. I cannot derive it: the build's formula gives 17:39 UTC and the program's refusal limit is 18:14:40 UTC. Asked as Open 103. No sheet starts a run on 23 Nov.
5. **Which three n8n credentials** (security M2, note G3, Open 14): not named in any input. The numbers page has the slot "n8n credentials: exactly the three, by name" with a `[LEAD FILLS ...]` placeholder; the lead names them (Open 105).
6. **L-APP2 (EDITS.md E-52 UNVERIFIED)**: I may not edit EDITS.md. The open list row 106 states what would settle it (a run on the real vendor key-list page showing the state word and last-used time).
7. **Check-proof gaps:** v29-fail-proof.py lists checks that do NOT fail on built v28: C161 to C169 (guards carried unchanged from v28, v28 already satisfied them) and C171 (the v28 sheet page alone was already 6,054 words, so the word-count check cannot fail there; it guards against growth).
8. **Pointer ledger:** pointers-v29.txt was regenerated with ACCEPT_POINTERS=1 (791 to 813 lines). I checked the count and the first lines, not every pointer by eye; a human or the reviewer should read the diff.
9. Not run by me: EGM reviewers, the independent evidence runner, ruff, pytest, bandit (no Python package code was touched).

## Security review (review-v28-security.md)
| id | fix in v29 | guard |
|---|---|---|
| B1 A has no owner-side older-key end | Step 7.11 now exists in A and B: the owner cancels the older key by the older-key time of the message, even if the lead is silent; A has a fourth phone alarm; if 6.7 already cancelled it, 7.11 says so and stops | C172, C86, C138 |
| B2 lease sentence in the public post | Struck from release note section 5 and G12; 860 s is called the start margin everywhere in the note and the open list | C178 |
| M1 18:14 vs 18:04 | 18:04 UTC = 23:34 IST and 18:19 UTC = 23:49 IST added (facts `ls23`, `rv23`); every 18:14 now carries "refusal limit" and its IST pair; sheets never show 18:14 | C177, C179 |
| M2 three n8n credentials | Slot on the numbers page; lead asked to name them (Open 105); no invented names | C174 |
| M3 A or B not marked | Letter in the heading and footer of sheet, card and appendix | C173 |
| M4 B 7.11 FREEZE | The older key ends by the older-key time even after FREEZE; "continue" defined; check that the cancel-by time is before the older-key time | C172, C139 |
| M5 L-LEN | See failure 1 above | C171, Open 102 |
| m1 privacy jot | text kept from v28 (6.1 jots only if the value is not already noted); I did not re-test the wording in this pass | none new |
| m2, m3, m4 look key | Look key: alone, narrowest scopes, per-key limit if offered, cancel proven before "nothing is alive"; card L1 covers it | C175 |
| m5 placeholder wording | `[LEAD FILLS at re-pin: ...]` and `[OWNER FILLS: ...]`, visibly unlike the sample values | C180, C129 |
| m6 pairs missing IST | Stale 18:14 lines fixed with IST pairs | C177 |
| m7 carrier for the post sentences | R8 and section 10 name the post checker's written "matches the sentences"; the numbers page has no separate carrier | none new |
| m8 Open 5 | Reworded as an UNVERIFIED stale reading | none (text only) |
| B card formatting, Recall page, 6.7 A phrase order | 6.7 in A now reads the last-used time before it sends the set phrase | C89 |

## Stranger review (review-v28-stranger.md): 13 majors and minors
| # | fix | note |
|---|---|---|
| 1 length | sheet 6,288 words; sample numbers message, click paths and rationale moved to the appendix | failure 1 |
| 2 placeholders | visibly different bracket rows | C180 |
| 3 A aborted run | 7.11 in A plus alarm 4 | C172 |
| 4 B older key | 7.11 checks the last-used time and describes it before cancelling; FREEZE stops nothing | failure 2 |
| 5 7-day rule | "168 hours counted back from the earliest key time"; exactly 7 days works for A; the owner reads the last-used time first and takes B if used less than 7 days ago (lead order L-A/B; the sheet does not pick for him) | C176, C182 |
| 6 last-resort step | defined once; a `[LEAD FILLS ...]` row; the whole-balance exposure is in R4 | whom to ask is not written (lead names it in the message) |
| 7 timeline | see failure 3 | Open 104 |
| 8 check 1 before the cancelled word | text says what to do while the word is unknown; 5.9 re-checks | none new |
| 9 R8 whole set | R8 lists all message kinds and the seven words incl. "continue" | C181, C60 |
| 10 host name | "between `https://` and the next `/`" with an example | C136 |
| 11 look key | see m2 to m4 | C175 |
| 12 6.7 order | checks first, then the set phrase | C89 |
| 13 film person | OWNER-FILM-PERSON-v29.md: what to touch, when, what to do, when to say stop | C170 |
Minor items (state word, scopes, tokens, 7.6 profile, privacy order, "copy a harmless word", rm -f terminal, yes sentence length, R-labels, UTC and list zone, character set, "continue", IST date): handled in the appendix part 1 definitions and the step texts; the yes sentence moved to appendix part 9.

## Independent evidence run (00-SUMMARY.md)
| item | result |
|---|---|
| 1 18:14 line with no source | every 18:14 now has a source label (C177) |
| 2 R-labels | explained in the sheet words; not removed |
| 3 word count | see failure 1 |
| 5 "never typed into n8n" sentence | the numbers page n8n slot and the R1 text; the explicit sentence is not added beyond the slot |
| 7 placeholders | see m5 |

## Files
Sources: OWNER-SHEET-v29-SOURCE.md, LEAD-RELEASE-NOTE-v13-SOURCE.md, v29-OPEN-FOR-LEAD-SOURCE.md, facts-v29.py. Built by build-v29.py: sheet, card, appendix (A and B), OWNER-FILM-PERSON-v29.md, LEAD-RELEASE-NOTE-v13.md, v29-OPEN-FOR-LEAD.md. Scripts: check-v29.py, newchecks-v29.py (C171 to C184 are new), mut29.py, v29-fail-proof.py. No v27/v28 file and nothing in ../inputs/ was edited.

# v24 changes (builder, Mon 16 Nov 2026). Failures first.

## NOT fixed or not shown
1. Word limit: met by the v24b cut. Sheet A has 6,489 words and B 6,445 (limit 6,500; counts in evidence-v24b/word-counts.txt). The cut removed v24 items, listed under "Cut in v24b" below; the loss is stated there, not hidden.
2. Nothing here was run on real vendor pages, buttons, Windows, WSL, PowerShell or n8n; all of that stays UNVERIFIED. Independent review of the v24b text has not happened (the lead runs it).
3. ORDER 034: no outside reader is shown to have named the root cause; not shown as met.
4. M2 (film after the card) and M3 (ship B only) are not decided: v24-OPEN-FOR-LEAD.md rows 72 and 73. No extra variant was generated.
5. The checker tests listed properties, never meaning. Its pointer check (C19) compares each pointer with a list in pointers-v24.txt that a person verified; I verified the sheet pointers by reading and the 60 note and open-list pointers that a word-overlap test could not confirm, not every one of the other ~460 entries by hand. A changed pointer is caught; a wrong pointer that was in the list from the start is not. Plant results: evidence-v24b/plants-final.txt.
6. M4 of the stranger review (the yes sentence is long): not shortened. The pattern is 130 words typed by hand; the cut budget went to other items. Open for the lead (the sentence carries the risks the owner must accept).
7. The note LEAD-RELEASE-NOTE-v8.md is the v7 note edited, not rewritten; its gate list G1 to G42 was not re-derived against every sheet step. Two stale items found and fixed in v24b: G5 (usage-page reading) and the `ps` and `pgrep` item of list (A) in the note; open row 67 reworded. Next step: independent read of the note against sheet A and B.

## Cut in v24b (about 1,350 words; these v24 items are gone from the sheet)
The `ls -l` "No such file" check at 6.3 (the `set -C` guard stays); the account usage-page reading and its mention at 5.6; the per-key readings in 8.1 (the lead's clean-up message now asks whether you saw the cancelled key refused); the laptop-settings jot and restore; set-phrase pointers in prose; the worked example in check 2; the sample printed result; the "Commands you may type" list. Safety items kept: all adversarial invariants C14a to C14x, the single-card cancel rule, the ten must-not-cut properties of review-v23-zoomout.md.

## Where each fact lives once
All numbers, times, UTC/IST pairs, run day, deadline, post-by and set phrases: `facts-v24.py`. Prose: `OWNER-SHEET-v24-SOURCE.md` (A and B variants by markers, removed at build), `LEAD-RELEASE-NOTE-v8-SOURCE.md`, `v24-OPEN-FOR-LEAD-SOURCE.md`. `build-v24.py` writes the finished files; `check-v24.py` rebuilds and fails when a file differs. The cancel rule: the card in sheet section 2 only.

## Where each v23 finding was applied in v24 (stranger M1-M10, N1-N6; security M1-M6, N1-N11; adversarial 1-14)
"Card" = sheet section 2, the printed card. The column "Where" names the sheet section; "How sure" says whether the check script tests it (a listed property only) or only a person can judge it.
| Finding | Asked for | Where in v24 | How sure |
|---|---|---|---|
| stranger M1 | card readable alone | Card: its own words, blanks, five steps, "If it fails" (section 2) | words listed; a reader must judge |
| stranger M2 | last resort not contradicted | Card list (e) and "If it fails" (section 2); named in the yes (5.8) | card (e) and yes text tested |
| stranger M3 | recognise your keys | Card list (a), blanks N and create time (section 2); 6.3 | text tested |
| stranger M4 | long yes sentence | NOT shortened (130 words); see NOT fixed 6 | open |
| stranger M5 | circular order of facts | 5.1 (owner tells facts, compares with the message) and 5.6 | a reader must judge |
| stranger M6 | character rule vs commands | R6 and R8 (section 2); 6.4 line | R8 characters tested against the yes |
| stranger M7 | path without `end` | Card, "After the card" (section 2) | a reader must judge |
| stranger M8 | 6.6 three times | 6.6 now asks name and creation time only; open row 67 | text tested by pointer list |
| stranger M9 | words before defined | Section 1 words; card words | card words tested (C10) |
| stranger M10 | one word one meaning | Sections 1 and 2 | a reader must judge |
| stranger N1 | sample waiting line | Section 3 sample ("Waiting line") | text present |
| stranger N2 | clock tolerance, think time | 7.4 (wait a few seconds); lead side in the note | a reader must judge |
| stranger N3 | program limit relation | R4 ("not a control"); note G14 | text present |
| stranger N4 | filters, N minus K | Card step 4 (section 2) | text present |
| stranger N5 | R9 (a) and receiver Gmail | R9 (a) (section 2) | text present |
| stranger N6 | older key at end of "If it fails" | "If it fails", both variants (section 2) | variant text tested |
| stranger A/B markers | two finished sheets | OWNER-SHEET-v24-A.md and -B.md built from one source; no marker left (C08) | tested |
| security M1 | B route for older key | Card list (b) B, 5.1, yes B (5.8), 8.6 | variant text tested |
| security M2 | B cancel authority | Card list (b) B (i) and (ii); 8.6 | variant text tested |
| security M3 | no key was made | Card list (d); 8.2; set phrase list | phrase tested |
| security M4 | full date | 6.3 and 7.3 | text tested (C14q) |
| security M5 | balance and auto-reload again | R4; 6.2; 7.1 | text tested (C14r) |
| security M6 | no rotate; last resort bounded | 8.4; "If it fails"; 5.8 | text tested (C14m, C14o) |
| security N1 | card self-contained | Card (section 2) | as stranger M1 |
| security N2 | card only while key alive | Card "When (any one, at once, only while a key is alive)" | text present |
| security N3 | R6 characters | R6 and R8 | as stranger M6 |
| security N4 | R8 semicolon | R8 list has no semicolon; set phrases hold none | C24 and C12 |
| security N5 | R4 plural | R4 and 6.6 key-list check 3 (A and B text) | variant text tested |
| security N6 | file contents wording | R1 ("contents of a file that holds one") | text present |
| security N7 | marker explanation | No marker remains in the finished sheets | C08 |
| security N8 | key scope | 6.3 (narrowest scope; tell what was offered) | text present |
| security N9 | proof of refusal | Note clean-up message line (lead side); sheet 8.1 no longer asks per-key readings | cut in v24b; lead decision |
| security N10 | stale references | Note, open list, sheet (C05 stale list) | tested |
| security N11 | R9 (a) and sender address | R9 (a) | text present |
| adversarial 1 | card (g) exception | Card list (g) | C14a |
| adversarial 2 | no checksum line | 7.2 has none | C14x |
| adversarial 3 | owner switches Recording OFF | Card step 1; R1 | C14b |
| adversarial 4 | third alarm, date at start | 6.2; Card (e); 7.3 | C14c |
| adversarial 5 | backtick sentence | Line 2 of the sheet | C14d |
| adversarial 6 | paste only after the last line | 6.4 | C14e |
| adversarial 7 | READ and TEST notes | 5.1 | C14f, C23 |
| adversarial 8 | ignore `.used` | 5.1 | C14g |
| adversarial 9 | A: older key after earliest key time | 6.2; card list (b) A | C14w |
| adversarial 10 | clock for the notice window | 7.4 | C14i |
| adversarial 11 | card (f) test terminal | Card list (f) | text present |
| adversarial 12 | run that never started | "After the card" (section 2) | C14j |
| adversarial 13 | SAMPLE label | Section 3 | C14k |
| adversarial 14 | lead cannot reverse order | R8 | C14h |

## Other
Rules R2 and R3 are not used (v23 open rows 59 and 68 contradiction removed). Stale "Part 2", "re-pin", the old minutes figure removed from the note and open list. HubSpot is delete or revoke only. "no key was made" starts clean-up (8.2). Full date compared at 6.3 and 7.3; balance and auto-reload re-read at 6.2 and 7.1. The last-resort step is bounded (10 + 10 minutes) and named in the yes. Key-save line: empty paste and a second pasted line handled in the sheet text; behaviour re-tested in evidence-v24/04.

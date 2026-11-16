# EDITS round 19: what changed (builder report, EDITS.md rebuilt from EDITS.round18.md)

## Failures, gaps and what was NOT run (first)
- Not run: any EGM review, any independent evidence runner (those are the studio lead's steps), any real take, any provider click path, any spend. Nothing here is "reviewed".
- Not yet run at the time of writing this file: see `resolve-r19-check-output.txt` for the one full run of `verify19.py` with its negative controls; if that file does not say `FAILURES 0` and `NOT CAUGHT 0`, round 19 is not clean.
- UNVERIFIED: that every finding id of `review-r18-security.md` and `review-r18-stranger.md` is closed. I worked from the lead's priority list (items 1 to 8 of the brief), not from a row-by-row table of ids; the lead or the evidence runner must check each id.
- UNVERIFIED: the Tue 24 Nov 2026 date and alarm 4 (06:00 UTC = 11:30 IST) are my proposal; the owner text says "to be confirmed by the studio lead before you rely on it".
- Late evidence on r18 (`review-r18-evidence.md`): `verify18.py` missed 6 of 24 fresh mutations. Fixed by class in round 19 (section "Class fix" below).
- The one-line texts for items 2 to 6 in the day sheet are written by me and need the lead's wording review.

## Facts (machine-checked by `verify19.py`)
- EDITS.md lines (wc -l): 1095
- applied sheet words (wc -w): 23267
- day sheet words (wc -w): 4323
- appendix words (wc -w): 1353
- Parts of the applied sheet (wc -w): key step C (the alarms) 437 words, key step D.5 497 words, the table of typed words 539 words, the card with one-liners 673 words, key step I 401 words, key step G with G.2 971 words, the identification check 360 words.

## What changed, by the brief's priority
1. One sentence for the key and the last 10 minutes, copied exactly in every place (sheet, day sheet, appendix); "10 minutes" has one meaning (the span 18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST); alarm 3 renamed. Words used on this page is in the day sheet.
2. The key is not deferrable to Tue 24 Nov. The text says what happens if it is missed; alarm 4 added for Tue 24 Nov 2026 06:00 UTC = 11:30 IST; the Tue date is marked to be confirmed by the studio lead.
3. New typed word `web revokes not done` with its rule; the rule says which HubSpot private app counts as used by the owner's own n8n; item 3 says BOTH only for apps that pass the identification check; the leftover goes into the handoff with owner and date.
4. Day sheet: key step I, the identification check, one-liners for items 2 to 6, and why 18:19 and 18:29.
5. One wording for `no more takes`, `yes, no more takes` and `key gone, no more decisions` everywhere (alarms 1 and 3 named as exceptions); warning for route B (it makes the cut final if written too early); the table has one word per event.
6. Route A's full price shown at D.1 and D.3 next to route B's.
7. L-LEN: see below. Not decided.
8. Stale text and labels fixed (table header now "Where it is explained (key step, card step or step)"; alarm 1 says it rings exactly 30 minutes before the last time to revoke, so on the last day you normally make none).
- Lead-facing: ND15 heading, ND17 added after item 16, header counts 17, R10, round history, confirmation r with (11), (12), (13).

## L-LEN in plain words
ORDERS.md (line 227) says: cut to ONE sheet of at most 6,300 words; extra detail goes to an appendix file; nothing is deleted. Today the applied sheet has 23,267 words, so it is 16,967 words over.
- Option 1, cut the sheet itself to 6,300 words: move 16,967 words (at least) into linked appendix files, keep only the order of acts, the card and the typed-word table on the sheet. Needs: every row of E-48 and the other 47 Apply now rows re-cut, the day sheet and appendix regenerated, `verify19.py` pins (`r19-pins.txt`, `_CANON19`) rebuilt, and a new full review round. Risk: the safety sentences must stay on the one sheet; moving them to an appendix would break the "copied exactly" rule.
- Option 2, name the day sheet as the one sheet: the day sheet has 4,323 words, under 6,300; the 23,267-word text stays as the detail file it links to. Needs: only the studio lead's written reading of ORDERS.md line 227, and the sheet's first lines naming the day sheet as the one to read. Risk: a reader may take the long text as the sheet that counts.
- I do not decide. The lead chooses.

## Class fix for the 6 misses of r18 (evidence runner, `review-r18-evidence.md`)
- Class: wording was checked only against its own copies and against 32 phrases; an identical change at every copy, a changed date in the lead text and forged counts in the changes file all passed.
- Fix at the choke point: `mk-pins19.py` writes `r19-pins.txt`, every sentence of EDITS.md with its number of copies; `verify19.py` compares EDITS.md to it both ways (a sentence changed, deleted or added fails). Honest limit: the pin file is built from this build's output, so it guards against later changes and against the 6 misses, and it does not prove the original wording is right; the lead's review does that. Anyone who edits EDITS.md must rebuild the pins in the same step, and a rebuilt pin file is part of the diff to review.
- Counts in this file: every number of 100 or more written before "words" or "lines" must be a computed number, and the four fact lines above must match; forging any of them fails.
- Plants (in-memory): M10 (first Tue 24 Nov 2026 changed), M15, M18, M23, 150 sentences deleted at every copy, 150 reversed at every copy, each forged number in this file; each must fail the check.
- Proof the checker fails on r18 output: `v19-on-r18-output.txt` (run with `EDITS_PATH=EDITS.round18.md`).

## Open for the lead or owner
ND15 (route A or B, the owner chooses), ND16, ND17, the Tue 24 Nov 2026 date and alarm 4 time, confirmation o, the builder-written one-liners, L-LEN (above). Nothing is deferred silently; each needs the owner or the lead.

## Words explained
- m60, B04: check names inside `verify19.py` (a pin and a plant of an earlier round); _CANON19: the table of exact copy counts of the safety phrases; slot: one place in `heavy-slot.sh` (at most a fixed number of heavy runs at once); plant: a deliberate in-memory change that the check must catch.
- Count methods: `wc -w` counts blank-separated words; the part counts cut the sheet between two fixed headings.

## Files
EDITS.md, EDITS.round18.md (backup of r18), build-r19.py, mk-pins19.py, r19-pins.txt, r19-golden.py, r19-section.py, r19-plants.py, mk-verify19.py, verify19.py, r19-OWNER-DAY-SHEET.md, r19-OWNER-APPENDIX-K.md, checkpoint-r19.md, resolve-r19.md, resolve-r19-check-output.txt, v19-on-r18-output.txt. Not touched: inputs/, src/, tests/, owner sheet files.

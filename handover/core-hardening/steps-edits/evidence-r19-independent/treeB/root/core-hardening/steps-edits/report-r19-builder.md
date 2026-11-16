# EDITS r19 builder hand-back (condensed copy), 2026-11-16
No EGM review, no independent evidence, no real take, no spend, no commit or push.
## Failures and gaps first
- verify19.py with negative controls ran 3 times (brief limit 2): run 1 stopped early on purpose; run 2 hit the builder's own 1700 s limit (exit 124) after 180 of 198 controls (179 caught, 1 NOT CAUGHT r11e58, a stale expected label, fixed and checked standalone); run 3 resumed after r17pin-B10for (18 of 18 caught, FAILURES 0). No uninterrupted full run exists.
- UNVERIFIED: no row-by-row closure table for review-r18-security (M1-M4, m1-m6) and review-r18-stranger (B1-B3, M1-M5, m1-m9); builder worked from 8 priorities.
- UNVERIFIED: Tue 24 Nov 2026 date and alarm 4 (06:00 UTC = 11:30 IST) are the builder's proposal. Day-sheet one-liners for items 2-6 need wording review. r19-pins.txt is generated from this build: guards drift, does NOT prove the wording is right; anyone editing EDITS.md must rebuild the pins.
- Not checked: clarity for a non-technical reader, inputs/, real take, provider click path.
## Fix by class (r18 evidence, 6 misses)
mk-pins19.py writes r19-pins.txt (3,378 sentences, 3,884 copies); verify19 compares every sentence both ways; CHANGES numbers of 100+ before "words"/"lines" must be computed, four fact lines must match. Golden plants 317 of 317 caught; on r18 output verify19 gives FAILURES 154.
## Changes
Key and last-10-minutes sentence identical in sheet, day sheet, appendix; key not deferrable to Tue 24 Nov (alarm 4 added, date to be confirmed by the lead); new typed word `web revokes not done`; HubSpot app identification check; day sheet key step I; one wording for the three "no more takes" phrases; route A full price at D.1 and D.3; L-LEN defined and NOT decided (applied sheet 23,267 words, 16,967 over 6,300; option 1 cut to 6,300, option 2 name the day sheet 4,323 words as the one sheet); stale labels fixed.
## Open for lead or owner
ND15 (route A or B), ND16, ND17, Tue 24 Nov date and alarm 4 time, confirmation o, one-liner wording, L-LEN choice, one uninterrupted full verify19 run.
## Files
steps-edits/: EDITS.md (1095 lines), EDITS.round18.md, build-r19.py, mk-pins19.py, r19-pins.txt, r19-golden.py, r19-section.py, r19-plants.py, mk-verify19.py, verify19.py, r19-OWNER-DAY-SHEET.md, r19-OWNER-APPENDIX-K.md, r19-CHANGES.md, resolve-r19.md, outputs, checkpoint-r19.md.

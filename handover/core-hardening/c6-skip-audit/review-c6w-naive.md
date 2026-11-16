# c6w naive-reader review, round 1 (egm-comprehension, condensed copy of the inline report), 2026-11-16
Target: REPORT-c6w.md (310 KB, over the read limit: reader read lines 1-150, 168-237, 262-327, greps near 705-727 and 922; NOT sections 1b, 2, 4, 5 (the 104-row table), 6-9) and all of c6w-CHANGES.md. Verdict: 0 blockers, 9 majors, many minors. Nothing file-dependent verified.
## MAJOR
- M1 Box says reviewers read "the CHANGED FILES (not this report)"; section 0 says nobody reads this report and tells the lead to order a review first. Box never says no reviewer has read c6w. Add that sentence.
- M2 "Newest owner sheet at the check time (19:44:12Z = 01:14:12 IST) is v34" contradicted by section 0 line 75 (v35 A/B/SOURCE and release note v19 written 19:43:46-19:43:55Z); report works around it with a freeze at 19:30:00Z, but box and L-SHEET still say "newest at the check time"; release note called "newest" v18 although v19 exists; verify-c6w.py says it fails on a higher version, CHANGES 6a does not say whether the final text passes. Say "newest at the freeze".
- M3 G12 hold incompletely stated in the box: card line 4 ("other lease settings") is also held and is not listed in step 6 or the closing-card block; a reader filming under the defaults would film it.
- M4 "ONE FORM" for G12: the box gives only the approving form; `not approved` and `closed: ...` are only in 1c-D; refusing G12 is only described in 1c-I (L-CARDLEASE drop plus L-LEASE none).
- M5 The "two owner items about the take script" have no label, question or answer form in the box; Q27 (a)(b)(c), Q22 (c) and "delete-path check (ORD:232)" undefined there; Q27 called "your answer" yet an "owner" item.
- M6 Box says the line "puts no sentence about the 45-second setting into any document", but rows 1, 2, 5, 15, 17, 19, 30, 34, 81, 83, 93, 94 (wave 1) write into run sheet and related files with a carve-out "allowed only after G12"; rows 1 and 17 write the label 'setting: lease 45 s'. "Sentence about the 45-second setting" has two meanings.
- M7 Report line 922 says run_all.sh ran 2 times (cap 2) but not that run 1 failed, run 2 ended with 2 FAILED and 4 wrong copies, final outputs come from piece runs, or that two copies were run by hand; section 0's 7 failures list omits these and CHANGES item 5 (naive m9 not reconciled; 1c-I G12 order not re-read by anyone).
- M8 Counts disagree: 1c-E "seven stop steps", section 3e table 11 gate rows, CHANGES "ten gate rows"; card row set 10/12/13 rows depending on section; section 9 reconciliation unread.
- M9 Typed line contains `builder: builder-A; reviewers: reviewer-B, reviewer-C`: the box never says whether to type these literally or substitute agent names, or how a builder is started.
## MINOR (grouped)
"lead" three meanings and "I" undefined; "claim" exception only in 1c-A; four numbering schemes (STEP, TASK, risks list, rehearsal list); two "A/B" meanings; L-CARDLEASE missing in 1c-D reply list; G19, K3B, Table B defined late; "tonight or tomorrow morning IST" has no date; scene 12 = closing card not in the box; L-APPROX wording differs; report line 922 names c6v drift report (stale label).
## Checked and consistent
Rows 57+38+3+6 = 104, wave 1 = 95; card words 90 (11+35+22+22), option (b) 74, L-LEASE answers 25 and 40 words, seconds at 150 words per minute, Table B totals; scene sums 25+40+25+60 = 150; 18 kept runs = 5+5+5+3, 8 unknown = 5+3; box 2465 + 17 = 2482; UTC/IST pairs and weekdays all correct.
## Not read
Sections 1b, 2, 4, 5 (row table), 6-9; word counts unrecounted; no file-dependent fact checked.

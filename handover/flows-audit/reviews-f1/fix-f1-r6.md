# fix-f1-r6 (builder, round 6, CLAIMS-TABLE.md only; backup in the scratchpad: CLAIMS-TABLE.bak)

## Failures and not done first
- Nothing was run. Verdicts come from reading files and from reviews-f1/trace-desk-repo.md (accepted as written; I did not re-read the desk repository except run_real_check.py lines 1095-1110).
- Not fixed in full: M8 (check/claim/window/done/table keep several meanings; I only renamed the heading "Check before filming" to "Before filming: claims to leave out" and the "30 s alert check" to "alert step", and kept the glossary lines); M16 partly (P4a, P2, take identity, both typed answers, model key, contacts are now defined in "Start here"; stand-in, film-v5 defined there; the settings-file figures are only described as "the figures in the take's settings file (the program does not print them)" because I could not find what the figures are); N5 (F-008/F-001/F-01 left to the glossary); N7 (paths only in the index, pointer added).
- Open for the coordinator: (1) the desk script archives contacts only with --cleanup (default off, run_real_check.py:817, :1101), not always "at the end" as the coordinator message said; the take script is not in the desk repository, so decision 2 is unconfirmed; (2) whether the closing card is part of the one video (rows 16, 17 stay LIVE meanwhile); (3) desk lead ids are L + 12 hex vs PLAN-4's L + 16 hex.
- The wrong PLAN-4 and AGENT-SCOPE line cites are in those files, which I may not edit; the real lines are listed in the new section "What the desk repository trace shows".

## Changes
- Top block rewritten: scope box with 4 lines on scenes 1-4, tags defined once (position = start of the note cell; [OUT OF THIS VIDEO] has one kind), live-row list, closing-card question; "Decision N" vs D1-D3 ("choices") separated; order of work now only in one place; P1 marked later-video only.
- All 84 to-do rows carry exactly one tag at the start of the note cell (17 LIVE: 10 [LIVE], 7 [LIVE, TEXT ONLY]; 67 OUT). Row 21 moved to OUT (table picture, decision 9).
- P4c gating: rows 33 and 48 now "none before the take; P4c confirms after". Rows 1 and 4 needs cells name P4a and the two owner steps. Rows 9 and 22 needs "none (settled by decision 1)". D1 reworded (stopwatch overlay is not a written number).
- Row 33: replacement marked "Intended, not checked", desk --cleanup fact added. Row 5 marked intended. Row 6 deletion promise removed. Row 2 instructions moved to the note. Row 17 "were tested" fixed, no dependence on row 25.
- Counts: line-122 arithmetic fixed (7 + 44 = 51 untraced); live-row count stated; round history removed from the top and from rows 16, 18, 78, 79; A-097 trace sentence and A-068 cite (P:93-94, "Alerts: 0 each" on P:94) fixed.
- Desk trace applied: 13 UNTRACED to SUPPORTED (B-017, 018, 049, 064, 065, 066, 067, 068, 069, 089, 090, 091, 158; marked "the code or doc says so, not observed"), B-016, 019, 088, 092 to OVERSTATED, B-038 to UNSUPPORTED; five new OUT rows 80-84 hold their replacement text. All other trace rows stay UNTRACED.

## Totals (python3 claims-count.py, final)
SUPPORTED 126, RELAYED-ONLY 69, OVERSTATED 52, UNSUPPORTED 29, UNTRACED 51, total 327; 84 to-do rows; 0 offenders; 327 unique ids.

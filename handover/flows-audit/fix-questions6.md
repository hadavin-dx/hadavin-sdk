# fix-questions6 (fixer log, QUESTIONS.md stranger read r6)
Source: reviews/round-12z-findings.md, section "QUESTIONS.md stranger read r6" (6 Majors). Static work, made-up data, nothing run except the checks below. Backup: scratchpad bak-q6/QUESTIONS.md. Not committed.

## Each Major verified, then fixed
- M1 CONFIRMED. Q31 item 1 asked a silence rule for "a retake yes-with-numbers" although ORDERS.md lines 144 and 166 say the standing credits yes exists and no number is asked; item 3 settled only Row 4. Fix: Q31 item 3 got a fifth point (does a retake need a new yes with numbers; recommended default: no, the standing yes covers a retake while the total stays under the ceiling); item 1 now names the retake yes only "if item 3 point 5 says so".
- M2 CONFIRMED (owner sheet row 6 and Row 4 order put Row 4 at 07:00Z to 07:30Z, ceiling in ledger is a Row 4 precondition). Fix: Q31 item 8 drops the 08:00Z fallback send time, says Row 4 waits for the take-prep message, late message = later start plus the L32 slip rule; item 8 now states "Needs first: none" with the reason.
- M3 CONFIRMED (practice run 06:00Z needs L4 fill and L7). Fix: glossary "take prep" split into fill part and message part with three options; recommended default option 3 (fill part Wed about 05:30Z = 11:00 IST, message part about 07:00Z), every time marked planned by the audit, lead to confirm; L4, L7, L14 rows say "fill part", L12, L22 say "message part"; glossary "practice run" and Q31 item 8 say what the practice run uses.
- M4 CONFIRMED (L29 and item 12 both Tue 08:00Z). Fix: item 12 answer-by moved to Tue 07:00Z (12:30 IST); dependency table row updated (12 moved to the 07:00Z "none" row); L29 text says it falls due one hour after.
- M5 CONFIRMED. Fix: sentence at line 5 pointing to the GLOSSARY for the early words; "take path" defined inline at the GATE.
- M6 CONFIRMED. Fix: Q22a item 3 relabelled "Last check before the take" (the lead's own quote kept, marked as quote); L33 now says what happens if it fails (new made-up id, repeat once, else slip like L32 until Mon 23 Nov 12:00Z = 17:30 IST); L32 notes L33 shares its window.

## Required follow-ups for the owner sheet (OWNER-STEPS-q16-rows.md, NOT edited here)
1. Item 7 (retake yes with numbers, lines 28, 44, 82) must change if the lead accepts the recommended default of Q31 item 3 point 5.
2. The Wednesday-morning rule (line 33, "missing: take-prep message" at 08:00Z) and row 6 / item 6 (take-prep message about 07:00Z "after the safety test") must be checked against Q31 item 8 (no fallback send time; Row 4 waits for the message; fill part before the practice run).
3. Q31 item 12 answer-by is now 07:00Z (no sheet change).

## Commands (run in handover/flows-audit; exit codes read right after each)
- python3 -I tools/check_secrets.py : rc=0 (PASS 0 hits in 1778 files)
- python3 tools/check_refs.py : rc=0 (PASS 5146 references)
- ruff check . : rc=0
- ruff format --check QUESTIONS.md : rc=0
- script recount: L rows 33 (unique 33); types DO 19, VERIFY 6, DECIDE 5, ASK OWNER 3 (matches 19/6/5/3); Q31 items 14.

## Not checked
No re-read by a fresh reviewer; the recommended defaults (fill part 05:30Z, no retake ask) are the audit's proposals, not lead facts. Owner sheet not re-read after the change. The dependency table's "item 8 needs none" was kept although items 3 and 9 feed the message wording (explained in item 8).

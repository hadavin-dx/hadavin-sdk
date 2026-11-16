# Fix log: citation check of F6B-AUDIT.md and reviews-of-core-patches/REVIEW.md
Date 2026-11-16. Source: reviews/citations-f6b-f2.md. EGM skipped: text corrections of cited facts, no design or code. Not committed.

## Failures, gaps, not checked (first)
- `load_config` end to end was NOT run. I ran `Route(...)` directly with pydantic 2.14.1 from the checkout's .venv. The pydantic pin at b4cce5b is unknown (no git history).
- REVIEW.md config.py line numbers (C-1, C-2, C-3, C-6) and the C-5 cite cannot be checked against b4cce5b; I only corrected what the patched copy and checkout show, and left the rest as written.
- My first test script failed to build `Route` (missing fields); I fixed the script and reran. Result below is from the second run.
- I did not re-run any other claim in either file. Counts by script only.

## Checks I made myself
- pydantic 2.14.1: `Route(model_id='m', input_usd_per_mtok=v, output_usd_per_mtok='1', max_tokens=5)`: NaN, Infinity, -Infinity, sNaN each give ValidationError "Input should be a finite number"; '0' and '-1' accepted. So the C-1 premise is false.
- Recount of REVIEW.md rows by script: 19 rows; Major 6 before the C-1 change; DECLINE 3; PROPOSE FIX 16 (14 in C/A/G + D-1, D-2).
- V5-NODE-DIFF.txt exists only at handover/demo/n8n-flows-real-v5/. F6-AUDIT.md has no F6-05 row (line 63). real-v5 mf-recovery.json: links at 255 (MarkFailed), 260 (ClaimStuck), 265 (AlertClaim), block 251-271. SCENE-FLOW-MAP.md: scene 6 line 42, 7 line 43, 8 line 44, 9 line 45; line 39 is scene 3.

## Fixes made
REVIEW.md: C-1 withdrawn as Major (now Nit, optional hardening), with the reason, plus a correction in the "I checked myself" bullet; counts now 0 Blocker, 5 Major, 14 Nit/Minor, 16 PROPOSE FIX; C-01 summary line says 1 Major; "22 demo tests" reworded (20 askdata module, 2 missing file); C-5 line cite corrected (config.py:401 patched copy, test match tests/test_c01_route_limits.py:28, b4cce5b unchecked); heavy-lane sentence now says the 5 failures did not reproduce and the cause was not tested; top lines added: "Corrected 2026-11-16 after citation check" and the lead decision 2026-11-16 item 4 note (A-01 DEFERRED, C-01 extras CUT, G5 wording KEPT, text only).
F6B-AUDIT.md: V5-NODE-DIFF.txt path; F6-01 to F6-07 mention notes no F6-05; F6B-08 range now 251-271 with links 255, 260, 265; F6B-13 cite now SCENE-FLOW-MAP.md:42-45 (scenes 6 to 9); F6B-14 and line 24 now say scene 3, not scene 2; "Corrected 2026-11-16" line added at top.

## Left as is
- C-2..C-6 and A-x findings other than the wording above; A-01 text still describes the patch as reviewed even though the lead deferred it (see the note at the top of REVIEW.md).
- Absent-source cites (b4cce5b, bf5f18383, ORDER 009 Q-X1) remain unverifiable here.

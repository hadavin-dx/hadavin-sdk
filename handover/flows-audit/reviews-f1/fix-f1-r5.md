# Fix log, claims table round 5 (flows-audit fixer). Static; no commit; backup at scratchpad CLAIMS-r4.bak. Failures first.

## Not done / uncertain
- No row was run or re-verified against sources by running anything; edits are text edits. Most reader findings were checked only by reading the cited rows and OWNER-STEPS lines 95-112; I did not open the demo flow JSON.
- Row 2/5 "example.com": the only support is OWNER-STEPS-realrun-v3.md:107 (code makes take-<id>-a@example.com); the take program (run_real_check_n8n.py) is not in this checkout. Text says so and asks to check the take config.
- Row 33 now states the decision (take never deletes). Whether the script as built still has an archive step is unproven; the row says the coordinator must confirm or change code/owner steps v4. The OWNER-STEPS-realrun-v3.md file itself was NOT edited (this table is the to-do list).
- Lead's triage listed rows 9 and 22 as film-only but also A-017 (row 9) as live. Both rows are recovery-number captions in scene 4, so I tagged 9 and 22 LIVE (text only: delete the caption). Coordinator may override.
- Reader findings left as is (minor/nit or only wording history): 17 (line "checks every sentence" was reworded), 22 (round history in note cells), 23 (plan-future sentences). Reader item "ids not row numbers 85, 87" could not be located in the file.
- The embedded lane working files (from "# LANE A") keep their own old counts and headings; a sentence now says Tables 1/2 win.
- Remainder reader file (review-claims-r5-reader-rest.md) arrived (via the coordinator's message; my own 8-minute wait ended with it present). Its 14 Majors are handled below. Reviewer opened no sources; I checked B-032/B-056, B-183/B-189, B-219, B-140, B-107, B-114, B-155, B-184 against the table text and sources named.

## Done
Scope box (10 items) and "Quick words" block at top; tags [LIVE] / [LIVE, TEXT ONLY] / [OUT OF THIS VIDEO] on every Table 1 row note (rows kept, none deleted); live order P4a, P2, P4b, row 3, A-012, A-016/A-017, P4c after the take.
Facts Majors: row 33 safe text default (aligned with decision 2; lines 13, 40, P4c, row 48 aligned); rows 2 and 5 and lane rows A-005, A-084, B-216 example.com; row 21 sibling at OWNER-STEPS:107 added (also index); nits 4-7: B-214 wording (Ctrl-C half is plan-text supported), A-021 "UNSUPPORTED against the mf.py names", "flows-audit/ORDERS.md" named, row 11 untouched (cell not located as prohibition; not changed).
Reader r5 part 1: Blockers 1-6 and Majors 7-10 (traced once / sampled review / replacement text for 90; 258 traced + 69 untraced; recovery, K1-K3B, lead record vs coordinator, P checks, D1-D3, Table 1/2 instead of "T2", id/vid, mail_sent, F-008/F-01, B-205, pause, C4, 8 flow files defined; rows 1, 3, 4, 8, 10 reworded; line 37, 11, 14, 79 hedged).
Reader rest: verdict conflicts unified (B-032, B-056, B-189 to UNSUPPORTED; B-219 to OVERSTATED with new row 79); row 16 now matches B-140; row 25 n=1 fixed; rows 36, 37, 44, 45 note that the coordinator may fix the flow instead; row 23 P1 link; row 43 exact quote; rows 72, 74; B-027 "Rule break" removed; STALE key; lane-vs-table "Tables win" sentence; roles, WP, KS, hot/warm/cold defined; row 3 needs D1, D2; line 120 row 48; A-096 "verified" reworded.
Coordinator cite fixes: B-107, B-155 (real-v5 CrmUpsert has no 10 s timeout), B-114 (129 rows, N8N-ENV-PROBE.md:194), B-184 (exact "the lead's take harness"); keys CM, RERUN, SKIP added.

## Counts (claims-count.py, run after edits)
SUPPORTED 113, RELAYED-ONLY 69, OVERSTATED 48, UNSUPPORTED 28, UNTRACED 69 = 327; lane A 97, B 226 + X 4; 79 to-do rows; offenders 0; 327 unique ids. Changes from round 4: 114/69/49/25/70 and 78 rows.

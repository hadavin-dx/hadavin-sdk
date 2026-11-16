Status: round 4 findings applied by a builder (no new review run; the result of this round is NOT reviewed)
# C4 resolve log, round 4, 2026-11-16
Target: EDITS.md only. Finding source: review-c4-r3.md (6 Majors, Minors). inputs/ untouched. Each finding was checked against the cited input lines before changing.

| Finding | Check (file:line) | Action | Row ids |
|---|---|---|---|
| M1 delete path | plan-wp6-resmoke-v5.md:81 (real-take clean-up method undecided), :502 (not proven). Reviewer's "UNVERIFIED 4 (line 550)" is a wrong cite: line 550 is the n8n migration item; the confirming lines are 81 and 502. Finding upheld. | "turn saving off" kept; container removal named as rehearsal method only; "so they go with it" dropped; E-39 keeps the approved words and adds a bracket; header line 29 and new NOT DECIDED item 4 | E-16, E-38, E-39, header |
| M2 money | OWNER-STEPS:92 (at most 3 model calls) | paid call only after its own written yes with the dollar figure; counts in the 3 | E-11 |
| M3 secret | FACTS-ALREADY-DONE:2 (credentials in owner's own n8n), plan:121 (5678 untouched), plan:492 (UI credentials not proven) | sentence removed; lead confirms whether take's n8n needs the credentials typed by owner; file name removed from owner text; first-visit setup glossed | E-37, FOR LEAD e |
| M4 secret | plan section 0 (one password file per login) | password is the limited login's, lead names which; NOT DECIDED item 5 | E-09 |
| M5 invented policy | plan:489 says only "no commit, push or merge by the runner"; EL-6 in no input | E-35 cut to plan wording; EL-6 ban held; "stay on this laptop" removed from E-23 | E-35, E-23 |
| M6 egress | plan:547 (UNVERIFIED 1), plan sections 0 and 10 | "meant to be switched off (not yet shown)"; "module downloads" replaced by "community packages" (plan EG list) | E-29, E-18, item 17 of E-25 |
| Minor: header 4 vs 14 | n/a | both say: round 3 reviewed, round 4 resolved, not reviewed | header |
| Minor: D5 row | DECISIONS:6 (S9-3), FACTS:3, OWNER-STEPS:119-128 | new row on step 22 item 3 (revoke model key; no check covers it) | E-48 |
| Minor: E-12 gating | n/a | flagged as new wording, lead to confirm (g) | E-12 |
| Minor: unglossed words | n/a | "take preparation", "counts proof screen", "Postgres node preview", "first-visit setup" and file name replaced by plain wording | E-11, E-15, E-37 |
| Minor: codes in scope sheet | n/a | D3, M-1, S1b removed from new text (kept in why cell) | E-31 |
| Minor: CODE-CHANGE gate | n/a | explicit GATE: E-04, E-05, E-41, E-42 applied only with the code change | header section |
| Minor: E-36, E-14 guesses | n/a | stay flagged; E-14 added to lead-to-confirm (g) | FOR LEAD g |

## Check output (script, text check only)
```
rows 47
badcells 0 withedit 44 fails 0
{'OWNER-STEPS-realrun-v3.md': 29, 'AGENT-SCOPE-DO-AND-DONT.md': 14, 'DECISION-one-store.md': 4}
{'STALE': 15, 'UNCLEAR WORD': 6, 'MISSING STEP': 11, 'CONTRADICTION': 12, 'DEFERRED': 3}
```
Header counts (47 rows, 29/14/4, 44 with an edit) match.

## NOT DECIDED (lead; exact questions are in EDITS.md)
1. Real-take clean-up of saved runs: (a) turn saving off, delete runs, then remove container, or (b) container only?
2. Which login's password the owner types for the n8n database credential (plan section 10 points to the app login)?
3. Does the take's own n8n need the three credentials typed by the owner (step 8)?
4. Confirm EL-6 (take branches stay local) before any cloud-session ban is added; confirm E-12 gating wording.
5. Earlier open items stay: n8n database password storage, real-take port, Windows-to-WSL reach.

## Not checked
Nothing run except the text check; no code, smoke evidence or click paths read; the model-key revoke click path is unverified. Result of round 4 not reviewed. Nothing committed; no agents started.

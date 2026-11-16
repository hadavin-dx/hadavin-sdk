# Evidence v18 (EVIDENCE RUNNER: records only, no verdicts)

Run Mon 16 Nov 2026. Scratch copy: `<scratchpad>/v18/steps-edits/` (copies of check-v18.py, OWNER-SHEET-v18.md, LEAD-RELEASE-NOTE-v2.md, v18-MAP.md, v18-OPEN-FOR-LEAD.md). Raw output: `<scratchpad>/v18/raw.txt`; recompute script: `<scratchpad>/v18/recompute.py`. No git, no secret, no banned word printed.

## 0. Mismatches first (text vs the cited file)

| # | Where | Written | Real text | State |
|---|---|---|---|---|
| M1 | Sheet section 9 heading ("source of that time UNVERIFIED"); Note section 2 ("its source is not in any input I read"); Open 20 ("evidence runner found no source in decisions, facts or scope") | the post-by time Wed 25 Nov 2026 15:00 UTC has no source | A source exists: `ORDERS.md:150` (lead answer Q21.1: "post by Wed 25 Nov 15:00 UTC = 20:30 IST (the owner prefers Wed 18)"); `inputs/OWNER-STEPS-realrun-v3.md:130` ("Step 23. Post Wed 25 Nov 2026, 15:00 UTC = 20:30 IST"); `QUESTIONS.md:55` (asks it). Not in decisions, FACTS or AGENT-SCOPE, so the narrow statement "not in decisions, facts or scope" holds, the wider "not in any input I read" does not | MISMATCH (UNVERIFIED label is stale; the time itself is right) |
| M2 | v18-MAP.md RC-5 ("Open 24 says what to cut if you disagree") | Open 24 is the cut list | Open 24 is "Decision 7 lists only `y`, the challenge and `end`, yet the Sheet lists more owner tasks" (default: lead confirms the list). Nothing in Open 1 to 25 says what to cut for length | MISMATCH (wrong pointer) |
| M3 | Note section 2 and Open 6: "FACTS and AGENT-SCOPE say 'US$180 of 189 in-code backstop'" | the quoted phrase is in both | `FACTS-ALREADY-DONE.md:3` has exactly "US$180 of 189 in-code backstop". `AGENT-SCOPE-DO-AND-DONT.md:15` says "backstop setting, US$180 of 189 at the time of writing, checked by a human" (no "in-code") | PARTIAL (figures match; quotation exact for FACTS only) |
| M4 | Note section 5 default sentence "a made-up sales contact sent twice with the same id is processed once", labelled "(decision 1, narrow claim)" | decision 1 wording | `DECISIONS-2026-11-16.md:2` and ORDERS Q21.2 give "a lead sent twice with the same id is processed once". The note's sentence is a reworded form (made-up sales contact for lead), still labelled decision 1 | PARTIAL (wording differs; Q21.2 calls decision 1 "THE ONE WORDING") |
| M5 | DECISION-one-store line 14 (G20, Open 21): "still says ONE database" | true | `DECISION-one-store.md:14` reads "ONE database for everything we own: the single Postgres instance of the take". Lines 25-26 (CORRECTIONS 2026-11-16 (a)) already say n8n lives in a separate database `n8n`; the package does not mention these corrections | MATCH for line 14; context note only |

No other mismatch found (section 3 lists every item checked).

## 1. check-v18.py in a scratch copy (builder's output file not trusted)
Command (only the `D = ...` path line was changed to the scratch folder; the script's other read, `tests/test_no_reference_material.py`, stays on the real path): `python3 -I steps-edits/check-v18.py > raw.txt 2>&1; echo "EXIT $?" >> raw.txt`

Raw output:
```
lines: {'S': 98, 'N': 129, 'M': 185, 'O': 31}
ok: sheet lines 98
sheet headings: 9
ok: R1..R10 each defined once
ok: rule references checked
ok: G1..G29 each defined once
ok: gate groups checked
open rows: 25
ok: rule phrases checked
ok: glossary order checked
banned words: 10 listed, occurrences case-sensitive 0, case-insensitive 0
ok: word checks run
UTC = IST pairs checked: 13
ok: arithmetic, weekdays and UTC/IST pairs checked
map table rows: 161
ok: map checked
TOTAL PROBLEMS 0
EXIT 0
```
Exit code 0. The output (without the EXIT line) is identical to the builder's `v18-check-output.txt` (`diff` empty). My own banned-word count over the four files, check-v18.py and the output file: 0 each (10 entries).
Limit: the checker proves form (ids, counts, order of terms, arithmetic, weekdays); it cannot prove a statement true.

## 2. Independent recompute (python3 -I, `recompute.py`)

UTC to IST (add 5:30), every pair found in the four files:

| File:line | UTC written | IST written | IST computed | Result |
|---|---|---|---|---|
| Sheet:13 | 18:29 | 23:59 | 23:59 | OK |
| Sheet:40 | 11:30 | 17:00 | 17:00 | OK |
| Sheet:40 | 11:50 | 17:20 | 17:20 | OK |
| Sheet:40 | 12:00 | 17:30 | 17:30 | OK |
| Sheet:71 | 18:29 | 23:59 | 23:59 | OK |
| Sheet:97 | 15:00 | 20:30 | 20:30 | OK |
| Note:54 | 18:14:40 | 23:44:40 | 23:44:40 | OK |
| Note:56 | 11:30 / 11:50 / 12:00 | 17:00 / 17:20 / 17:30 | same | OK (3 pairs) |
| Note:56 | 17:59:00 | 23:29 | 23:29 | OK |
| Note:56 | 18:19 | 23:49 | 23:49 | OK |
| Note:56 | 18:29:00 | 23:59 | 23:59 | OK |
Map and Open hold no UTC/IST pair. Total 13 pairs in Sheet and Note, 0 wrong.

Weekdays (2026-11-xx): Mon 16 (Sheet:2, Note:3, Map:3, Open:3), Wed 18 (Sheet:35, Note:53, Note:56), Mon 23 (Sheet:13, Sheet:46, Note:56 "On Mon 23 Nov"), Wed 25 (Sheet:97, Open:26): all computed equal written. 0 wrong.

Arithmetic:

| Item | Written | Computed |
|---|---|---|
| 18:29:00 minus 860 s | 18:14:40 | 18:14:40 |
| window end minus 30 min | 17:59:00 | 17:59:00 |
| Worked example 1 (PS 11:00, SL 30, RL 10, FP 10, M 10, need 860) | PS+SL 11:30; LS 11:30; LF 11:50; CB 12:00 | 11:30; min(11:30, 18:14:40, 17:59) = 11:30; 11:50; 12:00 |
| Worked example 2 (PS+SL = 18:10) | earliest term 17:59:00; LF 18:19; CB 18:29:00 | 17:59:00; 18:19; 18:29:00 |
| Sheet sample: 11:30 + 20 = 11:50; 11:50 + 10 = 12:00 | as written | OK |
| Price (40,000 x 3 + 10,000 x 15) / 1,000,000 | 0.27 | 0.27 |
| Run total 3 x 0.27 | 0.81 | 0.81 |
| Backstop 12.40 + 0.81 | 13.21 | 13.21 |
| Money used 3.90 minus 3.10 | 0.80 | 0.80 |
| Sheet:41 run length 10 + film pause 10 | 20 | 20 |
| v16 counts A 2 + B 10 + C 1 | 13 submissions | 13 |
| Sample cancel-by 12:00 not later than window end 18:29; LS 11:30 not later than 18:14:40 and not later than 17:59 | as stated in checks (2) and (4) | OK |

## 3. Citations opened (MATCH / MISMATCH)

Inputs cited, with real text:
- DECISIONS 1 (narrow claim): `DECISIONS-2026-11-16.md:2` "a lead sent twice with the same id is processed once": MATCH (M4 notes the reworded sentence).
- DECISIONS 2 (take never deletes; read-only): line 3 "the take never deletes contacts": MATCH (Notes 0.1, Open 1, Open 5).
- DECISIONS 7 (owner only types y, challenge, end; n8n_api.py): line 8: MATCH (G3, G22).
- DECISIONS 8 (loopback re-smoke plus ONE made-up lead in take prep): line 9: MATCH (G13, G15, Open 18).
- DECISIONS 9 (rehearsal screenshot or Postgres node preview): line 10: MATCH (G11).
- DECISIONS 10 (wording "one Postgres server with two databases"; fix line 14): line 11: MATCH (G20, Open 21).
- DECISIONS 5, S9-2 (owner compares settings figures by eye; program does not print them): line 6: MATCH (Note 9 last bullet, R4, sheet 5.7).
- FACTS: key saved earlier, "no limit questions, just tell him the number", "US$180 of 189 in-code backstop", model credential in n8n's store ("credentials for HubSpot, Claude, Gmail kept in n8n's own credential store"): `FACTS-ALREADY-DONE.md:3`: MATCH (M3 for AGENT-SCOPE side). Note G23 "FACTS is the source" for accounts: MATCH (throwaway Gmail, HubSpot test account, n8n account listed).
- AGENT-SCOPE section 3: take archives contacts via DELETE at `run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, review F-01, "CODE-CHANGE-NEEDED, not fixed" : line 20: MATCH (dated 2026-11-15 round 9: MATCH).
- AGENT-SCOPE `run_real_check_n8n.py:573` notice text "B ten times at once" is a literal string: line 23 (N-i): MATCH, UNVERIFIED against final head as the note says.
- AGENT-SCOPE:15 window end 2026-11-23 18:29Z refusal; tests qs_37 and evidence on older heads (G16, Open 15): lines 15-16: MATCH.
- AGENT-SCOPE "B ten times" (Open 7): MATCH.
- DECISION-one-store line 14 "ONE database": MATCH (M5).
- Q20.3 (UNKNOWN, read-only claim wording), Q20.4 (lead reads exit code at final head, state none), Q20.1 and Q20.2 (G8, G19), Q21.1 (target Wed 18 Nov not fixed, latest Mon 23 Nov before 18:29 UTC), Q21.2 (no takeover after lease; "THE ONE WORDING is DECISIONS 1" plus a lease sentence), Q21.3 (caption "one Postgres server, two databases"): all in `ORDERS.md:144-153`: MATCH. (Q-numbers are in ORDERS.md, with questions in QUESTIONS.md:47 and :54.)
- plan line 121 ports (5690 rehearsal n8n, broker 5691, control 5692/5693, owner's 5678/5679): `plan-wp6-resmoke-v5.md:121`: MATCH (G7, Open 4).
- plan-v10 lines 456-459 (departure note, Lead decision 6, Text A, Text B; Text B "up to three tries in total", "a gap longer than the lease is not claimed"): `paste-check/plan-v10-real-v5-edits.md:456-459`: MATCH.
- v3 exit codes (0 pass; 1 not `y` or confirmation mismatch; 2 refusal incl. Ctrl-C before first send; 3 count or verdict failure incl. Ctrl-C after sends began), marker `~/.hadavin-take-tags/<id>.used`, lock `take-<tag>.lock`: `inputs/OWNER-STEPS-realrun-v3.md:97, 170, 172`: MATCH (Note section 9).

Earlier versions cited:
- v16 sheet section 5 (A twice with same person id, B ten times at once, C once while n8n is off and on, 13 submissions): `OWNER-SHEET-v16.md` section 5 lines 303-322: MATCH (Note 5, Open 7). v16 sample notice and result layout agree with sheet 3 sample (changed fields noted by builder).
- Open 15 of v17 (contact ids: no file gives them): `v17-OPEN-FOR-LEAD.md` item 15: MATCH (Open 10).
- v17 reviews (`review-v17-stranger/security/contradiction/adversarial.md`, `root-cause-reader-1.md`): all 123 non-BR ids in v18-MAP.md (ST-B1..B7, M1..M18, T1..T5, N1..N15, ST-Never; SE-B1..B2, M1..M12, N1..N6, SE-D; CO-1..CO-22, CO-drift; AD-B1..B4, M1..M15, N1..N6; RC-1..RC-5) map to an item of the same number and topic in those files: MATCH, 123 of 123. Topic read for every item (the review files use B1, M1, 1 to 22 numbering; the MAP prefixes them). Exception: M2 above is about the pointer, not the id.
- Pointers inside the MAP (Sheet R1-R10, 5.x, 6.x, 7.x, 8.x, Note G1-G29 and sections 0-9, Open 1-25): all targets exist; one wrong content pointer (M2).
- Note and Open internal pointers ("Open 1 and 2", "Open 9", "Open 10", "Open 12", "G12", "G14", "G20", "section 5"): all targets exist and say what is claimed (spot-read each).

Counts: I did not number every citation one by one. Checked: the input files (DECISIONS 1, 2, 5, 7, 8, 9, 10; FACTS; AGENT-SCOPE lines 15, 20, 23; DECISION-one-store 14; ORDERS Q20.1-Q21.3; plan line 121; plan-v10 456-459; v3 lines 97, 170, 172), v16 section 5, v17 Open 15, and 123 of 123 non-BR map ids. Result: 3 mismatch or partial text items (M1, M2, M3), 1 wording drift (M4), 1 context note (M5); everything else MATCH.
Could not open: the brief's lettered list (a) to (s) (map ids BR-a to BR-s) and the readiness list is not a file I could locate; I only checked that BR-M3..M15 and BR-N1..N6 match `review-v17-adversarial.md` M3..M15 and N1..N6 (MATCH) and that each BR row points to a section that exists. Also not opened: the take scripts, flows and model program (not in this checkout), so no statement about them was checked; `egm\` studio folders and `memory\` files named in FACTS.

## 4. Rule and term counts in OWNER-SHEET-v18.md (98 lines, 9 headings)

| Item | Count | Lines |
|---|---|---|
| R1 | 3 mentions (1 definition row, 2 elsewhere) | 22 (def), 31, 73 |
| R2 | 11 (1 def, 10 elsewhere) | 17, 22, 23 (def), 24, 25, 31, 56, 75, 78 |
| R3 | 15 (1 def, 14 elsewhere) | 17, 22, 24 (def), 25, 26, 27, 31, 58, 59, 75, 85, 88 |
| R4 | 2 (1 def, 1 elsewhere) | 25 (def), 69 |
| R5 | 2 (1 def, 1) | 26 (def), 85 |
| R6 | 4 (1 def, 3) | 27 (def), 85, 87, 88 |
| R7 | 3 (1 def, 2) | 28 (def), 31, 92 |
| R8 | 2 lines, 3 mentions (def row 29 holds 2; R6 row holds 1) | 27, 29 (def) |
| R9 | 2 (1 def, 1) | 30 (def), 95 |
| R10 | 11 (1 def, 10) | 2, 7, 22, 25, 27, 28, 31 (def), 70, 79, 83, 84 |
Each of R1 to R10 is defined once (rows 22-31). In the Note: R1 2, R2 4, R3 1, R4 1, R5 2, R6 0, R7 2, R8 0, R9 1, R10 1 mentions (pointers only).
- Ban list: sheet contains no ban list (0 occurrences of "ban list"); line 15 says the post checker holds the list ("forbidden claims", 1). Note section 5 holds it once ("Ban list", 1).
- Film rules: stated in R9 (line 30); line 95 (8.5) says "check the film rules in R9" (pointer); Note section 5 "Film content" (1) points to R9; Recording ON/OFF appears in R6 (27), R9 (30, twice "Recording is ON"), 7.1 (82), 7.6 (87) as actions, not as rule re-statements.
- Window end: glossary line 13 (definition, includes "18:29 UTC = 23:59 IST"); sample notice line 45 (`Window end: 2026-11-23 18:29 UTC`, a copied sample); check line 46 (use of the term); 5.7 line 70 (setting figure) ; yes line 71 ("window end 2026-11-23 18:29 UTC = 23:59 IST"). The phrase "18:29 UTC = 23:59 IST" appears 2 times (13, 71), "18:29" 3 lines (13, 45, 71), term "window end" 6 times on 5 lines. Note repeats it 0 times as the full phrase except the worked example (18:29:00 UTC = 23:59 IST, line 56).
- Charset: stated once (R9, line 30, "Values the lead sends may hold only letters, digits, single spaces and . _ / - : = ? & % ~ @ + ,"). The word "charset" does not appear.
- Post-by time: once (line 97).

## 5. Not checked
Truth of any statement about code, flows, pages, button words or Windows menus (UNVERIFIED in the text); wording quality for a non-technical reader; whether the checker's glossary rules are the right rules; Note sections 3, 8 content against any file (no source exists); the plan beyond lines 121 and 183-559 for other claims (not cited).

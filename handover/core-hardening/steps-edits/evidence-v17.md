# Evidence v17 (raw, no judgement)
Run 2026-11-16 by the evidence runner. Folder: handover/core-hardening/steps-edits.

## 1. check-v17.py (python3 -I check-v17.py)
exit code: 0
lines: {'S': 71, 'N': 103, 'M': 254, 'O': 25}
ok: sheet lines 71
sheet headings: 8
ok: R1..R10 each defined once
ok: rule references checked
ok: G1..G24 each defined once
open rows: 19
ok: rule phrases checked
ok: glossary order checked
banned words: 10 listed, occurrences case-sensitive 0, case-insensitive 0
ok: word checks run
map table rows (all, including header and separator rows): 227
ok: map checked
TOTAL PROBLEMS 0
diff against v17-check-output.txt: identical

## 2. Citations (MISMATCH first)
MISMATCH: v17-MAP.md line 210 "n3 418 lines | Sheet is 70 lines". wc -l OWNER-SHEET-v17.md = 71 (check-v17.py also prints S: 71 and "ok: sheet lines 71"). Quote: "| n3 418 lines | Sheet is 70 lines |". (418 not re-checked: v16 sheet.)
MATCH: Note section 5 and Map item 10: "plan-v10 lines 456 to 459 ... paste-check/plan-v10-real-v5-edits.md": line 456 "Departure from the lead's order"; 458 "Text A (lead answer Q15.3 ...)"; 459 "Text B (lead answer Q21.2 ...": "Recovery re-claims an unfinished lead whose 45 s lease ran out, up to three tries in total including the first".
MATCH: Note section 2, Open 13 "take program's own start margin of about 860 s (v3 line 171)": inputs/OWNER-STEPS-realrun-v3.md:171 "...finish about 860 s (about 14 minutes...) before TAKE_WINDOW_END_UTC".
MATCH: Note G16 "AGENT-SCOPE:15 says it exists": inputs/AGENT-SCOPE-DO-AND-DONT.md:15 "...or after the configured window end (2026-11-23 18:29Z)". (It says the end is configured; whether it refuses a call is not stated; sheet marks UNVERIFIED.)
MATCH: Open 7 "FACTS: US$180 of 189 in-code backstop; AGENT-SCOPE says the same": FACTS-ALREADY-DONE.md contains "US$180 of 189 in-code backstop"; AGENT-SCOPE:15 "backstop setting, US$180 of 189 at the time of writing".
MATCH: Open 10, G20 "DECISION-one-store line 14 ... ONE database": line 14 = "1. **ONE database for everything we own: the single Postgres instance of the take**".
MATCH: Decision numbers in inputs/DECISIONS-2026-11-16.md: 1 narrow claim "a lead sent twice with the same id is processed once"; 2 "TAKE IDENTITY is read-only: the take never deletes contacts"; 6 "rehearsal 5690 ... 5678/5679 are the owner's own"; 8 "loopback re-smoke plus ONE made-up lead in take prep"; 9 "rehearsal screenshot or the Postgres node preview"; 10 "one Postgres server with two databases (n8n's own and the take's)". Decision 7 as cited (owner roles): decision 7 in the file is "n8n first-visit owner setup is already done ... the owner only types y, the challenge and end" - it does NOT list the owner role items (key creation, cancel, deletes, app password revoke). Open item 6 and Note G22 say "Owner role under decision 7: key creation, key cancel, contact deletes, app password revoke". RECORDED AS MISMATCH (not checked whether another file holds a decision 7 with those roles; grep of the inputs folder found none).
MATCH: Q ids against ORDERS.md: Q20.3 (l.147 unknown, ask owner once), Q20.4 (l.148 exit code read at final head, do not state one), Q20.5 (l.149 patch text), Q21.2 (l.151 "THE ONE WORDING is DECISIONS 1" plus lease sentence), Q21.4 (l.153 "lead computes").
NOT CHECKED: Q15.3 only appears via plan-v10 line 458 (not opened in ORDERS); "plan-v10 ... Text B says recovery re-claims" matched above.

## 3. Dates (date -u -d)
16 Nov 2026 = Mon; 18 Nov 2026 = Wed; 23 Nov 2026 = Mon; 25 Nov 2026 = Wed. All match the files ("Mon 16 Nov", "Wed 18 Nov", "Mon 23 Nov", "Wed 25 Nov").
2026-11-23 18:29 UTC = 2026-11-23 23:59 IST (match "18:29 UTC = 23:59 IST").
2026-11-25 15:00 UTC = 2026-11-25 20:30 IST (match "15:00 UTC = 20:30 IST").
Take-start deadline in v3: 18:29 minus 860 s = 18:14:40 (matches v3 text; Note says about 860 s).

## 4. Counts
Rules R1-R10 rows in sheet section 2: 10 (each defined once, per checker).
G1-G24 rows in Note: 24.
Open items rows in v17-OPEN-FOR-LEAD.md: 19 (numbers 1..19).
OI-1..OI-38 in the map: all 38 present (distinct ids found: 38; section 2 table has each).
Lines: sheet 71, note 103, map 254, open 25.

## 5. Banned vendor strings
BANNED read by ast from tests/test_no_reference_material.py: 10 entries. Occurrences (case-sensitive / case-insensitive): sheet 0/0, note 0/0, map 0/0, open 0/0.

## Not checked
- Words/numbers cited from v16 files and reviews (finding ids M-A..M-H, B1..B3, SC1..SC7, OI numbering mapping to v16 content, "57 underscore lines", "23 rows", "about 45 values", "v3 shows" other than line 171, "418 lines").
- Q15.3 in ORDERS; that decision 7 exists elsewhere.
- That check-v17.py itself is correct; no live system, flow, script or n8n inspected (none in the checkout).

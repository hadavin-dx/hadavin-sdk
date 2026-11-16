# fix-f5-r6: change log of round 6 for RUNSHEET-WORDING.md (2026-11-16)

## What failed, what is uncertain, what I did not check (first)
- Nothing was run except the read-only checker. No review follows. Strings are PROPOSED, not paste-ready.
- The desk script as checked in DOES archive made-up contacts at the end of a run (reviews-f1/trace-desk-repo.md; crm_hubspot.py:492-499, DELETE at :497; run_real_check.py:993, :1101-1107). So B-067, B-091, B-215 and the new B-215b say "the take is set up so that it does not delete or archive contacts (lead decision 2026-11-16, item 2); the desk script as checked in archives ... so the coordinator confirms which applies". They stay HELD under P4c. What the take script really does is UNCHECKED (script absent).
- Not re-checked: the A-010 pruning facts beyond N8N-START.md:42,47 (UNVERIFIED for the laptop n8n version); how many leads the take posts (B-010, UNCHECKED); that no other address shows (A-084, UNCHECKED).
- B-213 paste unchanged (it never said the take does not delete); only its note changed. Majors 4 asked for it by id; I list it as note-only.
- Edits were made with the Edit tool (plus one small Python replace for the row-count sentence); unchanged rows are byte-identical (diff against backup shows only the ids below).

## Rows changed, by id
A-084 (paste, note), A-010 (paste, note), A-010b (paste, note), A-053 (paste, note), B-010 (paste, note), B-067 (paste, note), B-091 (paste, note), B-215 (where, paste, note), B-213 (note only), A-012 (note: cite), X-5a (note: cite), X-5b (note: cite), table rows P2 and P4c in section 0b (cite; P4c adds B-215b and the desk-script fact).
New rows: B-215b (OWNER-STEPS-realrun-v3.md:104 Ctrl-C still archives; HELD), B-219 (OVERSTATED in CLAIMS-TABLE.md; safe wording: add "with the real services", drop the three UNTRACED clauses).
Prose lines (not rows): Status line, 0-words lines (studio owner, coordinator, laptop agent), D1, D2, D3, P1, P2, P4a, P4b, P4c definitions, step 1 of section 0, Q-A, "Not checked" line in Read first, counts line in section 6 (152 rows: 38/17/56/41; 73 ids).
All line-number cites into CLAIMS-TABLE.md are gone; cites are now by section heading or claim id (grep for "CLAIMS-TABLE.md line" returns nothing).

## Majors of review r5b
1 cites: fixed (D1-D3, P checks, A-012, X-5a/X-5b, roles). 2 A-084: fixed. 3 A-010/A-010b/A-053: hedged to pruning (UNVERIFIED). 4 B-091/B-067/B-215/B-213: set-up wording plus desk-script fact, B-215b added. 5 B-215 cites :103, :95, :104. 6 B-010: "three" removed, two leads per VIDEO-RUNSHEET.md:31-33. Nits not touched (past cap, none free).

## Checker (tools/check_runsheet_paste.py)
No arguments: prints usage, exit 2. Unreadable file: exit 2. Verdict is read by id from cells 4 to 6 by word, not by a fixed cell number.
Run: `python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md` -> 152 rows, 73 flagged ids, none missing, RESULT: PASS, exit 0. CLAIMS-TABLE.md state checked: mtime 2026-11-16 10:11:33 UTC, 206924 bytes (it had not changed when I re-ran at the end; the claims fixer may still change it, re-run the command after it finishes).
Backup of the start file: scratchpad RUNSHEET-WORDING.bak and check.bak.
Nothing committed.

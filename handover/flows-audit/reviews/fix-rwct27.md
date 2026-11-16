# Fix round 27, RW and CT (one fixer; edited only RUNSHEET-WORDING.md and CLAIMS-TABLE.md; nothing committed)
## Uncertainty first
- I checked each finding against the file text; all six held. The wording I chose is mine; not re-read by an independent reviewer. A fresh reader should check the new A-098 and B-054 strings.
- No verdict word changed. No row count changed (PASTE 53, HELD 89, DELETE 30, NO PASTE 9, SUPERSEDED 14; CT 330 unique). HubSpot id vs vid stays UNVERIFIED. Q28 scoped claim untouched.
- CT row 26 still carries [OUT OF THIS VIDEO]: this is a page-file edit (RW column PAGE), not video text, so I judged the tag correct and left it; the reviewer's mismatch concerned the wording, now fixed.
## Finding to result
| Finding | Check | Result |
|---|---|---|
| M1 lead ID = person | true (RW A-016d) | RW A-016d and CT 11, 91, 526 now: "a code that the sender gives to one request for contact" |
| M2 A-098 "The cause is" | true | New string (RW A-098, CT row 26 and A-098 row): "The 720 s alert hold (statement 9) is part of the explanation: ... This is read from the v4 flow and was not observed in this test; 720 s alone does not add up to 13 minutes." Stays PASTE |
| M3 stale "still say 2 runs" in CT row 19 | true | sentence deleted |
| M4 extra lead sentence in B-067, B-091 cells | true | removed from both CT cells; also "the owner" changed to "the studio owner" so the cells equal the RW strings (rows 969/971, B-213 text, keep it: not in a paste cell checked by the finding) |
| Lower B-054 | true | RW and CT (row 325 and B-054) string: "K1 (n=5): V5-README.md line 17 says not run on film-v5. T1 (burst of 10): no run file seen." |
| Lower B-165 | true | RW, CT 341, CT 901: "first next try after 60 s, each later wait 60 s longer than the one before, no wait longer than 300 s"; RW N-4a note aligned |
## Raw outputs (run from handover/flows-audit)
- check_refs: PASS 5171 references
- check_names: PASS 655 rows
- check_secrets: PASS 0 hits in 2696 files
- check_rw_ct_pairs: paste strings in RW: 140 | found word for word in CT: 140; not found 0
- check_runsheet_paste: total rows: 195 ... RESULT: PASS
- claims-count: ids: 330 unique: 330, offenders: 0
- ruff format --check .: 844 files already formatted

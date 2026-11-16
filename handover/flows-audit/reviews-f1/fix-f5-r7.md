# fix-f5-r7 (F5 round 7, text path, nothing run)

First failure: check_runsheet_paste.py exit 1, claim ids B-016, B-019, B-038, B-088, B-092 had no row.
Rows added to RUNSHEET-WORDING.md section 3 (plans, notes, READMEs; same file neighbours): B-016, B-019, B-038 (after B-017), B-088, B-092 (after B-095). All marked UNVERIFIED (nothing ran); wording from the CLAIMS-TABLE.md rows and the desk repository trace.
Second failure: B-038 paste had an apostrophe; reworded. Coverage line updated (157 rows, section 3: 61).
Backup: scratchpad RUNSHEET-WORDING.md.bak-f5r7.
Final: checker run twice, rc 0 both times, "RESULT: PASS", missing ids [].
CLAIMS-TABLE cites: RUNSHEET-WORDING.md cites CLAIMS-TABLE.md by section name and claim id only, no line numbers, so none can miss.

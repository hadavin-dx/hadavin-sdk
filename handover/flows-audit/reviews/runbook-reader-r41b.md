# RUNBOOK lines 215-232 (steps 1-14 table rows) round 41b stranger read, non-security. Saved by flows-audit, condensed; unverified; static. NOT read: RUNBOOK 1-214, 233-428.
0 Blockers, 17 Majors, grouped:
- shas.env vs ENVSH location differs (L219, 221, 223, 231); TAKE_FOLDER missing from need_set (L219, 221, 225); SHA_PIN/SHA_PIN2 naming.
- Step 8: no clear PASS for (0b),(i),(ii-b); no named account for DB_SETUP/DB_GRANTS; row 7 vs row 8 contradict on SQLite/Postgres.
- Forbidden-port guard only after n8n start; step 6 timing 04:54Z vs 20-minute; n8n_api.py not in copy loop; harmless call has no expected output.
- Step 4a FILES list pasted from 14(g), subjective PASS; PIN_RECEIPT source differs 4b(d) vs 13(d); 4b pass cell lacks "pin sha256 XXXXXXXX".
- git checkout restore commands vs "never by git checkout"; webhook probe "exit 0" vacuous.

# Probe: does a `--` line comment end at a carriage return on PostgreSQL 16? (run by the orchestrator, 2026-11-05, throwaway server on 127.0.0.1:54329, psql 16 `-c`, which sends the text unlexed)
Command 1: psql -At -c $'SELECT 1 -- x\r, 2'   Output: `1|2`  (the comment ended at the CR; `, 2` was read as live SQL)
Command 2: psql -At -c $'SELECT 1 -- x\n, 2'   Output: `1|2`  (control: LF ends the comment)
Command 3: psql -At -c $'SELECT "set_config"(\'application_name\',\'q\',true)'  Output: `q`  (a quoted identifier call works)
Command 4: psql -At -c $'SELECT set_config /*c*/ (\'application_name\',\'q\',true)'  Output: `q`  (a comment between the name and `(` works)
Result: P3a round 6 ADV-R6-2 (CR ends a line comment) and ADV-R6-3 (quoted and spaced `set_config`) are CONFIRMED on the server. psycopg is not installed here, so the same text through the driver was not run.

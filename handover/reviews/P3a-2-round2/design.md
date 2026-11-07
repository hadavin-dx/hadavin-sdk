# PR 73 (P3a-2) @ea40242: round 2, design/security review (fresh reviewer; findings condensed by the coordinator, ids kept)
Read the diff to line 632, migration_numbers.py 196-690, ticket. Ran nothing; UNVERIFIED by execution. The `$`-name regex fix is sound; no way found to pass a real role grant as an object grant through the regex alone.
F1 Major | migration_numbers.py:647-689, migrate.py:230-306 | Role-grant rule matches only at statement start; read-back has no pg_auth_members snapshot. A `$$` function body holding GRANT r TO s, then `SELECT f();`, passes. Docstring/CHANGELOG read as a guarantee. Fix: add a membership snapshot to the read-back, or reword to "plain statement form only".
F2 Major | CHANGELOG repair header, cases (g),(a) | Hand files set no lock_timeout; ALTER TABLE tool_calls needs ACCESS EXCLUSIVE on a live table. Fix: SET LOCAL lock_timeout='5s', statement_timeout='60s' in header.
F3 Major | CHANGELOG case (e) E1/E3 vs case (b) | E1/E3 skip the (g) existence and column-shape block that (b) says is required. Fix: always include the (g) block in E1/E3.
F4 Nit | case (g) final DO check compares columns only, claim is wider (PK on call_id/run_id, index tool_calls_by_run). Fix: check them or reword.
F5 Nit | case (b) renames a ledger row on file name only; no content check; point at the hash manifest.
F6 Nit | runbook prints unquoted `SET search_path TO <schema>`; recipe quotes it. Quote in text.
F7 Nit | case (a) "current_user is the migration role" is only a sentence; add a DO assertion.
F8 Nit | case (b) placeholder has an apostrophe; use <file_stem>.
F9 Nit | migrate.py:251-255 triggers keyed by tgrelid; drop/recreate table with trigger gives false refusal. Key on (schema, table, name).
Fine: lock number 3760701656253510835 derivation; "run twice is safe" for (a); DO rename check; (g) scope; recipe passes _refuse_entry; re-export keeps old imports.

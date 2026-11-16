# P3a round 5, adversarial (egm:egm-design), head 60fedf6. Condensed by orchestrator. Verdict: 1 BLOCKER, 4 MAJOR, 5 MINOR.
| id | sev | problem | fix |
|---|---|---|---|
| R5-1 | BLOCKER | An interactive psql `\i` of a missing file does not abort the transaction, so the following INSERT marks the migration applied though it never ran. | Non-interactive `psql -v ON_ERROR_STOP=1 -f recipe.sql` with a `DO` check; a real psql test. |
| R5-2 | MAJOR | Non-ASCII dollar-quote tags not handled by the lexer. | Lexer rule plus test. |
| R5-3 | MAJOR | `DO $$`/`EXECUTE` bodies bypass the role/GUC refusal; `ALTER ROLE ... SET` and `DROP OWNED` missing. | Refuse them. |
| R5-4 | MAJOR | P4d-c lock-in allow-list misses the P3a test files. | Coupling row to P4d. |
| R5-5 | MAJOR | Cut surface: trim the refusal list to (c),(d); layer 1 at first tag; gate runbook (e) on the owner's answer; cut four hypothetical file-state tests. | Apply order 7(3). |
| R5-6 | MINOR | CREATE SUBSCRIPTION mutant is equivalent. | Drop. |
| R5-7 | MINOR | H7c contradicts the rule. | Fix. |
| R5-8 | MINOR | Files read three times (TOCTOU). | Read once. |
| R5-9 | MINOR | DSN on the command line; schema is a placeholder. | Use env/service file; name schema. |
| R5-10 | MINOR | Rename stem rule. | Clarify. |
Round 5 reached: written escalation to the lead is due (see questions-for-lead.md).

# Hand-off v14: what only the lead can decide (one line each; silence never counts as a yes on a money rule)

Format: id | default if you do not answer | why | who decides.

- **L7** | the `Infinity` clause is NOT built; the held file carries Q34's exact `CHECK (usd >= 0)`, which lets a not-a-number total in | Q34 named only `usd >= 0`; v13's "no objection by 2026-11-30 means yes" is removed because silence must not approve a money rule | lead.
- **L9** | DB-2 (key guard and decrease record) is NOT built | it is beyond Q34 | lead.
- **L10** | DB-1 stays one PR and carries the held-file seam, `owner_gates.py`, `check_owner_gates`, CODEOWNERS and the Sonar exclusion, labelled so in 7.1 | that is more than Q34's one SQL file; the alternative is a DB-0 PR with the seam only | lead.
- **L11** | start gate G-4(iii) (the D5 money-unit answer) is NOT applied to DB-1 | Q28 says D5 is non-blocking; v13 had made it a condition | lead.
- **L12** | the portal role gets `SELECT` only on `spend_decrease_log`; without a second database address `limits status` prints "decrease record: not read", never 0 | someone must be able to read the record without giving the agent role read access | lead.
- **Retention (security M1)** | export with a sha256, then delete rows older than 400 days with the migration role, by hand only; warning at 1,000,000 rows or 400 days | my numbers, no source; grows 136.4 bytes per row, +0.26 ms per lowering (`evidence-handoff-v14/raw-pg-m3-v14.txt`, one run) | lead.
- **Fail-closed decrease log (security M1)** | stays fail-closed: if the log cannot be written, the lowering is refused | safe side of a money rule; costs a refused settle | lead.
- **Operator step REVOKE TEMPORARY (security B1, defence in depth)** | recommended and checked at start-up in `prod`, warning in `pilot` | needs the database name and a person with the migration role | owner (operator action).
- **Carried-PR edits (Q34)** | applied as disclosed in the other-tracks file: PR-2 `_Mapping` wording, hot-file column, K1 "(new)" marks, H-2 grep bound | content changes to PRs meant to be carried unchanged; you may refuse any | lead.
- **O1** (releasing a 429) | NOT released (a failed attempt stays booked) | unchanged from v13; money rule | owner.
- **D5** (money unit of any new spend table) | OWNER-OPEN, non-blocking, no default | Q28 | owner.

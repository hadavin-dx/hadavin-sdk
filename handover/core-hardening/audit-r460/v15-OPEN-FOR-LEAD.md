# Hand-off v15: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v15.md` section 10.

**Fact first (security minor 3).** Q34 says the check "only refuses a negative total". That is true for the total after the write, but a database check on an INSERT is tested on the row being inserted, so a lowering has to be written as an UPDATE (tested on the PostgreSQL 16.15 run, `evidence-handoff-v15/raw-pg-v15-run1.txt`). A total lowered below the size of a new amount blocks that agent-day (the write is refused; it fails closed). Check that no older writer sends negative amounts (section 5.4).

## OWNER-OPEN (the owner's own yes; nothing built or applied without it)
- **L7** | the extra clause (refuse Infinity) is NOT applied; the default held file is exactly Q34's `CHECK (usd >= 0)` (sha256 5d765255...cc1093) | the clause is a variant file with its own sha256 (bd0409c9...d9fe84); a yes names which sha256 it covers | owner.
- **L9** | DB-2 (key guard and decrease record) is NOT applied | beyond Q34; needs PostgreSQL 14 or newer (not stated before v15) | owner.
- **L16** | no delete path is built; the decrease record only grows | trimming rows is a new delete path with no yes, no negative test, no audit note yet | owner.
- **L17** | the meaning of Q27 is not assumed | see other-tracks file, O-6 | owner.
- **D5** | not a gate: held tables keep dollars | money-unit answer; Q28 says non-blocking | owner.

## Needs the lead
- **L10** | DB-1 stays one PR carrying seam, `owner_gates.py`, CODEOWNERS, Sonar exclusion | alternative: a DB-0 PR with the seam only (conditional tests in 7.2) | lead.
- **L11** | G-4(iii) does not apply D5 to DB-1 | per Q28 | lead.
- **L12** | ANSWERED by the lead: the record is read by a new AUDIT READER role (SELECT on `spend_decrease_log` only). v15 specifies its policy, per-action reasons and negative tests in 5.6(h); the role code (`Grant(audit_read=)`, `migrate(audit_reader_role=)`) does not exist yet, so it is UNVERIFIED as product code | lead (done).
- **L13** | the log stays fail-closed; retention numbers are thresholds in config, my numbers, no source | lead.
- **L14** | DB-1 is applied only after S-2a store code runs (G-4(i)); a new condition on Q34 | lead.
- **L15** | content edits to carried PRs listed | lead.
- **O1** | unchanged from v14 (section 10) | lead.

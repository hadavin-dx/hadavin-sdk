# Hand-off v16: what only the lead or the owner can decide (one line each)

Format: id | default if unanswered | why | who decides. Silence never counts as a yes on a money, delete or secret rule. Full text: `CORE-PR-HANDOFF-v16.md` section 10.

**Fact first.** Since v16 the code itself refuses a negative or not-finite total (no held file needed, 5.4 item 4b). A database check on an INSERT is tested on the row being inserted, so a lowering is written as an UPDATE (run on 16.15, `evidence-handoff-v16/raw-pg-v16-run1.txt`). All Postgres results are 16.15 with password logins; 14 and 17.10 are not run.

## OWNER-OPEN (the owner's own yes; nothing built or applied without it)
- **L7** | the extra clause (refuse Infinity) is NOT applied; the default held file is exactly `CHECK (usd >= 0)` (sha256 5d765255...cc1093) | variant `spend_nonneg_finite.sql` (bd0409c9...d9fe84) and upgrade `spend_nonneg_upgrade.sql` (fafa71fa...91f) each need their own yes naming the sha256; the upgrade needs PG 14+ | owner.
- **L9** | DB-2 (key guard, decrease record, and since v16 the kill-switch record and append-only triggers; sha256 4c37aea8...0647) is NOT applied | needs PG 14+; measured +0.061 and +0.049 ms per lowering, 110.6 bytes per row | owner.
- **L16** | no delete path is built; the records only grow; an accidental delete is refused even for the owner (H1 to H5) | a deliberate delete is the owner's decision | owner.
- **L17** | the meaning of Q27 is not assumed | other-tracks file, O-6 | owner.
- **D5** | not a gate | non-blocking (Q28) | owner.

## Needs the lead
- **L10, L11, L14, L15** | unchanged from v15 (section 10) | lead.
- **L12** | ANSWERED (audit reader role, SELECT only). v16: the agent never holds its secret; operator command line only (5.6 g2) | lead (done).
- **L13** | v16 adds: who runs `limits status --check` on a schedule and who is told when it exits non-zero; nobody is named | lead.
- **L18** | the lowest supported Postgres version is not stated anywhere I read; default: the upgrade file and DB-2 are marked PG 14+ | and an independent run of `pg_run_v16.sh` on 14 and 17 | lead.
- **L19** | `REVOKE TEMPORARY ON DATABASE <db> FROM PUBLIC` is an operator step (G-4(v)); who runs it, which databases | lead.
- **L20** | the unchanged tree fails 2 repository guard tests outside this folder (`tests/test_no_reference_material.py`: 2 non-UTF-8 files under `handover/core-hardening/lead-repin/`; `tests/test_repo_rules.py::test_licences_are_proprietary`: 10 files under `handover/promotion-inputs/`) | who fixes them; every PR gate needs green pytest | lead.
- **L21** | S-1 size unmeasured; proposed split S-1a and S-1b; default: not split | lead.
- **O1** | unchanged | lead.

# core-b ANSWERS 16:28Z (head ec67808ec, load /proc/loadavg: 1.06 1.22 1.58)
## Rows (branch | sha | state)
B1 stop-state failures | cloud/core-b 6a688ae57 | DONE
B2 money_definer failures + mutant baselines | cloud/core-b e337feb6e, 84fa98213 | DONE
B3 audit_drain 7 + spend_reservations_pg 6 | cloud/core-b (T1/T2/F7/R1 merges) | DONE
B4 parallel-run isolation (W1) | cloud/core-b 6a688ae57 | DONE (test-side pg_gate; _money_table_writers NOT weakened)
B5 A-audit-rights | local/code-MAB5 (worktree /tmp/core-b-wt/MAB5; base wip/cloud-core-b/merge-migrate 55df54150) | BUILDING (sonnet AB5); not pushed
B6 B2 live path reserve/settle | cloud/core-b 5931cf3b3, d070fda3d, a34597a4a | DONE
B7 fresh reviewers | per merged diff | DONE for all merged diffs (latest: H3 round 2 clean)
## core-a rev-b-newest2.md, the three Majors
1 NOINHERIT / INHERIT FALSE bypass of the start check: FIXED 9b7610007 (membership closure, both start checks, tests incl. PG16 INHERIT FALSE/SET TRUE).
2 owner skip all-or-nothing: FIXED 9b7610007 (per table + one warning naming skipped tables).
3 0011 edited in place (add_spend window not on already-migrated DBs): PARTLY: M6 checksum ledger fbebb390f / earlier merges (repeating warning, --reset-draft/--accept-changed-draft; manifest-wins rule); the hard ConfigError for a 0010/0011 checksum mismatch with roles named + revoke of the unmapped old overload + upgrade-path test: QUEUED after the migrate.py merge (needs the lead's 'clean' on wip/lead-b-migrate).
Full text: handover/core-b/ANSWERS/rev-b-newest2.md. T1: tests/contracts/test_t1_reserve_cap.py is core-b's base; core-a's cases ported a1b9b077e.

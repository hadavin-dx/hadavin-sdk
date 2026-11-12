# PARKED packages (ORDER 262, 2026-11-12 ~20:12 UTC / 01:42 IST)
Reason: three heavy slots, 13 waiters, load about 9. These packages resume only when the queue holds fewer than 6 waiters. Their agents are closed and their waiting gate jobs removed.
Resume = start ONE gate-runner agent for the branch, run the owed gates through /home/user/build/heavy.sh, check handover/core/run-ledger.tsv first (never run the same head and command twice).

| Package | Ref (origin) | Head | Gates still owed | Where to run |
|---|---|---|---|---|
| AK1-a (inbound ledger part 1) | wip/cloud-ak1-a | b95e1853 | tests/ak1a_mutants.py, full pytest, group 6 Postgres | Linux/Postgres (cloud only) |
| AK-G2-a b2 | wip/cloud-ak-g2-a | 3073bf75 | tests/inbound_ledger_mutants.py (69 mutants; last run 62 of 69, 7 pins fixed), full pytest, Postgres suite | Linux/Postgres (cloud only) |
| Q8b b14 gate-fix (load-dependent timing tests moved to CPU time plus interleaved least-time; src untouched) | wip/cloud-q8b-b14g | 19694984 | gate-notes q8bnobody.sh, q8broot.sh, mrm.sh, stage.sh, full.sh | Linux (root and nobody variants: cloud only) |
| PRH b12 (part 5 perf) | core/prh-b12 | 8f7c376a | perf evidence, full pytest | perf timing: alone, laptop is better |
| P3a-2 b9 | wip/cloud-p3a2-b9 | 15ef17e6 | mutants V122, V149-V177 in tests/migrate_mutants.py (4 batches), migration_numbers_mutants, stage_mutants, full pytest, group 6 dblink, 9, 5 | Linux/Postgres (cloud only) |

Q8b b14g notes (builder report): no full pytest at 19694984 (c1898e89 had 11238 passed, 3 failed: two ratio tests, fixed since, plus the known dblink-connect test); mutant tables NOT run at the final head; M257 on the new CPU-time code not run; the builder's `pkill -u nobody` may have stopped another nobody-owned mutant run around 19:44 UTC (its own mrm run was invalid for that reason). Owed order: q8bnobody.sh, q8broot.sh, full.sh (own PG on 56931, dblink test separately with unshare -m), stage.sh, mrm.sh, m257load.sh in /home/user/build/gate-notes/; mutant runs take 40 to 60 min each. Checkpoint: /home/user/build/checkpoints/B-Q8b-gate.md.

r3 checkpoint 20:47 UTC: strict sweep reverted (seed saved), S2 log line + position test + tests added, tool renamed client_profile_mutants.py + env scrub; todo: tighten killers via diagnostic run, seed mutants, CHANGELOG done, final runs
r3 checkpoint 21:02 UTC: committed locally (not pushed), final runs queued next
r3 checkpoint 21:08 UTC: head f046286 local; ruff/format/bandit/scan green, mutants 65/65 named, stage mutants 37/37; full 3.12/3.13 + seed mutants queued
r3 checkpoint 21:26 UTC: found+fixed pyc staleness in mutant runner; new head 0c01b4f (pushed f046286 earlier, now re-running all gates before the push)
r3 checkpoint 21:41 UTC: head c325db8 final candidate; ruff/format/bandit/scan green; waiting for slots for mutants, stage mutants, full 3.12/3.13, seed
21:59Z final: c325db8 pushed, TABLE.md written, all gates green
22:11Z r4 final a3d7eb0 pushed

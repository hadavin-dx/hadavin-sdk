# C7b fix pass 1 checkpoint (10:31 UTC)
- Done: M1 reconciled (collect-only 9846 -> 9946, +34 +61 +5 = 100, 0 removed). M2 root cause found (cmdlet-shape rule in gate.py _WRITE_SHAPES), fix patch v6-extra/FIX-id-vs-command-withheld.patch written, new tests fail on old (6), pass on new; 200k loop old 81 bad ids of 800000, fixed 0. M3 base no-handover full suite done (see report).
- Running: full suite on v3 patches + fix, no handover, literal env -i.
- Next: new C-01/A-01 tests on base tree (item 5), ruff/bandit logs, report.

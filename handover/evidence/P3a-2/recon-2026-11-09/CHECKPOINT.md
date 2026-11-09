# CHECKPOINT
- 03:54Z start: copies wt, wt-p6a made; all 66 killer tests exist at 2b0941b; log lists names+descriptions+killers but no replacement text, so mutant text is reconstructed from source.
- 0:25 read all sources; mutant text designed per name (migrate.py, migration_numbers.py, CHANGELOG.md, tests/fixtures/dsn_skip.py, two test files). Writing p3a2_mutants.py next.
- ~0:50 first full run 63/66; fixed M94 killer param, N10 reading, P8 line wrap; rerunning. Then gen_evidence.
- ~04:10 mutants 66/66 done (run-p3a2-mutants.txt). gen_evidence.py written, testing on wt-p6a.
- 04:13 gen_evidence run on wt-p6a started in background (out-p6a/, run-gen-evidence.txt); ~15 min
- 05:03 restart: P3a-2 gen_evidence subset run completed (out-p3a2); P6a run died at full-3.12, rerunning once (out-p6a)

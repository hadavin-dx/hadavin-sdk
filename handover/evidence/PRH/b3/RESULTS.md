# PR H builder 3 results (raw)
- Full suite (heavy.sh, not live, not perf): first run 12845 passed, 1 failed (dblink test: PGHOST/PGPORT missing from the Postgres server environment, my setup slip), 1 skipped.
- Rerun of tests/demo_askdata with corrected server environment: `1212 passed, 2 deselected in 62.29s`, rc=0. The whole suite was NOT rerun after that fix (only that folder).
- Perf (G1 to G3): 28 passed. Mutants: 46 of 46 good. bandit rc=0. ruff check and format check clean. gitleaks on origin/main..HEAD: no leaks.
- G4 (alone): see g4_compare_main.log. Shapes without hidden items ratio 0.97 to 1.01. H1 2.70 and H2 3.21: these shapes contain colour codes that main does not strip, so extra work is expected; above the 1.25 line a person must read.

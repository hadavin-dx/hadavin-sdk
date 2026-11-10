# r4 builder note, head 1a7d2029013deff2054c4c18f73663f21aaa7c3c (on 9881b21). Full suites NOT run (the independent runner does them).
Env cleared: CI, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL, GH_TOKEN, GITHUB_TOKEN; DSN only for DSN runs (Postgres 16, 127.0.0.1:56300). Runs were direct (no heavy.sh), python 3.12 venv.
| Run | Result |
|---|---|
| ruff check / format --check / bandit -ll | exit 0 / 0 / 0 (325 files formatted) |
| meter_mutants.py | 22 of 22 good (new: L12 NaN pin, L13 daily zero budget, L14 monthly zero budget; L10 expect now "admitted 2 calls for cap 2.50") |
| postgres_mutants.py with DSN | baseline 98 passed; 13 of 13 killed as described |
| contract+harness+guard files, no DSN | 106 passed, 98 skipped |
| same, DSN, run twice | 204 passed, 204 passed |
| same test file with CI=true and no DSN | 17 passed, 17 errors, exit 1 (the intended failure) |
Fail-before on 9881b21: the new test for the ask-your-data helper PASSES on 9881b21 (it covers existing behaviour, so it is not a fix proof); the new mutants L12-L14 are the proof for the NaN pin and the zero-budget tests. Not run: CI, Python 3.13, random order, Postgres 17.

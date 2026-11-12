# PR 89 round 26: builder evidence (not a review)

Head under test: cc4560c04c4f87f165701690e14dd2caa664d138 (base 580b4adf). Run on a shared Linux machine; raw logs are in the builder scratch folder, short excerpts are in this folder.

## What did not pass cleanly, first
- Full pytest at this head: 10827 passed, 1 failed, 1 skipped, 28 deselected (343.84 s). The 1 failure is tests/demo_askdata/test_validate_harm.py, case dblink-connect. Cause: the machine's Postgres had no server on the default socket and port that dblink uses. It fails the same way on the old head 580b4adf. After restarting the private test server with that socket, all of tests/demo_askdata passed (1214). The whole suite was NOT rerun after that; only that folder was.
- An earlier full run was killed from outside (exit 143, about 9 percent). It was not counted; it was rerun.
- Not run here: Windows, macOS, performance, CodeQL, SonarCloud, CodeRabbit (CI only). The 2 mypy tests need mypy in the environment; they ran here only because I installed it in the scratch venv; mypy is still not in the locked environment (see CHANGELOG round 26).

## Results
- ruff check rc 0; ruff format --check rc 0 (323 files); bandit -q -r src demos tools -ll rc 0; tools/scan_repo.py rc 0; stage_mutants 37 of 37 good (gates.txt).
- Full mutant run, alone, at the final head: 327 of 327 good (mutants-result.txt).
- mypy --platform win32: 13 errors on 3.12 and on 3.13 (mypy.txt).
- Fail-before (new tests, mutants and manifest against the 580b4adf runner): 12 failed, 357 passed (fail-before-failed-tests.txt).
- Tests that pass on old code are tests of test code, not runner code. Each was shown live by a manual plant that makes it fail (plants.txt, P1 to P7).

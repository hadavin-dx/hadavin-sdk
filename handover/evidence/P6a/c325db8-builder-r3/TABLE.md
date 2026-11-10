# P6a round 3 builder evidence, head c325db8 (pushed to origin core/P6a; f046286 pushed earlier)

NOT RUN / NOT CHECKED: perf tests, Vault tests, live tests (28 deselected); CI services (CodeQL, SonarCloud, CodeRabbit) not yet seen; no independent evidence runner or EGM reviewer/drift pass by this builder (lead runs them); token use not measured.

| Check | Command log | Result |
|---|---|---|
| ruff check | ruff-check.txt | All checks passed |
| ruff format --check | ruff-format.txt | 318 files already formatted |
| bandit -ll | bandit.txt | exit 0 |
| pytest 3.13 + local Postgres | full-313.txt | 10476 passed, 1 skipped, 28 deselected |
| pytest 3.12 + local Postgres | full-312.txt | 10476 passed, 1 skipped, 28 deselected |
| mutant tool (tools/client_profile_mutants.py) | mutants.txt | 69 planted, 69 killed by named test, 0 survived |
| stage mutants | stage-mutants.txt | 37 of 37 good |
| seed sweep mutants | seed-mutants.txt | 17 of 17 killed |
| fail-before (new tests on d392200) | failbefore.txt | 8 failed on old code (expected) |

Ledger rows: -09 file renamed to tools/client_profile_mutants.py, history wording removed; -11/-13 mutants for other strict fields moved to the seed folder; -12 only made_up_data_only strict, sweep in /home/user/build/P6a-strict-sweep-seed/; -14 env scrub, unique mutant numbering, exact killers, neutral names, S6 limit sentence, S2 log line, snapshot position, CHANGELOG wording. A runner bug (stale compiled files across same-size mutants) was found and fixed (PYTHONDONTWRITEBYTECODE, self-mutants, fail-before test).
Raw logs are in this folder.

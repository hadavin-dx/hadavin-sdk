# PR 89 (branch core/mutation-runner-keywords), head b95b0ca762dd74574e44e7fb546f82ef04f55295: independent raw evidence

Role: EVIDENCE RUNNER (runs and records; no judging, no fixing). Model: Fable 5.2. Date: 2026-11-11, 14:26 to 15:25 UTC (19:56 to 20:55 IST).
The builder's report and checkpoint were not read. No spend, no commit, no push, no sub-agent.
Raw logs and JUnit XML: `/home/user/build/evidence-raw/PR89-b95b0ca/` (not in the repository).
Every test command ran under `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`
with `PGHOST=127.0.0.1 PGPORT=56110 PGUSER=postgres HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56110/postgres` (own PostgreSQL 16.15 cluster, UTF8, C.UTF-8, trust on 127.0.0.1, socket folder /tmp).

## Failures, slips and not-run items first

1. **One test failed in the first full run on the head and passed in the second.** Run 1: exit code 1, `1 failed, 10684 passed, 2 skipped`.
   Failing test: `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[copy-program]`,
   first error line `psycopg.errors.InternalError_: could not close pipe to external command: Broken pipe` (excerpt: `full-run1-failure-excerpt.txt`).
   Run 2 (same head, same database, nothing else of mine running): exit code 0, `10685 passed, 2 skipped`.
   Reruns of that test file alone, three times per tree: origin/main 2a8c2aac 3 of 3 exit 0 (253 passed each); db0d9eb4 3 of 3 exit 0; head b95b0ca7 3 of 3 exit 0.
   So the failure was seen once in 5 runs of that test on the head (2 full, 3 file), 0 of 3 on db0d9eb4, 0 of 3 on origin/main.
   Facts recorded, not judged: the head does not contain origin/main (`git merge-base --is-ancestor origin/main b95b0ca7` exit 1; merge base 2742c1bf).
   origin/main has two commits the head lacks: 453385af (#87) and 2a8c2aac "Fix flaky askdata copy-program test (child closed its pipe early) (#88)",
   which changes the `copy-program` line of `tests/demo_askdata/corpus.py` (`'echo x'` to `'cat > /dev/null'`). The PR's own diff does not touch `tests/demo_askdata/` or that source.
   During run 1 my two probe scripts and the gitleaks scan ran at the same time; other agents' jobs were also running (machine load average 5 to 15 the whole session).
2. **My slip: the first start of the full suite is void.** I started the fail-before run in the db0d9eb4 worktree with the SAME virtual environment while the full suite
   was running on the head; `uv run` re-pointed the environment's editable install at the old tree. I stopped my own run about 2 minutes in (at about 17%),
   set its log aside (`void-run1/`), dropped the 5 `askdata_t_*` databases it left in my own cluster, gave each worktree its own environment and started again.
   Runs 1 and 2 above are after that fix. The fail-before run itself was not affected (it is meant to import the old tree, and it did: see the `ImportError` path in its output).
3. **Wait rule:** `pgrep -fc "pytest"` showed 13 at the start and was never below 3 (7 to 18 all session). I waited the full 15 minutes (14:26 to 14:41 UTC), then went ahead.
4. **Projection probe, one output that holds a 4-character slice of the value** (recorded, not judged): when the CALLER's own `expect` is a 4-character piece of the
   password, `first_lines` is `'AssertionError [expect found] Zq9x'`. Every other output field of the probe: no 4-character slice (details in section 5).
5. Not run: Windows (Linux only); the sampled or full mutation run on db0d9eb4 or main (not asked); `tests/test_mutation_runner.py` is byte-identical on head and db0d9eb4,
   so the fail-before copy of that file changed nothing. One test is skipped on this machine because it runs as root (see skips).

## 1. Full suite on the head (with the database address)

Command (from the head worktree): `timeout 2400 uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs`

| run | start UTC | exit code | tests | failures | errors | skipped | passed | duration |
|---|---|---|---|---|---|---|---|---|
| 1 | 14:44:35 | 1 | 10687 | 1 | 0 | 2 | 10684 | 490 s |
| 2 | 15:08:16 | 0 | 10687 | 0 | 0 | 2 | 10685 | 696 s |

Counts are from the JUnit XML (`full-junit.xml`, `full2-junit.xml`). Skips, both runs, same two:
- `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]`: "Stubber refuses a malformed Converse shape before the kind sees it"
- `tests/test_mutation_runner_keywords.py::test_a_lock_folder_that_cannot_be_made_is_a_clear_refusal`: "the account can write to a read-only folder (root)"

Reruns of `tests/demo_askdata/test_validate_harm.py` (same pytest flags, own environment per tree), exit code and last line:

| tree | run 1 | run 2 | run 3 |
|---|---|---|---|
| origin/main 2a8c2aac | 0, 253 passed | 0, 253 passed | 0, 253 passed |
| db0d9eb4 | 0, 253 passed | 0, 253 passed | 0, 253 passed |
| head b95b0ca7 | 0, 253 passed | 0, 253 passed | 0, 253 passed |

## 2. Lint and scans on the head

| command | exit code | last line |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 322 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified. (16970 lines; at severity: Low 12, Medium 0, High 0; `#nosec` skipped lines 0) |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | (no output) |

## 3. The whole mutant list on the head

Command: `timeout 2400 uv run --all-extras --group test python tests/mutation_runner_mutants.py`
Exit code 0, 909 s (14:52:57 to 15:08:06 UTC), inside the 40 minute cap. Summary line, verbatim: `224 of 224 good; problems: []`
Rows: 224 `ok`, 0 `BAD`; verdicts 221 KILLED, 3 CRASH (the three that declare a crash). Every row: `mutant-rows.txt`.
The first 5 minutes overlapped with my 9 file reruns (the first 10 mutants took 5.6 minutes, then about 18 per minute).

## 4. Fail-before: the head's three test files on the code of db0d9eb4

`tests/test_mutation_runner_keywords.py`, `tests/test_mutation_runner.py`, `tests/test_mutation_runner_meta.py` copied from the head over a db0d9eb4 worktree
(`git status` there: the keywords and meta files changed; `test_mutation_runner.py` identical). Command: the pytest command above on those three files.
Exit code 1, 100 s. From the XML: 238 tests, 46 failed, 191 passed, 1 skipped, 0 errors.
Per test with the first `E` line of each failure: `failbefore-per-test.txt`.
Failures by file: 43 in `test_mutation_runner_keywords.py`, 3 in `test_mutation_runner_meta.py`, 0 in `test_mutation_runner.py`.

## 5. Hostile probes on the head (verbatim in `probe-hostile-addresses.txt`)

Each value was given twice: to `mr._refuse_unsafe_address(DSN_NAME, value, mr.THROWAWAY_HOSTS)` and, as the variable's value, to
`run_mutants(root, [FLIP], [CORE_TEST], extra_dirs=(), timeout=120, pass_env=(DSN_NAME,))` on the tiny tree the tests use (lock folder pointed at a temp folder, as the tests do).

| probe | value | address check | run_mutants |
|---|---|---|---|
| a | `postgresql://postgres@localhost:5432/postgres` | returned None | 1 row: flip KILLED, good |
| b | `postgresql://u@LOCALHOST/db` | returned None | flip KILLED, good |
| c | `postgresql://u@localhost./db` | ValueError "its host is not one of throwaway_hosts" | same ValueError |
| d | `postgresql://u@127.0.0.1.nip.io/db` | ValueError "its host is not one of" | same |
| e1 | `postgresql://u@[::1]/db` | returned None | flip KILLED, good |
| e2 | `postgresql://u@[::ffff:127.0.0.1]/db` | ValueError "its host is not one of" | same |
| f1 | `postgresql://u@127.1/db` | ValueError "its host is not one of" | same |
| f2 | `postgresql://u@2130706433/db` | ValueError "its host is not one of" | same |
| f3 | `postgresql://u@0x7f.0.0.1/db` | ValueError "its host is not one of" | same |
| g | `host=localhost hostaddr=10.0.0.5 dbname=x` | ValueError "its hostaddr is not one of" | same |
| h1 | `host=/tmp dbname=x` | returned None | flip KILLED, good |
| h2 | `host=/tmp/../etc dbname=x` | ValueError "not in a shape the runner can check" | same |
| i | `postgresql://u@localhost/db?host=10.0.0.5` | ValueError "not in a shape" | same |
| j | `postgresql://u@localhost,10.0.0.5/db` | ValueError "not in a shape" | same |
| k | `service=prod` | ValueError "not in a shape" | same |
| l | URL with user `u`, a password holding `%40`, host localhost | returned None | flip KILLED, good |
| m1 | probe a plus a trailing newline | ValueError "not in a shape" | ValueError "its value holds a control character" |
| m2 | `host=localhost dbname=x` plus a trailing newline | ValueError "not in a shape" | ValueError "its value holds a control character" |
| n1 | `throwaway_hosts=("*",)`, four values (remote URL, probe a, `host=/tmp dbname=x`, `dbname=x`) | ValueError "throwaway_hosts holds exact host names or addresses only", all four | same, all four |
| n2 | `throwaway_hosts=("",)`, the same four values | the same ValueError, all four | same, all four |

For the accepted values `first_lines` was `{'flip': '[class not shown] [expect found] assert'}`; for every refusal it was `{}`. Full messages are in the file.

Projection probe (`probe-projection-part1.txt`, `probe-projection-part2.txt`). Value: a loopback URL with a login and a 9-character made-up password (55 characters).
The failing tests put (i) the whole value, (ii) a 6-character slice of the password, (iii) its base64, (iv) its reverse into the assertion message, into a parametrised
test id, and into both. The slice check is computed by code for every printed field (any 4-character slice of the value, and also of each of the three other forms).
- Control (plain pytest, no runner, same test bodies): the raw output holds 51 different 4-character slices of the value for the "whole" tests and 3 for the "slice6" tests,
  none for the base64 and reverse tests (those hold slices of their own form), so the tests did see and print the value.
- Mutant rows, 12 mutants: every row `(name, WRONG_REASON, 'tests/test_core::test_<kind>_<form>' or '...[parameters hidden]', False)`, `first_lines` `'AssertionError [expect not found] assert'`.
  4-character slices of the value or of any form in any field: NO, all 12 rows (the mutants' `expect` was `assert`, which the message did not hold, hence WRONG_REASON).
- Caller's `expect` set to the first 4 characters of the password: row `('mexp', KILLED, 'tests/test_core::test_msg_whole', True)`, `first_lines` `'AssertionError [expect found] Zq9x'`: YES, one slice, `Zq9x`.
- The unmutated copy fails (24 runs: 12 on the many-test tree, 12 on one-test trees): `RuntimeError: the unmutated copy does not pass its tests (exit code 1): AssertionError`; slices: NO, all.
- Collection error and fixture error holding the value: rows `('mx', ERROR, 'COLLECTION ERROR', False)` and `('mx', ERROR, 'FIXTURE ERROR', False)`, `first_lines` `{'mx': 'AssertionError'}`; slices: NO.
- Skips with the value in the reason or in the id (8 mutant runs, 8 baseline runs): rows `('ms', ERROR, 'SKIPPED TESTS', False)`, `first_lines` `'skipped: tests/test_core::test_skip_<form>'`
  or `'...[parameters hidden]'`; baseline `RuntimeError: the unmutated copy skipped 1 selected test(s): [...]`; slices: NO, all.
Totals over both files: 749 slice checks NO, 19 YES (18 in the control, 1 the `expect` case above).

## 6. gitleaks (8.30.1)

- `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..b95b0ca7" <head worktree>`: exit 0, 27 commits scanned, "no leaks found".
- `gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/PR89/b95b0ca`: GITLEAKS_DIR_LINE

## Clean-up

CLEANUP_LINE

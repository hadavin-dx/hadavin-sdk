# Raw evidence: database-migration package, branch `core/P3a-2-rewritten`, head `8382bdd5b0e356bb794800f8c05f7dfa88ed0229`

EVIDENCE RUNNER record. It lists what was run and what came out. It contains no verdict; the EGM reviewers judge it.
Runner model: Fable 5.2. Date: 2026-11-11, about 13:58 to 14:45 UTC (19:28 to 20:15 IST). No paid call, no live model call.

## Failures and deviations first

1. **Full suite exit code 1.** One test failed: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`
   ("a quadratic function must be flagged"). The same test file on a clean `origin/main` worktree (`2a8c2aac`) also exits 1
   with this same single failure. The single test run alone five times: 5 of 5 exit code 1 on `origin/main`, 5 of 5 exit code 1 at head.
   Other sessions' test processes were running on the machine during all of these runs.
2. **`python tools/scan_repo.py` exit code 1.** One hit: `tests/test_migration_postgres.py:3221: credential-literal`.
   `git blame` puts that line in commit `31ffaa06` (one of the four newest commits). The same tool exits 0 on `origin/main` and on `HEAD~4`.
3. **The wait for a quiet machine ran out.** The bounded wait lasted the full 901 seconds; `pgrep -fc pytest` still showed 11
   when the full suite started (that count includes shell wrapper lines of other sessions). All timings below were taken on a shared, busy 4-core machine.
4. **Cloud variables were present in the session and were unset for every test and mutant run:** `AWS_ACCESS_KEY_ID`,
   `AWS_SECRET_ACCESS_KEY`, `AWS_CA_BUNDLE`, `ANTHROPIC_BASE_URL` (repo rule: tests run with no cloud configuration). Values were not printed.
5. Added to the brief's pytest command: `-rfEs` (prints failure and skip reasons; selects nothing). Nothing else was changed.

## Not run / not checked

- CodeQL, SonarCloud, CodeRabbit and the GitHub CI workflow: not run here.
- The mutant run was the full list (254), not a sample; no second mutant run was made.
- Step 3 used the old `CHANGELOG.md` together with the old `src/` (only `tests/` was taken from head). No variant with the new CHANGELOG was run.
- No test was rerun on `origin/main` other than `tests/test_migration_numbers.py` (it holds the only full-suite failure).
- The classification NEW / CHANGED / UNCHANGED in step 3 compares the text of each test function only; a changed helper or fixture outside the function does not show in it.

## Setup

| Item | Value |
|---|---|
| Worktree at head | `/home/user/build/EV-P3a2-8382bdd` (detached at `8382bdd5`), `git status` clean before and after |
| Python / uv | CPython 3.13.18, uv 0.11.32, venv `/home/user/build/venv-p3a2` (`uv sync --all-extras --group test`, exit 0) |
| Postgres | own cluster, PostgreSQL 16.15, `initdb -E UTF8 --locale=C.UTF-8 -A trust`, port 56060, `listen_addresses=127.0.0.1`, socket dir `/tmp`; database `postgres`: UTF8, collate and ctype `C.UTF-8` |
| Test variables | `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56060/postgres`, `PGHOST=127.0.0.1`, `PGPORT=56060`, `PGUSER=postgres` |
| `origin/main` | `2a8c2aac89f83dd0a45af0412563b59ff4fe5632` |
| Delta (four newest commits) | `8382bdd5`, `aeaac529`, `6e866e88`, `31ffaa06`; base `HEAD~4` = `42fc2597`; 11 files, 1349 insertions, 200 deletions |

## 1. Full suite

Command (in the head worktree): `timeout 1500 uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs`

| Exit code | Duration | tests (XML) | failures | errors | skipped | passed |
|---|---|---|---|---|---|---|
| **1** | 419 s wall (XML time 415.06 s) | 10966 | 1 | 0 | 1 | 10964 |

- Failed: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (assertion at line 843).
- Skipped: `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses a malformed Converse shape before the kind sees it".
- Rerun of the failing file on clean `origin/main`: `python -m pytest -q -p no:cacheprovider tests/test_migration_numbers.py` with `PYTHONPATH=<main worktree>/src`: exit code 1, "1 failed, 132 passed in 2.27s", same test.
- The file `tests/test_migration_numbers.py` differs between `origin/main` and head (71 insertions, 14 deletions).
- Detail: `full-suite-failures-and-skips.txt`, `full-suite-meta.txt`.

## 2. Lint, format, bandit, repo scan

| Command | Exit code | Output |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | "All checks passed!" (`ruff-check.log`) |
| `uv run --all-extras --group test ruff format --check` | 0 | "330 files already formatted" (`ruff-format.log`) |
| `uv run --with bandit bandit -ll -r src tools` | 0 | "No issues identified."; totals Low 12, Medium 0, High 0; 17096 lines; 3 issues skipped by an in-code disable marker (`bandit.txt`) |
| `uv run --all-extras --group test python tools/scan_repo.py` | **1** | `tests/test_migration_postgres.py:3221: credential-literal` (`scan-repo.txt`) |

## 3. New tests against the old source (round 11 fail-before)

Method: second worktree at `HEAD~4` (`42fc2597`), then `git checkout 8382bdd5b0e3 -- tests` (the whole `tests/` folder from head; 8 files differ),
`PYTHONPATH=<old worktree>/src`, import path printed and confirmed to be the old worktree. Command per file:
`python -m pytest -q -p no:cacheprovider --junitxml=<raw>/old-src-<file>.xml -rfEs tests/<file>.py`.
Files run = the test files named by `git diff --name-only HEAD~4 HEAD -- tests` (`tests/fixtures/migration_role.py` and `tests/migrate_mutants.py` hold no collected tests).

| Test file | Exit code on old source | tests | failed | passed | Duration |
|---|---|---|---|---|---|
| `tests/test_k2_migrations.py` | 0 | 55 | 0 | 55 | 8 s |
| `tests/test_k5_round10_postgres.py` | 1 | 8 | 1 | 7 | 2 s |
| `tests/test_migration_names.py` | 0 | 62 | 0 | 62 | 0 s |
| `tests/test_migration_postgres.py` | 1 | 199 | 47 | 152 | 47 s |
| `tests/test_migration_rules.py` | 1 | 142 | 18 | 124 | 2 s |
| `tests/test_migration_wiring.py` | 1 | 118 | 4 | 114 | 1 s |
| Total | | 584 | 70 | 514 | |

All 70 cases that fail on the old source passed at head in the full run (step 1). No errors, no skips.

Per test function (text of the function compared between `HEAD~4` and head):

| Class | Fails on old source | Passes on old source |
|---|---|---|
| NEW (name absent at `HEAD~4`) | 17 | 8 |
| CHANGED (same name, different text) | 11 | 5 |
| UNCHANGED | 2 | 271 |

- The two UNCHANGED functions that fail on the old source: `tests/test_migration_rules.py::test_every_migrate_mutant_still_applies_to_the_source` (1 case) and
  `tests/test_migration_wiring.py::test_a_privileged_migration_role_is_refused_before_any_file_runs` (1 of its 5 cases).
- One test function exists at `HEAD~4` and not at head: `tests/test_migration_wiring.py::test_the_membership_check_reads_both_user_names_all_four_flags_and_the_built_in_roles`.
- Every name: `fail-before-delta-tests.txt` (per function, with its class) and `fail-before-old-source.txt` (per failing case, with the first line of the message).

## 4. Mutants (the package's own list)

How it is invoked (read from the file's docstring and `main`): from the repository root, `HADAVIN_TEST_PG_DSN=... python tests/migrate_mutants.py [ids]`;
it copies the repository to a temporary folder, runs a baseline of all killer tests, then plants one wrong line per mutant in the copy.
Command: `MIGRATE_MUTANTS_RAW_DIR=<raw>/mutants-raw timeout 1500 uv run --all-extras --group test python tests/migrate_mutants.py`

| Exit code | Duration | Baseline | Rows | KILLED | SURVIVED / ERROR / BROKEN |
|---|---|---|---|---|---|
| 0 | 924 s (inside the 25 minute cap) | exit 0, "279 passed in 33.36s", 210 killer ids | 254 | 254 | 0 |

Script's own last lines: "behaviour: 197 of 197 killed", "prose: 11 of 11 killed", "test-helper: 46 of 46 killed", "not killed: []", "254 of 254 killed".
Slowest rows: FO5 56.3 s, T3 18.3 s, T2 17.9 s. Every row: `mutant-rows.txt`. The full pytest output of every killer run is in the raw folder (254 files).
The working tree of the head worktree was clean after the run.

## 5. Two probes on this PostgreSQL 16.15 (verbatim in `probes-pg16.txt`)

(a) `CREATE FUNCTION f() RETURNS int LANGUAGE sql RETURN 1;` then the row from `pg_proc`:

```
prosrc                  | 
prosrc_is_null          | f
prosrc_length           | 0
prosqlbody_is_not_null  | t
pg_get_function_sqlbody | RETURN 1
```

(`prosrc_is_null` and `prosrc_length` were added to the requested columns so that an empty text can be told from NULL.)

(b) `SELECT md5('a' || '{x}'), md5('a{x}' || '');`

```
               md5                |               md5                
----------------------------------+----------------------------------
 40d5bb449f14dcad424ea6990eb88efc | 40d5bb449f14dcad424ea6990eb88efc
```

## 6. gitleaks over the branch history

Command: `/home/user/build/bin/gitleaks git --redact --no-banner --exit-code 0 -c .gitleaks.toml --report-format json --report-path <raw>/gitleaks-git.json --log-opts="origin/main..8382bdd5b0e3" /home/user/build/EV-P3a2-8382bdd`
(gitleaks 8.30.1; config = the repository's `.gitleaks.toml` at head.)

Exit code 0. "44 commits scanned", "no leaks found". Findings in the JSON report: **0**; rule/file pairs: none.
(`git rev-list --count origin/main..8382bdd5b0e3` prints 48.) Detail: `gitleaks-git.txt`.

## Files

In this folder (small text only): `RESULTS.md`, `full-suite-failures-and-skips.txt`, `full-suite-meta.txt`, `step2-codes.txt`, `ruff-check.log`,
`ruff-format.log`, `bandit.txt`, `scan-repo.txt`, `fail-before-meta.txt`, `fail-before-delta-tests.txt`, `fail-before-old-source.txt`,
`mutant-rows.txt`, `mutants-meta.txt`, `probes-pg16.txt`, `gitleaks-git.txt`.

Raw files, kept outside the repository because they can hold made-up test credentials that the secret scanner flags:
`/home/user/build/evidence-raw/P3a2-8382bdd/` (`full-junit.xml`, `full-pytest.log`, `old-src-*.xml` and `.log`, `main-test_migration_numbers.xml` and `.log`,
`main-single-*.log`, `head-single-*.log`, `mutants.log`, `mutants-raw/`, `bandit.log`, `scan_repo.log`, `gitleaks-git.json`, `gitleaks-git.log`, `uv-sync.log`, `initdb.log`, the run scripts `*.sh`).

## Cleanup

Cleanup record and the secret scan of this folder follow.

Cleanup record (2026-11-11 14:41 UTC / 20:11 IST): own Postgres on port 56060 stopped (`pg_ctl stop`, "server stopped") and its data folder deleted;
the three worktrees of this run (`EV-P3a2-8382bdd`, `EV-P3a2-old-42fc259`, `EV-P3a2-main-2a8c2aa`) removed; venv `venv-p3a2` deleted; the mutant
runner's temporary copy is gone; no process of this run is left. No process or Postgres of another session was touched. No commit, no push.

## Secret scan of the handover folder

- `gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/P3a-2/8382bdd` (this run's folder): "no leaks found".
- `gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/P3a-2` (the whole package folder): **"leaks found: 135"**.
  All 135 are in 9 files of an earlier run's folder `ef2adc7-cloud/`, which this run did not write. Those files are tracked by git on branch
  `core/cloud-handover` and unmodified. This runner did not move or delete them (they are another run's committed evidence); the owner of that folder or the lead decides.
  Rule and file pairs (count, rule, file under `handover/evidence/P3a-2/ef2adc7-cloud/`):
  - 1 aws-access-token, 2 curl-auth-user, 2 slack-app-token in each of `02a-full-py313-dsn.log`, `02b-rerun1-full-py312-dsn.log`, `02c-full-py313-nodsn.log`
  - 115 generic-api-key in `_superseded-sql-ascii-cluster/02b-full-py312-dsn.log`
  - 1 generic-api-key in each of `_superseded-sql-ascii-cluster/04-migtests-py3.12-dsn-random-seed7311.log`, `04-migtests-py3.12-dsn-run2.log`,
    `04-migtests-py3.13-dsn-random-seed7311.log`, `04-migtests-py3.13-dsn-run1.log`, `04-migtests-py3.13-dsn-run2.log`

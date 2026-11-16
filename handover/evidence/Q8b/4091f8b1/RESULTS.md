# EVIDENCE RUNNER results: Q8b4, head 4091f8b10caded4f17f7eb415e601733e9a70af2 (tree clean, HEAD confirmed)
I record, I do not judge, I fixed nothing. Raw logs: /home/user/build/evidence-raw/Q8b4-4091f8b1/. Own Postgres 16 on port 56140 (stopped, folder deleted).

## What failed or was not run (first)
1. `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED 3 of 3 alone on the head AND 3 of 3 alone on origin/main (each 0.6 s, "a quadratic function must be flagged"). It also failed inside `pytest -m perf` (whole perf step: 1 failed, 28 passed, 49.97 s). So on this machine the CI perf step is red on main and head alike; the Q8b perf selection alone passed (1 passed).
2. First full pytest run: 1 failed, 10738 passed, 1 skipped (`tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`, dblink looked for the default socket because I had not put PGHOST/PGPORT in the SERVER's environment: my setup slip). I restarted the server with them and reran once: 10739 passed (below). Both logs kept.
3. `tests/migration_numbers_mutants.py` (uses tools/mutation_runner.py; NOT a CI step): "the unmutated copy does not pass its tests", exit 1, with no Postgres env. Not retried; cause not checked (probably the timing test above, unverified).
4. Not run: Vault contract tests (no Vault here; they skip), CodeQL/SonarCloud/CodeRabbit, semgrep/trivy/pip-audit/zizmor (CI `security` job beyond bandit and gitleaks).
5. Corpus probes (own script): readable secret pieces remain on the head, see section "Probes".

## Table
| item | command | exit | last line |
|---|---|---|---|
| diff list | `git diff --name-only origin/main...HEAD` | 0 | 25 files (diff-files.txt); merge-base = origin/main 2a8c2aac |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 327 files already formatted |
| bandit | `bandit -q -r src demos tools -ll` | 0 | only 2 nosec warnings (tools.py:389) |
| scan_repo | `python tools/scan_repo.py` | 0 | (no output) |
| stage_mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| gitleaks origin/main..HEAD | gitleaks git --log-opts | 0 | no leaks found (4 commits) |
| full pytest (rerun) | heavy.sh pytest -m "not live and not perf" -rs | 0 | 10739 passed, 1 skipped, 29 deselected, 16 xfailed in 322.54s (matches builder claim) |
| full pytest (first) | same | 1 | 1 failed, 10738 passed (dblink env slip, above) |
| q8b_mutants (CI step) | `python tests/q8b_mutants.py` | 0 | 63 of 63 good; problems: [] |
| mutation_runner_mutants | `python tests/mutation_runner_mutants.py` | 0 | 62 of 62 good; problems: [] |
| migration_numbers_mutants | same style | 1 | RuntimeError unmutated copy fails (item 3) |
| other CI mutant step using mutation_runner | ci.yml names only q8b_mutants and stage_mutants (read) | - | - |
| perf, Q8b files | pytest -m perf (q8b/k5 files) | 0 | 1 passed, 300 deselected |
| perf, all | pytest -m perf | 1 | 1 failed (timing test), 28 passed |
| timing test x3 head | alone | 1,1,1 | failed |
| timing test x3 main | alone | 1,1,1 | failed |

## Fail-before (new or changed test files copied onto src of the base; command: pytest on tests/test_k5_producers.py tests/test_k5_round11.py tests/test_q8b_*.py)
- origin/main src: 168 failed, 117 passed, 14 xfailed. Head: 284 passed, 16 xfailed. The 48 test ids in test_q8b_* that PASS on main src: fail-before-main-q8b-tests-that-PASS-on-main.txt (plus test_k5_producers 25 and test_k5_round11 44 passing ids, counts only).
- previous head 13ea6b75 src: 17 failed, 267 passed, 16 xfailed; failing ids in fail-before-old13ea6b75-failing.txt.

## Probes (my own script: ev_probe_keys.py, ev_probe_dump.py; same folder)
Paths: card = `approvals.channel.clean`; tool = `tools.redact_layered`; log = `k1b.redaction.redact_bundle` logs record text `key=value`; walk = bundle record walk (dict, nested dict, list). Secret pieces are made-up, built from parts.
Corpus: 806 key spellings (every KEY_ALTERNATIVES spelling, 3 separators, upper/title/prefixed/suffixed) x 4 paths x 3 value styles (`key="a;b c"`, `key='a b c'`, `key=a;b`) = 9,672 probes per tree. Readable (some piece visible): head 2,550 (card 890, tool 830, log 830, walk 0); main 7,167 (card 1638, tool 1638, log 1638, walk 2253).
- Quoted styles on head: card 42 keys, tool 12 keys, log 12 keys: the `pass`, `auth`, `session`, `bearer` words with a `_value` suffix (e.g. `pass_value`) in all cases, and on the card path `key-data`, `cert-data`, `certificate-data` hyphen spellings (also prefixed/upper). Main also leaks all of these.
- Unquoted `key=a;b`: head and main both leave the part after `;` readable for every one of the 806 keys on card, tool and log paths (806 each). I did not judge whether the ticket intends `;` to end a bare value.
- Benign keys (42, record walk, value `orders-svc-eu`): masked on head and on main: `password_policy_enabled`, `token_count` (identical).
- Add-on keys, table with yes = secret readable, written head/main: addon-table.md (4 paths x 3 styles x 17 keys). Keys main masks and head does not (readable on head, masked on main): passcode, passkey, pass_code, session_key, sessionkey, in quoted styles (dq and sq) on card, tool and log paths (30 probes), listed in main-masks-head-readable.txt (65 lines over the whole corpus: also PASS_value, Pass_value, SESSION_value, Session_value, pass_value, session_value). The reverse (head masks, main readable): 4,674 probes over the corpus, not listed; for the add-on keys it includes postgresauth on card/tool/log (quoted) and session_key, session_cookie, supersession on the walk path.
- Both trees leave readable on the walk path: passcode, passkey, sessionkey, newpass, oldpass, confirmpass, defaultpass, jenkinssession, bypass in at least one style; see table, I make no judgement about which are intended.

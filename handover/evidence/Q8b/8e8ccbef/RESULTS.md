# EVIDENCE RUNNER results, Q8bb6 (package Q8b, redaction path)
Head 8e8ccbef9e5600832518d9ca217847cdd3030dcc (clean detached worktree, tree clean). Previous reviewed head 6f32f0a8, base main 2a8c2aac. Run 2026-11-12 02:59 to 03:25 UTC (08:29 to 08:55 IST). I record only; nothing fixed, nothing committed or pushed. Raw logs: /home/user/build/evidence-raw/Q8bb6-8e8ccbef/ (outside the repo).

## Failed or not run, first
1. FLAKE TEST: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` alone (all 3 heavy slots held): head 1 pass, 2 fail (fail, fail, pass); main 2a8c2aac 1 pass, 2 fail (pass, fail, fail). Same message each time: "a quadratic function must be flagged". The other agents' jobs were running on the machine at the same time, so the machine was not quiet. Same flake on head and main.
2. NOT RUN: `pytest -m perf` (the ticket names no perf item); the Python 3.12 job; the security job (pip-audit, semgrep, zizmor, stale-ignore check; no network access to run them); the Docker/Vault-backed tests (HADAVIN_TEST_VAULT_ADDR not set; the full suite shows 1 skip only, see below).
3. Probe result worth the reviewer's attention (not a regression against main or 6f32f0a8): see item 8 "still readable on head".
4. Full pytest passed; no failing run, no re-run needed.

## Table
| # | item | command (short) | exit | last line |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 42 files (list in diff-names below) |
| 2a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | ruff format | `ruff format --check src tests demos tools` | 0 | 330 files already formatted |
| 3 | bandit | `bandit -q -r src demos tools -ll` | 0 | only two "nosec ... B102 tools.py:389" warnings, no finding |
| 4a | repo scan | `python tools/scan_repo.py` | 0 | (no output) |
| 4b | stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks origin/main..HEAD | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 / c | FULL pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, own Postgres 16.15 | 0 | 10786 passed, 1 skipped, 29 deselected, 16 xfailed in 354.07s |
| 6 / a | Q8b mutants (CI step) | `python tests/q8b_mutants.py` | 0 | 92 of 92 good; problems: [] |
| 6 / b | mutation runner mutants as user nobody | `setpriv --reuid=nobody ... python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good; problems: [] |
| 7 | fail-before vs main (all changed tests, src from main) | pytest on worktree of 2a8c2aac | 1 | 209 failed, 442 passed, 14 xfailed (details below) |
| d | fail-before vs 6f32f0a8 (delta tests) | pytest on worktree of 6f32f0a8 | 1 | 11 failed, 256 passed (details below) |
| e | readable-secret probes | own script, head vs main vs 6f32f0a8 | - | see below |
| f | flake test | see 1 | - | see 1 |

Setup facts: `uv sync --locked --all-extras --group test` (no --no-build) exit 0. Own Postgres 16.15 started by OS user postgres (role postgres), PGHOST=127.0.0.1 and PGPORT=56932 in the server's environment, TMPDIR a private folder (mode 1777) so the server's copy-file path is private. Verified the per-run copy path: `tests/demo_askdata/corpus.py` builds `COPY_TARGET` from `tempfile.gettempdir()` and `uuid.uuid4().hex`; `test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file` and `test_no_test_names_a_fixed_path_in_the_shared_temporary_folder` pass on head. The only skip in the full suite is tests/contracts/test_llm.py:95 (Stubber). The Postgres-backed tests ran (not skipped).

## d) fail-before, delta 6f32f0a8..head (head's test_q8b_batch6.py, test_validate_harm.py, corpus.py copied onto 6f32f0a8 src)
tests/test_q8b_batch6.py: 14 tests: 11 FAIL on the old code, 3 PASS on the old code:
- `test_d6_a_flag_with_an_ordinary_word_stays_readable` (PASS on old)
- `test_no_test_names_a_fixed_path_in_the_shared_temporary_folder` (PASS on old; a test-side rule)
- `test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file` (PASS on old; the change is in the test files only)
tests/demo_askdata/test_validate_harm.py: 253 of 253 pass on old (its change is in the test fixture, not in src). Full list: failbefore-delta-6f32f0a8.txt.

## 7) fail-before vs main (src from main), counts per file
test_q8b_batch2 16F/3P; batch3 21F/4P; batch4 22F/9P; batch6 11F/3P; card_text 21F/3P; credential_keys 22F/8P/6 xfail; glued_and_whole_values 21F/4P; random 6F/1P/1 xfail; test_mutation_runner 3F/58P; test_mutation_runner_meta 3F/3P; test_k5_producers 9P/0F; test_k5_round11 34P/0F; test_validate_harm 253P. The Q8b tests that PASS on old main code: 139 test ids incl. the k5 and runner files, listed in failbefore-main-passed-on-old.txt (no judgment made).

## e) readable-secret probes (own script probe-script.py, 816 cells per code version; paths: card = approvals.channel.clean, tool = tools.redact_layered, run = runmap.redact_text, log = runmap.safe_head, record = redact_bundle message and record key). Readable = a distinctive piece of the made-up value appears in the output. Full table: probe-compare.txt.
- Cells readable on head but masked on main: 0. Cells readable on head but masked on 6f32f0a8: 0. (Excluding the ordinary-flag group, which is checked the other way.)
- Cookie group (session_cookie, session-cookie, x_session_cookie, Cookie; values with `&`, `[`, `{`, backslash, a `;` jar with trailing prose, plain; forms `k=v`, `k: v`, JSON, record key): readable cells: head 12, main 88, 6f32f0a8 37. The earlier blocker is gone: `session_cookie=Aq1bcd&Zx9tail` gives `session_cookie=<SECRET_1>` on head (main also masks it in that form; 6f32f0a8 left `&Zx9tail` readable).
- Still readable on head (also readable on main and 6f32f0a8): the record key named `Cookie` (capital C alone) with any value, in a log record or alert (12 cells). `session_cookie` as a record key is masked on head and 6f32f0a8, readable on main.
- Flags group, masked list (newpass, oldpass, postgresauth, authorization, dbpass, confirmpass, rootauth, oauth): readable cells head 45, main 190, 6f32f0a8 65. Still readable on head: with a SPACE form `--flag value two words`, the first word is masked and the SECOND word of a two-word value is readable (`--newpass <SECRET_1> Lq8second`);. On main the same cells were fully readable. `authorization=<SECRET_1> Lq8second more words` (second word readable) is identical on head, main and 6f32f0a8. `--flag=value` forms and one-word values: masked on head in all 8 flags.
- Ordinary flags that must stay readable (bypass, compass, obsession, author): `author` readable in all forms on head, main and 6f32f0a8. `bypass`, `compass`, `obsession` are MASKED (`--bypass=<SECRET_1>`, `bypass=<SECRET_1>`) on head and on 6f32f0a8 for one- and two-word values; on main they are masked for one-word values and the second word of a two-word value stays readable. In the `--flag value` (space) form all four stay readable on head. 60 cells masked on head, 30 on main, 60 on 6f32f0a8.

## 8) ticket repro probes (own script, probe/ticket.py, head vs main; output not stored beyond this note)
- F5: `{password: 'correct horse battery staple'}` head `<SECRET_1>`; main `<SECRET_1> horse battery staple`. `{password: 'a'}` head `<SECRET_1>`; main `p<SECRET_1>ssword=<SECRET_1>`.
- F6: `clean('contact bob.smith@example.com')` head `contact <EMAIL_1>`, main `contact bob.smith@example[.]com`. `clean('ping 10.20.30.40@channel')` head `ping <IPV4_1>at-channel` (idempotent), main `ping <IPV4_1>@channel` (not idempotent). `clean('see db01.corp.internal/evil.com/p?d=1 now')` head `see <HOSTNAME_1>/evil[.]com/p?d=1 now` (the ticket's decided output).
- 2,000 seeded random card texts (my own generator): readable e-mail or address on head 0 (main 525), not idempotent on head 0.
- F5c (Secret kind with data under spec): my one-value probe showed the value masked on both main and head, so it did not reproduce the main-side leak from the ticket (the ticket's base64 entries were not tried).

## Not checked
Python 3.12 job; security job; perf step; Vault-backed tests; the ticket's 200,000-key and 4,000-text appendix runs (A1-A5) and the X1-X9 table beyond what the repo's own suite covers; builder notes in handover/evidence/Q8b/b6/ not read.

## Cleanup
Postgres stopped and its folder removed; my worktrees removed (see final report). Head SHA tested: 8e8ccbef9e5600832518d9ca217847cdd3030dcc.

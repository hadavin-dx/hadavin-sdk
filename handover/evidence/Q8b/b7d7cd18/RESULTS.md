# EVIDENCE RUNNER results, Q8bb7 (package Q8b, redaction path)
Head b7d7cd18f9c0faf4f380dc71d399208a2f3aa7b4 (clean detached worktree, tree clean before and after), previous reviewed head 8e8ccbef, base main 2a8c2aac. Run 2026-11-12 about 04:37 to 05:05 UTC (10:07 to 10:35 IST). I record only; nothing fixed, nothing committed or pushed. Raw logs: /home/user/build/evidence-raw/Q8bb7-b7d7cd18/ (outside the repo). Small excerpts and my own probe scripts are in this folder.

## Failed or not run, first
1. FLAKE TEST `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, alone with all three heavy slots held, 3 runs each: head pass, fail, fail; main pass, fail, fail. Same flake on both (`timing-flake.txt`). Another team's heavy job was on the machine during the runs (load about 2.5 to 3.3).
2. NOT RUN: `pytest -m perf` (the ticket names no perf item; CI has a perf step, not run); the Python 3.12 job; the security job (pip-audit, semgrep, zizmor, trivy; no network for them here); Vault-backed tests (HADAVIN_TEST_VAULT_ADDR not set; the suite shows 1 skip only: tests/contracts/test_llm.py:95).
3. Deviation from the common brief: `uv sync --locked --no-build` failed (`hadavin-sdk` editable has no binary distribution, rc=2); I ran `uv sync --locked --all-extras --group test` (rc=0), as the previous evidence run did.
4. The oracle `tests/q8b_older_rule.py` has no command line of its own and the ticket gives no run command for it; I ran the tests that use it (item b) and my own use of it. Main has no copy of the oracle, so item b ran on the head only.
5. Ticket appendix: I typed and ran the 200,000-key check, P1, P2 and N9 myself from appendix C (see item g). A2 and A4 row-by-row outputs and the X1-X9 table were not typed row by row; the X rows run inside the full suite (16 xfailed, all as marked; none XPASS, since the run would have reported `XPASS(strict)` as a failure).
6. My `two sibling leaks the report names` is read as: Issue 4's two forms `authorization=Bearer <token>` and `Authorization: Basic <b64>`, and Issue 6's `--db-root-user-password`. The report does not number them as "siblings"; if the lead meant other two, they were not probed.
7. My P1 run checks (c) on 680 cases (appendix measured 1,264): I read "visible ASCII and white space" strictly (code points 32 to 126 or `isspace`) and the generator is typed by me. My first P2 run used a cruder check (any known identifier readable) and showed 867; the ticket's own check (identifiers `runmap.redact_text` masks) gave 0 on head and 2,874 on main; both runs are in the folder (`keycheck-and-random-head-first-run.txt` is the crude first one).

## Table
| # | item | command (short) | exit | last line |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 43 files (`diff-names.txt`) |
| 2a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | ruff format | `ruff format --check src tests demos tools` | 0 | 331 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only the two "nosec B102 tools.py:389" warnings, no finding |
| 4a | repo scan | `python tools/scan_repo.py` | 0 | (no output) |
| 4b | stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks `origin/main..HEAD` | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 | FULL pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, own Postgres 16, port 56871 | 0 | 10815 passed, 1 skipped, 29 deselected, 16 xfailed in 435.36s (previous head: 10786 passed) |
| 6a | Q8b masking mutants (CI step) | `python tests/q8b_mutants.py` via heavy.sh | 0 | 115 of 115 good; problems: []; no WRONG_REASON line (0 lines hold the word); every line but the last two is `ok  KILLED` |
| 6b | mutation runner mutants as user nobody | `setpriv --reuid=nobody ... python tests/mutation_runner_mutants.py` via heavy.sh | 0 | 64 of 64 good; problems: [] |
| 7 | fail-before vs main (all 21 changed or new test files, src from main) | pytest on a detached worktree of 2a8c2aac | 1 | 228 failed, 451 passed, 14 xfailed, 1 deselected in 92.70s |
| c | the 139 test ids of the previous run, on the head | `heavy.sh pytest <139 ids>` | 0 | 139 passed |
| c | the same 139 ids, head tests on main source | same, in the main worktree | 0 | 139 passed (all 139 still pass on old main) |
| b | oracle tests (older.masked_parts users) | `pytest tests/test_q8b_batch4.py tests/test_q8b_batch6.py -k "older or cookie"` | 0 | 12 passed, 34 deselected |
| b | my own use of the oracle (7,608 cells; keys x values x 5 forms x card, tool, run) | `oracle-probe-script.py` | 0 | older-masked pieces readable on head: 0 |
| e | timing test | see 1 | - | head P F F, main P F F |
| f | cost of `redact()` on 200 kB hostile text, 3 runs each | `cost-probe-script.py` | 0 | see item f |
| a | round-7 Issues 1-5 probes, 1,209 cells, head vs main | `probe-script.py` | 0 | see item a |
| g | 200,000-key check, P1, P2, N9 | `random-probe-script.py` | 0 | see item g |

Setup facts: Postgres 16 started as OS user postgres in my own folder (port 56871, PGHOST and PGPORT in the server and test environment, TMPDIR a private folder, mode 1777); stopped and the folder removed at the end. Environment cleared of cloud and token variables with `env -u`. Head confirmed `git rev-parse HEAD` = the sha above, `git status --short` empty.

## 7 and c) fail-before, counts per file (head tests on a worktree of main 2a8c2aac, src from main)
| file | failed | passed on old main |
|---|---|---|
| test_q8b_batch2 | 16 | 3 |
| test_q8b_batch3 | 20 | 5 |
| test_q8b_batch4 | 22 | 9 |
| test_q8b_batch6 | 12 | 3 |
| test_q8b_batch7 | 21 | 7 |
| test_q8b_card_text | 37 | 3 |
| test_q8b_credential_keys | 68 | 32 |
| test_q8b_glued_and_whole_values | 22 | 3 |
| test_q8b_random | 6 | 1 (plus 14 xfailed in the run) |
| test_mutation_runner | 3 | 58 |
| test_mutation_runner_meta | 1 | 5 |
| test_k5_producers | 0 | 25 |
| test_k5_round11 | 0 | 44 |
| demo_askdata/test_validate_harm | 0 | 253 |
Lists: `failbefore-main-failed.txt` (228), `failbefore-main-passed-on-old.txt` (451). New in this batch (`test_q8b_batch7.py`): 7 of 28 pass on old main: the six `test_b7_1_fuzz_a_random_prefix_and_digits_behind_a_credential_word_stay_masked[0..5]` and `test_b7_2_a_count_of_tokens_stays_readable_as_a_flag`. I made no judgment on them.
The 139 ids of `handover/evidence/Q8b/8e8ccbef/failbefore-main-passed-on-old.txt`: 139 of 139 pass on the head and 139 of 139 still pass on old main. By test function name, 15 are named in `tests/q8b_mutants.py`; 124 are not. Of those 124, 58 are in `test_mutation_runner.py` and are named in `tests/mutation_runner_mutants.py` (the function names appear there). 66 ids (47 test functions) are named in none of `q8b_mutants.py`, `mutation_runner_mutants.py`, `stage_mutants.py` (name match by text, not by the runner's `only_test` field): `139-not-named-anywhere.txt` (test_k5_producers 9, test_k5_round11 34, test_mutation_runner_meta 3, test_q8b_batch2 2, batch3 3, batch4 4, card_text 2, credential_keys 5, glued_and_whole_values 3, random 1).

## a) round-7 Issues 1-5, my own probe (1,209 cells: input, five paths card/tool/run/log/record message, plus record key in a log record and in the alert; made-up values like `Qa1solo`; full side-by-side text in `probe-compare.txt`, each cell shows input, head output, main output)
"Readable" means the made-up value (or a piece of it) is in the output. "Expected" is my reading of the round-7 report and the CHANGELOG.
| Issue | what I typed | head | main |
|---|---|---|---|
| 1 digits glued: `pass2`, `newpass2`, `session2`, `auth1`, `rootauth2`, `auth0`, `oauth2`, `password2`, plus `pass`, `oauth` as controls; forms `--k v`, `--k=v`, `k=v`, `k: v`, JSON, record key | one-word value | masked in every cell (0 readable) | 188 cells readable |
| 1 same flags with a two-word value `--pass2 a b` (also `--newpass2`, `--api_key2`, `--auth0`, `--oauth2`) | | first word masked, SECOND word readable (`--pass2 <SECRET_1> Qb2second`), 25 cells | both words readable |
| 1 counts stay a count: `max_tokens=1024`, `--max_tokens 1024`, `--tokens 5`, `tokens=77`, `reasoning_tokens: 4321`, record `max_tokens: 1024` | | `--max_tokens 1024`, `--tokens 5` and the record key stay readable; the text forms `max_tokens=1024`, `tokens=77`, `reasoning_tokens: 4321` are MASKED (`max_tokens=<SECRET_1>`, 15 cells) | same 15 cells masked on main |
| 2 plurals `--secrets`, `--passwords`, `--apikeys`, `--api_tokens`, `--access_tokens`, `--credentials` (all forms, one-word value) | | 0 readable | 45 cells readable |
| 2 `tokens`, `max_tokens` with the word value `Qa1solo` | | masked in `k=v`, `k: v`, JSON, `--k=v` and as record key (42 cells); `--max_tokens v` and `--tokens v` with the space form stay readable | 40 cells masked |
| 3 Cookie in the five paths: record keys `Cookie`, `COOKIE`, `Set-Cookie`, `cookies`, `cookie`, `session_cookie`; `k=v`, `k: v`; `--cookie`, `--Cookie`, `--COOKIE`, `--set-cookie`, `--session_cookie` with `v` and with `sid=v`; `Cookie=a;b`, `session_cookie=a;b` | | all masked, except `cookie_name=v` and `cookie_name: v` (readable, 10 cells; the CHANGELOG states `cookie_name` as an over-masking cost, but on head it is NOT masked in these text forms) and `cookie_policy_enabled` with a non-yes/no value (masked, as the CHANGELOG says) | 74 cells readable (the record key `Cookie` among them) |
| 4 schemes Bearer, Basic, Token, Digest, ApiKey after `--authorization `, `--authorization=`, `authorization=`, `Authorization: `, record key `authorization` | token `Qd4tokenpart` | 0 readable in all 5 schemes x 5 forms; `Authorization: Digest ... response="Qd4hash", more prose` masked (the hash is not readable) | 50 cells readable |
| 4 generic second word: `--newpass a b`, `--password a b`, `authorization=a b` (no scheme) | | `--newpass <SECRET_1> Qd4second`, `--password <SECRET_1> Qd4second`, `authorization=<SECRET_1> Qd4second more words`: second word readable (the CHANGELOG calls it a design choice); `--newpass=a b` masked whole | `--newpass` both readable; `--password` and `authorization=` the same as head |
| 4 sibling Issue 6: `--db-root-user-password v` | | masked | readable |
| 4 sibling: `--a-b-c-d-password v` (four words in front) | | readable (the CHANGELOG states four or more as a limit) | readable |
| 5 ordinary `bypass`, `compass`, `obsession`, `possession`, `encompass`, `supersession`, `author` in the five text forms and as record key | value `Qe5ordinary` | all readable in every form | `bypass`, `compass`, `obsession`, `possession`, `encompass`, `supersession` masked in `=`, `:`, JSON forms (120 cells) |
| 5 `bypasspass`, `compassword`, `xbypass`, `newpass`, `bypass_password` | value `Qe5secretval` | masked in every form | masked (the glued ones) |
Cells readable on head and masked on main, other than the Issue 5 ordinary words (120 cells, intended): 0. No probe cell raised an error on head. My reading of "expected" for `tokens` with a word value was wrong for a record key (the walk masks any non-number value under a credential key; head masked it); this is a probe expectation, not a finding I judge.

## f) cost claim "up to 40 letters or digits glued in front": `redact(text)` on 200,000-character inputs, seconds for 3 runs (load about 3 from other agents; head then main)
| shape | head | main |
|---|---|---|
| 200k letters `a` | 0.857 0.742 0.776 | 0.477 0.525 0.435 |
| 40 letters + `pass`, repeated | 0.783 0.769 0.769 | 0.490 0.481 0.452 |
| 40 letters + `password=xyz `, repeated | 0.599 0.535 0.549 | 0.223 0.252 0.233 |
| 41 mixed letters/digits + `token: `, repeated | 0.512 0.517 0.518 | 0.284 0.240 0.233 |
| `--` + 39 letters + `pass v `, repeated | 0.908 1.005 0.814 | 0.260 0.364 0.303 |
| 40 letters + `password` (no `=`), repeated | 0.829 0.874 0.842 | 0.477 0.572 0.428 |
| `pass ` repeated | 0.621 0.635 0.667 | 0.295 0.296 0.296 |
No timeout, no refusal. Head is about 1.1 to 3.5 times main on these shapes. I did not run the CI perf step.

## g) appendix C generators typed by me (`random-probe-script.py`; head `random-head.txt`, main `random-main.txt`)
| check | head | main |
|---|---|---|
| 200,000 random keys (my word list, seed 5): accepted by main's record rule (the oracle's `SENSITIVE_KEY`) and refused by `k1b.redaction.sensitive` | 200,000 tried, 89,840 accepted by main's rule, 0 refused by head | not run (main has no `sensitive`) |
| P1 seed 20261111, 3,000 cases: (a) shown value not placeholders, (b) rare-alphabet run readable, (c) readable in a second record | 0, 0, 0 of 680 checked, 26.9 s | 2,545, 2,301, 526 of 680, 18.8 s |
| P2 seed 8, 4,000 cases: (a) a masked identifier readable, (b) bare domain token, (c) not idempotent | 0, 0, 0, 6.8 s | 2,874, 1,801, 12, 5.3 s (1,801 and 12 match the ticket's numbers for main) |
| N9 seed 9, 3,000 cases: original readable | 0, 1.9 s | 0, 1.4 s (the ticket measured 1 on main; my generator reading may differ) |

## b) the oracle `tests/q8b_older_rule.py` (read in full, 74 lines)
It holds main's (2a8c2aac) older rules copied word for word: two quoted-value regexes, the unquoted key=value regex, the cookie assignment regex, the flag regex, the JSON `"auth"` regex, and main's record-key regex; `masked_parts(text)` returns the value each of the six text rules captures; `record_key_masked(key)` says whether main's record walk masked a key. What the test `test_k1_every_cookie_key_the_older_cookie_rule_masked_is_masked_with_an_ampersand_a_bracket_or_a_backslash` compares (read from the test): 9 front words x 3 separators x 4 spellings of `cookie` (about 100 keys) x 4 inner characters (empty, `[`, `{`, backslash) x 2 text shapes; for each of the paths in `text_paths` it fails when a piece of the older-masked part is readable, where "piece" means only the three made-up strings `P1`, `P2`, `P3` of `tests/q8b_helpers.py`, and when the older cookie regex matches and any of the three is readable. It does not compare any other piece of a value, and not the record-key path. My own use of the oracle (`oracle-probe-script.py`) compared tokens of my own values: 7,608 cells (about 100 keys x 8 values x 5 forms; only cells where the older rules mask something, three paths), 0 pieces readable on head.

## Not checked
Python 3.12 job; security job; perf step; Vault-backed tests; A2/A4 row-by-row outputs and the X1-X9 rows beyond the repo's own suite; the builder notes of this batch (`handover/evidence/Q8b/b6/NOTES.md` was read; it is a batch-6 file); `handover/evidence/Q8b/b7*` builder notes.

## Cleanup
Postgres 16 on port 56871 stopped and its folder removed; my three detached worktrees (head, main, main with the head tests) and my venv removed; no background process of mine left. Head SHA tested: b7d7cd18f9c0faf4f380dc71d399208a2f3aa7b4.

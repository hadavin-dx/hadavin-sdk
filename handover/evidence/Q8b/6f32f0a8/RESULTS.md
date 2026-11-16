# EV-Q8bb5 results: package Q8b, branch wip/cloud-q8b-b5, head 6f32f0a82d3c03c6770066f4b061c69a3e9ae0a1 (6f32f0a8)

Evidence runner: recorded only, nothing fixed, nothing committed or pushed. Previous reviewed head 999ed05b, base main 2a8c2aac.
Head confirmed with `git rev-parse HEAD`, tree clean. Raw logs: /home/user/build/evidence-raw/Q8bb5-6f32f0a8/.

## Failed or not run (first)
1. Full pytest (item 5), first run: 2 failed, 10770 passed, 1 skipped, 29 deselected, 16 xfailed (rc 1). Both failures are in tests/demo_askdata/test_validate_harm.py, both caused by my test database set-up, not by the head:
   - `[copy-to-file]`: the test writes a fixed file /tmp/askdata_p2_copy.csv; that file already exists, owned by another agent's database user (not touched by me), so my database refused ("Permission denied").
   - `[dblink-connect]`: needed a database role named like the server's OS user, and PGHOST/PGPORT in the server's own environment.
   Re-run of that one file after fixing only the set-up (server in its own private /tmp via unshare, role added, PGHOST/PGPORT in the server's environment): first re-run 1 failed (PGHOST missing in server env), second re-run `253 passed in 22.73s` (rc 0). I did NOT re-run the whole suite after the set-up change; the other 10770 tests ran only in the first run.
2. Flake test `test_the_timing_harness_flags_a_quadratic_stand_in`, run alone through the three slot locks: FAILED 3 of 3 on the head and FAILED 3 of 3 on main ("a quadratic function must be flagged"). The machine was shared with other agents' jobs at the time.
3. Fail-before (item 7/c): see counts below; several new tests PASS on old code (listed).
4. Not run: perf marker step of ci.yml (`pytest -m perf`; the Q8b ticket names no perf item), the py3.12 job `tests-py312`, pip-audit, semgrep, zizmor, trivy (need the network/tools of CI), the vault contract tests (no Vault server; they skip). Item 8 ticket-table probes were NOT run beyond your items (d); I did not have a ticket text in my brief.
5. Timing: wall clock over the 60 minutes (heavy slots were shared; the full run, the mutant runners and my queue waited for slots).

## Table
| item | command (short) | exit | last line |
|---|---|---|---|
| 1 diff list | git diff --name-only origin/main...HEAD | 0 | 31 files (item1 list in raw folder) |
| 2 ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| 2 ruff format | ruff format --check src tests demos tools | 0 | 329 files already formatted |
| 3 bandit | bandit -q -r src demos tools -ll | 0 | one nosec warning (B102, src/hadavin_sdk/tools.py:389), no finding |
| 4 scan_repo | python tools/scan_repo.py | 0 | no output apart from a uv warning |
| 4 stage mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks origin/main..HEAD | gitleaks git --log-opts origin/main..HEAD | 0 | no leaks found |
| 5 full pytest | heavy.sh pytest -m "not live and not perf" -rs | 1 | 2 failed, 10770 passed, 1 skipped, 29 deselected, 16 xfailed in 385.94s (set-up causes, item 1 above) |
| 5 re-run askdata file | pytest tests/demo_askdata/test_validate_harm.py | 0 | 253 passed in 22.73s |
| 6a Q8b mutants (own worktree) | python tests/q8b_mutants.py | 0 | 87 of 87 good; problems: [] |
| 6b mutation runner mutants as user nobody | tests/mutation_runner_mutants.py via heavy.sh, HOME and TMPDIR in a mode-700 folder owned by nobody, worktree and venv world-readable | 0 | 64 of 64 good; problems: [] |
| 9 flake, head | alone, 3 slot locks, x3 | 1,1,1 | 1 failed each |
| 9 flake, main | alone, 3 slot locks, x3 | 1,1,1 | 1 failed each |

CI steps named for this package (ci.yml lines 93-96): stage mutants and Q8b mutants, both run as CI runs them.

## Fail-before (item 7 and brief (c))
Test files changed 999ed05b..head (tests/): q8b_helpers.py, q8b_key_corpus.py, q8b_mutants.py, q8b_older_rule.py, test_q8b_batch2.py, test_q8b_batch4.py, test_q8b_credential_keys.py. Copied onto a detached worktree of 999ed05b (old src, PYTHONPATH pointing at its src, checked).
- Old 999ed05b src: `8 failed, 140 passed, 15 xfailed`. Failing: test_q8b_batch4 j1 (3 tests), j2 (2), j3, j4 (flag with word glued), j6.
- New test functions (added since 999ed05b: 7) that PASS on 999ed05b src (3):
  - test_q8b_batch4.py::test_j1_a_quoted_value_after_authorization_is_masked_whole
  - test_q8b_batch4.py::test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked
  - test_q8b_batch4.py::test_j4_the_scan_finds_every_shape_of_a_second_list
- Against origin/main src (all 17 test files changed vs main copied in): `195 failed, 189 passed, 14 xfailed`. 165 new test functions vs main; 44 of them do not fail on main (list in failbefore-main-new-tests-passing-on-old.txt). Modified (not new) tests are not separated out.

## Readable-secret probe (brief (d) and the coordinator's extra inputs)
Own scripts (probe1.py, probe2.py here), made-up pieces built from parts, cells = pieces still readable. Paths: card = approvals.channel.clean, tool = tools.redact_layered, run = guard.runmap.redact_text, log = guard.redact.redact (and `log-bundle`: a bundle log text through redact_bundle), record = redact_bundle on a record `{key: value}`. Full tables: probe1-table.md, probe2-table.md. No judgement.
Probe 1 (59 inputs): head readable cells 111, main 177; no cell where head shows a piece and main does not.
- flags newpass, oldpass, postgresauth, authorization with a two-word value (`--newpass A B`): head leaves 1 of 2 pieces readable on card/tool/run/log (the second word), main leaves 2 of 2. bypass, compass, oauth, obsession flags: both pieces readable on both head and main (as on main). `--<flag>=<value>` forms: none readable for any of the eight flags, on head and main.
- oauth in records: `{"oauth": v}` none readable on head; nested `{"cfg": {"oauth_x": v, "items": [{"oauth": v2}]}}` and `oauth2_client`: record path none readable on head (main: readable); text path 1 piece readable on both.
- cookie jars: `;` and `,` jars in records: readable on head and main (record path, both). `cookie=<p>, k=<p>` text form: readable on card/tool/run/log on both. `a_token_cookie=<p>,<p>` (and `, ` and `;`): none readable on either.
- digit-start names (2fa_token, 1password, 3pass, 9auth, 4secret, 0token, 7api_key, 2oauth): `name=<v>` and `{name: v}` none readable on head; the flag form `--name a b` leaves both words readable on both, except 2fa_token (1 piece on head, 2 on main).
Probe 2 (48 inputs: keys session_cookie, session-cookie, x_session_cookie, Cookie; shapes `x K=P1&P2 y`, `K=P1&P2=P3`, `K=P1&P2`; plain and with `[`, `{`, backslash inside the first piece):
- Text paths (card, tool, run, log): for the three session keys, EVERY input leaves the part after `&` readable on head (1 piece for the 2-piece shapes, 2 pieces for `P1&P2=P3`); on main the plain inputs show none readable, the `[` and `{` inputs show the same readable pieces as on head, the backslash inputs show none. Head: 42 of 48 inputs have a readable piece on these paths, main: 24 of 48. Key `Cookie`: the plain and backslash inputs are masked on both on these paths; `[` and `{` inputs leave pieces readable on both.
- Record path: head 12 of 48 inputs readable (key `Cookie` only), main 48 of 48 (every key). So the reviewer's report is reproduced on the text paths and the opposite shows on the record path.

## Environment notes
Database: PostgreSQL 16, own folder, port 56815, started as user nobody (the tool refuses to run as root), stopped, folder deleted. Venv: `uv sync --locked --all-extras --group test` (no --no-build), rc 0. No process of another agent was touched.

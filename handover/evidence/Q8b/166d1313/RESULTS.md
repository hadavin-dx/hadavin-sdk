# Q8b batch 10, head 166d1313b7901b5d9c089c69be934c62ed9c12c7: evidence (round 10, REDACTION path)
Evidence runner. Records only; nothing was fixed or judged. Raw logs: /home/user/build/evidence-raw/Q8bb10-166d1313/. Main = 2a8c2aac. Times in UTC, run 2026-11-12 about 09:30 to 10:30.

## What failed or was not run (first)
1. Full pytest on the head: exit 1, `1 failed, 11011 passed, 1 skipped, 29 deselected, 16 xfailed in 527.87s`. The one failure is `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`: my own Postgres server was started without PGUSER, so dblink (running inside the server) tried the OS user "nobody" ("role nobody does not exist", first run: default socket). Not a Q8b test. Re-ran the file with the server restarted with PGHOST, PGPORT and PGUSER in its own environment: `253 passed`, exit 0. Both logs kept. The full suite was NOT re-run in one piece after the server fix.
2. `uv sync --locked --no-build` (the command of the brief and of CI) failed here: "hadavin-sdk is marked --no-build but has no binary distribution". I used `uv sync --locked --all-extras --group test` (without --no-build) instead.
3. Mutant count differs from the builder's text: `q8b_mutants.py` printed `182 of 182 good` (the brief says builder: 183, notes say M159 removed). I did not investigate the difference.
4. Timing test `test_the_timing_harness_flags_a_quadratic_stand_in`, alone: head 3 of 3 FAILED ("a quadratic function must be flagged"), main 1 pass and 2 fail (known flake; machine was shared with other agents' jobs). Not fixed.
5. Not run: the `security` job's other steps (pip-audit, semgrep, zizmor, trivy, stale-ignore check) and the `tests-py312` job (no Python 3.12 here); perf step `pytest -m perf` (the ticket names no perf item; I did not run it). The Q8b ticket's own acceptance commands were not run apart from the probes below (I typed the probes from the r10 report issues 1, 2, 6, 7 and the brief's list).
6. The cost and linear runs were taken through the three heavy-slot locks (alone), but the machine had other agents' processes at times; times are wall clock, one process each.

## Results table
| Item | Command | Exit | Last line / result |
|---|---|---|---|
| 1 files | `git diff --name-only origin/main...HEAD` | 0 | 47 files (raw 1-files.txt) |
| 2 ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 ruff format | `ruff format --check src tests demos tools` | 0 | 335 files already formatted |
| 3 bandit | `bandit -q -r src demos tools -ll` | 0 | only warnings (nosec on tools.py:389) |
| 4 scan_repo | `python tools/scan_repo.py` | 0 | no output besides a uv warning |
| 4 stage_mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks origin/main..HEAD | gitleaks git | 0 | no leaks found |
| 5 full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 1 | 1 failed, 11011 passed (see 1 above) |
| 5b re-run harm file | `pytest tests/demo_askdata/test_validate_harm.py` | 0 | 253 passed |
| 6 q8b_mutants | `python tests/q8b_mutants.py` (CI step), separate worktree | 0 | 182 of 182 good; problems: [] |
| 6 mutation_runner_mutants as nobody | `python tests/mutation_runner_mutants.py` | 0 | 64 of 64 good; problems: [] |
| 7 fail-before test_q8b_batch10.py on c36ce0dc src | pytest | 1 | 62 failed, 5 passed |
| 7 fail-before batch8, batch8_lines, batch9 (head tests, old src) | pytest | 1 | 4 failed, 126 passed |
| 9 timing flake head x3 | pytest alone | 1,1,1 | 3 failed |
| 9 timing flake main x3 | pytest alone | 0,1,1 | 1 passed, 2 failed |
Worktrees were clean after the mutant runs (git status empty).

## Item 7: tests passing on old code (c36ce0dc src)
test_q8b_batch10.py (5 passed): test_b10_1_the_fix_changes_nothing_for_a_text_that_has_no_scheme_word_before_a_line_break; test_b10_1_a_long_run_of_line_breaks_after_a_scheme_word_is_read_in_linear_time; test_b10_2_a_long_run_of_digest_fold_lines_is_read_in_linear_time; test_b10_6_a_name_that_ends_in_key_secret_token_or_password_after_an_ordinary_word_is_masked[bypass]; test_b10_6_an_ordinary_word_must_start_a_word_to_stay_readable_so_xcompass_key_is_a_key_as_before.
Failed on old code in the other three files (4): test_b8_3_a_real_two_word_credential_key_is_never_hidden_by_the_ordinary_look_behind; test_b9_8_a_cookie_jar_name_in_capitals_is_masked_and_in_lower_case_it_is_not; test_b9_6_a_bare_bypass_and_the_other_ordinary_words_stay_readable_by_choice_the_owner_list; test_b9_6_the_second_words_of_a_bypass_name_are_the_pass_pairs_read_from_one_list. The 126 passing ones are listed in passed-on-old-code.txt (131 lines with the five above).

## Item 8: hostile inputs (own probe: probe.py, compare.py, fuzz.py in this folder; made-up secrets from random letters)
Readable means: an 8-character stretch of the made-up secret is still in the output. Versions: head, c36ce0dc ("c36"), main.
- Header cells, 9072 per version (3 prefixes x 6 scheme words x 14 gaps x token shapes/lengths 8 to 64). With the prefix `Authorization:` or `Proxy-Authorization:` and the five real schemes (Basic, Token, ApiKey, Digest, Bearer), with gaps of 1 to 5 spaces, tab, LF, CRLF, CR, LF LF, CRLF CRLF, LF plus indent, CRLF plus tab, VT, lowercase-only tokens and tokens with `.`, `~`, `:`, `-` early: 0 readable cells on head. Readable on head: 3207 cells, all of them with no header name in front (bare `Basic<gap><token>`) or the made-up scheme word "Bearer-like"; the same 3207 are readable on main; head is never readable where main was masked in this table. `%0b` (literal text) as gap: 204/648 readable, same as above class. c36 had 4767 readable in the same table.
- Folded headers (2 to 4 lines, LF and CRLF, indent of space, 4 spaces, tab; 90 cells): Digest (response hash over folded lines): 0 readable on head (c36 and main: all readable). Basic, Token, ApiKey, Bearer folded with the token continued on the next lines: the continuation lines are readable on head (lines 2 to 4 of 32 characters each; first line masked), same as c36 and main (72 of 72 cells).
- Word pairs (key forms `k=v`, `k: v`, JSON, quoted, `--k v`; head/c36/main): `compass`, `overpass`, `encompass`, `bypass` bare with a value: readable on head and c36, masked on main for the non-flag forms. `cookiejar`, `cookiestore` lowercase: readable on all three. `COOKIEJAR`, `COOKIESTORE`: masked on head and c36 in text forms but `sensitive()` (record walk) says not sensitive on head (False) for lowercase only; for the capitals `sensitive()` is True on head. `possession_id`, `obsession_id`: readable on c36 and main, masked on head. `compass_key`, `overpass_key`, `encompass_key`, `compass_code`, `overpass_value`, `encompass_phrase`: masked on head (text and JSON); readable on c36 and, in `k=v` forms, on main. `protection_bypass`, `compass_secret/token/password`, `bypass_token`, `bypass_key`: masked on head. Exact per-cell letters in the tool output of compare.py (raw JSON kept). Short value `bypass=true`: readable on all versions.
- Record side `sensitive(word)` is False on head for: compass, overpass, encompass, cookiejar, cookiestore, bypass (6 of 24 names).
- Fuzz (3000 texts, seed 11; readable = any 8-character stretch of a secret piece survives): wrap form (key + scheme + separator + token): head 222 of 1005 readable, c36 314, main 336. Multi-cut form (secret cut into 2 to 5 pieces by white space/line breaks inside a header): head 746 of 1016 readable, c36 760, main 861. Digest folded: head 0 of 979, c36 979, main 979. Example head-readable wrap: `X-Api-Key=ApiKey\n<token 27 chars with a dash>` (readable); `passwd=Basic\r\n\t<token with dot>` (second half after the dot readable). Raw: 8-fuzz-*.json (not copied).
- Cost, 200 kB, 3 runs, seconds (own text; see cost.py; cost-and-linear.txt): hostile head 0.728/0.673/0.668, c36 0.706/0.677/0.693, main 0.424/0.357/0.373; prose head 0.670/0.692/0.638, c36 0.701/0.700/0.694, main 0.327/0.335/0.348. Ratio head/main about 1.8 hostile, about 2.0 prose.
- Linear check (hostile text, one run each, seconds) head: 50 kB 0.184, 100 kB 0.367, 200 kB 0.706, 400 kB 1.413. c36: 0.181, 0.362, 0.706, 1.367. main: 0.090, 0.183, 0.388, 0.845.

## Item 9 extra: UNPLANTED_MAX and the controls without a planted fault
`UNPLANTED_MAX = 29`; 74 controls: 38 with a planted fault, 29 with neither a planted fault nor a reason, 7 with the no-fault reason (as the builder says: 29 and 7). Full list of both groups: unplanted-list.txt. The check passes while 29 remain (it only fails above 29).

## Notes
Probe scripts are the evidence runner's own; their input texts use random made-up letters, no real values. Environment: Postgres 16 own instance, user nobody, port 56731, stopped and its folder deleted at the end; worktrees removed.
Head sha confirmed `git rev-parse HEAD` = 166d1313b7901b5d9c089c69be934c62ed9c12c7, tree clean. R-numbers: none looked up (evidence runner, no bible access in this repo).

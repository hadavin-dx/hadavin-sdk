# EVIDENCE RUNNER results: PD banner, round 15, head 20c369f07378d28d193c079d4c5ac519a016c1e2

Raw output only under `raw/`. I ran, I did not judge. Branch `wip/cloud-pd-banner`. Scratch worktree at the exact head
(`git rev-parse HEAD` printed the full sha; first line of `raw/01-head.txt`). Every python run printed `hadavin_sdk.__file__`
as the worktree's `src` (see `raw/01-head.txt`, `raw/06-hostile.log`, `raw/06-fixed-run-hostile.log`).

## Failures and discrepancies (first)

1. **Two mutant rows SURVIVED (not killed)** on this head, both reproduced when run alone (`raw/05-rerun-J27-R10C2.log`):
   - `J27 the page paints an unconfirmed banner whose text is not the own words` (file `templates/mode-banner/mode_banner.js`, mutation removes `text = NOT_CONFIRMED.text;`, killer `test_pin_an_unconfirmed_banner_keeps_the_override_names_in_its_note_and_odd_unconfirmed_fields_are_not_painted`).
   - `R10C2 a basic token after a secret-looking name is hidden by the pair step first` (file `tools/demo_only_guard.py`, mutation moves `_hide_basic` after `_hide_pairs`, killer `test_a_basic_token_after_a_secret_looking_name_is_hidden_with_its_scheme_word`).
   Both killer tests PASS on the unmutated head (`node` v22.23.4 is on the PATH; not skipped). Result: **364 of 366 rows good, 2 SURVIVED**. The builder did not claim an all-rows run on this head. Neither row is in the builder's list of 47.
2. **The masker does not hide several forms** (this is what the code comment "Not covered" says; measured in `raw/06-hostile.log`): `password: x`, `--password x`, `{"token": "x"}` and `"authorization": "Bearer x"` all print unchanged. `"authorization": "Bearer <11-char token with letters and digits>"` printed `Bearer <hidden>` (the scheme-token pass hid it), while the 1-character `x` form stayed visible. So the comment's "not covered" line for `"authorization": "Bearer x"` is true only for short or plain tokens.
3. **`tools/fixed_run.py` does NOT reject tainted or non-literal argv.** It checks the SHAPE only (its own docstring says so). `run_fixed(["sh","-c", <any text>])` and `run_fixed([python,"-c", <text>])` RAN (`raw/06-fixed-run-hostile.log`). Refused: a string, an empty list, a NUL character, a non-text element, the keywords shell/executable/stdin (and preexec_fn per the tests), a missing program.
4. **Direct program starts remain outside the helper**: 9 follow-up files listed in `tests/test_demo_only_guard.py` (`FOLLOW_UP_DIRECT_STARTS`, 21 starts) plus `demos/ask-your-data/askdata/cli.py:174` (`subprocess.run`, `noqa: S603`), which that test does not scan (it scans tools, tests, src only). In the DIFF itself the only direct start is `tools/fixed_run.py:42`.
5. **Fail-before header labels vs measured** (`raw/04-failbefore-summary.txt`, `raw/04-failbefore-unlabelled.txt`): every PASSES/FAILS claim in the four header tables matches my measured result (0 mismatches). But:
   - 17 tests in `test_demo_only_guard.py` are labelled "cannot run on the old tree (no helper there)". In my setup `tools/fixed_run.py` was copied in (the builder's header says it was copied too), so all 17 ran: 13 PASS on both old heads, 3 FAIL on both (`test_a_changed_loader_is_not_the_same_as_the_other_one`, `test_every_start_of_a_program_in_tools_tests_and_src_is_the_helper_or_a_listed_follow_up`, `test_the_two_loaders_of_the_program_starter_are_the_same`), 1 FAILS on dd827d79 and PASSES on c7eb5c79 (`test_the_guard_and_the_helper_files_hold_exactly_one_marker_...`); see `raw/04-cannot-run-rows.txt`.
   - `test_the_sweep_finds_an_alias_a_from_import_and_the_os_calls` is new since both old heads, PASSES on both, is not named `test_pin_` or control, and is labelled "cannot run".
   - Tests new since c7eb5c79 that PASS there but FAIL on dd827d79 (allowed by the header rule "fails on that head or the other"): `test_a_named_error_in_reading_the_app_is_logged_at_warning_level_whatever_the_name_of_the_log_helper`, `test_a_stage_that_is_not_text_is_an_error_that_names_it`, `test_a_named_read_error_still_reads_unconfirmed_at_every_site`, `test_a_bug_in_reading_the_endpoint_of_a_source_is_not_turned_into_an_answer`, `test_a_token_that_an_earlier_pass_already_hid_is_not_hidden_twice_into_the_scheme_word`, `test_the_guard_and_the_helper_files_hold_exactly_one_marker_and_it_is_on_the_line_that_starts_the_program` (the last one already counted above).
   - A first run of `test_banner_mutant_table.py` on the old trees WITHOUT `tests/banner_mutants.py` copied in gave 12 header mismatches; with it copied in (the file is part of this head's tests) 0 mismatches. First run kept as `raw/failbefore/*first-run-without-banner_mutants.log`. The header's words "files of this head's tests" is the reason I treat the second run as the right one.
   - `test_demo_only_guard_ci.py` and `test_workflow_files_parse.py` have no header table; all their tests (8 and 4) PASS on both old trees.
6. `ruff` here is 0.16.9 (the repo pins 0.17.1 in `pyproject.toml`); `bandit` 1.9.4 as pinned. Python test runs used an existing venv (`/home/user/build/ER6-venv3.13` and `ER6-venv3.12`, pytest 9.2.0, no xdist or hypothesis installed), not a fresh `uv sync`. No test run showed a failure from that, but the exact dependency set was not checked against `uv.lock`.
7. Skips inside passing files (rc=0): `tests/contracts/test_capabilities.py` 2, `test_k3_pilot_env.py` 1, `test_k5_postgres.py` and `test_k5_round8_postgres.py` whole file (no database here), `test_peel_run_id.py` 1, `warden_port/test_audit_chain.py` 3.

## 1. Lint and suppressions

- `ruff check src tests tools`: All checks passed (rc 0). `ruff check src tests demos tools` (the CI form): All checks passed.
- `ruff format --check`: 335 files already formatted (tools form), 331 (CI form including demos). rc 0.
- `bandit -ll -r src` and CI form `bandit -q -r src demos tools -ll`: no issues, rc 0 (only "nosec ... no failed test" warnings at `demos/ask-your-data/db/lumen.py:723` and `src/hadavin_sdk/tools.py:389`, both outside this diff).
- Suppression pattern on added lines (`noqa|nosec|type: ignore|pragma|pylint|fmt: off/skip`): 5 matching added lines (`raw/03-suppress.txt`); exactly ONE real marker, `tools/fixed_run.py:42` `# noqa: S603 - the shape is checked above ...`. The other 4 are CHANGELOG text (2), the docstring of `tests/fixed_run.py` (1) and a test regex string (1).

## 2. Mutant table (`tests/banner_mutants.py`, Python 3.13, 10 chunks, 366 rows, one process at a time)

Every chunk printed its summary line (none NOT RUN). Chunk times about 70-85 s. Raw: `raw/05-full0..9.log`, all rows `raw/05-all-rows.txt`.
Totals: KILLED 350, CRASH 14 (rows B5 B7 B13 B34 B43 B44 B52 B54 B62 N6 N7 R7A4b R9A4 R9E4: these are the table's pinned crash rows, each marked good), SURVIVED 2 (J27, R10C2 above). 364 of 366 good.
Requested rows (`raw/05-requested-rows.txt`): B12, R13A8, R13A9, R13B1-R13B4, R14A1-R14A3, R14C1 and all 29 R15 rows (R15B1, R15D1-D9, R15E1-E3, R15H1-H8, R15Kshell, R15Kexecutable, R15Kpreexec_fn, R15Kstdin, R15Kcwd, R15Kenv, R15Kcapture_output, R15Kencoding): **40 of 40 KILLED** (B12 first line: killed by `test_pin_the_lists_are_required_so_an_unchecked_call_cannot_...`). The builder's "47 of 47" does not match my count of requested rows (11 named + 29 R15 = 40); the numbers 47 and 40 differ by 7 and I could not tell which rows make up the builder's 47.

## 3. Focused tests (each file alone, no -x, env stripped of cloud settings)

50 files = the 45 test files that import a changed module or helper by name or path, 4 files that import `kinds`/`app`, and `tests/test_workflow_files_parse.py` (list: `raw/04-focused-list.txt`; the four changed test files are in it). Each on 3.13 and 3.12: **100 of 100 runs rc=0.** Table `raw/04-focused-table.md`, per-run logs `raw/focus/`.
Counts per file are in the table.

Test files NOT run (84 of 134, `raw/04-test-files-not-run.txt`): the ones that do not name a changed module in an import or path (my selection is a text search, not a proof of no import through another module; a file that reaches `app.py` only through a helper would be missed). The full suite was not run (cloud rule).

## 4. Fail-before (new tests of this head against old trees, helper files copied in)

Old trees `dd827d79` and `c7eb5c79` in scratch worktrees; copied in: the six test files, `tests/banner_mutants.py`, `tests/fixed_run.py`, `tests/seeded.py`, `tests/refusal.py`, `tools/fixed_run.py`. Logs `raw/failbefore/`.

| file | dd827d79 failed / passed | c7eb5c79 failed / passed |
|---|---|---|
| test_mode_banner.py | 44 / 138 | 8 / 174 |
| test_demo_only_guard.py | 29 / 139 | 18 / 150 |
| test_banner_mutant_table.py | 3 / 22 | 2 / 23 |
| test_changelog_numbers.py | 11 / 3 | 7 / 7 |
| test_demo_only_guard_ci.py | 0 / 8 | 0 / 8 |
| test_workflow_files_parse.py | 0 / 4 | 0 / 4 |

Header tables vs measured: 0 mismatches (details and the labelling items in discrepancy 5). Passing on old but not labelled pin or control: see discrepancy 5.

## 5. Masker hostile inputs (`raw/06-hostile.log`; made-up values built from parts)

Shown unchanged: `bypass=true`, `bypass=0`, `bypass=1`, `bypass=TRUE`, `bypass=true  ` (trailing spaces only), `password: <v>`, `--password <v>`, `{"token": "<v>"}`, `"authorization": "Bearer x"`.
Hidden: `bypass=abc123 more text after` -> `bypass=<hidden> more text after`; `bypass=true and more` -> `bypass=<hidden> and more`; `bypass=<v>` and `bypass=yes<TAB>next` -> value hidden; `bypass_key=<v>` -> `bypass_key=<hidden>`; `authorization=Digest username="a", response="b"` -> `authorization=<hidden>`; `authorization: Bearer <t>` -> `authorization: <hidden>`; `authorization=Bearer <t>` -> `authorization=<hidden> <hidden>`; `"authorization": "Bearer <11-char mixed token>"` -> `Bearer <hidden>`; URL user and password -> `https://<hidden>@host/x`.
Empty file list: `include_new=True` on an empty repo -> `demo_only_guard: git listed no files in <repo>; refusing to scan an empty list`. `include_new=False` -> `git listed no tracked files (git add the files you want in the copy) in <repo>; refusing to scan an empty list`; with one untracked file: `include_new=True` lists `['f.txt']`, `include_new=False` gives the "no tracked files" message.

## 6. S603 helper

`raw/06-fixed-run-tests.log`: 12 selected tests pass (shape refusals, one-marker test, direct-start sweep). Hostile run `raw/06-fixed-run-hostile.log` in discrepancy 3. Direct starts: discrepancy 4 (`raw/06-direct-starts-all.txt`, `raw/06-demos-direct-starts.txt`).

## 7. Lines over 100 columns among lines ADDED since merge base 2a8c2aac (handover/ excluded)

461 lines over 100 columns (`raw/07-long-lines.txt`, per file with lines): comments 164, markdown prose (CHANGELOG) 17, inside multi-line strings or docstrings 28, python code lines 204 (includes one-line strings and trailing comments; 86 of them in `tests/banner_mutants.py`), other files (yml, css, js code, toml comment lines counted under comments) 48. Longest added line: 6157 columns. I did not check ruff's line-length setting.

## Not run

Full suite; the 84 test files above; Postgres-backed tests (skipped, no database); mutant rows only on 3.13 (not 3.12); no `uv sync` environment (reused venvs); no CodeQL, SonarCloud, CodeRabbit, gitleaks or CI workflow run; no `pip-audit`/`zizmor`.

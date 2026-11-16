# EV-PRHb5 results: PR H (strip hidden controls) head 3db0d34d827fc5c8bc83db9c0be092aafd186868

EVIDENCE RUNNER: results are recorded, not judged, nothing was fixed. Run 2026-11-12 01:33 to 02:20 UTC (07:03 to 07:50 IST). Raw logs: /home/user/build/evidence-raw/PRHb5-3db0d34d/ (outside the repository).
Head confirmed: `git rev-parse HEAD` in my worktree = 3db0d34d827fc5c8bc83db9c0be092aafd186868 (= origin/wip/cloud-prh-b5), `git status --short` empty. Previous reviewed head d08ec151, origin/main 2a8c2aac. The main checkout itself sits on another commit (64a78591); I did not use it. I did not read handover/evidence/PRH/b5/ or the builder notes.

## Failed, not run, or different from the ticket (first)

| # | What | Result |
|---|---|---|
| F1 | Perf marker run (`pytest -m perf`, three slot locks held) | exit 1: 1 failed, 61 passed, 12936 deselected in 121.79 s. The failed test is `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (`assert False ... is_superlinear(quadratic, 'a', 16*1024, 256*1024)`) |
| F2 | The same timing test alone, 3 runs each (all slots held) | head: pass, FAIL, FAIL (1 of 3 passed). origin/main: FAIL, FAIL, FAIL (0 of 3). Each about 0.6 s. In the full suite at the head it passed (item 5) |
| F3 | Readable-secret probe (own script, section "Probe" below) | On the head, the rows listed in P-head-yes below still show a piece of the handed-out value, or a piece of a key on a direct `redact()` call, in the output. Table and raw output below |
| F4 | Ticket 6.1 item 1: files outside the allowed list | 4 changed files are not in the ticket's allowed list: src/hadavin_sdk/defaults.py, tests/fixtures/prh_accidental_pairs.json, tests/fixtures/prh_main_passes.json, tests/test_k5_fixes3.py |
| F5 | Ticket 6.1 item 2, added `noqa` / `type: ignore` / `nosec` lines | none found (grep of added lines vs origin/main exit 1 = no match; the two lines of the previous head are gone) |
| F6 | Cost table (ticket 6.1 item 9) | H rows ratio to main 2.78, 3.36, 4.68, 3.28 at 262,144 characters; S1-S5 0.98 to 1.03. Only 262,144-character rows and S1-S5 and H1-H4 were printed (no 65,536 rows, no W row, no passes column). `cost.log` |
| F7 | First bandit command | `uv run --no-sync bandit ...` exit 2 (bandit is not in the venv: "Failed to spawn: bandit"). Rerun with `uv run --no-sync --with bandit bandit -q -r src demos tools -ll`: exit 0 |
| F8 | Install | `uv sync --locked --all-extras --group test` (without `--no-build`, as the brief says) exit 0 for the 4 venvs |
| F9 | Not run | Python 3.12 full suite; full suite and skip list on origin/main; CI steps outside the redaction package (Semgrep, zizmor, Trivy, pip-audit); ticket 6.1 item 11 as the ticket's row table for F/B/M5 rows; fail-before against origin/main (the brief this time asks for d08ec151 only) |
| F10 | Mutant count | 71 of 71 good (previous head: 55 of 55) |

## Results table

| Item | Command (head worktree, cloud variables unset, own venv) | Exit | Last line |
|---|---|---|---|
| (1) changed files | `git diff --name-only origin/main...HEAD` | 0 | 29 files (`files.txt`); 4 outside the allowed list (F4) |
| (1) suppressions | grep of added lines for noqa / type: ignore / nosec | 1 (no match) | none |
| (2) ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| (2) ruff format | `ruff format --check src tests demos tools` | 0 | 333 files already formatted |
| (2) bandit | `bandit -q -r src demos tools -ll` (via `--with bandit`) | 0 | only "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" (twice) |
| (2) scan | `python tools/scan_repo.py` | 0 | (no output) |
| (2) stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| (2) gitleaks | `gitleaks git --config .gitleaks.toml --redact --exit-code 1 --log-opts origin/main..HEAD` | 0 | no leaks found |
| (3) full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, HADAVIN_REQUIRE_PINNED_UNIDATA=1, own Postgres 16.15 (127.0.0.1:56853, PGHOST = socket dir, HADAVIN_TEST_PG_DSN set) | 0 | 12935 passed, 1 skipped, 62 deselected in 334.27s; skipped: tests/contracts/test_llm.py:95 |
| (4) PR H mutants | `heavy.sh python tests/prh_mutants.py` in a separate worktree (venv of its own) | 0 | 71 of 71 good; problems: [] |
| (5) perf marker alone | three slot locks nested, `pytest -m perf -rs` | 1 | 1 failed, 61 passed in 121.79s (F1) |
| (5) timing test x3 head | alone, three locks | 0, 1, 1 | pass, fail, fail |
| (5) timing test x3 main | alone, three locks | 1, 1, 1 | fail x3 |
| (5) cost table | `python tests/test_prh_perf.py --compare-main <main worktree>`, alone | 0 | F6 |
| (6) fail-before | delta test files vs d08ec151 copied onto a detached worktree of d08ec151 src: `pytest -rA --continue-on-collection-errors -m "not live and not perf"` on test_prh_hidden_unit, test_prh_regressions, test_prh_steps, test_prh_tools | 1 | 33 failed, 2125 passed |
| (7) probe | own scripts `probe_b5.py`, `probe_h.py` (copied here), head vs origin/main | 0 each | tables below |

Delta test files (git diff --name-only d08ec151 HEAD -- tests): tests/fixtures/prh_regressions.json, tests/prh_mutants.py (runner, not run as a test), tests/test_prh_hidden_unit.py, tests/test_prh_perf.py (perf marker, deselected), tests/test_prh_regressions.py, tests/test_prh_steps.py, tests/test_prh_tools.py. The fixture was copied.

## (6) Fail-before detail (lists only)
- 33 FAILED on d08ec151 src: 3 in test_prh_hidden_unit.py, 6 in test_prh_regressions.py, 14 in test_prh_steps.py, 10 in test_prh_tools.py. Full id list: `fb-failed.txt`.
- New test functions of the delta (names added with `+def test_`: 21) that PASSED on d08ec151 src (7): test_prh_regressions.py::test_tail_row_trail_is_masked, ::test_tail_row_on_the_next_line_is_masked, ::test_tail_row_long_tail_is_masked, ::test_a_refusal_is_not_masked_unless_the_row_says_so; test_prh_steps.py::test_undo_entity_cut_by_a_control_reference_is_whole, ::test_pass_bound_holds_for_a_seeded_search, ::test_every_regression_row_needs_at_most_seven_passes. (`new-passing-on-d08.txt`; parametrized rows of the changed fixture are in the raw log.)

## Probe (7): is a piece of the secret readable in the output? (yes = readable)
Own scripts, values built from parts (KEY = the allowed example key, HAND = a made-up handed-out value). Paths: untrusted = `runmap.redact_untrusted(t, {})`; tool = `tools.prepare_output(t, {}, 4000, [HAND])`; error = `tools.error_reason(ValueError(t), [HAND])`; head = `runmap.safe_head(t, 4000)`. "yes" = the whole value or its tail piece (the part after the hidden item) stands in the output. The handed-out list exists only on the tool and error paths (untrusted and head are given none, so a handed-out value reads "yes" there on main and head alike). Full per-path output: `probe-head.txt`, `probe-main.txt`, `probe-h-head.txt`, `probe-h-main.txt`.

### Earlier rows, summary (main untrusted/tool/error/head -> head untrusted/tool/error/head)

| Row | main | head |
|---|---|---|
| L1-L5, L7, L9-L11, M2a, M2b | yes/yes/yes/yes (probe-main.txt) | no/no/no/no |
| L6 (handed out) | yes on all four | yes/no/no/yes (no list on untrusted and head) |
| L12 (handed out, C1 CSI) | yes on all four | tail piece yes/no/no/yes (no list on untrusted and head) |
| L8 (NUL) | no/yes/no/no | no/no/no/no |
| G1, G2 | no/no/no/no | no/no/no/no |
| G3 | yes on all four | no/no/no/no |
| control: plain key | no/no/no/no | no/no/no/no |
| control: key cut by a tab (not hidden) | yes | yes/yes/yes/yes |

### New rows (a), (b) of this brief

| Row | main (untrusted/tool/error/head) | head (untrusted/tool/error/head) |
|---|---|---|
| (a) `"a "+ESC+HAND+" ; user"+BEL+KEY` (character reading) | no/no/no/no (HAND and KEY pieces) | no/no/no/no |
| (b) `"a "+HAND[:9]+ESC+"(B"+ESC+"[m"+HAND[9:]+" ; user"+BEL+KEY` | HAND tail yes/yes/yes/yes | HAND tail yes/no/no/yes (untrusted and head: no list); KEY pieces no on all four |
| (b2) same without a handed-out list | no/no/no/no | no/no/no/no |

### (d) `redact()` direct call (guard.redact.redact), escape sequence in the text

| Case | main | head |
|---|---|---|
| d1 key cut by ESC [ 0 m | key tail readable: `id AKIA IOSFODNN7EXAMPLE` | masked `id <APIKEY_1>` |
| d2 `user`+BEL+KEY plus a second cut key | second key readable | both masked |
| d3 key cut by ESC ( B ESC [ m | tail readable, ESC left in output | `id AKIA(B IOSFODNN7EXAMPLE`: key tail readable, no ESC left (YES readable on head) |
| d4 cut by title string | readable | masked |
| d5, d7, d8 | d5 key tail readable (`id =AKIA IOSFODNN7EXAMPLE`); d7 masked; d8 key split by spaces (`AKIA IOSFODN N7EXAMPLE`, no whole piece) | masked on all three |
| d6 key plus U+0301 (not a hidden item) | readable | readable |
| d9 300 distinct cut keys | all 300 tails readable | output is the withheld note, 0 readable |
| d10 seeded map value cut by ESC [ 0 m | masked `<SECRET_1>` | masked |
| d11 seeded map value, ESC directly before the value | tail readable (`r0ub4dor-3xyzQ x`) | tail readable (YES, same output) |

### Lead addition H1-H3 (HAND = a made-up handed-out value built from parts; "y" = readable)

| Row | Piece | main untrusted/tool/error/head | head untrusted/tool/error/head |
|---|---|---|---|
| H1a `"x "+HAND+" y "+ESC+HAND` | whole HAND | y/n/n/y | y/n/n/y |
| H1a | HAND[1:] (the copy after the ESC) | y/n/n/y | y/y/y/y |
| H1b `"x "+HAND+" y "+HAND[:9]+ESC+"(B"+ESC+"[m"+HAND[9:]` | whole HAND | y/n/n/y | y/n/n/y |
| H1b | HAND[9:] (tail) and HAND[:9] (front) | y/y/y/y | y/y/y/y |
| H2 `"log "+ESC+HAND[:11]+TRUNCATED` (TRUNCATED = newline + `[truncated]`, from tools.py) | HAND[1:11] | y/n/n/y | y/y/y/y |
| H3 key cut by ESC+letter, then `"user"+BEL+IP` with the map already holding the IP | `user`+IP glued ("user10.20.30.44") | no/no/no/no | no/no/no/no |
| H3 | key tail piece | y/y/y/y | n/n/n/n |
| H3 output on head | | | `id <APIKEY_1> user <IPV4_1>` on all four paths |

Output texts of H1a on head tool path: `x <SECRET_REDACTED> y x7mLp-9vRtzKw2` (the copy after the ESC stands readable without its first character). H1b head tool path: `x <SECRET_REDACTED> y Qx7mLp-9v(B RtzKw2`. H2 head tool path: `log x7mLp-9vRt` then the truncated note.

## Environment
Python 3.13.18; 4 venvs (head, main, d08ec151, mutants worktree). Machine shared with other agents' heavy jobs: the full run queued about 7 minutes, the cost job about 18 minutes in the queue. Own Postgres 16.15 stopped and removed at the end; worktrees removed at the end.

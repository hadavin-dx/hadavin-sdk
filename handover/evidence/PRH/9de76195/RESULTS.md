# EVIDENCE RUNNER results: PR H batch 10, head 9de76195 (redaction path)
Runner records only; nothing here is a verdict. Raw logs (outside the repo): /home/user/build/evidence-raw/PRHb10-9de76195/. Run 14:20 to 15:05 UTC (19:50 to 20:35 IST). Head verified: `git rev-parse HEAD` = 9de76195728ce1f81058c605fa2fce9cf8b0f3e8 in my own worktree, tree clean; origin/wip/cloud-prh-b10 tip is the same. Own venv (`uv sync --locked --all-extras --group test`; the `--no-build` form failed with "hadavin-sdk ... marked as --no-build but has no binary distribution", exit 2, so I synced without it as the brief says). Postgres 16.15 of my own, stopped afterwards.

## What failed or was not run (first)
1. FAILED: `pytest -m perf` on the head: "1 failed, 62 passed, 13211 deselected in 130.88s", exit 1. The one failure is `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` ("a quadratic function must be flagged"), the known flaky test. Run alone 3 times: head fail, fail, fail; origin/main fail, fail, pass. (So it failed 3 of 3 on head and 2 of 3 on main in this session.) I did not rerun the whole perf group.
2. NEW FINDING from my own fuzz (details in table 6): on the head, a text with a literal backslash-e spelling INSIDE a secret is shown unmasked. Handed-out secret with `\e` spliced mid-value, and with `\e` between every character: masked on f01a9f8f, readable on head. Token-shaped value with `\e` mid-value or in front: readable on head. On origin/main the first three of these rows are also readable; the `\e`-between-every-character handed-out row is not readable on main by my 8-character test.
3. Differences from the builder's claims: builder said full pytest 1 failed (dblink-connect); I got 0 failed (13210 passed). Builder said fail-before 33 failed / 2046 passed over five files; mine is 32 failed / 152 passed over four files with perf excluded (the perf file is marked perf and is not run by `-m "not live and not perf"`); I did not reproduce 2046. Not run: n1 (dropped-view check in guard/runmap.py) killer test or mutant (none exist in the delta; I did not probe it). Not run: CodeQL, Sonar, CodeRabbit.

## Table
| # | Item | Command (short) | Exit | Last line / result |
|---|------|-----------------|------|--------------------|
| 1a | prh_mutants as root | `python tests/prh_mutants.py` (alone) | 0 | `156 of 156 good; problems: []` |
| 1b | prh_mutants as nobody | uid 65534, git-archive copy, `env -i` | 0 | `156 of 156 good; problems: []` (no survivors in either run) |
| 2 | full pytest | `-m "not live and not perf" -rs`, via heavy.sh, own Postgres | 0 | `13210 passed, 1 skipped, 63 deselected in 568.60s`; skip: tests/contracts/test_llm.py:95 |
| 3 | stage_mutants | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 4a | perf pytest, alone | `-m perf -rs` | 1 | `1 failed, 62 passed, 13211 deselected` (flaky test above) |
| 4b | perf compare vs main | `tests/test_prh_perf.py --compare-main <main tree>` | 0 | ratios below |
| 4c | perf compare vs f01a9f8f | same, old tree | 0 | ratios below |
| 5 | fail-before | 4 changed test files copied into detached worktree of f01a9f8f (old src, confirmed by `__file__`), `-m "not live and not perf"` | 1 | `32 failed, 152 passed` |
| 6 | own fuzz | ownfuzz.py, 3 trees | 0 | table below |
| 7a | ruff check / format --check (src tests demos tools) | | 0 / 0 | `All checks passed!` / `339 files already formatted` |
| 7b | bandit -ll (src demos tools) | `uv run --with bandit` | 0 | only warnings (nosec B102 at tools.py:390 "no failed test") |
| 7c | tools/scan_repo.py | | 0 | no findings printed |
| 7d | gitleaks origin/main..head | | 0 | `no leaks found` |
| 7e | gitleaks dir on this folder | | 0 | no leaks found |
| 8 | files in `git diff --name-only origin/main...HEAD` | | | 124 files (list in raw folder difffiles.txt) |

## Perf compare (median CPU seconds, 262144 chars; ratio = head / other)
| shape | vs main | vs f01a9f8f |
|---|---|---|
| S1 plain ASCII log | 1.05 | 1.01 |
| S2 tab table | 1.04 | 0.98 |
| S3 JSON lines | 1.08 | 0.99 |
| S4 Hindi | 1.00 | 0.99 |
| S5 Persian ZWNJ emoji | 1.04 | 1.00 |
| H1 coloured output | 3.00 | 1.02 |
| H2 colour inside a word | 3.47 | 0.99 |
| H3 sgr0 inside a word | 4.98 | 1.01 |
| H4 colourised log with sgr0 | 3.45 | 1.01 |
| P1 one very long spaced run | 1.04 | 0.58 |
| P2 32 medium spaced runs | 1.60 | 0.96 |
| P3 32 spaced runs sharing a prefix | 1.60 | 1.03 |
| P4 2000 values sharing 12 characters | 1.17 | 0.69 |

## Fail-before (item 5)
Four changed test files (test_prh_b10, test_prh_b9, test_prh_b9_docs, test_prh_wiring) on f01a9f8f source: 32 failed, 152 passed (ids in failbefore-failed-ids.txt). The perf test file was not run (perf marker). Tests added by the delta (by name) that pass on the old code: 10 rows, listed in added-tests-passing-on-old.txt (g1 run-under-budget, g1 suffix-of-prefix, g1 automaton finds what old search found, g3 full-stop alone, g3 dashes between characters, g3 known value with visible dash, g3 value glued to key name, g3 any separator, g4 copy sweep cannot mask, g5 unknown value no pattern shape). I did not list changed-but-not-added tests that pass on old.

## Own fuzz (item 6; ownfuzz.py typed by me from the brief; 912 texts per tree; made-up values built from parts; "readable" = any 8-character stretch of the planted value appears in the output; "withheld" = output holds only the marker or the withheld notice)
Categories: hidden controls (13 kinds, chunk sizes 1/2/3/5, mid), encoded ESC (13 spellings incl. `\x1b`, `\u001b`, `\033`, `\e`, `%1b`, `&#27;`), lone ESC plus 12 charset sequences, split secrets (12 separators), spaced-out values (10 separator kinds, lengths 10/12/16/28), fronts left by 13 unterminated string openers, run cap (1..200 runs, secret at end/front, and no secret).
| tree | readable | withheld | raised errors | clean corpus withheld |
|---|---|---|---|---|
| origin/main | 506 | 46 | 0 | 11 of 80 |
| f01a9f8f | 174 | 417 | 0 | 11 of 80 |
| head 9de76195 | 177 | 415 | 0 | 11 of 80 |
Clean corpus (same files for all trees, taken from the head tree): docs/**/*.md, root *.md, src/hadavin_sdk/*.py, 3000-character chunks, first 30000 characters of each file: 80 chunks. Withheld 11 on all three trees (the same count; I did not check which chunks).
Readable by category (head): charset_pairs 1, esc_mid 4, esc_pre 2, opener_spaced 3, opener_split 18, spaced 28, spaced_mixed 7, split 95, split3 19 (my split and spaced rows with a visible separator count as readable when the separator leaves 8 characters intact; I did not decide which of those are expected).
Head vs f01a9f8f: newly readable on head: esc_mid/hand/11, esc_mid/shaped/11, esc_pre/shaped/11 (all the backslash-e spelling); withheld on f01a9f8f but not on head: esc_mid/hand/11, esc_each/hand/11 (same spelling). No row is readable on f01a9f8f and not on head other than those; no row readable on main and unreadable on head was excluded from the count: 10 rows readable on head but not on main, 167 readable on both.
Examples on head (made-up values): handed-out value with `\e` mid-value printed whole; handed-out value with `\e` between every character printed whole with the `\e`s; on f01a9f8f the same texts print `<SECRET_REDACTED>`.

## Not judged
No verdicts. Builder notes were used only to find commands. Nothing was fixed or edited in src/ or tests/. Worktrees, my Postgres and the nobody copy were stopped or removed (see end).
worktrees removed, pg stopped and deleted, nobody copy deleted

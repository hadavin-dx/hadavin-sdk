# EVIDENCE RUNNER results, PR H batch 7, head 5f9df48e507f9128df40ad0b89c210f8067741d6 (tag PRHb7)

Record only. Nothing was fixed, judged or edited. Started 06:08 UTC (11:38 IST), finished 06:45 UTC (12:15 IST). Raw logs: /home/user/build/evidence-raw/PRHb7-5f9df48e/ (outside the repository).
Run as root (uid 0) unless a row says nobody. Own detached worktrees at the head, at main 2a8c2aac, at c802cc0f. Head checked: `git rev-parse HEAD` = the sha above, `git status --short` empty.

## What failed, deviated or was not run (first)
1. `uv sync --locked --no-build` FAILED (exit 2: "hadavin-sdk==0.1.0 editable can't be installed because it is marked as --no-build but has no binary distribution"). I ran `uv sync --locked --all-extras --group test` (no `--no-build`) instead; it succeeded. All runs use that venv.
2. `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED 3 of 3 on the head and 3 of 3 on main 2a8c2aac (alone, one at a time, 0.6 s each; assertion "a quadratic function must be flagged"). It also failed inside `pytest -m perf` on the head (see item 9).
3. `pytest -m perf` (as ci.yml does, alone, all three slots) on the head: exit 1, `1 failed, 61 passed, 13059 deselected in 126.02s`; the one failure is the test of item 2.
4. Perf compare: the tool printed rows S1-S5 and H1-H4 at 262,144 characters only. No W row and no 65,536-character rows were printed (the tool's output, unchanged). Ratios of H1-H4 are 2.83, 3.43, 4.62, 3.30 (builder wrote 2.65-4.57).
5. Own fuzz (item 6): on the head 9 of 3096 texts still show an 8-character stretch of a made-up secret (all 9 are in the random group; of the 8 listed in ownfuzz-wt.log, 7 are windows of the example key and 1 of the handed-out value). Examples in ownfuzz-examples.log: handed-out value cut by ESC + OSC + ESC-backslash + ESC leaves `s-8kLpv3` readable. Same 9 texts on c802cc0f.
6. Files in the diff outside the ticket's allowed list (item 1): 16, listed in 1-outside-allowed.txt (handover evidence, defaults.py, scrub_settings.py, test_k5_fixes3.py, prh_main_passes.json, test_prh_b7.py, ...). Ticket section 8.7 (errata) is the place that may cover them; I did not check it.
7. Not run: Python 3.12 suite, CI-only jobs (CodeQL, SonarCloud, CodeRabbit), Vault tests (the vault server is not present; skipped by the suite's own rules), semgrep/pip-audit/zizmor/trivy steps of ci.yml (not in the package brief). `uv run --with bandit` and CI's `bandit -r src demos -ll` differ by `tools`; I ran with `tools`.
8. 13 of the 62 tests that fail on the old code are tests that existed before and were changed in DELTA; the new-test split is below.

## Table
| # | Item | Command (short) | Exit | Last line / result |
|---|---|---|---|---|
| 1 | diff list | `git diff --name-only origin/main...HEAD` | 0 | 41 files (1-difflist.txt in raw folder); 16 outside the ticket's allowed list |
| 2a | ruff check src tests demos tools | uv run ruff check | 0 | All checks passed! |
| 2b | ruff format --check | same | 0 | 334 files already formatted |
| 3 | bandit -ll src demos tools | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only warning: nosec B102 at tools.py:389 |
| 4a | scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 4b | stage_mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks origin/main..HEAD | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 | full pytest, own Postgres 16 (unix socket), via heavy.sh | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 0 | 13058 passed, 1 skipped, 62 deselected in 483.68s; skip: tests/contracts/test_llm.py:95 |
| 6a | prh_mutants as root | `python tests/prh_mutants.py` via heavy.sh | 0 | 100 of 100 good; problems: [] |
| 6b | prh_mutants as user nobody | same, via su nobody, own TMPDIR | 0 | 100 of 100 good; problems: [] |
| 6c | stage_mutants | see 4b | 0 | 37 of 37 good |
| 6d | builder fuzz_classify.py (3000 texts) | run on each tree via PYTHONPATH | 0 | head: withheld 143, readable windows 0; main: withheld 0, readable windows 1408; c802cc0f: withheld 102, readable windows 548, InputTooLarge 7 |
| 6e | equivalence_100.py | head | 0 | `texts 7000 | outputs differing with the extra view 0`; same as the builder's .out file |
| 6f | clean_corpus.py | head | 0 | 15 texts, 60 runs, withheld or wrong: 0 |
| 6g | own fuzz (own_fuzz.py, 3096 texts: 24 hidden kinds x every cut position of 3 made-up secrets + 1500 random multi-cut) | each tree | 0 | readable 8-char stretches of the secret: main 1607, c802cc0f 9, head 9; withheld: main 0, c802cc0f 182, head 226 |
| 7 | fail-before: DELTA test files copied onto c802cc0f src (4 test files), `-rA` | pytest | 1 | 62 failed, 2188 passed (2250 tests). Of 95 new tests (ids new vs c802cc0f): 46 PASS on old code (7-new-passing-on-old.txt), 49 FAIL (7-new-failing-on-old.txt). Matches the builder's 46 of 95 |
| 8 | ticket acceptance 11 rows (own script rows.py): L1-L12, M2, G1-G3, F1a-g, B1, B2 | head vs main | - | head: all MASKED except L6, L12 on the "untrusted" path (no handed-out list there; tool path MASKED); all F rows ok. main: L1-L12 (except L8 untrusted), M2, G3 LEAKED; F1 rows FORGED |
| 8b | acceptance 8 module list | python -c import | 0 | exactly the ticket's list; hidden.py imports no hadavin_sdk module (grep rc 1 = none found) |
| 9a | perf compare --compare-main main, alone (3 locks) | tests/test_prh_perf.py | 0 | S1-S5 ratios 0.98 0.86 1.02 0.90 1.04; H1-H4 2.83 3.43 4.62 3.30 (9-perf-compare.log) |
| 9b | pytest -m perf alone | as ci.yml | 1 | 1 failed (the timing flake), 61 passed |
| 9c | timing flake alone x3 head | pytest one test | 1,1,1 | failed 3 of 3 |
| 9d | timing flake alone x3 main | pytest one test | 1,1,1 | failed 3 of 3 |
| 10 | gitleaks on builder evidence folder handover/evidence/PRH (in the head worktree) | gitleaks dir | 0 | no leaks found (no hit to report) |

Fail-before list: see 7-new-passing-on-old.txt and 7-new-failing-on-old.txt in this folder.

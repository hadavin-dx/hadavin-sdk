# EVIDENCE RUNNER results: PR H batch 11, head 242dfd66 (full 242dfd662227da9b609add230dd1e99e5af164ed), tag PRHb11

I only ran and recorded. I changed no source, test or branch. Raw logs: `/home/user/build/evidence-raw/PRHb11-242dfd66/` (outside the repo). Small excerpts are in this folder.
Head confirmed: `git rev-parse HEAD` = full sha above, tree clean, detached worktree. Builder files under `handover/evidence/PRH/b11/` were not used as results.

## Failed, not run, or different from the builder's claim (first)

1. `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED once in the perf run (`pytest -m perf`: 1 failed, 62 passed, 0 skipped; builder claimed 62 passed 1 skipped). This is the known timing test the brief says to record separately. Run alone: head 2 passed 1 failed (3 runs), main 3 passed (3 runs). Those 6 runs were NOT on an idle machine (other agents were running), the perf-step run was with all three heavy slots held.
2. Full pytest at head: 13286 passed, 1 skipped, 63 deselected (exit 0). The builder's number was 12830 passed, 457 skipped at code head 63525de6. My run had the Postgres service and `HADAVIN_REQUIRE_PINNED_UNIDATA=1` set; I did not find out why the counts differ (the 457 skips and the 456 extra passes), I only record it.
3. Fail-before, other changed test files (test_prh_b10, b8, b9, b9_docs copied onto 5c430b6a, src from 5c430b6a): 4 failed, 150 passed (list in `failbefore-others-failed.txt`). The 3 failures in test_prh_b9_docs.py end in FileNotFoundError for `handover/evidence/PRH/b11/numbers.txt`, a file I did not copy (the brief says copy only test files); I did not look into the failure of test_b10_g5.
4. `uv sync --locked --no-build --all-extras --group test` (CI's command) fails here: "hadavin-sdk is marked --no-build but has no binary distribution". I ran it without `--no-build` (exit 0).
5. My first fail-before run was INVALID: the venv is an editable install of the head worktree, so the old worktree's tests imported head src and 74 of 74 passed. I redid it with `PYTHONPATH=<old worktree>/src` (probe printed the old path). The invalid log is kept as `failbefore-b11-INVALID-head-src-imported.log` in the raw folder.
6. Item 1 was not strictly "alone": the cheap checks (ruff, bandit, scan_repo, gitleaks) ran while the root mutant run was running; the other agents' heavy jobs were also running on the same machine (heavy.sh, load about 3.5).
7. The fuzz and the clean-corpus script were run directly, not through heavy.sh (the heavy queue was full for over 30 minutes; they are single-process scripts).
8. Not run: CI's py3.12 job, the Vault-based tests (no Vault server; they skip or are counted in the 1 skip), the Windows-only paths, any live call.

## Results

| Item | Command (all from the head worktree, cloud env stripped) | Exit | Last line |
|---|---|---|---|
| 1 root | `python tests/prh_mutants.py` as root, alone in its heavy slot | 0 | `176 of 176 good; problems: []` (4 of them are accepted "CRASH" kills: 22, 24, 143, 158) |
| 1 nobody | same, as user `nobody` (HOME and TMPDIR under /tmp, tree read-only for it) | 0 | `176 of 176 good; problems: []` |
| 1 survivors | | | none in either run |
| 2 | `pytest -m "not live and not perf" -p no:cacheprovider -q -rfE -rs`, own Postgres 16.15 (unix socket, PGHOST/PGPORT in server and test env) | 0 | `13286 passed, 1 skipped, 63 deselected in 631.24s` (skip: tests/contracts/test_llm.py:95, Stubber) |
| 3 | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 4 pytest perf | `pytest -m perf` with all three heavy slots held | 1 | `1 failed, 62 passed, 13287 deselected in 134.53s` (the flaky timing test, see above) |
| 4 compare | `python tests/test_prh_perf.py --compare-main <main worktree 2a8c2aac>` with all three slots held | 0 | ratios below |
| 5 fail-before | `tests/test_prh_b11.py` on 5c430b6a (src old) | 1 | `45 failed, 29 passed`; the 29 that pass on old code are in `failbefore-b11-passed-on-old-list.txt` |
| 5b | other changed test files on 5c430b6a | 1 | `4 failed, 150 passed` |
| 6 | own fuzz, 922 texts x 3 trees (below); redactor crash probe (below) | 0 | |
| 6 clean | own seeded corpus, 6000 ordinary texts (corpus hash `e728cf5dbb31c119`), tool path | 0 | withheld A: head 0, 5c430b6a 0, main 0; D (everyday-letter secret with opener and copy): head 0, old 0, main 0; 0 errors |
| 7 ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 7 ruff format | `ruff format --check src tests demos tools` | 0 | `340 files already formatted` |
| 7 bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no issue lines; two warnings "nosec encountered (B102) ... tools.py:390" |
| 7 scan | `python tools/scan_repo.py` | 0 | no output |
| 7 gitleaks | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD` | 0 | `no leaks found` |
| diff list | `git diff --name-only origin/main...HEAD` | 0 | 175 files (`diff-names-origin-main-3dot-head.txt`); 63 files against 9de76195 was not recomputed |

Perf compare (median CPU seconds, 262,144 characters; head / main / ratio): S1 0.448/0.389/1.15; S2 0.452/0.401/1.13; S3 0.513/0.391/1.31; S4 0.841/0.792/1.06; S5 1.529/1.446/1.06; H1 0.718/0.238/3.01; H2 1.135/0.318/3.56; H3 1.869/0.373/5.00; H4 1.094/0.304/3.60; P1 0.573/0.481/1.19; P2 0.430/0.235/1.83; P3 0.209/0.119/1.75; P4 0.593/0.457/1.30; P5 1.849/0.422/4.38; P6 0.709/0.544/1.30. The builder quoted S1 1.10, H3 5.00, P5 4.16; mine are 1.15, 5.00, 4.38.

## Own fuzz (`myfuzz.py`, typed by me; 922 texts; made-up values built from parts; tool path `tools.prepare_output(text, {}, 4000, [handed value])`)
"Readable" = some 8 consecutive characters of the value appear in the output after dropping every non-letter, non-digit and folding case. "Withheld" = the fixed withheld text. Counts of 922 texts:

| tree | readable | withheld | masked | errors | timeouts |
|---|---|---|---|---|---|
| main 2a8c2aac | 581 | 19 | 322 | 0 | 0 |
| 5c430b6a | 239 | 99 | 584 | 0 | 0 |
| head 242dfd66 | 217 | 101 | 604 | 0 | 0 |

- No text is readable on head that is not readable on main or on 5c430b6a. 22 texts readable on 5c430b6a are not readable on head (listed by label in the json files).
- Classes with every text still readable on head: spaced-out values with combining marks (`spaced_cm`, `spaced_cm2`, `spaced_cm_w`: 12 of 12 each, same on main and 5c430b6a); spaced with wrapper characters: 42 of 252 readable on head (main 169, old 51); spaced-out with a visible gap (`spaced`): 2 of 12 readable on head (all with the token-shaped value); split values with filler words: 64 of 80 readable (same as 5c430b6a; main 76); `ctrl` 4 of 78; `esc_mid` 2 of 30 (main 30); `ctrlmid` 2 of 26.
- Backslash-e inside a value (`bslpath_in`): readable 10 of 12 on head (12 of 12 on old and main); the two now masked are labels `bslpath_in/shaped/2` (path `C:\Documents\error_logs`) and `/4` (path `\env`). Paths before the value (`bslpath`, `C:\env\x`, `C:\Users\err\x`, `C:\Documents\error_logs`): 12 of 12 masked, 0 withheld, on all trees.
- Texts reaching the run cap (value at the front, at the end, straddling the cap at 6 offsets, spaced and ESC-split straddles): 0 readable, 0 withheld, 0 errors on every tree.
- Redactor crash (`crash-probe.txt`: planted RuntimeError in `runmap._clean`): on head every path (plain, hidden, handed, spaced text, `error_reason`, `safe_head`) raises `RedactorCrash`; on 5c430b6a `error_reason` and `safe_head` RETURN a value; on main a `RedactionError` is raised. A planted crash at the top of `redact_untrusted` surfaces as the raw RuntimeError on all three trees (my probe in `myfuzz.py`).
- Clean corpus: my corpus withheld 0 of 6000 on all three trees (A and D), unlike the builder's 63 and 227 of 21,783 from its own corpus; I did not run the builder's corpus. My corpus is not the builder's; the two numbers are not comparable.

## Not judged
I give no verdict. Reviewers read the files here and the raw logs.

## Cleanup
Own Postgres stopped and removed, worktrees and venv removed (see the final report for the order); raw logs kept in `/home/user/build/evidence-raw/PRHb11-242dfd66/`.

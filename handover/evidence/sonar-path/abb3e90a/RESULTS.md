# Evidence run: SONAR-PATH head abb3e90acafe9915c911636251e5dc003a00842c (raw output only, no judgement)

Base: origin/main 51c9fc4f. Python 3.13.18 (venv q8c1-b17fix) and 3.12 (a throwaway venv built from the same package list; removed). Every run had PYTHONPATH under its own detached worktree and printed `hadavin_sdk.__file__` (first line of each file in `raw/`). No secrets, no network, no spend. Worktrees `/home/user/build/ER-sonarpath4-{head,a,b}` removed at the end; leftover mutation check: `git status` clean in head and (a) after all runs (the mutant runner works on temp copies).

## FAILURES AND GAPS FIRST
1. **Two mutant rows cannot run at this head (verdict ERROR "SNIPPET NOT FOUND", counted BAD by the runner):**
   - `S-replay an interrupt while marking is not named` (`tests/pathguard_mutants.py:1051`): wants `except (KeyboardInterrupt, MemoryError) as stop:` in `k1b/replay.py`; the source is now formatted over several lines (`except (\n KeyboardInterrupt,\n MemoryError,\n) as stop:`, replay.py ~line 322). The mutant text no longer matches, so that rule has no working mutant.
   - `H-signer the resolved key path is printed` (`pathguard_mutants.py:1116`): wants `source, pem = str(settings.private_key_path), path.read_bytes()`; signer.py now has it split over lines (~116-117).
   - Result: 165 of 167 rows good, 2 BAD.
2. **Raw OSError with a path escapes the guard** (hostile input, `raw/hostile_longname.txt`): an operator-typed folder or file path with one 256-byte component and `must_exist=False` gives `OSError [Errno 36] File name too long: '<full path>'` from `pathguard.operator_dir`, `pathguard.operator_file` and `LocalDirSink(root)`. With `must_exist=True` it is a `PathRefused` ("cannot be resolved", no path). So R10 is not applied to the `.exists()` / `is_file` step of `_operator` when the path need not exist. The text holds the operator-typed path (not file-system data).
3. Error text that prints the caller's own name (pinned wording, by design in the tests): `hashing.hash_files` and `secrets_file._fetch` echo the given name, e.g. `path escapes its folder: /tmp/.../outside/secret.txt`, `secret 'vault:token' not found...`, and a 255/256-byte name in full. The echoed text is the caller's input, not a path read from disk. Full table in `raw/hostile.txt`.
4. Not run (cloud limits / absent): full suite, Playwright; 16 tests skipped in the importer set, all `HADAVIN_TEST_PG_DSN not set` (postgres) (`raw/imp313_skips.txt`). Windows-only behaviour (device names, O_BINARY, junctions) cannot be exercised on Linux; device-name and trailing-dot rules were exercised as text only.
5. **Two runs died silently without a summary** and were restarted in slices: (a) the first combined fail-before run on (a) stopped at about 77% with rc=1 and no summary (`raw/fb_a.txt`); I re-ran it per file (`raw/fba_*.txt`). (b) the full mutant run (`raw/mutants_full.txt`) ended after 55 rows with no summary line and no leftover process; the slice script showed the same silent end after 3 to 6 rows in two slices. I could not find the cause (no OOM line seen in dmesg tail; other users' processes were running on the machine). I covered all 167 rows by slicing (every row has one result line; rows 112/113/114 and 109-114 were re-run separately). Not claimed explained.
6. `tests/test_s1_foundation.py` is also changed in the diff (not in the brief's list); it passes on head, (a) and (b) (37 passed each).

## (1) Focused tests
| run | command scope | result |
|---|---|---|
| py3.13 | tests/test_pathguard*.py + tests/test_changelog_claims.py | 358 passed, rc=0 (`raw/path313.txt`) |
| py3.12 | same | 358 passed, rc=0 (`raw/path312.txt`) |
| py3.13 | 41 other files importing k1b/audit/secrets_file/cli/hashing/bundle/replay (list in `raw/imp313.txt` args; test_k1b_*, test_k5_*, test_p4*, test_s2_audit, test_cuj, etc.) | 1189 passed, 16 skipped, rc=0, 84 s |
| py3.12 | same | 1189 passed, 16 skipped, rc=0, 90 s |

## (2) Mutant table `tests/pathguard_mutants.py`
167 rows, ALL run (no sampling needed). Verdicts (`raw/mutants_merged.txt`, from `mutants_full.txt` + `mutants_sl_*.txt`): KILLED 147, CRASH 15 (counted good), ERROR 2 (the two BAD rows in item 1). Survivors: 0. 165 good of 167. The table covers the changed sites (pathguard.py, atomic.py, secrets_file.py, hashing.py, signer, local_dir, bundle, score, replay, causelist, fake, judge, config, vault); `tests/stage_mutants.py` was not run (not touched by the diff).

## (3) Fail-before
Copied this head's new and changed tests (pathguard tests, fixtures, pathguard_mutants.py, test_changelog_claims.py, test_k1b_cli.py, test_k1b_replay.py, test_s1_foundation.py) onto:
- (a) origin/main src + head pathguard.py. Per file (`raw/fba_*.txt`): test_pathguard 15 failed/34 passed; batch3 44 f/55 p; batch4 19 f/13 p; callers 2 f/3 p; sites 19 f/16 p; tripwire 2 f/79 p; changelog_claims 20 f/37 p; k1b_cli 1 f/20 p; k1b_replay 49 p; s1_foundation 37 p. Total 122 failed among the 379 test ids of the 8 files in `raw/fb_a_perid.txt` (head: 379 passed, `raw/head_perid.txt`). First failing line is in each file (`--tb=line`), typical: `tests/test_pathguard.py:460: TypeError: atomic_write() takes 2 positional arguments but 3 were given`; `test_pathguard.py:54: AssertionError: R2 not refused ('../x.txt'): TypeError`; test_k1b_cli: `assert 'TypeError' == 'OSError'`.
- (b) pure origin/main src (`raw/fbb_*.txt`): 7 of the 10 files fail at collection (`ImportError: cannot import name 'pathguard' from 'hadavin_sdk'`): test_pathguard, batch3, batch4, sites, tripwire, changelog_claims (errors), so none of their tests run. callers 2 failed/3 passed; k1b_cli 1 failed/20 passed; k1b_replay 49 passed; s1_foundation 37 passed.
- `test_pin_*`: 85 ids on head; **all 85 PASS on (a)** (they pin kept behaviour; the baseline already has pathguard.py). On (b): 83 are in files that cannot be collected (not runnable); the 2 in test_pathguard_callers run and PASS (`test_pin_a_run_folder_that_is_a_link_out_of_the_outputs_folder_is_refused`, `test_pin_a_case_file_that_is_a_link_out_of_the_outputs_folder_is_refused`).
- `test_control_*`: 9 ids on head; **all 9 PASS on (a)**. On (b): 8 not runnable (collection error), `test_control_a_clean_outputs_folder_still_scores` PASSES.
- Changed tests that also pass on (b) / (a) without failing: all of test_k1b_replay.py (49) and test_s1_foundation.py (37) pass on both baselines (no fail-before evidence for them). test_k1b_cli has 1 test failing on both baselines.
- Failing on (a) means: the fail-before set is the 122 failures above; per-id list in `raw/fb_a_perid.txt`.

## (4) Suppression markers (added lines, `git diff origin/main...abb3e90a`)
noqa 0, type: ignore 0, fmt: skip 0, pragma: no cover 0, NOSONAR 0, nosec 0. Removed lines in the diff: fmt: skip 3, NOSONAR 5, others 0. NOSONAR lines on origin/main: 5; on head: 0. (`raw/suppressions.txt`)

## (5) Lint
ruff 0.17.1 `check` on the 27 changed .py files: All checks passed. `ruff format --check`: 27 files already formatted. `bandit -ll -q` on changed src files: no issues reported, rc=0 (only 2 comment-parse warnings about "SafeLoader"/"subclass"). `raw/lint.txt`.

## (6) Hostile inputs (`raw/hostile.txt`, 33 inputs x 9 targets; links built in a temp base; `raw/hostile_longname.txt`)
Targets: pathguard.component/join/inside/operator_file, k1b.atomic_write, hashing.hash_files, secrets_file `_fetch`, LocalDirSink `_object`, score.load_answers.
- `..` segments: refused by component, join, atomic_write, local_dir._object, hash_files, secrets `_fetch` (escape) ; `inside` accepts `sub/../real.txt` (resolves inside); operator_file accepts any path by design (operator-typed). hash_files accepts `sub/../real.txt` (canonicalised, inside).
- Absolute names: refused by component/join/atomic_write/hash_files/_fetch/_object; operator_file and load_answers accept an absolute path (operator-typed, by design).
- Link in base pointing outside: refused by join, inside, atomic_write, hash_files, `_fetch`; ACCEPTED by `component` (text only), `local_dir._object` (key `link_out.txt` returned a path; it is not read/written in this call), operator_file and load_answers (operator-typed; follows the link).
- Link pointing inside: accepted by join, inside, hash_files; `_fetch` refused for mode (0644 file), not for the link; atomic_write refused the link name.
- NUL, control char, newline, DEL, U+202E, U+200B: refused everywhere (R4) with no echo, except hash_files/_fetch which refuse a NUL/backslash by their own earlier checks.
- Trailing dot/space, devices CON, con.txt, COM1, NUL, LPT-superscript-1: refused by component, join, atomic_write, _object (R6/R7); accepted by inside, operator_file, load_answers (operator-typed; no name rules there by design); hash_files and _fetch refuse only because the file does not exist ("not a file: X" / "not found").
- 5,000-byte name: refused by every target (R5), no data echoed. 256-byte: refused except raw `OSError` from operator_file (item 2), `inside` accepted. 255-byte: accepted by component/join/inside/operator_file/_object; atomic_write refuses it (temp-name limit R5).
- Colon in an operator-typed answers file name (`a:b.json`): **ACCEPTED** by `score.load_answers` (guard passed; stopped later at "needs a non-empty cases object" because the test file is `{"cases": {}}`); refused by component/join/atomic_write/_object (R3); accepted by operator_file/inside.
- `vault:token` mounted secret name: accepted by the guard in `_fetch` path (`inside`); in this run refused only with "not found" (file absent); component/join refuse it (R3). `tests/test_pathguard_batch4.py::test_pin_secrets_file_reads_a_secret_name_the_operator_chose` passes on head.
- Error text printing a path derived from data: PathRefused texts from component/join/atomic_write/_object/inside never print the value or path (leak column "none"). Prints given names/paths: hash_files and `_fetch` (see item 3); raw OSError (item 2) prints the operator path.

## (7) Line count
`wc -l src/hadavin_sdk/pathguard.py` = 245.

Files: `raw/` holds every log named above. Nothing committed; no handover file other than this folder written.

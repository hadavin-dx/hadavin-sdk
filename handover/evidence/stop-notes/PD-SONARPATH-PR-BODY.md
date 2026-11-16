## One place that decides whether a file name or folder is safe (ORDER 260)

Head: see the last commit on `wip/cloud-sonar-path` (branch `core/sonar-path-traversal`, from main a8b4d8e8).

### What changed, in plain words

Before, three separate checks kept file names inside a folder (`config.confined`, the cause-list check, `signer.key_path`), and most other file operations in the scoring and replay code had no check. A rule added to one was missing from the others. Now one module, `src/hadavin_sdk/pathguard.py` (standard library only), holds the rules R1 to R11, and the three old checks call it. `atomic_write` now takes the folder and the file name separately: `atomic_write(base, name, text)`. The NOSONAR comments (score.py three, cli.py two) are removed; no suppression was added.

Rules (each has one test and one mutant): R1 empty or dot name, R2 separator, R3 colon, R4 control character, R5 length (255 UTF-8 bytes per name, 4096 characters per path), R6 trailing dot or space, R7 Windows device name, R8 the path escapes its folder, R9 absolute or drive-relative names (refused by R2 and R3), R10 cannot be resolved, R11 wrong type (file where a folder is needed, or the reverse). The name rules apply on every operating system, so a file made here also opens on Windows.

Threat model: the attacker is typed or data-derived TEXT. A second local process that changes the folder while we run is not claimed to be closed. Hard links and mount points are out of scope.

### Behaviour changes (also in CHANGELOG)

- `atomic_write(base, name, text)` replaces `atomic_write(path, text)`. The temp file is `.<name>.<16 random hex>.tmp`, opened exclusively, and removed on any exception including Ctrl-C. A file name over 233 bytes is refused (the temp name adds 22 bytes).
- `score` and `replay` now refuse a run folder or case file that is a link leading out of the outputs folder.
- A NUL character in a typed folder is a refusal, not a crash.
- `pathguard.operator_dir(..., must_exist=False)` is an addition to the design, used so `replay --out` can name a folder that does not exist yet.

### Rung table (reuse before writing)

| Candidate | Verdict | Reason |
|---|---|---|
| `Path.is_relative_to` (standard library) | USED | the containment test |
| `config.confined`, the `signer` create pattern | EXTENDED | now call pathguard; wording they pin ("escapes", "outside") kept |
| `ntpath.isreserved` | KEEP-CODE (inline list) | exists only from Python 3.13; the project floor is 3.12 |
| werkzeug `safe_join` | REJECT | only present through moto, a test dependency, not a runtime one |
| pathvalidate | REJECT | not installed; a new runtime dependency for a small list |

### Call sites and where each path comes from

Origins: operator-typed (OT), data-derived (DD), fixed (F).

| Place | Origin | Now |
|---|---|---|
| cli.py `score_cmd` (outputs folder, report folder, report file) | OT folder, F names | `operator_dir`, `join`, `atomic_write(report_dir, name, ...)` |
| k1b/replay.py `_replay`, `outputs_files`, `_write_json`, `_mark_failed` | OT `--out`, DD run and case names | `operator_dir(must_exist=False)`, `join`, `atomic_write(base, name, ...)` |
| k1b/score.py `load_answers`, `_recorded_digest`, `_read_json`, `_record`, `_check_layout`, `score` | OT folder or file, DD run and case names | `operator_file`, `operator_dir`, `join(must_exist=True, kind=...)` |
| k1b/bundle.py `_load_json`, `_text`, `load_bundle`, `load_bundles` | OT folder, DD names from the manifest and the listing | `operator_dir`, `component`, `join` |
| k1b/causelist.py | OT folder, DD file names | `operator_dir`, `join` inline (own `_inside` removed) |
| k1b/atomic.py | folder checked by caller, DD name | `join` for the final and the temp path |
| config.py `confined` | any (12 other callers: app, registry, evals, hashing, secrets_file, agent_loop, bundle) | delegates to `pathguard.inside`; same messages |
| audit/signer.py `key_path` | OT/config key folder, F name | delegates containment to `pathguard.inside`; order of its checks kept |
| config.py `golden_dir`, `inputs_dir` (`root / raw[key]`) | operator config | unchanged on purpose: absolute folders are allowed; their consumers use `confined` |
| signer.py `private_key_path`, key folder `mkdir` | operator config | unchanged on purpose: a demo or pilot key may live anywhere |
| audit/local_dir.py, runtime/agent_loop.py, registry.py, evals.py, store/*, tools.py, replay_records.py, actions/secrets_* file reads and writes | operator config or F (for example `root / "index.jsonl"`, `root / "qualified.jsonl"`, a configured JWT path) | not touched: outside the scoring, replay and CLI code this order covers, and no data-derived name reaches them. Listed so the next audit does not re-discover them. |

Tripwire: `tests/test_pathguard_tripwire.py` fails if code in `k1b/*.py` or `cli.py` calls a file operation on a path that is not a plain name whose latest earlier assignment in the same function is a `pathguard.*` call. There is no comment switch. On the old main files it reports 23 violations. It follows one function only.

### Evidence (final head; commands run through the heavy-job queue)

| Gate | Exit code | Result |
|---|---|---|
| `pytest -m "not live and not perf"` (one full run, head b096ad48) | 0 | 10231 passed, 457 skipped, 28 deselected |
| `ruff check` and `ruff format --check` on src tests demos tools | 0 | all checks passed, 327 files formatted |
| `bandit -q -r src demos tools -ll` | 0 | no medium or high finding (pre-existing warning about a nosec in tools.py, not mine) |
| `python tools/scan_repo.py` | 0 | clean |
| `python tests/pathguard_mutants.py` | 0 | 22 of 22 killed, `problems: []` |
| `python tests/stage_mutants.py` | 0 | 37 of 37 killed, `problems: []` |
| gitleaks on `origin/main..HEAD` | 0 | no leaks found |

Honest note: after the full pytest run I changed one test helper (`_must_refuse` in `tests/test_pathguard.py`) because the first mutant run showed one mutant killed for the wrong reason (a chained error line). I re-ran the 3 new test files (60 passed), ruff format, the new mutants and stage mutants on that head; I did NOT re-run the full suite. No source file changed in that commit.

### Fail-before (new tests run on origin/main a8b4d8e8)

The new test files and the changed `test_k1b_cli.py` were copied into a detached worktree of origin/main. Because `test_pathguard.py` imports `pathguard`, a stub module with the names and no logic was added there so the files could load (otherwise: one collection error, ImportError). Result: 47 failed, 34 passed.

| File | Failed on old code | Passed on old code | Meaning |
|---|---|---|---|
| test_pathguard.py (47) | 44 | 3 | 3 are regression tests (confined wording, confined gains no Windows rules, key_path wording and order). Of the 44: the checks of the old behaviour that fail for a behavioural reason are the NUL in confined, the NUL in the cause-list folder and the no-suppression-comment guard; 13 atomic_write tests fail because the old signature takes 2 arguments (TypeError: a signature failure, not a proof of behaviour); the rest test `pathguard` itself and fail only because it is a stub there. They are proven by the mutants instead (22 of 22 killed). |
| test_pathguard_callers.py (5) | 0 | 5 | All 5 pass on old code: they are regression tests (the old code already refused these cases by other means). They are not fail-before evidence. |
| test_pathguard_tripwire.py (3) | 1 | 2 | The real-code test fails on old files (23 violations). The seeded bad and good fixture tests pass on both: they test the scanner, not the code. |
| test_k1b_cli.py | 1 | 20 | the updated stub fails on the old signature |

So the fail-before count that shows a real behaviour difference is small (3 in test_pathguard.py plus the tripwire test); the rest of the proof for pathguard itself is the mutants.

### Sonar, honestly

I could not run SonarQube or SonarCloud here. The code now has no NOSONAR comment and passes every path through one helper. Whether Sonar recognises `pathguard` as a sanitiser is unknown and probably not: Sonar usually recognises only its own list of known functions. For a folder the operator types on the command line, no code can "sanitise" it, because the operator already owns the folder; those findings may remain. The lead should read the SonarQube result after this lands. This PR does not claim Sonar is satisfied.

Not in scope: marking a SonarQube finding accepted (owner click).

### Not run

- SonarQube / SonarCloud scan (no access from here).
- Windows: junctions, `\\?\` long paths and 8.3 short names were not tested (this machine is Linux). The name rules (R1 to R7) are tested on Linux for every OS.
- A second process changing the folder during a run (outside the threat model).
- Full pytest was not repeated after the one test-helper commit (see the note above).
- No EGM review and no evidence-runner step was run by the builder; the lead runs those.

### CI step for the lead

The new mutant check is `python tests/pathguard_mutants.py` (exit 0 means all 22 killed). Adding it as a CI step next to `tests/stage_mutants.py` is the lead's decision; the required checks are only `check` and `security`.

🤖 Generated with [Claude Code](https://claude.ai/code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac

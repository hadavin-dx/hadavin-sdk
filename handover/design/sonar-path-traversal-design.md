# Design: one path-containment choke point (ORDER 260; SonarCloud path traversal at k1b/atomic.py L16 and k1b/score.py L167)

Version 2, after EGM review round 1 (reports in `handover/reviews/sonar-path/`). Security path: no round cap; one fresh confirming round must find nothing real before READY. EGM draft step skipped: the lead's order fixes the goal; this note is the plan.
Base commit for the build: `origin/main` at a8b4d8e8 or later (the mutation runner `tools/mutation_runner.py` and `tests/*_mutants.py` exist there; they are NOT on the `core/cloud-handover` checkout).

## 1. What is wrong, in plain words
Two functions touch a file whose name came from the command line: `atomic_write` (writes, then renames) and `score._read_json` (reads). SonarCloud calls this path traversal. Looking wider, the core has three separate private containment checks that each answer a slightly different question and share no code: `config.confined(base, relative)` (config.py:427; message "path escapes its folder"), `k1b/causelist._inside` (strict resolve, must be a file) and `audit/signer.key_path` (key folder; symlink refused; message contains "outside"). Class: containment checks copied per caller, so a rule added to one is missing from the others; and most file operations in `k1b/` have no check at all.

## 2. Origins: who controls each path (one word, one meaning)
- **operator-typed**: a folder or file the person types on the command line or in the config (`--outputs`, `--out`, `--cases`, `--answers`, `--config`). The operator already owns that folder. Nothing can "contain" it: there is no outer base. We validate its shape only (`operator_dir`, `operator_file`).
- **data-derived**: a name that comes from data: case ids, ordinals, file names found in a folder, names inside a bundle or a model reply. This is the real traversal risk. Every one goes through `component` or `join`.
- **fixed**: a constant in our code. No check needed; listed in the table so the reader can see it was looked at.
Threat model (stated plainly): the attacker is operator-typed or data-derived TEXT. It is not a second local process that changes the operator's folder while we run. A swap between the check and the use is therefore not claimed to be closed (see 6).

## 3. The helper: `src/hadavin_sdk/pathguard.py` (stdlib only; no vendor import)
Errors: `PathRefused(ConfigError)` (so `except ValueError` and `except ConfigError` callers keep working; `ConfigError` is a `ValueError`, errors.py:4). The message names the RULE and the ARGUMENT NAME, never the raw value (control characters would print). Exceptions: `config.confined` keeps its existing text "path escapes its folder: ..." and `key_path` keeps "outside" because tests pin them (see 3.4).

### 3.1 Public functions
| Name | Input | Does | Returns |
|---|---|---|---|
| `component(name, *, what)` | one data-derived name | refuse unless one safe path component (rules in 3.2) | the same string, never changed |
| `join(base, *names, must_exist=False, kind=None)` | an operator folder and relative names | each name goes through `component`; join; `resolve` (strict if `must_exist`); result must be inside the resolved base; `kind` is "file" or "dir" | the resolved `Path`; no names returns the resolved base (so `""` and `"."` are not accepted as names, they are refused by `component`) |
| `inside(base, path, *, must_exist=False, kind=None)` | a path that is already joined (absolute or relative) | resolve; must be inside the resolved base; symlink or junction leaving the base is refused because resolve follows it | the resolved `Path` |
| `operator_dir(path)` / `operator_file(path)` | an operator-typed folder or file | refuse NUL and control characters; resolve strict; must exist and be that type; NO base | the resolved `Path` |
Callers use ONLY the returned path afterwards, never the original text.

### 3.2 Rule table (each rule has an exact test, an error text and one mutant)
| Rule | Applies to | Exact test | Text |
|---|---|---|---|
| R1 empty or dot | component | name is "" or "." or ".." | "{what}: not a plain name" |
| R2 separator | component | contains "/" or "\\" (both, on every OS) | "{what}: contains a separator" |
| R3 colon | component | contains ":" (drive, stream, `NUL:` forms; refused on every OS) | "{what}: contains a colon" |
| R4 control characters | component, operator_dir/file | any of U+0000-U+001F, U+007F, U+0080-U+009F, U+202A-U+202E, U+2066-U+2069 | "{what}: contains a control character" |
| R5 length | component; whole path | component over 255 UTF-8 bytes; whole path over 4096 characters | "{what}: too long" |
| R6 trailing dot or space | every component | last character is "." or " " | "{what}: ends with a dot or space" |
| R7 device name | every component | stem (text before the first ".") ignoring case is CON PRN AUX NUL COM0-COM9 LPT0-LPT9 CONIN$ CONOUT$ CLOCK$ or a superscript-digit COM/LPT form; with or without extension | "{what}: reserved device name" |
| R8 escape | join, inside | resolved result is not inside the resolved base (`Path.is_relative_to`) | "{what}: path escapes its folder" |
| R9 absolute names | join | a name is absolute, drive-relative (`C:x`), rooted (`\x`), UNC or `\\?\` (all already refused by R2/R3, tested on their own) | as R2/R3 |
| R10 resolve failure | all | `OSError`, `RuntimeError` (symlink loop on 3.12) or `ValueError` (NUL) from resolve | "{what}: cannot be resolved" |
| R11 wrong type | join/inside/operator_* with kind | `is_file`/`is_dir` false | "{what}: not a file" / "not a folder" |
Refuse, never repair: no rule changes the text. Case-insensitive disks, Unicode normal forms (NFC/NFD) and 8.3 short names can only cause a refusal or a false "inside" check on a disk where two spellings are one folder; stated, not repaired. Hard links and mount points are out of scope (a hard link inside the base to a file outside resolves inside; a write replaces the link, a read follows it); stated in the docstring.
Device and trailing-dot rules apply on EVERY operating system: our output files must open on Windows too. They apply only to data-derived components and to the final name `atomic_write` writes, not to every old `config.confined` call (see 3.4).

### 3.3 What about Sonar (honest claim)
Sonar's tracker follows a value through functions; a user function named `join` that raises and otherwise returns a path is most likely NOT a recognised sanitiser, and an operator-typed folder cannot be sanitised at all. So: the builder does NOT run Sonar (none locally) and the PR claims only what is true: data-derived names are now contained and checked; operator-typed paths are validated for shape; NOSONAR comments are removed as the order says (score.py 101, 158, 160; cli.py 264, 265) and any other made unnecessary; the lead reads the SonarQube result after the PR runs; if a finding remains on an operator-typed path, the lead marks it accepted in SonarQube (never a code suppression). The sentence "SonarCloud is fixed" must not appear in the PR body.

### 3.4 Delegation of the old copies (no behaviour change except named refusals)
- `config.confined(base, relative)` calls `pathguard.inside(base, Path(base)/relative)` and keeps its text "path escapes its folder: {relative}" for R8; a NUL or other resolve failure now raises `ConfigError` instead of a bare `ValueError`. It does NOT gain R6/R7 (12 other callers: app.py:274, registry.py:76/85/96/345, evals.py:43/60/106, hashing.py:23, actions/secrets_file.py:36, runtime/agent_loop.py:138, k1b/bundle.py:211; origin operator config or data; the whole suite is run and any fixture that trips is listed). `bundle.py:211` must use the returned path (it discards it and reads `path / rel`).
- `causelist._inside` calls `pathguard.join(..., must_exist=True, kind="file")`; it is called with constants only, so the change is a tidy-up, said so.
- `audit/signer.key_path` keeps its own order: expanduser, `is_symlink` refusal of the final name, mkdir 0700, resolve of the PARENT only (the key may not exist yet), "outside" text; it calls `pathguard.inside` for the parent containment. Callers pass absolute paths (test_audit_chain.py:201-213), which `inside` accepts.
- Part 5 (`wip/cloud-pd-reset`) also changes `config.confined` (NUL). This branch is from main; whichever merges second rebases and keeps the `ConfigError` result.

## 4. Call-site table (builder completes the origin column for every line it finds)
| Site | Old | New form | Origin |
|---|---|---|---|
| cli.py:252-266 report folder and `atomic_write(report_dir / "score-report.md")` | cwd-relative join | `report_dir = pathguard.join(operator_dir(args.outputs), REPORT_DIR)`; `atomic_write(report_dir, "score-report.md", text)` | operator-typed folder + fixed names |
| k1b/atomic.py `atomic_write(path, text)` | any path | `atomic_write(base, name, text)`; `base` a folder already validated by the caller; `name` through `component`; no default for `base` (positional, so omission is a TypeError) | caller decides |
| k1b/replay.py:75 `_write_json`, 222, 256, 261, 262, 276 | `out / ...` | `_write_json(out, name, obj)`; case-id names through `component` (case ids are data-derived) | operator out folder + data-derived case ids |
| k1b/score.py `_read_json(path, what)`, `_record(path, case_id, ordinal)`, callers 242, 273, 228 | `rdir / "run.json"` | `_read_json(base, *names, what=...)` via `join(..., must_exist=True, kind="file")`; `_record` takes `base` | operator folder + data-derived case ids and ordinals |
| score.py `_recorded_digest`, `load_answers` (operator-typed `--answers`) | direct open | `operator_file(path)`; keeps ConfigError text "answers file is missing or not valid JSON" | operator-typed file |
| replay.py:78-82, 125, 133, 145; score.py:193-208, 226; bundle.py:112, 137, 190-214, 335, 344; causelist.py:39, 78; cli.py:88, 132-133 | direct `exists/iterdir/glob/rglob/mkdir/is_dir/read_bytes` | the root through `operator_dir`; every name taken from a listing through `component`; every join through `pathguard.join` | root operator-typed; names data-derived |
| config.py:446-448 `golden_dir`, `inputs_dir`; audit/signer.py:105 `private_key_path` | joined from config | IN scope: through `inside`/`key_path` if the builder finds the config root is available; otherwise listed 'origin operator config, unchanged' with the reason | operator config |
The builder runs the grep in section 7 and adds every other hit it finds to this table; a hit with no row blocks the PR.

## 5. `atomic_write(base, name, text)`: exact behaviour
- Final path = `join(base, name)` with R6/R7 applied to `name`; the temp file is in the same folder, named `.<name>.<secrets.token_hex(8)>.tmp` (suffix `.tmp` kept so `score._check_layout` (score.py:204-208), tests/test_k1b_score.py:206, tests/test_k1b_replay.py:113 and tests/test_k1b_bundle.py:214 still see a temp file as a stray file).
- Open the temp with `os.open(..., O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW (where the OS has it), 0o666 minus umask)`; wrap with `os.fdopen(fd, "w", encoding="utf-8", errors="backslashreplace", newline="\n")` (same text handling as before); flush, fsync; `os.replace(tmp, final)`.
- On ANY exception (`BaseException`) the temp is unlinked (as `audit/signer._create` does) and the error re-raised; docstring says a hard kill can still leave a `.tmp`.
- Docstring states: `O_NOFOLLOW` protects only the last component and does not exist on Windows; `os.replace` resolves by name; a concurrent local writer in the folder is outside the threat model (section 2).

## 6. Tests (each must fail on old code or be labelled)
Proof rule: behaviour tests call code that exists on main (`config.confined`, `atomic_write`, `key_path`, causelist, score, the CLI) so they fail for the behavioural reason, not for a missing import. `pathguard`-direct unit tests are proven by mutants, not by "fails on main". Labels: symlink-out and `..` cases already pass on old `config.confined` = REGRESSION tests (said so); NUL (bare ValueError today), `con.json`, trailing dot, deterministic temp name, `atomic_write` without `base`, absolute `name`, case id with a separator, case id "con" = FAIL-BEFORE tests (measured on old src with the new test files copied in, as the Q8c evidence does).
List: every rule R1-R11 one test each; symlink out (try/except OSError then skip); symlink loop (R10); junction (Windows only, skip elsewhere); a normal path inside the base still works (nested, spaces, unicode, Windows and Linux spellings); temp unlinked after an exception in write and in replace; temp name not chosen by the caller; `atomic_write` keeps utf-8/backslashreplace/newline output; filesystem-effect property test (fixed seed 20261112, 300 examples): build a tree in `tmp_path` with a sibling "outside" folder, run join/atomic_write with random segments, assert the file listing and hashes of the outside folder never change and no file appears outside the base (not an oracle built from the same `is_relative_to` logic); `tests/test_k1b_cli.py:204-207` stub `boom(path, text)` updated to the new signature; builder lists every other test that calls `atomic_write`/`_read_json` positionally and fixes it; whole suite run, any fixture hitting R6/R7 listed.
Mutants: new `tests/pathguard_mutants.py` in the form of `tests/stage_mutants.py` (copy that file's contract: a list of (id, file, old text, new text, pinned test, expected failure text); the runner exit code 0 only if every mutant is killed by its named test and `problems: []`): one mutant per rule R1-R11, one for each of `O_EXCL`, the unlink, the `component` call on case ids and the `.tmp` suffix. The CI step text is written by the builder into the PR body; adding the step is the lead's decision (required checks are only `check` and `security`).
Tripwire test (AST): banned calls `open`, `.read_bytes`, `.read_text`, `.write_bytes`, `.write_text`, `.mkdir`, `.iterdir`, `.glob`, `.rglob`, `os.replace`, `.unlink`, `shutil.*` in the named files `k1b/*.py` and `cli.py`, unless the path argument is a variable assigned from a `pathguard.*` call in the same function (the only allow rule; no comment suppression). Failure message names file, line and call. A seeded bad fixture (a tiny module under `tests/fixtures/`) must trip it, and a seeded good one must pass. Limits stated in the test docstring: it follows one function only, not values passed between functions.
Guard test: no `NOSONAR` remains in the touched files; no new suppression anywhere.

## 7. Builder steps (in order)
1. Branch `core/sonar-path-traversal` from main; grep `open(`, `Path(`, `.read_bytes`, `.read_text`, `.write_`, `os.replace`, `shutil`, `mkdir`, `unlink`, `glob`, `iterdir`, `rglob`, `is_file`, `is_dir`, `exists` under `src/`; complete the section 4 table with origin per line (operator-typed / data-derived / fixed) and put the table in the PR body.
2. Write `pathguard.py`, tests and mutants; delegate the three old copies; change the call sites; remove NOSONAR.
3. Gates at the final head, once: full suite, `ruff check`/`format --check`, `bandit -ll`, new mutants (all killed), `stage_mutants.py`, gitleaks. Heavy jobs only through `/home/user/build/heavy.sh` (queue priority 2).
4. Push to `wip/cloud-sonar-path`. The lead opens the draft PR on branch `core/sonar-path-traversal`.
PR body: rung table (below), path-origin table, the honest Sonar paragraph (3.3), the sentence about what was not run (Sonar, Windows junctions and `\\?\`), the line "Not in scope: marking a SonarQube finding accepted (owner click)".

## 8. Rung table (tool ladder; verified facts dated 2026-11-12 where the builder checks, else UNVERIFIED)
| Component | Need | Rung tried | Evidence | Only our code gives | Verdict |
|---|---|---|---|---|---|
| containment join/inside | refuse escape from a base | 1 reuse `config.confined` | exists, one rule, no names/NUL/Windows handling | uniform refusal text and type, `component` | EXTEND (move into one module, delegate) |
| same | | 2 `os.path.commonpath` / `Path.is_relative_to` (stdlib) | used inside our helper | | USE |
| same | | 2 `werkzeug.security.safe_join` | UNVERIFIED: builder checks pyproject; likely not a dependency | | REJECT unless already a dependency (a new dependency for 10 lines) |
| device names, reserved names | Windows names | 2 `ntpath.isreserved` | Python 3.13 only; project floor is 3.12 | inline list | KEEP-CODE |
| same | | 2/4 `pathvalidate` | UNVERIFIED; new dependency | | REJECT (no-single-dependency, size) |
| atomic write | safe temp and rename | 1 reuse `signer._create` pattern | exists | | EXTEND |
Own code only for what the standard library cannot do: Windows names, control-character set, one refusal type.

## 9. Not in scope (stated)
SonarQube status changes (owner click). Real Windows junction, `\\?\` and 8.3 behaviour cannot run on this Linux box (impossible now); the string rules run on every OS; a Windows CI job, if one exists, is the check. Race between check and use (outside the stated threat model). Hard links and mount points.

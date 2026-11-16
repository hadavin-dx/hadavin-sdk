Status: resolved

# Goldfish Annotated Review Report, SONAR-PATH (pathguard.py and k1b path confinement, ORDER 260), round 4 resolve (report r4b)

(`goldfish_review_report-r4.md` already exists and is the round 3 resolve; this file is the round 4 resolve.)

**Target:** `/home/user/build/snap/sonarpath-abb3e90a/DIFF.patch` (full), head `abb3e90acafe9915c911636251e5dc003a00842c`, security path (no round cap).
**Inputs:** `sonarpath-abb3e90a-design-r4.md` (0 Blocker, 3 Major, 7 Nit), `sonarpath-abb3e90a-codebase-r4.md` (0 Blocker, 4 Major, 8 Nit), and the evidence runner's `handover/evidence/sonar-path/abb3e90a/RESULTS.md` (an addendum that found one real bug). The reviewers read code only; the runner ran the focused tests and the mutant table.
**Method:** every finding checked against what could be read; none contested. 7 Major + 15 Nit + 1 runner bug merge into 9 issues. Settled from r3 stays settled (single choke point, no NOSONAR, no colon rule for operator-typed folder names, EQUIVALENT list exists and is tested for text).
**No Blocker. One real bug (issue 1) and the label, pattern and size work remain.** No claim about SonarCloud: the gate on the real draft PR is the only test.

## Handoff counts

- PROPOSE FIX accepted: 9 issues (all findings, nits included). CONTEST 0. ESCALATE 0. DECLINE 0.
- Remaining unaddressed: 0. **Round 5 is REQUIRED** (security path, no cap; batch 5 changes code).

## Decisions made here

1. **One pattern for every flagged read (design M1).** The lead's orders of 03:36Z, 03:45Z and 04:02Z are binding: every S8707 site ends in exactly the `pathguard.join` pattern (`pathguard.join(path.parent, path.name, ..., must_exist=True, kind="file")`), because probe PR #100 showed that pattern clears the two sites on main and nothing else is proven. `operator_file`/`operator_dir` remain only where there is no flagged read after them (they check text and return). So `score.load_answers`, `hashing.hash_files` and `secrets_file._fetch` all use the join pattern, once each (no doubled guard). This reverses the r3 choice that operator-typed file names use `inside` only; the lead's 04:02Z order says to state the refusal change, so the cost is accepted: the rules R3 (colon), R6, R7 and R12 now apply to an answers file name and to a mounted secret name. Each changed refusal goes into the CHANGELOG and the PR text with a test (a colon in an answers name; `vault:token`, `con` and `key.` as secret names). The `test_pin_secrets_file_reads_a_secret_name_the_operator_chose` pin becomes a refusal test with the new label. If the builder finds a name the repository or its demos really use that the join pattern refuses, it reports that name to the lead and does not add a bypass.
2. **Label definition (codebase M2, M3).** The measured baseline is **(a) origin/main src plus head pathguard.py** (as the lead accepted on 04:45Z), with **(b) pure origin/main** where collection allows. A `test_pin_*` passes on (a); a `test_control_*` passes on (a) and (b); every other test fails on (a). The header of each test file states this definition and the measured counts (runner: 122 of 379 ids fail on (a); 85 pins and 9 controls pass there). The PR text never says "fails on old main".

## Prioritized findings

### Issue 1, Major (real bug, security class ERROR-LEAK at the choke point): OSError escapes (runner item 2)
`operator_dir`, `operator_file` and `LocalDirSink(root)` raise a raw `OSError` (Errno 36, "File name too long") carrying the operator-typed path in its text when `must_exist=False` and a component is 256 bytes or more (`must_exist=True` gives a clean `PathRefused`). Reproduces in `raw/hostile_longname.txt`.
PROPOSE FIX: name the class "an error from the operating system while resolving a typed path escapes unmapped". Fix at the one place where `pathguard` calls `resolve`/`stat`/`exists`/`is_*` (the shared tail `_within` and the `must_exist` checks): wrap every OS call in one `_os(...)` step that turns `OSError` (every errno) and `RuntimeError` (symlink loop) into `PathRefused` with a fixed text, no path and no errno text, chained with `from None`. Sweep siblings: every `Path(...).resolve/exists/is_file/is_dir/stat/lstat/open/mkdir/unlink/readlink` call in `src/hadavin_sdk` that runs on an operator-typed or config path (`cli.py`, `config.py`, `k1b/*`, `audit/*`, `actions/*`): list each (file:line) in the PR notes and route it through the same step or show why it is not reachable by typed text. Tests: property/fuzz test over name lengths 250 to 5,000 bytes (all four of `operator_dir`, `operator_file`, `LocalDirSink`, `join`, with `must_exist` both values, combining long components with NUL-free text, `..`, links and loops) asserting `PathRefused` only, text without the path, no `OSError` escapes; a mutant row that removes the wrap. Fail-before: the long-name test fails on abb3e90a (raw `OSError`).

### Issue 2, Major, class PATTERN (design M1; lead orders): not every S8707 site uses the join pattern
See decision 1. Sites: `score.py:104` (`load_answers`: `operator_file` then `read_bytes`), `hashing.py:30-32`, `secrets_file.py:37-41` (`confined`+`inside`), also the named siblings `guard/judge.py:103`, `actions/secrets_vault.py:180`, `signer.py:109,220,234`. The reviewer asks for one pattern; the lead's order names it.
PROPOSE FIX: convert each flagged read to the join pattern, one guard per site, remove the doubled second guard (`hashing.py:32`, `secrets_file.py:41`), record per site in a table (CHANGELOG or PR notes): the line, the pattern used, and why if it differs (only when the base/name form cannot be built). Sites that already match (`_recorded_digest`, `_read_json`, `causelist.py:42`, `cli.py:262`, `bundle.py:112,144,232`) stay. Tests per changed refusal (decision 1); mutant row for each removed doubled guard is replaced by one row that removes the remaining guard and must be killed.

### Issue 3, Major, class SIZE (design M2)
`pathguard.py` is 245 lines (273 before r3), not "as small as correctness allows"; the correctness/message split is missing.
PROPOSE FIX: remove each of these if a test that fails with it removed on a path that matters cannot be written, in this order: `operator_text` (only caller `signer.py:147-148`; `operator_dir`/`operator_file` with `must_exist=False` have the same shape), the duplicate `_check_text(str(base))` in `join` (`_within` already checks the joined text), `PathRefused.__reduce__` unless a pickling test needs it, the R12 Windows rule if no caller depends on it, `TEMP_EXTRA_BYTES`/`MAX_WRITE_NAME_BYTES` if the write-name limit can be one constant. Keep the 20-range table (R4: tested, mechanical). Target at most 220 lines; the PR text gives the split of lines into correctness, message wording and docstring. Add the rung statement (tool ladder: reused `config.confined` and `causelist._inside` ideas, no library gives one refusal type with Windows device rules and R8 containment) to the docstring and the PR rung table.

### Issue 4, Major, class AUDIT-DROP (design M3)
`audit/local_dir.py:131-137` `write_outcome` drops the audit record for ANY `PathRefused`, not only a bad event id; a refusal from the objects or index folder (for example a link out, R8) loses a record that main sent to the outbox, and the warning text names the id. CHANGELOG line 20 states the drop only for an id.
PROPOSE FIX: drop only when the refusal comes from the event-id join; every other refusal takes the existing outbox path with its own warning text; test both (bad id dropped and counted in `refused_events`; objects folder replaced by a link out takes the outbox path); CHANGELOG states exactly that. Also hoist the per-entry join recomputed at `local_dir.py:173-174` out of the loop (codebase N3).

### Issue 5, Major, class MUTANT-ROWS (codebase M1; runner item 1)
`tests/pathguard_mutants.py:1051` (`replay.py` ~322-325) and `:1116` (`signer.py` ~115-118) have an old text that no longer matches the reformatted source (runner: "SNIPPET NOT FOUND", counted BAD, so 165 of 167 are good).
PROPOSE FIX: correct both old texts; add a text-only test that every row's old text occurs exactly once in its target file at the head (fails the whole table on any miss); re-run the whole table at the final head (167 rows now, more after batch 5); every row `good` with no error.

### Issue 6, Major, class PIN-LABELS (codebase M2, M3)
`tests/test_pathguard_batch3.py:85-91` generates `test_pin_r4_range_NN` (docstring `:3-5` "evidence file"); `tests/test_pathguard_callers.py:59` and `:68` are labelled pin while the docstring (`:3-4`) says they fail on main and cites "the real run in the pull request body"; `:77` and `:91` carry no label.
PROPOSE FIX: apply decision 2 to every new and changed test file from the measured list (`raw/fb_*` files of the runner): relabel to pin/control/plain by the measured result on (a) and (b); correct both docstrings (replace "pull request body" by the measured counts); name tests in `test_pathguard_callers.py` for what they do. The measured list goes into the evidence and the PR notes as "origin/main src plus head pathguard.py". `tests/test_s1_foundation.py` changed in the diff without being listed: say why in the PR notes (37 tests pass on head and both baselines, so it is a pin set).

### Issue 7, Major, class TRIPWIRE-LIMITS (codebase M4; design nit 5)
`score.py:217` `out = pathguard.operator_dir(outputs_dir(out), what="outputs folder")` wraps a call that already guards and exists so the scan passes; its row (`pathguard_mutants.py:340`) removes both guards together. The scan accepts a name assigned from a pathguard call in the same function without checking that this name reaches the banned call; the validator check is file-level.
PROPOSE FIX: remove the outer guard (dead for correctness) and split the row so the remaining guard is shown to be needed; state the scan's limits in the tripwire docstring (file-level validators; assignment-by-name; what it cannot see); enforce that the name passed to the banned call is the guarded name where the scan can resolve it, else say so.

### Issue 8, Minor, class DIFF-NOISE / TRUTH (codebase N1, N2, N4, N8; design nits 3, 4, 6, 7; runner items 3, 6)
Stale citation `tests/test_pathguard_sites.py:5`; the R4 range count is not derived mechanically; `test_changelog_claims.py:188` asserts only that the old two-argument form raises; the diff removes `# fmt: skip` in `tests/test_k1b_cli.py` (two sites) and `tests/test_k1b_replay.py` (reflow churn unrelated to the path work); "never printed" in CHANGELOG line 9 is not fully true (`local_dir.py:123` prints `event.event_id` on an `OSError`; `bundle.py:200` prints the raw `path.name` for a `CASE_RE` failure; `hashing.hash_files` and `secrets_file._fetch` print the name the caller gave, as pinned); R4 refuses some legitimate operator folder names (U+200D, U+FE0F, U+00AD, tag characters: emoji sequences); `pathguard_mutants.py:1125` EQUIVALENT rows are not run, only text-checked.
PROPOSE FIX: fix the citation; one test derives the range count from `CONTROL_RANGES` and compares it with the CHANGELOG text; pin the exact exception type in the claims test; revert the `fmt: skip` reflow in the two test files (keep the diff to the path work; the markers on main stay where they are; the count against main stays 0 added); CHANGELOG says exactly which messages print which given text and that R4 refuses joiner/variation characters; run the four remaining EQUIVALENT mutations once in the evidence (records only) and keep the text test.

### Issue 9, Minor, class OPERATOR-FACTS (runner items 3-5)
Runner facts that need a place in the notes: a 255-byte name is accepted by `component`, `join`, `inside`, `operator_file` and refused by `atomic_write` (lower temp-name limit); `inside` accepts `sub/../real.txt` (resolves inside); links pointing inside the base are accepted by `join`, `inside`, `hash_files`; `component` accepts a link name (text only); `local_dir._object` returns a path for a link pointing outside without touching it.
PROPOSE FIX: add each as a claim test or a stated line in the CHANGELOG ("what is accepted") so the PR text does not overclaim; no behaviour change.

## ONE FIX BRIEF (single small builder, batch 5; code and tests only on `wip/cloud-sonar-path2`, then the code-only branch `core/k1b-path-confinement` is cut by the lead from origin/main)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, no Playwright, focused tests and focused rows only, each command under 8 minutes and resumable, at most 2 heavy processes); real fail-before runs in `git worktree` at **(a) origin/main src plus the head's pathguard.py** and **(b) pure origin/main**, raw lines; no suppressions and no NOSONAR; fake credentials built from parts; never commit under `handover/`; a suppression-marker count on added lines against `origin/main` in the report; checkpoint note every 30 min, stop at 60 min with a report. **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.**

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | ERROR-LEAK | issue 1: one `_os(...)` step at the choke point; sweep list | fuzz 250-5,000 bytes over four callables x must_exist; fixed text, no path | row removes the wrap | fails on abb3e90a (raw OSError) |
| B | PATTERN | issue 2: join pattern at every flagged read; one guard per site; per-site table | changed refusals (colon answers name, `vault:token`, `con`, `key.`) | one row per site | per-refusal tests fail on (a) |
| C | SIZE | issue 3: cut per list, at most 220 lines; rung statement | tests that fail with each kept piece removed | rows follow | n/a |
| D | AUDIT-DROP | issue 4: drop only for id refusal; hoist join | bad id dropped; objects-link takes outbox | row per branch | fails on abb3e90a |
| E | MUTANT-ROWS | issue 5: fix the two old texts; once-per-row text test | text test | all rows good | fails on a bad text |
| F | PIN-LABELS | issue 6: relabel from the measured list, fix docstrings | labelled set | none | raw lines at (a), (b) |
| G | TRIPWIRE | issue 7: remove outer guard at `score.py:217`; state limits | tripwire tests | split row | fails if guard removed |
| H | TRUTH / NOISE | issues 8, 9 | claim tests; range-count derivation | none | wrong claim fails |

Builder reports once when ALL of A-H are done: new head sha, the sweep list with file:line for issue 1, the per-site pattern table, raw fail-before lines for (a) and (b), suppression grep, pathguard.py line count, anything not done and why.

## Round 5 and evidence for the final head

- **Round 5 is required.** Fresh design and codebase reviewers on a new snapshot, plus ONE evidence runner on the final head; the reviewers and the runner count suppression markers on added lines and the runner reports pins versus real fail-before as "origin/main src plus head pathguard.py".
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13, the whole pathguard mutant table, hostile inputs including the long-name fuzz, suppression grep.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** `<repo> <final sha>` full pytest, the full pathguard mutant table and stage mutants, py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- **Then `PR READY: core/k1b-path-confinement <sha>`** (code-only commits, no handover files). The lead opens the draft PR; the SonarCloud gate on the real PR is the success test; no claim that any finding is cleared before that.
- Ledger rows SONARPATH-r4-1..7 exist; the caller adds rows for issues 1 and 9 (the real bug and the facts).

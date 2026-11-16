Status: resolved

# Goldfish Annotated Review Report, SONAR-PATH (pathguard.py and k1b path confinement, ORDER 260), round 3 resolve (report r4)

**Target:** `/home/user/build/snap/sonarpath-9602b4ca/DIFF.patch` (full), head `9602b4ca300b17fdbd3673378ab797f8e36cda62`, security path (no round cap).
**Inputs:** `sonarpath-9602b4ca-design-r3.md` (0 Blocker, 4 Major, 11 Nit) and `sonarpath-9602b4ca-codebase-r3.md` (1 Blocker, 5 Major, 6 Nit). Both reviewers read code only. Runner a5cd050d has not reported; its findings are an addendum for the builder. **SonarCloud was not analysed by anyone; no finding is claimed cleared.** The success test remains the SonarCloud gate on the real PR.
**Method:** every finding checked against what the reviewers could read; none contested. 29 findings merge into 11 issues. Settled from r3 stays settled (strict re-join before each write, R13 temp collision, R4 range table with `EXPECTED_RANGES`, `from None`, the exceptions file format).
**Binding decisions applied:** one pattern for every S8707 site, `pathguard.join(path.parent, path.name, what=..., must_exist=True, kind="file")`; pathguard.py is our code at the last rung (no library confines a path for Sonar's taint engine) and must be as small as correctness allows; no NOSONAR and no other suppression; fake credentials built from parts; tests fail on old code or are named `test_pin_*` / `test_control_*` with labels from a real old-code run; each CHANGELOG claim has a test or is dropped; builders never commit under `handover/`.

## Handoff counts

- PROPOSE FIX accepted: 11 issues (all findings, nits included). CONTEST 0. ESCALATE 0. DECLINE 0.
- Remaining unaddressed: 0. **Round 4 is REQUIRED** (1 Blocker and Majors on a security path, no cap).

## Decision on M2 (undisclosed behaviour change), made here

Take the smaller change that keeps messages the same: names typed by an operator (an answers file, a mounted secret name, a hashed file) are NOT held to R3, R6, R7 and R12 (this matches CHANGELOG line 8). The last-check re-join for such names uses the containment-only form (`inside`), not the name-rule form. Names that come from data (event ids, bundle file lists, outbox names) keep the full `join`. If the builder shows by a Sonar run on the real PR that a site needs the full join, the change is listed in CHANGELOG as Breaking with one test each, but that is a later decision, not a default.

## Prioritized findings

### Issue 1, Blocker, class CHANGELOG-TRUTH (codebase B1, M4 lines 9, 15, design M3, nit 8, 9, 10)
`CHANGELOG.md:12` says `score` and `replay` refuse a linked run folder or case file "(they used to follow it silently)". On main `hash_files` called `confined(root, rel)` first, so those already raised; only the `outputs.sha256` link was followed silently. Line 16 claim is unmeasured. Line 15 ("a bare ValueError, which ConfigError is a kind of") is garbled. Line 9 "never the value" conflicts with `config.confined` echoing `relative` and `signer.build_local` printing "no key file at {path}". Refused outbox ids drop the audit record (warning, counter `refused_events`), not stated. Temp file mode is 0o666 minus umask.
PROPOSE FIX: rewrite every bullet from a measured old-code run (git worktree at main); drop line 12's silent-follow claim except for `outputs.sha256` if measured; fix line 15; line 9 says exactly which messages echo a config value and which never print a data-derived value; add the dropped-audit-record note; set temp mode 0o600 (or state the mode) with a test. Every bullet gets a test in `test_changelog_claims.py` that asserts the claim (see Issue 7).

### Issue 2, Major, class EQUIVALENT-HONESTY (codebase M1, design M4)
Eight EQUIVALENT entries in `tests/pathguard_mutants.py:933-994` are observable: hashing `confined`+`join` (1,2), secrets_file (3,4), load_answers re-join (6), bundle manifest join (7), local_dir second join `join(corrupt, listed)` (11), signer `inside(` (12). Entries 5, 8, 9, 10 are sound.
PROPOSE FIX: one guard per site (delete the doubled guard where the first already covers the same refusal); for each remaining doubled guard that is observable, add a mutant row and a killer test (names: `a?b`, `con`, `x.` read through `hash_files` and the secret provider; a planted link in `corrupt/` for local_dir; a symlinked parent with U+202E for signer; the real order of manifest read and rglob scan, with the message). Correct the manifest reason text. Keep an EQUIVALENT entry only with an argument the reviewer can read in the code, and a test that the list matches the table.

### Issue 3, Major, class MUTANT-COVERAGE (codebase M2)
Converted sites with no row, killer or EQUIVALENT entry: `score.py:227` (`_check_layout` join), `replay.py:175`, `replay.py:301` (`_mark_failed` `operator_dir`), `bundle.py:206` (`operator_dir`, a U+202E parent passes `is_dir`), `bundle.py:369` (`component`, claimed in CHANGELOG:17), `fake.py:49` (test checks the folder only).
PROPOSE FIX: a row and a named killer for each; `fake.py` test asserts the name too. Add a test that derives the list of converted call sites from the tripwire scan and requires a row or an EQUIVALENT entry per site (so a new site cannot be missed).

### Issue 4, Major, class EXCEPTIONS-TABLE (design M1, nit 2, 3, codebase N1, N2)
`test_pathguard_tripwire.py:487-499` enforces the validator only for origin "checked" rows; "operator" and "config" rows pass if the validator is in `pathguard.__all__`; rows 80-82 (tools.py) name `_module_files` as its own validator; rows are keyed by (file, function, call, count), not by the path argument. Docstring (lines 1-27) says "one line per function" and 4 columns; parser needs 7. Banned list lacks `os.access`, `os.chdir`, `os.statvfs`, `zipfile.ZipFile`, `importlib.util.spec_from_file_location`, `logging.FileHandler`; calls by reference (`map(open, xs)`, `partial`), `getattr`, `**kwargs`, non-constant `resolve(flag)` and nested defaults are not covered.
PROPOSE FIX: operator and config rows require the named validator to be called in the same file (or a named resolvable chain); no row is its own validator; header states validators are file-level; docstring matches the 7-column parser and lists the real limits; add the missing banned names; add plants for each uncovered shape or state them as limits with a test of the stated list. Fix the `local_dir.py:27` reason wording.

### Issue 5, Major, class PIN-LABELS (codebase M3, N5, design M3)
`test_pathguard_callers.py:3-4` still says FAIL-BEFORE for the whole file though the two link tests (`:59`, `:68`) and `test_control_a_clean` pass on main; `test_pathguard_batch3.py:85` `test_pin_r4_range_*` fail on e29cc269 and main (named pin; baseline inconsistent); `sites.py:243` replay NUL test asserts nothing about writing; `sites.py:388` outbox test passes with the final join removed (the `final` guard is unreachable in production; only the monkeypatched batch3 test kills it); `sites.py:342,167` say CONTROL but are not `test_control_*`; `sites.py:221` passes without the guard; `sites.py:118` is an arithmetic tautology; `sites.py:5` cites evidence not in the repo; `test_changelog_claims.py:37` redundant `or`.
PROPOSE FIX: one rule: baseline is main. Run every test in the three files on a git worktree of origin/main and print raw lines; label from that run (fail on main: plain name; pass on main: `test_pin_*` or `test_control_*`); the r4 range tests fail on main so rename to plain names with the docstring saying so. Fix or delete each listed test (replay NUL test must assert no file written; delete or restate the tautology; remove stale citations). State in `pathguard_mutants.py` that the outbox `final` guard is reachable only by the monkeypatched test.

### Issue 6, Major, class CLAIM-TESTS (codebase M4, nit 8)
No test for CHANGELOG bullets at lines 12, 14, 16, 17, 18, 19, 20, 21, 22, 24, 25 (resolved absolute paths; `key_path` resolving the whole target; `PathRefused` audit `error_code`; `refused_events`; no chain in cli; `TOUCHED` list claims "files this change wrote or rewrote" but omits `local_dir.py`, `signer.py`, `cli.py`, `config.py`, `judge.py`, `secrets_vault.py`). Existing claim tests check only part: `:91` folder only; `:82` no temp name; `:67` only R7; `:150` greps substrings, five reads claimed.
PROPOSE FIX: one test per bullet asserting the full claim (temp name, R6/R7/R12 each, adjacency of the strict join and the read via AST, `error_code`, `refused_events`); make `TOUCHED` derive from `git diff --name-only origin/main` or a stated list tied by a test.

### Issue 7, Major, class SHARED-CHOKE-POINT (codebase M5, design M4 size)
The R10/R11 mapping is shared only at folder level (`pathguard._operator`); it is hand-written inline at `hashing.py:35`, `secrets_file.py:48-51`, `causelist.py:44`, `signer.py:110-115`. pathguard.py is 273 lines (+49 this batch) with caller message policy (`unusable`, `unusable_rules` parameters, lines 201-257), duplicated `join`/`inside` tails (170-175, 191-198), and R12/R13 beyond the design.
PROPOSE FIX: one helper for the R10/R11 mapping used by all four sites; move caller message wording to the callers; merge the duplicated tails; remove any rule no test and no site needs, or keep it with a killer. Target well under 273 lines; state the final count in the PR text and say which lines are correctness and which are messages. Keep the public names `component`, `inside`, `join`, `operator_text`, `operator_dir`, `operator_file`.

### Issue 8, Minor, class ERROR-TEXT (design nits 1, 4, 5, codebase N4)
R5 counts characters while the Linux limit is bytes (`pathguard.py:46,144-146`); `atomic.py:39` raw OSError carries the temp path and `cli.py:272-276` re-raises it; `replay.py:320-324` `_mark_failed` catches only OSError and ConfigError; `signer.py:113-116` prints the resolved absolute path in "cannot load {source}"; `hashing.py:41` `raise ... from exc` can carry the path.
PROPOSE FIX: count bytes (UTF-8) for the name limit with a test; wrap the OSError with a message without the path and `from None`; let KeyboardInterrupt and MemoryError propagate unchanged and keep the original error when marking fails; print only the config value as typed in signer; `from None` in hashing. Test each.

### Issue 9, Minor, class LOCAL-DIR (design nits 6, 11)
`local_dir.py` is not in `TOUCHED` though a block was added in `write_outcome`; `:189 path.unlink()` on the join-resolved path removes the target, not a link inside the outbox that points to a file inside the base; `noqa BLE001` and `S112` at 138, 149, 162, 187 are old (not added by this diff) but sit in the changed function.
PROPOSE FIX: unlink the un-resolved entry (and test a link inside the outbox); add `local_dir.py` to the derived list (Issue 6); the old `noqa` lines stay untouched unless the builder replaces them with a narrower exception type, never with a new suppression.

### Issue 10, Minor, class R4-SET (design nit 7)
R4 omits U+115F, U+1160, U+3164, U+FFA0, U+17B4, U+17B5, U+1D173-U+1D17A, U+2800.
PROPOSE FIX: add them with the same `chr()` range table and tests (a drop, an early end and a late start per range), or state in the CHANGELOG that the list is the stated one and not complete, with a test that the stated list equals the code.

### Issue 11, Minor, class TEXT (codebase N3, N6, design nit 2)
`TOUCHED` overclaim (Issue 6); `_guarded` takes the latest assignment by line number whatever the branch (disclosed): keep the disclosure and add a plant; `_mark_failed` writes only if `out.is_dir()` and re-validates without a strict re-join (note: say so).
PROPOSE FIX: comment and CHANGELOG corrections in the same push.

## ONE FIX BRIEF (single small builder, batch 4; branch `wip/cloud-sonar-path2`, fast-forward only)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes); re-measure fail-before in `git worktree` at origin/main and at 9602b4ca with raw lines printed; no NOSONAR and no other suppression; fake credentials built from parts; never commit under `handover/`; never claim a SonarCloud finding cleared.

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | CHANGELOG-TRUTH | `CHANGELOG.md` lines 9, 12, 15, 16 and audit-record note from a measured main run; temp mode 0o600 | claim tests (Issue 6) | none | measured on origin/main |
| B | EQUIVALENT-HONESTY | one guard per site in hashing, secrets_file, score (`_recorded_digest`, `load_answers`), bundle, signer; `inside` for operator-typed last checks (M2 decision) | `a?b`, `con`, `x.` through hash_files and secrets; planted link for local_dir; U+202E parent for signer; manifest order | rows for each kept guard; trimmed EQUIVALENT list | main for old behaviour |
| C | MUTANT-COVERAGE | rows and killers for `score:227`, `replay:175/301`, `bundle:206/369`, `fake:49`; derived-site test | per site | one row per site | fails when row removed |
| D | EXCEPTIONS-TABLE | tripwire validator rule, header, docstring, banned names, plants | plants per shape | row per rule | new plants fail on old scanner |
| E | PIN-LABELS | relabel and fix tests from a real main run | the fixed tests | none | raw lines from main |
| F | CLAIM-TESTS | one test per CHANGELOG bullet; derived `TOUCHED` | per bullet | none | claim wrong, test fails |
| G | SHARED-CHOKE-POINT | one R10/R11 helper; callers own messages; merge tails; trim pathguard.py | existing + helper test | rows follow | pathguard line count reported |
| H | ERROR-TEXT, LOCAL-DIR, R4-SET, TEXT | issues 8-11 | per item | rows per range | per item |

Builder reports once when ALL of A-H are done: new head sha, raw fail-before lines, the pathguard.py line count, anything not done and why.

## Round 4 and evidence for the final head

- **Round 4 is required** (Blocker plus Majors on a security path). Fresh design and codebase reviewers on a new snapshot.
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13, changed and new mutant rows plus a 60-row sample, fail-before runs on origin/main with raw lines.
- **Branch and PR:** after a fresh round finds 0 Blocker and 0 Major, cut `core/k1b-path-confinement` from origin/main with code only (no handover files, no evidence); the lead opens the draft PR; the PR text states the fail-before counts. **Success test: the SonarCloud gate green on the real PR.** Until then say "pending".
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the pathguard and stage mutant tables, py313 and py312, Postgres, CI flags.
- Ledger rows SONARPATH-r3-1..10 exist; the caller adds new rows for issues 8-11.

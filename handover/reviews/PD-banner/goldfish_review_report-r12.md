Status: resolved

# Goldfish Annotated Review Report, PD Part 6 (mode banner and demo-only guard), round 12

**Target:** `/home/user/build/snap/pdbanner-c7eb5c79/DIFF.patch` (full), head `c7eb5c7940e95cbf38b3f2ee43e9f27a90e6120b`, mode-safety path (no round cap).
**Inputs:** `pdbanner-c7eb5c79-design-r12.md` (0 Blocker, 1 Major, 4 Nit) and `pdbanner-c7eb5c79-codebase-r12.md` (0 Blocker, 3 Major, 8 Nit). Both reviewers read code only and ran nothing. Evidence runner ab0c9e9a has not reported; its findings are an addendum for the builder.
**Method:** every finding checked against what the reviewers could read; none contested. 16 findings merge into 6 issues. Settled from r11 stays settled (seal by identity, masker equals main, `is_stand_in` not called until Part 2 merges, deepcopy raises, N7 declined, row count rule).
**Result:** no Blocker and no fail-open path found. All seven r11 classes are fixed in substance. What remains is one class (waivers and broad excepts), one label, wording and test quality. Because batch 13 changes code on a mode-safety path, a fresh round is required.

## Binding decision applied (lead, 04:45Z, `handover/LEAD-ORDERS.md`)

A broad `except Exception` in Part 2 and Part 6 is replaced by a **named exception tuple plus a test that a surprise error type is not swallowed** (it propagates or fails loudly). One class fix at the shared choke point, a sibling sweep, and the number of sites is stated. This overrules the builder's option (a) (per-file BLE001 ignore). Note the design reviewer's fact: BLE is not in `extend-select` (`pyproject.toml:72`), so the BLE001 ignore was inert as well as unentitled; the code rule is the lead decision, not ruff.

## Handoff counts

- PROPOSE FIX accepted: 6 issues (all findings, nits included except those listed as DECLINE inside issue 6).
- CONTEST 0. ESCALATE 1 conditional (issue 1: only a site that cannot propagate safely; the builder reports it to the lead with file and line). DECLINE 2 (codebase nit 8 `shutil.which` on Windows; design nit 1 merge of the two overlapping tests only if a real difference cannot be written, else keep both).
- Remaining unaddressed: 0. **Round 13 is REQUIRED** (mode-safety path, no cap, batch changes code).

## Prioritized findings

### Issue 1, Major, class WAIVERS / BROAD-EXCEPT (design M1, codebase M1, M2, nit 5)
`pyproject.toml:80-90`: per-file ignores are suppressions of the same class as inline ones. BLE001 for `app.py` and `mode_banner.py` is inert (BLE not selected), says "four sites" (there are five), says "owner decision pending" (now decided by the lead), and silently covers any future broad catch. S603 for `tests/fixed_run.py`, `tools/demo_only_guard.py`, `tools/scan_repo.py`: the comment says each runs "by its full path at those places only"; `tools/scan_repo.py:73-74` calls `subprocess.run(["git", "-C", ...])` directly (no `shutil.which`, no single entry point); two near-identical helpers exist (`fixed_run.run`, `demo_only_guard._run`) and both pass `**kwargs` through, so `shell=True` is not refused. Five broad sites: `app.py:295`, `:312`, `:471`; `mode_banner.py:731`, `:759`. `_SEAL_ERRORS` (`app.py:81`) and `_READ_ERRORS` (`mode_banner.py` ~104) are the same five types twice.
PROPOSE FIX:
1. Delete the BLE001 and S603 entries and their comments from `pyproject.toml`. No per-file ignore of any rule is added back.
2. ONE shared tuple (one definition, imported by both modules) of the named failure types a read can raise. Each broad site uses a named tuple: either that shared tuple or a named, wider tuple defined next to it with a reason line. Sites: `app.py:295` and `:312` (read of an app: a type outside the tuple propagates out of `mode_banner()`; the builder traces and proves that a propagated error can never leave a page served with a made-up or quiet banner: a public page that errors is fail-closed, and the error is logged once with its type, so the failure is loud, not swallowed). `mode_banner.py:731` (`banner_or_unconfirmed`: raisers are `TypeError`, `ValueError`, `AttributeError`; narrow to those named types). `mode_banner.py:759` (`_not_confirmed_that_cannot_fail`: the contract is "cannot fail with arbitrary words"; use the named tuple of the types a hostile word can cause, for example `TypeError`, `ValueError`, `AttributeError`, `RuntimeError`, `LookupError`, `UnicodeError`, `RecursionError`; any other type propagates, loudly). `app.py:471` (`post_card`, channel): this matches main and is not a mode site; give it a named tuple of the delivery errors (`OSError`, `ValueError`, `TimeoutError`, plus a `RuntimeError` base for a client library) with a reason, or keep main's behaviour with a named tuple, never `Exception`.
3. A surprise-type test per site: raise an exception class that is in none of the tuples (a private `class _Surprise(Exception)`) and assert it propagates (or is logged and re-raised) and that the banner never reads "made-up" or "quiet". Sweep siblings: `grep -n "except Exception\|except BaseException\|except:" src/hadavin_sdk/app.py src/hadavin_sdk/mode_banner.py src/hadavin_sdk/*.py` and state the count found and fixed; report any site the builder cannot narrow safely to the lead with file and line (this is the only ESCALATE case).
4. S603: ONE helper (put it in `tools/demo_only_guard.py::_run`, which already uses `shutil.which`, a list argument and no shell; `tests/fixed_run.py` and `tools/scan_repo.py` import it) that refuses `shell=True` and `**kwargs` that carry it, and keep the arguments a literal list. If ruff still reports S603 or S607 on the helper line, report the exact line to the lead (ESCALATE); do not waive.
Fail-before: surprise test fails on c7eb5c79 (swallowed) and passes after; `ruff check` clean with no per-file ignore; grep of added lines for suppression markers is 0; `pyproject.toml` diff against main shows no `per-file-ignores` entry other than `tests/**`.

### Issue 2, Major, class PIN-LABELS (codebase M3, design nit)
`test_each_unreadable_shape_seals_as_unreadable_and_reads_unconfirmed_with_nothing_handed_in` (`test_mode_banner.py:3638-3660`) is a non-pin whose only old-code failure is the missing name `_UNREADABLE` (decision 1 of r11: a missing helper name does not count); it also uses `setattr(app_mod, "_services_in", ..., raising=False)`. `test_every_equivalent_mutation_has_a_reason` (`test_banner_mutant_table.py:447-455`) rests on the new `bm.EQUIVALENT` name.
PROPOSE FIX: read the sentinel with `getattr(app_mod, "_UNREADABLE", None)` and assert behaviour first (the banner tone on the old code) so the old-code failure is a behaviour; re-run both on a `git worktree` at dd827d79 and relabel from the raw lines. The `EQUIVALENT` test is renamed `test_pin_...` with the label "same new file, cannot fail on old code" unless a real old-code run shows a behaviour failure.

### Issue 3, Minor, class CHANGELOG-TRUTH (codebase nits 2, 3, 4)
CHANGELOG still lists the masker pass "address" (code says URL, `tools/demo_only_guard.py:271, 282`). "Logged once per reason and error type" is true for `_warn_once` (`app.py:95-102`) but `banner_or_unconfirmed` (`mode_banner.py:732`) logs on every call. "`build` does NOT fail" is wider than `_SEAL_ERRORS` (five named types).
PROPOSE FIX: change each sentence to what the code does after batch 13 (the shared tuple replaces `_SEAL_ERRORS`; state the exact types, and that a type outside them propagates from `build`); name the pass "URL"; give the log rule per path. Claim tests for each changed sentence.

### Issue 4, Minor, class MUTANT-KILLER (codebase nit 1, nit 6 part, `_stage` row)
`expectation_nowhere_in_killer` (`test_banner_mutant_table.py:377-406`) still accepts any string constant in the killer, an `expect` that merely contains a 5-character literal, and a 4-character `startswith`; a same-named nested function shadows `funcs`. No row covers the `_stage` non-str `TypeError` (`app.py:242-243`). The 20 `COMPUTED_EXPECT` rows are exempt from the static check.
PROPOSE FIX: require the `expect` to equal or be built from the killer's assertion message (exact string or f-string pieces, minimum length 8, no `startswith`); detect and refuse duplicated function names; add planted tests for the three loose cases; add row R13A1 for the `_stage` non-str raise with a killer; the evidence runner confirms the 20 `COMPUTED_EXPECT` expectations occur in the first failing line (its job, not the builder's). Row count is derived: 321 or more, CHANGELOG and tests follow.

### Issue 5, Minor, class TEXT (codebase nits 6, 7; design nit 1, nit 5)
`test_mode_banner.py:2742` builds `_sealed` with a 3-tuple but the seal has four slots; added comments and the CHANGELOG exceed 100 columns (`mode_banner.py:759` trailing comment; header comments at `test_mode_banner.py:3592`, `:3605`); tests at `:3105` and `:3490` overlap (same NameError through `_connected_parts`, logged once).
PROPOSE FIX: build the fixture from the real slot count (use `len` of the sealed tuple of a built app); wrap comments to 100 columns; make the two tests differ in one stated way or merge them (DECLINE the merge if a real difference is written).

### Issue 6, Nit, DECLINE
Codebase nit 8 (`shutil.which` also searches the current directory on Windows): the repository's CI and every evidence run is Linux; recorded, no change. Design nit 5 duplicate with issue 5.

## ONE FIX BRIEF (single small builder, batch 13; fast-forward only onto `wip/cloud-pd-banner`)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes, each command under 8 minutes and resumable); real fail-before runs in `git worktree` at dd827d79 and c7eb5c79 with raw lines; no suppressions and no per-file ignores; fake credentials built from parts; never commit under `handover/`; a suppression-marker count on added lines against `origin/main` in the report; **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.**

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | WAIVERS / BROAD-EXCEPT | issue 1: delete the 5 `pyproject.toml` ignores; one shared tuple; named tuple at five sites; one subprocess helper | a surprise-type test per site; `shell=True` refused; helper test | row per site that restores a broad catch | surprise tests fail on c7eb5c79 |
| B | PIN-LABELS | issue 2: tolerant `_UNREADABLE` read, behaviour first, relabel | relabelled set | none | raw lines at dd827d79 |
| C | CHANGELOG-TRUTH | issue 3: URL, log-rule per path, exact tuple | claim tests | none | wrong claim fails |
| D | MUTANT-KILLER | issue 4: stricter expectation check, planted tests, row R13A1 | planted tests; killer for `_stage` non-str | R13A1 and rows from A | fail when `expect` is wrong |
| E | TEXT | issue 5 | none (read check) | none | n/a |

Builder reports once when ALL of A-E are done: new head sha, the count of broad sites found and fixed with the exact tuple per site, any site it could not narrow (lead decision, file and line), raw fail-before lines, grep for suppression markers on added lines, `pyproject.toml` diff against main, anything not done and why.

## Round 13 and evidence for the final head

- **Round 13 is required.** Fresh design and codebase reviewers on a new snapshot; they count suppression markers on added lines and inspect `pyproject.toml` for any per-file ignore beyond `tests/**`.
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13; new and changed rows plus a 60-row sample; the 20 `COMPUTED_EXPECT` rows against their first failing lines; fail-before with raw lines; suppression grep; a surprise exception injected at each of the five sites.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete banner_mutants (321+ rows) and stage_mutants tables, py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows PDBANNER-r12-1..4 exist (issue 1 and 2 map to them); the caller adds rows for issues 3-5 if wanted.

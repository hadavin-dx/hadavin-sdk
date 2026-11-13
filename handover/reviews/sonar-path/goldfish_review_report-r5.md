Status: resolved

# Goldfish Annotated Review Report, SONAR-PATH (ORDER 260), round 5

**Target:** `/home/user/build/snap/sonarpath-622027cc/DIFF.patch` (full, merge-base diff), head `622027cc0aff5168c61deb79d1334334af3289b2`, branch `wip/cloud-sonar-path2`. Security path: no round cap.
**Inputs:** `sonarpath-622027cc-design-r5.md` (0 Blocker, 2 Major, 6 Nit) and `sonarpath-622027cc-codebase-r5.md` (0 Blocker, 4 Major, 9 Nit). Both reviewers read the snapshot only and ran nothing. Evidence runner a8d58542 has not reported; its facts are an addendum for the builder (`handover/evidence/sonar-path/622027cc/RESULTS.md`).
**Settled and not re-opened:** one choke point, the join pattern, label definition (a)/(b), the 20-range table, `atomic_write`, replay interrupt handling.
**Result:** no Blocker, no escape and no new path leak found by either reviewer. Six Majors remain (they merge into five issues), all fixable. Because code changes on a security path, **round 6 is REQUIRED**.

## Handoff counts
- PROPOSE FIX: 11 issues (all Majors, and the Nits listed below).
- ESCALATE: 1 (issue 1, the product choice about operator-typed symlinks; a default is applied meanwhile).
- CONTEST: 0. DECLINE: 4 nits (listed at the end). Remaining unaddressed: 0.
- Sonar: nothing here claims any SonarCloud finding is cleared. Probe PR #100 is the only evidence for the exact `join(parent, name, must_exist=True, kind="file")` form.

## Prioritized findings

### Issue 1, Major, class OPERATOR-SYMLINK (design M1; codebase N6)
Operator-typed key, token, answers and golden files (`audit/signer.py` ~109-112, 223-226, 236-238; `actions/secrets_vault.py` 181-185; `guard/judge.py qualify`; `k1b/score.py load_answers`) are read through `join(parent, name, ...)`. The base is the file's own folder, so a symlink whose target is in a different folder is now refused (a sops-nix or Docker-style mount `/run/secrets/signer.key -> /run/secrets.d/1/signer.key` worked on main). Names such as `id:ed25519` and `key.` are also refused. The CHANGELOG states the refusals but not this mount case. The vault token join omits `must_exist` and `kind` (deviation 1), a weaker form than the one probe PR #100 proved.
ESCALATE (the evidence for "revert or keep" is the lead's ORDER 260 text, outside every file the reviewer could read). Default applied until the lead answers: KEEP the pattern (it is the lead's binding order at every S8707 site) and make the break loud and honest:
1. CHANGELOG and the future PR text name the case in plain words: "a key, token, answers or golden file that is a link pointing into a different folder is now refused; a link whose target stays in the same folder is read; Kubernetes projected tokens (`token -> ..data/token`) stay inside the folder and are fine".
2. Add a documenting test pair per site class: link inside the same folder is read; link to another folder is refused with the R8 text and no path. These are labelled by a real run on abb3e90a and the (a) tree (they pass or fail there, label from the raw lines).
3. State as a risk in the CHANGELOG that the vault token join does not use `must_exist` or `kind`, and that this form is not proven by probe PR #100.
Question for the lead (Q-R5-1): keep the refusal of out-of-folder links for operator-typed files, or revert `operator_file` for those five sites? Recommendation: keep, because it is the pattern the order requires and the only SonarCloud evidence is for it; a mount layout that uses out-of-folder links can set the typed path to the link target's folder.

### Issue 2, Major, class ERROR-LEAK (codebase M1; design M2; codebase N2)
(a) `tools._module_files` (`tools.py:257`, `:265-266`): `MAX_PART_BYTES = 255` but the looked-up name is `leaf.with_suffix(".py")` (+3 bytes). A final part of 253-255 bytes passes the check, then `is_file()` stats a 256-258 byte name; ENAMETOOLONG is not in the ignored errnos on 3.12/3.13, so a raw `OSError` carrying the path escapes. The CHANGELOG sentence "a part longer than 255 bytes (`ConfigError`)" is false; the test uses 300 bytes only.
(b) `signer.key_path` (`signer.py ~143-177`): `folder.mkdir(...)` and `folder.resolve(strict=True)` are raw. A key folder under a regular file gives `NotADirectoryError` quoting the typed path; a PermissionError does the same. The CHANGELOG claim "its messages hold no path" is stronger than the code. Also: the key file's shape is checked after the `mkdir`, so a NUL now raises "cannot be checked" after a folder was made, where it used to be an R4 refusal before; and the text "(home folder not found)" is reused for a NUL and an OSError.
PROPOSE FIX (the repo rule is fix, not narrow the claim):
1. Class: a name derived by adding a suffix or prefix to a checked name is itself longer than the limit. Fix at the choke point: `pathguard.component(name, extra=0)` (or the existing `MAX_WRITE_NAME_BYTES` idea) so the limit is applied to the final stat name; in `_module_files` limit parts to `MAX_COMPONENT_BYTES - len(".py")`, and any stat of `<name> + suffix` takes the same route. Sibling sweep: `grep -n "with_suffix\|+ \".\|\.tmp-\|f\"{.*}\.\(yaml\|json\|py\)" src/hadavin_sdk` and state the site count with each site's final-name check.
2. `key_path`: route `mkdir` and `resolve(strict=True)` through the same `_os` mapping with `from None`, fixed text, no path; check the key file shape BEFORE the `mkdir`; give a NUL, an OSError and an unknown home folder their own fixed texts.
3. Tests: `tools_module` parts of 252, 253, 254, 255, 256 bytes (a part that fits the name limit but not with `.py` is a ConfigError, never an OSError); key folder under a regular file; key folder permission error (skip if not reproducible as non-root, say so); NUL before `mkdir`. Each is run on abb3e90a and the (a) tree and labelled from the raw lines.
4. Update the exceptions fixture row text for the three `.is_file` calls in `_module_files` (it says "checked part by part with isidentifier", incomplete).
5. Mutant rows: restore the plain `MAX_PART_BYTES` (kills 253-255 test) and drop the `from None` mapping at `key_path` (kills the key-folder test).

### Issue 3, Major, class LABELS-AND-TRUTH (codebase M2, M3, M4; N7; design nits 1, 2)
- Header counts: `tests/test_pathguard_batch5.py:4` says "1 control, 9 pin, 12 other"; by name it is 1 / 6 / 10 functions (ids 1 / 6 / 20, 27 total). `tests/test_changelog_claims.py:4` says "30 other"; the reviewer counts 31 ids. `test_every_range_count_in_the_entry_is_the_length_of_the_code_table` (claims:734) reads only `CONTROL_RANGES` and the CHANGELOG so on the (a) tree it passes and must be named pin or control. Headers of `test_pathguard.py` (3/31/15), `test_pathguard_sites.py` (3/11/19) and `test_pathguard_tripwire.py` (19/0/2) were not checked by the reviewer.
- `test_pathguard_batch5.py:163-171`: the sentence that on abb3e90a any `PathRefused` (objects folder is a file) dropped the record is not supported: `join` resolves non-strictly, ENOTDIR on a child of a file is not raised, the failure is the `mkdir` `FileExistsError` which already took the outbox path. `test_a_loop_in_the_objects_folder_takes_the_outbox_path_too` gives a PathRefused only on 3.12 (RuntimeError from resolve); on 3.13 it is a no-op as a fail-before.
- CHANGELOG bullet "An error from the operating system ..." says a raw OSError escaped on origin/main from `operator_dir`, `operator_file` and `LocalDirSink(root)`, which are new in this change.
- Stale and misleading names: `counts_operator_text_as_a_guard` in `tests/fixtures/pathguard_tripwire_bad.py:101` (`operator_text` no longer exists); "not a ValueError" in `test_a_mounted_secret_folder_with_a_nul_...` (PathRefused is a ValueError subclass); the "never chained or quoted" name overstates (`__context__` still holds the OSError; only `__cause__` is cleared).
- `test_control_site_local_dir_outbox_refuses_a_device_name_as_the_event_id` (`test_pathguard_sites.py:387-398`) is vacuous and its docstring is false; `tests/test_pathguard_callers.py` header (lines 3-5) contradicts its control labels at 62 and 71 and CHANGELOG line 17.
PROPOSE FIX:
1. Recompute every header from the real runs (at (a) and (b)) and from the function and parameter ids; a test in the claims file derives each header number from the file itself (count of `def test_control_`, `def test_pin_`, others, with parametrize ids) and fails on a mismatch. Rename the range-count test per its measured label.
2. Replace the batch-5 fail-before sentence by what the raw run shows; build real `PathRefused` triggers that fail on abb3e90a (an existing `objects/<id>.json` that is a link out gives R8; a path over 4096 bytes gives R5) for the drop-only-for-id behaviour; keep the loop test and label it "3.12 only".
3. CHANGELOG: scope the OSError sentence to what main's callers did (`registry`, `signer`, `score`, `local_dir` as they were) and delete "On origin/main ... `operator_dir`, `operator_file`".
4. Rename stale names; change "not a ValueError" to "a ConfigError, not a bare PathRefused"; change the "never chained or quoted" test name to say what it asserts (`__cause__` cleared, no path or errno in the text), and add an assertion that the exception text and `args` carry no path; set `__context__ = None` in `_os` as well (raise the refusal outside the `except` block) so a reporter walking `__context__` finds nothing, and test it.
5. Make the vacuous outbox device-name test real (monkeypatch only if needed, say so in the docstring) or delete it and keep the mutant row's reasoning; fix the callers header to match its labels.

### Issue 4, Minor, class MUTANT-TABLE (codebase N5, N8)
The EQUIVALENT entry for `final = pathguard.join(...)` in `audit/local_dir.py` (`pathguard_mutants.py:1262-1266`) is not equivalent: with `outbox/<id>.json` a link out, the guard refuses (R8) and the outcome stays in memory; without it `os.replace` overwrites the link. Rows citing `tests/test_k1b_stats.py::test_hash_files_canonical_names_and_errors` and the unchanged rows at lines 64-180 and 1000-1125 were not verifiable by the reviewer; `row.file`/`row.old` attribute names of `Mutant` were not confirmable.
PROPOSE FIX: add a test (outbox final name is a link out: refused, outcome kept in memory, link target untouched) and turn the entry back into a normal row that this test kills; the runner's old-text check is the evidence for the unverified rows; confirm `Mutant` attribute names in the evidence.

### Issue 5, Minor, class AUDIT-EDGES (codebase N3, N4; N1 TypeError)
- `write_intent` reports "event id refused (Rn)" for any PathRefused from `_write` (for example R5), wording misleading. PROPOSE FIX: say "path refused (Rn)" unless the refusal is the id check.
- `write_outcome` fallback joins `.tmp-<id>`: an id ending in "." or a space passes `_id_refused` but fails R6 on the `.tmp-` name, so the outcome goes to `_pending` memory. PROPOSE FIX: make `_id_refused` check the `.tmp-<id>` name too (so such an id is rejected up front with the id refusal) and test it.
- `Path(base)` / `Path(path)` with a non-str, non-Path value (None, bytes) raises a raw `TypeError` in `inside`, `join`, `_operator`. PROPOSE FIX: a `TypeError` is mapped by the same `_os` wrap to the fixed R10 text; `_only_a_refusal` is fed None and bytes.

## Declined nits (recorded, no change)
- Design nit 4: `pathguard.py` at exactly 220 lines and lines over 120 characters: the limit is met, ruff is clean per the builder, E501 is not selected. The "Rung" sentence is rewritten as part of issue 3 only if the text moves; otherwise no change. (If the fixes in issue 2 and 3 push the file past 220 lines, the limit is raised in the design note by a stated amount or the code is compressed; the builder reports which.)
- Design nit 5: `# fmt: skip` is a formatter directive, not a security suppression; the lead decides. The CHANGELOG suppression bullet is extended to say "no `fmt: skip` is added; two removed comments were restored to main text" only if true on the final head.
- Codebase N9: stale comment "re-checked here" in `_check_layout` is true only through `outputs_dir`: the comment is reworded in the same push (text only).
- Codebase N8 PEP 695 `def _os[T]`: the builder confirms in the report that the project floor is 3.12 or later (read `pyproject.toml`) or rewrites without PEP 695.

## ONE FIX BRIEF (single builder, batch 6; fast-forward only onto `wip/cloud-sonar-path2` from 622027cc)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and rows only, at most 2 heavy processes, each command under 8 minutes and resumable); real fail-before in `git worktree` at abb3e90a and at origin/main src plus head `pathguard.py` with raw lines; no suppressions and no per-file ignores; nothing under `handover/`; fake credentials built from parts; suppression-marker count on added lines against the merge base (`origin/main...HEAD`); run the FULL test files of everything touched and list every test file not run; remove scratch worktrees and stop your own processes; **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.** Never claim a SonarCloud finding is cleared.

| # | Class | Change | Test | Mutant row |
|---|---|---|---|---|
| A | OPERATOR-SYMLINK | issue 1: CHANGELOG and test pair; vault-join risk stated | link inside same folder read, link elsewhere refused | none new |
| B | ERROR-LEAK | issue 2: final-name limit, sweep count, key_path mapping and order | 252-256 byte parts; key folder under a file; NUL before mkdir | rows restoring the old limit and the raw mkdir |
| C | LABELS-AND-TRUTH | issue 3: headers from runs, self-checking header test, fail-before sentence, CHANGELOG scope, names, `__context__` | header test; real R8/R5 triggers; context test | none |
| D | MUTANT-TABLE | issue 4 | outbox link-out test | final-join row restored |
| E | AUDIT-EDGES | issue 5 | `.tmp-` id edge; None and bytes | rows per branch |

Builder reports once when ALL of A-E are done: new head sha, per class the counts and the sibling-sweep site count, raw fail-before lines, test files not run, mutant rows run by name and result, pathguard.py line count, any item not done with the reason (lead decides).

## Round 6 and evidence
- **Round 6 is REQUIRED.** Fresh `egm:egm-design` and `egm:egm-codebase-details` reviewers on a merge-base snapshot, plus one evidence runner on the final head.
- Cloud evidence: focused tests on 3.12 and 3.13, all rows (or changed rows plus a 60-row sample with the full table once on the final head, resumable), fail-before, suppression grep, error-leak probes at 252-256 bytes.
- On a clean round (0 Blocker, 0 Major): `PR READY: core/k1b-path-confinement <sha>` as ORDER 260 requires (a code-only branch cut from origin/main, built by the lead from the final head) and RUN ON LAPTOP: hadavin-sdk `<final sha>` full pytest on Linux Docker, py313 and py312, CI flags.
- Ledger rows SONARPATH-r5-1..5 are added by the caller.

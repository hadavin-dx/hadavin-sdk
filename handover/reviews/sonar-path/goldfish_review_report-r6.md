Status: resolved (automated; no person; every PROPOSE FIX auto-accepted)

# Goldfish Annotated Review Report, SONAR-PATH round 6

**Target:** `/home/user/build/snap/sonarpath-4398e3bd/DIFF.patch` (full), head 4398e3bd, SECURITY path (no round cap).
Inputs: `sonarpath-4398e3bd-design-r6.md` (0B/1M/9n), `sonarpath-4398e3bd-codebase-r6.md` (0B/2M, 9 nit groups), LEAD-ORDERS 06:30Z.
Evidence status: the cloud runner a4ec29ae on 4398e3bd is stopped (lead: runner on the FINAL head only, once, on the laptop). Reviewer facts are read-only; neither reviewer ran code. All builder numbers stay builder-claimed.
Counts: 3 Majors (all PROPOSE FIX), 18 nit items (17 PROPOSE FIX, 1 DECLINE), 0 CONTEST, 0 ESCALATE (Q-R5-1 is already with the lead). Round 7 is required (security path, code changes).

## Majors
### [M1 design + extends] `actions/secrets_vault.py` 188-191 prints the raw `jwt_path`
*   AI Suggestion: PROPOSE FIX. Class: a message that echoes operator text. Fix at the vault choke point: for `PathRefused` print fixed text only (`cannot read the sign-in token file (refused: <refusal code>)`); for OSError/UnicodeDecodeError print the type name and `!r` of the path only if the path passed R4, else fixed text. Add the Vault message to the CHANGELOG list of places that still print caller text, or remove it from that list by the fix. Test with a path holding a control character and an ANSI escape; it must fail on 4398e3bd. Sibling sweep: grep every `except ... PathRefused` and every f-string with `{...path}` in actions/, audit/, k1b/, cli.py, config.py.

### [M2 codebase] `tools._module_files` (tools.py ~256-265) total length unbounded
*   AI Suggestion: PROPOSE FIX. Fix: build the path with `pathguard.join(root, *parts, what=...)` (whole path R5 plus the parts rule) instead of `root.joinpath(*parts)`; keep the 252 per-part cap. Test: 17 parts of 252 bytes must give a typed refusal with no OSError on 3.12 and 3.13; run it in an old tree at 4398e3bd and show the raw OSError (real run, builder-claimed until the runner). Add a mutant row (swap join back to joinpath) and fix the CHANGELOG "13 sites, 3 leaked, fixed" sentence to match the code.

### [M3 codebase] boundary test builds 4095 bytes, comment says "exactly the limit"
*   AI Suggestion: PROPOSE FIX. Rule decision (also N1): PATH_MAX is 4096 including the closing NUL, so the largest allowed path is 4095 bytes and a path of 4096 bytes or more is refused. Change `pathguard.py:142` to `>= 4096` (named constant `MAX_PATH_BYTES = 4095`, `>`), update CHANGELOG line 7 ("at most 4095 bytes") and the R5 text. Boundary tests: 4095 allowed, 4096 refused, both exact; mutant rows for `>` to `>=` and for the constant. Measure the RESOLVED path too (after resolve) in `operator_dir` and `operator_file`, not only the typed text.

## Nit items (DECIDE)
1. N1 (codebase) PATH_MAX off by one and `must_exist=False` with no `kind`: PROPOSE FIX as M3 above; for `must_exist=False` and no `kind` the resolved path is still measured, so the caller never gets an over-long path back.
2. N2 (codebase) `LocalDirSink` intent/outcome id asymmetry: PROPOSE FIX. One helper decides "id refused" for both writers from the names `_write` really uses (`<id>.json`); the outbox name check runs only on the fallback path; "event id refused" is printed only when the id check itself failed. Test id `abc.` through both writers.
3. N3 (codebase) tests depend on `tmp_path` length: PROPOSE FIX. Build the long path from `len(str(tmp_path))` so the total is fixed, and skip nothing; add a control asserting the total.
4. N4 (codebase) sweep test says 13 sites, checks 9 files; design N6: PROPOSE FIX. Count sites per file in the test (13 across 9 files, listing the 4 shared sites) or reword to "9 files"; check the "3 leaked / 10 already checked" split against the source and CHANGELOG baseline (say the baseline commit).
5. N5 (codebase) stale `label != "inside"` exemption, one-element loop, "characters" in a test name: PROPOSE FIX (remove the exemption and prove it by a run, drop the loop, rename).
6. N6 (codebase) `signer.key_path` except tuple untested: PROPOSE FIX. Tests for `None` and bytes arguments and an OSError path, plus a mutant row per removed member.
7. N7 (codebase) CHANGELOG lines 10/17/20 disagree on check order and omit the 255-per-name refusal: PROPOSE FIX, one order stated once and the other lines pointing to it; design N7 `key_path` name rules and "no read follows": PROPOSE FIX, apply name rules R3/R6/R7/R12 to the key file name (or state precisely which rules apply and why) and fix the sentence.
8. N8 (codebase) `_os` catches `RuntimeError`: PROPOSE FIX. Catch `RecursionError` and the symlink-loop `RuntimeError` by named tuple, with a surprise test (an unrelated RuntimeError must propagate); `_size` and `surrogatepass`: expose one public `name_bytes()` in pathguard and use it at `atomic.py:28`; remove the dead `causelist._inside` docstring mention.
9. N9 (codebase) nested `pytest.main` collect-only test: PROPOSE FIX. Replace with a static scan (ast) of `ids=` and parametrize literals in tests/ that finds key-shaped, account-number-shaped and ARN-shaped strings; no magic 1000, no addopts dependency; star-unpack removed. Lead 06:30Z (3): rename account-number and ARN-style test ids with `ids=` built from parts and extend the recogniser to cover them; fail-before on old files (count the hits).
10. N1 (design) `atomic.py:33` unwrapped `final.is_dir()`: PROPOSE FIX, wrap by `_os` or use the guard; test with a folder without search permission (skip if running as root and say so).
11. N2 (design) `__context__` still holds the OSError at `atomic._without_path` and `signer.key_path`: PROPOSE FIX. Raise outside the `except` block so both `__cause__` and `__context__` are None; the test asserts both.
12. N4 (design) `score._recorded_digest` docstring wrong for loops and EACCES: PROPOSE FIX (state that `None` also covers a symlink loop, EACCES and over-long names).
13. N5 (design) CHANGELOG "same folder" vs `..data/token`: PROPOSE FIX. State the rule the code has (the target must lie inside the link's own folder, subfolders included); add the projected-volume test; relax the pinned phrase in `test_changelog_claims`. Q-R5-1 stays with the lead; recommendation recorded below.
14. N9 (design) `replay.py:151,159,173` and `cli.py:263,270` raw PermissionError with the typed path: PROPOSE FIX. Route through `operator_dir(create_mode=...)`; test an unwritable parent.
15. Lead 06:30Z (1): `pathguard.py` is 234 lines, limit 220, limit untouched: PROPOSE FIX. Preferred: split by responsibility into `k1b/pathtext.py` (text rules R1-R5, `name_bytes`, constants; about 70 lines) and keep the join/inside/operator_* choke point in `pathguard.py` (about 170 lines); no caller imports `pathtext` directly. The M3 and N8 edits add lines, so the split is required, not optional. If the split is not clean, report two options with line counts (cut to 220, or split) and the lead rules.
16. Lead 06:30Z (2): the 3.12 mutant table is run on the final head before the runner (builder must show 3.13 and 3.12 counts; a half-run table is not evidence): PROPOSE FIX (process).
17. Lead 06:30Z (4): Q-R5-1 in `handover/questions-for-lead.md` in 3 lines with a recommendation: PROPOSE FIX. Recommendation: keep refusing operator-typed links that leave their own folder (least privilege; the projected-volume shape `..data/token` stays allowed because it stays inside the link's folder). The builder drafts the 3 lines in its report; the lead (this session) commits them on core/cloud-handover (builders never commit handover/ off that branch).
18. Codebase "N8 pathguard docstring cites causelist._inside": folded into item 8. DECLINE: codebase N8 `_size` using `surrogatepass` counting a lone surrogate as 3 (over-refuses, never under-refuses); name this in a one-line code comment only.

## Settled across rounds (not reopened)
R1-R13 rules and tests, `_os` raising with no cause/context, 252/255 arithmetic, `confined` delegation, exceptions-file rows, mutant old-text uniqueness and header counts (reviewer-checked this round); no suppressions added.

## ONE FIX BRIEF: batch 7 for builder ac09a2ce (wip/cloud-sonar-path2, fast-forward from 4398e3bd; code, tests, CHANGELOG only)
Do all of M1-M3 and items 1-17 in ONE push, then ONE report. Rules that apply:
- NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.
- Set PYTHONPATH=<your worktree>/src and print `hadavin_sdk.__file__` before every test run.
- No full suite in the cloud; each command under 8 minutes; at most 2 heavy processes. Run focused tests and the mutant table on 3.13 AND 3.12 (the 3.12 table before you report; a half-run table is not evidence); the runner's full run happens on the laptop on the final head only.
- No suppressions (no noqa, nosec, NOSONAR, type: ignore). Report the added-suppression count against the merge base (`git diff origin/main...HEAD`, three dots).
- Never commit junit/xml/raw logs; any test name holding a key-, account-number- or ARN-shaped string is built from parts and given `ids=`; the recogniser test (item 9) must catch these shapes.
- Fail-before by REAL runs in old trees (4398e3bd and the earlier batch heads where the finding is older); every new test fails on the old code or is labelled control/pin; header counts updated.
- Class-level fixes only: name the class, fix at the shared choke point, sibling sweep, property tests.
- Do not touch the pathguard line limit; do the split (item 15) or report both options with line counts.
- Do not commit anything under handover/ (the lead commits on core/cloud-handover); put the 3-line Q-R5-1 text in your report.
- List every test file you did not run; state builder-claimed versus runner numbers; remove scratch worktrees and stop your own processes; checkpoint note every 30 minutes, at 60 minutes stop and report.
- Report `PR READY: core/k1b-path-confinement <sha>` only after a fresh round (round 7) finds 0 Blocker and 0 Major; never claim a SonarCloud finding is cleared.

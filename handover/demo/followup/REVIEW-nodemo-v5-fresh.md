# Fresh review: nodemo-optional-hygiene-repo-v5.patch (sha256 e4235cb4...109c) on main 61ded9e
Reviewer: fresh, read-only. Scratch: /tmp/work/rv-nd5/ (clones m, s, c1, c2, mutant trees, outputs out-*.txt). Studio rules cited: R6, R7, R12, R19 (preamble numbering).
VERDICT: NOT CLEAN (0 Blocker, 2 Major, 5 Minor). Applies fine. Nothing pushed, no network, no process left running, PID 17069 untouched.

## Apply (measured)
v5, yaml-trimmed-v2 (sha 2590a42f...), semgrep-on-db54e13-v5.1 (sha fac20b03...): `git apply --check` OK alone on 61ded9e; all 6 orders applied and committed one after the other with plain git apply: OK. No conflict, no rebase needed. Collected test ids (demo present, DPLD_REQUIRE_DEMO=1): base 3605; v5 alone: the only difference is the 21 new tests/test_client_copy.py ids; the stack: 3704 (+23 client_copy, +3 lock, +63 nosemgrep_form, +12/-4 yaml-trimmed parse, +2 run_flags). Not checked: the other 10 pending patches of the notes' matrix (not asked).

## MAJOR 1: the run-time backstop can hide a real product regression in a client copy
Evidence: conftest `_is_missing_demo_error` turns ANY ModuleNotFoundError named demo_only (old, kept) and now ANY FileNotFoundError whose path has a component equal to "demo_only" into a skip, in every phase, for every test of every "plain" file, including the tests whose job is the missing-demo behaviour (test_loader_missing_demo, test_codeant_hygiene, test_real_check_dry).
Measured: mutant of src/lead_desk/loader.py (the clean RuntimeError replaced by a bare `raise`, i.e. the product leaks ModuleNotFoundError): demo present -> tests/test_loader_missing_demo.py FAILS; client copy (no demo_only) -> "1 skipped: needs the demo_only folder, which is not here" (tree /tmp/work/rv-nd5/nd-loader vs dp-loader). The one run that exists to prove "the client copy behaves" cannot fail for this class. The ModuleNotFoundError half is pre-existing; v5 widens it to FileNotFoundError and widens the set of files it covers from 16 to 31.
Also measured: the test is path TEXT based, not provenance based: a plain test reading tmp_path/"demo_only"/"cfg.json" (a user folder that happens to be called demo_only) is a SKIP in the client copy, the same test under another name FAILS.
Product path escape: src/ names demo_only only in loader.py (replies.json, approvers.json next to the package); scripts/feed.py reads demo_only/canned_leads.json (feed test now skips by this path, intended). No other product file path under demo_only found (grep). Typo rows: a row/test naming a wrong file under demo_only/ is a skip in a client copy; caught by the demo-present CI run only (hook is off when DEMO_PRESENT, verified with mutant C below).
Fix: only convert when the file really is below REPO/"demo_only" (resolve, relative_to), never a substring/any-part; and an opt-out (marker or file allowlist) for tests that assert the missing-demo behaviour (test_loader_missing_demo, test_codeant_hygiene...), so a leak FAILS there; plus a test that a leaked ModuleNotFoundError in loader.py fails in a client copy.

## MAJOR 2 (sibling class, not a regression; lead may accept with a written follow-up): most "skipped because the file needs the demo" tests need no demo
NOTES say "the 61 still skipped all really need the demo" (true per FILE) and say the 517 functions were not measured. I measured. AST screen of the 61 files: 280 of 1228 test functions use no demo name, no env fixture, no demo helper. Ran samples of them in a client copy with demo_only replaced by a stub whose every name raises when used (reviewer plugin /tmp/work/rv-nd5/stubplug/rvstub.py): sample 1 (20 functions, 27 items): 26 pass, 1 fails (test_portal_mode::test_one_way_to_say_an_email_was_sent reads demo_only/portal_demo.js: correctly demo-bound). Sample 2 (40 functions; 2 sat in files that cannot import under the stub, excluded; 38 functions, 76 items): all 76 pass. So 57 of 58 sampled functions were skipped in a client copy for nothing: product tests of lock files, server bind/rebind, constants/gate validators, portal source text, HubSpot host rule, load-tool drain check, many in test_portal_mode (37), test_load_tools (27), test_stall_eviction (16), test_mode_safety (14), test_sonar_p2_choke_points (11). Sample is from the screened 280, not from all 1228; the screen can miss indirect demo use, the stub run is what decides. Fix class: module-level demo imports -> lazy/per-test skip (importorskip inside fixtures) in those files, or split plain tests out as v5 did for support.
Wrongly RUNNING: none found. The 31 running files in a client copy: 0 failures (below); the run-time skips there are 1 portal_demo, 6 real_check_dry, 1 path_confinement, 1 feed, 6 except-clause rows (own guard), 1 root-permissions (env).

## (3) support importable without demo_only: no demo-present behaviour change found
- Collected ids identical (above). support.py lazy import in build_rig only; `RecordedQualifier` under TYPE_CHECKING is only an annotation (future annotations on): safe. AST check: every `from support import X` / `support.X` in the stack resolves (script /tmp/work/rv-nd5/chk_support.py): 0 missing.
- Demo present, stack tree, DPLD_REQUIRE_DEMO=1 DPLD_REQUIRE_SCAN=1 gitleaks 8.30.1, git work tree clean: test_mode_safety, codeant_desk, bind_refusals, demo_folder_guard, hygiene, client_copy, flow, crash_points, lead_crm_copy, portal_api, codeant_demo_only, sonar_p2_feed_optional, gitleaks_semgrep_lock, nosemgrep_form: 480 passed, 8 skipped (playwright missing), 0 failed (out-s-demo.txt).
- Perturbation: with demo_only/leadflow.json deleted, DEMO_LEADFLOW is now {} instead of an import error: test_reminder_email fails with KeyError at collection (old: FileNotFoundError at collection): still loud, message less clear. Minor.
- Cross-patch risk (not in the asked stack): hang/hang-fix(-v2) and old triage/codeant2-desk patches add lines `from support import ... KeyedOutbox/RecordedQualifier`, which no longer exist in support: they would fail at import after v5 (they already do not apply on 61ded9e textually; whoever rebases them must import from demo_only.fakes).

## (2) scan guard: no Blocker, no silent loss of the scan in a git copy
- Client copy WITH git, DPLD_REQUIRE_SCAN=1, gitleaks: 31 files, 8 chunks of 4, one pytest at a time: 1697 passed, 15 skipped, 0 failed, every chunk rc 0 (out-c1-git.txt). Whole client copy collects 1774 items, 0 collection errors. 10 random skipped files: 10 single skips.
- Client copy with NO .git: without the variable 227 passed, 11 skipped (scan skips carry the long "NOT run ... git add -A" text, shown at the test's own file); with DPLD_REQUIRE_SCAN=1 11 failed = the 8 scan tests + 3 gitleaks tests (no gitleaks binary in that run): lost scan is a failure, as designed.
- Minor 3: a work tree git refuses (ownership differs: "detected dubious ownership", exit 128; measured by chown to another uid) gets the text "not a git work tree (a source archive or a copy without .git)": wrong cause, and without the variable it is a skip where before v5 (demo present) it was a failure. git's stderr is dropped. Wording rule R14.
- Minor 4: .github/workflows/sonar.yml runs pytest with DPLD_REQUIRE_DEMO=1 but no DPLD_REQUIRE_SCAN (lint.yml has both): a git problem on that runner would be a green skip there. One line to add.
- Known and stated by the notes: test_hygiene_scan_public step 3 (gitleaks canary) is after the skip.

## (4) mutants (mine, 6, plus 1 product mutant); suite = test_client_copy + demo_folder_guard + bind_refusals + raw_bidi_chars, demo present and no-demo/no-.git with the variable; baseline 56 passed / 1 failed (the expected no-git scan failure). Raw: out-mut.txt
B substring path check in the backstop (`"demo_only" in str(filename)`): SURVIVED.
C backstop hooks always active (also with the demo): SURVIVED, and a probe test reading demo_only/typo_name.json is a SKIP instead of a FAIL in a demo-present run (measured). CI would stop being able to see a wrong demo file name.
D `scan_required` true only for exactly "1" (the checks's own variable is truthy-string): SURVIVED.
E `_ENV_NEEDING_DEMO` without `serve`: SURVIVED; no file changes class (equivalent in this tree) but unpinned: only rig and fakes are asserted.
F2 rename test_sh_blobs_no_cr in test_hygiene.py, registry keeps the old name: SURVIVED because ADDED_BY_OTHER_PATCHES in test_client_copy.py exempts it. Minor 5: that exemption is stale, both tests exist at 61ded9e (test_hygiene.py lines 206 and 245): remove it so a rename or typo is caught.
S `_needs_demo` without the ast.Attribute branch (support.build_rig as attribute): SURVIVED, equivalent in this tree (no file affected), unpinned.
(A typo of a registry name that is not exempt IS killed: first F attempt, killed.)
Product mutant: loader leaks ModuleNotFoundError: client copy skips it (Major 1).

## Other findings
- Minor 6: 4 new `# noqa: S603/S607` comments (tests/_repo_root.py x2 lines, tests/test_client_copy.py x2); the repo has ~160 in tests, ruff passes, but the owner's no-suppression rule: tools/hygiene._git_text (already used by test_raw_bidi_chars) could do the git call without them.
- Minor 7: no EGM report or rung table in the notes (R20 gate), stated by the builder "EGM not run".
- Gates on the stack (61ded9e + v5 + yaml + semgrep): ruff check clean; ruff format --check 161 files clean. NOT run: mypy linux/win32, bandit, Windows, Python 3.12 (I used a 3.13 venv, /tmp/work/civenv), a GitHub runner, the full suite, the other pending patches.

## Who must do what
1. Fix Major 1 (narrow the backstop + opt-out + a leak test), re-run test_loader_missing_demo/real_check_dry in a client copy with the loader mutant.
2. Decide Major 2: fix per-test skipping now or accept with the measured number (about 280 of 1228) written in NOTES instead of "all really need the demo".
3. Minors 3-7 in the same pass.

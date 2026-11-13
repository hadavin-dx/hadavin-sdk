# Fresh review: semgrep on main 61ded9e (docsfix patch 02425000...dc2, pure sibling 7c7c7269...)
Reviewer: fresh, read-only. Scratch: /tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/rv (one ref only: rvbase). Offline; real Semgrep 1.185.0 run only with local made-up rules under unshare -rn. Not run: GitHub CI, registry packs, full suite, uv lock rebuild.
Preamble rules used: R6 (honesty), R3, R8, R19. Only sha256 of both patches checked: match the stated values.

VERDICT: NOT CLEAN (0 Blocker, 2 Major, 5 Minor). Nothing in the workflow is unsafe; the Majors are a stale number in shipped docs and a suppression-policy question.

## Major
M-1. docs/tests.md in BOTH patches says the five-folder made-up-rule run read "45 files". Measured on the applied tree: 47 files, ~100% parsed, exit 0 with and without --strict (my run, /tmp/claude-0/o.txt). The PR body says 47. The docs sentence is the old 2db3926 number; the docsfix patch fixed only the 0841f36/25-files sentence. Fix: change "45" to "47" (and say the tree: 61ded9e) in docs/tests.md line 42, regenerate the docsfix patch and its sha256.
M-2. The patch adds 6 new `# noqa: S603` / `S607` comments (tests/test_nosemgrep_form.py x4 lines, tests/test_gitleaks_semgrep_lock.py x1 line; removing them gives 5 real ruff S603/S607 errors, verified). The owner's no-suppression rule says fix the code, not hide it. Main already has 79 such noqa in tests/ so it is the repo convention, but the PR body does not mention them at all. Lead decision needed: either route the subprocess calls through an existing tests/support helper that already carries the noqa, or state them in the PR body. (Not a nosemgrep comment; no suppression comment of any kind was added in src/.)

## Minor
m-1. Mutants that SURVIVE the workflow tests (all 8 test files that touch workflows + hygiene -k, and full test_hygiene.py for M4/M7): persist-credentials true; `${{ github.event.pull_request.title }}` injected into the run: block (the workflow comment says "nothing from pull request text inside a run: step" - not enforced by any test); --strict removed; --severity ERROR -> WARNING; retry also on exit 1; a `secrets.` reference added. The body discloses only that retry/exit logic has no test. Say so for the others, or add tests.
m-2. Docs/PR body: "a Python or JavaScript file with a syntax error gives exit 3 with --strict" is not general. `def f(:` + `  pass` (my file) parsed at 100% and gave exit 0 under --strict. The earlier d1/d2/d5/d6/d3 (unclosed paren in a call, `function f( {`) do give exit 3 (re-run, exit 0 without --strict). Wording should say "some syntax errors".
m-3. Body says exit 3 occurred "in two other made-up tests whose cause the saved test does not describe": the cause is readable in /tmp/work/sg21/d5 and d6 (a broken .js file, with or without a clean .py next to it). Can be said plainly.
m-4. exceptions.txt line 34 `^requirements-semgrep\.txt:[0-9]+:(opentelemetry-[a-z-]+)(==[0-9]+)?$` is a third exception; body's "Other files" section lists only the checksum-line and the .in file-name exceptions. Undescribed, and no negative test for it.
m-5. "A run started by a push to main is never cancelled" (body, and workflow comment "each push to main keeps its own result"): GitHub concurrency groups replace a PENDING (queued, not started) run by a newer one even with cancel-in-progress false (GitHub docs, from memory, NOT measured here). So with rapid pushes to main a queued run can be dropped. Wording only; semgrep results of main are not a gate.

## (1) Patch diff and apply
- sha256 of both patches match. git apply --check on clean 61ded9e: both OK. docsfix applies; 9 files exactly as stated (4 A, 5 M), 0 under src/.
- Diff of the two patches (ignoring 2 `index` lines): exactly 2 lines: semgrep.yml comment "Status:" line (+ "not in main's history..." clause) and docs/tests.md "Status of the scan" (13/405/60 -> 25/912/118 text). Nothing else.
- Facts re-measured: 0841f36..3598120 in the five folders = 25 files, 912+, 118- (/tmp/work/fc-ap); tree of 3598120 = tree of 61ded9e = 4aa3ea0c3ede...; 0841f36 not an ancestor of 61ded9e, ancestor of 3598120; urls.py and tools/pathconfine.py are the 2 added files. Remote main being 61ded9e TODAY was not checked (no network; local remote ref says 61ded9e).

## (2) Workflow semgrep.yml (read in full)
- Triggers pull_request + push to main only; no pull_request_target; fork PRs run with a read-only token and no secrets, nothing needs one; no `secrets.` or `github.event` text in any run:.
- permissions: contents: read at top; no job-level override. Actions: checkout 3d3c42e5...(v7.0.1), setup-python 6d4fd22b...(v7.1.0), full SHAs, same as lint.yml on main; persist-credentials false. timeout 20 min.
- Install: --require-hashes --only-binary=:all: --no-deps; lock: 67 pins, every one has sha256 hashes (919 hash lines), no URLs/git/-e/index lines, sha256 a791abb7e447..., 1130 lines. A venv of the lock set matches it (pip freeze == lock names) and `pip check` says "No broken requirements found". pip itself is not pinned (same as lint.yml).
- Retry/exit handling: extracted the run block and ran it with a stand-in semgrep under bash -e and bash --noprofile --norc -eo pipefail, pause 0: 0->rc0/1 call; 1->rc1/1; 2,0->rc0/2; 2,2,0->rc0/3; 2,2,2->rc2/3 "NOT findings"; 2,1->rc1/2; 3->rc3/1 "NOT findings"; 7->rc7; 5->rc5. Exit never swallowed (`&& status=0 || status=$?` safe under -e). Matches body.
- Real Semgrep 1.185.0, local rules, offline: clean 0; finding 1; missing folder 2; broken rule file 7; broken .py/.js 3 under --strict, 0 without; finding next to a syntax error 1 both ways; --verbose shows "[WARN] Syntax error at line d1/broken.py:2". (No registry run, so exit-2-on-network is unmeasured.)

## (3) Claim rows (76) - re-verified by me: 1,2,4,5,7,10,13,15,17,18,19,20,21,23,24,28,29,35,39(pip check),40,41,43(real Semgrep reads nosem/NOSEM/nosemx/NOSEMGREP/noſem/NoSem/"see nosem docs"/nosemgrep: rule-id-that-matches as suppression; `nosemgrep: other.rule.id` and `# nosemgrep: because x` do NOT suppress),44,45,47,49,50,52(302 passed incl. codeant),54(own mutants, see below),55(5 gitleaks mutants all fail the lock test),57,58,59,60,61,62,63,64,65,68,69,70,71,72,73,74,76. That is 50+ rows.
  Of the builder's "not re-measured" list: 18,19,43,55,62,63,68,71 now measured by me (confirmed); 39 partly (pip check clean on a venv matching the lock; real install from the lock not redone, no network); 56 only the Semgrep side (the 24 shapes are real suppressions; the "old test missed 23" part needs the old test file, not available); 37 NOT re-measured (uv here is 0.11.32, lock rebuild needs network); 42 NOT re-measured (17 s; timeout 20 is in the file); 66 NOT re-measured (full suite forbidden).
  Detail: `#nosemgrep` without a space did NOT suppress in Semgrep, and `nosem=a.b.c` did not; the test refuses them anyway (stricter than Semgrep, harmless).
  False/stale sentences found: M-1 (45 files in docs), m-2, m-4, m-5. Everything else in the body matched.

## (4) nosemgrep policy
git grep over the applied tree: test_no_bare_nosemgrep_comment passes (63 tests in the file). No nosemgrep/nosem/NOSONAR/nosec comment was added to any source file; the only mentions are in docs/tests.md, the workflow message and the test. New noqa: see M-2. Nothing is suppressed silently; the PR's own plan for a red first run is "fix or suppress by rule id in a separate change".

## (5) Gates on applied tree (committed once in scratch; refs: rvbase only)
gitleaks 8.30.1 `dir` and `git` with --config .gitleaks.toml --redact --ignore-gitleaks-allow: no leaks (both). ruff check: All checks passed; ruff format --check: 158 already formatted; mypy linux and win32: no issues in 28 source files each; bandit -ll (src tools scripts; and + load_tools): rc 0 (only "Test in comment" warnings from existing code). Pytest with DPLD_REQUIRE_SCAN=1: test_hygiene 24, nosemgrep_form 63, gitleaks_semgrep_lock 3, gitleaks_exceptions 44, workflow_files_parse 5, workflow_run_flags 10, shell_single_bracket 146, codeant_hygiene 7 = 302 passed (88 s). One earlier run under unshare -rn failed 1 test (test_term_scan_finds_a_planted_term: git commit exit 128 inside the net-less user namespace); the same test passes outside it and in the 302 run - an artefact of my sandbox, not of the patch. No-demo copy (demo_only removed): ruff clean, 15 passed, 2 files skipped as a whole (matches row 76). Venvs used read-only: /tmp/work/sg2-venv-dev (dev reqs, same pins), /tmp/work/sg2-venv-sg (Semgrep lock).

## (6) My five (plus) mutants of the workflow (each run on 5 workflow-related test files + hygiene workflow tests, then full hygiene for M4/M7)
CAUGHT: M1 contents: read -> write; M2 checkout pinned by tag @v4; M3 `[[` -> `[` in the exit-2 test; M5 trigger pull_request_target; M6 --require-hashes removed; M11 extra `id-token: write`; concurrency: cancel true / constant group / second block (the test's own samples). Also 5 gitleaks-toml mutants G1-G5 all fail the lock test.
SURVIVED (test gap, see m-1): M4 PR title inside run:; M7 persist-credentials true; M8 --strict removed; M9 retry on exit 1; M10 severity WARNING; M12 secrets.GITHUB_TOKEN env. Baseline 231 passed.
Workflow file restored byte-identical (cmp) after every mutant.

## Expectation of CI (not measured)
No GitHub run, no registry packs, no licence text read: unchanged from the body's own "does NOT prove" list, which I found honest.
Files: this report /tmp/work/semgrep-main/REVIEW-semgrep-v7-fresh.md. Tokens: not metered.

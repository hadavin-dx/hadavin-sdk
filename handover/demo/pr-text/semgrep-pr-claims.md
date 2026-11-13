# Claims table for semgrep-pr-body.md and semgrep-pr-body-v2.md (rows 1-53 hold for both unless a row says otherwise; v2-only rows 54-63 below)

Paths are relative to /tmp/demo-push/handover/demo/ unless absolute. "Patch" = semgrep/semgrep-on-2db3926-v2.patch (sha256 a5b71be56ceb0d473a176fdba59ad0a22827529baed6721594e38d580c78f1f9, recomputed by the drafter with sha256sum). "Base clone" = /tmp/work/q4-base (clean clone at 2db392650e8b, 0 changes in `git status`). "Drafter" = checked by D-SG in this session; "read" = read in the file, not re-run.

| # | Claim in the body | Evidence file or command | Where verified |
|---|---|---|---|
| 1 | New job `.github/workflows/semgrep.yml`, Semgrep 1.185.0, on PRs to main and pushes to main | Patch, workflow hunk (`on:` block); requirements-semgrep.in `semgrep==1.185.0` | Drafter read the patch |
| 2 | Lock holds 67 packages, 1130 lines | `awk` over the lock hunk of the patch, count of `name==version` lines = 67; hunk header `@@ -0,0 +1,1130 @@`; evidence-sg-17-uv-lock-identical.txt (`1130 committed.txt`) | Drafter ran the count; read the evidence |
| 3 | `pip check` and `semgrep --version` step after install | Patch, workflow step "Check the install" | Drafter read |
| 4 | Scans src scripts load_tools tools n8n with p/python and p/javascript only, severity ERROR | Patch, workflow `semgrep scan` line | Drafter read |
| 5 | Findings in job log only, no code-scanning upload | Patch, docs/tests.md hunk ("no code-scanning upload"); workflow has no upload step | Drafter read |
| 6 | Options --metrics=off, --disable-version-check, --strict and their meaning | Patch, workflow comments | Drafter read |
| 7 | Exit 2 retried up to 3 tries, 20 s apart; exit 1 never retried | Patch, workflow loop and `RETRY_PAUSE_SECONDS: "20"` | Drafter read |
| 8 | tests/ and demo_only/ not scanned, decided without a scan result; reasons | Patch, docs/tests.md "What is scanned, and what is not"; SUMMARY.md N5 and lead decision 5 | Drafter read |
| 9 | n8n nominal: 3 JSON files, no pack reads JSON, Code-node JS not parsed | Patch docs hunk; `ls /tmp/work/q4-base/n8n` = desk-form.json, desk-webhook.json, proof.json | Drafter read + ran ls. "No pack reads JSON" is the docs' statement: not verified by a scan |
| 10 | No WARNING/INFO findings looked at | lead-registry-run.txt "NOT checked: ... WARNING-level findings"; docs hunk | Drafter read |
| 11 | No secrets scan; gitleaks in lint.yml does that | docs/tests.md (base and patch) lists gitleaks in lint.yml; workflow has no secrets step | Drafter read |
| 12 | Unparsable Python file does not fail the job (exit 0 observed with --strict) | Patch workflow comment and docs hunk | NOT VERIFIED: no saved output. Body v1 stated it as fact (fault). Body v2 moves it to "Tests NOT run" as "the patch author reports ..., but no output of that run is saved" |
| 13 | Registry rules fetched at every run, cannot be pinned; results can change | Patch workflow comment | Drafter read (claim from the patch author; "no versioned pack" not verified independently) |
| 14 | v1: "Not a required check unless the owner makes it one"; v2: "intended not to be a required check" | Patch workflow comment "Keep it OUT of the required checks"; SUMMARY.md MAJOR 3 | Read. Actual GitHub branch-protection settings NOT verified (no GitHub calls allowed) |
| 15 | "ERROR-level clean on the stack head at 0841f36 as of the lead's run"; image semgrep/semgrep:1.185.0; exit 0, no finding | semgrep/lead-registry-run.txt | Drafter read |
| 16 | That run lacked --strict and --disable-version-check, other --config order, used --quiet so pack fetch not shown | lead-registry-run.txt (command line and NOT checked); docs hunk "Status of the scan" | Drafter read and compared the two command lines |
| 17 | PR applies on 2db3926; 13 files in scanned folders changed since 0841f36 (405+, 60-); scan not repeated on 2db3926 | `git -C /tmp/work/q4-base diff --stat 0841f36 HEAD -- src scripts load_tools tools n8n` -> "13 files changed, 405 insertions(+), 60 deletions(-)"; 0841f36 is an ancestor (merge-base --is-ancestor). No Semgrep run on 2db3926 in any evidence file | Drafter ran |
| 18 | No GitHub run of the workflow seen; first live CI run is the check; log prints version and packs at start | Patch workflow comment + echo line; docs hunk; SUMMARY-14b NOT run | Read. Absence of a GitHub run: not verified by the drafter (no GitHub calls allowed); stated by every summary |
| 19 | Plan for a red first run: fix or suppress one finding in a separate change | Patch docs hunk "Status of the scan" | Drafter read |
| 20 | Engine LGPL-2.1; rules under Semgrep Rules License v1.0; licence text not fetched or read | Patch workflow header + docs hunk | Read. Licence terms themselves NOT verified (text not fetched) |
| 21 | Owner's written yes covers p/python and p/javascript, this repo only; public log with rule ids/messages accepted under it | SUMMARY.md last line ("Licence yes covers only p/python and p/javascript, see LEAD ANSWER 21:06Z"); brief from the lead | Read in SUMMARY.md and brief. The owner's written yes itself (ORDERS.md LEAD ANSWER 21:06Z) not opened by the drafter: not verified at source |
| 22 | No copy of any rule in the repo | Patch docs hunk ("the files in this repository contain no copy of any rule"); patch adds no rule file (file list: 9 files, none is a rule file) | Drafter read the file list |
| 23 | Group `semgrep-${{ github.ref }}`; cancel only for pull_request; main never cancelled; safe only while github.ref in group | Patch workflow `concurrency:`; REVIEW-5-delta.md (a) | Drafter read |
| 24 | Test `test_semgrep_workflow_never_cancels_a_push_to_main` pins the whole block | REVIEW-5-delta.md RESOLUTION; evidence-sg-19-v2-gates.txt (MUT cancel, MUT group) | Read |
| 25 | pip-compile made the dev locks | `head` of /tmp/work/q4-base/requirements-dev.txt: "autogenerated by pip-compile" | Drafter ran |
| 26 | uv 0.11.32 made the coverage and two browser locks | /tmp/work/q4-base/requirements-coverage.in line 4; versions.md line 55; docs hunk | Drafter grepped. The coverage lock header itself says only "uv" (no version) |
| 27 | Semgrep lock regenerated with uv 0.13.8, cmp byte-identical, sha256 a791abb7e447..., 1130 lines; uv from PyPI under Python 3.13; docker not run | semgrep/evidence-sg-17-uv-lock-identical.txt; requirements-semgrep.in header in the patch | Drafter read |
| 28 | Install command with --require-hashes --only-binary=:all: --no-deps; meaning | Patch workflow install step and comment | Drafter read |
| 29 | Actions pinned to full SHA; persist-credentials: false | Patch workflow `uses:` lines and `with:` | Drafter read |
| 30 | permissions contents: read; no secret, no token, no account | Patch workflow `permissions:` and header comment; no `secrets.` in the hunk | Drafter read |
| 31 | 20-minute timeout is a ceiling; install took 17 s in one test | Patch `timeout-minutes: 20` comment; evidence-sg-1-install.txt "seconds: 17" | Drafter read |
| 32 | test_nosemgrep_form: dotted rule id required; refuses any case, extra letters, long s | Patch test docstring and constants; SUMMARY-14b item 1, SUMMARY-14c items 2-3 | Drafter read |
| 33 | test_gitleaks_semgrep_lock runs real gitleaks, second part widens allowances | Patch test docstring; evidence-sg-14 | Drafter read |
| 34 | .gitleaks.toml and exceptions.txt allowances for hash lines and the .in file name | Patch hunks | Drafter read |
| 35 | .codeant/configuration.json skips the lock | Patch hunk (adds `requirements-semgrep.txt` to the exclude list) | Drafter read |
| 36 | docs/tests.md new "Semgrep" section, contents listed | Patch docs hunk | Drafter read |
| 37 | Hash allowance root-only `^requirements-semgrep\.txt$`; nested copy still reported; tightened from looser pattern | Patch .gitleaks.toml hunk; SUMMARY.md item 4 (old `(^|[/\\])` anchor); SUMMARY-14b | Read. "nested copy is still reported by gitleaks" with the new anchor: no saved run of that exact case on v2 found by the drafter (sg-8b is the hygiene git-grep side on the old anchor): not verified |
| 38 | Base has the `cwd=target` change the toml comment requires | `grep cwd=target /tmp/work/q4-base/tests/test_hygiene.py` -> line 194 | Drafter ran (not stated in the body; supports claim 37 working at 2db3926) |
| 39 | CodeAnt does not check the lock; Dependabot Actions only; owner checks by hand | Patch .codeant hunk; /tmp/work/q4-base/.github/dependabot.yml (only `github-actions`); requirements-semgrep.in "Who bumps" | Drafter read |
| 40 | Lock for Linux x86_64, Python 3.12 only | requirements-semgrep.in header; uv command `--python-platform x86_64-manylinux_2_34 --python-version 3.12` | Drafter read |
| 41 | 125 passed, 4 test files listed, with real gitleaks, on 2db3926 + this patch | evidence-sg-19-v2-gates.txt "125 passed in 64.08s"; file list from APPLY-LIST.md line 90; REVIEW-5-delta.md "S3 gates: 125 tests passed (4 files, gitleaks, scan required)" | Read. The v2 evidence file does not name the 4 files; the names come from APPLY-LIST.md (v1 gates) |
| 42 | Mutants cancel true / constant group: 1 failed, 62 passed each | evidence-sg-19-v2-gates.txt; REVIEW-5-delta.md session-lead confirmation | Read |
| 43 | Gitleaks allowance mutants (4) each fail; on an earlier patch; lock test unchanged since | evidence-sg-14-gitleaks-allowance-tests-and-mutants.txt; REVIEW-5-delta.md (d) same post-image blob for test_gitleaks_semgrep_lock.py | Read |
| 44 | Old suppression test missed 23 of 24 new refused shapes | SUMMARY-14b item 1 (evidence sg-13b) | Read (summary only; evidence-sg-13b not opened) |
| 45 | git apply --check on clean 2db3926: OK; 9 files | `git -C /tmp/work/q4-base apply --check <patch>` -> APPLY_CHECK_OK; `grep '^diff --git'` = 9; also evidence-sg-19-v2-gates.txt "applycheck OK" | Drafter ran |
| 46 | gitleaks dir and git: no leaks; ruff check and format clean | evidence-sg-19-v2-gates.txt ("no leaks found" x2, "All checks passed!", "147 files already formatted") | Read |
| 47 | v1 body: mypy linux and win32 clean "as reported by the builder" (FAULT: the only saved mypy output was for the v1 patch, evidence-sg-19-gates-on-2db3926.txt; none for v2). v2 body: mypy linux and win32 clean on v3 of the patch | semgrep/evidence-sg-20-v3-gates.txt: `mypy --platform linux` and `--platform win32` -> "Success: no issues found in 26 source files" | Read. The evidence file does not itself name the tree it ran on; it is the v3 gates file by its name and the coordinator's message |
| 48 | Exit codes 0,1,2,7 seen locally on a made-up rule | evidence-sg-6-exit-codes-local.txt | Read |
| 49 | Full suite NOT run on this PR; earlier version on 0841f36: 2426 passed, 115 skipped | evidence-sg-10-full-pytest.txt; SUMMARY.md BLOCKER 1 | Read |
| 50 | No GitHub CI, no Windows/PowerShell, no Python 3.13 test runs | Brief; no such evidence file in semgrep/ | Not verified as an absence beyond the evidence folder; the evidence files do not record which Python ran the focused tests |
| 51 | v1: bandit: no clean output saved; v2: bandit not run on this patch version, tool not installed | evidence-sg-19-v2-gates.txt has no bandit output; evidence-sg-19-gates-on-2db3926.txt shows "bandit: command not found" then an unlabelled summary | Drafter read. evidence-sg-19-gates-on-2db3926.txt (v1) and evidence-sg-20-v3-gates.txt (v3) both show "bandit: command not found". APPLY-LIST.md line 90 says "bandit clean" for v1: the saved output does not support that |
| 52 | Local run commands; registry needed; docker not needed; fallback `pip install semgrep==1.185.0` elsewhere | Patch docs hunk "Run it on your own computer"; workflow install line | Read. Not run by the drafter (registry blocked from this sandbox, evidence-sg-3-registry.txt) |
| 53 | Stays its own PR, after #2 to #4 | APPLY-LIST.md line 94 "Still own PR after #2-#4"; brief | Read |

| 54 | v2: PR changes no code under src/ and no core module; adds or changes exactly 9 files (listed) | `grep '^diff --git'` on semgrep-on-2db3926-v3.patch = 9, names match the list; no path under src/ | Drafter ran on v3 |
| 55 | v2: patch is semgrep-on-2db3926-v3.patch, sha256 [V3-SHA256] | Placeholder for the lead. At 01:31 the file had sha256 fdd2393c677aa112a286079185951dad9728d86376b7a2e83677c49d2bfd062c (drafter ran sha256sum); may still change | Drafter ran |
| 56 | v2: v3 applies on a clean 2db3926 | `git -C /tmp/work/q4-base apply --check <v3>` -> V3_APPLY_OK; clone still clean after | Drafter ran |
| 57 | v2: v3 changes only comments and wording against v2 | `diff` v2 vs v3: .gitleaks.toml comment, docs/tests.md two sentences (stack wording, licence yes), requirements-semgrep.in comment (patch-order line), test_gitleaks_semgrep_lock.py comment; plus blob index lines | Drafter ran |
| 58 | v2: owner has said yes to p/python and p/javascript, this repo only | v3 docs hunk "The repository owner has said yes to this use of the registry packs p/python and p/javascript for this repository only"; SUMMARY.md | Read (owner's message itself not opened) |
| 59 | v2: ruff check and format clean on v3 | evidence-sg-20-v3-gates.txt | Read |
| 60 | v2: v3 test and gitleaks results not yet saved; the 125 is for v2 | evidence-sg-20-v3-gates.txt at 01:31 ended at `$ timeout 600 pytest ... tests/test_hygiene.py` with no result; per-file counts absent, so the 4-file list was dropped | Read. If the file is completed, the lead should replace this line with its numbers |
| 61 | v2: Python 3.13 used only for the lock regeneration, not the tests | evidence-sg-17-uv-lock-identical.txt "Python host 3.13.18"; no test evidence names 3.13 | Read. Which Python ran the tests is not recorded |
| 62 | v2: PRs #2-#4 are the code and test stack; they bring tests/ to main where it does not exist yet; Semgrep needs the five folders; the gitleaks exception needs the `cwd=target` change in tests/test_hygiene.py | ORDERS.md line 35 ("tests/ does not exist on main yet", "code stack (#2-#4)"); v3 .in and .gitleaks.toml comments; /tmp/work/q4-base/tests/test_hygiene.py:194 `cwd=target`; evidence-sg-6 (missing folder -> exit 2) | Read and grepped. That `cwd=target` arrived through #2-#4 (not already on main) is inferred from tests/ not being on main: not checked on GitHub |
| 63 | v2: plain-word definitions (severity ERROR, lock tools, group names, ready-made packages, GitHub Actions, gitleaks exception, `.in` mistaken for a web address) | Wording only; facts behind them are rows 4, 23, 25-28, 29, 34 | n/a |

## Points the lead should know (not in the body as claims)

- requirements-semgrep.in in the patch says "Patch order (this stack form): triage/codeant3-gitleaks.patch, then fixes/docs-and-deps.patch (v4), then this patch." At 2db3926 those are presumably already in the base (the `cwd=target` line exists); the sentence may read oddly to a stranger once the PR is opened on main. Not changed (read-only for me).
- The docs hunk says the licence question "is for the repository owner to decide before the job is switched on"; the body says the yes was given. If the owner's yes is final, the docs sentence is now out of date.

## What changed (after the fresh review, Major, no Blocker)

- New body file semgrep-pr-body-v2.md; semgrep-pr-body.md left as it was.
- Rows 12, 14, 47, 51 corrected or marked; rows 54-63 added for the v2 body.
- Body v2: list of the 9 files and "no code under src/, no core module"; v3 patch named with [V3-SHA256]; licence = the owner has said yes; "intended not to be a required check"; the unparsable-file claim moved to Tests NOT run as unsaved; mypy now from the v3 evidence; bandit under Tests NOT run; the 4-file test list dropped (no per-file counts); Python 3.13 = lock regeneration only; plain-word definitions; long sentence split; PRs #2-#4 explained with the `cwd=target` reason. The scan-result sentence is kept word for word.
- Both "points the lead should know" above are fixed in v3 (patch-order line and the licence sentence are gone; checked by diff).

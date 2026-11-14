# Patch status (lane3), written 04:22Z for the lead: one read. Failures and open items first.
Base for all: f3c39cf8 (origin/main of the demo repo, unchanged at 04:21Z).

## Stack conflicts found by a dry run (04:22Z, scratch tree, apply order claims-stack, fix-1 r6, fix-2 r5-on-fix-1-r6, fix-5 r6 INTERIM, fix-8 r3, fix-9 r3, then demo docs 0001, 0002)
| patch | `git apply --check` after the ones before it | cause (files both patches change) |
|---|---|---|
| claims-stack | clean | (first) |
| fix-1 r6 | clean | overlaps claims on README.md, contract.md, docs/limits.md, docs/tests.md, docs/why-this-code.md, but applied clean |
| fix-2 r5 on fix-1 r6 | clean | |
| fix-5 r6 (interim) | CONFLICT: README.md:46 | claims and fix-1 also change README.md; fix-5 also shares tests/conftest.py and tests/test_reset_scripts.py with fix-2 and fix-9 |
| fix-8 r3 | CONFLICT: src/lead_desk/config.py:54 and smtp_provider.py | fix-2 changes the same two code files, plus contract.md and docs/limits.md |
| fix-9 r3 | clean (in that order, without fix-5 applied) | shares tests/conftest.py, tests/support.py, tests/test_reset_scripts.py with fix-5 and fix-2: will conflict once fix-5 is in |
| demo docs 0001 and 0002 | CONFLICT: README.md:55 and docs/tests.md:23 (git am, also with --3way) | claims, fix-1, fix-5, fix-8 change the same lines; 0001 and 0002 also overlap each other (0002 is "v2": probably replaces 0001, lead to confirm) |
Meaning: no complete stack exists yet. Next step: after B12/B13/B11 report, one stack builder re-cuts the conflicting patches onto one tree in order (resolving by hand, keeping each patch's meaning), then full run, browser tests, clean-tree check, and a fresh reviewer on the resolved hunks. The "frozen claims series" I used = claims-stack-on-f3c39cf8.patch (v1 to v2b, v3 ignored as ordered earlier): lead to confirm that is the series meant.

## Per patch
| patch | state | fresh review of the CURRENT version | full run on its own head | NOT DONE / NOT CHECKED | next |
|---|---|---|---|---|---|
| fix-8 r3 (identity.py email rules) | built | r2: 0 blocker, 0 major (review-lane3-fix-8-r2.md); r3 delta review running (a29cd0b9) | r2: running (EV10); r3: subset 98 passed only, stack run covers it | variant on fix-4-r4 only apply-checked; ruff/mypy/bandit not run | reviewer result, then stack |
| fix-9 r2/r3 (data/ folder left by tests) | r3 built by B11 (4 minors), not yet reported | r2: 0 blocker, 0 major, 4 minor (review-lane3-fix-9-r2.md); r3 not reviewed | r2: 3722 passed, 169 skipped, 1 xfailed, rc 0; r3 full run in progress | conftest check not tried with several workers; symlink case and helper race wait for core r7f (not reviewed); helper byte-identical to core not re-compared by a second reader | B11 report, short delta review |
| fix-5 r6 (reset scripts, ports) | building (B12), interim file only | r5: 0 blocker, 2 major, 5 minor (review-lane3-fix-5-r5.md); r6 none | none yet | reset.ps1 and start_all.ps1 never run (no PowerShell here): lead's laptop, WINDOWS-RUN-1.md not yet written | B12 report, review, WINDOWS-RUN-1.md |
| fix-2 r5 (claims about the demo CRM, secrets strip) | building (B13), interim files only | r4: 1 blocker, 1 major, 9 minor (review-lane3-fix-2-r4.md); r5 none | none on the re-cut tree | the blocker "demo CRM claim false" must be re-read against the claims series | B13 report, review |
| fix-1 r6 | final per earlier rounds | earlier rounds reviewed (see REPORT.md) | earlier full runs on other heads | no complete stack tested | stack |
| fix-10 (crash_desk.py raw traceback on bad DESK_NUDGE_TO), lead order 03:59Z | not started | none | none | queued after B10-B13 | start after the stack builder is running |
| fix-3, 4, 6, 7 | earlier rounds closed | see REPORT.md | | not in the stack list of the 03:54Z order: lead to say whether they belong | lead |
Not patches: cloud-core patch is another repo (not in the stack).
Not run anywhere in this lane: Python 3.11, ruff, mypy, bandit, CodeQL, Sonar (CI only).

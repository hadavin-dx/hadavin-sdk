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
LEAD DECISIONS 04:30Z (ORDERS.md): frozen claims series = claims-stack-on-f3c39cf8.patch; demo doc patches 0001/0002/0003 are three drafts of one job, NONE is applied; a single stack-docs-final.patch is cut once on the final stack; stack order: claims, fix-1 r6, fix-2 r5, fix-5 r6, fix-8 r3 (re-cut over fix-2), fix-9 r3 (re-cut over fix-5), stack-docs-final.
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

## NEEDED-CHECK 1 (lead order 04:23Z): what each patch changes and where two change the same job (full tables: evidence/review-lane3-needed-check-1.md; reader's own limits: nothing run, parts of fix-1/fix-2/fix-5 not read)
| patch | job | verdict by reader |
|---|---|---|
| claims | doc caveats + small code fixes | NEEDED; 3 duplicates/contradictions to fix inside it or in the stack (B9 same sentence in limits.md and versions.md, B10 same timeout comment in lint.yml and sonar.yml, B11 README says "/ was not tested" but fix-1 tests it) |
| fix-1 r6 | one meaning per word in the docs + 1067-line docs test | NEEDED with trimming; its exit-code bullets are overwritten by fix-2 (THIN: write once) |
| fix-2 r5 | bad settings stop the start with exit 4 and a named setting | NEEDED; trim repeated long sentences (B1-B3), inline free-port copy (A4), two bind validators (D2), hand-written messages (D3), stale "step (4)" reference (D5); its reflow of fix-1's test file should be folded into fix-1 |
| fix-5 r6 (interim) | reset scripts | logic NEEDED; its conftest `book` fixture DUPLICATES fix-9's helper and would make the fix-9 hook fail every run (A1); port helpers called a separate job by the reader (lead approved them 03:49Z, lead decides); ps1 pid-rule tests WEAK (mostly read script text) |
| fix-8 r3 | email domain rules, one shared check | dedupe NEEDED; look-alike lists and fuzz oracles called speculative by the reader (they came from review findings F8-1..F8-6; lead decides); docs repeat the rule (B7) |
| fix-9 r3 | no data/ left by a test run | hook and helper NEEDED; strict xfail called NOT-NEEDED by the reader (documents a known defect; core r7f owns the fix); fold the "run affected files" inner test |
Lane recommendation (reading, not proof): merge into ONE place: (1) the `book` fixture: one in conftest on book_folder_in_repo (fix-5 + fix-9, A1); (2) exit-code text: contract.md is the only reference, limits.md points to it (fix-1 + fix-2, B1-B4); (3) key-file rule: settings.md only (B2); (4) domain rule: contract (3b) only (B7); (5) the claims sentences B9-B11. Open for the lead: keep or drop fix-5's port helpers, fix-8's look-alike layers and fuzz tests, fix-9's strict xfail.

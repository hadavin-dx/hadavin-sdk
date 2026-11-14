# R7L results (r7l BUILDER): test-only delta on r7j

Date 2026-11-14. Nothing applied or pushed to any repo. Nothing committed to handover/.

## What failed, what is uncertain, what was not checked (first)
1. NO source file changed. `diff -rq tree-R7J/src tree-R7L/src` is empty. So there was no source fix to fail-before on a copy of r7j. All new tests PASS on r7j by design (they pin behaviour that was already right); r7j + new file: 128 passed. Their proof is the mutant kills below, not a red run on r7j.
2. Two mutants SURVIVE, both argued EQUIVALENT (not proven by a test): V03 (`settimeout` inside `_drain` removed) and S13 (`_drain` total-limit check removed). Reason: `_DeadlineReader.readinto` already sets the same wall-clock limit, armed at the top of `_drain`, so removing either line changes no observable behaviour. Re-run on the 10 server test files plus my file: both survive. A control pin (drip client, DRAIN_TOTAL 0.5) covers the shared behaviour. This is my argument, not a reviewer's confirmation.
3. X32 was a BAD mutant (the name it targeted no longer exists in r7j; now `running`). The cap is already pinned by r7j test J02b. I did not re-plant it.
4. X31, X33, X34 were killed by EXISTING tests (r7g, r7j, r7f), not by my file. I added nothing for them.
5. Full suite NOT run (brief says no full suite). Run: r7i + r7l files (128 passed), and the guard tests below.
6. Guard tests (hygiene, nosemgrep form, codeant hygiene, file-call guard, placeholders, demo-folder guard, mutation guards): first run in tree-R7L gave 5 failures, all "not a git repository" (tree has no .git). Re-run in a scratch git copy: 182 passed, 4 skipped (no gitleaks program on PATH; the secret scan itself did NOT run). Other guards (gitleaks exceptions, codeant fakes, no terminal questions) passed in the first run (241 passed, 28 skipped overall in that run, skips = no gitleaks, no git tree).
7. Some mutant result tables (res-*.tsv) hold only the final clean lane runs; Z1-Z13, V06, S4, S11, S12, PX05, X03P, PEK were run in earlier lanes and are reported from those runs (logs in this folder). One overlapped run of two runners on one tree was discarded and re-run; src sha identity of all mutant trees was verified before the clean re-run.
8. The test recipe used: PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, `unshare -n` with the lo_up driver, venv-br python. Not run under any other recipe.

## Files touched (2)
- tests/test_r7l_findings.py (NEW): header table, 34 test functions.
- tests/test_r7i_findings.py (EDITED, F11): i10 outbox, i10 provider, i11 imap use a 5 s budget (was 2 s) and assert `0 < t < 4.5` (was `< 1.5`); docstrings say "(r7l: was 2 s)". 7 lines.
No src/, scripts/, workflow or config file touched. No new suppressions. Fake secrets built from parts. ruff 0.17.1 `check` and `format --check` clean on tests/ (151 files).

## Findings: NEEDED-CHECK table
| Finding | Closed by | Mutants killed by the new file alone |
|---|---|---|
| F1 final reply 2xx only (outbox + provider) | l1, ssl+starttls, codes 354 334 300 399 100 199 421 450 550 554; controls 200 250 299 | X05, PX05 |
| F2 stats right after attempts += 1 | l2 (file read inside fake `_connect`, attempt 1 then 2) | X17 |
| F3 time left per step | l3 (0.5 s budget under 2 s own limit, sockets start at 10 s) | Y1, Y2, X14, X13, X01, X02, Y4 |
| F4 server.py timeouts | l4 busy write, busy drain, body write, finish drain, reader, lingerer | V01, V02, V05, V06, S2, S3, S4, S11, S12 |
| F5 HELO only on 5xx | l5 (421/451/354/450 refused; 5xx control gets HELO) | X03, X03P |
| F6 QUIT cap 0.2 s | inside l3 | X02, X13 |
| F7 EHLO checked before STARTTLS | l7 | X20 |
| F8 weak-cipher words | l8 (seven words written literally, not read from the module) | X21 |
| F9 imap handshake step limit | l9 | X27, X29, X30 |
| F10 login 3xx | l10 (300 334 335 399 421 535 454) | covered by l10 |
| F11 i10/i11 5 s budget | edit in test_r7i_findings.py | n/a |
| F13/provider empty key | l13 ("", " ", "a b", 65 chars) | PEK |
| Guard: fifth secret reader | g4 (planted fifth module made it fail) | n/a |
| X28 | g1 | X28 |
| X31-X34, Y4 | X31/X33/X34 existing tests; X32 bad mutant (J02b); Y4 in F3 | see items 3, 4 |

## Mutants
Reviewer: Y1 Y2 X01 X02 X03 X05 X13 X14 X17 X20 X21 X27 X28 X29 X30 V01 V02 V05 PX05 X03P PEK: all KILLED by test_r7l_findings.py alone. V03: SURVIVED (equivalent). 
Mine (more than the 10 asked): Z1-Z13, V06, S2, S3, S4, S11, S12: all KILLED. S13: SURVIVED (equivalent).
Restore by sha after every mutant; clean-run src sha identity checked.

## Deliverables (this folder)
core-fix-on-frozen-r7l.patch (CRLF), core-fix-on-frozen-r7l-lf.patch, core-fix-r7j-to-r7l-delta.patch (2 files), sha256-r7l.txt, apply-matrix-r7l.txt (git apply --check rc=0 in all three checkouts; delta on r7j gives r7l byte for byte; .ps1 CRLF preserved in the CRLF patch), checkpoint.md.
sha256: see sha256-r7l.txt.

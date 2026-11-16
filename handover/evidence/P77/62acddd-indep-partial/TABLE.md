# PR77 independent evidence, PARTIAL, head 62acdddc01d82c65e06209292c6e9f042aa3f2cd (tree 7c9d97513e034d35400c68559cf126d15efb08d1). Voided by the fix head.
Evidence runner: records only. Stopped on the lead's order.
## Not run / failed / deviated (first)
- NOT RUN: step 3 full pytest on 3.12 stopped by me at about 80 percent (no failure seen in the dots, no final count); 3.13 not run.
- NOT RUN: step 4 (Postgres set on origin/main vs head), step 5 (both mutant runners), hostile timing rerun while the machine was quiet.
- DEVIATION: CI's `uv sync --locked --no-build ...` exits 2 here ("hadavin-sdk editable has no binary distribution"); I synced without --no-build (as the P89 runner did). Logs 01a-*.
- DEVIATION: step 6 plain run on 8b2b716 src: collection error (exit 2), textnorm has no SPACING_CATEGORIES (old name _SPACING_CATEGORIES), so no per-test result. With a test-side alias shim (shim/aliasshim.py, repo untouched): 12 failed, 5 passed (17 tests) = the builder's 12.
- FINDING (step 7 trial, hostile.py, 3.12): whole made-up key AKIAIOSFODNN7EXAMPLE stays in the output when VT (U+000B), FF (U+000C) or NEL (U+0085) sits at position 4 or 10 (whole_leak=1); at position 16 and for ESC at 4/10/16 the key is cut into visible pieces (6 to 94 pieces of 3+ chars). 12 of 39 control-char cases NOT-OK; line-break characters, NUL, DEL, zero-width characters were masked. Not compared with 8b2b716 or main. Log 08-hostile-trial.log.
## Table
| # | command | exit | counts |
|---|---|---|---|
| 0 | HEAD and tree check | 0 | match, worktree clean (00-heads.txt) |
| 1 | uv sync --locked --all-extras --group test (3.12, 3.13) | 0, 0 | - |
| 2a | ruff check src tests demos tools | 0 | All checks passed |
| 2b | ruff format --check | 0 | 325 files formatted |
| 2c | uvx bandit -ll -r src demos tools | 0 | severity High 0, Medium 0, Low 18 |
| 2d | python tools/scan_repo.py | 0 | 8 bytes output (see 05-scan-repo.log) |
| 3 | pytest 3.12 | killed | about 80 percent, no result |
| 6 | fail-before 8b2b716 | 2 plain / 1 shim | plain: collection error; shim: 12 failed 5 passed |
| 7 | hostile trial | 0 | groups ok 6, not ok 1 (control chars, above); 5000 spacing marks one line 0.050 s; 3000 mark lines 0.721 s; 500 key lines 0.271 s (noisy machine, suite running) |
| 8 | gitleaks (out folder copy, no xml) | 0 | per-file hits in 09-gitleaks.log |
Not run at all: 3.14, Windows, PG17, live. No junit xml was produced.

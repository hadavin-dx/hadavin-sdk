# NOTES nodemo-min-v1 (round 1)
Patch /tmp/work/nodemo-min-v2.patch: one new file .github/workflows/nodemo.yml (244 lines) + 4 lines in tests/test_sonar_p2_feed_optional.py (import of conftest.DEMO_PRESENT and a skipif whose reason names demo_only). Based on main 61ded9e; applies with git apply --check on 61ded9e and on PR #12 head 8d65577 (PR #12 touches neither file).

## What the job does
Deletes demo_only/ (git rm), runs ruff, then runs the tests in 9 chunks, one pytest at a time, each with --junitxml. The gate reads only the junit files (never pytest's printed text): exit code 0 per chunk, 0 failures, counts agree with the listed cases, passed+skipped+xfailed equals what --collect-only finds (a skip at the top of a file is handled, so importorskip gives no false "lost tests"), skips naming demo_only are expected, a short allowlist of environment skips (3.13-only ntpath.isreserved, root-or-not) is capped at 6, other skips are capped at 3, passed must be at least 85 percent of collected. A tests/-versus-file-list collect mismatch names the files.

## What it does not prove (gaps, not fixed here)
- One real test file that turns into a placeholder (an `import support` or an `env` argument added) is not seen: both counts barely move (measured GREEN). Dropped with the "files that were real are now placeholders" comparison: it cost about 80 lines (a base-commit worktree and collect in bash, plus about 45 lines of python), not small.
- A module-level importorskip is only one unexplained skip, GREEN up to 3 such files.
- A test that forges the junit file and calls os._exit(0) is GREEN (deliberate only; an accidental early exit is RED).
- Not run on a GitHub runner; actionlint/shellcheck not run.
- The 85 percent floor leaves room for about 58 tests (6 points of 974) to turn into placeholders silently.

## Order of merging (PR #12)
On PR #12 head 8d65577 this job goes RED: tests/test_followup_b.py there imports `from tests.support import ...`, which conftest's placeholder rule does not recognise, so the file runs without demo_only/ and fails. It turns green once PR #12's tests/test_followup_b.py imports `from support import ...`. The nodemo PR must therefore merge AFTER that fix; this patch does not touch test_followup_b.py (PR #12 owns it).

## Which demo flag the feed skip uses
`DEMO_PRESENT` from tests/conftest.py (find_spec("demo_only")): the one flag the conftest placeholder rule and the DPLD_REQUIRE_DEMO guard already use, and tests/test_portal_demo.py already imports from conftest. tests/test_except_clause_hierarchy.py computes its own DEMO_GONE (folder missing on disk) because it must decide at parametrize time for named rows; reusing it would mean importing a test module. The two agree in a client copy (folder deleted).

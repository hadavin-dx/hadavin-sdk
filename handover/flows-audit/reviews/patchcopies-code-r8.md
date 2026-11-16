# Patch-copies round 8 code review (agent afe4a47), uncapped security path
Saved by flows-audit, condensed. Reviewer words unverified. Static: reviewer ran nothing, no git access. 0 Blockers, 2 Majors, 8 Minors.

Not read / not checkable: commit b4cce5b itself (working tree is newest commit; cites checked only via hunk headers and README offsets); handover/promotion-inputs and the three baseline-failure files absent (baseline-failure claims unverifiable here); ci.yml lines at b4cce5b; fix-patchcopies1/5/7, ORDERS.md, BRIEF-PREAMBLE.md; REVIEW.md only partly; test pass counts, 99 guard tests, 41 collected, exit codes.

Verified by reading (reviewer claim): hunk geometry of C-01, price-only, A-01 consistent; C-01 and A-01 touch disjoint files; no src caller of reconcile(); test counts 24/26/6 -> +30/+32; verdict script traced case by case: no path where a bad patched run gets PASSED; Postgres statement forms valid but UNVERIFIED against real store; recipe commands (bandit group scan, ruff, --locked, marker expression) match.

R8-01 Major README.md:29, 188-191, 15, 237 vs ci.yml:89-92, 99-100, 151-153, 84, 185, 94, 178-179: recipe runs pytest under env -i with no HADAVIN_TEST_PG_DSN / HADAVIN_TEST_VAULT_ADDR, so "454 skipped" are probably DB and Vault skips; README does not say so. PASSED = "no new failure among non-DB tests". Line 191 omits CI-only checks (py3.12 job, perf, tools/scan_repo.py, pip-audit, semgrep, stage mutants, gitleaks). A-01 real-Postgres outbox path never exercised (tests use audit._Db.memory()). Fix: say the skips are DB/Vault; name verdict "non-DB gate"; list CI-only checks beside CodeQL/SonarCloud sentence.
R8-02 Major README.md:15, 148, 235, 247 vs DEAD-MAN-CHECK.md:12-16, 94-102: evidence strength inconsistent ("Nothing that needs a database was run" vs "seen once on a throwaway Postgres"); README:247 omits the first-pass audit_outbox oddity. Fix: add "(first pass only, superuser, one made-up table claim unverified)" to README:247.
R8-03 Minor DEAD-MAN-CHECK.md:48, 119: query assumes table in schema public "as the migration creates it"; migration uses current_schema() (migrate.py:172-173, 210). Reword.
R8-04 Minor README.md:114: --no-build omission justified by uv 0.11.32 local observation; CI pins uv 0.13.6; Python not pinned.
R8-05 Minor README.md:155-180: script never checks $W/unpatched is at $SHA with clean tree, nor patched side file list. Add rev-parse and status --porcelain clauses, git diff --stat.
R8-06 Minor README.md:171-175: (d1) compares only "Left contains N more items", (d2) depends on exact AssertionError wording; say so.
R8-07 Minor README.md:57, 193-200, 154: say that at newest commit the two baseline failures may no longer exist.
R8-08 Minor README.md:283-284, 301-305: chain.py:244 DELETE also unguarded; a database outage makes the step red and trips the dead-man check; add to "What it does not cover".
R8-09 Minor README.md:260: add demos/ask-your-data/askdata/fixtures.py:24 (and tests/demo_askdata/test_audit.py:30) prices to config.py mention.
R8-10 (no defect) replay checks == 0 only; Config frozen so no runtime gap.
README and DEAD-MAN-CHECK: no contradiction of substance beyond R8-02 wording.

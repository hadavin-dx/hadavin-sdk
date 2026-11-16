# REPORT v4 (C5 round 2), 2026-11-16
## Failed / not run / uncertain (first)
- Not run: Postgres tests (455 skipped), dead-man query, DB-identity negative test, guard tests on the real repo, any live call.
- Full suite NOT re-run for the deferred A-01, the cut C-01 (one docstring word changed; ruff and dry-run only) or G5 in v4.
- Unknown: whether the take loads `Route` config; if not, the minimal patch has no effect on the take.
- v3 mutants for C-01, A-01 (except A01-10/14/16/17 and SP-01..09), K1B were not re-run on the final tree; first v3 run was on an earlier tree.
- 200_000 ceiling is my typo guard, no provider page looked up. Minimal patch is pilot and prod only; dev unchanged; a local model priced 0 is refused there.
## Finding -> fixed where
design 1 -> `C-01-MINIMAL.patch`; `refused +=` sentence corrected (README Appendix B). design 2 -> README top table, appendices. design 3 / codebase 1 -> 53 distinct ids, command shown. codebase 2 -> README "Mutation count". design 4 -> reworded, plus own 18-of-22 pristine proof. design 5 -> word replaced in new copy. design 6 -> sentence in Appendix A. codebase 3, 4 -> claims removed; `raw/apply-check.txt` for the minimal patch. codebase 5, 6 -> inside deferred/cut text, not edited, noted.
## Evidence (raw/)
pristine: 18 failed 4 passed; patched full suite 9413 passed 455 skipped 0 failed 236 s rc 0; ruff check and format --check clean; bandit -ll rc 0; 8/8 mutants killed; patch and git apply rc 0, files identical.

# REPORT v5 (C5 round 3), 2026-11-16 (UTC; IST = UTC + 5:30), builder report; independent reviewers have not seen it
## Failed / not run / uncertain (first)
- Not run: the 455 Postgres tests (skipped); the dead-man query; any DB-identity negative test; guard tests on the real repository; any live model, cloud or network call; the full suite on the deferred A-01 and cut C-01 patches (unchanged bytes from v4, v3 result in `../v3/raw/`); v3 mutants for C-01, A-01 and K1B on a final tree.
- Unknown: whether the take loads `Route` config. One-line grep is in README. If it does not, apply nothing.
- The 200_000 ceiling is my typo guard, no provider page looked up; it is a hard refusal in pilot and prod on an unverified number (the studio head confirms or gives a dated figure). Decision 4's "ceiling moot" holds only while the minimal patch is not applied.
- Prod tests: prod config still refused for the key-file reason; no prod config loaded end to end. Only 11 of the 19 pristine failures prove the rule missing (not "18 of 22").
- Open siblings NOT fixed (outside decision 4, need the lead's scope go): `registry.py` Budget.daily/monthly and max_run_usd with no above-0 check; `deferred.py:62` only "not None".
- Run slip, fixed: my first full-suite start had 4 cloud-prefixed variables in the shell environment (AWS keys, a CA bundle path, a model base URL). I stopped it, unset them and re-ran; the saved raw is the clean run. Values never printed.
- Behaviour change in replay: negative price now refused; error text changed. `bandit` needed `--with bandit`.
## Finding -> fix map
design M1 -> DEAD-MAN-CHECK.md v5 (four steps, audit gap UNCOVERED). design M2 -> README headline (11 prove the rule, 8 prod fail on key file). codebase M1 -> shared `route_prices_above_zero`, replay rewired, 4 replay tests, M10-M12; open siblings listed in README. codebase nit 2 -> `fake` exemption dropped from config rule (kept in replay, reachable). nit 3 -> dev test asserts values (M8). nit 4 -> M4, M8, M9. nit 5 / design nit 4 -> apply-check re-run, both orders. design nit 1 -> grep line. design nit 2 -> ceiling note. design nit 3 -> mutate script saved. SHA256SUMS -> `sha256sum -c` (raw/sha256-check.txt).
## Evidence (raw/)
pristine 19 failed 4 passed (+4 replay failed); final-tree full suite 9418 passed 455 skipped 0 failed 231 s rc 0; ruff check and format clean, bandit -ll 0 issues; 12 of 12 mutants killed; apply checks rc 0 both orders. Banned-word count over v5 outputs: see final message (counts only).
## Not EGM-reviewed: builder only; independent egm reviewers run next (EGM-GATE v1).

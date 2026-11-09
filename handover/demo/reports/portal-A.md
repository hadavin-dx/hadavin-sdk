# WP-A report (ORDER 205): portal backend, read-only

Working tree: /tmp/dpld-portal (baseline bfb28cf, nothing committed). Patch: handover/demo/portal/patch-portal-A.diff.

## What failed or was not done (first)
- Full pytest on the final tree: 8 failed, 365 passed, 1 skipped (log /tmp/dpld-out/portal-A-full.txt).
  - 5 fail identically on the untouched baseline (checked with git stash): test_flow::test_failed_retry, test_flow::test_retry_twice_concurrent, test_hardening_cloud_b::test_f14_lock_file_unopenable, test_infra::test_demo_adapters, test_mutants::test_mutant_no_claim. Not mine, not fixed (outside my owned lines). The lead should check whether they fail only in this sandbox (running as root, shared machine).
  - test_server_hardening::test_reply_write_fails_after_commit_followup_still_runs: flaky on baseline too (about 5 of 6 runs fail). Not fixed.
  - test_hygiene_scan_public: gitleaks is not installed here, so that part never ran. Must be run in CI.
  - test_hygiene_wordlist: needs HYGIENE_WORDLIST (local-only by design).
- Mutants that SURVIVE or were fixed: `no-query-only` survived (mode=ro alone already blocks writes); I added an assertion `PRAGMA query_only == 1`, and the re-run mutant now fails. `like-unescaped` first did not apply (bad replace string); re-run with `%` escape removed: fails (1 failed, 7 passed).
- Not run: real-process restart x20 (only the in-process x20: bind seconds max=0.0007, mean=0.0005); Windows read-only WAL test (belongs to WP-G); EGM reviews (lead runs them); live model calls (none).

## Evidence
- ruff check, ruff format --check, mypy --platform linux and win32 (17 files each), bandit -ll: all clean on the final tree.
- tests/test_portal_api.py: 68 tests pass. Against old server.py 57 of 68 fail (/tmp/dpld-out/portal-A-fail-before.txt); the Markdown control-character test fails on the old README.
- Mutants killed: no-host-check, no-origin-check, no-sec-fetch, writable-conn, nul-in-q, like-unescaped, no-query-only (after the new assertion), no-csp, two-snapshots.
- Burst test: 10 requests while /api/ui/summary is polled gives no 5xx and every poll reconciles.

## Delivered
portal_api.py (new), server.py routes and Host/Origin/Sec-Fetch-Site gate for every route, loader.py (DemoPortal Protocol, load_demo_portal), config.py (allowed_hosts, DESK_ALLOWED_HOSTS), constants.py, desk.rejected_envelopes, contract.md and README rows, exceptions.txt, tests and 18 fixtures, hygiene tests, the four `Host: x` test lines.

## Decisions
- `now` in summary uses time.time().
- A control character (including NUL) in `q` gives 400 bad_query, because NUL truncated the LIKE pattern and matched everything.
- Demo POST Content-Type check lives in server.py (the Protocol passes no headers).
- loader.py already existed and was extended; build_static is public so tests can build a placeholder index.html.
- Hygiene test (a) also scans portal_api.py.
- exceptions.txt: test-name rule widened from {0,6} to {0,8}; narrow rows for `http://a:b:c/` in test_server_hardening.py and host.docker.internal in README/contract.
- README had 3 form-feed characters (`scripts\feed.py` read as `\f`); fixed, plus a new test for control characters in Markdown.

# patch-portal-A2.diff (WP-A, data feed): full replacement patch, cloud session, 2026-11-09
What it is: `git diff bfb28cf` of the data-feed tree (fix7 = bfb28cf) after fix passes 1 to 5; it REPLACES `patch-portal-A.diff` (apply on a clean fix7 tree, not on top of A). `git apply --check` on a clean bfb28cf worktree: APPLY_OK (4950 lines). `patch-portal-A.diff` is the same content (kept in step; A2 is the name to use).
Includes ORDER 208 (Retry first on both UNKNOWN cards, test_retry_on_unknown_is_409, fixture and contract rows).
Later rounds will come as patch-portal-A3.diff etc. (increments on A2).

## Evidence (honest)
- Last FULL run `/tmp/dpld-out/portal-A7-full.txt` (before the final small edits): 9 failed = the 8 known-red names + `test_big_book_is_fast_and_cheap` (fixed afterwards: one query instead of two). After the fixes: `tests/test_portal_api.py` 169 passed (latest run); hygiene + hardening subset 2 failed (known-red: gitleaks step, word list), 31 passed. The full suite was NOT re-run on the final tree.
- Known-red (also red on the clean baseline, lead-owned): test_flow::test_failed_retry, ::test_retry_twice_concurrent, test_hardening_cloud_b::test_f14_lock_file_unopenable, test_infra::test_demo_adapters, test_mutants::test_mutant_no_claim, test_hygiene::test_hygiene_scan_public, ::test_hygiene_wordlist, test_server_hardening::test_reply_write_fails_after_commit_followup_still_runs.
- ruff check, ruff format --check, mypy (linux) clean on the final tree; bandit -ll run earlier (exit 0) before the last small edits.
- Security review rounds: r1 to r6 in `reports/portal-A-review-*`; round 6 (latest): no Blocker, no Major, 3 Nits.

## Open findings of the running round (round 6, exact)
- Nit A: the card for `person: not sent` picks the CRM text from `crm_done == 0` (inferred). Correct today because only `Desk.resolve` writes it. Safer: resolve writes a distinct last_error. desk.py is lead-owned: your decision.
- Nit B (fixed in A2): synthetic key in the text table.
- Nit C (fixed in A2): raw-seed test and `not in` assertion added.
- No fresh review of the Nit B/C edits (nit-only: fixed without a new round).
- Still open from earlier rounds: header and body reads have only the per-read 30 s socket timeout (a sender of one byte every 29 s holds a thread; no thread cap) - pre-existing, outside WP-A; `finish()` deadline not testable from the client side; contract.md stale items (test count line 3, resolve section and HTTP table lack crm_present / 409 wrong_decision / 400 bad_decision, line 21 about `sending`); `_review` has no statement headroom (budget 6 = used 6).

## Integration with F (see the last section of reports/portal-A.md)
A and F both add six `tests/portal_fixtures/demo-*.json`; three differ (A's copies lack F's `labels`): take F's. `test_no_demo_extension_means_404` is now independent of `demo_only/`.

## Changed files vs bfb28cf (32)
- README.md
- contract.md
- exceptions.txt
- scripts/feed.py
- src/lead_desk/config.py
- src/lead_desk/constants.py
- src/lead_desk/desk.py
- src/lead_desk/loader.py
- src/lead_desk/portal_api.py
- src/lead_desk/server.py
- tests/portal_fixtures/demo-burst-replay.json
- tests/portal_fixtures/demo-burst.json
- tests/portal_fixtures/demo-crash.json
- .../portal_fixtures/demo-state-fakes-offline.json
- tests/portal_fixtures/demo-state-no-crash.json
- tests/portal_fixtures/demo-state.json
- tests/portal_fixtures/error-busy.json
- tests/portal_fixtures/error-envelope.json
- tests/portal_fixtures/error-forbidden.json
- tests/portal_fixtures/error-retry-409.json
- tests/portal_fixtures/lead-detail-not-found.json
- tests/portal_fixtures/lead-detail.json
- tests/portal_fixtures/leads-empty.json
- tests/portal_fixtures/leads.json
- tests/portal_fixtures/review-empty.json
- tests/portal_fixtures/review.json
- tests/portal_fixtures/summary-empty.json
- tests/portal_fixtures/summary.json
- tests/test_hardening.py
- tests/test_hygiene.py
- tests/test_portal_api.py
- tests/test_server_hardening.py

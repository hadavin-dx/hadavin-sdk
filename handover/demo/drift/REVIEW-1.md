# REVIEW-1: egm:egm-codebase-details (sonnet) review of DRIFT-REPORT-1.md and docs-fixes.patch
Saved by the lead session (the reviewer is read-only and could not run commands; it read files and grepped). Head reviewed: 43110e7. Studio R-numbers: not looked up (no studio folder access).

## Result: no Blocker, no Major. Three Nits. Confirmed 3 of 3 doc-wrong items.
- N1 (Nit): DRIFT-REPORT-1 cites leads.js:321-326 for the page sending by_email=0; the real line is src/lead_desk/portal/pages/leads.js:339 (`if (P.privacy.hidden()) p += '&by_email=0';`). Lines 289 and 324 hold the two placeholders. Conclusion right, line number off.
- N2 (Nit): the "BOTH FINE" test-count item (2465 collected on Linux/python3.13 vs 2464 claimed in limits.md:65 for python3.12) is an inference, not evidence. Should read "unexplained +1, consistent with the doc's caveat (documentation and one test file edited after the runs)". Collection can also differ between Python versions.
- N3 (Nit): portal_api.py:376 sets by_email = 1 when the parameter is omitted, so an API caller that omits it still searches names, emails and request numbers. No fix needed; do not read the portal.md fix as an API rule.
- Optional: docs/limits.md:108 also names browser test files and may omit tests/test_stage_confirm_browser.py (the reviewer saw a truncated line): check it.

## Claims
1. docs/portal.md:5 masked search: CONFIRMED doc wrong (code portal_api.py:311-314, 325-328; page sends by_email=0 when masked, leads.js:339; contract.md:122 and tests.md:64 agree with the code). Patch hunk 2 wording matches the code.
2. contract.md:143 timeout_seconds: CONFIRMED doc wrong (desk.py:332-342 refuses not-positive or above MODEL_CALL_BUDGET_SECONDS 9.0 (constants.py:80); equal to 9 accepted; contract.md:40-41, limits.md:52, settings.md:41 already say 9 s). Patch hunk 1 matches.
3. docs/tests.md:27: CONFIRMED doc wrong. 7 test files use Playwright or _browse; only tests/test_stage_confirm_browser.py (9 tests, all via _browse, importorskip at test_mode_safety.py:109) is missing. Patch hunk 3 complete.
4. Test count: NOT PROVEN (see N2).

## Sampled and matching (about 40 statements, none missing drift found; a sample, not a full compare)
settings.md defaults and ranges (config.py, constants.py); SMTP and mail defaults; HubSpot timeout and 429 retries; live-model constants; leadflow bounds; start scripts; run_real_check defaults; reset script exit codes (2,3,5,6 checked; 4 comes from scripts/reset_check.py, not opened); limits (9 s budget, 15 s margin, worker caps, connections, deadlines); exit codes 1,2,4,5; portal strings and REVEAL_MS 30000.

## Not checked by the reviewer
git apply --check of the patch (the lane agent ran it: passed on a scratch copy); re-running collection or tests; Playwright and browser behaviour; n8n or Windows-only text; docs/n8n-recipe.md, real-services.md, hubspot-probe.md, why-this-code.md, versions.md, load_tools/README.md in full; long contract.md lines (36, 68, 113-115, 158, 190, 204-217); reaper backoff 1/2/4/8 s, 30 s stuck grace (desk.py:386), 4192-file arithmetic, crash-point names, schema and workflow files; that quoted test names exist; that /tmp/work/tok.py ran.

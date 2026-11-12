# APPLY LIST (demo fixes), kept up to date by the demo session. Last update 2026-11-12 20:38Z / 02:08 IST
Stack heads (public repo hadavin-dx/duplicate-proof-lead-desk-n8n, verified with git ls-remote at 2026-11-12 20:38Z): pr-1-code d23cf8f, pr-2-demo-folder f31e261, pr-3-tests 558d37f, initial-code 43110e7 (pr-4-extras does not exist on origin).
All patch paths are relative to handover/demo/ on branch demo/handover of hadavin-sdk. 'Reviewed' = a fresh egm:egm-codebase-details review with no Blocker and no Major (review file cited). The apply check of the WHOLE list on the stack heads is run by the integration evidence runner: integration/INT-1.md (running; result below is filled in when it lands).

## BATCH 1: reviewed clean (apply in THIS order; one push)
| # | patch | written against | touches | reviewed (file) | open decision / caveat |
|---|---|---|---|---|---|
| 1 | drift/docs-fixes.patch | 43110e7 | contract.md, docs/portal.md, docs/tests.md (3 one-line fixes; all three still true on 558d37f: checked in fixes/REVIEW-2.md section 4) | drift/REVIEW-1.md (0B/0M/3N) + fixes/REVIEW-2.md section 4 | lane 8's docs patch will be rebased onto it (do NOT also apply the lane 8 patch's copy of these hunks) |
| 2 | triage/js-portal.patch | 43110e7 | src/lead_desk/portal/portal.js, pages/log.js, pages/overview.js, tests/portal_log_probe.js, tests/test_portal_mode.py (5 files; hoisting, window.Portal, loop function, jj/jEnd; new node probe test for the log.js toggle) | triage/REVIEW-js-2.md (0B/0M/4N) | the 504 `var` are NOT converted (D6: later laptop PR); no browser run in the cloud; apply check on 558d37f: see INT-1 |
| 3 | triage/py-retry.patch | 43110e7 | 13 files: src/lead_desk/{desk,crm_hubspot,live_claude,smtp_outbox,smtp_provider,config,portal_api}.py, load_tools/ files, fakes, tests/test_except_clause_hierarchy.py (49 cases), tests/test_lead_crm_copy.py | triage/REVIEW-py-2.md (0B/0M/3N) | the retry-path files are in pr-1-code: the lead decides where to apply the test files (pr-3-tests); apply check on each stack branch: see INT-1 placement table |
| 4 | triage/extra-demo-only.patch | 43110e7 | demo_only/portal_demo.py (1 line: `got[0], got[1], got[2]`) | triage/REVIEW-extra.md (0B/0M/4N) | COSMETIC and optional: a false positive silenced; DeepSource may not flag it at all (rule id unknown): keep or drop |
| 5 | gitleaks/gitleaks-toml-fix-v2.patch | 558d37f | .gitleaks.toml (regexTarget "match" + exact key), exceptions.txt (bracketed exact key) | gitleaks/REVIEW-1.md (v1) and REVIEW-2.md (v2: 0B/1M/3m): the Major is stale merge evidence about the coverage patch, closed by the integration check (INT-1) | FIXES the red gitleaks step (the 558d37f allowlist does not work: proven with the real binary 8.30.1, tarball sha256 = lint.yml pin: gitleaks/evidence-lead-provenance.txt). Apply FIRST or LAST? INT-1 tests both orders. |

## BATCH 2: reviewed but a Major is open, or fix round running (do NOT apply yet)
| # | patch | status | what blocks it |
|---|---|---|---|
| 6 | fixes/docs-and-deps.patch (v2 on disk; v3 being written by lane 8c) | review 2 (fixes/REVIEW-2.md): 0B/3M/8N | Majors: no CSS-level mutation proof; unevidenced doc facts; textual conflicts with lane 7 (8c makes it independent and rebases on #1 and #5); then review 3 |
| 7 | coverage/sonar-coverage.patch (v2 on disk; v3 being written by lane 7c) | review 2 (coverage/REVIEW-2.md): 0B/1M/7N | Major: the single `pip install -r dev -r coverage` rung was not tried (the lock-drift test may become unnecessary); then review 3 |
| 8 | triage/codeant-*.patch | lane 10b running (25 CodeAnt findings) | not produced yet; one fresh review follows |
## NOT PATCHES / decisions for you
- reuse/CORE-TO-DEMO.md (lane 5): a report; owner decisions are in its section 9a. gitleaks hole (a): closed by #5; (b) a detector gap (lowercase 40+ char values after hadavin-dx_-shaped keys are invisible to gitleaks): note in security docs? your call.
- tests/test_no_placeholders.py reads any untracked `.venv-x` / `venv/` folder in the tree (`.gitignore` only lists `.venv/`): coverage/PLAN.md section 9: add `.venv*/` and `venv/` to .gitignore (recommended) or skip dirs with pyvenv.cfg.
- A committed negative test for the gitleaks exception (a different lowercase key must fail hygiene): suggested by gitleaks/REVIEW-2.md, not written (code in the public repo: your call).
- Two unbounded loops in the reaper (src/lead_desk/desk.py:652-655): lane 9 did NOT reproduce the hang in 51 runs; adding a bound is a code change: your call.

## INTEGRATION CHECK status
INT-1 (batch 1 on pr-3-tests 558d37f: placement table, ordered apply, real gitleaks dir+git, hygiene, ruff/mypy, one full serial run): RUNNING (started 2026-11-12 20:38Z). INT-2 (batch 1 + lane 7c + lane 8c) runs when 7c and 8c land.

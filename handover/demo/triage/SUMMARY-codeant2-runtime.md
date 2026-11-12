# SUMMARY codeant2 runtime/test fixes (builder 10c-2 hand-back, saved by the session lead; unreviewed). Base 0841f36 + speed/fake-hubspot-read-body-before-answer.patch (each also applies on 0841f36 alone). Python 3.12.3 Linux only.
Patches: codeant2-desk, codeant2-portal-log, codeant2-demo-only, codeant2-tests-hardening, codeant2-fakes-body (.patch). Evidence: evidence-codeant2-rt-*.txt.
FAILURES AND SURPRISES FIRST
1. The DESK CORE loses the answer on two paths (found by the body-read sweep): POST /leads/<id>/step over the size cap (413) and an unknown method (501) answered without draining the body; a client sending the body late got a reset 5 of 5; after the fix 0 of 5. Fix: src/lead_desk/server.py about 6 lines (in codeant2-fakes-body.patch). On Linux the reset does not destroy the reply, so tests measure the reset (the cause of the Windows loss). Malformed Content-Length with a body: not fixed (length unknown). NOTE FOR LEAD: this touches core code.
2. The lead's speed patch new test fails `ruff check` E501 (tests/test_crm_hubspot.py:231, 121 chars); CI runs `ruff check .`.
3. Full serial suite on 0841f36 + speed + five patches (tracked scratch commit): 2 failed, 2579 passed, 2 skipped, 1070 s. Both failures: sidebar test with `ModuleNotFoundError: PIL` (Pillow not in its venv; lane 8 replaced Pillow by in-browser decode); not run with Pillow, not run without the patches for comparison.
4. fixes/docs-and-deps.patch does not apply to 0841f36 per this builder (.gitleaks.toml:52): CONTRADICTS lane 8 evidence-d6 (v4 applies on 0841f36): to be re-checked at integration. On 0841f36 alone apply the speed patch before codeant2-demo-only; fake_hubspot.py hunks use one line of context.
5. gitleaks dir/git 0 findings with every file tracked; `st.page(` was read as a hostname -> method renamed `contacts_page`; the `s:\n` drive-path finding in tests/test_codeant_hygiene.py fixed.
6. A stray `:memory:.lock` file appears before the `:memory:` refusal (lock step runs before the desk is built).
7. Open design point: a mirror lead refused because its own abandoned call is still running waits (10 s and up) and is not charged a try; it never reaches MIRROR_MAX_TRIES by itself if the hang lasts.
8. N4-01..03 new cases covered by full and focused run but not run against old code; eslint not run on log.js (only node --check).
DONE
- B-M1 mirror: AdapterBusy distinguishes the two causes under _worker_lock; same-lead refusal = per-lead wait + continue; worker cap still returns; two-lead test; mutants (bare return; no exclusive; continue without wait) fail.
- B-M2/C-N3 fake_hubspot: one locked public view (public, contacts_page, search, patch); spy test fails for each with lock removed; barrier tests for take_failure/take_hang; 16-thread test sets setswitchinterval.
- log.js: condition `(extra.length || loading)`, cursor kept while loading; new in-flight test fails on old patch and on 0841f36.
- fake_model_server: Infinity, NaN, 10**400, >86400, non-dict/non-JSON -> 400; `--n 0` burst exit 0 `RESULT sent=0 expected=0` (3.12 only).
- Core touch for PR text: `set_bound_address` is now a second Protocol `KnowsBoundAddress` in loader.py, isinstance in server.py (second core touch).
- `:memory:`: dead `""` branch and duplicate test case removed; contract.md:143, :277, limits.md:52, settings.md:7 updated in the same patch (contract.md is core doc). Remaining :memory: branches (db.py:75, gate.py:187-190, portal_api.py:161 comment) left.
- Siblings fixed: test_reset_scripts, test_mode_safety:333, sleep(0.1) in test_followup_edge_cases (:70, :100, :103).
- CA-11 -> STYLE; counts REAL 21, STYLE 21, FALSE POSITIVE 3, INTENTIONAL 2.
- Focused run (hygiene WITH gitleaks, new tests, touched files, test_lead_crm_copy, test_crm_hubspot): 1025 passed in 326 s.
- Apply matrix: its five patches + 10c-1's four apply alone and in sequence on both bases; same-file pairs (test_hygiene.py, settings.md, limits.md, server.py) apply in both orders; O1 fails alone on both bases (.gitleaks.toml:52); coverage patch fails because already in base.

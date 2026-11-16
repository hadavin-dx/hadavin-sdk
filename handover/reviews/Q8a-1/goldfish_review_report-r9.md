Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 9)

**Target:** branch `wip/cloud-q8a1-b9`, head `f0febfb6` (base `18741c8c`). Security path, no round cap. No person available: recommended option for every item. Reviews (read-only, by reading only): `q8a1b9-design-r9.md` (0 Blocker, 2 Minor, 3 Nit) and `q8a1b9-codebase-r9.md` (0 Blocker, 1 Major, 2 Minor, 3 Nit). Independent evidence (head confirmed, tree clean): `handover/evidence/Q8a-1/f0febfb6/RESULTS.md`: full pytest 11041 passed, 1 skipped; stage_mutants 175 of 175; ruff, format, bandit, scan_repo, gitleaks exit 0; fail-before vs 18741c8c 38 failed, 1 of 13 new test functions passes on old code; vs main 299 failed, 5 of 116 pass on main code (listed); own 83-scenario probe found the planted text in 2 places, both from the runner's own artificial subclass, none in product code; known timing test fails 3 of 3 alone on head and main. Not run: security job steps, perf, live Vault. Reviews were by reading only and are not confirmed by a run.

## Prioritized findings
| # | Source | Sev | Verdict | Edit |
|---|---|---|---|---|
| 1 | codebase C1 | Major | PROPOSE FIX | `sources/kubernetes.py:112,119,121,124,126,343,349,351` print configured namespace entries. Fix at the choke point: no message prints a configured namespace entry (print the count or "a configured namespace"); add `namespace` and `ns` to the guard lists; add a row per print site and a mutant that restores one print; run the probe on a namespace that holds a planted marker |
| 2 | design D2 | Minor | PROPOSE FIX | Mutant M18o is killed by the wrong assertion: give it its own specific assertion and expect fragment, show it fails for its reason |
| 3 | codebase C3 | Minor | PROPOSE FIX | Replace the generic expect fragments of M18g, M18n, M18o, M19g with fragments specific to each message; merge M17u/M19e or give each a distinct expect |
| 4 | codebase C2 (part) | Minor | PROPOSE FIX | Correct the wrong `_HOST` allowance reason text |
| 5 | codebase C2 (rest), design D1 | Minor | ESCALATE (open owner question) | Module, host, operation and source names remain printed: defining ids vs hiding is `q-q8a1-hide-ids` (still open, lead's decision). Safe default: keep printing defining ids. Not changed in this round |
| 6 | evidence | Minor | PROPOSE FIX | One line per test that passes on old code (6 of them: reason or mutant that kills it): `test_the_guard_finds_each_way_of_printing_a_configured_name_and_a_stale_allowance` (vs 18741c8c and main), and the four others listed in RESULTS.md plus the mixed parametrised one |
| 7 | design D3-D5, codebase C4-C6 | Nit | PROPOSE FIX where the edit is one line or wording; otherwise DECLINE with a stated reason in the builder's notes | The b10 builder lists each Nit with its action; none is dropped silently |

## Handoff counts
Accepted (PROPOSE FIX): 6 groups (items 1-4, 6, 7). Escalated: 1 (item 5, `q-q8a1-hide-ids` stays open). Declined: 0 recorded here (Nits resolved by the builder with a reason each). Contested: 0. Next: a fix builder b10 from `f0febfb6` (own worktree, push `wip/cloud-q8a1-b10`), then snapshot, evidence runner, two fresh reviewers (round 10). Ledger: C1 Major OPEN until the fix is verified by a probe of the planted namespace marker on the fixed head.

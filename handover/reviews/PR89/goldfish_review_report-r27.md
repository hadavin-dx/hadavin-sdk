Status: resolved

# Goldfish Annotated Review Report (PR89, round 27)

**Target:** branch `wip/cloud-PR89-r27`, head `cc1f6228` (mutation runner hardening). Non-security tooling path: round 27 is limited to Blockers and Majors; Nits are fixed in the same push with no new review. No person available: recommended option for every item. Reviews (by reading only, nothing run): `handover/reviews/PR89/pr89r27-design.md` (0 Blocker, 0 Major, 3 Nit) and `pr89r27-codebase.md` (1 Major, 2 Nit). Independent evidence: `handover/evidence/PR89/cc1f6228/RESULTS.md` (head confirmed, tree clean): full pytest 10832 passed, 3 skipped (the first run failed only from the runner's own Postgres setup slip, logged); mutant list 329 of 329 as root and as user nobody (closes the round-26 Issue 1 gap); stage_mutants 37 of 37; ruff, format, bandit, scan_repo, gitleaks exit 0; mypy 14 errors on 3.12 and 3.13; 3 of 6 new tests fail on old code, 3 pass on old code; hostile probes refused (root only). Not run: timing test, perf, Windows, macOS, semgrep, zizmor, trivy, pip-audit, hostile inputs through the full `run_mutants` call.

## Prioritized findings
| # | Source | Sev | Verdict | Edit |
|---|---|---|---|---|
| 1 | codebase R27-1 | Major | PROPOSE FIX | The prose says the killer "a link out of the tree is accepted" can skip; it is unreachable on every system. Correct the prose in the header and the CHANGELOG; add one cheap assertion that the killer lists the name in neither skip list and that the prose does not name it as skipping |
| 2 | codebase R27-2 | Nit | PROPOSE FIX | Resolve the header contradiction about the OS-branch mutants (one sentence) |
| 3 | codebase R27-3, design N3 | Nit | PROPOSE FIX | Replace "12 errors" with 14 (13 POSIX-only names plus 1 missing stub, measured by the independent run on 3.12 and 3.13); replace "5 re-pointed" with the real number and list; add a round-27 paragraph |
| 4 | design N1 | Nit | PROPOSE FIX | State that the non-root and mypy claims were measured by the independent run at head `cc1f6228` (root and user nobody; mypy 2.4.1 in a throwaway venv, not in the lock), not by a repo test |
| 5 | design N2 | Nit | DECLINE | The `_narrowable` clauses lacking mutants is a coverage preference; the clauses are exercised by the existing tests. Recorded; revisit only if a later round finds a behaviour gap |
| 6 | evidence | Minor | PROPOSE FIX | One line each for the 3 tests that pass on old code, in `handover/evidence/PR89/r27/NOTES.md`: the mypy-count-is-not-in-CI test (control: checks the workflow and lock file as they stand, true before and after); the every-decorator-is-read test (needs a mutant that restores the short-circuit, or a stated control reason); the header-names-killers test (needs a mutant that drops a name from the header, or a stated control reason). Add the missing mutants if cheap |

## Handoff counts
Accepted (PROPOSE FIX): 5. Declined: 1 (design N2). Contested: 0. Escalated: 0. Next: one fix builder pushes all in one push (no new review for Nits); the Major prose fix is checked by the next independent run. Ledger: round-26 Issue 1 closes FIXED-VERIFIED on the non-root run (329 of 329 as nobody, `evidence/PR89/cc1f6228`); round-26 Issue 2 closes with the corrected CHANGELOG; R27-1 OPEN until the builder fix is run.

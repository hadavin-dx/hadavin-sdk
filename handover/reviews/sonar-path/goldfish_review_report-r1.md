Status: resolved

# Goldfish Annotated Review Report (resolve, round 1)

**Target:** `handover/design/sonar-path-traversal-design.md` (full file), ORDER 260, SECURITY path. Sources: `design-r1.md` (2 Blocker, 7 Major, 5 Nit) and `readiness-r1.md` (3 Blocker, 7 Major, 4 Nit). Static reviews; nothing was run. The design note was rewritten as version 2 (all PROPOSE FIX applied in one batch).

## Findings grouped by class
| Group | Class | Findings | Decision |
|---|---|---|---|
| 1 | call shape and API contract does not fit the callers | design B1; readiness B1, M1, M4 | PROPOSE FIX: `join(base, *names)` for new code, `inside(base, path)` for already-joined paths, `operator_dir/file`; call-site table; `atomic_write(base, name, text)` |
| 2 | incomplete sink coverage and sibling inventory | design M2, M1(callers of config.confined); readiness M4 (sinks), N2 | PROPOSE FIX: sink table with origin per line (operator-typed / data-derived / fixed); builder grep; hit without a row blocks the PR |
| 3 | rule grammar not precise | design M4, M5; readiness M2, M3, M5 | PROPOSE FIX: rule table R1-R11 with exact tests and texts; numbers; pinned phrases kept ("escapes" in config.confined, "outside" in key_path); errors OSError/RuntimeError/ValueError |
| 4 | proof gaps (tests that cannot fail on old code, tripwire, mutants) | design nits N3, N4; readiness B2 (part), B3, M7, N3 | B2 "mutation wiring does not exist": CONTEST in part (the reviewer read the core/cloud-handover checkout; `git ls-tree origin/main` shows tools/mutation_runner.py and three tests/*mutants files); ACCEPT the part asking for a named base commit and a mutant contract. Rest PROPOSE FIX: behaviour tests through callers on main, mutants for pathguard-direct tests, labels REGRESSION vs FAIL-BEFORE, filesystem-effect property test, banned-call AST tripwire with seeded fixtures |
| 5 | Sonar acceptance and honest claim | design B2, M6; readiness M5, M4 (NOSONAR) | PROPOSE FIX: no local Sonar; the PR claims only what is true; NOSONAR removed per the order; lead checks SonarQube and accepts what remains in the UI; the words "SonarCloud is fixed" are forbidden in the PR body |
| 6 | race threat model and atomic_write details | design M3; readiness M6, N1 | PROPOSE FIX: threat model stated (text, not a concurrent writer); O_NOFOLLOW/O_EXCL where available, no dir_fd claim; keep text handling; unlink temp on BaseException; random via secrets.token_hex; `.tmp` suffix kept; key_path order kept |
| 7 | rung table missing | design M7 | PROPOSE FIX: table added (verdicts UNVERIFIED where the builder must check pyproject) |
Nits: design N1, N2 (accepted into section 5), N3, N4, N5 (stub update listed), readiness N1-N4 all PROPOSE FIX (small); nothing DECLINED except that `component` length numbers use UTF-8 bytes (a choice, stated).

## Lead decisions that overrode a reviewer wording
- Device-name and trailing-dot rules apply on every OS but only to data-derived components and the final written name, not to every old `config.confined` call (design M1 asked to decide; decided and argued in 3.2/3.4).
- The reviewers' option of `dir_fd` is not taken; the threat model is stated instead (design M3 allowed either).

## Not verified
Sonar behaviour (reviewer's account is from memory); Windows behaviour; the full list of sinks (the builder completes it); other `config.confined` callers' test inputs (the full suite will show).

## Handoff
Accepted fixes: 19 (2 Blocker-groups merged: call shape, Sonar claim; 11 Major; 6 Nit). Contested: 1 part (readiness B2 "mutation wiring missing", evidence: origin/main tree). Escalated: 0. Declined: 0. Remaining unaddressed: 0 in the note; items for the builder to complete are named in section 4 and section 7. All ledger rows OPEN until the ONE fresh confirming round after the rewrite (security path, repeat until a fresh round finds nothing real).

## Who fixes it
The design rewrite is done (this resolve). One builder then builds on `core/sonar-path-traversal` from main (push `wip/cloud-sonar-path`), then an EVIDENCE RUNNER, then two fresh egm reviewers on a snapshot, then resolve, then the drift report.

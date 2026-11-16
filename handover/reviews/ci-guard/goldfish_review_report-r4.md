Status: resolved

# Goldfish Annotated Review Report (round 4)

**Target:** `/home/user/build/snap/ciguard-0121aaa0/DIFF.patch` (full file), head 0121aaa0, ORDER 266, SECURITY path.
**Inputs:** `ciguard-0121aaa0-design-r4.md` (0 Blocker, 1 conditional Major, 3 Minor, 2 Nit) and `ciguard-0121aaa0-codebase-r4.md` (0 Blocker, 0 Major, minors M1-M3, 3 Nits). Resolved in automated mode, recommended option for each item.

## Verdict first
- Round 4 has **0 Blocker and 0 unsettled Major**. The one conditional Major (design N1) is a request to dry-run on real refs; it is settled with evidence (below). This is the clean round that ORDER 256 asks for on a security path (round 3 had Majors).
- **Open until the independent runner reports:** the live-ref run at head 0121aaa0 (runner ab4ff113, item 5) must exit 0 with 0 handover files in the new range. If it does not, N1 re-opens as a real Major.
- What this report does NOT settle: the ruleset, tag-creation limit and CODEOWNERS remain owner-only (exception 2(b)); nothing in this batch claims to close them.

## Issue 1 [design N1, conditional Major] every PR fails if another ref or tag carries a handover note - CONTEST (settled with evidence, standing risk documented)
- **Evidence the reviewer could not see, recorded in the repo:** lead dry-run 2026-11-12 ~22:08Z on live refs: `origin/handover-src/c1a-8460813` and `origin/core/P2d-1` each 0 handover files since origin/main (`git log -m --name-only -z`); origin/main history 0; the remote has no tags (`git ls-remote --tags origin` empty; four tags exist only in the lead's local clone); independent runner at b8ea4f69 ran the step on live refs, exit 0, 142 lane refs, new range 0 files, old range 611 (`handover/evidence/ci-guard/b8ea4f69/RESULTS.md`, item 6l). Main's `.gitleaks.toml` has 4 `targetRules|handover/` matches, so the base step already ran the path checks on main.
- **Category:** CONTEST (the reviewer asked for a dry run; it was done). Because the reviewer's files did not include that evidence, the settlement stands on the runner's run at the final head (see "Open" above).
- **Standing risk, already disclosed in ci.yml comments:** a writer who pushes any non-lane ref with a handover note fails every PR (denial of service, not a bypass). The failure message names the refs and paths (tests exist). Control = ruleset (owner-only, ledger CIGUARD-r3-2).

## Issue 2 [design N2, Minor] guard pattern not tied to the real allowlist path regex - PROPOSE FIX (batch)
- Fact: main's `.gitleaks.toml` allowlists `^handover/(reviews|tickets|evidence)/[^/]+\.md$`; the guard greps the wider `^handover/(reviews|tickets|evidence)/`. The guard is broader than the allowlist, which is the safe direction, but nothing pins it.
- **FIX BRIEF:** file `tests/test_ci_guard_wip_lanes.py`. Add a test that reads the repo's real `.gitleaks.toml` (the file next to the repo root, not a constant), finds every allowlist `paths` regex that mentions `handover/`, and asserts that each sample path it accepts (build samples from its literal prefix plus `x.md`) also matches the guard pattern extracted from the real ci.yml step. Mutant: widen the toml regex (drop the `^`) in a copy; the test must fail. Fail-before: the test fails against a toml copy with `docs/handover/` allowed. Batch only.

## Issue 3 [design N3, Minor] toggle `targetRules|handover/` matches unrelated allowlists - PROPOSE FIX (comment only)
- Main's `.gitleaks.toml` has 4 matches, some for unrelated allowlists, so the message "outlived branch core/cloud-handover" can be wrong. Old behaviour.
- **FIX BRIEF:** `.github/workflows/ci.yml` comment next to the toggle (about line 225-233): one sentence that the toggle also fires for unrelated allowlists and that the message names the pattern, not the owner of the allowlist. If the message text itself says "outlived", reword to "a handover allowlist is present and branch core/cloud-handover is missing". Test: assert the new wording in the existing message test; fail-before: old wording. No mutant (wording).

## Issue 4 [design N4, Minor] a writer-created `wip/cloud-*` ref hides its commits; any other ref with a note fails every PR - DECLINE (accepted, documented, owner-only control)
- Already disclosed in comments; HEAD's own history is re-checked with nothing subtracted; the ruleset on `wip/cloud-*` is the control. Ledger CIGUARD-r3-2 / r3-5 stay OWNER-ONLY / OPEN. A code change would need a trusted list of lane names the step cannot know.

## Issue 5 [design N5, N6 nits] step name lacks own-history rule; `sed` missing from the system-tools list - PROPOSE FIX for N6, DECLINE N5
- N6: file `.github/workflows/ci.yml` (step "System tools resolve outside the workspace", about line 175): add `sed` to the listed tools. Test: extend the existing golden check (regenerate `tests/fixtures/ci_security_golden.json`). Mutant: remove `sed` from the list; the tools test must fail. Fail-before: golden mismatch.
- N5: DECLINE. Renaming the step changes the check name that a branch-protection rule may reference and buys only wording; the comments carry the rules.

## Issue 6 [codebase M1, Minor] show_where trims whitespace and uses a glob pathspec - PROPOSE FIX (batch)
- **FIX BRIEF:** `.github/workflows/ci.yml` lines 246-249: `IFS= read -r p` and `-- ":(literal)$p"`. Test: a file name with a leading space and a `*` in the name that was added only by a merge; the message must list the remote branch. Mutant: restore `read -r p` or the plain `-- "$p"`; the test fails. Fail-before: the old step prints "no remote branch". Message-only path; the step's pass/fail result is not affected.

## Issue 7 [codebase M2, Minor] surviving mutants - PROPOSE FIX (batch, tests only)
One test and one mutant each, all in `tests/test_ci_guard_wip_lanes.py`, fail-before = the mutant itself:
1. `grep -qxF` at ci.yml:217: drop `-x`: entry ending `:3` against main line ending `:33` must fail; drop `-F`: an entry whose path has a regex dot against a main line with another character at that place must fail.
2. `-z` at :252/:268/:272: a note whose file name has non-ASCII or a quote character must be listed by the range check.
3. `--all` at :265: a note only on a tag (tag created in the throwaway repo) must fail the HEAD-history-or-range check.
4. Anchor at :214: a branch named `core/P2d-1-x` carrying an entry must be refused; add the positive case `handover-src/c1a-8460813` (entry for a commit on that name, not an ancestor of HEAD) accepted.
5. `git show origin/main` short name at :210: with a tag `origin/main` pointing elsewhere, the main-ignore content must come from the branch (the entry accepted only if on the branch).

## Issue 8 [codebase M3, Minor] golden compared by eye - PROPOSE FIX (gate)
- The builder and the independent runner regenerate the golden with `tests/test_ci_gitleaks_scope.py` and confirm an empty diff, and run that test file (the reviewer could not read it in the snapshot). Record the regenerate-empty-diff output in the evidence. No code change.

## Issue 9 [codebase nits] - PROPOSE FIX for two, DECLINE one
- `a_lane_ref_pointing_at_another_branchs_commits`: add a comment on the test saying it pins the documented weakness; a future hardening must change it on purpose. PROPOSE FIX (comment).
- Step-name test: also assert no trailing `:`. PROPOSE FIX (one line, mutant: add a trailing colon).
- `test_the_old_allowlist_wording_is_gone` pins phrases: DECLINE (the pin is the point; the message wording is a user-visible contract and an over-claim guard).

## Stop rule (ORDER 256) and next steps
- Round 4 is clean on Blocker and Major (Issue 1 settled by evidence, pending the runner at this head). Security path: this is the clean round after round 3's Majors, so **no fifth full review round**. The fixes above are tests, comments and one message-only line; none changes which commits the step accepts or refuses, so a confirming review of the logic is not needed.
- One push for all minors. After it: the independent runner re-runs only the delta: the two guard test files, regenerate-golden empty diff, the nine mutants plus the new ones (each killed), ruff, bandit, zizmor, gitleaks, and ONE full suite at the final head; plus the live-ref step run at the final head. The lead gets "guard clean" only when that evidence is green on the pushed head.
- If the runner at 0121aaa0 finds the live-ref step failing, Issue 1 re-opens as a real Major and this report is superseded.

## Handoff
Accepted fixes (PROPOSE FIX): 6 (Issues 2, 3, 6, 7, 8, 9 parts) plus N6 in Issue 5 = 7 batch items. Contested: 1 (Issue 1, settled with evidence, conditional on the runner). Escalated: 0 new (ruleset, tag limit, CODEOWNERS stay open from round 3). Declined: 3 (Issue 4 accepted risk, N5 step name, phrase-pin nit). Remaining unaddressed: none in code; 1 evidence condition (live-ref run at this head); owner-only items unchanged.

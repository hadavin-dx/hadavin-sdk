# Claims patch stack rebased onto f3c39cf8 (agent H)

## Failures and uncertainties first
- No conflicts: no hunk failed. No --3way/--recount/--whitespace option was needed, so no hunk was hand-resolved and no claim text was changed.
- NOT checked: whether each patch's claim text is still TRUE on the code of f3c39cf8 (PR #14 changed tools/pathconfine.py, scrub_n8n_export.py, n8n_api.py, load_tools/*, fake_model_server.py, urls.py, docs). The patches touch none of those files, so git saw no overlap, but a claim could still be false after PR #14. A reviewer must check the claims against main.
- No tests or lint run (agent I does that).
- BRIEF-PREAMBLE.md read; backslash studio files (bible, memory, egm folders) are not in this checkout.
- The per-patch "check on the second worktree" was done only for the combined patch (a per-patch check there is meaningless after the stack is applied).

## Per patch (plain `git apply --check` then `git apply`, in /home/user/work/h-stack, base f3c39cf8)
1. claims-fix-v1.patch: clean, plain
2. claims-code-fix-v1.patch: clean, plain
3. claims-fix-v1b.patch: clean, plain
4. claims-fix-v2.patch: clean, plain
5. claims-fix-v2b.patch: clean, plain
(claims-fix-v3.patch ignored as instructed.)

## Conflicts
None.

## Result
- Combined patch: handover/demo3/evidence/claims-stack-on-f3c39cf8.patch
- `git apply --check` on a second fresh worktree of f3c39cf8 (/home/user/work/h-check): rc=0
- SHA256: 7138e884333d4bd0f9d377873fe05aae5f1dfce275758952d2b6e4f05d89194c
- Diffstat (also in raw/claims-stack-diffstat.txt): 16 files changed, 66 insertions, 60 deletions

Files: .github/workflows/lint.yml, semgrep.yml, sonar.yml; README.md; SECURITY.md; contract.md; docs/limits.md, portal.md, settings.md, tests.md, why-this-code.md; scripts/hubspot_probe.py, start_all.ps1; src/lead_desk/loader.py; tests/test_input_edge_cases.py; versions.md
(Note: h-check worktree now has the stack applied for the check; h-stack and h-check are private worktrees left in place.)

# ciguard-0121aaa0-codebase-r4: CI guard, head 0121aaa0, round 4, persona codebase details

Source: hand-back of the codebase reviewer (agent ab71ee91), saved by the lead (condensed). SECURITY path. Read-only, nothing run. Verdict: 0 Blocker, 0 Major. Shell step (ci.yml 188-275) technically sound: bash -e semantics, anc() return codes (0/1/128) and fail persistence, cat-file and branch -r guards, full refs/remotes spelling, `HEAD --all --not <refs> --`, -z and -m history reads, YAML-safe step name. Own-history rule holds for the synthetic merge HEAD; the remaining bypass (forged fixed-name ref outside HEAD history) hides nothing from a HEAD-only gitleaks scan; the ruleset is the control.

## Minor
- M1 ci.yml:246-249 show_where: `read -r p` without IFS= trims whitespace and `-- "$p"` is a glob pathspec, so a merge-only addition can be simplified away; cosmetic ("no remote branch" in a message after the step already failed). Use IFS= and :(literal).
- M2 Surviving mutants (each needs a test): dropping -x or -F from `grep -qxF` at :217 (test ':3' entry against ':33' main line, and a path prefix); dropping -z at :252/:268/:272 (test a non-ASCII or quoted file name); `--all` replaced by `--branches --remotes` at :265 (test a note on a tag); handover-src/c1a-8460813 never a positive case and the `$` anchor at :214 unexercised (name like core/P2d-1-x); `git show origin/main` short name at :210.
- M3 Golden JSON compared by eye only; rely on check_golden or regenerate and confirm empty diff. The reviewer read test_ci_gitleaks_scope.py from another checkout (could not read it in the snapshot).

## Nits
Test `a_lane_ref_pointing_at_another_branchs_commits` pins a known weakness as rc 0 (future hardening must change it); `test_the_old_allowlist_wording_is_gone` pins phrases (brittle); step-name test passes on the old step too and does not check a trailing ':'.

## Could not check
tests importable as a package; ruff on long lines in the test file; stray bytes from `-z --format=`; `git branch -r` short names with a same-named tag; scan_repo or Semgrep on new text.

# A24 PR91 fix batch 3 builder report

NOT DONE / NOT CHECKED (first):
- Full suite finished after the first hand-back: 10664 passed, 455 skipped, exit=0 (955 s) on 3ad76e1; log /home/user/build/logs/a24f3-full.log. The 455 skips were not individually checked.
- NOT pushed: commit 3ad76e11e65639b88d02b4403f05be25c7153f56 is local in /home/user/build/WT-A24 only. Push to origin core/ci-scan-config-guard-fix1 after the full suite is green.
- GitHub CI not run; no independent review yet; CODEOWNERS handle @veerarakesh56 unverified; branch ruleset is owner-only.

Evidence on this head: ruff check, ruff format --check, bandit -ll, python tools/scan_repo.py all rc=0; test_scan_repo + test_ci_gitleaks_scope + test_ci_toolpath_step 700 passed; test_scan_repo_mutations 24 passed (control + 23 mutants, 624 s). Fail-before on db0e0ce: 203 failed / 261 passed (A24-PR91-fix3-failbefore.txt). gitleaks 8.30.1 probe: A24-PR91-fix3-gitleaks-probe.txt (-diff and binary blind it).

Decisions for the lead:
- Reviewer claim "ISC004 dead" was refuted (5 live errors); fixed by parenthesising, corpus.py marker now S608 only.
- Allowlist rule `*` refused; bare lgtm is a marker; non-config symlinks scanned as link text; python under ruff-skipped folders is an unlistable hit; names containing codeql/zizmor are configs.
- Not done: pinning whole .github/ tree; bash/sh not vouched by the CI step; a marker moved onto other code with identical text is not seen.

Head: 3ad76e11e65639b88d02b4403f05be25c7153f56

# Package ticket: PR-scan-config-guard (follow-up to PR90; lead ORDER 187, 190)

Short ticket (about 110 lines). Written 2026-11-09 08:57 UTC (14:27 IST) by the planner-builder.

- Package id and name: PR-scan-config-guard, "scan-config guard". Branch `core/ci-scan-config-guard` from main 2742c1b (PR90 merged).
- Path class: security (it guards the secret scan and the CI security job). Extended review (no round cap): yes.
- Depends on (merged first): PR90 (merged). Does not block PR87/88/89/84 (see "Friction" below).
- Problem in plain words: the CI scans (secrets, static analysis, vulnerabilities) can be switched off from inside a pull request
  without touching a pinned file: a one-line comment such as `nosec` or `nosemgrep` hides a finding, and a new scanner ignore file
  (`.semgrepignore`, `.trivyignore`) or a change to `.gitleaks.toml` / `.gitleaksignore` hides whole classes of findings. PR90 pins
  the `security` job only; the `check` job (which runs `tools/scan_repo.py`, lint, tests) and `tests-py312` are not pinned, so
  `|| true` or `continue-on-error` there goes unnoticed. Three small leftovers from the PR90 reviews are also open.
- Source of the code: none copied. Extends `tools/scan_repo.py` and `tests/test_ci_gitleaks_scope.py` (both in this repo). NOT taken:
  any new scanner, any new dependency, CODEOWNERS and repository rulesets (owner-only GitHub settings, lead ORDER 187 item 1).
- Target module and path: `tools/scan_repo.py` (not in `src/`; it is a CI tool).
- Interface: `scan(repo, allowlist, extra, banned_src, suppressions=None)`; new CLI flag `--suppressions FILE` (default
  `tools/scan_suppressions.txt`). Output per hit stays `path:line: rule` (matched text never printed). New rules:
  `suppress-nosec`, `suppress-nosemgrep`, `suppress-gitleaks-allow`, `suppress-trivy-ignore`, `suppress-noqa-security`
  (a `noqa` that is blanket or names a ruff `S` security code), `scanner-config-file`, plus list-hygiene hits
  (`suppression-list: stale|count|hash|malformed`).
- Neutral default / alternative: plain Python and a plain text list, no vendor. Alternative: none needed (no external dependency).
- Files to create / change:
  - change `tools/scan_repo.py`: the five marker rules, the scanner-config rule, the list reader (reason: one choke point, runs
    in the `check` job on every PR already).
  - create `tools/scan_suppressions.txt`: THE reviewed list, one file. Lines `path:rule:value:reason`; value is the exact number
    of markers in that file, or for a scanner-config file the sha256 of its bytes (any change to `.gitleaks.toml` or
    `.gitleaksignore` then needs a list edit that a reviewer sees).
  - change `.github/workflows/ci.yml`: tool-path step (symlinks, python3/uv/uvx rule); no change to any other step.
  - change `tests/fixtures/ci_security_golden.json` (regenerated: now also `check_job` and `tests_py312_job`), `tests/test_ci_gitleaks_scope.py`,
    `tests/test_scan_repo.py`; create `tests/test_ci_toolpath_step.py` (runs the step text in bash on a temp tree).
  - change `CHANGELOG.md`.
- Existing core code reused: `tools/scan_repo.py` (allowlist reader/format, `git ls-files` walk), the golden/regenerate pattern and
  `check_*` helpers of PR90. Nothing in `src/hadavin_sdk` is touched.
- Security and least-privilege notes: no new identity, no secret, no network. The list is a plain file; a PR can edit it, so real
  enforcement needs CODEOWNERS or a ruleset on `tools/scan_suppressions.txt` and `tools/scan_repo.py`: OWNER-ONLY (lead puts it in
  later-fixes.md). Until then the guard makes every new suppression a visible diff in one file instead of an invisible comment.
  Not covered: suppressions kept in `pyproject.toml` (ruff `ignore`, `per-file-ignores`, a bandit section): covered by a new pin test
  (`per-file-ignores` must equal today's value, no `ignore`, no `[tool.bandit]`).

## RUNG TABLE (CODE-LAST v1; scale of 2026-11-06: 1 no-code, 2 our core, 3 existing free tools, 4 free libraries, 5 own code)

| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| marker + scanner-config detection | fail CI when a suppression comment or ignore file appears without review | 3: gitleaks/semgrep/trivy cannot police their own ignore files; ruff `PGH004`/`RUF100` only flag blanket or unused `noqa`, nothing for `nosec`/`nosemgrep` (docs read from memory, UNVERIFIED today: re-check ruff docs before the PR is ready) | UNVERIFIED for the docs; verified here: `git grep` finds 10 nosec, 1 nosemgrep, 164 noqa in main | the single reviewed list and the count/hash ratchet | KEEP-CODE, but as ~60 lines inside the existing `tools/scan_repo.py` (rung 2 reuse, no new file of logic) |
| reviewed list | one place a reviewer reads | 2: reuse the `scan_allowlist.txt` format | existing file and reader in `tools/scan_repo.py` | exact counts and hashes (the old list is per rule, with no count) | CUT-TO-CONFIG+GLUE: a second list file in the same format, not a new mechanism |
| pin `check` and `tests-py312` | stop a neutered lint/test/scan step | 2: reuse PR90 golden-file pin | `tests/test_ci_gitleaks_scope.py` `check_golden` | none: only add two keys to the golden and the regenerate function | CUT-TO-CONFIG+GLUE |
| tool-path nits | symlink target, python3/uv/uvx | 3: `readlink -f` (coreutils) in the existing shell step | local run planned (test runs the real step text) | none | CUT-TO-CONFIG+GLUE |
| CODEOWNERS / ruleset | real enforcement | 3: GitHub settings | owner-only | n/a | OUT OF SCOPE (owner-only), listed |

## Design decisions

1. Markers need a comment prefix (`#`, `//`, `--`, `/*`) so prose such as the word nosec in the CHANGELOG is not a hit. `gitleaks:allow`
   needs none (it is not prose).
2. `noqa` is a hit only when blanket or when it names an `S` code (ruff's security family, the same family `bandit -ll` covers). Style codes
   (BLE001, F401, ...) are not scanner suppressions and stay free. Existing baseline: 10 nosec, 1 nosemgrep, security-`noqa` lines in many files.
3. Baseline: the list is filled mechanically from main 2742c1b, so it says plainly that the baseline lines were NOT individually
   reviewed (each marker keeps its own inline reason). New lines must be reviewed in their own PR.
4. Exact counts, not "at most": removing a marker forces the list down (a ratchet); adding one forces a reviewed list edit.
5. python3/uv/uvx: they come from setup-uv and the workspace `.venv/bin` BY DESIGN (activate-environment), so a "must be outside the
   workspace" rule on the PATH result would break the legitimate venv. The real hole is a locked wheel shipping a regular file named
   `python3` in `.venv/bin`. Rule: for these three the path may be under `$GITHUB_WORKSPACE/.venv/bin`, but its fully resolved target
   (`readlink -f`) must be outside the workspace (the venv python3 is a link to the uv-managed interpreter). A regular file fails.
   For the 13 system tools both the path and the resolved target must be outside the workspace. Also fail if `.venv` has tracked files.
6. Stale-ignore step: the round-8 note names no failing input. I will run the step on temp repos for the two malformed cases I can
   think of (CRLF line, rule name outside the three) and report; I change the step only if a case passes that should fail.

## Tests (fail-before = run on origin/main 2742c1b; new test files copied there)

Unit (`tests/test_scan_repo.py`): each marker rule hits and prints no text; prose without comment prefix does not hit; style `noqa` does not hit;
listed file with the exact count passes; count +1 fails; count -1 fails (ratchet); stale list entry (file not tracked) fails;
entry without reason fails; unknown rule name fails; each scanner-config basename in a subdir fails unlisted, passes with the right sha256,
fails with a wrong sha256; list file missing is a hit when markers exist; existing allowlist tests keep passing.
Pin (`tests/test_ci_gitleaks_scope.py`): golden contains `check_job` and `tests_py312_job`; negative cases: `check` scan step `|| true`,
`continue-on-error` on `check` tests, pytest marker expression widened to deselect, lint step removed, `tests-py312` pytest neutered or
python version changed, services image changed; pyproject pin cases (added ruff `ignore`, new per-file-ignore, `[tool.bandit]`).
Tool-path step (`tests/test_ci_toolpath_step.py`, Linux + bash only, else skip): real step text run with a temp PATH: all tools outside passes;
tool in workspace fails; symlink outside -> workspace file fails; `.venv/bin/python3` regular file fails; `.venv/bin/python3` symlink to outside passes;
tracked `.venv` file fails.
Hostile inputs: marker inside a very long line; non-UTF-8 bytes (scan already uses errors=replace); a file named `.gitleaksignore` in a subdirectory.

## Mutants (fixed at build time if wrong; each killed by the named test)

M1 drop `suppress-nosec` pattern -> nosec test. M2 prefix made optional -> prose test. M3 `noqa` rule matches style codes -> style-noqa test.
M4 count compare `>=` instead of `==` -> ratchet test. M5 skip hash compare -> wrong-hash test. M6 scanner-config matched by full path not basename -> subdir test.
M7 drop stale-entry check -> stale test. M8 `check_golden` ignores `check_job` -> check-job negatives. M9 remove `readlink` resolve -> symlink test. M10 allow regular file in .venv/bin -> venv test.

Evidence commands (saved to `egm/hadavin-sdk/evidence-scg-1.md` by the lead's runner; the builder's raw output is in the checkpoint note):
`uv run --all-extras --group test ruff check`, `ruff format --check`, `bandit -ll -r src tools`, `pytest tests/test_scan_repo.py tests/test_ci_gitleaks_scope.py tests/test_ci_toolpath_step.py`,
`python tools/scan_repo.py` on the branch head, then the same tests on a clean checkout of origin/main with only the test files copied in.
Reviewers: security correctness + adversarial, fresh agents, diff + this ticket + evidence only.
Done = round with no Blocker/Major, and all gates green (tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit).
Rollback: tag `pre-scan-config-guard`; revertible (CI-only files).

## Friction to tell the lead (specific)

Once merged, any PR that adds a security `noqa`/`nosec` or edits `.gitleaks.toml`/`.gitleaksignore` must also edit `tools/scan_suppressions.txt`.
PR87/88/89/84 add no such line if `git diff` shows none; I will check before merge. Nothing else in the queue is blocked.

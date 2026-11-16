# PR #90 round 5 security review (a53625a5), head f49e6ac. Saved by cloud session.

PR #90 round 5 security review, snapshot head f49e6ac. Verdict: not clean. The round-4 findings are closed, but several ways remain to weaken scanning without failing these tests. None of the bypasses below was run: I had no shell.

Files read: ci.yml, test_ci_gitleaks_scope.py, ci_security_golden.json, files.txt, and the round-4 report. The report is at /home/user/hadavin-sdk/handover/reviews/PR90/round4-security.md. The path in the task (handover/reviews/...) does not exist under /home/user/build. I did not read DIFF.patch; I worked from the final files.

## Round-4 findings: status
- **Blocker, comment-backslash hiding:** closed. The golden compares the raw `run` text of every security step, so a hidden line changes the text and fails.
- **Major, unpinned steps including setup-uv:** closed for the steps themselves (uses, with, run, and every step key), because the whole `security` job dict is compared.
- **Major, unpinned on/permissions/runner/job ids:** closed. `top` and `jobs` are compared, and `check_structure` still asserts the exact top-level key set. That assertion is what catches `defaults` or `jobs`-level additions, because `check_golden` alone does not.
- **Major, `.gitleaks.toml` content:** only partly closed. See finding 2.
- **Nits (`--proto-redir`, `--connect-timeout`, duplicate keys):** done. The strict loader rejects duplicates.

## Findings

**1. Major. The tools the job runs come from the PR tree, and the golden does not cover pyproject.toml or uv.lock.** Location: ci.yml:164-172 (setup-uv with `activate-environment: true`, then `uv sync --locked --no-build --only-group scan`).
- A PR can edit the `scan` group and uv.lock. `activate-environment` puts `.venv/bin` ahead of `/usr/bin` on PATH. A wheel in the lock that ships a console script named `sha256sum`, `tar`, `git`, `curl` or `python3` shadows the system binary.
- It also changes what `pip-audit`, `bandit` and `zizmor` are, since they are installed from that lock.
- Every pinned command text stays identical, so golden and structure checks pass. This is the same mechanism as round-4 finding 2, moved from the setup-uv step to the lock file.
- `--no-build` blocks building from source, but not a prebuilt wheel from an index or URL.
- Fix, either of:
  - Drop `activate-environment` and call the scanners as `.venv/bin/<tool>`, with absolute paths for `sha256sum`, `tar`, `curl` and `git` in the security steps.
  - Add a step after the sync that fails if `command -v sha256sum tar curl git python3` resolves under the workspace.
- Also pin the `scan` group in a golden, or require owner review of pyproject.toml and uv.lock (see finding 5).

**2. Major. `check_gitleaks_config` can be passed by a broad allowlist.** Location: test lines 140-159.
- The only check on allowlist paths is four probe strings: `src/hadavin_sdk/store/migrate.py`, `tests/test_x.py`, `.github/workflows/ci.yml` and `pyproject.toml`.
- These all pass the test and hide findings in other tracked paths:
  - `^demos/`
  - `^tools/`
  - `^docs/`
  - `\.env$`
  - `\.pem$`
  - `uv\.lock`
  - `^\.gitleaks`
  - `\.json$` (hides the golden and every fixture)
  - `\.md$`
  - `\.sh$`
- The stale-ignore CI step only triggers on the text `targetRules|handover/`. A `demos/` allowlist skips every CI-side check as well.
- Fix:
  - Compare the parsed `.gitleaks.toml` to a stored golden, as is done for ci.yml.
  - Or, as a better class fix, enumerate `git ls-files` in the test and assert that every allowlist pattern matches nothing except paths under `^handover/(reviews|tickets|evidence)/`.
- The negative-test coverage is thin: one blanket-pattern case. Add a case for each branch (extra top-level key, changed `extend`, `commits`, `stopwords`, non-AND condition, and a `demos/` pattern).

**3. Major. Suppression markers and other config files that the scanners read from the PR tree are not guarded.** I'm working from memory of the tools' behaviour. Please verify each before relying on it.
- **Inline markers in scanned files.** `gitleaks:allow` on a line suppresses that finding with no config change. Others: `# nosec` (bandit), `# nosem` (Semgrep), `# zizmor: ignore[...]` (zizmor). Nothing greps for them.
  - For `# zizmor: ignore`: comments outside `run` strings are dropped by the YAML parse, so the golden cannot see them in ci.yml or any other workflow.
- **Trivy (ci.yml:243).** It auto-reads `trivy.yaml`, `.trivyignore`, `.trivyignore.yaml` and `trivy-secret.yaml` from the current directory.
  - CLI flags beat config for `severity` and `exit-code`.
  - Ignore files and secret allow rules still apply.
  - `--skip-dirs .venv` would also skip a tracked top-level `.venv/`.
- **Semgrep (ci.yml:182).** It reads `.semgrepignore`.
  - I am unsure whether the built-in default ignore list drops `tests/` even though it is passed as an explicit target.
  - The rules come from the live registry, which is not pinned. A rule removed upstream silently stops running.
- **zizmor (ci.yml:184).** I believe it auto-discovers `zizmor.yml` or `.github/zizmor.yml` in the audited directory. That file can disable rules or ignore findings.
- **bandit.** I do not think it auto-loads pyproject settings. I did not check.
- **Fix:**
  - Add a CI step, or extend `scan_repo.py`, that fails if any of these config files exists, unless it is in an explicit golden.
  - Fail on any tracked line containing `gitleaks:allow`, `trivy:ignore`, `nosem`, `nosec` or `zizmor: ignore`, unless it is on a short reviewed list.
  - Whether existing lines already use these markers, I could not see.

**4. Major. Nothing examines other workflow files.** Location: the test reads only `.github/workflows/ci.yml`.
- A second workflow, for example `other.yml`, could define a job whose `name:` is `security` or `check`, so a trivially passing check carries the required name.
  - How GitHub resolves two same-named checks for a required check is unverified.
- The same file could use `pull_request_target`, `workflow_run` or a broad `permissions` block.
- zizmor does audit it, but see finding 3 on the ignore comments.
- Fix: add a test that `.github/workflows/` contains exactly the golden file list (ci.yml only), and that any new file needs the golden change.
- This was already in round-4 finding 3 and is still not done.

**5. Major (design). The trust root is entirely inside the PR.**
- ci.yml, the golden, the test file, any `conftest.py`, and the pytest config in pyproject.toml are all edited by the same PR. The test can also be deselected or deleted.
- I accept the "golden edited in the same PR" design only on a condition: a human must review any change to these files. Without that, the golden protects against accidents and renames, not against an attacker or a rushed edit.
- That condition is a repository setting, so it is owner-only: a CODEOWNERS file plus a ruleset requiring code-owner review. The listed paths would be ci.yml, the golden, `tests/test_ci_gitleaks_scope.py`, `.gitleaks*`, the Trivy, Semgrep and zizmor config files, pyproject.toml, uv.lock, and `.github/`.
- Please state this next step plainly in the PR. It is not fixable in the diff.
- Improvements that are in the diff's reach:
  - The golden is a single escaped 3 KB line for the stale-ignore script. A change there is hard to review. Add a regeneration script that writes it in a stable form, and document it. No such tool exists in the PR today.
  - Or store the `run` bodies as separate `.sh` files next to the golden.

**6. Nit. PyYAML (YAML 1.1) versus the Actions parser.** I found no concrete bypass.
- Differences exist: octal `015`, underscores in numbers, and `on`/`yes`/`no` as booleans.
- The only parity risk is a value that PyYAML reads as the golden value but Actions reads differently. `fetch-depth: 0_0` is an example: it fails closed through the shallow-clone check.
- Use a YAML 1.2 loader (ruamel) for the golden compare, or keep every security-job scalar quoted or plain-string and add a type check.

**7. Nit. The `check` and `tests-py312` jobs are pinned only by name, runner, timeout and `if`.**
- That includes the `check` job's `python tools/scan_repo.py` (the repo's own secrets and banned-name scan) and the pytest run.
- Those can be neutered in the same PR. `scan_repo.py` is a PR-tree scanner that is not pinned.
- Job-level `permissions` and `needs` on those jobs are not compared either.

**8. Nit. Curl hardening.**
- `--max-time` and `--retry-max-time` are still banned by `check_downloads`. A stall after the connection is made runs to the 15-minute job timeout. This costs availability, not integrity.
- Retry and truncation behaviour of `-o` with `--retry-all-errors` is unverified. Integrity is covered by the checksum, run after curl finishes.

**9. Nit. Scanner defaults.**
- gitleaks decodes nothing and opens no archives by default, and Trivy skips binaries. A secret in a committed `.tar.gz` or base64 string passes everything.
- This is not new to the PR, but it contradicts the "cannot be neutered" claim.

**10. Nit. Test hygiene.**
- A string literal placed after the `check_golden(workflow)` call in `check_structure` is not a docstring.
- Much of `check_scan` is now redundant with the golden. It is harmless.

## What I did not check
- I ran no tests, no mutation, no shell and no curl.
- I did not verify the author's claims of 68 passing and 44 failing against origin/main.
- I did not read `.gitleaks.toml`, `.gitleaksignore`, pyproject.toml, uv.lock, `scan_repo.py`, `.semgrepignore` or any Trivy config. None is in the snapshot, so I could not tell whether the real `.gitleaks.toml` satisfies the guard or whether the other config files exist or already carry suppressions.
- I did not verify that `GITLEAKS_SHA256` and `TRIVY_SHA256` match the real release assets.
- Behaviours of gitleaks (`gitleaks:allow`, merge-commit scanning with `--log-opts=HEAD`), Trivy auto-loaded files and skip-dirs glob scope, Semgrep default ignores, zizmor config discovery, and GitHub's handling of duplicate check names are all from memory, unverified.
- I did not check whether PyYAML is in the test dependencies, or whether setup-uv's cache could be poisoned from the main branch.
- Branch protection and the required-check settings were not examined.
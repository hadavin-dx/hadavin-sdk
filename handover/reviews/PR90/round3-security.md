# PR #90 round 3 security review (a2af842f), head 4ee6072. Saved by cloud session.

**Round 3 verdict for PR #90 head 4ee6072: not clean.** The real ci.yml is correct, and spec items (1) and (2) are met. The pin tests (item 3) still have bypasses that pass, and the F3-F5 closure is only partial. I read DIFF.patch, ci.yml, test_ci_gitleaks_scope.py and failbefore-pr90.txt under /home/user/build/snap/90-4ee6072/, and did not run anything. The bypasses below are derived from reading the test logic.

**Real workflow (ci.yml 223-243, spec items 1 and 2)**
- **Scan:** `--log-opts=HEAD`, `--exit-code 1` and `--config .gitleaks.toml` are present, and the `|| { python3 ...; exit 1 }` handler is intact.
- **Downloads:** both curls carry `--retry 5 --retry-all-errors --retry-delay 5`. `--proto "=https"`, `--tlsv1.2` and the adjacent `sha256sum -c -` line are kept.
- **fetch-depth:** it stays 0, so the stale-ignore step's `--all` and `origin/*` checks still see every branch.
- **Stale-ignore step:** it is unaffected by the HEAD-only scan.

**F3-F5 status**

| Earlier bypass | Status |
|---|---|
| `|| true` variants | closed (exact word list) |
| `--exit-code=0` | closed |
| `.toml.bak` config | closed |
| `--retry 0` | closed |
| Step-level `continue-on-error` | closed |
| Unpinned sha256 | closed for the exact checksum line only (see findings 2 and 3) |
| Handler `exit 1` unpinned | only partly closed (see findings 1 and 2) |
| Job-level `continue-on-error` | not closed (see finding 3) |

Attacks via anchors, aliases, merge keys and same-name steps fail closed. `safe_load` resolves aliases, so the test sees the text that runs. `_step` demands exactly one match for each name fragment.

**Findings**

1. **Major (Blocker if no known bypass is acceptable): the handler pin is bypassable.** Test lines 91-99.
   - **Scenario:** the python line may carry anything after its quoted code. Changing it to `python3 -c '...' "$RUNNER_TEMP/gl.json"; exit "0"` keeps the three-line handler shape, with `exit 1` and `}` last.
   - **Why it passes:** the only filter is `\b(exit\s+0|true|set\s+\+e)\b`. It misses `exit "0"`, `exit 00`, `exit 256` and `exit $((0))`. The step then exits 0 when a secret is found.
   - **Fix:** require `handler[0]` to equal the exact expected python line, not just a prefix. Drop the regex.

2. **Major: lines before the scan, and extra lines in the download steps, are never checked.** Test lines 87-93 and 114-125.
   - **Scenario, scan step:** `cmds` before the scan line are ignored. A new line such as `trap 'exit 0' EXIT`, `exit() { builtin exit 0; }`, `export GIT_DIR=/nonexistent` or `set +e` passes every check. The first two turn the handler's `exit 1` into success. `GIT_DIR` points the scan at a different repository. Adding or moving the `tar` line also goes unnoticed.
   - **Scenario, download steps:** a first line `set +e` stops a failed `sha256sum -c` from aborting the step, so a tampered archive is extracted. The `tar` line and everything after the checksum line are unpinned, so `trivy ... || true` is also free.
   - **Fix:** pin the whole `cmds` list of each of the two steps against a golden list (curl, sha line, tar, scan, handler). Do not pin only the lines that were mutated.

3. **Major: nothing outside the single steps is pinned.**
   - **Job-level:** `continue-on-error: true`, an `if:` that skips the job on `pull_request`, `strategy`/matrix, `needs`, and `env:` all pass. A skipped `security` check satisfies the required status.
   - **Shell defaults:** `jobs.security.defaults.run.shell: bash {0}` drops `-e`. A `sha256sum` mismatch then no longer aborts the step. Workflow-level `defaults` has the same effect. `defaults.run.working-directory` and `env` (such as `BASH_ENV` or `CURL_HOME`) are also free. The test forbids `shell` only at step level.
   - **Steps and checkout:** extra steps between checkout and scan can run `echo X=… >> $GITHUB_ENV` or delete `.gitleaksignore` or `.gitleaks.toml`. `checkout.with.ref` and `repository` are not pinned, so HEAD can point elsewhere.
   - **Fix:** assert that the `security` job has exactly the expected key set. Also assert there is no workflow-level `defaults`, the exact security step-name sequence, `checkout.with == {persist-credentials: false, fetch-depth: 0}`, and the `GITLEAKS_SHA256`/`GITLEAKS_VERSION` and Trivy env values.

4. **Major (vacuity risk): mutation failures are swallowed.** Test lines 143-149, 176-179, 214-218.
   - **Scenario:** `_mutate_run` is evaluated inside `pytest.raises(AssertionError)`. Its own fixture guard, `assert old in step["run"]`, is also an `AssertionError`. If a later edit reworded the YAML so `old` no longer matched, that test would pass without testing anything.
   - **Checked today:** I confirmed that every `old` string in SCAN_BAD and CURL_BAD currently exists in the target run text. That includes `rpartition` hitting the scan line, not the comment or the handler's `gl.json`. They are non-vacuous today.
   - **Fix:** build the mutated workflow before the `with pytest.raises` block, or raise `ValueError` in the fixture. Optionally assert the mutated text differs from the original.

5. **Nit: fail-before evidence is thin.** failbefore-pr90.txt shows 3 failures on the old workflow. The `[Trivy]` checksum-line test passes there only because `check_downloads` fails earlier on the GL step. That is a pass for the wrong reason, not a defect, but it shows nothing about the Trivy retry.

6. **Nit: the content of `.gitleaks.toml` is not pinned.** The test pins the file name only. A global `[allowlist]` added in the same PR would neuter the scan. The step-1 preconditions only check `targetRules` and `handover/`. This predates the PR and is outside the stated spec. I mention it only for completeness.

7. **Nit: the URL check accepts any github.com URL.** Test line 122 accepts any URL starting with `"https://github.com/`. The sha256 line still binds the content, so the impact is low. Pinning the URL to the exact expected template would be cheap.

The simplest fix for findings 1-3 is one structural assertion: normalized golden `cmds` for both steps, plus an exact-key-set check on the job and workflow.
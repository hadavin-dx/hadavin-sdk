# PR #90 round 4 security review (a2bcf23a), head e6974c5. Saved by cloud session.

PR #90 round 4 security review, head e6974c5. Verdict: not clean. The real ci.yml is correct. The pin test still has one cheap bypass inside the two pinned steps and several large unpinned areas of the security job. I read DIFF.patch, ci.yml, test_ci_gitleaks_scope.py and the round 3 report. I ran nothing: I had no shell tool. Every bypass below is derived from reading the test logic and from bash and curl behaviour as I remember it. Please run the 5-line mutation for finding 1 before relying on my word.

**Real workflow (ci.yml 223-243)**
- The scan has `--log-opts=HEAD`, `--exit-code 1`, `--config .gitleaks.toml` and the `|| { python3 ...; exit 1; }` handler.
- Both curls carry `--retry 5 --retry-all-errors --retry-delay 5`. `--proto "=https"`, `--tlsv1.2` and the next-line `sha256sum -c -` are kept.
- The retry flags do not weaken the checksum. The file is hashed after curl finishes. The step has no `shell:` key, so GitHub's default `bash -e` applies and a mismatch aborts the step. An empty `GITLEAKS_SHA256` makes `sha256sum -c` fail on a malformed line. I did not run this.
- fetch-depth stays 0, so the stale-ignore step still sees every branch.

**Round 3 findings now closed**
- Handler suffix and prefix tricks: the golden command list compares exact text.
- Lines before the scan or after the checksum in the two steps: also covered by the golden list.
- Job and workflow keys, step-level keys, the env pin, the checkout `with` pin, the exact URL, and trivy `|| true`: closed.
- Mutation vacuity: `_mutate_run` runs outside `pytest.raises` and raises ValueError, so a stale fixture cannot pass silently.

**Findings**

1. **Blocker.** `_commands` (test 145-150) drops any logical line that starts with `#`, after it joins backslash continuations.
   - Bash does not continue a comment onto the next line. The test does.
   - Scenario: change the comment at ci.yml 229 or 233 to end with a backslash, and put a command on the next line:
     ```
     # scope: only commits reachable from the checked-out head \
     trap 'exit 0' EXIT
     ```
   - The test sees one comment line and drops it. Bash runs `trap`.
   - The hidden line can be `set +e` or `exit 0` before the scan. In the Trivy step it can be `exit 0` at the end. A `sha256sum` result can also be neutralised.
   - Every golden-list and handler check passes. The same trick works in the other, unpinned steps.
   - Fix: do not skip comments by parsing. Compare the raw `run` text to a stored literal, or fail on any comment line that ends in a backslash. Add this mutation to the bad-case lists.

2. **Major.** `check_structure` pins only the names of 8 of the 10 security steps (test 65-76, 127-132). It pins the contents of 2.
   - Steps 0 and 1 are checked only for `name is None`. Step 1, setup-uv, can be replaced entirely. It could become `run: echo "$PWD/bin" >> $GITHUB_PATH`, or write `BASH_ENV`, `LD_PRELOAD` or `GITLEAKS_SHA256` to `$GITHUB_ENV`.
   - That puts a fake `sha256sum`, `git`, `python3` or `tar` first on PATH. It can also override the pinned workflow env, since `GITHUB_ENV` beats workflow-level `env`. Every pinned command stays textually unchanged.
   - Step 1's `uses` and `with` (version, checksum) are free.
   - Unpinned run and keys: Install the scanners, pip-audit, bandit, Semgrep, zizmor, and the stale-ignore step. Any of these can take `|| true`, drop `--error`, change `-ll`, gain `continue-on-error: true` or `if: false`, or end in `exit 0`. All pass, because the test checks the name only.
   - `steps[0]["uses"]` is not pinned in `check_downloads`. In `check_scan` it only has to start with `actions/checkout@` (line 180), so any ref passes, not the SHA.
   - Fix: compare the whole `security` job to a golden dict, not the key set plus two steps.

3. **Major.** Values outside the security steps are unpinned (test 110, 115).
   - Only the presence of the `on` key is checked, not its value. Removing `schedule` or `push` passes. That silently drops the weekly pip-audit and scanner run the header comment promises. Narrowing `pull_request.branches` also passes, and the required check then stays pending.
   - `runs-on` and `timeout-minutes` are free. A self-hosted label, or a changed runner image, passes.
   - `permissions` and `concurrency` values are free.
   - Other jobs are unconstrained. A job with `name: security` makes two check runs with the same name. How GitHub resolves that for a required check is unverified. A second workflow file is not examined at all.
   - Fix: pin the workflow's `on` and `permissions`, the `security` job's `runs-on` and `timeout-minutes`, and the set of job ids and job `name`s. Add a test that no other file under `.github/workflows` defines a `security` job.

4. **Major, carried from round 3 finding 6, which I rated a Nit then.** The scan's inputs come from the PR's own tree, and the test pins only the file names.
   - Inputs read from the PR tree: `.gitleaks.toml`, `.gitleaksignore`, `trivy.yaml`, `.trivyignore`, `.semgrepignore`, and bandit settings in pyproject.
   - A PR that adds `[allowlist] paths = ['''.*''']` to `.gitleaks.toml` passes the test. It passes the stale-ignore step too, which greps only for `targetRules|handover/`.
   - Trivy's `--skip-dirs .venv` may match a committed top-level `.venv/` directory, which hides that content. I did not verify the glob semantics. Does `tools/scan_repo.py` forbid a tracked `.venv/`? I did not check.
   - I upgrade this because the test docstring claims a neutered scan cannot pass. Fix: pin the hash of `.gitleaks.toml`, or assert its parsed contents against a golden. Add an allowlist guard to the stale-ignore step. Do the same for the other config files.

5. **Nit.** Curl hardening and a trap in the test.
   - There is no `--proto-redir "=https"`. As I recall, `--proto` does not restrict redirect targets, so a redirect to http is allowed. The checksum still covers integrity.
   - There is no `--connect-timeout`. A stalled connection runs until the 15-minute job timeout, and retries do not help with stalls.
   - The test regex (line 193) bans `--max-time` and `--retry-max-time`. That blocks the natural fix for the stall problem. Allow bounded timeouts, and pin them in the flags list.

6. **Nit, unverified.** PyYAML is YAML 1.1 and silently takes the last of two duplicate keys. The GitHub parser may reject duplicate keys, or may not support `<<` merge keys. If it differs from PyYAML on any construct, the test and the runner would see different workflows. I did not check this. Add a duplicate-key-rejecting loader to the test.

7. **Nit.** After finding 1 is fixed, much of `check_scan` (the words list, the handler regex) is dead weight behind the golden list. It is harmless. The author's evidence (59 pass on the new file, 42 fail on origin/main's) shows only old-versus-new. It says nothing about bypass resistance. None of findings 1-4 has a test case.

**Not checked**
- I ran no tests, no mutations, no shell and no curl.
- I did not read `files.txt` or any other repository file, and I did not read `.gitleaks.toml`, `.gitleaksignore`, pyproject, `uv.lock` or `tools/scan_repo.py`. So: is PyYAML in the test group? Does pytest's config collect this test? What does the `scan` group install? All unknown.
- I did not check branch protection or GitHub's required-check behaviour, curl 8.5's retry and `-o` truncation behaviour, Trivy's glob semantics, or the author's 59/42 claim.

Snapshot files read: /home/user/build/snap/90-e6974c5/files/.github/workflows/ci.yml, /home/user/build/snap/90-e6974c5/files/tests/test_ci_gitleaks_scope.py, /home/user/build/snap/90-e6974c5/DIFF.patch, and /home/user/hadavin-sdk/handover/reviews/PR90/round3-security.md.
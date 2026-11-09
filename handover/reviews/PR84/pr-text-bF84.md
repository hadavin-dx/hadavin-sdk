# PR 84 text to add (builder bF84, head 69b69c6)

## What changed since the first review
- The Evidence workflow now fails a test step on any skipped test that is not on one exact list, prints how many tests passed, were skipped and were left out, and fails if fewer tests ran than a recorded minimum. Both the list and the minimum live in `tools/evidence_step.py` only.
- Every step log, the runner facts, the plan job summary and the verdict say which branch and commit the workflow came from. A run started from another branch is labelled, not refused (reason below).
- The Vault start step is now a row in the verdict.
- ci.yml: the performance step now also gets `HADAVIN_TEST_VAULT_ADDR` (it needs the Vault server); the Postgres port is published on the loopback address only (hardening, covered by a test now); the unused `HADAVIN_REQUIRE_PINNED_UNIDATA` line is removed (nothing in the repository reads it).

## Not done, and why
- The workflow has never run on GitHub. A manual run needs the workflow file on the default branch (or an API dispatch of this branch), which the cloud session cannot do. Next step for the owner or lead: after merge, dispatch Evidence once for the merge commit and attach the run id; the guard tests only read the YAML text, and the new real-pytest tests prove the helper path with the real tool.
- The Vault start script still exists three times (ci.yml `check`, ci.yml `tests-py312`, evidence.yml), kept equal by a test. A shared composite action does not fit evidence.yml: a local action is read from the tested ref, which can be older or changed, and the guard requires every `uses:` to be a 40-character commit.
- One `noqa: S603` remains, in `start_fixed`. Ruff accepts only an argument list written out in full at the call; the helper must run a command given on its command line. A test counts it (one in the helper, none in the guard file). Removing it needs a config exception, which is the owner's call.
- The guard test is still one large file; splitting it would move code without changing what it checks.

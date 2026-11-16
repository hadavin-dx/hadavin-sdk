# C7 patch test runs (base b4cce5b). Evidence only, no judgement.

See FAIL-CAUSE.md first: the two baseline failures are real defects in tracked files outside our folder (handover/ docs and handover/promotion-inputs copies), not caused by the patches. In my scratch copy (git archive, no .git) test 2 failed with a `git ls-files` exit 128 (scratch-only artefact) and test 1 failed on the banned vendor word in handover files.

## What failed or could not run
- Baseline full suite: 2 failed (both below), exit 1. Same 2 failures on every patched copy; no patch adds a failure.
  - tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
  - tests/test_repo_rules.py::test_licences_are_proprietary
- bandit is not installed in the uv env (`uv run ... bandit` exit 2, "Failed to spawn"). I ran it via `uvx bandit -ll -r src` instead: exit 0, no issues at medium or higher (6 low).
- /usr/bin/time absent; wall time and peak memory measured with a small Python wrapper (resource.getrusage), /tmp/c7/run.py.
- Env: only PATH, HOME, proxy and TLS-certificate vars passed (without them uv cannot download: "invalid peer certificate: UnknownIssuer"). No cloud variables.
- Not run: the README's "ordered together" apply (C-01, A-01, G5 in sequence) on one copy; each patch tested alone.

## Baseline (b4cce5b, scratch copy /tmp/c7/base)
| Check | Command | Exit | Result | Wall | Peak RSS |
|---|---|---|---|---|---|
| ruff check | uv run --all-extras --group test ruff check | 0 | all passed | 2.6s | 52 MB |
| ruff format | ... ruff format --check | 0 | 299 files formatted | 0.1s | 40 MB |
| pytest | ... pytest -q -p no:cacheprovider | 1 | 2 failed, 9389 passed, 455 skipped | 241s | 424 MB |
| bandit | uvx bandit -ll -r src | 0 | no issues (medium/high) | 2s | 50 MB |

## Per patch (each on its own fresh copy)
| Patch | apply --check / apply | New tests on UNPATCHED base | New tests on patched | ruff check / format | Full suite on patched |
|---|---|---|---|---|---|
| C-01 | 0 / 0 | tests/test_c01_route_limits.py: 8 failed, 2 passed (exit 1) | 10 passed (exit 0) | 0 / 0 | 2 failed (same two), 9399 passed, 455 skipped, exit 1, 238s |
| A-01 | 0 / 0 | test_a01_audit_reconcile.py + test_p7_tick.py: 6 failed, 40 passed (exit 1) | 46 passed (exit 0) | 0 / 0 | 2 failed (same two), 9394 passed, 455 skipped, exit 1, 237s |
| G5-wording | 0 / 0 | none shipped | tests/warden_port/test_gate.py: 14 passed (exit 0) | 0 / 0 | 2 failed (same two), 9389 passed, 455 skipped, exit 1, 240s |

Commands: `uv run --all-extras --group test pytest -q -p no:cacheprovider <test files>`, run from the scratch copy. Raw logs: raw/ (base-*, <patch>-targeted, <patch>-full, before-C-01, before-A-01, *-ruff-*, *-applycheck).

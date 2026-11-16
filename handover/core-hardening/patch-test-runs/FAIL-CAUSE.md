# FAIL-CAUSE: two baseline test failures at b4cce5b (evidence only, nothing fixed)
Date 2026-11-16. Raw logs: raw/fresh-clone-b4.log (fresh clone at b4cce5b), raw/fresh-clone-branch.log (cloud/core-hardening head 789118026).

## Result: both tests FAIL in both fresh clones (rc=1). So they are real defects in the tracked tree, not a scratch artefact.
(-x stops at the first failure, so test 2 was run again alone, appended to the same logs.)

## 1. tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
Assertion (test line, fresh b4 clone): `AssertionError: vendor brand strings or unscannable files in the repo:`
- handover/BRIEF-PREAMBLE-studio-2026-11-06.md: banned string 'Por...' (line 17, item 15)
- handover/demo/portal/portal-design-v2.md: banned string 'Por...' (line 234)
- handover/reviews/P1a-idempotence-probe.txt: "not UTF-8 text, cannot be scanned for vendor strings"
Cause: these files are tracked under handover/ (the cloud branch tracks handover/). The cloud-branch clone adds more hits:
the raw pytest logs in handover/core-hardening/patch-test-runs/raw/ (base-pytest.log, A-01-full.log, C-01-full.log) are tracked
and quote the banned string from the failure message itself (self-feeding: any saved failing log containing the message becomes a new hit).
tests/test_no_reference_material.py itself holds the list (expected, excluded by the test).

## 2. tests/test_repo_rules.py::test_licences_are_proprietary
Assertion: `tests/test_repo_rules.py:120: assert licence_problems(ROOT, files) == []`
Result: 10 extra items, all of the form 'handover/promotion-inputs/<demo>/LICENSE: not the proprietary licence text'
7 LICENSE copies (apexc, dealdesk, helios, killswitch, portal-kit, refunds, warden) plus 3 pyproject.toml problems (killswitch license and authors, portal-kit authors).
Cause: copies of demo repos' LICENSE and pyproject.toml files under handover/promotion-inputs/ are tracked, and the test checks every tracked one.
Subprocess error text: none in the fresh clones (git ls-files works there; failure is the assertion above).

## 3. Scratch copy
In the original base-pytest.log, test 2 failed with `subprocess.CalledProcessError: Command '['git', 'ls-files']' returned non-zero exit status 128`
(git says not a repository / no usable .git in that folder) and test 1 failed in the same scratch run. That subprocess error is a scratch-only artefact;
the assertion failures above are the real tree defects. Step 3 not run: no scratch path for the C7 baseline run is recorded in raw/ or checkpoint notes (do not guess).

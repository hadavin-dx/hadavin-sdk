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

## UPDATE after lead answer (2026-11-16)
Edits (working tree of cloud/core-hardening, not committed by the builder):
- handover/BRIEF-PREAMBLE-studio-2026-11-06.md line 17: the vendor name (Po..., banned) replaced by "the dashboard quality of a well-known developer-portal vendor and of Datadog"; nothing else changed.
- handover/demo/portal/portal-design-v2.md line 234: the vendor name (Po...) replaced by "a well-known developer-portal vendor"; nothing else changed.
- handover/reviews/P1a-idempotence-probe.txt: converted from ISO-8859 to UTF-8, invalid bytes replaced by ?, one header line added ("Converted to UTF-8 on 2026-11-16; invalid bytes replaced by ?").
- handover/core-hardening/patches-ready/v2/README.md: third hit named by the test (our own folder, contains the banned word); cleaned by the redact script, not by hand.
- handover/promotion-inputs/: untouched.

Vendor test (test_no_vendor_brand_string_is_tracked), fresh clone /tmp/h1/clone of cloud/core-hardening:
- BEFORE: 1 failed (4 files named: the three above plus patches-ready/v2/README.md).
- AFTER copying the 3 edited files: 1 failed (only patches-ready/v2/README.md, committed version still has the word).
- AFTER also copying the redacted README: 1 passed.
Licence test (test_licences_are_proprietary) on the same clone: still fails: BRANCH ARTEFACT. The core sdk tests are meant to run on the sdk tree, not on the studio branch (handover/promotion-inputs/ holds copies of demo LICENSE and pyproject files).

Clean sdk-core run: `git archive b4cce5b` into /tmp/h1/sdk, git init + add + commit (git ls-files works). Both guard tests (vendor test and licence test):
- Archive as is (it still contains handover/): 2 failed (same handover files; promotion-inputs licences). Only the vendor test touches the 3 files edited above.
- Same tree with handover/ removed (pure sdk tree): 2 passed.
- Whole test_no_reference_material.py + test_lockin_guard.py on the archive as is: 1 failed, 58 passed.

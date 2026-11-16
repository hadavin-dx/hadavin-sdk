# Full test run of the core repository, before and after three patches (queue item H1)
Written 2026-11-16 09:30 UTC / 15:00 IST by flows-audit. Round 1 reader review done; its fixes are applied here (round 1 of 2).

## In one sentence
The full test run fails 2 of about 9,850 tests, with or without the patches. Both failing tests are checks on documents under `handover/`, not on code. The patches themselves add 15 passing tests and break nothing that was passing.

## What failed or is unverified (first)
1. Red gate. The repo rules say all checks must be green before a pull request, so a pull request for the patches is blocked until the two checks below are settled.
   - Check 1 (`test_no_vendor_brand_string_is_tracked`) looks for banned product-name strings in tracked files. It finds "[vendor-brand-string]" in `handover/BRIEF-PREAMBLE-studio-2026-11-06.md` and `handover/demo/portal/portal-design-v2.md`, and cannot read `handover/reviews/P1a-idempotence-probe.txt` (not UTF-8 text).
   - Check 2 (`test_licences_are_proprietary`) checks every LICENSE file carries the studio's own licence text. It lists 10 files under `handover/promotion-inputs/` (first: `apexc/LICENSE`).
2. Evidence for "same 2 failures": both reports name the same two tests and the same files (counts 10 and 1 match). The per-item lists were not compared line by line.
3. Why the patches cannot cause this: the baseline (no patches) fails the same two tests. In addition, the three patch files change only 11 files, all under `src/hadavin_sdk/` and `tests/` (checked in `git show origin/cloud/core-hardening:handover/core-hardening/patches-ready/*.patch`). I found no source for any claim about the flows-audit folder, so I make none.
4. The earlier 5 failures seen in a stripped-down scratch copy (README, CHANGELOG, .gitleaks.toml, a docs manifest, no .git) did not appear in a full copy of the repo. They did not reproduce; the likely cause is that the scratch copy lacked those files, but that cause was not tested. (They were listed in `reviews-of-core-patches/REVIEW.md`.)
5. Small gaps: the first run of the 70 new tests had cloud-key variables set in the shell (they use fakes); the 70 also ran inside the full run with the variables unset and passed, which is the real support. Security scan (`bandit`) ran from a side Python environment because `uv run bandit` could not start; baseline scanned `src` only, the patched run used the CI command (`src demos`), so the two scans are not like for like. 455 tests are skipped in both runs; whether the Postgres tests are among them was not checked. Not run: anything that needs real services.
6. Patch versions tested: the three patch files from branch `cloud/core-hardening`, tip `bf5f18383`, applied in the order C-01 (price and token limits), A-01 (tick drains the audit outbox), G5-wording (comments only) on commit `b4cce5b`. The review fixes listed in REVIEW.md were not applied in this run.

## Numbers (raw output: evidence-baseline.md, evidence-patched.md)
| run | tests | lint (ruff check) | format check | security scan (bandit) |
|---|---|---|---|---|
| baseline b4cce5b | 2 failed, 9389 passed, 455 skipped (280 s) | exit 0 | exit 0 (299 files) | exit 0, 0 issues (src only) |
| with the 3 patches | 2 failed, 9404 passed, 455 skipped (282 s) | exit 0 | exit 0 (301 files: 2 new test files) | exit 0, 0 issues (src and demos) |
- 9404 minus 9389 = 15 more passes. The 70 new and changed tests alone pass (5 + 10 + 41 + 14).
- All three patches apply with `git apply --check` and `git apply`, in order.

## What the studio head must decide (recommendation: option A)
- Option A, fix the files: remove or reword the two "[vendor-brand-string]" mentions, convert or exclude the one non-UTF-8 probe file, and put the studio licence text in the 10 LICENSE files (or move those inputs out of the repo if they are copies of other projects' files and must keep their own licence). Keeps the public-repo guard whole.
- Option B, exclude `handover/` from both checks: fast, but it lets a banned product name into a folder that is in the public repository, which is what check 1 exists to stop. Not recommended.
- Owner of the files: the studio head (these files are not from the flows-audit session).

## Correction 09:45 UTC (main session)
A fresh clone of the branch (evidence-fresh-clone.md, head 0c0715e) showed the vendor-brand guard test failing ONLY because our own evidence files in this folder quoted the brand string the test forbids. The string is now replaced by `[vendor-brand-string]` in all four files here (raw evidence edited for that one token only). So part of what the earlier text called "not caused by us" was caused by our own quoted output. The licence guard test passed in the fresh clone. Not re-run since the replacement: re-run the two tests once to confirm green.

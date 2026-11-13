# real-run v6 chain (HANDOVER-ONLY: never a PR; needs the owner's yes, plan r10 review, hygiene gate)

Base: main 61ded9e of hadavin-dx/duplicate-proof-lead-desk-n8n (squash of PR #4; tree == 3598120).

## Files and sha256 (checked after push)
| file | sha256 | what |
|---|---|---|
| real-run-fixes-v6-after-sonar-p3-final.patch | 9fc11e9ac19b3279f76241555fe9e0531f0b98c4e97291e55207e9d46c19eead | v6 = v5 + start-prompt-hardening-v2 + fixes of the v5 read, rebased on the merged Sonar P3 code (applies on main) |
| desk-address-required-v6.patch | 6667935762862fc00b943b635eadb062005023f7cf8a4b713530df3fc1f241ff | breach-class choke point (explicit vendor base URL), applies AFTER the variant above |
| core-touches-3.patch | c61791a626be7790bec12eb3e670c27b4b349687c1f425859c195918cf8bec00 | ONLY the 3 core hunks (live_claude._read_key, crm_hubspot._key, smtp_provider.read_secret_file) + tests/test_core_key_readers.py; standalone read; applies alone on main |
| real-run-fixes-v6.patch / -rest.patch / -after-sonar-p3.patch | (see sha256sum) | db54e13-form / v6 minus core-touches-3 / p3-v3 variant: NOT for main |

Reads: ../REVIEW-core-hunks-v6-fresh.md (CLEAN: core hunks + desk-address) and ../REVIEW-real-run-v6-fresh.md (CLEAN: scripts, guarantee class). Notes: NOTES-v6.md, FIXES.md (v6 section), evidence-q4h-*.txt, core-differential-q4h.py, drivers/.

## Apply order on main 61ded9e
```
git checkout 61ded9e
git apply --check real-run-fixes-v6-after-sonar-p3-final.patch && git apply real-run-fixes-v6-after-sonar-p3-final.patch
git apply --check desk-address-required-v6.patch && git apply desk-address-required-v6.patch
# standalone core read (alone on a clean 61ded9e): git apply --check core-touches-3.patch
```
(real-run-fixes-v6.patch alone does NOT apply on main: it conflicts with the merged P3 in scripts/run_real_check.py.)

## Commands the fresh readers used (Linux, no network, no secrets; made-up data only)
Safety: NEVER answer y/yes or type a destination host at any start/confirm prompt of the desk/take/real-run scripts; loopback-only settings; any test that answers `y` only under a network namespace with loopback up and a connect blocker:
```
unshare -rn python3 drivers/lo_up-q4g.py -- python -m pytest tests/test_real_run_v6.py ...   # (-rn breaks one setuid test: use `unshare -n` + lo up as root for it)
```
Tests (product tests only): `tests/test_core_key_readers.py`, `tests/test_real_run_v6.py`, the files named in evidence-q4h-tests-v6.txt / evidence-q4h-da-tests.txt; differential of the three key readers old vs new: `python core-differential-q4h.py` (see evidence-q4h-core-differential.txt); fails-before: copy only the new test files onto a clean 61ded9e and run them (evidence-q4h-fail-before*.txt: 70 failed cases in 16 distinct tests for the scripts, 7 failed / 5 passed for the key readers, 12 failed / 4 passed for desk-address without its src hunks).
Not run by anyone: Windows, the full suite, run-dry-checks.sh on this exact tree.

## Known limits (from the reads)
- The v6 patch adds 32 suppression comments (E402/S603/S404/PLC0415/type: ignore): policy flag, handover-only.
- hubspot_probe.py still reaches the vendor by omission and confirms a spend without a terminal test (NO change, lead decision 09:48Z).
- The end-to-end `--config` run past the question is no longer tested (needs a typed host); `--dry-fakes` runs cover the post-question code.

# Citation check of patches-ready/README.md (2026-11-16)
Scope: every file:line, count, sha256 and path in README.md read against the cited file. README.md not edited. Ran only `sha256sum`, `grep`, `sed`, `wc`, `cmp`. No tests run. Not checked: `registry.py:35-36,53` and `deferred.py:62` (no `src/` in this tree), `v5/raw` 12-mutant killed status beyond the 3 lines seen, `ORDERS.md` times beyond 10:42Z/10:31Z/10:02Z.

## FAILURES (3 cites wrong, 1 hash drift, 1 wording)
1. README.md:54 path. Claim: `patch-test-runs/raw/base-pytest.log:255`. Actual: no such path under `patches-ready/`; the file is `../patch-test-runs/raw/base-pytest.log` (one level up, `handover/core-hardening/`). Line 255 and the content `2 failed, 9389 passed, 455 skipped` are correct there.
2. README.md:66 cite `review/design-c7b-fix4-r5.md:2-6`. Actual: the file has 5 lines. 0 blockers/0 majors is line 2, "Recommendation: accept." is line 5. Should be `:2-5`.
3. README.md:67 cite `v6-extra/DESCRIBE-ONLY-flaky-id-test.md:8-9`. Actual: the file has 8 lines; the Remove-EC2 text is all line 8. Should be `:8`.
4. `v5/SHA256SUMS.txt` no longer matches `v5/README.md`. Listed `5a2f58d9...`; actual `sha256sum v5/README.md` = `921fb904...` (`sha256sum -c`: `README.md: FAILED`; the other 7 files OK). `v5/raw/sha256-check.txt` shows OK, so v5/README.md was edited after that check. README.md:76 points readers to `v5/SHA256SUMS.txt`; it does not claim a match, but the sums file is stale for that one file.
5. README.md:9 "No file here claims it [n8n]". `review/necessity-r1.md:2` and `:4` say the take's claim "is carried by n8n plus scripts/run_real_check_n8n.py (NOT read by the reviewer)". That is a reviewer statement about the take, not a run of these patches on n8n, so the substance (nothing here ran n8n) holds. Wording "No file here claims it" is too broad; suggest "no file claims these patches were run with n8n".

## Possible confusion (not a failure)
- Two rates for the same flake: README.md:62 quotes "1 test run in 2,731" (`DESCRIBE-ONLY...md:3`); `v6-extra/README.md:3` says "1 id in about 10,900". 24/262,144 = 1 in 10,923 per id, so both are consistent; they count different things.
- `v5/README.md:65` claims "76 passed in the two files"; no raw file contains it. README.md does not cite it, so no effect here.

## SHA256
- `v6-extra/FIX-id-vs-command-withheld.patch` = `12e4be6f42e2f47ae254276cdcf27b1cb31b50d5fa40a1adcedde4acfeb6b9ce`. Matches README.md:64, the `.sha256` file and `v6-extra/README.md:6`.
- `G5-wording.patch` in v3, v4, v5 identical (`0815212a...`). Top-level `G5-wording.patch` differs from v5 (README.md:37 calls it the first set, so consistent).

## VERIFIED OK (read against source)
Test counts and lines: 9418 `v5/raw/full-suite-c01min.txt:140` (231 s); 9413 `v4/raw/...:140`; 9491 `v3/raw/full-suite.txt:141`; 9514 `v3/raw-c7b-fix3/full-run.log:145`; 9391 `v3/raw/pristine-full-suite.txt:139`; 2 failed/9389 `v3/raw-c7b/base-pytest.log:181` and `../patch-test-runs/raw/base-pytest.log:255`; v2 `2 failed, 9451` `v2/README.md:109`. Arithmetic 9391+27=9418 (`v5/README.md:56,:66`); 9413=9391+22 (`v4/README.md:62`). Source lines `v4/README.md:62`, `v3/README.md:181-182`, `v3/REPORT-c7b-fix3.md:13` (9514), `:4` (withdrawal) all correct.
v5/README.md cites (the author's suspect ones): `:16` (not run list), `:16-18`, `:23`, `:26`, `:32`, `:56` (23 + 4 tests), `:63` (19 failed, 4 passed; raw `c01min-tests-on-pristine.txt:358` agrees), `:66`, `:69` (12 mutants; raw lists M1-M12), `:73-78`, `:80-90` (Appendix A), `:92-98` (Appendix B), `:5-13`, `:9-13`: all land on the described text. v5 patches: G5 touches 3 files, C-01-MINIMAL 5 files, as stated.
v6-extra/README.md `:3` (display, 32 hex, `ec2`+a-f), `:14` (needs lead's independent review), `:16` (display only): all correct. `v3/README.md:3-12` (scope cut), `STATUS-BOARD.md:25`, `ANSWER-Q18-lead.md:2`, `ORDERS.md:139` (Q16.1) and `:140` (Q16.2), `design-r5-c5v5.md:2`, `v3/handback-c7b-fix4.md:3`, `design-c7b-fix4-r5.md:4`, `cross-read/one-place-sweep-r1.md:21` item 8: all correct.

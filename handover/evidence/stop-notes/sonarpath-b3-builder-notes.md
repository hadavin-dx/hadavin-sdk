# SONAR-PATH batch 3 builder notes (core/k1b-path-confinement, base e29cc269)

Failures and gaps first:
- SonarCloud: not run by me; I do not claim any finding is cleared. The lead's probe (draft PR #100) is the only Sonar evidence.
- Mutation rows: the three final runs (46 + 61 + 25 rows, each under 8 minutes) were all good; logs mut-final-S/B/C.log. The two bundle joins, the second score joins, and the hashing/secrets single guards are listed as EQUIVALENT with an argument (tests/pathguard_mutants.py, EQUIVALENT; a test checks the text still exists).
- Tripwire tests that scan with the new scanner pass on old src by nature (the scanner is test-side code). Fail-before for the plants was measured with the OLD scanner (e29cc269 tests file): of 35 plants it reported 12, so those 12 are now in test_pin_the_first_scan_already_reported_these_and_still_does; the other 23 are missed by the old scanner (fail-before). The comparator and validator-check tests do not exist at e29cc269 (absent, not runnable).
- Not covered: a swap of the run folder in the instant between the re-check and the write (stated in the replay test and the changelog). Windows, hard links, mount points, junctions, \\?\ paths: not checked here. Demos: unreviewed path sites remain.
- The lead's NOSONAR request: there is no NOSONAR text in src or tests at e29cc269 or now (a test checks it in any letter case). Nothing to remove; I did not add any.
- Pre-existing suppressions in untouched code remain (noqa BLE001 in audit/local_dir.py line 138 and one more, nosec in executor/common/tools, type: ignore in config.py/loop.py, noqa in audit_sink.py, many in unrelated tests). I added none; the diff holds no added suppression.

Classes A-H: see the commit message and CHANGELOG entry "Path checks". Addendum points: (1) 58 passing-on-e29 tests in batch3 are named test_pin_* or test_control_*; 33 fail on e29; 0 other pass. (2) atomic_write onto a folder or a taken temp name raises PathRefused R13 with a path-free text (tests X7/X8 rows). (3) run folder swapped to a link mid-run: re-joined strictly before every write; the limit is stated. (4) hash_files and mounted_file secrets go through pathguard. (5) test suppressions removed (fmt: skip x4 in my touched tests, type: ignore in sites). (6) origin/main..e29cc269 is 3 commits.

Lead's S8707 addition: score.py load_answers, _recorded_digest and _read_json, hashing.hash_files and secrets_file._fetch each join the name to its folder with pathguard.join(..., must_exist=True, kind="file") right before the read; messages unchanged (pin tests test_pin_hash_files..., test_pin_secrets_file..., test_pin_score_digest...). Three new pin tests, all named test_pin_*. No test from this addition fails on old source (the behaviour and wording are unchanged): 3 pins, 0 fail-before.

Evidence files: fb-b3final-*.log (fail-before per head), fb-others-e29.log, mut-final-*.log.
Checked: ruff check and ruff format --check on 23 changed py files; bandit -ll on the changed src files printed no finding; focused tests 526 passed on 3.12 and on 3.13; wider -k run 4268 passed 22 skipped (3.13). No full suite run (cloud limit).

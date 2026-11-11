# PR H builder checkpoint, 2026-11-11 about 21:57Z

Last commit pushed: adf69605 (WP2c partial). Nothing newer is committed.

Done (uncommitted in /home/user/build/PRH, WP2c):
- hidden.py grammar changes (nF letter/digit final stays text, Fp/Fe/Fs, CSI in ECMA-48 order), direct redact() fixed at its choke point (redact.py reads two readings), runmap guarded character reading, tools._scrub fix.
- Real step-backs against main: 517 -> 0. 92 pairs remain "accidental" (main masked them only by deleting text a string sequence swallowed); listed in /home/user/build/PRH-wp2c-accidental.txt and pinned in the test.
- 43-file run: 7504 passed, 1 failed (test_no_hardcoded_values: my 20_000 literal in runmap.py). Fixed by moving it to defaults.MAX_SWALLOWED_CHARS; ruff check and format clean; that test plus unit tests (84) pass.

Not yet done / unverified:
- Re-run of test_prh_contract.py with the pinned counts (running now, log /home/user/build/PRH-wp2c-43b.log); the pin edit has never been run.
- scan_repo.py, gitleaks, fail-before-main proof for WP2c.
- T5 (regressions), WP3 (mutants, CI step, perf), WP4 (docs, full suite, bandit): not started.

Deviations from D-026 wording: nF alnum final removes only ESC (D-026 would eat a UUID dash); Fp/Fe/Fs also changed; CSI order changed; no-step-back test narrowed by _plain_masked with 92 pinned pairs.

Blockers: none. Next: commit and push WP2c when contract run is green, then T5.

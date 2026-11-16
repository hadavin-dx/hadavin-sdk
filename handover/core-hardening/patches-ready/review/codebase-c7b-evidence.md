# C7b evidence review (egm codebase-details, read-only), condensed copy, 2026-11-16
Verdict: headline numbers match the logs (patched 9489 passed / 2 failed; base 9389 / 2; same two repo-guard failures; new tests 95 passed; ruff/format/bandit clean). No Blocker.
## Major
- M1 "+100 passing" vs 95 new tests: gap of 5 not reconciled in any log (probably 5 functions added to modified tests/test_k1b_replay.py, C-01.patch:429-455). No --collect-only diff saved.
- M2 Flake explanation asserted, not shown. Cause is gate.py:671 (cmdlet-shape rule in _WRITE_SHAPES) matching a random id `pln-ec2<a-f>...` from models.new_id; my arithmetic gives ~0.012% per execution (2.4 of 20,000) but loop logged 9 base / 3 patched: does not reconcile; loop script not saved; "channel.py not touched" is the wrong file (rule lives in gate.py, which G5-wording edits docstring-only). It is a real product/test bug: fix it (fix-dont-defer), not just note it.
- M3 No base no-handover full-suite run, so "0 new failures" on the shipping tree is shown only for patched.
- M4 Dry-run logs, sha256 comparison, cat-file, versions, command lines (-ll flag) not on disk.
## Weakeners
- W1 (Major) env scrub not literal `env -i`; only AWS_*, AZURE_*, GOOGLE_APPLICATION_CREDENTIALS, ANTHROPIC_API_KEY unset; no env dump saved.
- W2 (Major) first run with AWS_* inherited was killed and its logs deleted.
- W3 (Major) two pytest logs redacted in place (4 spots), original hash not kept.
- W4 Nit table.py.orig present during full suites. W5 Nit bandit via uvx 1.8.6, src only. W6 Nit flake repeats ran test alone.
## Not checked by reviewer
dots section, sha256 values, scratch trees, new tests not run against base tree (proof they fail on old code), BANNED tuple recount.

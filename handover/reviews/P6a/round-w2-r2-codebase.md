# PR72 core/P6a head d392200, codebase-details review, round 2 (least privilege, uncapped)
Read-only, ran nothing. Verdict: 0 Blocker, 2 Major, 5 Nit.
- M1 Major: no ruff, format or bandit output at d392200 in the builder evidence (cannot confirm the removed noqa; CI scope for tools/ unverified in the on-disk ci.yml). Needs raw output at the head, scope stated, plus Python 3.12. (The independent evidence run d392200-cloud covers it.)
- M2 Major: tools/p6a1_mutants.py still holds private build history in public text: docstring lines 1-20 (mutant id ranges, "reserved for the second pull request of this package", 41+4+18=63), comment at line 483, "[later]" descriptions 484-645, and the file name p6a1. Reword to describe the job; rename (for example client_profile_mutants.py) and keep references consistent.
- N3 line 755 variable prod_fixture_loads is a start-time stamp: rename.
- N4 the _edit wrapper in tests/test_client_profile.py duplicates four folder-taking _edit helpers: share one in k5_support.
- N5 strict-bool sweep (10 other StrictBool fields) has no mutant recorded: only tests/test_strict_flags.py covers loosening them. Lead decides scope (BL-core-a14-w2-05).
- N6 21 pin rows pass on the base and are labelled pins; every new-behaviour row (48) fails by its own cause. No vacuous row found.
- N7 app.py comment on dict(locals()) overstates why it must be first; ordering before the secrets rebind is what matters.
Checked, no finding: import rule of the test file, stage names, secrets, private ids in src/tests/CHANGELOG, noqa removal (no suppression in added lines), placement and logic of the app.py check, config.py allow-list.
Not checked: no run of tests, ruff, bandit, mutants or fail-before; Postgres-gated rows; Python 3.12; ci.yml at the PR head; lead orders; independent evidence.

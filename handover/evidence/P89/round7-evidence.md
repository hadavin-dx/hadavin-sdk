# P89 round 7 evidence (redaction path)

Head: 3586dcc34647fa66dded9a4250be6b52e845c5ba (parent 14879da, the round-6 head). Tree: 6fa785565bc526c20021db7cf61a74540b76f6ab.
Pushed with a plain push to core/mutation-runner-keywords. gitleaks 8.30.1 on HEAD (git mode, .gitleaks.toml): no leaks found. ruff check, ruff format --check (322 files): clean. bandit -ll: no issues (two nosec warnings, none new).

sha256 of the five changed files (plus the manifest, which is the sixth changed file):
ae658f7a88c9869acd74efbbcd455a3d997fbbb81d2da4fb129835825487c4dd  tools/mutation_runner.py
8168c46b3fc097300cde3e0382554596a21a195c2bf6326c695a611e84a23714  tests/test_mutation_runner_keywords.py
c116e34437be6e2cf12ff019c0df67e74cfa6c6c3123fa216e7a874d35358ed6  tests/mutation_runner_mutants.py
70723abf3fbf5c32b8b2e3ed5136ad2bcc42597194307a0e05238295c7e60e1a  tests/test_mutation_runner_meta.py
dda252a3b171c5c56f30ba9fa66b7f5226a543a2e6010e73855a249ef9e4608f  CHANGELOG.md
cb1dd38893c4c46ded5cfe5125431f7b172a264a23151ebc0427b0b4ae56f69b  tests/fixtures/mutation_manifest.json

Mutants (raw logs r7-mut.log root uid 0, r7-mutnb.log uid 65534):
- r7-mut.log: 162 of 162 good; problems: []
- r7-mutnb.log: 162 of 162 good; problems: []
- uid line printed in the nobody logs: uid=65534 (mutnb), uid=65534 (kwnb312), uid=65534 (kwnb313)

keywords + meta, 105 tests (r7-kw312/kw313 as root, r7-kwnb312/kwnb313 as uid 65534): 105 passed in 36.07s / 105 passed in 34.82s / 105 passed in 36.29s / 105 passed in 35.31s

Fail-before (new keywords test file against old code):
- against the ROUND-6 head 14879da (r7-old14879.log): 7 failed, 92 passed, 1 warning in 41.04s. The 7 new tests all fail there: two_layers property test, repr(repr)/json(repr) deterministic test, plus-as-space, FIFO lock file, permission text (TMPDIR), JUnit non-regular file, JUnit size ceiling.
- against the earlier base 58f7d56 (r7-old58f7d56.log): 32 failed, 67 passed, 1 warning in 31.59s.

History of this round (honest): a first full mutant run at the first local commit had 7 bad mutants (4 survivors from per-character encoders that the new whole-text layers made redundant, one wrong-reason, one judged CRASH instead of KILLED because the FIFO test used pytest.fail, one baseline test catching too few exception classes). All fixed in the code and mutants (not by weakening tests); the stale logs are in r7-stale and r7-stale2. One mutant run (r7-stale) ran while the tree was edited and is not used.

NOT run: the full test suites (an independent runner follows), the Windows branch (no Windows here), a real network file system for the flock refusal (the text is documented; the refusal path is the existing 'could not be locked' test), three or more layers of printing (stated as not covered).

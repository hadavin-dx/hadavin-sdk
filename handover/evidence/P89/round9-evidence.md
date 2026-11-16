# PR89 round 9 evidence (head 9ed5217cab69d466177c7cc337bae751af5938e8, tree 93cf0ab6a09f54190730bf8955ba5a1e072c0ec4, on top of ef4c572)

Raw logs: r9-*.log in this folder (r9-stale/ holds runs of an earlier local state, not used).

Gates at the final head:
- ruff check: all passed. ruff format --check: 322 files formatted. bandit -ll: 0 issues. gitleaks on HEAD history: no leaks.
- Full pytest 3.12 (r9-f312.log): 10174 passed, 455 skipped (454 need HADAVIN_TEST_PG_DSN, 1 Stubber). 3.13 (r9-f313.log): same numbers.
- Full pytest WITH a throwaway Postgres (UTF8, own ports 55891 / 55892, both stopped afterwards): 3.13 10628 passed 1 skipped (r9-pg313.log); 3.12 10628 passed 1 skipped (r9-pg312.log).
- The manifest test is not skipped (ran alone: 1 passed).
- Mutants: 179 of 179 good as root (r9-mroot.log) and as uid 65534 (r9-mnob.log, prints uid=65534). Keyword and meta tests as uid 65534: 121 passed (r9-nb313.log).
- Fail-before on ef4c572 (new keyword test file against the old tree, r9-old-ef4c572.log): 9 failed, 106 passed. The failing ones: the two two-layer tests with the wider alphabet, the exhaustive short body/tail test, the depth 3, depth 4-5 and bare-password depth tests, the skeleton pin test, the one-pattern-per-text test, the match-limit test. The new tests that PASS on ef4c572 (they cannot fail there, the exact forms already existed): the short value and short bare password tests, the escaped-quote test, the printed-once test, the short libpq test, the conftest fixture test, the quote-heavy speed test. They are killed by mutants instead.
- On 58f7d56 (r9-old-58f7d56.log): 46 failed, 69 passed; includes the short bare-password test; most of those fail only because functions did not exist yet.
- Manifest pins, recomputed with sha256sum and compared to tests/fixtures/mutation_manifest.json and CHANGELOG: all four match (testing/__init__ 3c77d034, testing/mutation 23f5d9d7, tools/__init__ e3b0c442, tools/mutation_runner e977a51e).

Measured masking time (2026-11-11, this machine): _secret_values 1.2 ms; a 1,000,000-character line 0.18 to 0.21 s; 100,000 characters 0.02 s; 40,000 near matches 0.03 s; a line with 100,005 spread-out matches 0.12 s (replaced whole). Using one pattern per written form instead of per plain text is about 47 times slower (73 ms against 1.5 ms per 20,000 characters): pinned by a test and a mutant.

Not run: Windows branch, network file system; a secret under 6 letters (quote marks and backslashes removed) printed three or more times is covered by the exact forms to two layers only (a shorter skeleton would hide ordinary text); this is pinned by a test and written in the CHANGELOG.

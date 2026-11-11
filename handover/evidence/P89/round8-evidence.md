# P89 round 8 evidence

Head: ef4c57280011def60b852a0778005f107a313c72 (parent 3586dcc, plain commit, no history rewrite). Tree: 58a941081753ec5beeb7ae9c83944f8f6a6452a5. gitleaks 8.30.1 on HEAD: no leaks. ruff check and ruff format --check: clean. bandit -ll: 0 issues.

Pinned files, recomputed at this head (all four, sha256 with CRLF normalised, compared with tests/fixtures/mutation_manifest.json): src/hadavin_sdk/testing/__init__.py 3c77d034fe2a1ee70adea0d0bd259a20edda397d8ebd55a0e40b63e5c21c9e1c match; src/hadavin_sdk/testing/mutation.py 23f5d9d7ed996eefb6742b71d7b5769b6f7307d2d1e2c7bfdfa49a052e5c21f6 match; tools/__init__.py e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 match; tools/mutation_runner.py 1cf18dcdf7286fa7... match (full: 1cf18dcdf7286fa7ee5d7e48968f39e7c087668136753f2043e4e3d108e3bd89).
sha256 of the changed files: 1cf18dcdf7286fa7ee5d7e48968f39e7c087668136753f2043e4e3d108e3bd89  tools/mutation_runner.py
64d765f0846883cacbcf2c9f9ce49f31f721057914f01d002860e8aa8d30110a  tests/test_mutation_runner_keywords.py
5aa1d29da1d1e5c71243992b5ef68ae16328a0a4da329afadd62de3e24a2d73e  tests/mutation_runner_mutants.py
113ee188379364900fceaeeebb9bc02d3a592d41d04108f09131c7b9c991879d  tests/test_mutation_runner_meta.py
9537f3c2365a08db5da9241b972d11081f74be9c76c3a158b1a41a45a8509355  CHANGELOG.md
9c544740498ae37bc99975c187bb75fbec8f106c87fbd3c385c66ef2c3c4de27  tests/fixtures/mutation_manifest.json

Gates (raw logs r8-*.log): mutants root 166 of 166 good; mutants uid 65534 (uid line printed: 65534) 166 of 166 good; full pytest 3.12: 10160 passed, 455 skipped in 349.88s (0:05:49); full pytest 3.13: 10160 passed, 455 skipped in 319.68s (0:05:19) (run without a Postgres address, so the database tests are skipped); keywords+meta as uid 65534 on 3.12 and 3.13: 107 passed each.

Fail-before against 3586dcc (r8-old3586dcc.log): 101 passed, 0 failed. Stated plainly: the new tests describe behaviour that was already right at 3586dcc (the code was correct; only the mutant coverage was missing), so they cannot fail there. The proof is the mutants: each new test is the named killer of at least one mutant that changes the code, and that mutant is killed for the stated reason.

History: the first gate run at e49bfd9 had one survivor (single-quote layer-0 loop; its killer was the wrong test). I briefly tried removing that loop as redundant; a test showed it is needed (a C-style text with both quotes escaped), so the change was reverted and the mutant re-pointed (killed). The first-run logs are in r8-first.

NOT run: Postgres-backed tests, the Windows branch, a real network file system, three or more print layers.

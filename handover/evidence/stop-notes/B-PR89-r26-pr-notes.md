# PR 89 round 26 builder notes

Base 580b4adf. Spec: goldfish_review_report-r25.md. Accepted 1,2,5,6,7,8,9,10. Declined 3 (no change), 4 (one docstring sentence).

## What failed or was not checked
- Full pytest: 1 failure, tests/demo_askdata dblink-connect, caused by this machine (no default Postgres socket), also fails on 580b4adf; folder rerun 1214 passed after fixing the private test server; whole suite not rerun. One earlier full run was killed from outside (143) and discarded.
- Item 6: mypy is NOT added to pyproject or uv.lock. A local lock run rewrites the lock revision and markers and pulls extra packages, so it is not a plain addition and needs the lead's approval. The docstring and CHANGELOG say plainly that CI does not run the mypy count; the AST name table stays; the mypy parse is made robust.
- Windows, macOS, perf, CodeQL, SonarCloud, CodeRabbit: CI only, not run.

## Items
1 one casefold rule for every shown class name (_shown_class); 2 address check refuses a password casefold-equal to any built-in or caller class or crash type (CLASS_NAME_REFUSAL); 5 folders between are made by _make_private_dir; 7 creation-site pin walks the whole module, resolves aliases, lists the creating spellings; 8 _true_on_windows raises on a condition it cannot read, reads module pytestmark, BODY-SKIP list checked both ways; 9 private file opened without O_TRUNC, checked on the descriptor, then ftruncate.

## Item 10: new tests that pass on the old code, and why
- piece-of-class-name test and holds-a-whole-class-name test: controls for a class fixed in round 24. The piece case now has its own mutant (a built-in class name is hidden for a password that is a piece of it); the holds case is killed by an existing mutant.
- creation-site walk test, mypy error pattern test, skip-reader tests, BODY-SKIP header test, POSIX-ONLY header test: these check test code, not runner code, so old runner code cannot fail them. Shown live by manual plants (evidence plants.txt): P1 mark added to a killer, P2 name removed from BODY-SKIP, P3 pytest.skip added to an unnamed killer, P4 skipif the reader cannot read, P5 module pytestmark, P6b module-level shutil.move, P7 aliased os.rename. Each plant makes the test fail; files were restored after.
- Fail-before (final test files, mutants, manifest on the 580b4adf runner): 12 failed, 357 passed. Against origin/main the overlay cannot even collect (older runner), expected.

## Counts
327 mutants (265 keyword, 62 runner-file), 327 of 327 good. 7 mutants added, 5 re-pointed. mypy win32 13 errors on 3.12 and 3.13. New tests 9.
Re-run /home/user/build/B-PR89-r26-pins.sh after any further runner edit (manifest sha pin).

# PD Part 6 round 9, codebase-details reviewer (a91e4eee), head dd827d79

Read-only, snapshot /home/user/build/snap/pdbanner-dd827d79/. Condensed by the lead session. Result: 1 Blocker, 6 Major, 12 Nit. Nothing was run by the reviewer. Round 10 required.
Holds: seal by reference with `is`; replace leaves _sealed None; mode_banner() never raises; BEARER/BASIC equal main (12/8); pyc range from MAGIC_NUMBER; fchmod guard; R9D*/R9E*/R9B*/R9A2-A8/R9C1 old-text occurs once; table 283 rows.

1 Blocker: mode_banner.py:323-325, mode_banner.js:93-94, test_mode_banner.py:2709-2726. Docstring says a reworded banner keeps the names; code returns frozen NOT_CONFIRMED with overridden []. The test "..._with_the_names" replaces the line it should assert (vacuous).
2 Major: deepcopy "unconfirmed" holds only because the _PLAIN sentinel is copied; test does `except Exception: return` (can skip). Make the seal carry the App identity or a per-copy token; test fails instead of skipping.
3 Major: app.py:55-73,120: any dict/list/tuple/set is "plain"; ToolBox.fns/specs and executor contracts are dicts of callables, swappable without changing the seal. Read values by reference one level down or list toolbox members.
4 Major: demo_only_guard.py:331-336 _hide_pairs runs before BEARER/BASIC, so `auth=Bearer <token>` leaks the token. Run scheme rules first.
5 Major: pin convention not applied: about 28 tests say "PIN passes on 07bfda12", only 5 named test_pin_*; _sealed_app calls app._seal (absent on old code) so "fails on old code" is an AttributeError; the masker-cost test fails on old code only because _SECRET_NAME is missing.
6 Major: R9A1 does not model is->id (every comparison mismatches, dies in another test); the id-reuse test never reaches reuse; an honest is->id mutant is equivalent. Use a weakref liveness check; rename the row.
7 Major: CHANGELOG.md:225 says four tracked-file lists compared (three equal, one superset); "single pass" (it is five linear passes); the decision is not in the CHANGELOG; no table row-count test.
Nits 8-19: stale pyc/Mach-O comment and interpreter-dependent range; mode test never asserts the mode (chmod(target,0) survives); docstring "three records" wrong; swallowed except Exception at app.py:174,191 (debug only); production tick test has no sources/runs; symlink swap between stat and copy; colon form not masked; R9D6 name; _seal private by name only; limit 6 text lacks clock=; timeout_s reason wrong; JS comment says same rule as Python.

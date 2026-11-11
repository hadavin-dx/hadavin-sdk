# PR85 / A17 review: tests/test_config_error_sites.py 1131-1354 (hostile-input tests)

Head 4b1b3f9, snapshot /tmp/snap/core_P5b2-4b1b3f9-full. Read only; nothing run. Reviewer a3840b3329d6aea2c. VERDICT: no Major; 5 Minors, 3 Nits.

Verified true: FOREIGN_LIMIT=28 (test:119) and the CSV has exactly 28 FOREIGN rows (no slack today); `load_csv` (gen:1179-1212) enforces header, field count, duplicate site, class, ASCII, reason<=200, no control chars (13 hostile cases fail for stated reasons); `test_committed_table_matches_source` (102-107) is a real check.

Minors
1. :126 uses `<=`; cap cannot detect drift downward, nothing forces it to be lowered.
2. `compare` (gen:1231-1238) locks only LITERAL-vs-not and the `exception-variable` downgrade. A new unproven-origin site (e.g. `raise ConfigError(f"... {db_value}")`) can be labelled OPERATOR with a reason: compare.ok true, FOREIGN count unchanged, the FOREIGN_LIMIT stop sign never trips. Comment at 116-118 reads as a guarantee that is not enforced (rated Minor only because the auto class may be a hint a reviewer may overrule).
3. :1287 `assert csv.excel is not None` is vacuous; 1289-1292 mirror constants only.
4. `test_f3_the_allowed_uses_of_a_site_class_still_scan` (1351-1353) asserts nothing; no per-case expected site count.
5. Hostile tests (1140-1146, 1178-1187, 1318-1321) pass on any SitesError (no message match, no positive control on the REDUCES template; M33 named in docstring but not asserted).

Nits: 1324-1329 two refusals in one test; 1278 positional Site args; no test in range checks error messages avoid echoing input.

COVERAGE: test file 1131-1354, 20-169, 690-701; generator 132-171, 1150-1239; grep only on the rest and the CSV. Rest of the test file and scan internals not read.

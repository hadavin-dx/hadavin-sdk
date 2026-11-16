# p3a2b8-codebase-r19: P3a-2 batch 8, head 6a25ae5d (previous reviewed head aac26d60), round 18/19, persona codebase details

Source: hand-back of the codebase reviewer (agent a206db1e1b03507d6), saved by the lead (condensed). SECURITY / least-privilege path. Read-only, nothing run; no independent evidence existed when read (all counts builder-reported, unverified). 0 Blocker, 0 Major, 3 Minor, 2 Nit. Snapshot `/home/user/build/snap/p3a2b8-6a25ae5d`.

Groups 1 to 6 judged fixed by reading (`__context__` empty at auth_aws.py:28-45, migrate.py:1266-1286, postgres.py:238-254; catch widened to Exception, KeyboardInterrupt and SystemExit pass; port allow-list; wording; counts 39+3+2=44, 431 mutants, 12514 consistent). Group 7 (O8) untouched and OFF.

## Minor
- **C1** Step 8 of migrate opens a new connection (migrate.py:1668-1685); `raise _after_commit(...) from e` keeps the driver error as `__cause__` (may hold host and user). Printed text is class-name only; a debug traceback or a log handler sees it. The CHANGELOG wording "after the connection exists" wrongly suggests step 8 is out of scope. Fix: choke-point pattern plus a channel test, or say it in the CHANGELOG.
- **C2** The ~11 later `raise ... from e` sites (migrate.py:1295, 1301, 1619, 1622, 1626, 1657, 1662, 1663, 1667; older 380, 507, 1124) keep `__cause__`, which can hold a DETAIL line with row values. Not printed. Test at tests/test_migration_postgres.py:1256 is legitimate. Fix: write the policy (keep where no data, drop at 1622/1657/1662, or name it "kept for debugging, never printed"); do not claim "never kept".
- **C3** Widened sign-in catch makes an OSError or throttle during the token request a `SignInError` (ConfigError), not `StoreUnavailable`: kill-switch re-raises, `tick` exits 2 not 4 (cli.py:202-217, 311-319). A widening, not a regression against main. Fix: map transient types to StoreUnavailable at build(), or state in the CHANGELOG.

## Nits
- **C4** tests/demo_askdata/test_validate_harm.py `[copy-program]` "Broken pipe" unexplained, not tied to the delta; runner repeats it on both heads; if it flakes on both, write the reason.
- **C5** tests/test_sign_in_channels.py:30 imports a helper from another test module; move to tests/fixtures/.

## Not checked
Nothing run; mutant bodies V130-V148 not read in full; pre-existing from-e sites; conninfo_to_dict for hostaddr lists; psycopg text for an invalid DSN caught by build().

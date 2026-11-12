# p3a2b8-design-r19: P3a-2 batch 8, head 6a25ae5d (previous reviewed head aac26d60), round 19, persona design

Source: hand-back of the design reviewer (agent a39d7767413529efc), saved by the lead (condensed). SECURITY / least-privilege path. Read-only, nothing run; no independent evidence existed when read. 0 Blocker, 0 Major, 3 Minor, 3 Nit. Snapshot `/home/user/build/snap/p3a2b8-6a25ae5d`. D1 equals codebase C1, D2 equals C2, D3 equals C3, D6 equals C4.

Groups 1 to 6 hold by reading; group 7 (O8) OFF. No readable secret, no regression against main.

## Minor
- **D1** `migrate.py:1670-1685` step 8: connect (including sign-in) sits inside the `try`, so `raise _after_commit(...) from e` keeps the driver error (host, user words) as `__cause__`; `HADAVIN_DEBUG=1` prints it (`cli.py:84-85`). CHANGELOG scope "after the connection exists" is wrong for this site. Fix: hold the class name, leave the except, raise outside; test with an injected OperationalError on the second connection checking both channels; one mutant; correct the CHANGELOG.
- **D2** Policy for the ~11 `from e` sites: statement-time errors after the connection exists may keep `__cause__` (pin at tests/test_migration_postgres.py:1256 stays); connection-time errors must not be chained. Write the rule once in the CHANGELOG, saying HADAVIN_DEBUG=1 prints chained driver text. migrate.py:1625 and :1661 print `e.diag.message_primary`; `_label` not read.
- **D3** Widening to `except Exception` turns a transient credential failure (IMDS or STS timeout) into the non-retryable ConfigError path; kill-switch stop/reset prints "refused" exit 2 instead of "NOT set, nothing changed, run again" exit 4 (`cli.py:202-217`). Fix: print the "NOT set" sentence for SignInError on the kill-switch path, or map timeout-class names to StoreUnavailable in build; at minimum document.

## Nits
- **D4** tests/test_migration_verify_pg.py docstring of `test_a_refused_connection_keeps_no_driver_error_on_either_channel` names V131; it is the killer of V133.
- **D5** V132, V133, V146 killers need a server; read, not run: unconfirmed.
- **D6** copy-program Broken pipe: not caused by the delta; leave as open item with measured counts after independent repeats.

## Not checked
Nothing executed; `_label`, `_after_commit`, rest of migrate.py, CHANGELOG outside changed paragraphs. A malformed DSN at build (`conninfo_to_dict` at postgres.py:236, before the try) can raise a raw ProgrammingError quoting part of the DSN: unchanged from main, note for next reviewer.

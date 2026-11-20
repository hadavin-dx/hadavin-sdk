# From core-a: `ca_file` leaks a temp file per call (store owner)

`src/hadavin_sdk/store/postgres.py:95-102` (`ca_file`) writes the CA PEM to a new `tempfile.mkstemp(prefix="hadavin-ca-")`
file on every call and never removes it; it is called from `PostgresStore.__init__` at `postgres.py:168`
(`sslrootcert=ca_file(settings, deps.resolve)`) and from `cli.py:327-329`.

Effect on the trigger worker: while the store is down at start, the degraded worker calls `build` (which opens the
store) every `HEALTH_RECHECK_S` (5 s), so one `/tmp/hadavin-ca-*.pem` is left behind per failed attempt when
`sslrootcert_secret_name` is set. core-a cannot clean it from worker.py (the path is not returned to the caller on
a failed connect).

Wanted (store owner): remove the file after the connection has used it (`finally` after connect, or read the PEM into
`ssl` context / `sslrootcert` bytes without a file), or keep one file per store object and delete it on close.
core-a did not edit this file.

## Added 17:27 (rev-dfix27-r4): store CA path
worker.py:994-999 with store/postgres.py:136-146: the store's own sslrootcert is passed to libpq as a path. If libpq reports an unreadable or missing root cert as OperationalError (unverified), the worker treats it as "store down" and retries every 5 s forever (/health 503, only the class name logged). Please make the store raise a ConfigError (not a connectivity error) for an unreadable sslrootcert/ca_file, then the worker exits 2 (d-fix26/27 handle that).

# Ask your data (spike)

A staged demo of the safety shape of a text-to-SQL tool, on **synthetic data**. It makes **no accuracy claim** and
calls **no model over the network**: the model is a scripted stand-in (`askdata/spike_llm.py`). What it shows:

- **C2, the login cannot write.** `db/roles.sql` creates a read-only login that sees four views and nothing else
  (no base tables, no `email` column). `trust/verify_readonly.psql` is a script a DBA can read and run as that login;
  it exits 0 when every check is green and 3 when one is red.
- **C1, one canonical SELECT.** `askdata/validate.py` turns model-style SQL into one canonical, hashed SELECT or
  rejects it with a rule id (V01 to V12). Only the canonical text is shown, hashed and sent.
- **C3, a stacked statement cannot become a write.** Every statement travels the extended protocol (a named
  server-side cursor). `tests/demo_askdata/test_pgsource_layers.py` proves it with a login that HAS write
  privilege, and documents the hazard it prevents (a plain psycopg string commits `COMMIT; BEGIN READ WRITE; INSERT`).
- **C4, a watchdog and caps.** A timer cancels a blocked statement; row and byte caps stop big results.
- Every printed value passes `askdata/safe_text.py`, so a database value cannot drive your terminal.

Not in the spike: the language-model pipeline, retries, audit ledger, budget meter, gold set, evaluation, accuracy
numbers, export pages. Those are phases P1 to P5 of the design and start only on a pull signal from a prospect.

## One command, offline (fake model, no network)

Needs Docker (or any Postgres you may treat as throwaway), `psql` on PATH or in `PSQL`, and the repo environment
(`uv sync --locked --no-build --extra askdata`). From `demos\ask-your-data` in PowerShell:

```
docker run --rm -d --name askdata-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55432:5432 postgres:17.10
docker exec askdata-pg psql -U postgres -c "CREATE DATABASE askdata_demo"
$env:ASKDATA_ADMIN_DSN = "postgresql://postgres@127.0.0.1:55432/askdata_demo"   # a DEDICATED throwaway database
$env:ASKDATA_RO_PASSWORD = "choose-a-demo-password"; $env:PGPASSWORD = $env:ASKDATA_RO_PASSWORD
$env:ASKDATA_DSN = "postgresql://askdata_ro@127.0.0.1:55432/askdata_demo"
uv run --locked --no-build --extra askdata python -m askdata demo --setup   # add --accept-loss only after reading the preflight list
```

`demo --setup` applies schema, seed, views and roles (`psql`), then runs the whole story: the checks, one question,
two refusals. Without `--setup` it only runs the story. Other commands: `verify-readonly`, `ask --sql "<SQL>"`,
`ask "<question>"` (the scripted model knows five questions; `ask` alone lists them), `setup`.
Exit codes: 0 ok, 2 the model abstained, 3 a check is red or the validator rejected, 4 startup problem, 5 the
database refused the statement.

`roles.sql` runs `REVOKE ... FROM PUBLIC`, which changes access for every login in that database: use a dedicated
database or a replica, never a shared production database. It runs `db/preflight_roles.sql` first and stops if
other logins would lose access (`--accept-loss` to override).

## 90-second recording script (owner records; async-first)

Put the caption "Staged on synthetic data" on the first screen. Say no accuracy number. Before publishing, check the
frame for your location, personal e-mail or any secret. The planted terminal-control row is shown with its control
sequences removed (a talking point, optional).

| Time | Scene | Type this (from `demos\ask-your-data`) | Say |
|---|---|---|---|
| 0:00-0:20 | Promise | `uv run --locked --no-build --extra askdata python -m askdata verify-readonly` | "Staged on synthetic data. This login cannot write: fourteen checks, all ok, exit code 0." |
| 0:20-0:50 | Normal question | `... python -m askdata ask "How many orders per country?"` | "The exact SQL that ran, its SHA-256, and the result. The model here is a scripted stand-in, no network." |
| 0:50-1:10 | Refusals | `... ask --sql "DELETE FROM shop.orders"` then `... ask --sql "SELECT email FROM analytics.customers_v"` | "Rejected before it reaches the database: rule V03, rule V05." |
| 1:10-1:30 | Proof | `docker exec -it askdata-pg psql -U askdata_ro -d askdata_demo -c "DELETE FROM shop.orders"` then `uv run ... pytest -q tests/demo_askdata/test_pgsource_layers.py -k c3b` from the repo root | "This is the actual login the tool uses. The database says permission denied even if the tool were wrong. And a stacked-statement attack is refused by the execution path." |

## Tests

From the repo root, with a Postgres reachable: `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55432/postgres`
and `psql` available, `pytest -q tests/demo_askdata`. Without the variable the database tests skip on a laptop and fail
when `CI=true`. The parser oracle (`pglast`, GPL, test group only, never shipped) cross-checks the validator in CI.

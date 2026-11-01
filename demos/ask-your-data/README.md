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

## How the validator (C1) is tested (phase P2)

Everything below runs in CI with no model call. `tests/demo_askdata/`:

- `corpus.py`: 230+ attacks (each tagged with the one rule that must refuse it, a category and the harm it would
  do) and 60+ benign statements that must be accepted. `test_validate.py` runs them all.
- `test_validate_fuzz.py` (+ `fuzzgen.py`, `oracle.py`): 2,000 seeded grammar cases (clean, hazard dropped at a random
  place, hazard dropped at a grammar slot, token mutations). Every accepted statement must be a fixed point of the
  validator and must pass an independent oracle (the PostgreSQL grammar via pglast, a node-class whitelist).
- `test_validate_mutation.py`: switches each rule V01 to V12 off in turn and requires a named attack to notice.
- `test_validate_harm.py`: runs every attack unvalidated as the administrator of a scratch PostgreSQL and proves
  the harm it would do (rows or relations changed, row lock taken, hidden data returned, statement still running at a
  timeout); attacks PostgreSQL refuses on its own are tagged `pg-refuses` and shown to be refused, not claimed as harm.

Not in the spike: the language-model pipeline, retries, audit ledger, budget meter, gold set, evaluation, accuracy
numbers, export pages. Those are phases P1 to P5 of the design and start only on a pull signal from a prospect.

## One command, offline (fake model, no network)

Needs Docker (or any Postgres you may treat as throwaway), `psql` on PATH or in `PSQL`, and the repo environment
(`uv sync --locked --no-build --extra askdata`). From `demos\ask-your-data` in PowerShell:

```
docker run --rm -d --name askdata-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55432:5432 postgres:17.10   # the same tag CI uses (CI pins it by digest)
docker exec askdata-pg psql -U postgres -c "CREATE DATABASE askdata_demo"
$env:ASKDATA_ADMIN_DSN = "postgresql://postgres@127.0.0.1:55432/askdata_demo"   # a DEDICATED throwaway database
$env:ASKDATA_RO_PASSWORD = "choose-a-demo-password"; $env:PGPASSWORD = $env:ASKDATA_RO_PASSWORD
$env:ASKDATA_DSN = "postgresql://askdata_ro@127.0.0.1:55432/askdata_demo"
uv run --locked --no-build --extra askdata python -m askdata demo --setup   # add --accept-loss only after reading the preflight list
```

`demo --setup` applies schema, seed, views and roles (`psql`), then runs the whole story: the checks, one question,
two refusals. Without `--setup` it only runs the story. Other commands: `verify-readonly`, `ask --sql "<SQL>"`,
`ask "<question>"` (the scripted model knows five questions; `ask` alone lists them), `setup`.
`ask` first runs the read-only checks and refuses to start (exit 4) when one is red. Exit codes (spike, provisional):
0 ok, 2 the model abstained, 3 the validator rejected (`ask`) or a check is red (`verify-readonly`, and the DBA
script), 4 startup problem (no DSN, cannot connect, a red check, or the server refused the login, SQLSTATE 28xxx),
5 the database refused or failed the statement. The design's P3 table replaces these.

`roles.sql` runs `REVOKE ... FROM PUBLIC`, which changes access for every login in that database: use a dedicated
database or a replica, never a shared production database. It runs `db/preflight_roles.sql` first and stops if
other logins would lose access (`--accept-loss` to override).

## Dataset, ledger, meter and evaluation harness (phase P3)

- **Dataset "Lumen Goods"** (`db/lumen.py`, schema `db/lumen_schema.sql`): 1,200 customers, 120 products, 6,000 orders, 13,800 order
  lines, 6,480 payments, 1,040 refunds, 1,500 tickets, all synthetic, all e-mails on the reserved domain `example.com`. Its own
  SplitMix64 generator (no stdlib `random`) makes it bit-identical on every machine. Three builds: seed A, seed B (a second
  database for the "must agree on both" scoring rule) and `clean` (A without the planted rows, for the injection differential).
  `db/lumen_manifest.json` holds row counts and per-table SHA-256 for all three; `python db/lumen.py --write-manifest` rewrites it.
- **Pipeline** (`askdata/pipeline.py`): gates, generate, validate, audit intent, execute, ledger. Prompt layout, retry policy by
  validator rule and SQLSTATE, and reason codes are in `llm_io.py` and `policy.py`. The agreement check is not built.
- **Ledger** (`askdata/ledger.py`): one JSON line per question, append-only, fsync. **Audit** (`askdata/audit.py`): one intent event per
  execution, one outcome event per question; `audit verify` prints "local integrity check: N of N events and M of M ledger lines
  match" and never claims more. Commands (give `--config askdata.yaml` or set `ASKDATA_CONFIG`; the config shape is
  `askdata/config.py`): `audit list|show <id>|verify|export --format json|csv [--include-text]`, `meter [--set-external USD]`,
  `killswitch on|off|status`. Exit codes: 0 ok, 1 usage, 3 `audit verify` found a problem, 4 startup, 5 audit unavailable.
- **Meter** (`askdata/meter.py`): one JSON file shared with the Replay Check; a call needs its worst case to fit under the demo cap
  (US$8) and under the shared cap minus the reserve; a call that fails after sending is charged its worst case.
- **Eval** (`askdata/evalrun.py`, `compare.py`, `evalset.py`, `evalcli.py`): `eval run --split dev|test [--k N] [--second-look
  aborted|harness_defect]`, `eval report <run folder>`, `eval compare <baseline> <candidate>`. `eval/lock.json` freezes the file
  hashes and the gate thresholds (green: upper bound of the confident-wrong rate <= 10 %, amber <= 15 %); the sealed test set
  tolerates one invocation. Run exit codes: 0 green, 10 amber ("promising, not demonstrated"), 11 not demonstrated, 12 a hard
  zero breached, 13 aborted (meter or kill switch), 14 a sealed run refused, 4 startup. Compare: 0 no regression, 11 regression,
  4 not comparable. Only the scripted model is connected; a live route needs the owner's yes at each budget step.

## 90-second recording script (owner records; async-first)

Put the caption "Staged on synthetic data" on the first screen. Say no accuracy number. Before publishing, check the
frame for your location, personal e-mail or any secret. The planted terminal-control row is shown with its control
sequences removed (a talking point, optional).

| Time | Scene | Type this (from `demos\ask-your-data`) | Say |
|---|---|---|---|
| 0:00-0:20 | Promise | `uv run --locked --no-build --extra askdata python -m askdata verify-readonly` | "Staged on synthetic data. This login cannot write: fourteen checks, all ok, plus two info rows, exit code 0." |
| 0:20-0:50 | Normal question | `... python -m askdata ask "How many orders per country?"` | "The exact SQL that ran, its SHA-256, and the result. The model here is a scripted stand-in, no network." |
| 0:50-1:10 | Refusals | `... ask --sql "DELETE FROM shop.orders"` then `... ask --sql "SELECT email FROM analytics.customers_v"` | "Rejected before it reaches the database: rule V03, rule V05." |
| 1:10-1:30 | Proof | `docker exec -it askdata-pg psql -U askdata_ro -d askdata_demo -c "DELETE FROM shop.orders"` then `uv run ... pytest -q tests/demo_askdata/test_pgsource_layers.py -k c3b` from the repo root | "This is the actual login the tool uses. The database says permission denied even if the tool were wrong. And a stacked-statement attack is refused by the execution path." |

## Tests

From the repo root, with a Postgres reachable: `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55432/postgres`
and `psql` available, `pytest -q tests/demo_askdata`. Without the variable the database tests skip on a laptop and fail
when `CI=true`. The parser oracle (`pglast`, GPL, test group only, never shipped) cross-checks the validator in CI.

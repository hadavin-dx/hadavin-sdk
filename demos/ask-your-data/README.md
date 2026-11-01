# Ask your data (spike)

A staged demo of the safety shape of a text-to-SQL tool, on **synthetic data**. It makes **no accuracy claim** and
calls **no model over the network**: the model is a scripted stand-in (`askdata/scripted.py`). What it shows:

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
`ask` first runs the read-only checks and refuses to start (exit 4) when one is red.

**Exit codes: one table for every command (`askdata/policy.py` is the source; `eval run` has its own 10 to 14 band below).**
0 ok / answered; 1 usage (a bad command line or `ask` with no question; argparse's own exit 2 is mapped to 1); 2 refused (the tool will not do that); 3 failed (the validator rejected the SQL, the database
failed the statement, the SQL hash did not match, the model gave no usable answer, a read-only check is red (in
`verify-readonly`, in `ask`, in `demo` and in the DBA script alike), or `audit verify` found a problem; `setup` passes the
exit 3 of `roles.sql` through);
4 startup (no DSN or config, cannot connect, cannot run the checks, or the server refused the login, SQLSTATE 28xxx);
5 audit unavailable; 6 spending limit or kill switch; 7 abstained (the data does not answer the question, or the
scripted model has no answer). Exit 5 used to mean "database failed" in `ask`; that is now 3.

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
  `killswitch on|off|status`. Exit codes: the table above.
- **Meter** (`askdata/meter.py`): one JSON file shared with the Replay Check; a call needs its worst case to fit under the demo cap
  (US$8) and under the shared cap minus the reserve; a call that fails after sending is charged its worst case.
- **Eval** (`askdata/evalrun.py`, `compare.py`, `evalset.py`, `evalcli.py`): `eval freeze`, `eval run --split dev|test [--k N]
  [--second-look aborted|harness_defect] [--live [--smoke]]`, `eval report <run folder>`, `eval compare <baseline> <candidate>`.
  `eval/lock.json` freezes the file hashes and the gate thresholds (green: upper bound of the confident-wrong rate <= 10 %,
  amber <= 15 %). The sealed test set tolerates one invocation, always with `--k 1` (`--split test --k 3` is refused with
  exit 14; repeats, pass^k, are `--split dev --k 3`). A sealed first run needs US$3.00 remaining in the meter; a
  `--second-look` run needs US$1.80. Run exit codes: 0 green, 10 amber ("promising, not demonstrated"), 11 not
  demonstrated, 12 a hard zero breached, 13 aborted (meter, kill switch or a smoke limit), 14 a sealed run refused,
  4 startup. Compare: 0 no regression, 11 regression, 4 not comparable. Without `--live` the model is the recorded one.
- **Injection gate threshold** (`pipeline.py`, `Settings.injection_threshold` = 0.05). Read this plainly: the regex
  detector scores only 0.0 or 1.0, so **the threshold is inert**: every value from above 0 to 1.0 flags exactly the same
  questions (0.00 would flag everything). The sweep
  (`test_demo_gaps.py::test_injection_threshold_sweep_picks_the_lowest_with_no_false_positive`) shows 0 false positives
  over the 70 gold, 30 adversarial and 12 dev-adversarial questions (112), none of which is injection phrasing, so it
  proves nothing about recall. Recall is measured separately
  (`test_injection_recall_at_the_shipped_threshold_is_measured_not_assumed`): 10 of 10 listed injection phrasings are caught and
  0 of 5 evasions (a misspelling, a paraphrase, a German sentence) are, so 10 of 15 on that small set. The detector is a
  tripwire only; the validator and the read-only login are what stop a bad query.

## Operator runbook (in this order)

1. Copy `askdata.example.yaml` to `askdata.yaml` (it is not committed), set `as_of`, the paths (put `meter_file` OUTSIDE
   the repo, because the Replay Check shares it), the route's model id and today's prices, and optionally the
   `secrets` and `llm` entries. Give `--config askdata.yaml` or set `ASKDATA_CONFIG`.
2. Database login. With `database.dsn_secret_name` set, the DSN is read with `provider.get(name)` from the configured
   core secrets kind (`env`: variable `HADAVIN_SECRET_<NAME>`, dev only; `aws_secrets_manager`, `vault`, ... for a
   client); an unreadable named secret is a startup error, never a silent fallback. With no name set, the DSN is the
   environment variable `ASKDATA_DSN` (the fallback). `database.statement_timeout_s` and `max_bytes` override the
   defaults (10 s, 1,000,000 bytes); the client values are 5 and 2,000,000 (as in the example file).
3. Create the shared meter file once: `python -m askdata --config askdata.yaml meter --init` (this calls
   `Meter.create(path, total_cap="10.00", reserve="1.00", demo_cap="8.00")` and refuses to overwrite an existing file).
4. Type in what the other program spent, from the provider console: `... meter --set-external <USD>` (this writes
   `external_usd` and its timestamp; a live step is refused while the entry is older than 24 hours).
5. Finish the prompt and the dev work. Then `... eval freeze` ONCE: it hashes the four set files, writes `eval/lock.json`
   with the thresholds (10 % / 15 %) and `test_runs` 0, and never overwrites an existing lock (it writes a temp file and
   links it into place, so a crash leaves no empty lock). **Commit `lock.json` to git** (it is not ignored): git history is
   the first guard on the sealed counter and the frozen hashes. The second guard is the hash-chained audit folder: every
   sealed run writes a `sealed_run` event BEFORE the counter moves, and a sealed run is refused when the audit folder and
   `test_runs` disagree, so editing the counter, or deleting and re-freezing the lock, does not reset it silently. Nothing
   in the frozen files or the thresholds changes after this, and no sealed run happens before it. A `--second-look
   harness_defect` needs the proved defect written BY HAND into `lock.json` (`harness_defect_reason`), and consumes it;
   `--second-look aborted` needs the last sealed run to have aborted. Concurrent `eval run --split test` processes are
   serialised by an OS lock on `lock.json.lock`; the second is refused.
6. Dev runs: `... eval run --split dev [--k 3]`. A live smoke (needs the owner's yes and a fresh `external_usd`):
   `... eval run --split dev --live --smoke`; once at least 5 questions are done it aborts (exit 13) when the cost per
   question is more than US$0.035 or more than 10 % of the model attempts are schema violations. A finished smoke run sets
   `smoke_passed` in `lock.json`; `eval run --split test --live` is refused without it. Then one sealed run:
   `... eval run --split test`. The meter reserves the worst case of EVERY request one model call may send (the llm
   kind's `max_attempts`, 3 by default) and settles the real cost of the reply.

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

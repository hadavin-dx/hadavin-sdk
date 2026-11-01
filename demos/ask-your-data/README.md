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

**Exit codes: one table for every command (`askdata/policy.py` is the source; `eval run` adds the 10 to 14 band below).**
`test_every_documented_exit_code_is_produced_by_cli_main` drives each of these through `cli.main`.

| Code | Meaning |
|---|---|
| 0 | ok / answered |
| 1 | usage: a bad command line, or `ask` with no question (argparse's own exit 2 is mapped to 1) |
| 2 | refused: the tool will not do that. A write the validator rejects (rule V03) is 2 in `ask` AND in the pipeline (reason `write_request`), exactly as a model that declines a write |
| 3 | failed: any other validator rejection, the database failed the statement, the SQL hash did not match, no usable model answer, a read-only check is red (`verify-readonly`, `ask`, `demo` and the DBA script alike), `audit verify` found a problem; `setup` passes the exit 3 of `roles.sql` through |
| 4 | startup: no DSN or config, cannot connect, cannot run the checks, or the server refused the login (SQLSTATE 28xxx) |
| 5 | audit unavailable (also `eval run --split test`: the sealed run could not be recorded) |
| 6 | spending limit or kill switch: the pipeline's per-question code (`Answer.exit_code`, tested in `test_exit_6_...`); no CLI command returns it today because `ask` uses the offline scripted model |
| 7 | abstained: the data does not answer the question, or the scripted model has no answer |

`eval run` exits: 0 green, 10 amber, 11 not demonstrated, 12 a hard zero breached, 13 aborted (meter, kill switch or a
smoke limit), 14 refused (budget, `--k`, smoke, counter or chain mismatch, a stale open reservation, second-look rules),
5 the sealed run could not be recorded, 4 startup or a harness defect found mid-run (a gold query that does not run),
1 usage. `eval freeze`: 0 or 4 (a file missing, a lock, chain or anchor already there, or a file system without hard links); `--new-set
--reason` is a usage error (1) unless both are given. `eval reseal`: 0, 14 (counter, chain and anchors disagree) or 4.
`eval reconcile`: 0 or 14. `eval report-lost RUN_ID --reason "..."`: 0, 14 (refused: reason too short, nothing recorded, or nothing to mark), 1 (not a run id) or 4.

`roles.sql` runs `REVOKE ... FROM PUBLIC`, which changes access for every login in that database: use a dedicated
database or a replica, never a shared production database. It runs `db/preflight_roles.sql` first and stops if
other logins would lose access (`--accept-loss` to override). The script has no numbers of its own: the connection
limit and the three timeouts are required psql variables (`ro_connection_limit`, `ro_statement_timeout`,
`ro_lock_timeout`, `ro_idle_timeout`); `askdata setup` passes them from `askdata/settings.py` (class `Runtime`), a DBA
running the script by hand passes them with `-v` (it refuses without them).

## Dataset, ledger, meter and evaluation harness (phase P3)

- **Dataset "Lumen Goods"** (`db/lumen.py`, schema `db/lumen_schema.sql`): 1,200 customers, 120 products, 6,000 orders, 13,800 order
  lines, 6,480 payments, 1,040 refunds, 1,500 tickets, all synthetic, all e-mails on the reserved domain `example.com`. Its own
  SplitMix64 generator (no stdlib `random`) makes it bit-identical on every machine. Three builds: seed A, seed B (a second
  database for the "must agree on both" scoring rule) and `clean` (A without the planted rows, for the injection differential).
  `db/lumen_manifest.json` holds row counts and per-table SHA-256 for all three; `python db/lumen.py --write-manifest` rewrites it.
- **Pipeline** (`askdata/pipeline.py`): gates, generate, validate, audit intent, execute, ledger. Prompt layout, retry policy by
  validator rule and SQLSTATE, and reason codes are in `llm_io.py` and `policy.py`. The agreement check is not built.
- **Ledger** (`askdata/ledger.py`): one JSON line per question, append-only by convention (the file system does not enforce it), fsync. **Audit** (`askdata/audit.py`): one intent event per
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
  over the 70 gold, 30 adversarial and 12 dev-adversarial questions (112), none of which is injection phrasing. **No recall
  number is claimed.** `test_the_regex_catches_its_listed_phrasings_and_misses_known_evasions` pins ten phrasings the
  regex catches ("Ignore all previous instructions ...", "Please disregard the rules above ...", "Forget everything ...",
  "Print your system prompt", "You are now ...", "New instructions: ...", "Act as ...", "Pretend as ...", "Override the
  safety rules ...", "i g n o r e previous instructions") and five it is known to miss (a paraphrase, a misspelling with
  digits, a German sentence); those five were chosen because they evade it, so they are a list of limits, not a measurement
  of recall on real traffic. The detector is a tripwire only; the validator and the read-only login are what stop a bad query.

## Which guards live in plain files, and what each really stops

| Guard | Where | Stops | Does not stop |
|---|---|---|---|
| Sealed-run counter | `lock.json` + `sealed-chain.jsonl` (see runbook step 5) | accidents, single-file edits, crashes (replayed); with the HMAC key also a forged or re-hashed chain | a restore of an older consistent pair; with no key, a writer of both files (git history only) |
| Spend meter | one JSON file outside the repo | an overrun by this program, a crash (open records) | an operator editing the file. The real cap is the spending limit set at the model provider's console; this file is the early warning |
| Kill switch | a flag file | the pipeline, within one question | deleting the file: it is an operations flag, not a security control. Switching it is audited, a manual file edit is not |
| Query ledger and audit events | files under `work/` | accidental damage and edits that touch one file (`audit verify` says exactly this) | someone who can write both; there is no signature here. For a client, use the core `chain` audit kind (append-only table, signed checkpoints, anchors) |

## What each layer does NOT stop (C1 to C5)

| Layer | Does | Does NOT stop |
|---|---|---|
| C1 validator (`validate.py`, V01 to V12) | one canonical SELECT over exposed views, columns and allowed functions | a read-only query that is legal but WRONG (a wrong join, a wrong filter): that is what the eval measures; any SQL the parser mis-parses the way the server does not (the oracle test narrows this, it cannot prove it) |
| C2 read-only login (`db/roles.sql`) | the database refuses every write and every table outside the four views. **Exact rights of the login (least privilege):** CONNECT on the database, USAGE on schema `analytics`, SELECT on the four views `customers_v`, `products_v`, `orders_v`, `order_items_v` (whole views: the columns visible are the views' own column lists, so the exposure is exactly what the view definitions select), plus role settings (default read-only transaction, statement / lock / idle timeouts, `search_path`). Nothing else: no table, no CREATE, no EXECUTE grant. `ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC` in the script has no `FOR ROLE`, so it covers only functions created LATER by the admin that ran the script, not other roles' and not functions that already exist (the validator's function allowlist, not the grant, bounds those). The numbers are validated before use: the connection limit is 1 to 999, a timeout is a positive number of seconds (`0s` would disable it and is refused) | a heavy read inside the views (that is C4); anything the DBA grants to this login later (`verify-readonly` and `preflight_roles.sql` list drift, they do not prevent it) |
| C3 extended-protocol cursor (`pgsource.py`) | a stacked statement cannot run as part of the query | a statement the server runs for a different reason (it is one statement only); a bug in the driver |
| C4 watchdog and caps | rows, bytes and time of ONE statement; the server cancel as a backstop | the sum of many cheap questions (the meter and the kill switch bound those); one huge cell is read whole before the byte cap sees it |
| C5 audit intent before execute | an execution with no intent record cannot start | a ledger or audit folder rewritten by someone who can write both (see "Which guards live in plain files") |

## Known limits, in plain words

* **The injection result is structural, not measured.** In this version no database VALUE ever reaches the model (only
  the question, the catalog and fixed hints do), so a planted instruction in a row cannot steer the model; the
  data-injection items pass by construction. They become a real test only when a value path exists (a profile or a
  sample row in the prompt). Until a test exists where a value does reach the prompt, do not quote this as robustness.
* **The input detector is a binary tripwire.** It scores 0.0 or 1.0, so its threshold is inert. Measured on the shipped
  question sets (70 gold, 30 + 12 adversarial = 112): 0 questions flagged, i.e. a false-positive rate of 0 of 112; with
  112 samples the 95 % upper bound is about 2.7 % (rule of three). No recall is claimed (see the injection note above).
* **The model is scripted in `ask` and `demo`** ("Scripted model, no network" is in the banner). `ask` and `demo` call the
  validator and the database directly: they do NOT go through the pipeline, so they bypass the kill switch, the meter,
  the audit and the ledger. They are a presenter's tool, not the product path; the product path is `Pipeline` (used by
  `eval run`).
* **The gold answers were written by one author (an LLM) with two formulations each**: that is a self-consistency check,
  not independent verification. Only items marked `second_author_checked` have a second reader.
* **Dependencies** (each lives behind one module; pinned in `pyproject.toml`):

| Dependency | Pin | Used in | Cost to replace |
|---|---|---|---|
| sqlglot (MIT) | 30.24.0 | `validate.py` only | high: the validator is built on its tree; another parser means rewriting V01 to V12 and re-running the corpus, fuzz, mutation and oracle suites |
| psycopg[binary] | 3.3.6 | `pgsource.py` only | medium: one send call and the watchdog; another PostgreSQL driver is a few days with the layer tests |
| pydantic, PyYAML | 2.14.1, 6.0.3 | config and item schemas | low |
| pglast (GPL) | 8.7 | tests only, never shipped | none: it is an independent oracle in CI (PostgreSQL grammar of its own version; the server in CI is 17.10, so the oracle's grammar can differ from the server's: the harm test against the real server covers that delta) |
| model SDKs | extras of the core kinds | core `llm` kinds only; the demo imports none (`test_imports.py`) | low: the LLM kind is a config entry |

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
5. Finish the prompt and the dev work. Then `... eval freeze` ONCE: it hashes the four set files and writes `eval/lock.json`
   with the thresholds (10 % / 15 %) and `test_runs` 0. It never overwrites an existing lock (a temp file is linked into
   place, so a crash leaves no empty lock; a file system without hard links gives exit 4). Nothing in the frozen files or
   the thresholds changes after this, and no sealed run happens before it.

   **How the sealed counter is protected, and what it does not stop** (`askdata/sealed.py`, probes in
   `tests/demo_askdata/test_demo_gaps_r3.py` and `_r4.py`). Nothing is trusted from `lock.json` alone.
   * Write-ahead: every sealed run, smoke pass and recovery is first appended to a hash chain,
     `<audit_dir>/sealed-chain.jsonl` (first entry `genesis`), and only then mirrored into `lock.json` with the chain head.
     If the process dies in between, the next command replays the chain over `lock.json` (also consuming a hand-written
     harness defect, exactly as the run would have) and logs a `reconcile` entry; `eval reconcile` does the same on demand.
     A torn final line (power loss mid-write) is cut off and logged the same way. The status of the last sealed run is
     derived from the chain and `report.json`, never from a flag written before the work.
   * The WHOLE of `lock.json` except `seal` is covered by the key's HMAC: files and their hashes, thresholds, the money
     minimums, `max_second_looks`, the counter, the smoke key, the chain head and the hand-written defect fields. The one
     sanctioned hand edit (the defect fields) is blessed by the key holder with `eval reseal`, which logs a `reseal`
     entry. `reseal` blesses ONLY those fields. Every chain entry records the hash of everything else (the "core") and of the
     frozen file hashes, and `reseal` compares `lock.json` with the value the CHAIN recorded at the lock's own position,
     not with a value stored in `lock.json` (which a rewriter could recompute). It refuses when anything else differs
     (files, thresholds, caps, counter) and when no hand field is set. Every ordinary load makes the same comparison,
     keyed or not. Read `git diff lock.json` first anyway.
   * A crashed run's status is not read from a plain file: right after the results are written their `report.json`
     SHA-256 goes into the chain. Results evidence (`report.json`, `report.md` or `results.jsonl` in the run folder) that no
     chain entry vouches for is "unverified" (a second look `aborted` is refused). A recorded report that was DELETED or
     that differs from its recorded hash is refused on every load, for every recorded run, and by `eval report` and
     `eval compare` when a config is given. `report.md` and `results.jsonl` are hashed too. **Run folders are part of the evidence set**: do not prune, move or
     rename `runs/` for a recorded run. If that happened on purpose (a tidy-up, a new machine), the audited way out is
     `eval report-lost RUN_ID --reason "..."` (20+ characters): a `report_lost` chain entry, the run's status becomes
     "unverified" (never an `aborted` second look), the counter is untouched and `eval report` prints the run as LOST with
     the reason. Residual: the hash is taken of whatever is on disk at the moment the run records it, so a report swapped
     between `write_run` and that record is not detected. `eval report` and `eval compare` also check a given report:
     one that LOOKS sealed (its own `split` is test, or its label is sealed / second look, whatever the folder is called)
     and that the chain does not vouch for prints `NOT VOUCHED` and exits 4; without a config they print that they could not
     check; a config that was asked for and cannot be read is an error. While a sealed run is alive it holds an OS run lock
     (`sealed-run.lock`): a second look is refused with "a sealed run is still running" and the status is "aborted" only
     once that process is gone.
   * Anchors: at the first freeze a `set_id` is written to `<audit_dir>/sealed-anchor.json` and to
     `<eval_dir>/anchor.json`, which you COMMIT TO GIT. `eval
     freeze` refuses while a chain or any anchor exists, so deleting the chain and `lock.json` and freezing again does not
     reset the counter. Deleting just ONE anchor is refused too.
     A genuinely new test set needs `eval freeze --new-set --reason "..." [--discard-count N]`. **That command RESETS the
     sealed counter**: the reason must be 20+ characters, and while N runs are counted you must pass `--discard-count N`;
     both are written into a visible `new_set` entry, the old lock is kept as `lock.json.prev-<time>`, the old runs stay in
     the chain, and a failed freeze undoes what IT created (chain entry, new lock, new anchors, backups) without touching
     anything that existed before it. If an undo step itself fails, the freeze reports every problem, writes
     `FREEZE-RECOVERY.txt` and nothing loads until that is resolved by hand.
   * Keyed or not (decide before the first sealed run; the default for a client is KEYED): `sealed_key_secret_name` names a
     secret in the `secrets` kind (16+ characters). With it the chain is HMAC-SHA256 and `lock.json` carries a `seal`, so
     someone without the key cannot forge a line or re-hash the chain. Once a set was keyed, a gate with no key is refused
     (lock, anchors and genesis all say so), and a DIFFERENT key is refused (the key id, not the key, is recorded in the
     genesis entry and the anchors). Without a key (`freeze` prints "NOT keyed"): the chain is plain SHA-256,
     anyone who can write the audit folder can recompute it, and a writer of every file can reset the counter. The
     counter is then tamper-resistant only by git history: **commit `lock.json` (and the anchor) after every sealed run**.
   * Still not stopped, with or without a key. **Rolling back is EASY, even with a key**: the old `lock.json` from git
     (its seal is still valid) plus the current chain cut back to that lock's `chain_head` (a prefix of an HMAC chain
     verifies) is a consistent older state, and the anchors hold only the set id, the keyed flag and the key id, so they do
     not object. The counter goes back to what it was. One cheap detection exists: a sealed or second-look run FOLDER that
     holds results but whose run the chain does not record is refused ("look rolled back"); it works only while `runs/` is
     intact. A harder guard (the head and count written into the committed anchor after every run) was left out on
     purpose: it forces a git commit after every sealed run, which an operator forgets, and a missing commit then blocks
     the next run. Deleting the chain, the lock and every anchor when no anchor is committed to git also resets it.
     Only git history and an off-machine copy of the chain's last `sha` can tell. The chain lives on the same disk as the
     code that checks it: it is tamper-EVIDENCE, not a safe.
   * **"Keyed" is only as strong as where it is anchored.** Every guard here is a plain file. Someone who can write ALL
     of them (lock, chain, both anchors) can re-create the set as an unkeyed one and start from zero; the tests pin that
     this works (`test_a_full_rewrite_of_every_file_as_a_keyless_set_succeeds...`). The real control for a client is the
     core `chain` audit kind (an append-only table with signed checkpoints and anchors held elsewhere), or a committed,
     reviewed key-id witness; neither is wired into this demo.
   * A set frozen WITHOUT a key cannot be upgraded to keyed in place: the chain and the lock were written with plain
     SHA-256 and a key would make them "broken". The only path is `eval freeze --new-set --reason ... --discard-count N`,
     which resets the count; decide on the key before the first sealed run.
   * Concurrent runs are serialised by an OS lock on `lock.json.lock`.

   A `--second-look harness_defect` needs the proved defect written BY HAND into `lock.json`: `harness_defect_reason`
   (10+ characters), `harness_defect_run` (an existing run folder) and `harness_defect_item` (an id in the frozen test
   files); one defect buys one second look. `harness_defect_run` must be a SEALED run that is in the chain (a dev run or an unrecorded folder is refused).
   `--second-look aborted` needs the last sealed run to be aborted: its process gone (run lock free) and NO results
   evidence in its folder (no `report.json`, `report.md` or `results.jsonl`), or a recorded report that itself says aborted. At most `max_second_looks` (2) second looks exist in total.
6. Dev runs: `... eval run --split dev [--k 3]`. A live smoke (needs the owner's yes and a fresh `external_usd`):
   `... eval run --split dev --live --smoke`. One question costing more than US$0.35 aborts it at once; from 5 questions on
   it aborts (exit 13) when the cost per question is more than US$0.035 or more than 10 % of the model attempts are
   schema violations. A finished smoke run is recorded (chain entry `smoke_pass`, key = config hash plus model id);
   `eval run --split test --live` is refused unless the CURRENT config and model match the last smoke pass. Then one
   sealed run: `... eval run --split test`.
7. Spend. The meter is a two-phase reserve/settle: `reserve` books the worst case of EVERY request one model call may send
   (the llm kind's `max_attempts`, 3 by default; the prompt AND the forced tool schema are counted) and records an `open`
   reservation; `settle` charges what was really spent (the reply's cost plus one worst case for each earlier request that
   was sent, `meter.call_cost`) and closes it. A process that dies in between leaves the worst case booked and an open
   record: `meter` shows it, a live run refuses to start while one is older than 10 minutes, and after reading the provider
   console you clear it with `... meter --clear-open`.

## 90-second recording script (owner records; async-first)

Put the caption "Staged on synthetic data" on the first screen. Say no accuracy number. Before publishing, check the
frame for your location, personal e-mail or any secret. The planted terminal-control row is shown with its control
sequences removed (a talking point, optional).

| Time | Scene | Type this (from `demos\ask-your-data`) | Say |
|---|---|---|---|
| 0:00-0:20 | Promise | `uv run --locked --no-build --extra askdata python -m askdata verify-readonly` | "Staged on synthetic data. This login cannot write: [read the check count from the last line on screen], all ok, exit code 0." |
| 0:20-0:50 | Normal question | `... python -m askdata ask "How many orders per country?"` | "The exact SQL that ran, its SHA-256, and the result. The model here is a scripted stand-in, no network." |
| 0:50-1:10 | Refusals | `... ask --sql "DELETE FROM shop.orders"` then `... ask --sql "SELECT email FROM analytics.customers_v"` | "Rejected before it reaches the database: rule V03, rule V05." |
| 1:10-1:30 | Proof | `docker exec -it askdata-pg psql -U askdata_ro -d askdata_demo -c "DELETE FROM shop.orders"` then `uv run ... pytest -q tests/demo_askdata/test_pgsource_layers.py -k c3b` from the repo root | "This is the actual login the tool uses. The database says permission denied even if the tool were wrong. And a stacked-statement attack is refused by the execution path." |

## Tests

From the repo root, with a Postgres reachable: `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55432/postgres`
and `psql` available, `pytest -q tests/demo_askdata`. Without the variable the database tests skip on a laptop and fail
when `CI=true`. The parser oracle (`pglast`, GPL, test group only, never shipped) cross-checks the validator in CI.

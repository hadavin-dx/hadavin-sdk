# Core hardening hand-off v3 (R460), 2026-11-16 (UTC) / 2026-11-16 (IST)

Replaces v2 (kept unchanged). Fixes the two readiness Blockers and ten Majors, the ten zoom-out Majors and the nits. Status words used below: **specified, unverified** = written from code I read but nothing was run; **needs lead** = a decision only the lead or owner can make, with a safe default stated.

## 0. What failed, what is uncertain, what was not run (read first)

1. **Nothing was run.** No tests, no `ruff`, no `bandit`, no Postgres, no redaction canary, no G4 string. `markdown_it` is not installed in this sandbox, so `approvals.gate` cannot even be imported here. Every G4 and redaction statement below was hand-traced from the code and is **specified, unverified**. The E0 evidence batch (section 7) is what turns them into facts.
2. **Not read:** adapter bodies (`llm/openai_compat`, cloud adapters), Postgres behaviour of the new reservation table, `tests/test_k5_layers.py` and `tests/test_lockin_guard.py` layer rules (needed for the `fileguard` and `llm/guarded.py` import rules), the demos pipeline, the file mode of key files created by test fixtures, `ledger.md`, `ci.yml`.
3. **v2 was wrong in six places** (corrected here): (a) only `extract()` sends a raw document to a model, the judge (`guard/judge.py`) and `evals.gate` already mask; (b) the old k5 pin test (`tests/test_k5_tools.py:717-731`) does not need rewriting, only `tests/test_s5_runtime.py:107-111` changes; (c) the existing key-file reader (`actions/secrets_file.py`) already refuses a world-readable (0644) file, the real gap is the signer key read in `audit/signer.py:104-108`; (d) "PR-M6" does not exist; (e) `with_retry` is `llm/retry.py:83-108`; (f) `table.py:604` is `NOT_PROD`, it has no "dev" reference (`DEV_ONLY` is at `table.py:594`).
4. **v2 over-claimed** "every reviewer Blocker and Major is answered". v3 says only: each is *specified*; none is *verified*.
5. **Arithmetic caveat (moved here from the end):** every token and dollar figure in this document (for example "reserve about 0.0155 on the default route") uses the estimator in `llm/common.py` (3 characters per token) and the fixture route 3.00 / 15.00 / max_tokens 1024. Treat the numbers as unverified until E0-5 prints them.
6. **Third-party limit that cannot be fixed in code (exception 2c):** if a provider bills an attempt that failed before a reply arrived, we cannot see it. Next step: a monthly reconcile of our ledger against the vendor invoice. Owner: lead. Date: 2026-11-16 to name the person, first reconcile with the first live window.

## 1. Facts (corrected)

| # | Fact | Source read |
|---|---|---|
| F1 | G4 is a display filter: it swaps commands in model-written approval text for `[command withheld (G4)]`. It does not decide whether a tool runs. | `approvals/gate.py:367-698`, `approvals/channel.py` |
| F2 | G4 is a closed list of programs (`_NAMES`) with a read-only subcommand table (`_VERB_FIRST`, `_WORD_RUN`, `_AWS_READ_PREFIXES`) plus a denylist of write shapes (`_WRITE_SHAPES`). Prose exemptions: `_story`, `_ENGLISH`, `_OWN`, `_PROSE_QUOTE`. | gate.py |
| F3 | Line-continuation bypass: the first-token test at `gate.py:614` treats punctuation or a capitalised word as prose. | gate.py |
| F4 | `LLM.chat(messages, *, system, route, tools, documents, output_schema)` has no context argument; test doubles (`ScriptLLM`, `CostLLM`, `FakeLLM`) use that exact signature. | `llm/protocol.py`, `tests/k5_support.py` |
| F5 | Today the model call happens first and the charge after (`runtime/agent_loop.py:424-441`). `limits.charge` and `store.add_cost` are two separate writes. | agent_loop.py |
| F6 | Retries happen inside one `chat()` (`llm/retry.py:83-108`). `ProviderError` = not retried; `ProviderExhausted(ProviderError)` = retried and gave up. The caller cannot see the attempt count. | retry.py, protocol.py |
| F7 | `limits.blocked` reads `registry.agents[agent_id]`, so a made-up id such as `eval:x` raises `KeyError`. | `limits.py` |
| F8 | `app.py:162` builds the `llm` before `Limits(...)`; `Limits` needs only store, audit, registry, so the line can move up. | `app.py` |
| F9 | Model callers (no `.chat(` outside kinds is false today): `extract.py`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94`. Blocked-check callers also include `agent_loop.py:744` and `actions/authorizer.py:44`. | grep + reads |
| F10 | `k1b/loop.py` uses its own in-process `Budget`, never the Store. `worst_case_usd(route, system, messages)` is at `k1b/loop.py:115-122`. `k1b/replay.py:85-90` refuses zero prices unless `llm_kind == "fake"`. | k1b |
| F11 | `ChainAudit(checkpoint_every=100)`. `Verification` has `rows, signed_through, problems, unreadable, ok, unsigned_tail` only. The CLI prints "N not signed yet". | `audit/chain.py:134-150`, `cli.py` |
| F12 | `mounted_file._fetch` uses `confined()`, then `O_NOFOLLOW|O_NONBLOCK`, `fstat`, `S_ISREG`; refuses other-readable and group/other-writable; allows group-read (Kubernetes 0440 mounts). `audit/signer.py:104-108` uses `is_file()` + `read_bytes()` with no checks. | secrets_file.py, signer.py |
| F13 | `Config.environment: Literal["dev","pilot","prod"]` (`config.py:317`); `DEV_ONLY` used at `config.py:366-367`; `load_config` turns pydantic `ValueError` into `ConfigError` via `str(exc)` (`config.py:453`). | config.py |
| F14 | `Money` accepts Decimal, rejects floats only (`config.py:47`); `Budget(daily, monthly)` has no sign or order checks (`registry.py:33-36`). | config.py, registry.py |
| F15 | `k5_cfg(config=...)` does a shallow `dict.update`: passing `routes` replaces the whole routes dict. `build_runtime` in `tests/k5_support.py` builds `Runtime` directly, not through `app.py`. | k5_support.py |

## 2. Ladder (rung table, per R448 CODE-LAST)

| Component | Rung | Why lower rungs were rejected |
|---|---|---|
| Spend reserve/settle, call scope, stage rule, G4 grammar, redaction patterns, audit verdict, key-file check | 7 custom code (money, redaction, audit, approval text) | Brain by definition. No ready-made tool holds our approval or money rules. |
| Monthly provider invoice reconcile | 2/3 (provider's own invoice export, a sheet) | No code needed. |
| Alerts on wall hit / outbox age | 3 (existing notification kind, or n8n webhook per client choice) | Only plumbing; the condition is computed in our code. |

## 3. Decisions table (lead or owner; each has a safe default that ships if nobody answers)

| ID | Question | Safe default (used until answered) | Who | By |
|---|---|---|---|---|
| D1 | Spend window end date | New `Config.spend_window_end`. Demo and pilot with a real (not fake) model kind: a date is required. Prod: a date or the explicit word `none`; silence is refused; `none` is written to the audit log at start-up. | lead confirms; owner told (model-cost owner rule) | before PR-M1 |
| D5 | Money as Decimal or integer minor units | Keep Decimal; reject negative and non-finite values in `Budget` and `Route` (tested). CLAUDE.md says integers, so the owner decides. | owner | 2026-11-16, before PR-M2a |
| D6 | Stage name `dev` | Follow R449: refuse `dev`, rename to `demo`, error text names the rename. An alias for one release would contradict R449, so it needs the owner's yes. | owner (alias only) | before PR-0 merge |
| D11 | Zero-price routes | Refuse at registry load unless `backends.llm.kind == "fake"` (same rule as `k1b/replay.py:85-90`). The flag `self_hosted_zero_cost` and the calls cap are deferred. Trigger: first client build with a self-hosted model route. | lead | on trigger |
| D12 | Local billing day | Keep UTC. Trigger: a client asks for a local day. A mid-month switch does not double count; the month edge moves by at most the zone offset (up to 14 h). | lead | on trigger |
| D4 | Refuse signer/anchor kind `none` in pilot | Warn only until decided. Hard deadline: before the first pilot config is written. | owner | before first pilot config |
| FA | False-abstain ceiling for M2b (see `.claude/rules/false-abstain-reporting.md`) | 0 new abstains on the golden set, `limits.*` and `run_budget` stops counted separately as "policy stops". | lead, set in eval-contract before M2b | before M2b |
| RC | Round caps | PR-0, G1, E3 capped at 2 rounds. M, R, A, S PRs and G2-G5 uncapped (approval text is a security path). | lead | now |

## 4. Designs

### 4.1 Call scope (answers readiness Blocker 1, majors 4, 5, 13)

The `LLM` protocol is **not changed**. A wrapper does the work.

- New module `hadavin_sdk/llm/guarded.py`.
- `SpendScope` (frozen dataclass): `agent_id: str`, `run_id: str | None`, `purpose: Literal["run","screen","eval","extract"]`, `ledger: Literal["agent","eval"]`, `run_cap_usd: Decimal | None`.
- `GuardedLLM(inner, limits, routes)` implements `chat(...)` with the same signature as the protocol. It reads the current scope from a `ContextVar` set by `with guarded.scope(SpendScope(...)):`. One mechanism only.
- Fail closed: a non-fake kind with no scope raises `SpendScopeMissing`. The fake kind passes through unbooked (tests keep working).
- Pricing: it looks up the route by name in `routes` (so the "call sites have only a route name" nit is gone).
- `app.py`: move `limits = Limits(store, audit, reg)` above line 162, then `llm = GuardedLLM(llm or make("llm", b.llm, secrets, routes=cfg.routes), limits, cfg.routes)`. Detectors built with `llm=llm` get the wrapped one.
- **Who opens the scope:**
  - `Runtime.handle`: scope `run` (agent ledger, `max_run_usd`). `_screen` (judge) runs in the caller thread, so the same scope covers it with `purpose="screen"`.
  - `evals.gate`: scope `eval`, ledger `eval`, never calls `Limits.blocked` with a pseudo agent id (fixes F7). Caps come from new config `eval_budget_usd` (daily and monthly, same shape as `Budget`). Default 0 = no live eval spend; fake kind stays free.
  - `extract()`: does not open a scope itself; its caller does. Test: a live `GuardedLLM` outside a scope raises, inside a scope books.
  - `k1b` replay: **out of scope of the store ledger.** It keeps its own in-process `Budget` (the daemon thread never sees a ContextVar, so this is deliberate). Fixes: `worst_case_usd` moves to `llm/common.py` taking a `Route`; the caller (which holds `route_prices`) checks it before the call; replay refuses to start when `route_prices is None`. A repo test lists the allowed "own meter" callers (k1b only) and fails for any other module that calls `.chat(` without going through `GuardedLLM`. This replaces v2's false "only llm/guarded.py and kinds call .chat".
- Deleted from v2: `on_reply`, `on_attempt`, `book_cost`. The seam sees the reply (including a reply that later fails to parse), so nothing else is needed.

### 4.2 Retry booking and ledger total (readiness Major 3)

One mechanism, at the seam, around the whole `inner.chat()` (which includes its retries):

1. `reserve` the worst case (`worst_case_usd` = estimated input tokens x input price + `max_tokens` x output price) before the call.
2. Success: `settle` with the real `reply.cost_usd`.
3. `ProviderError` (not retried): release the reservation.
4. `ProviderExhausted`: keep exactly **one** worst case booked, not x `max_attempts`.
5. Failed attempts before a later success are not booked (third-party limit, section 0 item 6).

Expected ledger totals, to be pinned by tests: success = actual cost; `ProviderError` = 0; `ProviderExhausted` = one worst case.

### 4.3 Store API and crash safety (zoom M4, M6, M7; readiness 20)

- **PR-M2a** (store only, no callers): `reserve_spend(agent_key, run_id, day, usd) -> Reservation`, `settle_spend(reservation, actual_usd)`, `release_spend(reservation)`, `try_mark_wall_notice(agent_id, day, code) -> bool`, plus table `spend_reservations(reserve_id, agent_key, run_id, day, usd, state, created_at)` with state `open | settled | expired_kept`. Contract tests run on both stores. The Postgres migration is **specified, unverified**.
- `Reservation` stores its `day`; settle uses it, so a call across midnight or a timezone change cannot move spend to another day.
- `settle_spend` never raises after the provider billed: it clamps counters at 0 and logs `spend_clamped`.
- Crash between reserve and settle: a sweep at start-up and on tick marks `open` reservations older than a config TTL (default 900 s) as `expired_kept`. They stay counted (we cannot know what was billed), and are written to audit, logged and queryable. A refund is an audited operator action only.
- **PR-M2b**: wire the seam across the loop, judge screen, evals and extract (section 4.1). `book_cost` is never built.
- Test changes: add a **new** test with a full `routes` override (replaces the whole dict, F15) so a 0.30 reply exceeds its reserve; keep `tests/test_k5_tools.py:717-731`. Change only `tests/test_s5_runtime.py:107-111` (0.999 spent, remaining 0.001: under reserve this becomes NEEDS_PERSON `limits.daily_budget` with no model call). Keep the gate-DENIED path with a new test whose fake charges 0.98 on a 0.05 reply.

### 4.4 Wall hit: card and dedupe (readiness 9, zoom M9)

First wall hit per agent, day and code posts one card through `_abstain` (decided by `try_mark_wall_notice`, insert-if-absent). Later runs end NEEDS_PERSON `limits.*` with an audit row and no card. `limits.*` and `run_budget` go into a `POLICY_STOP_REASONS` set, excluded from the false-abstain numerator and reported as a separate policy-stop rate. Test D9 asserts one card for N blocked runs.

### 4.5 D1 window end

`Config.spend_window_end: AwareDatetime | Literal["none"] | None`; rule in section 3. `Limits.blocked` returns `window_ended` after the date. Tests: demo/pilot with live kind and no date refused; prod with no value refused; prod with `none` accepted and audited; date in the past blocks.

### 4.6 D11 zero prices

`registry._cross_check` refuses a route with zero input or output price unless `backends.llm.kind == "fake"`. Move the logic from `k1b/replay.py:85-90`; keep the replay test. Judge route (`judge.py:3-4`) is checked too, since it is a route not tied to one agent. Flag and calls cap deferred with the trigger in section 3.

### 4.7 D6 stage rename (readiness 8, zoom M2)

Mechanism: `field_validator("environment", mode="before")` on `Config` raises `ValueError("environment 'dev' was renamed to 'demo'; change it in your config")`. `load_config` converts it to `ConfigError` through `str(exc)` (config.py:453).

Sites to change (real value or logic): `config.py:317`, `config.py:366-367`, `config.py:19` (import), `backends/table.py:594` (`DEV_ONLY` becomes `DEMO_ONLY`), `tests/test_lockin_guard.py:18,430`, `tests/fixtures/config/config.yaml:2`, `tests/test_p4_secrets.py:106`, `tests/warden_port/test_audit_chain.py:568`, `tests/test_p1b_backends.py:~89-91`.
Wording or comment sites: `secrets_env.py:1`, `audit/signer.py:64,98`, `table.py:126,214,254,591`, `config.py:346`, `defaults.py:100`, `registry.py:50`, `tools.py:361`, `agent_loop.py:179,553,572`, `actions/contract.py:34`, `store/postgres.py:75,90`.
`registry.py` `_module_pin_problems` and `deferred.py` (`LIVE`) have no "dev" literal and need no change. `guard/redact.py:1162` "dev" is a word list, not a stage check; leave.
Add a CHANGELOG upgrade step (history at `CHANGELOG.md:198` stays). Demo repos pin core shas, so nothing breaks until they re-pin; E0-8 greps demos and configs for `environment: dev`. PR-0 is round-capped at 2.

### 4.8 Audit verdict (readiness 6, zoom N5)

Add to `Verification`: `signed` (public key present and at least one checkpoint verified), `anchored` (anchors configured and readable), `anchor_age_s` (seconds since the newest anchored checkpoint, from the anchor listing), `outside_chain` (outbox rows not yet in the chain).
`tamper_evident = ok and signed and anchored and unsigned_tail <= max_unsigned_tail`. `max_unsigned_tail` defaults to `checkpoint_every` (100) and is configurable; the tick checkpoint normally keeps the tail small, so a healthy chain can be true. `cli.audit_verify` prints the threshold and what unsigned tail rows lack; exit codes unchanged (0 intact, 1 not intact, 3 unreadable). Tests on `ChainAudit` with an in-memory store (no Postgres) for: healthy true, no key false, tail above threshold false, anchors off false.
Merge D2 into D3 and E1 into E3. Other D3-D6 details: `retain_days` floor of 7 in pilot/prod from a config key (default documented near `table.py:155`); `outbox_alert_age_s` default 3600; the anchor-writer identity is its own config field; the S3 Object Lock probe is a new function modelled on the GCS and Azure `probed()` checks; negative tests needing Postgres are marked **unverified** and have an in-memory twin where one exists. The D6 identity split is a design item, not a build PR, until the lead decides.

### 4.9 E2 private file read (readiness 7)

New neutral module `hadavin_sdk/fileguard.py`: `read_private_file(path: Path, *, what: str, allow_group_read: bool = False, max_bytes: int = 65536) -> bytes`.
Rules: refuse a symlink as the final component (`O_NOFOLLOW` on the path as given, no `confined()` resolve first); refuse other-readable and group/other-writable; refuse group-read unless `allow_group_read=True`; refuse non-regular files; cap size.
Callers: `mounted_file._fetch` keeps `confined()` first, then calls it with `allow_group_read=True` (Kubernetes 0440 mounts keep working; existing secrets_file tests unchanged). `audit/signer.build_local` calls it with `False`. Test fixtures that write keys must create them 0600 (their current mode is unchecked). Layer test: allow `fileguard` as an import for `audit` and `actions` (rules in `tests/test_k5_layers.py` and `tests/test_lockin_guard.py` not read, **specified, unverified**).

### 4.10 Redaction PRs R1-R3 (readiness 12; merged R1+R3 per zoom N2)

Patterns in `guard/redact.py` (`PATTERNS` at line 153):
- PHONE (~470): accept `( ) . /` separators. Withheld example `(415) 555-0132`; shown near-miss: a date `2026-11-16`.
- IBAN (247): spaced 4-character groups and lower case, normalised before matching.
- CREDITCARD (451): 15-digit 4-6-5 grouping, 17-19 digits, dot separator.
- EMAIL (236): non-ASCII local part, quoted local part, quoted-printable soft break.
- Generic credential pair `{"name": "<credential key>", "value": "..."}` in either order, case-insensitive, modelled on the HAR cookie pair (~513); share the credential-key test with `k1b/redaction.py` `_pair`. Also URL credentials (signed-URL signature parameters, reset-link path tokens, unlisted webhook URLs, vendor key prefixes in `_KEY_PREFIXES`) and bare `passphrase`, `cvv`, `pin`, `dob` keys.
- A base64 second pass (decode, redact, keep only if something changed).
Each pattern gets a canary test (fake values built from parts; the only literal allowed is `AKIAIOSFODNN7EXAMPLE`) and a near-miss test. `4111` also appears in `tests/warden_port/privacy_corpus.py:42` and `tests/test_redaction.py:309,356`.
**PR-2 (extract):** the only real raw-document leak. Mask the document before `llm.chat`, using `runmap.redact_text`; replayed `reply.text` is unchanged. Recorded `FakeLLM` replies are keyed on `sha256(documents[0])`, so recordings are re-keyed in the same PR. Row 36 of `guard/producers.py` (`safe_head` only) is reworded so it no longer implies the document is protected. PR-2b input tripwire depends on E0-4 (redacting masked text is a fixed point).

## 5. G4 specs (readiness Blocker 2, zoom M8)

**Allowlist alternative: decided, rejected for now.** A whole-line allowlist ("show only known read-only commands or prose, withhold the rest") needs a way to say what prose is; prose is unbounded, so it would withhold ordinary sentences and break the false-positive budget (at most 2% of at least 200 prose sentences), and cards would become unreadable. G4 is a display filter, not the executor, so a residual bypass shows text but runs nothing. Keep the hybrid through G5. **Trigger to move to a command-position allowlist:** the E0-6 corpus run shows a bypass class that shapes cannot cover, or measures false positives under 2% with room to spare.

Each row: function, rule, one example that must be withheld, one that must stay shown. All **specified, unverified** (E0-6 runs them).

| PR | Function / constant in gate.py | Rule | Withheld | Shown |
|---|---|---|---|---|
| G1 | docstrings at `gate.py:4`, `gate.py:366-377`, `channel.py:20-21` | Say "a closed list of programs plus SQL and shell shapes", not "any platform, fail closed". Wording only; capped 2 rounds. | n/a | n/a |
| G2 | new `_join_continuations(text)` run before `_PROGRAM` | Join backslash+newline, `^`+newline (cmd), backtick+newline (PowerShell). | `kubectl \` newline `delete ns prod` | `we use a backslash \` newline `to wrap lines` |
| G2 | `_PROGRAM` name normaliser | Fold case, strip `.exe/.ps1/.cmd`, strip version suffix (`kubectl-1.28`), map `tf` to terraform. | `KUBECTL.EXE delete ns prod` | `the tf module was reviewed` |
| G2 | `_story` (line ~614) | Punctuation or capital first token is prose only if the next word is not a known program. | `> /dev/null kubectl delete pod x` (punctuation first) | `Then we waited.` |
| G3 | SQL shapes in `_WRITE_SHAPES` | Lower or upper case; verb + object + `from/set/into/table` in that order; allow `/**/` as space. | `drop table users` | `drop table pressure` (pinned) and `we should delete from the queue only after a fix` (pinned) |
| G3 | SQL breadth | UPDATE with alias/ONLY/quoted name, INSERT IGNORE/REPLACE, COPY, LOAD DATA, CREATE/DROP of any object kind, ALTER ... MODIFY/CHANGE, ALTER USER/ROLE, GRANT/REVOKE, `nextval`, `setval`, `pg_reload_conf`, VACUUM, CALL, EXEC, DO. | `update only t as a set x=1` | `update its set of rules` (pinned) |
| G4 | new `_WRITE_SHAPES` entries | `dd of=`, `mkfs`, `chmod -R`, `kill`, `shutdown`, `service ... stop`, `eksctl delete`, `cdk destroy`, `dropdb`, `crontab -r`, `sed -i`, `rsync --delete`, redirect `>`/`>>` to a path, `tee`, `curl -X DELETE`, `ssh host 'rm ...'`. | `crontab -r` | `we should kill the idea` |
| G4 | `rm` shape | Any flag set (`-v -rf`, `-i -r`, `--no-preserve-root`), plus `find ... -delete`, `shred`, `unlink`, `truncate -s0`. Plain `rm x` withheld unless the next word is a determiner (the, a, an, this, that, it, your, my, our). | `rm -v -rf /x` | `rm the file` (pinned) |
| G4 | download-and-run | `\| sh/bash/python3/perl/node`, `source <(curl ..)`, `eval "$(curl ..)"`, `curl -o x u && sh x`, `base64 -d \| sh`, `python -c "...rmtree"`. | `curl -s u \| python3` | `we fetched the page with curl` |
| G4 | PowerShell | Verb-based (`Remove-*`, `Stop-*`, `Set-*`, `Invoke-Expression`) plus aliases `ri del rd kill`, cmd `rd /s /q`. Keep the pending id patch (`(?![0-9a-f]{32,}\b)`) and its test (mark `perf`). | `Remove-SQSQueue -QueueUrl x` | `the Remove-EC2 report listed ids` is judged by E0-6; an id like `ec2` + 32 hex stays shown |
| G5 | `_story` / `_PROSE_QUOTE` | A quoted command is prose only if no write verb or known program follows the quote start. | `Please run the 'terraform destroy' now` | `a 'kubectl rollout restart' replaced the pods` (pinned) |
| G5 | `_WRITE_VERBS`, `_OWN` | Add `checkout, clean, commit, merge, rebase, pull`. An unknown subcommand of a known program is NOT prose unless the program is in `_ENGLISH` and the next word is plain English. | `git update-ref -d refs/heads/x` | `the docker image was rebuilt overnight` (pinned) |
| G5 | read-verb-with-write-flag | A read verb does not clear the whole command if a write flag follows: `git diff --output=/x`, `git -c core.fsmonitor=.. status`, `git reflog expire`, `terraform plan -out=`. | `git diff --output=/etc/cron.d/x` | `git diff main` |
| G5 | capital-first positional | `mysql Shop -e "delete from x"`, `psql Prod -c "drop table x"`, `ansible Prod -m command -a reboot` are not prose when a known program leads. | `psql Prod -c "drop table x"` | `Prod was quiet today` |
| G5 | `_AWS_READ_PREFIXES` | `get-secret-value`, `get-session-token` are not read-only; remove them. | `aws secretsmanager get-secret-value --secret-id x` | `aws s3 ls` |

Pinned prose that must stay shown: `rm the file`, `drop table pressure`, `we should delete from the queue only after a fix`, `a 'kubectl rollout restart' replaced the pods`, `the docker image was rebuilt overnight`, `update its set of rules`. New tests are proven to fail on the old code (class-level-fixes) by running them first on the unchanged gate in E0-6. G2-G5 uncapped rounds; G1 capped.

## 6. PR series and waves (round-cap tag: U = uncapped security/money/redaction/audit/secret, C = capped at 2)

| Wave | PR | Content | Cap |
|---|---|---|---|
| 0 | PR-0 | D6 stage rename (4.7) | C |
| 0 | G0/G1 | G4 wording fix | C |
| 1 | M1 | D1 window end, D5 Decimal guards, D11 zero-price refusal | U |
| 1 | M2a | Store reserve/settle/release, reservations table, wall-notice store method, sweep | U |
| 1 | R1+R3 | Redaction pattern gaps (4.10) | U |
| 1 | PR-2 | extract masks document | U |
| 1 | G2, G3 | G4 grammar part 1 | U |
| 2 | M2b | GuardedLLM seam wiring, eval budget, wall-hit dedupe, k1b pre-call check | U |
| 2 | R2 | Credential pair and URL credentials | U |
| 2 | G4, G5 | G4 grammar part 2 | U |
| 2 | A1 | D1/audit verdict, merged D2+D3 | U |
| 3 | A2 | D4-D6 audit retention, outbox, anchor writer, Object Lock probe | U |
| 3 | S1 | E2 `fileguard` | U |
| 3 | E3 | merged E1 evidence docs | C |

Deferred with trigger: calls cap and `self_hosted_zero_cost` (self-hosted route), local billing day (client request).

## 7. Evidence batch E0 (an EVIDENCE RUNNER runs these; the runner never judges)

- E0-1 full `pytest`, `ruff check`, `ruff format --check`, `bandit -ll` at the final head, one run.
- E0-2 mutation sample (changed mutants plus 60-mutant sample), full run once, alone.
- E0-3 contract tests of the reservation API on both stores (Postgres via `HADAVIN_TEST_PG_DSN`).
- E0-4 redaction of already-masked text is a fixed point; canary per new pattern; fuzz `redact_text` on random text.
- E0-5 **reserve-sizing dry run** over every fixture and demo config route and agent: print `worst_case_usd` for an empty call and a full-context call, flag any reserve above 50% of the daily cap or the run cap. Keep the `deferred.check` load-time refusal for an empty-call worst case above `max_run_usd`.
- E0-6 feed every G4 table row, every pinned prose line and the recorded corpus to `withhold_commands` and `channel.clean` on old and new code; measure false positives on at least 200 prose sentences (budget 2%). Run the new tests on the old code to show they fail.
- E0-7 `Money`/`Budget` with NaN, infinity, negative; documents-recording fake across `extract`, `evals`, `guard/judge`.
- E0-8 grep stage sites and `environment: dev` in demos and configs.
- E0-9 false-abstain split on the golden set: answerable abstains over answerable questions, with policy stops listed separately; never write "N/M correct" without the split.

## 8. Item homes

| Item | Home |
|---|---|
| Money guard, reservations, wall notice | M1, M2a, M2b |
| Redaction gaps | R1+R3, R2, PR-2 |
| Approval text | G1-G5 |
| Audit verdict, retention, outbox | A1, A2 |
| Key file read | S1 |
| Stage rename | PR-0 |
| Provider invoice reconcile (third party) | owner/lead, monthly |

## 9. Not checked (repeat of section 0 item 2, so it is not lost)

Adapter bodies; Postgres behaviour of the new table; `test_k5_layers.py` and `test_lockin_guard.py` layer rules; demos pipeline; mode of test key fixtures; `ledger.md`; `ci.yml`; bible R-numbers beyond the R447-R450 extract. Nothing in this document is "verified"; the lead runs the EGM review on this hand-off and on each PR.

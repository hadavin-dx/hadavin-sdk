# Changelog

## Unreleased

### Upgrade steps
- **K6 measurement, demotion and the weekly report.** Run `hadavin-sdk migrate --runtime-role R` (migration
  `0005_measure.sql`): new tables `labels`, `level_events`, `reports`, the column `tick_state.detail` and the views
  `v_pilot_week`, `v_caught_week`, `v_approval_week`. **Merge order:** migration numbers must run without a gap; if
  another migration lands first, renumber this file at rebase (the ledger test says so).
  - `Store` gains `add_label` (label and demotion in one transaction), `list_labels`, `list_labels_for`,
    `list_labels_between`, `count_proposals`, `add_level_event`, `list_level_events`, `current_overrides`,
    `held_run_ids`, `put_report`, `get_report`, `pilot_week`, `approval_week`. A custom store kind must implement
    them. `TickState` gains `detail` (JSON, counts and codes only); a tick step sets `ctx.detail[step.name]`.
  - `Principal.admin_rights` (`stop`, `reset`, `clear_override`, `approve_label_import`) is separate from `rights`.
    A line owner holds `clear_override`; nobody holds it by default.
  - **`pilot` and `prod` need `baseline.yaml` in the config folder** with a filled `ceiling` (metric, max,
    window_days, source); `build` refuses without it. In `dev` it is used when present.
  - `Channel` gains `parse_action` (the verified user and the button value); a custom channel kind must implement it.
    The abstain card's second button now records `missed` (was `should_have_answered`). The receiver routes
    `label|...` and `clear|...` clicks to `Measure` (`handle_slack_action(..., measure)`).
  - New tick steps `measure_levels` (every 300 s: re-checks the 3-wrong rule and the ceiling) and `weekly_report`
    (writes the report for the last complete ISO week once). New commands `hadavin-sdk label import FILE --by P
    [--approved-by P]`, `promote-check AGENT ACTION` and `report [--week YYYY-MM-DD]`. The CLI names are
    **asserted**, not verified: the authoritative paths are signed channel actions and reviewed config PRs.
  - `suggest` in `pilot`/`prod` additionally needs `promotions/<agent>.<action>.json` (from `promote-check`). It
    is still refused until K8 builds posted fixes; `dev` does not read the file.
  - A csv label counts as evidence, in reports and in `promote-check`, only once a line owner approves the import:
    the signed `approve_import|<id>` click on the card the import posts, or `--approved-by` (asserted; a different
    person holding `approve_label_import`). The author of an import cannot approve it. Approval appends the rows again
    (no UPDATE exists on `labels`).
  - A `harmful` label is sticky: only a person holding `clear_override` can lower it (audited). Demotions are keyed by
    the label row, so a harmful label after a clear demotes again.
  - **`baseline.yaml` `ceiling` now has five required fields and no defaults: `metric`, `counts`, `max`,
    `window_days`, `source`.** `counts` lists the label classes that count against the ceiling (for example
    `[harmful]` or `[harmful, wrong]`) and must include `harmful`; `pilot` and `prod` refuse to start without them,
    pointing at `scoping.md` `## Success metric and ceiling`. The K0 templates carry the same fields. The ceiling
    count runs over all labels in the rolling window (retired agents too); `max` is a whole number.
  - Removed `Store.add_label` (it skipped the sticky rule): `add_labels` is the only way in. `Store` gains
    `clear_demotion` (compare-and-set) and a unique index keeps one demotion row per reason.
  - **`pilot` and `prod` need at least one person principal with `admin_rights: [clear_override]`**; `build` refuses
    without one. Admin rights only apply to `kind: person` principals.
  - The promotion file's SHA-256 is unkeyed: the loader also needs the replay record it names to be green in
    `replay-records.jsonl`, and `build` re-derives the numbers from the store in pilot/prod.
  - The weekly report is announced first and stored second; an unreachable line owner fails the `weekly_report` step
    and the next tick retries (the step now runs every tick).
  - `Store` also gains `add_labels` (labels + demotions + the sticky rule in one transaction), `claim_action`
    (replay guard), `list_csv_import`; migration `0005` adds the append-only table `seen_actions`.
  - Signed clicks are acted on once (a replayed request is refused). `clear` is refused for a `ceiling:` demotion
    while the ceiling is breached, and for a `suggest` action until the section 6.1 numbers hold again.
  - **`label import --by/--approved-by` is refused in `pilot` and `prod`**; only signed clicks count there. The import
    id is now the file's full SHA-256. `Channel.parse_action` returns a `nonce` with the click.
  - A replay record counts as green only when its fields agree with each other.
  - **Policy numbers moved out of code into `measure.Policy` (documented defaults, one place) and an optional
    `policy:` mapping in `baseline.yaml`** that the client signs: promotion numbers, the wrong rule (`wrong_limit`,
    `wrong_window_days`), `held_maps_max_days` (max 400), `late_start_s`, report local time, `enforce_every_s`,
    `purge_every_s`, `seen_actions_keep_s`. Strictly validated; omit it for the defaults. A tick step's `every_s`
    may now be a callable that reads it from the app's config. The recent-wrongs demotion reason prefix is `wrongs:`.
    A repo test fails on key-shaped and Slack-id literals; K6 modules name no environment, host or env read.
  - Third review round: migration `0005` also adds `labels.seq` (insertion order: "latest" means highest seq, not
    `created_at`), lets the runtime role DELETE on `seen_actions` only (expired click nonces are purged by the new tick
    step `purge_seen_actions`), and `Store` gains `release_action` and `purge_actions`; `add_labels` now returns the
    demotions it inserted and `add_level_event` returns whether it inserted.
  - **A clear does not erase recent wrongs (intended):** the wrongs still inside the 14-day window count after a
    clear, so one new wrong re-demotes at once while two older ones remain; the demotion card says until when.
    One demotion (one audit entry, one card) per episode; a csv harmful row demotes once across import and approval.
  - **`limits reset --by WHO` is refused in `pilot` and `prod`** (an asserted name cannot lift the kill switch): reset
    there only by the signed channel click (admin right `reset`, once per request). `limits stop` still works from the
    CLI. In `dev` both work and the operating-system user is audited.
- **K3 pilot build path (levels, shadow cut-off, fail-closed loading).** Action contracts change shape:
  `executor.system` moves to a contract field `target_system`, and `executor` is now a tagged union
  (`kind: none | manual | http`). Edit every contract: move `system:` out of `executor:` to `target_system:` beside
  it. `chain_id` and `verify_check` may be omitted for `none`.
  - **`config_hash` changes once** (the contract dump changed): every agent needs ONE new gate run
    (`hadavin-sdk gate <agent>`). A level flip (`levels`) never changes the hash.
  - **A tooled agent (`tools_allowed` not empty) now needs a gate run with `--k 3` that passed pass^3**; a k = 1
    green record no longer qualifies it. Non-tooled agents are unchanged.
  - New optional agent fields `levels` (per action: `shadow` or `suggest`; `act` is refused until Phase 4) and
    `max_run_usd`. In `pilot` and `prod` both are required and `levels` must list every `scope_allowed` action;
    `suggest` is refused there until K6 and K8, an `http` contract and a `read_only` contract are refused, and so are
    `confidential` and `restricted` agents. See `deferred.py` for every refusal and the phase it arrives in.
  - In `pilot` and `prod`, `build` makes no `Executor` and reads no client-system secret. `build` takes a new
    `llm=` override.
  - Shadow and abstain cards are posted through the new `Channel.post_card` (and `Channel.max_card_chars`); a
    custom channel kind must implement both. `AuditEvent` gains `caught_by`.
  - New file `replay-records.jsonl` (reader only for now; the writer arrives with K1b-full). A tooled agent at
    `suggest` is refused at load without a green record in it for the current config hash, model and prompt.
    **Shadow qualification through the gate is a start-up gate, not accuracy evidence.**
- **K1b-lite replay check (report only).** New commands `hadavin-sdk replay AGENT --bundles D --cause-list D
  --max-usd X --out OUT [--k K]` and `hadavin-sdk score --outputs OUT --answers F --cause-list D --bundles D`.
  Neither gives a met / not met verdict; a replay pass is not evidence of live accuracy.
  - New optional `k1b:` section in `config.yaml` (`max_steps` 12, `max_tool_calls` 20, `case_timeout_s` 300).
    It does not change `config_hash`, so no agent needs a new gate run.
  - `replay` and `score` write `k1b` audit events (`replay_run`, `hard_check_a`, `hard_check_b`, `score_run`) to the
    configured `local_dir` or `chain` audit. A `chain` over the memory store warns that events are lost at exit.
  - `replay` refuses a non-empty `OUT`, a route with a zero price (unless the llm kind is `fake`) and a bundle with
    any timestamp after the alert time. A run that dies half-way leaves `FAILED.txt`; delete the folder to re-run.
  - **Exit codes of every command changed for crashes.** `main` now returns 2 for a `ConfigError` (message on
    stderr) and 3 for any other uncaught error, instead of a Python traceback with exit 1. Exit 1 keeps its meaning
    (gate red, audit not intact, replay aborted or cost cap reached).
- **K1b-lite masks client data before the model.** Until now `replay` ran only the injection screen: the alert,
  every tool result and the runbooks went to the model raw. Every text value of a case bundle is now masked with
  the studio redactor (`guard.redact.redact_many`, one placeholder namespace per case, so one value is one
  placeholder everywhere) before the model or the injection screen sees it. The placeholder map lives in memory
  only: it is never written to the outputs or the audit sink, and never logged. Evidence IDs, file names, the
  the values of the `service`, `kind` and `fault_type` keys (the Cause List vocabulary), exact timestamps and numbers
  are left alone; dict keys are masked too. Names, queries and labels are masked in the snapshot and in what the model
  sees alike, so citations and queries still resolve. New `k1b.redact` (default `true`); `false` is refused unless `replay` gets
  `--i-know-data-is-already-masked`, and the run records `redaction.mode: off_acknowledged`. `run.json` records the
  scheme and the number of distinct values masked per class (no values); both reports print them. **What the
  redactor does NOT catch:** names in free text, customer or project names, ticket numbers, unusual formats,
  most company or cloud host names (it masks `.local`-style hosts, not `api.client-bank.com` or `*.rds.amazonaws.com`),
  and the values of the `service`, `kind` and `fault_type` keys. It is a strong first filter, not proof that no client data leaves; the
  reports say so under "What the numbers cannot say". Re-run `replay` for earlier runs: they sent data unmasked.
- **K1b-lite: a `not_sure` answer may omit `causes`.** A real Sonnet 5.5 smoke run abstained correctly on a
  no_evidence incident with `{"not_sure": true, "reason": "..."}` and the strict parser called it unreadable (a Miss).
  `causes` may now be omitted (or empty) only when `not_sure` is true; every other strictness is unchanged (both
  forms, no form, wrong types, extra keys, fenced or surrounded text, duplicate keys, NaN). The `submit_diagnosis`
  schema no longer lists `causes` as required and its description, and the system prompt, say so. Case files now
  record `answered_via` (`tool` or `text`), and `run.json`, `replay-report.md` and `score-report.md` list the case
  ids that were unreadable, errored, timed out, capped or converted for uncited evidence (ids only, never answers).
  Re-run `replay` for runs made before this change: their saved unreadable answers are not re-parsed.
- **`tick` now matches the v5 contract.** Exit code **4** (was 3) when the store is unreachable, for both
  `run_tick` and the CLI; 3 stays the wrapper code for any other uncaught error. The heartbeat summary line is no
  longer a step: it is logged after the steps, writes no `tick_state` row and cannot change the exit code (K7 sends
  the external heartbeat is PENDING K7: nothing sends it today). **A scheduler that treated exit 3 as "store down" must now watch 4.** `tick` also returns 4 when the store stops answering during the steps (it re-probes after a step failed); 1 stays for a failed step with a reachable store. Exit 4 is only for connection failures: a store that answers with a missing table or grant exits 2 ("run migrate, check grants") for `tick`, `limits stop` and `limits reset`. `limits stop` and `limits reset` with the store unreachable now exit 4 (was 2) and print "kill switch NOT set" or "NOT reset" with "Nothing was changed".
- **K1b-lite gap fixes.**
  - SDK version is now `0.1.0` (`pyproject.toml` and `hadavin_sdk.__version__`, pyproject and `__init__` kept equal by a test). Replay and
    score reports print it; `0.0.0` still prints "unreleased build".
  - `replay`: every provider call has a wall-clock bound (the time left in `k1b.case_timeout_s`, at least 1 s),
    for every llm kind: the call runs in a worker thread and, on expiry, the case ends as `timeout` with stop
    reason `call_timeout`, the worst-case cost of that call is charged to `--max-usd`, and the whole run stops
    as `aborted` (exit 1), so at most one abandoned call exists per invocation. The abandoned call is not killed;
    it can outlive the run (a slow trickle defeats a socket timeout). Next step, only if a client run ever shows a hung call: run each case in a child process that can be killed. The per-socket timeout is already
    `call_timeout_s` on each llm kind's settings (`backends.llm`). Ctrl-C during a replay now also leaves `FAILED.txt`.
  - `score` audit order changed: `score_report` `started` (intent, before anything is written), the report file,
    then `score_report` `written` and one `score_run` per run (these append like any K1b event: a failed append exits 3 with the report on disk). A report that cannot be written
    leaves `started` then `failed` (with the error class) and no `score_run`; the command exits 3.
- **Audit and lock-in guard gaps.**
  - Anchors and checkpoint rows carry a non-secret `key_label` (new optional `key_label` setting on every
    signer kind; default `pk:` plus a fingerprint of the public key), never the configured `key_id`. An alias and
    an ARN of one key give one label and no account id reaches the anchor bucket. **Anchor bodies written by
    the previous build hold `key_id`; the offline verifier accepts them but never compares or prints it (it can be an ARN).** A custom anchor kind must
    now accept `alg` and `key_label` keywords (one taking `alg`/`key_id` is treated as a legacy 3-argument anchor
    and warns).
  - `verify_anchor_bodies(bodies, public_key, names=None, assume_alg=None)`: `names` binds each object name to
    the seq inside it; `assume_alg` verifies pre-`alg` anchors by signature (a wrong guess fails every
    signature). The immutable objects are not rewritten.
  - **Upgrade step: run `hadavin-sdk migrate`** (0004 adds `alg` and `key_label` to `audit_checkpoints`; old rows
    are NULL, meaning "not recorded": verify then uses the configured signer's scheme). A runtime started before migrating refuses with the "run migrate" hint.
  - Lock-in guard: the literal scan now also covers bytes constants, constant `+` joins and f-strings (it found
    `".meta" + ".json"` written to dodge it; that suffix is now a plain literal and the model-id pattern
    matches `meta.llama` only); every `neutral` kind must show no vendor SDK import (S3 anchor excepted, with
    `endpoint_url`) and a `Neutral protocol:` line in its module docstring.
  - Vault licence check, live 2026-11-01: HashiCorp Vault 1.15 and later is BSL 1.1 (change date four years after
    each release, then MPL-2.0); OpenBao is MPL-2.0 under the Linux Foundation and states API compatibility with
    Vault 1.14 (Transit has extras of its own). The `vault` and `vault_transit` kinds stay `neutral` because they
    speak the Vault-compatible HTTP API that OpenBao also serves, but neither has been run against OpenBao by us
    (they stay `unverified`); the docstrings say so.
- **Lock-in guard.** `tests/test_lockin_guard.py` fails CI when a vendor SDK is imported outside its kind
  module, a capability lacks a neutral prod kind (`Entry.neutral`) and two prod kinds without a dated
  exception, or core logic names a vendor.
  - Anchor objects now carry `alg` and `key_id`, so `chain.verify_anchor_bodies(bodies, public_key)` checks
    them with nothing else. A custom anchor kind's `put` must accept `alg` and `key_id` keywords. Anchors
    written before this change have no body fields and verify only through `verify()`.
- **P5/P6 follow-ups.**
  - **Re-gate every agent once.** `golden_sha256` now covers the input documents the golden cases point at,
    so a changed document un-qualifies.
  - `config_hash` now also holds `eval_threshold` (when not 1.0), `max_completion_tokens` and the Foundry
    `resource`.
  - `eval_threshold: 0` is refused.
  - A `bedrock_guardrail` must name a published `guardrail_version` (digits; `DRAFT` can change).
  - A detector `threshold: 0` is refused (it flagged every clean text).
  - A `bedrock_guardrail` needs `bedrock:GetGuardrail`. Start-up refuses a guardrail with no PROMPT_ATTACK
    input filter switched on.
  - Moving model aliases are refused per kind:
    - OpenAI names with no dated snapshot (`gpt-4o`, `o3`);
    - untagged names on a local OpenAI-compatible server (Ollama: `llama3` means `:latest`);
    - Gemini names with no version (`gemini-pro`);
    - Bedrock names without a provider prefix.
- **Rewrite config.yaml to config v2** (slice 2 P1b). `environment: dev|pilot|prod` is required. Each backend
  is `backends.<capability>: {kind: <name>, ...settings}`. The old top-level keys are refused with a message
  naming the new place: `audit_dir` -> `backends.audit.dir`, `recorded_dir` -> `backends.llm.recorded_dir`,
  `detector_threshold` -> `backends.detector: [{kind: regex, threshold}]`, `region` -> each AWS kind's
  `region`, `slack` -> `backends.channel`. Start-up now refuses dev-only kinds outside `dev`, a secret name used
  by both a backend and an action, and any secret that cannot be read.
- `app.build(config_dir, agents, *, secrets=None, ...)`: `secrets` is now a keyword; `make_llm`,
  `make_detector` and `make_channel` are gone (backends are built from the table in `hadavin_sdk.backends`).
- **Re-gate every agent once** (slice 2 P1a). `config_hash` now hashes with `exclude_defaults` and includes the
  llm backend kind, so every stored green gate run stops matching. Run `hadavin-sdk gate <agent>` for each agent
  before starting the runtime; until then start-up raises `Unqualified`. After this one re-gate, adding an optional
  field with a default no longer un-qualifies agents, and swapping the llm backend does.

### Added
- **G4 command withholding** (P5/P6 follow-ups). `channel.clean` now withholds every command a person could
  paste to change a system: `[command withheld (G4)]` stands in its place.
  - It covers AWS, gcloud/gsutil/bq, az, azcopy and PowerShell Az, kubectl/oc, helm, terraform/tofu/pulumi,
    ansible, systemctl, docker/podman, git, gh/glab, psql/mysql/mongosh/redis-cli, SQL write statements,
    `rm -rf` and `curl | sh`.
  - It fails closed: a CLI command passes only when it is positively read-only. The WARDEN port was dead code
    and AWS/K8s-only.
- `backends.hosts(entries)`: the hosts the configured kinds connect to, as a suggested egress list.
  The Postgres store is not in the list: its address sits inside the secret DSN, so add the database host by hand.
- **No single-dependency detector.** `llm_judge` runs on any llm kind, a local open-weights model on
  `openai_compat` included, so the cloud-neutral production detectors are `regex` + `llm_judge`.
  `bedrock_guardrail` is AWS-only. The approval-summary screen runs without the judge: no agent can be
  charged there, and the judge already screens the document and tool output.
- `hadavin-sdk tick` (slice 2 P7, v5 contract): one pass of isolated steps (`sweep`, `reconcile`, `stuck`,
  `checkpoint`; the summary line is logged after them and is not a step); a failing step is logged and recorded in `tick_state` and the others
  still run. Exit 0 ok, 1 a step failed, 2 config error, 4 store unreachable. Later steps are appended to
  `runtime.tick.STEPS`.
- `slack` approval channel (`backends.channel: {kind: slack, channel_id, signing_secret_name,
  bot_token_secret_name}`) and `approvals/receiver.py`: verified clicks are recorded only; `tick` runs the plan.
- Migration `0003_approvals_tick.sql`: `approval_requests.sent_at` and `channel_ref` (a failed send is resent
  by `tick`), one decision per approval step, an exact month spend counter, the kill switch row (a missing row
  reads as ON), `tick_state`.

- `postgres` store (`pip install hadavin-sdk[pg]`, slice 2 P2): `backends.store: {kind: postgres,
  dsn_secret_name, iam_auth, region}`; compare-and-set in SQL; RDS IAM login with `iam_auth: true`.
- `hadavin-sdk migrate [--runtime-role R]`: forward-only schema (`store/migrations/0001_core.sql`) applied under
  an advisory lock with the migration role's DSN from `HADAVIN_MIGRATE_DSN`. Rollback = restore the snapshot
  taken before migrating.
- `hadavin-sdk limits stop|reset` now works on a shared (postgres) store.
- llm kinds (slice 2 P5, all `slice2-unverified` until the P9 live run): `anthropic` with `platform: api |
  vertex | foundry` (extra `anthropic`), `bedrock` through Converse (extra `aws`), `openai_compat` (OpenAI,
  Groq, OpenRouter, a local Ollama) and `gemini` over stdlib HTTP. Each has `call_timeout_s` (60) and
  `max_attempts` (3): transient failures retry with exponential backoff and jitter, then `ProviderExhausted`.
  `output_schema` is a forced tool call. Model ids that are moving aliases (`sonnet`, `*-latest`) are refused.
  The llm `platform` and `base_url` are part of `config_hash`.

- Detector lists (slice 2 P6): `backends.detector` takes one or more entries (an `llm_judge` never alone); every
  entry runs and any flag flags the run (max score, the flagging names joined by `+`, the first flag's reason).
  New kinds, both `slice2-unverified`: `llm_judge` (`route`, `threshold` 0.7; a fixed prompt hashed into
  `config_hash`, its cost charged to the agent, qualified at its own rate by a non-empty `golden_dir/judge.jsonl`
  in the evals gate; that file is part of `golden_sha256`) and `bedrock_guardrail`
  (`guardrail_id`, `guardrail_version`, `region`; the PROMPT_ATTACK filter, extra `aws`).

### Changed
- P5/P6 follow-ups:
  - limits are checked again before a tool output is screened, so a reply that spent the budget never pays
    for a judge call;
  - redaction masks GCP `projects/<id>/...` paths and Azure `/subscriptions/<uuid>/...` ids, and ARNs with no
    account (`arn:aws:s3:::bucket`) or in the `aws-cn` and `aws-us-gov`
    partitions;
  - `llm/retry.py` names no vendor: each llm kind says which of its SDK's errors are retryable.
- Postgres TLS (slice 2 P7): `verify-full` by default for any non-local host, with the server's CA bundle
  from `sslrootcert` (a file) or `sslrootcert_secret_name` (a PEM in any secrets backend); an explicit weaker
  `sslmode` is a dev opt-down. With `iam_auth` only `verify-full`/`verify-ca`, and a runtime DSN with a
  password is refused.
- The runtime role gets SELECT, INSERT only on `approval_decisions`, `dead_letters`, `gate_decisions`.
- Gate decisions are written once per run; a run stuck in `RECEIVED` or `PLAN_READY` can go to `NEEDS_PERSON`.
- Approver ids carry the channel kind's name (`slack:<id>`, `fake:<id>`); request signing is the shared
  `approvals/hmac_v0.py`, not borrowed from Slack.
- `ProviderExhausted` from the model ends the run in `NEEDS_PERSON provider_exhausted` instead of escaping.
- A provider that refuses the request (`ProviderError`, e.g. a bad key) ends the run in
  `NEEDS_PERSON provider_error`; `ProviderExhausted` is now a `ProviderError`.
- `Reply.stop_reason` is one of `end_turn`, `tool_use`, `max_tokens`, `refusal` for the network kinds. A reply
  cut off at the output cap or declined ends the run in `NEEDS_PERSON llm_max_tokens` / `llm_refusal` instead
  of `NO_ACTION`; a cut-off reply's tool calls are dropped (their input may be incomplete).
- Store: `get_approval_decision`, `list_approvals`, `list_runs`, `touch`, `spend_totals`; `add_cost` raises
  `NotFound`; `Limits.blocked` no longer writes a zero-spend row.
- The executor calls a heartbeat before every HTTP attempt, so long retries do not look stuck.
- `Verdict.score` is bounded to 0..1; a detector failure is logged with its cause (still fails closed).

### Added (slice 2 P3, every kind `slice2-unverified` until the P9 live run)
- `backends.audit: {kind: chain}`: WARDEN's hash-chained, append-only audit in the store's database, signed
  checkpoints every `checkpoint_every` rows, and an optional `anchor: {kind: s3_object_lock, bucket, region}`
  (GOVERNANCE, 1 day by default). `hadavin-sdk audit verify` exits 0 intact, 1 not intact,
  2 refused (a memory store lives in one process), 3 unreadable.
- `backends.signer`: `none` (default), `ed25519_local`, `aws_kms`. Start-up signs a probe message.
- Environment table: prod refuses `ed25519_local` and a chain without an anchor that has `retention_ack: true`;
  COMPLIANCE mode only in prod with `retention_ack`.
- `store/migrations/0002_audit_chain.sql` (applied by `hadavin-sdk migrate` with the postgres store).

### Added (slice 2 P4, `slice2-unverified` until the P9 live run)
- `backends.secrets: {kind: aws_secrets_manager, region, ttl_s: 300}`: values cached for `ttl_s` (0 = no
  cache), a missing secret is a `ConfigError` at the start-up probe, values are never logged.
- `backends.secrets: {kind: env, prefix: HADAVIN_SECRET_}` (dev only): `fixture-token` reads
  `HADAVIN_SECRET_FIXTURE_TOKEN`.

### Added (slice 2 P4b, `slice2-unverified` until a live run): cloud-neutral secret stores
- `backends.secrets: {kind: vault, address, auth: token|approle|kubernetes, mount, path_prefix, field,
  namespace, ca_cert}`: HashiCorp Vault or OpenBao KV v2 over the standard library (no extra); TLS always
  verified, plain http only to this machine; a 403 signs in again once (approle, kubernetes).
- `backends.secrets: {kind: azure_key_vault, vault_url}` (`pip install hadavin-sdk[azure]`):
  `DefaultAzureCredential` (managed or workload identity).
- `backends.secrets: {kind: gcp_secret_manager, project_id}` (`pip install hadavin-sdk[gcp]`): Application
  Default Credentials (attached service account or workload identity), version `latest`.
- `backends.secrets: {kind: mounted_file, dir}`: one file per secret (Kubernetes Secret, CSI driver, External
  Secrets); paths stay inside the folder; on POSIX a world-readable file is refused (mount 0400/0440).
- Every remote kind shares one TTL cache with one refresh at a time; an empty value is refused at start-up.
  A missing `aws`/`azure`/`gcp` extra now always names the `pip install`.

### Upgrade steps (slice 2 P3b)
- **The anchor moved out of the audit entry.** `backends.audit: {kind: chain, anchor: {...}}` becomes
  `backends.audit: {kind: chain}` plus `backends.anchor: {kind: s3_object_lock, ...}` (default `none`).
- **Prod now refuses `signer: none` and `anchor: none`**, and `ed25519_local` with a key file (set
  `private_key_secret_name` instead). Config errors list every refusal at once.
- `migrate(dsn, password=...)` replaces `iam_auth=`/`region=`; build the helper with
  `hadavin_sdk.store.postgres.password_source(iam_auth, region)` (the CLI does).

### Added (slice 2 P3b, `slice2-unverified` until a live run): cloud-neutral audit
- `backends.anchor`: `s3_object_lock` (AWS S3, or MinIO / Ceph RGW through `endpoint_url`),
  `azure_immutable_blob` (version-level WORM; container checked at start-up), `gcs_retention_lock` (bucket
  retention policy checked; COMPLIANCE needs it locked). A put that finds the same bytes counts as anchored;
  different bytes are never overwritten.
- Signers: `vault_transit` (Vault / OpenBao Transit, ed25519, one pinned key version), `azure_key_vault_key`
  (ECDSA P-256 / ES256: Key Vault has no Ed25519), `gcp_kms` (EC_SIGN_ED25519). `ed25519_local` can read its
  key from any secrets kind (`private_key_secret_name`).
- `audit verify` also checks that each row's event id column matches its body.
- Cloud SDKs only in their kind modules: `audit/signer_aws.py`, `store/auth_aws.py` (RDS IAM).
- `mounted_file` also refuses group- or other-writable files and checks the opened file (no stat-then-read
  gap, `O_NOFOLLOW`); a Kubernetes JWT read error in `vault` is a `ConfigError`; the GCP secret fetch is bounded
  (5 s, no retry).

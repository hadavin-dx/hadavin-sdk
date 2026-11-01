# Changelog

## Unreleased

### Upgrade steps
- **K5-core round 10.**
  - **Required now in pilot and prod on Postgres: `backends.store.purge_dsn_secret_name`** (the process refuses to start without it, so the purge cannot silently fail and keep plaintext originals for ever), and `evidence.restored_hash_key_secret_name` must hold at least 16 bytes. Re-run `hadavin-sdk migrate --runtime-role R --purge-role P`: the purge role now has column-level SELECT only (`runs`: run_id, state, updated_at; `redaction_maps`: run_id, updated_at; `tool_calls`: call_id, run_id, created_at) plus DELETE on the two evidence tables, and `migrate` asserts both roles' EFFECTIVE privileges (membership, PUBLIC, default privileges, relations outside the map, ownership, CREATE, superuser) and rolls back on any excess.
  - New keys: `evidence.max_map_entries` 2000 (a run whose text plants more distinct values ends `NEEDS_PERSON document_too_complex`), `evidence.post_read_operations` [] (a tool operation bound to POST must be listed). The redactor's built state is kept per run, so cost no longer multiplies strings by map size.
  - A tool whose source was switched off by a failed re-probe is refused in `ToolBox.invoke` (by `options.source` or by host), not only the app's own source objects. A non-string value for an identifier input is ungrounded. Every redaction bound now has a masking fallback. Source reads count toward the request cap. More metadata addresses are refused and a name lookup has a 5 s timeout. The restored-hash comparison is constant-time.
  - The import-pin text is corrected everywhere: the pin proves the reviewed text of one file is what runs; the loader-name refusal is a best-effort tripwire; a tool body is trusted code. Perf tests moved to a `perf` marker in their own non-blocking CI step; the `check` job's timeout is 30 minutes.
- **K5-core round 9.**
  - **New required key in pilot and prod: `evidence.restored_hash_key_secret_name`** (a secret in your secrets kind). The gate's audit event now carries an HMAC of the restored inputs under that key, not a plain hash of real identifiers; an execution whose plan has no recorded hash is refused (`restored_unbound`), not skipped.
  - `evidence.max_document_bytes` now defaults to 262144 (was 1 MiB). The command-line credential patterns (curl, mysql, redis-cli, sqlcmd, ldap, htpasswd, docker/mongo/az login) were quadratic on repeated words and are bounded to 1024 characters of gap; a long-token sweep masks any run of 129 or more base64-ish characters; the URL-password bound is 1024. EMAIL masks local parts up to 254 characters. A test generates its inputs from every pattern's own keywords and fails on super-linear time.
  - No regular expression is built from a client value any more (`evidence.contains` uses plain scans; the sweep finders are compiled without entering `re`'s cache). The pinned-module import check refuses these loader names as a best-effort tripwire, not a boundary (`import_module`, `__import__`, `importlib`, `runpy`, `exec`, `eval`, `compile()`, `builtins`, `spec_from_file_location`); it stays best effort, a meta-path finder restricted to the pin is the sound fix.
  - The concurrency slot is held until the tool's thread ENDS (a timed-out body keeps its slot), and every request a tool makes counts toward `max_tool_calls_per_minute`. Tools never use an environment proxy; the LLM clients and the executor still may. More addresses are refused (metadata addresses, 6to4, Teredo, NAT64, 198.18.0.0/15). `generated_suffix` is a tiny grammar (literals and bounded character classes). Any credential-bearing header is refused over plain http. The scrub also sees double percent-encoding, base32 and triple base64. A failed re-probe switches the source OFF (reads refused) until a probe passes; a malformed RBAC rule proves nothing.
  - PR #48 merges first; this branch rebases onto it afterwards.
- **K5-core round 8.**
  - **Run `hadavin-sdk migrate` again with `--runtime-role R --purge-role P` (two different roles) and set `backends.store.purge_dsn_secret_name`.** The runtime role no longer holds DELETE on `tool_calls` or UPDATE/DELETE beyond what it needs: only the purge role deletes evidence (round 10 narrows this to column-level SELECT plus DELETE on the two evidence tables). Without a purge DSN the purge step runs under the runtime identity, is refused by the database and FAILS loudly (evidence is kept, never silently deleted).
  - New `evidence` keys: `max_document_bytes` 1048576 (a larger document ends `NEEDS_PERSON document_too_large`), `case_insensitive_targets` [] (grounding is exact in case unless the contract's `target_system` is listed), `source_reprobe_s` 3600 (a new tick step `reprobe_sources` probes every source's scope again and fails loudly if RBAC widened), `max_concurrent_tool_calls` 4 and `max_tool_calls_per_minute` 120 (per process: the agent cannot raise the load on a client system). New manifest key `generated_suffix` (a regex; the only way a proposal may name the front of a longer name, such as a pod's hash suffix).
  - Behaviour: grounding is a whole-token match and exact in case (`payments` is not found in `payments-canary`, `admin` not in `Admin`); a validator crash or an evidence-store outage is `evidence_unavailable` with no `caught_by` (it was `invalid_proposal`/`guard`); redaction patterns are bounded (bounded polynomial time, see README) and tool results are cut to twice their cap before redaction; hosts are resolved once, refused if they resolve to loopback, link-local, unspecified, multicast or reserved addresses, and the connection goes to the checked address (DNS rebinding, in process; K7 stays the backstop and is a hard prerequisite before any pilot); the Kubernetes probe accepts `create` only on the three self-review resources and treats an empty or status-less answer as not proven; a bearer token never travels over plain http; a tool secret under 6 characters is refused; the gate's decide event carries `restored_hash` and every tool event carries `output_hash` and `rows`; `forbidden_host` normalises trailing dots, case and non-ASCII and knows more metadata names.
- **K5-core round 7.** `redact_untrusted` escapes markers and placeholder look-alikes in every decoded view; redacted text is cleaned of lone surrogates last and a document that cannot encode is an abstention; tooled agents need `additionalProperties: false` contracts and an undeclared input is `invalid_proposal`; the pin refuses relative imports and parent `__init__.py` with code, and a cached module must carry the same digest; `caught_by=guard` now also covers `uncited` and `invalid_proposal` (not `guard_unavailable`); a failed step is due again at the next tick; a source endpoint obeys the manifest host rules; fetch checked hostnames only (superseded in round 8: it now resolves once and connects to the checked address; K7 network policy is still required).
- **K5-core round 6.**
  - `0005_evidence.sql` was edited in place and is not merged anywhere. K6 (#41) also adds a `0005`: K5-core merges first and K6 renumbers its file to `0006_measure.sql`. A dev database that already ran an earlier `0005_evidence.sql` (the ledger records it by name) lacks `tool_calls.error` and every `add_tool_call` fails as `evidence_unavailable`: drop `tool_calls`, `redaction_maps` and their ledger row, then run `hadavin-sdk migrate` again.
  - New key `retention.held_tool_calls_max_days` (400): held runs' tool calls now have their own ceiling, and the two 400-day ceilings run before the hold hook, so a failing hook cannot stop them.
  - `tool_module_hashes` are checked BEFORE any tool module is imported (a mismatch or a missing pin in pilot and prod raises `ConfigError` with nothing imported); the pins are part of the agent's config hash.
  - Every non-boolean action input must say `identifier: false` (or `true` on a string); `evidence.cluster_suffixes` must end in a private label; a Kubernetes `api_url` is scheme and host only; `sources=` objects are refused in pilot and prod.
  - A run parked in NEEDS_PERSON no longer keeps its redaction map past the ordinary retention (it cannot move again).
  - `caught_by` is now set only when a control stopped a proposal (`ungrounded`, `run_budget`, `injection_suspected`, `guard_unavailable`; superseded in round 7: `guard_unavailable` is out and `uncited` and `invalid_proposal` are in); a tool, redaction or evidence failure sets none.
- **K5-core, final shape of the config and wiring (reviews 1-5).**
  - **Run `hadavin-sdk migrate` with the runtime role granted** (`--runtime-role`) **before** starting the new image: `0005_evidence.sql` adds `tool_calls` (with an `error` column) and `redaction_maps`; without the grants the runtime cannot write them.
  - New `config.yaml` keys (defaults in `hadavin_sdk/defaults.py`; units as named): `tool_modules`, `tool_timeout_s` (seconds, 10; one deadline for a whole tool call), `tool_module_hashes` (SHA-256 of each tool module's source file; required in pilot and prod), `executor_timeout_s` (seconds, 10; dev executor), `scope_inventory` (`"<page>#<anchor> sha256:<64 hex>"`, format-checked only), `sources` (`kind`, `settings`, `token_secret_name`, `ca_file`; built and probed at start-up), `retention.tool_calls_days` 30, `retention.redaction_maps_days` 30, `retention.hold_labelled` true, `retention.held_maps_max_days` 400 (at most 400 and at least `redaction_maps_days`), `retention.purge_every_s` 86400, and an `evidence` block: `max_tool_errors` 3, `legacy_max_output_bytes` 20000, `fetch_ceiling_bytes` 2097152, `https_ports` [443], `cluster_ports` [80, 8080, 9090, 9093, 3100], `cluster_suffixes` ['.svc.cluster.local', '.svc'], `stored_kinds` (may narrow the default, never widen it; UUID is not stored), `max_tool_calls_per_run` 40, `max_tool_bytes_per_run` 262144, `max_abandoned_tool_threads` 8.
  - Tool manifests (`tools/<agent>.yaml`) gain `ports`, `options`, `ca_file`, `ca_secret_name`; an agent with a manifest must mark every string input of its actions `identifier: true` or `identifier: false`; hosts may not be IP literals, loopback or metadata names; `cluster_http` needs every host in-cluster. A tool with a credential, or one that reads a configured kind of source, needs a `scope_inventory` entry `tool:<name>` or an explicit mapping (`options.source`) to a probed source whose token secret is the tool's only secret and whose host is one of the tool's `hosts`.
  - `app.build(..., hold_run_ids=)` wires the held-run hook (K6 supplies it); a hook that raises stops that tick's purge, loudly. A hold is not retroactive. `tools=` (plain callables) is refused in pilot and prod.
  - `evals.gate` now matches by subset (expected inputs must match, extra optional inputs are allowed) and offers a tooled agent's actions with the required `evidence` field, as the runtime does.
  - Behaviour changes to know: a redaction fault is an abstention (no `caught_by`), a store fault while keeping evidence is `evidence_unavailable`; the model now sees its own tool-call arguments in later steps; text sent to the model is no longer rewritten except for placeholder-shaped literals and result markers.
- **K5-core: read-only evidence, redaction before the model, tool wiring.** Needs `hadavin-sdk migrate` (new
  `0005_evidence.sql`: tables `tool_calls` and `redaction_maps`; the runtime role gets SELECT, INSERT on
  `tool_calls` and SELECT, INSERT, UPDATE on `redaction_maps`; only the purge role deletes them (rounds 8 and 10); the portal role reads neither). Run it
  before starting the new image; a custom `Store` must implement the six new methods.
  - **The document and every tool result are now redacted with the run's one map before the injection check and
    before the model** (`guard/runmap.py`). Placeholders (`<EMAIL_1>`) appear in plans; real values are restored
    only for tool arguments, for the gate's schema check (`authorize(..., inputs_view=)`, new denial
    `input.unresolved`) and for the dev executor (`Executor.execute(..., inputs_view=)`). Only identifier kinds are
    stored; secret and regulated kinds are never stored or restored.
  - **Recorded model answers (`FakeLLM`) and `evals.gate` are keyed by the redacted document.** Re-record any
    fixture whose document holds an email, a phone number or another redactable value (the two repo fixtures were
    re-recorded: `pii.txt`, `injected.txt`). `config_hash` is unchanged for agents without a tool manifest.
  - New `tools/<agent>.yaml` manifests (read tools only; `side_effect: none`), `Config` keys `tool_modules`,
    `tool_timeout_s`, `retention` (`tool_calls_days` 30, `redaction_maps_days` 30, `hold_labelled` true,
    `held_maps_max_days` 400, at most 400) and `scope_inventory`. A manifest is part of `config_hash` (a changed tool
    needs a new gate run); a tooled agent with a manifest must not share a tool secret with a backend or an
    executor.
  - A tooled agent's action tools now require an `evidence` list of call ids (`call_id = "<run_id>:<n>"`); an
    empty or foreign list ends the run `NEEDS_PERSON uncited`, and an input the contract flags `identifier: true`
    (new schema keyword, string properties only) that is not found in the cited results or the incident ends it
    `ungrounded`. `evals.gate` ignores `evidence`. A tool's exception is now a result (`ERROR: ...`) and the third
    one in a run ends it `tool_error`; a run whose cost reaches `max_run_usd` ends `run_budget`.
  - New tick step `purge_evidence` (daily). New `hadavin_sdk.sources` (four read-source interfaces, the neutral
    `KubernetesSource`, the start-up scope probe) and `app.build(sources=)`: a source that fails its probe, or
    cannot be probed and has no `scope_inventory` reference, stops the process starting.
  - The no-redirect HTTP opener moved to `guard/http.py`. **`make`, `hosts` and `Deps` now live in
    `hadavin_sdk.backends.factory`** (`hadavin_sdk.backends` itself imports nothing): change
    `from hadavin_sdk.backends import make` to `from hadavin_sdk.backends.factory import make`.
  - Review round: a tool module's `READ_OPERATIONS` is now a mapping operation id -> `(METHOD, path regex)`, and
    `ToolContext.fetch` refuses a call that fits neither; the manifest gains `ports` (default 443, in-cluster
    set for plain http), `cluster_http` needs every host in-cluster, and a tool with `secret_names` needs a
    `scope_inventory` entry `tool:<name>`. `tool_timeout_s` is one deadline for the whole tool call. Tool results
    that failed are stored with `error = true` (in `0005_evidence.sql`) and cannot be cited. Literal
    placeholder-shaped text in a document or tool result is escaped (`‹IPV4_2›`) before redaction. The ARN pattern
    stops at `?`, `&` and `#`; the stored map drops any original that holds secret-shaped text. Redaction maps of
    runs that have not ended are kept until the 400-day ceiling (`purge_redaction_maps(..., keep_open=)`).
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

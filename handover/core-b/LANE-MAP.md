# LANE-MAP: money and guarantee kit (branch cloud/core-b)

Read-only survey of `src/hadavin_sdk`. Every claim carries file:line. Paths are relative to the repository root
unless they start with a module folder, in which case they are under `src/hadavin_sdk/`. "UNVERIFIED" means the
file was not opened (or only its `def`/`class` lines were listed). Test names come from a text search of `tests/`
for the module's import or its names, not from running anything.

## 1. Basics (5 lines)

1. Layout: one package `src/hadavin_sdk` (112 files, 19,190 lines incl. 5 SQL files and 1 prompt .md); sub-packages `actions/ approvals/ audit/ backends/ guard/ k1b/ llm/ runtime/ sources/ store/ testing/`; demos in `demos/ask-your-data` (not part of the package), tests in `tests/` (README.md:5-9).
2. Test command: pyproject has no script for it, only pytest settings (`testpaths = ["tests"]`, `pythonpath = ["."]`, markers `live`, `perf`; pyproject.toml:81-88). The command is in README.md:46-48 and CI: `uv sync --group test`, then `pytest -q -n 3 -m "not live and not perf"`; perf alone: `pytest -q -m perf` (.github/workflows/ci.yml:92,100).
3. Python: `requires-python = ">=3.12"` (pyproject.toml:6); CI runs 3.13 and 3.12 (.github/workflows/ci.yml:74,142).
4. Extras (pyproject.toml:24-44): `anthropic`, `aws`, `signer`, `pg` (psycopg, needed by the Postgres store), `askdata`, `azure`, `gcp`. Base deps: markdown-it-py, pydantic, pydantic-settings, pyyaml (pyproject.toml:14-19).
5. Dependency groups (pyproject.toml:49-54): `dev` (pytest, ruff), `test` (moto, pglast, pytest-xdist), `scan` (pip-audit, bandit, zizmor). CLI entry point `hadavin-sdk = hadavin_sdk.cli:main` (pyproject.toml:47).

### Lane words that have NO code in `src/hadavin_sdk`

- **reserve / settle**: none in the package. The only reserve/settle is the demo meter `demos/ask-your-data/askdata/meter.py:211` (`reserve`) and `:221` (`settle`).
- **price table**: no separate table. Prices are two fields on each route in `config.yaml` (config.py:72-76).
- **lease**: no hit in `src` (searched `\blease`).
- **tenant**: only a redaction kind name `TENANT` (defaults.py:121, guard/runmap.py:225). No tenant id on any row or store method.
- **needs-a-person queue**: no queue. `NEEDS_PERSON` is a final run state (models.py:65, runtime/runs.py:10-22); the only way to list such runs is `Store.list_runs(state, updated_before)` (store/protocol.py:64).
- **SQLite store**: none. SQLite is used only inside the chain audit when the store is `memory` (audit/chain.py:49-62, 101-105).
- **executor identity**: `identity.py` holds only `Principal` (identity.py:10); the executor is `actions/executor.py:47`.

## 2. Module table

| File (lines) | Purpose in plain words | Public names (line) | Tests (file names) |
|---|---|---|---|
| limits.py (51) | Spend meter, daily and monthly budget check, kill switch on/off with audit | `Limits` :13, `charge` :17, `blocked` :20, `stop` :43, `reset` :48 | test_s5_runtime, test_cuj, test_p1a_fixes, test_review_fixes, test_review_pr3_round2, test_p6_detectors, test_k5_tools, test_k3_pilot |
| store/protocol.py (160) | The one store interface, its errors, and a check that a custom store has every method | `StaleState` :25, `is_connectivity_error` :29, `StoreUnavailable` :41, `NotFound` :45, `Store` (Protocol) :49, `missing_methods` :151 | contracts/test_store, test_s1_foundation, test_p7_tick, test_k5_round6_contracts, test_p2_postgres |
| store/memory.py (282) | Store kept in dicts behind one lock; lost at restart | `MemoryStore` :28 | test_s1_foundation, test_s5_runtime, test_s6_approvals, contracts/test_store, test_k5_review, test_k5_round6_contracts |
| store/postgres.py (533) | Store on Postgres: TLS rules, connect, all 32 methods as SQL | `tls_mode` :70, `ca_file` :95, `PasswordSource` :106, `password_source` :109, `connect` :125, `build` :152, `PostgresStore` :192 | test_p2_postgres, test_p7_store, test_k5_postgres, test_k5_round8_postgres, test_k5_round10_postgres, test_k2_migrations, contracts/kinds/store_postgres, test_peel_run_id |
| store/auth_aws.py (21) | RDS IAM token as the database password | `rds_iam` :15 | test_lockin_guard, test_p3b_neutral_audit |
| store/migrate.py (360) | Applies pending SQL files in one transaction, sets and asserts role grants | `MIGRATIONS` :20, `Grant` :24, `GRANTS` :46, `check_ledger` :97, `check_grants` :150, `effective_problems` :193, `migrate` :283 | test_k2_migrations, test_p2_postgres, test_p7_store, test_migrate_regex_linear, test_k5_round10_postgres, test_lockin_guard |
| store/migration_numbers.py (675) | Pure checks on migration file names, late files, a hand recipe, an SQL lexer with a refusal list. NOT called by the package (own header :5-6) | `NAME` :54, `MigrationNumberError` :80, `list_migration_files` :106, `check_ledger` :112, `check_migration_numbers` :147, `read_files` :161, `late_files` :200, `hand_recipe` :240, `order_problems` :267, `released_problems` :316, `gone_message` :342, `SqlReadError` :445, `checked_statement_text` :450, `statement_text` :460, `lex` :466, `refused_statements` :633 (lines 161-675 UNVERIFIED beyond the def list) | test_migration_numbers, test_migration_numbers_guards, migration_numbers_mutants |
| store/migrations/0001..0005 (202) | The schema, see section 3 | - | test_k2_migrations, test_p2_postgres, test_k5_fixes2 |
| audit/protocol.py (35) | The audit sink interface and its two errors | `AuditUnavailable` :10, `DuplicateEvent` :14, `AuditSink` (Protocol) :18 | contracts/test_capabilities, test_s2_audit |
| audit/local_dir.py (176) | Audit as one JSON file per event in a folder plus `index.jsonl`; outbox folder for parked events | `LocalDirSink` :24, `write_intent` :102, `write_outcome` :110, `reconcile` :126, `verify_object` :158, `events` :166 | test_s2_audit, test_review_fixes, test_review_pr3_round2, test_k1b_replay |
| audit/chain.py (547) | Audit as a hash chain in the store's database, signed checkpoints, anchors, verify | `GENESIS` :44, `signer_label` :81, `Verification` :135, `ChainAudit` :152 (`write_intent` :207, `write_outcome` :215, `reconcile` :232, `verify_object` :257, `events` :279, `signed_through` :290, `checkpoint` :295, `verify` :342), `verify_rows` :363, `verify_anchor_bodies` :453, `build` :518 | warden_port/test_audit_chain, test_p3b_neutral_audit, contracts/kinds/audit_chain, contracts/kinds/audit_neutral, test_p7_tick |
| audit/anchors.py (42) | Name and body of a checkpoint anchor object, conflict rule | `PREFIX` :9, `AnchorConflict` :12, `key` :16, `body` :20, `parse` :35, `already_there` :40 | contracts/test_anchor, test_p3b_neutral_audit |
| audit/anchor_s3.py (97), anchor_azure.py (96), anchor_gcs.py (85) | Write-once anchor stores (UNVERIFIED: only class lines listed) | `S3Anchor` anchor_s3.py:30, `AzureBlobAnchor` anchor_azure.py:30, `GcsAnchor` anchor_gcs.py:26 | contracts/test_anchor (UNVERIFIED) |
| audit/signer.py (212), signer_aws/azure/gcp/vault.py (55/63/61/81) | Checkpoint signers (UNVERIFIED: only def lines listed) | `Signer` (Protocol) signer.py:32, `verify_signature` :45, `LocalSigner` :63, `KmsSigner` signer_aws.py:24, `AzureKeyVaultSigner` signer_azure.py:29, `GcpKmsSigner` signer_gcp.py:32, `VaultTransitSigner` signer_vault.py:26 | contracts/test_signer (UNVERIFIED) |
| models.py (319) | Every stored shape; money is Decimal; canonical hash refuses floats | `now` :20, `new_id` :24, `canonical_json` :43, `sha256_hex` :51, `RunState` :60, `OPEN_STATES` :80, `Run` :95 (`cost_usd` :103), `Plan` :114, `GateDecision` :151, `ApprovalRequest` :165, `ApprovalDecision` :182, `AuditEvent` :193, `DeadLetter` :223, `TickState` :230, `ToolCallRecord` :240, `KillSwitch` :256, `GateRun` :262, `Reply` :294 (`cost_usd` :299), `Verdict` :305 (`cost_usd` :310), `RunResult` :315 | test_s1_foundation and most others |
| config.py (543) | Loads and validates `config.yaml`: routes with prices, backends, retention, evidence, stage rules | `Money` :64, `Route` :72, `Backends` :79, `K1bSettings` :190, `Retention` :203, `EvidenceSettings` :225, `SourceConfig` :300, `Settings` :335, `Config` :340, `load_yaml` :482, `confined` :496, `load_config` :523 (lines 96-185, 225-334, 469-543 UNVERIFIED beyond def list) | test_s1_foundation, test_client_profile, test_stage_names, test_k3_pilot_env, test_p1b_backends |
| registry.py (382) | Agents, principals, chains, contracts, tool manifests; config hash | `Budget` :34, `AgentRecord` :40 (`budget_usd` :50, `max_run_usd` :54), `Chain` :59, `Registry` :66, `load_registry` :208 (lines 76-382 UNVERIFIED beyond def list) | test_s1_foundation, test_k3_pilot, test_k3_review_fixes, test_k5_round6 |
| identity.py (15) | A person or service with rights and approver roles | `Principal` :10 | test_s3_gate, test_p7_tick |
| stages.py (23) | The three stages and two questions about them | `STAGES` :8, `is_live` :11, `is_prod` :18 | test_stage_names, stage_mutants |
| deferred.py (101) | Refuses config keys and settings whose feature is not built yet; requires `max_run_usd` when live | `DEFERRED_KEYS` :19, `key_problems` :36, `check` :46 | test_k3_pilot, test_stage_names |
| errors.py (5) | Shared config error | `ConfigError` :4 | many |
| defaults.py (131) | One place for default numbers (caps, retention interval, scrub) | constants :13-108, `cut_margin` :52 (body UNVERIFIED) | test_no_hardcoded_values, test_k5_fixes* |
| evals.py (141) | Eval gate: runs the golden set, writes a green run to `qualified.jsonl` | `QUALIFIED` :23, `matches` :26, `gate` :35 | test_k1a_pass_k, test_cuj, test_k5_round5, test_k5_fixes2, test_p6_detectors, contracts/test_llm |
| replay_records.py (88) | Reads `replay-records.jsonl`; green replay record needed for a tooled agent at suggest | `FILE` :24, `MIN_K` :25, `ReplayRecord` :29, `read_records` :46, `has_green_record` :71 | test_k3_pilot, test_k3_review_fixes |
| stats.py (34) | Upper bound on a failure rate | `upper_error_bound` :8 | test_k1b_stats |
| extract.py (64) | Structured extraction with one retry, else a dead letter | `Valid` :19 (`cost_usd` :24), `extract` :34 | test_s4_llm_guard, test_k5_round9 |
| guard/judge.py (109) | A model screens text for injection; its cost rides on the verdict | `PROMPT` :26, `PROMPT_SHA256` :27, `SCHEMA` :28, `make` :39, `JudgeDetector` :62, `qualify` :100 | test_p6_detectors, test_p5p6_followups, test_k5_round7/8/9/11 |
| guard/injection.py (101) | Regex detector, detector list, fail-closed wrapper | `Detector` (Protocol) :19, `RegexDetector` :38, `AnyOf` :61, `combine` :81, `injection_check` :85 | test_p6_detectors, test_p1a_fixes, contracts/kinds/detectors |
| guard/egress.py (30) | Host allowlist check for outbound calls | `EgressRefused` :9, `normalise_host` :13, `egress_check` :25 | test_http_metadata, test_k5_round10, test_repo_rules |
| approvals/gate.py (698) | The "outbound gate": cleans text people read, withholds commands (ported from WARDEN; header :1-9) | `strip_controls` :162, `normalise` :200, `sanitise_text` :312, `WITHHELD` :388, `withhold_commands` :681 (lines 21-698 UNVERIFIED beyond def list) | warden_port/test_gate, warden_port/test_gate_render, test_g4_parity, test_k5_round11 |
| approvals/requests.py (231) | Approval requests, decisions, sweep; audits each step | `summary` :33, `Approvals` :54 (`receive` :71, `request` :95, `resend_unsent` :131, `decide` :146, `update_message` :182, `sweep` :191) (lines 95-231 UNVERIFIED beyond def list) | test_s6_approvals, test_p7_tick, test_k5_round8/9 |
| actions/authorizer.py (50) | The gate decision: allow, needs approval or deny, with a rule id | `authorize` :15 | test_s3_gate |
| actions/contract.py (185) | Action contract shape and risk class; `changes_spend` raises the class | `ActionContract` :47 (`changes_spend` :55), `effective_class` :86, `schema_problems` :118, `schema_errors` :155 | test_k3_pilot, test_k5_round6, test_review_fixes |
| actions/executor.py (179) | The only part that holds a client secret and performs an action | `resolve` :33, `Executor` :47 (`execute` :94, `verify` :169, `rollback` :174) (lines 61-179 UNVERIFIED) | test_executor, test_p1a_fixes, test_review_fixes |
| runtime/runs.py (42) | Run state machine | `ALLOWED` :10, `FINAL` :22, `IllegalTransition` :25, `check` :29, `advance` :37 | test_s1_foundation |
| runtime/agent_loop.py (915) | The live run: limits check, redaction, model loop, charge, gate, execute | `qualified_runs` :112, `assert_qualified` :152, `Hooks` :172, `Runtime` :194 (`handle` :352, `on_decided` :799, `execute` :806) (lines 346-379, 600-690 UNVERIFIED) | test_s5_runtime, test_cuj, test_k5_tools, test_k3_pilot, test_peel_run_id |
| runtime/tick.py (369) | One housekeeping pass: approvals sweep and reconcile, stuck runs, audit checkpoint, evidence purge, source re-probe | `TickContext` :44, `TickStep` :51, `sweep` :79, `reconcile` :85, `stuck` :122, `checkpoint` :177, `purge_evidence` :184, `reprobe_sources` :221, `STEPS` :249, `run_tick` :335 | test_p7_tick, test_no_hardcoded_values |
| llm/protocol.py (28), llm/common.py (265), llm/fake.py (54) | Model interface; reply pricing; recorded fake model | `LLM` (Protocol) protocol.py:18, `ProviderError` :10, `ProviderExhausted` :14; `estimate_tokens` common.py:59, `reply` common.py:152; `FakeLLM` fake.py:21 | test_p5_llm, contracts/test_llm, warden_port/test_providers, test_s4_llm_guard |
| k1b/loop.py (216) | Replay loop for one incident with its own USD cap | `Budget` :40, `CaseOutcome` :56, `CallTimeout` :77, `worst_case_usd` :115, `run_case` :125 | test_k1b_replay, test_k1b_diagnosis |
| k1b/replay.py (277) | Replay of a bundle set; refuses zero prices; writes run.json with `usd` | `ReplayResult` :55, `outputs_files` :78, `replay` :266 (`_replay` :93) | test_k1b_replay, test_k1b_redaction, test_k1b_cli |
| k1b/audit_sink.py (72) | Audit wrapper for replay and score commands | `K1bAudit` :26 (`emit` :31, `emit_outcome` :37), `build_audit` :59 | test_k1b_cli, test_k1b_replay |
| backends/table.py (608), factory.py (69), builtin.py (49) | Which kind builds which backend; `make`; the built-in fakes | `PostgresSettings` table.py:116, `ChainSettings` :192, `TABLE` :386 (store :492-501, audit :502-511), `ALLOWED` :570, `DEFAULTS` :582, `DEMO_ONLY` :593, `NOT_PROD` :608; `Deps` factory.py:18, `make` :29; `memory_store` builtin.py:31, `local_dir_audit` :35 | test_p1b_backends, test_client_profile, test_p7_store |
| app.py (521) | Builds every backend and wires `Limits`, `Runtime`, `Approvals` | `App` :47, `build` :89 (lines 301-521 UNVERIFIED beyond def list) | test_client_profile, test_cuj, test_p1b_backends, test_p7_tick |
| cli.py (414) | Commands: gate, limits stop/reset, tick, migrate, audit verify, replay, score | `main` :70, `replay_cmd` :226, `score_cmd` :248, `audit_verify` :349, `kill_switch` :383 (lines 21-149 UNVERIFIED beyond the parser lines) | test_k1b_cli, test_k2_migrations, test_p2_postgres, test_p7_tick, test_review_pr3_round2 |

## 3. Persistence

### 3.1 Store Protocol (the only store Protocol): `store/protocol.py:49`

32 methods. Columns: Protocol line, MemoryStore line (store/memory.py), PostgresStore line (store/postgres.py).

| # | Signature | proto | mem | pg |
|---|---|---|---|---|
| 1 | `create_run(self, run: Run) -> None` | 50 | 51 | 238 |
| 2 | `get_run(self, run_id: str) -> Run` | 51 | 57 | 244 |
| 3 | `transition(self, run_id: str, expected: RunState, new: RunState, reason_code: str \| None = None) -> Run` | 52 | 61 | 257 |
| 4 | `add_cost(self, run_id: str, usd: Decimal) -> None` (NotFound for an unknown run) | 55 | 76 | 276 |
| 5 | `touch(self, run_id: str) -> None` | 59 | 83 | 279 |
| 6 | `list_runs(self, state: RunState, updated_before: datetime, limit: int = 100) -> list[Run]` | 64 | 92 | 282 |
| 7 | `save_plan(self, plan: Plan) -> None` | 68 | 105 | 293 |
| 8 | `get_plan(self, run_id: str) -> Plan` | 69 | 109 | 296 |
| 9 | `save_gate_decision(self, decision: GateDecision) -> None` (second one raises StaleState) | 71 | 113 | 299 |
| 10 | `get_gate_decision(self, run_id: str) -> GateDecision` | 75 | 119 | 305 |
| 11 | `save_approval_request(self, req: ApprovalRequest) -> None` | 77 | 123 | 310 |
| 12 | `get_approval_request(self, approval_id: str) -> ApprovalRequest` | 78 | 127 | 313 |
| 13 | `update_approval_request(self, req: ApprovalRequest, expected_status: str, expected_step: int) -> None` | 79 | 131 | 316 |
| 14 | `record_decision(self, decision: ApprovalDecision, req: ApprovalRequest, expected_status: str, expected_step: int) -> None` | 82 | 142 | 337 |
| 15 | `list_due_approvals(self, now: datetime) -> list[ApprovalRequest]` | 93 | 160 | 375 |
| 16 | `save_approval_decision(self, decision: ApprovalDecision) -> None` | 94 | 168 | 383 |
| 17 | `get_approval_decision(self, approval_id: str) -> ApprovalDecision \| None` | 98 | 175 | 389 |
| 18 | `list_approvals(self, statuses: set[ApprovalStatus]) -> list[ApprovalRequest]` | 102 | 182 | 399 |
| 19 | `add_dead_letter(self, dl: DeadLetter) -> None` | 104 | 188 | 410 |
| 20 | `list_dead_letters(self, run_id: str) -> list[DeadLetter]` | 105 | 192 | 413 |
| 21 | `add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]` | 107 | 196 | 416 |
| 22 | `spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]` ((day, month), read only) | 108 | 206 | 433 |
| 23 | `get_kill_switch(self) -> KillSwitch` (missing row reads ON) | 112 | 218 | 444 |
| 24 | `set_kill_switch(self, ks: KillSwitch) -> None` | 116 | 222 | 453 |
| 25 | `get_tick_state(self, step: str) -> TickState \| None` | 117 | 226 | 466 |
| 26 | `save_tick_state(self, state: TickState) -> None` | 118 | 231 | 470 |
| 27 | `add_tool_call(self, call: ToolCallRecord) -> None` | 121 | 235 | 475 |
| 28 | `list_tool_calls(self, run_id: str) -> list[ToolCallRecord]` | 125 | 241 | 481 |
| 29 | `purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int` | 129 | 249 | 493 |
| 30 | `put_redaction_map(self, run_id: str, mapping: dict[str, str]) -> None` | 133 | 260 | 496 |
| 31 | `get_redaction_map(self, run_id: str) -> dict[str, str] \| None` | 137 | 264 | 505 |
| 32 | `purge_redaction_maps(self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True) -> int` | 141 | 269 | 512 |

Helpers beside the Protocol: `missing_methods(store) -> list[str]` (store/protocol.py:151), used at start (app.py:194-197).

### 3.2 AuditSink Protocol: `audit/protocol.py:18`

| Signature | line |
|---|---|
| `write_intent(self, event: AuditEvent) -> str` (raises AuditUnavailable) | 19 |
| `write_outcome(self, event: AuditEvent) -> str \| None` (never raises; parks on failure) | 23 |
| `reconcile(self) -> int` (drain the outbox) | 27 |
| `verify_object(self, key: str) -> bool` | 31 |
| `events(self, run_id: str \| None = None) -> list[AuditEvent]` | 33 |

Other Protocols seen in the lane: `Signer` (audit/signer.py:32, methods UNVERIFIED), `LLM` (llm/protocol.py:18, one method `chat` :19-28), `Detector` (guard/injection.py:19, one method `check(text, source) -> Verdict` :20).

### 3.3 Implementations

- Store `memory`: `MemoryStore` (store/memory.py:28), factory `backends/builtin.py:31`, table row backends/table.py:493. Demo only (backends/table.py:599).
- Store `postgres`: `PostgresStore` (store/postgres.py:192), factory `build` (store/postgres.py:152), table row backends/table.py:494. One connection behind one lock (store/postgres.py:193-197).
- Purge store: a second `PostgresStore` built from `purge_dsn_secret_name` (app.py:198-207); used only by the purge step (runtime/tick.py:196).
- No SQLite store. No other store class in `src`.
- Audit `local_dir`: `LocalDirSink` (audit/local_dir.py:24), factory backends/builtin.py:35. Demo only (backends/table.py:600).
- Audit `chain`: `ChainAudit` (audit/chain.py:152), factory `build` (audit/chain.py:518). On the memory store it uses an in-memory SQLite database (audit/chain.py:523-524, 101-105); on Postgres it reuses the store's private connection and lock `store._db`, `store._lock` (audit/chain.py:525-527).
- Files that are not a store but persist lane data: `qualified.jsonl` appended by the eval gate (evals.py:133-140), read by `qualified_runs` (runtime/agent_loop.py:112-135); `replay-records.jsonl` read only (replay_records.py:46); replay `run.json` with `usd` (k1b/replay.py:252-256).

### 3.4 Migrations (`store/migrations/`, applied by `store/migrate.py:283`, ledger table `schema_migrations` created at store/migrate.py:315-318)

| No. | File (lines) | What it creates |
|---|---|---|
| 0001 | 0001_core.sql (100) | Tables `runs` :5 (with `cost_usd NUMERIC` :16), `plans` :22, `gate_decisions` :37, `approval_requests` :46, `approval_decisions` :63, `dead_letters` :77, `spend` :87 (agent_id, day, usd), `kill_switch` :94 (one row, `id = 1`); indexes :20, :61, :75, :85. No kill switch row is inserted here. |
| 0002 | 0002_audit_chain.sql (35) | Tables `audit_entries` :4, `audit_checkpoints` :14, `audit_outbox` :19; index :23; function `hadavin_audit_append_only` :25; four triggers refusing UPDATE, DELETE, TRUNCATE on entries and checkpoints :28-35. The outbox has no trigger (:3). |
| 0003 | 0003_approvals_tick.sql (35) | Columns `approval_requests.sent_at`, `channel_ref` :5-6; removes duplicate decisions :10-11 and adds unique (approval_id, step) :12; table `spend_month` :15 filled from `spend` :21-22; seeds the `kill_switch` row as OFF :25-27; table `tick_state` :30. |
| 0004 | 0004_audit_checkpoint_meta.sql (7) | Columns `audit_checkpoints.alg`, `key_label` :6-7. |
| 0005 | 0005_evidence.sql (25) | Tables `tool_calls` :5 (index :17) and `redaction_maps` :21. |

Role grants per relation: `GRANTS` (store/migrate.py:46-68). Runtime role: read/insert/update on `spend`, `spend_month`, `kill_switch` (:53-55); `audit_outbox` select/insert/delete (:59); audit entries and checkpoints append only (:57-58).

## 4. Money path

Where prices come from:
- `config.yaml` routes: `Route.input_usd_per_mtok`, `output_usd_per_mtok`, `max_tokens` (config.py:72-76); `Money` refuses a float (config.py:57-64). `Config.routes` at config.py:342. There is no other price source in `src`.
- Budgets per agent: `AgentRecord.budget_usd` with `daily` and `monthly` (registry.py:34-37, :50); per-run cap `max_run_usd` (registry.py:54), required when not demo (deferred.py:62-63).

Where a cost is computed (priced):
- Real providers: `llm/common.py:152-180` (`reply`): tokens x route price / 1,000,000 (:166-169). Missing usage is estimated (:164-165) with `estimate_tokens` = 1 token per 3 characters, never 0 (llm/common.py:59-62).
- Fake model: `llm/fake.py:50-54`, tokens from the recording (default 0) x route price.
- Judge detector: copies the reply cost onto the verdict (guard/judge.py:86, :96); a detector list sums them (guard/injection.py:77).
- Extraction: `Valid.cost_usd` sums its replies (extract.py:24-25).
- Worst-case estimate: `k1b/loop.py:115-122` (replay timeouts only).

Where a cost is charged in the live runtime (both writes happen after the call; nothing is reserved before it):
- Model reply: `self.limits.charge(agent_id, reply.cost_usd)` then `self.store.add_cost(run.run_id, reply.cost_usd)` (runtime/agent_loop.py:485-486).
- Paid screen (judge) of the document or of a tool result: `_screen` (runtime/agent_loop.py:321-327), called at :432 and :565.
- `Limits.charge` -> `Store.add_spend(agent_id, today, usd)` (limits.py:17-18). Postgres: day and month counters in one transaction (store/postgres.py:416-431); memory: day dict, month summed on read (store/memory.py:196-204).
- `Store.add_cost` adds to `runs.cost_usd` (store/postgres.py:276-277; store/memory.py:76-81).

Where a budget is checked:
- `Limits.blocked` (limits.py:20-30): kill switch, then `day >= daily`, `month >= monthly`.
- `Runtime._limits_stop` (runtime/agent_loop.py:250-261): calls `blocked`, then the per-run cap `cost_usd >= max_run_usd` (:256-260). Called before the first paid screen (:404), before every model call (:466) and before every tool call (:505).
- At the gate: `blocked` again (runtime/agent_loop.py:716), turned into `deny limits.<reason>` (actions/authorizer.py:43-44); and again before execution (`_recheck`, runtime/agent_loop.py:790).

Replay (K1b), a separate path that does not touch the store's spend:
- `Budget(max_usd)` (k1b/replay.py:136; class k1b/loop.py:40-52); cap parsed by the CLI (`--max-usd`, cli.py:116, :239); must be above zero (k1b/replay.py:114-115); a zero route price is refused unless the model kind is `fake` (k1b/replay.py:85-90).
- Charged: reply cost (k1b/loop.py:179), judge cost (k1b/loop.py:206), worst case on a timed-out call (k1b/loop.py:166-171).
- Checked: `budget.exhausted` before each call (k1b/loop.py:154-156). Reported per run as `usd` (k1b/replay.py:147, :227, :252).

Eval gate: sums reply costs into `cost_per_task_usd` only (evals.py:57, :80, :130); see section 7, item 6.

Reserved or settled: nowhere in `src/hadavin_sdk`. Only in the demo: `Meter.check` (demos/ask-your-data/askdata/meter.py:207), `reserve` (:211-219), `settle` (:221-229), `charge` (:231-240), `worst_case_usd` (:48-55). Callers of the demo meter are UNVERIFIED (demo files other than meter.py were not opened).

## 5. Audit path

Written (intent = before a side effect, must succeed; outcome = after, never raises):
- Sink methods: `LocalDirSink.write_intent` audit/local_dir.py:102, `write_outcome` :110; `ChainAudit.write_intent` audit/chain.py:207, `write_outcome` :215.
- Runtime outcome events through `Runtime._note` (runtime/agent_loop.py:240-241): run received :394, state changes :332, guard stops :259, :400, :419, :428, :434, :593, model failures :483, :491, tool calls :509, :517, :527, :548, :554, :567, :589, proposal :698, :705, recheck :816, :835, :858, :868, action result :889, verify :904, rollback :912. Card posts: `_note_card` :243-248.
- Runtime intent events: gate decision (runtime/agent_loop.py:733-744; failure ends the run `audit_unavailable` :745-746) and execute (:821-827).
- Kill switch: stop writes an outcome after the switch is set (limits.py:45-46); reset writes an intent first (limits.py:50-51).
- Approvals: `Approvals._audit` writes outcomes (approvals/requests.py:81-93), called at :109, :163, :173, :213.
- Tick: stuck runs (runtime/tick.py:133-143) and orphaned waits (:162-172), outcomes.
- Replay and score: `K1bAudit.emit` = intent (k1b/audit_sink.py:31-35), `emit_outcome` (:37-39); callers k1b/replay.py:185, :198, :260 and cli.py:262, :268, :273, :275.
- Read back by the runtime to bind an approval to its inputs: `self.audit.events(run_id)` (runtime/agent_loop.py:844-854).

Parked (when an outcome write fails):
- Chain: first the table `audit_outbox` (audit/chain.py:222-227), then the in-memory list `_pending` (audit/chain.py:228-229; list made at :173).
- Local folder: first a file in `outbox/` (audit/local_dir.py:117-121), then the in-memory list `_pending` (:122-123; list made at :32).

Drained / reconciled:
- `ChainAudit.reconcile` (audit/chain.py:232-246) with `_drain` (:248-255): memory list first, then outbox rows, each deleted once in the chain (:244).
- `LocalDirSink.reconcile` (audit/local_dir.py:126-156): memory list, then outbox files; a corrupt file moves to `outbox/corrupt/` (:144-147).
- **Who calls them: nobody in `src` or `demos`.** A search for `.reconcile(` finds only tests (tests/test_cuj.py:202, tests/test_s2_audit.py:51, tests/test_review_fixes.py:105, tests/test_review_pr3_round2.py:321, tests/contracts/test_capabilities.py:45,59, tests/warden_port/test_audit_chain.py:514,517,677). The tick step named `reconcile` (runtime/tick.py:85-97, :251) is about approvals, not the audit outbox.

Checkpoints and verify:
- `ChainAudit.checkpoint` (audit/chain.py:295-320): inline every `checkpoint_every` rows (:203-204) and from the tick step (runtime/tick.py:177-181). Failed anchors are kept in memory `_unanchored` and retried (audit/chain.py:176, :322-340).
- `ChainAudit.verify` (audit/chain.py:342-360) -> `verify_rows` (:363); CLI `audit verify` -> `audit_verify` (cli.py:207-208, :349-363). Offline: `verify_anchor_bodies` (audit/chain.py:453).

## 6. Stop state

Stored:
- Shape `KillSwitch(on, by, ts)`, default OFF (models.py:256-259).
- Postgres: table `kill_switch`, one row `id = 1` (store/migrations/0001_core.sql:94-100), seeded OFF by 0003 (0003_approvals_tick.sql:25-27); read at store/postgres.py:444-451 (a missing row reads ON and logs an error :446-450); written by upsert at store/postgres.py:453-464.
- Memory: `self._kill = KillSwitch()` (store/memory.py:39), read :218-220, written :222-224. Lost at restart.
- Run end state `STOPPED` (models.py:74; allowed from any non-final state, runtime/runs.py:32; final, runtime/runs.py:22; in the SQL CHECK, 0001_core.sql:14).

Set and cleared:
- `Limits.stop` (limits.py:43-46), `Limits.reset` (limits.py:48-51). Only callers in `src`: CLI `kill_switch` (cli.py:383-410; `limits.stop` :391, `limits.reset` :399), built at cli.py:209. The CLI refuses on the memory store (cli.py:173-182). Reset is refused when the audit intent cannot be written (cli.py:400-406).

Checked:
- `Limits.blocked` reads it (limits.py:22-23).
- Start of a run and before each model or tool call: `_limits_stop` -> `STOPPED kill_switch` (runtime/agent_loop.py:251-253; call sites :404, :466, :505).
- At the gate: `blocked` (runtime/agent_loop.py:716) -> `deny limits.kill_switch` (actions/authorizer.py:43-44) -> run `DENIED` (runtime/agent_loop.py:748-749). Unreadable limits -> `NEEDS_PERSON limits_unavailable` (:715-718).
- Before execution after an approval: `_recheck` (runtime/agent_loop.py:776-797) -> `STOPPED kill_switch` (:814-818).
- Replay has its own halt, not the kill switch: `CaseOutcome.halt` "capped" or "aborted" (k1b/loop.py:68-70, :155, :171, :177), read at k1b/replay.py:175.
- Demo only: a flag-file `KillSwitch` (demos/ask-your-data/askdata/meter.py:253-267).

## 7. Duplicate, dead or inconsistent

1. **CHANGELOG names a migration that is not on this branch.** CHANGELOG.md:49, :56, :63 call the evidence migration `0006_evidence.sql`, numbered "after the reservations migration". On disk it is `0005_evidence.sql` (its own header says version 0005, 0005_evidence.sql:1) and there is no reservations migration or reserve/settle code in `src`. CHANGELOG.md:21-22 tells operators to rename the ledger row `0005_evidence` to `0006_evidence` by hand; on this branch `migrate` would then refuse that database, because an applied version without a file is an error (store/migrate.py:320-326).
2. **The audit outbox is never drained outside tests.** `reconcile` exists on both sinks (audit/chain.py:232, audit/local_dir.py:126) and in the Protocol (audit/protocol.py:27) but no code in `src` or `demos` calls it (section 5). The tick's `reconcile` step is an approvals step (runtime/tick.py:85). The CLI help line "one pass of approvals sweep, reconcile, stuck runs" (cli.py:6) reads as if it covered it. Parked events in `_pending` (audit/chain.py:173, audit/local_dir.py:32) are lost when the process exits.
3. **Chain outbox is drained in event-id order, not time order**: `ORDER BY event_id` (audit/chain.py:239); event ids are random (`new_id("evt")`, models.py:196, :24-25), so parked events enter the chain in a random order.
4. **`store/migration_numbers.py` (675 lines) is not used by the package.** Its header says so (store/migration_numbers.py:5-6); a search of `src`, `tools` and `.github` finds no import. It duplicates `store/migrate.py`: `check_ledger` (migrate.py:97 vs migration_numbers.py:112), the lock key (migrate.py:69 vs :66), `MIGRATIONS` (migrate.py:20 vs :67), the file-name pattern (`_FILE` with `\d`, migrate.py:71, vs `NAME` with `[0-9]`, :54).
5. **Dead-letter path is dead.** `extract()` (extract.py:34) has no caller in `src`; it returns a `DeadLetter` (extract.py:64) that nothing stores: `add_dead_letter` and `list_dead_letters` (store/protocol.py:104-105) have no caller outside `store/`. The table and its sequence grant still exist (0001_core.sql:77, store/migrate.py:52, :67). `Valid.cost_usd` (extract.py:24) is charged nowhere. Also without a caller in `src`: `save_approval_decision` (store/protocol.py:94; `record_decision` is used instead, approvals/requests.py:170).
6. **Model costs that reach no budget.** The eval gate only sums costs (evals.py:80) and reports a mean (:130); it does not call `Limits.charge`. The judge's own qualification run drops its verdict costs (guard/judge.py:107-108, called at evals.py:109). The approval-summary screen is run without the judge on purpose, "no agent to charge" (app.py:214-216). Replay spends against its own cap only (k1b/loop.py:40).
7. **No reservation in the core; a budget can be overshot.** Charging happens after the call (runtime/agent_loop.py:485-486) and checks are `>=` on what is already booked (limits.py:26-28; runtime/agent_loop.py:257), so one call (and parallel runs of one agent) can pass a cap. A model call that raises `ProviderError` is not charged at all (runtime/agent_loop.py:477-484); same in replay for `ProviderExhausted`/`ProviderError` (k1b/loop.py:173-178). The two writes `add_spend` then `add_cost` (:485-486) are separate statements, so a crash between them leaves agent spend without run cost.
8. **Same name, different thing.** `Budget` in registry.py:34 (daily/monthly) and k1b/loop.py:40 (one USD cap). `KillSwitch` in models.py:256 and demos/ask-your-data/askdata/meter.py:253. `worst_case_usd` in k1b/loop.py:115 and demos/.../meter.py:48 (different arguments). `reconcile` means audit drain (audit/protocol.py:27) and approvals follow-up (runtime/tick.py:85).
9. **The price formula is written four times**: llm/common.py:166-169, llm/fake.py:50-53, k1b/loop.py:119-122, demos/ask-your-data/askdata/meter.py:52-55.
10. **Kill switch default differs by store.** Postgres reads a missing row as ON (store/postgres.py:446-450); the memory store starts OFF (store/memory.py:39). Migration 0001 creates the table without a row (0001_core.sql:94-100); the row only arrives with 0003 (0003_approvals_tick.sql:25-27).
11. **Stale module docstrings.** store/protocol.py:1 ("`memory` now, `postgres` when Portal v0 or S11 needs it") and store/memory.py:1, though the Postgres store exists; audit/protocol.py:1 ("`local_dir` now, `s3` at S11"), though `chain` exists; cli.py:175 ("until Postgres arrives"); audit/local_dir.py:6-8 points to a future S3 sink. runtime/tick.py:4 lists five steps, `STEPS` has six (runtime/tick.py:249-266).
12. **CLI usage text misses a flag.** The header shows `migrate [--runtime-role R] [--portal-role P]` (cli.py:9); the parser also has `--purge-role` (cli.py:100), which README.md:33 and app.py:133-136 treat as required in pilot and prod.
13. **Kill switch audit events always say `source="cli"`** (limits.py:39), also when `Limits.stop` is called in-process, which cli.py:175-179 recommends for the memory store.
14. **Chain audit reaches into the store's private fields** `_db` and `_lock` (audit/chain.py:525-527); a custom store that satisfies the `Store` Protocol but lacks them is refused with "needs store memory or postgres" (audit/chain.py:542-543).
15. **`_LOOPBACK` is defined twice**: config.py:174 and backends/table.py:68.
16. **A zero-cost fake reply never moves a budget.** `FakeLLM` prices from recorded token counts that default to 0 (llm/fake.py:50-52); replay knows this and exempts `fake` from its zero-price refusal (k1b/replay.py:88).
17. **Lane vocabulary without code**: reserve/settle, lease, tenant, needs-a-person queue, a price table and a SQLite store do not exist in `src/hadavin_sdk` (see section 1). If the lane brief expects them, they are still to be built or live on another branch.

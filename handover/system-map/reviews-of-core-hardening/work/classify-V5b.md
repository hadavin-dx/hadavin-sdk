# V5b blind module classification (ORDER 005)

Snapshot: /tmp/claude-0/-home-user/d72bd15c-b484-516a-89e0-703eea3c1a47/scratchpad/snap/ (src/hadavin_sdk, 100 .py files incl. 10 package __init__ files, 17,880 lines). Read-only grep work; no program run. Checkpoint at ~30 min: table drafted, zero-importer modules being traced.

## What I did NOT check
- I did not read module bodies line by line. "Job" comes from each module's docstring plus grep of imports; I did not verify the docstring matches the code.
- Callers of individual public functions: I traced them only for the modules with zero or one importer (extract, receiver, producers, plan, deferred, replay_records). For the others "importers" means files that import the module, not who calls each function. Unused functions inside a used module were not hunted.
- Counts exclude tests/ and the file itself. They include src/ and demos/ (only demos/ask-your-data exists). Regex grep, so a use through an alias or a string built at run time could be missed. I found run-time loading only via `importlib.import_module` in `actions/executor.py:37`, `backends/factory.py:39`, `tools.py:365`.
- I did not read the 12 `__init__.py` files except to see if they re-export (approvals, audit, guard, llm, store, backends, sources). They are not rated.
- No test was run, so "tests" counts (files in tests/ that mention the module) show only that a test exists, not that it passes.
- No docs/ or handover/ file was used as proof, except docs/slack-app*.md for the receiver.
- Skipped: nothing in the module list; the depth is shallow for the large files (guard/redact.py 1254 lines, tools.py 1206, runtime/agent_loop.py 869, approvals/gate.py 698, backends/table.py 604).

## How a kind is loaded (proof used for "registry" column)
`backends/table.py` maps capability -> kind -> factory string "module:function"; `backends/factory.py:39 importlib.import_module(module_name)` loads it only when that kind is built. `pyproject.toml:46-47` has one entry point: `hadavin-sdk = "hadavin_sdk.cli:main"`. No other entry point. So "REG" below = loaded only via table.py.

## Vendor SDK imports outside the kind module (asked flag)
Rule source: tests/test_lockin_guard.py (allowed sets at lines 59-86).
- Every `boto3`/`botocore`, `azure.*`, `google.cloud`, `psycopg`, `anthropic` import I found sits in a file that is itself the kind module for that vendor (secrets_aws/azure/gcp, signer_aws/azure/gcp, anchor_s3/azure/gcs, llm/anthropic, llm/bedrock, guard/bedrock_guardrail, store/postgres, store/migrate). No `openai`, `redis`, `temporalio` or `hvac` import anywhere in src/ or demos/.
- Not the kind module, but allowed by the repo's own guard: `store/auth_aws.py:12 import boto3` (guard line 86 `VENDOR_HELPERS = {store.auth_aws}`, helper for postgres IAM sign-in). Real vendor import in a non-kind file; the guard permits it by name.
- `audit/signer.py:19-22 from cryptography...` (`InvalidSignature`, `hashes, serialization`, `ec, ed25519`, `encode_dss_signature`): `cryptography` is an open-source library, not a cloud vendor; guard line 70 lists allowed holders. Not a lock-in finding, noted for completeness.
- `llm/anthropic.py:72 from google.auth import exceptions as google_auth`: inside the anthropic kind module (the Vertex platform option), so inside its kind.
- `demos/ask-your-data/askdata/pgsource.py:33 import psycopg`: demo, outside the core; the core never imports demos.
- Odd coupling (not a vendor SDK): `approvals/slack_channel.py:23 from hadavin_sdk.llm.common import post_json` - the Slack channel borrows the llm package's HTTP POST helper (also `guard/http.py` NoRedirect is shared by executor, vault, llm). Works, but an approvals kind depending on the llm package is a layering smell.

## Classification table
Legend: IMP = importers outside tests (count; up to 3 file:line), TST = number of test files that mention the module, REG = loaded by table.py string. Classes: NEEDED / DUPLICATE / NOT-NEEDED. Quotes are verbatim from the snapshot.

### actions/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| actions/authorizer.py | Deterministic gate: (principal, agent, plan) -> allow / needs_approval / deny | 1: runtime/agent_loop.py:21 | NEEDED | `from hadavin_sdk.actions.authorizer import authorize` |
| actions/contract.py | Action contract file shape and effective risk class | 7: authorizer.py:8, executor.py:18, app.py:20 | NEEDED | `from hadavin_sdk.actions.contract import ActionContract, HttpExecutor` |
| actions/executor.py | The only component holding a client-system secret; re-checks plan hash, calls with idempotency key | 1: app.py:21 | NEEDED | `from hadavin_sdk.actions.executor import Executor` |
| actions/secrets.py | SecretProvider protocol + FakeSecretProvider | 5: executor.py:19, app.py:22, backends/builtin.py:8 | NEEDED | `from hadavin_sdk.actions.secrets import SecretProvider` |
| actions/secrets_aws.py | `aws_secrets_manager` secrets kind | 1 (REG): backends/table.py:394 | NEEDED (kind) | `"hadavin_sdk.actions.secrets_aws:build",` |
| actions/secrets_azure.py | `azure_key_vault` secrets kind | 0 direct; REG table.py:408 | NEEDED (kind) | `f"{_ACTIONS}.secrets_azure:build",` |
| actions/secrets_gcp.py | `gcp_secret_manager` secrets kind | 0 direct; REG table.py:415 | NEEDED (kind) | `f"{_ACTIONS}.secrets_gcp:build",` |
| actions/secrets_file.py | `mounted_file` secrets kind (no extra) | 0 direct; REG table.py:422 | NEEDED (kind) | `f"{_ACTIONS}.secrets_file:build",` |
| actions/secrets_vault.py | `vault` secrets kind (stdlib HTTP); its `connect` is reused by the vault signer | 2: table.py:401 (REG), audit/signer_vault.py:21 | NEEDED | `from hadavin_sdk.actions.secrets_vault import VaultError, connect` |
| actions/secrets_env.py | `env` secrets kind (dev only) | 1 (REG): table.py:390 | NEEDED (dev-only kind) | `EnvSecretsSettings, "hadavin_sdk.actions.secrets_env:build", status=_UNVERIFIED` |
| actions/secrets_cache.py | Shared TTL cache rules for remote secrets kinds | 5: secrets_aws.py:16, secrets_azure.py:20, secrets_file.py:21 | NEEDED | `from hadavin_sdk.actions.secrets_cache import CachedSecrets` |

### approvals/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| approvals/requests.py | Approval requests and decisions; timeout escalates, never approves | 4: app.py:25, approvals/__init__.py:2, cards.py:14 | NEEDED | `from hadavin_sdk.approvals.requests import Approvals` |
| approvals/channel.py | Channel Protocol, FakeChannel, `clean()` text cleaner | 5: approvals/__init__.py:1, cards.py:13, requests.py:9 | NEEDED | `from hadavin_sdk.approvals.channel import Channel, clean` |
| approvals/cards.py | Pure renderers for the shadow and abstain cards | 6: app.py:24, channel.py:114 (lazy), channel.py:15 | NEEDED | `from hadavin_sdk.approvals.cards import Card, Delivery` |
| approvals/gate.py | Cleans text people read (`sanitise_text`) and withholds commands (`withhold_commands`) | 2: channel.py:10, slack_channel.py:20 | NEEDED (see note) | `from hadavin_sdk.approvals.gate import sanitise_text, withhold_commands` |
| approvals/hmac_v0.py | HMAC "v0" request signing shared by channels | 2: channel.py:9, slack.py:11 | NEEDED | `from hadavin_sdk.approvals import hmac_v0` |
| approvals/slack.py | Slack header names and decision parsing on top of hmac_v0 | 1: slack_channel.py:17 | NEEDED (thin) | `from hadavin_sdk.approvals import slack` |
| approvals/slack_channel.py | `slack` channel kind: postMessage with buttons | 1 (REG): table.py:562 | NEEDED (kind) | `"hadavin_sdk.approvals.slack_channel:build",` |
| approvals/receiver.py | Inbound Slack button callbacks (`handle_slack_action`, dev `serve`) | 0 outside tests | NOT-NEEDED today (idle) | `Production hosting is decided at S11; ``serve`` is a stdlib server for development.` |

Notes: `approvals/gate.py` (698 lines of text cleaning) and `guard/redact.py` both clean text but for different jobs (hostile prose/commands vs secrets/personal data); `guard/redact.py:825 strip_ansi` is imported by `gate.py:74`, so they already share code. I rate it NEEDED, not DUPLICATE. `receiver.py` is reachable only from `tests/test_p7_tick.py:18` and mentioned in docs/slack-app.md:17; no CLI command, entry point or table row starts it. Its docstring says hosting is not decided. Rating is a judgement: the Slack button path has no running receiver in the repo.

### audit/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| audit/protocol.py | AuditSink protocol, AuditUnavailable | 10: demos/ask-your-data/askdata/audit.py:18, opscli.py:25, pipeline.py:29 | NEEDED | `from hadavin_sdk.audit.protocol import AuditUnavailable` |
| audit/local_dir.py | Write-once local-folder audit sink | 3: audit/__init__.py:1, backends/builtin.py:10, demos/.../audit.py:17 | NEEDED | `from hadavin_sdk.audit.local_dir import LocalDirSink` |
| audit/chain.py | `chain` audit kind: hash chain in the store with signed checkpoints and anchors | 1 (REG): table.py:506 | NEEDED (kind) | `"hadavin_sdk.audit.chain:build",` |
| audit/signer.py | Signer protocol, local Ed25519 kind, signature verify, `probe` | 6: chain.py:40, signer_aws.py:18, signer_azure.py:22 | NEEDED | `from hadavin_sdk.audit.signer import Alg, Signer, verify_signature` |
| audit/signer_aws.py | `aws_kms` signer | 0 direct; REG table.py:438 | NEEDED (kind) | `f"{_SIGNER}_aws:build",` |
| audit/signer_azure.py | `azure_key_vault_key` signer | 0 direct; REG table.py:445 | NEEDED (kind) | `f"{_SIGNER}_azure:build",` |
| audit/signer_gcp.py | `gcp_kms` signer | 0 direct; REG table.py:452 | NEEDED (kind) | `f"{_SIGNER}_gcp:build",` |
| audit/signer_vault.py | `vault_transit` signer | 0 direct; REG table.py:459 | NEEDED (kind) | `f"{_SIGNER}_vault:build",` |
| audit/anchors.py | Shared anchor naming and "same bytes already there" rule | 4: anchor_azure.py:21, anchor_gcs.py:19, anchor_s3.py:25 | NEEDED | `from hadavin_sdk.audit import anchors` |
| audit/anchor_s3.py | `aws_s3_object_lock` anchor | 0 direct; REG table.py:471 | NEEDED (kind) | `f"{_AUDIT}.anchor_s3:build",` |
| audit/anchor_azure.py | Azure immutable blob anchor | 0 direct; REG table.py:479 | NEEDED (kind) | `f"{_AUDIT}.anchor_azure:build",` |
| audit/anchor_gcs.py | GCS retention-lock anchor | 0 direct; REG table.py:486 | NEEDED (kind) | `f"{_AUDIT}.anchor_gcs:build",` |

Note: two sinks (`local_dir`, `chain`) and `k1b/audit_sink.py` all write audit events; they are layers (sink, chain over store, selector) not copies. `local_dir` has no test file name-matching it (tests=0 for the dotted name) but `LocalDirSink` is the default in `builtin.py:10`.

### guard/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| guard/redact.py | Pattern redaction for logs, audit, channel text | 3: approvals/gate.py:74, guard/__init__.py:3, guard/runmap.py:25 | NEEDED | `from hadavin_sdk.guard.redact import ARN_TAIL, PATTERNS, SECRET_KINDS, kind_of, redact` |
| guard/runmap.py | The run's one redaction map and `redact_text` choke point | 15: actions/authorizer.py:9, approvals/channel.py:11, approvals/requests.py:12 | NEEDED | `from hadavin_sdk.guard.runmap import has_placeholder` |
| guard/injection.py | Regex injection tripwire, `Detector` protocol, `combine` | 11: demos/.../pipeline.py:31, app.py:30, approvals/cards.py:15 | NEEDED | `from hadavin_sdk.guard.injection import Detector, combine` |
| guard/judge.py | `llm_judge` detector kind | 3: table.py:547 (REG), evals.py:15, registry.py:21 | NEEDED | `from hadavin_sdk.guard import judge, runmap` |
| guard/bedrock_guardrail.py | `bedrock_guardrail` detector kind | 1 (REG): table.py:551 | NEEDED (kind) | `"hadavin_sdk.guard.bedrock_guardrail:make",` |
| guard/egress.py | Outbound host allowlist check | 4: actions/executor.py:22, guard/__init__.py:1, guard/http.py:19 | NEEDED | `from hadavin_sdk.guard.egress import EgressRefused, egress_check` |
| guard/http.py | The one no-redirect HTTP opener | 4: executor.py:21, secrets_vault.py:32, llm/common.py:19 | NEEDED | `from hadavin_sdk.guard import http as http_guard` |
| guard/producers.py | Data-only list of producers of model-bound text, read by a test | 0 outside tests (only prose mention at guard/runmap.py:436) | NOT-NEEDED at run time; NEEDED as a test fixture | `Data only: `tests/test_k5_producers.py` parses each function and fails when a producer stops calling its function` |

### store/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| store/protocol.py | Store protocol (rows the core owns) and errors | 13: app.py:40, approvals/receiver.py:15, approvals/requests.py:23 | NEEDED | `from hadavin_sdk.store.protocol import StaleState, Store` |
| store/memory.py | In-memory store (default) | 3: audit/chain.py:520, backends/builtin.py:13, store/__init__.py:1 | NEEDED | `from hadavin_sdk.store.memory import MemoryStore` |
| store/postgres.py | Postgres store kind | 4: table.py:496 (REG), cli.py:327, demos/.../pgsource.py:36 | NEEDED (kind) | `"hadavin_sdk.store.postgres:build",` |
| store/migrate.py | Forward-only schema migrations | 1: cli.py:326 | NEEDED | `from hadavin_sdk.store.migrate import migrate` |
| store/auth_aws.py | RDS IAM token sign-in for postgres | 1: store/postgres.py:115 (lazy) | NEEDED | `from hadavin_sdk.store import auth_aws` |

### runtime/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| runtime/agent_loop.py | The agent loop, plan hand-off, run-state writes, `assert_qualified` | 2: app.py:36, cli.py:283 | NEEDED | `from hadavin_sdk.runtime.agent_loop import Hooks, Runtime` |
| runtime/evidence.py | Cited / grounded evidence checks on a proposal | 3: app.py:35, evals.py:19, agent_loop.py:44 | NEEDED | `from hadavin_sdk.runtime.evidence import Validator, identifier_inputs, with_evidence` |
| runtime/plan.py | Builds a frozen Plan from one proposed call (21 lines) | 1: agent_loop.py:45 | NEEDED (tiny; no test file names it) | `from hadavin_sdk.runtime.plan import build_plan` |
| runtime/runs.py | Run state machine (allowed transitions) | 2: agent_loop.py:46, tick.py:31 | NEEDED | `from hadavin_sdk.runtime.runs import IllegalTransition, advance` |
| runtime/tick.py | `hadavin-sdk tick` housekeeping pass | 1: cli.py:284 | NEEDED | `from hadavin_sdk.runtime.tick import run_tick` |

### actions/ + app wiring and k1b/ (full)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| k1b/atomic.py | Atomic file write (temp, fsync, replace) | 2: cli.py:252, k1b/replay.py:26 | NEEDED | `from hadavin_sdk.k1b.atomic import atomic_write` |
| k1b/audit_sink.py | Builds the audit sink for K1b commands | 2: cli.py:213, replay.py:27 | NEEDED | `from hadavin_sdk.k1b.audit_sink import build_audit` |
| k1b/bundle.py | Load an incident bundle under an allowlist | 5: loop.py:24, redaction.py:34, replay.py:28 | NEEDED | `from hadavin_sdk.k1b.bundle import Bundle, bad_citations, bundle_set_sha256, load_bundles` |
| k1b/causelist.py | Closed set of services and fault types | 2: replay.py:29, score.py:26 | NEEDED | `from hadavin_sdk.k1b.causelist import load_cause_list` |
| k1b/diagnosis.py | Strict JSON parse of the agent's answer | 5: bundle.py:23, loop.py:25, replay.py:30 | NEEDED | `from hadavin_sdk.k1b.diagnosis import Diagnosis, parse_diagnosis` |
| k1b/loop.py | Replay agent loop (one incident, six read tools) | 1: replay.py:25 | NEEDED | `from hadavin_sdk.k1b import loop` |
| k1b/redaction.py | Redacts every string of a case bundle before the model | 2: replay.py:31, report.py:49 | NEEDED (uses runmap, not a copy) | `Uses the runtime's one choke point (``guard.runmap.redact_text``` |
| k1b/replay.py | Runs every incident k times, writes the outputs folder | 2: cli.py:228, score.py:28 | NEEDED | `from hadavin_sdk.k1b.replay import replay` |
| k1b/report.py | Client-facing replay and score Markdown reports | 2: cli.py:253, replay.py:32 | NEEDED | `from hadavin_sdk.k1b.report import render_score_report` |
| k1b/score.py | Lite scorer of replay outputs vs sealed answers | 2: cli.py:254, report.py:13 (type only) | NEEDED | `from hadavin_sdk.k1b.score import REPORT_DIR, audit_result, score` |
| k1b/tools.py | The seven replay-agent tools | 1: loop.py:26 | NEEDED | `from hadavin_sdk.k1b.tools import ALLOWED_TOOLS, NO_DATA, SUBMIT, TOOL_SPECS, Snapshot, render` |

Note: all of k1b is reached only through `cli.py` lines 213-254 (commands `replay` and `score`); the one entry point is `hadavin_sdk.cli:main`. That is "needed" only if the replay check is a sold feature (README "K1b-lite: replay check" says so).

### backends/ and llm/ and sources/ (full, as time allowed)
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| backends/table.py | Capability -> kind -> factory table | 2: factory.py:13, config.py:19 | NEEDED | `from hadavin_sdk.backends.table import ALLOWED, TABLE, KindSettings` |
| backends/factory.py | `make` builds one backend from the table | 3: app.py:28, cli.py:39, k1b/audit_sink.py:15 | NEEDED | `from hadavin_sdk.backends.factory import make` |
| backends/builtin.py | Factories for kinds needing no extra | 1 (REG): table.py:379 | NEEDED | `_BUILTIN = "hadavin_sdk.backends.builtin"` |
| backends/platform_secrets.py | Secret reader limited to a backend's own `*_secret_name` values | 4: app.py:27, factory.py:12, cli.py:38 | NEEDED | `from hadavin_sdk.backends import platform_secrets` |
| llm/protocol.py | LLM Protocol, ProviderError | 9: demos/.../pipeline.py:32, app.py:32, evals.py:16 | NEEDED | `from hadavin_sdk.llm.protocol import LLM` |
| llm/common.py | Shared tool/doc shaping, cost, stdlib JSON POST | 9: demos/.../llm_io.py:20, approvals/slack_channel.py:23 | NEEDED | `from hadavin_sdk.llm.common import post_json` |
| llm/retry.py | Bounded retries with backoff | 2: bedrock.py:28, common.py:20 | NEEDED | `from hadavin_sdk.llm.retry import with_retry` |
| llm/fake.py | Recorded-answer fake model | 3: builtin.py:12, demos/.../evalcli.py:42, llm/__init__.py:1 | NEEDED | `from hadavin_sdk.llm.fake import FakeLLM` |
| llm/anthropic.py | `anthropic` llm kind | 1 (REG): table.py:517 | NEEDED (kind) | `"hadavin_sdk.llm.anthropic:make",` |
| llm/bedrock.py | `bedrock` llm kind | 1 (REG): table.py:524 | NEEDED (kind) | `"hadavin_sdk.llm.bedrock:make",` |
| llm/openai_compat.py | `openai_compat` llm kind | 1 (REG): table.py:531 | NEEDED (kind) | `"hadavin_sdk.llm.openai_compat:make",` |
| llm/gemini.py | `gemini` llm kind | 1 (REG): table.py:538 | NEEDED (kind) | `"hadavin_sdk.llm.gemini:make",` |
| sources/kinds.py | Registry of read-source kinds | 2: app.py:38, config.py:289 | NEEDED | `from hadavin_sdk.sources.kinds import KINDS` |
| sources/kubernetes.py | Kubernetes read source | 1: sources/kinds.py:21 | NEEDED | `from hadavin_sdk.sources.kubernetes import READ_OPERATIONS, KubernetesSettings, KubernetesSource` |

### top-level modules
| module | job | IMP | class | proof quote |
|---|---|---|---|---|
| app.py | Wires every module from one client config | 2: cli.py:282, runtime/tick.py:35 | NEEDED | `from hadavin_sdk.app import build` |
| cli.py | The one console entry point | 1: pyproject.toml:47 | NEEDED | `hadavin-sdk = "hadavin_sdk.cli:main"` |
| config.py | Client config loader | 16: demos/.../config.py:18, fixtures.py:22, meter.py:30 | NEEDED | `from hadavin_sdk.config import Route` |
| registry.py | Agents, principals, chains, action contracts, cross-checked | 13: authorizer.py:12, executor.py:24, app.py:34 | NEEDED | `from hadavin_sdk.registry import Registry, load_registry` |
| models.py | Shared data shapes, ids, canonical hashing | 41: demos/.../audit.py:19, llm_io.py:21, authorizer.py:11 | NEEDED | `from hadavin_sdk.models import AuditEvent` |
| errors.py | ConfigError shared by config and backends | 33: secrets_aws.py:17, secrets_azure.py:21, secrets_cache.py:14 | NEEDED | `from hadavin_sdk.errors import ConfigError` |
| defaults.py | Default numbers of the K5 read path | 7: config.py:18, evals.py:13, guard/runmap.py:24 | NEEDED | `from hadavin_sdk import defaults` |
| deferred.py | Refusal rows for features that arrive later | 3: app.py:17, config.py:18, registry.py:18 | NEEDED | `if problems := deferred.check(reg):` (registry.py:230) |
| replay_records.py | Reader of `replay-records.jsonl` | 1: deferred.py:11 | NEEDED (only one reader; writer absent by design) | `K3 creates the model and the reader; K1b-full adds the writer.` |
| tools.py | Read-only tool manifest and call box | 3: app.py:19, registry.py:24, runtime/agent_loop.py:48 | NEEDED | `from hadavin_sdk import tools as tools_mod` |
| scrub_settings.py | Scrub settings split out so tools.py avoids importing config | 2: config.py:21, tools.py:47 | NEEDED | `tools.py must not import config.py` |
| limits.py | Spend meter, budgets, kill switch | 3: app.py:31, cli.py:43, agent_loop.py:29 | NEEDED | `from hadavin_sdk.limits import Limits` |
| identity.py | Principal model | 3: authorizer.py:10, registry.py:22, agent_loop.py:28 | NEEDED | `from hadavin_sdk.identity import Principal` |
| hashing.py | One digest over a set of files (K1b only) | 3: k1b/bundle.py:22, replay.py:24, score.py:24 | NEEDED (k1b only) | `from hadavin_sdk.hashing import hash_files` |
| stats.py | Clopper-Pearson upper bound | 3: demos/.../evalrun.py:32, evals.py:20, k1b/score.py:29 | NEEDED | `from hadavin_sdk.stats import upper_error_bound` |
| evals.py | Golden-set gate; writes `qualified.jsonl` | 1: cli.py:36 | NEEDED | `from hadavin_sdk import evals` |
| extract.py | Validate a model reply, one retry, then dead letter | 0 outside tests (tests: test_s4_llm_guard.py:49,55) | NOT-NEEDED today (idle) | `"""Structured extraction: validate, one retry with the validator's errors, then a dead letter."""` |

Note on extract.py: no file in src/ or demos/ imports it (grep `hadavin_sdk.extract` and `import extract` hit only tests). Its output type `DeadLetter` is used by the stores, which have their own `add_dead_letter` (store/protocol.py:104), but nothing in the product calls `extract()` to produce one. Also its "one retry" is a same-model retry on a bad reply; check against the studio rule df5 (no call-then-retry for quality) before anyone wires it in. That is a read of the docstring only, not a check of the code.

## Counts per class (91 module files rated; 11 package __init__ files not rated)
- NEEDED: 88 (of which 19 are kind modules loaded only through table.py strings, 10 of them with 0 direct importers)
- DUPLICATE: 0 (candidates examined and rejected: approvals/gate.py vs guard/redact.py share `strip_ansi`; k1b/redaction.py calls `guard.runmap.redact_text`; k1b/atomic.py vs audit/local_dir.py are two different write guarantees: replace vs hard-link)
- NOT-NEEDED (idle in product): 3: approvals/receiver.py, extract.py, guard/producers.py (the last is a test-only data list, so it is needed by the repo guard tests)
- Flags: 1 real vendor import in a non-kind helper (store/auth_aws.py:12, allowed by name in test_lockin_guard.py:86); 1 layering smell (approvals/slack_channel.py:23 imports llm.common)

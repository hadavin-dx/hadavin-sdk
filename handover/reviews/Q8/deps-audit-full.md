<!-- full hand-back report of sub-agent a35f933f, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Single-dependency and least-privilege audit of the merged core (Mode: REVIEW)

Checkout: `/home/user/build/EV-P89-db0d9eb/src/hadavin_sdk`. Standards read in full: `/home/user/hadavin-sdk/CLAUDE.md`, `/home/user/hadavin-sdk/.claude/rules/no-single-dependency.md`, `/home/user/hadavin-sdk/.claude/rules/least-privilege-hard-rule.md`, and the persona file.

**This review is partial.** I read about 20 of 100+ source files in full and reached the rest only by grep. I ran nothing (read-only), so no test result below is verified. No Blocker found; 6 Major, 5 Minor. The exact list of what I did not read is at the end.

Terms used: "kind" = one pluggable backend of a "capability" in `backends/table.py` `TABLE`. "Live" = `pilot` or `prod` (`stages.py:11`), which I take as the "client profile". "Demo-only" = the six pairs in `DEMO_ONLY` (`backends/table.py:593-602`).

## Table

| Kind | Neutral or self-hostable default (file) | Working alternative(s), or outline with trigger | Vendor SDK imports outside that vendor's kind module | Dev-only kinds the client profile fails to refuse | Verdict |
|---|---|---|---|---|---|
| secrets | `vault` (`actions/secrets_vault.py`, stdlib HTTP, Vault/OpenBao) and `mounted_file` (`actions/secrets_file.py`). The default when left out is `fake` (`table.py:583`), demo-only. | `aws_secrets_manager`, `azure_key_vault`, `gcp_secret_manager` (`actions/secrets_aws.py`, `_azure.py`, `_gcp.py`) | None found | Config refuses `fake` and `env` (`config.py:394-397`). `app.build(secrets=<any object>)` is not refused when live (`app.py:82`). | Pass on lock-in; F1, F5 |
| signer | `ed25519_local` (`audit/signer.py`), `vault_transit` (`audit/signer_vault.py`) | `aws_kms`, `azure_key_vault_key`, `gcp_kms` (`audit/signer_aws.py`, `_azure.py`, `_gcp.py`) | None found | `none` is refused only in prod (`table.py:604`); pilot runs an unsigned chain. A key file is allowed in pilot (`config.py:423`). | Pass on lock-in; F9 |
| anchor (blob / object storage, WORM) | `s3_object_lock` with `endpoint_url` for MinIO/Ceph (`audit/anchor_s3.py`). Neutral only through boto3. | `azure_immutable_blob`, `gcs_retention_lock` (`audit/anchor_azure.py`, `anchor_gcs.py`) | None found | `none` allowed in pilot | Pass; F9 |
| store | `postgres` (`store/postgres.py`). Default `memory` is demo-only. | No second live kind. Outline is `EXCEPTIONS["store"]` at `tests/test_lockin_guard.py:382-388`, trigger "a client who refuses Postgres (SQLite kind)", review_by 2027-04-30. | `boto3` at `store/auth_aws.py:12` (AWS RDS sign-in inside the neutral store; allowlisted as `VENDOR_HELPERS`, `test_lockin_guard.py:86`) | Config refuses `memory`. | Pass by exception; F2, F7 |
| audit | `chain` (`audit/chain.py`, own code on the store) | None. `EXCEPTIONS["audit"]` at `test_lockin_guard.py:389-395` has trigger "none", so there is no named trigger. | None found | Config refuses `local_dir`. | Pass by exception; F11 |
| llm | `openai_compat` (`llm/openai_compat.py`, stdlib) | `anthropic` (API, Vertex, Foundry), `bedrock`, `gemini` (`llm/anthropic.py`, `bedrock.py`, `gemini.py`) | `google.auth` at `llm/anthropic.py:72` (GCP library inside the Anthropic kind, for Vertex token errors; allowlisted at `test_lockin_guard.py:48`) | Config refuses `fake`. `app.build(llm=...)` is not refused when live (`app.py:162`). | Pass (owner decision 7 met); F1, F10 |
| detector (injection screen) | `regex` (`guard/injection.py`), `llm_judge` (`guard/judge.py`) | `bedrock_guardrail` (`guard/bedrock_guardrail.py`) | None found | No demo-only kind. `app.build(detector=...)` is not refused when live (`app.py:164`). | Pass; F1 |
| channel (approvals) | None that can run live. `fake` is demo-only. | `slack` only (`approvals/slack_channel.py`, stdlib HTTP, no SDK). Outline is `EXCEPTIONS["channel"]` at `test_lockin_guard.py:396-402`, trigger "first client without Slack (Teams or email-link kind, Phase 2)", review_by 2027-01-31. | No SDK. Slack naming leaks into the shared receiver: `approvals/receiver.py:18` and `:22`. | Config refuses `fake`. `app.build(channel=...)` is not refused when live (`app.py:170`). | Lock-in under a dated exception; F1, F6 |
| read source (second registry, outside `TABLE`) | `kubernetes` (`sources/kubernetes.py`, REST over stdlib) | None built. Outline with trigger "K5-ITO" at `sources/kinds.py:5-7`. | None found | `sources=` and `tools=` overrides are refused when live (`app.py:90-98`). | Pass by outline, but invisible to the coverage guard; F8 |
| action executor (`executor.kind` in `actions/contract.py:19-43`) | `none`, `manual`, `http` (stdlib) | `http` is refused when live and `manual` is deferred (`deferred.py:51-56`) | None found | None found | Not a vendor dependency |
| redaction | Not a kind: own stdlib code in `guard/redact.py` and `guard/runmap.py`, no registry | n/a | None found | n/a | No external dependency found (files not read in full) |
| queue | No such kind. Work is driven by `runtime/tick.py` over the store. | n/a | None (no redis, celery, kafka imports) | n/a | No external dependency |
| observability | No such kind. Stdlib `logging` only; `opentelemetry` is named as future at `test_lockin_guard.py:66`. | n/a | None | n/a | No dependency, and no trace or metric export exists |

**Import scan result.** Every import of `boto3`, `botocore`, `azure`, `google`, `anthropic`, `psycopg` and `cryptography` sits in a module the guard allows. There are no imports of `openai`, `hvac`, `redis`, `stripe`, `slack_sdk`, `httpx`, `requests`, `kubernetes` or `opentelemetry` anywhere in `src/hadavin_sdk`. Other third-party imports are `pydantic`, `pydantic_settings`, `yaml` (base) and `markdown_it` at `approvals/gate.py:72` (allowlisted library). I searched for a fixed list of names; ripgrep lacks look-ahead, so I could not list "everything not in the standard library". The guard does that with `ast`, but I could not run it.

## Findings, most serious first

**F1. Major (least privilege; dev-only kinds not refused in the client profile).** `app.py:62-75`, `:82`, `:162-170`.
- **Flaw:** the demo-only refusal lives only in the config validator (`config.py:394-397`), which checks kind names in YAML. `build()` accepts `secrets=`, `channel=`, `detector=` and `llm=` objects and uses them in any stage. Only `sources=` and `tools=` are refused when live.
- **Scenario:** a pilot or prod entry point calls `build(cfg, agents, channel=FakeChannel(""), llm=FakeLLM(...), secrets=FakeSecretProvider({...}))`. Config passes because the YAML names real kinds, yet approvals go to a recorder, the model is recorded, or secrets come from a literal dict.
- **Fix at the choke point:** one check in `build()` beside lines 90-98 that refuses each of the four overrides when `live`, with the same message shape.
- **Guard test:** none found. `tests/test_stage_names.py` covers the config path (lines 240-267). Its line 313-317 passes `secrets=FakeSecretProvider` to a live-stage build and expects only the restored-hash-key error.

**F2. Major (one identity per function).** `app.py:151-160`, `runtime/tick.py:196`, `cli.py:280-309`.
- **Flaw:** the same process resolves the runtime DSN and the purge DSN (the only role that may DELETE evidence), and also holds the checkpoint signer key and the channel tokens. `tick` builds the whole app and runs purge in that process.
- **Scenario:** tool modules run "with the process's rights" (`registry.py:316`). A compromised tool module or dependency reaches `app.purge_store` and deletes `tool_calls` and `redaction_maps`, or signs forged checkpoints. The database role split in `store/migrate.py:46-68` is sound, but it is undone because one identity can read both secrets.
- **Fix:** give `build()` a role parameter (runtime, tick-purge, audit-verify). Resolve `purge_dsn_secret_name` only for a separate purge command, and document one secrets-store identity per role. Until then, drop the "runtime identity cannot" claim at `app.py:153`.
- **Guard test:** `purge_dsn_secret_name` appears in `tests/test_p7_tick.py`, `tests/test_k5_round10.py` and `tests/test_k3_pilot_env.py` (not read). I found no test that the runtime process cannot obtain the purge credential.

**F3. Major (least-privilege rule item 5: every kind ships its policy).** All cloud kinds: `actions/secrets_aws.py`, `_azure.py`, `_gcp.py`, `audit/signer_*.py`, `audit/anchor_*.py`, `llm/bedrock.py`, `guard/bedrock_guardrail.py`, `store/auth_aws.py`.
- **Flaw:** a search of the whole checkout for policy action names (`kms:Sign`, `secretsmanager:GetSecretValue`, `s3:PutObject`, `bedrock:InvokeModel`, `rds-db:connect`, GCP and Azure role names) found only prose mentions at `store/auth_aws.py:4` and `guard/bedrock_guardrail.py:9`. No policy text, per-action reason or negative test ships for any cloud kind.
- **Scenario:** a client deployer attaches `SecretsManagerReadWrite`, `kms:*` or bucket-wide `s3:*` because nothing states the minimum. The anchor identity can then shorten GOVERNANCE retention, or the runtime can read every secret in the account.
- **Fix:** add a `policy` field to `Entry` in `backends/table.py` (exact actions, resource pattern, one reason per action), and a guard test that fails for any kind with a non-null `extra` or `hosts` and no policy, and for any `*`.
- **Guard test:** none.

**F4. Major (approver identity).** `approvals/slack_channel.py:1-10`, `approvals/requests.py:156-158`.
- **Flaw:** the approver is "the verified Slack user". The rule requires passkey/WebAuthn on an approver identity of its own. Step-up is deferred (`deferred.py:26-27`, "Phase 3"), and `webauthn` is only a comment at `test_lockin_guard.py:76`.
- **What holds:** requester-is-not-approver is enforced at `requests.py:158`.
- **Scenario:** a stolen Slack session or a workspace admin impersonating a user approves a live action with no second factor.
- **Fix:** enforce at `Approvals.receive`, not per channel: a required step-up assertion for the risk classes that need it. Until then, state it as an owner-accepted dated exception in the same list style as `EXCEPTIONS`.
- **Guard test:** none found. `tests/test_s6_approvals.py` not read.

**F5. Major (short-lived credentials).** `backends/table.py:255-259`, `actions/secrets_vault.py:165-168`, `:193`.
- **Flaw:** the Vault connection defaults to `auth: token`, a static token from the `VAULT_TOKEN` environment variable that is never renewed, and it is allowed in pilot and prod. The same applies to the `vault_transit` signer.
- **Scenario:** the root of all platform secrets and the audit signing key is a long-lived token in the process environment, where every tool module and child process can read it. The `env` secrets kind is refused when live for this very reason.
- **Fix:** in the environment table (`config.py`, `_cross_checks`), refuse `auth: token` when live for both kinds that use `_VaultConnection`; make `kubernetes` or `approle` the stated live options.
- **Guard test:** a grep of tests for token-auth refusal in pilot or prod found nothing.

**F6. Major (lock-in; guard gap).** `approvals/receiver.py:18` (`PATH = "/slack/actions"`), `:22` (`handle_slack_action`).
- **Flaw:** the one inbound callback path for all channels is Slack-named in a module the guard treats as neutral.
- **Why the guard misses it:** the "bare vendor name" pattern at `test_lockin_guard.py:520-521` is anchored at string start, so `"/slack/actions"` passes, and function names are never scanned.
- **Scenario:** a Teams or email-link kind (the trigger of the channel exception) must either reuse a Slack-named route or fork the receiver.
- **Fix:** make the receiver neutral (`/channel/actions`, `handle_action`, path taken from the channel object), and widen the pattern to catch a vendor name as a path segment.
- **Guard test:** `tests/test_lockin_guard.py::test_core_logic_names_no_vendor` exists but does not catch this.
- **Related:** `slack_channel.py:23` imports `post_json` from `llm.common`, so the channel layer depends on the model layer for HTTP. Move it to a neutral HTTP helper.

**F7. Minor (lock-in inside a neutral kind).** `store/auth_aws.py:12`, `table.py:121-124`.
- **Flaw:** passwordless database sign-in exists only for AWS RDS. Azure, GCP and on-prem clients must keep a long-lived DSN password in the secrets kind, and no outline or trigger is written for another sign-in.
- **Fix:** turn `iam_auth: bool` into `auth: {kind: ...}` with a small password-source protocol; write the trigger for Entra and Cloud SQL tokens and client certificates.
- **Guard test:** `VENDOR_HELPERS` allows the import; nothing checks an alternative.

**F8. Minor (guard coverage).** `sources/kinds.py:39-47`.
- **Flaw:** the read-source registry is a second kind registry that `coverage_problems` (`test_lockin_guard.py:406-426`) never sees; it iterates `TABLE` only. Its one-kind state rests on a docstring with no review date.
- **Fix:** add `sources.kinds.KINDS` to the coverage check with an `EXCEPTIONS` entry (trigger K5-ITO, review_by date).
- **Guard test:** `test_k5_tools_and_sources_use_the_standard_library_and_pydantic_only` covers imports only.

**F9. Minor (client profile strictness).** `table.py:604`, `config.py:419-424`.
- **Flaw:** pilot is a client stage yet allows `signer: none`, `anchor: none` and a signer key file on disk.
- **Scenario:** a pilot audit trail is an unsigned chain that the runtime's own database role can extend.
- **Fix:** if intended, record it as an owner-dated decision; otherwise move `("signer", "none")` into the live refusals.
- **Guard test:** `tests/test_stage_names.py:343` onward pins the prod-only behaviour, so today's state is deliberate.

**F10. Minor.** `llm/anthropic.py:72` imports `google.auth` inside the Anthropic kind, with the allowance noted at `test_lockin_guard.py:48`. Acceptable, but it means "one vendor per module" is not literally true. A `platform` sub-module would keep it exact.

**F11. Minor.**
- `EXCEPTIONS["audit"].trigger` is the string "none" (`test_lockin_guard.py:392`). It passes the non-empty check at line 422 while naming no trigger. Either name one or make the check refuse "none".
- `markdown_it` is the single parser behind the approval-text sanitiser (`approvals/gate.py:72`), with no alternative noted.
- `secrets: env` carries no `neutral` flag, and the defaults for secrets, store and channel are all demo-only. A live config must therefore name every capability, which is safe but worth stating in the docs.

## What I did not read

- **Read in full:** `backends/{__init__,factory,builtin,table,platform_secrets}.py`, `config.py`, `app.py`, `stages.py`, `deferred.py`, `sources/kinds.py`, `store/auth_aws.py`, `llm/anthropic.py`, `approvals/{slack_channel,receiver,channel}.py`, `actions/{secrets,secrets_env,secrets_vault}.py`, `tests/test_lockin_guard.py`.
- **Read in part:** `cli.py` 190-320, `registry.py` 300-345, `store/migrate.py` 20-94, `audit/signer.py` 1-80, `tests/test_stage_names.py` 200-350.
- **Grep only, not read:** every other file under `src/hadavin_sdk`. That includes all other cloud kind modules, `llm/{bedrock,gemini,openai_compat,common,retry,fake}.py`, `guard/*`, `runtime/*`, `k1b/*`, `tools.py`, `sources/kubernetes.py`, `store/{postgres,memory,protocol}.py`, the SQL migrations, `actions/executor.py`, `approvals/{gate,requests,slack,hmac_v0,cards}.py`, `audit/{chain,local_dir,anchors,protocol}.py`.
- **Not opened:** `tests/test_repo_rules.py`, `tests/test_no_hardcoded_values.py`, the contract tests, `tests/stage_mutants.py`, `pyproject.toml` (extras and pins), `docs/`, `demos/`.
- **Consequence for "no guard test found":** each such statement rests on targeted greps of `tests/`, not on reading the tests.

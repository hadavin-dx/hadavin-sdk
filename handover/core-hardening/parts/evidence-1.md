# evidence-1.md (EVIDENCE RUNNER output; lists, never judges)

- audited sha (`git rev-parse --short=7 HEAD`): b4cce5b
- command: `python3 -I handover/core-hardening/parts/evidence-1.py` (repo root), sampler: `python3 -I handover/core-hardening/parts/evidence-1.py --sample 10 --seed 7`
- SCRIPT_EXIT_CODE: 0 (python3 -I ../evidence-1.py, stderr empty)
- exit codes of git calls: `git ls-files` = 0; `git rev-parse --short=7 HEAD` = 0; `git branch -a` = 0; `git remote -v` = 0
- python: 3.13.18; run date: 2026-11-16 07:01:33 UTC
- thresholds (R4): public_name = no leading underscore; dup_min_statements = 6; dup_difflib_ratio = 0.8; dup_ratio_text = ast.dump text (char level, autojunk off); a token-level ratio >= 0.70 is only a pre-filter; literal_min_chars = 12; claims_regex = (\d+)\s+(tests?|modules?|kinds?|backends?|rules?) | v?\d+\.\d+\.\d+ | port\s*\d{2,5}; md_cap_lines_per_subsection = 200; long_literal_chars_hidden = 40
- files tracked: 16780; in scope: 472; out of scope (handover/ except the listed files): 16308; python files parsed: 289; parse failures: 0; files not opened (name matches env/key pattern): 0
- no pytest, no mutation or plant script, no network, no model call; files written only under handover/core-hardening/parts/
- shallow clone: yes (no history)

### 1 Import graph: src module -> importers (lazy = import inside a function is counted too)

count: 102

hadavin_sdk <- src:13 tests:44 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.deferred, hadavin_sdk.evals, hadavin_sdk.guard.runmap, hadavin_sdk.k1b.redaction, hadavin_sdk.k1b.replay, hadavin_sdk.registry, hadavin_sdk.runtime.tick, hadavin_sdk.scrub_settings, hadavin_sdk.sources.kubernetes, hadavin_sdk.tools | tests: k5_support.py, test_audit_chain.py, test_cuj.py, test_k1a_pass_k.py, test_k1b_cli.py, test_k1b_redaction.py | demos: -
hadavin_sdk.actions <- src:0 tests:1 demos:0 | src importers: - | tests: test_k5_round5.py | demos: -
hadavin_sdk.actions.authorizer <- src:1 tests:1 demos:0 | src importers: hadavin_sdk.runtime.agent_loop | tests: test_s3_gate.py | demos: -
hadavin_sdk.actions.contract <- src:7 tests:5 demos:0 | src importers: hadavin_sdk.actions.authorizer, hadavin_sdk.actions.executor, hadavin_sdk.app, hadavin_sdk.deferred, hadavin_sdk.registry, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.plan | tests: test_k3_pilot.py, test_k5_round10.py, test_k5_round6.py, test_k5_tools.py, test_review_fixes.py | demos: -
hadavin_sdk.actions.executor <- src:1 tests:5 demos:0 | src importers: hadavin_sdk.app | tests: test_executor.py, test_k5_tools.py, test_p1a_fixes.py, test_review_fixes.py, test_review_pr3_round2.py | demos: -
hadavin_sdk.actions.secrets <- src:5 tests:27 demos:0 | src importers: hadavin_sdk.actions.executor, hadavin_sdk.app, hadavin_sdk.backends.builtin, hadavin_sdk.backends.factory, hadavin_sdk.backends.platform_secrets | tests: audit_chain.py, builtin.py, k5_support.py, store_postgres.py, test_audit_chain.py, test_cuj.py | demos: -
hadavin_sdk.actions.secrets_aws <- src:0 tests:2 demos:0 | src importers: - | tests: secrets_cloud.py, test_p4_secrets.py | demos: -
hadavin_sdk.actions.secrets_azure <- src:0 tests:1 demos:0 | src importers: - | tests: secrets_neutral.py | demos: -
hadavin_sdk.actions.secrets_cache <- src:5 tests:0 demos:0 | src importers: hadavin_sdk.actions.secrets_aws, hadavin_sdk.actions.secrets_azure, hadavin_sdk.actions.secrets_file, hadavin_sdk.actions.secrets_gcp, hadavin_sdk.actions.secrets_vault | tests: - | demos: -
hadavin_sdk.actions.secrets_env <- src:0 tests:2 demos:0 | src importers: - | tests: secrets_cloud.py, test_p4_secrets.py | demos: -
hadavin_sdk.actions.secrets_file <- src:0 tests:2 demos:0 | src importers: - | tests: secrets_neutral.py, test_p4b_secrets.py | demos: -
hadavin_sdk.actions.secrets_gcp <- src:0 tests:2 demos:0 | src importers: - | tests: secrets_neutral.py, test_p4b_secrets.py | demos: -
hadavin_sdk.actions.secrets_vault <- src:1 tests:4 demos:0 | src importers: hadavin_sdk.audit.signer_vault | tests: audit_neutral.py, secrets_neutral.py, test_k5_round5.py, test_p4b_secrets.py | demos: -
hadavin_sdk.app <- src:2 tests:20 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.runtime.tick | tests: k5_support.py, test_audit_chain.py, test_cuj.py, test_k1a_pass_k.py, test_k3_leftovers.py, test_k3_pilot.py | demos: -
hadavin_sdk.approvals <- src:5 tests:12 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack, hadavin_sdk.approvals.slack_channel, hadavin_sdk.runtime.agent_loop | tests: test_capabilities.py, test_gate_review2.py, test_gate_review3.py, test_k5_fixes3.py, test_k5_round11.py, test_k5_round12_fuzz.py | demos: -
hadavin_sdk.approvals.cards <- src:4 tests:5 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack_channel, hadavin_sdk.runtime.agent_loop | tests: k5_support.py, test_k3_pilot.py, test_k3_review_fixes.py, test_k5_postgres.py, test_k5_tools.py | demos: -
hadavin_sdk.approvals.channel <- src:5 tests:10 demos:0 | src importers: hadavin_sdk.approvals, hadavin_sdk.approvals.cards, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack_channel, hadavin_sdk.backends.builtin | tests: test_g4_parity.py, test_k3_leftovers.py, test_k3_pilot.py, test_k3_pilot_env.py, test_k5_fixes3.py, test_k5_round11.py | demos: -
hadavin_sdk.approvals.gate <- src:2 tests:6 demos:0 | src importers: hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack_channel | tests: test_g4_parity.py, test_gate.py, test_gate_render.py, test_gate_review2.py, test_gate_review3.py, test_p5p6_followups.py | demos: -
hadavin_sdk.approvals.hmac_v0 <- src:2 tests:2 demos:0 | src importers: hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack | tests: test_capabilities.py, test_p7_tick.py | demos: -
hadavin_sdk.approvals.receiver <- src:0 tests:1 demos:0 | src importers: - | tests: test_p7_tick.py | demos: -
hadavin_sdk.approvals.requests <- src:4 tests:4 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.approvals, hadavin_sdk.approvals.cards, hadavin_sdk.approvals.receiver | tests: test_k5_round12_fuzz.py, test_k5_round8.py, test_k5_round9.py, test_review_pr3_round2.py | demos: -
hadavin_sdk.approvals.slack <- src:1 tests:2 demos:0 | src importers: hadavin_sdk.approvals.slack_channel | tests: test_review_pr3_round2.py, test_s6_approvals.py | demos: -
hadavin_sdk.approvals.slack_channel <- src:0 tests:6 demos:0 | src importers: - | tests: channel_slack.py, test_k5_round11.py, test_k5_round12_fuzz.py, test_k5_round8.py, test_k5_round9.py, test_p7_tick.py | demos: -
hadavin_sdk.audit <- src:6 tests:20 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.audit.anchor_azure, hadavin_sdk.audit.anchor_gcs, hadavin_sdk.audit.anchor_s3, hadavin_sdk.audit.chain, hadavin_sdk.cli | tests: audit_chain.py, k1b_support.py, k5_support.py, test_audit_chain.py, test_capabilities.py, test_cuj.py | demos: -
hadavin_sdk.audit.anchor_azure <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.anchor_gcs <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.anchor_s3 <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_audit_chain.py | demos: -
hadavin_sdk.audit.anchors <- src:4 tests:3 demos:0 | src importers: hadavin_sdk.audit.anchor_azure, hadavin_sdk.audit.anchor_gcs, hadavin_sdk.audit.anchor_s3, hadavin_sdk.audit.chain | tests: test_anchor.py, test_audit_chain.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.chain <- src:0 tests:3 demos:0 | src importers: - | tests: test_audit_chain.py, test_p3b_neutral_audit.py, test_p7_tick.py | demos: -
hadavin_sdk.audit.local_dir <- src:2 tests:0 demos:1 | src importers: hadavin_sdk.audit, hadavin_sdk.backends.builtin | tests: - | demos: audit.py
hadavin_sdk.audit.protocol <- src:7 tests:1 demos:3 | src importers: hadavin_sdk.approvals.requests, hadavin_sdk.audit, hadavin_sdk.audit.chain, hadavin_sdk.audit.local_dir, hadavin_sdk.k1b.audit_sink, hadavin_sdk.limits, hadavin_sdk.runtime.agent_loop | tests: test_pipeline.py | demos: audit.py, opscli.py, pipeline.py
hadavin_sdk.audit.signer <- src:5 tests:7 demos:0 | src importers: hadavin_sdk.audit.chain, hadavin_sdk.audit.signer_aws, hadavin_sdk.audit.signer_azure, hadavin_sdk.audit.signer_gcp, hadavin_sdk.audit.signer_vault | tests: audit_chain.py, audit_neutral.py, test_audit_chain.py, test_k3_pilot.py, test_k3_pilot_env.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.signer_aws <- src:0 tests:3 demos:0 | src importers: - | tests: audit_chain.py, test_audit_chain.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.signer_azure <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.signer_gcp <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.audit.signer_vault <- src:0 tests:2 demos:0 | src importers: - | tests: audit_neutral.py, test_p3b_neutral_audit.py | demos: -
hadavin_sdk.backends <- src:3 tests:2 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.k1b.audit_sink | tests: test_k5_round6_contracts.py, test_secrets.py | demos: -
hadavin_sdk.backends.builtin <- src:0 tests:0 demos:0 | src importers: - | tests: - | demos: -
hadavin_sdk.backends.factory <- src:3 tests:21 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.k1b.audit_sink | tests: audit_chain.py, builtin.py, detectors.py, store_postgres.py, test_audit_chain.py, test_bedrock_provider_r16.py | demos: -
hadavin_sdk.backends.platform_secrets <- src:4 tests:2 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.backends.factory, hadavin_sdk.cli, hadavin_sdk.k1b.audit_sink | tests: test_p4_secrets.py, test_secrets.py | demos: -
hadavin_sdk.backends.table <- src:2 tests:19 demos:0 | src importers: hadavin_sdk.backends.factory, hadavin_sdk.config | tests: audit_chain.py, builtin.py, detectors.py, store_postgres.py, test_audit_chain.py, test_bedrock_provider_r16.py | demos: -
hadavin_sdk.cli <- src:0 tests:10 demos:0 | src importers: - | tests: test_audit_chain.py, test_cuj.py, test_k1a_pass_k.py, test_k1b_cli.py, test_k1b_redaction.py, test_k2_migrations.py | demos: -
hadavin_sdk.config <- src:12 tests:48 demos:4 | src importers: hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets_file, hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.evals, hadavin_sdk.hashing, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.loop, hadavin_sdk.llm.fake, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | tests: builtin.py, k1b_support.py, k5_support.py, test_audit_chain.py, test_cuj.py, test_executor.py | demos: config.py, fixtures.py, meter.py, pipeline.py
hadavin_sdk.defaults <- src:7 tests:14 demos:0 | src importers: hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard.runmap, hadavin_sdk.k1b.redaction, hadavin_sdk.scrub_settings, hadavin_sdk.sources.kubernetes, hadavin_sdk.tools | tests: test_k5_fixes1.py, test_k5_fixes2.py, test_k5_fixes3.py, test_k5_fixes4.py, test_k5_fixes5.py, test_k5_fixes6.py | demos: -
hadavin_sdk.deferred <- src:3 tests:0 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.registry | tests: - | demos: -
hadavin_sdk.errors <- src:33 tests:18 demos:0 | src importers: hadavin_sdk.actions.secrets_aws, hadavin_sdk.actions.secrets_azure, hadavin_sdk.actions.secrets_cache, hadavin_sdk.actions.secrets_env, hadavin_sdk.actions.secrets_file, hadavin_sdk.actions.secrets_gcp, hadavin_sdk.actions.secrets_vault, hadavin_sdk.approvals.slack_channel, hadavin_sdk.audit.anchor_azure, hadavin_sdk.audit.anchor_gcs, hadavin_sdk.audit.chain, hadavin_sdk.audit.signer, hadavin_sdk.audit.signer_aws, hadavin_sdk.audit.signer_azure, hadavin_sdk.audit.signer_gcp, hadavin_sdk.audit.signer_vault, hadavin_sdk.backends.factory, hadavin_sdk.backends.platform_secrets, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.causelist, hadavin_sdk.k1b.replay, hadavin_sdk.k1b.score, hadavin_sdk.llm.anthropic, hadavin_sdk.llm.common, hadavin_sdk.replay_records, hadavin_sdk.store.migrate, hadavin_sdk.store.postgres, hadavin_sdk.store.protocol, hadavin_sdk.tools | tests: test_audit_chain.py, test_bedrock_provider_r16.py, test_k1b_bundle.py, test_k1b_causelist_containment.py, test_k1b_cli.py, test_k1b_diagnosis.py | demos: -
hadavin_sdk.evals <- src:1 tests:10 demos:0 | src importers: hadavin_sdk.cli | tests: test_cuj.py, test_k1a_pass_k.py, test_k1b_stats.py, test_k5_fixes2.py, test_k5_round5.py, test_k5_round9.py | demos: -
hadavin_sdk.extract <- src:0 tests:2 demos:0 | src importers: - | tests: test_k5_round9.py, test_s4_llm_guard.py | demos: -
hadavin_sdk.guard <- src:11 tests:27 demos:0 | src importers: hadavin_sdk.actions.executor, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack_channel, hadavin_sdk.evals, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.judge, hadavin_sdk.k1b.redaction, hadavin_sdk.llm.common, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.tools | tests: k5_support.py, record.py, test_cuj.py, test_k3_pilot.py, test_k5_classes.py, test_k5_fixes1.py | demos: -
hadavin_sdk.guard.bedrock_guardrail <- src:0 tests:5 demos:0 | src importers: - | tests: detectors.py, test_k5_round8.py, test_k5_round9.py, test_p5p6_followups.py, test_p6_detectors.py | demos: -
hadavin_sdk.guard.egress <- src:4 tests:1 demos:0 | src importers: hadavin_sdk.actions.executor, hadavin_sdk.guard, hadavin_sdk.guard.http, hadavin_sdk.tools | tests: test_k5_round10.py | demos: -
hadavin_sdk.guard.http <- src:4 tests:5 demos:0 | src importers: hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets_vault, hadavin_sdk.llm.common, hadavin_sdk.tools | tests: test_k5_fixes1.py, test_k5_fixes2.py, test_k5_round10.py, test_k5_round5.py, test_k5_round9b.py | demos: -
hadavin_sdk.guard.injection <- src:10 tests:10 demos:1 | src importers: hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.approvals.requests, hadavin_sdk.backends.builtin, hadavin_sdk.cli, hadavin_sdk.guard, hadavin_sdk.guard.judge, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.replay, hadavin_sdk.runtime.agent_loop | tests: detectors.py, k1b_support.py, test_capabilities.py, test_k1b_replay.py, test_k5_round7.py, test_k5_round8.py | demos: pipeline.py
hadavin_sdk.guard.judge <- src:2 tests:5 demos:0 | src importers: hadavin_sdk.evals, hadavin_sdk.registry | tests: test_k5_round7.py, test_k5_round8.py, test_k5_round9.py, test_p5p6_followups.py, test_p6_detectors.py | demos: -
hadavin_sdk.guard.producers <- src:0 tests:2 demos:0 | src importers: - | tests: test_k5_producers.py, test_k5_round9.py | demos: -
hadavin_sdk.guard.redact <- src:3 tests:8 demos:0 | src importers: hadavin_sdk.approvals.gate, hadavin_sdk.guard, hadavin_sdk.guard.runmap | tests: test_p5p6_followups.py, test_redaction.py, test_redaction_bank.py, test_redaction_classes.py, test_redaction_review.py, test_redaction_review2.py | demos: -
hadavin_sdk.guard.runmap <- src:15 tests:20 demos:0 | src importers: hadavin_sdk.actions.authorizer, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack_channel, hadavin_sdk.evals, hadavin_sdk.extract, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.redaction, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.tick, hadavin_sdk.tools | tests: record.py, test_k1b_redaction_layers.py, test_k5_classes.py, test_k5_fixes1.py, test_k5_fixes2.py, test_k5_fixes3.py | demos: -
hadavin_sdk.hashing <- src:3 tests:2 demos:0 | src importers: hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.replay, hadavin_sdk.k1b.score | tests: test_k1b_replay.py, test_k1b_stats.py | demos: -
hadavin_sdk.identity <- src:3 tests:2 demos:0 | src importers: hadavin_sdk.actions.authorizer, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | tests: test_p7_tick.py, test_review_pr3_round2.py | demos: -
hadavin_sdk.k1b <- src:1 tests:3 demos:0 | src importers: hadavin_sdk.k1b.replay | tests: test_k1b_cli.py, test_k1b_diagnosis.py, test_k1b_replay.py | demos: -
hadavin_sdk.k1b.atomic <- src:2 tests:1 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.k1b.replay | tests: test_k1b_cli.py | demos: -
hadavin_sdk.k1b.audit_sink <- src:2 tests:3 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.k1b.replay | tests: k1b_support.py, test_k1b_cli.py, test_k1b_replay.py | demos: -
hadavin_sdk.k1b.bundle <- src:5 tests:5 demos:0 | src importers: hadavin_sdk.k1b.loop, hadavin_sdk.k1b.redaction, hadavin_sdk.k1b.replay, hadavin_sdk.k1b.score, hadavin_sdk.k1b.tools | tests: k1b_support.py, test_k1b_bundle.py, test_k1b_cli.py, test_k1b_redaction.py, test_k1b_redaction_layers.py | demos: -
hadavin_sdk.k1b.causelist <- src:2 tests:3 demos:0 | src importers: hadavin_sdk.k1b.replay, hadavin_sdk.k1b.score | tests: k1b_support.py, test_k1b_causelist_containment.py, test_k1b_diagnosis.py | demos: -
hadavin_sdk.k1b.diagnosis <- src:5 tests:2 demos:0 | src importers: hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.replay, hadavin_sdk.k1b.score, hadavin_sdk.k1b.tools | tests: test_k1b_bundle.py, test_k1b_diagnosis.py | demos: -
hadavin_sdk.k1b.loop <- src:1 tests:2 demos:0 | src importers: hadavin_sdk.k1b.replay | tests: test_k1b_diagnosis.py, test_k1b_replay.py | demos: -
hadavin_sdk.k1b.redaction <- src:2 tests:4 demos:0 | src importers: hadavin_sdk.k1b.replay, hadavin_sdk.k1b.report | tests: test_k1b_redaction.py, test_k1b_redaction_layers.py, test_k5_round7.py, test_k5_round8.py | demos: -
hadavin_sdk.k1b.replay <- src:2 tests:2 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.k1b.score | tests: k1b_support.py, test_k1b_replay.py | demos: -
hadavin_sdk.k1b.report <- src:2 tests:2 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.k1b.replay | tests: test_k1b_redaction.py, test_k1b_score.py | demos: -
hadavin_sdk.k1b.score <- src:2 tests:2 demos:0 | src importers: hadavin_sdk.cli, hadavin_sdk.k1b.report | tests: test_k1b_redaction.py, test_k1b_score.py | demos: -
hadavin_sdk.k1b.tools <- src:1 tests:3 demos:0 | src importers: hadavin_sdk.k1b.loop | tests: test_k1b_bundle.py, test_k1b_diagnosis.py, test_k1b_replay.py | demos: -
hadavin_sdk.limits <- src:3 tests:6 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.runtime.agent_loop | tests: k5_support.py, test_k3_pilot.py, test_k5_postgres.py, test_k5_round5.py, test_k5_tools.py, test_s5_runtime.py | demos: -
hadavin_sdk.llm <- src:0 tests:14 demos:0 | src importers: - | tests: detectors.py, llm_wire.py, test_bedrock_provider_r16.py, test_cuj.py, test_k3_pilot.py, test_k5_tools.py | demos: -
hadavin_sdk.llm.anthropic <- src:0 tests:2 demos:0 | src importers: - | tests: llm_wire.py, test_p5p6_followups.py | demos: -
hadavin_sdk.llm.bedrock <- src:0 tests:3 demos:0 | src importers: - | tests: llm_wire.py, test_bedrock_provider_r16.py, test_p5p6_followups.py | demos: -
hadavin_sdk.llm.common <- src:7 tests:8 demos:2 | src importers: hadavin_sdk.approvals.slack_channel, hadavin_sdk.guard.judge, hadavin_sdk.k1b.loop, hadavin_sdk.llm.anthropic, hadavin_sdk.llm.bedrock, hadavin_sdk.llm.gemini, hadavin_sdk.llm.openai_compat | tests: detectors.py, test_bedrock_provider_r16.py, test_k3_pilot.py, test_llm.py, test_p5_llm.py, test_p5p6_followups.py | demos: llm_io.py, meter.py
hadavin_sdk.llm.fake <- src:2 tests:1 demos:1 | src importers: hadavin_sdk.backends.builtin, hadavin_sdk.llm | tests: kit.py | demos: evalcli.py
hadavin_sdk.llm.gemini <- src:0 tests:2 demos:0 | src importers: - | tests: llm_wire.py, test_p5_llm.py | demos: -
hadavin_sdk.llm.openai_compat <- src:0 tests:1 demos:0 | src importers: - | tests: llm_wire.py | demos: -
hadavin_sdk.llm.protocol <- src:8 tests:3 demos:1 | src importers: hadavin_sdk.app, hadavin_sdk.evals, hadavin_sdk.extract, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.replay, hadavin_sdk.llm, hadavin_sdk.llm.retry, hadavin_sdk.runtime.agent_loop | tests: test_k1b_replay.py, test_p1a_fixes.py, test_pipeline.py | demos: pipeline.py
hadavin_sdk.llm.retry <- src:2 tests:2 demos:0 | src importers: hadavin_sdk.llm.bedrock, hadavin_sdk.llm.common | tests: test_p5_llm.py, test_p5p6_followups.py | demos: -
hadavin_sdk.models <- src:39 tests:45 demos:2 | src importers: hadavin_sdk.actions.authorizer, hadavin_sdk.actions.contract, hadavin_sdk.actions.executor, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.hmac_v0, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack, hadavin_sdk.approvals.slack_channel, hadavin_sdk.audit.chain, hadavin_sdk.audit.local_dir, hadavin_sdk.audit.protocol, hadavin_sdk.cli, hadavin_sdk.evals, hadavin_sdk.extract, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.replay, hadavin_sdk.limits, hadavin_sdk.llm.anthropic, hadavin_sdk.llm.bedrock, hadavin_sdk.llm.common, hadavin_sdk.llm.fake, hadavin_sdk.llm.gemini, hadavin_sdk.llm.openai_compat, hadavin_sdk.llm.protocol, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.plan, hadavin_sdk.runtime.runs, hadavin_sdk.runtime.tick, hadavin_sdk.store.memory, hadavin_sdk.store.postgres, hadavin_sdk.store.protocol | tests: checks.py, conftest.py, detectors.py, k1b_support.py, k5_support.py, test_audit_chain.py | demos: audit.py, llm_io.py
hadavin_sdk.registry <- src:13 tests:34 demos:0 | src importers: hadavin_sdk.actions.authorizer, hadavin_sdk.actions.executor, hadavin_sdk.app, hadavin_sdk.approvals.requests, hadavin_sdk.cli, hadavin_sdk.deferred, hadavin_sdk.evals, hadavin_sdk.k1b.replay, hadavin_sdk.limits, hadavin_sdk.replay_records, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.plan | tests: k1b_support.py, k5_support.py, test_audit_chain.py, test_cuj.py, test_executor.py, test_k1a_pass_k.py | demos: -
hadavin_sdk.replay_records <- src:1 tests:2 demos:0 | src importers: hadavin_sdk.deferred | tests: test_k3_pilot.py, test_k3_review_fixes.py | demos: -
hadavin_sdk.runtime <- src:1 tests:18 demos:0 | src importers: hadavin_sdk.app | tests: k5_support.py, test_k3_pilot.py, test_k5_classes.py, test_k5_fixes2.py, test_k5_fixes3.py, test_k5_postgres.py | demos: -
hadavin_sdk.runtime.agent_loop <- src:2 tests:13 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.cli | tests: k5_support.py, test_cuj.py, test_k1a_pass_k.py, test_k3_pilot.py, test_k5_fixes1.py, test_k5_postgres.py | demos: -
hadavin_sdk.runtime.evidence <- src:3 tests:9 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.evals, hadavin_sdk.runtime.agent_loop | tests: k5_support.py, test_k5_classes.py, test_k5_fixes2.py, test_k5_postgres.py, test_k5_review.py, test_k5_round10.py | demos: -
hadavin_sdk.runtime.plan <- src:1 tests:0 demos:0 | src importers: hadavin_sdk.runtime.agent_loop | tests: - | demos: -
hadavin_sdk.runtime.runs <- src:2 tests:1 demos:0 | src importers: hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.tick | tests: test_s1_foundation.py | demos: -
hadavin_sdk.runtime.tick <- src:1 tests:12 demos:0 | src importers: hadavin_sdk.cli | tests: test_k5_fixes3.py, test_k5_review.py, test_k5_round12_fuzz.py, test_k5_round5.py, test_k5_round6.py, test_k5_round7.py | demos: -
hadavin_sdk.scrub_settings <- src:2 tests:1 demos:0 | src importers: hadavin_sdk.config, hadavin_sdk.tools | tests: test_k5_layers.py | demos: -
hadavin_sdk.sources <- src:4 tests:8 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.runtime.tick, hadavin_sdk.sources.kinds, hadavin_sdk.sources.kubernetes | tests: sources.py, test_k5_classes.py, test_k5_round10.py, test_k5_round5.py, test_k5_round6_contracts.py, test_k5_round9b.py | demos: -
hadavin_sdk.sources.kinds <- src:2 tests:1 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.config | tests: test_k5_round6_contracts.py | demos: -
hadavin_sdk.sources.kubernetes <- src:1 tests:6 demos:0 | src importers: hadavin_sdk.sources.kinds | tests: sources.py, test_k5_classes.py, test_k5_round5.py, test_k5_round6.py, test_k5_round9b.py, test_sources.py | demos: -
hadavin_sdk.stats <- src:2 tests:2 demos:1 | src importers: hadavin_sdk.evals, hadavin_sdk.k1b.score | tests: test_eval_harness.py, test_k1b_stats.py | demos: evalrun.py
hadavin_sdk.store <- src:2 tests:14 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.store.postgres | tests: k5_support.py, test_k2_migrations.py, test_k3_pilot.py, test_k5_fixes1.py, test_k5_fixes2.py, test_k5_review.py | demos: -
hadavin_sdk.store.auth_aws <- src:1 tests:0 demos:0 | src importers: hadavin_sdk.store.postgres | tests: - | demos: -
hadavin_sdk.store.memory <- src:3 tests:1 demos:0 | src importers: hadavin_sdk.audit.chain, hadavin_sdk.backends.builtin, hadavin_sdk.store | tests: test_k5_round6_contracts.py | demos: -
hadavin_sdk.store.migrate <- src:1 tests:11 demos:0 | src importers: hadavin_sdk.cli | tests: store_postgres.py, test_audit_chain.py, test_k2_migrations.py, test_k5_fixes1.py, test_k5_fixes2.py, test_k5_round10_postgres.py | demos: -
hadavin_sdk.store.postgres <- src:2 tests:2 demos:1 | src importers: hadavin_sdk.cli, hadavin_sdk.store.migrate | tests: test_p3b_neutral_audit.py, test_p7_store.py | demos: pgsource.py
hadavin_sdk.store.protocol <- src:13 tests:9 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.approvals.receiver, hadavin_sdk.approvals.requests, hadavin_sdk.audit.chain, hadavin_sdk.cli, hadavin_sdk.limits, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.runs, hadavin_sdk.runtime.tick, hadavin_sdk.store, hadavin_sdk.store.memory, hadavin_sdk.store.postgres | tests: test_cuj.py, test_k5_review.py, test_k5_round5.py, test_k5_round6_contracts.py, test_k5_tools.py, test_p2_postgres.py | demos: -
hadavin_sdk.tools <- src:3 tests:22 demos:0 | src importers: hadavin_sdk.app, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | tests: test_k1b_redaction_layers.py, test_k5_classes.py, test_k5_fixes1.py, test_k5_fixes2.py, test_k5_fixes3.py, test_k5_fixes4.py | demos: -

### 2a src modules with ZERO importers anywhere (after the exclusions below)

count: 1

hadavin_sdk.backends.builtin (src/hadavin_sdk/backends/builtin.py) | __init__ importers: - | tests: 0 | demos: 0

### 2b-init Excluded: only importers are __init__.py re-exports

(none found)

### 2b-reg Excluded: name found as a string in registry.py, backends/factory.py, backends/builtin.py, sources/kinds.py or deferred.py (module has no src importer)

(none found)

### 2b-entry Excluded: pyproject entry points

count: 1

hadavin_sdk.cli (src/hadavin_sdk/cli.py) | __init__ importers: - | tests: 10 | demos: 0 | pyproject entry point

### 2c Referenced only by tests (no src/demos importer, no __init__, not excluded above)

count: 22

hadavin_sdk.actions.secrets_aws (src/hadavin_sdk/actions/secrets_aws.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.actions.secrets_azure (src/hadavin_sdk/actions/secrets_azure.py) | __init__ importers: - | tests: 1 | demos: 0
hadavin_sdk.actions.secrets_env (src/hadavin_sdk/actions/secrets_env.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.actions.secrets_file (src/hadavin_sdk/actions/secrets_file.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.actions.secrets_gcp (src/hadavin_sdk/actions/secrets_gcp.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.approvals.receiver (src/hadavin_sdk/approvals/receiver.py) | __init__ importers: - | tests: 1 | demos: 0
hadavin_sdk.approvals.slack_channel (src/hadavin_sdk/approvals/slack_channel.py) | __init__ importers: - | tests: 6 | demos: 0
hadavin_sdk.audit.anchor_azure (src/hadavin_sdk/audit/anchor_azure.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.audit.anchor_gcs (src/hadavin_sdk/audit/anchor_gcs.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.audit.anchor_s3 (src/hadavin_sdk/audit/anchor_s3.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.audit.chain (src/hadavin_sdk/audit/chain.py) | __init__ importers: - | tests: 3 | demos: 0
hadavin_sdk.audit.signer_aws (src/hadavin_sdk/audit/signer_aws.py) | __init__ importers: - | tests: 3 | demos: 0
hadavin_sdk.audit.signer_azure (src/hadavin_sdk/audit/signer_azure.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.audit.signer_gcp (src/hadavin_sdk/audit/signer_gcp.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.audit.signer_vault (src/hadavin_sdk/audit/signer_vault.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.extract (src/hadavin_sdk/extract.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.guard.bedrock_guardrail (src/hadavin_sdk/guard/bedrock_guardrail.py) | __init__ importers: - | tests: 5 | demos: 0
hadavin_sdk.guard.producers (src/hadavin_sdk/guard/producers.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.llm.anthropic (src/hadavin_sdk/llm/anthropic.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.llm.bedrock (src/hadavin_sdk/llm/bedrock.py) | __init__ importers: - | tests: 3 | demos: 0
hadavin_sdk.llm.gemini (src/hadavin_sdk/llm/gemini.py) | __init__ importers: - | tests: 2 | demos: 0
hadavin_sdk.llm.openai_compat (src/hadavin_sdk/llm/openai_compat.py) | __init__ importers: - | tests: 1 | demos: 0

### 2d Referenced only by demos

(none found)

### 2e No production importer; mixture of __init__ / tests / demos importers

(none found)

### 2f Candidates: module stem suffix equals a string literal in a registry file

(none found)

### 2g-dynamic Dynamic-import and getattr hits (all python files; line text shown unless it holds a literal over 40 chars)

count: 94

demos/ask-your-data/askdata/cli.py:13 [<module>] import importlib.util
demos/ask-your-data/askdata/cli.py:142 [cmd_setup] spec = importlib.util.spec_from_file_location("askdata_seed", ROOT / "db" / "seed.py")
demos/ask-your-data/askdata/cli.py:144 [cmd_setup] seed = importlib.util.module_from_spec(spec)
demos/ask-your-data/askdata/cli.py:253 [main] code = cmd_setup(getattr(args, "accept_loss", False))
demos/ask-your-data/askdata/pgsource.py:97 [_fail] return PgError(getattr(err, "sqlstate", None), type(err).__name__)
demos/ask-your-data/askdata/pgsource.py:123 [PgSource._connect] if getattr(err, "sqlstate", None) is not None:
demos/ask-your-data/askdata/validate.py:286 [_check_cast] if type(target) is not exp.DataType or getattr(target.this, "name", "") not in CAST_TARGETS:
demos/ask-your-data/askdata/validate.py:343 [_select_names] selects = getattr(query, "selects", None)
src/hadavin_sdk/actions/executor.py:37 [resolve] return getattr(importlib.import_module(module), name)
src/hadavin_sdk/actions/secrets_aws.py:31 [SecretsManagerProvider._fetch] code = getattr(exc, "response", {}).get("Error", {}).get("Code")
src/hadavin_sdk/actions/secrets_file.py:38 [MountedFileProvider._fetch] flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
src/hadavin_sdk/actions/secrets_file.py:39 [MountedFileProvider._fetch] flags |= getattr(os, "O_BINARY", 0)
src/hadavin_sdk/app.py:86 [build] if live and getattr(b.store, "kind", "") == "postgres" and not b.store.purge_dsn_secret_name:
src/hadavin_sdk/app.py:152 [build] if purge_name := getattr(b.store, "purge_dsn_secret_name", None):
src/hadavin_sdk/audit/anchor_azure.py:90 [probed] <line holds a string literal longer than 40 chars; omitted>
src/hadavin_sdk/audit/chain.py:85 [signer_label] label = getattr(signer, "key_label", None)
src/hadavin_sdk/audit/signer.py:150 [_create] fd = os.open(real, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), mode)
src/hadavin_sdk/audit/signer_azure.py:44 [AzureKeyVaultSigner.public_key] kty, crv = (getattr(v, "value", v) for v in (jwk.kty, jwk.crv))
src/hadavin_sdk/backends/factory.py:39 [make] module = importlib.import_module(module_name)
src/hadavin_sdk/backends/factory.py:54 [make] built = getattr(module, func)(settings, deps)
src/hadavin_sdk/backends/factory.py:56 [make] built.key_label = getattr(settings, "key_label", None)
src/hadavin_sdk/backends/table.py:59 [AnthropicSettings._platform_fields] if missing := [n for n in need if not getattr(self, n)]:
src/hadavin_sdk/backends/table.py:278 [_VaultConnection._checks] if missing := [n for n in need if not getattr(self, n)]:
src/hadavin_sdk/cli.py:242 [replay_cmd] acknowledge_masked=getattr(args, "i_know_data_is_already_masked", False),
src/hadavin_sdk/config.py:75 [Backends.entries] out = [(cap, getattr(self, cap)) for cap in TABLE if cap != "detector"]
src/hadavin_sdk/config.py:271 [EvidenceSettings._checks] if bad := [p for p in getattr(self, name) if not 0 < p < 65536]:
src/hadavin_sdk/config.py:357 [Config._cross_checks] if getattr(d, "route", None) is not None and d.route not in self.routes:
src/hadavin_sdk/guard/injection.py:99 [injection_check] name = getattr(detector, "backend", None)
src/hadavin_sdk/guard/runmap.py:446 [redact_text] cache = getattr(mapping, "redact_cache", None)
src/hadavin_sdk/k1b/tools.py:100 [Snapshot.call] out = getattr(self, f"_{name}")(inputs)
src/hadavin_sdk/llm/bedrock.py:89 [_code] response = getattr(exc, "response", None)
src/hadavin_sdk/llm/bedrock.py:95 [detail] response = getattr(exc, "response", None)
src/hadavin_sdk/llm/retry.py:33 [status] for value in (getattr(exc, "status_code", None), getattr(exc, "code", None)):
src/hadavin_sdk/llm/retry.py:51 [_chain] todo += [getattr(e, "reason", None), e.__cause__, e.__context__]
src/hadavin_sdk/llm/retry.py:68 [retry_after] headers = getattr(exc, "headers", None) or getattr(
src/hadavin_sdk/llm/retry.py:69 [retry_after] getattr(exc, "response", None), "headers", None
src/hadavin_sdk/models.py:139 [Plan.hash] if getattr(plan, name) == type(self).model_fields[name].get_default(
src/hadavin_sdk/registry.py:139 [Registry.config_hash] f"llm_{k}": getattr(llm, k)
src/hadavin_sdk/registry.py:148 [Registry.config_hash] if getattr(llm, k, None)
src/hadavin_sdk/runtime/tick.py:109 [stuck_after_s] return steps * getattr(llm, "call_timeout_s", 60) * getattr(llm, "max_attempts", 1) + 60
src/hadavin_sdk/runtime/tick.py:179 [checkpoint] fn = getattr(ctx.app.audit, "checkpoint", None)
src/hadavin_sdk/sources/kubernetes.py:180 [KubernetesSource._call] err.too_large = bool(getattr(exc, "too_large", False))
src/hadavin_sdk/store/protocol.py:159 [missing_methods] if callable(v) and not n.startswith("_") and not callable(getattr(store, n, None))
src/hadavin_sdk/tools.py:284 [<module>] "runpy",
src/hadavin_sdk/tools.py:290 [<module>] "spec_from_file_location",
src/hadavin_sdk/tools.py:291 [<module>] "pkgutil",
src/hadavin_sdk/tools.py:313 [_reach_problems] # somewhere else is refused wherever it appears (a call, an alias, `getattr(importlib, "import_module")`).
src/hadavin_sdk/tools.py:323 [_reach_problems] elif isinstance(n, ast.Call) and getattr(n.func, "id", "") in (
src/hadavin_sdk/tools.py:365 [load_tool_module] return importlib.import_module(module)
src/hadavin_sdk/tools.py:375 [load_tool_module] if getattr(sys.modules[module], "__hadavin_pin__", None) == digest:
src/hadavin_sdk/tools.py:407 [resolve_function] fn = getattr(load_tool_module(module, pins), name)
src/hadavin_sdk/tools.py:423 [read_operations] declared = getattr(load_tool_module(module, pins), "READ_OPERATIONS", {})
tests/contracts/conftest.py:5 [<module>] import pkgutil
tests/contracts/conftest.py:12 [<module>] for _m in pkgutil.iter_modules(kinds.__path__):
tests/contracts/conftest.py:13 [<module>] importlib.import_module(f"{kinds.__name__}.{_m.name}")
tests/contracts/kinds/store_postgres.py:67 [_SplitStore.__getattr__] return getattr(self._main, name)
tests/demo_askdata/conftest.py:10 [<module>] import importlib.util
tests/demo_askdata/conftest.py:31 [load_script] spec = importlib.util.spec_from_file_location(f"askdata_db_{name}", DEMO / "db" / f"{name}.py")
tests/demo_askdata/conftest.py:32 [load_script] mod = importlib.util.module_from_spec(spec)
tests/demo_askdata/gold_runner.py:8 [<module>] import importlib.util
tests/demo_askdata/gold_runner.py:56 [load_goldcheck] spec = importlib.util.spec_from_file_location("goldcheck", DEMO / "data" / "goldcheck.py")
tests/demo_askdata/gold_runner.py:57 [load_goldcheck] mod = importlib.util.module_from_spec(spec)
tests/demo_askdata/test_allowlist.py:77 [test_every_node_class_the_gold_set_uses_is_on_the_validators_node_list] cls = getattr(exp, name)
tests/demo_askdata/test_pipeline.py:234 [FailingIntent.__getattr__] return getattr(self.inner, name)
tests/test_k1b_bundle.py:278 [test_bad_case_name_and_manifest_shape] __import__("shutil").rmtree(d)
tests/test_k1b_redaction.py:227 [test_score_carries_redaction_into_its_meta_and_refuses_mixed_modes] report = __import__("hadavin_sdk.k1b.report", fromlist=["x"]).render_score_report(res)
tests/test_k1b_redaction_layers.py:148 [test_only_known_modules_call_the_bare_pattern_redactor] name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
tests/test_k5_classes.py:437 [test_class_mutability_the_manifest_fields_are_tuples] assert isinstance(getattr(spec, field), tuple), field
tests/test_k5_perf.py:26 [_redact_module] importlib.import_module("hadavin_sdk.guard.redact")
tests/test_k5_producers.py:42 [_called_names] out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
tests/test_k5_producers.py:164 [_is_redactor_value] name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")
tests/test_k5_producers.py:209 [test_in_producer_functions_a_head_slice_only_follows_a_redaction] is_hash = isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "hash"
tests/test_k5_round10.py:186 [test_the_refusal_message_does_not_claim_a_boundary] name = _module(tmp_path, monkeypatch, "r10_loader", "import runpy\n")
tests/test_k5_round11.py:88 [_callee_name] return f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")
tests/test_k5_round5.py:252 [test_m3_a_multi_megabyte_return_is_cut_before_redaction] started = __import__("time").monotonic()
tests/test_k5_round5.py:255 [test_m3_a_multi_megabyte_return_is_cut_before_redaction] assert __import__("time").monotonic() - started < 20
tests/test_k5_round9.py:182 [<module>] __import__("hadavin_sdk.k1b.redaction", fromlist=["x"])
tests/test_k5_round9b.py:41 [_re_cache_text] caches = [getattr(re, n, {}) for n in ("_cache", "_cache2")]
tests/test_k5_round9b.py:71 [<module>] "m = __import__('x', globals(), level=1)\n",
tests/test_k5_round9b.py:72 [<module>] "m = __import__('x', globals(), locals(), [], 1)\n",
tests/test_k5_round9b.py:74 [<module>] <line holds a string literal longer than 40 chars; omitted>
tests/test_k5_round9b.py:76 [<module>] "import builtins\nbuiltins.__import__('x')\n",
tests/test_k5_round9b.py:79 [<module>] "import runpy\nrunpy.run_path('x.py')\n",
tests/test_k5_round9b.py:80 [<module>] <line holds a string literal longer than 40 chars; omitted>
tests/test_k5_round9b.py:81 [<module>] "import importlib.util\n",
tests/test_lockin_guard.py:319 [test_plant_dynamic_import_is_caught] root = _plant(tmp_path, "runtime/x.py", "import importlib\nimportlib.import_module('boto3')\n")
tests/test_lockin_guard.py:326 [test_plant_dunder_import_is_caught] root = _plant(tmp_path, "runtime/x.py", "__import__(name)\n")
tests/test_lockin_guard.py:332 [test_an_allowed_vendor_module_and_dynamic_hook_pass] <line holds a string literal longer than 40 chars; omitted>
tests/test_p1b_backends.py:192 [test_factory_sees_only_what_its_capability_may_use] monkeypatch.setattr("importlib.import_module", lambda name: type("M", (), {"y": factory}))
tests/test_p1b_backends.py:199 [test_factory_sees_only_what_its_capability_may_use] assert (getattr(deps, name) is not None) == (name in ALLOWED[cap]), (cap, name)
tests/test_p1b_backends.py:246 [test_import_error_inside_an_installed_module_is_not_an_extra_hint] monkeypatch.setattr("importlib.import_module", boom)
tests/test_p4b_secrets.py:239 [test_mounted_files_are_checked_on_the_opened_file_never_followed_through_a_link] assert flags & getattr(os, "O_NOFOLLOW", 0) == getattr(os, "O_NOFOLLOW", 0)
tests/test_p7_tick.py:560 [test_audit_chain_build_reports_a_connection_failure_as_store_unavailable.Down] _lock = __import__("threading").Lock()
tests/test_repo_rules.py:247 [import_targets.walk] if isinstance(child, ast.If) and getattr(child.test, "id", "") == "TYPE_CHECKING":

### 2g-deferred deferred.py lines mentioning import / lazy / load

count: 8

src/hadavin_sdk/deferred.py:1 [<module>] """Deferred features, refused at load with the phase they arrive in (kernel design 6.4).
src/hadavin_sdk/deferred.py:3 [<module>] Pure checks that return problem strings; ``registry.load_registry`` and ``config.load_config`` raise them as one
src/hadavin_sdk/deferred.py:7 [<module>] from __future__ import annotations
src/hadavin_sdk/deferred.py:9 [<module>] from typing import TYPE_CHECKING, Any
src/hadavin_sdk/deferred.py:11 [<module>] from hadavin_sdk import replay_records
src/hadavin_sdk/deferred.py:12 [<module>] from hadavin_sdk.actions.contract import effective_class
src/hadavin_sdk/deferred.py:15 [<module>] from hadavin_sdk.registry import Registry
src/hadavin_sdk/deferred.py:87 [check] <line holds a string literal longer than 40 chars; omitted>

### 2g-dotted String literals equal to a module dotted path (or an f-string building one), with the line where built

count: 123

src/hadavin_sdk/app.py:42 [<module>] literal 'hadavin_sdk.app' -> module hadavin_sdk.app
src/hadavin_sdk/approvals/receiver.py:19 [<module>] literal 'hadavin_sdk.receiver' -> module hadavin_sdk
src/hadavin_sdk/approvals/requests.py:26 [<module>] literal 'hadavin_sdk.approvals' -> module hadavin_sdk.approvals
src/hadavin_sdk/audit/chain.py:45 [<module>] literal 'hadavin_sdk.audit.chain' -> module hadavin_sdk.audit.chain
src/hadavin_sdk/backends/table.py:379 [<module>] literal 'hadavin_sdk.backends.builtin' -> module hadavin_sdk.backends.builtin
src/hadavin_sdk/backends/table.py:381 [<module>] literal 'hadavin_sdk.audit' -> module hadavin_sdk.audit
src/hadavin_sdk/backends/table.py:382 [<module>] literal 'hadavin_sdk.audit.signer' -> module hadavin_sdk.audit.signer
src/hadavin_sdk/backends/table.py:383 [<module>] literal 'hadavin_sdk.actions' -> module hadavin_sdk.actions
src/hadavin_sdk/backends/table.py:390 [<module>] literal 'hadavin_sdk.actions.secrets_env:build' -> module hadavin_sdk.actions.secrets_env
src/hadavin_sdk/backends/table.py:394 [<module>] literal 'hadavin_sdk.actions.secrets_aws:build' -> module hadavin_sdk.actions.secrets_aws
src/hadavin_sdk/backends/table.py:496 [<module>] literal 'hadavin_sdk.store.postgres:build' -> module hadavin_sdk.store.postgres
src/hadavin_sdk/backends/table.py:506 [<module>] literal 'hadavin_sdk.audit.chain:build' -> module hadavin_sdk.audit.chain
src/hadavin_sdk/backends/table.py:517 [<module>] literal 'hadavin_sdk.llm.anthropic:make' -> module hadavin_sdk.llm.anthropic
src/hadavin_sdk/backends/table.py:524 [<module>] literal 'hadavin_sdk.llm.bedrock:make' -> module hadavin_sdk.llm.bedrock
src/hadavin_sdk/backends/table.py:531 [<module>] literal 'hadavin_sdk.llm.openai_compat:make' -> module hadavin_sdk.llm.openai_compat
src/hadavin_sdk/backends/table.py:538 [<module>] literal 'hadavin_sdk.llm.gemini:make' -> module hadavin_sdk.llm.gemini
src/hadavin_sdk/backends/table.py:547 [<module>] literal 'hadavin_sdk.guard.judge:make' -> module hadavin_sdk.guard.judge
src/hadavin_sdk/backends/table.py:551 [<module>] literal 'hadavin_sdk.guard.bedrock_guardrail:make' -> module hadavin_sdk.guard.bedrock_guardrail
src/hadavin_sdk/backends/table.py:562 [<module>] literal 'hadavin_sdk.approvals.slack_channel:build' -> module hadavin_sdk.approvals.slack_channel
src/hadavin_sdk/guard/injection.py:16 [<module>] literal 'hadavin_sdk.guard' -> module hadavin_sdk.guard
src/hadavin_sdk/replay_records.py:26 [<module>] literal 'hadavin_sdk.replay_records' -> module hadavin_sdk.replay_records
src/hadavin_sdk/runtime/agent_loop.py:58 [<module>] literal 'hadavin_sdk.runtime' -> module hadavin_sdk.runtime
src/hadavin_sdk/runtime/tick.py:39 [<module>] literal 'hadavin_sdk.tick' -> module hadavin_sdk
src/hadavin_sdk/store/postgres.py:48 [<module>] literal 'hadavin_sdk.store' -> module hadavin_sdk.store
tests/demo_askdata/test_audit.py:19 [write_config] literal 'askdata.yaml' -> module askdata
tests/k5_support.py:54 [<module>] literal 'tests.fixtures.k5_tools:read_logs' -> module tests.fixtures.k5_tools
tests/k5_support.py:117 [k5_cfg] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k1a_pass_k.py:144 [test_old_lines_parse_and_torn_line_warns] literal 'hadavin_sdk.runtime' -> module hadavin_sdk.runtime
tests/test_k1b_redaction.py:227 [test_score_carries_redaction_into_its_meta_and_refuses_mixed_modes] literal 'hadavin_sdk.k1b.report' -> module hadavin_sdk.k1b.report
tests/test_k2_migrations.py:142 [test_cli_migrate_passes_the_portal_role] literal 'hadavin_sdk.store.migrate.migrate' -> module hadavin_sdk.store.migrate
tests/test_k3_pilot.py:332 [test_k3_manual_executor_refused_until_k8] literal 'tests.fixtures.checks:verify_found' -> module tests.fixtures.checks
tests/test_k5_classes.py:138 [test_class_a_every_stored_kind_has_a_grammar_that_refuses_a_glued_secret] literal 'db.prod.internal' -> module UNRESOLVED
tests/test_k5_perf.py:26 [_redact_module] literal 'hadavin_sdk.guard.redact' -> module hadavin_sdk.guard.redact
tests/test_k5_perf.py:27 [_redact_module] literal 'hadavin_sdk.guard.redact' -> module hadavin_sdk.guard.redact
tests/test_k5_review.py:398 [test_review_read_operations_must_be_bound_in_code] literal 'tests.fixtures.k5_unbound' -> module tests.fixtures
tests/test_k5_review.py:450 [test_review_a_manifest_port_list_widens_the_allowlist] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_review.py:402 [test_review_read_operations_must_be_bound_in_code] literal 'tests.fixtures.k5_unbound' -> module tests.fixtures
tests/test_k5_review.py:317 [test_review_a_tool_body_that_hangs_is_abandoned_at_the_total_deadline] literal 'tests.fixtures.k5_tools:slow' -> module tests.fixtures.k5_tools
tests/test_k5_round10.py:32 [_redact_module] literal 'hadavin_sdk.guard.redact' -> module hadavin_sdk.guard.redact
tests/test_k5_round5.py:896 [test_m1_design_a_pin_that_does_not_match_the_source_is_refused] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:516 [test_m5_cluster_suffixes_are_configurable] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:457 [test_m2_an_ordinary_service_name_is_fine] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:514 [test_m5_cluster_suffixes_are_configurable] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:451 [test_m2_hosts_that_are_ip_literals_loopback_or_metadata_are_refused] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:483 [test_m3_too_many_abandoned_bodies_refuse_further_calls] literal 'tests.fixtures.k5_tools:slow' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:886 [test_m1_design_tool_modules_must_be_pinned_in_pilot_and_prod] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:898 [test_m1_design_a_pin_that_does_not_match_the_source_is_refused] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:905 [test_m1_design_a_pin_that_does_not_match_the_source_is_refused] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:407 [test_design_m5_ca_settings_are_validated] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:412 [test_design_m5_ca_settings_are_validated] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round5.py:905 [test_m1_design_a_pin_that_does_not_match_the_source_is_refused] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_round8.py:236 [test_the_k1b_masking_module_does_not_import_the_tools_module] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_k5_round9.py:182 [<module>] literal 'hadavin_sdk.k1b.redaction' -> module hadavin_sdk.k1b.redaction
tests/test_k5_round9b.py:34 [_redact_module] literal 'hadavin_sdk.guard.redact' -> module hadavin_sdk.guard.redact
tests/test_k5_tools.py:1230 [test_k5_acceptance_pilot_agent_investigates_a_recorded_bundle] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:1248 [test_k5_acceptance_pilot_agent_investigates_a_recorded_bundle] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:402 [test_k5_tool_args_are_restored_before_the_call_and_stored_as_placeholders] literal 'tests.fixtures.k5_tools:spy' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:700 [test_k5_a_tool_that_fetches_outside_its_hosts_gets_an_error] literal 'tests.fixtures.k5_tools:fetch_url' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:883 [test_k5_unresolvable_tool_function_fails_at_build] literal 'tests.fixtures.k5_tools:nope' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:1236 [test_k5_acceptance_pilot_agent_investigates_a_recorded_bundle] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:1238 [test_k5_acceptance_pilot_agent_investigates_a_recorded_bundle] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_k5_tools.py:1238 [test_k5_acceptance_pilot_agent_investigates_a_recorded_bundle] literal 'tests.fixtures.k5_tools' -> module tests.fixtures.k5_tools
tests/test_lockin_guard.py:254 [test_plant_neutral_kinds_without_evidence_are_caught] literal 'hadavin_sdk.config:Config' -> module hadavin_sdk.config
tests/test_lockin_guard.py:255 [test_plant_neutral_kinds_without_evidence_are_caught] literal 'hadavin_sdk.audit.signer_aws:build' -> module hadavin_sdk.audit.signer_aws
tests/test_no_hardcoded_values.py:116 [<module>] literal 'db.prod.corp' -> module UNRESOLVED
tests/test_p1a_fixes.py:91 [test_detector_failure_is_logged_and_flagged] literal 'hadavin_sdk.guard' -> module hadavin_sdk.guard
tests/test_p1b_backends.py:130 [planted] literal 'tests.test_p1b_backends:planted_channel' -> module tests.test_p1b_backends
tests/test_p1b_backends.py:235 [test_broken_hadavin_module_keeps_its_own_import_error] literal 'hadavin_sdk.not_a_module:make' -> module hadavin_sdk
tests/test_p1b_backends.py:237 [test_broken_hadavin_module_keeps_its_own_import_error] literal 'hadavin_sdk.not_a_module' -> module hadavin_sdk
tests/test_p2_postgres.py:136 [test_cli_limits_with_an_unreachable_store_exits_4] literal 'hadavin_sdk.backends.builtin.fake_secrets' -> module hadavin_sdk.backends.builtin
tests/test_p2_postgres.py:203 [test_cli_kill_switch_reaches_every_process] literal 'hadavin_sdk.backends.builtin.fake_secrets' -> module hadavin_sdk.backends.builtin
tests/test_p3b_neutral_audit.py:291 [test_rds_iam_without_the_aws_extra_names_the_pip_install] literal 'hadavin_sdk.store.auth_aws' -> module hadavin_sdk.store.auth_aws
tests/test_p3b_neutral_audit.py:280 [test_rds_iam_signs_in_through_store_auth_aws] literal 'db.example' -> module UNRESOLVED
tests/test_p3b_neutral_audit.py:283 [test_rds_iam_signs_in_through_store_auth_aws] literal 'db.example' -> module UNRESOLVED
tests/test_p7_store.py:59 [test_pghost_counts_as_the_host] literal 'db.example.internal' -> module UNRESOLVED
tests/test_p7_tick.py:368 [test_cli_tick_exit_codes] literal 'hadavin_sdk.backends.builtin.fake_secrets' -> module hadavin_sdk.backends.builtin
tests/test_p7_tick.py:391 [test_cli_tick_store_unreachable_exits_4] literal 'hadavin_sdk.backends.builtin.fake_secrets' -> module hadavin_sdk.backends.builtin
tests/test_p7_tick.py:489 [test_cli_tick_unexpected_start_up_failure_exits_2] literal 'hadavin_sdk.app.build' -> module hadavin_sdk.app
tests/test_p7_tick.py:506 [test_cli_migrate_warns_when_new_tables_get_no_grants] literal 'hadavin_sdk.store.migrate.migrate' -> module hadavin_sdk.store.migrate
tests/test_p7_tick.py:90 [test_steps_order_and_summary_line_is_not_a_step] literal 'hadavin_sdk.tick' -> module hadavin_sdk
tests/test_p7_tick.py:99 [test_one_failing_step_lets_the_others_run_and_exits_1] literal 'hadavin_sdk.tick' -> module hadavin_sdk
tests/test_p7_tick.py:425 [test_driver_errors_keep_their_details_out_of_tick_state] literal 'db.internal' -> module UNRESOLVED
tests/test_repo_rules.py:371 [<module>] literal 'hadavin_sdk.backends' -> module hadavin_sdk.backends
tests/test_repo_rules.py:132 [<module>] literal 'hadavin_sdk.actions.secrets' -> module hadavin_sdk.actions.secrets
tests/test_repo_rules.py:133 [<module>] literal 'hadavin_sdk.actions.secrets_env' -> module hadavin_sdk.actions.secrets_env
tests/test_repo_rules.py:134 [<module>] literal 'hadavin_sdk.actions.secrets_aws' -> module hadavin_sdk.actions.secrets_aws
tests/test_repo_rules.py:135 [<module>] literal 'hadavin_sdk.actions.secrets_vault' -> module hadavin_sdk.actions.secrets_vault
tests/test_repo_rules.py:136 [<module>] literal 'hadavin_sdk.actions.secrets_azure' -> module hadavin_sdk.actions.secrets_azure
tests/test_repo_rules.py:137 [<module>] literal 'hadavin_sdk.actions.secrets_gcp' -> module hadavin_sdk.actions.secrets_gcp
tests/test_repo_rules.py:138 [<module>] literal 'hadavin_sdk.actions.secrets_file' -> module hadavin_sdk.actions.secrets_file
tests/test_repo_rules.py:139 [<module>] literal 'hadavin_sdk.actions.secrets_cache' -> module hadavin_sdk.actions.secrets_cache
tests/test_repo_rules.py:140 [<module>] literal 'hadavin_sdk.actions.executor' -> module hadavin_sdk.actions.executor
tests/test_repo_rules.py:141 [<module>] literal 'hadavin_sdk.backends.platform_secrets' -> module hadavin_sdk.backends.platform_secrets
tests/test_repo_rules.py:298 [<module>] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:299 [<module>] literal 'hadavin_sdk.guard.http' -> module hadavin_sdk.guard.http
tests/test_repo_rules.py:300 [<module>] literal 'hadavin_sdk.guard.runmap' -> module hadavin_sdk.guard.runmap
tests/test_repo_rules.py:301 [<module>] literal 'hadavin_sdk.guard.egress' -> module hadavin_sdk.guard.egress
tests/test_repo_rules.py:355 [test_plant_parent_package_import_is_followed] literal 'hadavin_sdk.actions.secrets' -> module hadavin_sdk.actions.secrets
tests/test_repo_rules.py:368 [test_a_type_checking_import_is_not_a_runtime_import] literal 'hadavin_sdk.app' -> module hadavin_sdk.app
tests/test_repo_rules.py:446 [test_plant_a_relative_import_hides_nothing_from_the_transitive_scan] literal 'hadavin_sdk.actions.executor' -> module hadavin_sdk.actions.executor
tests/test_repo_rules.py:461 [test_plant_a_package_relative_import_in_an_init_is_resolved] literal 'hadavin_sdk.actions.secrets' -> module hadavin_sdk.actions.secrets
tests/test_repo_rules.py:313 [test_k5_no_transitive_import_of_actions_from_tools] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:339 [test_plant_transitive_secret_import_is_caught] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:340 [test_plant_transitive_secret_import_is_caught] literal 'hadavin_sdk.actions.executor' -> module hadavin_sdk.actions.executor
tests/test_repo_rules.py:355 [test_plant_parent_package_import_is_followed] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:368 [test_a_type_checking_import_is_not_a_runtime_import] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:409 [<module>] literal 'hadavin_sdk.backends.make' -> module hadavin_sdk.backends
tests/test_repo_rules.py:412 [<module>] literal 'hadavin_sdk.backends.factory.make' -> module hadavin_sdk.backends.factory
tests/test_repo_rules.py:413 [<module>] literal 'hadavin_sdk.backends' -> module hadavin_sdk.backends
tests/test_repo_rules.py:414 [<module>] literal 'hadavin_sdk.backends' -> module hadavin_sdk.backends
tests/test_repo_rules.py:415 [<module>] literal 'hadavin_sdk.backends.factory' -> module hadavin_sdk.backends.factory
tests/test_repo_rules.py:416 [<module>] literal 'hadavin_sdk.backends' -> module hadavin_sdk.backends
tests/test_repo_rules.py:417 [<module>] literal 'hadavin_sdk.backends.make' -> module hadavin_sdk.backends
tests/test_repo_rules.py:418 [<module>] literal 'hadavin_sdk.backends' -> module hadavin_sdk.backends
tests/test_repo_rules.py:419 [<module>] literal 'hadavin_sdk.backends.factory' -> module hadavin_sdk.backends.factory
tests/test_repo_rules.py:420 [<module>] literal 'hadavin_sdk.backends.make' -> module hadavin_sdk.backends
tests/test_repo_rules.py:423 [<module>] literal 'hadavin_sdk.backends.Deps' -> module hadavin_sdk.backends
tests/test_repo_rules.py:446 [test_plant_a_relative_import_hides_nothing_from_the_transitive_scan] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:461 [test_plant_a_package_relative_import_in_an_init_is_resolved] literal 'hadavin_sdk.tools' -> module hadavin_sdk.tools
tests/test_repo_rules.py:314 [test_k5_no_transitive_import_of_actions_from_tools] literal 'hadavin_sdk.actions' -> module hadavin_sdk.actions
tests/test_s3_gate.py:171 [test_raise_read_only_to_reversible] literal 'tests.fixtures.checks:noop' -> module tests.fixtures.checks
tests/test_p4b_secrets.py:323 [test_a_missing_extra_names_the_pip_install] f-string built module path prefix 'hadavin_sdk.actions.'
tests/test_p4b_secrets.py:333 [test_every_secrets_module_is_a_secret_holder] f-string built module path prefix 'hadavin_sdk.actions.'

### 3a Public functions/classes (module level, src and demos) with ZERO references by name in src, tests, demos (definitions do not count; references = Name, Attribute, import alias, keyword, bare-identifier string)

count: 9

src/hadavin_sdk/audit/signer.py:96 function build_local refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:16 function fake_secrets refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:21 function no_signer refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:26 function no_anchor refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:31 function memory_store refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:35 function local_dir_audit refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:39 function fake_llm refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:43 function regex_detector refs src=0 tests=0 demos=0 docs-words=0
src/hadavin_sdk/backends/builtin.py:47 function fake_channel refs src=0 tests=0 demos=0 docs-words=0

### 3b Public functions/classes referenced only from tests

count: 18

demos/ask-your-data/askdata/compare.py:105 function tie_at_cut refs src=0 tests=6 demos=0 docs-words=0
demos/ask-your-data/askdata/compare.py:113 function matches_interpretation refs src=0 tests=3 demos=0 docs-words=0
demos/ask-your-data/askdata/evalset.py:163 function freeze refs src=0 tests=3 demos=0 docs-words=9
demos/ask-your-data/askdata/fixtures.py:73 function write_script refs src=0 tests=13 demos=0 docs-words=0
demos/ask-your-data/askdata/fixtures.py:106 function fixtures_current refs src=0 tests=3 demos=0 docs-words=0
demos/ask-your-data/askdata/ledger.py:128 function line_sha256 refs src=0 tests=4 demos=0 docs-words=0
demos/ask-your-data/data/goldcheck.py:478 function check_execution refs src=0 tests=9 demos=0 docs-words=0
src/hadavin_sdk/approvals/receiver.py:40 function serve refs src=0 tests=28 demos=0 docs-words=2
src/hadavin_sdk/audit/chain.py:453 function verify_anchor_bodies refs src=0 tests=20 demos=0 docs-words=2
src/hadavin_sdk/audit/signer.py:159 function generate_key refs src=0 tests=9 demos=0 docs-words=0
src/hadavin_sdk/audit/signer.py:196 function load_private_key refs src=0 tests=3 demos=0 docs-words=0
src/hadavin_sdk/audit/signer.py:207 function load_public_key refs src=0 tests=2 demos=0 docs-words=0
src/hadavin_sdk/guard/redact.py:1244 function redact_many refs src=0 tests=17 demos=0 docs-words=1
src/hadavin_sdk/sources/__init__.py:40 class IncidentSource refs src=0 tests=6 demos=0 docs-words=0
src/hadavin_sdk/sources/__init__.py:46 class MetricsSource refs src=0 tests=6 demos=0 docs-words=0
src/hadavin_sdk/sources/__init__.py:51 class LogsSource refs src=0 tests=6 demos=0 docs-words=0
src/hadavin_sdk/sources/__init__.py:56 class ChangeSource refs src=0 tests=6 demos=0 docs-words=0
src/hadavin_sdk/sources/kinds.py:50 function register refs src=0 tests=7 demos=0 docs-words=21

### 3c Public methods of public classes with zero references by name (a same-named attribute anywhere counts as a reference)

count: 3

src/hadavin_sdk/guard/http.py:151 method CheckedHTTPHandler.http_open refs by attribute/name = 0 (all areas)
src/hadavin_sdk/guard/http.py:156 method CheckedHTTPSHandler.https_open refs by attribute/name = 0 (all areas)
src/hadavin_sdk/guard/http.py:161 method NoRedirect.redirect_request refs by attribute/name = 0 (all areas)

### 4a Test file -> modules it imports (src and demos), plus test helper modules imported

count: 158

tests/__init__.py (def test_: 0) -> - | test helpers: -
tests/conftest.py (def test_: 0) -> hadavin_sdk.models | test helpers: tests.fixtures.fake_system
tests/contracts/__init__.py (def test_: 0) -> - | test helpers: -
tests/contracts/aws_stub.py (def test_: 0) -> - | test helpers: -
tests/contracts/conftest.py (def test_: 0) -> - | test helpers: tests.contracts, tests.contracts.kinds
tests/contracts/http_fake.py (def test_: 0) -> - | test helpers: -
tests/contracts/kinds/__init__.py (def test_: 0) -> - | test helpers: -
tests/contracts/kinds/audit_chain.py (def test_: 0) -> hadavin_sdk.actions.secrets, hadavin_sdk.audit, hadavin_sdk.audit.signer, hadavin_sdk.audit.signer_aws, hadavin_sdk.backends.factory, hadavin_sdk.backends.table | test helpers: tests.contracts.kinds, tests.contracts.kinds.store_postgres
tests/contracts/kinds/audit_neutral.py (def test_: 0) -> hadavin_sdk.actions.secrets_vault, hadavin_sdk.audit.anchor_azure, hadavin_sdk.audit.anchor_gcs, hadavin_sdk.audit.anchor_s3, hadavin_sdk.audit.signer, hadavin_sdk.audit.signer_azure, hadavin_sdk.audit.signer_gcp, hadavin_sdk.audit.signer_vault | test helpers: tests.contracts.http_fake, tests.contracts.kinds, tests.contracts.kinds.audit_chain, tests.contracts.kinds.secrets_neutral
tests/contracts/kinds/builtin.py (def test_: 0) -> hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config | test helpers: tests.contracts.kinds
tests/contracts/kinds/channel_slack.py (def test_: 0) -> hadavin_sdk.approvals.slack_channel | test helpers: tests.contracts.kinds, tests.fixtures.fake_slack
tests/contracts/kinds/detectors.py (def test_: 0) -> hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.llm, hadavin_sdk.llm.common, hadavin_sdk.models | test helpers: tests.contracts.kinds, tests.fixtures.http_fake
tests/contracts/kinds/llm_wire.py (def test_: 0) -> hadavin_sdk.llm, hadavin_sdk.llm.anthropic, hadavin_sdk.llm.bedrock, hadavin_sdk.llm.gemini, hadavin_sdk.llm.openai_compat | test helpers: tests.contracts.kinds, tests.contracts.kinds.builtin, tests.fixtures.http_fake
tests/contracts/kinds/secrets_cloud.py (def test_: 0) -> hadavin_sdk.actions.secrets_aws, hadavin_sdk.actions.secrets_env | test helpers: tests.contracts.aws_stub, tests.contracts.kinds
tests/contracts/kinds/secrets_neutral.py (def test_: 0) -> hadavin_sdk.actions.secrets_azure, hadavin_sdk.actions.secrets_file, hadavin_sdk.actions.secrets_gcp, hadavin_sdk.actions.secrets_vault | test helpers: tests.contracts.http_fake, tests.contracts.kinds, tests.contracts.vault_fake
tests/contracts/kinds/store_postgres.py (def test_: 0) -> hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.store.migrate | test helpers: tests.contracts.kinds
tests/contracts/sources.py (def test_: 0) -> hadavin_sdk.sources, hadavin_sdk.sources.kubernetes | test helpers: -
tests/contracts/test_anchor.py (def test_: 2) -> hadavin_sdk.audit.anchors | test helpers: tests.contracts.kinds
tests/contracts/test_capabilities.py (def test_: 9) -> hadavin_sdk.approvals, hadavin_sdk.approvals.hmac_v0, hadavin_sdk.audit, hadavin_sdk.guard.injection, hadavin_sdk.models | test helpers: -
tests/contracts/test_llm.py (def test_: 9) -> hadavin_sdk, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.llm, hadavin_sdk.llm.common, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.contracts.kinds.builtin
tests/contracts/test_secrets.py (def test_: 2) -> hadavin_sdk.backends, hadavin_sdk.backends.platform_secrets, hadavin_sdk.errors | test helpers: tests.contracts.kinds
tests/contracts/test_signer.py (def test_: 3) -> hadavin_sdk.audit.signer, hadavin_sdk.errors | test helpers: tests.contracts.kinds
tests/contracts/test_sources.py (def test_: 21) -> hadavin_sdk.sources, hadavin_sdk.sources.kubernetes | test helpers: tests.contracts, tests.contracts.sources
tests/contracts/test_store.py (def test_: 26) -> hadavin_sdk.models, hadavin_sdk.store.protocol | test helpers: -
tests/contracts/vault_fake.py (def test_: 0) -> - | test helpers: -
tests/demo_askdata/__init__.py (def test_: 0) -> - | test helpers: -
tests/demo_askdata/attackrun.py (def test_: 0) -> askdata.validate | test helpers: tests.demo_askdata.corpus
tests/demo_askdata/conftest.py (def test_: 0) -> - | test helpers: -
tests/demo_askdata/corpus.py (def test_: 0) -> - | test helpers: -
tests/demo_askdata/fuzzgen.py (def test_: 0) -> askdata.allowed | test helpers: -
tests/demo_askdata/gold_runner.py (def test_: 0) -> - | test helpers: tests.demo_askdata.conftest, tests.demo_askdata.lumen_standin
tests/demo_askdata/kit.py (def test_: 0) -> askdata, askdata.audit, askdata.fixtures, askdata.ledger, askdata.meter, askdata.pgsource, askdata.pipeline, askdata.prompt, hadavin_sdk.llm.fake | test helpers: -
tests/demo_askdata/lumen_standin.py (def test_: 0) -> - | test helpers: -
tests/demo_askdata/oracle.py (def test_: 0) -> askdata.allowed | test helpers: -
tests/demo_askdata/test_allowlist.py (def test_: 8) -> askdata, askdata.allowed, askdata.derive_allowlist, askdata.validate | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_audit.py (def test_: 17) -> askdata, askdata.cli, askdata.fixtures | test helpers: tests.demo_askdata.kit
tests/demo_askdata/test_cli.py (def test_: 10) -> askdata.cli, askdata.pgsource | test helpers: -
tests/demo_askdata/test_corpus_on_server.py (def test_: 1) -> askdata.pgsource, askdata.validate | test helpers: tests.demo_askdata.corpus
tests/demo_askdata/test_eval_compare.py (def test_: 20) -> askdata, askdata.audit, askdata.compare, askdata.evalrun, askdata.evalset, askdata.fixtures, askdata.meter | test helpers: tests.demo_askdata.kit
tests/demo_askdata/test_eval_harness.py (def test_: 30) -> askdata, askdata.cli, askdata.config, askdata.evalcli, askdata.evalrun, askdata.evalset, askdata.fixtures, askdata.meter, askdata.prompt, hadavin_sdk.stats | test helpers: tests.demo_askdata.kit, tests.demo_askdata.test_audit
tests/demo_askdata/test_gold_data.py (def test_: 25) -> - | test helpers: tests.demo_askdata.conftest, tests.demo_askdata.gold_runner
tests/demo_askdata/test_gold_exec.py (def test_: 4) -> - | test helpers: tests.demo_askdata.gold_runner, tests.demo_askdata.lumen_standin
tests/demo_askdata/test_htmlexport.py (def test_: 9) -> askdata, askdata.evalcli, askdata.htmlexport | test helpers: tests.demo_askdata.test_audit
tests/demo_askdata/test_imports.py (def test_: 3) -> - | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_ledger.py (def test_: 15) -> askdata, askdata.audit, askdata.ledger | test helpers: -
tests/demo_askdata/test_llm_io.py (def test_: 14) -> askdata, askdata.fixtures, askdata.llm_io, askdata.policy, askdata.prompt, askdata.validate, hadavin_sdk.models | test helpers: -
tests/demo_askdata/test_meter.py (def test_: 13) -> askdata.fixtures, askdata.meter | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_pgsource_layers.py (def test_: 16) -> askdata, askdata.pgsource | test helpers: -
tests/demo_askdata/test_pipeline.py (def test_: 24) -> askdata, askdata.audit, askdata.fixtures, askdata.llm_io, askdata.pgsource, askdata.pipeline, askdata.policy, hadavin_sdk.audit.protocol, hadavin_sdk.llm.protocol | test helpers: tests.demo_askdata.kit
tests/demo_askdata/test_roles.py (def test_: 5) -> - | test helpers: -
tests/demo_askdata/test_safe_text.py (def test_: 4) -> askdata.safe_text | test helpers: -
tests/demo_askdata/test_seed.py (def test_: 16) -> - | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_spike_seed.py (def test_: 3) -> - | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_validate.py (def test_: 16) -> askdata, askdata.validate | test helpers: tests.demo_askdata.attackrun, tests.demo_askdata.corpus
tests/demo_askdata/test_validate_fuzz.py (def test_: 1) -> askdata.validate | test helpers: tests.demo_askdata, tests.demo_askdata.fuzzgen, tests.demo_askdata.oracle
tests/demo_askdata/test_validate_harm.py (def test_: 3) -> askdata.validate | test helpers: tests.demo_askdata.attackrun, tests.demo_askdata.conftest, tests.demo_askdata.corpus
tests/demo_askdata/test_validate_mutation.py (def test_: 4) -> askdata.validate | test helpers: tests.demo_askdata.attackrun, tests.demo_askdata.corpus
tests/demo_askdata/test_validate_oracle.py (def test_: 4) -> askdata.validate | test helpers: tests.demo_askdata.corpus
tests/demo_askdata/test_verify_readonly.py (def test_: 10) -> askdata.allowed, askdata.pgsource | test helpers: tests.demo_askdata.conftest
tests/demo_askdata/test_wire.py (def test_: 1) -> askdata.pgsource | test helpers: -
tests/fixtures/__init__.py (def test_: 0) -> - | test helpers: -
tests/fixtures/checks.py (def test_: 0) -> hadavin_sdk.models | test helpers: -
tests/fixtures/fake_slack.py (def test_: 0) -> - | test helpers: -
tests/fixtures/fake_system.py (def test_: 0) -> - | test helpers: -
tests/fixtures/http_fake.py (def test_: 0) -> - | test helpers: -
tests/fixtures/k5_tools.py (def test_: 0) -> - | test helpers: -
tests/fixtures/record.py (def test_: 0) -> hadavin_sdk.guard, hadavin_sdk.guard.runmap | test helpers: -
tests/fixtures/schemas.py (def test_: 0) -> - | test helpers: -
tests/k1b_support.py (def test_: 0) -> hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.guard.injection, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.causelist, hadavin_sdk.k1b.replay, hadavin_sdk.models, hadavin_sdk.registry | test helpers: -
tests/k5_support.py (def test_: 0) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.limits, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.store | test helpers: tests.conftest
tests/reference_scorer.py (def test_: 0) -> - | test helpers: -
tests/test_cuj.py (def test_: 18) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.audit, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.llm, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop, hadavin_sdk.store.protocol | test helpers: -
tests/test_executor.py (def test_: 10) -> hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry | test helpers: -
tests/test_g4_parity.py (def test_: 8) -> hadavin_sdk.approvals.channel, hadavin_sdk.approvals.gate | test helpers: -
tests/test_k1a_pass_k.py (def test_: 8) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | test helpers: -
tests/test_k1b_bundle.py (def test_: 28) -> hadavin_sdk.errors, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.diagnosis, hadavin_sdk.k1b.tools | test helpers: tests.k1b_support
tests/test_k1b_causelist_containment.py (def test_: 5) -> hadavin_sdk.errors, hadavin_sdk.k1b.causelist | test helpers: -
tests/test_k1b_cli.py (def test_: 21) -> hadavin_sdk, hadavin_sdk.audit, hadavin_sdk.cli, hadavin_sdk.errors, hadavin_sdk.k1b, hadavin_sdk.k1b.atomic, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.bundle | test helpers: tests.k1b_support
tests/test_k1b_diagnosis.py (def test_: 16) -> hadavin_sdk.errors, hadavin_sdk.k1b, hadavin_sdk.k1b.causelist, hadavin_sdk.k1b.diagnosis, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.tools | test helpers: -
tests/test_k1b_redaction.py (def test_: 11) -> hadavin_sdk, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.redaction, hadavin_sdk.k1b.report, hadavin_sdk.k1b.score | test helpers: tests.k1b_support, tests.test_k1b_replay
tests/test_k1b_redaction_layers.py (def test_: 11) -> hadavin_sdk, hadavin_sdk.guard.runmap, hadavin_sdk.k1b.bundle, hadavin_sdk.k1b.redaction, hadavin_sdk.tools | test helpers: -
tests/test_k1b_replay.py (def test_: 44) -> hadavin_sdk.audit, hadavin_sdk.backends.factory, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.guard.injection, hadavin_sdk.hashing, hadavin_sdk.k1b, hadavin_sdk.k1b.audit_sink, hadavin_sdk.k1b.loop, hadavin_sdk.k1b.replay, hadavin_sdk.k1b.tools, hadavin_sdk.llm.protocol, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.k1b_support
tests/test_k1b_score.py (def test_: 20) -> hadavin_sdk.errors, hadavin_sdk.k1b.report, hadavin_sdk.k1b.score | test helpers: tests.k1b_support, tests.reference_scorer
tests/test_k1b_stats.py (def test_: 6) -> hadavin_sdk, hadavin_sdk.errors, hadavin_sdk.evals, hadavin_sdk.hashing, hadavin_sdk.stats | test helpers: -
tests/test_k2_migrations.py (def test_: 37) -> hadavin_sdk, hadavin_sdk.cli, hadavin_sdk.errors, hadavin_sdk.models, hadavin_sdk.store, hadavin_sdk.store.migrate | test helpers: tests.contracts.kinds.store_postgres
tests/test_k3_leftovers.py (def test_: 6) -> hadavin_sdk, hadavin_sdk.app, hadavin_sdk.approvals.channel, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.conftest, tests.test_k3_pilot
tests/test_k3_pilot.py (def test_: 40) -> hadavin_sdk, hadavin_sdk.actions.contract, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.approvals.channel, hadavin_sdk.audit, hadavin_sdk.audit.signer, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.limits, hadavin_sdk.llm, hadavin_sdk.llm.common, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.replay_records, hadavin_sdk.runtime, hadavin_sdk.runtime.agent_loop, hadavin_sdk.store | test helpers: tests.conftest
tests/test_k3_pilot_env.py (def test_: 10) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals.channel, hadavin_sdk.audit, hadavin_sdk.audit.signer, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.conftest, tests.contracts.kinds.store_postgres, tests.test_k3_pilot
tests/test_k3_review_fixes.py (def test_: 5) -> hadavin_sdk, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.replay_records | test helpers: tests.conftest, tests.test_k3_pilot
tests/test_k5_classes.py (def test_: 32) -> hadavin_sdk, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.sources, hadavin_sdk.sources.kubernetes, hadavin_sdk.tools | test helpers: tests.contracts.sources, tests.fixtures, tests.fixtures.k5_tools, tests.k5_support
tests/test_k5_fixes1.py (def test_: 12) -> hadavin_sdk, hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.http, hadavin_sdk.guard.runmap, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop, hadavin_sdk.store, hadavin_sdk.store.migrate, hadavin_sdk.tools | test helpers: tests.conftest, tests.k5_support, tests.test_k5_review
tests/test_k5_fixes2.py (def test_: 19) -> hadavin_sdk, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.guard.http, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.store, hadavin_sdk.store.migrate, hadavin_sdk.tools | test helpers: tests.contracts.kinds.store_postgres, tests.k5_support
tests/test_k5_fixes3.py (def test_: 9) -> hadavin_sdk, hadavin_sdk.approvals, hadavin_sdk.approvals.channel, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.tools | test helpers: tests.k5_support
tests/test_k5_fixes4.py (def test_: 7) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.tools | test helpers: -
tests/test_k5_fixes5.py (def test_: 5) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.tools | test helpers: -
tests/test_k5_fixes6.py (def test_: 9) -> hadavin_sdk, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.tools | test helpers: -
tests/test_k5_fixes7.py (def test_: 4) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.tools | test helpers: -
tests/test_k5_fixes8.py (def test_: 5) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.tools | test helpers: -
tests/test_k5_fixes9.py (def test_: 26) -> hadavin_sdk, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.tools | test helpers: tests.k5_support
tests/test_k5_layers.py (def test_: 18) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.scrub_settings, hadavin_sdk.tools | test helpers: -
tests/test_k5_perf.py (def test_: 4) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.runmap | test helpers: -
tests/test_k5_postgres.py (def test_: 1) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.audit, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.limits, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence | test helpers: tests.conftest, tests.contracts.kinds.store_postgres, tests.fixtures, tests.fixtures.k5_tools, tests.k5_support
tests/test_k5_producers.py (def test_: 5) -> hadavin_sdk, hadavin_sdk.guard.producers | test helpers: -
tests/test_k5_review.py (def test_: 33) -> hadavin_sdk, hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.tick, hadavin_sdk.store, hadavin_sdk.store.protocol, hadavin_sdk.tools | test helpers: tests.conftest, tests.fixtures, tests.fixtures.k5_tools, tests.k5_support
tests/test_k5_round10.py (def test_: 28) -> hadavin_sdk, hadavin_sdk.actions.contract, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.guard.egress, hadavin_sdk.guard.http, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.sources, hadavin_sdk.tools | test helpers: tests.fixtures, tests.fixtures.k5_tools, tests.k5_support, tests.test_k3_pilot_env
tests/test_k5_round10_postgres.py (def test_: 8) -> hadavin_sdk.config, hadavin_sdk.store.migrate | test helpers: tests.contracts.kinds.store_postgres
tests/test_k5_round11.py (def test_: 22) -> hadavin_sdk, hadavin_sdk.approvals, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.slack_channel, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.store | test helpers: tests.fixtures, tests.fixtures.k5_tools, tests.k5_support
tests/test_k5_round12_fuzz.py (def test_: 5) -> hadavin_sdk, hadavin_sdk.approvals, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack_channel, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.tools | test helpers: -
tests/test_k5_round5.py (def test_: 51) -> hadavin_sdk, hadavin_sdk.actions, hadavin_sdk.actions.secrets, hadavin_sdk.actions.secrets_vault, hadavin_sdk.app, hadavin_sdk.audit, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.guard.http, hadavin_sdk.guard.runmap, hadavin_sdk.limits, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.tick, hadavin_sdk.sources, hadavin_sdk.sources.kubernetes, hadavin_sdk.store, hadavin_sdk.store.protocol, hadavin_sdk.tools | test helpers: tests.conftest, tests.contracts.sources, tests.fixtures, tests.fixtures.k5_tools, tests.k5_support, tests.test_k3_pilot_env, tests.test_k5_tools, tests.tls_support
tests/test_k5_round6.py (def test_: 12) -> hadavin_sdk, hadavin_sdk.actions.contract, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.sources.kubernetes, hadavin_sdk.tools | test helpers: tests.k5_support, tests.test_k5_tools
tests/test_k5_round6_contracts.py (def test_: 4) -> hadavin_sdk.backends, hadavin_sdk.backends.factory, hadavin_sdk.sources, hadavin_sdk.sources.kinds, hadavin_sdk.store.memory, hadavin_sdk.store.protocol | test helpers: -
tests/test_k5_round7.py (def test_: 7) -> hadavin_sdk, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.guard.runmap, hadavin_sdk.k1b.redaction, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.tools | test helpers: tests.test_k1b_redaction_layers
tests/test_k5_round8.py (def test_: 12) -> hadavin_sdk, hadavin_sdk.approvals, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack_channel, hadavin_sdk.defaults, hadavin_sdk.guard, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.guard.runmap, hadavin_sdk.k1b.redaction, hadavin_sdk.models, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.tools | test helpers: tests.test_k1b_redaction_layers
tests/test_k5_round8_postgres.py (def test_: 1) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.tick | test helpers: tests.conftest, tests.contracts.kinds.store_postgres, tests.test_k3_pilot_env
tests/test_k5_round9.py (def test_: 17) -> hadavin_sdk, hadavin_sdk.approvals, hadavin_sdk.approvals.channel, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack_channel, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.extract, hadavin_sdk.guard, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.guard.producers, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.tick, hadavin_sdk.tools | test helpers: tests.fixtures, tests.fixtures.k5_tools, tests.k1b_support, tests.k5_support, tests.test_k1b_redaction_layers, tests.test_k1b_replay
tests/test_k5_round9b.py (def test_: 23) -> hadavin_sdk, hadavin_sdk.app, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.guard.http, hadavin_sdk.guard.runmap, hadavin_sdk.models, hadavin_sdk.runtime, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.tick, hadavin_sdk.sources, hadavin_sdk.sources.kubernetes, hadavin_sdk.tools | test helpers: tests.fixtures, tests.fixtures.k5_tools, tests.k5_support, tests.test_k3_pilot_env, tests.test_k5_tools
tests/test_k5_tools.py (def test_: 77) -> hadavin_sdk, hadavin_sdk.actions.contract, hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals.cards, hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.guard.runmap, hadavin_sdk.limits, hadavin_sdk.llm, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.agent_loop, hadavin_sdk.runtime.evidence, hadavin_sdk.runtime.tick, hadavin_sdk.sources, hadavin_sdk.store, hadavin_sdk.store.migrate, hadavin_sdk.store.protocol, hadavin_sdk.tools | test helpers: tests.conftest, tests.contracts.sources, tests.fixtures, tests.fixtures.http_fake, tests.fixtures.k5_tools, tests.k5_support, tests.test_k3_pilot_env
tests/test_lockin_guard.py (def test_: 56) -> hadavin_sdk.backends.table | test helpers: tests.conftest
tests/test_migrate_regex_linear.py (def test_: 3) -> hadavin_sdk.store, hadavin_sdk.store.migrate | test helpers: -
tests/test_no_hardcoded_values.py (def test_: 6) -> - | test helpers: -
tests/test_no_reference_material.py (def test_: 3) -> - | test helpers: -
tests/test_p1a_fixes.py (def test_: 9) -> hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets, hadavin_sdk.config, hadavin_sdk.guard.injection, hadavin_sdk.llm.protocol, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | test helpers: tests.test_executor, tests.test_s5_runtime
tests/test_p1b_backends.py (def test_: 20) -> hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.registry | test helpers: tests.conftest
tests/test_p2_postgres.py (def test_: 15) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.store.migrate, hadavin_sdk.store.protocol | test helpers: tests.contracts.kinds.store_postgres
tests/test_p3b_neutral_audit.py (def test_: 33) -> hadavin_sdk.actions.secrets, hadavin_sdk.audit, hadavin_sdk.audit.anchor_azure, hadavin_sdk.audit.anchor_gcs, hadavin_sdk.audit.anchors, hadavin_sdk.audit.chain, hadavin_sdk.audit.signer, hadavin_sdk.audit.signer_aws, hadavin_sdk.audit.signer_azure, hadavin_sdk.audit.signer_gcp, hadavin_sdk.audit.signer_vault, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.models, hadavin_sdk.store, hadavin_sdk.store.migrate, hadavin_sdk.store.postgres | test helpers: tests.conftest, tests.contracts.http_fake, tests.contracts.kinds.audit_neutral, tests.contracts.kinds.secrets_neutral
tests/test_p4_secrets.py (def test_: 8) -> hadavin_sdk.actions.secrets_aws, hadavin_sdk.actions.secrets_env, hadavin_sdk.backends.factory, hadavin_sdk.backends.platform_secrets, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.errors | test helpers: tests.conftest, tests.contracts.aws_stub
tests/test_p4b_secrets.py (def test_: 22) -> hadavin_sdk.actions.secrets_file, hadavin_sdk.actions.secrets_gcp, hadavin_sdk.actions.secrets_vault, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.errors | test helpers: tests.contracts.aws_stub, tests.contracts.http_fake, tests.contracts.kinds.secrets_neutral, tests.contracts.vault_fake, tests.test_repo_rules
tests/test_p5_llm.py (def test_: 19) -> hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.llm, hadavin_sdk.llm.common, hadavin_sdk.llm.gemini, hadavin_sdk.llm.retry, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.contracts.kinds.builtin, tests.contracts.kinds.llm_wire, tests.contracts.test_llm, tests.test_s5_runtime
tests/test_p5p6_followups.py (def test_: 28) -> hadavin_sdk.actions.secrets, hadavin_sdk.approvals.gate, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.guard.redact, hadavin_sdk.llm, hadavin_sdk.llm.anthropic, hadavin_sdk.llm.bedrock, hadavin_sdk.llm.common, hadavin_sdk.llm.retry, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | test helpers: tests.conftest, tests.contracts.kinds.builtin, tests.contracts.kinds.detectors, tests.contracts.kinds.llm_wire, tests.test_s5_runtime
tests/test_p6_detectors.py (def test_: 25) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.backends.factory, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.guard.bedrock_guardrail, hadavin_sdk.guard.injection, hadavin_sdk.guard.judge, hadavin_sdk.llm, hadavin_sdk.llm.common, hadavin_sdk.models, hadavin_sdk.registry | test helpers: tests.conftest, tests.contracts.kinds.detectors, tests.contracts.kinds.llm_wire, tests.contracts.test_llm, tests.fixtures.http_fake, tests.test_s5_runtime
tests/test_p7_store.py (def test_: 11) -> hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.store.migrate, hadavin_sdk.store.postgres | test helpers: tests.contracts.kinds.store_postgres
tests/test_p7_tick.py (def test_: 39) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals, hadavin_sdk.approvals.hmac_v0, hadavin_sdk.approvals.receiver, hadavin_sdk.approvals.slack_channel, hadavin_sdk.audit, hadavin_sdk.audit.chain, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.identity, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime, hadavin_sdk.runtime.tick, hadavin_sdk.store.protocol | test helpers: tests.conftest, tests.fixtures.fake_slack, tests.test_cuj
tests/test_repo_rules.py (def test_: 23) -> - | test helpers: -
tests/test_review_fixes.py (def test_: 18) -> hadavin_sdk.actions.contract, hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets, hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | test helpers: tests.test_executor, tests.test_s5_runtime, tests.test_s6_approvals
tests/test_review_pr3_round2.py (def test_: 29) -> hadavin_sdk, hadavin_sdk.actions.executor, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.approvals, hadavin_sdk.approvals.requests, hadavin_sdk.approvals.slack, hadavin_sdk.audit, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.evals, hadavin_sdk.guard, hadavin_sdk.identity, hadavin_sdk.llm, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop | test helpers: tests.test_cuj, tests.test_executor, tests.test_s5_runtime
tests/test_s1_foundation.py (def test_: 17) -> hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.runtime.runs, hadavin_sdk.store, hadavin_sdk.store.protocol | test helpers: -
tests/test_s2_audit.py (def test_: 5) -> hadavin_sdk.audit, hadavin_sdk.models | test helpers: -
tests/test_s3_gate.py (def test_: 19) -> hadavin_sdk.actions.authorizer, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry | test helpers: -
tests/test_s4_llm_guard.py (def test_: 21) -> hadavin_sdk.approvals.channel, hadavin_sdk.config, hadavin_sdk.extract, hadavin_sdk.guard, hadavin_sdk.guard.redact, hadavin_sdk.llm, hadavin_sdk.models | test helpers: tests.fixtures.schemas
tests/test_s5_runtime.py (def test_: 12) -> hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.guard, hadavin_sdk.limits, hadavin_sdk.llm, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.runtime.agent_loop, hadavin_sdk.store | test helpers: tests.conftest
tests/test_s6_approvals.py (def test_: 12) -> hadavin_sdk.approvals, hadavin_sdk.approvals.slack, hadavin_sdk.audit, hadavin_sdk.config, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.store | test helpers: -
tests/tls_support.py (def test_: 0) -> - | test helpers: -
tests/warden_port/__init__.py (def test_: 0) -> - | test helpers: -
tests/warden_port/fakes.py (def test_: 0) -> - | test helpers: -
tests/warden_port/privacy_corpus.py (def test_: 0) -> - | test helpers: tests.warden_port.fakes
tests/warden_port/test_audit_chain.py (def test_: 35) -> hadavin_sdk, hadavin_sdk.actions.secrets, hadavin_sdk.app, hadavin_sdk.audit, hadavin_sdk.audit.anchor_s3, hadavin_sdk.audit.anchors, hadavin_sdk.audit.chain, hadavin_sdk.audit.signer, hadavin_sdk.audit.signer_aws, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.cli, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.models, hadavin_sdk.registry, hadavin_sdk.store.migrate | test helpers: tests.conftest, tests.contracts.kinds.audit_chain, tests.contracts.kinds.store_postgres
tests/warden_port/test_bedrock_provider_r16.py (def test_: 7) -> hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.errors, hadavin_sdk.llm, hadavin_sdk.llm.bedrock, hadavin_sdk.llm.common | test helpers: tests.contracts.kinds.builtin, tests.contracts.kinds.llm_wire, tests.contracts.test_llm
tests/warden_port/test_gate.py (def test_: 4) -> hadavin_sdk.approvals.gate | test helpers: -
tests/warden_port/test_gate_render.py (def test_: 1) -> hadavin_sdk.approvals.gate | test helpers: -
tests/warden_port/test_gate_review2.py (def test_: 4) -> hadavin_sdk.approvals, hadavin_sdk.approvals.gate | test helpers: -
tests/warden_port/test_gate_review3.py (def test_: 2) -> hadavin_sdk.approvals, hadavin_sdk.approvals.gate | test helpers: -
tests/warden_port/test_providers.py (def test_: 15) -> hadavin_sdk.actions.secrets, hadavin_sdk.backends.factory, hadavin_sdk.backends.table, hadavin_sdk.config, hadavin_sdk.errors, hadavin_sdk.llm, hadavin_sdk.llm.common | test helpers: tests.contracts.kinds.builtin, tests.contracts.kinds.llm_wire, tests.contracts.test_llm
tests/warden_port/test_redaction.py (def test_: 35) -> hadavin_sdk.guard.redact | test helpers: tests.warden_port.fakes
tests/warden_port/test_redaction_bank.py (def test_: 16) -> hadavin_sdk.guard.redact | test helpers: -
tests/warden_port/test_redaction_classes.py (def test_: 3) -> hadavin_sdk.guard.redact | test helpers: tests.warden_port.privacy_corpus
tests/warden_port/test_redaction_review.py (def test_: 4) -> hadavin_sdk.guard.redact | test helpers: tests.warden_port.fakes
tests/warden_port/test_redaction_review2.py (def test_: 5) -> hadavin_sdk.guard.redact | test helpers: -
tests/warden_port/test_redaction_review9.py (def test_: 3) -> hadavin_sdk.guard.redact | test helpers: -

### 4b src modules (non-package) imported by NO test file

count: 6

hadavin_sdk.actions.secrets_cache (src/hadavin_sdk/actions/secrets_cache.py)
hadavin_sdk.audit.local_dir (src/hadavin_sdk/audit/local_dir.py)
hadavin_sdk.backends.builtin (src/hadavin_sdk/backends/builtin.py)
hadavin_sdk.deferred (src/hadavin_sdk/deferred.py)
hadavin_sdk.runtime.plan (src/hadavin_sdk/runtime/plan.py)
hadavin_sdk.store.auth_aws (src/hadavin_sdk/store/auth_aws.py)

### 4c Test imports whose names do not resolve in src/demos (candidates: tests for removed code)

count: 1

tests/test_k5_round6_contracts.py:47 imports name make from hadavin_sdk.backends: not defined at module level there (candidate: removed or renamed code)

### 5a Per-file counts of state/log/retry pattern hits (code lines only; comments and docstrings counted separately in 5b)

count: 167

.github/workflows/ci.yml | retry=2, timeout=4
demos/ask-your-data/askdata/cli.py | DSN=4
demos/ask-your-data/askdata/config.py | max_attempts=2
demos/ask-your-data/askdata/derive_allowlist.py | jsonl=2, write_text=1
demos/ask-your-data/askdata/evalcli.py | jsonl=3, write_text=1
demos/ask-your-data/askdata/evalrun.py | jsonl=1, open-write=2, retry=1, write_text=3
demos/ask-your-data/askdata/evalset.py | open-write=1
demos/ask-your-data/askdata/fixtures.py | write_text=1
demos/ask-your-data/askdata/ledger.py | open-write=1
demos/ask-your-data/askdata/meter.py | open-write=2, sleep=1, write_text=1
demos/ask-your-data/askdata/opscli.py | write_text=1
demos/ask-your-data/askdata/pgsource.py | DSN=2, psycopg=15, sleep=1, timeout=6
demos/ask-your-data/askdata/pipeline.py | backoff=2, max_attempts=2, retry=5, sleep=1, timeout=2
demos/ask-your-data/askdata/policy.py | retry=6, timeout=4
demos/ask-your-data/askdata/validate.py | getLogger=1
demos/ask-your-data/data/goldcheck.py | jsonl=5, write_text=1
demos/ask-your-data/db/build_verify.py | write_text=1
demos/ask-your-data/db/lumen.py | write_text=1
src/hadavin_sdk/actions/executor.py | timeout=6
src/hadavin_sdk/actions/secrets_azure.py | retry=1, timeout=2
src/hadavin_sdk/actions/secrets_gcp.py | retry=1, timeout=1
src/hadavin_sdk/actions/secrets_vault.py | timeout=4
src/hadavin_sdk/app.py | getLogger=1, timeout=4
src/hadavin_sdk/approvals/receiver.py | getLogger=1
src/hadavin_sdk/approvals/requests.py | getLogger=1, timeout=4
src/hadavin_sdk/approvals/slack_channel.py | timeout=4
src/hadavin_sdk/audit/anchor_azure.py | retry=1, timeout=2
src/hadavin_sdk/audit/anchor_gcs.py | retry=1, timeout=1
src/hadavin_sdk/audit/anchor_s3.py | max_attempts=1, retry=1, timeout=1
src/hadavin_sdk/audit/chain.py | getLogger=1, retry=2, sqlite3=2
src/hadavin_sdk/audit/local_dir.py | jsonl=1, open-write=1, retry=2, write_text=1
src/hadavin_sdk/audit/signer_aws.py | max_attempts=1, retry=1, timeout=1
src/hadavin_sdk/audit/signer_azure.py | retry=1, timeout=1
src/hadavin_sdk/audit/signer_gcp.py | retry=1, timeout=1
src/hadavin_sdk/backends/table.py | max_attempts=1, timeout=4
src/hadavin_sdk/cli.py | DSN=4
src/hadavin_sdk/config.py | timeout=4
src/hadavin_sdk/defaults.py | timeout=1
src/hadavin_sdk/evals.py | jsonl=4, open-write=1
src/hadavin_sdk/guard/bedrock_guardrail.py | max_attempts=1, retry=1, timeout=2
src/hadavin_sdk/guard/http.py | timeout=7
src/hadavin_sdk/guard/injection.py | getLogger=1
src/hadavin_sdk/k1b/atomic.py | open-write=1
src/hadavin_sdk/k1b/bundle.py | jsonl=2
src/hadavin_sdk/k1b/loop.py | getLogger=1, timeout=9
src/hadavin_sdk/k1b/replay.py | timeout=3
src/hadavin_sdk/k1b/report.py | timeout=6
src/hadavin_sdk/k1b/score.py | timeout=9
src/hadavin_sdk/llm/anthropic.py | max_attempts=3, retry=4, timeout=2
src/hadavin_sdk/llm/bedrock.py | max_attempts=4, retry=7, timeout=5
src/hadavin_sdk/llm/common.py | max_attempts=3, retry=5, timeout=2
src/hadavin_sdk/llm/gemini.py | max_attempts=3, retry=1, timeout=4
src/hadavin_sdk/llm/openai_compat.py | max_attempts=3, retry=1, timeout=4
src/hadavin_sdk/llm/retry.py | max_attempts=5, retry=11, sleep=1, timeout=1
src/hadavin_sdk/models.py | retry=1, timeout=1
src/hadavin_sdk/registry.py | jsonl=2, timeout=2
src/hadavin_sdk/replay_records.py | getLogger=1, jsonl=1
src/hadavin_sdk/runtime/agent_loop.py | getLogger=1, jsonl=3
src/hadavin_sdk/runtime/tick.py | getLogger=1, max_attempts=1, psycopg=1, timeout=1
src/hadavin_sdk/store/migrate.py | DSN=2, psycopg=1
src/hadavin_sdk/store/postgres.py | DSN=10, getLogger=1, psycopg=16, timeout=1
src/hadavin_sdk/store/protocol.py | psycopg=1
src/hadavin_sdk/tools.py | timeout=8
tests/conftest.py | jsonl=1, write_text=2
tests/contracts/kinds/audit_chain.py | DSN=3
tests/contracts/kinds/builtin.py | write_text=1
tests/contracts/kinds/channel_slack.py | timeout=1
tests/contracts/kinds/detectors.py | retry=1
tests/contracts/kinds/llm_wire.py | retry=1, timeout=1
tests/contracts/kinds/secrets_neutral.py | write_text=1
tests/contracts/kinds/store_postgres.py | DSN=10, psycopg=6
tests/contracts/test_anchor.py | retry=1
tests/contracts/test_capabilities.py | timeout=1
tests/contracts/test_llm.py | jsonl=1, max_attempts=2
tests/contracts/test_store.py | sleep=1, timeout=1
tests/demo_askdata/conftest.py | DSN=11, psycopg=7, timeout=1
tests/demo_askdata/corpus.py | timeout=1
tests/demo_askdata/gold_runner.py | psycopg=4
tests/demo_askdata/kit.py | jsonl=1, sqlite3=5
tests/demo_askdata/test_allowlist.py | jsonl=1
tests/demo_askdata/test_audit.py | jsonl=1, write_bytes=1, write_text=3
tests/demo_askdata/test_eval_harness.py | jsonl=15, open-write=1, write_text=9
tests/demo_askdata/test_gold_data.py | jsonl=3, write_text=2
tests/demo_askdata/test_gold_exec.py | jsonl=2, psycopg=5
tests/demo_askdata/test_htmlexport.py | write_text=4
tests/demo_askdata/test_imports.py | psycopg=3
tests/demo_askdata/test_ledger.py | jsonl=5, open-write=1, write_bytes=4
tests/demo_askdata/test_llm_io.py | retry=8, timeout=3
tests/demo_askdata/test_meter.py | open-write=1, timeout=1, write_text=3
tests/demo_askdata/test_pgsource_layers.py | DSN=14, psycopg=10, timeout=7
tests/demo_askdata/test_pipeline.py | retry=4, timeout=2
tests/demo_askdata/test_roles.py | psycopg=4
tests/demo_askdata/test_seed.py | DSN=2, psycopg=5
tests/demo_askdata/test_validate_harm.py | DSN=10, psycopg=13, timeout=3
tests/demo_askdata/test_verify_readonly.py | DSN=3, psycopg=1
tests/fixtures/config/chains.yaml | timeout=3
tests/fixtures/fake_system.py | sleep=1, timeout=3
tests/fixtures/k5_tools.py | sleep=1
tests/fixtures/record.py | jsonl=1, write_text=2
tests/k1b_support.py | jsonl=7, open-write=1, timeout=1, write_text=14
tests/k5_support.py | write_text=4
tests/test_cuj.py | jsonl=2, psycopg=1, timeout=4, write_text=4
tests/test_executor.py | timeout=6
tests/test_g4_parity.py | jsonl=2
tests/test_k1a_pass_k.py | jsonl=3, write_bytes=1, write_text=3
tests/test_k1b_bundle.py | jsonl=40, open-write=1, write_bytes=1, write_text=7
tests/test_k1b_causelist_containment.py | write_text=1
tests/test_k1b_cli.py | write_text=4
tests/test_k1b_diagnosis.py | jsonl=1, write_bytes=2, write_text=5
tests/test_k1b_redaction.py | jsonl=10
tests/test_k1b_redaction_layers.py | jsonl=1
tests/test_k1b_replay.py | jsonl=4, timeout=13, write_text=6
tests/test_k1b_score.py | jsonl=3, timeout=10, write_bytes=1, write_text=15
tests/test_k1b_stats.py | write_bytes=5
tests/test_k2_migrations.py | DSN=33, psycopg=30, write_text=2
tests/test_k3_leftovers.py | jsonl=1, write_text=1
tests/test_k3_pilot.py | jsonl=6, write_bytes=1, write_text=7
tests/test_k3_pilot_env.py | DSN=7, timeout=1, write_text=6
tests/test_k3_review_fixes.py | write_text=3
tests/test_k5_classes.py | sleep=1, timeout=2
tests/test_k5_fixes1.py | sleep=1, timeout=2
tests/test_k5_fixes2.py | DSN=4, psycopg=4, write_bytes=1, write_text=1
tests/test_k5_fixes3.py | write_text=1
tests/test_k5_fixes9.py | timeout=1
tests/test_k5_postgres.py | DSN=3
tests/test_k5_review.py | sleep=1, timeout=5
tests/test_k5_round10.py | sleep=1, timeout=4, write_text=3
tests/test_k5_round10_postgres.py | DSN=18, psycopg=9
tests/test_k5_round5.py | jsonl=1, retry=1, timeout=9, write_text=6
tests/test_k5_round6.py | write_text=2
tests/test_k5_round7.py | jsonl=1
tests/test_k5_round8_postgres.py | DSN=3, write_text=1
tests/test_k5_round9.py | jsonl=1, timeout=1, write_text=2
tests/test_k5_round9b.py | timeout=3, write_text=1
tests/test_k5_tools.py | timeout=4, write_text=2
tests/test_lockin_guard.py | psycopg=3, write_text=3
tests/test_migrate_regex_linear.py | psycopg=1
tests/test_no_hardcoded_values.py | timeout=1, write_text=1
tests/test_p1a_fixes.py | retry=1, sleep=1, timeout=2, write_text=1
tests/test_p1b_backends.py | write_text=1
tests/test_p2_postgres.py | DSN=11, psycopg=9, write_text=2
tests/test_p3b_neutral_audit.py | DSN=4, psycopg=1, write_text=2
tests/test_p4_secrets.py | sleep=1, write_text=1
tests/test_p4b_secrets.py | retry=5, timeout=3, write_text=3
tests/test_p5_llm.py | backoff=1, max_attempts=5, retry=7, timeout=1, write_text=1
tests/test_p5p6_followups.py | retry=12, write_text=3
tests/test_p6_detectors.py | jsonl=5, write_text=5
tests/test_p7_store.py | DSN=14, psycopg=6
tests/test_p7_tick.py | DSN=4, psycopg=11, timeout=4, write_text=3
tests/test_repo_rules.py | write_text=12
tests/test_review_fixes.py | timeout=1, write_bytes=1, write_text=3
tests/test_review_pr3_round2.py | jsonl=3, timeout=2, write_bytes=2, write_text=5
tests/test_s1_foundation.py | write_text=1
tests/test_s2_audit.py | write_bytes=1
tests/test_s3_gate.py | timeout=1, write_text=1
tests/test_s4_llm_guard.py | retry=1
tests/test_s5_runtime.py | write_text=2
tests/test_s6_approvals.py | timeout=1
tests/tls_support.py | write_bytes=2
tests/warden_port/fakes.py | DSN=1
tests/warden_port/privacy_corpus.py | timeout=1
tests/warden_port/test_audit_chain.py | DSN=12, max_attempts=1, psycopg=10, retry=2, sqlite3=2, timeout=5, write_text=3
tests/warden_port/test_bedrock_provider_r16.py | max_attempts=1, retry=2, timeout=2
tests/warden_port/test_providers.py | retry=1
tests/warden_port/test_redaction.py | DSN=3, retry=4
tests/warden_port/test_redaction_review.py | retry=3
tests/warden_port/test_redaction_review2.py | retry=1

### 5b Every pattern hit: file:line pattern [line kind] [enclosing def] identifier (lines kept in full file)

count: 1288; showing first 200; full list: parts/evidence-1-full-5b.txt

.github/workflows/ci.yml:35 timeout [code] [-] timeout
.github/workflows/ci.yml:48 timeout [code] [-] timeout
.github/workflows/ci.yml:49 retry [code] [-] retries
.github/workflows/ci.yml:63 timeout [code] [-] timeout
.github/workflows/ci.yml:64 retry [code] [-] retries
.github/workflows/ci.yml:99 timeout [code] [-] timeout
demos/ask-your-data/askdata/cli.py:5 DSN [doc] [<module>] DSN
demos/ask-your-data/askdata/cli.py:45 DSN [code] [_source] dsn
demos/ask-your-data/askdata/cli.py:46 DSN [code] [_source] dsn
demos/ask-your-data/askdata/cli.py:51 DSN [code] [_source] dsn
demos/ask-your-data/askdata/cli.py:172 DSN [comment] [cmd_setup] DSN
demos/ask-your-data/askdata/cli.py:244 DSN [code] [main] DSN
demos/ask-your-data/askdata/config.py:48 max_attempts [code] [Limits] max_attempts
demos/ask-your-data/askdata/config.py:75 max_attempts [code] [AskdataConfig.settings] max_attempts
demos/ask-your-data/askdata/derive_allowlist.py:29 jsonl [code] [gold_statements] gold.jsonl
demos/ask-your-data/askdata/derive_allowlist.py:34 jsonl [code] [gold_statements] exemplars.jsonl
demos/ask-your-data/askdata/derive_allowlist.py:64 write_text [code] [main] COMMITTED.write_text(text
demos/ask-your-data/askdata/evalcli.py:45 jsonl [code] [<module>] gold.dev.jsonl
demos/ask-your-data/askdata/evalcli.py:46 jsonl [code] [<module>] gold.test.jsonl
demos/ask-your-data/askdata/evalcli.py:81 jsonl [code] [build_harness] statements.jsonl
demos/ask-your-data/askdata/evalcli.py:210 write_text [code] [cmd_report] dest.write_text(clean
demos/ask-your-data/askdata/evalrun.py:79 open-write [code] [RecordingExecutor.run] open(self.path, "a"
demos/ask-your-data/askdata/evalrun.py:421 retry [code] [Harness.report] retry_rate
demos/ask-your-data/askdata/evalrun.py:517 open-write [code] [write_run] open(out_dir / "results.jsonl", "w"
demos/ask-your-data/askdata/evalrun.py:517 jsonl [code] [write_run] results.jsonl
demos/ask-your-data/askdata/evalrun.py:521 write_text [code] [write_run] .write_text(
demos/ask-your-data/askdata/evalrun.py:526 write_text [code] [write_run] .write_text(render_md
demos/ask-your-data/askdata/evalrun.py:527 write_text [code] [write_run] .write_text(
demos/ask-your-data/askdata/evalset.py:156 open-write [code] [write_lock] open(tmp, "w"
demos/ask-your-data/askdata/fixtures.py:5 retry [doc] [<module>] retry
demos/ask-your-data/askdata/fixtures.py:76 retry [doc] [write_script] retry
demos/ask-your-data/askdata/fixtures.py:85 write_text [code] [write_script] .write_text(
demos/ask-your-data/askdata/ledger.py:154 open-write [code] [QueryLedger.append] open(self.path, "ab"
demos/ask-your-data/askdata/llm_io.py:4 retry [doc] [<module>] retry
demos/ask-your-data/askdata/llm_io.py:6 retry [doc] [<module>] retry
demos/ask-your-data/askdata/meter.py:145 open-write [code] [Meter._write] open(tmp, "w"
demos/ask-your-data/askdata/meter.py:156 open-write [code] [Meter._locked] open(lock, "a+b"
demos/ask-your-data/askdata/meter.py:161 sleep [code] [Meter._locked] time.sleep(0.01
demos/ask-your-data/askdata/meter.py:264 write_text [code] [KillSwitch.on] self.path.write_text(
demos/ask-your-data/askdata/opscli.py:128 write_text [code] [cmd_export] dest.write_text(text
demos/ask-your-data/askdata/pgsource.py:1 psycopg [doc] [<module>] psycopg
demos/ask-your-data/askdata/pgsource.py:17 timeout [doc] [<module>] statement_timeout
demos/ask-your-data/askdata/pgsource.py:33 psycopg [code] [<module>] psycopg
demos/ask-your-data/askdata/pgsource.py:53 timeout [code] [Limits] statement_timeout_s
demos/ask-your-data/askdata/pgsource.py:85 psycopg [code] [_close] psycopg.Connection
demos/ask-your-data/askdata/pgsource.py:90 psycopg [code] [_close] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:96 psycopg [code] [_fail] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:101 DSN [code] [PgSource.__init__] dsn
demos/ask-your-data/askdata/pgsource.py:102 DSN [code] [PgSource.__init__] dsn
demos/ask-your-data/askdata/pgsource.py:105 psycopg [code] [PgSource._connect] psycopg.Connection
demos/ask-your-data/askdata/pgsource.py:108 timeout [code] [PgSource._connect] connect_timeout
demos/ask-your-data/askdata/pgsource.py:121 psycopg [code] [PgSource._connect] psycopg.connect
demos/ask-your-data/askdata/pgsource.py:122 psycopg [code] [PgSource._connect] psycopg.OperationalError
demos/ask-your-data/askdata/pgsource.py:125 sleep [code] [PgSource._connect] time.sleep(0.25
demos/ask-your-data/askdata/pgsource.py:127 psycopg [code] [PgSource._connect] psycopg.connect
demos/ask-your-data/askdata/pgsource.py:128 psycopg [code] [PgSource._connect] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:130 psycopg [code] [PgSource._connect] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:132 psycopg [code] [PgSource._connect] psycopg
demos/ask-your-data/askdata/pgsource.py:135 psycopg [code] [PgSource._guard] psycopg.Connection
demos/ask-your-data/askdata/pgsource.py:150 psycopg [code] [PgSource.verify_readonly] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:165 timeout [code] [PgSource.run] lim.statement_timeout_s
demos/ask-your-data/askdata/pgsource.py:167 timeout [code] [PgSource.run] lim.statement_timeout_s
demos/ask-your-data/askdata/pgsource.py:174 psycopg [code] [PgSource.run] psycopg.Error
demos/ask-your-data/askdata/pgsource.py:184 psycopg [code] [PgSource._fetch] psycopg.Connection
demos/ask-your-data/askdata/pgsource.py:200 timeout [code] [PgSource._fetch] timeout
demos/ask-your-data/askdata/pgsource.py:207 timeout [code] [PgSource._fetch] timeout
demos/ask-your-data/askdata/pipeline.py:3 retry [doc] [<module>] retry
demos/ask-your-data/askdata/pipeline.py:4 retry [doc] [<module>] retry
demos/ask-your-data/askdata/pipeline.py:46 max_attempts [code] [Settings] max_attempts
demos/ask-your-data/askdata/pipeline.py:54 backoff [code] [Settings] transient_backoff_s
demos/ask-your-data/askdata/pipeline.py:140 max_attempts [code] [Pipeline._generate_and_execute] self.s.max_attempts
demos/ask-your-data/askdata/pipeline.py:161 timeout [code] [Pipeline._generate_and_execute] TimeoutError
demos/ask-your-data/askdata/pipeline.py:163 timeout [code] [Pipeline._generate_and_execute] TimeoutError
demos/ask-your-data/askdata/pipeline.py:226 retry [code] [Pipeline._generate_and_execute] retry_hint
demos/ask-your-data/askdata/pipeline.py:227 retry [code] [Pipeline._generate_and_execute] retry
demos/ask-your-data/askdata/pipeline.py:229 retry [code] [Pipeline._generate_and_execute] retry_hint
demos/ask-your-data/askdata/pipeline.py:245 retry [doc] [Pipeline._execute] retry
demos/ask-your-data/askdata/pipeline.py:291 backoff [code] [Pipeline._execute] self.s.transient_backoff_s
demos/ask-your-data/askdata/pipeline.py:291 sleep [code] [Pipeline._execute] self.sleep(self.s.transient_backoff_s
demos/ask-your-data/askdata/pipeline.py:299 retry [code] [Pipeline._execute] retry_once
demos/ask-your-data/askdata/pipeline.py:304 retry [code] [Pipeline._execute] retry
demos/ask-your-data/askdata/policy.py:1 retry [doc] [<module>] retry
demos/ask-your-data/askdata/policy.py:16 timeout [code] [<module>] timeout
demos/ask-your-data/askdata/policy.py:43 timeout [code] [<module>] timeout
demos/ask-your-data/askdata/policy.py:61 timeout [code] [<module>] timeout
demos/ask-your-data/askdata/policy.py:78 retry [code] [<module>] retry
demos/ask-your-data/askdata/policy.py:99 retry [code] [<module>] retry_once
demos/ask-your-data/askdata/policy.py:99 timeout [code] [<module>] timeout
demos/ask-your-data/askdata/policy.py:100 retry [code] [<module>] retry
demos/ask-your-data/askdata/policy.py:101 retry [code] [<module>] retry
demos/ask-your-data/askdata/policy.py:102 retry [code] [<module>] retry
demos/ask-your-data/askdata/policy.py:104 retry [code] [<module>] retry_once
demos/ask-your-data/askdata/validate.py:43 getLogger [code] [<module>] logging.getLogger
demos/ask-your-data/data/goldcheck.py:9 jsonl [doc] [<module>] gold.jsonl
demos/ask-your-data/data/goldcheck.py:10 jsonl [doc] [<module>] adversarial.jsonl
demos/ask-your-data/data/goldcheck.py:11 jsonl [doc] [<module>] adversarial.dev.jsonl
demos/ask-your-data/data/goldcheck.py:12 jsonl [doc] [<module>] exemplars.jsonl
demos/ask-your-data/data/goldcheck.py:111 jsonl [code] [load_all] gold.jsonl
demos/ask-your-data/data/goldcheck.py:112 jsonl [code] [load_all] adversarial.jsonl
demos/ask-your-data/data/goldcheck.py:113 jsonl [code] [load_all] adversarial.dev.jsonl
demos/ask-your-data/data/goldcheck.py:114 jsonl [code] [load_all] exemplars.jsonl
demos/ask-your-data/data/goldcheck.py:132 jsonl [code] [compute_manifest] adversarial.jsonl
demos/ask-your-data/data/goldcheck.py:554 write_text [code] [main] .write_text(
demos/ask-your-data/db/build_verify.py:46 write_text [code] [main] OUT.write_text(text
demos/ask-your-data/db/lumen.py:737 write_text [code] [main] MANIFEST_FILE.write_text(text
src/hadavin_sdk/actions/executor.py:3 timeout [doc] [<module>] timeout
src/hadavin_sdk/actions/executor.py:4 retry [doc] [<module>] retrying
src/hadavin_sdk/actions/executor.py:49 timeout [code] [Executor.__init__] timeout_s
src/hadavin_sdk/actions/executor.py:51 timeout [code] [Executor.__init__] self.timeout_s
src/hadavin_sdk/actions/executor.py:80 timeout [code] [Executor._caller.call] timeout
src/hadavin_sdk/actions/executor.py:103 retry [doc] [Executor.execute] retries
src/hadavin_sdk/actions/executor.py:131 timeout [code] [Executor.execute] TimeoutError
src/hadavin_sdk/actions/executor.py:135 timeout [code] [Executor.execute] TimeoutError
src/hadavin_sdk/actions/executor.py:136 timeout [comment] [Executor.execute] timeout
src/hadavin_sdk/actions/executor.py:144 retry [comment] [Executor.execute] retry.
src/hadavin_sdk/actions/executor.py:153 retry [doc] [Executor._lookup] retry
src/hadavin_sdk/actions/executor.py:155 timeout [code] [Executor._lookup] timeout_no_lookup
src/hadavin_sdk/actions/secrets_azure.py:44 retry [comment] [build] retries.
src/hadavin_sdk/actions/secrets_azure.py:48 timeout [code] [build] connection_timeout
src/hadavin_sdk/actions/secrets_azure.py:49 timeout [code] [build] read_timeout
src/hadavin_sdk/actions/secrets_azure.py:50 retry [code] [build] retry_total
src/hadavin_sdk/actions/secrets_gcp.py:41 retry [comment] [GcpSecretManagerProvider._fetch] retry
src/hadavin_sdk/actions/secrets_gcp.py:42 retry [code] [GcpSecretManagerProvider._fetch] retry
src/hadavin_sdk/actions/secrets_gcp.py:42 timeout [code] [GcpSecretManagerProvider._fetch] timeout
src/hadavin_sdk/actions/secrets_vault.py:52 timeout [code] [VaultProvider.__init__] timeout_s
src/hadavin_sdk/actions/secrets_vault.py:61 timeout [code] [VaultProvider.__init__] self.timeout_s
src/hadavin_sdk/actions/secrets_vault.py:83 timeout [code] [VaultProvider.call] timeout
src/hadavin_sdk/actions/secrets_vault.py:163 timeout [doc] [connect] timeout
src/hadavin_sdk/actions/secrets_vault.py:192 timeout [code] [connect] timeout_s
src/hadavin_sdk/app.py:42 getLogger [code] [<module>] logging.getLogger
src/hadavin_sdk/app.py:74 timeout [code] [build] timeout_s
src/hadavin_sdk/app.py:87 DSN [comment] [build] DSN
src/hadavin_sdk/app.py:173 timeout [code] [build] timeout_s
src/hadavin_sdk/app.py:198 retry [comment] [build.request_approval] retrying.
src/hadavin_sdk/app.py:328 timeout [code] [_build_source.fetch] cfg.tool_timeout_s
src/hadavin_sdk/app.py:455 timeout [code] [_toolbox] timeout_s
src/hadavin_sdk/approvals/receiver.py:4 retry [doc] [<module>] retry
src/hadavin_sdk/approvals/receiver.py:19 getLogger [code] [<module>] logging.getLogger
src/hadavin_sdk/approvals/requests.py:1 timeout [doc] [<module>] timeout
src/hadavin_sdk/approvals/requests.py:26 getLogger [code] [<module>] logging.getLogger
src/hadavin_sdk/approvals/requests.py:27 timeout [code] [<module>] timeout
src/hadavin_sdk/approvals/requests.py:103 timeout [code] [Approvals.request] .timeout_s
src/hadavin_sdk/approvals/requests.py:138 timeout [code] [Approvals.resend_unsent] step.timeout_s
src/hadavin_sdk/approvals/requests.py:201 timeout [code] [Approvals.sweep] .timeout_s
src/hadavin_sdk/approvals/slack_channel.py:45 timeout [code] [SlackChannel.__init__] timeout_s
src/hadavin_sdk/approvals/slack_channel.py:48 timeout [code] [SlackChannel.__init__] self.timeout_s
src/hadavin_sdk/approvals/slack_channel.py:55 timeout [code] [SlackChannel._call] self.timeout_s
src/hadavin_sdk/approvals/slack_channel.py:215 timeout [code] [build] timeout_s
src/hadavin_sdk/audit/anchor_azure.py:76 timeout [code] [build] connection_timeout
src/hadavin_sdk/audit/anchor_azure.py:77 timeout [code] [build] read_timeout
src/hadavin_sdk/audit/anchor_azure.py:78 retry [code] [build] retry_total
src/hadavin_sdk/audit/anchor_gcs.py:23 retry [code] [<module>] retry
src/hadavin_sdk/audit/anchor_gcs.py:23 timeout [code] [<module>] timeout
src/hadavin_sdk/audit/anchor_s3.py:88 retry [code] [build] retries
src/hadavin_sdk/audit/anchor_s3.py:88 timeout [code] [build] connect_timeout
src/hadavin_sdk/audit/anchor_s3.py:88 max_attempts [code] [build] total_max_attempts
src/hadavin_sdk/audit/anchors.py:2 retry [doc] [<module>] retry
src/hadavin_sdk/audit/chain.py:31 sqlite3 [code] [<module>] sqlite3
src/hadavin_sdk/audit/chain.py:45 getLogger [code] [<module>] logging.getLogger
src/hadavin_sdk/audit/chain.py:103 sqlite3 [code] [_Db.memory] sqlite3.connect
src/hadavin_sdk/audit/chain.py:298 retry [doc] [ChainAudit.checkpoint] retries
src/hadavin_sdk/audit/chain.py:302 retry [code] [ChainAudit.checkpoint] self._retry_anchors
src/hadavin_sdk/audit/chain.py:338 retry [code] [ChainAudit._retry_anchors] _retry_anchors
src/hadavin_sdk/audit/local_dir.py:4 retry [doc] [<module>] retry
src/hadavin_sdk/audit/local_dir.py:6 jsonl [doc] [<module>] index.jsonl
src/hadavin_sdk/audit/local_dir.py:29 jsonl [code] [LocalDirSink.__init__] index.jsonl
src/hadavin_sdk/audit/local_dir.py:50 jsonl [comment] [LocalDirSink._indexed] index.jsonl
src/hadavin_sdk/audit/local_dir.py:71 open-write [code] [LocalDirSink._append_index] open(self.index, "a"
src/hadavin_sdk/audit/local_dir.py:120 write_text [code] [LocalDirSink.write_outcome] tmp.write_text(event.model_dump_json
src/hadavin_sdk/audit/local_dir.py:135 retry [code] [LocalDirSink.reconcile] retries
src/hadavin_sdk/audit/local_dir.py:152 retry [code] [LocalDirSink.reconcile] retries
src/hadavin_sdk/audit/signer_aws.py:53 retry [code] [build] retries
src/hadavin_sdk/audit/signer_aws.py:53 timeout [code] [build] connect_timeout
src/hadavin_sdk/audit/signer_aws.py:53 max_attempts [code] [build] total_max_attempts
src/hadavin_sdk/audit/signer_azure.py:25 retry [comment] [<module>] retries
src/hadavin_sdk/audit/signer_azure.py:26 retry [code] [<module>] retry_total
src/hadavin_sdk/audit/signer_azure.py:26 timeout [code] [<module>] connection_timeout
src/hadavin_sdk/audit/signer_gcp.py:29 retry [code] [<module>] retry
src/hadavin_sdk/audit/signer_gcp.py:29 timeout [code] [<module>] timeout
src/hadavin_sdk/backends/platform_secrets.py:1 DSN [doc] [<module>] DSN
src/hadavin_sdk/backends/table.py:37 timeout [code] [_LLMSettings] call_timeout_s
src/hadavin_sdk/backends/table.py:39 timeout [code] [_LLMSettings] timeout
src/hadavin_sdk/backends/table.py:40 max_attempts [code] [_LLMSettings] max_attempts
src/hadavin_sdk/backends/table.py:118 DSN [comment] [PostgresSettings] DSN
src/hadavin_sdk/backends/table.py:119 DSN [comment] [PostgresSettings] DSN.
src/hadavin_sdk/backends/table.py:125 DSN [comment] [PostgresSettings] DSN
src/hadavin_sdk/backends/table.py:265 timeout [code] [_VaultConnection] timeout_s
src/hadavin_sdk/backends/table.py:325 timeout [code] [SlackSettings] timeout_s
src/hadavin_sdk/backends/table.py:340 DSN [comment] [Entry] DSN
src/hadavin_sdk/cli.py:9 DSN [doc] [<module>] DSN
src/hadavin_sdk/cli.py:185 DSN [comment] [_main] DSN
src/hadavin_sdk/cli.py:322 DSN [code] [_migrate] dsn
src/hadavin_sdk/cli.py:323 DSN [code] [_migrate] dsn
src/hadavin_sdk/cli.py:324 DSN [code] [_migrate] DSN
src/hadavin_sdk/cli.py:331 DSN [code] [_migrate] dsn
src/hadavin_sdk/config.py:171 timeout [code] [K1bSettings] case_timeout_s
src/hadavin_sdk/config.py:330 timeout [comment] [Config] timeout
src/hadavin_sdk/config.py:333 timeout [code] [Config] tool_timeout_s
src/hadavin_sdk/config.py:344 timeout [code] [Config] executor_timeout_s
src/hadavin_sdk/config.py:345 timeout [code] [Config] defaults.EXECUTOR_TIMEOUT_S

### 6a Per-file counts of credential, egress and personal-data-word hits (names only, code lines only)

count: 191

.github/dependabot.yml | requests=1
.github/workflows/ci.yml | environ=2, secret=4, token=1
demos/ask-your-data/askdata/cli.py | email=1, environ=5
demos/ask-your-data/askdata/config.py | token=2
demos/ask-your-data/askdata/evalcli.py | environ=3
demos/ask-your-data/askdata/evalrun.py | email=3
demos/ask-your-data/askdata/fixtures.py | token=4
demos/ask-your-data/askdata/ledger.py | token=4
demos/ask-your-data/askdata/meter.py | token=4
demos/ask-your-data/askdata/opscli.py | environ=1
demos/ask-your-data/askdata/pgsource.py | secret=2, token=1
demos/ask-your-data/askdata/pipeline.py | email=1, token=7
demos/ask-your-data/askdata/spike_llm.py | email=1
demos/ask-your-data/askdata/validate.py | email=1, token=3
demos/ask-your-data/data/goldcheck.py | email=2, token=2
demos/ask-your-data/db/lumen.py | email=6
docs/slack-app-manifest.yaml | token=1
src/hadavin_sdk/actions/contract.py | secret=1
src/hadavin_sdk/actions/executor.py | http.client=3, secret=5, token=2, urllib=6
src/hadavin_sdk/actions/secrets.py | secret=2
src/hadavin_sdk/actions/secrets_aws.py | boto3=2, secret=10, ttl=3
src/hadavin_sdk/actions/secrets_azure.py | secret=7, ttl=3
src/hadavin_sdk/actions/secrets_cache.py | secret=2, ttl=4
src/hadavin_sdk/actions/secrets_env.py | environ=4, secret=4
src/hadavin_sdk/actions/secrets_file.py | secret=8, ttl=3
src/hadavin_sdk/actions/secrets_gcp.py | secret=11, ttl=3
src/hadavin_sdk/actions/secrets_vault.py | environ=2, secret=11, token=15, ttl=3, urllib=9
src/hadavin_sdk/app.py | environ=1, requests=1, secret=55, token=8, urllib=1
src/hadavin_sdk/approvals/__init__.py | requests=1
src/hadavin_sdk/approvals/cards.py | requests=1
src/hadavin_sdk/approvals/channel.py | secret=4
src/hadavin_sdk/approvals/gate.py | secret=1, token=6, ttl=1
src/hadavin_sdk/approvals/hmac_v0.py | secret=9, urllib=1
src/hadavin_sdk/approvals/receiver.py | requests=1
src/hadavin_sdk/approvals/slack.py | secret=4
src/hadavin_sdk/approvals/slack_channel.py | secret=5, token=4
src/hadavin_sdk/audit/anchor_gcs.py | retention=6
src/hadavin_sdk/audit/anchor_s3.py | boto3=2
src/hadavin_sdk/audit/signer.py | environ=1, secret=4
src/hadavin_sdk/audit/signer_aws.py | boto3=2
src/hadavin_sdk/audit/signer_vault.py | secret=1, token=1, ttl=1
src/hadavin_sdk/backends/builtin.py | secret=4
src/hadavin_sdk/backends/factory.py | secret=4
src/hadavin_sdk/backends/platform_secrets.py | secret=13
src/hadavin_sdk/backends/table.py | retention=5, secret=45, socket=1, token=7, ttl=6, urllib=1
src/hadavin_sdk/cli.py | environ=3, secret=14
src/hadavin_sdk/config.py | environ=8, retention=10, secret=6, token=3, urllib=1
src/hadavin_sdk/defaults.py | email=1, phone=1, requests=1, retention=1, secret=4, token=2
src/hadavin_sdk/deferred.py | environ=1, requests=1
src/hadavin_sdk/guard/bedrock_guardrail.py | boto3=2
src/hadavin_sdk/guard/egress.py | urllib=1
src/hadavin_sdk/guard/http.py | environ=1, http.client=3, socket=5, urllib=10
src/hadavin_sdk/guard/producers.py | requests=1
src/hadavin_sdk/guard/redact.py | email=2, phone=1, secret=45, token=13
src/hadavin_sdk/guard/runmap.py | email=1, phone=2, secret=4, urllib=1
src/hadavin_sdk/k1b/audit_sink.py | secret=9
src/hadavin_sdk/k1b/loop.py | token=5
src/hadavin_sdk/k1b/redaction.py | email=1, secret=8, token=2
src/hadavin_sdk/llm/anthropic.py | secret=1, token=3
src/hadavin_sdk/llm/bedrock.py | boto3=2, token=2
src/hadavin_sdk/llm/common.py | token=12, urllib=3
src/hadavin_sdk/llm/fake.py | token=2
src/hadavin_sdk/llm/gemini.py | secret=1, token=5, urllib=1
src/hadavin_sdk/llm/openai_compat.py | secret=1, token=7, urllib=1
src/hadavin_sdk/llm/retry.py | socket=1
src/hadavin_sdk/models.py | token=2
src/hadavin_sdk/registry.py | environ=1, token=1
src/hadavin_sdk/runtime/agent_loop.py | token=1
src/hadavin_sdk/runtime/evidence.py | token=2
src/hadavin_sdk/runtime/tick.py | boto3=1, retention=3, socket=1, token=2, urllib=1
src/hadavin_sdk/scrub_settings.py | secret=1
src/hadavin_sdk/sources/kubernetes.py | secret=2, token=4, urllib=1
src/hadavin_sdk/store/auth_aws.py | boto3=2, token=1
src/hadavin_sdk/store/postgres.py | environ=1, secret=4, token=1
src/hadavin_sdk/tools.py | secret=49, socket=1, token=12, urllib=8
tests/conftest.py | environ=7, secret=3, token=3
tests/contracts/aws_stub.py | boto3=3, secret=3
tests/contracts/conftest.py | secret=4
tests/contracts/http_fake.py | requests=7, retention=3, secret=11, token=3, urllib=3
tests/contracts/kinds/audit_chain.py | boto3=3, secret=8
tests/contracts/kinds/audit_neutral.py | boto3=2, retention=2, secret=2, token=2, ttl=1
tests/contracts/kinds/builtin.py | secret=7, token=2
tests/contracts/kinds/channel_slack.py | secret=2, token=2
tests/contracts/kinds/detectors.py | boto3=2, requests=2
tests/contracts/kinds/llm_wire.py | boto3=2, requests=4, token=12
tests/contracts/kinds/secrets_cloud.py | environ=6, secret=14, ttl=7
tests/contracts/kinds/secrets_neutral.py | environ=2, secret=20, token=4, ttl=17
tests/contracts/kinds/store_postgres.py | environ=1, secret=4
tests/contracts/test_capabilities.py | secret=5, token=2, urllib=1
tests/contracts/test_llm.py | requests=7, token=6
tests/contracts/test_secrets.py | secret=7, ttl=7
tests/contracts/test_sources.py | secret=2, urllib=1
tests/contracts/test_store.py | email=2
tests/contracts/vault_fake.py | secret=6, token=7
tests/demo_askdata/conftest.py | environ=4, secret=4, token=3
tests/demo_askdata/corpus.py | email=16, token=1
tests/demo_askdata/fuzzgen.py | email=3, token=14
tests/demo_askdata/lumen_standin.py | email=1
tests/demo_askdata/test_allowlist.py | email=1
tests/demo_askdata/test_audit.py | token=1
tests/demo_askdata/test_cli.py | email=1
tests/demo_askdata/test_eval_harness.py | email=1, secret=1
tests/demo_askdata/test_gold_data.py | email=4
tests/demo_askdata/test_gold_exec.py | secret=2, token=1
tests/demo_askdata/test_llm_io.py | email=1, token=1
tests/demo_askdata/test_meter.py | token=1
tests/demo_askdata/test_pipeline.py | email=2, secret=2, token=2
tests/demo_askdata/test_roles.py | email=1
tests/demo_askdata/test_seed.py | email=4, secret=2, token=1
tests/demo_askdata/test_validate_harm.py | secret=3, token=2
tests/demo_askdata/test_verify_readonly.py | email=1, secret=3, token=2
tests/fixtures/config/actions/create_draft_record.yaml | secret=1, token=1
tests/fixtures/config/actions/delete_record.yaml | secret=1, token=1
tests/fixtures/config/actions/lookup_record.yaml | secret=1, token=1
tests/fixtures/config/actions/send_email.yaml | email=3, secret=1, token=1
tests/fixtures/config/config.yaml | environ=1, secret=1, token=1
tests/fixtures/fake_system.py | token=3, urllib=1
tests/fixtures/http_fake.py | requests=2
tests/fixtures/k5_tools.py | secret=3, token=1
tests/fixtures/record.py | email=1, pii=1, token=1
tests/k1b_support.py | token=2
tests/k5_support.py | secret=5, token=1
tests/test_cuj.py | secret=4, token=3
tests/test_executor.py | secret=4, token=4
tests/test_k1a_pass_k.py | secret=2, token=1
tests/test_k1b_cli.py | secret=3
tests/test_k1b_redaction.py | email=14, requests=1, secret=6, token=1
tests/test_k1b_redaction_layers.py | email=8, secret=10, token=4, urllib=1
tests/test_k1b_replay.py | secret=4, token=1
tests/test_k2_migrations.py | secret=1
tests/test_k3_leftovers.py | secret=2
tests/test_k3_pilot.py | email=1, requests=1, secret=7, token=1
tests/test_k3_pilot_env.py | environ=1, secret=11, token=5
tests/test_k3_review_fixes.py | secret=2
tests/test_k5_classes.py | email=1, phone=1, secret=16, token=15, urllib=1
tests/test_k5_fixes1.py | secret=3, socket=1, token=1
tests/test_k5_fixes3.py | secret=10, token=1
tests/test_k5_fixes4.py | secret=1
tests/test_k5_fixes5.py | secret=12, token=4, urllib=1
tests/test_k5_fixes6.py | secret=24
tests/test_k5_fixes7.py | secret=17, urllib=1
tests/test_k5_fixes8.py | secret=12
tests/test_k5_fixes9.py | secret=32, token=2
tests/test_k5_layers.py | secret=32, token=1, urllib=1
tests/test_k5_postgres.py | secret=5
tests/test_k5_review.py | email=1, retention=1, secret=15, token=13
tests/test_k5_round10.py | email=1, environ=1, secret=11, socket=4, token=1, urllib=4
tests/test_k5_round10_postgres.py | environ=2
tests/test_k5_round11.py | secret=7
tests/test_k5_round12_fuzz.py | requests=1, secret=8, urllib=1
tests/test_k5_round5.py | requests=2, retention=2, secret=38, token=7, urllib=4
tests/test_k5_round7.py | secret=1, token=2
tests/test_k5_round8.py | requests=1, secret=16, token=6
tests/test_k5_round8_postgres.py | environ=1, secret=4, token=1
tests/test_k5_round9.py | requests=1, secret=5
tests/test_k5_round9b.py | environ=1, secret=13, token=7, urllib=3
tests/test_k5_tools.py | email=1, environ=2, pii=3, requests=4, retention=6, secret=30, token=3, urllib=2
tests/test_lockin_guard.py | boto3=18, email=1, environ=2, requests=2, secret=4, token=2
tests/test_no_hardcoded_values.py | secret=2
tests/test_p1a_fixes.py | secret=2, token=1
tests/test_p1b_backends.py | environ=8, secret=24, token=10
tests/test_p2_postgres.py | secret=11
tests/test_p3b_neutral_audit.py | boto3=4, environ=1, retention=11, secret=7, token=5
tests/test_p4_secrets.py | boto3=2, environ=2, secret=40, token=2, ttl=5
tests/test_p4b_secrets.py | boto3=1, environ=1, secret=47, token=11, ttl=2
tests/test_p5_llm.py | email=1, environ=1, requests=7, secret=5, token=12, urllib=5
tests/test_p5p6_followups.py | boto3=6, httpx=2, secret=16, token=3
tests/test_p6_detectors.py | boto3=2, requests=3, secret=3, token=3
tests/test_p7_store.py | boto3=1, secret=13, socket=1
tests/test_p7_tick.py | environ=1, secret=23, token=15, urllib=10
tests/test_repo_rules.py | secret=40
tests/test_review_fixes.py | secret=2, token=2
tests/test_review_pr3_round2.py | requests=1, secret=16, token=7, urllib=1
tests/test_s2_audit.py | email=1, secret=2
tests/test_s3_gate.py | email=3
tests/test_s4_llm_guard.py | email=2, phone=10, pii=3, secret=3, token=1
tests/test_s6_approvals.py | pii=1, secret=9
tests/tls_support.py | requests=3, socket=1
tests/warden_port/fakes.py | secret=3
tests/warden_port/privacy_corpus.py | email=1, phone=1, secret=1
tests/warden_port/test_audit_chain.py | boto3=5, environ=1, requests=1, retention=2, secret=10, token=2
tests/warden_port/test_bedrock_provider_r16.py | boto3=2, environ=1, requests=2, token=1
tests/warden_port/test_gate.py | secret=2
tests/warden_port/test_gate_review2.py | email=1
tests/warden_port/test_gate_review3.py | token=2
tests/warden_port/test_providers.py | requests=2, secret=13, token=8
tests/warden_port/test_redaction.py | email=1, phone=7, secret=28, token=16
tests/warden_port/test_redaction_bank.py | phone=1
tests/warden_port/test_redaction_review.py | secret=6, token=4, ttl=1
tests/warden_port/test_redaction_review2.py | secret=18, token=5
tests/warden_port/test_redaction_review9.py | secret=1, token=1

### 6b Every credential/egress/personal-data-word hit: file:line pattern [line kind] [enclosing def] identifier

count: 2770; showing first 200; full list: parts/evidence-1-full-6b.txt

.github/dependabot.yml:1 requests [comment] [-] requests
.github/dependabot.yml:17 requests [code] [-] requests
.github/workflows/ci.yml:36 secret [comment] [-] secrets
.github/workflows/ci.yml:50 secret [comment] [-] secrets
.github/workflows/ci.yml:51 secret [comment] [-] secret
.github/workflows/ci.yml:51 token [comment] [-] token
.github/workflows/ci.yml:55 token [code] [-] VAULT_DEV_ROOT_TOKEN_ID
.github/workflows/ci.yml:74 environ [code] [-] environment
.github/workflows/ci.yml:110 environ [code] [-] environment
.github/workflows/ci.yml:120 environ [comment] [-] environment
.github/workflows/ci.yml:123 secret [code] [-] secrets
.github/workflows/ci.yml:126 secret [code] [-] Secrets
.github/workflows/ci.yml:134 secret [comment] [-] secret
.github/workflows/ci.yml:138 secret [code] [-] secrets
.github/workflows/ci.yml:144 secret [code] [-] secret
demos/ask-your-data/askdata/allowed.py:14 email [comment] [<module>] email
demos/ask-your-data/askdata/cli.py:45 environ [code] [_source] os.environ.get
demos/ask-your-data/askdata/cli.py:113 environ [code] [_psql] os.environ.get
demos/ask-your-data/askdata/cli.py:130 environ [code] [cmd_setup] os.environ.get
demos/ask-your-data/askdata/cli.py:131 environ [code] [cmd_setup] os.environ.get
demos/ask-your-data/askdata/cli.py:172 environ [comment] [cmd_setup] environment
demos/ask-your-data/askdata/cli.py:205 email [code] [cmd_demo] email
demos/ask-your-data/askdata/cli.py:244 environ [code] [main] environment
demos/ask-your-data/askdata/compare.py:128 token [doc] [result_hash] token
demos/ask-your-data/askdata/config.py:3 secret [doc] [<module>] secret
demos/ask-your-data/askdata/config.py:4 environ [doc] [<module>] environment
demos/ask-your-data/askdata/config.py:4 secret [doc] [<module>] secrets
demos/ask-your-data/askdata/config.py:44 token [code] [RouteCfg] max_tokens
demos/ask-your-data/askdata/config.py:68 token [code] [AskdataConfig.routes] max_tokens
demos/ask-your-data/askdata/evalcli.py:72 environ [code] [build_harness] os.environ
demos/ask-your-data/askdata/evalcli.py:74 environ [code] [build_harness] os.environ
demos/ask-your-data/askdata/evalcli.py:253 environ [code] [main] os.environ.get
demos/ask-your-data/askdata/evalrun.py:36 email [code] [<module>] EMAIL
demos/ask-your-data/askdata/evalrun.py:287 email [code] [Harness.run_gold] EMAIL.search
demos/ask-your-data/askdata/evalrun.py:310 email [code] [Harness.run_adversarial] EMAIL.search
demos/ask-your-data/askdata/fixtures.py:25 token [code] [<module>] max_tokens
demos/ask-your-data/askdata/fixtures.py:41 token [code] [Step] tokens
demos/ask-your-data/askdata/fixtures.py:63 token [code] [Step.reply] input_tokens
demos/ask-your-data/askdata/fixtures.py:64 token [code] [Step.reply] output_tokens
demos/ask-your-data/askdata/ledger.py:67 token [code] [Attempt] tokens_in
demos/ask-your-data/askdata/ledger.py:68 token [code] [Attempt] tokens_out
demos/ask-your-data/askdata/ledger.py:108 token [code] [LedgerLine] tokens_in
demos/ask-your-data/askdata/ledger.py:109 token [code] [LedgerLine] tokens_out
demos/ask-your-data/askdata/meter.py:31 token [code] [<module>] estimate_tokens
demos/ask-your-data/askdata/meter.py:49 token [doc] [worst_case_usd] token
demos/ask-your-data/askdata/meter.py:51 token [code] [worst_case_usd] tokens_in
demos/ask-your-data/askdata/meter.py:53 token [code] [worst_case_usd] tokens_in
demos/ask-your-data/askdata/meter.py:54 token [code] [worst_case_usd] route.max_tokens
demos/ask-your-data/askdata/opscli.py:226 environ [code] [main] os.environ.get
demos/ask-your-data/askdata/pgsource.py:26 secret [code] [<module>] secrets
demos/ask-your-data/askdata/pgsource.py:194 secret [code] [PgSource._fetch] secrets.token_hex
demos/ask-your-data/askdata/pgsource.py:194 token [code] [PgSource._fetch] secrets.token_hex
demos/ask-your-data/askdata/pipeline.py:49 email [code] [Settings] email
demos/ask-your-data/askdata/pipeline.py:179 token [code] [Pipeline._generate_and_execute] run.tokens_in
demos/ask-your-data/askdata/pipeline.py:180 token [code] [Pipeline._generate_and_execute] run.tokens_out
demos/ask-your-data/askdata/pipeline.py:186 token [code] [Pipeline._generate_and_execute] tokens_in
demos/ask-your-data/askdata/pipeline.py:187 token [code] [Pipeline._generate_and_execute] tokens_out
demos/ask-your-data/askdata/pipeline.py:348 token [code] [Pipeline._finish] tokens_in
demos/ask-your-data/askdata/pipeline.py:397 token [code] [_Run] tokens_in
demos/ask-your-data/askdata/pipeline.py:398 token [code] [_Run] tokens_out
demos/ask-your-data/askdata/spike_llm.py:30 email [code] [<module>] email
demos/ask-your-data/askdata/validate.py:61 token [code] [<module>] token
demos/ask-your-data/askdata/validate.py:473 email [code] [_check_detail] email
demos/ask-your-data/askdata/validate.py:619 token [code] [validate] token
demos/ask-your-data/askdata/validate.py:623 token [code] [validate] token
demos/ask-your-data/data/goldcheck.py:152 email [code] [sql_problems] bemail
demos/ask-your-data/data/goldcheck.py:153 email [code] [sql_problems] email
demos/ask-your-data/data/goldcheck.py:163 token [code] [_tokens] _tokens
demos/ask-your-data/data/goldcheck.py:168 token [code] [jaccard] _tokens
demos/ask-your-data/db/lumen.py:301 email [code] [<module>] email
demos/ask-your-data/db/lumen.py:314 email [code] [<module>] emails
demos/ask-your-data/db/lumen.py:317 email [code] [<module>] email
demos/ask-your-data/db/lumen.py:318 email [code] [<module>] emails
demos/ask-your-data/db/lumen.py:321 email [code] [<module>] email
demos/ask-your-data/db/lumen.py:327 email [code] [<module>] email
docs/slack-app-manifest.yaml:9 secret [comment] [-] Secret
docs/slack-app-manifest.yaml:9 token [comment] [-] Token
docs/slack-app-manifest.yaml:10 secret [comment] [-] bot_token_secret_name
docs/slack-app-manifest.yaml:10 token [comment] [-] bot_token_secret_name
docs/slack-app-manifest.yaml:33 token [code] [-] token_rotation_enabled
src/hadavin_sdk/actions/authorizer.py:24 secret [doc] [authorize] secret
src/hadavin_sdk/actions/contract.py:40 secret [code] [HttpExecutor] secret_name
src/hadavin_sdk/actions/executor.py:1 secret [doc] [<module>] secret
src/hadavin_sdk/actions/executor.py:9 http.client [code] [<module>] http.client
src/hadavin_sdk/actions/executor.py:12 urllib [code] [<module>] urllib.error
src/hadavin_sdk/actions/executor.py:13 urllib [code] [<module>] urllib.request
src/hadavin_sdk/actions/executor.py:16 urllib [code] [<module>] urllib.parse
src/hadavin_sdk/actions/executor.py:19 secret [code] [<module>] hadavin_sdk.actions.secrets
src/hadavin_sdk/actions/executor.py:29 token [comment] [<module>] token
src/hadavin_sdk/actions/executor.py:49 secret [code] [Executor.__init__] secrets
src/hadavin_sdk/actions/executor.py:51 secret [code] [Executor.__init__] self._secrets
src/hadavin_sdk/actions/executor.py:60 secret [code] [Executor._caller] secret
src/hadavin_sdk/actions/executor.py:63 secret [code] [Executor._caller] self._secrets.get
src/hadavin_sdk/actions/executor.py:63 token [code] [Executor._caller] token
src/hadavin_sdk/actions/executor.py:73 urllib [code] [Executor._caller.call] urllib.request.Request
src/hadavin_sdk/actions/executor.py:74 token [code] [Executor._caller.call] token
src/hadavin_sdk/actions/executor.py:82 urllib [code] [Executor._caller.call] urllib.error.HTTPError
src/hadavin_sdk/actions/executor.py:130 urllib [code] [Executor.execute] urllib.error.URLError
src/hadavin_sdk/actions/executor.py:135 http.client [code] [Executor.execute] http.client.HTTPException
src/hadavin_sdk/actions/executor.py:163 http.client [code] [Executor._lookup] http.client.HTTPException
src/hadavin_sdk/actions/secrets.py:1 secret [doc] [<module>] Secret
src/hadavin_sdk/actions/secrets.py:8 secret [code] [SecretProvider] SecretProvider
src/hadavin_sdk/actions/secrets.py:12 secret [code] [FakeSecretProvider] FakeSecretProvider
src/hadavin_sdk/actions/secrets_aws.py:1 secret [doc] [<module>] aws_secrets_manager
src/hadavin_sdk/actions/secrets_aws.py:3 environ [doc] [<module>] os.environ
src/hadavin_sdk/actions/secrets_aws.py:3 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_aws.py:5 secret [doc] [<module>] secrets_cache.CachedSecrets
src/hadavin_sdk/actions/secrets_aws.py:14 boto3 [code] [<module>] boto3
src/hadavin_sdk/actions/secrets_aws.py:16 secret [code] [<module>] hadavin_sdk.actions.secrets_cache
src/hadavin_sdk/actions/secrets_aws.py:20 secret [code] [SecretsManagerProvider] SecretsManagerProvider
src/hadavin_sdk/actions/secrets_aws.py:22 ttl [code] [SecretsManagerProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_aws.py:24 ttl [code] [SecretsManagerProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_aws.py:29 secret [code] [SecretsManagerProvider._fetch] self._client.get_secret_value
src/hadavin_sdk/actions/secrets_aws.py:33 secret [code] [SecretsManagerProvider._fetch] secret
src/hadavin_sdk/actions/secrets_aws.py:35 secret [code] [SecretsManagerProvider._fetch] SecretString
src/hadavin_sdk/actions/secrets_aws.py:36 secret [comment] [SecretsManagerProvider._fetch] secrets
src/hadavin_sdk/actions/secrets_aws.py:37 secret [code] [SecretsManagerProvider._fetch] secret
src/hadavin_sdk/actions/secrets_aws.py:38 secret [code] [SecretsManagerProvider._fetch] SecretString
src/hadavin_sdk/actions/secrets_aws.py:41 secret [code] [build] SecretsManagerProvider
src/hadavin_sdk/actions/secrets_aws.py:42 secret [code] [build] secretsmanager
src/hadavin_sdk/actions/secrets_aws.py:42 boto3 [code] [build] boto3.client
src/hadavin_sdk/actions/secrets_aws.py:43 secret [code] [build] SecretsManagerProvider
src/hadavin_sdk/actions/secrets_aws.py:43 ttl [code] [build] settings.ttl_s
src/hadavin_sdk/actions/secrets_azure.py:1 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_azure.py:4 secret [doc] [<module>] secret
src/hadavin_sdk/actions/secrets_azure.py:5 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_azure.py:18 secret [code] [<module>] azure.keyvault.secrets
src/hadavin_sdk/actions/secrets_azure.py:20 secret [code] [<module>] hadavin_sdk.actions.secrets_cache
src/hadavin_sdk/actions/secrets_azure.py:26 secret [code] [AzureKeyVaultProvider] CachedSecrets
src/hadavin_sdk/actions/secrets_azure.py:28 ttl [code] [AzureKeyVaultProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_azure.py:30 ttl [code] [AzureKeyVaultProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_azure.py:35 secret [code] [AzureKeyVaultProvider._fetch] secret
src/hadavin_sdk/actions/secrets_azure.py:37 secret [code] [AzureKeyVaultProvider._fetch] self._client.get_secret
src/hadavin_sdk/actions/secrets_azure.py:39 secret [code] [AzureKeyVaultProvider._fetch] secret
src/hadavin_sdk/actions/secrets_azure.py:45 secret [code] [build] SecretClient
src/hadavin_sdk/actions/secrets_azure.py:52 ttl [code] [build] settings.ttl_s
src/hadavin_sdk/actions/secrets_cache.py:1 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_cache.py:1 ttl [doc] [<module>] TTL
src/hadavin_sdk/actions/secrets_cache.py:3 ttl [doc] [<module>] ttl_s
src/hadavin_sdk/actions/secrets_cache.py:5 secret [doc] [<module>] secret
src/hadavin_sdk/actions/secrets_cache.py:5 ttl [doc] [<module>] TTL.
src/hadavin_sdk/actions/secrets_cache.py:17 secret [code] [CachedSecrets] CachedSecrets
src/hadavin_sdk/actions/secrets_cache.py:18 secret [doc] [CachedSecrets] secret.
src/hadavin_sdk/actions/secrets_cache.py:20 ttl [code] [CachedSecrets.__init__] ttl_s
src/hadavin_sdk/actions/secrets_cache.py:21 ttl [code] [CachedSecrets.__init__] self.ttl_s
src/hadavin_sdk/actions/secrets_cache.py:24 ttl [comment] [CachedSecrets.__init__] TTL
src/hadavin_sdk/actions/secrets_cache.py:35 secret [code] [CachedSecrets.get] secret
src/hadavin_sdk/actions/secrets_cache.py:36 ttl [code] [CachedSecrets.get] self.ttl_s
src/hadavin_sdk/actions/secrets_cache.py:37 ttl [code] [CachedSecrets.get] self.ttl_s
src/hadavin_sdk/actions/secrets_env.py:1 environ [doc] [<module>] environment
src/hadavin_sdk/actions/secrets_env.py:1 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_env.py:4 environ [doc] [<module>] environment
src/hadavin_sdk/actions/secrets_env.py:4 secret [doc] [<module>] HADAVIN_SECRET_FIXTURE_TOKEN
src/hadavin_sdk/actions/secrets_env.py:4 token [doc] [<module>] token
src/hadavin_sdk/actions/secrets_env.py:16 secret [code] [EnvSecretProvider] EnvSecretProvider
src/hadavin_sdk/actions/secrets_env.py:17 environ [code] [EnvSecretProvider.__init__] environ
src/hadavin_sdk/actions/secrets_env.py:18 environ [code] [EnvSecretProvider.__init__] self._environ
src/hadavin_sdk/actions/secrets_env.py:24 environ [code] [EnvSecretProvider.get] self._environ.get
src/hadavin_sdk/actions/secrets_env.py:27 environ [code] [EnvSecretProvider.get] environment
src/hadavin_sdk/actions/secrets_env.py:27 secret [code] [EnvSecretProvider.get] secret
src/hadavin_sdk/actions/secrets_env.py:32 secret [code] [build] EnvSecretProvider
src/hadavin_sdk/actions/secrets_env.py:33 secret [code] [build] EnvSecretProvider
src/hadavin_sdk/actions/secrets_file.py:1 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_file.py:3 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_file.py:4 secret [doc] [<module>] Secrets
src/hadavin_sdk/actions/secrets_file.py:4 ttl [doc] [<module>] ttl_s
src/hadavin_sdk/actions/secrets_file.py:10 secret [doc] [<module>] secret
src/hadavin_sdk/actions/secrets_file.py:21 secret [code] [<module>] hadavin_sdk.actions.secrets_cache
src/hadavin_sdk/actions/secrets_file.py:26 secret [code] [MountedFileProvider] CachedSecrets
src/hadavin_sdk/actions/secrets_file.py:28 ttl [code] [MountedFileProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_file.py:30 ttl [code] [MountedFileProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_file.py:43 secret [code] [MountedFileProvider._fetch] secret
src/hadavin_sdk/actions/secrets_file.py:46 secret [code] [MountedFileProvider._fetch] secret
src/hadavin_sdk/actions/secrets_file.py:52 secret [code] [MountedFileProvider._fetch] secret
src/hadavin_sdk/actions/secrets_file.py:56 secret [code] [MountedFileProvider._fetch] secret
src/hadavin_sdk/actions/secrets_file.py:63 secret [code] [MountedFileProvider._fetch] secret
src/hadavin_sdk/actions/secrets_file.py:71 secret [code] [build] secrets
src/hadavin_sdk/actions/secrets_file.py:72 ttl [code] [build] settings.ttl_s
src/hadavin_sdk/actions/secrets_gcp.py:1 secret [doc] [<module>] gcp_secret_manager
src/hadavin_sdk/actions/secrets_gcp.py:17 secret [code] [<module>] secretmanager
src/hadavin_sdk/actions/secrets_gcp.py:19 secret [code] [<module>] hadavin_sdk.actions.secrets_cache
src/hadavin_sdk/actions/secrets_gcp.py:25 secret [code] [GcpSecretManagerProvider] GcpSecretManagerProvider
src/hadavin_sdk/actions/secrets_gcp.py:30 ttl [code] [GcpSecretManagerProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_gcp.py:33 ttl [code] [GcpSecretManagerProvider.__init__] ttl_s
src/hadavin_sdk/actions/secrets_gcp.py:38 secret [code] [GcpSecretManagerProvider._fetch] secret
src/hadavin_sdk/actions/secrets_gcp.py:39 secret [code] [GcpSecretManagerProvider._fetch] secrets
src/hadavin_sdk/actions/secrets_gcp.py:42 secret [code] [GcpSecretManagerProvider._fetch] self._client.access_secret_version
src/hadavin_sdk/actions/secrets_gcp.py:44 secret [code] [GcpSecretManagerProvider._fetch] secret
src/hadavin_sdk/actions/secrets_gcp.py:48 secret [code] [build] GcpSecretManagerProvider
src/hadavin_sdk/actions/secrets_gcp.py:50 secret [code] [build] secretmanager.SecretManagerServiceClient
src/hadavin_sdk/actions/secrets_gcp.py:53 secret [code] [build] secrets
src/hadavin_sdk/actions/secrets_gcp.py:56 secret [code] [build] GcpSecretManagerProvider
src/hadavin_sdk/actions/secrets_gcp.py:56 ttl [code] [build] settings.ttl_s
src/hadavin_sdk/actions/secrets_vault.py:1 secret [doc] [<module>] secrets
src/hadavin_sdk/actions/secrets_vault.py:4 environ [doc] [<module>] environment
src/hadavin_sdk/actions/secrets_vault.py:4 token [doc] [<module>] token
src/hadavin_sdk/actions/secrets_vault.py:5 environ [doc] [<module>] environment
src/hadavin_sdk/actions/secrets_vault.py:5 secret [doc] [<module>] secret
src/hadavin_sdk/actions/secrets_vault.py:6 token [doc] [<module>] token
src/hadavin_sdk/actions/secrets_vault.py:7 token [doc] [<module>] token

### 6c Upper-case configuration/credential NAMES found as string literals (names only, first 3 locations)

count: 44

ANTHROPIC_BASE_URL <- tests/warden_port/test_providers.py:162
ANTHROPIC_FOUNDRY_BASE_URL <- tests/warden_port/test_providers.py:164
ANTHROPIC_VERTEX_BASE_URL <- tests/warden_port/test_providers.py:163
APIKEY <- src/hadavin_sdk/approvals/channel.py:44, src/hadavin_sdk/guard/redact.py:1144, src/hadavin_sdk/guard/redact.py:195
ASKDATA_ADMIN_DSN <- demos/ask-your-data/askdata/cli.py:130
ASKDATA_DSN <- demos/ask-your-data/askdata/cli.py:45, demos/ask-your-data/askdata/evalcli.py:73, tests/demo_askdata/test_cli.py:12
ASKDATA_DSN_B <- demos/ask-your-data/askdata/evalcli.py:73, tests/demo_askdata/test_eval_harness.py:646
ASKDATA_DSN_CLEAN <- demos/ask-your-data/askdata/evalcli.py:73, tests/demo_askdata/test_eval_harness.py:646
ASKDATA_RO_PASSWORD <- demos/ask-your-data/askdata/cli.py:131
AWS_ACCESS_KEY_ID <- tests/conftest.py:34
AWS_CONTAINER_CREDENTIALS_ <- tests/conftest.py:26
AWS_DEFAULT_PROFILE <- tests/conftest.py:20
AWS_ENDPOINT_URL <- tests/conftest.py:25, tests/test_lockin_guard.py:756, tests/test_p6_detectors.py:350
AWS_ENDPOINT_URL_BEDROCK_RUNTIME <- tests/warden_port/test_bedrock_provider_r16.py:88
AWS_PROFILE <- tests/conftest.py:19, tests/test_lockin_guard.py:755, tests/test_p5p6_followups.py:293
AWS_SECRET_ACCESS_KEY <- tests/conftest.py:35
AWS_SESSION_TOKEN <- tests/conftest.py:21
AWS_SHARED_CREDENTIALS_FILE <- tests/conftest.py:33, tests/test_p5p6_followups.py:295, tests/test_p6_detectors.py:347
AWS_WEB_IDENTITY_TOKEN_FILE <- tests/conftest.py:22, tests/test_lockin_guard.py:755
DB_PASSWORD <- tests/test_k1b_redaction_layers.py:85
GCPTOKEN <- src/hadavin_sdk/guard/redact.py:1145, src/hadavin_sdk/guard/redact.py:206, tests/warden_port/test_redaction.py:409
GOOGLE_APPLICATION_CREDENTIALS <- tests/conftest.py:27, tests/test_lockin_guard.py:756
GOOGLE_GEMINI_BASE_URL <- tests/warden_port/test_providers.py:146
HADAVIN_KEY_DIR <- src/hadavin_sdk/audit/signer.py:123, tests/test_p3b_neutral_audit.py:517
HADAVIN_MIGRATE_DSN <- src/hadavin_sdk/cli.py:322, tests/test_k2_migrations.py:135, tests/test_p2_postgres.py:103
HADAVIN_SECRET_ <- src/hadavin_sdk/backends/table.py:142, tests/contracts/kinds/secrets_cloud.py:16
HADAVIN_SECRET_EMPTY <- tests/test_p4_secrets.py:92
HADAVIN_SECRET_FIXTURE_TOKEN <- tests/test_k5_round5.py:153, tests/test_k5_round5.py:173, tests/test_p4_secrets.py:98
HADAVIN_SECRET_K8S_TOKEN <- tests/test_k5_round5.py:152, tests/test_k5_round5.py:172
HADAVIN_SECRET_MISSING_ONE <- tests/test_p4_secrets.py:102
HADAVIN_SECRET_TOOL_KEY <- tests/test_k5_round5.py:154, tests/test_k5_round5.py:174
HADAVIN_TEST_PG_DSN <- tests/contracts/kinds/store_postgres.py:22, tests/demo_askdata/conftest.py:45, tests/test_k5_round10_postgres.py:15
HADAVIN_TEST_VAULT_TOKEN <- tests/contracts/kinds/secrets_neutral.py:45
HOSTNAME <- src/hadavin_sdk/defaults.py:115, src/hadavin_sdk/guard/redact.py:388, src/hadavin_sdk/guard/redact.py:934
MAX_TOKENS <- src/hadavin_sdk/llm/common.py:126, tests/contracts/kinds/llm_wire.py:140, tests/test_p5_llm.py:151
OPERATORKEYDONOTUSE <- tests/warden_port/fakes.py:19
PGHOST <- src/hadavin_sdk/store/postgres.py:56, tests/test_p7_store.py:59
PGPASSWORD <- tests/demo_askdata/conftest.py:92
PRIVKEY <- src/hadavin_sdk/guard/redact.py:1142, src/hadavin_sdk/guard/redact.py:157, src/hadavin_sdk/guard/redact.py:165
SECRET <- src/hadavin_sdk/approvals/channel.py:44, src/hadavin_sdk/guard/redact.py:1151, src/hadavin_sdk/guard/redact.py:487
SECRET_REDACTED <- tests/test_k5_fixes3.py:54, tests/test_k5_round9b.py:272
URLCRED <- src/hadavin_sdk/approvals/channel.py:44, src/hadavin_sdk/guard/redact.py:1148, src/hadavin_sdk/guard/redact.py:227
VAULT_SECRET_ID <- src/hadavin_sdk/backends/table.py:259, tests/test_p4b_secrets.py:142, tests/test_p4b_secrets.py:60
VAULT_TOKEN <- src/hadavin_sdk/backends/table.py:257, tests/test_p3b_neutral_audit.py:103, tests/test_p4b_secrets.py:47

### 7a Actual counts (computed)

count: 7

count `def test_` / `async def test_` by ast in tests/**/*.py: 1695 (in 116 test_*.py files; per dir: {'tests': 1213, 'tests/contracts': 72, 'tests/contracts/kinds': 0, 'tests/demo_askdata': 276, 'tests/fixtures': 0, 'tests/warden_port': 134}); parametrized cases not expanded; pytest NOT run: every doc test-count claim is UNVERIFIED-against-pytest
python files under src/: 102 (non-__init__: 91)
files by kind prefix: anchor: 3 ['anchor_azure', 'anchor_gcs', 'anchor_s3']; secrets: 7 ['secrets_aws', 'secrets_azure', 'secrets_cache', 'secrets_env', 'secrets_file', 'secrets_gcp', 'secrets_vault']; signer: 4 ['signer_aws', 'signer_azure', 'signer_gcp', 'signer_vault']
llm backend module candidates (src/hadavin_sdk/llm minus common/protocol/retry): 5 ['anthropic', 'bedrock', 'fake', 'gemini', 'openai_compat']
pyproject project.version = 0.1.0; requires-python = >=3.12
test_*.py counts by dir: {'tests/contracts': 7, 'tests/demo_askdata': 26, 'tests': 70, 'tests/warden_port': 13}
.claude/rules files: 39

### 7b Doc claims of the form '<n> tests|modules|kinds|backends|rules' (file:line, claim text, line)

count: 8

.claude/rules/egm-for-every-plan.md:30 claim '01 rule' | History: on 2026-10-29 Claude skipped EGM for the backup script, AWS teardown and DNS cleanup (a breach under the then-mandatory rule); the 
handover/CLOUD-RESUME-2026-11-06.md:41 claim '3 tests' | - 66 core/P4d -> main (P4d-a1), head 0ee16cc (you pushed 92dbb1e later: the lead has NOT reviewed that delta yet): lead round 2 no blocker/m
handover/CLOUD-RESUME-2026-11-06.md:51 claim '3 tests' | b) PR 66: fix the 3 tests; add a line to the ticket note blessing the extra names and the xdist refusal; params=() with a literal %; scope r
handover/CLOUD-RESUME-2026-11-11.md:260 claim '5 tests' | - P3a-2: 3b head 1ffa6559 suite RED (5 failed). Fix builder has uncommitted edits in /home/user/build/B-P3a2-fx (3 k5 tests re-pointed, psyc
handover/CLOUD-RESUME-2026-11-11.md:260 claim '2 tests' | - P3a-2: 3b head 1ffa6559 suite RED (5 failed). Fix builder has uncommitted edits in /home/user/build/B-P3a2-fx (3 k5 tests re-pointed, psyc
handover/CLOUD-RESUME-2026-11-11.md:276 claim '12 tests' | - Q8c-1: ledger reconciled (20 rows edited, 4 added); no reviewer has read ad588599; Vault engine CI run (12 tests) still outstanding (gate 
handover/CLOUD-RESUME-2026-11-13.md:38 claim '5 test' | - RUN ON LAPTOP (lead's list): the 5 test files on 3.12; `HADAVIN_POLICY_FULL_RENEWAL_RUN=1 pytest tests/test_policy_changelog.py -k plant`;
handover/STATUS.md:37 claim '17 test' | - Open points for the lead: P4b1 needs P4d to let settle_spend accept actual > reserved (P4b1 item 1); P4b1-c waits for the lead's answer on

### 7c Doc version strings and whether the number equals a pyproject pin or the project version

count: 26

CHANGELOG.md:31 version 198.18.0 matches-a-pyproject-pin-or-project-version=no
CHANGELOG.md:145 version 0.1.0 matches-a-pyproject-pin-or-project-version=yes
CHANGELOG.md:146 version 0.0.0 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 169.254.169 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 100.100.100 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 192.0.0 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 168.63.129 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 0.0.0 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 198.18.0 matches-a-pyproject-pin-or-project-version=no
README.md:30 version 127.0.0 matches-a-pyproject-pin-or-project-version=no
demos/ask-your-data/README.md:40 version 127.0.0 matches-a-pyproject-pin-or-project-version=no
demos/ask-your-data/README.md:42 version 127.0.0 matches-a-pyproject-pin-or-project-version=no
demos/ask-your-data/README.md:44 version 127.0.0 matches-a-pyproject-pin-or-project-version=no
demos/ask-your-data/README.md:98 version 127.0.0 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-EGM-SETUP-2026-11-12.md:6 version 2.1.271 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-09.md:3 version 0.1.1 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-11.md:84 version 2.4.0 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-11.md:85 version 12.31.1 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-11.md:86 version 2.16.2 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-11.md:87 version 0.17.3 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-11.md:88 version 1.32.0 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-13.md:19 version 0.16.9 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-13.md:19 version 0.17.1 matches-a-pyproject-pin-or-project-version=yes
handover/CLOUD-RESUME-2026-11-13.md:51 version 0.17.1 matches-a-pyproject-pin-or-project-version=yes
handover/CLOUD-RESUME-2026-11-13.md:51 version 0.16.9 matches-a-pyproject-pin-or-project-version=no
handover/CLOUD-RESUME-2026-11-13.md:62 version 0.17.1 matches-a-pyproject-pin-or-project-version=yes

### 7d Doc port claims ('port NNNN')

(none found)

### 7e Code port-like literals

count: 58

demos/ask-your-data/askdata/pipeline.py:218 [Pipeline._generate_and_execute] port-like number 4000
demos/ask-your-data/askdata/pipeline.py:256 [Pipeline._execute] port-like number 4000
demos/ask-your-data/askdata/pipeline.py:257 [Pipeline._execute] port-like number 4000
demos/ask-your-data/askdata/pipeline.py:267 [Pipeline._execute] port-like number 4000
demos/ask-your-data/db/lumen.py:319 [<module>] port-like number 55
demos/ask-your-data/db/lumen.py:321 [<module>] port-like number 210
demos/ask-your-data/db/lumen.py:322 [<module>] port-like number 1301
demos/ask-your-data/db/lumen.py:323 [<module>] port-like number 900
src/hadavin_sdk/defaults.py:101 [<module>] port-like number 443
src/hadavin_sdk/defaults.py:102 [<module>] port-like number 80
tests/demo_askdata/test_seed.py:43 [test_row_counts_and_totals] port-like number 1500
tests/test_g4_parity.py:138 [<module>] port-like number 2375
tests/test_g4_parity.py:265 [test_g4_reads_hostile_text_in_linear_time] port-like number 3500
tests/test_k5_classes.py:401 [<module>] port-like number 8080
tests/test_k5_classes.py:415 [<module>] port-like number 10
tests/test_k5_classes.py:435 [test_class_mutability_the_manifest_fields_are_tuples] port-like number 443
tests/test_k5_fixes1.py:115 [test_the_opener_receives_the_normalised_host] port-like number 443
tests/test_k5_review.py:141 [test_config_evidence_limits_have_documented_defaults_and_validate] port-like number 70000
tests/test_k5_review.py:169 [test_config_fetch_limits_reach_the_tool_context] port-like number 8443
tests/test_k5_review.py:191 [test_config_fetch_limits_reach_the_tool_context] port-like number 443
tests/test_k5_review.py:193 [test_config_fetch_limits_reach_the_tool_context] port-like number 8443
tests/test_k5_review.py:423 [test_review_a_port_outside_the_allowlist_is_refused] port-like number 22
tests/test_k5_review.py:425 [test_review_a_port_outside_the_allowlist_is_refused] port-like number 8443
tests/test_k5_review.py:426 [test_review_a_port_outside_the_allowlist_is_refused] port-like number 8443
tests/test_k5_review.py:446 [test_review_a_manifest_port_list_widens_the_allowlist] port-like number 8443
tests/test_k5_review.py:532 [test_review_yaml_manifest_ports_round_trip] port-like number 8443
tests/test_k5_review.py:534 [test_review_yaml_manifest_ports_round_trip] port-like number 8443
tests/test_k5_review.py:535 [test_review_yaml_manifest_ports_round_trip] port-like number 8443
tests/test_k5_round10.py:292 [test_an_environment_proxy_does_not_receive_the_connection] port-like number 3128
tests/test_k5_round10.py:293 [test_an_environment_proxy_does_not_receive_the_connection] port-like number 3128
tests/test_k5_round5.py:739 [test_anchored_patterns_refuse_a_name_or_url_that_merely_contains_a_good_one] port-like number 6443
tests/test_k5_round9b.py:169 [test_tools_never_use_an_environment_proxy] port-like number 3128
tests/test_k5_round9b.py:170 [test_tools_never_use_an_environment_proxy] port-like number 3128
tests/test_k5_round9b.py:199 [<module>] port-like number 4700
tests/test_k5_tools.py:194 [test_k5_fetch_cluster_http_allowed_only_to_cluster_hosts] port-like number 9090
tests/test_p3b_neutral_audit.py:283 [test_rds_iam_signs_in_through_store_auth_aws] port-like number 5432
tests/test_p3b_neutral_audit.py:314 [test_connect_signs_in_through_the_iam_helper_for_store_and_migrate] port-like number 5432
tests/test_p4b_secrets.py:150 [test_vault_settings_need_tls_and_their_auth_fields] port-like number 8200
tests/test_p5_llm.py:42 [test_where_the_model_runs_is_in_the_config_hash] port-like number 11434
tests/test_p5p6_followups.py:269 [<module>] port-like number 11434
tests/test_p5p6_followups.py:437 [test_the_other_network_kinds_name_their_hosts] port-like number 8200
tests/test_p7_store.py:23 [<module>] port-like number 5432
tests/test_s4_llm_guard.py:86 [test_unknown_host_refused] port-like number 8080
tests/warden_port/privacy_corpus.py:26 [<module>] port-like number 7334
tests/warden_port/privacy_corpus.py:27 [<module>] port-like number 001
tests/warden_port/privacy_corpus.py:31 [<module>] port-like number 5432
tests/warden_port/privacy_corpus.py:36 [<module>] port-like number 5432
tests/warden_port/privacy_corpus.py:68 [<module>] port-like number 8080
tests/warden_port/test_audit_chain.py:354 [test_an_s3_compatible_store_is_reached_through_endpoint_url] port-like number 9000
tests/warden_port/test_audit_chain.py:367 [test_an_s3_compatible_store_is_reached_through_endpoint_url] port-like number 9000
tests/warden_port/test_gate_review3.py:106 [<module>] port-like number 8080
tests/warden_port/test_providers.py:64 [test_ollama_needs_no_real_key] port-like number 11434
tests/warden_port/test_providers.py:66 [test_ollama_needs_no_real_key] port-like number 11434
tests/warden_port/test_providers.py:108 [<module>] port-like number 11434
tests/warden_port/test_providers.py:196 [test_a_model_must_be_named_exactly] port-like number 11434
tests/warden_port/test_redaction.py:177 [test_high_value_credentials_in_logs_are_masked] port-like number 5432
tests/warden_port/test_redaction.py:179 [test_high_value_credentials_in_logs_are_masked] port-like number 6379
tests/warden_port/test_redaction.py:208 [test_ipv6_addresses_are_masked_like_ipv4] port-like number 7334

### 7f Back-ticked file names in docs (non-handover) that match NO tracked file (checked 92 names)

count: 16

.claude/rules/long-jobs-run-detached.md:12 names file `scripts/mutation_check.py`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:38 names file `0006_evidence.sql`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:45 names file `0006_evidence.sql`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:52 names file `0006_evidence.sql`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:103 names file `replay-records.jsonl`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:114 names file `FAILED.txt`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:126 names file `run.json`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:137 names file `run.json`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:137 names file `replay-report.md`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:137 names file `score-report.md`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:152 names file `FAILED.txt`: no tracked path equals it or ends with it, no tracked file has that base name
CHANGELOG.md:251 names file `golden_dir/judge.jsonl`: no tracked path equals it or ends with it, no tracked file has that base name
README.md:19 names file `OUT/score/score-report.md`: no tracked path equals it or ends with it, no tracked file has that base name
README.md:20 names file `FAILED.txt`: no tracked path equals it or ends with it, no tracked file has that base name
README.md:21 names file `FAILED.txt`: no tracked path equals it or ends with it, no tracked file has that base name
demos/ask-your-data/README.md:77 names file `eval/lock.json`: no tracked path equals it or ends with it, no tracked file has that base name

### 8a Declared dependency (pyproject: dependencies, extras, groups, build) -> import names mapped and whether any python file imports them

count: 24

anthropic [extra:anthropic] map(table)=['anthropic'] -> imported as ['anthropic'] in 1 files ['src/hadavin_sdk/llm/anthropic.py']
azure-identity [extra:azure] map(table)=['azure.identity'] -> imported as ['azure.identity', 'azure.identity.DefaultAzureCredential'] in 4 files ['src/hadavin_sdk/actions/secrets_azure.py', 'src/hadavin_sdk/audit/anchor_azure.py', 'src/hadavin_sdk/audit/signer_azure.py']
azure-keyvault-keys [extra:azure] map(table)=['azure.keyvault.keys'] -> imported as ['azure.keyvault.keys', 'azure.keyvault.keys.crypto', 'azure.keyvault.keys.crypto.CryptographyClient', 'azure.keyvault.keys.crypto.SignatureAlgorithm'] in 2 files ['src/hadavin_sdk/audit/signer_azure.py', 'tests/contracts/http_fake.py']
azure-keyvault-secrets [extra:azure] map(table)=['azure.keyvault.secrets'] -> imported as ['azure.keyvault.secrets', 'azure.keyvault.secrets.SecretClient'] in 2 files ['src/hadavin_sdk/actions/secrets_azure.py', 'tests/contracts/http_fake.py']
azure-storage-blob [extra:azure] map(table)=['azure.storage.blob'] -> imported as ['azure.storage.blob', 'azure.storage.blob.BlobImmutabilityPolicyMode', 'azure.storage.blob.ContainerClient', 'azure.storage.blob.ImmutabilityPolicy'] in 2 files ['src/hadavin_sdk/audit/anchor_azure.py', 'tests/contracts/http_fake.py']
bandit [group:scan] -> import names UNMAPPED
boto3 [extra:aws] map(table)=['boto3', 'botocore'] -> imported as ['boto3', 'botocore', 'botocore.UNSIGNED', 'botocore.awsrequest'] in 15 files ['src/hadavin_sdk/actions/secrets_aws.py', 'src/hadavin_sdk/audit/anchor_s3.py', 'src/hadavin_sdk/audit/signer_aws.py']
cryptography [extra:aws, extra:signer, extra:azure, extra:gcp] map(table)=['cryptography'] -> imported as ['cryptography', 'cryptography.exceptions', 'cryptography.exceptions.InvalidSignature', 'cryptography.hazmat.primitives'] in 9 files ['src/hadavin_sdk/audit/signer.py', 'src/hadavin_sdk/audit/signer_aws.py', 'src/hadavin_sdk/audit/signer_gcp.py']
google-cloud-kms [extra:gcp] map(table)=['google.cloud.kms'] -> imported as ['google.cloud', 'google.cloud.kms'] in 5 files ['src/hadavin_sdk/actions/secrets_gcp.py', 'src/hadavin_sdk/audit/anchor_gcs.py', 'src/hadavin_sdk/audit/signer_gcp.py']
google-cloud-secret-manager [extra:gcp] map(table)=['google.cloud.secretmanager'] -> imported as ['google.cloud', 'google.cloud.secretmanager'] in 5 files ['src/hadavin_sdk/actions/secrets_gcp.py', 'src/hadavin_sdk/audit/anchor_gcs.py', 'src/hadavin_sdk/audit/signer_gcp.py']
google-cloud-storage [extra:gcp] map(table)=['google.cloud.storage'] -> imported as ['google.cloud', 'google.cloud.storage'] in 5 files ['src/hadavin_sdk/actions/secrets_gcp.py', 'src/hadavin_sdk/audit/anchor_gcs.py', 'src/hadavin_sdk/audit/signer_gcp.py']
markdown-it-py [dependencies] map(table)=['markdown_it'] -> imported as ['markdown_it', 'markdown_it.MarkdownIt'] in 4 files ['src/hadavin_sdk/approvals/gate.py', 'tests/warden_port/test_gate_render.py', 'tests/warden_port/test_gate_review2.py']
moto [group:test] map(table)=['moto'] -> imported as ['moto', 'moto.mock_aws'] in 3 files ['tests/contracts/kinds/audit_neutral.py', 'tests/test_p4_secrets.py', 'tests/warden_port/test_audit_chain.py']
pglast [group:test] map(table)=['pglast'] -> imported as ['pglast', 'pglast.ast', 'pglast.visitors', 'pglast.visitors.Visitor'] in 2 files ['tests/demo_askdata/oracle.py', 'tests/demo_askdata/test_validate_oracle.py']
pip-audit [group:scan] -> import names UNMAPPED
psycopg [extra:pg, extra:askdata] map(table)=['psycopg'] -> imported as ['psycopg', 'psycopg.conninfo', 'psycopg.conninfo.conninfo_to_dict', 'psycopg.conninfo.make_conninfo'] in 18 files ['demos/ask-your-data/askdata/pgsource.py', 'src/hadavin_sdk/store/migrate.py', 'src/hadavin_sdk/store/postgres.py']
pydantic [dependencies] map(table)=['pydantic'] -> imported as ['pydantic', 'pydantic.BaseModel', 'pydantic.BeforeValidator', 'pydantic.ConfigDict'] in 30 files ['demos/ask-your-data/askdata/config.py', 'demos/ask-your-data/askdata/evalset.py', 'demos/ask-your-data/askdata/ledger.py']
pydantic-settings [dependencies] map(table)=['pydantic_settings'] -> imported as ['pydantic_settings', 'pydantic_settings.BaseSettings', 'pydantic_settings.SettingsConfigDict'] in 1 files ['src/hadavin_sdk/config.py']
pytest [group:dev] map(table)=['pytest', '_pytest'] -> imported as ['pytest'] in 113 files ['tests/conftest.py', 'tests/contracts/conftest.py', 'tests/contracts/kinds/detectors.py']
pyyaml [dependencies] map(table)=['yaml'] -> imported as ['yaml'] in 30 files ['demos/ask-your-data/askdata/config.py', 'src/hadavin_sdk/config.py', 'src/hadavin_sdk/registry.py']
ruff [group:dev] -> import names UNMAPPED
sqlglot [extra:askdata] map(table)=['sqlglot'] -> imported as ['sqlglot', 'sqlglot.errors', 'sqlglot.errors.OptimizeError', 'sqlglot.errors.SqlglotError'] in 5 files ['demos/ask-your-data/askdata/validate.py', 'tests/demo_askdata/test_allowlist.py', 'tests/demo_askdata/test_gold_data.py']
uv_build [build-system] -> import names UNMAPPED
zizmor [group:scan] -> import names UNMAPPED

### 8b Imported third-party names NOT covered by a declared dependency mapping (top-level shown; 101 packages in uv.lock)

count: 20

azure.core.credentials (first dist-name match in uv.lock: no)
azure.core.credentials.AccessToken (first dist-name match in uv.lock: no)
azure.core.exceptions (first dist-name match in uv.lock: no)
azure.core.exceptions.ResourceExistsError (first dist-name match in uv.lock: no)
azure.core.exceptions.ResourceNotFoundError (first dist-name match in uv.lock: no)
azure.core.pipeline.transport (first dist-name match in uv.lock: no)
azure.core.pipeline.transport.RequestsTransport (first dist-name match in uv.lock: no)
google.api_core.exceptions (first dist-name match in uv.lock: no)
google.api_core.exceptions.NotFound (first dist-name match in uv.lock: no)
google.api_core.exceptions.PreconditionFailed (first dist-name match in uv.lock: no)
google.auth (first dist-name match in uv.lock: no)
google.auth.credentials (first dist-name match in uv.lock: no)
google.auth.credentials.AnonymousCredentials (first dist-name match in uv.lock: no)
google.auth.exceptions (first dist-name match in uv.lock: no)
google.auth.exceptions.DefaultCredentialsError (first dist-name match in uv.lock: no)
httpx2 (first dist-name match in uv.lock: yes)
requests (first dist-name match in uv.lock: yes)
requests.adapters (first dist-name match in uv.lock: yes)
requests.adapters.BaseAdapter (first dist-name match in uv.lock: yes)
urllib3 (first dist-name match in uv.lock: yes)

### 8c uv.lock package names that are neither declared in pyproject nor imported by top-level name (transitive candidates; list only)

count: 74

annotated-types
anyio
azure-core
boolean-py
cachecontrol
certifi
cffi
charset-normalizer
colorama
cyclonedx-python-lib
defusedxml
docstring-parser
filelock
google-api-core
google-auth
google-cloud-core
google-crc32c
google-resumable-media
googleapis-common-protos
grpc-google-iam-v1
grpcio
grpcio-status
h11
hadavin-sdk
httpcore2
httpx2-jsfetch
idna
iniconfig
isodate
jiter
jmespath
license-expression
markupsafe
mdurl
msal
msal-extensions
msgpack
opentelemetry-api
packageurl-python
packaging
pip
pip-api
pip-requirements-parser
platformdirs
pluggy
proto-plus
protobuf
psycopg-binary
py-partiql-parser
py-serializable
pyasn1
pyasn1-modules
pycparser
pydantic-core
pygments
pyjwt
pyparsing
python-dateutil
python-dotenv
responses
rich
s3transfer
six
sniffio
sortedcontainers
stevedore
tomli
tomli-w
truststore
typing-extensions
typing-inspection
tzdata
werkzeug
xmltodict

### 8d Dist names with no import-name mapping (not in site-packages, not in the written table)

count: 5

bandit
pip-audit
ruff
uv_build
zizmor

## 9 Duplicate candidates

### 9a Exact AST-hash equal function bodies (>= 6 statements, docstring removed, argument names kept)

(none found)

### 9b Function pairs with difflib ratio >= 0.80 on ast.dump text, bodies >= 6 statements (pairs compared across all src and demos functions; 454 functions; 15s)

count: 14

src/hadavin_sdk/backends/table.py:356 _vertex_host <-> src/hadavin_sdk/llm/anthropic.py:26 _vertex_base_url ratio=0.960 stmts=6/6
src/hadavin_sdk/runtime/evidence.py:165 make_validator <-> src/hadavin_sdk/runtime/evidence.py:175 validate ratio=0.936 stmts=22/18
src/hadavin_sdk/guard/redact.py:1111 _trie_regex <-> src/hadavin_sdk/guard/redact.py:1114 build ratio=0.934 stmts=14/11
src/hadavin_sdk/app.py:399 _switched_off <-> src/hadavin_sdk/app.py:403 why ratio=0.898 stmts=11/8
src/hadavin_sdk/approvals/receiver.py:40 serve <-> src/hadavin_sdk/approvals/receiver.py:44 do_POST ratio=0.871 stmts=19/13
demos/ask-your-data/askdata/meter.py:72 _try_lock <-> demos/ask-your-data/askdata/meter.py:89 _unlock ratio=0.870 stmts=10/6
src/hadavin_sdk/guard/runmap.py:541 _redact_value <-> src/hadavin_sdk/guard/runmap.py:560 restore_value ratio=0.869 stmts=7/7
demos/ask-your-data/askdata/meter.py:221 settle <-> demos/ask-your-data/askdata/meter.py:231 charge ratio=0.864 stmts=8/9
src/hadavin_sdk/audit/signer_aws.py:39 public_key <-> src/hadavin_sdk/audit/signer_gcp.py:43 public_key ratio=0.863 stmts=7/7
src/hadavin_sdk/guard/runmap.py:531 _chars <-> src/hadavin_sdk/guard/runmap.py:570 has_placeholder ratio=0.861 stmts=7/8
demos/ask-your-data/askdata/evalset.py:153 write_lock <-> src/hadavin_sdk/k1b/atomic.py:9 atomic_write ratio=0.834 stmts=7/7
src/hadavin_sdk/guard/runmap.py:531 _chars <-> src/hadavin_sdk/guard/runmap.py:560 restore_value ratio=0.817 stmts=7/7
src/hadavin_sdk/guard/runmap.py:531 _chars <-> src/hadavin_sdk/guard/runmap.py:541 _redact_value ratio=0.813 stmts=7/7
demos/ask-your-data/db/lumen.py:716 sql_statements <-> demos/ask-your-data/db/seed.py:117 sql_statements ratio=0.811 stmts=6/6

### 9c Same-named public functions/classes in different files (src and demos)

count: 34

Answer: demos/ask-your-data/askdata/pipeline.py:59; src/hadavin_sdk/k1b/score.py:57; src/hadavin_sdk/llm/common.py:184
Budget: demos/ask-your-data/askdata/ledger.py:81; src/hadavin_sdk/k1b/loop.py:40; src/hadavin_sdk/registry.py:33
Config: demos/ask-your-data/askdata/evalrun.py:114; src/hadavin_sdk/config.py:316
ConfigError: demos/ask-your-data/askdata/config.py:21; src/hadavin_sdk/errors.py:4
Executor: demos/ask-your-data/askdata/pipeline.py:37; src/hadavin_sdk/actions/executor.py:47
KillSwitch: demos/ask-your-data/askdata/meter.py:253; src/hadavin_sdk/models.py:251
Limits: demos/ask-your-data/askdata/config.py:47; demos/ask-your-data/askdata/pgsource.py:52; src/hadavin_sdk/limits.py:13
Rng: demos/ask-your-data/db/lumen.py:337; demos/ask-your-data/db/seed.py:28
RunResult: demos/ask-your-data/askdata/pgsource.py:60; src/hadavin_sdk/models.py:310
Settings: demos/ask-your-data/askdata/pipeline.py:44; src/hadavin_sdk/config.py:311
build: demos/ask-your-data/db/build_verify.py:32; demos/ask-your-data/db/lumen.py:481; src/hadavin_sdk/actions/secrets_aws.py:41; src/hadavin_sdk/actions/secrets_azure.py:42; src/hadavin_sdk/actions/secrets_env.py:32; src/hadavin_sdk/actions/secrets_file.py:68; src/hadavin_sdk/actions/secrets_gcp.py:48; src/hadavin_sdk/actions/secrets_vault.py:152; src/hadavin_sdk/app.py:62; src/hadavin_sdk/approvals/slack_channel.py:206; src/hadavin_sdk/audit/anchor_azure.py:70; src/hadavin_sdk/audit/anchor_gcs.py:58; src/hadavin_sdk/audit/anchor_s3.py:84; src/hadavin_sdk/audit/chain.py:518; src/hadavin_sdk/audit/signer_aws.py:51; src/hadavin_sdk/audit/signer_azure.py:53; src/hadavin_sdk/audit/signer_gcp.py:53; src/hadavin_sdk/audit/signer_vault.py:77; src/hadavin_sdk/store/postgres.py:152
canonical: demos/ask-your-data/data/goldcheck.py:99; src/hadavin_sdk/guard/runmap.py:229
check: src/hadavin_sdk/backends/platform_secrets.py:36; src/hadavin_sdk/deferred.py:46; src/hadavin_sdk/runtime/runs.py:29
clean: demos/ask-your-data/askdata/safe_text.py:37; src/hadavin_sdk/approvals/channel.py:18
connect: src/hadavin_sdk/actions/secrets_vault.py:162; src/hadavin_sdk/store/postgres.py:125
decide: .claude/hooks/agent_preamble_gate.py:32; demos/ask-your-data/askdata/policy.py:108
describe: demos/ask-your-data/askdata/validate.py:626; src/hadavin_sdk/llm/retry.py:77
digest: demos/ask-your-data/askdata/fixtures.py:69; demos/ask-your-data/data/goldcheck.py:103
floating: src/hadavin_sdk/llm/anthropic.py:63; src/hadavin_sdk/llm/bedrock.py:59; src/hadavin_sdk/llm/gemini.py:23; src/hadavin_sdk/llm/openai_compat.py:40
gate: demos/ask-your-data/askdata/cli.py:70; src/hadavin_sdk/evals.py:35
literal: demos/ask-your-data/db/lumen.py:694; demos/ask-your-data/db/seed.py:101
load_config: demos/ask-your-data/askdata/config.py:80; src/hadavin_sdk/config.py:436
main: .claude/hooks/agent_preamble_gate.py:71; demos/ask-your-data/askdata/cli.py:228; demos/ask-your-data/askdata/derive_allowlist.py:61; demos/ask-your-data/askdata/evalcli.py:230; demos/ask-your-data/askdata/opscli.py:195; demos/ask-your-data/data/goldcheck.py:551; demos/ask-your-data/db/build_verify.py:38; demos/ask-your-data/db/lumen.py:731; src/hadavin_sdk/cli.py:70
make: src/hadavin_sdk/backends/factory.py:29; src/hadavin_sdk/guard/bedrock_guardrail.py:61; src/hadavin_sdk/guard/judge.py:39; src/hadavin_sdk/llm/anthropic.py:80; src/hadavin_sdk/llm/bedrock.py:42; src/hadavin_sdk/llm/gemini.py:31; src/hadavin_sdk/llm/openai_compat.py:52
norm: demos/ask-your-data/askdata/compare.py:25; src/hadavin_sdk/k1b/causelist.py:22
normalise: demos/ask-your-data/data/goldcheck.py:458; src/hadavin_sdk/approvals/gate.py:200; src/hadavin_sdk/runtime/evidence.py:56
out: demos/ask-your-data/askdata/cli.py:29; demos/ask-your-data/askdata/opscli.py:31
probed: src/hadavin_sdk/audit/anchor_azure.py:83; src/hadavin_sdk/audit/anchor_gcs.py:69
render: demos/ask-your-data/askdata/prompt.py:38; src/hadavin_sdk/k1b/tools.py:230
result_hash: demos/ask-your-data/askdata/compare.py:127; demos/ask-your-data/data/goldcheck.py:464
retryable: src/hadavin_sdk/llm/anthropic.py:67; src/hadavin_sdk/llm/bedrock.py:104
sql_statements: demos/ask-your-data/db/lumen.py:716; demos/ask-your-data/db/seed.py:117
verify: demos/ask-your-data/askdata/audit.py:115; src/hadavin_sdk/approvals/hmac_v0.py:37; src/hadavin_sdk/approvals/slack.py:18
worst_case_usd: demos/ask-your-data/askdata/meter.py:48; src/hadavin_sdk/k1b/loop.py:115

### 9d Duplicate regex literals (passed to re.*, >= 12 chars) appearing in 2 or more files

count: 2

'[a-z0-9_-]{1,40}' in 2 files: src/hadavin_sdk/actions/contract.py:44; src/hadavin_sdk/config.py:251
'[0-9a-f]{64}' in 2 files: src/hadavin_sdk/config.py:299; src/hadavin_sdk/k1b/bundle.py:212

### 9e Duplicate string literals (>= 12 chars, not docstrings, not regexes) appearing in 2 or more files (src and demos)

count: 122

'execution_failed' in 2 files: demos/ask-your-data/askdata/pipeline.py:281; demos/ask-your-data/askdata/pipeline.py:295; demos/ask-your-data/askdata/pipeline.py:354; demos/ask-your-data/askdata/policy.py:100
'gold_sql_alt' in 2 files: demos/ask-your-data/askdata/derive_allowlist.py:31; demos/ask-your-data/data/goldcheck.py:178; demos/ask-your-data/data/goldcheck.py:183; demos/ask-your-data/data/goldcheck.py:220
'input_schema' in 8 files: src/hadavin_sdk/actions/contract.py:118; src/hadavin_sdk/evals.py:52; src/hadavin_sdk/k1b/tools.py:31; src/hadavin_sdk/k1b/tools.py:71
'out_of_scope' in 5 files: demos/ask-your-data/askdata/evalset.py:26; demos/ask-your-data/askdata/llm_io.py:41; demos/ask-your-data/askdata/pipeline.py:109; demos/ask-your-data/askdata/policy.py:15
'tool module ' in 2 files: src/hadavin_sdk/registry.py:323; src/hadavin_sdk/registry.py:333; src/hadavin_sdk/tools.py:255; src/hadavin_sdk/tools.py:269
'data_injection' in 3 files: demos/ask-your-data/askdata/evalrun.py:322; demos/ask-your-data/askdata/evalset.py:78; demos/ask-your-data/data/goldcheck.py:337; demos/ask-your-data/data/goldcheck.py:344
'additionalProperties' in 5 files: demos/ask-your-data/askdata/llm_io.py:62; src/hadavin_sdk/actions/contract.py:112; src/hadavin_sdk/actions/contract.py:145; src/hadavin_sdk/actions/contract.py:180
'external_usd' in 2 files: demos/ask-your-data/askdata/meter.py:125; demos/ask-your-data/askdata/meter.py:132; demos/ask-your-data/askdata/meter.py:176; demos/ask-your-data/askdata/meter.py:181
'prompt_sha256' in 7 files: demos/ask-your-data/askdata/config.py:101; demos/ask-your-data/askdata/evalcli.py:104; demos/ask-your-data/askdata/evalrun.py:508; demos/ask-your-data/askdata/htmlexport.py:86
'confident_wrong' in 2 files: demos/ask-your-data/askdata/evalrun.py:410; demos/ask-your-data/askdata/evalrun.py:482; demos/ask-your-data/askdata/evalrun.py:555; demos/ask-your-data/askdata/evalrun.py:561
'canonical_sql' in 4 files: demos/ask-your-data/askdata/evalrun.py:441; demos/ask-your-data/askdata/evalrun.py:66; demos/ask-your-data/askdata/htmlexport.py:56; demos/ask-your-data/askdata/htmlexport.py:67
'external_updated_at' in 2 files: demos/ask-your-data/askdata/meter.py:125; demos/ask-your-data/askdata/meter.py:137; demos/ask-your-data/askdata/meter.py:182; demos/ask-your-data/askdata/meter.py:199
'injection_suspected' in 6 files: demos/ask-your-data/askdata/pipeline.py:113; demos/ask-your-data/askdata/policy.py:14; demos/ask-your-data/askdata/policy.py:34; src/hadavin_sdk/guard/bedrock_guardrail.py:113
'audit_unavailable' in 3 files: demos/ask-your-data/askdata/pipeline.py:262; demos/ask-your-data/askdata/policy.py:16; demos/ask-your-data/askdata/policy.py:46; demos/ask-your-data/askdata/policy.py:60
'manifest.json' in 2 files: demos/ask-your-data/data/goldcheck.py:116; demos/ask-your-data/data/goldcheck.py:117; demos/ask-your-data/data/goldcheck.py:554; src/hadavin_sdk/k1b/bundle.py:191
'application/json' in 5 files: src/hadavin_sdk/actions/executor.py:75; src/hadavin_sdk/actions/secrets_vault.py:73; src/hadavin_sdk/audit/anchor_gcs.py:44; src/hadavin_sdk/llm/common.py:260
'InputTooLarge' in 2 files: src/hadavin_sdk/guard/runmap.py:130; src/hadavin_sdk/guard/runmap.py:155; src/hadavin_sdk/guard/runmap.py:395; src/hadavin_sdk/guard/runmap.py:450
'hard_check_a' in 3 files: src/hadavin_sdk/k1b/replay.py:186; src/hadavin_sdk/k1b/replay.py:191; src/hadavin_sdk/k1b/replay.py:225; src/hadavin_sdk/k1b/replay.py:44
'approval_requests' in 2 files: src/hadavin_sdk/store/migrate.py:50; src/hadavin_sdk/store/postgres.py:311; src/hadavin_sdk/store/postgres.py:314; src/hadavin_sdk/store/postgres.py:331
'upper_error_bound' in 2 files: demos/ask-your-data/askdata/evalrun.py:409; demos/ask-your-data/askdata/evalrun.py:483; demos/ask-your-data/askdata/evalrun.py:562; demos/ask-your-data/askdata/htmlexport.py:96
'direct_write' in 2 files: demos/ask-your-data/askdata/evalset.py:78; demos/ask-your-data/data/goldcheck.py:312; demos/ask-your-data/data/goldcheck.py:354; demos/ask-your-data/data/goldcheck.py:355
'model_followed_injection' in 2 files: demos/ask-your-data/askdata/evalcli.py:188; demos/ask-your-data/askdata/evalrun.py:395; demos/ask-your-data/askdata/evalrun.py:446; demos/ask-your-data/askdata/evalrun.py:556
'resource_abuse' in 2 files: demos/ask-your-data/askdata/evalset.py:78; demos/ask-your-data/data/goldcheck.py:312; demos/ask-your-data/data/goldcheck.py:355; demos/ask-your-data/data/goldcheck.py:57
'restricted_data' in 3 files: demos/ask-your-data/askdata/llm_io.py:41; demos/ask-your-data/askdata/pipeline.py:111; demos/ask-your-data/askdata/policy.py:14; demos/ask-your-data/askdata/policy.py:33
'schema_violation' in 2 files: demos/ask-your-data/askdata/pipeline.py:199; demos/ask-your-data/askdata/pipeline.py:201; demos/ask-your-data/askdata/policy.py:16; demos/ask-your-data/askdata/policy.py:44
'unsafe_query' in 2 files: demos/ask-your-data/askdata/pipeline.py:223; demos/ask-your-data/askdata/policy.py:16; demos/ask-your-data/askdata/policy.py:41; demos/ask-your-data/askdata/policy.py:61
'input.unresolved' in 3 files: src/hadavin_sdk/actions/authorizer.py:40; src/hadavin_sdk/approvals/cards.py:47; src/hadavin_sdk/runtime/agent_loop.py:616; src/hadavin_sdk/runtime/agent_loop.py:794
'needs_approval' in 4 files: src/hadavin_sdk/actions/authorizer.py:49; src/hadavin_sdk/actions/executor.py:111; src/hadavin_sdk/models.py:86; src/hadavin_sdk/runtime/agent_loop.py:709
'card_too_long' in 3 files: src/hadavin_sdk/app.py:188; src/hadavin_sdk/app.py:196; src/hadavin_sdk/approvals/slack_channel.py:164; src/hadavin_sdk/runtime/agent_loop.py:719
'uncited_conversions' in 3 files: src/hadavin_sdk/k1b/replay.py:209; src/hadavin_sdk/k1b/replay.py:43; src/hadavin_sdk/k1b/report.py:104; src/hadavin_sdk/k1b/score.py:295
'bundle_set_sha256' in 3 files: src/hadavin_sdk/k1b/replay.py:238; src/hadavin_sdk/k1b/report.py:114; src/hadavin_sdk/k1b/report.py:219; src/hadavin_sdk/k1b/score.py:250
': operation ' in 2 files: src/hadavin_sdk/registry.py:296; src/hadavin_sdk/registry.py:301; src/hadavin_sdk/tools.py:434; src/hadavin_sdk/tools.py:437
'%Y-%m-%dT%H:%M:%SZ' in 4 files: demos/ask-your-data/askdata/compare.py:39; demos/ask-your-data/askdata/ledger.py:117; demos/ask-your-data/askdata/meter.py:34; demos/ask-your-data/db/lumen.py:657
'golden_sha256' in 2 files: demos/ask-your-data/askdata/evalcli.py:106; demos/ask-your-data/askdata/evalrun.py:508; demos/ask-your-data/askdata/evalrun.py:543
'verdict_text' in 3 files: demos/ask-your-data/askdata/evalcli.py:175; demos/ask-your-data/askdata/evalrun.py:411; demos/ask-your-data/askdata/evalrun.py:487; demos/ask-your-data/askdata/htmlexport.py:91
'write_request' in 2 files: demos/ask-your-data/askdata/llm_io.py:41; demos/ask-your-data/askdata/policy.py:14; demos/ask-your-data/askdata/policy.py:32; demos/ask-your-data/askdata/policy.py:53
'insufficient_schema' in 2 files: demos/ask-your-data/askdata/llm_io.py:41; demos/ask-your-data/askdata/policy.py:15; demos/ask-your-data/askdata/policy.py:39; demos/ask-your-data/askdata/policy.py:55
'model_unavailable' in 2 files: demos/ask-your-data/askdata/pipeline.py:176; demos/ask-your-data/askdata/policy.py:16; demos/ask-your-data/askdata/policy.py:45; demos/ask-your-data/askdata/policy.py:60
'Authorization' in 4 files: src/hadavin_sdk/actions/executor.py:74; src/hadavin_sdk/app.py:340; src/hadavin_sdk/approvals/slack_channel.py:54; src/hadavin_sdk/llm/openai_compat.py:92
'Content-Type' in 4 files: src/hadavin_sdk/actions/executor.py:75; src/hadavin_sdk/actions/secrets_vault.py:73; src/hadavin_sdk/llm/common.py:260; src/hadavin_sdk/sources/kubernetes.py:34
'total_max_attempts' in 4 files: src/hadavin_sdk/audit/anchor_s3.py:88; src/hadavin_sdk/audit/signer_aws.py:53; src/hadavin_sdk/guard/bedrock_guardrail.py:36; src/hadavin_sdk/llm/bedrock.py:51
'bedrock-runtime' in 3 files: src/hadavin_sdk/backends/table.py:527; src/hadavin_sdk/backends/table.py:555; src/hadavin_sdk/guard/bedrock_guardrail.py:66; src/hadavin_sdk/llm/bedrock.py:44
'replay_run_id' in 2 files: src/hadavin_sdk/k1b/replay.py:232; src/hadavin_sdk/k1b/score.py:309; src/hadavin_sdk/k1b/score.py:326; src/hadavin_sdk/k1b/score.py:36
'cause_services_sha256' in 3 files: src/hadavin_sdk/k1b/replay.py:239; src/hadavin_sdk/k1b/report.py:218; src/hadavin_sdk/k1b/score.py:248; src/hadavin_sdk/k1b/score.py:327
'cause_fault_types_sha256' in 3 files: src/hadavin_sdk/k1b/replay.py:240; src/hadavin_sdk/k1b/report.py:218; src/hadavin_sdk/k1b/score.py:249; src/hadavin_sdk/k1b/score.py:328
'returned_ids' in 2 files: src/hadavin_sdk/k1b/replay.py:213; src/hadavin_sdk/k1b/score.py:180; src/hadavin_sdk/k1b/score.py:181; src/hadavin_sdk/k1b/score.py:285
'harness_defect' in 2 files: demos/ask-your-data/askdata/evalcli.py:237; demos/ask-your-data/askdata/evalset.py:132; demos/ask-your-data/askdata/evalset.py:134
'refused_no_exec' in 3 files: demos/ask-your-data/askdata/evalrun.py:345; demos/ask-your-data/askdata/evalset.py:83; demos/ask-your-data/data/goldcheck.py:56
'no_restricted_value' in 3 files: demos/ask-your-data/askdata/evalrun.py:347; demos/ask-your-data/askdata/evalset.py:84; demos/ask-your-data/data/goldcheck.py:56
'no_unsafe_statement' in 3 files: demos/ask-your-data/askdata/evalrun.py:349; demos/ask-your-data/askdata/evalset.py:85; demos/ask-your-data/data/goldcheck.py:57
'bounded_resources' in 3 files: demos/ask-your-data/askdata/evalrun.py:351; demos/ask-your-data/askdata/evalset.py:86; demos/ask-your-data/data/goldcheck.py:57
'readonly_violation' in 2 files: demos/ask-your-data/askdata/evalrun.py:437; demos/ask-your-data/askdata/policy.py:18; demos/ask-your-data/askdata/policy.py:96
'answers_match_clean' in 2 files: demos/ask-your-data/askdata/evalset.py:87; demos/ask-your-data/askdata/evalset.py:94; demos/ask-your-data/data/goldcheck.py:58
'askdata_spent' in 3 files: demos/ask-your-data/askdata/meter.py:180; demos/ask-your-data/askdata/opscli.py:162; demos/ask-your-data/askdata/pipeline.py:337
' is not an exposed view' in 2 files: demos/ask-your-data/askdata/validate.py:322; demos/ask-your-data/askdata/validate.py:324; demos/ask-your-data/data/goldcheck.py:159
'@example.com' in 3 files: demos/ask-your-data/data/goldcheck.py:342; demos/ask-your-data/db/lumen.py:590; demos/ask-your-data/db/seed.py:57
'confidential' in 3 files: src/hadavin_sdk/actions/contract.py:92; src/hadavin_sdk/deferred.py:64; src/hadavin_sdk/registry.py:43
'AZURERESOURCE' in 3 files: src/hadavin_sdk/defaults.py:112; src/hadavin_sdk/guard/redact.py:176; src/hadavin_sdk/guard/runmap.py:177
'guard_unavailable' in 2 files: src/hadavin_sdk/guard/injection.py:101; src/hadavin_sdk/guard/judge.py:108; src/hadavin_sdk/guard/judge.py:85
'<SECRET_REDACTED>' in 2 files: src/hadavin_sdk/k1b/redaction.py:86; src/hadavin_sdk/tools.py:722; src/hadavin_sdk/tools.py:766
'outputs.sha256' in 2 files: src/hadavin_sdk/k1b/replay.py:261; src/hadavin_sdk/k1b/score.py:227; src/hadavin_sdk/k1b/score.py:33
'invalid_proposal' in 2 files: src/hadavin_sdk/runtime/agent_loop.py:666; src/hadavin_sdk/runtime/agent_loop.py:84; src/hadavin_sdk/runtime/evidence.py:188
'gate_decisions' in 2 files: src/hadavin_sdk/store/migrate.py:49; src/hadavin_sdk/store/postgres.py:301; src/hadavin_sdk/store/postgres.py:306
'approval_decisions' in 2 files: src/hadavin_sdk/store/migrate.py:51; src/hadavin_sdk/store/postgres.py:385; src/hadavin_sdk/store/postgres.py:392
'dead_letters' in 2 files: src/hadavin_sdk/store/migrate.py:52; src/hadavin_sdk/store/postgres.py:411; src/hadavin_sdk/store/postgres.py:414
'order_items_v' in 2 files: demos/ask-your-data/askdata/allowed.py:19; demos/ask-your-data/data/goldcheck.py:84
'order_item_id' in 2 files: demos/ask-your-data/askdata/allowed.py:20; demos/ask-your-data/db/lumen.py:330
'dataset_contract.json' in 2 files: demos/ask-your-data/askdata/allowed.py:67; demos/ask-your-data/data/goldcheck.py:115
'sql_generate' in 2 files: demos/ask-your-data/askdata/config.py:40; demos/ask-your-data/askdata/pipeline.py:45
'exemplars.jsonl' in 2 files: demos/ask-your-data/askdata/derive_allowlist.py:34; demos/ask-your-data/data/goldcheck.py:114
'adversarial.dev.jsonl' in 2 files: demos/ask-your-data/askdata/evalcli.py:45; demos/ask-your-data/data/goldcheck.py:113
'adversarial.jsonl' in 2 files: demos/ask-your-data/askdata/evalcli.py:46; demos/ask-your-data/data/goldcheck.py:112
'ASKDATA_CONFIG' in 2 files: demos/ask-your-data/askdata/evalcli.py:253; demos/ask-your-data/askdata/opscli.py:226
'startup: give --config or set '... <len=44 sha1=ec896596> in 2 files: demos/ask-your-data/askdata/evalcli.py:255; demos/ask-your-data/askdata/opscli.py:228
'claimed:eval' in 2 files: demos/ask-your-data/askdata/evalcli.py:88; demos/ask-your-data/askdata/evalrun.py:266
'^[0-9a-f]{64}$' in 2 files: demos/ask-your-data/askdata/evalset.py:25; demos/ask-your-data/askdata/ledger.py:34
'input_tokens' in 2 files: demos/ask-your-data/askdata/fixtures.py:63; src/hadavin_sdk/llm/fake.py:51
'output_tokens' in 2 files: demos/ask-your-data/askdata/fixtures.py:64; src/hadavin_sdk/llm/fake.py:52
'submit_answer' in 2 files: demos/ask-your-data/askdata/fixtures.py:58; src/hadavin_sdk/llm/common.py:24
'verify_checks.sql' in 2 files: demos/ask-your-data/askdata/pgsource.py:38; demos/ask-your-data/db/build_verify.py:11
'hash_mismatch' in 2 files: demos/ask-your-data/askdata/pipeline.py:280; demos/ask-your-data/askdata/policy.py:18
'[1A local integrity check: 41 '... <len=48 sha1=764e0883> in 2 files: demos/ask-your-data/db/lumen.py:306; demos/ask-your-data/db/seed.py:25
'INSERT INTO shop.' in 2 files: demos/ask-your-data/db/lumen.py:723; demos/ask-your-data/db/seed.py:122
'class.read_only' in 2 files: src/hadavin_sdk/actions/authorizer.py:50; src/hadavin_sdk/approvals/cards.py:42
'scope.principal' in 2 files: src/hadavin_sdk/actions/authorizer.py:37; src/hadavin_sdk/approvals/cards.py:45
'input.schema' in 2 files: src/hadavin_sdk/actions/authorizer.py:42; src/hadavin_sdk/approvals/cards.py:46
'class.reversible' in 2 files: src/hadavin_sdk/actions/authorizer.py:49; src/hadavin_sdk/approvals/cards.py:43
' is outside check_modules' in 2 files: src/hadavin_sdk/actions/executor.py:36; src/hadavin_sdk/registry.py:378
'plan_hash_mismatch' in 2 files: src/hadavin_sdk/actions/executor.py:110; src/hadavin_sdk/approvals/requests.py:161
'secretsmanager' in 2 files: src/hadavin_sdk/actions/secrets_aws.py:42; src/hadavin_sdk/backends/table.py:397
'Vault answered with an unexpec'... <len=44 sha1=acf594a1> in 2 files: src/hadavin_sdk/actions/secrets_vault.py:133; src/hadavin_sdk/audit/signer_vault.py:47
': Vault answered ' in 2 files: src/hadavin_sdk/actions/secrets_vault.py:119; src/hadavin_sdk/audit/signer_vault.py:43
'class.sign_off.' in 2 files: src/hadavin_sdk/approvals/cards.py:53; src/hadavin_sdk/runtime/agent_loop.py:615
'bad_signature' in 2 files: src/hadavin_sdk/approvals/receiver.py:34; src/hadavin_sdk/approvals/requests.py:78
'https://slack.com/api' in 2 files: src/hadavin_sdk/approvals/slack_channel.py:26; src/hadavin_sdk/backends/table.py:324
'audit_entries' in 2 files: src/hadavin_sdk/audit/chain.py:60; src/hadavin_sdk/store/migrate.py:57
'audit_checkpoints' in 2 files: src/hadavin_sdk/audit/chain.py:60; src/hadavin_sdk/store/migrate.py:58
'SELECT pg_advisory_xact_lock(%s)' in 2 files: src/hadavin_sdk/audit/chain.py:120; src/hadavin_sdk/store/migrate.py:314
'ed25519_local' in 2 files: src/hadavin_sdk/backends/table.py:429; src/hadavin_sdk/config.py:395
'openai_compat' in 2 files: src/hadavin_sdk/backends/table.py:529; src/hadavin_sdk/llm/openai_compat.py:75
'bedrock_guardrail' in 2 files: src/hadavin_sdk/backends/table.py:549; src/hadavin_sdk/guard/bedrock_guardrail.py:89
'cluster_ports' in 2 files: src/hadavin_sdk/config.py:270; src/hadavin_sdk/tools.py:1069
'source kind ' in 2 files: src/hadavin_sdk/config.py:293; src/hadavin_sdk/sources/kinds.py:59
' is not available until ' in 2 files: src/hadavin_sdk/deferred.py:40; src/hadavin_sdk/tools.py:113
'Process the attached request document.' in 2 files: src/hadavin_sdk/evals.py:22; src/hadavin_sdk/runtime/agent_loop.py:59
'qualified.jsonl' in 2 files: src/hadavin_sdk/evals.py:23; src/hadavin_sdk/runtime/agent_loop.py:102
'injection_check' in 2 files: src/hadavin_sdk/guard/__init__.py:12; src/hadavin_sdk/guard/producers.py:33
'service_label' in 2 files: src/hadavin_sdk/k1b/bundle.py:44; src/hadavin_sdk/k1b/redaction.py:65
'deploys.json#' in 2 files: src/hadavin_sdk/k1b/bundle.py:322; src/hadavin_sdk/k1b/tools.py:178
' is missing or not valid JSON' in 2 files: src/hadavin_sdk/k1b/causelist.py:47; src/hadavin_sdk/k1b/score.py:169
'provider_exhausted' in 2 files: src/hadavin_sdk/k1b/loop.py:174; src/hadavin_sdk/runtime/agent_loop.py:436
'replay-report.md' in 2 files: src/hadavin_sdk/k1b/replay.py:262; src/hadavin_sdk/k1b/score.py:33
'distinct_values_masked' in 2 files: src/hadavin_sdk/k1b/replay.py:248; src/hadavin_sdk/k1b/report.py:73
'cases_with_masking' in 2 files: src/hadavin_sdk/k1b/replay.py:249; src/hadavin_sdk/k1b/report.py:80
'off_acknowledged' in 2 files: src/hadavin_sdk/k1b/replay.py:244; src/hadavin_sdk/k1b/score.py:258
'max_completion_tokens' in 2 files: src/hadavin_sdk/llm/openai_compat.py:60; src/hadavin_sdk/registry.py:146
': its source hash is ' in 2 files: src/hadavin_sdk/registry.py:333; src/hadavin_sdk/tools.py:370
'..., the pin says ' in 2 files: src/hadavin_sdk/registry.py:333; src/hadavin_sdk/tools.py:370
'run exists: ' in 2 files: src/hadavin_sdk/store/memory.py:54; src/hadavin_sdk/store/postgres.py:242
'gate decision exists: ' in 2 files: src/hadavin_sdk/store/memory.py:116; src/hadavin_sdk/store/postgres.py:303
'decision exists: ' in 2 files: src/hadavin_sdk/store/memory.py:172; src/hadavin_sdk/store/postgres.py:387
'tool call exists: ' in 2 files: src/hadavin_sdk/store/memory.py:238; src/hadavin_sdk/store/postgres.py:479

### 9f Demo module (demos/ask-your-data/askdata) -> best three line-level difflib ratios against the R5 core pair list

count: 24

demos/ask-your-data/askdata/__init__.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/__main__.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/allowed.py | best 3 line-level ratios: src/hadavin_sdk/guard/injection.py 0.144; src/hadavin_sdk/scrub_settings.py 0.122; src/hadavin_sdk/guard/redact.py 0.023
demos/ask-your-data/askdata/audit.py | best 3 line-level ratios: src/hadavin_sdk/audit/local_dir.py 0.126; src/hadavin_sdk/audit/chain.py 0.089
demos/ask-your-data/askdata/cli.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/compare.py | best 3 line-level ratios: src/hadavin_sdk/llm/anthropic.py 0.181; src/hadavin_sdk/llm/bedrock.py 0.156; src/hadavin_sdk/llm/openai_compat.py 0.139
demos/ask-your-data/askdata/config.py | best 3 line-level ratios: src/hadavin_sdk/config.py 0.104; src/hadavin_sdk/defaults.py 0.103
demos/ask-your-data/askdata/derive_allowlist.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/evalcli.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/evalrun.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/evalset.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/fixtures.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/htmlexport.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/ledger.py | best 3 line-level ratios: src/hadavin_sdk/audit/signer.py 0.192; src/hadavin_sdk/audit/anchors.py 0.133; src/hadavin_sdk/audit/protocol.py 0.128
demos/ask-your-data/askdata/llm_io.py | best 3 line-level ratios: src/hadavin_sdk/llm/retry.py 0.191; src/hadavin_sdk/llm/openai_compat.py 0.156; src/hadavin_sdk/llm/anthropic.py 0.156
demos/ask-your-data/askdata/meter.py | best 3 line-level ratios: src/hadavin_sdk/audit/signer.py 0.134; src/hadavin_sdk/audit/local_dir.py 0.113; src/hadavin_sdk/audit/anchors.py 0.097
demos/ask-your-data/askdata/opscli.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/pgsource.py | best 3 line-level ratios: src/hadavin_sdk/sources/__init__.py 0.163; src/hadavin_sdk/sources/kubernetes.py 0.125; src/hadavin_sdk/sources/kinds.py 0.112
demos/ask-your-data/askdata/pipeline.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/policy.py | best 3 line-level ratios: src/hadavin_sdk/guard/injection.py 0.170; src/hadavin_sdk/guard/http.py 0.162; src/hadavin_sdk/guard/bedrock_guardrail.py 0.160
demos/ask-your-data/askdata/prompt.py | best 3 line-level ratios: src/hadavin_sdk/llm/protocol.py 0.217; src/hadavin_sdk/llm/retry.py 0.198; src/hadavin_sdk/llm/fake.py 0.186
demos/ask-your-data/askdata/safe_text.py | best 3 line-level ratios: src/hadavin_sdk/scrub_settings.py 0.243; src/hadavin_sdk/guard/injection.py 0.188; src/hadavin_sdk/guard/redact.py 0.023
demos/ask-your-data/askdata/spike_llm.py | no core counterpart: not in the R5 pair list
demos/ask-your-data/askdata/validate.py | best 3 line-level ratios: src/hadavin_sdk/guard/redact.py 0.072; src/hadavin_sdk/guard/injection.py 0.059; src/hadavin_sdk/scrub_settings.py 0.028

### 9g Parity table of secrets_*, signer_*, anchor_* kinds: public names per member and test files that name each

count: 23

## family secrets: members ['secrets_aws.py', 'secrets_azure.py', 'secrets_cache.py', 'secrets_env.py', 'secrets_file.py', 'secrets_gcp.py', 'secrets_vault.py'] base files ['secrets.py']
- src/hadavin_sdk/actions/secrets_aws.py classes=['SecretsManagerProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:connect', 'get', 'var'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p4_secrets.py', 'tests/test_p4b_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_azure.py classes=['AzureKeyVaultProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:connect', 'get', 'var'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p4b_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_cache.py classes=['CachedSecrets'] | lacks (vs union of family public names): ['authed', 'call', 'fn:build', 'fn:connect', 'var'] | test files naming the module or its classes: ['tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_env.py classes=['EnvSecretProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:connect'] | test files naming the module or its classes: ['tests/test_p4_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_file.py classes=['MountedFileProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:connect', 'get', 'var'] | test files naming the module or its classes: ['tests/test_p4b_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_gcp.py classes=['GcpSecretManagerProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:connect', 'get', 'var'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p4b_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets_vault.py classes=['VaultError', 'VaultProvider'] | lacks (vs union of family public names): ['get', 'var'] | test files naming the module or its classes: ['tests/test_k5_round5.py', 'tests/test_p4b_secrets.py', 'tests/test_repo_rules.py']
- src/hadavin_sdk/actions/secrets.py classes=['SecretProvider', 'FakeSecretProvider'] | lacks (vs union of family public names): ['authed', 'call', 'fn:build', 'fn:connect', 'var'] | test files naming the module or its classes: ['tests/contracts/test_capabilities.py', 'tests/contracts/test_secrets.py', 'tests/contracts/test_sources.py', 'tests/demo_askdata/test_gold_exec.py', 'tests/demo_askdata/test_seed.py', 'tests/demo_askdata/test_validate_harm.py', 'tests/demo_askdata/test_verify_readonly.py', 'tests/test_cuj.py']
## family signer: members ['signer_aws.py', 'signer_azure.py', 'signer_gcp.py', 'signer_vault.py'] base files ['anchors.py', 'protocol.py', 'signer.py']
- src/hadavin_sdk/audit/signer_aws.py classes=['KmsSigner'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:build_local', 'fn:generate_key', 'fn:key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:parse', 'fn:probe'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py', 'tests/warden_port/test_audit_chain.py']
- src/hadavin_sdk/audit/signer_azure.py classes=['AzureKeyVaultSigner'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:build_local', 'fn:generate_key', 'fn:key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:parse', 'fn:probe'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py']
- src/hadavin_sdk/audit/signer_gcp.py classes=['GcpKmsSigner'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:build_local', 'fn:generate_key', 'fn:key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:parse', 'fn:probe'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py']
- src/hadavin_sdk/audit/signer_vault.py classes=['VaultTransitSigner'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:build_local', 'fn:generate_key', 'fn:key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:parse', 'fn:probe'] | test files naming the module or its classes: ['tests/test_p3b_neutral_audit.py']
- src/hadavin_sdk/audit/anchors.py classes=['AnchorConflict'] | lacks (vs union of family public names): ['events', 'fn:build', 'fn:build_local', 'fn:generate_key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:probe', 'fn:verify_signature', 'public_key', 'reconcile'] | test files naming the module or its classes: ['tests/contracts/test_anchor.py', 'tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py', 'tests/warden_port/test_audit_chain.py']
- src/hadavin_sdk/audit/protocol.py classes=['AuditUnavailable', 'DuplicateEvent', 'AuditSink'] | lacks (vs union of family public names): ['fn:already_there', 'fn:body', 'fn:build', 'fn:build_local', 'fn:generate_key', 'fn:key', 'fn:key_dir', 'fn:key_path', 'fn:load_private_key', 'fn:load_public_key', 'fn:parse', 'fn:probe'] | test files naming the module or its classes: ['tests/contracts/test_capabilities.py', 'tests/contracts/test_sources.py', 'tests/contracts/test_store.py', 'tests/demo_askdata/test_pgsource_layers.py', 'tests/demo_askdata/test_pipeline.py', 'tests/demo_askdata/test_validate_harm.py', 'tests/test_cuj.py', 'tests/test_k1b_cli.py']
- src/hadavin_sdk/audit/signer.py classes=['Signer', 'LocalSigner'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:build', 'fn:key', 'fn:parse', 'reconcile', 'verify_object', 'write_intent', 'write_outcome'] | test files naming the module or its classes: ['tests/contracts/test_signer.py', 'tests/test_k1b_replay.py', 'tests/test_k3_pilot.py', 'tests/test_k3_pilot_env.py', 'tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py', 'tests/test_p7_tick.py', 'tests/warden_port/test_audit_chain.py']
## family anchor: members ['anchor_azure.py', 'anchor_gcs.py', 'anchor_s3.py'] base files ['anchors.py', 'protocol.py']
- src/hadavin_sdk/audit/anchor_azure.py classes=['AzureBlobAnchor'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:key', 'fn:parse', 'reconcile', 'verify_object', 'write_intent', 'write_outcome'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py']
- src/hadavin_sdk/audit/anchor_gcs.py classes=['GcsAnchor'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:key', 'fn:parse', 'reconcile', 'verify_object', 'write_intent', 'write_outcome'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py']
- src/hadavin_sdk/audit/anchor_s3.py classes=['S3Anchor'] | lacks (vs union of family public names): ['events', 'fn:already_there', 'fn:body', 'fn:key', 'fn:parse', 'fn:probed', 'reconcile', 'verify_object', 'write_intent', 'write_outcome'] | test files naming the module or its classes: ['tests/test_lockin_guard.py', 'tests/warden_port/test_audit_chain.py']
- src/hadavin_sdk/audit/anchors.py classes=['AnchorConflict'] | lacks (vs union of family public names): ['all', 'events', 'fn:build', 'fn:probed', 'put', 'reconcile', 'verify_object', 'write_intent', 'write_outcome'] | test files naming the module or its classes: ['tests/contracts/test_anchor.py', 'tests/test_lockin_guard.py', 'tests/test_p3b_neutral_audit.py', 'tests/warden_port/test_audit_chain.py']
- src/hadavin_sdk/audit/protocol.py classes=['AuditUnavailable', 'DuplicateEvent', 'AuditSink'] | lacks (vs union of family public names): ['all', 'fn:already_there', 'fn:body', 'fn:build', 'fn:key', 'fn:parse', 'fn:probed', 'put'] | test files naming the module or its classes: ['tests/contracts/test_capabilities.py', 'tests/contracts/test_sources.py', 'tests/contracts/test_store.py', 'tests/demo_askdata/test_pgsource_layers.py', 'tests/demo_askdata/test_pipeline.py', 'tests/demo_askdata/test_validate_harm.py', 'tests/test_cuj.py', 'tests/test_k1b_cli.py']

### 9h llm backends: public classes and test files that name each

count: 9

src/hadavin_sdk/llm/__init__.py classes=[] | test files naming it: ['tests/contracts/test_sources.py', 'tests/demo_askdata/test_cli.py', 'tests/demo_askdata/test_eval_harness.py', 'tests/demo_askdata/test_pipeline.py', 'tests/test_cuj.py', 'tests/test_k1a_pass_k.py', 'tests/test_k1b_replay.py', 'tests/test_k1b_score.py']
src/hadavin_sdk/llm/anthropic.py classes=['AnthropicLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/test_k1b_replay.py', 'tests/test_lockin_guard.py', 'tests/test_no_hardcoded_values.py', 'tests/test_p5_llm.py', 'tests/test_p5p6_followups.py', 'tests/test_p6_detectors.py', 'tests/warden_port/test_bedrock_provider_r16.py']
src/hadavin_sdk/llm/bedrock.py classes=['BedrockLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/test_k5_round11.py', 'tests/test_k5_round8.py', 'tests/test_k5_round9.py', 'tests/test_lockin_guard.py', 'tests/test_p1a_fixes.py', 'tests/test_p5p6_followups.py', 'tests/test_p6_detectors.py']
src/hadavin_sdk/llm/common.py classes=['Answer', 'NetworkLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/test_k3_pilot.py', 'tests/test_p5_llm.py', 'tests/test_p5p6_followups.py', 'tests/test_p6_detectors.py', 'tests/warden_port/test_bedrock_provider_r16.py', 'tests/warden_port/test_gate_render.py', 'tests/warden_port/test_gate_review2.py']
src/hadavin_sdk/llm/fake.py classes=['UnknownRecording', 'FakeLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/contracts/test_secrets.py', 'tests/contracts/test_store.py', 'tests/demo_askdata/test_audit.py', 'tests/demo_askdata/test_gold_data.py', 'tests/demo_askdata/test_llm_io.py', 'tests/demo_askdata/test_meter.py', 'tests/demo_askdata/test_pgsource_layers.py']
src/hadavin_sdk/llm/gemini.py classes=['GeminiLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/test_lockin_guard.py', 'tests/test_no_hardcoded_values.py', 'tests/test_p5_llm.py', 'tests/test_p5p6_followups.py', 'tests/warden_port/test_providers.py']
src/hadavin_sdk/llm/openai_compat.py classes=['OpenAICompatLLM'] | test files naming it: ['tests/contracts/test_llm.py', 'tests/test_k3_pilot_env.py', 'tests/test_lockin_guard.py', 'tests/test_p5_llm.py', 'tests/test_p5p6_followups.py', 'tests/warden_port/test_providers.py']
src/hadavin_sdk/llm/protocol.py classes=['ProviderError', 'ProviderExhausted', 'LLM'] | test files naming it: ['tests/contracts/test_capabilities.py', 'tests/contracts/test_llm.py', 'tests/contracts/test_sources.py', 'tests/contracts/test_store.py', 'tests/demo_askdata/test_pgsource_layers.py', 'tests/demo_askdata/test_pipeline.py', 'tests/demo_askdata/test_validate_harm.py', 'tests/test_cuj.py']
src/hadavin_sdk/llm/retry.py classes=[] | test files naming it: ['tests/contracts/test_anchor.py', 'tests/demo_askdata/test_llm_io.py', 'tests/demo_askdata/test_pipeline.py', 'tests/test_k5_round5.py', 'tests/test_p4b_secrets.py', 'tests/test_p5_llm.py', 'tests/test_p5p6_followups.py', 'tests/test_s4_llm_guard.py']

### 9i Test files whose names differ only by a number (consecutive pairs) and their ratio

count: 17

test_gate_review#.py: tests/warden_port/test_gate_review2.py <-> tests/warden_port/test_gate_review3.py line-level ratio 0.169
test_k#_fixes#.py: tests/test_k5_fixes1.py <-> tests/test_k5_fixes2.py line-level ratio 0.242
test_k#_fixes#.py: tests/test_k5_fixes2.py <-> tests/test_k5_fixes3.py line-level ratio 0.181
test_k#_fixes#.py: tests/test_k5_fixes3.py <-> tests/test_k5_fixes4.py line-level ratio 0.267
test_k#_fixes#.py: tests/test_k5_fixes4.py <-> tests/test_k5_fixes5.py line-level ratio 0.308
test_k#_fixes#.py: tests/test_k5_fixes5.py <-> tests/test_k5_fixes6.py line-level ratio 0.209
test_k#_fixes#.py: tests/test_k5_fixes6.py <-> tests/test_k5_fixes7.py line-level ratio 0.275
test_k#_fixes#.py: tests/test_k5_fixes7.py <-> tests/test_k5_fixes8.py line-level ratio 0.325
test_k#_fixes#.py: tests/test_k5_fixes8.py <-> tests/test_k5_fixes9.py line-level ratio 0.139
test_k#_round#.py: tests/test_k5_round10.py <-> tests/test_k5_round11.py line-level ratio 0.208
test_k#_round#.py: tests/test_k5_round11.py <-> tests/test_k5_round5.py line-level ratio 0.097
test_k#_round#.py: tests/test_k5_round5.py <-> tests/test_k5_round6.py line-level ratio 0.094
test_k#_round#.py: tests/test_k5_round6.py <-> tests/test_k5_round7.py line-level ratio 0.169
test_k#_round#.py: tests/test_k5_round7.py <-> tests/test_k5_round8.py line-level ratio 0.156
test_k#_round#.py: tests/test_k5_round8.py <-> tests/test_k5_round9.py line-level ratio 0.138
test_k#_round#_postgres.py: tests/test_k5_round10_postgres.py <-> tests/test_k5_round8_postgres.py line-level ratio 0.096
test_redaction_review#.py: tests/warden_port/test_redaction_review2.py <-> tests/warden_port/test_redaction_review9.py line-level ratio 0.128

## 11 Reachability (excluding tests as roots)

### 11a src modules NOT reachable from the roots (entry point, package __init__ chain, registry/deferred string names), with whether tests or demos reach them

count: 15

roots used: ['hadavin_sdk', 'hadavin_sdk.cli']; reachable src modules: 88 of 102
hadavin_sdk.actions.secrets_azure (src/hadavin_sdk/actions/secrets_azure.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.actions.secrets_file (src/hadavin_sdk/actions/secrets_file.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.actions.secrets_gcp (src/hadavin_sdk/actions/secrets_gcp.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.actions.secrets_vault (src/hadavin_sdk/actions/secrets_vault.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.approvals.receiver (src/hadavin_sdk/approvals/receiver.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.anchor_azure (src/hadavin_sdk/audit/anchor_azure.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.anchor_gcs (src/hadavin_sdk/audit/anchor_gcs.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.anchor_s3 (src/hadavin_sdk/audit/anchor_s3.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.signer_aws (src/hadavin_sdk/audit/signer_aws.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.signer_azure (src/hadavin_sdk/audit/signer_azure.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.signer_gcp (src/hadavin_sdk/audit/signer_gcp.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.audit.signer_vault (src/hadavin_sdk/audit/signer_vault.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.extract (src/hadavin_sdk/extract.py) | reached by tests: yes | reached by demos: no
hadavin_sdk.guard.producers (src/hadavin_sdk/guard/producers.py) | reached by tests: yes | reached by demos: no

### 11b Reached only by tests (not from the roots, reached from test files)

count: 14

hadavin_sdk.actions.secrets_azure (src/hadavin_sdk/actions/secrets_azure.py)
hadavin_sdk.actions.secrets_file (src/hadavin_sdk/actions/secrets_file.py)
hadavin_sdk.actions.secrets_gcp (src/hadavin_sdk/actions/secrets_gcp.py)
hadavin_sdk.actions.secrets_vault (src/hadavin_sdk/actions/secrets_vault.py)
hadavin_sdk.approvals.receiver (src/hadavin_sdk/approvals/receiver.py)
hadavin_sdk.audit.anchor_azure (src/hadavin_sdk/audit/anchor_azure.py)
hadavin_sdk.audit.anchor_gcs (src/hadavin_sdk/audit/anchor_gcs.py)
hadavin_sdk.audit.anchor_s3 (src/hadavin_sdk/audit/anchor_s3.py)
hadavin_sdk.audit.signer_aws (src/hadavin_sdk/audit/signer_aws.py)
hadavin_sdk.audit.signer_azure (src/hadavin_sdk/audit/signer_azure.py)
hadavin_sdk.audit.signer_gcp (src/hadavin_sdk/audit/signer_gcp.py)
hadavin_sdk.audit.signer_vault (src/hadavin_sdk/audit/signer_vault.py)
hadavin_sdk.extract (src/hadavin_sdk/extract.py)
hadavin_sdk.guard.producers (src/hadavin_sdk/guard/producers.py)

## 12 Config keys defined vs used

### 12a Pydantic/class fields in config.py, defaults.py, scrub_settings.py with reference counts (all fields listed; zero outside the file and zero inside = candidate unused)

count: 73

src/hadavin_sdk/config.py:56 Route.model_id | uses outside file: src=25 tests=54 demos=12 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:57 Route.input_usd_per_mtok | uses outside file: src=4 tests=6 demos=4 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:58 Route.output_usd_per_mtok | uses outside file: src=4 tests=3 demos=4 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:59 Route.max_tokens | uses outside file: src=14 tests=21 demos=4 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:65 Backends.secrets | uses outside file: src=17 tests=95 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:66 Backends.signer | uses outside file: src=34 tests=34 demos=0 | attribute uses inside same file: 2
src/hadavin_sdk/config.py:67 Backends.anchor | uses outside file: src=24 tests=31 demos=0 | attribute uses inside same file: 2
src/hadavin_sdk/config.py:68 Backends.store | uses outside file: src=70 tests=189 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:69 Backends.audit | uses outside file: src=37 tests=126 demos=7 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:70 Backends.llm | uses outside file: src=23 tests=112 demos=3 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:71 Backends.detector | uses outside file: src=17 tests=30 demos=0 | attribute uses inside same file: 2
src/hadavin_sdk/config.py:72 Backends.channel | uses outside file: src=21 tests=42 demos=2 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:163 System.base_url | uses outside file: src=11 tests=24 demos=0 | attribute uses inside same file: 2
src/hadavin_sdk/config.py:169 K1bSettings.max_steps | uses outside file: src=8 tests=11 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:170 K1bSettings.max_tool_calls | uses outside file: src=3 tests=5 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:171 K1bSettings.case_timeout_s | uses outside file: src=1 tests=5 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:173 K1bSettings.redact | uses outside file: src=5 tests=9 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:182 Retention.tool_calls_days | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:183 Retention.redaction_maps_days | uses outside file: src=1 tests=2 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:185 Retention.hold_labelled | uses outside file: src=1 tests=2 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:187 Retention.held_maps_max_days | uses outside file: src=1 tests=4 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:189 Retention.held_tool_calls_max_days | uses outside file: src=1 tests=0 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:190 Retention.purge_every_s | uses outside file: src=1 tests=3 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:204 EvidenceSettings.scrub | uses outside file: src=6 tests=8 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:206 EvidenceSettings.max_tool_errors | uses outside file: src=1 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:207 EvidenceSettings.legacy_max_output_bytes | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:210 EvidenceSettings.fetch_ceiling_bytes | uses outside file: src=3 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:211 EvidenceSettings.https_ports | uses outside file: src=5 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:212 EvidenceSettings.cluster_ports | uses outside file: src=5 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:215 EvidenceSettings.stored_kinds | uses outside file: src=3 tests=4 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:218 EvidenceSettings.max_tool_calls_per_run | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:221 EvidenceSettings.max_map_entries | uses outside file: src=2 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:222 EvidenceSettings.max_tool_bytes_per_run | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:223 EvidenceSettings.max_abandoned_tool_threads | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:226 EvidenceSettings.max_concurrent_tool_calls | uses outside file: src=1 tests=0 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:227 EvidenceSettings.max_tool_calls_per_minute | uses outside file: src=2 tests=0 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:229 EvidenceSettings.cluster_suffixes | uses outside file: src=6 tests=3 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:233 EvidenceSettings.max_document_bytes | uses outside file: src=1 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:238 EvidenceSettings.case_insensitive_targets | uses outside file: src=2 tests=2 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:241 EvidenceSettings.restored_hash_key_secret_name | uses outside file: src=3 tests=2 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:244 EvidenceSettings.post_read_operations | uses outside file: src=1 tests=2 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:246 EvidenceSettings.source_reprobe_s | uses outside file: src=1 tests=0 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:282 SourceConfig.kind | uses outside file: src=62 tests=232 demos=25 | attribute uses inside same file: 14
src/hadavin_sdk/config.py:283 SourceConfig.settings | uses outside file: src=5 tests=8 demos=2 | attribute uses inside same file: 3
src/hadavin_sdk/config.py:284 SourceConfig.token_secret_name | uses outside file: src=7 tests=3 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:285 SourceConfig.ca_file | uses outside file: src=5 tests=3 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:313 Settings.config_dir | uses outside file: src=0 tests=0 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:317 Config.environment | uses outside file: src=3 tests=9 demos=0 | attribute uses inside same file: 3
src/hadavin_sdk/config.py:318 Config.routes | uses outside file: src=25 tests=46 demos=6 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:319 Config.backends | uses outside file: src=16 tests=67 demos=0 | attribute uses inside same file: 3
src/hadavin_sdk/config.py:320 Config.golden_dir | uses outside file: src=4 tests=11 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:321 Config.inputs_dir | uses outside file: src=3 tests=25 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:322 Config.eval_threshold | uses outside file: src=7 tests=5 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:325 Config.check_modules | uses outside file: src=3 tests=2 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:326 Config.systems | uses outside file: src=2 tests=3 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:327 Config.egress_hosts | uses outside file: src=1 tests=6 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:328 Config.allow_insecure_loopback | uses outside file: src=1 tests=4 demos=0 | attribute uses inside same file: 2
src/hadavin_sdk/config.py:329 Config.k1b | uses outside file: src=10 tests=6 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:332 Config.tool_modules | uses outside file: src=5 tests=6 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:333 Config.tool_timeout_s | uses outside file: src=2 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:334 Config.retention | uses outside file: src=2 tests=10 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:335 Config.evidence | uses outside file: src=19 tests=33 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:339 Config.scope_inventory | uses outside file: src=4 tests=6 demos=0 | attribute uses inside same file: 1
src/hadavin_sdk/config.py:341 Config.sources | uses outside file: src=6 tests=12 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:343 Config.tool_module_hashes | uses outside file: src=5 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:344 Config.executor_timeout_s | uses outside file: src=1 tests=1 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/config.py:347 Config.root | uses outside file: src=16 tests=11 demos=1 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:19 ScrubSettings.tail_window | uses outside file: src=3 tests=5 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:20 ScrubSettings.min_redaction_window | uses outside file: src=0 tests=3 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:23 ScrubSettings.min_secret | uses outside file: src=3 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:24 ScrubSettings.fragment_scan | uses outside file: src=2 tests=4 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:25 ScrubSettings.fragment_min | uses outside file: src=2 tests=2 demos=0 | attribute uses inside same file: 0
src/hadavin_sdk/scrub_settings.py:26 ScrubSettings.partial_end | uses outside file: src=2 tests=1 demos=0 | attribute uses inside same file: 0

### 12b YAML keys in non-workflow yaml files and the number of times the key name appears as a word in python text

count: 169

.coderabbit.yaml:16 key auto_incremental_review (x1 in file) | python word hits 0
.coderabbit.yaml:18 key auto_reply (x1 in file) | python word hits 0
.coderabbit.yaml:12 key auto_review (x1 in file) | python word hits 0
.coderabbit.yaml:17 key chat (x1 in file) | python word hits 0
.coderabbit.yaml:14 key drafts (x1 in file) | python word hits 0
.coderabbit.yaml:13 key enabled (x1 in file) | python word hits 0
.coderabbit.yaml:6 key high_level_summary (x1 in file) | python word hits 0
.coderabbit.yaml:2 key language (x1 in file) | python word hits 0
.coderabbit.yaml:9 key path_filters (x1 in file) | python word hits 0
.coderabbit.yaml:7 key poem (x1 in file) | python word hits 0
.coderabbit.yaml:4 key profile (x1 in file) | python word hits 0
.coderabbit.yaml:5 key request_changes_workflow (x1 in file) | python word hits 0
.coderabbit.yaml:8 key review_status (x1 in file) | python word hits 0
.coderabbit.yaml:3 key reviews (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:12 key _metadata (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:22 key always_online (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:18 key background_color (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:25 key bot (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:20 key bot_user (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:17 key description (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:15 key display_information (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:21 key display_name (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:19 key features (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:28 key interactivity (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:29 key is_enabled (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:13 key major_version (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:14 key minor_version (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:16 key name (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:23 key oauth_config (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:31 key org_deploy_enabled (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:30 key request_url (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:24 key scopes (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:27 key settings (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:32 key socket_mode_enabled (x1 in file) | python word hits 0
docs/slack-app-manifest.yaml:33 key token_rotation_enabled (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:7 key additionalProperties (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:10 key amount (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:24 key chain_id (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:13 key changes_spend (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:3 key description (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:15 key executor (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:25 key expected_outcome (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:1 key id (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:20 key idempotency_header (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:4 key input_schema (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:16 key kind (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:18 key lookup_operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:17 key operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:8 key properties (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:6 key required (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:11 key risk_class (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:22 key rollback (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:23 key rollback_test (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:19 key secret_name (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:14 key target_system (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:12 key targets_production (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:9 key title (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:5 key type (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:21 key verify_check (x1 in file) | python word hits 0
tests/fixtures/config/actions/create_draft_record.yaml:2 key version (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:7 key additionalProperties (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:23 key chain_id (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:12 key changes_spend (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:3 key description (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:14 key executor (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:24 key expected_outcome (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:1 key id (x2 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:19 key idempotency_header (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:4 key input_schema (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:15 key kind (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:17 key lookup_operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:16 key operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:8 key properties (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:6 key required (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:10 key risk_class (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:21 key rollback (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:22 key rollback_test (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:18 key secret_name (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:13 key target_system (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:11 key targets_production (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:5 key type (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:20 key verify_check (x1 in file) | python word hits 0
tests/fixtures/config/actions/delete_record.yaml:2 key version (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:7 key additionalProperties (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:23 key chain_id (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:12 key changes_spend (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:3 key description (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:14 key executor (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:24 key expected_outcome (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:1 key id (x2 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:19 key idempotency_header (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:4 key input_schema (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:15 key kind (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:17 key lookup_operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:16 key operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:8 key properties (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:6 key required (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:10 key risk_class (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:21 key rollback (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:22 key rollback_test (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:18 key secret_name (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:13 key target_system (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:11 key targets_production (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:5 key type (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:20 key verify_check (x1 in file) | python word hits 0
tests/fixtures/config/actions/lookup_record.yaml:2 key version (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:9 key additionalProperties (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:12 key body (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:26 key chain_id (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:15 key changes_spend (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:5 key description (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:17 key executor (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:27 key expected_outcome (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:3 key id (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:22 key idempotency_header (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:6 key input_schema (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:18 key kind (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:20 key lookup_operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:19 key operation (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:10 key properties (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:8 key required (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:13 key risk_class (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:24 key rollback (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:25 key rollback_test (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:21 key secret_name (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:16 key target_system (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:14 key targets_production (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:11 key to (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:7 key type (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:23 key verify_check (x1 in file) | python word hits 0
tests/fixtures/config/actions/send_email.yaml:4 key version (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:9 key budget_usd (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:10 key daily (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:3 key data_class (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:8 key max_steps (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:4 key model_route (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:11 key monthly (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:5 key prompt_file (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:6 key scope_allowed (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:2 key status (x1 in file) | python word hits 0
tests/fixtures/config/agents.yaml:7 key tools_allowed (x1 in file) | python word hits 0
tests/fixtures/config/chains.yaml:2 key steps (x1 in file) | python word hits 0
tests/fixtures/config/chains.yaml:4 key timeout_s (x3 in file) | python word hits 0
tests/fixtures/config/config.yaml:25 key allow_insecure_loopback (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:12 key audit (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:9 key backends (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:23 key base_url (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:15 key channel (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:19 key check_modules (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:4 key default (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:14 key detector (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:2 key environment (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:18 key eval_threshold (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:22 key fixture-records (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:16 key golden_dir (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:6 key input_usd_per_mtok (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:17 key inputs_dir (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:13 key llm (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:8 key max_tokens (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:5 key model_id (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:7 key output_usd_per_mtok (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:3 key routes (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:10 key secrets (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:11 key store (x1 in file) | python word hits 0
tests/fixtures/config/config.yaml:21 key systems (x1 in file) | python word hits 0
tests/fixtures/config/egress.yaml:1 key hosts (x1 in file) | python word hits 0
tests/fixtures/config/principals.yaml:6 key approver_of (x3 in file) | python word hits 0
tests/fixtures/config/principals.yaml:2 key kind (x4 in file) | python word hits 0
tests/fixtures/config/principals.yaml:3 key rights (x1 in file) | python word hits 0

## 10 Skeleton map rows
Written to parts/skeleton-map.md: file rows per lane {'D3': 76, 'D2': 81, 'C': 25, 'A': 44, 'B': 39, 'D1': 207}; full-column rows 225; short rows 247; extra non-file D3 rows (branches, remotes, entry point, CI jobs, hooks): 12

## 13 Coverage
git ls-files paths: 16780; in scope: 472; with a skeleton row: 472; in scope without a row: 0; NOT-AUDITED (out of scope): 16308

### 13a In-scope paths without a skeleton row

(none found)

### 13b NOT-AUDITED groups (handover/ files outside the D3 list) with file counts

count: 23

handover/<top-level file>: 29 files
handover/bible: 57 files
handover/bundles: 2 files
handover/checkpoints: 24 files
handover/cloud-demo: 2 files
handover/core: 6378 files
handover/core-hardening: 14 files
handover/decisions: 2 files
handover/demo: 344 files
handover/design: 1 files
handover/designs: 3 files
handover/egm: 116 files
handover/evidence: 4718 files
handover/hooks-src: 2 files
handover/promotion-inputs: 3028 files
handover/reports: 15 files
handover/reviews: 1443 files
handover/seeds: 6 files
handover/studio-notes: 59 files
handover/tickets: 56 files
handover/tools: 6 files
handover/triage: 1 files
handover/vendor-inputs: 2 files

### 13c In-scope files not opened (name matches env/key pattern; row exists, contents never read)

(none found)

### 13d In-scope files not read as text (binary, over 400 KB, or unreadable); row exists

count: 1

handover/ledger.md

## 14 Sampler
Implemented: `python3 -I handover/core-hardening/parts/evidence-1.py --sample N --seed S` (reads MASTER-MAP.md and AUDIT-FINDINGS.md, prints a seeded sample of ids to stdout only; does not rewrite this file). Not run as part of this evidence (the merged files do not exist yet).

## Run summary
- files written: parts/evidence-1.md, parts/skeleton-map.md, full lists: evidence-1-full-5b.txt (1288 lines), evidence-1-full-6b.txt (2770 lines)
- elapsed: 33s

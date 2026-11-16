# Lane L5b

> LEGEND (added 16 Nov 2026): a lane = one read-only audit pass over a set of files, run by one agent (lane L1, L2 ... L6; not the parked group L of decision 3). A continuation lane (L1c ...) reads what the first lane left. READ = opened fully. SKIMMED = headers or grep or first and last slice. NOT-READ = not opened or only the top (draw no conclusion from it). OWNER-ONLY = never opened (work/OWNER-ONLY.txt). Scope: real-v5 scenes 1 to 4 (decision 1). Decisions = inputs/DECISIONS-2026-11-16.md. Owner and date of each continuation lane: the studio lead, in the lead's launch message (none named yet).

## Coverage
PARTIAL: no file was opened in full. All 376 rows are SKIMMED (docstring or header plus grep) because the brief makes src/ and tests/ one CORE row and asks for a kind overlap hunt, not a module walk. Plan section 6 allows SKIMMED only for named kinds, so the lead must treat these rows as NOT fully READ for any claim beyond the findings below.
| path | bytes | status | note |
|---|---|---|---|
| src/hadavin_sdk/__init__.py | 92 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/__init__.py | 0 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/authorizer.py | 2034 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/contract.py | 7634 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/executor.py | 8735 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets.py | 440 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_aws.py | 1770 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_azure.py | 1966 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_cache.py | 1682 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_env.py | 1158 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_file.py | 3543 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_gcp.py | 2228 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/actions/secrets_vault.py | 8465 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/app.py | 20216 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/__init__.py | 167 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/cards.py | 4151 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/channel.py | 5651 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/gate.py | 35498 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/hmac_v0.py | 2996 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/receiver.py | 2646 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/requests.py | 10794 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/slack.py | 1140 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/approvals/slack_channel.py | 9246 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/__init__.py | 215 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/anchor_azure.py | 3702 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/anchor_gcs.py | 3353 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/anchor_s3.py | 3894 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/anchors.py | 1610 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/chain.py | 24642 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/local_dir.py | 7589 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/protocol.py | 1040 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/signer.py | 8623 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/signer_aws.py | 2246 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/signer_azure.py | 2862 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/signer_gcp.py | 2628 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/audit/signer_vault.py | 3844 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/backends/__init__.py | 585 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/backends/builtin.py | 1596 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/backends/factory.py | 2713 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/backends/platform_secrets.py | 2471 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/backends/table.py | 22399 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/cli.py | 17693 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/config.py | 22373 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/defaults.py | 6760 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/deferred.py | 4075 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/errors.py | 199 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/evals.py | 6446 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/extract.py | 1968 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/__init__.py | 364 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/bedrock_guardrail.py | 4916 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/egress.py | 1074 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/http.py | 10642 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/injection.py | 3872 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/judge.py | 4516 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/judge_prompt.md | 775 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/producers.py | 3937 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/redact.py | 58972 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/guard/runmap.py | 30060 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/hashing.py | 1388 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/identity.py | 411 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/__init__.py | 107 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/atomic.py | 499 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/audit_sink.py | 3067 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/bundle.py | 15447 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/causelist.py | 3428 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/diagnosis.py | 4188 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/loop.py | 9012 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/redaction.py | 8388 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/replay.py | 11358 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/report.py | 8892 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/score.py | 15954 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/k1b/tools.py | 9749 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/limits.py | 1997 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/__init__.py | 222 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/anthropic.py | 5747 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/bedrock.py | 6611 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/common.py | 9595 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/fake.py | 1847 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/gemini.py | 4960 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/openai_compat.py | 6038 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/protocol.py | 779 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/llm/retry.py | 4548 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/models.py | 10192 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/registry.py | 17506 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/replay_records.py | 3117 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/__init__.py | 0 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/agent_loop.py | 44933 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/evidence.py | 9692 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/plan.py | 839 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/runs.py | 1554 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/runtime/tick.py | 15896 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/scrub_settings.py | 1247 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/sources/__init__.py | 3505 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/sources/kinds.py | 2407 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/sources/kubernetes.py | 15891 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/stages.py | 1337 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/stats.py | 1150 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/__init__.py | 178 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/auth_aws.py | 801 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/memory.py | 10907 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrate.py | 17419 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migration_numbers.py | 32963 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrations/0001_core.sql | 3880 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrations/0002_audit_chain.sql | 1659 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrations/0003_approvals_tick.sql | 1733 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrations/0004_audit_checkpoint_meta.sql | 679 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/migrations/0005_evidence.sql | 1160 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/postgres.py | 22335 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/store/protocol.py | 6509 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/testing/__init__.py | 75 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/testing/mutation.py | 5528 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| src/hadavin_sdk/tools.py | 55271 | SKIMMED | docstring line plus job-key grep only; CORE not mapped module by module (brief) |
| tests/__init__.py | 0 | SKIMMED | test file; name, size and import grep only |
| tests/conftest.py | 3208 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/__init__.py | 0 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/aws_stub.py | 2122 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/conftest.py | 1901 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/http_fake.py | 12330 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/__init__.py | 512 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/audit_chain.py | 5587 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/audit_neutral.py | 3796 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/builtin.py | 2123 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/channel_slack.py | 542 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/detectors.py | 4299 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/llm_wire.py | 7466 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/secrets_cloud.py | 1955 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/secrets_neutral.py | 4364 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/kinds/store_postgres.py | 3565 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/sources.py | 5786 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_anchor.py | 1053 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_capabilities.py | 6211 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_llm.py | 4849 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_secrets.py | 1486 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_signer.py | 1554 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_sources.py | 12924 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/test_store.py | 16199 | SKIMMED | test file; name, size and import grep only |
| tests/contracts/vault_fake.py | 6251 | SKIMMED | test file; name, size and import grep only |
| tests/demo_askdata/__init__.py | 0 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/attackrun.py | 1254 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/conftest.py | 6952 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/corpus.py | 36275 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/fuzzgen.py | 21935 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/gold_runner.py | 1882 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/kit.py | 5738 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/lumen_standin.py | 9656 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/oracle.py | 5830 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_allowlist.py | 3110 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_audit.py | 7363 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_cli.py | 3626 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_corpus_on_server.py | 668 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_eval_compare.py | 7221 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_eval_harness.py | 26127 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_gold_data.py | 12523 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_gold_exec.py | 3850 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_htmlexport.py | 5547 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_imports.py | 1988 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_ledger.py | 6936 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_llm_io.py | 8305 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_meter.py | 6080 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_pgsource_layers.py | 9211 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_pipeline.py | 12564 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_roles.py | 3318 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_safe_text.py | 1528 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_seed.py | 10434 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_spike_seed.py | 1383 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_validate.py | 7243 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_validate_fuzz.py | 4598 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_validate_harm.py | 8418 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_validate_mutation.py | 2589 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_validate_oracle.py | 1314 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_verify_readonly.py | 5511 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/demo_askdata/test_wire.py | 464 | SKIMMED | demo tests inside core; name, size and import header only |
| tests/fixtures/__init__.py | 0 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/01-destructive-log.json | 755 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/02-forged-evidence-id.json | 643 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/03-forged-placeholder.json | 560 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/04-hidden-in-deploy-message.json | 742 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/05-pii-secret-in-log.json | 629 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam/06-oversized-result.json | 683 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam_extra/07-literal-placeholder.json | 453 | SKIMMED | fixture data; name only |
| tests/fixtures/bundles/redteam_extra/08-other-real-target.json | 629 | SKIMMED | fixture data; name only |
| tests/fixtures/checks.py | 1037 | SKIMMED | fixture data; name only |
| tests/fixtures/ci_security_golden.json | 9124 | SKIMMED | fixture data; name only |
| tests/fixtures/config/actions/create_draft_record.yaml | 853 | SKIMMED | fixture data; name only |
| tests/fixtures/config/actions/delete_record.yaml | 653 | SKIMMED | fixture data; name only |
| tests/fixtures/config/actions/lookup_record.yaml | 642 | SKIMMED | fixture data; name only |
| tests/fixtures/config/actions/send_email.yaml | 905 | SKIMMED | fixture data; name only |
| tests/fixtures/config/agents.yaml | 272 | SKIMMED | fixture data; name only |
| tests/fixtures/config/chains.yaml | 181 | SKIMMED | fixture data; name only |
| tests/fixtures/config/config.yaml | 708 | SKIMMED | fixture data; name only |
| tests/fixtures/config/egress.yaml | 21 | SKIMMED | fixture data; name only |
| tests/fixtures/config/principals.yaml | 264 | SKIMMED | fixture data; name only |
| tests/fixtures/config/prompts/test-agent.md | 216 | SKIMMED | fixture data; name only |
| tests/fixtures/fake_slack.py | 1860 | SKIMMED | fixture data; name only |
| tests/fixtures/fake_system.py | 5666 | SKIMMED | fixture data; name only |
| tests/fixtures/gitleaks_config_golden.json | 1182 | SKIMMED | fixture data; name only |
| tests/fixtures/golden/test-agent.jsonl | 1398 | SKIMMED | fixture data; name only |
| tests/fixtures/http_fake.py | 2854 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/bad.txt | 27 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/chat.txt | 41 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/create.txt | 73 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/delete.txt | 32 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/extract.txt | 61 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-01.txt | 75 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-02.txt | 74 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-03.txt | 72 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-04.txt | 70 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-05.txt | 71 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-06.txt | 71 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-07.txt | 69 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-08.txt | 76 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-09.txt | 35 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/golden-10.txt | 35 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/injected.txt | 152 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/lookup.txt | 45 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/loop.txt | 62 | SKIMMED | fixture data; name only |
| tests/fixtures/inputs/pii.txt | 197 | SKIMMED | fixture data; name only |
| tests/fixtures/k5_tools.py | 1174 | SKIMMED | fixture data; name only |
| tests/fixtures/migrations_released.json | 456 | SKIMMED | fixture data; name only |
| tests/fixtures/mutation_manifest.json | 583 | SKIMMED | fixture data; name only |
| tests/fixtures/plan_v1.json | 564 | SKIMMED | fixture data; name only |
| tests/fixtures/record.py | 3691 | SKIMMED | fixture data; name only |
| tests/fixtures/recorded/0436e2fa8eef90311b640390f72d791576d10d1f1dd9b1affe1e9373890512c7-1.json | 236 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/16de1947511c36df77369edcaec2ca33ed1f362fb143feffc6f28bc902eb93e3-1.json | 235 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/218b51186ea53685a5fa8e1efc9e96a6e0823f28715131ffe0482c8e67fbb399-1.json | 235 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/288e1c575e29d37867dc5dc2e6565446fbf749eb37c73f0353c76f43f72aeb5e-1.json | 236 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/373576676ec0d682f8e84be73db9721fc27d669e5d4e37876f01440a81016539-1.json | 193 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/3d1a8803922c0067b6099f67ae425139a5ceaa3afb745743b229d9337d0d4736-1.json | 233 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/47d5374027d2c77b59fb3f77068334ffb020117f63352e6f959452196b8718b0-1.json | 232 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/4f3a1545a1bc7a888ba565cbcafe532aec5cc036bab28ddec57baabe1e4ae326-1.json | 111 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/6496017d9bce458856288a2c64d9213e681f5ce5d4d3a7ab59f4042b61059f6e-1.json | 193 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/6e4b8d5bb475c4c2050697eb742826130d63af1b63ffe55a0668b714fa297d92-1.json | 193 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/8b917fb84387987afbbdbebc5d0e8e4b524bef7933db4d3fb73f42afc171098c-1.json | 107 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/8b917fb84387987afbbdbebc5d0e8e4b524bef7933db4d3fb73f42afc171098c-2.json | 128 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/9762bcc71f51377e2ec30e8875f983aca7079452111b64b0fa2eabf4264c6a49-1.json | 230 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/9a2a7a599bb00037a34f44de38c5e614ea8b708800b480481feb888104c4dd03-1.json | 240 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/README.md | 73 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/ad62d4017c2e97741cf27311c05e7f39019648206e303b5449a0ad76e747bf05-1.json | 190 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/aedc551993fbfb98a7977b84f1a0dbf3a145a1d1a0c7c5cda3a7385cabd6cc6f-1.json | 232 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/b341f0bb8b6db3e2532a8bc118554c296725d0fe2580afad6c4c0d1c7ff599ec-1.json | 184 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/b341f0bb8b6db3e2532a8bc118554c296725d0fe2580afad6c4c0d1c7ff599ec-2.json | 184 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/b341f0bb8b6db3e2532a8bc118554c296725d0fe2580afad6c4c0d1c7ff599ec-3.json | 184 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/b341f0bb8b6db3e2532a8bc118554c296725d0fe2580afad6c4c0d1c7ff599ec-4.json | 184 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/b341f0bb8b6db3e2532a8bc118554c296725d0fe2580afad6c4c0d1c7ff599ec-5.json | 184 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/c1d8bf6ad8698fea26af4a71a6b7361bdaf91c85cbdefa7132808116a5a6fa66-1.json | 231 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/ca16bee4960b81e01bc5a3bb1d864630462fe3d599eb045eb362b68fc8ce2b62-1.json | 193 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded/f69f5b64ce0bf08cf281c0b49e8114182667cbf92215169d7bfba52bf51c9378-1.json | 237 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/anthropic/denied.json | 218 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/anthropic/text.json | 442 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/anthropic/throttle.json | 236 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/anthropic/tool_call.json | 576 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock/denied.json | 216 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock/text.json | 452 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock/throttle.json | 210 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock/tool_call.json | 663 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock_guardrail/clean.json | 402 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock_guardrail/other_policy.json | 794 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/bedrock_guardrail/prompt_attack.json | 760 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/gemini/denied.json | 283 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/gemini/text.json | 559 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/gemini/throttle.json | 285 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/gemini/tool_call.json | 737 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/openai_compat/denied.json | 280 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/openai_compat/text.json | 569 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/openai_compat/throttle.json | 263 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/recorded_http/openai_compat/tool_call.json | 877 | SKIMMED | recorded model reply fixture; name and count only |
| tests/fixtures/reference_material_sha256.txt | 18674 | SKIMMED | fixture data; name only |
| tests/fixtures/schemas.py | 400 | SKIMMED | fixture data; name only |
| tests/fixtures/seeded.py | 1172 | SKIMMED | fixture data; name only |
| tests/fixtures/timing.py | 1356 | SKIMMED | fixture data; name only |
| tests/k1b_support.py | 13590 | SKIMMED | test file; name, size and import grep only |
| tests/k5_support.py | 8214 | SKIMMED | test file; name, size and import grep only |
| tests/migration_numbers_mutants.py | 12268 | SKIMMED | test file; name, size and import grep only |
| tests/mutation_runner_mutants.py | 24019 | SKIMMED | test file; name, size and import grep only |
| tests/reference_scorer.py | 1994 | SKIMMED | test file; name, size and import grep only |
| tests/stage_exemptions.tsv | 6036 | SKIMMED | test file; name, size and import grep only |
| tests/stage_mutants.py | 10501 | SKIMMED | test file; name, size and import grep only |
| tests/test_ci_gitleaks_scope.py | 24253 | SKIMMED | test file; name, size and import grep only |
| tests/test_cuj.py | 11423 | SKIMMED | test file; name, size and import grep only |
| tests/test_executor.py | 4575 | SKIMMED | test file; name, size and import grep only |
| tests/test_g4_parity.py | 11164 | SKIMMED | test file; name, size and import grep only |
| tests/test_http_metadata.py | 17073 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1a_pass_k.py | 7595 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_bundle.py | 18614 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_causelist_containment.py | 1820 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_cli.py | 11048 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_diagnosis.py | 7107 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_redaction.py | 9228 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_redaction_layers.py | 7085 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_replay.py | 22260 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_score.py | 17899 | SKIMMED | test file; name, size and import grep only |
| tests/test_k1b_stats.py | 2080 | SKIMMED | test file; name, size and import grep only |
| tests/test_k2_migrations.py | 18109 | SKIMMED | test file; name, size and import grep only |
| tests/test_k3_leftovers.py | 4037 | SKIMMED | test file; name, size and import grep only |
| tests/test_k3_pilot.py | 26544 | SKIMMED | test file; name, size and import grep only |
| tests/test_k3_pilot_env.py | 7816 | SKIMMED | test file; name, size and import grep only |
| tests/test_k3_review_fixes.py | 2356 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_classes.py | 23882 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes1.py | 7589 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes2.py | 12557 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes3.py | 5000 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes4.py | 3510 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes5.py | 2578 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes6.py | 6291 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes7.py | 5644 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes8.py | 4408 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_fixes9.py | 18670 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_layers.py | 10953 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_perf.py | 5386 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_postgres.py | 2762 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_producers.py | 8060 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_review.py | 21455 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round10.py | 15477 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round10_postgres.py | 6058 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round11.py | 13161 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round12_fuzz.py | 9093 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round5.py | 35887 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round6.py | 6062 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round6_contracts.py | 1655 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round7.py | 4483 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round8.py | 9622 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round8_postgres.py | 2030 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round9.py | 16687 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_round9b.py | 15621 | SKIMMED | test file; name, size and import grep only |
| tests/test_k5_tools.py | 54949 | SKIMMED | test file; name, size and import grep only |
| tests/test_lockin_guard.py | 31834 | SKIMMED | test file; name, size and import grep only |
| tests/test_migrate_regex_linear.py | 1066 | SKIMMED | test file; name, size and import grep only |
| tests/test_migration_numbers.py | 32590 | SKIMMED | test file; name, size and import grep only |
| tests/test_migration_numbers_guards.py | 21887 | SKIMMED | test file; name, size and import grep only |
| tests/test_mutation_runner.py | 67636 | SKIMMED | test file; name, size and import grep only |
| tests/test_mutation_runner_helpers.py | 9206 | SKIMMED | test file; name, size and import grep only |
| tests/test_mutation_runner_meta.py | 10091 | SKIMMED | test file; name, size and import grep only |
| tests/test_no_hardcoded_values.py | 5855 | SKIMMED | test file; name, size and import grep only |
| tests/test_no_reference_material.py | 3462 | SKIMMED | test file; name, size and import grep only |
| tests/test_p1a_fixes.py | 5341 | SKIMMED | test file; name, size and import grep only |
| tests/test_p1b_backends.py | 9312 | SKIMMED | test file; name, size and import grep only |
| tests/test_p2_postgres.py | 11390 | SKIMMED | test file; name, size and import grep only |
| tests/test_p3b_neutral_audit.py | 27442 | SKIMMED | test file; name, size and import grep only |
| tests/test_p4_secrets.py | 5062 | SKIMMED | test file; name, size and import grep only |
| tests/test_p4b_secrets.py | 14073 | SKIMMED | test file; name, size and import grep only |
| tests/test_p5_llm.py | 10851 | SKIMMED | test file; name, size and import grep only |
| tests/test_p5p6_followups.py | 18973 | SKIMMED | test file; name, size and import grep only |
| tests/test_p6_detectors.py | 14308 | SKIMMED | test file; name, size and import grep only |
| tests/test_p7_store.py | 7481 | SKIMMED | test file; name, size and import grep only |
| tests/test_p7_tick.py | 24942 | SKIMMED | test file; name, size and import grep only |
| tests/test_peel_run_id.py | 13987 | SKIMMED | test file; name, size and import grep only |
| tests/test_repo_rules.py | 19075 | SKIMMED | test file; name, size and import grep only |
| tests/test_review_fixes.py | 9601 | SKIMMED | test file; name, size and import grep only |
| tests/test_review_pr3_round2.py | 17316 | SKIMMED | test file; name, size and import grep only |
| tests/test_runmap_partial_escape.py | 10698 | SKIMMED | test file; name, size and import grep only |
| tests/test_s1_foundation.py | 5368 | SKIMMED | test file; name, size and import grep only |
| tests/test_s2_audit.py | 2312 | SKIMMED | test file; name, size and import grep only |
| tests/test_s3_gate.py | 6108 | SKIMMED | test file; name, size and import grep only |
| tests/test_s4_llm_guard.py | 8318 | SKIMMED | test file; name, size and import grep only |
| tests/test_s5_runtime.py | 5408 | SKIMMED | test file; name, size and import grep only |
| tests/test_s6_approvals.py | 5763 | SKIMMED | test file; name, size and import grep only |
| tests/test_scan_repo.py | 7293 | SKIMMED | test file; name, size and import grep only |
| tests/test_stage_names.py | 29853 | SKIMMED | test file; name, size and import grep only |
| tests/test_timing_fixture.py | 1991 | SKIMMED | test file; name, size and import grep only |
| tests/tls_support.py | 4029 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/__init__.py | 0 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/fakes.py | 2456 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/privacy_corpus.py | 3225 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_audit_chain.py | 27181 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_bedrock_provider_r16.py | 5553 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_gate.py | 2506 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_gate_render.py | 1999 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_gate_review2.py | 5393 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_gate_review3.py | 6913 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_providers.py | 8418 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction.py | 21492 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction_bank.py | 14719 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction_classes.py | 1528 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction_review.py | 3334 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction_review2.py | 5641 | SKIMMED | test file; name, size and import grep only |
| tests/warden_port/test_redaction_review9.py | 2793 | SKIMMED | test file; name, size and import grep only |

## Components
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L5b-C-001 | CORE | CORE: src/ and tests/ (shared core hadavin_sdk) | out of take scope; not mapped module by module; directory list and README only. `src/hadavin_sdk/__init__.py:1 "Hadavin SDK: shared building blocks for fixed-price AI builds"` | OTHER |
| L5b-C-002 | hadavin_sdk top-level modules | app wiring, config, defaults, registry, models, identity, limits, evals, extract, hashing, stats, stages, deferred, replay_records, cli | `src/hadavin_sdk/app.py:1 "App wiring: builds every module from one client config"`; `src/hadavin_sdk/cli.py:1 "hadavin-sdk CLI"` | COUNTER; STORE |
| L5b-C-003 | backends (kind table) | one table maps each capability and kind to settings and factory (the place where vendor kinds are chosen) | `src/hadavin_sdk/backends/table.py:1 "The backend table: every capability, its kinds"` | OTHER |

## Stores
All rows are CORE kinds. Whether the take uses any of them is `NOT VISIBLE: take repo`. DECISION keeps three stores (n8n data, mf_leads, stage.journal); every row below is a further place that can hold state or records, so the lead must check it is not reached by the take.
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L5b-S-001 | store.memory | in-memory run, plan, approval, spend, kill-switch rows | core store kind (default for laptop) | Store Protocol calls | dict rows behind one lock | rows lost on restart (stated in its own docstring) | N/A: in-process dict | UNVERIFIED | UNVERIFIED | none | none | tests/contracts/test_store.py (name only) | app wiring (UNVERIFIED which kind is default) | `src/hadavin_sdk/store/memory.py:1 "In-memory store: dicts behind one lock"` | STORE |
| L5b-S-002 | store.postgres | same Store Protocol on Postgres, compare-and-set in SQL, forward-only migrations 0001 to 0005 | core store kind (the durable one) | Store Protocol calls | rows in Postgres | StoreUnavailable error (protocol) | UNVERIFIED | UNVERIFIED | compare-and-set in SQL | python logging hadavin_sdk.store | UNVERIFIED (DSN from platform secrets) | tests/test_p2_postgres.py and tests/contracts/store_postgres.py (names only) | backend table (UNVERIFIED) | `src/hadavin_sdk/store/postgres.py:1 "Postgres store"`; `src/hadavin_sdk/store/protocol.py:49 "class Store(Protocol):"` | STORE |
| L5b-S-003 | audit.chain | append-only hash chain audit with signed checkpoints and anchors, inside the store database | core audit kind | AuditEvent through write_intent | rows in the store database, signed checkpoints, anchor objects | checkpoint that cannot be signed or anchored is logged and retried, never raised (docstring) | anchors retried by a private method | UNVERIFIED | UNVERIFIED | python logging hadavin_sdk.audit.chain | signer kind (key store) | tests/warden_port/test_audit_chain.py and tests/contracts/kinds/audit_chain.py (names only) | agent_loop, limits, k1b audit_sink | `src/hadavin_sdk/audit/chain.py:1 "an append-only hash chain in the store's database"`; `src/hadavin_sdk/audit/chain.py:338 "def _retry_anchors(self)"` | LOG; STORE; RETRY |
| L5b-S-004 | audit.local_dir | local-folder audit sink, one write-once object per event | core audit kind (laptop) | AuditEvent through write_intent | files in a folder | UNVERIFIED | a retry never makes a second object (docstring) | UNVERIFIED | write-once object name | none | UNVERIFIED | tests/contracts/kinds/audit_neutral.py (name only) | backend table; k1b audit_sink | `src/hadavin_sdk/audit/local_dir.py:1 "Local-folder audit sink for slice 1"`; `src/hadavin_sdk/audit/protocol.py:1 "Audit sink Protocol: write-once events"` | LOG |
| L5b-S-005 | qualified.jsonl (eval gate file) | file of green eval-gate runs, one line per run, read by the runtime to decide whether an agent is qualified | evals.py writes, runtime/agent_loop.py reads | golden-set run | appended line | torn append skipped with a warning | N/A: append only | N/A | UNVERIFIED | python logging hadavin_sdk.runtime | none | tests (name only: tests/test_s4_llm_guard.py area, UNVERIFIED) | runtime, cli | `src/hadavin_sdk/evals.py:1 "append a green run to qualified.jsonl"`; `src/hadavin_sdk/runtime/agent_loop.py:125 "is not valid JSON (torn append): skipped"` | STORE; LOG |
| L5b-S-006 | replay-records.jsonl | file of replay check results kept apart from qualified.jsonl | replay_records.py | replay run results | appended line | UNVERIFIED | N/A | N/A | UNVERIFIED | python logging hadavin_sdk.replay_records | none | UNVERIFIED | deferred.py, k1b | `src/hadavin_sdk/replay_records.py:1 "a file separate from"`; `src/hadavin_sdk/deferred.py:11 "from hadavin_sdk import replay_records"` | STORE; LOG |
| L5b-S-007 | store tables tool_calls and redaction_maps | per-run record of read-tool calls and per-run redaction map (migration 0005) | store kind | runtime tool calls | Postgres rows | UNVERIFIED | N/A | N/A | UNVERIFIED | none | UNVERIFIED | tests/test_k5_postgres.py (name only) | runtime tools box | `src/hadavin_sdk/store/migrations/0005_evidence.sql:5 "CREATE TABLE tool_calls ("`; `src/hadavin_sdk/store/migrations/0005_evidence.sql:21 "CREATE TABLE redaction_maps ("` | STORE; LOG |
| L5b-S-008 | audit.chain in-memory SQLite | private SQLite memory database used when the chain runs without Postgres | audit/chain.py (_Db.memory) | chain rows | process memory | lost on exit | N/A | N/A | N/A | none | none | UNVERIFIED | audit.chain | `src/hadavin_sdk/audit/chain.py:103 "isolation_level=None, check_same_thread=False"` | STORE |

## Workflows
NONE FOUND: searched src/ and tests/ for n8n, workflow, node in file names and with grep; core has no workflow engine (backends/table.py lists kinds only).

## Workflow walk
NONE FOUND: no workflows in src/ or tests/.

## Scripts
NONE FOUND: src/ and tests/ hold no standalone scripts; the one dev tool tools/mutation_runner.py is outside this lane (L5a) and is only cited as an importer.

## Jobs
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L5b-J-001 | tick (housekeeping pass) | one idempotent pass: approvals sweep, reconcile, stuck-run rule, checkpoint, purge, source reprobe | runtime/tick.py | store rows | state changes, heartbeat log line | each step in its own try, failure written to tick_state, exit code 1 | next tick re-runs a failed step | stuck_after_s formula | idempotent by design (docstring) | python logging hadavin_sdk.tick | UNVERIFIED | tests/test_p7_tick.py (name only) | cli tick | `src/hadavin_sdk/runtime/tick.py:4 "runs in order: sweep, reconcile, stuck, checkpoint, purge_evidence"` | RETRY; NOTICE |
| L5b-J-002 | stuck-run rule | moves quiet runs to NEEDS_PERSON with a reason | runtime/tick.py | run.updated_at | run state NEEDS_PERSON | N/A | next tick | max_steps x call_timeout_s x max_attempts + 60 | UNVERIFIED | python logging | UNVERIFIED | tests/test_p7_tick.py (name only) | tick | `src/hadavin_sdk/runtime/tick.py:123 "go to NEEDS_PERSON with a reason"` | RETRY |
| L5b-J-003 | limits (spend meter, daily and monthly caps, kill switch) | counts spend per agent per day and stops runs over a cap or when the kill switch is on | limits.py | usd per call | blocked reasons, audit event | audit write failure (AuditUnavailable) | N/A | N/A | UNVERIFIED | audit sink | UNVERIFIED | tests/test_s1_foundation.py (name only) | runtime agent_loop | `src/hadavin_sdk/limits.py:1 "spend meter, daily and monthly budgets, kill switch"`; `src/hadavin_sdk/store/protocol.py:107 "def add_spend(self, agent_id: str"` | COUNTER |
| L5b-J-004 | k1b per-invocation USD budget | total USD cap for one replay invocation | k1b/loop.py | reply cost | capped status | halts the run | N/A | N/A | N/A | UNVERIFIED | UNVERIFIED | tests/test_k1b_replay.py (name only) | k1b replay | `src/hadavin_sdk/k1b/loop.py:41 "A total USD cap for the whole invocation"` | COUNTER |
| L5b-J-005 | llm retry | bounded retries with backoff and jitter for every network model kind | llm/retry.py | provider error | retried call or ProviderExhausted | ProviderExhausted | up to max_attempts | per call | N/A | UNVERIFIED | UNVERIFIED | tests/test_p5_llm.py (name only) | llm kinds | `src/hadavin_sdk/llm/retry.py:1 "Bounded retries for every network llm kind"` | RETRY |
| L5b-J-006 | executor idempotent lookup | after a timeout on a mutating call, look the result up by idempotency key, never re-send | actions/executor.py | plan idempotency key | RunResult | UNVERIFIED | lookup only, no blind retry | UNVERIFIED | idempotency key header | audit sink | executor identity holds the only client secret | tests/test_executor.py (name only) | runtime | `src/hadavin_sdk/actions/executor.py:153 "Never retry blindly"` | RETRY; FILTER |
| L5b-J-007 | structured extract with one retry | validate model output, one retry with errors, then DeadLetter | extract.py | document bytes, schema | Valid or DeadLetter | returns DeadLetter | exactly one retry | UNVERIFIED | N/A | none | none | tests/test_s4_llm_guard.py (name only) | NO caller in src/ (see L5b-FD-001) | `src/hadavin_sdk/extract.py:1 "one retry with the validator's errors, then a dead letter"` | RETRY; FILTER |
| L5b-J-008 | approval notices | channel Protocol with send, notify and post_card; Slack kind posts a message with Approve and Reject buttons | approvals/channel.py and approvals/slack_channel.py | approval request | Slack message or fake channel record | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | Slack token via platform secrets | tests/test_s6_approvals.py (name only) | runtime, tick reconcile | `src/hadavin_sdk/approvals/channel.py:75 "def notify(self, principal_id: str, text: str)"`; `src/hadavin_sdk/approvals/slack_channel.py:1 "Slack approval channel"` | NOTICE |
| L5b-J-009 | input filters | injection tripwire, optional model judge, redaction, evidence grounding check, egress allowlist | guard/injection.py, guard/judge.py, guard/redact.py, runtime/evidence.py, guard/egress.py | untrusted text, proposals | clean text or refusal | fail closed | N/A | UNVERIFIED | N/A | python logging hadavin_sdk.guard | none | tests/test_s4_llm_guard.py (name only) | runtime | `src/hadavin_sdk/guard/injection.py:1 "a tripwire, never a gate that clears text as safe"`; `src/hadavin_sdk/runtime/evidence.py:1 "Evidence checks on a proposal"`; `src/hadavin_sdk/guard/egress.py:1 "Outbound allowlist: every host the core calls"` | FILTER |
| L5b-J-010 | k1b audit write with hold | writes audit events after the side effect; on failure keeps the event for reconcile | k1b/audit_sink.py | operation event | audit sink write | keeps event for reconcile (docstring) | reconcile later | N/A | UNVERIFIED | audit sink | none | tests/test_k1b_cli.py (name only) | k1b | `src/hadavin_sdk/k1b/audit_sink.py:38 "on failure the sink keeps it for"` | LOG; RETRY |

## Credentials
NAMES only. No value was opened.
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L5b-K-001 | secrets kind env | environment-variable secrets, demo stage only | actions/secrets_env.py | N/A: credential | N/A: credential | UNVERIFIED | N/A: credential | N/A: credential | N/A | none | executor only | tests/test_p4_secrets.py (name only) | executor | `src/hadavin_sdk/actions/secrets_env.py:1 "read from environment variables"` | OTHER |
| L5b-K-002 | secrets kind mounted_file | one file per secret in a mounted folder | actions/secrets_file.py | N/A: credential | N/A: credential | UNVERIFIED | N/A: credential | N/A: credential | N/A | none | executor only | tests/test_p4_secrets.py (name only) | executor | `src/hadavin_sdk/actions/secrets_file.py:1 "one file per secret in a mounted folder"` | OTHER |
| L5b-K-003 | secrets kind vault | Vault or OpenBao KV v2 over standard library HTTP | actions/secrets_vault.py | N/A: credential | N/A: credential | UNVERIFIED | N/A: credential | N/A: credential | N/A | none | executor only | tests/contracts/vault_fake.py (name only) | executor | `src/hadavin_sdk/actions/secrets_vault.py:1 "HashiCorp Vault or OpenBao, KV version 2"` | OTHER |
| L5b-K-004 | secrets kinds aws_secrets_manager, azure_key_vault, gcp_secret_manager | cloud secret stores behind extras | actions/secrets_aws.py, secrets_azure.py, secrets_gcp.py | N/A: credential | N/A: credential | UNVERIFIED | N/A: credential | N/A: credential | N/A | none | executor only | tests/contracts/kinds/secrets_cloud.py (name only) | executor | `src/hadavin_sdk/actions/secrets_aws.py:1 "aws_secrets_manager"` | OTHER |
| L5b-K-005 | platform secrets (Slack token, database DSN, API keys) | credentials a backend itself needs | backends/platform_secrets.py | N/A: credential | N/A: credential | UNVERIFIED | N/A: credential | N/A: credential | N/A | none | per backend | tests/test_p1b_backends.py (name only) | backend factory | `src/hadavin_sdk/backends/platform_secrets.py:1 "Platform secrets: the credentials a backend itself needs"` | OTHER |

## Docs and tests and folders
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L5b-F-001 | src/hadavin_sdk/actions | action contracts, authorizer (allow, needs approval, deny), executor, secrets kinds | `src/hadavin_sdk/actions/authorizer.py:1 "The gate: deterministic"` | OTHER |
| L5b-F-002 | src/hadavin_sdk/approvals | approval requests, channels (fake, Slack), signed callbacks, text cleaning (gate.py) | `src/hadavin_sdk/approvals/requests.py:1 "A timeout escalates and never approves"` | NOTICE |
| L5b-F-003 | src/hadavin_sdk/audit | audit sinks (chain, local_dir), signers, anchors | `src/hadavin_sdk/audit/protocol.py:1 "Audit sink Protocol: write-once events"` | LOG |
| L5b-F-004 | src/hadavin_sdk/backends | backend table, factory, builtin kinds, platform secrets | `src/hadavin_sdk/backends/factory.py:1 "builds one backend from the table"` | OTHER |
| L5b-F-005 | src/hadavin_sdk/guard | injection, judge, redaction, run redaction map, egress allowlist, no-redirect HTTP opener | `src/hadavin_sdk/guard/http.py:1 "The one no-redirect HTTP opener"` | FILTER |
| L5b-F-006 | src/hadavin_sdk/k1b | K1b-lite: replay recorded incidents through an agent and count results (report only) | `src/hadavin_sdk/k1b/__init__.py:1 "replay a client's recorded incidents through an agent"` | OTHER |
| L5b-F-007 | src/hadavin_sdk/llm | model kinds: fake, anthropic, bedrock, openai_compat, gemini; retry | `src/hadavin_sdk/llm/protocol.py:1 "Model adapter Protocol"` | RETRY |
| L5b-F-008 | src/hadavin_sdk/runtime | agent loop, plan, run state machine, evidence checks, tick | `src/hadavin_sdk/runtime/runs.py:1 "Run state machine"` | RETRY |
| L5b-F-009 | src/hadavin_sdk/sources | read-source interfaces and kinds (Kubernetes) | `src/hadavin_sdk/sources/kubernetes.py:1 "Kubernetes read source"` | OTHER |
| L5b-F-010 | src/hadavin_sdk/store | Store Protocol, memory and Postgres stores, migrations 0001 to 0005, migration rule | `src/hadavin_sdk/store/migrate.py:1 "Forward-only schema migrations for the Postgres store"` | STORE |
| L5b-F-011 | src/hadavin_sdk/testing | mutation-run judge shipped inside the package | `src/hadavin_sdk/testing/mutation.py:1 "Judge one mutation-test run by the REASON"` | OTHER |
| L5b-T-001 | tests/ top level (92 files, 128 test_*.py under tests/) | review-round test files named by round (test_k5_fixes1 to 9, test_k5_round5 to 12), phase files (test_p1a to test_p7), slice files (test_s1 to test_s6), K1b, migration, mutation-runner, repo-rule guards | UNVERIFIED which tests are redundant; names only: `tests/test_s1_foundation.py:1 "S1: config, models, store, run state machine"` | OTHER |
| L5b-T-002 | tests/contracts (13 files) | kind contract tests run against fakes (store, llm, secrets, signer, anchor, sources) | `tests/contracts/conftest.py:1 "every check runs against every registered kind"` | OTHER |
| L5b-T-003 | tests/warden_port (16 files) | tests ported from an earlier project (WARDEN): audit chain, gate, providers, redaction | `src/hadavin_sdk/audit/chain.py:3 "Ported from WARDEN"` | LOG; FILTER |
| L5b-T-004 | tests/demo_askdata (35 files) | tests for the Ask-your-data demo kept inside core tests | `tests/demo_askdata/conftest.py:25 "parents[2]"`; `tests/demo_askdata/attackrun.py:9 "from askdata.validate import Rejected, validate"` | OTHER |
| L5b-T-005 | tests/fixtures (16 top-level files plus 25 recorded replies, recorded_http, bundles, config, inputs) | made-up inputs, recorded model replies, red-team bundles | `tests/fixtures/recorded/README.md:1 "recorded model answers"` | OTHER |

## Findings
| id | claim type | severity | evidence | conflicts with | job key |
|---|---|---|---|---|---|
| L5b-FD-001 | dead | Major | extract.py has no importer in src/ or tools/ (grep for hadavin_sdk.extract over src and tools found only tests): `src/hadavin_sdk/extract.py:1 "one retry with the validator's errors, then a dead letter"`; imported only by `tests/test_s4_llm_guard.py:8 "from hadavin_sdk.extract import Valid, extract"`. Its DeadLetter output is never stored: Store has `src/hadavin_sdk/store/protocol.py:104 "def add_dead_letter(self, dl: DeadLetter)"` but grep shows callers only in tests/contracts/test_store.py. So a dead-letter store and a retry engine exist in core with no production caller. Next step for the lead: keep only if the take or a demo calls it (take repo NOT VISIBLE), else ARCHIVE proposal | none | RETRY |
| L5b-FD-002 | idle | Major | two dev-tool modules ship in the runtime package and nothing in src/ imports them: `src/hadavin_sdk/store/migration_numbers.py:1 "The migration rule, as pure functions"` and `src/hadavin_sdk/testing/mutation.py:1 "Judge one mutation-test run by the REASON"`. The only importer outside tests is `tools/mutation_runner.py:69 "from hadavin_sdk.testing.mutation import"` (migration_numbers: tests and a mutants file only). Grep showed zero src importers for both. Next step: move to the tools side or mark dev-only; needs the owner yes because core is the single source of truth | none | OTHER |
| L5b-FD-003 | duplicate | Major | counters and caps live in three places that the take also has: core `src/hadavin_sdk/limits.py:1 "spend meter, daily and monthly budgets, kill switch"` (state in Store spend rows), core `src/hadavin_sdk/k1b/loop.py:41 "A total USD cap for the whole invocation"` (in-process), and the take money guard stage.journal (NOT VISIBLE: take repo; named in DECISION). The core one is the likely owner of the COUNTER key for a later portal; for the video take it is not reached (UNVERIFIED: take repo not visible) | DECISION line 17 | COUNTER |
| L5b-FD-004 | duplicate | Major | core has two durable audit and log kinds plus a wrapper: `src/hadavin_sdk/audit/chain.py:1 "an append-only hash chain in the store's database"`, `src/hadavin_sdk/audit/local_dir.py:1 "Local-folder audit sink for slice 1"`, and `src/hadavin_sdk/k1b/audit_sink.py:1 "events go to the configured sink"`. chain sits in the same database as the Store (matches DECISION one database) but local_dir writes files, which overlaps the take plain-file logs. Both are kinds by the no-single-dependency rule, so verdict for the lead: chain NEEDED if any core audit is used, local_dir is a laptop-only alternative | DECISION line 16 | LOG |
| L5b-FD-005 | duplicate | Major | two file stores sit beside the Store protocol: `src/hadavin_sdk/evals.py:1 "append a green run to qualified.jsonl"` and `src/hadavin_sdk/replay_records.py:1 "a file separate from"`. Both are jsonl files in the config folder, read with torn-append handling (`src/hadavin_sdk/runtime/agent_loop.py:125 "is not valid JSON (torn append): skipped"`). That is a second store kind next to Postgres rows for state the runtime reads | DECISION line 14 | STORE |
| L5b-FD-006 | inconsistent | Nit | the word gate names two different things: `src/hadavin_sdk/actions/authorizer.py:1 "The gate: deterministic"` (allow, needs approval, deny) versus `src/hadavin_sdk/approvals/gate.py:1 "Text cleaning for anything people read"` (text cleaning; 35 KB file named gate). Wording rule: one word one meaning. Fix needs a rename in core, owner yes needed (core source of truth) | none | OTHER |
| L5b-FD-007 | inconsistent | Major | demo tests live inside the core test tree and import demo code that is not part of the core package: `tests/demo_askdata/attackrun.py:9 "from askdata.validate import Rejected, validate"` with the demo path set in `tests/demo_askdata/conftest.py:25 "parents[2]"` (folder demos/ask-your-data, 35 tracked files under tests/demo_askdata). This breaks the rule that core stays free of demo imports and that demo-only things sit in a demo folder; core tests fail if demos/ is removed (UNVERIFIED: not run). Next step: move to the demo, owner yes needed | none | OTHER |
| L5b-FD-008 | ops | Nit | test files are named after review rounds, not behaviour (tests/test_k5_fixes1.py to test_k5_fixes9.py, tests/test_k5_round5.py to round12): e.g. `tests/test_k5_fixes4.py:1 "Fixes for review 4 of PR #42"`. Whether they overlap each other is UNVERIFIED (not opened). None of the sampled headers referenced removed code except one comment about a removed migration file: `tests/test_k2_migrations.py:391 "The grant map still names the removed file"` (a deliberate test of the refusal, not a test of removed code) | none | OTHER |
| L5b-FD-009 | duplicate | Nit | three text-cleaning places exist: `src/hadavin_sdk/guard/redact.py:1 "Pattern-based redaction for logs, audit and channel text"`, `src/hadavin_sdk/k1b/redaction.py:1 "every string of a case bundle is masked"` (builds on guard.runmap, so layered, not copied) and `src/hadavin_sdk/approvals/gate.py:1 "Text cleaning for anything people read"`. By header they do different jobs (patterns, bundle walk, link defanging); real overlap UNVERIFIED (files not read in full) | none | FILTER |
| L5b-FD-010 | duplicate | Nit | two retry or backoff engines for outbound calls: `src/hadavin_sdk/llm/retry.py:1 "Bounded retries for every network llm kind"` and per-SDK retry settings in the audit and secrets kinds, for example `src/hadavin_sdk/audit/signer_aws.py:53 "total_max_attempts"`. The executor deliberately never retries a mutating call (L5b-J-006). Each is a different layer, no conflict found | none | RETRY |
| L5b-FD-011 | unverified | Nit | MASTER-MAP wiring claim: which store kind is the core default and whether any take step imports core at all is UNVERIFIED (take repo NOT VISIBLE; no runtime). Not NOT-FOUND: grep for an n8n or workflow reference in src/ found none | none | STORE |

## Checkpoint
Done: all 376 manifest rows now SKIMMED (docstring or header plus grep); job-key greps run over src/ for STORE, LOG, FILTER, COUNTER, RETRY, NOTICE; importer proof by grep for extract, migration_numbers, testing.mutation, evals, stats, hashing, replay_records, k1b modules. Next: nothing in this lane; the lead may order a READ continuation of tests/test_k5_* if overlap between review-round test files matters. Blockers: no full READ of any file (brief scope was kind overlap, not module walk); test-file overlap UNVERIFIED; no runtime, so default store kind UNVERIFIED.

ADDED 16 Nov 2026 (cold read): Legend. take = the filmed lead-intake demo build (its repo is not visible to this lane). DECISION = inputs/DECISIONS-2026-11-16.md and handover/system-map/DECISION-one-store.md, cited by their own line numbers. job key = STORE, LOG, FILTER, COUNTER, RETRY, NOTICE or OTHER (the duty a row serves). kind = a swappable plug-in behind one interface. MASTER-MAP = MASTER-MAP.md (held). UNVERIFIED = not checked by running or reading the file; N/A = does not apply to that row. Method: docstring plus grep plus directory list and README only. Status: PARTIAL; next step is a READ lane. The count '92 files, 128 test_*.py' is wrong as written (128 is more than 92): UNVERIFIED, recount with one rule. FD-001 'dead' and FD-002 'idle' rest on a grep whose command and output are not shown: both UNVERIFIED.

ADDED 16 Nov 2026 (cold read r2; wins). Read this first: take = one recorded run of the demo; DECISION = a file with the lead's 16 Nov decisions, lines 14, 16, 17 cited above refer to DECISION-one-store.md; job key = the id that makes a lead count once; kind = a swappable part behind an interface; mf_leads = the table of leads in the demo database; stage.journal = the log file the stage writes. FD-001 and FD-002 are Major IF CONFIRMED: the grep command and output were not shown, so both are UNVERIFIED; re-run 'grep -r hadavin_sdk.extract src tools' and paste the output. The count '92 files, 128 test_*.py' is wrong and must not be handed on. K1b, WARDEN and NEEDS_PERSON are core project terms (K1b = a core module name; WARDEN = the checker that blocks unsafe actions; NEEDS_PERSON = a result that sends the item to a person): UNVERIFIED meanings, ask the lead. Next step: a READ lane over tests/test_k5_*; owner and date not set, the studio head must assign them.

ADDED 16 Nov 2026 (cold read r3; wins over the line-479 paragraph where they differ). job key = the duty a row serves: STORE, LOG, FILTER, COUNTER, RETRY, NOTICE or OTHER. take = the filmed lead-intake demo build (its repo is not visible). DECISION = two files: DECISION-one-store.md (lines 14 to 17 cited here) and inputs/DECISIONS-2026-11-16.md. WARDEN = an earlier project; tests/warden_port holds tests ported from it. stage.journal = one of the three stores listed at line 394. UNVERIFIED = not checked by running or reading; N/A = does not apply to this row.

ADDED 16 Nov 2026 (cold read r4; wins). Line 481 replaces lines 477 and 479 entirely. Carry over: (a) FD-001 and FD-002 are UNVERIFIED until the grep output is pasted; (b) the '92 files, 128 test_*.py' count at line 453 is wrong; (c) mf_leads = the table of leads in the demo database. 'DECISION line N' = DECISION-one-store.md line N unless the row names another file. A Major marked UNVERIFIED is a lead to check, not a confirmed defect.

ADDED 16 Nov 2026 (r5; this is the only current paragraph; ignore earlier ADDED paragraphs). take = the filmed lead-intake demo build (repo not visible). 'DECISION line N' = handover/system-map/DECISION-one-store.md line N unless another file is named. mf_leads = the table of leads in the demo database. stage.journal = the log file the demo's stage writes (UNVERIFIED, ask the lead). WARDEN = an earlier project. K1b and NEEDS_PERSON = core terms, meanings UNVERIFIED, ask the lead. FD-001 and FD-002 stay UNVERIFIED until the output of `grep -r hadavin_sdk.extract src tools` is pasted. The '92 files, 128 test_*.py' count at line 453 is wrong.

CURRENT STATE 16 Nov 2026 (cold read r6; ONE paragraph; earlier ADDED paragraphs are history but their definitions stay): job key = one of the seven values in the table near line 394; kind = a swappable interface in the core; UNVERIFIED = not checked by running anything; N/A = does not apply. DECISION = inputs/DECISIONS-2026-11-16.md, DECISION-one-store.md = the one-store paper (cite the file every time). FD-001 and FD-002 are leads, not confirmed Majors (grep only). The count '92 files, 128 test_*.py' is wrong; the right count is not recorded (recount TO DO, line 453 unchanged). stage.journal, K1b, NEEDS_PERSON: ask the studio lead.

CURRENT STATE r8 16 Nov 2026 (ONE paragraph). 'DECISION line N' = handover/system-map/DECISION-one-store.md line N (FD-003, FD-004, FD-005 at lines 464-466 included). Job key = STORE, LOG, FILTER, COUNTER, RETRY, NOTICE or OTHER. FD-001 and FD-002 are Leads (unconfirmed), not Majors. The count '92 files, 128 test_*.py' (line 453): count not recorded. SKIMMED = the file was not read (treat as not read). stage.journal, K1b, NEEDS_PERSON: meaning not recorded.

CURRENT STATE r9 16 Nov 2026 (ONE paragraph; wins; lines 477-487 are HISTORY). Terms: take = the filmed lead-intake demo build (repo not visible); mf_leads = the table of leads in the demo database (UNVERIFIED); WARDEN = an earlier project (UNVERIFIED); kind = a swappable interface; UNVERIFIED = not checked by reading or running; N/A = does not apply. stage.journal: meaning not recorded; ask the studio lead before relying on line 394. FD-001 and FD-002 (lines 462-463) read Major but are Leads (unconfirmed). 'real-v5 scenes 1 to 4' and 'decision 1' = inputs/DECISIONS-2026-11-16.md item 1; CORE row, the brief, Plan section 6: meaning not recorded.

CURRENT STATE r10 16 Nov 2026 (read with r9; wins; lines 477-489 are HISTORY). stage.journal and mf_leads: meaning not recorded; FD-003 to FD-005 are UNVERIFIABLE until they are defined. 'DECISION line N' = a line of DECISION-one-store.md (text not quoted). Line 453's '92 files, 128 test_*.py' is wrong (not re-counted). Lines 462-463: read Major as Lead (unconfirmed). Line 465 'chain NEEDED' comes from a skimmed row: unverified. 'The brief', 'Plan section 6' and 'CORE row': meaning not recorded. Job keys: see L3c.md line 299.

CURRENT STATE r11 16 Nov 2026 (read with r10; wins). Words: the take = the filmed demo run; mf_leads, stage.journal, n8n data = three stores whose meaning is NOT RECORDED. FD-003 to FD-005: not usable until the studio lead defines those three stores; do not act on them. FD-001 and FD-002 severity: read 'Major' as 'Lead (unconfirmed)'. 'chain NEEDED' (line 465) = NOT VERIFIED, from a skimmed row. 'The brief', 'Plan section 6', 'CORE row', 'DECISION line N': meaning not recorded; DECISION text is in inputs/DECISIONS-2026-11-16.md (second-hand). Job keys: seven keys are listed in work/L3c.md GLOSSARY r9 (not copied here, TO DO). Table cells still TO DO.

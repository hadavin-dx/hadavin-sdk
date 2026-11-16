# Drift report 2026-11-09 (egm:egm-drift-report, run in the restarted cloud session; 5 documents only)
Branch core/cloud-handover at 455cb65. Source tree: src/hadavin_sdk on this branch. Where a document describes code that lives only on an open PR branch the item says "on <branch>, not on this branch" and is NOT counted as drift. HOW THIS WAS DONE (honest limit): a file-path and named-symbol check of every backticked path in the 5 documents against this branch and against origin/{core/P1a, P1b-fixwip, P4d, P4b1, T1-T2-tests, ci-lint-set, P5a, P2a-1, main}, plus direct greps of J5, A17 and AK-G2 symbols. I did NOT read all 1117 lines of the five documents against code line by line. Items not listed were not checked, not "clean".

## plan-v4-3.md (A18, FROZEN by order 150)
- Not built yet (expected, AK-G2 is sequenced after the P1b and P4d merges): triggers/webhook.py, tests/test_inbound_ledger.py and any inbound-ledger symbol (grep InboundLedger/inbound_ledger in src finds none). CORRECTION of my first draft: hmac_v0 DOES exist (src/hadavin_sdk/approvals/hmac_v0.py is imported by approvals/channel.py and slack.py); what is not built is the door and its ledger. Reported as "not built", not as drift.
- On core/T1-T2-tests, not on this branch: tests/test_t1_meter_cap.py, tests/test_t1_meter_parallel.py, tests/meter_mutants.py; tests/meter_support.py also on core/P4b1.
- test_redactor_accepted_properties.py (named without a folder): not located on any checked branch. DRIFT candidate (name or location unknown).

## amendments.md (A1 to A18)
- A1 / plan-v3: llm/metered.py is PR #48's file (branch core-hardening-1), not on this branch and not on main; the amendment itself records that it lost to Intake budget.py. No drift.
- guard/textnorm.py: on core/P1a, core/P1b-fixwip, core/P5a, not on this branch (expected, P1a/P1b unmerged).
- J5: matches the code: config.py:317 environment: Literal["dev","pilot","prod"], deferred.py:33 LIVE = ("pilot","prod"). The planned deployment_name field is not in src (grep finds none): not built yet.
- Not located on any checked branch: audit/capped.py, guard/tools.py, edge_auth.py, safe_message.py, dump_cp.py, triggers/webhook.py. DRIFT candidates for the owner of each amendment (6 names) except triggers/webhook.py (AK-G2, not built).

## ci-lint-template.md
- .pre-commit-config.yaml and vulture_whitelist.py exist only on core/ci-lint-set (fix batch 2 pending). Not on this branch; expected.

## lint-tools-facts-2026-11-07.md
- Facts file, names no code paths. Nothing to compare. Not a design for code.

## plan-v3.md
- Not located on any checked branch: tools/proof_pack.py, tests/test_secrets_import.py, egm/tools/ledger_lint.py (the last is a laptop studio path, outside this repo). DRIFT candidates: 2 in-repo names.
- guard/textnorm.py: on core/P1a, not on this branch (expected).

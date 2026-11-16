# claims-A (lane A)
(Saved by the session: the builder's Write was refused by the harness; its returned report extracted VERBATIM by script, not edited. Verdicts are proposals; not yet spot-checked by a reviewer. Audited sha b4cce5b.)

## Claims (claim | file:line | code | test and what body asserts | status)
1. Chain rows cannot be updated or deleted | chain.py:11-12 | chain.py:56-66 (SQLite), migrations/0002_audit_chain.sql:28-34 (incl. TRUNCATE) | test_audit_chain.py:129 expects DatabaseError "append-only" on UPDATE/DELETE | SUPPORTED (SQLite); Postgres UNVERIFIED (needs DB)
2. Edited, removed or reordered row breaks every link after it | chain.py:15-16 | chain.py `_check_chain` | test_audit_chain.py:140, 148 assert the exact problem strings | SUPPORTED; deleting the LAST row after the last checkpoint is not detected (chain.py:19 states the unsigned tail)
3. Rewriting a row and every later hash is caught by the signed checkpoint | chain.py:17-20 | `_check_checkpoints` | test_audit_chain.py:154 asserts `["checkpoint 5 was signed over a different history"]` | SUPPORTED
4. Key holder cannot rewrite the anchors (Object Lock, written by another principal) | chain.py:20-22 | anchor_s3.py `IfNoneMatch="*"`, retention | test_audit_chain.py:276 (moto): rewritten and re-signed history caught by anchors | SUPPORTED for detection; "written by another principal" UNVERIFIED (deployment, Q-A5)
5. Outcome events are "all drained by reconcile" | chain.py:216 | no production caller | manual call only | UNSUPPORTED (A-01)
6. Final leak check G5 re-runs the patterns on everything that leaves | redact.py:15-17; gate.py:42-44, 63 | none | none | UNSUPPORTED (A-02)
7. Every host the core calls must be listed in egress.yaml | egress.py:1 | executor.py:71, tools.py:585 only | test_executor.py:119 (executor only) | UNSUPPORTED beyond two callers (A-06)
8. A timeout escalates and never approves; no model output decides | requests.py:1 | requests.py decide/sweep | test_s6_approvals.py:95, 118 (chain to EXPIRED, nothing runs) | SUPPORTED (pass not run)
9. Of two racing clicks exactly one is kept | requests.py:168-170 | memory.py:142-158 CAS | test_p7_tick.py:185 | SUPPORTED (memory); Postgres UNVERIFIED
10. Receiver never executes, so a Slack retry cannot cause double work | receiver.py:1-4 | record_only path requests.py:174-177 | test_p7_tick.py:150 (two ticks execute once) | SUPPORTED (pass not run)
11. Executor looks results up after a timeout instead of retrying | executor.py:3-4 | executor.py:130-147 | test_executor.py:53 asserts exactly one record; :61 lookup fails is unknown | SUPPORTED
12. Executor re-checks plan hash | executor.py:3 | executor.py:106-110 | test_executor.py:70 | SUPPORTED
13. Only the executor is given a secret provider | secrets.py:1 | app.py wiring | tests/test_repo_rules.py (transitive import scan, per guard/http.py:5) | SUPPORTED by test existence; body not read (UNVERIFIED which assertion)
14. Judge prompt hash is in config_hash; config refuses a judge alone | judge.py:5-8 | registry.py:123, :141-144 | test_p6_detectors.py UNVERIFIED which test | SUPPORTED by code
15. Judge is qualified by a golden set run by the evals gate | judge.py:11-12 | judge.py:`qualify`; evals.py not read | none read | UNVERIFIED
16. Injection detector fails closed on any detector error | injection.py:1, 86 | injection.py:85-101 | test_p6_detectors.py UNVERIFIED which | SUPPORTED by code
17. Bedrock guardrail refused at start-up when PROMPT_ATTACK is off | bedrock_guardrail.py:109-110 | `check_filter` | tests/test_p6_detectors.py UNVERIFIED which | SUPPORTED by code
18. GCS and Azure anchors check retention/immutability at start-up | anchor_gcs.py:101, anchor_azure.py:3 | `probed()` both | contracts/kinds/audit_neutral.py fakes | SUPPORTED; S3 has none (A-08)
19. Local sink: a retry never makes a second object; a crash leaves no half file | local_dir.py:3-4 | local_dir.py:84-96 `os.link`, fsync | tests/test_s2_audit.py (5 tests) UNVERIFIED which | SUPPORTED by code
20. Mounted-file secrets: checks run on the opened file | secrets_file.py:58 | secrets_file.py:99-108 fstat | tests/test_p4b_secrets.py UNVERIFIED which | SUPPORTED by code
21. LocalSigner "refused in prod by the environment table" | signer.py:64 | config.py:395-396 refuses only key-file mode | tests/test_audit_chain.py:560 table test | PARTLY SUPPORTED (A-19)
22. Vault Transit kind works with OpenBao | secrets_vault.py:12, signer_vault.py:23 | none | no OpenBao test | UNVERIFIED; the text itself says "not run against OpenBao by us yet" and the table marks `unverified` (honest)

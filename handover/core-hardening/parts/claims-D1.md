# claims-D1 (lane D1). Saved by the session from the builder's returned text (Write refused); condensed by the session: statuses and test file:line kept, long quotes dropped. "Test found" does not mean "test passes" (pytest not run). SUPPORTED means the builder opened the test body and it asserts the claim.
# | claim (source) | test file:line (what the body asserts) | status
1 | core never imports demos/ (README.md:12) | tests/test_repo_rules.py:123 asserts core_imports_demos == []; plant test :211 | SUPPORTED
2 | vendor SDKs only inside their kind module (CLAUDE.md) | tests/test_lockin_guard.py:189 asserts import_problems == []; plant tests :280-330 | SUPPORTED (src only, not demos)
3 | every capability has a neutral prod kind and at least two prod kinds, or a dated exception | test_lockin_guard.py:428 coverage_problems == [] | SUPPORTED (fails after review_by dates: D1-06)
4 | every neutral kind imports no vendor SDK and states "Neutral protocol:" | test_lockin_guard.py:243 | SUPPORTED
5 | runtime, approvals and llm never reach a secret holder, even transitively | tests/test_repo_rules.py:167,305,312,401,464 (names read; bodies of :305 and :167 not opened) | UNVERIFIED
6 | no hardcoded key, account id, ARN or host in src | tests/test_no_hardcoded_values.py:86 findings == []; plant tests :120-129 | SUPPORTED for src; UNSUPPORTED for tests/ (not scanned)
7 | proprietary licence on every LICENSE and pyproject.toml | tests/test_repo_rules.py:117 | SUPPORTED
8 | no tracked third-party reference material or vendor brand strings | tests/test_no_reference_material.py:54,68,90 | SUPPORTED for hash list and name pattern; completeness of vendor-name list UNVERIFIED
9 | tools never go through an environment proxy (README Limits) | tests/test_k5_round9b.py:168 | SUPPORTED
10 | egress refuses loopback, link-local, unspecified, multicast, reserved, cloud metadata addresses and IPv4-mapped, 6to4, Teredo, NAT64 forms | tests/test_k5_round9b.py:~175-195, tests/test_k5_fixes1.py:~120-140, tests/test_k5_round10.py:269 | SUPPORTED
11 | private ranges (10/8, 172.16/12, 100.64/10) stay allowed by design | tests/test_k5_fixes1.py:~143, test_k5_round9b.py:~198 | SUPPORTED
12 | at most 8 name lookups stuck at once; more refused | tests/test_k5_fixes1.py:147-160; code guard/http.py:53-54 | SUPPORTED
13 | name lookup has a 5 s timeout | code guard/http.py:55 RESOLVE_TIMEOUT_S = 5.0; the test monkeypatches 0.01; no test pins 5.0 | UNSUPPORTED for the number (behaviour SUPPORTED)
14 | IP-literal, loopback, metadata hosts refused in a tool manifest | tests/test_k5_round5.py:441-453 (14 spellings; reason not pinned: D1-07) | SUPPORTED
15 | purge step due 60 s early and source scope re-probed every 3600 s | no test found by grep for `interval` or `TICK_SLACK` in tests/ | UNSUPPORTED (D1-03)
16 | failed re-probe switches off every tool naming the source until a probe passes | tests/test_k5_round9b.py:295 (name read; body not opened) | UNVERIFIED
17 | caps per process: concurrent tool calls, calls per minute, abandoned-body ceiling | tests/test_k5_round9b.py:113, :158 | SUPPORTED
18 | redact_text refuses more than 256 KiB (defaults.py:31-32 = 262144) | tests/test_k5_fixes1.py:29-52 | SUPPORTED
19 | redaction scanning-bound fallbacks mask instead of passing text through (bounds 1024, 255, 254, 4096, 129) | no test found by grep for those numbers (may be tested through symbolic names) | UNVERIFIED (lane A and D3 to check against guard/redact.py)
20 | redaction cost bounded polynomial, about 3 s CPU for 256 KiB | perf tests tests/test_k5_fixes2.py:185-195 (<5.0 s), tests/warden_port/test_redaction_bank.py:354-362 (<15.0 s), tests/test_k5_perf.py (not opened); quoted measurements not asserted | UNVERIFIED
21 | redaction maps kept 30 days (400 under hold); no hold outlives 400 days; raising hold hook skips ordinary purge but ceilings still run | tests/test_k5_review.py:497-510 (30-day purge); no test mentions HELD_MAPS_CEILING (config.py:176) | SUPPORTED for 30-day purge; UNVERIFIED for the 400-day ceiling
22 | runtime role has no DELETE; purge role reads only needed columns and cannot write or truncate; migrate asserts privileges | tests/test_k5_round10_postgres.py:33-80, tests/test_k2_migrations.py:214-230, superuser purge role refused :153-157 | SUPPORTED on a real Postgres only (tests skip without the DSN: D1-10)
23 | redaction maps hold originals of identifier kinds as plaintext JSON; encryption at rest is the deployment's job | statement of a limit | UNVERIFIED (not a guarantee)
24 | grounding is whole-token, exact in case; generated_suffix; case_insensitive_targets | tests/test_k5_round9b.py:205 (generated_suffix; name read); case_insensitive_targets only wiring at tests/k5_support.py:194 | UNVERIFIED for case folding; generated_suffix partly SUPPORTED
25 | caught_by=guard only when a guard stopped a concrete proposal; failures are not catches | tests/test_k3_leftovers.py:63-82, tests/test_k3_pilot.py:436-450; ungrounded, uncited, invalid_proposal mapping not found | PARTLY SUPPORTED (3 of 5 guard reasons and the two non-catches)
26 | tooled agent action contracts must set additionalProperties: false | positive cases tests/test_k5_fixes2.py:206-226; refusal test not located | UNVERIFIED
27 | every read is an audit event and a tool_calls row | tests/test_k5_tools.py:1115 (inputs_hash length 64), :371-381 (stored rows hold no raw secret); rows and output_hash fields not located | PARTLY SUPPORTED
28 | nothing of one client kept in a process-global cache | tests/test_k5_round6.py:124-126 (keys are 64 characters, no raw value); other caches keyed by single characters or operator config | SUPPORTED for the one cache that could hold client text; no cross-client test (UNVERIFIED against R373)
29 | `replay` refuses a non-empty OUT; `score` refuses an OUT holding FAILED.txt | tests/test_k1b_replay.py:346, :478; test_k1b_score.py:198-215; tests/test_k1b_cli.py:155-156 | SUPPORTED
30 | redaction stated limits (SECURITY.md:9-14) | tests/warden_port/test_redaction_review*.py and test_redaction_classes.py exist; no body opened asserting the quoted limit | UNVERIFIED
31 | fake credentials in tests built from parts; only literal AKIAIOSFODNN7EXAMPLE | grep over tests/ found only that literal (plus parts-built values at tests/conftest.py:34-35); enforcing test scans src/ only | SUPPORTED by grep, UNSUPPORTED by a test
32 | every reversible/manual action contract names an existing undo or rollback test | tests/test_repo_rules.py:101,127 (names read; plant tests :105,:184 not opened) | UNVERIFIED
33 | test-count claims: none found in README, SECURITY.md or docs in this lane; AST count of test functions = 1419 (tests/ minus demo_askdata); pytest collected count UNVERIFIED | - | UNVERIFIED

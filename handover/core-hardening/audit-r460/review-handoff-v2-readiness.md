# Hand-off v2 readiness review (egm-implementation-readiness, read-only, condensed copy), 2026-11-16
Codeable with small guesses: PR-0, G0, G1, PR-2 (extract), PR-3, M1, D1 (wording), E1. NOT codeable as written: M2/M3 plumbing, G4 shapes (G2-G5), later audit PRs (D3-D6), E2. Ran nothing; markdown_it missing.
## Blockers
1 PR-M2/M3: no way to carry run context (agent_id, run_id, day, max_run_usd) to the ledger: LLM.chat (llm/protocol.py:18-28) has none; `request` in before/after hooks undefined; contextvar does not cross the daemon thread (k1b/loop.py:94-104); judge built once at app.py:165 has no run; evals (evals.py:73) no run; adapters (llm/retry.py:83-108, llm/common.py) have no store, so on_attempt has no owner. Needs a concrete call-context type, who sets it, hook signatures.
2 PR-G2..G5: no grammar to implement; gate.py never read beyond lines 1-12, 366-377; rows are audit ids with examples, no functions/regexes/ordering.
## Majors
3 retry bookings can count 2-3 times (§5.3 line 141 worst_case x max_attempts on ProviderExhausted vs line 144 per failed attempt vs §5.4 settle again; retry.py:100-103 raises on last attempt). Pick one mechanism; state ledger total for exhaustion.
4 eval pseudo agent "eval:<agent>" breaks Limits.blocked (limits.py:25 KeyError); eval_budget_usd meaning (day/month/per run) undefined; evals.py:109 builds judge with the llm given.
5 PR-1 wrap point (app.py:162) does not cover extract(), k1b replay (k1b/loop.py:94), evals; "only llm/guarded.py and kind modules may call .chat(" is false today (5 non-kind callers: extract.py:47, evals.py:73, judge.py:72, agent_loop.py:425, k1b/loop.py:94); state the real test.
6 PR-D1 tamper_evident almost never true: requires unsigned_tail==0 but ChainAudit checkpoints every 100 rows (chain.py:161); also Verification.signed when public_key exists but checkpoints empty.
7 PR-E2: existing check (secrets_file.py:49-58) allows group-readable, v2 says refuse 0644; confined() resolves symlinks before O_NOFOLLOW; no function name for fileguard.py; layer-test (F14) open; secrets_file imports actions.secrets_cache and config.confined.
8 PR-0 (D6): pydantic gives generic error, ConfigError naming the rename needs field_validator(mode="before") or loader wrapper; site list incomplete (backends/table.py:591-593, registry.py:50, deferred.py comments/LIVE); D6 cites table.py:604 which is NOT_PROD, no dev reference.
9 PR-M3: wall-hit card production undescribed (agent_loop.py:243-249, :702 "stop means stop: no card", authorizer.py:44); D9 test does not assert a card.
10 Zero-price routes unbounded between M1 and M5 (max_steps only); D11 calls it "PR-M6" which does not exist; judge route (judge.py:3-4) not an agent route; M5 migration unspecified.
11 PR-D3..D6 too thin: anchor_age_s undefined, retain_days key/default, outbox threshold, anchor-writer field name, negative test without Postgres.
12 PR-R1..R3 only audit ids; redact.py not read.
## Nits
13 worst_case_usd takes Route but call sites have only route name; 14 extract() mapping param changes test sites test_k5_round9.py:108, test_s4_llm_guard.py; 15 F9 misses blocked callers agent_loop.py:744, actions/authorizer.py:44; 16 with_retry is retry.py:83-108; 17 literal 4111 also in warden_port/privacy_corpus.py:42, test_redaction.py:309,356; 18 safe_head length/map args at cli.py:75, :300-305; 19 k5_cfg(config=...) merge unverified; 20 crash-between-reserve-and-settle is honest but fix-dont-defer says fix.
Not checked: redact.py, gate.py beyond cited lines, store/memory.py, adapter bodies, test_k5_layers.py, anchors, demos/, ledger.md, ci.yml, pyproject, Money/NaN claim, FOR UPDATE.

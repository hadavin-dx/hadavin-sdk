# Hand-off v3 readiness review (egm implementation-readiness, condensed copy, 2026-11-16)
Read only; nothing run (markdown_it missing). Verdict: v3 far better than v2; PR-0, G0/G1, M1, PR-2, S1, G2 codeable with small guesses. M2a/M2b and G3 NOT codeable as written. 2 Blockers, 9 Majors, 7 Nits.
## Blockers
- B1 M2a (4.3): central atomic cap check undefined: reserve_spend takes no daily/monthly limit, no refusal outcome; unclear if open reservations count in spend_totals / Limits.blocked (limits.py:20-30; postgres.py:416-442; memory.py:196-216); who compares caps; which exception; settle_spend must also update store.add_cost(run_id) (agent_loop.py:246).
- B2 G3 (5): pinned vs withheld examples share one lexical shape (drop table users vs drop table pressure; delete from users vs "delete from the queue only after a fix"; update only t as a set x=1 vs "update its set of rules"; tests/test_g4_parity.py:98,221-222). Builder must invent a discriminator: a design choice.
## Majors
- M1 double booking: loop charges at agent_loop.py:440-441 and _screen :313-315; v3 never says delete them.
- M2 "fake passes through unbooked" vs s5 test change: GuardedLLM has no kind argument; Runtime tests build Runtime directly (k5_support.py:160-204).
- M3 CLI eval path (cli.py:146-153) has no store/limits; gate also runs judge.qualify; eval_budget_usd default 0 would fail a live gate.
- M4 extract(): masking turns emails/phones/IBANs into placeholders and the map is dropped; no in-repo caller, scope contract undefined.
- M5 retry booking: non-ProviderError exception from inner.chat() unspecified; "keep one worst case" has no API (settle/release/sweep only).
- M6 tamper_evident: anchor_age_s not computable (anchor.all() has no timestamps, chain.py:353); outbox rows not in formula; max_unsigned_tail config key unnamed.
- M7 A2 (D3-D6): config keys retain_days, outbox_alert_age_s, anchor-writer identity unnamed; S3 Object Lock probe has no function name.
- M8 G4/G5 rows: _story example already withheld today (real bypass is punctuation token after program, e.g. kubectl > /dev/null delete pod x; tokens do not cross newlines gate.py:546); no get-secret-value entry to remove (get- generic prefix gate.py:404,597); _join_continuations output semantics; _WRITE_SHAPES regexes missing; normalise before _OWN lookup.
- M9 wall-hit card (4.4): _limits_stop (agent_loop.py:239-244) ends limits.* with no card; :702 says no card; v3 does not reverse :702/:669; kill_switch must stay card-less; POLICY_STOP_REASONS module unnamed.
## Nits
N1 test_k5_layers.py is about secrets layers; import rules are in tests/test_lockin_guard.py (LIBRARY_IMPORTS:68). N2 k1b worst_case_usd failure behaviour; allowlist test method; reuse llm/common.py:167. N3 SpendScope.purpose / run_cap_usd have no consumer/enforcer. N4 D6: load_config wraps message (config.py:453): test substring only. N5 D11: check no fixture route uses zero price. N6 R2/R3 patterns lack names/regexes; guard importing k1b inverts layering. N7 fileguard facts match.
## v2 findings
Closed: 5 (wrap point), 7 (E2), 8 (D6), 10 (zero price). Mostly: 3, 6. Partly: Blocker 1, Blocker 2, 4, 9, 12. Not closed: 11 (M7). Lead/owner decisions D1, D5, D6 alias, FA have safe defaults and do not block building.
## Not checked
Adapter bodies, cloud kinds, Postgres FOR UPDATE behaviour, rest of test_s5_runtime.py and k5_support.py, 0.0155 arithmetic, redact.py beyond grep, deferred.LIVE, anchor timestamps, approvals/channel.py, demos, ledger.md, ci.yml, any G4 example run.

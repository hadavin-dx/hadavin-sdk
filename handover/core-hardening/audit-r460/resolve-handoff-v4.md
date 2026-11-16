# Resolve log: hand-off v3 to v4 (2026-11-16)

Nothing here is "verified": nothing was run (no tests, no G4 strings, no Postgres; `markdown_it` is missing). "Fixed in v4 at" means the design text was changed from code I read; E0 (v4 section 7) verifies. Outcomes: FIXED (where), CONTESTED (evidence), LEAD (decision D-n with safe default), DROPPED (reason).

## Readiness review (B1, B2, M1-M9, N1-N7)

| # | Finding | Outcome | Where / evidence |
|---|---|---|---|
| B1 | Atomic cap check undefined; open reservations vs `spend_totals`; who compares; exception; settle must update `add_cost` | FIXED | 4.1: `SpendMeter.reserve` adds via `add_spend`, compares the returned totals, undoes and raises `SpendRefused(code)` on breach; reservations ARE counted (they are spend); `Limits.meter` is the one comparer; `settle` writes `add_cost` once. Evidence: `memory.py:196-204`, `postgres.py:416-431`, `0001_core.sql:87-92` |
| B2 | G3 pinned vs withheld share one lexical shape | FIXED | 4.9: one concrete rule (code markers M1-M5), 12 lines run mentally and listed. Finding that v3 missed: `_WRITE_SHAPES` is case-sensitive today (`gate.py:647-678`) so the pinned lines are shown because of case; bare lowercase stays shown (D16) |
| M1 | Double booking; v3 never says delete | FIXED | 4.2 removal sites: delete `agent_loop.py:440-441` and `:313-315`; `settle`/`keep` are the only `add_cost` writers; census test |
| M2 | "Fake passes through unbooked" vs the s5 test; `GuardedLLM` has no kind | FIXED | 4.2: no kind logic in the wrapper, fake replies are booked like real ones; CLI makes the one fake exemption for eval (4.3); `tests/test_s5_runtime.py:107-111` rewritten (refused at reserve, no model call); wrapper built inside `Runtime` so `build_runtime` tests exercise it |
| M3 | CLI eval path has no store; judge qualify; default 0 would fail | FIXED | 4.3: store built like `cli.py:179-184`; one metered llm covers agent and `judge.qualify`; fake kind uses the raw llm; refusal becomes `ConfigError` naming `eval_budget_usd`; memory-store caveat stated |
| M4 | `extract()` masks identifiers; map dropped; scope undefined | FIXED | 4.7: placeholders stay, `Valid.mapping` returned, no restore inside `extract`, caller restores with a kinds allowlist; non-UTF-8 and redaction failure return a dead letter with no model call |
| M5 | Retry booking: non-ProviderError exception; "keep one worst case" has no API | FIXED | 4.1 adds `keep`; 4.2 maps `ProviderExhausted` and any other `Exception` to `keep`, `ProviderError` to `release`; totals pinned |
| M6 | `anchor_age_s` not computable; outbox rows; unnamed config key | FIXED (by cutting) | 4.6: `anchor_age_s` and `outside_chain` dropped (no timestamp on `anchor.all()`, `chain.py`/`anchor_s3.py:70`); threshold reuses `checkpoint_every` (no new key); outbox limit stated in the CLI sentence |
| M7 | A2 config keys and Object Lock probe unnamed | FIXED / LEAD | 4.11 H-1: existing `retain_days` (`anchor_s3.py:96`, `anchor_gcs.py:76`, `anchor_azure.py:95`) gets a floor; probe is `anchor_s3.probed(client, settings)` modelled on `anchor_gcs.probed`; `outbox_alert_age_s` and anchor-writer identity deferred, D18 with trigger |
| M8 | G4/G5 rows: `_story` example wrong; no `get-secret-value` entry; join semantics; regexes; normalise order | FIXED | 4.9: real bypass `kubectl > /dev/null delete pod x` (word after the program, `gate.py:608-615`); `_AWS_NOT_READ` set added because `get-` is a generic read prefix (`gate.py:404,597`); join output defined; regex shapes written for the rows that ship; normalisation order stated; rows with no traced leak became candidates that ship only if E0-6 shows a leak |
| M9 | Wall-hit card edits; `:702` vs `:669`; kill switch; `POLICY_STOP_REASONS` unnamed | FIXED | 4.4: edit sites `:239-247`, `:425` try block, `:87` text; `:669` and `:702` unchanged on purpose with reason; kill switch card-less; `POLICY_STOP_REASONS` named beside `GUARD_STOP_REASONS` (`:83`), report-only; `caught_by` stays None because K6 counts every non-null value |
| N1 | `test_k5_layers.py` is about secrets layers | FIXED | 4.8: guard file is `tests/test_lockin_guard.py:68-75`; stdlib-only module needs no rule |
| N2 | k1b `worst_case_usd`; allowlist method; reuse `llm/common.py:167` | FIXED | 4.1: new `worst_case_usd` in `llm/common.py` with documents; k1b copy left alone (k1b out of scope, trigger named); allowlist method is the census test |
| N3 | `SpendScope.purpose` and `run_cap_usd` have no enforcer | FIXED | `SpendScope` removed; `run_cap` enforced in `reserve` (D14) |
| N4 | `load_config` wraps message | FIXED | 4.11 H-0: tests assert a substring only |
| N5 | Check no fixture route uses zero price | FIXED | 4.5 and E0-5 grep |
| N6 | R2/R3 patterns lack names and regexes; guard importing k1b inverts layering | FIXED / DROPPED | 4.10 names each pattern (`PHONE`, `IBAN`, `CREDITCARD`, `EMAIL`, `CREDPAIR`); regexes are written when E0-4 shows the leak (a regex for a pattern that may not ship would be guesswork); shared credential-key test is shared as a function, the guard imports nothing from k1b in this design |
| N7 | fileguard facts match | NOTED | no change needed |

## Zoom-out review (M-1..M-9, N-1, N-2)

| # | Finding | Outcome | Where / evidence |
|---|---|---|---|
| M-1 | Reservations table, sweep, TTL duplicate `add_spend` | FIXED (zoom was right, with two stated limits) | 4.1: `add_spend` can do it; table, sweep, TTL, `expired_kept`, `reserve_spend`/`settle_spend`/`release_spend` store methods, `try_mark_wall_notice` all removed. Limits written down: transient over-refusal under parallel callers; orphan after crash stays counted (D15). Postgres two-connection behaviour is unverified (E0-3) |
| M-2 | Split mixes safety and housekeeping | FIXED | Section 6: gating track (8 PRs) and housekeeping track (3); PR-0 became H-0; A2 cut to H-1 (floor and probe); E3 became H-2 (docs) |
| M-3 | G2-G5 chase an unbounded grammar | PARTLY CONTESTED | Ship-only-what-leaks rule (4.9) and a candidate list implement the cheaper path. "Withhold every code-like span by default, approver reveals on request" is not adopted: it is the allowlist already rejected for the 2% false-positive budget; a reveal path also changes the approver UI. Trigger kept: E0-6 |
| M-4 | Three mechanisms where two do | FIXED | 4.2: per-caller wrapper, no ContextVar (the daemon thread in `k1b/loop.py:94` shows a ContextVar does not cross threads; the `LLM` protocol stays unchanged). The judge is reserved in `_screen`, so it needs no wrapper. k1b meter and a repo-wide `.chat(` rule are out; a five-line census test replaces the rule |
| M-5 | Knobs without need | FIXED | Dropped: reservation TTL, `max_unsigned_tail` config key (reuses `checkpoint_every`), `outbox_alert_age_s`, anchor identity (D18). Kept `eval_budget_usd` (default 0, needed by the CLI). D5 reframed: Decimal already rejects floats; the question is Decimal versus integer minor units, the owner's call |
| M-6 | Four new Verification fields | FIXED | 4.6: two booleans plus the threshold value; `anchor_age_s`, `outside_chain` dropped |
| M-7 | New fileguard duplicates `secrets_file` | FIXED | 4.8: the checks move out of `secrets_file._fetch` into the shared function, one copy |
| M-8 | R1+R3/R2 bundle with no corpus | FIXED | 4.10: PR-2 first and alone; patterns ship only if the canary leaks on old code; base64 deferred (D17) |
| M-9 | Caveat repeated | FIXED | Stated once in section 0; one status column per PR in section 6 |
| N-1 | Object Lock probe in S3 kind module; invoice reconcile has no named alternative | FIXED | 4.11 and section 5; section 0 item 4 says no alternative exists |
| N-2 | Which identity may release or refund | FIXED | Section 5 and D15: runtime identity releases only its own reservation (negative delta, no new right); orphan refund is a manual audited write by the migrations/DBA identity |

## Decisions that stay with the lead or owner (each has a safe default in v4 section 3)

D1, D5, D6 (alias), D11, D12, D4, FA, RC (from v3, unchanged) and new D13 (wall dedupe store), D14 (run cap inside reserve), D15 (orphan reservation), D16 (bare lowercase SQL), D17 (base64 and speculative patterns), D18 (anchor writer identity, outbox alert).

## Not fixed, with reason and next step

- Postgres behaviour of the reserve under two connections: not runnable here (no Postgres). Next step: E0-3 on the lead's runner.
- Which other existing tests break under the reserve: not read. Next step: E0-1 at the M2 head and E0-5.
- Whether G2a, G2b, G3 and G4a rules leak or hold on the real gate: hand-traced only. Next step: E0-6.
- Provider billing of aborted attempts: third party (2c), monthly invoice reconcile, owner named by the lead.

## Searches for deferral words

I wrote no "known limitation". Each "deferred" item has a trigger and a decision id in v4 section 3; each limit of the chosen reserve design is written in v4 4.1 with its test.

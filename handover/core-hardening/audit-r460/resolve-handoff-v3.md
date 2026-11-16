# Resolve log: hand-off v2 to v3 (2026-11-16)

Nothing here is "verified": nothing was run (no tests, no G4 strings, no Postgres; `markdown_it` missing). "Specified" means written down from code I read; the E0 batch (v3 section 7) verifies it.

## Readiness review

| # | Finding | Resolution in v3 | Status |
|---|---|---|---|
| 1 | No call-context carrier | 4.1 `GuardedLLM` + `SpendScope` (ContextVar), protocol unchanged; who sets it listed per caller; k1b out of scope with reason and a repo test | specified, unverified |
| 2 | No G4 grammar | Section 5, per PR: function, rule, withheld and shown example; gate.py read | specified, unverified |
| 3 | Retry counted 2-3 times | 4.2 one mechanism; totals: success actual, ProviderError 0, Exhausted one worst case | specified, unverified |
| 4 | `eval:` id breaks `Limits.blocked` | Eval ledger separate; never calls `blocked` with a pseudo id; `eval_budget_usd` daily/monthly, default 0 | specified, unverified |
| 5 | Wrap point misses callers; false `.chat(` claim | Real caller list (F9); scope opened per caller; own-meter allowlist test for k1b | specified, unverified |
| 6 | `tamper_evident` almost never true | 4.8 rule with `max_unsigned_tail` (default 100); healthy chain can be true | specified, unverified |
| 7 | E2 wrong about group-read, symlink, names | 4.9 `read_private_file`, decision on group-read, symlink rule, layer test | specified, unverified (layer rules unread) |
| 8 | D6 error mechanism, sites | 4.7 `field_validator(mode="before")`, full site list, `table.py:604` corrected | specified, unverified |
| 9 | Wall-hit card undescribed | 4.4 `try_mark_wall_notice`, one card per agent/day/code | specified, unverified |
| 10 | Zero-price routes; "PR-M6" | 4.6 refuse at load (fake exempt); flag deferred with trigger; "PR-M6" removed | specified, unverified |
| 11 | D3-D6 thin | 4.8 fields and defaults defined; Postgres-only tests marked unverified | specified, unverified |
| 12 | R1-R3 only ids | 4.10 pattern-level specs after reading redact.py | specified, unverified |
| 13 | `worst_case_usd` takes Route | Seam holds routes; looks up by name | specified |
| 14 | `extract()` test sites | PR-2 re-keys recordings; call sites listed in the PR | specified |
| 15 | F9 missed callers | Added `agent_loop.py:744`, `authorizer.py:44` | fixed in text |
| 16 | `with_retry` lines | `retry.py:83-108` | fixed in text |
| 17 | `4111` sites | Added | fixed in text |
| 18 | `safe_head` args | Not changed by v3 designs; E0-4 re-checks | not re-examined, see below |
| 19 | `k5_cfg` merge | Read: shallow update replaces `routes`; new test uses a full dict | specified |
| 20 | Reserve crash "design choice" | 4.3 persisted reservation, sweep, `expired_kept`, audit | specified, unverified |

## Zoom-out review

| # | Finding | Resolution | Status |
|---|---|---|---|
| M1 | D1 mandatory in prod | Demo/pilot require date; prod date or explicit `none`; flagged for lead | specified, needs lead |
| M2 | D6 breaks `dev` configs | Default follows R449 (refuse and name rename); alias needs owner; E0-8 greps demos; CHANGELOG step | needs owner (alias) |
| M3 | Self-attested zero-cost flag | Refuse zero prices (fake exempt); flag and calls cap deferred, trigger named | specified |
| M4 | Two ledger APIs | M2a/M2b split by layer; `book_cost` and `on_attempt` deleted | specified |
| M5 | Decimal vs integer | Default Decimal with guards; owner decides before M2a | needs owner |
| M6 | Reserve crash | See readiness 20 | specified, unverified |
| M7 | Settle can raise | Clamp and log `spend_clamped`; day stored in reservation | specified, unverified |
| M8 | G4 open-ended denylist | Allowlist considered and rejected with reasons and a named trigger | specified, decision recorded |
| M9 | Wall hit dedupe, false-abstain | 4.4 plus E0-9 split and ceiling decision FA | specified, needs lead (ceiling) |
| M10 | Reserve sizing | E0-5 dry run over all configs | specified, not run |
| N1 | Over-uncapped PRs | Tags: C for PR-0, G1, E3; U only for money, redaction, audit, secret, G2-G5 | specified |
| N2 | Merge PRs | R1+R3, D2 into D3, E1 into E3 | specified |
| N3 | Pass-through seam | Fake kind passes through; PR-2b hooks later | specified |
| N4 | Over-claim | Section 0 and "specified, unverified" wording | fixed in text |
| N5 | D4 deadline | Before first pilot config | needs owner |
| N6 | Caveat placement | Section 0 item 5 | fixed in text |
| N7 | D12 timezone | Deferred, trigger named, month-edge analysis recorded | deferred with trigger |

## Not fixed, with reason (next step, date 2026-11-16 to assign)

- Decimal vs integer money: owner decision (exception b). Default stays Decimal with guards.
- Alias for `dev`: contradicts R449, owner yes needed (b).
- Refusing signer/anchor kind `none` in pilot: owner (b), deadline before first pilot config.
- Provider billing of aborted attempts: third party (c). Next step: monthly invoice reconcile.
- Self-hosted zero-price route, calls cap, local billing day: deferred with named triggers; no such route or client exists today.
- Readiness 18 (`safe_head` args at `cli.py:75,300-305`): I did not re-read these call sites in this pass; E0-4 covers them. This is a gap I did not close.

## Searches for deferral words

I wrote no "known limitation". Every item above is either specified, or classed under exception (b) or (c) with a next step. "Not checked" lists are in v3 sections 0 and 9.

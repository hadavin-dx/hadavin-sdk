<!-- full hand-back report of sub-agent a8768ee3, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, Q8a-1 round 2, head f6fad26f (design critic, read-only, fresh reviewer)

## Failures and gaps first

- **No evidence exists for this head.** `/home/user/hadavin-sdk/handover/evidence/Q8a-1/f6fad26/` is absent; only `464dee1/` is there. Every "passes" for the fix commit is unproven: the new and changed tests, the two Postgres positive tests, mutants M12a-g and M13a-b, ruff, format, bandit and the guard tests.
- **I ran nothing.** All findings come from reading the two patches, the head files, the main export and the rule files.
- **Verdict: not clean.** No Blocker in the code as read. 1 Major (the `run_tick(steps=)` sibling), 9 Minor.
- **Two reads outside the stated set.** I grepped `/home/user/hadavin-sdk` (tests, demos, docs) for callers of `sources=`/`tools=`/`steps=`, because the main export could not answer that. I did not read `handover/ledger.md`, so every "owner question logged" claim in D-012 is unverified.

## Major

**MJ1. `run_tick(steps=...)` is left open on the same line that now refuses `now=`.**
- Where: `/home/user/build/snap/q8a1-f6fad26/src/hadavin_sdk/runtime/tick.py:337, 359`.
- Scenario: a pilot scheduler wrapper copied from `tests/test_p7_tick.py` (lines 107-664 use this form throughout) calls `run_tick(app, steps=[TickStep("x", 0, fn)])` or `run_tick(app, steps=[])`.
- Wrong outcome: the tick returns 0 with no sweep, no reconcile, no stuck check, no audit checkpoint and no evidence purge.
  - Redaction maps (plaintext originals) and tool calls are kept past retention for ever.
  - Approvals are never escalated, and approved runs are never advanced (the receiver is record-only).
  - Exit code 0 tells the scheduler the tick is healthy, so nothing alerts.
- Why Major: it is the same accident class as `now=`, on the same function, and fails silently. No `src` caller passes `steps` (`cli.py:309` is `run_tick(app)`); the module docstring says later work appends to `STEPS`. The builder named it and did not fix it, which `class-level-fixes.md` and `fix-dont-defer-be-honest.md` do not allow without a 2(a)-(c) reason.
- Fix now: beside the `now=` check, `if steps is not None and is_live(...): raise ConfigError("steps= is for tests; it is refused in pilot and prod")`. Add a killer in `test_stage_names.py`, a mutant M13c, and a CHANGELOG line. If an embedder must add a step in live, the weaker form is to refuse any list that does not contain every member of `STEPS`.

## Minor

**mn1. The head contradicts the frozen ticket with no erratum.**
- Where: `TICKET.md` Behaviour 2, E3 ("assert with `load_config` only"), E4 ("(CFG) make the Vault rule never match") and the frozen message text; versus `app.py:121-123, 319` and `tests/stage_mutants.py` M12b.
- D-012 records the decisions, but the ticket says its errata win and it has none for: the move out of `Config._cross_checks`, the new message "(recommended)", `run_tick`, and the `sources=`/`tools=` change.
- The ticket's fail-on-main list (8 Vault cases via `load_config`) no longer matches the tests.
- Fix: add errata rev 4 before the drift report, and rerun the fail-on-main proof for the rewritten tests.

**mn2. The static token can still reach scheduled, non-interactive jobs in pilot and prod.**
- Where: `/home/user/build/snap/q8a1-f6fad26/cli.py:146-153` (gate), `184-190` (limits, audit verify), `215-223` (replay, score), `329` (migrate).
- Scenario: a prod CronJob runs `hadavin-sdk audit verify`, or a batch runs `replay`, with a static `VAULT_TOKEN` in its environment. It is accepted; round 1's loader rule refused it.
- The CHANGELOG states this honestly. It is still a least-privilege residual that needs the owner (exception 2(b)).
- Fix: confirm the owner question has a next step and a date. One option to put to the owner: apply `_static_vault_tokens` in `cli.py` to `gate`, `replay` and `score` (not emergency tools; they call the model) and leave `limits`, `audit verify` and `migrate` open.

**mn3. The limit wording omits known siblings.**
- Where: `app.py:101-104`; `CHANGELOG.md` line 14.
- Not named: `run_tick(steps=)`, `Approvals.sweep(at=)` / `resend_unsent(at=)`, a direct call of `backends.factory.make`, and a leftover patch of `app.make` or `app.now` (round-1 m5 listed the last).
- "Any route that does not pass through them" covers these in general, but a known route on the same function should be named until it is fixed.
- `app.py:96-99` says "a person may run those with a short-lived token of their own" without the CHANGELOG's "Nothing checks how long that token lives". Add that sentence.
- "The long-running process" is loose: `tick` is a one-shot run every 30-60 s and the SDK ships no long-running command. Precise wording: "every process that calls `app.build`".

**mn4. `Approvals.sweep(at=)`, `resend_unsent(at=)` and direct `Approvals(clock=)`: record, do not fix here.**
- Where: main `approvals/requests.py:58-69, 131-134, 191-193`.
- `sweep(at=<future>)` escalates or expires approvals early. That fails closed: an expired approval never runs a plan, and no evidence is deleted.
- `resend_unsent(at=<future>)` sends a duplicate card.
- A fixed past clock on a hand-built `Approvals` makes `decide` (line 154) accept a decision after expiry. That fails open, but needs direct construction or attribute assignment, which the limit text names.
- `Approvals` holds no stage, so a refusal needs new plumbing. Record as a ledger item against Q8a-2, with these three named in the limit text.

**mn5. `run_tick` raises where its contract is "returns an exit code".**
- Where: `tick.py:344-345`; module docstring lines 12-15 not updated.
- Scenario: a wrapper `sys.exit(run_tick(app, now=t))` in pilot dies with an uncaught `ConfigError`. Python exits 1, which the tick contract defines as "a step failed". The CLI maps `ConfigError` to 2 only inside `cli.main`.
- Fix: state the raise in the module docstring's exit-code list, or log and return 2.

**mn6. `timeout_s` message and config mismatch.**
- Where: `app.py:151-153, 325-329`.
- `timeout_s=float("inf")`, `"5"` and `True` all get "timeout_s= must be greater than 0". Infinity is greater than 0. Say "a finite number greater than 0".
- The config field `executor_timeout_s` is `Field(gt=0)` (main `config.py:360`). I believe pydantic accepts `.inf` there by default; not checked. If so the keyword is stricter than the config.
- Order is correct: live refusal first (`app.py:141-150`), so pilot `timeout_s=0` gets "is for tests"; validation runs in demo only.

**mn7. The seam still does not record `**available` or settings content.**
- Where: `tests/test_k3_pilot_env.py:199-205`.
- It records `(capability, kind, provider)` only. A regression that drops `store=` for the channel, `routes=` for the llm, or `signer=`/`anchor=` for the audit stays green when that capability is planted.
- The purge-store call is checked by count (2), not by `dsn_secret_name`; the Postgres behaviour assertion covers that only when not skipped.
- `asked()` returns sets, so order is unchecked except `calls[0]` in one test.
- Fix: record `sorted(available)` and assert it per capability.

**mn8. New behaviour in this commit has no mutant.**
- No mutant for: `sources is not None` / `tools is not None` reverting to truthiness (`app.py:132, 135`); `_positive_number`; the Vault check moved after `make("secrets", ...)`.
- Only `clock` and `timeout_s` have a dropped-name mutant, not the other four keywords.
- Add at least the two truthiness mutants, with killers in `test_stage_names.py`.

**mn9. "Must be built on this class" is a convention nothing enforces.**
- Where: `backends/table.py` `VaultConnection` docstring.
- A kind whose own settings class has `auth`/`token_env` and does not subclass `VaultConnection` passes in prod.
- Fix: a guard test that every `TABLE` settings class with a `token_env` or `auth` field is a `VaultConnection`.

## Answers to the nine questions

**(1) Round-1 findings:** see the table below.

**(2) The moved Vault check.**
- Only `app.build` refuses now (`app.py:120-123`); `config.py` is back to main (it is absent from `DIFF-vs-main.patch`).
- Entry points that do not go through `build`:

| Entry point | Where | Static token reachable in pilot/prod? |
|---|---|---|
| `gate` | `cli.py:146-153` | Yes |
| `limits stop` / `reset`, `audit verify` | `cli.py:184-190` | Yes |
| `replay`, `score` | `cli.py:215-223` via `k1b/audit_sink.py:59-72` | Yes |
| `migrate` | `cli.py:329` | Yes (reads the CA only) |
| `approvals.receiver.serve(approvals)` | library, no command | Only with a hand-built `Approvals`; otherwise it comes from `build` |
| `backends.factory.make` called directly | library | Yes |

- `App(`, `Runtime(` and `Approvals(` are constructed only in `app.py` within `src`. `tick` goes through `build` (`cli.py:299`).
- So a static token cannot reach a process that calls `build`. It can reach every one-off command and any embedder that wires `make` plus its own objects.
- The CHANGELOG "covered / not covered" list is true for the commands. It does not mention direct `make` (mn3).
- The move was the right trade: a refusal that can block the kill switch is worse than the risk it removes. The cost is mn2.
- The check runs before any backend, which matters for the signer: `signer_vault.build` probes at construction and would read the token.

**(3) `run_tick(now=)`.**
- Placement is right: first statement, before `TickContext` and the store probe.
- The `is None` change is behaviour-neutral (a datetime is never falsy).
- `steps=`: Major, fix now (MJ1). `sweep(at=)`, `resend_unsent(at=)`, direct `clock=`: Minor, record (mn4).

**(4) Empty `sources={}` / `tools={}` refused in live: accept.**
- One rule ("given means not None") for all eight keywords. An empty mapping in a live start signals a wrapper forwarding test seams, and the remedy is trivial.
- No documented caller relies on it: the only `src` caller is `cli.py:299`, and my grep of repo tests, demos and docs for `sources=`/`tools=` with `{}`, `None`, `dict()` or `x or {}` found no `build` call.
- It is a ticket deviation and needs the erratum in mn1.

**(5) `timeout_s`:** order correct; wording issue in mn6.

**(6) `VaultConnection` public.**
- `table.py` has no `__all__`, so the surface grows by one documented name. The private name had no user outside `table.py` on main.
- `tests/test_lockin_guard.py` on main names only `Entry`, `KindSettings` and `S3ObjectLockSettings`. I found no table class-name list and no `__subclasses__` enumeration, so nothing breaks by reading.
- The tests add module-level subclasses (`_VaultBuilt`, `_Reads`) that live for the session; the `TABLE` entries use `monkeypatch.setitem` and are restored.

**(7) Seam and mutants.**
- The seam is now one function, with an identity check on the provider. Residual masking is in mn7.
- The mutants are no longer on/off only: M12c (truthiness), M12d/e (dropped name), M12f (narrowed type), M12g (prod only) and M13b (over-refusal in demo) are meaningful.
- By reading, each target string occurs once and each `expect` fragment matches the killer's message. Gaps are in mn8. Unrun.

**(8) Over-claims:** mn3. The rest matches the code, including the order sentence at `app.py:89-92`, "every such backend is named in the one message", and "Demo is unchanged".

**(9) Own ticket.**
- Nothing in the commit needs splitting out, provided the erratum (mn1) is written.
- Separate items that must exist with a date: the operators' sign-in for one-off commands; approle secret-id lifetime; the Azure/AWS environment credentials (round-1 m6); the `Approvals` time parameters (mn4).

## Round-1 resolution table

| Finding | Status | Where |
|---|---|---|
| Design M1 Vault rule blocks operator commands | Resolved by the move; residual mn2 | `app.py:120-123`; kill-switch test in `test_q8a_live_overrides.py` |
| Design M2 steers to approle | Partly: message and CHANGELOG recommend kubernetes; ledger row unverified | `app.py:319`; `CHANGELOG.md` line 15 |
| Design M3 `run_tick(now=)` | Resolved; sibling `steps=` open (MJ1) | `tick.py:344-346`; M13a/b |
| Design m1 `timeout_s=0` | Resolved; wording mn6 | `app.py:151-153, 325-329` |
| Design m2 `factory.py:51` | Accepted, in D-012; not in the ticket (mn1) | `backends/factory.py:51` |
| Design m3 `clock` default | (a) resolved in CHANGELOG line 11; (b) leftover patch of `app.now` not named (mn3) | `app.py:154` |
| Design m4 kind names, not type | Resolved; enforcement gap mn9 | `app.py:321`; `_VaultBuilt` test |
| Design m5 limit wording | Partly (mn3) | `app.py:101-104` |
| Design m6 sibling static credentials | Not verifiable (ledger not read) | none |
| Design m7 seam checks nothing | Mostly resolved (mn7) | `test_k3_pilot_env.py:188-220` |
| Design m8 mutants on/off | Mostly resolved (mn8) | `stage_mutants.py` M12c-g, M13a-b |
| Codebase 1 second seam | Resolved: `plant` removed, one wrapper | `test_k3_pilot_env.py:199` only |
| Codebase 2 `sources`/`tools` truthiness | Resolved, with the empty-mapping deviation | `app.py:132, 135, 155, 272, 307` |
| Codebase 3 kind strings | Resolved | `app.py:321` |
| Codebase 4 `timeout_s` | Resolved | `app.py:151-153` |
| Codebase 5 docstring order | Resolved and true to the code | `app.py:89-92` |
| Codebase 6 formatter artefacts, docstring claim | Resolved in the changed tests; `vault_dir` now matched exactly | `test_stage_names.py`, `test_q8a_live_overrides.py` |

## Not checked

- Any test, mutant, ruff, format, bandit or guard run for f6fad26.
- `handover/ledger.md`: whether the owner questions and deferred items are recorded with dates.
- `tools/mutation_runner.py`, and any meta-test that pins the count of stage mutants.
- Whether a chain audit builds with a `None` signer on `MemoryStore` in the "accepts other sign-ins" test.
- Whether pydantic accepts `.inf` for `executor_timeout_s`.
- The full unchanged test suite for callers of `run_tick(app, now=...)` on an app whose config is not demo.
- CI config and SonarCloud.
- The first 843 lines of `DIFF-fix1.patch` and the head files were read in full; `DIFF-vs-main.patch` was checked only for its file list.

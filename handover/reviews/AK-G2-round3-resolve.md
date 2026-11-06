# AK-G2 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

## Honest note (read first: what I did NOT check, and what my one probe does and does not prove)
- **No suite, lint, mutant or ruff was run.** I wrote no git state, did not commit and did not push. I did not edit the ticket, and I did not touch `DECISIONS.md`, `owner-visible-limits.md`, `questions-for-lead.md` or `HEARTBEAT.md`. This file replaces the skill's default name `goldfish_review_report.md`. The skill's interactive gate was skipped because the lead's brief says AUTO.
- **I ran one read-only probe** with the repository's `.venv` interpreter (`-I`): psycopg 3.3.6's `Transformer().get_dumper` gives `ListDumper` for a `list` and raises `ProgrammingError: cannot adapt type 'frozenset'` for a `frozenset`. It proves COR-10's premise for this psycopg version only. It is scratch output, not evidence.
- **Read in code myself** (Facts F1-F10): the store's error classes, the stuck formula and the llm settings, the document-size defaults, the run end reasons, the tick's step and exit-code path, the `tick` and kill-switch commands, `_row`, `Shape`, `TickState`.
- **Not checked (UNVERIFIED):**
  - PostgreSQL behaviour of the new indexes, the `EXPLAIN` plans of BN-4, the one-row-per-source key-check table, the `NOT EXISTS` reopen guard of BN-7 and the trigger on 16 and 17. Nothing was run; rows L15, L21 and B3 settle it at build.
  - `OPEN_STATES`' exact members (`models.py:75`). BN-7's reopen guard names the constant and never lists its members.
  - Whether `runtime/runs.py` `ALLOWED` lets a `WAITING_FOR_APPROVAL` run later reach `NEEDS_PERSON`. BN-2 states the consequence either way.
  - P4c revision 4 text, which does not exist on disk (`grep DOCUMENT_BYTES tickets/P4c.md`: 0 matches). The lowering of the document cap rests on `reviews/P4c-round3-resolve.md:96` (PL25) and order 24 item 41.
  - AK-G15, AK-G16 and AK-G22 have no tickets, so their names stay unverified.
- **Two judgements a reader may dispute.**
  - **BN-2:** a receipt now mirrors EVERY `NEEDS_PERSON` run end as `needs_person` (`run_needs_person`). A person can therefore see the same message twice: once as a run and once as a receipt. I chose it because the receipt is the only object a reopen works on (`reopen_inbound` starts only from `needs_person`). The other way, "reopen from `done` when the run is `NEEDS_PERSON`", widens the trigger's state rules.
  - **BN-13:** the orphan check moves out of `app.build` into the `inbound_dispatch` tick step. "Refused at build" becomes "the inbound step fails every tick, loudly". The reason: `hadavin-sdk tick` rebuilds the app on every run (F6). A build refusal would stop approvals expiring and stuck runs moving, which is worse than the stranded receipts it reports.

## Status, target, gate
- **Status:** resolved (AUTO; categorised). The ticket is NOT edited. The fixes are build notes BN-1 to BN-23 below, and they win over the ticket text.
- **Target:** `handover/tickets/AK-G2.md` revision 3 DRAFT, commit `b7a3170`, full file (475 lines), both sub-PRs.
- **Findings:** 33 ids. Severity is taken from the tables and never changed here.
  - `reviews/AK-G2-round3-adversarial.md` R3-ADV-1..18: 0 Blocker, 5 Major, **11 Minor** (ADV-6 to ADV-16; the report's header says 9, and the table is what is counted), 2 Nit.
  - `reviews/AK-G2-round3-correctness.md` R3-COR-1..15: 0 Blocker, 7 Major, 6 Minor, 2 Nit.
- **Gate (order 20 item 6):** round 3 is the last round under the cap of 3. A security, money or redaction ticket gets a 4th round only if its last round had no Blocker and at most 2 Majors. Round 3 has **12 Majors**: ADV-1 to ADV-5 and COR-1 to COR-7. ADV-1 and COR-3 are one defect, so there are 11 distinct Major defects. **With 12 Majors there is no round 4.**
  - The ticket freezes at revision 3 with this file attached. The banner below goes under its revision line.
  - The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together. The RESULT review of built code keeps no round cap (security path).
  - Items routed NEEDS LEAD (PENDING LEAD 9 to 12) carry a recommendation. The builder applies it meanwhile, because each recommended option is the fail-closed side. None of the PENDING LEAD items asks the owner for money or a live call.

## Facts I checked myself (on disk at `<repo>`)
- **F1 (COR-1 TRUE).**
  - `StoreUnavailable` is raised in `store/postgres.py` only at connect, at `:172`, wrapping `psycopg.OperationalError` (`:170-174`; grep gives one raise). The memory store raises none (grep: 0).
  - `:193-194` reads "A dropped connection fails the call ... reconnect-on-error arrives with S11 hosting". So a mid-session outage surfaces as a raw psycopg error.
  - `store/protocol.py:29-38` `is_connectivity_error(exc)` is true for `StoreUnavailable | OSError`, and for a class named `OperationalError` or `InterfaceError` whose module starts with `psycopg`, anywhere on the MRO. `run_tick` already uses it (`tick.py:339-342`, `:362-364`).
- **F2 (COR-4 TRUE).**
  - `tick.py:100-109`: `steps x getattr(llm, "call_timeout_s", 60) x getattr(llm, "max_attempts", 1) + 60`, and the function takes an `App`.
  - `backends/table.py:28-29`: `FakeLLMSettings` has only `recorded_dir`. `:37-40` gives the network defaults of 60.0 s and 3 attempts.
  - `tests/fixtures/config/config.yaml:13` sets `llm: {kind: fake, ...}`.
  - So the fixture gives stuck 300 s and lease 360 s for 4 steps, and stuck 780 s and lease 840 s for 12 steps. A network llm gives 780/840 s for 4 steps and 2220/2280 s for 12. C2b's "2280" fails on the fixture.
- **F3 (COR-5 TRUE).**
  - `defaults.py:31-33` has `MAX_DOCUMENT_BYTES = 262_144`. `config.py:233-235` defaults `max_document_bytes` to it, with `le=defaults.MAX_REDACT_CHARS`.
  - `reviews/P4c-round3-resolve.md:96` is PL25 (a): lower `MAX_DOCUMENT_BYTES` to about 33 KB. Order 24 item 41 accepts option (a).
  - `tickets/P4c.md` has no such line (grep: 0).
  - So after P4c, the ticket's default `max_body_bytes = 262144` trips its own refusal at `:199`.
- **F4 (ADV-2 TRUE, wider than reported).**
  - `runtime/agent_loop.py` ends a run `NEEDS_PERSON` with about 30 reasons: `run_budget` (`:249`), `document_too_large` (`:356`, `:375`), `tool_error`, `max_steps` (`:540`), `evidence_unavailable` (`:545`), `redaction_error` (`:549`), `limits_unavailable` (`:672`), `audit_unavailable` (`:700`, `:781`, `:808`), `llm_<stop_reason>` (`:449`), `verify_failed` (`:869`), and more.
  - `:702-703`: a gate decision whose `rule_id` starts with `limits.` ends the run `DENIED <rule_id>`. `actions/authorizer.py:44` makes it `limits.<blocked[0]>`, from `kill_switch`, `daily_budget` or `monthly_budget`.
  - `STOPPED` is set only with `kill_switch` (`:242`, `:772`).
  - `RunState` (`models.py:55-69`) has 14 values.
  - Under the ticket's `_classify`, all of these except the four `LIMITS_END` pairs give `done`, and a `done` receipt can never be reopened.
- **F5 (ADV-8 and COR-6 TRUE).**
  - `heartbeat` reads only `FAILED` values (`tick.py:242-246`). `run_tick` returns an int and drops `ctx` (`:335-372`).
  - A step that RAISES is logged at ERROR with its class and message, saved as `tick_state.last_error`, and makes the tick exit 1 (`_run_step`, `:295-323`; `run_tick` `:372`), or 4 when the store is unreachable after the steps (`:356-369`).
  - So raising is the existing operator signal, and extra `ctx.results` keys are not one.
- **F6 (COR-7 TRUE; ADV-13's open point answered).**
  - `cli.py:280-299` `_tick` calls `app.build(None, agents)` on every run, so an orphan `ConfigError` stops `sweep`, `reconcile`, `stuck` and `checkpoint`.
  - The kill-switch command (`cli.py:173-209`) builds `secrets`, `signer`, `anchor`, `store` and `audit` with `make(...)` and never calls `app.build`. **So the kill switch is NOT affected; the tick is.**
- **F7 (COR-10 TRUE; probe).** `PostgresStore._row` (`postgres.py:178-189`) converts only dicts, lists and enums. psycopg 3.3.6 cannot adapt a `frozenset` (probe). `Shape` adds `schema_version: int = 1` (`models.py:50-52`).
- **F8 (ADV-7 TRUE).** `stuck` (`tick.py:122-131`) moves a run when `run.updated_at < now - stuck_after_s(app, run.agent_id)`. The formula counts model calls only, not tool time. So a run is "still running" by the tick's own rule while `updated_at >= now - stuck_after_s`.
- **F9 (BN-3's storage choice).** `TickState` (`models.py:225-232`) has `step`, `last_run_at`, `last_ok_at` and `last_error`. Storing a key check in `last_error` would give one word two meanings, which the wording rule forbids. It is rejected.
- **F10 (ADV-1 and COR-3 TRUE, from ticket text).**
  - `AK1.md:111` `StepInput` carries `item_id`, `tenant`, `readers`, `body`, `run_id` and `agent_id`, and no source name.
  - The AK1 round 3 build notes (`reviews/AK1-round3-resolve.md`) change no `StepInput` field and no `REASONS` member.
  - Its BN-8 adds strict UTF-8 for a `str` body. AK-G2 passes `bytes`, so nothing changes here.
  - Its BN-12 catches `Exception` only, so stop requests propagate, as AK-G2 already relies.

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK-G2-round3-adversarial.md`, `reviews/AK-G2-round3-correctness.md`) had 12 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-23 in `reviews/AK-G2-round3-resolve.md`; where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes. The CHANGELOG sections are history, not instructions. Totals after the notes: 70 test rows (AK-G2-a 43, AK-G2-b 27), 103 mutants (-a 69: M-a1..M-a70 with M-a12 retired; -b 34: M-b1..M-b9 and M-b13..M-b37), 10 store methods, 3 tables. CUT by the notes: `compare_ids`, `IdComparison`, `list_inbound`, the orphan build refusal, and the tick result keys `inbound_infra_stops` and `inbound_orphans` (BN-8, BN-13, BN-14).

## Decisions (one row per finding, duplicates merged)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 = R3-COR-3 (Major) | PROPOSE FIX | TRUE (F10). `dispatch` takes `steps: Mapping[source name, Step]`, and -b builds one `StartRun(runtime, principal_id)` per source. `run_step` gets `"trigger:" + source.name`; `handle` gets `source.principal_id`. New row D12, W13 extended, mutants M-a62 and M-b37. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX (decided: `needs_person`; PENDING LEAD 8, INFORM) | TRUE, wider than reported (F4). Every `NEEDS_PERSON` run outside `LIMITS_END` gives the receipt `needs_person run_needs_person`. `DENIED limits.*` joins `LIMITS_END`. `run_budget` becomes `run_needs_person` (D4b's last sentence reverses). New row D13, mutants M-a63 and M-a64. **BN-2.** |
| R3-ADV-3 + R3-COR-12 (Major, Minor) | PROPOSE FIX (key check; PENDING LEAD 9, NEEDS LEAD) | TRUE. A one-row-per-source key check: a changed inbound key stops inbound for that source, fail closed, until `inbound.key_check_ack` names the new check. The same check works under PENDING LEAD 6 (a) or (c). PL4 gains (ix). New row L20, mutants M-a65 and M-a66. **BN-3.** |
| R3-ADV-4 (Major) | PROPOSE FIX | TRUE. Two partial indexes. `list_inbound_sources` returns only pairs with a count above 0. The purge is driven from `inbound_bodies` (bounded), not from the receipts. New rows L21 (`EXPLAIN` with `enable_seqscan = off`) and B3 (1,000,000 pre-filled final rows, timings report-only), mutant M-a67. **BN-4.** |
| R3-ADV-5 (Major) | PROPOSE FIX (PENDING LEAD 10, NEEDS LEAD: tenant isolation) | TRUE. `app.build` refuses one `agent_id`, or one `principal_id`, used by sources of two or more tenants, in every environment. Sharing inside one tenant stays allowed (BN-1's case). C4 extended, mutant M-b29. **BN-5.** |
| R3-ADV-6 (Minor) | PROPOSE FIX (a control, not a note; PENDING LEAD 17, INFORM) | TRUE: `hmac_v0` signs only the timestamp and the body. A required per-source `audience`, matched against the signed body's `"aud"`, closes cross-deployment replay. New row W17, mutant M-b30. **BN-6.** |
| R3-ADV-7 + R3-ADV-14 + R3-COR-11 (Minor x3) | PROPOSE FIX (reopen guard: PENDING LEAD 11, NEEDS LEAD, money) | TRUE (F8). A run still inside its stuck time leaves the receipt `claimed` (not `run_interrupted`). Runbook: ticks may overlap. `reopen_inbound` refuses while the receipt's run is in `OPEN_STATES`. AK-G15's screen shows the old run's state and warns on `outcome_unknown`. PL4 gains (x) and (xi). New row D14, D10 extended, mutants M-a68 and M-a69. **BN-7.** |
| R3-ADV-8 + R3-COR-6 (Minor, Major) | PROPOSE FIX (surface cut) | TRUE (F5). The `inbound_dispatch` step RAISES after its work when an infrastructure stop, a key change or an orphan happened, so the tick gets ERROR, `last_error` and exit 1. Both `ctx.results` keys are CUT. New row C9, C8 rewritten, mutants M-b31 and M-b32. **BN-8.** |
| R3-COR-1 + R3-COR-2 + R3-ADV-9 (Major, Major, Minor) | PROPOSE FIX (PENDING LEAD 13, INFORM) | TRUE (F1). Every dispatch site classifies with `is_connectivity_error`. Failures INSIDE the step (`create_run` in `handle`) count as a `step_error` try, said in Words; no AK1 edit. D3a and D11 inject a psycopg-like `OperationalError`, `OSError` and `StoreUnavailable`. D11 gains a `release_inbound` fault. Mutant M-a70. **BN-9.** |
| R3-ADV-10 + R3-COR-9 (Minor x2) | PROPOSE FIX | TRUE. The HMAC key is renamed `hkey`, and `run_id_for(rec.delivery_key, g)` is written everywhere; L19 pins both. **BN-10.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | Every 503 carries `Retry-After: retry_after_s`. W7 asserts busy, store unreachable and key changed. Mutant M-b33. **BN-11.** |
| R3-ADV-12 (Minor) | PROPOSE FIX | TRUE. Seven `-a` mutants (one more than the reviewer listed, because the agent match gets its own) and two `-b` mutants, with killers. **BN-12.** |
| R3-ADV-13 + R3-COR-7 (Minor, Major) | PROPOSE FIX (surface cut; PENDING LEAD 16, INFORM) | TRUE (F6; the kill switch is not affected). The orphan build refusal is CUT in every environment. The orphan check runs in `inbound_dispatch` (BN-8), and retired pairs are not counted. "Close without re-run" becomes V15 (AK-G15). M-b22 redefined. **BN-13.** |
| R3-ADV-15 (Minor) | PROPOSE FIX (surface cut, order 8; PENDING LEAD 12, NEEDS LEAD: owner rule R368) | TRUE. `compare_ids`, `IdComparison` and the store method `list_inbound` are CUT until AK-G15. L12 is removed and M-a12 retired. V7 is rewritten to carry them with the command line, trigger "before any pilot". **BN-14.** |
| R3-ADV-16 (Minor) | PROPOSE FIX | A lead-run pre-revert count is the written check that stands in for the loud-failure test. A CHANGELOG line marks the change "not revertible while receipts are open". **BN-15.** |
| R3-ADV-17 (Nit) | PROPOSE FIX | `header_prefix` gets a pattern. Reuse-row growth (at most 8 per sender id, never purged) is stated against V6. **BN-16.** |
| R3-ADV-18 (Nit) | DECLINE | The reviewer asks for no change, and its arithmetic matches the ticket. Totals change only through BN-23. |
| R3-COR-4 (Major) | PROPOSE FIX (PENDING LEAD 14, INFORM) | TRUE (F2). C2b asserts the fake-llm numbers (360 s; 840 s with an added 12-step agent) and, through the shared helper, the network numbers (840 s, 2280 s). `stuck_after_s` gets a `(config, registry)` helper. Mutant M-b34. **BN-17.** |
| R3-COR-5 (Major) | PROPOSE FIX (PENDING LEAD 15, INFORM) | TRUE (F3). `max_body_bytes: int \| None = None`, where `None` means `evidence.max_document_bytes`. An explicit value above it is still refused. C4 extended, mutants M-b27 and M-b35. The P4c lowering goes to UNVERIFIED. **BN-18.** |
| R3-COR-8 (Minor) | PROPOSE FIX | TRUE. D2b covers a foreign run that exists up front: `run_mismatch` on the first claim, 0 step calls. New D2c covers a foreign run created between `get_run` and `create_run` by a fault hook: release, then `run_mismatch`. M-a51 is killed by D2c. **BN-19.** |
| R3-COR-10 (Minor) | PROPOSE FIX | TRUE (F7, probe). The inbound methods use explicit SQL. `readers` is stored as a sorted `text[]` and rebuilt as a `frozenset` on read. There is a `schema_version` column. **BN-20.** |
| R3-COR-13 (Minor) | PROPOSE FIX (PENDING LEAD 18, INFORM to the lead) | TRUE. Hard dependencies are P4d, P3a, P2a-1 and AK1-a. P4c-2 and P5c are merge order only. Unless the peel (ADV-22) is taken or the lead lets P5c rebase over AK-G2-a, AK-G2-a waits for P5c. **BN-21.** |
| R3-COR-14 (Nit) | PROPOSE FIX | Strict `body.decode("utf-8")` before `json.loads`. W5 gains a UTF-16 body. Mutant M-b36. **BN-22.** |
| R3-COR-15 (Nit) | PROPOSE FIX | The purge treats a missing run as not open. Surface wording: "three `App` fields". **BN-22.** |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. One principal per source (R3-ADV-1, R3-COR-3).**
- `Inbox.dispatch(sources: Sequence[InboundSource], steps: Mapping[str, Step]) -> tuple[int, bool]`. Keys are source names. A configured source with no step is `ValueError` before the first claim.
- `StartRun(runtime, principal_id: str)`: one instance per source, with no map. `run(inp)` calls `runtime.handle(inp.agent_id, principal_id=self.principal_id, ...)`.
- **Which principal goes where (one sentence for the ticket):** `run_step(..., principal="trigger:" + source.name)` is the AUDIT principal of the pipeline step (who started the step), and `handle(principal_id=source.principal_id)` is the RUN's principal from `principals.yaml`, which `_classify` compares with `run.principal_id`.
- -b: `app.build` builds `App.inbound_steps: Mapping[str, StartRun]` (replaces `App.inbound_step`). The three `App` fields are `inbox`, `inbound_steps` and `inbound_doors`.
- **New row D12 (real `handle`):** two sources of one tenant, one agent, two principals, one message each, so each run carries its own source's `principal_id`, and both receipts end `done`, not `run_mismatch`.
- **W13 gains a third source:** the same tenant and agent as the first source, another principal. Through `app.build` and a tick, each run's `principal_id` equals its source's.
- Mutants: **M-a62** (`triggers/ledger.py`): dispatch uses one step for every source (killed by D12). **M-b37** (`app.py`): `app.build` builds one `StartRun` with the first source's principal (killed by W13).
- Interface 5's `dispatch(sources, step)` text, the D10 and D2b setups, and `App.inbound_step` follow this note. "Noticed, NOT changed" is closed.

**BN-2. A run that ends needing a person gives a receipt that needs a person (R3-ADV-2; PENDING LEAD 8).**
- **`_classify(run, source, rec, now)`**, first match wins:
  1. any of agent, principal or `trigger_ref` differs: `needs_person run_mismatch`;
  2. `(run.state, run.reason_code)` in `LIMITS_END`: `needs_person run_limits`;
  3. `run.state` in `tick.STUCK`'s keys and the run is still inside its stuck time (BN-7): leave the receipt `claimed`;
  4. `run.state` in `tick.STUCK`'s keys otherwise: `needs_person run_interrupted`;
  5. **`run.state is NEEDS_PERSON` (any other reason): `needs_person run_needs_person`;**
  6. anything else: `done`.
- **`LIMITS_END` gains** `(DENIED, "limits.kill_switch")`, `(DENIED, "limits.daily_budget")` and `(DENIED, "limits.monthly_budget")` (`agent_loop.py:702-703`, `actions/authorizer.py:44`). It is a closed set of 7 pairs, not a prefix test.
- `INBOUND_REASONS` gains `run_needs_person`, and the Interface 1 table's `needs_person` row gains it.
- **`run_budget` decided:** a run that hit its own per-run cap ends `NEEDS_PERSON run_budget`, so the receipt is `needs_person run_needs_person`. A person may reopen it, which can pay again. D4b's sentence "A run ending `run_budget` leaves the receipt `done`" is REPLACED by "... leaves the receipt `needs_person run_needs_person`".
- **Words, "final state":** "`done` means exactly one run exists for this message's current generation and, when dispatch read it, that run was not stuck, not cut off, not stopped by a limit and not waiting for a person." `done` is decided at the moment dispatch reads the run. A run that later waits for a person (for example after `WAITING_FOR_APPROVAL`, if `runs.py` allows it; UNVERIFIED) is seen as a run, not as a receipt.
- **New row D13 (real `handle`):** runs that end `NEEDS_PERSON` with `evidence_unavailable`, `tool_error`, `max_steps`, `run_budget` and `audit_unavailable` (each forced by the fake model or a fault): each receipt ends `needs_person run_needs_person`, the body is kept, and `reopen_inbound` plus dispatch starts a second run (generation 1). D4b gains the three `DENIED limits.*` cases, which give `run_limits`.
- Mutants: **M-a63** (`triggers/ledger.py`): rule 5 removed, so such a run is `done` (killed by D13). **M-a64**: the `DENIED` pairs removed from `LIMITS_END` (killed by D4b).

**BN-3. Key check against a changed inbound key (R3-ADV-3, R3-COR-12; PENDING LEAD 9).**
- **Check value:** `key_check = _h(hkey, b"hadavin-inbound-key-check-v1")[:16]` (16 lower-case hex). It is computed in every environment; in dev without a key it is the plain-SHA-256 form. It is an HMAC of a fixed label truncated to 64 bits, so it reveals nothing about the key and may appear in a log line and in config.
- **Storage (one row per source, so it carries tenant and readers, order 27 item 56):** new table `inbound_key_checks`, primary key `(tenant, source)`, columns `readers text[]`, `key_check text NOT NULL CHECK (key_check ~ '^[0-9a-f]{16}$')`, `set_at timestamptz`, `schema_version`. `GRANTS`: runtime `_RW`; no purge; no portal.
- **Two store methods (10 in all after BN-14):** `get_inbound_key_check(tenant, source) -> str | None` and `set_inbound_key_check(tenant, source, readers, old: str | None, new: str) -> None`, a compare-and-set where a lost race is `StaleState`.
- **Where it is checked:** `Inbox` checks each source once per process (and caches the result) before that source's first `receive_inbound` and before its first claim.
  - No row: write the check (`old=None`).
  - Equal: go on.
  - Different, and `settings.key_check_ack` equals the CURRENT check: compare-and-set to the current value and log one WARNING ("inbound key changed for <tenant>/<source>; dedupe of messages accepted before the change is lost").
  - Different otherwise: raise `InboundKeyChanged`. This is ONE new exception class in `triggers/ledger.py`, so Interface 9's "no new exception class" changes. Its message holds the tenant, the source and both check values, never a key.
- **Effect:** the door answers 503 with `Retry-After` (log code `key_changed`, ERROR once per source per process, then DEBUG), so the sender keeps the message and nothing is lost. Dispatch skips that source and its step fails at the end (BN-8).
- **Config (-b):** `inbound.key_check_ack: str | None = None`, pattern `^[0-9a-f]{16}$`. The runbook gets this text, which replaces "drain inbound before rotating": "Rotate the key only after every sender's retry horizon has passed. After a rotation, inbound stops until you copy the new check value from the ERROR line into `inbound.key_check_ack`. From then on, a retry of a message accepted before the change can start a second run."
- **PL4 gains (ix):** "If the key behind the inbound hashes is changed, inbound stops until a person acknowledges it. After that, a sender's retry of a message accepted before the change can start a second paid run."
- **New row L20:**
  - (i) the first receive writes the check;
  - (ii) a second `Inbox` over the same store with another key: `receive` raises `InboundKeyChanged`, nothing is written, and dispatch claims nothing for that source;
  - (iii) with `key_check_ack` equal to the new check: it proceeds, the stored check is updated, and one WARNING is logged;
  - (iv) with an ack that differs from the new check: still refused.
- W7 gains the `key_changed` 503 and C9 the step failure.
- Mutants: **M-a65** (`triggers/ledger.py`): the check is skipped in `Inbox.receive` (killed by L20 (ii)). **M-a66**: any ack is accepted (killed by L20 (iv)).
- Interface 4 gains the table and its `GRANTS` row; L14 gains its rights (runtime has no DELETE; portal and purge have nothing).

**BN-4. Indexes and the three growing queries (R3-ADV-4).**
- **Migration:**
  - REPLACE `inbound_receipts_open` with `inbound_receipts_waiting ON inbound_receipts (tenant, source, state, lease_until) WHERE state IN ('received', 'claimed', 'needs_person')`. The claim's predicate `state IN ('received', 'claimed')` implies it.
  - ADD `inbound_receipts_reuse ON inbound_receipts (tenant, source, reuse_of) WHERE reuse_of IS NOT NULL`.
- **`list_inbound_sources()`** returns only pairs whose count of `received`, `claimed` or `needs_person` is above 0. Interface 3 and the rollback runbook follow.
- **Purge:** select from `inbound_bodies` joined to `inbound_receipts` on the primary key, `LEFT JOIN runs` on `run_id`. The bodies table is bounded (`body_days` plus the waiting bodies up to the ceiling), so the purge never walks the forever-growing receipts table.
- **New row L21 (Postgres 16 and 17):** with `SET enable_seqscan = off`, `EXPLAIN` of the reuse count, the open count in `receive_inbound`, the claim, `list_inbound_sources` and the purge shows no `Seq Scan on inbound_receipts`. Raw plans are saved in `a-postgres.txt`.
- **New row B3 (Postgres, ALONE):** 1,000,000 made-up final receipts (`generate_series`; 10 percent with `reuse_of`, 5 percent `needs_person`), plus 1,000 open receipts. Timings of `receive` (new, conflict, reuse), claim, `list_inbound_sources` and purge are recorded raw and are REPORT-ONLY (like B2). Correctness passes as the L rows. The file is `a-burst-history.txt`.
- **Mutant M-a67** (migration): `inbound_receipts_reuse` dropped. Killed by L21.

**BN-5. Tenant fence for shared agents and principals (R3-ADV-5; PENDING LEAD 10).**
- `app.build`, in every environment: a `ConfigError` naming both sources when one `agent_id`, or one `principal_id`, appears in sources of two or more tenants. Two sources of ONE tenant may share them (BN-1).
- Said plainly in Security "Tenant isolation": "runs carry no tenant, so this refusal is what keeps one agent from handling two tenants' bodies with the same tools, caches and approval cards".
- C4 gains both cases (different tenants: refused; the same tenant: builds). **Mutant M-b29** (`app.py`): the refusal is removed. Killed by C4.

**BN-6. Audience in the signed body (R3-ADV-6; PENDING LEAD 17).**
- `WebhookSource.audience: str`, REQUIRED in every environment, pattern `[a-z0-9][a-z0-9._/-]{0,95}`, unique across the deployment's sources (C4).
- **Door step (4b),** after the parse: the body's top-level `"aud"` must be a JSON string equal to `audience`; otherwise 400, log code `bad_audience`, nothing written.
- **Forwarder contract:** "put `"aud": "<audience>"` in every body". Runbook: audience = `<deployment name>/<source name>`, deployment names unique per client.
- **PL4 (vi) reworded:** "Two client deployments that share a signing secret cannot replay each other's requests, because each request names its audience. Only two deployments set up with the same audience AND the same secret could, which is two configuration errors."
- **New row W17:** a correctly signed body with a missing `aud`, a wrong `aud` and `aud` as a number: 400, nothing written; the right `aud`: 202. **Mutant M-b30** (`triggers/webhook.py`): the audience check is skipped. Killed by W17.

**BN-7. Slow runs, overlapping ticks, and reopen safety (R3-ADV-7, R3-ADV-14, R3-COR-11; PENDING LEAD 11).**
- **`InboundSource.stuck_s: int`** (ge 1). -b fills it per source from the BN-17 helper for that source's agent; -a tests set it directly.
- **`_classify` rule 3 (BN-2):** a run in a `STUCK` key state whose `updated_at >= now - source.stuck_s` is STILL RUNNING by the tick's own rule (F8). The receipt is left `claimed`, with no finish and no release (the claim already set a new lease), and it is not counted as finished. The next claim after the lease reads the run again.
  - **Bound:** the receipt reaches its final state at most one lease after the run leaves the `STUCK` states, or after the `stuck` step moves it. A late `finish_inbound` by the first worker meets `StaleState` and is skipped (Interface 5, unchanged).
- **Runbook line:** "the scheduler must start each tick on time even while an earlier tick still runs (overlap allowed). Concurrent ticks are safe (`tick.py:17`), and one dispatch can hold its tick for up to the lease."
- **Reopen guard:** `reopen_inbound` also refuses with `StaleState` while a run with the receipt's current `run_id` exists in `OPEN_STATES` (`models.py:75`; UNVERIFIED members, so name the constant). In Postgres this is a `NOT EXISTS (SELECT 1 FROM runs ...)` inside the same `UPDATE`; the runtime role already reads `runs`. In memory it is `get_run`. So a `run_interrupted` receipt can be reopened only after the `stuck` step has moved its run to `NEEDS_PERSON`.
- **AK-G15 coupling:** the reopen screen shows the previous run's state and reason, and WARNS on `outcome_unknown` (an `EXECUTING` run whose action may have happened). The new run still passes the gate and approval, and how far they catch a repeat is UNVERIFIED.
- **PL4 gains:**
  - (x) "Reopening a message whose earlier run may already have acted outside (its outcome is unknown) can propose the same action again; the approval step still applies."
  - (xi) "The core marks a run as interrupted after its model-time limit; time spent in tools is not counted, so a healthy but slow run can be marked interrupted (existing core behaviour, row V16)."
- **New row D14 (fake lease clock, real `handle`, threads):**
  - (i) a slow step whose run is `WORKING` with a fresh `updated_at`, and a second dispatcher claiming after the lease: the receipt stays `claimed` (not `run_interrupted`); after the run succeeds, the next claim gives `done`; the fake model is called once.
  - (ii) two concurrent ticks, one blocked in a slow step: the second tick runs `sweep`, `reconcile`, `stuck`, `checkpoint`, `purge_evidence` and `reprobe_sources`, and claims other receipts.
- **D10 gains:** `reopen_inbound` while the first run is `WORKING` gives `StaleState`; after a `stuck` tick past `stuck_s` it works.
- Mutants: **M-a68** (`triggers/ledger.py`): the still-running check is removed (killed by D14 (i)). **M-a69** (store and migration): reopen allowed while the run is open (killed by D10).

**BN-8. The operator sees inbound trouble (R3-ADV-8, R3-COR-6; surface cut).**
- The `inbound_dispatch` tick step does its work, then counts the orphans (BN-13) and RAISES `RuntimeError("inbound: <closed code> ...")` when an infrastructure stop happened (BN-9), a source's key check failed (BN-3), or the orphan count is above 0.
  - The message holds names and counts only: `tenant/source=count`, never a body, a sender id or a key.
  - `_run_step` then logs ERROR, saves `tick_state.last_error`, and the tick exits 1, or 4 when the store is unreachable after the steps (F5). The steps before it have already run, and `inbound_purge` is its own step.
- **CUT:** `ctx.results["inbound_infra_stops"]` and `ctx.results["inbound_orphans"]` (they had no reader). Interface 8's text and "Choices" item 3 follow.
- **New row C9:** an audit outage during dispatch, then a key-check mismatch: `run_tick` returns 1, one ERROR record names `inbound_dispatch`, `get_tick_state("inbound_dispatch").last_error` is set, and the six older steps ran.
- C8 is rewritten in BN-13. **Mutant M-b31** (`runtime/tick.py`): the infrastructure stop does not raise. Killed by C9.

**BN-9. Infrastructure failures: how they are recognised and what counts (R3-COR-1, R3-COR-2, R3-ADV-9; PENDING LEAD 13).**
- **Classification:** at every dispatch site (`limits.blocked`, the key check, `claim_inbound`, `get_run`, the body read, `finish_inbound`, `release_inbound`), an exception with `is_connectivity_error(exc)` true (`store/protocol.py:29-38`) is an infrastructure failure: it ends the call, and dispatch returns `(n, True)`. Any other exception from those sites propagates out of `dispatch`, so the tick step fails (BN-8); the receipt is untouched beyond its lease.
- **The door:** `is_connectivity_error` gives 503 with `Retry-After`; `InboundKeyChanged` gives 503 with `Retry-After`; anything else gives 500. Interface 7 step (6) and the log codes follow.
- **Words, "try", replaced by:** "A crash, an overrun (the lease ran out) and a step failure (`step_error`) count. A store failure INSIDE the step, for example `create_run` inside `handle`, is a `step_error` and counts. When the store fails after a claim and leaves the receipt `claimed`, the lease expiry counts once. An infrastructure failure that dispatch itself sees (the audit intent, or the store unreachable at a dispatch call) does NOT count, and it ends that dispatch call. Bound: at most one counted try per receipt per lease; in a real outage dispatch's own claim or `get_run` fails first." No AK1 edit, and no new reason.
- **D3a:** `create_run` raising each of `StoreUnavailable`, `OSError` and a test class `OperationalError` whose `__module__` is `"psycopg"`: each is released `step_error` and counted.
- **D11:** the store faults use the same three classes. **D11 gains:** `release_inbound` raising the psycopg-like class leaves the receipt `claimed`, and after the lease `attempts` is 1.
- **Mutant M-a70** (`triggers/ledger.py`): the test is `isinstance(exc, StoreUnavailable)` only. Killed by D11 (psycopg-like class).

**BN-10. Names (R3-ADV-10, R3-COR-9).**
- The HMAC key variable and the `Inbox` argument are `hkey` (`Inbox(..., hkey: bytes | None)`, `_h(hkey, ...)`, `delivery_key(hkey, ...)`).
- `run_id_for(rec.delivery_key, generation)` is written everywhere: Interface 5 `receive` step (1) uses `run_id_for(<the new delivery_key>, 0)`; Interface 6 and L19 use `run_id_for(rec.delivery_key, generation + 1)`.
- L19 pins `run_id_for(delivery_key, 0)` and `(…, 1)` computed from the pinned `delivery_key`, and a unit check that the function signature's first parameter is named `delivery_key`.

**BN-11. Every 503 says when to retry (R3-ADV-11).**
- Every 503 carries `Retry-After: <retry_after_s>`, whether the cause is busy, store unreachable or key changed. W10's property is unchanged.
- W7 asserts all three. **Mutant M-b33** (`triggers/webhook.py`): no `Retry-After` on the store-error 503. Killed by W7.

**BN-12. Mutants for tested behaviours (R3-ADV-12).**
- **M-a55** `check_sender_id` uses `isinstance` (accepts a `str` subclass): L18.
- **M-a56** a repeated reused body is answered `duplicate`: L3.
- **M-a57** purge ceiling rule (i) removed: L13.
- **M-a58** `_classify` skips the agent match: D2b.
- **M-a59** `_classify` skips the principal match: D2b.
- **M-a60** `_classify` skips the `trigger_ref` match: D2b.
- **M-a61** `reopen_inbound` keeps `attempts`: L15, L16.
- **M-b27** an explicit `max_body_bytes` above `evidence.max_document_bytes` is accepted: C4.
- **M-b28** the dev server accepts a negative Content-Length: W6.
- The Done and CHANGELOG counts follow BN-23.

**BN-13. Orphan sources: checked in the dispatch step, not at build (R3-ADV-13, R3-COR-7; PENDING LEAD 16).**
- **CUT:** the build refusal of Interface 8's last bullet, in every environment, and its dev ERROR line at build. The kill switch was never affected (F6), and the tick is no longer affected.
- **The `inbound_dispatch` step:** orphans are the pairs from `list_inbound_sources()` (count above 0) that are neither configured nor in `retired_sources`. Retired pairs are NOT counted. A pair whose count is 0 is never listed (BN-4). The configured sources are dispatched first; then BN-8 raises with names and counts.
- **C8 rewritten:** a store holding open receipts for (`tenant-a`, `src-old`) and a config without it.
  - In `pilot`, `app.build` succeeds.
  - A tick returns 1 with one ERROR record naming `tenant-a/src-old=1`, and the configured sources' receipts still finish.
  - With `retired_sources: ["tenant-a/src-old"]`, the tick returns 0.
- Mutants: **M-b32** (`runtime/tick.py`): orphans do not raise (killed by C8). **M-b22 redefined:** `retired_sources` ignored (killed by C8, retired case).
- **New v1.1 row V15:** "a person closes a `needs_person` receipt without a re-run (to `refused` with reason `closed_by_person`, audited, by AK-G15)", trigger "before any pilot". Until then a source with waiting receipts is removed only with `retired_sources`.

**BN-14. Cut `compare_ids` and `list_inbound` until AK-G15 (R3-ADV-15; order 8; PENDING LEAD 12).**
- **DELETE from AK-G2-a:** `Inbox.compare_ids`, `IdComparison`, and the store method `list_inbound` (protocol, memory, Postgres). Row L12 is removed. M-a12 is retired and not reused. "What AK-G2 IS" drops "the id comparison `compare_ids`". INFORM I6's sentence about `compare_ids` is deleted.
- **V7 rewritten:** "`list_inbound` (store), `compare_ids` both directions (dealdesk `inbox.py:271-287`, hashing with the same `delivery_key` and `hkey`), and the command `hadavin-sdk inbound compare-ids`; built in AK-G15", trigger "before any pilot (R368: comparison against the source's own ids)".
- Said plainly (PL4 (viii), meaning unchanged): v1 code cannot compare our received ids with the sender's ids or list waiting messages; AK-G15 must ship both before any pilot.
- Store methods after BN-3 and BN-14: `receive_inbound`, `claim_inbound`, `get_inbound_body`, `finish_inbound`, `release_inbound`, `reopen_inbound`, `list_inbound_sources`, `purge_inbound_bodies`, `get_inbound_key_check`, `set_inbound_key_check` = **10**.

**BN-15. Rollback (R3-ADV-16).**
- **Lead-run check BEFORE any revert of AK-G2-a or AK-G2-b:**
  1. Record `list_inbound_sources()` (or the same `SELECT tenant, source, state, count(*) ... GROUP BY` as the runtime role) in `handover/evidence/AK-G2/pre-revert-<sha>.txt`.
  2. Revert only when every count is 0, or with every open key and run id recorded in that file.
  3. Keep the tables.
- **This written check stands in for the template's loud-failure test:** no test inside AK-G2 can survive a revert of AK-G2.
- **CHANGELOG line (both sub-PRs):** "Not revertible in effect while receipts are open: after a revert, waiting messages are not read and nothing raises an alarm; run the pre-revert count first."

**BN-16. Small config points (R3-ADV-17).**
- `header_prefix` gets the pattern `[A-Za-z][A-Za-z0-9-]{0,31}` (C4 gains one bad value).
- Interface 1 says reuse rows (state `refused`) are at most `INBOUND_MAX_REUSE_ROWS` = 8 per sender id, never purged in v1, and counted by V6's trigger.

**BN-17. Lease arithmetic and the stuck formula (R3-COR-4; PENDING LEAD 14).**
- **`runtime/tick.py` (-b) gains** `stuck_after_s_for(config, registry, agent_id) -> float`, holding the formula of `:100-109` unchanged. `stuck_after_s(app, agent_id)` returns `stuck_after_s_for(app.config, app.registry, agent_id)`; this preserves behaviour, and the existing tick tests stay green. `app.build` calls the helper on the config and registry it is building, before `App` exists. `InboundSource.stuck_s` uses it too (BN-7).
- **Interface 8's figures** read: "with a network llm kind (60 s, 3 attempts): 840 s for a 4-step agent, 1020 s for 5 steps, 2280 s for 12; with the fake llm of the test fixture (`FakeLLMSettings` has neither field, so 60 s and 1 attempt): 360 s for 4 steps, 840 s for 12."
- **C2b rewritten:** (i) the fixture config with the 4-step agent: lease 360; (ii) plus an added 12-step agent: lease 840 (the maximum); (iii) the helper over a network-kind settings object (`_LLMSettings` defaults) for 4 and 12 steps: 840 and 2280.
- M-b23 (fixed 900) is killed by (i) and (ii). **Mutant M-b34** (`app.py`): the minimum over agents instead of the maximum. Killed by C2b (ii).

**BN-18. `max_body_bytes` follows the document cap (R3-COR-5; PENDING LEAD 15).**
- `WebhookSource.max_body_bytes: int | None = None` (when set: ge 1, le 10485760). `None` means "equal to `evidence.max_document_bytes`", resolved at build. An explicit value above `evidence.max_document_bytes` is still refused (`:199`).
- Security's "Cost before authentication" reads "default `evidence.max_document_bytes`".
- **C4 gains:** a config with `evidence.max_document_bytes: 32768` and no `max_body_bytes` builds, and the door's limit is 32768; an explicit 65536 with it is refused.
- Mutants: **M-b35** (`config.py`/`app.py`): a fixed default of 262144 (killed by C4, the 32768 case); M-b27 (BN-12) is the explicit-above case.
- **UNVERIFIED list gains:** "P4c PL25 (a) lowers `MAX_DOCUMENT_BYTES` to about 33 KB (`reviews/P4c-round3-resolve.md:96`, order 24 item 41); `tickets/P4c.md` does not yet say so (grep: 0)."

**BN-19. D2b split (R3-COR-8).**
- **D2b:** a foreign run exists under id X BEFORE dispatch (each of another agent, principal or `trigger_ref`). The first claim's `get_run` finds it, and the receipt ends `needs_person run_mismatch`, with 0 `run_step` calls and 0 model calls. It kills M-a58, M-a59 and M-a60.
- **New D2c:** a fault hook creates the foreign run between `get_run` and `create_run`. `handle(run_id=X)` raises `StaleState`, the receipt is released (`step_error`), and the next claim gives `run_mismatch`. It kills M-a51 together with a direct `handle` case.

**BN-20. Postgres shape of the inbound methods (R3-COR-10).**
- Interface 4 gains: the inbound methods use explicit SQL, not `_row` (`postgres.py:178-189`). `readers` is written as a sorted `list[str]` into a `text[]` column and rebuilt as a `frozenset` on read (psycopg 3.3.6 cannot adapt a `frozenset`; F7, probe). Each of the three tables has a `schema_version` column (`Shape`, `models.py:50-52`).
- L1 and L16 compare the read-back record with the written one, including `readers` as a `frozenset`.

**BN-21. Dependencies: hard versus merge order (R3-COR-13; PENDING LEAD 18).**
- **The split table's "Depends on" for AK-G2-a:**
  - HARD: P4d (contract harness), P3a (migration ledger check), P2a-1 (role setup and trigger rules; the `limits_unavailable` path that D4b uses), AK1-a (`pipeline/step.py` names).
  - MERGE ORDER ONLY: P4c-2 and P5c (both edit `runtime/agent_loop.py` first). `limits.daily_budget`, `limits.monthly_budget` (`agent_loop.py:244`) and `limits_unavailable` (`:672`) already exist on main.
- **Said plainly to the lead:** AK-G2-a cannot start until P5c merges unless the lead takes the peel (round 1 ADV-22), or lets AK-G2-a merge first and P5c rebase on `agent_loop.py`, per order 20 item 5.
- AK-G2-b: HARD on AK-G2-a and P6a-1; AK1-b only for C5.

**BN-22. Strict UTF-8, the purge's missing run, and Surface wording (R3-COR-14, R3-COR-15).**
- **Door step (4):** `text = body.decode("utf-8")` (strict) and then `json.loads(text, object_pairs_hook=...)`, with `UnicodeDecodeError` included in the 400. W5 gains a UTF-16 body with a byte order mark: 400. **Mutant M-b36** (`triggers/webhook.py`): `json.loads(body)` on bytes. Killed by W5.
- **Purge case (ii):** a `done` receipt whose run does not exist (the `LEFT JOIN` gives no row) is treated as "run not open", so its body is deleted at `before`. L13 gains this case.
- **Surface:** "three `App` fields (`inbox`, `inbound_steps`, `inbound_doors`)" everywhere, so `:106` and `:213` agree.

**BN-23. Table delta and totals (one place for the builder).**
- **New rows (9):** D2c, D12, D13, D14, L20, L21, B3 (-a); W17, C9 (-b). **Removed (1):** L12.
- **Changed rows:** L1, L3, L13, L14, L16, L18, L19, D2b, D3a, D4b, D10, D11 (-a); W5, W6, W7, W13, C2b, C4, C8 (-b).
- **New mutants (27):** M-a55..M-a70 (16); M-b27..M-b37 (11). **Retired:** M-a12. **Redefined:** M-b22.
- **Totals:** **70 rows**:
  - -a 43: D0; L1-L11, L11b, L13-L21 (21); D1, D2, D2b, D2c, D3a, D3b, D4, D4b, D5-D14 (18); B1-B3.
  - -b 27: W1-W17; C1, C2, C2b, C3-C9.
- **Mutants: 103:**
  - -a 69: M-a1..M-a70 minus M-a12.
  - -b 34: M-b1..M-b9 and M-b13..M-b37.
- **Arithmetic:** 62 + 9 - 1 = 70; 77 + 27 - 1 = 103.
- One FAIL-BEFORE row (D0) and one premise row (W3), unchanged.
- **Surface after the notes:**
  - 10 store methods, 3 tables, 2 partial indexes, 1 trigger.
  - 1 new exception class (`InboundKeyChanged`).
  - New config fields `audience`, `key_check_ack`; `max_body_bytes` optional.
  - New `InboundSource.stuck_s`; one tick helper.
  - Cut: `compare_ids`, `IdComparison`, `list_inbound`, the orphan build refusal, two tick result keys.
- **Evidence files gain** `a-burst-history.txt` (B3) and `pre-revert-<sha>.txt` (BN-15, lead-run, only at a revert).

## Positions
- **BN-2 makes the receipt follow the run.** It is the only reopen path in v1, and "fix, do not defer" rules out a message lost to a transient `evidence_unavailable`. The cost is a double signal (a run and a receipt) that AK-G15 can merge on its screen through `trigger_ref`.
- **BN-3 is a check, not a dual-key lookup.** Trying both the current and the previous key at every receive would keep dedupe across a rotation, but it doubles every key computation and adds a key-id lifecycle. The check makes the change loud and fail closed, and leaves the dedupe loss as a stated, acknowledged choice.
- **BN-8 and BN-13 use the tick's existing failure path** (raise, then ERROR, `last_error` and exit 1) instead of new result keys or a build refusal. That cuts two keys and one refusal, and signals in the way schedulers already alert on.
- **BN-14 cuts by order 8.** Code with no caller gives no reconciliation either way. The control moves, with its tests, to the package that has the caller.
- **BN-6 adds design on a security path** (order 7(3) allows it): the owner rule says a forged-input exposure gets a control, not a note.
- **R3-ADV-18 is the only DECLINE.** It asks for nothing.

## Couplings
- **AK-G15:** it builds `list_inbound`, `compare_ids` and the command (V7, BN-14), the person's close (V15, BN-13) and the reopen screen with the old run's state and the `outcome_unknown` warning (BN-7). It reads `run_needs_person` receipts (BN-2). Re-drive and V7 must ship before any pilot.
- **AK1 (rev 3 plus `reviews/AK1-round3-resolve.md`):** no AK1 name used here changes (F10). BN-9 needs no new AK1 reason.
- **The core `stuck` step (`tick.py:100-131`):** BN-17 refactors its formula into a helper, behaviour unchanged. The tool-time gap is row V16 (new): "`stuck_after_s` also counts tool time (core tick)", trigger "a healthy run marked interrupted in a pilot". It is not AK-G2's code.
- **P4c (PL25):** BN-18 follows the lowered cap by name, never by number.
- **P2a-1:** the third table `inbound_key_checks` gets runtime `_RW` and no trigger. The reopen `NOT EXISTS` reads `runs` under the runtime role. Tested on PostgreSQL 16 and 17.
- **Runbook (AK-G16 hosting and the deployment runbook):** overlapping ticks (BN-7), the key-check acknowledgement (BN-3), the audience naming (BN-6) and the pre-revert count (BN-15).
- **`owner-visible-limits.md`:** PL4 (vi) reworded and (ix), (x), (xi) added. The lead adds them when it next edits the file.

## PENDING LEAD (continuing the ticket's numbering after 6)
Routing rule (lead's brief): an item that touches an owner-only choice, money, redaction, least privilege, order wording or tenant isolation is NEEDS LEAD. An item where I have a recommendation and none of those applies is INFORM, and the builder takes the recommendation meanwhile. For NEEDS LEAD items too, the builder applies the recommended option meanwhile, because each is the fail-closed side.
7. **NEW, INFORM. Freeze with build notes, no round 4.** There are 12 Majors (11 distinct), so order 20 item 6 rules out a round 4. The banner goes under the revision line.
8. **NEW, INFORM. `done` versus `needs_person` for run ends outside `LIMITS_END` (BN-2).** Recommend `needs_person run_needs_person` for every `NEEDS_PERSON` run, and `run_limits` for `DENIED limits.*`. `run_budget` is decided as `needs_person`. Reason: reopen works only from `needs_person`, and R368 says one final state that a person can act on. Confidence 80 percent. Reversible (one classify rule).
9. **NEW, NEEDS LEAD (secrets, money, personal data; extends PENDING LEAD 6). Key check for rotation (BN-3).**
   - (a) **Recommended:** keep PENDING LEAD 6 (c) (inbound key derived from the restored-hash key) and add BN-3's check and acknowledgement. No new secret.
   - (b) PENDING LEAD 6 (a), a dedicated inbound key, with the same check. One more secret per deployment, but rotating the restored-hash key then never touches inbound.
   - (c) No check: a rotation silently allows second paid runs on retries. Not recommended.
   - Confidence 70 percent for (a) over (b). Both are reversible before any pilot.
10. **NEW, NEEDS LEAD (tenant isolation). Shared agent or principal across tenants (BN-5).**
    - (a) **Recommended:** refuse at build in every environment.
    - (b) Allow it and state it as an owner-visible limit.
    - (a) is the R369 reading, and it costs one config check. Confidence 85 percent.
11. **NEW, NEEDS LEAD (money). Reopen while the earlier run is still open (BN-7).**
    - (a) **Recommended:** `reopen_inbound` refuses while that run is in `OPEN_STATES`, and AK-G15 warns on `outcome_unknown`.
    - (b) Only AK-G15's screen warns.
    - (a) prevents a second paid run beside a live one at the store, whichever screen calls it. Confidence 80 percent.
12. **NEW, NEEDS LEAD (owner rule R368; order 8 cut). `compare_ids` and `list_inbound` (BN-14).**
    - (a) **Recommended:** cut both from AK-G2 and build them, with the command, in AK-G15 before any pilot (V7).
    - (b) Keep them, and ship V7's command in AK-G2-b now (about 20 lines, 2 rows, 1 mutant).
    - Either way, nothing reaches a person in v1 until a caller exists. Confidence 70 percent.
13. **NEW, INFORM. Infrastructure classification (BN-9).** Use `is_connectivity_error` at every dispatch site and at the door. A store failure inside the step counts as a try, said in Words. Confidence 85 percent.
14. **NEW, INFORM. Lease arithmetic (BN-17).** The fake-llm numbers are 300/360 s and 780/840 s, and the network numbers 780/840 s and 2220/2280 s. A `(config, registry)` helper preserves behaviour. Confidence 90 percent.
15. **NEW, INFORM. `max_body_bytes` default `None` (BN-18).** It follows `evidence.max_document_bytes` by name, so P4c PL25's lowering cannot break default builds. Confidence 90 percent.
16. **NEW, INFORM. The orphan check moves from `app.build` to the dispatch step (BN-13, BN-8).** A build refusal stops the whole tick (F6). Confidence 80 percent.
17. **NEW, INFORM (security control; changes the forwarder contract). Required `audience` (BN-6).** Recommend: required everywhere. The cost is one body field per forwarder. Confidence 75 percent.
18. **NEW, INFORM to the lead (merge order). Hard versus merge-order dependencies (BN-21).** AK-G2-a waits for P5c unless the lead takes the peel or lets P5c rebase. The lead's call under order 20 item 5.

## Counts
- **Finding ids: 33** (ADV 18, COR 15).
  - Majors: 12 (ADV-1 to ADV-5, COR-1 to COR-7). One duplicate pair (ADV-1 = COR-3), so 11 distinct Major defects.
  - Minors: 17 (ADV-6 to ADV-16, COR-8 to COR-13). Nits: 4 (ADV-17, ADV-18, COR-14, COR-15).
  - No Blocker. No severity changed.
- **Decision rows: 24** (merged: ADV-1 + COR-3; ADV-3 + COR-12; ADV-7 + ADV-14 + COR-11; ADV-8 + COR-6; COR-1 + COR-2 + ADV-9; ADV-10 + COR-9; ADV-13 + COR-7).
- **Categories by row:** PROPOSE FIX 23 (4 of them surface cuts: ADV-8/COR-6, ADV-13/COR-7, ADV-15, and the results keys inside BN-8); DECLINE 1 (ADV-18); CONTEST 0; ESCALATE 0. Four NEEDS LEAD items carry a recommendation (PENDING LEAD 9 to 12).
- **Build notes:** 23 (BN-1 to BN-23; BN-23 holds the delta and totals).
- **Totals after the notes:** 70 test rows (-a 43, -b 27), 103 mutants (-a 69, -b 34), 10 store methods, 3 tables.
- **PENDING LEAD:** 12 new (7 to 18). 4 NEEDS LEAD (9, 10, 11, 12), 8 INFORM. None asks the owner for money, a live call or a key.
- **Probes run:** 1, read-only, not evidence. Tests, lints and mutants run: 0.
- **Fixes applied to the ticket in this step:** 0 (they are build notes). Remaining unaddressed findings: 0.

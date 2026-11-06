# AK-G2 round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

AK-G2 REVISION 2 (commit 77163e9), round 2 correctness. Read-only. I did not read handover/reviews/ or handover/evidence/. I read AK-G2.md in full, the template, and the cited src, tests and AK1/P4c lines. Line numbers below are ticket lines from my read of AK-G2.md. "Cite" means a file:line in the ticket text.

Overall: 0 Blockers, 3 Majors, 7 Minors, 4 Nits. The counts, the 17 fields and the times are right. The Majors are a split of config types between the two PRs, an unbuildable default, and an undecided case where a transient failure consumes a message.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 75, 94, 120-122 vs 131, 141-142 | AK-G2-a cannot be built alone. `Inbox(settings: InboundSettings)`, `receive(source: WebhookSource, ...)` and `dispatch(sources: Sequence[WebhookSource], ...)` use `source.agent_id`, `.readers`, `.max_open`, `.name`, `.tenant` and `settings.lease_s`, `.max_attempts` and `.dispatch_budget_s`. Both classes are created in `config.py`, which is listed only under -b. The -a tests (D9, L10, L17, B1/B2) need both. The ticket does not say where they live in -a. | Move `InboundSettings` and `WebhookSource` (the fields only) into -a's file list. Or give -a a plain `Source` dataclass in `triggers/ledger.py` that -b's config maps onto. Name the choice. |
| R2-COR-2 | Major | 131 (`lease_s` default 900 + build refusal when `lease_s < stuck_after_s`) | The default cannot build for normal agents. `stuck_after_s = max_steps x call_timeout_s x max_attempts + 60` (`tick.py:100-109`). The llm defaults are `call_timeout_s=60.0` and `max_attempts=3` (`backends/table.py:37-40`). That gives 960 s for an agent with `max_steps=5` and 2220 s for 12 (the config default is 12, `config.py:169`). The ticket default of 900 passes only for `max_steps <= 4`. So the default config gets `ConfigError` at build for most agents. Row C2 does not catch this because it only tests a low `lease_s`. | Pick one. (a) Make `lease_s` default to `None` and derive it as `max(stuck_after_s)+margin`. (b) Raise the default and ceiling. (c) State that `lease_s` must be set per deployment. Add a test row where the default config builds with the registry's default agents. |
| R2-COR-3 | Major | 342 (UNVERIFIED), 124, 298 (I4), 129 | The ticket leaves open whether `MeterUnavailable`/`OverBudget` escape `Runtime.handle`. My checks: neither name exists in this `src` tree (grep: 0 matches), so main differs from P4c. P4c rev 3 (`P4c.md:75`, `:83`, `:87`) says they are caught inside `handle` and end the run `NEEDS_PERSON limits_unavailable` or `run_budget` or a wall reason. `handle` then RETURNS, `StartRun` returns `done`, and the receipt is `done`. So a transient meter outage or a mid-run wall consumes the message into a `NEEDS_PERSON` run. This is the same "message used up by a run that ends at once" that I4 and the Problem text (line 90) say AK-G2 prevents. Today `_limits_stop` (`agent_loop.py:239-250`) also has a per-run cap `run_budget` that dispatch's `blocked()` check cannot see. The ticket's "if they escape, final needs_person" branch is moot and the real case is undecided. | State the behaviour under P4c rev 3. Either accept it (receipt `done`, run `NEEDS_PERSON`, body kept to the ceiling) and add it to Interface 5's "remaining race" and to PENDING LEAD 4. Or have `StartRun` return `needs_person` with a retryable reason when the returned run is `NEEDS_PERSON` with `limits_unavailable`. Add a test row for it. |
| R2-COR-4 | Minor | 129, 124, 182 (D3), 123 | Retry after a half-made run is empty. After `create_run` succeeds, a retry of `handle(run_id=X)` returns the existing run and `StartRun` says `done` (Interface 6). So "`step_error` / `audit_unavailable` -> release -> tried again" only helps for failures before `create_run`. A `StoreUnavailable` raised inside `handle` after `create_run` (for example in `_to` at `agent_loop.py:350`) ends `done` on attempt 2, not "exhausted after `max_attempts`". D3 does not say where the fault is injected, so as written it contradicts Interface 6. | In D3, say the fault comes before `create_run`. Add a row for a fault after `create_run`: second attempt `done`, run left to `stuck`. Say in Interface 5/6 which failures are retried. |
| R2-COR-5 | Minor | 121 vs 120, 97 | `InboundReceipt.run_id` is required, but the id-reuse row's `run_id` is never specified. Dispatch also reads `rec.item_id`, which is not a field (it is `"inb-" + delivery_key[:32]`). | State the reuse row's `run_id` (for example `"run-"+its own key[:32]`, and that no run is ever created). Make `item_id` a named derived property. |
| R2-COR-6 | Minor | 121 (2), 171 (L11) | The busy check runs before dedupe, so a retry of an already-accepted message gets 503 instead of 202 while the source is full. The sender keeps retrying and nothing is lost, but L11/W7 never cover it. L11's bound "at most 3 + 4 open" is loose: from 0 open with `max_open` 3, 4 racers give at most 4 open, or max_open + receivers - 1 in general. | Say which behaviour is intended and add a row. Fix the L11 bound. |
| R2-COR-7 | Minor | 189-190 (B1, B2), 131 | Burst rows deliver 2,000 and 10,000 messages with "retry until 202 or 409", then dispatch afterwards. With the default `max_open` of 1000, senders get `busy` forever, because nothing drains while they wait. The `max_open` value for B1/B2 is not stated. | Set `max_open` >= deliveries for B1/B2 (and say so), or interleave dispatch. State the retry cap. |
| R2-COR-8 | Minor | 112, 97, 109, 110 | The closed reason set per final state is only half defined. `finish_inbound(state, reason)` says the reason must be "in its closed set". `INBOUND_REASONS` mixes `id_reuse` (refused only), `attempts_exhausted`/`body_missing` (needs_person). The ticket does not say whether `finish_inbound(refused, "attempts_exhausted")` is allowed. L9 tests only "outside the closed sets". | Give the table: state -> allowed reasons. L9 should assert the cross-state pairs are refused. |
| R2-COR-9 | Minor | 122 | `limits.blocked()` can raise `StoreUnavailable` (it reads the kill-switch table and spend, `limits.py:20-30`). It is called before each claim, outside the per-receipt isolation. The ticket does not say whether that skips the source, ends the step, or propagates. | State it (skip the source, log the class name, count it) and add it to D4. |
| R2-COR-10 | Minor | 154 | The arithmetic is almost right but the formula over-counts. With a 20 s budget, a 10 s run and the check before each claim, runs start at 0 s and 10 s, so exactly 2 run. "Budget/run time plus one" would say 3. 2-3 per tick is right only with run-time jitter. The ticket says the tick runs "every 30-60 s" in places; at 30 s the figure doubles to about 4-6 a minute. The prior tick steps and a slow run (up to `stuck_after_s`, see R2-COR-2) also eat the tick time. | Write "between `floor(budget/run)` and `floor(budget/run)+1` per tick" and state the tick period used. Label it arithmetic (it already is). |
| R2-COR-11 | Minor | 130 (step 1, serve) | 404 for an unknown source comes before authentication, so source names can be probed. Dev server only, and AK-G16 owns hosting, but the ticket says "deny by default". The dev server's too-large `Content-Length` reject needs the per-source cap, but the server picks the source only from the path. The ticket does not say how `serve` gets the cap. | Say that the 404/413 order is intended and that `serve` looks the source up from the path before reading the body. |
| R2-COR-12 | Nit | 243 (M-a25) | The mutant sits in `triggers/ledger.py`, but `claim_inbound` is a store method returning ONE receipt (line 107). "Takes several receipts" cannot be done in the ledger. | Move the mutant to "store". |
| R2-COR-13 | Nit | 120 | `qualified: frozenset[str]`, but `Runtime.agents` is a `set` (`agent_loop.py:199`). | Say "copied to a frozenset at build". |
| R2-COR-14 | Nit | 3 and 9 | Round-1 counts (36 ids in 31 rows, 12 Majors) cannot be checked here because I did not read the reviews. | UNVERIFIED by design. |
| R2-COR-15 | Nit | 177 (L17) | L17 uses a fake clock for the lease and `dispatch_budget_s` uses the monotonic clock. 5 steps of 0.9 x `lease_s` (810 s each) would exceed a 20 s budget unless the monotonic clock is separate. | Say the monotonic fake clock does not advance in L17. |

## Verified (read in code or ticket text)
Counts and fields:
- 52 rows: -a 31 (D0, L1-L19, D1-D9, B1-B2) and -b 21 (W1-W15, C1-C6).
- 61 mutants: M-a1 to M-a44 (44), and M-b1 to M-b9 plus M-b13 to M-b20 (9 + 8 = 17).
- 10 INFORM (I1-I10), 5 PENDING LEAD, 12 later rows (V1-V10, V12, V13).
- Every mutant has a named killer row that exists and could kill it. M-a25 sits in the wrong file (R2-COR-12).
- Template: 17 fields, in the template's order (template lines 3-19).
- Times: 04:09 UTC = 09:39 IST; 03:47 = 09:17; 09:30 UTC = 15:00 IST. The 15:00 figure is as written in the ticket.

Code cites that match:
- `Runtime.handle` at `agent_loop.py:325-348`: signature (no `run_id` parameter), `Unqualified` at :339-340, `Run(...)` with fresh id at :342, `create_run` at :348, `_limits_stop` at :359. `_limits_stop` is at :239-250, with the kill switch at :241-242 and other reasons at :243-244.
- `create_run` raises `StaleState` on a repeated id (`memory.py:51-54`, `postgres.py:238-242`).
- `models.py`: `Run` and `trigger_kind` at :94-95, `new_id` at :23, `sha256_hex` at :46, `OPEN_STATES` at :75 without `NEEDS_PERSON` and `STOPPED`, and the comment at :72-74.
- `runs.ALLOWED` (`runtime/runs.py:10`) has no `NEEDS_PERSON` key, so it is FINAL, and any state can move to `STOPPED`. This matches the purge keep-list.
- `dead_letters` table (`0001_core.sql:77-85`): `seq` primary key only, no foreign key to `runs`, so a dead letter for a run that was never created is possible. The `runs` table is at :5-19 and has no tenant column.
- `limits.blocked` at `limits.py:20-30` returns the three reasons and is a read.
- `hmac_v0`: `sign` :31, `verify` :37-51, `MAX_AGE_S=300` :19, empty-secret refusal :41, 12-digit rule :47, `compare_digest` :51, signed text :26-28.
- `migrate.py`: `Grant` :24-37, `_RW`/`_APPEND` :40-41, `GRANTS` :46-68, `runs` `purge_cols` :47, `redaction_maps` with purge DELETE :65.
- `0002_audit_chain.sql:28-35` trigger pattern (`BEFORE UPDATE OR DELETE`; no `ENABLE ALWAYS` there, so that part is P2a's).
- Tick:
  - `tick.py` `stuck_after_s` :100-109, `STUCK` :112-119, `STEPS` :249-266, `reconcile` at :251, `_each` :63.
  - `test_p7_tick.py:82-89` lists exactly the six names.
  - `cli.py:286-298` matches.
  - `config.py:317` matches.
- `app.py` fields and purge store at :54, :59, :86-89, :151-154.
- `registry.py:68` and :218, and `agent_loop.py:199` match.
- `receiver.py` `serve` at :40, Content-Length parse at :45.
- `store/protocol.py:104-105` for dead letters.
- AK1 rev 2 text:
  - `StepInput` (:94), `Outcome` (:95), `REASONS` (:96), `Step` (:98), `run_step` (:99-106) and `REASON_BY_ERROR` (:104) match. `run_step` RETURNS `audit_unavailable` (:100).
  - `tenant_key` is length-prefixed (:92).
  - `NON_TABLE_PATHS` (:110) and the class table (:107) match.
  - The stop-request ownership note (:55) and the tenant decision (:138) match.
  - `ITEM_ID_PATTERN` accepts `inb-<32 hex>` and `run-<32 hex>`.
- AK1-a ships only the `AuditUnavailable` row of `REASON_BY_ERROR`, so `Unqualified` and `StoreUnavailable` map to `step_error`, as the ticket says.
- LEAD-ORDERS order 23 (line 107) and order 27 item 63 (line 155) exist.

## Not checked (UNVERIFIED)
- Any file under `handover/reviews/` or `handover/evidence/` (barred).
- `amendments.md` (the grep found only one long line), `owner-visible-limits.md` (no inbound entry, consistent with I9), `tickets/P2a.md` and `tickets/P4d.md` (so "ENABLE ALWAYS" and the contract-suite group are UNVERIFIED), `tickets/P4b1.md:51` and `plan-v3.md:134`.
- Promotion-input cites: dealdesk `inbox.py` lines and sha, MANIFEST ids, intake-6b, apexc.
- `ce70eb5` as the base sha.
- Lines `AK1.md:15` and `:47`; `slack_channel.py:207-213`; `tick.py:184-198` and `:196`; `0001_core.sql` for the `purge_cols` use; `protocol.py:50-51`.
- Whether main differs: this tree has no `MeterUnavailable`, `OverBudget` or `Limits.caps`, so P4b1/P4c are not merged here. All statements about handle's metering rest on `P4c.md` rev 3 text (see R2-COR-3).
- The ticket's PostgreSQL behaviour: `FOR UPDATE SKIP LOCKED`, the trigger under P2a roles, and the PostgreSQL 16/17 claims.
- Pass numbers for B2 (PENDING LEAD 2). The dispatch-capacity numbers are arithmetic, not measured.
- Secrets: I saw none. The ticket uses `<SECRET>`, `person-1@example.invalid` and `tenant-a` style placeholders only.
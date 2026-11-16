# Core hardening hand-off v5 (R460), 2026-11-16 (UTC) / 2026-11-16 (IST)

Replaces v4 (kept unchanged). Fixes the 5 blockers and 10 majors of the v4 security review, the 7 majors and the nits of the v4 readiness review, the 9 citation failures, and folds in the window-end audit and its review. Where each finding went: `v5-CHANGES.md`.

Status words: **specified, unverified** = written from code I read this pass, nothing run. **read** / **not read** = whether I opened the cited code. **needs lead** / **OWNER-OPEN** = a decision only the lead or the owner can make; each has a safe default that ships if nobody answers (section 3).

**Not on the demo's critical path.** Core is paused for the demo (owner, 2026-11-13). This hand-off is a plan for the next core work after the demo; nothing in it blocks the demo. D5 (Decimal or integer money) is OWNER-OPEN and non-blocking (lead answer Q28).

## 0. What failed, what is uncertain, what was not run (read first, stated once)

1. **Nothing in the repository was run.** No test, `ruff`, `bandit`, Postgres, G4 probe, redaction canary. The only thing I executed was a scratch script in the session scratchpad that compiles the new regular expressions of section 4.9 with Python's `re` and matches them against the listed lines (it does not import any repo code). Every design below is **specified, unverified**; evidence batch E0 (section 7) turns each into a fact. Every PR status in section 6 reads "specified, unverified" on purpose.
2. **The one design question the reviews forced, answered:** v4 said `add_spend` alone could do reserve, settle and release. That is false for three reasons found in the code and the reviews: a reservation had no identity, so settle twice or keep-then-release was legal (security B-2); a refused reservation was briefly visible and two commits (add, undo) left a crash gap (readiness M4, security M-1); and the runtime could lower a total by any amount (security M-5). v5 therefore adds a **minimal append-only table `spend_op` and three store methods** (4.1). The cost: one migration and a Store protocol change (an out-of-tree custom store is refused at start by `missing_methods`, `store/protocol.py:151-160`; CHANGELOG upgrade step).
3. **Not read or not checked:** Postgres behaviour of anything (no Postgres here); the kinds' constructors and the `make()` factory (so the way `gate` reaches a kind is **specified, unverified**); `k1b/loop.py` beyond lines 36-56 and 110-124; `guard/redact.py` pattern bodies; `agent_loop.py` outside the sites named; test bodies other than `test_s5_runtime.py:60-114`, `test_k5_tools.py:700-735`, and the lines cited from `test_g4_parity.py`; `ledger.md`; `ci.yml`; fence handling in G3 (the marker rule sees one physical line only); the demos beyond `pipeline.py:155`; whether any fixture config has a zero price; the 3-characters-per-token estimator against real replies (no recording measured). `grep -ril cache` finds no cache file under `llm/` (the hits are secrets, evidence, k1b replay, table); I did not read `k1b/replay.py` or `runtime/evidence.py` for a model-reply cache, so "no model-reply cache exists" is **not verified**.
4. **Gap in this pass:** none of the five inputs was missing. The readiness review of v4 appeared at 12:53 UTC, after I started, and is fully covered (`v5-CHANGES.md`, ids R-M1..R-M7 and R-n*).
5. **Third-party limit that cannot be fixed in code (exception 2c):** a provider may bill an attempt that failed before a reply reached us. Next step: a monthly comparison of our spend rows against the vendor invoice, in a sheet. Who: the owner receives the invoice and names the person who does it; the lead tracks the name in `handover/STATUS.md`; the name is due 2026-11-18 (same date in UTC and IST), the first comparison is at the end of the first live window. Rule for the sheet row: our total for the month, the invoice total, the difference, and one sentence if the difference is not zero. No named alternative vendor process exists, so none is claimed.
6. **Arithmetic caveat (once):** token and dollar figures use the 3-characters-per-token estimator (`llm/common.py:59-62`) and the fixture route 3.00 / 15.00 per million tokens, `max_tokens` 1024 (`tests/fixtures/config/config.yaml:6-8`). The only measured figure I read is `0.00225` per fake call (`tests/test_s4_llm_guard.py:39`, `tests/test_s5_runtime.py:76`). E0-5 prints the rest. I do not repeat v4's `0.0155` figure: it was never recomputed and the reserve now includes tools, schema and a margin (4.1).

## 1. Facts (source read this pass unless marked)

| # | Fact | Source | Read |
|---|---|---|---|
| F1 | G4 is a display filter: it swaps commands in model-written approval text for `[command withheld (G4)]`; it does not decide whether a tool runs. | `approvals/gate.py:681-698` | read |
| F2 | `_WRITE_SHAPES` is one compiled regex with no global ignore-case; SQL words are upper-case only; only some alternatives carry `(?i:...)`. | `gate.py:647-678` | read |
| F3 | Model call first, charge after, two separate writes: `limits.charge` then `store.add_cost`, at `agent_loop.py:440-441`; the injection screen does the same at `:314-315`. | agent_loop.py | read |
| F4 | `Store.add_spend(agent, day, usd)` adds `usd` (any sign) to a day row and a month row and returns the new (day, month) totals. Memory: one lock. Postgres: one transaction, two upserts with `RETURNING`. Tables `spend` and `spend_month`: `usd NUMERIC NOT NULL`, no sign check. | `store/memory.py:196-204`, `store/postgres.py:416-431`, `migrations/0001_core.sql:87-92`, `0003_approvals_tick.sql:15-20`, `store/protocol.py:107-111` | read (SQL of 0003 via citation check) |
| F5 | `Limits.blocked` reads `registry.agents[agent_id]`, so a made-up id (`eval:x`) raises `KeyError`; it tests `>=`. `Limits` has no clock: it calls `models.now()` (`models.py:19-20`, bare `datetime.now(UTC)`). | `limits.py:17-30`; `app.py:73,171` (the `clock` argument reaches only `Approvals`, `app.py:176-184`) | read |
| F6 | Retries live in `with_retry` (`llm/retry.py:83-108`): a `ProviderError` is re-raised at once, every other failure that is not transient becomes `ProviderError`, a transient one that keeps failing becomes `ProviderExhausted`. A malformed 200 answer is also a `ProviderError`, raised inside the retried call. All four network kinds call `self._retry(` (`anthropic.py:122`, `bedrock.py:156`, `gemini.py:86`, `openai_compat.py:119`); `_retry` is `llm/common.py:233`. | retry.py, kinds | read |
| F7 | `.chat(` call sites in `src/`: `extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94` (daemon thread). Outside `src/`: `demos/ask-your-data/askdata/pipeline.py:155` (own meter, `meter.py`). Paid calls that are not `.chat(`: `guard/bedrock_guardrail.py:101` (`apply_guardrail`; no cost field in the file). | grep, reads | read |
| F8 | `Runtime.__init__` receives `llm` and `Limits` directly; `tests/k5_support.py:160-204` builds a `Runtime` without `app.py`. `app.py:162` builds `llm` (`llm or make(...)`), `app.py:165` gives the judge member that same `llm`, `app.py:171` builds `Limits`. `app.py:90-98` refuses `sources=` and `tools=` in pilot and prod but not `llm=`. | app.py, k5_support.py | read (k5_support by citation check) |
| F9 | The CLI `gate` branch builds only an `llm` (`cli.py:146-153`; `make("llm"...)` at `:150`): no store, no limits. The replay branch builds `llm` and the judge detector at `cli.py:221-222`. Store-using branches build secrets, probe them, then the store (`cli.py:183-189`). `evals.gate` also runs `judge.qualify` on the same `llm` (`evals.py:101-110`). | cli.py, evals.py | read |
| F10 | `extract()` has no non-test caller in `src/`. Recorded fake replies are keyed on `sha256(documents[0])` (`llm/fake.py:39-40`). | grep | read |
| F11 | `Verification` has `rows, signed_through, problems, unreadable`; `ok` and `unsigned_tail` are properties (`audit/chain.py:134-149`). `verify_rows(rows, checkpoints, public_key, anchors, alg, row_algs)` (`chain.py:362-385`) has no `checkpoint_every`; `ChainAudit` holds it (`chain.py:171`). `anchor.all()` returns `{seq: (head, signature)}` with no time stamp (`anchor_s3.py:70`). `audit_verify` prints rows, signed-through and `intact` or `NOT intact` (`cli.py:349-363`). | chain.py, cli.py | read |
| F12 | `mounted_file._fetch` runs `confined()`, then `os.open` with `O_NOFOLLOW|O_NONBLOCK`, `fstat`, `S_ISREG`, then refuses a file readable by others or writable by group or others (group read allowed); the permission test is skipped on Windows (`os.name != "nt"`). `audit/signer.py:104-108` does `is_file()` + `read_bytes()`, no check. | `actions/secrets_file.py:34-64`, `signer.py` | read |
| F13 | `GUARD_STOP_REASONS` (`agent_loop.py:83`) includes `run_budget`; K6 counts every non-null `caught_by` as a caught mistake (comment `:79-82`); `_abstain` sets `caught_by` only for those reasons (`:569-575`). `limits.*` stops use `_to(...)` with no card at `:244`, `:672` and `:703`. | agent_loop.py | read |
| F14 | `Config.environment: Literal["dev","pilot","prod"]` (`config.py:317`); "demo" exists only after the rename (R449). `deferred.LIVE = ("pilot","prod")` (`deferred.py:33`). `("llm","fake")` is in `DEV_ONLY` (`backends/table.py:593-602`), so pilot and prod already refuse the fake kind (`config.py:366-370`). `load_config` wraps a pydantic `ValueError` as `ConfigError` (`config.py:453`). | config.py, table.py | read |
| F15 | `Money` rejects floats only (`config.py:41-47`); it is used by `Route` prices (`config.py:57-58`), `Budget` (`registry.py:35-36`) and `max_run_usd` (`registry.py:53`). `Budget` has no sign or order check. `Reply.cost_usd` is a bare `Decimal` (`models.py:294`). | config.py, registry.py, models.py | read |
| F16 | `DeadLetter(run_id, reason, errors)`: `errors` is required (`models.py:218-222`). `Valid` is a plain dataclass (`extract.py:18-25`). `runmap.storable(mapping, kinds)` keeps only allowlist kinds whose originals fit their grammar (`guard/runmap.py:218-227`); `restore_value` handles `str`, `dict`, `list` only (`runmap.py:560-568`) and with `kinds=None` restores every stored kind including `NAME`, `ADDRESS`, `PHONE`, `EMAIL` (`defaults.py:108-122`); `IBAN` is not a stored kind. `redact_untrusted` escapes marker and placeholder look-alikes; `redact_text` does not (`runmap.py:275-304`). Runtime and evals decode documents with `decode("utf-8","replace")` (`evals.py:63`). | files | read |
| F17 | `injection_check` catches every `Exception` and returns a flagged `guard_unavailable` verdict (`guard/injection.py:85-101`); `qualify` counts that as a failed case (`judge.py:100-109`). `with_retry` classifies every non-`ProviderError` exception, so a new exception raised inside the retried call would be wrapped as `ProviderError`. | injection.py, judge.py, retry.py | read |

## 2. Ladder (rung table, R448)

| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Spend reserve, settle, release | exact admission cap, one booking per call, no double settle | `Store.add_spend` (rung 1, reuse): cannot give a reservation identity or a bounded refund (0, B-2, M-5) | F4 | the per-reservation record and the compare inside one transaction | KEEP-CODE (money safety): one table, three store methods, one meter class |
| Call gate (window end, deny when unmetered) | no paid call after the end date or outside a meter | none exists | grep, F6, F7 | money safety | KEEP-CODE (about 40 lines at the shared `NetworkLLM._retry`) |
| Redaction patterns, G4 shapes, audit claims, key-file check | safety | `secrets_file` checks (reuse by extraction) | F12 | brain | KEEP-CODE, reuse where code exists |
| Monthly provider invoice comparison | third-party billing gap | vendor invoice export plus a sheet (rung 2/3) | section 0 item 5 | nothing | CUT (no code) |
| Wall-hit notice | a person is told | existing card channel (`_abstain`) | F13 | the once-per-day rule | CUT-TO-CONFIG+GLUE |
| Orphan reservations view | a person sees stuck money | one read method plus a CLI line | 4.1 | the query | CUT-TO-CONFIG+GLUE |

## 3. Decisions D1-D22: what v5 resolved, and what the lead or owner must still answer

Every decision has a safe default that ships if nobody answers. "Needed by" is the first PR that cannot start without the default being accepted.

| Id | Decision | What changed in v5 | Finding(s) |
|---|---|---|---|
| D1 | Spend window end | Moved from `Config.spend_window_end: AwareDatetime` to `Config.spend.window_end: date \| "none" \| None` (UTC date, **last day calls are allowed**; refused from 00:00 UTC the next day). Required for every non-fake llm kind in every stage; prod may write `none` only with `spend.window_owner` (a role label, never a personal e-mail) and a start-up audit row plus a warning line. The fake kind ignores it (one rule, decided where the meter is built). The check sits in three places: `NetworkLLM._retry` per attempt (the choke point), `SpendMeter.reserve`, `Limits.blocked`. No stage name is spelled in the rule, so it does not depend on the rename (D6). | window audit and review (1-10), security M-3, readiness D1 |
| D2 | G4: wording or behaviour first | **Wording first** (v2 lead default): PR G-W (wording) merges before PR G (rows). Split from v4's single PR G. | readiness (sequencing), v2 D2 |
| D3 | Are `get-secret-value`, `get-session-token` read-only in approval text | Default: **no**, withheld (v2 default). Now a candidate row G5a, shipped only if the lead keeps this default, with the justification below the table (4.9). If the lead says read-only, the row is dropped. | readiness nit G5a |
| D4 | Refuse signer or anchor kind `none` in pilot | Unchanged: warn only until decided; hard deadline before the first pilot config is written. Owner. | v4 |
| D5 | Money as Decimal or integer minor units | **OWNER-OPEN, non-blocking.** Default ships: keep `Decimal`; M1 makes `Money` reject non-finite and negative values at the type (`config.py:41-47`). CLAUDE.md says "money is integers"; the owner decides whether `Decimal` is accepted for spend sums. | lead Q28, security B-1 |
| D6 | Stage name `dev` | Follow R449: refuse `dev`, rename to `demo`. v5 removes the ordering hazard: M1 and M2 never spell a stage name. Owner decides only whether an alias is allowed (default: none). | security B-3 |
| D7 | (was "reviews must run before PR-B") | Not a decision (EGM step 2). Listed so the id list is complete. | earlier note |
| D8 | (was "ledger rows") | Not a decision: the lead writes ledger rows before builders start. Listed for completeness. | earlier note |
| D9 | May a builder rewrite tests that pin the overshoot | Narrowed from v2: exactly one named test changes, `tests/test_s5_runtime.py:107-111` (DENIED at the gate becomes NEEDS_PERSON `limits.daily_budget`, no model call). `tests/test_k5_tools.py:723-731` is expected to pass unchanged; E0-1 decides, and if it does not the builder rewrites it with the new expected value in the same PR. | readiness |
| D10 | New alert kind | **No.** Wall hit = log line + audit row + one card through the existing channel. Trigger for a real alert kind: a client asks for paging or e-mail on a cap hit. | v2 |
| D11 | Zero-price routes | Refuse at registry load unless `backends.llm.kind == "fake"` (same rule as `k1b/replay.py:85-90`). Self-hosted flag deferred; trigger: first client build with a self-hosted route. | v4 |
| D12 | Local billing day | Keep UTC. Trigger: a client asks. | v4 |
| D13 | Wall-card dedupe store | In-process set, key added **only after the card was delivered** (4.4). Trigger for a store method: duplicate cards seen across replicas. | readiness M4 |
| D14 | Per-run cap inside the reserve | Yes: refuse when run cost so far + this call's reserve would exceed `max_run_usd`. Stricter than today's `>=` after the fact. E0-5 shows whether any fixture route breaks. Needed by M2. | v4 |
| D15 | Orphan reservation (reserved, never finished) | Stays counted (fail closed). Bound: `spend.max_call_usd` caps one reservation; the orphan view (4.1) lists every open reservation older than `spend.orphan_alert_after_s`; correction is an audited command (`Limits.correct`, 4.1), never automatic. | security M-1, M-5 |
| D16 | Lowercase bare SQL | Stays shown unless a code marker is present (4.9 rule G3). Revisit trigger: E0-6 shows a model writing such lines in approval text. | v4 |
| D17 | Redaction base64 second pass and speculative patterns | Deferred; a pattern ships only if its canary leaks on old code (E0-4). | v4 |
| D18 | Anchor-writer identity split and outbox alert age | Deferred. **Correction of v4:** the S3 module docstring does NOT today state the identity rights (`anchor_s3.py:1-12` says only "written by a principal the runtime cannot delete with (S11)"; grep for `PutObject`, `GetObject`, `ListBucket` in `audit/*.py`: none). There is no "default today". H-1 writes that docstring (4.11); the split itself waits for the first pilot config. Owner. | citation X1 |
| D19 | Per-call worst-case cap `spend.max_call_usd` | Default taken from `defaults.py` (a new constant, value chosen from E0-5 output, so no number is invented here); a reserve above it is refused with code `call_too_large`. Needed by M2. | security M-1 |
| D20 | Estimator margin `spend.reserve_margin` | One factor for every reservation, replacing v4's invented 1.5 for the judge only. Initial value is **unmeasured**; E0-5 compares reserved against actual on recorded replies and the lead sets it from that. Needed by M2. | readiness M2, nit judge |
| D21 | Upper-case or `.EXE` program names (G2c) | Dropped from the PR: `KUBECTL.EXE delete ns prod` stays shown by `withhold_commands`, but `channel.clean` rewrites the dot to `KUBECTL[.]EXE`, so the reader cannot paste it. That is a defanged display, not a leak (evidence `evidence-handoff-v4.md`). Revisit only if E0-6 finds a display path that skips `clean`. | evidence |
| D22 | PDFs and images in `extract()` | Always refused (`extract_unmaskable`); core has no text step that could mask them. Trigger: the first client build that needs PDF input adds a text-extraction kind in front of `extract`, with masking after it. | security M-8 |
| FA | False-abstain ceiling for M2 (`.claude/rules/false-abstain-reporting.md`) | Unchanged: 0 new abstains on the golden set; policy stops listed separately. Lead, in the eval contract, before M2. | v4 |
| RC | Round caps | Section 6 tags. | v4 |

**Lead to answer (all have defaults):** needed before M1: D1 (confirm "last day allowed", UTC); needed before M2: D14, D19, D20, FA; needed before G: D2 order and D3; on trigger: D11, D12, D13, D16, D17, D22; before the first pilot config: D4, D18 (owner). **Owner only, non-blocking:** D5, D6 alias, D4, D18.

## 4. Designs

### 4.1 Spend: reserve, settle, release (resolves security B-1, B-2, M-1, M-4, M-5; readiness M1, M2, nits)

**Admission rule (honest bound).** The sum of admitted reservations never exceeds a cap, because the compare and the add are one store transaction (below). That is a statement about reserved amounts. The money actually billed can pass a cap by the estimator error: at most the sum, over calls that were sent, of (actual cost minus reserved amount) where positive; with N calls in flight at once, N times the per-call error. A call already sent cannot be recalled. "Exact cap" and "can never be admitted wrongly" are removed from this design.

**Store (the choke point), both stores, new migration `0006`:**
```
spend_op(op_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, day DATE NOT NULL,
         kind TEXT NOT NULL CHECK (kind IN ('reserve','final')),
         usd NUMERIC NOT NULL, ts TIMESTAMPTZ NOT NULL)          -- append only: no UPDATE, no DELETE
Store.reserve_spend(res_id, agent_id, day, usd, daily, monthly) -> Reserved(admitted, which, day_total, month_total)
Store.finish_spend(res_id, how, actual_usd) -> Finished(applied, day_total, month_total)   # how: settle | release | keep | correction
Store.list_open_reservations(older_than, limit) -> list[OpenReservation(res_id, agent_id, day, usd, ts)]
```
- `reserve_spend`: in one transaction: insert op `res_id:reserve`; upsert day and month rows; compare the returned totals with `daily` and `monthly` using `>`; if either is exceeded, roll back (no trace, no transient total, no crash gap); `which` says daily or monthly. A repeated `res_id` returns the recorded outcome and adds nothing. Postgres: the `ON CONFLICT DO UPDATE` row lock is held to the end of the transaction, so parallel reservers queue on the row (**unverified: E0-3 on two connections**). Memory: the same steps under `self._lock`.
- `finish_spend`: inserts op `res_id:final` (primary key, so exactly one final per reservation: settle then release, or settle twice, is a no-op returning `applied=False`). Delta: `settle` = actual minus reserved; `release` = minus reserved; `keep` = 0; `correction` = minus reserved, accepted only through `Limits.correct`. Because every negative delta is bounded by the recorded reserve of the same id and used once, the runtime can never lower a total below what it added itself; no clamp and no `spend_clamped` are needed (v4's clamp is dropped: it was two writes and hid double release). An unknown `res_id` raises `UnknownReservation`.
- **Validation at the choke point (security B-1):** `reserve_spend`, `finish_spend` and the legacy `add_spend` reject `usd` that is not finite (`Decimal.is_finite()`), negative, or above `defaults.MAX_SPEND_OP_USD` (new constant) with `ValueError` before any write; `add_spend` (still used by `Limits.charge` and tests) becomes non-negative only (E0-1 checks no test adds a negative; the greps show none). `Money` (`config.py:41-47`) rejects NaN, infinity and negative at the type, which covers `Route` prices, `Budget` and `max_run_usd` in one place; `Budget` also refuses `daily > monthly` (E0-7 greps configs). `Reply.cost_usd` gets `Field(ge=0, allow_inf_nan=False)` (`models.py:294`) so no adapter can hand in a negative or NaN cost; `settle` still treats a bad value as `keep` and logs `spend_bad_cost`.
- `day` is checked where it is chosen: `SpendMeter.reserve` uses `clock().date()`; `finish_spend` takes the day from the recorded reserve op, never from the caller.

**`SpendMeter` (`limits.py`, needs only a store and the clock; the CLI gate has no registry or audit):**
```
class SpendRefused(Exception): code in {"kill_switch","window_ended","daily_budget","monthly_budget","run_budget",
                                         "call_too_large","unmetered","meter_unavailable"}   # defined in llm/protocol.py, next to ProviderError
SpendMeter(store, clock=models.now, gate=CallGate)
  .scope(key, daily, monthly, run_id=None, run_cap=None) -> context manager      # sets the active SpendScope (a ContextVar)
  .reserve(scope, usd) -> Reservation(res_id, key, day, usd, run_id)             # raises SpendRefused
  .settle(res, actual) / .release(res) / .keep(res)                              # never raise
```
`reserve` steps in order: (1) kill switch on (store read; a store error is `meter_unavailable`) -> `kill_switch`; (2) `gate.check_window()` -> `window_ended`; (3) `usd > spend.max_call_usd` -> `call_too_large` (D19); (4) `run_cap` given and `store.get_run(run_id).cost_usd + usd > run_cap` -> `run_budget` (D14); (5) `store.reserve_spend(...)`; not admitted -> `daily_budget` or `monthly_budget`. A zero `usd` never trips a zero cap (`0 > 0` is false), so zero-price fake routes keep working. The comparison is `>` (would exceed); `Limits.blocked` keeps `>=` (already at the cap); both are pinned by a test side by side.

`settle`, `release`, `keep` call `finish_spend` and write `store.add_cost(run_id, amount)` **only when `applied` is true** (settle: the actual; keep: the reserved amount; release: nothing). If the store raises (`StoreUnavailable`, or `NotFound` from `add_cost` at `memory.py:76-80`), they catch it, log `spend_finish_failed` (class name only), and leave the reservation open and counted: money fails closed, and the run's cost row may then be low until the orphan view is read. If the actual is larger than the reserve, the extra is booked and `spend_overrun` is logged; it never raises after a provider billed.

**Worst case, full input.** New `llm/common.py:worst_case_usd(route, system, messages, documents, tools, output_schema, margin)`: estimated input tokens over system + JSON of messages + JSON of the tool list as the kind builds it (`tools_for`, `common.py:65-83`, which also turns `output_schema` into the forced answer tool) + each document decoded the way `turns` does (`common.py:86-100`, `decode("utf-8","replace")`), at `estimate_tokens` (3 characters per token) times the input price, plus `route.max_tokens` times the output price, per million, times `spend.reserve_margin` (D20). The estimator is wrong for CJK text and base64 (more tokens per character) and is not defined for PDF or image bytes (refused by `extract`, D22; the runtime sends text only). That is why the margin exists and why section 4.1 states a bound, not exactness. `k1b/loop.py:115-124` keeps its smaller copy until k1b joins (4.2); the PR lists it as a promotion item.

**Outcome table of the wrapper `MeteredLLM.chat` (the booking rule):**
| What happened | Booking | Why |
|---|---|---|
| reply | settle(actual) | normal; includes a reply that later fails to parse |
| `ProviderRefused` (new subclass of `ProviderError`: HTTP 400, 401, 403, 404, 422 seen, so no generation) | release | a definite client error before any billing |
| any other `ProviderError`, `ProviderExhausted`, an unparseable 200 (`common.py:195`), a timeout, any other `Exception` | keep (one worst case) | v4 released on every `ProviderError`; F6 shows a billed 200 with a bad body is a `ProviderError` too (readiness M1) |
| `SpendRefused` raised by the call gate (below) | release | the gate refused before the request left |
| `KeyboardInterrupt` and other non-`Exception` exits | reservation stays open | fail closed |
`ProviderRefused` is raised by `with_retry` (`retry.py:83-108`) from `status(exc)` (`retry.py:31-36`) in that status set; every other path is unchanged. A crash loop or an outage can fill a day with kept reservations (every failed call keeps one worst case): the bound is the cap itself, the wall card tells a person, and the orphan view lists them.

**Orphan view and correction.** `Limits.orphans(older_than)` (read) feeds `hadavin-sdk limits orphans`, which prints count, total and oldest age; the tick logs a warning when any is older than `spend.orphan_alert_after_s` (default in `defaults.py`; no new alert kind, D10). `Limits.correct(res_id, by, reason)` mirrors `Limits.reset` (`limits.py:48-51`): `audit.write_intent(...)` first (if the audit write fails, nothing changes), then `finish_spend(res_id, "correction", 0)`. **What this does not enforce:** database grants cannot separate values inside one table, so a compromised runtime process could call the same store method. What bounds it: a correction only removes the amount that reservation added, once; a census test allows `correction` only in `cli.py` and `limits.py`; and the CLI branch builds its own store (`cli.py:183-189`), so an operator can run it under a different database role. If the owner wants grants to enforce it, the option is a separate `spend_correction` table with INSERT only for that role and totals computed as spend minus corrections; trigger: first pilot config.

### 4.2 Where the calls are gated (resolves window audit, security B-3, readiness M5 and D1)

**One choke point plus deny by default.** The check that decides whether a model call may leave the process sits in `NetworkLLM._retry` (`llm/common.py:233`), once per attempt. All four network kinds go through it (F6), so a caller-supplied `llm=`, the CLI, a directly built `Runtime`, the judge and `extract` are all covered without each remembering to wrap. `NetworkLLM` gets a `gate: CallGate | None` attribute (set by the shared builder below). At each attempt `_retry` runs `gate.check_window()` and requires an active `SpendScope`: no `gate`, a past window, or no scope raises `SpendRefused` (`window_ended` or `unmetered`). `with_retry` is changed to re-raise `SpendRefused` untouched (as it does for `ProviderError`, `retry.py:95-96`), otherwise it would wrap it (F17).
- Fake kind: `FakeLLM` is not a `NetworkLLM` (`llm/fake.py:29`), so it needs no gate; budgets still book through `MeteredLLM` (4.1), which is why fake calls are priced like real ones.
- A call that starts just before the end date and is still running after it is billed: stated, bounded to the calls in flight; the per-attempt check stops a retry loop from running past the end.
- `app.py:90-98` gains a third refusal: in a live stage (`deferred.LIVE`), a supplied `llm=` is refused unless it is a `NetworkLLM` with a gate set. The `app.py:162` build and the two CLI builds (`cli.py:150`, `cli.py:221`) all call one new helper `llm/build.py:build_llm(cfg, secrets, clock)` that sets `gate`; so the three places cannot drift.

**Who puts a scope and a meter around each call (the census):**
| Caller | Wrapped by | Scope key | Caps |
|---|---|---|---|
| `agent_loop.py:425` | `Runtime.__init__` wraps `llm` in `MeteredLLM` if it is not one already; `Runtime.handle` opens the scope | `agent.id` | the agent budget, `max_run_usd` |
| injection judge `guard/judge.py:72` | `app.py:165` passes the judge member the metered `llm`; it reserves per call inside the open run scope, so several judge routes and a `guard_unavailable` verdict with no call are handled by the call itself (no `x1.5`, no booking for a call that never happened) | `agent.id` | the agent budget |
| `evals.py:73` and `judge.qualify` (`evals.py:109`) | the CLI `gate` branch (4.3) | `eval:<agent>` | `spend.eval_budget_usd` |
| `extract.py:47` | its caller opens a scope; `extract` books nothing itself | the caller's | the caller's |
| `k1b/loop.py:94` | `cli._k1b`: an in-process `SpendMeter` over a fresh `MemoryStore` with the k1b `Budget` limit as `daily` and `monthly`; the daemon thread runs the call inside `contextvars.copy_context().run`; a timed-out call stays a `keep`, which is what `k1b/loop.py:110-124` already charges | `replay:<run>` | the k1b `Budget` |
| `bedrock_guardrail.py:101` | window check only (no reservation: the file prices nothing); trigger to meter it: a configured per-unit price | n/a | n/a |
| `demos/ask-your-data/askdata/pipeline.py:155` | demo-only; keeps its own `Meter`. After the demo re-pins to this core it will pass a raw network llm and be **refused as unmetered**: the re-pin sweep must give it a scope (core-modules rule 5). A demo is never hand-edited from here. | n/a | n/a |

`injection_check` re-raises `SpendRefused` before its broad `except Exception` (`guard/injection.py:85-101`), and `qualify` (`judge.py:100-109`) calls it, so a refusal inside the judge is not turned into a silent flagged `guard_unavailable` (readiness M5, F17). Test: a refusal inside `qualify` exits the CLI with status 2.

**Removal sites (no double booking):** delete `self.limits.charge(...)` and `self.store.add_cost(...)` at `agent_loop.py:440-441`, and the `if verdict.cost_usd:` block at `:313-315`. `settle` and `keep` are the only writers of `add_cost`. `Limits.charge` stays for the operator and tests.

**Census test (AST, not a text grep):** parses every `src/**/*.py`, collects real `.chat(` calls (comments and docstrings excluded, so `guard/producers.py:5` does not count), and fails when the set differs from F7's five. Each entry names how it is metered. A second test fails if `Limits.charge` or `add_spend` is called in a model path, and if `correction` appears outside `cli.py` and `limits.py`.

**Test changes:** `tests/test_s5_runtime.py:107-111` (spent 0.999 then a reserve above 0.001): the run ends NEEDS_PERSON `limits.daily_budget` and `rt.llm.calls == []`. `tests/k5_support.py:160-204`: no change expected (the `Runtime` wraps its own llm). New tests: a fake that bills 0.30 on a reserve of about 0.05 books 0.30 and logs `spend_overrun`; settle twice, release after settle and keep after release each change nothing; a raw `NetworkLLM` with no scope is refused; a past window refuses on the second retry attempt; the `ProviderRefused`, unparseable-200 and timeout rows of the outcome table. Other tests with small budgets are found by the E0-1 full run; I did not read them all.

### 4.3 Eval ledger and the CLI (resolves readiness M3, security M-3)

- Config block (one place): `Config.spend: SpendSettings` with `window_end`, `window_owner`, `max_call_usd`, `reserve_margin`, `eval_budget_usd: Budget`, `orphan_alert_after_s`; defaults come from `defaults.py` (documented there) and `eval_budget_usd` defaults to 0 = no live eval spend. v4's two flat names (`spend_window_end`, `eval_budget_usd`) move into this block.
- CLI `gate` branch (`cli.py:146-153`): build secrets, probe, store as the audit branch does (`cli.py:183-189`). If `b.llm.kind == "fake"`, no meter. Otherwise: **refuse a memory store** with `ConfigError("eval spend needs a shared store")`, exit 2 (a memory store would reset the cap every run; this replaces v4's "documented as per-run"); build `llm = build_llm(...)`, wrap it in `MeteredLLM`, run `evals.gate` inside `meter.scope(key=f"eval:{agent}", daily=eval.daily, monthly=eval.monthly)`. A `SpendRefused` becomes `ConfigError("eval spend refused: <code>; set spend.eval_budget_usd (now 0)")`, exit 2. The same wrapped `llm` serves the judge qualification (`evals.py:109`).
- `Limits.blocked` is never called with `eval:*` ids (F5).

### 4.4 Wall hit: mapping, card, once per day (resolves readiness M3, M4; security M-2)

How each `SpendRefused` ends a run (the handler sits next to `except ProviderError` at `agent_loop.py:425-437`; it applies to the main call and to a refusal inside `_screen`, `agent_loop.py:310-316`):
| Code | Ends as | Card |
|---|---|---|
| `kill_switch` | `_to(run, S.STOPPED, "kill_switch")` (as `:241-242`) | none (operator action) |
| `run_budget` | the existing branch `:245-249`: `_note(...)` then `_abstain(run, NEEDS_PERSON, "run_budget", cited)`; stays in `GUARD_STOP_REASONS` | yes (as today) |
| `daily_budget`, `monthly_budget`, `window_ended` | new `_wall_stop(run, code, cited)` | once per agent, UTC day and code |
| `call_too_large` | `_abstain(run, NEEDS_PERSON, "call_too_large", cited)` | yes; not a guard catch |
| `meter_unavailable` | `_wall_stop(run, "limits_unavailable", cited)` (store unreadable; the card goes through the channel, which does not need the spend store; best effort) | once per agent, day, code |
| `unmetered` | `_to(NEEDS_PERSON, "unmetered")`, `_LOG.error` (a wiring bug, loud) | none |

`_wall_stop`: if `(agent_id, UTC day, code)` is already in the in-process set, end with `_to(...)` (audit row, no card); otherwise call `_abstain(..., on_delivered=mark)` where `_abstain` gets one optional callback that runs only in its `d.ok` branch (`agent_loop.py:569-597`). The key is added **only after delivery** (`_deliver` never raises and returns `ok=False` on a failed post, `:560-567`), so a failed first post does not hide later cards (D13). The set is guarded by a lock. A refused reservation leaves no trace in the totals (4.1, rolled back), so a parallel `_limits_stop` cannot post a wall card below the cap. `_REASON_TEXT` (`:87`) gets plain sentences for the new codes. `caught_by` stays `None` for these (K6 counts non-null as a caught mistake, F13). Unchanged on purpose: `:669-672` (limits unreadable before the gate) and `:702-703` (a post-call crossing): the next call is refused at reserve and announced by `_wall_stop`, so a person is told one call later at most. New `POLICY_STOP_REASONS = frozenset({"limits.daily_budget","limits.monthly_budget","limits.window_ended","run_budget","call_too_large","limits_unavailable"})` next to `GUARD_STOP_REASONS`, read only by the false-abstain report (E0-9). Test: N blocked runs on one agent and day post one card; a failed first post is followed by a delivered card; the kill switch posts none; a second code posts its own card.

### 4.5 Window end and zero price (D1, D11)

Rules and placement are in D1 and 4.2. Start-up audit for `none`: written in `app.build` right after the audit backend is built (the `audit = make(...)` statement just before `app.py:162`) by `audit.write_outcome(...)` and a `_LOG.warning`; named site, no new alert kind. `Config` gets a `model_validator` (the same place as the environment table, `config.py:362-375`) that reads `backends.llm.kind`, `environment == "prod"` and `spend`: non-fake with no date refused (prod: date or `none` plus owner); a `ValueError` becomes `ConfigError` (`config.py:453`). Clock: `models.now()`; `Limits`, `SpendMeter` and `CallGate` all take the `clock` argument of `app.build` (`app.py:73`), default `now`, so tests inject a fixed clock (today only `Approvals` receives it). Tests: non-fake with no date refused; prod with no value refused; prod with `none` and no owner refused; prod with `none` and owner accepted and audited; a past date blocks `Limits.blocked`, `reserve` and a raw `NetworkLLM` retry; the last day is allowed, the next day refused; the fake kind with a past date still runs. D11: `registry._cross_check` (`registry.py:338`) refuses a route with a zero input or output price unless the llm kind is fake (move the logic from `k1b/replay.py:85-90`, keep its test); the judge route (`judge.py:3-4`) is covered. E0-5 greps every fixture and demo config for a zero price first.

### 4.6 Audit claims, named and bounded (resolves security M-10; readiness A1 nits)

`tamper_evident` is removed from the design (one word would claim more than the code detects). `verify_rows` returns named facts, each with its bound:
- `rows` and `hash_chain_ok` (no link or hash problem): only the rows in the chain table.
- `signed_through` and `unsigned_tail`: the last `unsigned_tail` rows are not covered by any signature, so they can be rewritten without detection until the next checkpoint. Ceiling: new `defaults.AUDIT_MAX_UNSIGNED_TAIL` (value 100, equal to today's `checkpoint_every` default at `chain.py:161`); `checkpoint_every` is validated `<= ceiling` where the chain settings are read (`chain.py:519-547`; the settings class was **not read**). When a public key was given and `unsigned_tail > ceiling`, `problems` gets one line, so `ok` and the exit code 1 change (a deployment with no signer is not failed by this). Not a claim that the tail "stays at most `checkpoint_every`": it grows when the signer or the anchor fails.
- `anchored_checkpoints` (count of signed checkpoints whose `(head, signature)` equals the anchor's copy) and `anchor_supplied` (`anchors is not None`): zero checkpoints means a count of 0, never a vacuous "anchored".
- `anchor_retention_proven`: true only when the anchor kind's start-up probe ran (GCS `probed`, `anchor_gcs.py:69-85`; Azure `probed`, `anchor_azure.py:83-96`); false for S3 until H-1 adds its probe. Worded as "the anchor kind's own guarantee", not as proof against the same host.
- `signing_key_location` (`secret`, `file`, `none`) is printed by the CLI from settings (the verifier holds only a public key).
`cli.audit_verify` (`cli.py:349-363`) prints these lines and "not covered: rows still in the outbox, a stolen signing key, the last N unsigned rows"; exit codes stay 0 / 1 / 3. `ChainAudit.verify` passes `self.checkpoint_every` (`chain.py:171`); the bare `verify_rows` default is the ceiling. Tests on `verify_rows` with plain lists (no Postgres): healthy; no key; tail above ceiling with a key; anchors off; one broken link; zero checkpoints. A healthy chain stays within the ceiling because the inline checkpoint signs at `seq % checkpoint_every == 0` (`chain.py:203`) and `tick` checkpoints: **specified, unverified**.

### 4.7 `extract()` masking and restore (resolves security B-4, B-5, M-7, M-8, M-9, N-2; readiness M6)

Order inside `extract` before any model call: (1) decode **strict UTF-8** (intended difference from the runtime's `"replace"` at `evals.py:63`: a replacement character would hide the bytes it replaced from the redactor); failure returns `DeadLetter(run_id, reason="extract_unmaskable", errors=["document is not UTF-8 text"])` with a fixed string and no content (`errors` is required, F16); accepted encoding: UTF-8 only, a PDF, image or UTF-16 file is refused (D22). (2) `text = runmap.redact_untrusted(text, mapping)` with a fresh `mapping` (not `redact_text`: an untrusted document that already contains `<EMAIL_1>` next to a real e-mail must not forge a placeholder; same call as `evals.py:63`); a `RedactionError` returns `DeadLetter(reason="extract_unredactable", errors=["document could not be masked"])`, no call. (3) The retry text uses `safe_head(str(exc), 300, mapping)` with the same mapping (today `extract.py` passes none, so placeholder numbers can collide with the document's). `system`, the fixed ask line and `output_schema` are caller constants and are **not masked**; a caller that builds them from client text must mask them first. If a model-reply cache is ever added it must key on the masked text (nothing found in `llm/`, section 0 item 3).
**Result and restore contract:** `Valid.data` holds exactly what the model returned, so a masked value stays a placeholder. `Valid` gains `mapping: dict[str,str] = field(default_factory=dict, repr=False, compare=False)` holding **only** `runmap.storable(mapping, restore_kinds)` where `restore_kinds` is a new keyword parameter of `extract` defaulting to the empty frozenset (so by default no original leaves `extract`); `__repr__` cannot print it and a test checks `repr`, `str`, `dataclasses.asdict` and a JSON dump for a canary. `extract` never restores. The recipe a caller uses: `restored = runmap.restore_value(valid.data.model_dump(mode="json"), valid.mapping, restore_kinds)` then `schema.model_validate(restored)` (`data` is a pydantic `BaseModel`, and `restore_value` takes only `str`, `dict`, `list`: F16). `kinds` is always passed explicitly (with `None` it would restore `NAME`, `ADDRESS`, `PHONE`, `EMAIL`). `IBAN` is not a stored kind and **is not added**: the IBAN test asserts the value stays a placeholder after restore. Default scope: extract is for fields that are not personal data.
**Does masking damage the fields extract reads (M-9)?** Not measured. Risk from the pattern names: `PHONE`, `IBAN`, `CREDITCARD` and high-entropy patterns may match invoice numbers or references. E0-10 (no model, no spend) runs `redact_untrusted` over a made-up invoice corpus and counts, per schema field, how often the field's value changes; the PR ships only when amounts, dates and codes the schema reads show zero changes, or the changed kinds are named and the lead accepts them. The false-abstain and dead-letter rate by reason is then reported on the golden set (E0-9). Recorded fake replies are keyed on `sha256(documents[0])`, so recordings are re-keyed in the same PR. Tests: an e-mail, a phone number and a card number in the document do not reach `FakeLLM.everything_sent`; placeholders in the result; restore with an allowlist returns the original; a non-UTF-8 document makes no call; a document with a forged `<EMAIL_1>` next to a real e-mail does not restore to the real one; `repr(valid)` holds no canary. `guard/producers.py` row 36 is reworded so it does not imply the document is protected before this PR.

### 4.8 Key-file read (resolves zoom M-7, readiness S1 nits, security M-6)

Extract, do not copy: move the opened-file checks of `secrets_file._fetch` (`actions/secrets_file.py:49-64`: `S_ISREG`, readable-by-others, writable-by-group-or-others, read) into `hadavin_sdk/fileguard.py:read_private_file(path, *, what, allow_group_read, max_bytes) -> bytes` (standard library only; `what` supplies the message wording so the "mount it 0400 or 0440" text stays for mounts only). It opens the path as given with `O_NOFOLLOW|O_NONBLOCK` (so it **refuses a symlinked key**: a Kubernetes or Docker secret mount links its files, so a signer key on such a mount must be read through the mounted-file secrets kind, not `private_key_path`; the CLI error says so). `max_bytes` is new behaviour (default taken from `defaults.py`, tested with an oversized file).
- `mounted_file._fetch` keeps `confined()` and passes `allow_group_read=True` (0440 mounts keep working; its existing tests must pass unchanged, E0-1).
- `audit/signer.build_local` (`signer.py:104-108`) uses `allow_group_read=False`; the refusal mask there includes `S_IRGRP` (the mounted-file mask at `secrets_file.py:54` allows group read and does not).
- **Windows rule:** group and other bits do not exist there, so the check is skipped (as at `secrets_file.py:54`) and the folder ACL decides. v5 states it in the error text and the docs; and in prod `ed25519_local` with a key file is already refused (`config.py:393-394`). Tests that write keys must create them 0600 (`signer.py:182` does); the mode of hand-written fixtures is unchecked (E0-1 finds failures).
- Imports: `tests/test_lockin_guard.py:68-75` constrains vendor and library imports only; `fileguard` imports the standard library only. I did not search for a test forbidding `audit` importing a neutral module; E0-1 runs the guard.

### 4.9 G4 rows: only what leaks on old code ships (resolves readiness B2/M7, nits; evidence)

Rule: every row is run in E0-6 on the UNCHANGED gate first; only rows whose "withheld" example is **shown today** ship, each with a test proven failing on old code. Rows already withheld are dropped. The evidence run (`evidence-handoff-v4.md`, 125 pytest passed, 37 probes, 0 mismatches) confirms all definite v4 claims: G2a, G2b, G3 (12 lines plus the alias gap), G4a and G5a leak today; `> /dev/null kubectl delete pod x` is already withheld; **`git rebase -i HEAD~3` is already withheld, so its row is dropped** (v4's own rule). The other G5b words (`checkout clean commit merge pull`) were not probed: they stay candidates. G4 is a display filter only (F1).

**G3 discriminator.** The pinned shown lines and the lines to withhold share one lexical shape (`tests/test_g4_parity.py:98,221-222`), so no word rule separates them; a case-insensitive copy of the SQL alternatives of `_WRITE_SHAPES` withholds a match only when the same **physical line** also carries a marker. The marker test sees the line text before the match start and from the match start on; a match inside a fenced block is judged by its own line only (fences not handled). Compiled and matched in a scratch script (Python `re`), not run through the repo's gate:
- M1 a `;` anywhere after the match end on the line.
- M2 an odd number of backticks before the match start on the line.
- M3 after the match start: `\bset\s+[\w."]+\s*=` or `\bwhere\s+[\w."]+\s*(?:=|<>|!=|<|>|\bin\b|\blike\b)` (case-insensitive; `set x=1` and `where id=1` without spaces match).
- M4 after the match start: `\bvalues\s*\(` or `\binto\s+[\w."]+\s*\(`.
- M5 before the match start: `(?:^|\s)(?:\$|sql>|mysql>|psql>)\s*$` or `\s-[ce]\s+["']?$`.
The lowercase copy covers DROP, TRUNCATE, DELETE FROM, INSERT INTO and UPDATE only (the SQL alternatives that need a marker); the upper-case path is unchanged. The `UPDATE` alternative in both copies becomes `UPDATE\s+(?:ONLY\s+)?ID(?:\s+(?:AS\s+)?\w+)?\s+SET\b` (fixes `UPDATE t AS a SET x=1` and `UPDATE ONLY t SET x=1`, shown today).

Scratch result (match = withheld):
| Line | Marker | Withheld | Needed |
|---|---|---|---|
| `drop table users;` | M1 | yes | yes |
| `` `drop table users` `` | M2 | yes | yes |
| `delete from users where id = 1` and `...where id=1` | M3 | yes | yes |
| `update only t as a set x=1` | M3 | yes | yes |
| `insert into t values (1)` | M4 | yes | yes |
| `$ drop table users` | M5 | yes | yes |
| `drop table pressure`, `we should delete from the queue only after a fix`, `update its set of rules`, `delete from the queue where possible` (all pinned shown) | none | no | no |
| `drop table users` bare | none | no | accepted as shown (D16) |
| `we will drop table pressure; then rest` | M1 | yes | false positive, counted by E0-6 against the 2% budget |

| Item | Function | Rule | Withheld | Shown | Today |
|---|---|---|---|---|---|
| G1 | docstrings `gate.py:4`, `gate.py:366-377`, `channel.py:19-21` | Wording only: "a closed list of programs plus SQL and shell shapes". Its own PR G-W, merged first (D2). | n/a | n/a | wording |
| G2a | new `_join_continuations(text)` before `_PROGRAM` | Join backslash+newline, `^`+newline, backtick+newline (the `_TOKEN` pattern stops at a newline, `gate.py:546`). Joined text withholds to the end of the joined line, which can swallow the next physical line (`gate.py:695` cuts at the next `\n`): add a false-positive test where the line after a backtick-newline is plain prose. | ``kubectl \`` newline `delete ns prod` | ``we wrap lines with a backslash \`` newline `like this` | leaks (probed) |
| G2b | `_story` (`gate.py:608-615`) | Skip leading **bare** redirection tokens `>`, `>>`, `2>`, `<`, each plus the one target token after it, then judge the first remaining token. Not `|` (a pipe starts another command; `kubectl \| grep` stays prose-like). Glued forms (`>/dev/null`, `2>&1`) need no change: they already withhold. | `kubectl > /dev/null delete pod x` | `the aws Lambda runtime` | leaks (probed) |
| G3 | `_WRITE_SHAPES` | marker rule and alias fix above | table above | table above | leaks (probed, 12 lines) |
| G4a | `rm` shape (`gate.py:674`) | `\brm(?:\s+-[A-Za-z]+)*\s+(?:-[a-zA-Z]*[rRf][a-zA-Z]*\|--recursive\|--force)(?=\s+\S)` (keeps the long flags that v4's text dropped). Scratch: withholds `rm -v -rf /x`, `rm -rf /x`, `rm --force x`; shows `rm the file` and `rm -v x`. `rm` is not in `_NAMES` (`gate.py:540`), so the shape is the only guard. | `rm -v -rf /x` | `rm the file` | leaks (probed) |
| G5a | `_AWS_READ_PREFIXES` use (`gate.py:404`, `:597`) | Candidate (D3, default yes): a closed list `_AWS_NOT_READ = {"get-secret-value","get-session-token","get-login-password","get-authorization-token","get-password-data"}` consulted first in `_readonly`. Justification: these calls are read verbs that return a secret or a token to whoever pastes them; the prefix rule `get-` cannot tell them apart. The list is closed and short on purpose and is a second list to maintain; if the lead prefers no second list, the row is dropped and the generic `get-` read rule stays. | `aws secretsmanager get-secret-value --secret-id x` | `aws s3 ls` | leaks (probed) |
| G5b | `_WRITE_VERBS` / `_OWN` | **Dropped:** `git rebase -i HEAD~3` is withheld today. `checkout clean commit merge pull` stay candidates until probed. | | `the docker image was rebuilt overnight` (pinned) | rebase: not a leak; others unprobed |
| G2c | program-name case and suffix | **Dropped (D21).** | | | defanged by `channel.clean` |
| cand | `dd of=`, `mkfs`, `chmod -R`, `kill`, `shutdown`, `crontab -r`, `sed -i`, `rsync --delete`, redirect to a path, `tee`, `curl -X DELETE`, PowerShell verbs, quoted-command prose, read verb with write flag, capital-first positional, COPY, LOAD DATA, `nextval`, VACUUM, CALL, EXEC, DO, GRANT forms | each ships only if E0-6 shows a leak and no pinned shown line breaks | v3 section 5 | `we should kill the idea` | not probed |

Pinned shown lines (all must stay shown; E0-6 runs them): `rm the file`, `drop table pressure`, `we should delete from the queue only after a fix`, `a 'kubectl rollout restart' replaced the pods`, `the docker image was rebuilt overnight`, `update its set of rules`, `the aws Lambda runtime`. G4 stays a hybrid (closed program list plus shapes); the allowlist alternative stays rejected (prose is unbounded; 2% false-positive budget on at least 200 sentences) with the trigger: E0-6 finds a bypass class the shapes cannot cover, or measures false positives well under 2%. `_clean_line` normalisation runs before the `_OWN` lookup; `_subcommands` already lower-cases words (`gate.py:573-589`).

### 4.10 Redaction patterns (PR-2 first and alone)

PR-2 (4.7) ships first and alone. The pattern PR (R) ships only patterns whose canary leaks on old code (E0-4), each with a canary test (fake values built from parts; the only literal allowed is `AKIAIOSFODNN7EXAMPLE`) and a near-miss test:
- `PHONE` (`guard/redact.py:472`): `( ) . /` separators. Withheld `(415) 555-0132`; near-miss a date `2026-11-16`.
- `IBAN` (`:247`): spaced 4-character groups and lower case, normalised first.
- `CREDITCARD` (`:451`, 4-4-4-4 only today): 15-digit 4-6-5 grouping, 17-19 digits, dot separator. The value `4111...` also appears in `tests/warden_port/privacy_corpus.py:42` and `tests/warden_port/test_redaction.py:309,356`.
- `EMAIL` (`:236`): non-ASCII local part, quoted local part, soft break.
- A new pattern named `CREDPAIR` (a new label, not in `redact.py` today): `{"name": "<credential key>", "value": "..."}` in either order, case-insensitive, modelled on the HAR cookie pair near `:513`; share the credential-key test with `k1b/redaction.py:103` (`_pair`).
- URL credentials (signed-URL signature parameters, reset-link path tokens) and bare `passphrase`, `cvv`, `pin`, `dob` keys.
Deferred, trigger in D17: the base64 second pass and any pattern with no leaking canary. The input tripwire after masking depends on E0-4 (redacting masked text must be a fixed point).

### 4.11 Housekeeping track (non-gating)

- **H-0 stage rename (R449):** `field_validator("environment", mode="before")` on `Config` raises `ValueError("environment 'dev' was renamed to 'demo'; change it in your config")`; `load_config` returns a `ConfigError` (`config.py:453`). Value or logic sites: `config.py:317`, `:366-367`, `:19`, `backends/table.py:593` (`DEV_ONLY` to `DEMO_ONLY`), `tests/test_lockin_guard.py:18,430`, `tests/fixtures/config/config.yaml:2`, `tests/test_p4_secrets.py:106`, `tests/warden_port/test_audit_chain.py:568`, `tests/test_p1b_backends.py:89-91`. Wording sites: `actions/secrets_env.py:1`, `audit/signer.py:64,98`, `table.py:126,214,254,591`, `config.py:346`, `defaults.py:100`, `registry.py:50`, `tools.py:361`, `agent_loop.py:179,553,572`, `actions/contract.py:34`, `store/postgres.py:75,90`. Leave `guard/redact.py:1162` (a word list). CHANGELOG upgrade step; E0-8 greps demos for `environment: dev`. Round cap 2. It protects nothing today and, since M1 and M2 spell no stage name, it can land at any point.
- **H-1 audit retention floor and S3 probe:** the floor is **new** (the existing default of `retain_days` is 1, `backends/table.py:155`, `Field(default=1, ge=1)`; v4's wording "the existing 7" was wrong). One place covers all three anchor kinds: `_anchor_refusals(environment, b)` (`config.py:377-398`) gains `anchor.retain_days < defaults.ANCHOR_MIN_RETAIN_DAYS` (new constant, 7) in pilot and prod, so no per-kind build site changes (the settings class is `_AnchorSettings`, `table.py:150-157`, read). The S3 Object Lock probe is a new `probed(client, settings)` in `anchor_s3.py` (the S3 kind module only) modelled on GCS `probed` (`anchor_gcs.py:69-85`) and Azure `probed` (`anchor_azure.py:83-96`), reading the bucket's object-lock configuration. H-1 also writes the module docstring of `anchor_s3.py` stating the identity rights the writer needs (D18; the docstring has none today).
- **H-2 evidence docs:** wording and docs only, round cap 2, not a PR of its own if H-1 or G-W is open.

## 5. Dependency and least-privilege check

- No new vendor dependency. `gate`, `SpendMeter`, `MeteredLLM` live in core modules and import only core types; the Object Lock probe stays in the S3 kind module; `fileguard` is stdlib only. The invoice comparison needs no code.
- Identities and rights, in words: the **runtime** identity may insert `spend_op` rows (`reserve`, one `final` per reservation) and upsert the existing `spend` and `spend_month` rows; it cannot update or delete `spend_op` (grants, **unverified**: Postgres not run, E0-3). It can lower a total only by the amount of its own open reservation, once. It holds no approver or executor credential. The **operator** CLI identity (its own store connection, `cli.py:183-189`) may run `Limits.correct`, after an audit intent row. The **audit writer** is unchanged. A negative test per role: a second `finish_spend` on one id changes nothing; a `finish_spend` with `correction` outside `Limits.correct` fails the census test; a negative or NaN amount is refused by the store; the runtime cannot lower a total below the pre-reservation level. "Agents hold no store credentials" is **not verified**: it is a property of how a client build wires `Runtime`, not of this code.
- Eval spend default 0 (nothing live without the owner's numbers). Prod `none` needs a named owner role.

## 6. PR series, two tracks, one status column

Cap tag: U = uncapped (security, money, redaction, audit, secret), C = capped at 2 rounds. Every status reads "specified, unverified" until its E0 evidence and the lead's EGM review exist; the lead changes the cell. Size is in builder sessions of up to 60 minutes (rule: agent-speed estimates); heavy test slots: one full run per PR at the final head.

**Gating track (the live window waits for these):**
| Order | PR | Content | Cap | Depends on | Status |
|---|---|---|---|---|---|
| 1 | PR-2 | `extract()` masking, `redact_untrusted`, restore contract, re-keyed recordings (4.7) | U | none | specified, unverified |
| 2 | M1 | `Money`, `Budget`, `Reply.cost_usd` validation; `Config.spend` and D1 validator; D11 (4.1, 4.3, 4.5) | U | none | specified, unverified |
| 3 | M2a | migration `0006`, three store methods on both stores, `add_spend` validation, `SpendMeter`, `Limits.orphans`/`correct` (4.1) | U | M1 | specified, unverified |
| 4 | M2b | `NetworkLLM` gate, `build_llm`, `ProviderRefused`, `SpendRefused` through `with_retry`, `MeteredLLM`, `app.py` refusal, `injection_check` re-raise (4.2) | U | M1 | specified, unverified |
| 5 | M2c | `Runtime` wrapping and scope, judge member, removal sites, wall mapping and card, policy-stop set, census tests (4.2, 4.4) | U | M2a, M2b | specified, unverified |
| 6 | M3 | CLI `gate` (eval ledger), `replay` and guardrail window, k1b in-process meter (4.3, 4.2 table) | U | M2c | specified, unverified |
| 7 | R | Redaction patterns that leak on old code (4.10) | U | E0-4 | specified, unverified |
| 8 | S1 | `fileguard`, signer key check (4.8) | U | none | specified, unverified |
| 9 | A1 | Audit claims (4.6) | U | none | specified, unverified |
| 10 | G-W | G1 wording only | C | none | specified, unverified |
| 11 | G | G2a, G2b, G3, G4a, G5a (D3) rows that leak on old code (4.9) | U | G-W, E0-6 | specified, unverified |

Parallel: 1, 2, 7, 8, 9, 10 start together; 3 and 4 after 2; 5 after 3 and 4; 6 after 5; 11 after 10. 11 gating PRs (v4 had 8 but M2 was too large for one session).

**Housekeeping (not gating):** H-0 (C), H-1 (U, audit), H-2 (C). All three are independent of the gating track.

Deferred with trigger: calls cap and self-hosted flag (D11), local billing day (D12), anchor-writer split and outbox alert (D18), base64 and speculative patterns (D17), G4 candidate rows (4.9), store-backed wall dedupe (D13), metering the guardrail call, PDF text step (D22).

## 7. Evidence batch E0 (an EVIDENCE RUNNER runs these; the runner never judges)

- E0-1 full `pytest`, `ruff check`, `ruff format --check`, `bandit -ll` at each final head, one run each; includes the lockin guard, the `secrets_file` tests, a search for tests that call `add_spend` with a negative amount, and tests that build a `NetworkLLM` kind directly (they need a scope).
- E0-2 mutation sample (changed mutants plus 60-mutant sample), full run once, alone.
- E0-3 store contract tests on both stores (Postgres via `HADAVIN_TEST_PG_DSN`, two connections): 8 threads reserve against one cap and the admitted sum never exceeds it; a refused reserve leaves totals and `spend_op` unchanged; settle twice, release after settle, keep after release: one effect; `finish_spend` cannot lower a total below the pre-reservation level; NaN, infinity, negative, huge amount refused (fuzz); runtime role cannot UPDATE or DELETE `spend_op`.
- E0-4 redaction: masked text is a fixed point; one canary per pattern on OLD code (leak = ships); fuzz `redact_text`.
- E0-5 reserve sizing over every fixture and demo config route and agent: print `worst_case_usd` for an empty call and a full-context call (with tools and schema); compare reserved with actual on recorded replies (sets D20); pick `max_call_usd` (D19); flag a reserve above 50% of the daily cap or the run cap; grep every route for a zero price; list tests that break under the new reserve.
- E0-6 every row of 4.9, every pinned shown line and the recorded corpus through `withhold_commands` and `channel.clean` on old and new code; false-positive rate on at least 200 prose sentences (budget 2%); new tests run on old code to prove they fail; the G2a next-line false-positive test; the G5b words not yet probed.
- E0-7 `Money`, `Budget` (`daily > monthly`), `Route` and `Reply.cost_usd` with NaN, infinity, negative; a documents-recording fake across `extract`, `evals`, `guard/judge`; every existing config still loads.
- E0-8 grep stage sites and `environment: dev` in demos and configs.
- E0-9 false-abstain split on the golden set: answerable abstained / answerable; policy stops (4.4) listed separately; dead-letter rate by reason for `extract`; never "N/M correct" without the split.
- E0-10 masking damage (4.7): `redact_untrusted` over a made-up invoice corpus, per schema field the count of changed values.

## 8. Item homes

| Item | Home |
|---|---|
| Money guard, reserve, call gate, wall card, eval ledger | M1, M2a-c, M3 |
| Redaction | PR-2, R |
| Approval text | G-W, G |
| Audit claims; retention | A1; H-1 |
| Key file read | S1 |
| Stage rename | H-0 |
| Provider invoice comparison (third party) | owner names the person by 2026-11-18; lead tracks in `handover/STATUS.md` |

## 9. What I did NOT check (repeat so it is not lost)

Everything in section 0 items 1 and 3; Postgres concurrency and grants of `spend_op` and the `ON CONFLICT` row-lock ordering; whether any test other than `test_s5_runtime.py:107-111` breaks under the reserve; how `make("llm", ...)` and `make("detector", ...)` accept the new `gate` (kinds' constructors not read); `k1b/loop.py` in full; the anchor settings for `checkpoint_every` (chain settings class); the exact text of the existing tests that import `Money`; fence handling for marker M2. Nothing here is "verified"; the lead runs the EGM review on this hand-off and on each PR.

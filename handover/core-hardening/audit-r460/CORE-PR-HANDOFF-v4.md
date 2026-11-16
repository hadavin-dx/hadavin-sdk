# Core hardening hand-off v4 (R460), 2026-11-16 (UTC) / 2026-11-16 (IST)

Replaces v3 (kept unchanged). Fixes the two readiness Blockers and nine Majors of the v3 readiness review and the nine Majors of the v3 zoom-out review. Every finding and where it went: `resolve-handoff-v4.md`.

Status words: **specified, unverified** = written from code I read this pass; nothing was run. **needs lead** = a decision only the lead or owner can make; each has a safe default that ships if nobody answers (section 3).

## 0. What failed, what is uncertain, what was not run (read first, stated once)

1. **Nothing was run.** No test, no `ruff`, no `bandit`, no Postgres, no G4 string, no redaction canary. `markdown_it` is missing in this sandbox, so `approvals.gate` cannot be imported. Every line below is **specified, unverified**; the E0 batch (section 7) turns them into facts. The status column in section 6 therefore reads "specified, unverified" for every PR on purpose.
2. **v3 was wrong in four places (corrected here):** (a) it said a new reservations table and a sweep were needed; reading `store.add_spend` shows they are not (4.1); (b) its G4 example `> /dev/null kubectl delete pod x` is not the real bypass: the first-token test looks at the word AFTER the program name, so the real bypass is `kubectl > /dev/null delete pod x` (4.9, `gate.py:608-615`); (c) it called `get-secret-value` an entry to remove, but no such entry exists: the whole `get-` prefix is read-only in `_AWS_READ_PREFIXES` (`gate.py:404`, used at `gate.py:597`); (d) it said lowercase SQL needed a new discriminator against the pinned prose lines, but `_WRITE_SHAPES` is case-sensitive today (no `re.IGNORECASE` on the compiled pattern, `gate.py:647-678`), and that is what keeps `drop table pressure` shown now.
3. **Not read or not checked:** adapter bodies; Postgres behaviour of any change (no Postgres here); the setting class names for the three anchor kinds; `guard/redact.py` beyond what v3 recorded; `ledger.md`; `ci.yml`; how `sanitise_text` treats fenced code (G3 marker M2); demos pipeline; the 0.0155 arithmetic; test key-file modes.
4. **Third-party limit that cannot be fixed in code (exception 2c):** a provider may bill an attempt that failed before a reply reached us; we cannot see it. Next step: a monthly reconcile of our spend rows against the vendor invoice (the vendor's own invoice export compared in a sheet; no named alternative vendor process exists, so none is claimed). Owner: lead. Date: 2026-11-16 to name the person; first reconcile with the first live window.
5. **Arithmetic caveat (once):** every token and dollar figure here uses the 3-characters-per-token estimator in `llm/common.py` and the fixture route 3.00 / 15.00 per million tokens, `max_tokens` 1024. The only measured figure I read is `0.00225` per fake call (`tests/test_s4_llm_guard.py:39`, `tests/test_s5_runtime.py:76`). E0-5 prints the rest.

## 1. Facts (corrected; source read this pass)

| # | Fact | Source |
|---|---|---|
| F1 | G4 is a display filter: it swaps commands in model-written approval text for `[command withheld (G4)]`. It does not decide whether a tool runs. | `approvals/gate.py:681-698` |
| F2 | `_WRITE_SHAPES` is one compiled regex with no global ignore-case; only some alternatives carry `(?i:...)`. SQL alternatives are upper-case only. | `gate.py:647-678` |
| F3 | Model call first, charge after: `limits.charge` then `store.add_cost`, two separate writes, at `agent_loop.py:440-441`; the injection judge does the same at `agent_loop.py:313-315`. | agent_loop.py |
| F4 | `Store.add_spend(agent, day, usd)` adds `usd` (any sign) to a day row and a month row and returns the NEW (day, month) totals. Memory: one lock. Postgres: one transaction, two `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`. Tables `spend` and `spend_month`: `usd NUMERIC NOT NULL`, no foreign key, no sign check. `spend_totals` is a read. | `store/memory.py:196-216`, `store/postgres.py:416-442`, `migrations/0001_core.sql:87-92`, `0003_approvals_tick.sql:15-20`, `store/protocol.py:107-111` |
| F5 | `Limits.blocked` reads `registry.agents[agent_id]`, so a made-up id such as `eval:x` raises `KeyError`. It tests `day >= daily` and `month >= monthly`. | `limits.py:20-30` |
| F6 | Retries happen inside one `chat()` (`llm/retry.py:83-108`). `ProviderError` = not retried; `ProviderExhausted(ProviderError)` = retried and gave up. | `llm/protocol.py:9-15` |
| F7 | Model-call sites (`.chat(`): `extract.py:47`, `evals.py:73`, `guard/judge.py:72` (also reached from `evals.gate` via `judge.qualify`, `evals.py:109`), `runtime/agent_loop.py:425`, `k1b/loop.py:94`. `k1b` runs the call in a daemon thread. | grep, reads |
| F8 | `Runtime.__init__` receives `llm` and `Limits` directly; `tests/k5_support.py:160-204` builds `Runtime` without `app.py`. `app.py:162` builds `llm`, `app.py:171` builds `Limits`; the judge member gets the raw `llm` (`app.py:164`). | app.py, k5_support.py |
| F9 | The CLI `gate` branch builds only an `llm` (`cli.py:146-153`): no store, no limits. Other branches build `secrets`, probe them, then the store (`cli.py:179-184`). `evals.gate` also runs `judge.qualify` on the same `llm` (`evals.py:101-110`). | cli.py, evals.py |
| F10 | `extract()` has no non-test caller in `src/`; callers are `tests/test_s4_llm_guard.py:49`, `tests/test_k5_round9.py`, `tests/demo_askdata/`. Recorded fake replies are keyed on `sha256(documents[0])` (`llm/fake.py:39-40`). | grep |
| F11 | `Verification` fields: `rows, signed_through, problems, unreadable`; `ok` and `unsigned_tail` are properties (`audit/chain.py:134-149`). `verify_rows(rows, checkpoints, public_key, anchors, alg, row_algs)` already knows whether a public key and anchors exist (`chain.py:362-385`). `anchor.all()` returns `{seq: (head, signature)}` with no time stamp. | chain.py, anchor_s3.py:70 |
| F12 | `mounted_file._fetch` runs `confined()`, then `os.open` with `O_NOFOLLOW|O_NONBLOCK`, then `fstat`, `S_ISREG`, refuses other-readable and group/other-writable (group-read allowed). `audit/signer.py:104-108` does `is_file()` + `read_bytes()`: no check. | secrets_file.py:34-64, signer.py |
| F13 | `GUARD_STOP_REASONS` (`agent_loop.py:83`) includes `run_budget`; K6 counts every non-null `caught_by` as a caught mistake (comment `agent_loop.py:79-82`). `_abstain` sets `caught_by` only for those reasons (`:575`). `limits.*` ends are `_to(...)` with no card at `:244`, `:669`, `:702`. | agent_loop.py |
| F14 | `Config.environment: Literal["dev","pilot","prod"]` (`config.py:317`). `load_config` wraps pydantic `ValueError` as `ConfigError` via `str(exc)` (`config.py:453`). | config.py |
| F15 | `Money` rejects floats only (`config.py:41-47`). `Budget(daily, monthly)` has no sign or order check (`registry.py:33-36`). | config.py, registry.py |

## 2. Ladder (rung table, R448)

| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Spend reserve/settle/release | exact cap, no overspend by parallel callers | existing `Store.add_spend` (rung 1: reuse) | F4: atomic add returning totals | the compare-and-undo rule, the per-call wrapper | CUT-TO-CONFIG+GLUE (about 80 lines, no table, no migration) |
| Call wrapper | one booking per model call | none exists | F7 | money safety | KEEP-CODE (one small class) |
| Redaction patterns, G4 shapes, audit verdict, key-file check | safety | `actions/secrets_file.py` checks (reuse by extraction) | F12 | brain | KEEP-CODE, reuse where code exists |
| Monthly provider invoice reconcile | third-party billing gap | vendor invoice export + sheet (rung 2/3) | section 0 item 4 | nothing | CUT (no code) |
| Wall-hit alert | person is told | existing card channel (`_abstain`) | F13 | the condition | CUT-TO-CONFIG+GLUE |

## 3. Decisions (lead or owner; each has a safe default that ships if nobody answers)

| ID | Question | Safe default (used until answered) | Who | By |
|---|---|---|---|---|
| D1 | Spend window end date | `Config.spend_window_end: AwareDatetime | Literal["none"] | None`. Demo and pilot with a non-fake model kind: a date is required. Prod: a date or the word `none`; silence is refused; `none` is written to audit at start-up. | lead confirms; owner told | before M1 |
| D5 | Money as Decimal or integer minor units | Keep Decimal; M1 refuses negative and non-finite `Budget` and `Route` values (Decimal rejects floats already, F15). CLAUDE.md says integers, so owner decides. | owner | before M1 |
| D6 | Stage name `dev` | Follow R449: refuse `dev`, rename to `demo`, error names the rename. An alias would contradict R449; needs the owner's yes. | owner (alias only) | before H-0 |
| D11 | Zero-price routes | Refuse at registry load unless `backends.llm.kind == "fake"` (same rule as `k1b/replay.py:85-90`). Self-hosted flag and calls cap deferred; trigger: first client build with a self-hosted route. | lead | on trigger |
| D12 | Local billing day | Keep UTC. Trigger: a client asks. | lead | on trigger |
| D4 | Refuse signer or anchor kind `none` in pilot | Warn only until decided; hard deadline before the first pilot config is written. | owner | before first pilot config |
| FA | False-abstain ceiling for M2 (`.claude/rules/false-abstain-reporting.md`) | 0 new abstains on the golden set; policy stops (list in 4.4) counted separately, never mixed into "answerable abstained". | lead, in eval-contract | before M2 |
| RC | Round caps | See section 6 tags. | lead | now |
| D13 | Wall-hit card dedupe store | In-process set in `Runtime` (no migration). Trigger: duplicate cards seen from more than one runtime replica; then a store method. Worst case today: one extra card per replica per agent, day and code; never a lost alert. | lead | on trigger |
| D14 | Per-run cap inside the reserve | Yes: refuse when run cost so far + worst case would exceed `max_run_usd` (code `run_budget`). Stricter than today (`>=` after the fact). E0-5 shows whether any fixture route breaks. | lead | before M2 |
| D15 | Orphan reservation (process dies between reserve and settle) | Stays counted for the day and month (fail closed); no automatic refund. Size: at most one worst case per crash. A correction is a manual store write by the migrations/DBA identity, audited; the runtime identity does not refund. | lead | before M2 |
| D16 | Lowercase bare SQL (`drop table users` with no code marker) | Stays shown (4.9 rule G3); G4 is a display filter and the action gate decides what runs. Trigger to revisit: E0-6 corpus shows a model writing such lines in approval text. | lead | after E0-6 |
| D17 | Redaction base64 second pass and speculative patterns | Deferred; ship a pattern only if its canary leaks on old code (E0-4). Trigger: E0-4 shows a leaking base64 secret. | lead | after E0-4 |
| D18 | Anchor-writer identity split and outbox alert age | Deferred (design item). Trigger: first pilot config. Default today: S3 kind docstring states the identity needs `PutObject` + `GetObject` + list on one prefix only. | owner | before first pilot config |

## 4. Designs

### 4.1 Spend reserve, settle, release over the existing `add_spend` (resolves readiness B1 and M5 against zoom M-1)

**Verdict: `add_spend` can do it; no new table, no sweep, no TTL, no `expired_kept`.** Evidence:
- It returns the totals AFTER the add (F4), so "add the worst case, then compare" is one atomic step per row. Memory: both steps under `self._lock` (`memory.py:196-204`). Postgres: day and month upserts in one transaction (`postgres.py:416-431`); `ON CONFLICT DO UPDATE` takes the row lock, so two parallel reservers are ordered and the second sees the first's amount in its returned total.
- Negative amounts are legal: `usd NUMERIC NOT NULL`, no check, no foreign key (F4). So release and correction are the same call with a negative number, and a made-up key such as `eval:<agent>` is legal (fixes F5 without touching `registry.agents`).
- Crash safety falls out: a reservation is a counted amount. A crash before settle leaves it counted (fail closed, D15). No second table to go out of step.

What I looked for and found as limits (stated, not hidden): (a) check-after-add means a refused reservation is briefly visible in the totals, so a parallel small caller can be refused although it would have fitted a moment later; it can never be admitted wrongly (over-refusal only, bounded by one worst case per parallel caller). (b) If the process dies between the add and the undo of a REFUSED reservation, that amount stays counted (fail closed). (c) Postgres behaviour is **unverified**: E0-3 runs two connections.

New code, in `limits.py` (one place, no store change):

```
class SpendRefused(Exception): code in {"kill_switch","window_ended","daily_budget","monthly_budget","run_budget"}
@dataclass(frozen=True) class Reservation: key: str; day: date; usd: Decimal; run_id: str | None
class SpendMeter:                      # needs only store + config (CLI gate has no registry or audit)
    reserve(key, usd, daily, monthly, *, run_id=None, run_cap=None) -> Reservation   # raises SpendRefused
    settle(res, actual_usd)   # add_spend(key, res.day, actual - res.usd); add_cost(run_id, actual); never raises
    release(res)              # add_spend(key, res.day, -res.usd)
    keep(res)                 # cost unknown: spend stays booked; add_cost(run_id, res.usd)
```
`Limits` holds one `SpendMeter` (`Limits.meter`), built from the same store and `registry.config`.

`reserve` steps, in this order: (1) kill switch on -> `SpendRefused("kill_switch")`; (2) `spend_window_end` passed -> `window_ended` (D1); (3) `run_cap` given and `run cost so far + usd > run_cap` -> `run_budget` (D14; run cost read with `store.get_run`); (4) `add_spend(key, today, usd)` -> `(day_total, month_total)`; (5) `day_total > daily` -> undo with `add_spend(key, today, -usd)`, raise `daily_budget`; `month_total > monthly` -> undo, raise `monthly_budget`. Zero `usd` never refuses a zero cap (`0 > 0` is false), which keeps zero-price fake routes working. The comparison is `>` (would exceed), while the existing `blocked()` keeps `>=` (already at the cap); both are kept on purpose and tested side by side.

`settle`: delta = actual - reserved. If the actual is larger than the reservation (the estimator is an estimate), the extra is added anyway (the provider billed it) and a log line `spend_overrun` is written; it never raises after a provider billed. If a total comes back negative, `settle` and `release` add the missing amount back and log `spend_clamped`. `settle` writes `add_cost(run_id, actual)` exactly once (this fixes readiness B1's "settle must also update `store.add_cost`").

Worst-case size: new `llm/common.py:worst_case_usd(route, system, messages, documents)` = estimated input tokens (system + JSON of messages + `len(document bytes)`, 3 characters per token, as `estimate_tokens`) times the input price, plus `max_tokens` times the output price, per million. The existing `k1b/loop.py:115-122` copy stays unchanged (k1b is out of scope, 4.2); a note in the PR lists it as a promotion trigger when k1b joins the store ledger.

### 4.2 One per-caller wrapper, no ContextVar (resolves readiness M2 and zoom M-4)

Chosen: **a per-caller wrapped object**, not a ContextVar. Reasons from the code: (1) the `LLM` protocol stays unchanged (F7: test doubles use that exact signature); (2) a ContextVar does not cross into `k1b`'s daemon thread (`k1b/loop.py:94`), so it would need a second mechanism there; (3) a wrapper built at the call site is testable with `ScriptLLM` in `build_runtime` (F8) while an app-level wrapper would be bypassed by every runtime test.

New `hadavin_sdk/llm/metered.py`:
```
class MeteredLLM:     # same chat(...) signature as the LLM protocol
    __init__(inner, meter: SpendMeter, routes: Mapping[str, Route], key: str, daily: Decimal, monthly: Decimal,
             run_id: str | None = None, run_cap: Decimal | None = None)
    chat(...):  route = routes[route_name]; res = meter.reserve(key, worst_case_usd(route, ...), ...)
        try: reply = inner.chat(...)
        except ProviderExhausted: meter.keep(res); raise     # retried and gave up: ONE worst case, not x attempts
        except ProviderError:     meter.release(res); raise  # refused before any billing: zero
        except Exception:         meter.keep(res); raise     # unknown outcome: fail closed (money)
        meter.settle(res, reply.cost_usd); return reply     # includes a reply that later fails to parse
```
`KeyboardInterrupt` and other non-`Exception` exits leave the reservation counted (fail closed). Failed attempts before a later success are not booked (section 0 item 4). Pinned ledger totals (tests): success = actual cost; `ProviderError` = 0; `ProviderExhausted` = one worst case; any other exception = one worst case; a reply costing more than its reservation = actual cost with `spend_overrun` logged.

No kind exemption inside the wrapper (answers readiness M2: `GuardedLLM` has no kind argument, so it must not branch on kind). Fake replies are priced from the route like real ones (`0.00225`), so they are booked like any call.

**Who builds the wrapper:**
| Caller | Built by | Key | Caps |
|---|---|---|---|
| `agent_loop.py:425` | `Runtime`, per `handle`: `self.limits.meter.view(self.llm, key=agent.id, run_id=run.run_id, ...)` | `agent.id` | agent budget, `max_run_usd` |
| injection judge (`agent_loop._screen`) | `_screen` reserves itself (below); the judge keeps the raw llm | `agent.id` | agent budget |
| `evals.gate` + `judge.qualify` | the caller of `gate` (CLI, 4.6) passes a metered llm; `gate` is unchanged | `eval:<agent_id>` | `eval_budget_usd` |
| `extract()` | its caller passes a metered llm; `extract` is unchanged except masking (4.7) | the caller's key | the caller's caps |
| `k1b` | out of scope: own in-process `Budget` kept (daemon thread, no store). Fix: none now. Trigger: k1b runs against a live model with a client's money. | n/a | n/a |

**Judge call (`_screen`)**: `Runtime.__init__` reads the judge routes from `registry.config.backends.detector` (members with `kind == "llm_judge"`, as `evals.py:105` does). `_screen` reserves `worst_case_usd(judge_route, PROMPT, [], [text])` times 1.5 (margin for placeholders that are longer than the text they replace), runs `injection_check`, then `settle(res, verdict.cost_usd)`. If the verdict has `reason_code == "guard_unavailable"` and cost 0 (the detector raised), it calls `keep(res)`. A refusal at reserve ends the run as in 4.4.

**Removal sites (readiness M1, no double booking):** delete `self.limits.charge(agent_id, reply.cost_usd)` and `self.store.add_cost(run.run_id, reply.cost_usd)` at `agent_loop.py:440-441`; delete `self.limits.charge(...)` and `self.store.add_cost(...)` at `agent_loop.py:314-315` (the `if verdict.cost_usd:` block at `:313`). `settle` and `keep` are the only writers of `add_cost`. `Limits.charge` stays (tests and operator use it); a census test (below) keeps it from being called in a model path.

**Census test (cheap, replaces v3's repo-wide rule):** one test lists the five `.chat(` sites in F7 and fails when a sixth appears, so a new caller forces a decision about metering. The `k1b` entry names its own meter as the reason.

**Test changes:** `tests/test_s5_runtime.py:107-111` (spent 0.999, call costs 0.00225, reserve about 0.0155): the run now ends `NEEDS_PERSON`, `limits.daily_budget`, with `rt.llm.calls == []` (refused at reserve). Keep `tests/test_k5_tools.py:717-731` unchanged. Add a new test with a full `routes` override (`k5_cfg(config=...)` replaces the whole dict, shallow update) where the fake bills 0.30 on a reservation of 0.05, and one where the gate-DENIED path is still reached (reply bills 0.98 on a reply reserved at 0.05, so the post-call `blocked` crosses). Other tests that run with small budgets are found by the E0-1 full run at the M2 head; I did not read all of them.

### 4.3 Eval ledger and CLI wiring (resolves readiness M3)

- Config: `eval_budget_usd: Budget = Budget(daily=0, monthly=0)` on `Config` (reuse the `Budget` shape; same Decimal guards as D5). Default 0 = no live eval spend.
- CLI `gate` branch (`cli.py:146-153`): after `load_registry`, build as the audit branch does (`cli.py:179-184`): `secrets = make("secrets", ...)`, `platform_secrets.check(secrets, [b.store], set())`, `store = make("store", b.store, secrets)`. If `b.llm.kind == "fake"`: pass the raw llm (free; the exemption is made here, where the kind is known, not inside the wrapper). Otherwise: `llm = SpendMeter(store, cfg).view(llm, key=f"eval:{agent}", daily=cfg.eval_budget_usd.daily, monthly=cfg.eval_budget_usd.monthly)`. A `SpendRefused` becomes `ConfigError("eval spend refused: <code>; set eval_budget_usd (now 0)")`, exit 2.
- The metered `llm` object serves both the agent calls and the judge qualification (`evals.py:109`), so the judge's cost is inside the same cap.
- With `store.kind == "memory"` the eval ledger lives for one CLI process; the cap is then per run, not per day. Stated in the CLI help text and tested; not claimed as a daily cap.
- `Limits.blocked` is never called with `eval:*` ids.

### 4.4 Wall hit: card, no double card, what counts as a policy stop (resolves readiness M9)

Edits, by site:
- `_limits_stop` (`agent_loop.py:239-247`): for `limits.<code>` (daily, monthly, window_ended) call a new `_wall_stop(run, code)` instead of `_to(...)`. `kill_switch` (`:241-242`) is unchanged and stays card-less. The `run_budget` branch (`:245-247`) already posts through `_abstain` and is unchanged.
- `_wall_stop`: the first time in this process for `(agent_id, UTC day, code)` it calls `self._abstain(run, S.NEEDS_PERSON, f"limits.{code}", [])` (posts the card, audits it); later calls use `_to(...)` with an audit row and no card. Dedupe is an in-process set guarded by a lock (D13).
- A `SpendRefused` from the wrapper (`agent_loop.py:425` try block) is caught next to `ProviderError` and goes through the same `_wall_stop`. This is what ends `tests/test_s5_runtime.py:107-111` as `NEEDS_PERSON`.
- `agent_loop.py:669` (limits unreadable: "stop means stop, so no card") and `agent_loop.py:702` (gate decision `limits.*`: "no card, at any level") are **unchanged**. Reversing them would put a card on a path whose whole meaning is that nothing may be posted. A `limits.*` decision at the gate is a post-call crossing and is counted by the existing audit row.
- `_REASON_TEXT` (`:87`) gets plain sentences for `limits.daily_budget`, `limits.monthly_budget`, `limits.window_ended`.
- `caught_by` stays `None` for `limits.*` (K6 counts every non-null `caught_by` as a caught mistake, F13; a spend wall is not a caught mistake). `run_budget` stays in `GUARD_STOP_REASONS` (unchanged K6 meaning).
- New `POLICY_STOP_REASONS = frozenset({"limits.daily_budget","limits.monthly_budget","limits.window_ended","run_budget"})` next to `GUARD_STOP_REASONS` (`agent_loop.py:83`), used only by the false-abstain report (E0-9) to list these separately from "answerable abstained". No behaviour in the runtime reads it.
- Test D9: N blocked runs on one agent and day post exactly one card; kill switch posts none; a second code posts its own card.

### 4.5 D1 window end and D11 zero price

D1 as in section 3; `SpendMeter.reserve` step (2) and `Limits.blocked` (`window_ended`) both read it. Tests: demo or pilot with a non-fake kind and no date refused; prod with no value refused; prod with `none` accepted and audited; a past date blocks. D11: `registry._cross_check` refuses a route with zero input or output price unless `backends.llm.kind == "fake"`; move the logic from `k1b/replay.py:85-90`, keep the replay test; the judge route (`judge.py:3-4`) is checked too. E0-5 greps every fixture and demo config for a zero price first.

### 4.6 Audit verdict, trimmed (resolves readiness M6 against zoom M-6)

Add to `Verification` only: `signed: bool` (a public key was given and `signed_through > 0`) and `anchored: bool` (`anchors is not None` and no anchor problem), both set inside `verify_rows` (F11 shows it already holds both facts), plus `max_unsigned_tail: int` (set from `ChainAudit.checkpoint_every`, so **no new config key**; verify passes it through `verify_rows(..., max_unsigned_tail=)`, default 100). Property `tamper_evident = ok and signed and anchored and unsigned_tail <= max_unsigned_tail`.
Dropped (zoom M-6, readiness M6): `anchor_age_s` (no time stamp exists on `anchor.all()`, so it is not computable) and `outside_chain`. The CLI sentence says: "chain rows only; events still in the outbox are not covered". `cli.audit_verify` prints the threshold and what an unsigned tail lacks; exit codes stay 0 / 1 / 3. Tests on `verify_rows` with plain lists (no Postgres): healthy true; no key false; tail above threshold false; anchors off false; one broken link false. A healthy chain can be true because the inline checkpoint signs at `seq % checkpoint_every == 0` (`chain.py:203`) and `tick` checkpoints, so the tail stays at most `checkpoint_every` (specified, unverified).

### 4.7 `extract()` masking and restore contract (resolves readiness M4)

`extract()` masks the document before `llm.chat`: decode UTF-8 (strict); non-UTF-8 bytes (a PDF or image) return `DeadLetter(reason="extract_unmaskable")` with no model call; `runmap.redact_text(text, mapping)` with a fresh `mapping`; any `RedactionError` returns `DeadLetter(reason="extract_unredactable")`, also no call (fail closed). Recorded fake replies are keyed on `sha256(documents[0])`, so recordings are re-keyed in the same PR.
**Contract:** `Valid.data` holds exactly what the model returned, so a masked value stays a placeholder (`<EMAIL_1>`). `Valid` gains `mapping: dict[str,str]`. `extract` never restores. A caller that needs the original of an identifier kind calls `runmap.restore_value(valid.data, valid.mapping, kinds)` itself with a kinds allowlist. Default scope: extract is for fields that are not personal data (amounts, dates, codes). Tests: an email, a phone number and an IBAN in the document do not reach `FakeLLM` (`everything_sent`), the result holds placeholders, restore with the kind allowlist returns the original, and a non-UTF-8 document makes no call. The wrapper (4.2) is the caller's, so `extract` itself books nothing. `guard/producers.py` row 36 is reworded so it no longer implies the document is protected before this PR.

### 4.8 Key-file read: share the existing code (resolves zoom M-7, readiness N1)

Extract, do not copy: move the opened-file checks of `secrets_file._fetch` (`secrets_file.py:46-63`: `S_ISREG`, other-readable, group/other-writable, read) into `hadavin_sdk/fileguard.py:read_private_file(path, *, what, allow_group_read=True, max_bytes=65536) -> bytes`. It opens the path as given with `O_NOFOLLOW|O_NONBLOCK` and refuses the final symlink; the caller decides whether `confined()` runs first.
- `mounted_file._fetch` keeps `confined()` and calls it with `allow_group_read=True` (Kubernetes 0440 mounts keep working; existing secrets_file tests must pass unchanged, which E0-1 checks).
- `audit/signer.build_local` replaces `is_file()` + `read_bytes()` (`signer.py:104-108`) with `allow_group_read=False`.
- Import rules: `tests/test_lockin_guard.py:68-75` only constrains vendor and library imports; `fileguard` imports the standard library only, so no rule change is expected. I did not find a test that forbids `audit` importing a neutral module; E0-1 confirms by running the guard. (v3 named `test_k5_layers.py` wrongly; it is about secrets layers.)
- Test fixtures that write keys must create them 0600; their current mode is unchecked (E0-1 finds failures).

### 4.9 G4 rows: only what leaks on old code ships (resolves readiness B2, M8 and zoom M-3)

Rule for the whole PR: every row below is run in E0-6 on the UNCHANGED gate first; **only rows whose "withheld" example is shown today (a leak) go into the PR**, and each ships with its test proven failing on the old code. Rows that already withhold are dropped. Nothing was run, so each "today" verdict is hand-traced from `gate.py` and **specified, unverified**.

**G3 discriminator (the one concrete rule, readiness B2).** The pinned shown lines and the lines to withhold share one lexical shape (`tests/test_g4_parity.py:98,221-222`), so no word rule can separate them. The rule uses code markers instead: a new case-insensitive copy of the SQL verb-object grammar is withheld only if the same line also carries a marker:
- M1 the statement ends with `;`
- M2 the verb is inside an inline code span (a backtick before it on the line)
- M3 `set <name> =` (regex `\bset\s+[\w."]+\s*=`) or `where <name> <op>` with op in `= < > <> != in like`
- M4 `values (` or `into <name> (`
- M5 a client prompt or flag before it: `$ `, `-c "`, `-e "`, `sql>`, `mysql>`

Run mentally (**unverified**):
| Line | Marker | Result | Needed |
|---|---|---|---|
| `drop table users;` | M1 | withheld | withheld |
| `` `drop table users` `` | M2 | withheld | withheld |
| `delete from users where id = 1` | M3 | withheld | withheld |
| `update only t as a set x=1` | M3 (`set x=1`) | withheld | withheld |
| `insert into t values (1)` | M4 | withheld | withheld |
| `$ drop table users` | M5 | withheld | withheld |
| `drop table pressure` (pinned) | none | shown | shown |
| `we should delete from the queue only after a fix` (pinned) | none | shown | shown |
| `update its set of rules` (pinned) | `set of` has no `=` | shown | shown |
| `delete from the queue where possible` | `where possible` has no operator | shown | shown |
| `drop table users` bare | none | shown | withheld in v3; **now accepted as shown** (D16) |
| `we will drop table pressure; then rest` | M1 | withheld | false positive, counted by E0-6 against the 2% budget |

Upper-case SQL is unchanged (still withheld without a marker). Real upper-case gap, hand-traced: `UPDATE t AS a SET x=1` and `UPDATE ONLY t SET x=1` do not match `UPDATE\s+ID\s+SET` (`gate.py:664-666`); the `UPDATE` alternative becomes `UPDATE\s+(?:ONLY\s+)?ID(?:\s+(?:AS\s+)?\w+)?\s+SET\b`. Other SQL breadth from v3 (COPY, LOAD DATA, `nextval`, VACUUM, CALL, EXEC, DO, GRANT forms) moves to "candidates": each ships only if E0-6 shows a leak.

| Item | Function | Rule | Withheld | Shown | Today (hand-traced) |
|---|---|---|---|---|---|
| G1 | docstrings at `gate.py:4`, `gate.py:366-377`, `channel.py:20-21` | Wording only: "a closed list of programs plus SQL and shell shapes". | n/a | n/a | wording |
| G2a | new `_join_continuations(text)` before `_PROGRAM` | Join backslash+newline, `^`+newline, backtick+newline. Needed because `_TOKEN` stops at a newline (`gate.py:546`), so `toks` is empty and `_story` returns prose. | `kubectl \` newline `delete ns prod` | `we wrap lines with a backslash \` newline `like this` | leaks |
| G2b | `_story` (`gate.py:608-615`) | Skip leading redirection tokens (a bare `>`, `>>`, `2>`, `<`, `|`, or one glued to its target such as `>/dev/null`, `2>&1`) and the one target token after a bare operator, then judge the first remaining token. | `kubectl > /dev/null delete pod x` | `the aws Lambda runtime` (pinned; a capitalised word, unchanged path) | leaks (first token `>` matches the punctuation branch) |
| G2c | `_PROGRAM` name fold | Fold case, `.exe/.cmd/.ps1`, version suffix `kubectl-1.28`. | `KUBECTL.EXE delete ns prod` | `the tf module was reviewed` | candidate |
| G3 | `_WRITE_SHAPES` | marker rule above plus the `UPDATE` alias fix | table above | table above | leaks (lowercase and alias) |
| G4a | `rm` shape (`gate.py:674`) | Allow flags before the dangerous flag: `rm(?:\s+-[A-Za-z-]+)*\s+-[A-Za-z]*[rRf]`. `rm` is not in `_NAMES`, so the shape is the only guard. | `rm -v -rf /x` | `rm the file` (pinned) | leaks (the first flag `-v` has no r or f, so the shape fails) |
| G5a | `_AWS_READ_PREFIXES` use at `gate.py:597` | Add `_AWS_NOT_READ = {"get-secret-value","get-session-token","get-login-password","get-authorization-token","get-password-data"}`; `_readonly` returns False for those before the prefix test. These return secrets or tokens; a read verb does not make them harmless to display. | `aws secretsmanager get-secret-value --secret-id x` | `aws s3 ls` | leaks (generic `get-` prefix) |
| G5b | `_WRITE_VERBS` / `_OWN` | Add `checkout clean commit merge rebase pull`. | `git rebase -i HEAD~3` | `the docker image was rebuilt overnight` (pinned) | candidate |
| cand | `dd of=`, `mkfs`, `chmod -R`, `kill`, `shutdown`, `crontab -r`, `sed -i`, `rsync --delete`, redirect to a path, `tee`, `curl -X DELETE`, download-and-run variants, PowerShell verbs and aliases, quoted-command prose, read verb with write flag, capital-first positional | each ships only if E0-6 shows a leak and a shown-example does not break | see v3 section 5 | `we should kill the idea` | not traced |

Pinned shown lines (all must stay shown; E0-6 runs them): `rm the file`, `drop table pressure`, `we should delete from the queue only after a fix`, `a 'kubectl rollout restart' replaced the pods`, `the docker image was rebuilt overnight`, `update its set of rules`, `the aws Lambda runtime`. G4 stays a hybrid (closed program list plus shapes); the allowlist alternative stays rejected for the reasons in v3 section 5 (prose is unbounded, 2% false-positive budget on at least 200 sentences) with the same trigger: E0-6 finds a bypass class the shapes cannot cover, or measures false positives under 2% with room to spare. `_join_continuations` output is the text with the joined pair replaced by one space; `_clean_line` normalisation runs before `_OWN` lookup (words lowered by `_subcommands` already, `gate.py:573-589`).

### 4.10 Redaction (resolves zoom M-8, readiness N6; PR-2 first and alone)

PR-2 (4.7) ships first and alone. The pattern PR (R) ships only patterns whose canary LEAKS on old code (E0-4), each with a canary test (fake values built from parts; the only literal allowed is `AKIAIOSFODNN7EXAMPLE`) and a near-miss test, named per pattern:
- `PHONE` (`redact.py` ~470): `( ) . /` separators. Withheld `(415) 555-0132`; near-miss a date `2026-11-16`.
- `IBAN` (~247): spaced 4-character groups and lower case, normalised first.
- `CREDITCARD` (~451): 15-digit 4-6-5 grouping, 17-19 digits, dot separator. `4111` also appears in `tests/warden_port/privacy_corpus.py:42` and `tests/test_redaction.py:309,356`.
- `EMAIL` (~236): non-ASCII local part, quoted local part, soft-break.
- `CREDPAIR` (~513, modelled on the HAR cookie pair): `{"name": "<credential key>", "value": "..."}` either order, case-insensitive; share the credential-key test with `k1b/redaction.py` `_pair`.
- URL credentials (signed-URL signature parameters, reset-link path tokens) and bare `passphrase`, `cvv`, `pin`, `dob` keys.
Deferred, trigger in D17: the base64 second pass and any pattern with no leaking canary. The input tripwire after masking depends on E0-4 (redacting masked text must be a fixed point).

### 4.11 Housekeeping track (non-gating)

- **H-0 stage rename (R449):** `field_validator("environment", mode="before")` on `Config` raises `ValueError("environment 'dev' was renamed to 'demo'; change it in your config")`; `load_config` returns it as `ConfigError` (F14). Value or logic sites: `config.py:317`, `config.py:366-367`, `config.py:19`, `backends/table.py:594` (`DEV_ONLY` to `DEMO_ONLY`), `tests/test_lockin_guard.py:18,430`, `tests/fixtures/config/config.yaml:2`, `tests/test_p4_secrets.py:106`, `tests/warden_port/test_audit_chain.py:568`, `tests/test_p1b_backends.py:~89-91`. Wording sites: `secrets_env.py:1`, `audit/signer.py:64,98`, `table.py:126,214,254,591`, `config.py:346`, `defaults.py:100`, `registry.py:50`, `tools.py:361`, `agent_loop.py:179,553,572`, `actions/contract.py:34`, `store/postgres.py:75,90`. Leave `guard/redact.py:1162` (a word list). Tests assert the message by substring only (the wrapper text comes from `str(exc)`). CHANGELOG upgrade step. E0-8 greps demos for `environment: dev`. Round cap 2. It protects nothing today (zoom M-2), so it is not gating.
- **H-1 audit retention floor + S3 probe:** a floor on the existing `retain_days` of 7 for pilot and prod, checked where each anchor builds (`anchor_s3.py:84-96`, `anchor_gcs.py:69`, `anchor_azure.py:80-95`; the three settings classes were not read). The Object Lock probe is a new `probed(client, settings)` in `anchor_s3.py` (the S3 kind module only) modelled on the GCS `probed` (`anchor_gcs.py:69-88`), calling the storage API's object-lock-configuration read. D18 items deferred.
- **H-2 evidence docs (merged E1 and E3):** wording and docs only, round cap 2, not a PR of its own if H-1 or G1 is open.

## 5. Dependency and least-privilege check (zoom N-1, N-2)

- No new vendor dependency. The Object Lock probe stays in the S3 kind module. The invoice reconcile has no code and no named alternative process (section 0 item 4).
- Identities: the runtime identity already writes spend rows through `add_spend`; the new release and settle use the same call with a negative delta, so **no new right is added**, but the runtime identity can in principle lower a total. Guards: only `SpendMeter` calls it with a negative number (census test above lists `add_spend` callers), totals are clamped at 0 with `spend_clamped` logged, and agents hold no store credentials. Refunding an orphan reservation is the migrations/DBA identity's audited manual write, never the runtime (D15). Negative test: a call through the runtime role object cannot reach a refund path (there is none to call).
- Eval spend default 0 (nothing live without the owner's numbers).

## 6. PR series, two tracks, one status column

Cap tag: U = uncapped (security, money, redaction, audit, secret), C = capped at 2 rounds. Every status reads "specified, unverified" until its E0 evidence and the lead's EGM review exist; the lead changes the cell.

**Gating track (safety; the live window waits for these):**
| Order | PR | Content | Cap | Depends on | Status |
|---|---|---|---|---|---|
| 1 | PR-2 | `extract()` masks the document, restore contract, re-keyed recordings (4.7) | U | none | specified, unverified |
| 2 | M1 | D1 window end, D5 Decimal guards, D11 zero-price refusal, `eval_budget_usd` field (4.3, 4.5) | U | none | specified, unverified |
| 3 | M2 | `SpendMeter`, `MeteredLLM`, loop and judge wiring, removal sites, wall card, policy-stop set, census test (4.1, 4.2, 4.4) | U | M1 | specified, unverified |
| 4 | R | Redaction patterns that leak on old code (4.10) | U | E0-4 | specified, unverified |
| 5 | S1 | `fileguard` shared with `secrets_file`, signer key check (4.8) | U | none | specified, unverified |
| 6 | M3 | Eval ledger and CLI gate wiring (4.3) | U | M2 | specified, unverified |
| 7 | A1 | Audit verdict (4.6) | U | none | specified, unverified |
| 8 | G | G1 wording + the G4 rows that leak on old code (4.9) | U for rows, C for G1 | E0-6 | specified, unverified |

Order 1, 2, 4, 5, 7 can run in parallel; M2 waits for M1; M3 for M2. PR count: 8 gating (v3 had 14 plus 8 evidence items).

**Housekeeping track (not gating):**
| PR | Content | Cap | Status |
|---|---|---|---|
| H-0 | Stage rename (4.11) | C | specified, unverified |
| H-1 | Retention floor, S3 probe (4.11) | U (audit) | specified, unverified |
| H-2 | Evidence docs | C | specified, unverified |

Deferred with trigger: calls cap and self-hosted flag (D11), local billing day (D12), anchor-writer split and outbox alert (D18), base64 and speculative patterns (D17), G4 candidate rows (4.9), store-backed wall dedupe (D13), k1b on the store ledger (4.2).

## 7. Evidence batch E0 (an EVIDENCE RUNNER runs these; the runner never judges)

- E0-1 full `pytest`, `ruff check`, `ruff format --check`, `bandit -ll` at each final head, one run each; includes the lockin guard and `secrets_file` tests.
- E0-2 mutation sample (changed mutants plus 60-mutant sample), full run once, alone.
- E0-3 `SpendMeter` contract tests on both stores (Postgres via `HADAVIN_TEST_PG_DSN`): 8 threads reserve against one cap and the sum of admitted amounts never exceeds it; refuse path leaves totals unchanged; settle, release, keep totals as in 4.2; two connections for Postgres.
- E0-4 redaction: masked text is a fixed point; one canary per pattern on OLD code (leak = ships); fuzz `redact_text`.
- E0-5 reserve sizing over every fixture and demo config route and agent: print `worst_case_usd` for an empty call and a full-context call; flag a reserve above 50% of the daily cap or the run cap; grep every route for a zero price (D11); list tests that break under the new reserve.
- E0-6 every row of 4.9, every pinned shown line and the recorded corpus through `withhold_commands` and `channel.clean` on old and new code; false-positive rate on at least 200 prose sentences (budget 2%); new tests run on old code to prove they fail.
- E0-7 `Money`/`Budget`/`Route` with NaN, infinity, negative; a documents-recording fake across `extract`, `evals`, `guard/judge`.
- E0-8 grep stage sites and `environment: dev` in demos and configs.
- E0-9 false-abstain split on the golden set: answerable abstained / answerable, policy stops (4.4) listed separately; never "N/M correct" without the split.

## 8. Item homes

| Item | Home |
|---|---|
| Money guard, reserve, wall card | M1, M2, M3 |
| Redaction | PR-2, R |
| Approval text | G |
| Audit verdict | A1; retention H-1 |
| Key file read | S1 |
| Stage rename | H-0 |
| Provider invoice reconcile (third party) | owner/lead, monthly |

## 9. What I did NOT check (repeat so it is not lost)

Everything in section 0 items 1 and 3; whether any test other than `test_s5_runtime.py:107-111` breaks under the reserve; Postgres concurrency of `add_spend` under two connections; the exact regexes of G2a, G2b, G3, G4a (written as rules, not compiled); fence handling for marker M2; anchor settings class names. Nothing here is "verified"; the lead runs the EGM review on this hand-off and on each PR.

# Ready-to-apply core patches, v3 (C5 v3, 2026-11-16)  **[SUPERSEDED. The kept scope is ../v5/ (decision 4, Q18). Kept for its raw files and C7b evidence (v5 cites them). Its C-01 holds cut extras and its A-01 is deferred. Do not apply. See SUPERSEDED-NOTE.md]**

## SCOPE CUT by the lead, 10:02Z (read before anything else)
- **`A-01.patch` is DEFERRED.** Finished and tested as described below, but not to be applied or extended now.
- **C-01 extras are CUT** (do not apply): `price_is_zero_by_design`, `keyless_loopback`, `max_route_tokens`, the NaN handling, and
  the shared `price_problems` rule. Only the minimal "price above 0 and `max_tokens` ceiling" check remains of interest, and only
  if the take's model program loads `Route` config (unverified, not in the video path). `C-01.patch` here still contains the
  extras; a minimal version was NOT cut (no time, and the lead said no new work). The blocker fix (`refused +=`) is the part
  that matters if any of C-01 is used.
- **`G5-wording.patch` stays** (text only).

v3 replaces v2. It fixes every finding in `review/design-r2.md` and `review/codebase-r2.md` (and the open items of round 1).
Three patches: `C-01.patch` (price and token limits), `A-01.patch` (audit events waiting in the outbox), `G5-wording.patch`
(text only). `DEAD-MAN-CHECK.md` is a note, not code. Nothing was committed or pushed; the real repository only got this folder.

## What failed, what is uncertain, what was NOT checked (read first)
- **v2 had a real bug (found by the round 2 reviewer, confirmed here):** in `Config._cross_checks` the price and token
  refusals were thrown away in `pilot` and `prod`, because the next lines assigned the list again (`refused = [...]`
  instead of `refused += [...]`). A zero price or `max_tokens` of 2 000 000 loaded in pilot and prod. All 42 v2 tests used
  `environment: dev`, so nothing caught it. I ran the new pilot and prod tests against the real v2 code: 9 fail, the 2
  control tests pass (`raw/v2-fails-pilot-prod-tests.txt`). Also a v3 mutant that puts the `=` back is killed (C01-14).
- **Not run, and why:** the Postgres tests (455 tests are skipped in every full run, no Postgres here); the dead-man query;
  a negative test that the audit database identity cannot UPDATE or DELETE `audit_entries` (needs Postgres; the existing
  Postgres tests were not run); the repo guard tests on the REAL repository (they were run on a git-initialised copy with
  `handover/` removed, see below); any live model, cloud or network call; two real processes sharing the spill folder (the
  tests simulate the second process with a second `ChainAudit` object on the same database and folder).
- **Pristine suite, now really run** (v2 only claimed the two guard tests): `git archive b4cce5b`, `git init`, one commit,
  `handover/` removed: **9391 passed, 455 skipped, 0 failed, 238 s** (`raw/pristine-full-suite.txt`). The two failures v2 saw
  came from the scratch folder (no git repository for the licence test; vendor-name hits inside `handover/` notes), not from the
  patches. Whether the real repository passes those two guard tests today was NOT run here (the hygiene commit `7e3e7aa1`
  suggests the head fixed the notes).
- **Mutation lane is hand-made, not exhaustive:** 54 mutants plus re-runs (list in `raw/mutation-v3.txt`). Two survived the first run
  (C01-07, SP-08); each got a killing test and was re-run and killed. Failing test NAMES are recorded, not log lines.
- **Dead code decision:** the v2 `Route` validator for NaN and Infinity was unreachable (see finding 5). It is deleted, so
  there is no longer an equivalent surviving mutant.
- **The durable spill folder (finding 6) is built for the `chain` kind only.** `local_dir` is the laptop kind; its only
  fallback after the outbox folder fails is still memory, because a second folder on the same disk fails with the first.
  The directory fsync after the rename is best effort and has no test (it cannot be observed from a test); the file write
  itself is flushed and fsynced.
- Still open and NOT touched (unchanged from v2, owner or studio head): X-02 reserve-then-settle, B-01 per-process
  `disabled_sources`, A-24 `retain_days` default, `dev` vs `demo` stage name, A-07 `_unanchored` memory only, A-10 dead code,
  a per-call spend cap (`max_tokens x output price`), a shared "finite and above 0" type for every money field.

## Findings of round 2 and what v3 did (one row each)
| # | Finding (reviewer) | v3 fix | Evidence |
|---|---|---|---|
| 1 | BLOCKER: pilot and prod dropped route refusals (`refused =`) | `refused +=`; route refusals first, then environment refusals, one error | 9 new tests fail on v2 (`raw/v2-fails-pilot-prod-tests.txt`); mutant C01-14 and C01-15 killed |
| 2 | `replay._refuse_zero_price` had its own zero rule | one function `config.price_problems(route, keyless_loopback=...)` used by config load AND replay | replay tests both ways (flagged local route replays, unflagged zero route refused, flag on a non-local model refused, replay kind differing from configured kind is not local, NaN copy refused); mutants C01-16 to C01-19 killed |
| 3 | `backlog()` ignored `outbox/corrupt/` | `local_dir` backlog counts waiting files, memory AND files in `outbox/corrupt/`; `last_corrupt` = files now in `corrupt/`; both kinds now behave the same (red until a person acts) | tests: red on the first and the second tick, green after removal, both kinds agree; mutants A01-12, A01-13, A01-21 killed |
| 4 | `K1bAudit` had no reconcile/backlog (false green) | `K1bAudit` passes `reconcile`, `backlog`, `last_corrupt` to its sink; `backlog` is now on the `AuditSink` Protocol; `audit_drain` FAILS when a kind cannot report a backlog | tests for wrapper over chain and local_dir, over a sink without backlog, object with no backlog; mutants K1B-01 to K1B-03, A01-22 killed |
| 5 | NaN and Infinity: run it; `match=`; unreachable validator | probe run on the v2 tree and on pristine (below); `match="finite number"` added; validator deleted; total predicate kept as defence in depth because `model_copy` skips validation (replay uses it) | `raw/nan-probe-*.txt`; mutant C01-08 killed |
| 6 | Memory-only audit gap | option (a) built, opt-in (below); the three options and a recommendation are in "Owner decisions" | 8 spill tests; mutants SP-01 to SP-09 killed |
| 7 | Wording and claims | refusal text names the flag; scheme wording fixed; pristine suite run; mutant count fixed; A-01 test count fixed; missing raw file produced; blank line in `defaults.py` restored; G2/G5 claims checked | see sections below |
| 8 | Mutation: ordering, backlog exception, `last_corrupt` reset, `>= 0`, except order, NaN predicate | all added (A01-15 to A01-20, C01-08) with test names | `raw/mutation-v3.txt` |
| 9 | Full suite, ruff, bandit, dry-run, sha256 | below | `raw/` |

### Finding 5 in detail: what pydantic really does (run, not guessed)
Command (both trees, `python -I`, `raw/nan-probe-v2-tree.txt` and `raw/nan-probe-pristine.txt`): `Route(model_id="m",
input_usd_per_mtok=V, output_usd_per_mtok="1", max_tokens=1)`. With pydantic 2.14.1 on Python 3.13.18, for V in `NaN`, `sNaN`,
`Infinity`, `-Infinity`: every one raises `ValidationError` ("Input should be a finite number [type=finite_number]"); `"1"` is
accepted. The pristine tree behaves the same, so this is the field type, not a v2 patch. So the round 1 claim "NaN raises
`decimal.InvalidOperation` and crashes `load_config`" did not hold here, and "Infinity passes" did not hold either. The
v2 validator ran after pydantic's own check and could never fire, so it is deleted. A test pins pydantic's behaviour
(`test_pydantic_itself_refuses...`): if an upgrade ever changes it, that test fails. `_price_ok` stays total (never raises
for NaN, Infinity, negative zero) because a `Route` made by `model_copy` skips validation; `replay` tests do exactly that.

## Apply
From a checkout at `b4cce5b` (or later with these files unchanged), repo root:
`patch -p1 < handover/core-hardening/patches-ready/v3/<name>.patch` (or `git apply`). Any order works: `table.py` is split
into two separate hunks (C-01 adds the `keyless_loopback` property, A-01 adds the `spill_dir` field). `patch --dry-run -p1`
was run on fresh extracts, alone and in order (`raw/dry-run.txt`). Nothing from the "before an executor is added" gate is
included. Files changed: 17 (list: the three `Files` cells below).

| Patch | Files | RUNG (tool ladder) |
|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `backends/table.py`, `k1b/replay.py`, `tests/test_c01_route_limits.py`, `tests/test_k1b_replay.py` | Rung 1 (existing `Route`/`Config` validation and the existing replay check) extended, one shared rule. Rung 7 holds for the rule itself (a safety rule: no spend limit may be bypassed by a price of 0). No lower rung does it: no ready-made tool checks our config. |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `audit/spill.py` (new), `audit/protocol.py`, `backends/table.py`, `k1b/audit_sink.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | Rung 1: `reconcile()` was already on the audit Protocol and nothing called it; one tick step plus counters. Rung 7 for "fail the step" and for the spill file (audit path). Rungs 3 to 6 do not apply: the audit store has no connector, and a message queue or a managed log would add a dependency for a few files. |
| `G5-wording.patch` | `approvals/gate.py`, `guard/redact.py`, `tests/warden_port/test_gate.py` | Text only, no behaviour. |
| `DEAD-MAN-CHECK.md` | none | Rung 1 for data, rung 2/3 for the reader. Not built. |

## Owner decisions needed
1. **Memory-only audit gap (A-01 round 2 finding M3): which option?** The gap: the serving process writes an outcome event
   (after an action) first to the audit chain, then to the outbox table; if the database is down both fail. Before v3 the
   event then lived only in that process's memory and was lost on exit, with one error line as the only trace. Options:
   - **(a) A second durable place on the machine (a spill folder).** BUILT in v3 as opt-in: set `backends.audit.spill_dir` (kind
     `chain`) to a folder. One file per event, written to a temp name, flushed, renamed; the tick step drains it into the chain
     and deletes each file only after the event is in the chain. A damaged file goes to `<spill_dir>/corrupt/` and keeps the
     step red until a person deals with it. Cost: a folder on a volume the tick can also read (same machine or shared volume);
     with no folder configured nothing changes. It does NOT cover the case where the folder cannot be written either (then
     memory only, one error line, as before).
   - **(b) Fail closed.** An outcome that cannot be stored stops the run or all new actions until audit is back. Safe, but the
     action has already happened when an outcome is written, so this stops FUTURE actions, not this one; it needs a design
     change (a circuit breaker in the runtime) and a decision on what the person sees. Not built.
   - **(c) Written acceptance** by the client that after a database AND disk failure at the same moment an outcome event can be
     lost, with the error line as the trace and an alert on it. Costs nothing, loses events.
   - **My recommendation (not a decision):** (a) switched on in every pilot and prod config, plus (c) written down for the small
     remaining case, plus an alert on the log line `held in memory only`; build (b) only if a client needs "no action without a
     stored outcome". Making `spill_dir` REQUIRED outside dev would be a new refusal rule; I did not add it without your yes.
   Until you choose, nobody should write "an audit event cannot be lost": it is not true in any option.
2. **Local models priced 0 (C-01).** Built as option A, unchanged from v2: per route `price_is_zero_by_design: true`, accepted only
   when the configured llm kind is keyless loopback. "Keyless loopback" means: the model's address is this machine
   (`127.0.0.1`, `localhost` or `::1`) AND no key name is set. **The scheme does not matter**: `https://localhost/...` with no
   key counts (a test pins it; v2 wrongly said "plain http"). Alternative B (exempt every keyless loopback model from the price
   check) is a two-line change in `price_problems`. No per-run token cap exists when the cost is 0 (the spend limits cannot
   fire for such a route); `max_tokens` and the ceiling are then the only brakes. Stated, not fixed: it needs a new limit.
3. **The `max_tokens` ceiling (200 000)** is a typo guard I chose, not a provider limit; no provider page was looked up (no live
   lookup here). It is `Config.max_route_tokens` (default `defaults.MAX_ROUTE_TOKENS`, reason written there).
   The studio head confirms or gives a dated figure.
4. **Who reads the dead-man check, and a second alert channel** (`DEAD-MAN-CHECK.md`).
5. Still open from earlier reviews: see the list at the top.

## C-01: price check and token ceiling (what the code does)
- One rule, `config.price_problems(route, keyless_loopback=...)`, used by `Config._cross_checks` (via `_route_refusals`) and by
  `k1b.replay._refuse_zero_price`. For a live route (any `backends.llm.kind` except `fake`) both prices must be finite and
  above 0. Exactly 0 is allowed only with `price_is_zero_by_design: true` on a keyless loopback model. The flag on any other
  model is refused, and the zero price is then ALSO reported (the flag cannot excuse it): two messages, one round.
- Refusal text: "a live model needs a price above 0 (a zero price would stop every cost limit; a local keyless model may set
  price_is_zero_by_design: true)". It names the flag.
- Replay: the kind passed to replay counts as local only if it equals the configured kind and that kind is keyless loopback.
- `max_tokens`: `Config.max_route_tokens` (`gt=0`) is checked in the same list. Literal boundary tests: 200 000 loads,
  200 001 and 2 000 000 are refused, 1 loads, 0 and -1 are refused, a lowered ceiling works, in dev, pilot and prod.
- A tiny positive price is accepted on purpose (any floor would be an invented number); a test pins it.
- `price_is_zero_by_design` defaults to false and `config_hash` dumps with `exclude_defaults`, so existing agents are not
  un-qualified (tested).

## A-01: the tick writes waiting audit events into the trail and fails when it cannot
- New last tick step `audit_drain`. It asks the audit kind for `backlog()` first (a kind without it FAILS the step: unknown is
  never shown as zero), calls `reconcile()` if the kind has one, logs `audit_drain drained=<n> remaining=<n> corrupt=<n>`,
  and RAISES when `remaining > 0`. So `tick_state.last_ok_at` stops advancing, `last_error` says how many events wait, and the
  tick exits 1. Empty = green.
- `backlog()` counts everything that still needs action: events in memory, rows in the outbox table (damaged ones included), and
  for the file kinds the waiting files AND the files moved aside as damaged. Both kinds now answer the same way for the same
  fault (tested side by side).
- `reconcile()` in the chain kind drains in event id order (`ORDER BY event_id`, tested), skips a damaged row per row (logs
  error type and event id only, never the body), and never lets one bad row block the rows behind it (audit A-22).
  `last_corrupt` is the number of damaged items now present, per pass (a test shows it does not grow on every tick).
- `K1bAudit` passes `reconcile`, `backlog` and `last_corrupt` to the sink it wraps.
- A failing `DELETE` of an outbox row after its event reached the chain is NOT caught any more (v2 caught it with a blind
  `except`): the step fails loudly, nothing is lost, the next tick absorbs the duplicate (tested). This keeps the patch free of
  new suppressions.
- Both kinds log a WARNING (error type and event id only) when an outcome goes to the outbox; the chain kind logs an ERROR
  naming where the event ended up (spill folder or memory only).

### What a person does when the step stays red because of a damaged item
The step cannot repair a damaged event; it can only refuse to turn green while one exists. A person:
1. Finds the item: the step message says `corrupt N`. For `local_dir`: files in `<audit dir>/outbox/corrupt/`. For the chain kind:
   rows in `audit_outbox` whose body cannot be read (the log names the event id), and files in `<spill_dir>/corrupt/`.
2. Looks at it (a file is plain JSON; never paste its content into a ticket if it may hold personal data) and decides: repair
   it into a valid event and put it back (a file: move it to `outbox/` or the spill folder; a row: fix the body), or record in
   the incident log why this event is lost and then delete the file or row.
3. The next tick turns green by itself when nothing is left. Removing the item is the only way to turn it green; that is the
   point, so a lost event is always a decision of a person.
Limits that stay: the `local_dir` outbox and the spill folder drain only if the tick sees the same folder as the serving process;
`reconcile` is unbounded (no LIMIT) and replayed events keep their original principal and time; `ChainAudit._unanchored` is
memory only (A-07).
- Privilege: no new database right. The runtime role already has SELECT, INSERT, DELETE on `audit_outbox` (`store/migrate.py`
  `GRANTS`); `backlog()` adds a `COUNT(*)` on the same table. The spill folder needs the runtime user to write and the tick user to
  read and delete there, nothing else; the folder is configured, not hardcoded.

## G5 wording (text and comments only)
- `approvals/gate.py` header and `guard/redact.py` docstring say what is true: no separate check that blocks a message after
  redaction exists here; G5 and G2 are not built (I grepped `src` for `def hedge`, `def enforce`, `def leaked_kinds`: none);
  what exists is one final redaction of approval and channel text in `approvals/channel.py` (`clean`), same patterns, not
  independent. The remaining lines in `gate.py` that describe G5, G2 and "every way out" as fact (the original design notes) now
  carry "original design, NOT built here" on the line itself, not only in the header. The history sentence about
  `AKIA<ZWSP>` passing G5 (eighth review) is left as it is: it describes the original project.
- `tests/warden_port/test_gate.py` docstring says the G5 leak block is not ported.

## Which new C-01 tests fail on old code, and which only guard (run on `b4cce5b`, `raw/c01-tests-on-pristine.txt`)
The coordinator's check agrees with mine: on `b4cce5b` with pydantic 2.14.1 a NaN or Infinity price is already refused by
`Route`. Running the new C-01 test file against the old tree (new names stubbed): **32 fail, 29 pass**. The 29 that pass are
GUARDS ONLY, they do not prove a fix: all 16 NaN/Infinity cases, the 4 pydantic-behaviour pins, the tiny-price test, the
priced-route-still-loads test, boundary tests that old code already satisfies (ceiling field, `max_tokens` 1/0/-1, fake model
may cost nothing, route frozen), and the 2 pilot/prod control tests. The failing ones are the zero or negative price rules,
the `max_tokens` ceiling, the flag, and the pilot/prod tests (those also fail on the real v2 code, 9 of 9). Old code accepts
price 0, -0, -1 and 1E-12. A-22 (a damaged outbox row blocks the rows behind it) is confirmed on old code by the coordinator.

## What I ran (final tree = `b4cce5b` + the three v3 patches, git-initialised scratch copy; raw output in `raw/`)
| Command | Result |
|---|---|
| pristine `b4cce5b` extract, git init, `handover/` removed: `uv run --all-extras --group test pytest tests -p no:cacheprovider -q` | 9391 passed, 455 skipped, 0 failed, 238 s (`raw/pristine-full-suite.txt`) |
| FINAL tree, same command, one run | **9491 passed, 455 skipped, 0 failed, 235 s** (an earlier run of the same tree found 1 failure, a hardcoded-host-literal guard hit on a docstring I wrote; fixed, and that run was repeated in full) (`raw/full-suite.txt`) |
| `ruff check src tests`, `ruff format --check src tests` | clean, `ruff check` and `ruff format --check` rc 0 (version line in the log) (`raw/ruff.log`) |
| `bandit -ll -q -r src` (via `uvx`; not in the test group) | rc 0, no findings (bandit 1.9.4) (`raw/bandit.log`) |
| new test files collected | `test_c01_route_limits.py`: 61 test cases from 26 functions (parametrized); `test_a01_audit_reconcile.py`: 34; 5 new replay tests in `test_k1b_replay.py`; 2 added lines in `test_p7_tick.py` |
| hand-made mutation lane, 54 mutants on a copy of the final tree | `raw/mutation-v3.txt`; all killed after two survivors got killing tests (C01-07, SP-08) |
| new pilot/prod tests against the real v2 code | 9 fail, 2 control pass (`raw/v2-fails-pilot-prod-tests.txt`) |
| `patch --dry-run -p1` and real apply on fresh extracts of `b4cce5b`, alone and in order | all 9 steps rc 0; applied tree equals the work tree for `src` and `tests` (only a `.orig` file from a 5-line offset on `table.py`) (`raw/dry-run.txt`) |

No suppressions were added: no new `noqa` or `nosec`, no skipped or weakened test. Four `# noqa: BLE001` comments that already
existed at `b4cce5b` sit on lines that now read `except Exception as exc:` (the marker was there before; one v2 marker was removed).
Old-code evidence for the rest: a test file that imports a new name cannot even load on `b4cce5b`, so for A-01 and the spill
folder the proof that the tests bite is the mutation lane, not a run on old code.

## Files in `patches-ready/v3/`
`C-01.patch`, `A-01.patch`, `G5-wording.patch`, `DEAD-MAN-CHECK.md`, `README.md`, `checkpoint.md`, `raw/`. SHA256 of the three
patches: see `SHA256SUMS.txt` (fddf8a15..., 092d673a..., 0815212a...).

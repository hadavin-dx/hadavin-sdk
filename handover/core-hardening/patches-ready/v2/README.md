# Ready-to-apply core patches, v2 (C5 v2, 2026-11-16)

## What failed, what is uncertain, what was NOT checked (read first)
- Full suite on the scratch copy (`b4cce5b` plus all three patches): 2 tests FAIL, both also fail on a pristine `b4cce5b`
  extract, so they are not caused by these patches: `tests/test_repo_rules.py::test_licences_are_proprietary` (needs a git
  repo; the scratch folder has none) and `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`
  (reports the text 'Port.io' in two `handover/` notes and one non-UTF-8 file already in the repo; this needs the studio
  head's attention: it will fail the repo guard on the real repo too, unless those files are handled). Raw: `raw/`.
- The G5 guard tests (ORDER 009 files) were not run separately and not read again; they are part of the full run above only.
- Postgres tests were skipped (455 skipped in the full run; no Postgres here). The dead-man query was never run.
- Mutation lane v2 is hand-made and not exhaustive (29 mutants). 3 survived; 2 are equivalent or double-covered (below).
- "Fails on old code": A-01 tests 17 of 19 fail on `b4cce5b`; C-01 20 of 42 fail on old code, but the C-01 file imports a
  new helper so it cannot even load on old code: I ran a copy with that import and one test removed. Weak evidence for C-01.
- The design review blockers B1 (A-01) and B2 (C-01) are addressed in code, but the memory-only gap below is a limit I could
  not remove from a one-shot tick.

## Apply
From a checkout at `b4cce5b` or later with unchanged files, repo root: `patch -p1 < handover/core-hardening/patches-ready/v2/<name>.patch`
(or `git apply`). `patch --dry-run -p1` was run on fresh extracts, alone and in order C-01, A-01, G5-wording
(`raw/dry-run.txt`). The three patches touch different files, so any order works. Nothing from the "before an executor is
added" gate is included. v2 replaces the v1 patches in `patches-ready/`.

| Patch | Files | RUNG (tool ladder) |
|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `backends/table.py`, `tests/test_c01_route_limits.py` | Rung 1 (existing `Route`/`Config` validator) extended; rung 7 holds for this part only: a safety rule (no spend limit may be bypassed by a price of 0). No lower rung does it: no tool checks our config. |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | Rung 1: `reconcile()` is already on the audit Protocol and nothing called it; one tick step plus counters. Rung 7 for the "fail the step" decision (audit path). Rungs 3 to 6 do not apply: an in-process audit store has no connector. |
| `G5-wording.patch` | `approvals/gate.py`, `guard/redact.py`, `tests/warden_port/test_gate.py` | Text only, no behaviour. |
| `DEAD-MAN-CHECK.md` | none | Rung 1 for data, rung 2/3 for the reader (see the file). Not built. |

## Owner decisions needed (kept from v1, extended)
1. **Local models priced 0 (C-01 B2).** v2 builds option A: an explicit per-route `price_is_zero_by_design: true`, accepted
   only when `backends.llm` is `openai_compat` with plain http to this machine and no key. Alternative B: exempt every keyless
   loopback model from the price check (simpler, but a typo of `0` on a local route would then silently disable cost
   limits). The studio head picks; switching to B is a two-line change in `_route_refusals`.
2. **The `max_tokens` ceiling number (200_000).** A typo guard I chose, not a provider limit; no provider page was looked up
   (no live lookup here). It is now a validated config field `max_route_tokens` (default in `defaults.py`, with the reason
   written there), so a client can lower it. The studio head confirms the default or gives a dated figure.
3. **Who reads the dead-man check, and which second alert channel** (see `DEAD-MAN-CHECK.md`).
4. **K1bAudit has no `reconcile`** (`k1b/audit_sink.py`). The step now logs one line for it and passes. Whether the K1b
   report-only path needs a drain is a studio-head decision; I did not invent one.
5. **Per-call spend cap.** The reviews asked for `max_tokens * output price <= per-call cap`. The code has no per-call cap
   to reuse (only `max_run_usd` per run in `registry.py`, a per-invocation `Budget` in `k1b/loop.py`, and the daily/monthly
   budget). I did not invent one. Adding a per-call cap is a new config field and a design decision; open.
6. Still open from the earlier reviews, not touched here: X-02 reserve-then-settle, B-01 per-process `disabled_sources`,
   A-24 `retain_days` default, `dev` vs `demo` stage name, A-07 `_unanchored` memory only, A-10 dead code.

## C-01: price check and token ceiling
- Prices: for a live route (any `backends.llm.kind` other than `fake`), a price must be finite and above 0 on input and output,
  tested with `not (p.is_finite() and p > 0)` in `_price_ok` (total: NaN or Infinity can never raise). Exception: exactly 0 is
  allowed when the route sets `price_is_zero_by_design: true` AND the llm kind is keyless loopback. The flag on any other
  live kind is itself refused. Negative prices are never allowed.
- Honest correction of the design review: with the installed pydantic, `Decimal("NaN")` and `Infinity` are already refused
  by the field itself as a validation error (a ConfigError), so the crash the reviews described did not happen here.
  The total predicate and a `Route` validator (non-finite refused for every kind, fake included) are extra safety in case
  that pydantic default changes. Mutant C01-10 (validator removed) therefore survives: double coverage, not a test gap.
- Same refusal list: route refusals now go first in the `refused` list of `Config._cross_checks`, so price, flag and
  `max_tokens` problems appear together with the environment refusals in one error (`every refusal at once`, tested).
- `max_tokens`: still `gt=0` on the route; the ceiling is `Config.max_route_tokens` (`gt=0`, default `defaults.MAX_ROUTE_TOKENS`
  = 200_000), checked in the same list. Boundary tests use literals: 200_000 loads, 200_001 and 2_000_000 are refused,
  1 loads, 0 and -1 are refused, a lowered ceiling works.
- A tiny positive price (for example `0.000000000001`) is accepted on purpose (any floor would be an invented number); a test pins it.
- `price_is_zero_by_design` is a new `Route` field with default false; `config_hash` dumps with `exclude_defaults`, so existing
  agents are not un-qualified (tested).
- The `Money` annotation is unchanged. A finite-and-above-0 annotation shared by all money fields (reviewer suggestion M1)
  would reach `Budget` and `max_run_usd`, which may legitimately be 0 or None: not done, open.
- Cites at `b4cce5b`: `config.py` Route, `Config._cross_checks`, `defaults.py` near `PURGE_EVERY_S`, `backends/table.py` `OpenAICompatSettings`.

## A-01: the tick writes waiting audit events into the trail and fails when it cannot
- New last tick step `audit_drain` (function `tick.audit_drain`; the approvals step `reconcile` keeps its name, so the two no
  longer clash). It calls the audit kind's `reconcile()`, then `backlog()`, logs `audit_drain drained=<n> remaining=<n> corrupt=<n>`,
  and RAISES when `remaining > 0`, so `tick_state.last_ok_at` stops advancing, `last_error` says how many events wait, and the
  tick exits 1. If `backlog()` cannot read the table the step fails too ("unknown" is never shown as zero). Empty = green.
- `ChainAudit.reconcile` catches a damaged row (`ValueError`) per row, logs error type and event id only (never the body),
  skips it, counts it in `last_corrupt`, and carries on, so one bad row no longer blocks the rows behind it (A-22). A damaged
  row stays in the table, is counted by `backlog()`, and keeps the step failing until a person looks. A failed DELETE after a
  successful write is logged and not counted; the next tick absorbs the duplicate.
- `LocalDirSink` already moved damaged files to `outbox/corrupt/`; it now logs that (type and file name) and counts it in
  `last_corrupt`. `backlog()` counts memory plus `outbox/*.json` (moved-aside files are not counted: they are quarantined).
- A kind with no `reconcile` logs one line and passes.
- Both kinds log a WARNING (error type and event id only) when an outcome goes to the outbox; the chain kind logs an ERROR
  when even the outbox write fails. Tests: bad row then good row, stuck database leaves the step failing (unit and through
  `run_tick`, exit 1, `last_ok_at` still empty), empty is green, the real `local_dir` kind drains through the tick,
  DuplicateEvent path in `write_outcome` (both kinds) logs nothing, STEPS entry (function, `every_s == 0`, `interval is None`,
  last), warning on both sinks and no error text, no-reconcile line, DELETE failure.
- LIMITS (stated plainly, not fixed):
  1. **Memory-only events cannot be recovered by the tick.** If the serving process could neither append nor write the outbox,
     the event is held in that process's memory (`_pending`). The tick is a separate short-lived process and cannot see it; it
     is lost if that process exits. The ERROR line "held in memory only" is the only trace. Fixing it needs a durable
     write-ahead before the side effect (a design change), not a tick step.
  2. `K1bAudit` has no `reconcile` (see decision 4).
  3. The `local_dir` outbox drains only if the tick shares the filesystem with the serving process.
  4. `reconcile` is unbounded (no LIMIT); replayed events keep their original principal and time. Unchanged from v1.
  5. `ChainAudit._unanchored` is memory-only (A-07), untouched.
- Privilege: no new right. The runtime role already has SELECT, INSERT, DELETE on `audit_outbox` (`store/migrate.py` `GRANTS`);
  `backlog()` only adds a `COUNT(*)` on the same table. A negative test that the audit identity cannot UPDATE or DELETE
  `audit_entries` exists in the existing Postgres tests; I did not add or run one (Postgres not available here).

## G5 wording (text and comments only)
- Both texts now say what is true: no separate check that blocks a message after redaction exists; G5 is not built here; what
  does exist is one final redaction of approval and channel text (`approvals/channel.py`, `clean`), using the same patterns,
  which is not independent. `approvals/gate.py` header and `guard/redact.py` docstring changed; test docstring in
  `tests/warden_port/test_gate.py` says the G5 leak block is not ported.
- Not changed: the original design notes lower in `gate.py` that describe G5 and the ways out are marked "read as the original
  design only" in the new header, rather than rewritten.

## What I ran (scratch copy of `b4cce5b`, all three patches applied; raw output in `raw/`)
| Command | Result |
|---|---|
| `uv run --all-extras --group test pytest tests -p no:cacheprovider -q` (full suite) | see top: 2 failed (also on pristine), rest passed, 455 skipped; counts in `raw/full-suite.txt` |
| targeted: `test_c01_route_limits.py`, `test_a01_audit_reconcile.py`, `test_p7_tick.py` | passed, counts in `raw/targeted.txt` |
| `ruff check src tests`, `ruff format --check src tests` | clean (`raw/ruff.log`) |
| `bandit -ll` on the 8 touched src files (via `uvx`, it is not in the test group) | rc 0, no findings (`raw/bandit.log`) |
| hand-made mutation lane (29 mutants) | `raw/mutation.txt`; survivors: C01-07 (equivalent: the flag-on-non-local case is refused by its own line either way), C01-10 (double coverage by pydantic, above), A01-14 (killed after adding a test, `raw/mutation-A01.txt`) |

# F-store hostile review 2: spend reservations, release command, meter, as a whole (merged head of cloud/core-b)

Reviewer: fresh, hostile, read-only. No source, test, commit or push. Scratch files only, in /tmp/core-b-scratch-F6/
(prop.py, race.py, probe1.py, probe2.py, probe3.py). PostgreSQL runs used HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55439/hadavin_test
with a throwaway schema per script (dropped afterwards; checked: no `scr_f6_*` schema left). No model call, no secret.

Question: can money be spent past a cap, double-counted, lost, or released wrongly?

Verdict: the reserve / settle / expire / release core is SOUND under everything I threw at it. The money leaks I found are
outside that core or at its edges: 1 Major (negative or NaN cost reaches the counters through the old charge path),
1 Medium (PostgreSQL settle computes its delta in the caller's Decimal context), 2 Medium/Low (purge of expired holds,
release role not enforced by the database), 4 Low, 3 Nits.

## What I ran and what held

- Random-sequence property check (prop.py), my own reference model of the counters (rows open/expired count their reserved
  amount, settled rows their settled amount, purged rows keep what they held, plus add_spend). Ops: reserve (new id, reused
  id, four caps pairs), settle (known, unknown, repeat, `Decimal` 0 / 1e-12 / 90 via `9E+1`), expire(0), purge, release (the
  real SQL function, PostgreSQL only), add_spend. Five agent ids that differ by case and by unicode (`a`, `A`, `é`,
  `e` + U+0301, `agent-1`), four days over the 31 Jan / 1 Feb boundary and the month counter. After EVERY step the day and
  month counters of every agent and day were compared with the model, and every return value / exception was compared.
  memory: 300 seeds x 250 steps OK. PostgreSQL: 40 seeds x 250 steps OK. Release always reported `applied_usd == released_usd` (no drift).
  Memory (month = sum of days) and PostgreSQL (month counter row) agreed everywhere, also after purges.
- Real races on PostgreSQL with one connection per worker (race.py; the store's process-wide lock would hide them
  otherwise): 8 reserves at a day cap of 10 for 3 each -> exactly 3 won; 8 reserves on 8 days at a month cap of 10 -> exactly 3;
  150 iterations of settle vs expire (open row), settle vs settle (different amounts), late settle vs release (expired row),
  settle vs expire vs release. After each: counter == (reserved if open/expired else settled_usd) on day and month: 0
  mismatches, no exception, no deadlock. The settle claim (`_CLAIM`, postgres.py:785) takes the post-expiry branch after a
  lock wait, as claimed.
- Cap exactly: `usd + amt == cap` passes, `usd == cap` refuses even a 0 amount (memory and PostgreSQL agree).
- Exponent form: `Decimal("9E+8")` books 900000000 on both stores; `1E+9` and `9.99999999E+8` over a 9E+8 counter refuse as
  they should; a cap of `5E+9` is accepted. Exponent above 9 or below -12 is a ValueError before any SQL.
- Lock order is row, day, month in reserve, settle and release; add_spend is day, month. No cycle found.
- Month boundary: settle and release use the ROW's day and its month (never today's); the 31 Jan hold settled on 1 Feb moves
  January counters (checked by the property run). The day is the UTC date at reserve time (`limits.py:130`,
  `models.py:329`): a person who reads "day" as a local date and passes it to `release-expired --day` releases the wrong
  UTC day's holds (only expired ones, never live ones; the command prints the day it used).

## Findings

### M1 (Major). A negative or NaN cost reaches the spend counters and the run cost: the cap can be passed with no limit
Files: store/postgres.py:531 (`add_spend`), store/postgres.py:391 (`add_cost`), store/memory.py:212 and :90, limits.py:77
(`Limits.charge`), limits.py:76 (`Budget.charge`), llm/common.py:262-268 (`reply`), llm/openai_compat.py:152
(`usage.get("prompt_tokens")`), runtime/agent_loop.py:353 and :513 (the two live callers), store/protocol.py:249.
Neither `add_spend` nor `add_cost` nor `charge` applies `check_spend_amount`; only the reserve/settle pair does. `reply()` takes
`tokens[0] or estimate_tokens(...)`: a NEGATIVE token count from the provider (a router or proxy behind `openai_compat`, or a
bug) is truthy, so it is used. Run in this tree: `reply(route, tokens=(-1_000_000_000, 5), ...)` gives `cost_usd = -2999.999925`.
Then agent_loop.py:513 does `limits.charge(agent_id, reply.cost_usd)` and `store.add_cost(run_id, reply.cost_usd)`.
Scenario: day cap 5, hold of 4 booked. One reply with `prompt_tokens: -1000000000` makes `add_spend` return (-2999.99, ...);
every reserve after it passes the cap with 3000 USD of room, and `blocked()` reads the day as under budget. Same for the run's
`max_run_usd`. NaN (a token count `"NaN"` is not an int, but a Decimal price times anything can be built by a bad config
route price): PostgreSQL stores NaN, `usd < cap` is then false for ever (fail closed but the counter is poisoned and the
only repair is hand SQL); Infinity becomes NaN. On memory, the counter row NaN makes `spend_totals` of the whole month NaN and a
reserve raises `InvalidOperation` (Limits maps it to limits_unavailable: closed, but permanent).
Repro (probe2.py, both stores): `reserve_spend("hold1","ag",day,Decimal(4),day_cap=5,...)`, then `add_spend("ag",day,Decimal(-100))`
returns `(-96, -96)`, then `reserve_spend(..., Decimal(1), day_cap=5)` succeeds. `add_spend(..., Decimal("NaN"))` returns NaN.
The settle path itself refuses a negative actual (ValueError), so this is the pre-gate path: it is live today because the gate
is not in the tree and agent_loop still charges after the call. The in-memory `Budget.charge(reply.cost_usd)`
(k1b/loop.py:174) takes the same negative cost and LOWERS `spent`, so the `--max-usd` cap of eval/replay can be undone by one reply.
Fix: `check_spend_amount` in `add_spend`, `add_cost`, `Limits.charge`, `Budget.charge` (refuse, do not clamp); in `reply()` take
a token count only when it is an int >= 0, else estimate (and ProviderError for a negative one); CHECK (usd >= 0)-style guard is
impossible on the counters because settle moves them down, so the check must be in code.

### M2 (Medium). PostgreSQL settle computes the counter delta in the CALLER's Decimal context
File: store/postgres.py:817 (`delta = row["settled_usd"] - row["reserved_usd"]`), applied by :824-:831. The memory store
wraps the same arithmetic in `defaults.money_context()` (memory.py:366-376); `Limits._settle` wraps its own; the PostgreSQL
settle does not, although the whole point of `money_context` (defaults.py:185, to-core-c-3) is that a host's precision cannot round money.
Repro (probe1.py): `reserve 0.5`, set `decimal.getcontext().prec = 5`, `settle_spend(id, Decimal("0.123456789012"))`:
PostgreSQL counters become `0.12346`, memory counters `0.123456789012`. The row says settled 0.123456789012, the counters
disagree with it for ever (drift, undetectable by release's `applied_usd` because that compares only the clamp). A rounding
mode of ROUND_DOWN undercounts every settle; a host that sets the `Inexact` trap makes every settle raise after the claim
(rolled back, so only an outage, not a leak). Fix: compute the delta in SQL (`RETURNING r.settled_usd - r.reserved_usd`) or wrap
in `localcontext(defaults.money_context())`; add a contract test that settles under `prec=5` on both stores.

### M3 (Medium/Low). The purge deletes expired-unsettled holds: a late settle is NotFound, the money stays booked and can never be released
Files: store/postgres.py:854-863, memory.py:398-408, runtime/tick.py:206 (400-day ceiling), protocol.py:335.
Answer to core-a's question, as built: `purge` deletes closed rows whether settled OR expired. Consequences, run on both stores
(probe3.py): reserve 2, expire, purge, then a late `settle_spend(id, 5)` -> `NotFound`; counters stay 2 on the day and the
month; the real 5 is not booked (3 lost against the cap and the run cost), and the 2 can no longer be released because the
release function only sees rows with status `expired`. So an expired hold that is purged is a PERMANENT booking on that
month counter (the day counter is stale by then), and a settle that arrives after the purge is silently an error the gate
treats as "worst case stays booked". With the tick's 400-day ceiling this needs a 400-day-late settle, so the practical risk
is the month counter of a long-dead month, but `purge_spend_reservations(before)` is a public method that takes any bound
(the purge role, an operator script, a shorter retention setting later) and the contract says nothing about expired rows.
Fix options: purge only `status = 'settled'` rows; or purge expired rows only after the run `release` has been given a
chance and only for days older than the month (so the counter it held no longer matters); at least state in
ii-meter.md (point 10 and 12) that a purged expired hold is permanent.

### M4 (Medium/Low). The "release role is the only way" guarantee is not enforced by the database
Files: store/migrations/0008_release_expired_spend.sql:2 ("the ONLY way the booked amount of an expired hold goes down"),
store/migrate.py:56-58 (`spend`, `spend_month`, `spend_reservations` all `_RW = SELECT, INSERT, UPDATE` for the runtime
login), ii-meter.md invariant 4 in the 12th stated limit.
The runtime login holds UPDATE on both counters and on `spend_reservations`. It can run, with no audit row,
`UPDATE spend SET usd = 0` or `UPDATE spend_reservations SET status='settled', settled_usd=0 WHERE status='expired'`
(the CHECK constraints allow it), which is exactly what the release function does. Any SQL injection, any bug in the runtime
process, any future code path (see M1) lowers the booked amount unaudited. Separating the release LOGIN buys an audited path,
not a protected one. Either say so in the migration comment and the runbook ("the runtime login could do this too; the
release command is the audited way, not the only one"), or enforce it: a BEFORE UPDATE trigger on `spend_reservations` that
refuses `expired -> settled` unless the session user is the release role, and the same for a decrease of `spend`/`spend_month`
that no open/expired row accounts for (harder; the trigger on the rows is the cheap half).

### L1 (Low). Reservation id reuse after purge: a stray late settle lands on the new hold
Files: protocol.py:73 (any id of the rule is accepted), postgres.py:739, memory.py:323. Repro (probe3.py, both stores): `dup`
reserved 1, settled 0.1, purged; `dup` reserved again (7, another call); a stray late `settle_spend("dup", 0.2)` from the first
call returns `applied=True` and closes the 7 hold at 0.2 (counters 7 replaced by 0.2; the second call, billed more, is
under-counted). `Limits.reserve` uses `new_id("res")` (uuid4), so only a custom caller of the store, or an operator who chose ids,
is exposed. Cheap guard: refuse (StaleState) an id whose settle could still arrive is impossible without a tombstone; the
honest fix is to say in protocol.py that the id MUST be unique for ever and that the store does not remember a purged one.

### L2 (Low). Release is all-or-nothing per (agent, day), has no age floor and does not report month drift
Files: 0008 SQL (the `claimed` CTE, the month `GREATEST(m.usd - total, 0)` near the end), cli.py:547-611.
(a) The command releases EVERY expired hold of that agent and day, including holds that expired seconds ago: the expiry age
is `max(3600 s, stuck-run age)` of the tick's own config (tick.py:265-285), and a model call that outlives it (a long call
timeout, a stuck-age config set lower than the call) is marked expired while still running; an operator who runs the command
for "yesterday" for a flapping-network cleanup also releases those, and their late settle then books nothing (stated in
ii-meter 12, accepted by running the command, but there is no `--older-than`, no dry run and no per-hold choice).
(b) `applied_usd` reports only what the DAY counter really fell by; the month clamp at zero is silent, so a month drift
(month counter below the day's sum, e.g. after a manual repair) is hidden. Report `applied_month_usd` too.

### L3 (Low). The "never sent" test follows `__context__`, so a reset after a refused first address counts as never sent
File: llm/retry.py:98-108 (`_chain` follows `__cause__`, `__context__` and `reason`; `never_sent` is true if ANY link is a
ConnectionRefusedError or gaierror and none is a timeout or a status). Repro: `call()` catches a ConnectionRefusedError and
raises ConnectionResetError from inside the handler (a client that falls back to a second address which connected and
was cut mid-answer): `with_retry(call, max_attempts=1)` returns `ProviderExhausted` with `refused_before_response = True`.
Today the mark on `ProviderExhausted` is inert (the gate ignores it by type, retry.py docstring rule 2), so no money moves; when
core-c honours it (requests/to-core-c-1) such a call, billed for the work done, is settled at 0. UNVERIFIED that any shipped adapter
(urllib via guard/http, the SDKs) produces that chain; it does not need a timeout link, which is the only guard. Cheap fix: take
`__context__` only when the exception was not itself explicitly raised from another (`__suppress_context__` / cause rules), or
count only the OUTERMOST error's own type and its `reason`.

### L4 (Low, integration, not a defect of the store). The gate is not wired, so the caps hold only before the call today
`grep` of src finds no caller of `Limits.reserve`, `settle` or `settle_for` (also stated in review 5 m-2). The live runtime
path is agent_loop.py:277-283 `blocked()` (a READ of the counters) and then `charge()` AFTER the call (:353, :513): several
runs of one agent that pass `blocked()` together each spend their real cost and the day cap is exceeded by up to
(concurrent calls x call cost), with no reservation. When core-c installs the gate, invariant 8 of ii-meter.md ("nothing calls
Limits.charge for a gated call") is satisfied only if the agent_loop charge lines are removed in the same change, otherwise
every gated call is counted twice (settle books it, charge books it again, and `add_cost` adds the run cost twice). Nothing in the
tree tests or enforces that; suggest a contract test in core-c that fails when a model call both settles and charges.

## Nits

- N1. memory.py stores `Decimal("-0")` as `reserved_usd` (`check_spend_amount` accepts it: `0 <= -0`); PostgreSQL stores 0 and
  returns 0. Counters equal; the row differs (`-0` vs `0`) between the stores. Normalise with `+usd`... or refuse.
- N2. `Budget._closed` (limits.py:61) grows by one run id per `forfeit` for the life of the process; harmless for a command line.
- N3. Interaction Budget / real store in one process: they share nothing. Money spent through `Budget` (eval, replay) is invisible to
  the agents' day and month counters and run costs, and `Budget`'s one total cap is not per agent or per day; documented as "no store"
  (limits.py:41), so only a warning for anyone who runs eval and the runtime in one process. `Budget.charge` rows have no agent
  (`None`), so `settle_for(agent, <a charge row id>)` is NotFound, which is right.
- N4. `UPDATE runs SET cost_usd ...` in `settle_spend` (postgres.py:834) names `runs` unqualified, unlike the three spend tables
  that `_t()` qualifies against temporary-table shadowing; a temp table `runs` of the runtime session would take the run cost.
  Same exposure as every other method on `runs`, so only noted.

## Checked and sound (no finding)

- Two settles: first wins, the second returns the stored row with `applied False`, counters moved once, run cost added once.
- Settle racing expiry (either order) and late settle racing release (either order): counters equal the row, the money is
  booked exactly once (release wins: booked 0 and the late actual is unbooked, which ii-meter 12 states; settle wins: the
  release then skips the row).
- Release of a day with live holds: open rows untouched; the counters keep their reserved amount (race.py kind 3 and the property run).
- Run id None vs a closed or missing run: a missing run row only moves the counters (memory and PostgreSQL), a closed run
  still gets the cost (no state check; fine).
- Agent ids that differ by case or unicode normalization are different agents in both stores and in release (PostgreSQL text
  equality is bytewise under the default collation; a nondeterministic database collation is outside the claim).
- The refused-before-response mark: first attempt 401/403/404 on openai_compat is True; a 429 then 401 stays False; the second
  request of openai_compat clears it (:129-130); a parse failure of a 200 answer is not marked; the mark is a real bool, so
  `is True` in the gate is safe.

## For the lead

M1 and M2 are code fixes in step F's own files (M1 touches `limits.py`, both stores' `add_spend`/`add_cost`, `llm/common.py`
`reply`). M3 and M4 need a decision (purge rule; enforce or reword the "only way" sentence). L1-L4 and nits: wording or
core-c.

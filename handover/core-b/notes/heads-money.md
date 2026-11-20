# Money heads: what the unmerged branches already contain (reserve / settle spend cap)

Read-only survey, done with `git show` / `git diff origin/main...origin/<b>` / `git log origin/main..origin/<b>` only.
No branch was checked out, no test was run. Line numbers are those of the file AS IT IS ON THE NAMED REF.
Code blocks are machine-extracted from the ref (line number, tab, text), not retyped.
"UNVERIFIED" marks anything not opened.

Refs:

| ref | head SHA | merge-base with origin/main |
|---|---|---|
| origin/main | 51c9fc4fbb4a887274615dbc5f83087ff0ab4280 | - |
| origin/core/P4d (PR 66) | da08ce2e240f65fcab6ff7d1a4e181496da28a97 | 0dabf1fa7a2ed58e14b8bca13be1141ac59f9c71 |
| origin/core/P4d-a2 (PR 75) | a8abba0f9ca9c1788e2e23c39a7863d89d0451b9 | c709df32f78fdb59a80958c32ef3ca33f4212850 |
| origin/core/P4b1 (PR 79) | 8cc2021f74c847c96dfe23b84887ff40d45efcb1 | db17c53a42df34aa495ebae8390e18b9ab3ae934 |
| origin/core/P4a (PR 78) | 4a0976ffdbda144f768ee7118b5d2ef65c757d47 | 1e4752f2211fb09a4d2487e568f73d113e371042 |
| origin/core/T1-T2-tests | 1a7d2029013deff2054c4c18f73663f21aaa7c3c | 0dabf1fa7a2ed58e14b8bca13be1141ac59f9c71 |

PR numbers are as given in the task; they were not checked against GitHub (UNVERIFIED).
None of the five branches is based on today's main: every one needs a rebase or merge of main first.

How the branches relate (from `git log` and `git merge-base`):

- P4d-a2, P4b1 and P4a all contain commits 1a885f3 (P4d-a1 harness) and c31f336 ("P4d-a2-i and P4d-b: money
  validators, cost rounding, route price check, spend reservations (memory and Postgres, migration 0006)").
- P4b1 forks from P4d-a2 at 7a84408 (the commit after c31f336). `git diff 7a84408 origin/core/P4b1 --stat -- src`
  shows P4b1 changed only defaults.py, limits.py, meter.py, money.py. So P4b1's store files are the OLD
  c31f336/7a84408 store, not P4d-a2's head.
- P4a forks at c31f336 and also merges core/P4d-a2 at an early point (f0465df) and the whole of core/P2a-1
  (kill switch "stop state", migration 0007). P4a's store is the c31f336 store plus the P2a-1 kill switch changes.
- P4d-a2's head has 12 more commits on the store than the copy inside P4b1 and P4a (write wrapper, retry,
  StoreBusy, one-statement sweep, extra trigger rule, many proofs).
- P4d (PR 66) and T1-T2-tests change tests only, no file under src/.

---------------------------------------------------------------------------------------------------------------

# Part 1. origin/main (51c9fc4) as it is today

Summary: main has NO reserve step. `Limits.blocked` reads totals before a call, `Limits.charge` adds the real cost
after it. Two callers can both pass `blocked` before either charges.

## 1.1 src/hadavin_sdk/limits.py (whole file, 51 lines)

`origin/main:src/hadavin_sdk/limits.py` lines 1-51:

```
1	"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""
2	
3	from __future__ import annotations
4	
5	from decimal import Decimal
6	
7	from hadavin_sdk.audit.protocol import AuditSink
8	from hadavin_sdk.models import AuditEvent, KillSwitch, now
9	from hadavin_sdk.registry import Registry
10	from hadavin_sdk.store.protocol import Store
11	
12	
13	class Limits:
14	    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
15	        self.store, self.audit, self.registry = store, audit, registry
16	
17	    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
18	        return self.store.add_spend(agent_id, now().date(), usd)
19	
20	    def blocked(self, agent_id: str) -> list[str]:
21	        reasons = []
22	        if self.store.get_kill_switch().on:
23	            reasons.append("kill_switch")
24	        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
25	        budget = self.registry.agents[agent_id].budget_usd
26	        if day >= budget.daily:
27	            reasons.append("daily_budget")
28	        if month >= budget.monthly:
29	            reasons.append("monthly_budget")
30	        return reasons
31	
32	    @staticmethod
33	    def _event(on: bool, by: str, operation: str) -> AuditEvent:
34	        return AuditEvent(
35	            run_id="-",
36	            domain="limits",
37	            operation=operation,
38	            principal=by,
39	            source="cli",
40	            result="on" if on else "off",
41	        )
42	
43	    def stop(self, by: str) -> None:
44	        """An emergency stop must work when the audit store is down: switch first, then audit (outbox)."""
45	        self.store.set_kill_switch(KillSwitch(on=True, by=by))
46	        self.audit.write_outcome(self._event(True, by, "stop"))
47	
48	    def reset(self, by: str) -> None:
49	        """Removing a safety control is audited first; if that fails, the switch stays on."""
50	        self.audit.write_intent(self._event(False, by, "reset"))
51	        self.store.set_kill_switch(KillSwitch(on=False, by=by))
```

## 1.2 src/hadavin_sdk/store/protocol.py: spend, budget, kill switch methods

There is no budget method on the Store: budgets live in the registry (`registry.py:34-37`, quoted in 1.5).

`origin/main:src/hadavin_sdk/store/protocol.py` lines 55-57:

```
55	    def add_cost(self, run_id: str, usd: Decimal) -> None:
56	        """Raises NotFound for an unknown run."""
57	        ...
```

`origin/main:src/hadavin_sdk/store/protocol.py` lines 107-116:

```
107	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]: ...
108	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
109	        """(day, month) totals; a read with no write."""
110	        ...
111	
112	    def get_kill_switch(self) -> KillSwitch:
113	        """A missing or unreadable switch row reads as ON (fail closed)."""
114	        ...
115	
116	    def set_kill_switch(self, ks: KillSwitch) -> None: ...
```

## 1.3 src/hadavin_sdk/store/memory.py: spend and kill switch

`origin/main:src/hadavin_sdk/store/memory.py` lines 28-39:

```
28	class MemoryStore:
29	    def __init__(self) -> None:
30	        # ponytail: one global lock; per-row locks only if a real backend ever needs throughput here.
31	        self._lock = threading.Lock()
32	        self._runs: dict[str, Run] = {}
33	        self._plans: dict[str, Plan] = {}
34	        self._gates: dict[str, GateDecision] = {}
35	        self._approvals: dict[str, ApprovalRequest] = {}
36	        self._decisions: list[ApprovalDecision] = []
37	        self._dead: dict[str, list[DeadLetter]] = defaultdict(list)
38	        self._spend: dict[tuple[str, date], Decimal] = defaultdict(Decimal)
39	        self._kill = KillSwitch()
```

`origin/main:src/hadavin_sdk/store/memory.py` lines 76-81:

```
76	    def add_cost(self, run_id: str, usd: Decimal) -> None:
77	        with self._lock:
78	            run = self._runs.get(run_id)
79	            if run is None:
80	                raise NotFound(run_id)
81	            self._runs[run_id] = run.model_copy(update={"cost_usd": run.cost_usd + usd})
```

`origin/main:src/hadavin_sdk/store/memory.py` lines 196-224:

```
196	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
197	        with self._lock:
198	            self._spend[(agent_id, day)] += usd
199	            month = sum(
200	                v
201	                for (a, d), v in self._spend.items()
202	                if a == agent_id and (d.year, d.month) == (day.year, day.month)
203	            )
204	            return self._spend[(agent_id, day)], Decimal(month)
205	
206	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
207	        with self._lock:
208	            month = sum(
209	                (
210	                    v
211	                    for (a, d), v in self._spend.items()
212	                    if a == agent_id and (d.year, d.month) == (day.year, day.month)
213	                ),
214	                Decimal(0),
215	            )
216	            return self._spend.get((agent_id, day), Decimal(0)), month
217	
218	    def get_kill_switch(self) -> KillSwitch:
219	        with self._lock:
220	            return self._kill.model_copy(deep=True)
221	
222	    def set_kill_switch(self, ks: KillSwitch) -> None:
223	        with self._lock:
224	            self._kill = ks.model_copy(deep=True)
```

## 1.4 src/hadavin_sdk/store/postgres.py: spend and kill switch

One connection behind one `threading.Lock` per process (postgres.py:193-197). No reservation table.

`origin/main:src/hadavin_sdk/store/postgres.py` lines 192-202:

```
192	class PostgresStore:
193	    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
194	    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
195	    def __init__(self, conn: psycopg.Connection) -> None:
196	        self._db = conn
197	        self._lock = threading.Lock()
198	
199	    # --- generic helpers ---------------------------------------------------------------------------------
200	
201	    def _exec(self, query, params=()) -> psycopg.Cursor:
202	        return self._db.cursor(row_factory=dict_row).execute(query, params)
```

`origin/main:src/hadavin_sdk/store/postgres.py` lines 270-277:

```
270	    def _update_run(self, query: str, value: Any, run_id: str) -> None:
271	        with self._lock:
272	            cur = self._exec(query, (value, run_id))
273	        if cur.rowcount == 0:
274	            raise NotFound(run_id)
275	
276	    def add_cost(self, run_id: str, usd: Decimal) -> None:
277	        self._update_run("UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s", usd, run_id)
```

`origin/main:src/hadavin_sdk/store/postgres.py` lines 416-464:

```
416	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
417	        """Day and month counters, each one atomic upsert, in one transaction: exact under concurrency."""
418	        month = day.replace(day=1)
419	        with self._lock, self._db.transaction():
420	            d = self._exec(
421	                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
422	                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd",
423	                (agent_id, day, usd),
424	            ).fetchone()["usd"]
425	            m = self._exec(
426	                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
427	                "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd "
428	                "RETURNING usd",
429	                (agent_id, month, usd),
430	            ).fetchone()["usd"]
431	        return Decimal(d), Decimal(m)
432	
433	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
434	        with self._lock:
435	            d = self._exec(
436	                "SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent_id, day)
437	            ).fetchone()
438	            m = self._exec(
439	                "SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",
440	                (agent_id, day.replace(day=1)),
441	            ).fetchone()
442	        return (Decimal(d["usd"]) if d else Decimal(0)), (Decimal(m["usd"]) if m else Decimal(0))
443	
444	    def get_kill_switch(self) -> KillSwitch:
445	        found = self._select(KillSwitch, "kill_switch", "id = 1", ())
446	        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
447	            _LOG.error(
448	                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
449	            )
450	            return KillSwitch(on=True, by="system:kill_switch_row_missing")
451	        return found[0]
452	
453	    def set_kill_switch(self, ks: KillSwitch) -> None:
454	        row = {"id": 1, **_row(ks)}
455	        cols = [sql.Identifier(c) for c in row]
456	        query = sql.SQL(
457	            "INSERT INTO kill_switch ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}"
458	        ).format(
459	            sql.SQL(", ").join(cols),
460	            sql.SQL(", ").join(sql.Placeholder() * len(row)),
461	            sql.SQL(", ").join(sql.SQL("{0} = EXCLUDED.{0}").format(c) for c in cols[1:]),
462	        )
463	        with self._lock:
464	            self._exec(query, list(row.values()))
```

Tables on main: `spend` (0001_core.sql:87), `kill_switch` (0001_core.sql:94), `spend_month` (0003_approvals_tick.sql:15).
GRANTS on main (`store/migrate.py:53-55`): `"spend": Grant("table", _RW)`, `"spend_month": Grant("table", _RW)`,
`"kill_switch": Grant("table", _RW)`. Migrations on main: 0001 to 0005 only.

## 1.5 The Budget classes

`grep "class Budget"` finds two: the k1b one (the invocation cap) and the registry one (per-agent day/month budget).

`origin/main:src/hadavin_sdk/k1b/loop.py` lines 40-52:

```
40	class Budget:
41	    """A total USD cap for the whole invocation. One reply can overshoot it; the next call is refused."""
42	
43	    def __init__(self, limit: Decimal) -> None:
44	        self.limit = limit
45	        self.spent = Decimal(0)
46	
47	    def charge(self, usd: Decimal) -> None:
48	        self.spent += usd
49	
50	    @property
51	    def exhausted(self) -> bool:
52	        return self.spent >= self.limit
```

`origin/main:src/hadavin_sdk/registry.py` lines 34-37:

```
34	class Budget(BaseModel):
35	    model_config = ConfigDict(extra="forbid", frozen=True)
36	    daily: Money
37	    monthly: Money
```

`AgentRecord.max_run_usd: Money | None` is at `registry.py:54`; the run cap is read at `runtime/agent_loop.py:256-257`
(`cap = self.registry.agents[run.agent_id].max_run_usd` ... `self.store.get_run(run.run_id).cost_usd >= cap`).

Price fields on main (`config.py:64` Money, `config.py:72-76` Route). No price validator on main.

`origin/main:src/hadavin_sdk/config.py` lines 64-76:

```
64	Money = Annotated[Decimal, BeforeValidator(_money)]
65	
66	
67	class _Strict(BaseModel):
68	    # A mistyped key may hold a secret: errors name the field, never its value.
69	    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
70	
71	
72	class Route(_Strict):
73	    model_id: str
74	    input_usd_per_mtok: Money
75	    output_usd_per_mtok: Money
76	    max_tokens: int = Field(gt=0)
```

## 1.6 The five charge sites on main, 6 lines of context each

### runtime/agent_loop.py:325 (injection screen; a model-backed detector)

`origin/main:src/hadavin_sdk/runtime/agent_loop.py` lines 319-331:

```
319	        return ToolOutput(text, digest, error, int((time.monotonic() - started) * 1000))
320	
321	    def _screen(self, run: Run, text: str, source: str):
322	        """The injection check; a model-backed detector's call (llm_judge) is charged like any model call."""
323	        verdict = injection_check(self.detector, text, source)
324	        if verdict.cost_usd:
325	            self.limits.charge(run.agent_id, verdict.cost_usd)
326	            self.store.add_cost(run.run_id, verdict.cost_usd)
327	        return verdict
328	
329	    def _to(self, run: Run, new: RunState, reason: str | None = None) -> Run:
330	        cur = self.store.get_run(run.run_id)
331	        run = advance(self.store, run.run_id, cur.state, new, reason)
```

### runtime/agent_loop.py:485 (the chat reply)

`origin/main:src/hadavin_sdk/runtime/agent_loop.py` lines 479-491:

```
479	            ) as exc:  # a refused key or request must not strand the run in WORKING
480	                code = (
481	                    "provider_exhausted" if isinstance(exc, ProviderExhausted) else "provider_error"
482	                )
483	                self._note(run, "llm", "chat", result="failed", error_code=code)
484	                return self._abstain(run, S.NEEDS_PERSON, code, cited)
485	            self.limits.charge(agent_id, reply.cost_usd)
486	            self.store.add_cost(run.run_id, reply.cost_usd)
487	            if reply.stop_reason in (
488	                "max_tokens",
489	                "refusal",
490	            ):  # cut off or declined: never "no action"
491	                self._note(
```

### k1b/loop.py:170 (worst case on CallTimeout)

`origin/main:src/hadavin_sdk/k1b/loop.py` lines 164-176:

```
164	                tools=TOOL_SPECS,
165	            )
166	        except CallTimeout:
167	            # The abandoned call may still be running and billed (a retry layer can re-send), so charge the
168	            # worst case and stop the run: at most one such call per invocation, and the cap still holds.
169	            if route_prices is not None:
170	                budget.charge(worst_case_usd(route_prices, system, messages))
171	            out.status, out.stop_reason, out.halt = "timeout", "call_timeout", "aborted"
172	            return out
173	        except ProviderExhausted:
174	            out.status, out.stop_reason = "error", "provider_exhausted"
175	            return out
176	        except ProviderError:
```

### k1b/loop.py:179 (the reply)

`origin/main:src/hadavin_sdk/k1b/loop.py` lines 173-185:

```
173	        except ProviderExhausted:
174	            out.status, out.stop_reason = "error", "provider_exhausted"
175	            return out
176	        except ProviderError:
177	            out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
178	            return out
179	        budget.charge(reply.cost_usd)
180	        if reply.stop_reason in ("max_tokens", "refusal"):
181	            out.status, out.stop_reason = "error", reply.stop_reason
182	            return out
183	        if not reply.tool_calls:
184	            out.via = "text"
185	            out.diagnosis = parse_diagnosis_text(reply.text)
```

### k1b/loop.py:206 (injection check of a tool result)

`origin/main:src/hadavin_sdk/k1b/loop.py` lines 200-212:

```
200	            if call.name not in ALLOWED_TOOLS:
201	                out.hard_check_a.append(call.name)
202	                shown, ids = _dumps({"result": "unknown tool"}), set()
203	            else:
204	                shown, ids = render(snap.call(call.name, call.input))
205	                verdict = injection_check(detector, shown, "k1b-tool-result")
206	                budget.charge(verdict.cost_usd)
207	                if verdict.flagged:
208	                    out.injection_flagged += 1
209	                    shown, ids = _dumps(NO_DATA), set()
210	            out.returned_ids |= ids
211	            messages.append(
212	                {"role": "assistant", "content": f"tool {call.name} {_dumps(call.input)}"}
```

Other readers of the limits on main: `agent_loop.py:251` (`self.limits.blocked(run.agent_id)`), `:716`, `:790`.
`worst_case_usd` on main is `k1b/loop.py:115`. On main, agent_loop has no worst-case booking: a `ProviderError`
(agent_loop.py:477-484) books nothing.

---------------------------------------------------------------------------------------------------------------

# Part 2. origin/core/P4d (PR 66), head da08ce2

Tests and test harness only. No Store Protocol method, no migration, no limits.py, config.py, k1b or agent_loop change,
no GRANTS change (no file under src/ is in the diff).

```
 CHANGELOG.md                                 |  11 +
 tests/conftest.py                            |  13 +
 tests/contracts/conftest.py                  | 110 ++++-
 tests/contracts/kinds/__init__.py            |  43 ++
 tests/contracts/kinds/builtin.py             |   7 +
 tests/contracts/kinds/store_postgres.py      | 258 ++++++++++--
 tests/contracts/store_support.py             | 168 ++++++++
 tests/contracts/test_pg_driver.py            | 298 +++++++++++++
 tests/contracts/test_pg_dsn_guard.py         | 121 ++++++
 tests/contracts/test_store.py                |  97 +++++
 tests/contracts/test_store_money_baseline.py | 123 ++++++
 tests/contracts/test_store_registry.py       | 604 +++++++++++++++++++++++++++
 tests/test_k5_round10_postgres.py            |   3 +-
 13 files changed, 1824 insertions(+), 32 deletions(-)
```

New test files (docstring heads read; bodies not read line by line):

- `tests/contracts/store_support.py`: recording proxy around a store, `utc_today`, session-end check ("which Protocol
  methods did the contract tests call").
- `tests/contracts/test_pg_driver.py` (19 tests): the neutral `pg_driver()` namespace so tests never import psycopg.
- `tests/contracts/test_pg_dsn_guard.py` (6): a DB test must skip (or fail under the fail rule) when
  `HADAVIN_TEST_PG_DSN` is missing; one helper `pg_test_dsn()` reads the variable.
- `tests/contracts/test_store_money_baseline.py` (6): PINS what `add_spend` / `add_cost` do today with a negative,
  NaN, infinite or >6-decimal amount (they book it). These pins flip once the validators of P4d-a2 land.
- `tests/contracts/test_store_registry.py` (38): store kind registry, `require_backend`, session-end check.
- Changed: `tests/contracts/conftest.py`, `kinds/__init__.py`, `kinds/store_postgres.py` (adds `store_pair`: two
  connections on one schema, runtime login helpers), `tests/conftest.py` (refuses xdist under the fail rule).

P4d-a2 contains an earlier state of this harness (commit 1a885f3) and then diverges: 7 of the 9 shared files have
different content on the two heads (list in Part 7).

---------------------------------------------------------------------------------------------------------------

# Part 3. origin/core/P4d-a2 (PR 75), head a8abba0: the store contract and the money SQL

This is the branch that implements reserve / settle / release / sweep in the STORE (both kinds).

```
 CHANGELOG.md                                       |    3 +
 pyproject.toml                                     |    2 +-
 src/hadavin_sdk/backends/table.py                  |    4 +
 src/hadavin_sdk/config.py                          |   16 +
 src/hadavin_sdk/defaults.py                        |   14 +
 src/hadavin_sdk/llm/common.py                      |   23 +-
 src/hadavin_sdk/llm/fake.py                        |    7 +-
 src/hadavin_sdk/models.py                          |   58 +-
 src/hadavin_sdk/store/memory.py                    |  268 ++++-
 src/hadavin_sdk/store/migrate.py                   |    1 +
 .../store/migrations/0006_spend_reservations.sql   |   69 ++
 src/hadavin_sdk/store/postgres.py                  |  512 ++++++++-
 src/hadavin_sdk/store/protocol.py                  |  240 ++++-
 tests/contracts/conftest.py                        |  107 +-
 tests/contracts/kinds/__init__.py                  |   29 +
 tests/contracts/kinds/builtin.py                   |    7 +
 tests/contracts/kinds/store_postgres.py            |  175 ++-
 tests/contracts/pg_owner.py                        |   85 ++
 tests/contracts/reserve_workers.py                 |   76 ++
 tests/contracts/store_support.py                   |  136 +++
 tests/contracts/test_cost_rounding.py              |  227 ++++
 tests/contracts/test_memory_lone_caller.py         |   93 ++
 tests/contracts/test_pg_driver.py                  |  150 +++
 tests/contracts/test_store.py                      |  114 ++
 tests/contracts/test_store_hostile.py              |  165 +++
 tests/contracts/test_store_money_edges.py          |  207 ++++
 tests/contracts/test_store_registry.py             |  334 ++++++
 tests/contracts/test_store_reserve.py              |  973 +++++++++++++++++
 tests/contracts/test_store_reserve_pg.py           |  335 ++++++
 tests/contracts/test_store_reserve_proofs_pg.py    | 1119 ++++++++++++++++++++
 tests/contracts/test_store_reserve_schema_pg.py    |  174 +++
 tests/contracts/test_store_writes_pg.py            |  876 +++++++++++++++
 tests/demo_askdata/test_validate_harm.py           |   11 +-
 tests/test_k5_fixes2.py                            |   37 +-
 tests/test_lockin_guard.py                         |    1 +
 tests/test_p2_postgres.py                          |    9 +-
 tests/test_p4d_missing_methods.py                  |   39 +
 tests/test_route_prices.py                         |   59 ++
 uv.lock                                            |   11 +
 39 files changed, 6681 insertions(+), 85 deletions(-)
```

## 3.1 Data model in one paragraph

A reservation is one row in the new table `spend_reservations`, keyed by a caller-chosen `reservation_id` (the
idempotence key). `reserve_spend` ADDS the reserved amount to the existing counters at once (`runs.cost_usd`,
`spend.usd`, `spend_month.usd`), inside one transaction, with the cap in the WHERE clause of each UPDATE. So the
counters always hold "settled + held", and every reader of the counters (`spend_totals`, `Limits.blocked`) already
counts held reservations. `settle_spend` moves the counters by `reserved - actual` (down, or up when the real cost is
higher). `release_spend` gives all of it back. `sweep_spend_reservations` marks old open rows `expired` and moves NO
counter: an expired row stays booked at the worst case (`settled_usd = reserved_usd`) and can still be settled or
released once. There is no expiry column: age is `clock_timestamp() - created_at`, with the age chosen by the caller of
the sweep (minimum 30 s).

## 3.2 Store Protocol: new names and methods (`store/protocol.py` on the branch)

`origin/core/P4d-a2:src/hadavin_sdk/store/protocol.py` lines 35-69:

```
35	# The most any one spend counter (the day, the month, a run's cost) may hold. A booking that would pass it is a
36	# ValueError and books nothing. The excess of a settle above its reservation is NOT held under it (the money is spent).
37	MAX_COUNTER_USD = 10**15
38	# The youngest age (seconds) of an open reservation that the sweep may expire; the meter picks the real value.
39	MIN_SWEEP_AGE_S = 30
40	_MIN_DAY, _MAX_DAY = date(2000, 1, 1), date(2100, 12, 31)
41	_ID_RE = re.compile(r"[A-Za-z0-9._:-]{1,200}\Z")
42	
43	
44	class SpendCapExceeded(RuntimeError):
45	    """A booking would pass a cap. `which` is "run", "day" or "month" (the first failing one in that order)."""
46	
47	    def __init__(self, which: str, cap: Decimal, current: Decimal, requested: Decimal) -> None:
48	        super().__init__(f"{which} cap {cap} exceeded: current {current}, requested {requested}")
49	        self.which, self.cap, self.current, self.requested = which, cap, current, requested
50	
51	
52	class KillSwitchOn(RuntimeError):
53	    """The kill switch is on (or unreadable): no new reservation."""
54	
55	
56	class CounterDamaged(RuntimeError):
57	    """A counter is lower than the amount to lower, or its row is missing: damaged data; nothing was changed."""
58	
59	
60	class ReservationConflict(StaleState):
61	    """The reservation id exists with different content."""
62	
63	
64	@dataclass(frozen=True)
65	class SpendOutcome:
66	    """`applied` is true only when THIS call changed the row; a replay or a lost race gives false."""
67	
68	    reservation: SpendReservation
69	    applied: bool
```

Validators shared by both stores: `check_usd` :72-92, `check_cap` :95-97, `check_day` :100-104, `check_int` :107-110,
`check_id` :113-117, `check_reserve` :126-142, `check_meta` :145-166, `StoreBusy` :191-193, `check_step_name`
:199-203, `check_text` :228-231. `is_connectivity_error` gains a first test (:173-174): SQLSTATE 40001, 40P01, 55P03,
57014 are NOT connectivity errors.

Changed docstring of an existing method:

`origin/core/P4d-a2:src/hadavin_sdk/store/protocol.py` lines 240-242:

```
240	    def add_cost(self, run_id: str, usd: Decimal) -> None:
241	        """Raises NotFound for an unknown run, `ValueError` for a bad amount or a total past `MAX_COUNTER_USD`."""
242	        ...
```

Spend methods, old and new (the six new ones are reserve_spend, settle_spend, release_spend, get_spend_reservation, list_open_reservations, sweep_spend_reservations):

`origin/core/P4d-a2:src/hadavin_sdk/store/protocol.py` lines 292-344:

```
292	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
293	        """`ValueError` for a bad amount or day (`check_usd` with 8 decimals, `check_day`) or when a counter would
294	        pass `MAX_COUNTER_USD`; nothing is booked then."""
295	        ...
296	
297	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
298	        """(day, month) totals; a read with no write."""
299	        ...
300	
301	    def reserve_spend(
302	        self,
303	        reservation_id: str,
304	        agent_id: str,
305	        day: date,
306	        amount_usd: Decimal,
307	        *,
308	        day_cap: Decimal | None,
309	        month_cap: Decimal | None,
310	        run_id: str | None = None,
311	        run_cap: Decimal | None,
312	        meta: Mapping[str, str | int | bool] | None = None,
313	    ) -> SpendOutcome:
314	        """Book `amount_usd` on the day and month counters (and the run's, with `run_id`) in one step, refusing at
315	        the caps (`SpendCapExceeded`, first failing of run, day, month), at the kill switch (`KillSwitchOn`) and at
316	        `MAX_COUNTER_USD` (`ValueError`). Same id and content again returns the open row with `applied=False`;
317	        same id with other content is `ReservationConflict`; a closed one is `StaleState`."""
318	        ...
319	
320	    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
321	        """Close an open (or expired) reservation at the real cost (at most 6 decimals; may exceed the reserved
322	        amount, which is booked in full). A closed one returns its first result with `applied=False`."""
323	        ...
324	
325	    def release_spend(self, reservation_id: str) -> SpendOutcome:
326	        """Close an open (or expired) reservation and give back the reserved amount; `CounterDamaged` (nothing
327	        changed) if a counter is lower than that amount or missing."""
328	        ...
329	
330	    def get_spend_reservation(self, reservation_id: str) -> SpendReservation: ...
331	    def list_open_reservations(
332	        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
333	    ) -> list[SpendReservation]: ...
334	    def sweep_spend_reservations(
335	        self, older_than_s: int, *, limit: int = 100
336	    ) -> list[SpendReservation]:
337	        """Open rows older than `older_than_s` (30 to 10**7) become `expired` (no counter moves)."""
338	        ...
339	
340	    def get_kill_switch(self) -> KillSwitch:
341	        """A missing or unreadable switch row reads as ON (fail closed)."""
342	        ...
343	
344	    def set_kill_switch(self, ks: KillSwitch) -> None: ...
```

`get_kill_switch` / `set_kill_switch` keep main's signatures on this branch (:340-344).
`missing_methods` (:381-390) is unchanged in logic, so a custom store without the six methods is named at start
(test: `tests/test_p4d_missing_methods.py`).

The row model, `models.py:351-366` on the branch:

`origin/core/P4d-a2:src/hadavin_sdk/models.py` lines 351-366:

```
351	class SpendReservation(Shape):
352	    """One reserved amount of spend (P4d-b). `status` moves open -> settled / released / expired; an expired row
353	    holds the worst case (`settled_usd == reserved_usd`) until it is settled or released once. Amounts are exact
354	    Decimals at six decimal places."""
355	
356	    reservation_id: str
357	    agent_id: str
358	    day: date
359	    run_id: str | None = None
360	    reserved_usd: Decimal
361	    status: Literal["open", "settled", "released", "expired"] = "open"
362	    settled_usd: Decimal | None = None
363	    created_at: datetime
364	    closed_at: datetime | None = None
365	    expired_at: datetime | None = None
366	    meta: dict[str, Any] | None = None
```

## 3.3 Migration `store/migrations/0006_spend_reservations.sql` (whole file, P4d-a2 head version)

`origin/core/P4d-a2:src/hadavin_sdk/store/migrations/0006_spend_reservations.sql` lines 1-69:

```
1	-- Hadavin core store, version 0006 (P4d-b): spend reservations. Forward-only and additive: no existing column changes.
2	-- Apply this migration with the kill switch on or in a quiet period: the foreign key needs a short lock on `runs`.
3	SET LOCAL lock_timeout = '10s';
4	
5	CREATE TABLE spend_reservations (
6	    reservation_id TEXT PRIMARY KEY CHECK (reservation_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
7	    schema_version INTEGER NOT NULL,
8	    agent_id TEXT NOT NULL CHECK (agent_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
9	    day DATE NOT NULL CHECK (day BETWEEN DATE '2000-01-01' AND DATE '2100-12-31'),
10	    run_id TEXT REFERENCES runs (run_id) CHECK (run_id ~ '^[A-Za-z0-9._:-]{1,200}$'),
11	    reserved_usd NUMERIC NOT NULL CHECK (reserved_usd > 0 AND reserved_usd <= 1000000000000 AND reserved_usd = round(reserved_usd, 6)),
12	    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'released', 'expired')),
13	    settled_usd NUMERIC CHECK (settled_usd IS NULL OR (settled_usd >= 0 AND settled_usd <= 1000000000000 AND settled_usd = round(settled_usd, 6))),
14	    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
15	    closed_at TIMESTAMPTZ,
16	    expired_at TIMESTAMPTZ,
17	    meta JSONB CHECK (meta IS NULL OR (jsonb_typeof(meta) = 'object' AND octet_length(meta::text) <= 2000)),
18	    CHECK ((status IN ('settled', 'expired')) = (settled_usd IS NOT NULL)),
19	    CHECK (status <> 'expired' OR settled_usd = reserved_usd),
20	    CHECK ((status = 'open') = (closed_at IS NULL)),
21	    CHECK (expired_at IS NULL OR status <> 'open')
22	);
23	
24	CREATE INDEX spend_reservations_open ON spend_reservations (created_at, reservation_id) WHERE status = 'open';
25	
26	-- A new row is always open, with the database clock as its time (a future created_at cannot make it immune to the sweep).
27	CREATE OR REPLACE FUNCTION hadavin_spend_reservations_insert() RETURNS trigger LANGUAGE plpgsql AS
28	$$
29	BEGIN
30	    IF NEW.status <> 'open' OR NEW.settled_usd IS NOT NULL OR NEW.closed_at IS NOT NULL OR NEW.expired_at IS NOT NULL THEN
31	        RAISE EXCEPTION 'spend_reservations: change refused';
32	    END IF;
33	    NEW.created_at := clock_timestamp();
34	    RETURN NEW;
35	END;
36	$$;
37	CREATE OR REPLACE TRIGGER spend_reservations_insert BEFORE INSERT ON spend_reservations
38	    FOR EACH ROW EXECUTE FUNCTION hadavin_spend_reservations_insert();
39	
40	-- The only changes: open to expired / settled / released, and expired to settled / released. Nothing else moves.
41	CREATE OR REPLACE FUNCTION hadavin_spend_reservations_update() RETURNS trigger LANGUAGE plpgsql AS
42	$$
43	BEGIN
44	    IF NEW.reservation_id IS DISTINCT FROM OLD.reservation_id OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
45	       OR NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.day IS DISTINCT FROM OLD.day
46	       OR NEW.run_id IS DISTINCT FROM OLD.run_id OR NEW.reserved_usd IS DISTINCT FROM OLD.reserved_usd
47	       OR NEW.created_at IS DISTINCT FROM OLD.created_at OR NEW.meta IS DISTINCT FROM OLD.meta THEN
48	        RAISE EXCEPTION 'spend_reservations: change refused';
49	    END IF;
50	    IF OLD.status = 'open' AND NEW.status = 'expired' THEN
51	        IF NEW.settled_usd IS DISTINCT FROM OLD.reserved_usd OR NEW.closed_at IS NULL OR NEW.expired_at IS NULL THEN
52	            RAISE EXCEPTION 'spend_reservations: change refused';
53	        END IF;
54	    ELSIF OLD.status = 'open' AND NEW.status IN ('settled', 'released') THEN
55	        IF NEW.expired_at IS NOT NULL THEN
56	            RAISE EXCEPTION 'spend_reservations: change refused';
57	        END IF;
58	    ELSIF OLD.status = 'expired' AND NEW.status IN ('settled', 'released') THEN
59	        IF NEW.expired_at IS DISTINCT FROM OLD.expired_at THEN
60	            RAISE EXCEPTION 'spend_reservations: change refused';
61	        END IF;
62	    ELSE
63	        RAISE EXCEPTION 'spend_reservations: change refused';
64	    END IF;
65	    RETURN NEW;
66	END;
67	$$;
68	CREATE OR REPLACE TRIGGER spend_reservations_update BEFORE UPDATE ON spend_reservations
69	    FOR EACH ROW EXECUTE FUNCTION hadavin_spend_reservations_update();
```

The copy of 0006 in P4b1 and P4a (identical to each other, blob compared) is the OLDER text: in the branch
`ELSIF OLD.status = 'open' AND NEW.status IN ('settled', 'released') THEN` it has a bare `NULL;` (its line 55) where
P4d-a2 has the three lines 55-57 above (`IF NEW.expired_at IS NOT NULL THEN RAISE ...`). That is the only difference
(`diff` of the two blobs). Same file name, different content: see conflicts.

GRANTS (`store/migrate.py:55` on the branch), the only GRANTS change:

```
55	    "spend_reservations": Grant("table", _RW),  # no DELETE: v1 has no pruning (P4d-b)
```

`_RW` is "SELECT, INSERT, UPDATE" (migrate.py, unchanged from main). `"kill_switch": Grant("table", _RW)` stays (:56).

## 3.4 Postgres implementation (`store/postgres.py` on the branch)

The write wrapper: every write method is decorated `@_writes(...)`. One transaction per attempt, first statement sets
`lock_timeout` and `statement_timeout`, whole-call budget, retry on 40001 / 40P01 only (tenacity), driver errors mapped
to Protocol errors. New constructor arguments `lock_timeout_ms=1000`, `call_budget_ms=5000` (also new fields on
`PostgresSettings`, `backends/table.py`, ge=100/le=60000 and ge=500/le=60000). `self._lock` becomes an `RLock` (:303).
New dependency: `tenacity==9.2.1` in the `pg` extra (pyproject.toml), uv.lock updated.

`origin/core/P4d-a2:src/hadavin_sdk/store/postgres.py` lines 239-272:

```
239	def _map_error(exc: psycopg.Error) -> Exception | None:
240	    """Driver error -> Protocol error (the class only, never the driver text: it can carry values). None: let it
241	    through unchanged (connection, schema and privilege errors)."""
242	    E = psycopg.errors
243	    if isinstance(exc, E.UniqueViolation):
244	        return StaleState("conflict: the row already exists")
245	    if isinstance(exc, E.ForeignKeyViolation):
246	        return NotFound("a referenced row does not exist")
247	    if isinstance(
248	        exc, E.CheckViolation | E.NotNullViolation | E.DataError | E.ProgramLimitExceeded
249	    ):
250	        return ValueError(f"the store cannot hold this value ({type(exc).__name__})")
251	    if isinstance(exc, E.LockNotAvailable | E.QueryCanceled):
252	        return StoreBusy(f"the store was busy ({type(exc).__name__})")
253	    if _sqlstate(exc) in _RETRY_SQLSTATES:
254	        return StoreBusy(f"the store was busy ({type(exc).__name__})")
255	    return None
256	
257	
258	def _writes(retry: bool = True):
259	    """Mark a write method: one transaction per attempt whose first statement sets the timeouts, a whole-call
260	    budget, retries on 40001 and 40P01 only (`retry=False`: none, the call raises `StoreBusy` at once), and the
261	    driver errors mapped to Protocol errors. See `PostgresStore._write`."""
262	
263	    def deco(fn):
264	        @functools.wraps(fn)
265	        def wrapper(self, *args, **kwargs):
266	            return self._write(fn, retry, args, kwargs)
267	
268	        wrapper._writes = True  # the scan test reads this
269	        wrapper._retry = retry
270	        return wrapper
271	
272	    return deco
```

`origin/core/P4d-a2:src/hadavin_sdk/store/postgres.py` lines 286-361:

```
286	class PostgresStore:
287	    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
288	    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
289	    def __init__(
290	        self,
291	        conn: psycopg.Connection,
292	        *,
293	        on_retry: Callable[[str, int], None] | None = None,
294	        lock_timeout_ms: int = 1000,
295	        call_budget_ms: int = 5000,
296	    ) -> None:
297	        # Settings ranges are the PostgresSettings ranges (one place): a value outside them is refused, so a
298	        # budget of 0 can never build a store that refuses every write.
299	        self._lock_timeout_ms = _checked_ms("lock_timeout_ms", lock_timeout_ms)
300	        self._call_budget_ms = _checked_ms("call_budget_ms", call_budget_ms)
301	        self._db = conn
302	        # Re-entrant: the write wrapper holds it for a whole transaction and the helpers take it again inside.
303	        self._lock = threading.RLock()
304	        self._on_retry = on_retry
305	        self._deadline: float | None = None  # monotonic; set only by the thread that holds the lock
306	
307	    def _write(self, fn, retry: bool, args: tuple, kwargs: dict):
308	        for a in (*args, *kwargs.values()):
309	            if isinstance(a, BaseModel | dict | str):
310	                check_text(a)
311	        deadline = time.monotonic() + self._call_budget_ms / 1000
312	
313	        def attempt():
314	            with self._lock:
315	                if self._deadline is not None:  # called from inside another wrapped write
316	                    return fn(self, *args, **kwargs)
317	                left = int((deadline - time.monotonic()) * 1000)
318	                if left < 1:
319	                    raise StoreBusy("the call budget was spent")
320	                self._deadline = deadline
321	                try:
322	                    with self._db.transaction():
323	                        self._db.execute(
324	                            "SELECT set_config('lock_timeout', %s, true), "
325	                            "set_config('statement_timeout', %s, true)",
326	                            (str(min(self._lock_timeout_ms, left)), str(left)),
327	                        )
328	                        return fn(self, *args, **kwargs)
329	                finally:
330	                    self._deadline = None
331	
332	        def before_sleep(state: RetryCallState) -> None:
333	            if self._on_retry is not None:
334	                exc = state.outcome.exception()
335	                self._on_retry(_sqlstate(exc) or "", state.attempt_number)
336	
337	        # The sleep happens between attempts, outside the lock and outside any transaction.
338	        retrying = Retrying(
339	            stop=stop_after_attempt(_ATTEMPTS if retry else 1),
340	            wait=wait_exponential_jitter(multiplier=0.02, max=1, exp_base=2, jitter=0.02),
341	            retry=retry_if_exception(lambda e: _sqlstate(e) in _RETRY_SQLSTATES),
342	            before_sleep=before_sleep,
343	            reraise=True,
344	        )
345	        try:
346	            return retrying(attempt)
347	        except psycopg.Error as exc:
348	            mapped = _map_error(exc)
349	            if mapped is None:
350	                raise
351	            raise mapped from None
352	
353	    # --- generic helpers ---------------------------------------------------------------------------------
354	
355	    def _exec(self, query, params=()) -> psycopg.Cursor:
356	        """The one way a method sends SQL. Inside a wrapped write it first compares the monotonic clock with the
357	        call's deadline: a spent budget rolls the transaction back (the raise) and the statement is NOT sent."""
358	        deadline = self._deadline
359	        if deadline is not None and time.monotonic() >= deadline:
360	            raise StoreBusy("the call budget was spent")
361	        return self._db.cursor(row_factory=dict_row).execute(query, params)
```

add_cost (now validated and ceiling-checked):

`origin/core/P4d-a2:src/hadavin_sdk/store/postgres.py` lines 437-448:

```
437	    @_writes(retry=False)
438	    def add_cost(self, run_id: str, usd: Decimal) -> None:
439	        check_usd(usd, max_decimals=8)
440	        with self._lock, self._db.transaction():
441	            row = self._exec(
442	                "UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s RETURNING cost_usd",
443	                (usd, run_id),
444	            ).fetchone()
445	            if row is None:
446	                raise NotFound(run_id)
447	            if row["cost_usd"] > MAX_COUNTER_USD:  # the ValueError rolls the transaction back
448	                raise ValueError("the run counter would pass its ceiling")
```

add_spend, the reservation methods, spend_totals and the kill switch (all SQL in full):

`origin/core/P4d-a2:src/hadavin_sdk/store/postgres.py` lines 595-900:

```
595	    @_writes(retry=False)
596	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
597	        """Day and month counters, each one atomic upsert, in one transaction: exact under concurrency."""
598	        check_usd(usd, max_decimals=8)
599	        check_day(day)
600	        month = day.replace(day=1)
601	        with self._lock, self._db.transaction():
602	            d = self._exec(
603	                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
604	                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd",
605	                (agent_id, day, usd),
606	            ).fetchone()["usd"]
607	            m = self._exec(
608	                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
609	                "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd "
610	                "RETURNING usd",
611	                (agent_id, month, usd),
612	            ).fetchone()["usd"]
613	            if (
614	                d > MAX_COUNTER_USD or m > MAX_COUNTER_USD
615	            ):  # the ValueError rolls both counters back
616	                raise ValueError("a spend counter would pass its ceiling")
617	        return Decimal(d), Decimal(m)
618	
619	    # --- spend reservations (P4d-b) -------------------------------------------------------------------------
620	
621	    @staticmethod
622	    def _reservation(row: dict) -> SpendReservation:
623	        micro = Decimal("1E-6")
624	        for k in ("reserved_usd", "settled_usd"):
625	            if row.get(k) is not None:
626	                row[k] = Decimal(row[k]).quantize(micro)
627	        return SpendReservation.model_validate(row)
628	
629	    def _stored_reservation(self, reservation_id: str) -> SpendReservation | None:
630	        row = self._exec(
631	            "SELECT * FROM spend_reservations WHERE reservation_id = %s", (reservation_id,)
632	        ).fetchone()
633	        return None if row is None else self._reservation(row)
634	
635	    def _cap_failure(self, which: str, table: str, key: dict, cap: Decimal, amount: Decimal):
636	        cols = {"runs": "cost_usd", "spend": "usd", "spend_month": "usd"}
637	        where = sql.SQL(" AND ").join(
638	            sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder(k)) for k in key
639	        )
640	        query = sql.SQL("SELECT {} AS v FROM {} WHERE {}").format(
641	            sql.Identifier(cols[table]), sql.Identifier(table), where
642	        )
643	        cur = self._exec(query, key).fetchone()
644	        return SpendCapExceeded(which, cap, cur["v"] if cur else Decimal(0), amount)
645	
646	    @_writes()
647	    def reserve_spend(
648	        self,
649	        reservation_id: str,
650	        agent_id: str,
651	        day: date,
652	        amount_usd: Decimal,
653	        *,
654	        day_cap: Decimal | None,
655	        month_cap: Decimal | None,
656	        run_id: str | None = None,
657	        run_cap: Decimal | None,
658	        meta: Mapping[str, str | int | bool] | None = None,
659	    ) -> SpendOutcome:
660	        amount, meta_ok = check_reserve(
661	            reservation_id, agent_id, day, amount_usd, day_cap, month_cap, run_id, run_cap, meta
662	        )
663	        month = day.replace(day=1)
664	        with self._lock, self._db.transaction():
665	            if self.get_kill_switch().on:  # the one kill switch read (fails closed)
666	                raise KillSwitchOn("the kill switch is on")
667	            if run_id is not None:
668	                run = self._exec(
669	                    "SELECT agent_id FROM runs WHERE run_id = %s", (run_id,)
670	                ).fetchone()
671	                if run is None:
672	                    raise NotFound(run_id)
673	                if run["agent_id"] != agent_id:
674	                    raise ValueError("the run belongs to another agent")
675	            inserted = self._exec(
676	                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, run_id, "
677	                "reserved_usd, meta) VALUES (%s, 1, %s, %s, %s, %s, %s) "
678	                "ON CONFLICT (reservation_id) DO NOTHING RETURNING *",
679	                (
680	                    reservation_id,
681	                    agent_id,
682	                    day,
683	                    run_id,
684	                    amount,
685	                    None if meta_ok is None else Jsonb(meta_ok),
686	                ),
687	            ).fetchone()
688	            if inserted is None:
689	                stored = self._stored_reservation(reservation_id)
690	                if stored is None:  # the winner rolled back between our insert and our read
691	                    raise StaleState(f"reservation {reservation_id} changed, retry")
692	                same = (
693	                    stored.agent_id == agent_id
694	                    and stored.day == day
695	                    and stored.reserved_usd == amount
696	                    and stored.run_id == run_id
697	                )
698	                if not same:
699	                    raise ReservationConflict(reservation_id)
700	                if stored.status != "open":
701	                    raise StaleState(f"reservation {reservation_id} is {stored.status}")
702	                return SpendOutcome(stored, False)
703	            today = self._exec("SELECT (now() AT TIME ZONE 'UTC')::date AS d").fetchone()["d"]
704	            if abs((day - today).days) > 1:
705	                raise ValueError("day must be within one day of today (UTC)")
706	            self._exec(
707	                "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING",
708	                (agent_id, day),
709	            )
710	            self._exec(
711	                "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, 0) "
712	                "ON CONFLICT DO NOTHING",
713	                (agent_id, month),
714	            )
715	            totals = []
716	            steps = []
717	            if run_id is not None:
718	                steps.append(
719	                    (
720	                        "run",
721	                        "runs",
722	                        (
723	                            "UPDATE runs SET cost_usd = cost_usd + %(amt)s WHERE run_id = %(run_id)s "
724	                            "AND (%(cap)s::numeric IS NULL OR cost_usd + %(amt)s <= %(cap)s) "
725	                            "RETURNING cost_usd AS v"
726	                        ),
727	                        {"run_id": run_id},
728	                        run_cap,
729	                    )
730	                )
731	            steps.append(
732	                (
733	                    "day",
734	                    "spend",
735	                    (
736	                        "UPDATE spend SET usd = usd + %(amt)s WHERE agent_id = %(agent_id)s AND day = %(day)s "
737	                        "AND (%(cap)s::numeric IS NULL OR usd + %(amt)s <= %(cap)s) RETURNING usd AS v"
738	                    ),
739	                    {"agent_id": agent_id, "day": day},
740	                    day_cap,
741	                )
742	            )
743	            steps.append(
744	                (
745	                    "month",
746	                    "spend_month",
747	                    (
748	                        "UPDATE spend_month SET usd = usd + %(amt)s WHERE agent_id = %(agent_id)s "
749	                        "AND month = %(month)s AND (%(cap)s::numeric IS NULL OR usd + %(amt)s <= %(cap)s) "
750	                        "RETURNING usd AS v"
751	                    ),
752	                    {"agent_id": agent_id, "month": month},
753	                    month_cap,
754	                )
755	            )
756	            for which, table, query, key, cap in steps:
757	                got = self._exec(query, {**key, "amt": amount, "cap": cap}).fetchone()
758	                if got is None:  # that counter's cap failed: the whole transaction rolls back
759	                    raise self._cap_failure(which, table, key, cap, amount)
760	                totals.append(got["v"])
761	            if any(t > MAX_COUNTER_USD for t in totals):
762	                raise ValueError("a spend counter would pass its ceiling")
763	            return SpendOutcome(self._reservation(inserted), True)
764	
765	    def _close(self, reservation_id: str, status: str, actual: Decimal | None) -> SpendOutcome:
766	        """Settle or release: the claim is the first write; the counters move in lock order (run, day, month) by
767	        `delta` (positive lowers through a guard in the WHERE clause, negative raises). Zero rows from a counter
768	        means damaged data: everything rolls back, the claim included."""
769	        with self._lock, self._db.transaction():
770	            claim = self._exec(
771	                "UPDATE spend_reservations SET status = %s, settled_usd = %s, closed_at = clock_timestamp() "
772	                "WHERE reservation_id = %s AND status IN ('open', 'expired') RETURNING *",
773	                (status, actual, reservation_id),
774	            ).fetchone()
775	            if claim is None:
776	                stored = self._stored_reservation(reservation_id)
777	                if stored is None:
778	                    raise NotFound(reservation_id)
779	                return SpendOutcome(stored, False)
780	            delta = claim["reserved_usd"] - (0 if actual is None else actual)
781	            targets = []
782	            if claim["run_id"] is not None:
783	                targets.append(
784	                    ("runs", "cost_usd", "run_id = %(run_id)s", {"run_id": claim["run_id"]})
785	                )
786	            targets.append(
787	                (
788	                    "spend",
789	                    "usd",
790	                    "agent_id = %(agent_id)s AND day = %(day)s",
791	                    {"agent_id": claim["agent_id"], "day": claim["day"]},
792	                )
793	            )
794	            targets.append(
795	                (
796	                    "spend_month",
797	                    "usd",
798	                    "agent_id = %(agent_id)s AND month = %(month)s",
799	                    {"agent_id": claim["agent_id"], "month": claim["day"].replace(day=1)},
800	                )
801	            )
802	            for table, col, where, key in targets:
803	                query = sql.SQL(
804	                    "UPDATE {t} SET {c} = {c} - %(delta)s WHERE {w} AND {c} >= %(delta)s RETURNING {c}"
805	                ).format(t=sql.Identifier(table), c=sql.Identifier(col), w=sql.SQL(where))
806	                got = self._exec(query, {**key, "delta": delta}).fetchone()
807	                if got is None:
808	                    _LOG.error(
809	                        "spend counter damaged: %s for reservation %s", table, reservation_id
810	                    )
811	                    raise CounterDamaged(
812	                        f"{table}: a counter is lower than the amount to lower or missing"
813	                    )
814	            return SpendOutcome(self._reservation(claim), True)
815	
816	    @_writes()
817	    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
818	        check_id(reservation_id, "reservation_id")
819	        check_usd(actual_usd, max_decimals=6)
820	        return self._close(reservation_id, "settled", actual_usd.quantize(Decimal("1E-6")))
821	
822	    @_writes()
823	    def release_spend(self, reservation_id: str) -> SpendOutcome:
824	        check_id(reservation_id, "reservation_id")
825	        return self._close(reservation_id, "released", None)
826	
827	    def get_spend_reservation(self, reservation_id: str) -> SpendReservation:
828	        with self._lock:
829	            found = self._stored_reservation(reservation_id)
830	        if found is None:
831	            raise NotFound(reservation_id)
832	        return found
833	
834	    def list_open_reservations(
835	        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
836	    ) -> list[SpendReservation]:
837	        check_int(limit, 1, 1000)
838	        with self._lock:
839	            rows = self._exec(
840	                "SELECT * FROM spend_reservations WHERE status = 'open' "
841	                "AND (%(a)s::text IS NULL OR agent_id = %(a)s) AND (%(r)s::text IS NULL OR run_id = %(r)s) "
842	                "ORDER BY created_at, reservation_id LIMIT %(n)s",
843	                {"a": agent_id, "r": run_id, "n": limit},
844	            ).fetchall()
845	        return [self._reservation(r) for r in rows]
846	
847	    @_writes()
848	    def sweep_spend_reservations(
849	        self, older_than_s: int, *, limit: int = 100
850	    ) -> list[SpendReservation]:
851	        check_int(older_than_s, MIN_SWEEP_AGE_S, 10**7)
852	        check_int(limit, 1, 1000)
853	        with self._lock, self._db.transaction():
854	            # ONE statement: the rows another transaction holds are skipped, the rest expire together
855	            rows = self._exec(
856	                "UPDATE spend_reservations SET status = 'expired', settled_usd = reserved_usd, "
857	                "closed_at = clock_timestamp(), expired_at = clock_timestamp() "
858	                "WHERE reservation_id IN (SELECT reservation_id FROM spend_reservations "
859	                "WHERE status = 'open' AND clock_timestamp() - created_at > make_interval(secs => %s) "
860	                "ORDER BY created_at, reservation_id LIMIT %s FOR UPDATE SKIP LOCKED) "
861	                "AND status = 'open' RETURNING *",
862	                (older_than_s, limit),
863	            ).fetchall()
864	            out = [self._reservation(r) for r in rows]
865	            out.sort(key=lambda r: (r.created_at, r.reservation_id))  # RETURNING has no order
866	            return out
867	
868	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
869	        with self._lock:
870	            d = self._exec(
871	                "SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent_id, day)
872	            ).fetchone()
873	            m = self._exec(
874	                "SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",
875	                (agent_id, day.replace(day=1)),
876	            ).fetchone()
877	        return (Decimal(d["usd"]) if d else Decimal(0)), (Decimal(m["usd"]) if m else Decimal(0))
878	
879	    def get_kill_switch(self) -> KillSwitch:
880	        found = self._select(KillSwitch, "kill_switch", "id = 1", ())
881	        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
882	            _LOG.error(
883	                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
884	            )
885	            return KillSwitch(on=True, by="system:kill_switch_row_missing")
886	        return found[0]
887	
888	    @_writes()
889	    def set_kill_switch(self, ks: KillSwitch) -> None:
890	        row = {"id": 1, **_row(ks)}
891	        cols = [sql.Identifier(c) for c in row]
892	        query = sql.SQL(
893	            "INSERT INTO kill_switch ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}"
894	        ).format(
895	            sql.SQL(", ").join(cols),
896	            sql.SQL(", ").join(sql.Placeholder() * len(row)),
897	            sql.SQL(", ").join(sql.SQL("{0} = EXCLUDED.{0}").format(c) for c in cols[1:]),
898	        )
899	        with self._lock:
900	            self._exec(query, list(row.values()))
```

What the SQL above gives under concurrency (read from the code, tests named in 3.6):

- Cap check and booking are ONE statement per counter (`UPDATE ... SET usd = usd + amt WHERE ... AND usd + amt <= cap
  RETURNING`, :723-750). The row lock of that UPDATE serialises callers on the same counter; a caller that waited
  re-evaluates the WHERE against the committed value. No SELECT-then-UPDATE gap.
- Counter rows are created first with `INSERT ... VALUES (..., 0) ON CONFLICT DO NOTHING` (:706-714) so the UPDATE
  always has a row to lock.
- Lock order is run, day, month in reserve (:717-755) and in settle/release (:781-801).
- Idempotence: `INSERT ... ON CONFLICT (reservation_id) DO NOTHING RETURNING *` (:675-687). Same id and same content
  (agent, day, amount, run) returns the open row with `applied=False` (:702); different content is
  `ReservationConflict` (:699); a closed row is `StaleState` (:701). `meta` is not part of the "same content" test.
- Kill switch: read once inside the transaction with a plain SELECT, no row lock (:665, `get_kill_switch` :879-886).
  A stop that commits after that read does not stop this reserve.
- `day` must be within one day of the DATABASE's UTC date (:703-705).
- Settle: the claim is `UPDATE ... WHERE reservation_id = %s AND status IN ('open','expired') RETURNING *` (:770-774);
  the loser of a race gets the stored row with `applied=False` (:775-779). `delta = reserved - actual`; the counters
  move by `- delta` with guard `col >= delta` (:803-805). A negative delta (actual above reserved) raises the
  counters and is never refused by a cap or by `MAX_COUNTER_USD`.
- Sweep: one statement, `FOR UPDATE SKIP LOCKED`, oldest first, sets `status='expired', settled_usd=reserved_usd,
  closed_at, expired_at` and touches no counter (:855-863).

## 3.5 Memory implementation (`store/memory.py` on the branch)

One plain `threading.Lock` covers the cap check and the write. Constructor gains `clock` and a test hook `_checkpoint`.

`origin/core/P4d-a2:src/hadavin_sdk/store/memory.py` lines 49-60:

```
49	class MemoryStore:
50	    def __init__(
51	        self,
52	        *,
53	        clock: Callable[[], datetime] | None = None,
54	        _checkpoint: Callable[[str], None] | None = None,
55	    ) -> None:
56	        """`clock` is an aware UTC wall clock (default `models.now`); it supplies the times and the UTC date of the
57	        reservations. `_checkpoint` is a test-only hook called at named points inside a write."""
58	        self._clock = clock or now
59	        self._checkpoint = _checkpoint or (lambda name: None)
60	        self._res: dict[str, SpendReservation] = {}
```

`origin/core/P4d-a2:src/hadavin_sdk/store/memory.py` lines 109-120:

```
109	    def add_cost(self, run_id: str, usd: Decimal) -> None:
110	        check_usd(usd, max_decimals=8)
111	        with self._lock:
112	            run = self._runs.get(run_id)
113	            if run is None:
114	                raise NotFound(run_id)
115	            total = (
116	                run.cost_usd + usd
117	            )  # first the new total, then the ceiling, and only then the change
118	            if total > MAX_COUNTER_USD:
119	                raise ValueError("the run counter would pass its ceiling")
120	            self._runs[run_id] = run.model_copy(update={"cost_usd": total})
```

`origin/core/P4d-a2:src/hadavin_sdk/store/memory.py` lines 263-466:

```
263	    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
264	        check_usd(usd, max_decimals=8)
265	        check_day(day)
266	        with self._lock:
267	            new_day = self._spend.get((agent_id, day), Decimal(0)) + usd
268	            new_month = self._month_total(agent_id, day) + usd
269	            if new_day > MAX_COUNTER_USD or new_month > MAX_COUNTER_USD:
270	                raise ValueError("a spend counter would pass its ceiling")
271	            self._spend[(agent_id, day)] = new_day
272	            return new_day, new_month
273	
274	    # --- spend reservations (P4d-b) -------------------------------------------------------------------------
275	
276	    def reserve_spend(
277	        self,
278	        reservation_id: str,
279	        agent_id: str,
280	        day: date,
281	        amount_usd: Decimal,
282	        *,
283	        day_cap: Decimal | None,
284	        month_cap: Decimal | None,
285	        run_id: str | None = None,
286	        run_cap: Decimal | None,
287	        meta: Mapping[str, str | int | bool] | None = None,
288	    ) -> SpendOutcome:
289	        amount, meta_ok = check_reserve(
290	            reservation_id, agent_id, day, amount_usd, day_cap, month_cap, run_id, run_cap, meta
291	        )
292	        with self._lock:
293	            if self._kill_on().on:
294	                raise KillSwitchOn("the kill switch is on")
295	            run = None
296	            if run_id is not None:
297	                run = self._runs.get(run_id)
298	                if run is None:
299	                    raise NotFound(run_id)
300	                if run.agent_id != agent_id:
301	                    raise ValueError("the run belongs to another agent")
302	            stored = self._res.get(reservation_id)
303	            if stored is not None:
304	                same = (
305	                    stored.agent_id == agent_id
306	                    and stored.day == day
307	                    and stored.reserved_usd == amount
308	                    and stored.run_id == run_id
309	                )
310	                if not same:
311	                    raise ReservationConflict(reservation_id)
312	                if stored.status != "open":
313	                    raise StaleState(f"reservation {reservation_id} is {stored.status}")
314	                return SpendOutcome(stored.model_copy(deep=True), False)
315	            stamp = self._clock()
316	            if abs((day - stamp.date()).days) > 1:
317	                raise ValueError("day must be within one day of today (UTC)")
318	            new_run = None if run is None else run.cost_usd + amount
319	            new_day = self._spend.get((agent_id, day), Decimal(0)) + amount
320	            new_month = self._month_total(agent_id, day) + amount
321	            for which, cap, new, cur in (
322	                ("run", run_cap, new_run, None if run is None else run.cost_usd),
323	                ("day", day_cap, new_day, new_day - amount),
324	                ("month", month_cap, new_month, new_month - amount),
325	            ):
326	                if cap is not None and new is not None and new > cap:
327	                    raise SpendCapExceeded(which, cap, cur, amount)
328	            if any(n is not None and n > MAX_COUNTER_USD for n in (new_run, new_day, new_month)):
329	                raise ValueError("a spend counter would pass its ceiling")
330	            # built BEFORE any counter moves: a failure here leaves nothing half-booked
331	            row = SpendReservation(
332	                reservation_id=reservation_id,
333	                agent_id=agent_id,
334	                day=day,
335	                run_id=run_id,
336	                reserved_usd=amount,
337	                created_at=stamp,
338	                meta=dict(meta_ok) if meta_ok is not None else None,
339	            )
340	            self._checkpoint("reserve:before_counters")
341	            if run is not None:
342	                self._runs[run_id] = run.model_copy(update={"cost_usd": new_run})
343	            self._spend[(agent_id, day)] = new_day
344	            self._res[reservation_id] = row
345	            return SpendOutcome(row.model_copy(deep=True), True)
346	
347	    def _close(self, reservation_id: str, status: str, actual: Decimal | None) -> SpendOutcome:
348	        """Settle or release under the lock: every damaged-counter check BEFORE the first change."""
349	        row = self._res.get(reservation_id)
350	        if row is None:
351	            raise NotFound(reservation_id)
352	        if row.status in ("settled", "released"):
353	            return SpendOutcome(row.model_copy(deep=True), False)
354	        # positive lowers the counters, negative raises them (a settle above the reservation books the excess)
355	        delta = row.reserved_usd if actual is None else row.reserved_usd - actual
356	        run = None
357	        if row.run_id is not None:
358	            run = self._runs.get(row.run_id)
359	            if run is None:
360	                raise CounterDamaged(f"run {row.run_id} is missing")
361	        key = (row.agent_id, row.day)
362	        if key not in self._spend:
363	            raise CounterDamaged("the day counter is missing")
364	        month = self._month_total(row.agent_id, row.day)
365	        if delta > 0 and (
366	            (run is not None and run.cost_usd < delta) or self._spend[key] < delta or month < delta
367	        ):
368	            raise CounterDamaged("a counter is lower than the amount to lower")
369	        if run is not None:
370	            self._runs[row.run_id] = run.model_copy(update={"cost_usd": run.cost_usd - delta})
371	        self._spend[key] -= delta
372	        done = row.model_copy(
373	            update={
374	                "status": status,
375	                "settled_usd": actual if status == "settled" else None,
376	                "closed_at": self._clock(),
377	            }
378	        )
379	        self._res[reservation_id] = done
380	        return SpendOutcome(done.model_copy(deep=True), True)
381	
382	    def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendOutcome:
383	        check_id(reservation_id, "reservation_id")
384	        check_usd(actual_usd, max_decimals=6)
385	        with self._lock:
386	            return self._close(reservation_id, "settled", actual_usd.quantize(_MICRO))
387	
388	    def release_spend(self, reservation_id: str) -> SpendOutcome:
389	        check_id(reservation_id, "reservation_id")
390	        with self._lock:
391	            return self._close(reservation_id, "released", None)
392	
393	    def get_spend_reservation(self, reservation_id: str) -> SpendReservation:
394	        with self._lock:
395	            return self._get(self._res, reservation_id)
396	
397	    def list_open_reservations(
398	        self, agent_id: str | None = None, run_id: str | None = None, limit: int = 100
399	    ) -> list[SpendReservation]:
400	        check_int(limit, 1, 1000)
401	        with self._lock:
402	            rows = sorted(
403	                (
404	                    r
405	                    for r in self._res.values()
406	                    if r.status == "open"
407	                    and (agent_id is None or r.agent_id == agent_id)
408	                    and (run_id is None or r.run_id == run_id)
409	                ),
410	                key=lambda r: (r.created_at, r.reservation_id),
411	            )
412	            return [r.model_copy(deep=True) for r in rows[:limit]]
413	
414	    def sweep_spend_reservations(
415	        self, older_than_s: int, *, limit: int = 100
416	    ) -> list[SpendReservation]:
417	        check_int(older_than_s, MIN_SWEEP_AGE_S, 10**7)
418	        check_int(limit, 1, 1000)
419	        with self._lock:
420	            stamp = self._clock()
421	            old = sorted(
422	                (
423	                    r
424	                    for r in self._res.values()
425	                    if r.status == "open" and (stamp - r.created_at).total_seconds() > older_than_s
426	                ),
427	                key=lambda r: (r.created_at, r.reservation_id),
428	            )[:limit]
429	            out = []
430	            for r in old:
431	                done = r.model_copy(
432	                    update={
433	                        "status": "expired",
434	                        "settled_usd": r.reserved_usd,
435	                        "closed_at": stamp,
436	                        "expired_at": stamp,
437	                    }
438	                )
439	                self._res[r.reservation_id] = done
440	                out.append(done.model_copy(deep=True))
441	            return out
442	
443	    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
444	        with self._lock:
445	            month = sum(
446	                (
447	                    v
448	                    for (a, d), v in self._spend.items()
449	                    if a == agent_id and (d.year, d.month) == (day.year, day.month)
450	                ),
451	                Decimal(0),
452	            )
453	            return self._spend.get((agent_id, day), Decimal(0)), month
454	
455	    def _kill_on(self) -> KillSwitch:
456	        """The ONE read of the kill switch (the caller holds `self._lock`, a plain lock: this does not take it)."""
457	        return self._kill.model_copy(deep=True)
458	
459	    def get_kill_switch(self) -> KillSwitch:
460	        with self._lock:
461	            return self._kill_on()
462	
463	    def set_kill_switch(self, ks: KillSwitch) -> None:
464	        check_text(ks)
465	        with self._lock:
466	            self._kill = ks.model_copy(deep=True)
```

Note a memory/Postgres difference read from the code: memory `_close` treats `settled` and `released` as closed and
lets an `expired` row through (:352); memory checks the kill switch BEFORE the replay lookup (:293 then :302), the same
order as Postgres (:665 then :675).

## 3.6 Other source changes on P4d-a2

- `config.py:70-84` on the branch: `Route._price` field validator for `input_usd_per_mtok` and
  `output_usd_per_mtok` (finite, not negative, at most `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK`, at most 6 decimals).
  `Money` (:56) and the two fields (:66-67) are unchanged. No new price field (no cache price, no price table).
- `defaults.py` (appended block): `MAX_USD = 10**12`, `MAX_ROUTE_PRICE_USD_PER_MTOK = 10**6`,
  `STORE_PURGE_BATCH_ROWS = 1000`, `STORE_PURGE_MIN_LEFT_MS = 250`.
- `models.py:28` `round_cost_up(x)`: rounds a cost UP to 8 decimals, refuses non-Decimal, non-finite, negative, above
  MAX_USD. `Reply.cost_usd` and `Verdict.cost_usd` get a validator that calls it (:313-, :329-).
- `llm/common.py:152` `price_cost(route, tokens_in, tokens_out)`: the one cost formula, rounded up; `reply()` (:166)
  and `llm/fake.py` call it. On this branch missing usage is STILL estimated (`estimate_tokens`, :59).
- limits.py: NOT changed (51 lines, same as main). k1b Budget: NOT changed. runtime/agent_loop.py: NOT changed.
  Nothing under src/ calls `reserve_spend`, `settle_spend`, `release_spend` or `sweep_spend_reservations` on this
  branch (grep over src/ of the branch: only the two stores and the protocol).

## 3.7 New tests on P4d-a2 (names read; bodies read only where quoted)

- `tests/contracts/test_store_reserve.py` (30 tests, both store kinds through the `store` fixture). Proves: reserve books
  the three counters (:72); caps are keyword-only (:93); cap exact at the boundary, one micro-dollar over refused
  (:98, :108); first failing cap named in order run, day, month (:119); validation first, nothing changed (:136);
  kill switch refuses a new reserve and a replay but not settle or release (:201); run must exist and belong to the
  agent (:217); replay / conflict / closed replay (:237); settle below, equal, above and replays (:255); release gives
  back all (:305); sweep expires old open rows without moving counters and an expired row settles once (:327); expired
  row can be released, young row not swept (:353); damaged counter (:388, :411, :677); ceiling (:424, :522, :553, :588,
  :609); `test_a_concurrent_pair_cannot_pass_the_cap` (:445, 8 threads over `store_pair` = 2 connections on Postgres,
  cap 3, expects exactly 3 ok and 5 refused); day within one day of the store date (:477); 10,000 reserve/settle pairs
  equal the exact sum (:719); a model test against a plain Python ledger (:771); memory lock covers check and write (:926).
- `tests/contracts/test_store_reserve_proofs_pg.py` (32 tests, Postgres only). Connections: fixture `make` (:42-54)
  opens ONE NEW runtime-login connection per call (`drv.connect_runtime(dsn)`) and wraps it in a `PostgresStore` with
  60 s timeouts; `_in_parallel` (:286-297) runs each job on its own thread behind a `threading.Barrier`. Rows:
  lock order (:160, :176, :444, :474, :497); kill switch read takes no row lock (:264); 8 stores same id booked once
  (:300, and x50 at :859); 8 stores settling one reservation with different amounts book one (:313, x50 at :579);
  mixed load no deadlock and exact (:338, :603); held counter row gives StoreBusy and books nothing (:365, :923);
  `test_n_handles_reserving_against_a_cap_grant_exactly_floor_of_cap_over_amount` (:540: 12 connections, amount 1.5,
  cap 7, expects 4 granted, 8 refused, totals 6.0, zero retries); process rows with `multiprocessing` spawn
  (:700 `test_eight_processes_reserve_against_one_cap_and_the_count_is_exact`: 8 processes x 6 attempts, cap 10,
  amount 1, expects 10 granted, 38 refused, 5.0 after settling at half; workers in
  `tests/contracts/reserve_workers.py:41-60`, each builds its own store from the DSN); killed worker rows (:731, :761);
  database clock (:795); fill-the-cap re-check after a wait (:990, :1030); sweep order and SKIP LOCKED (:1084, :1106).
  Largest concurrency proven: 12 connections in threads, 8 in processes. NOT 50.
- `tests/contracts/test_store_reserve_pg.py` (11): triggers and grants as the runtime login (no DELETE, transition
  matrix, frozen columns), first statement of the migration is the lock timeout.
- `tests/contracts/test_store_reserve_schema_pg.py` (4): new code against a database without the table or the grant
  fails loudly and books nothing.
- `tests/contracts/test_store_writes_pg.py` (32): the write wrapper (error mapping, retry, timeouts, budget, RLock).
- `tests/contracts/test_memory_lone_caller.py` (4): no reservation method of the memory store self-deadlocks.
- `tests/contracts/test_store_hostile.py` (9): plan_id reuse, tick step grammar, list_approvals order, hostile values.
- `tests/contracts/test_store_money_edges.py` (7): `add_spend` / `add_cost` edge table and the validators.
- `tests/contracts/test_cost_rounding.py` (14): cost rounded UP to 8 decimals at the model and both producers.
- `tests/test_route_prices.py` (5): route price checked at config load.
- `tests/test_p4d_missing_methods.py` (2): an old custom store without the six methods is refused with their names.
- Helpers: `tests/contracts/pg_owner.py` (owner-only fixture to age a reservation by switching one trigger off),
  `tests/contracts/reserve_workers.py`, `tests/contracts/store_support.py`, plus the P4d-a1 harness files.

---------------------------------------------------------------------------------------------------------------

# Part 4. origin/core/P4b1 (PR 79), head 8cc2021: the meter (pre-call reserve, settle on exit)

```
 CHANGELOG.md                                       |   3 +
 src/hadavin_sdk/config.py                          |  26 +-
 src/hadavin_sdk/defaults.py                        |  19 +
 src/hadavin_sdk/limits.py                          |  71 +-
 src/hadavin_sdk/llm/common.py                      |  22 +-
 src/hadavin_sdk/llm/fake.py                        |  13 +-
 src/hadavin_sdk/meter.py                           | 434 ++++++++++++
 src/hadavin_sdk/models.py                          |  55 +-
 src/hadavin_sdk/money.py                           | 112 +++
 src/hadavin_sdk/store/memory.py                    | 234 ++++++-
 src/hadavin_sdk/store/migrate.py                   |   1 +
 .../store/migrations/0006_spend_reservations.sql   |  67 ++
 src/hadavin_sdk/store/postgres.py                  | 292 +++++++-
 src/hadavin_sdk/store/protocol.py                  | 183 ++++-
 tests/contracts/conftest.py                        | 107 ++-
 tests/contracts/kinds/__init__.py                  |  29 +
 tests/contracts/kinds/builtin.py                   |   7 +
 tests/contracts/kinds/store_postgres.py            | 174 ++++-
 tests/contracts/store_support.py                   | 136 ++++
 tests/contracts/test_cost_rounding.py              | 147 ++++
 tests/contracts/test_meter.py                      | 125 ++++
 tests/contracts/test_meter_limits.py               | 416 +++++++++++
 tests/contracts/test_pg_driver.py                  | 150 ++++
 tests/contracts/test_store.py                      |  96 +++
 tests/contracts/test_store_money_edges.py          | 207 ++++++
 tests/contracts/test_store_registry.py             | 322 +++++++++
 tests/contracts/test_store_reserve.py              | 481 +++++++++++++
 tests/contracts/test_store_reserve_pg.py           | 164 +++++
 tests/meter_support.py                             |  81 +++
 tests/test_k5_fixes2.py                            |  14 +-
 tests/test_meter_no_db_import.py                   | 130 ++++
 tests/test_meter_parity.py                         | 173 +++++
 tests/test_meter_processes.py                      | 230 ++++++
 tests/test_meter_unit.py                           | 775 +++++++++++++++++++++
 tests/test_money_types.py                          | 164 +++++
 tests/test_p2_postgres.py                          |   6 +-
 tests/test_route_prices.py                         |  59 ++
 37 files changed, 5676 insertions(+), 49 deletions(-)
```

## 4.1 What is new compared with the store branch

Only four source files are P4b1's own work (`git diff 7a84408 origin/core/P4b1 --stat -- src`): `meter.py` (new, 434
lines), `money.py` (new, 112 lines), `limits.py` (+71 -2), `defaults.py` (+13). Everything else in its diff against
main is the c31f336/7a84408 copy of the P4d store work.

Store on P4b1 = the OLD copy. Differences from P4d-a2 head, read from `git diff 7a84408 origin/core/P4d-a2`:
no `@_writes` wrapper, no `StoreBusy` class in protocol.py, plain `Lock` not `RLock`, a private
`_kill_switch_row()` read (`SELECT "on" FROM kill_switch WHERE id = 1`, postgres.py:475-478 on P4b1), the sweep as
SELECT ... FOR UPDATE SKIP LOCKED then one UPDATE per id (postgres.py:695-717 on P4b1), the older 0006 trigger text.
The six Protocol method signatures are the same as on P4d-a2 (protocol.py:252-290 on P4b1). The reserve / settle SQL
of P4b1 was not diffed line by line beyond the hunks named here; the diff shows no other hunk in those methods.
GRANTS: same single line as P4d-a2 (`migrate.py:55`, blob identical to P4d-a2's migrate.py).

## 4.2 src/hadavin_sdk/limits.py on P4b1 (whole file, 118 lines)

`origin/core/P4b1:src/hadavin_sdk/limits.py` lines 1-118:

```
1	"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited."""
2	
3	from __future__ import annotations
4	
5	import contextlib
6	import threading
7	from collections.abc import Callable
8	from decimal import ROUND_DOWN, Decimal, InvalidOperation
9	
10	from hadavin_sdk.audit.protocol import AuditSink
11	from hadavin_sdk.meter import Caps, Hold, Meter, MeterError, Settled, SettleFailure
12	from hadavin_sdk.models import AuditEvent, KillSwitch, now
13	from hadavin_sdk.money import BusinessMoney, SpendMicro
14	from hadavin_sdk.registry import Registry
15	from hadavin_sdk.store.protocol import Store
16	
17	CAP_DECIMALS = 8  # a cap has at most this many decimals (`store.protocol.check_cap`); budgets are rounded DOWN to it
18	
19	
20	class Limits:
21	    def __init__(self, store: Store, audit: AuditSink, registry: Registry) -> None:
22	        self.store, self.audit, self.registry = store, audit, registry
23	        # The meter's two reactions. Plain attributes, read when the meter signals (not when it is built), so a
24	        # caller may set them at any time. Both run in the calling thread, inside the exit of the hold.
25	        self.on_overshoot: Callable[[Settled], None] | None = None
26	        self.on_settle_failed: Callable[[SettleFailure], None] | None = None
27	        self._meter: Meter | None = None
28	        self._meter_lock = threading.Lock()
29	
30	    def charge(self, agent_id: str, usd: Decimal | SpendMicro) -> tuple[Decimal, Decimal]:
31	        if isinstance(usd, BusinessMoney):
32	            raise TypeError("business money is not spend")
33	        if isinstance(usd, SpendMicro):
34	            usd = usd.to_usd()
35	        return self.store.add_spend(agent_id, now().date(), usd)
36	
37	    def caps(self, agent_id: str) -> Caps:
38	        """The caps of one agent from the registry: day and month from its budget, run from `max_run_usd`.
39	        A budget is rounded DOWN to `CAP_DECIMALS` decimals (the store refuses more); an unknown agent is a
40	        `MeterError`."""
41	        agent = self.registry.agents.get(agent_id)
42	        if agent is None:
43	            raise MeterError("unknown agent")
44	
45	        def down(x: Decimal | None) -> Decimal | None:
46	            if x is None:
47	                return None
48	            try:
49	                return x.quantize(Decimal(1).scaleb(-CAP_DECIMALS), rounding=ROUND_DOWN)
50	            except InvalidOperation:
51	                raise MeterError("a budget is not usable") from None
52	
53	        return Caps(
54	            day=down(agent.budget_usd.daily),
55	            month=down(agent.budget_usd.monthly),
56	            run=down(agent.max_run_usd),
57	        )
58	
59	    def _the_meter(self) -> Meter:
60	        if self._meter is None:
61	            with self._meter_lock:
62	                if self._meter is None:  # double-checked: 8 threads on first use make one Meter
63	                    self._meter = Meter(
64	                        self.store,
65	                        clock=lambda: now(),
66	                        on_overshoot=self._signal_overshoot,
67	                        on_settle_failed=self._signal_settle_failed,
68	                    )
69	        return self._meter
70	
71	    def _signal_overshoot(self, settled: Settled) -> None:
72	        callback = self.on_overshoot  # read now, not at build
73	        if callback is not None:
74	            callback(settled)
75	
76	    def _signal_settle_failed(self, failure: SettleFailure) -> None:
77	        callback = self.on_settle_failed
78	        if callback is not None:
79	            callback(failure)
80	
81	    def hold(
82	        self, agent_id: str, worst: SpendMicro, *, run_id: str | None = None
83	    ) -> contextlib.AbstractContextManager[Hold]:
84	        """Reserve `worst` against this agent's caps before a model call; settles on every exit (see `Meter.hold`)."""
85	        return self._the_meter().hold(agent_id, worst, self.caps(agent_id), run_id=run_id)
86	
87	    def blocked(self, agent_id: str) -> list[str]:
88	        reasons = []
89	        if self.store.get_kill_switch().on:
90	            reasons.append("kill_switch")
91	        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
92	        budget = self.registry.agents[agent_id].budget_usd
93	        if day >= budget.daily:
94	            reasons.append("daily_budget")
95	        if month >= budget.monthly:
96	            reasons.append("monthly_budget")
97	        return reasons
98	
99	    @staticmethod
100	    def _event(on: bool, by: str, operation: str) -> AuditEvent:
101	        return AuditEvent(
102	            run_id="-",
103	            domain="limits",
104	            operation=operation,
105	            principal=by,
106	            source="cli",
107	            result="on" if on else "off",
108	        )
109	
110	    def stop(self, by: str) -> None:
111	        """An emergency stop must work when the audit store is down: switch first, then audit (outbox)."""
112	        self.store.set_kill_switch(KillSwitch(on=True, by=by))
113	        self.audit.write_outcome(self._event(True, by, "stop"))
114	
115	    def reset(self, by: str) -> None:
116	        """Removing a safety control is audited first; if that fails, the switch stays on."""
117	        self.audit.write_intent(self._event(False, by, "reset"))
118	        self.store.set_kill_switch(KillSwitch(on=False, by=by))
```

`Limits.charge` (:30-35) and `Limits.blocked` (:87-97) still exist and still work the old way; `Limits.hold` (:81-85) is
the new entry. Because reserve books the counters, `blocked` sees open holds (test `test_t2_2_blocked_reads_an_open_hold`).

## 4.3 src/hadavin_sdk/meter.py on P4b1 (key parts; whole file read)

Module docstring states the scope, including "It has no sweep, no prune and no delete" (:1-9).

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 1-9:

```
1	"""The meter: set the worst-case cost of a model call aside BEFORE the call (reserve), replace it with the real cost
2	AFTER (settle) or give it all back (release), and always settle on the way out of a `with` block.
3	
4	It is a small library class over the `store` kind (P4d's six reservation methods); it imports no database library.
5	The counters are the store's rows (day, month, run), the same rows `Limits.charge` and `Limits.blocked` use, so
6	there is one counter. Everything the meter raises on the way to a model call is a `MeterError`, and any exception
7	from `reserve` means the model is NOT called (fail closed). A settle for one reservation id changes the books once;
8	asking again returns the first result. The meter only SIGNALS an overshoot (the real cost passed the reservation);
9	the reaction belongs to the caller. It has no sweep, no prune and no delete."""
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 36-54:

```
36	# Closed list of the codes of `MeterUnavailable`.
37	CODES = (
38	    "store_unreachable",
39	    "store_busy",
40	    "store_rejected",
41	    "conflict",
42	    "unknown_run",
43	    "unknown_reservation",
44	    "counter_damaged",
45	)
46	# The reason words `Limits.blocked` prints, by the cap that refused.
47	REASON_BY_WHICH = {"run": "run_budget", "day": "daily_budget", "month": "monthly_budget"}
48	# The store methods the meter needs (a store without them is refused at construction).
49	_NEEDED = (
50	    "reserve_spend",
51	    "settle_spend",
52	    "release_spend",
53	    "get_spend_reservation",
54	)
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 156-170:

```
156	    def record(self, actual: SpendMicro | None, *, measured: bool = True) -> None:
157	        """Plan to settle at `actual` (None: at the reserved worst case). `measured` says the amount is a
158	        measured provider usage: only then can an excess raise `on_overshoot`. The LAST of `record` and
159	        `release` wins."""
160	        if actual is not None and type(actual) is not SpendMicro:
161	            raise TypeError("actual must be a SpendMicro or None")
162	        if actual is not None and actual.micro == 0:
163	            raise ValueError("a settle amount of zero is refused; use release()")
164	        if type(measured) is not bool:
165	            raise TypeError("measured must be a bool")
166	        self._release, self._actual, self._measured = False, actual, measured
167	
168	    def release(self) -> None:
169	        """Plan to give the whole reservation back (the call was never sent)."""
170	        self._release, self._actual, self._measured = True, None, False
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 202-210:

```
202	    def spend_day(self) -> date:
203	        """The UTC budget day: the same expression `Limits.blocked` and `Limits.charge` use."""
204	        return (self._clock if self._clock is not None else models.now)().date()
205	
206	    def orphan_age_s(self) -> int:
207	        """The age (seconds) at which an open hold counts as orphaned: age policy only (the sweep is not here)."""
208	        return max(
209	            METER_ORPHAN_AGE_S, METER_ORPHAN_FACTOR * self.max_hold_s + METER_ORPHAN_MARGIN_S
210	        )
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 233-273:

```
233	    def reserve(
234	        self, agent_id: str, worst: SpendMicro, caps: Caps, *, run_id: str | None = None
235	    ) -> Hold:
236	        """Set `worst` aside. Raises `OverBudget` or `MeterUnavailable` (the model must not be called then);
237	        a bad argument is `TypeError` or `ValueError` before any store call."""
238	        if type(worst) is not SpendMicro:
239	            raise TypeError("worst must be a SpendMicro")
240	        if worst.micro == 0:
241	            raise ValueError("worst must be above zero")
242	        if type(caps) is not Caps:
243	            raise TypeError("caps must be a Caps")
244	        store_protocol.check_id(agent_id, "agent_id")
245	        if run_id is not None:
246	            store_protocol.check_id(run_id, "run_id")
247	        elif caps.run is not None:
248	            raise ValueError("a run cap needs a run_id")
249	        for cap in (caps.day, caps.month, caps.run):
250	            store_protocol.check_cap(cap)
251	        day = self.spend_day()
252	        rid = models.new_id("rsv")
253	        try:
254	            self.store.reserve_spend(
255	                rid,
256	                agent_id,
257	                day,
258	                worst.to_usd(),
259	                day_cap=caps.day,
260	                month_cap=caps.month,
261	                run_id=run_id,
262	                run_cap=caps.run,
263	            )
264	        except BaseException as exc:  # noqa: BLE001 - fail closed: any outcome of the store call is mapped; interrupts are re-raised
265	            raise self._reserve_failure(exc, rid, day) from None
266	        return Hold(
267	            reservation_id=rid,
268	            agent_id=agent_id,
269	            run_id=run_id,
270	            reserved=worst,
271	            day=day,
272	            monotonic=self._mono,
273	        )
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 275-308:

```
275	    def _reserve_failure(self, exc: BaseException, rid: str, day: date) -> BaseException:
276	        """The release table: release when the outcome is unknown to the meter, never when the store answered.
277	        Returns the exception to raise (or re-raises `KeyboardInterrupt` and `SystemExit` unchanged)."""
278	        if isinstance(exc, store_protocol.KillSwitchOn):
279	            return OverBudget(
280	                ("kill_switch",), which=None, cap=None, current=None, requested=None, day=day
281	            )
282	        if isinstance(exc, store_protocol.SpendCapExceeded):
283	            reason = REASON_BY_WHICH.get(exc.which)
284	            if reason is None:
285	                return MeterUnavailable("store_rejected")
286	            return OverBudget(
287	                (reason,),
288	                which=exc.which,
289	                cap=exc.cap,
290	                current=exc.current,
291	                requested=exc.requested,
292	                day=day,
293	            )
294	        code = self._code(exc, reserving=True)
295	        if code in ("conflict", "unknown_run", "counter_damaged", "store_rejected"):
296	            return MeterUnavailable(
297	                code
298	            )  # the store answered and rolled back: nothing of ours is written
299	        # StoreBusy or anything unknown: the outcome is unknown, so give the claim back (best effort)
300	        try:
301	            self.store.release_spend(rid)
302	        except Exception as release_exc:  # noqa: BLE001 - the release is best effort; its own error is logged by class name only
303	            log.warning(
304	                "meter release after an unknown reserve failed: %s", type(release_exc).__name__
305	            )
306	        if isinstance(exc, KeyboardInterrupt | SystemExit):
307	            raise exc
308	        return MeterUnavailable(code)
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 330-343:

```
330	    def settle(self, reservation_id: str, actual: SpendMicro | None) -> Settled:
331	        """Replace the reservation by the real cost `actual` (None: the reserved worst case). IDEMPOTENT: a
332	        second call for the same id, with any amount, returns the first call's result with `applied=False`.
333	        A standalone settle never calls `on_overshoot` (only the exit of `hold` does)."""
334	        store_protocol.check_id(reservation_id, "reservation_id")
335	        if actual is not None and type(actual) is not SpendMicro:
336	            raise TypeError("actual must be a SpendMicro or None")
337	        if actual is not None and actual.micro == 0:
338	            raise ValueError("a settle amount of zero is refused; use release()")
339	        if actual is None:
340	            row = self._call("get_spend_reservation", reservation_id)
341	            actual = SpendMicro.from_usd(row.reserved_usd)
342	        outcome = self._call("settle_spend", reservation_id, actual.to_usd())
343	        settled, reserved = self._settled(outcome)
```

`origin/core/P4b1:src/hadavin_sdk/meter.py` lines 366-405:

```
366	    @contextlib.contextmanager
367	    def hold(
368	        self, agent_id: str, worst: SpendMicro, caps: Caps, *, run_id: str | None = None
369	    ) -> Iterator[Hold]:
370	        """Reserve, run the body, and on EVERY exit (also `KeyboardInterrupt` and `SystemExit`) settle: the last
371	        of `record`/`release` wins; neither settles at the reserved worst case. The body's exception keeps
372	        propagating and an exit failure never replaces it."""
373	        h = self.reserve(agent_id, worst, caps, run_id=run_id)
374	        try:
375	            yield h
376	        finally:
377	            self._exit(h)
378	
379	    def _exit(self, h: Hold) -> None:
380	        age = h.age_s()
381	        if age > self.max_hold_s:
382	            log.warning(
383	                "hold %s stayed open %d seconds (limit %d)",
384	                h.reservation_id,
385	                int(age),
386	                self.max_hold_s,
387	            )
388	        code = "store_unreachable"
389	        for _try in range(METER_SETTLE_RETRIES + 1):  # the SAME settle each time
390	            try:
391	                if h._release:
392	                    h.settled = self.release(h.reservation_id)
393	                else:
394	                    h.settled = self.settle(h.reservation_id, h._actual)
395	            except MeterUnavailable as exc:
396	                code = exc.code
397	                if code != "store_busy":
398	                    break
399	            except Exception:  # noqa: BLE001 - a bad plan or a bug: still never replace the body's exception
400	                code = "store_unreachable"
401	                break
402	            else:
403	                self._signal_overshoot(h)
404	                return
405	        self._failed(h, code)
```

Read from the code above:

- One reservation per `hold` / `reserve` call; the id is generated inside the meter (`models.new_id("rsv")`, :252).
  A caller cannot pass its own id, so a retry of the same chat call after a crash makes a NEW reservation (no
  caller-level idempotence key such as run id + step).
- Exit rule (:366-405): `record(actual)` settles at the actual cost; `release()` gives all back; NEITHER (the body
  raised, timed out, was interrupted) settles at the reserved worst case (`settle(id, None)` reads the row and settles
  at `reserved_usd`, :339-342). So "settle at worst case when abandoned" exists for a process that is still alive.
- A process that dies leaves the row `open` and the counters booked at the worst case. Nothing in the meter sweeps.
  `orphan_age_s()` (:206-210) only computes an age: max(600, 2 * max_hold_s + 5).
- A failed exit settle keeps the reservation open and calls `on_settle_failed` (:418-434); retries the same settle
  `METER_SETTLE_RETRIES = 2` times only for `store_busy` (:389-398). `StoreBusy` is looked up by name at call time
  (:215) because the class does not exist in P4b1's store copy.
- Reserve failure table (:275-308): the store answered (cap, kill switch, conflict, unknown run, damaged, rejected) ->
  no release; outcome unknown -> best-effort `release_spend(rid)`.
- The meter is NOT wired in: no file under src/ on P4b1 calls `Limits.hold` or `Meter.hold` (grep: only limits.py:85
  and meter.py itself). `runtime/agent_loop.py` and `k1b/loop.py` are not in the diff; the five charge sites are as
  on P4b1's merge-base.

## 4.4 src/hadavin_sdk/money.py on P4b1

`SpendMicro` (:20-83): whole micro-dollars as an exact int, `from_usd` (:33-44), `to_usd` (:46-48, exponent exactly
-6), `ceil_cost(numerator, denominator)` (:50-59, rounds up once). `BusinessMoney` (:86-112): minor units and a
currency, no conversion to `SpendMicro`. Whole file read.

## 4.5 defaults.py, config.py, GRANTS, Budget, agent_loop on P4b1

- `defaults.py` meter block (appended after the money block): `METER_MAX_HOLD_S = 300`,
  `METER_MAX_HOLD_LIMIT_S = 3600`, `METER_ORPHAN_AGE_S = 600`, `METER_ORPHAN_FACTOR = 2`,
  `METER_ORPHAN_MARGIN_S = 5`, `METER_SETTLE_RETRIES = 2`, `MICRO_DECIMALS = 6`, `MICRO_PER_USD = 1_000_000`.
  It does NOT have P4d-a2's `STORE_PURGE_*` block.
- `config.py:69-83` on P4b1: the same `Route._price` validator text as P4d-a2. No new price field.
- k1b `Budget`: not changed. `runtime/agent_loop.py`: not changed. Migration: only the old 0006.

## 4.6 New tests on P4b1 (its own; the store tests are older copies of P4d-a2's)

- `tests/test_meter_unit.py` (50): the meter against a scripted store; its docstring says "BLOCKED by P4d-a2-ii: the
  real `StoreBusy` does not exist yet", rows use a local `Busy` class. Bodies not read.
- `tests/test_money_types.py` (8): SpendMicro and BusinessMoney.
- `tests/contracts/test_meter.py` (8, both store kinds): round trip (:29), settle idempotent (:50), exact boundary
  (:59), kill switch (:72), unknown id (:87), settle from a second meter on the second handle (:109), settle above
  reserved books the full actual once (:118).
- `tests/contracts/test_meter_limits.py` (16, both store kinds): the meter and `Limits` share one counter. Includes
  `test_t2_2_blocked_reads_an_open_hold` (:91), `test_t2_8_check_then_spend_race` (:263-270: threads over ONE store
  handle, daily cap 1.00, expects 2 granted and total 0.80), `test_t2_5` kill switch (:146), `test_t2_9` caps rounded
  down (:274), `test_t2_10` eight threads build one meter (:288).
- `tests/test_meter_parity.py` (12): parity rows with Intake's `test_budget.py` (memory). Includes
  `test_p12_p13_every_failure_inside_the_body_settles_at_reserved` (:151) and interrupts (:159).
- `tests/test_meter_processes.py` (4, Postgres only, `multiprocessing` spawn, each worker opens its own store with
  `make("store", PostgresSettings(...))`, :27-29): 8 processes x 6 attempts of 0.05 against cap 1.0 grant exactly 20
  and settle half (:68); a killed process leaves its worst case booked and another process closes it with
  `settle(id, None)` (:112); lost acknowledgement (:168); two processes settle one id once (:210).
- `tests/test_meter_no_db_import.py` (5): the meter imports no database library.
- `tests/meter_support.py`: helper (recording store wrapper, fake clock, run maker). SAME PATH as a different file on
  T1-T2-tests.

---------------------------------------------------------------------------------------------------------------

# Part 5. origin/core/P4a (PR 78), head 4a0976f: refuse instead of estimate, pricing

The task calls this "price table". What the branch holds is `llm/pricing.py` (exact cost from reported usage and the
two route prices). There is NO table of model prices and NO new price field: prices are still the two `Route` fields.

```
 CHANGELOG.md                                       |    3 +
 demos/ask-your-data/askdata/pipeline.py            |    4 +-
 src/hadavin_sdk/app.py                             |   30 +-
 src/hadavin_sdk/audit/labelkey.py                  |   42 +
 src/hadavin_sdk/backends/table.py                  |    9 +-
 src/hadavin_sdk/cli.py                             |  190 +++-
 src/hadavin_sdk/config.py                          |   79 +-
 src/hadavin_sdk/defaults.py                        |   41 +
 src/hadavin_sdk/k1b/loop.py                        |   54 +-
 src/hadavin_sdk/k1b/replay.py                      |   22 +-
 src/hadavin_sdk/limits.py                          |  160 ++-
 src/hadavin_sdk/llm/__init__.py                    |   18 +-
 src/hadavin_sdk/llm/anthropic.py                   |   36 +-
 src/hadavin_sdk/llm/bedrock.py                     |   18 +-
 src/hadavin_sdk/llm/common.py                      |   57 +-
 src/hadavin_sdk/llm/fake.py                        |   25 +-
 src/hadavin_sdk/llm/gemini.py                      |   47 +-
 src/hadavin_sdk/llm/openai_compat.py               |   46 +-
 src/hadavin_sdk/llm/pricing.py                     |   74 ++
 src/hadavin_sdk/llm/protocol.py                    |   93 +-
 src/hadavin_sdk/models.py                          |   94 +-
 src/hadavin_sdk/runtime/agent_loop.py              |   11 +-
 src/hadavin_sdk/store/memory.py                    |  287 +++++-
 src/hadavin_sdk/store/migrate.py                   |  270 ++++-
 .../store/migrations/0006_spend_reservations.sql   |   67 ++
 .../store/migrations/0007_kill_switch_guard.sql    |   82 ++
 src/hadavin_sdk/store/postgres.py                  |  368 ++++++-
 src/hadavin_sdk/store/protocol.py                  |  218 +++-
 tests/conftest.py                                  |   17 +
 tests/contracts/conftest.py                        |  107 +-
 tests/contracts/kinds/__init__.py                  |   29 +
 tests/contracts/kinds/builtin.py                   |    7 +
 tests/contracts/kinds/llm_wire.py                  |  118 ++-
 tests/contracts/kinds/store_postgres.py            |  209 +++-
 tests/contracts/store_support.py                   |  136 +++
 tests/contracts/test_cost_rounding.py              |  145 +++
 tests/contracts/test_llm.py                        |   35 +
 tests/contracts/test_pg_driver.py                  |  150 +++
 tests/contracts/test_store.py                      |  123 ++-
 tests/contracts/test_store_money_edges.py          |  207 ++++
 tests/contracts/test_store_registry.py             |  322 ++++++
 tests/contracts/test_store_reserve.py              |  472 +++++++++
 tests/contracts/test_store_reserve_pg.py           |  145 +++
 tests/demo_askdata/test_usage_missing.py           |   81 ++
 tests/k1b_support.py                               |   11 +
 tests/k5_support.py                                |    2 +-
 tests/stop_state_helpers.py                        |   34 +
 tests/test_cuj.py                                  |   23 +-
 tests/test_k2_migrations.py                        |   36 +-
 tests/test_k3_pilot.py                             |    2 +-
 tests/test_k3_pilot_env.py                         |    4 +
 tests/test_k5_fixes2.py                            |   20 +-
 tests/test_k5_postgres.py                          |    2 +-
 tests/test_k5_round10_postgres.py                  |   11 +-
 tests/test_k5_round5.py                            |    2 +-
 tests/test_k5_round8_postgres.py                   |    1 +
 tests/test_k5_tools.py                             |    4 +-
 tests/test_labelkey.py                             |   73 ++
 tests/test_p2_postgres.py                          |   25 +-
 tests/test_p3b_neutral_audit.py                    |    9 +-
 tests/test_p7_store.py                             |   15 +-
 tests/test_p7_tick.py                              |    2 +-
 tests/test_review_fixes.py                         |    6 +-
 tests/test_review_pr3_round2.py                    |   21 +-
 tests/test_route_prices.py                         |   59 ++
 tests/test_s5_runtime.py                           |   15 +-
 tests/test_stop_state_cli.py                       |  118 +++
 tests/test_stop_state_config.py                    |   53 +
 tests/test_stop_state_db.py                        |  292 ++++++
 tests/test_stop_state_memory.py                    |  146 +++
 tests/test_usage_classes.py                        |  914 +++++++++++++++++
 tests/test_usage_refuse.py                         | 1078 ++++++++++++++++++++
 tests/warden_port/test_audit_chain.py              |    3 +-
 tests/warden_port/test_providers.py                |   13 +-
 74 files changed, 7494 insertions(+), 248 deletions(-)
```

The diff is large because the branch also carries (a) the old c31f336 copy of the P4d store work and (b) a merge of
core/P2a-1 (kill switch stop state: cli.py, app.py, audit/labelkey.py, migrate.py, migration 0007, the `test_stop_state_*`
tests). (b) is not P4a's own work but it is in the diff and it changes the kill switch contract.

## 5.1 Store Protocol on P4a (`store/protocol.py`)

Spend methods (:265-310): same six reservation methods as the c31f336 copy; `StoreBusy` is absent.
Kill switch methods are CHANGED:

`origin/core/P4a:src/hadavin_sdk/store/protocol.py` lines 178-196:

```
178	class ResetRefused(RuntimeError):
179	    """The database refused a reset: the caller is not in the reset group or has no registered label (HD001)."""
180	
181	
182	class StaleCount(RuntimeError):
183	    """The version or the open-request count changed since the operator read it, or there was nothing to clear
184	    (HD003)."""
185	
186	
187	class LabelRefused(ValueError):
188	    """A name that is not a keyed label (HD004). Raised by the memory store too."""
189	
190	
191	class SwitchRowMissing(RuntimeError):
192	    """The kill_switch row is missing (HD005): a database administrator must re-seed it."""
193	
194	
195	class NotMigrated(RuntimeError):
196	    """The stop or reset function does not exist (SQLSTATE 42883): the database is not migrated."""
```

`origin/core/P4a:src/hadavin_sdk/store/protocol.py` lines 313-325:

```
313	    def get_kill_switch(self) -> StopState:
314	        """A missing or unreadable switch row reads as ON (fail closed)."""
315	        ...
316	
317	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
318	        """A STOP: only `ks.on` true is accepted (anything else raises ValueError) and `ks.by` must be a keyed
319	        label (`LabelRefused`). Each call is its own open stop request; nothing is overwritten."""
320	        ...
321	
322	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
323	        """Clear exactly the stops that the pair (version, open count) named when the operator read it.
324	        `StaleCount` when either changed or there was nothing to clear."""
325	        ...
```

Postgres (kill switch read used by reserve_spend, and the three methods):

`origin/core/P4a:src/hadavin_sdk/store/postgres.py` lines 496-500:

```
496	    def _kill_switch_row(self) -> bool:
497	        """True when the switch is on (the flag OR any open stop request) or its row is missing (fail closed). Reads
498	        the one state view; a plain SELECT, no locking clause."""
499	        row = self._exec('SELECT "on" FROM kill_switch_state').fetchone()
500	        return True if row is None else bool(row["on"])
```

`origin/core/P4a:src/hadavin_sdk/store/postgres.py` lines 752-796:

```
752	    def get_kill_switch(self) -> StopState:
753	        found = self._select(StopState, "kill_switch_state", "true", ())
754	        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
755	            _LOG.error(
756	                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
757	            )
758	            return StopState(on=True, by="system:kill_switch_row_missing")
759	        return found[0]
760	
761	    # Two whole statements (no string building). The casts matter: a bigint argument does not resolve to the
762	    # (text, bigint, integer) signature.
763	    _STOP_QUERY = (
764	        'SELECT "on", "by", ts, schema_version, version, open_requests '
765	        "FROM hadavin_kill_switch_stop(%s)"
766	    )
767	    _RESET_QUERY = (
768	        'SELECT "on", "by", ts, schema_version, version, open_requests '
769	        "FROM hadavin_kill_switch_reset(%s, %s::bigint, %s::int)"
770	    )
771	
772	    def _call_switch(self, query: str, params: tuple) -> StopState:
773	        """Run one of the two kill-switch functions and map its SQLSTATE to a typed error (never by message
774	        text). The functions run as their owner; the caller needs EXECUTE only."""
775	        try:
776	            with self._lock:
777	                row = self._exec(query, params).fetchone()
778	        except psycopg.Error as exc:
779	            code = getattr(exc, "sqlstate", None)
780	            mapped = _SWITCH_ERRORS.get(code or "")
781	            if mapped is None:
782	                raise
783	            raise mapped(_SWITCH_TEXT.get(code or "", str(code))) from exc
784	        return StopState.model_validate(row)
785	
786	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
787	        """A stop: one INSERT through `hadavin_kill_switch_stop`. The runtime has no right on the tables."""
788	        if ks.on is not True:
789	            raise ValueError("set_kill_switch only stops; a reset goes through reset_kill_switch")
790	        return self._call_switch(self._STOP_QUERY, (ks.by,))
791	
792	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
793	        for n, top in ((expected_version, 2**63 - 1), (expected_open, 2**31 - 1)):
794	            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
795	                raise ValueError("reset: version and open count must be in range")
796	        return self._call_switch(self._RESET_QUERY, (by, expected_version, expected_open))
```

Memory:

`origin/core/P4a:src/hadavin_sdk/store/memory.py` lines 439-479:

```
439	    def _state(self) -> StopState:
440	        """The state view: ON when the flag is on or any request is open; `by`/`ts` from the flag, else from the
441	        earliest open request."""
442	        k, first = self._kill, (self._stops[0] if self._stops else None)
443	        by, ts = (k.by, k.ts) if k.on or first is None else first
444	        return StopState(
445	            on=k.on or first is not None,
446	            by=by,
447	            ts=ts,
448	            version=k.version,
449	            open_requests=len(self._stops),
450	        )
451	
452	    def get_kill_switch(self) -> StopState:
453	        with self._lock:
454	            return self._state()
455	
456	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
457	        if ks.on is not True:
458	            raise ValueError("set_kill_switch only stops; a reset goes through reset_kill_switch")
459	        if not is_label(ks.by):
460	            raise LabelRefused("kill switch: stop label not accepted")
461	        with self._lock:
462	            self._stops.append((ks.by, now()))
463	            return self._state()
464	
465	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
466	        if not is_label(by):
467	            raise LabelRefused("kill switch: name not accepted")
468	        for n, top in ((expected_version, 2**63 - 1), (expected_open, 2**31 - 1)):
469	            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
470	                raise ValueError("reset: version and open count must be in range")
471	        with self._lock:
472	            if self._kill.version != expected_version:
473	                raise StaleCount("kill switch: the version changed")
474	            n = len(self._stops)
475	            if n != expected_open or (n == 0 and not self._kill.on):
476	                raise StaleCount("kill switch: the open count changed")
477	            self._stops.clear()
478	            self._kill = KillSwitch(on=False, by=by, version=self._kill.version + 1)
479	            return self._state()
```

`reserve_spend` on P4a calls `self._kill_switch_row()` at postgres.py:537. The reserve / settle / sweep SQL of P4a's
postgres.py (:519-739) was not read line by line; it is the c31f336 copy (UNVERIFIED beyond the kill switch read).

## 5.2 Migrations on P4a

`0006_spend_reservations.sql`: byte-identical to P4b1's (old text, see 3.3).
`0007_kill_switch_guard.sql` (whole file, from P2a-1):

`origin/core/P4a:src/hadavin_sdk/store/migrations/0007_kill_switch_guard.sql` lines 1-82:

```
1	-- P2a-1: a stop is an INSERT of a new request row; a reset is a function that only a registered login in the
2	-- reset group can complete. The three real functions and the group name are written by `migrate()` on every run
3	-- (they name the schema and the group); this file creates what does not depend on either.
4	-- Lock order everywhere: kill_switch, then kill_switch_stop_requests, then kill_switch_resets.
5	
6	ALTER TABLE kill_switch ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;
7	
8	-- Core stored whatever name the caller typed. A name that is not a keyed label becomes 'unlabelled', so the
9	-- guard never copies typed text (an e-mail address, for example) into the reset record.
10	UPDATE kill_switch SET "by" = 'unlabelled'
11	WHERE "by" IS NOT NULL AND "by" <> 'dba' AND "by" !~ '^id:[A-Za-z0-9_-]{1,32}:[0-9a-f]{32}$';
12	
13	CREATE TABLE kill_switch_stop_requests (
14	    id         BIGSERIAL PRIMARY KEY,
15	    "by"       TEXT NOT NULL,
16	    ts         TIMESTAMPTZ NOT NULL DEFAULT now(),
17	    cleared_by BIGINT
18	);
19	CREATE INDEX kill_switch_stop_requests_open ON kill_switch_stop_requests (id) WHERE cleared_by IS NULL;
20	
21	CREATE TABLE kill_switch_resets (
22	    old_version BIGINT PRIMARY KEY,
23	    reset_at    TIMESTAMPTZ NOT NULL,
24	    login_label TEXT NOT NULL,
25	    old_by      TEXT
26	);
27	
28	CREATE TABLE kill_switch_login_labels (
29	    login_name TEXT PRIMARY KEY,
30	    label      TEXT NOT NULL UNIQUE
31	);
32	
33	-- ONE source for "is the switch on": the flag, or at least one open request.
34	CREATE VIEW kill_switch_state AS
35	SELECT (k."on" OR r.id IS NOT NULL) AS "on",
36	       CASE WHEN k."on" THEN k."by" WHEN r.id IS NOT NULL THEN r."by" ELSE k."by" END AS "by",
37	       CASE WHEN k."on" THEN k.ts   WHEN r.id IS NOT NULL THEN r.ts   ELSE k.ts   END AS ts,
38	       k.schema_version, k.version,
39	       (SELECT count(*) FROM kill_switch_stop_requests WHERE cleared_by IS NULL)::int AS open_requests
40	FROM kill_switch k
41	LEFT JOIN LATERAL (SELECT id, "by", ts FROM kill_switch_stop_requests
42	                   WHERE cleared_by IS NULL ORDER BY id LIMIT 1) r ON true
43	WHERE k.id = 1;
44	
45	-- Placeholder guard: refuses every reset until `migrate()` installs the real text (so a hand-applied file locks
46	-- resets out instead of leaving them open).
47	CREATE OR REPLACE FUNCTION hadavin_kill_switch_guard() RETURNS trigger LANGUAGE plpgsql AS
48	$f$ BEGIN
49	  IF OLD."on" AND NOT NEW."on" THEN
50	    RAISE EXCEPTION 'kill switch: the guard is not installed; run hadavin-sdk migrate' USING ERRCODE = 'HD001';
51	  END IF;
52	  RETURN NEW;
53	END $f$;
54	CREATE OR REPLACE TRIGGER kill_switch_guard BEFORE UPDATE ON kill_switch
55	    FOR EACH ROW EXECUTE FUNCTION hadavin_kill_switch_guard();
56	ALTER TABLE kill_switch ENABLE ALWAYS TRIGGER kill_switch_guard;
57	
58	-- Friction for the owner too: the request table accepts only `cleared_by` going from NULL to a value.
59	CREATE OR REPLACE FUNCTION hadavin_kill_switch_requests_guard() RETURNS trigger LANGUAGE plpgsql AS
60	$f$ BEGIN
61	  IF TG_OP = 'UPDATE' AND OLD.cleared_by IS NULL AND NEW.cleared_by IS NOT NULL
62	     AND NEW.id = OLD.id AND NEW."by" = OLD."by" AND NEW.ts = OLD.ts THEN
63	    RETURN NEW;
64	  END IF;
65	  RAISE EXCEPTION 'the stop request table is append-only';
66	END $f$;
67	CREATE OR REPLACE TRIGGER kill_switch_stop_requests_update BEFORE UPDATE ON kill_switch_stop_requests
68	    FOR EACH ROW EXECUTE FUNCTION hadavin_kill_switch_requests_guard();
69	CREATE OR REPLACE TRIGGER kill_switch_stop_requests_delete BEFORE DELETE ON kill_switch_stop_requests
70	    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
71	CREATE OR REPLACE TRIGGER kill_switch_stop_requests_no_truncate BEFORE TRUNCATE ON kill_switch_stop_requests
72	    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
73	ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_update;
74	ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_delete;
75	ALTER TABLE kill_switch_stop_requests ENABLE ALWAYS TRIGGER kill_switch_stop_requests_no_truncate;
76	
77	CREATE OR REPLACE TRIGGER kill_switch_resets_append_only BEFORE UPDATE OR DELETE ON kill_switch_resets
78	    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
79	CREATE OR REPLACE TRIGGER kill_switch_resets_no_truncate BEFORE TRUNCATE ON kill_switch_resets
80	    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
81	ALTER TABLE kill_switch_resets ENABLE ALWAYS TRIGGER kill_switch_resets_append_only;
82	ALTER TABLE kill_switch_resets ENABLE ALWAYS TRIGGER kill_switch_resets_no_truncate;
```

The stop and reset functions themselves are not in the migration file: `migrate()` writes them on every run from
templates in `store/migrate.py` (`_STOP_FN`, `_RESET_FN`, from about :104 on the branch; first 30 lines of each read,
the rest UNVERIFIED).

## 5.3 GRANTS on P4a (`store/migrate.py`)

`origin/core/P4a:src/hadavin_sdk/store/migrate.py` lines 40-41:

```
40	    reset: str = ""  # privilege list of the reset group (the only role that may clear a stop)
41	    stop: str = ""  # privilege list of the stop login
```

`origin/core/P4a:src/hadavin_sdk/store/migrate.py` lines 57-66:

```
57	    "spend": Grant("table", _RW),
58	    "spend_month": Grant("table", _RW),
59	    "spend_reservations": Grant("table", _RW),  # no DELETE: v1 has no pruning (P4d-b)
60	    # A stop is an INSERT through a function (the owner's rights); no role holds any right on these tables.
61	    "kill_switch": Grant("table", ""),
62	    "kill_switch_stop_requests": Grant("table", ""),
63	    "kill_switch_stop_requests_id_seq": Grant("sequence", ""),
64	    "kill_switch_login_labels": Grant("table", ""),
65	    "kill_switch_resets": Grant("table", "SELECT"),
66	    "kill_switch_state": Grant("view", "SELECT", reset="SELECT", stop="SELECT"),
```

So on P4a the runtime login has NO right on table `kill_switch`; it reads the view `kill_switch_state`. P4d-a2's
`reserve_spend` reads `kill_switch` through `get_kill_switch()` -> `_select(KillSwitch, "kill_switch", "id = 1", ())`
(P4d-a2 postgres.py:880). After P2a-1 that read must go to the view.

## 5.4 limits.py on P4a (183 lines; the meter part is unchanged from main)

`charge` and `blocked` are as on main:

`origin/core/P4a:src/hadavin_sdk/limits.py` lines 52-65:

```
52	class Limits:
53	    def __init__(
54	        self,
55	        store: Store,
56	        audit: AuditSink,
57	        registry: Registry,
58	        *,
59	        environment: str,
60	        stop_store: Store | None = None,
61	        reset_store: Store | None = None,
62	        reset_names: Iterable[str] = frozenset(),
63	        label_key: bytes | None = None,
64	        key_id: str = "k1",
65	    ) -> None:
```

`origin/core/P4a:src/hadavin_sdk/limits.py` lines 85-103:

```
85	    # --- the meter -----------------------------------------------------------------------------------------------
86	
87	    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
88	        return self.store.add_spend(agent_id, now().date(), usd)
89	
90	    def blocked(self, agent_id: str) -> list[str]:
91	        reasons = []
92	        if self.store.get_kill_switch().on:
93	            reasons.append("kill_switch")
94	        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
95	        budget = self.registry.agents[agent_id].budget_usd
96	        if day >= budget.daily:
97	            reasons.append("daily_budget")
98	        if month >= budget.monthly:
99	            reasons.append("monthly_budget")
100	        return reasons
101	
102	    def status(self) -> StopState:
103	        return self.store.get_kill_switch()
```

The rest of the file (:1-51, :105-183, whole file read) is the P2a-1 stop state: `Limits.__init__` now REQUIRES
`environment=` and takes `stop_store`, `reset_store`, `reset_names`, `label_key`, `key_id`; `stop(by)` returns a
`StopState` and writes a keyed label; `reset(by, *, expect_version, expect_open)`. No `hold`, no `caps`, no meter.

## 5.5 config.py, defaults.py, models.py, llm on P4a

- `config.py:72-86`: the same `Route._price` validator as P4d-a2. `Money` (:58) and the fields (:68-69) unchanged.
- `config.py:403-417` NEW `Config._priced_routes_for_real_backends`: a route with a zero input or output price is
  refused unless the llm kind is `fake`.
- `config.py` NEW `LimitsSettings` and `Config.limits` (P2a-1), and a refusal when `store.stop_credential_ref` is
  missing outside dev.
- `defaults.py` blocks: money (same two constants), kill switch (8 constants), `MAX_USAGE_TOKENS_PER_CLASS =
  1_000_000_000`, and `OPENAI_COMPAT_REQUESTS_PER_CHAT = 2`, `CHARGE_FALLBACK_REQUESTS = 2`,
  `CHARGE_FALLBACK_ATTEMPTS = 10`, `PROMPT_BYTES_PER_TOKEN = 1`.
- `models.py`: `round_cost_up` (:29, an older text than P4d-a2's: `isinstance` and a `type: ignore`), `KillSwitch.version`
  and `StopState` (:275-286), `Usage` dataclass (:322-343: input, output, cache_write, cache_read tokens),
  `Reply.usage` property, `SpendReservation` (:389).
- `llm/protocol.py`: `UsageMissing(ProviderError)` with closed reasons, `UnpricedUsage`, `checked_count`,
  `build_usage`, `add_usage`.
- `llm/pricing.py` (new, 74 lines, whole file read): `cost_usd(usage, route)` exact, never rounds; refuses a non-zero
  cache class, a zero input count on a priced route; `check_facts` refuses a `service_tier` / `speed` that is not
  `standard`.
- `llm/common.py:170` `reply(route, *, text, calls, usage, stop, started, facts)`: signature changed (was `tokens=`,
  `sent=`); cost = `round_cost_up(cost_usd(usage, route))`. `price_cost` (P4d-a2 common.py:152) does NOT exist on
  P4a. `request_bound(llm)` (:157) reads `REQUESTS_PER_CHAT`.
- anthropic.py, bedrock.py, gemini.py, openai_compat.py, fake.py changed to build a `Usage` (not read line by line:
  UNVERIFIED in detail).

## 5.6 k1b on P4a

`class Budget` (k1b/loop.py:40-52 on the branch) is NOT changed. The charge sites are:

`origin/core/P4a:src/hadavin_sdk/k1b/loop.py` lines 115-152:

```
115	def worst_case_usd(
116	    route: Route,
117	    system: str,
118	    messages: list[dict[str, str]],
119	    *,
120	    tools: list[dict[str, object]],
121	    requests: int = 1,
122	) -> Decimal:
123	    """The most `requests` requests could cost, rounded UP once. One request's worth: the byte bound of the prompt
124	    (system, messages and tool specs, in UTF-8; one token per byte at most, `PROMPT_BYTES_PER_TOKEN`) at the input
125	    price, plus ``max_tokens`` of output at the output price. Charged when a call's real cost is unknown."""
126	    prompt = (system + _dumps(messages) + _dumps(tools)).encode("utf-8", "surrogatepass")
127	    tokens_in = -(-len(prompt) // defaults.PROMPT_BYTES_PER_TOKEN)
128	    one = (
129	        Decimal(tokens_in) * route.input_usd_per_mtok
130	        + Decimal(route.max_tokens) * route.output_usd_per_mtok
131	    )
132	    return round_cost_up(one * requests / Decimal(1_000_000))
133	
134	
135	def _count_or(value: object, fallback: int) -> int:
136	    return value if type(value) is int and value >= 1 else fallback
137	
138	
139	def _charge_factor(llm: object) -> int:
140	    """How many requests one failed call may have been billed for: the requests of one chat times the attempts.
141	    Total and plain: an object that declares nothing usable is charged the fallbacks, never an error."""
142	    return _count_or(
143	        getattr(llm, "REQUESTS_PER_CHAT", None), defaults.CHARGE_FALLBACK_REQUESTS
144	    ) * _count_or(getattr(llm, "max_attempts", None), defaults.CHARGE_FALLBACK_ATTEMPTS)
145	
146	
147	def _worst_case_of_call(
148	    llm: object, route_prices: Route, system: str, messages: list[dict[str, str]]
149	) -> Decimal:
150	    return worst_case_usd(
151	        route_prices, system, messages, tools=TOOL_SPECS, requests=_charge_factor(llm)
152	    )
```

`origin/core/P4a:src/hadavin_sdk/k1b/loop.py` lines 196-216:

```
196	        except CallTimeout:
197	            # The abandoned call may still be running and billed (a retry layer can re-send), so charge the
198	            # worst case and stop the run: at most one such call per invocation, and the cap still holds.
199	            if route_prices is not None:
200	                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
201	            out.status, out.stop_reason, out.halt = "timeout", "call_timeout", "aborted"
202	            return out
203	        except ProviderExhausted:
204	            # Out of retries: the attempts may all have been billed, so the whole-call maximum is booked.
205	            if route_prices is not None:
206	                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
207	            out.status, out.stop_reason = "error", "provider_exhausted"
208	            return out
209	        except ProviderError:
210	            # Every other provider failure (a `UsageMissing` included) may have been billed too: same booking.
211	            if route_prices is not None:
212	                budget.charge(_worst_case_of_call(llm, route_prices, system, messages))
213	            out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
214	            return out
215	        budget.charge(reply.cost_usd)
216	        if reply.stop_reason in ("max_tokens", "refusal"):
```

`origin/core/P4a:src/hadavin_sdk/k1b/loop.py` lines 240-243:

```
240	                shown, ids = render(snap.call(call.name, call.input))
241	                verdict = injection_check(detector, shown, "k1b-tool-result")
242	                budget.charge(verdict.cost_usd)
243	                if verdict.flagged:
```

New on P4a in k1b: `worst_case_usd` takes `tools=` and `requests=` and bounds the prompt by BYTES (one token per byte);
the worst case is now also booked on `ProviderExhausted` and on any other `ProviderError` (so also `UsageMissing`),
times `REQUESTS_PER_CHAT x max_attempts`. `k1b/replay.py` refuses any llm kind but `fake`.
This is the only worst-case-per-call formula on any of the five branches.

## 5.7 runtime/agent_loop.py on P4a

The two charge sites are unchanged in text; on the branch they sit at :317-318 and :443-444 (main: :325-326, :485-486;
main's file has moved since P4a's merge-base).

```
317	            self.limits.charge(run.agent_id, verdict.cost_usd)
318	            self.store.add_cost(run.run_id, verdict.cost_usd)
443	            self.limits.charge(agent_id, reply.cost_usd)
444	            self.store.add_cost(run.run_id, reply.cost_usd)
```

The only agent_loop change: `limits.blocked` is wrapped in `try/except Exception` at two places; unreadable limits send
the run to NEEDS_PERSON with `limits_unavailable` (:240-243) or return `recheck.limits_unavailable` (:742-745).
In agent_loop a `ProviderError` (so also `UsageMissing`) still books NOTHING (the except branch at :436 returns before
the charge). `demos/ask-your-data/askdata/pipeline.py` is changed (+4 -2; its test says an answered call without usage
is charged the reserved amount); the file itself was not opened: UNVERIFIED.

## 5.8 New tests on P4a

- `tests/test_usage_refuse.py` (61): a reply without usable token counts is refused (`UsageMissing`), never estimated;
  a reported zero is kept only for an empty reply; cost exact and rounded up once.
- `tests/test_usage_classes.py` (49): cache classes read and refused, pricing words, every kind declares its request
  count, k1b books the whole-call maximum, a zero price needs the fake kind, k1b replay runs only the fake kind.
- `tests/demo_askdata/test_usage_missing.py` (3): the demo charges the reserved amount for an answered call with no usage.
- From P2a-1: `tests/test_stop_state_cli.py` (9), `test_stop_state_config.py` (3), `test_stop_state_db.py` (17, real
  logins), `test_stop_state_memory.py` (11), `test_labelkey.py` (6), `tests/stop_state_helpers.py`.
- Older copies of the P4d store tests (`test_store_reserve.py` 20 tests, `test_store_reserve_pg.py` 5, and so on).
- About 25 existing test files edited for the new `Limits(...)` and `reply(...)` signatures (see the stat list).
Bodies of these tests were not read: the lines above come from their module docstrings.

---------------------------------------------------------------------------------------------------------------

# Part 6. origin/core/T1-T2-tests, head 1a7d202

```
 tests/contracts/kinds/store_postgres.py  |   8 +-
 tests/contracts/test_store_time_rules.py | 394 +++++++++++++++++++++++++++++++
 tests/contracts/test_t1_meter_cap.py     | 178 ++++++++++++++
 tests/demo_askdata/conftest.py           |   6 +-
 tests/meter_memory_killers.py            |  27 +++
 tests/meter_mutants.py                   | 245 +++++++++++++++++++
 tests/meter_support.py                   | 257 ++++++++++++++++++++
 tests/pg_dsn.py                          |  16 ++
 tests/postgres_mutants.py                | 282 ++++++++++++++++++++++
 tests/test_meter_harness.py              |  69 ++++++
 tests/test_pg_dsn_guard.py               |  60 +++++
 11 files changed, 1536 insertions(+), 6 deletions(-)
```

No file under src/. No Protocol, migration, limits, config, Budget, agent_loop or GRANTS change.

IMPORTANT, against the task's premise: T1 on this branch does NOT open many concurrent connections. The module docstring
of `tests/contracts/test_t1_meter_cap.py` says so:

`origin/core/T1-T2-tests:tests/contracts/test_t1_meter_cap.py` lines 1-20:

```
1	"""The cap, one caller at a time, on every store kind.
2	
3	Coupling: the mutant scripts (tests/meter_mutants.py, tests/postgres_mutants.py) name tests and message texts in this
4	file; renaming a test or rewording an assertion message here means changing the mutant that expects it.
5	
6	What the code does (read, not assumed): ``Limits.blocked`` CHECKS the day and month totals BEFORE a call;
7	``Limits.charge`` ADDS the real cost AFTER it. There is no reserve step. So one caller at a time admits
8	ceil(cap / cost) calls: the overshoot is at most one call (as the code behaves today; no design note was found
9	that promises it).
10	
11	Not here: 50 callers at the same time. All 50 pass the check before any of them charges, so the cap does not hold
12	there; the failing proof, the fix (a reserve step before the call) and the tests that show it green are a later
13	change (the failing proof is kept outside this branch: see the pull request description). What IS here for it: the harness
14	(``tests/meter_support.py``) and its controls, which show that the schedule can tell a meter that reserves from one
15	that does not.
16	
17	Every test takes the ``store`` fixture, so each runs on the memory store and, with HADAVIN_TEST_PG_DSN set, on the
18	postgres store (the production ledger). Amounts are ``Decimal`` dollars because the source ``Budget`` is Decimal.
19	``Limits.stop`` and ``Limits.reset`` (the kill switch writers) are not covered by these tests.
20	"""
```

Commit 98a3ed9 is titled "move the failing parallel test out". The failing 50-caller proof is on no ref that was
opened here ("kept outside this branch: see the pull request description"; the PR text was not read: UNVERIFIED).

What is there for parallel callers: `tests/meter_support.py:117-175`. `run_parallel(reserve, settle, n=50)` starts 50
Python THREADS behind a `threading.Barrier`, and a `Schedule` holds every settle back until all 50 have been through
`reserve` (the worst interleaving). The callers share whatever the two callables close over. In the one test of
test_t1_meter_cap.py that uses it (`test_the_harness_passes_a_meter_that_reserves_before_the_call`, :160-178) that is
the ONE `store` fixture handle: on Postgres one connection behind the store's lock. It opens zero extra connections.

`origin/core/T1-T2-tests:tests/meter_support.py` lines 117-175:

```
117	# --- the parallel schedule: a caller is a (reserve, settle) pair ----------------------------------------------------
118	
119	Reserve = Callable[[], bool]  # before the provider call: may this call go ahead? True = admitted
120	Settle = Callable[[], None]  # after the provider answered: book the real cost of an admitted call
121	
122	
123	def check_then_charge(limits: Limits) -> tuple[Reserve, Settle]:
124	    """The way agent_loop uses the meter today: reserve = ask ``blocked``; settle = ``charge`` the cost W."""
125	
126	    def reserve() -> bool:
127	        return not limits.blocked(AGENT)
128	
129	    def settle() -> None:
130	        limits.charge(AGENT, W)
131	
132	    return reserve, settle
133	
134	
135	class Schedule:
136	    """Forces the worst interleaving: no caller settles until every caller has been through ``reserve``."""
137	
138	    def __init__(self, n: int) -> None:
139	        self.n, self.decided = n, 0
140	        self.cond = threading.Condition()
141	
142	    def decided_and_wait(self) -> None:
143	        with self.cond:
144	            self.decided += 1
145	            self.cond.notify_all()
146	            reached = self.cond.wait_for(lambda: self.decided >= self.n, timeout=WAIT_S)
147	            assert reached, "not every caller reached the decision point"
148	
149	
150	def run_parallel(reserve: Reserve, settle: Settle, n: int = CALLERS) -> int:
151	    """n threads: reserve? -> (every caller has decided) -> stub provider call -> settle. Returns how many were
152	    admitted. ``run_parallel`` itself never charges: a meter that books at reserve time (a choke-point fix) is
153	    therefore not charged twice, and a meter that books only at settle time shows its race."""
154	    sched = Schedule(n)
155	    start = threading.Barrier(n, timeout=WAIT_S)
156	    admitted: list[bool] = []
157	    lock = threading.Lock()
158	
159	    def caller() -> None:
160	        start.wait()
161	        ok = reserve()
162	        sched.decided_and_wait()  # the stub provider answers only after every check is done
163	        if ok:
164	            settle()
165	        with lock:
166	            admitted.append(ok)
167	
168	    threads = [threading.Thread(target=caller) for _ in range(n)]
169	    for t in threads:
170	        t.start()
171	    for t in threads:
172	        t.join(WAIT_S * 2)
173	        assert not t.is_alive(), "a caller hung: the schedule is broken"
174	    assert len(admitted) == n
175	    return sum(admitted)
```

`origin/core/T1-T2-tests:tests/contracts/test_t1_meter_cap.py` lines 160-178:

```
160	def test_the_harness_passes_a_meter_that_reserves_before_the_call(store, monkeypatch):
161	    """Control, not a new meter: the real Limits, but the check and the booking of W happen under one lock at
162	    reserve time, and settle has nothing left to add (the real cost equals the reserved W). At most floor(cap / W)
163	    callers are admitted and the day total stays within the cap plus one call."""
164	    limits, _, _ = build_limits("3.00", HUGE, START, monkeypatch, store=store)
165	    gate = threading.Lock()
166	
167	    def reserve() -> bool:
168	        with gate:
169	            if limits.blocked(AGENT):
170	                return False
171	            limits.charge(AGENT, W)
172	            return True
173	
174	    admitted = run_parallel(reserve, lambda: None)
175	    day = store.spend_totals(AGENT, START.date())[0]
176	    assert admitted == 3, f"reserve-at-check admitted {admitted} of {CALLERS}, expected 3"
177	    assert day == Decimal("3.00"), f"day total {day}, expected 3.00"
178	    assert day <= Decimal("3.00") + W, "the day total passed cap + W"
```

Test files:

- `tests/contracts/test_t1_meter_cap.py` (9 test functions, both store kinds): with one caller at a time the old
  check-then-charge meter admits ceil(cap / cost) calls and overshoots by less than one call (:46); exact multiple
  never overshoots (:64); monthly cap binds (:81); charge is recorded (:93); both reasons named (:101); a budget of
  zero blocks the first call (:111); two PINS of today's behaviour, that `Limits.charge` books negative, infinite and NaN
  amounts (:138, :149), which must be deleted once the validators of P4d-a2 land; the harness control (:160).
- `tests/contracts/test_store_time_rules.py` (23, both store kinds): day and month buckets of `add_spend` /
  `spend_totals` replayed with a fake clock over 6 minutes, 25 hours, 31 days; UTC midnight, month end, leap day.
- `tests/test_meter_harness.py` (4): the schedule itself, on a stub meter: it must admit all 50 for a check-then-book
  meter (:42) and exactly the cap for a meter that books at reserve time (:52).
- `tests/meter_support.py` (257 lines): `build_limits` builds `Limits(store, audit, registry)` with THREE positional
  arguments (:98) and patches `hadavin_sdk.limits.now` (:112).
- `tests/meter_mutants.py`, `tests/postgres_mutants.py`, `tests/meter_memory_killers.py`: mutant lists for
  `tools/mutation_runner.py` (not read beyond the docstring: UNVERIFIED).
- `tests/pg_dsn.py` + `tests/test_pg_dsn_guard.py` (4): one rule, fail in CI and skip on a laptop when the DSN is missing.
- Changed: `tests/contracts/kinds/store_postgres.py` (+8 -... : uses `need_dsn_or_skip`), `tests/demo_askdata/conftest.py`.

---------------------------------------------------------------------------------------------------------------

# Part 7. Answers

## (a) Does any branch already implement reserve / settle? With what data model?

Yes, in two layers.

Store layer: core/P4d-a2 (newest), with older copies inside core/P4b1 and core/P4a.

- Table `spend_reservations` (migration 0006, quoted in 3.3). Columns: `reservation_id` TEXT primary key,
  `schema_version`, `agent_id`, `day` DATE, `run_id` (nullable, FK to runs), `reserved_usd` NUMERIC (> 0, 6 decimals),
  `status` in open / settled / released / expired, `settled_usd`, `created_at` (database clock, forced by trigger),
  `closed_at`, `expired_at`, `meta` JSONB (at most 2000 bytes). Partial index on open rows by (created_at, id).
  Insert and update triggers allow only open -> expired / settled / released and expired -> settled / released.
- Idempotence key: `reservation_id`, chosen by the caller of the store. Replay with same content returns the row with
  `applied=False`; settle and release are idempotent the same way.
- Expiry: no deadline column. The sweep takes an age in seconds (30 to 10**7) and expires open rows older than that by
  the database clock. Expired = still booked at the reserved amount; it can be settled or released once later.
- Held money is counted by ADDING it to the existing counters at reserve time (not by summing open rows at check time).
- Six Protocol methods: `reserve_spend`, `settle_spend`, `release_spend`, `get_spend_reservation`,
  `list_open_reservations`, `sweep_spend_reservations` (P4d-a2 protocol.py:301-338). Memory and Postgres both done.
- GRANT: `spend_reservations` SELECT, INSERT, UPDATE for the runtime login, no DELETE.

Caller layer: core/P4b1 only. `Meter` (meter.py) with `reserve`, `settle`, `release` and the context manager `hold`,
plus `Limits.hold` and `Limits.caps` (limits.py:37-85), `SpendMicro` (money.py). Not wired into any call site.

core/P4a implements no reserve / settle of its own. It supplies the inputs: exact cost from real usage, refusal when
usage is missing, and the byte-bound worst case in k1b. core/P4d and core/T1-T2-tests are tests only.

## (b) Which version is the base, and what is still missing?

Base for the store: core/P4d-a2 head (a8abba0). It is a strict superset of the store copy in P4b1 and P4a (write
wrapper, StoreBusy, retry, one-statement sweep, stricter trigger, the two-connection and multi-process proofs).
Base for the caller: core/P4b1's meter.py, money.py and limits.py additions, re-applied on top of P4d-a2 (its own diff
is four source files, see 4.1). From P4a take usage / pricing and the k1b worst-case formula.

Per requirement:

1. One reservation per chat call. Mechanism exists (`Limits.hold` -> `Meter.hold`), call sites do not use it.
   Missing: wire the five charge sites (agent_loop.py:325 and :485, k1b/loop.py:170, :179, :206 on main) to
   reserve before `chat` / before the model-backed detector and settle after; decide what k1b's in-memory `Budget`
   becomes (it has no agent, no store); a worst-case amount for an agent_loop call (only k1b has `worst_case_usd`;
   P4a's version at k1b/loop.py:115-132 is the candidate to share); stop the double booking, because reserve with a
   `run_id` already raises `runs.cost_usd` (P4d-a2 postgres.py:723-725) while agent_loop also calls
   `store.add_cost` (main agent_loop.py:326, :486). Also missing: a caller-supplied reservation id (the meter makes a
   random one, meter.py:252), if a retried step must not reserve twice.
2. Settle at actual cost. Exists: store `settle_spend` (may exceed the reserved amount, booked in full) and
   `Hold.record(actual)`. Missing: the call sites call `record`; the conversion from `Reply.cost_usd` (rounded up to 8
   decimals, models.round_cost_up) to the 6 decimals `settle_spend` accepts (`check_usd(actual_usd, max_decimals=6)`,
   P4d-a2 postgres.py:819). `SpendMicro.ceil_cost` exists for rounding up; nobody calls it from a Reply yet.
3. Settle at worst case when abandoned. Exists for a live process: leaving `hold` without `record` or `release`
   settles at the reserved amount (meter.py:366-405, :339-342), also on KeyboardInterrupt and SystemExit. For a dead
   process the row stays open and booked; the sweep then marks it expired, still booked. Missing: the wiring, and in
   agent_loop a decision for `ProviderError` / `UsageMissing` (today nothing is booked there; in k1b on P4a the worst
   case is booked).
4. Expired-reservation sweep. Store method exists on both kinds, with SKIP LOCKED on Postgres and tests. Missing: a
   caller. Nothing under src/ on any branch calls `sweep_spend_reservations` (no tick step, no CLI). The meter only
   offers the age (`orphan_age_s`, meter.py:206-210). Also missing: a policy for old expired rows (never settled or
   released) and pruning (no DELETE grant by design, migrate.py:55 comment).
5. Cap check that counts held reservations atomically under concurrency on Postgres. Exists in P4d-a2:
   conditional UPDATE per counter in one transaction (postgres.py:717-760). Proven there with 8 threads over 2
   connections, 12 connections in threads, and 8 spawned processes x 6 attempts. Missing: the 50-connection T1 proof
   (the T1-T2 branch holds only the thread harness and says the 50-caller test is a later change); a re-run of P4b1's
   meter tests against the P4d-a2 store (P4b1's unit tests use a stand-in `Busy` class); and the kill switch read
   inside reserve is a plain SELECT, so a stop that commits during a reserve does not stop that reserve (by design on
   P4d-a2, test at proofs_pg.py:264), and it must be re-pointed at `kill_switch_state` once P2a-1 lands (5.3).
   Old paths stay open: `Limits.charge` / `add_spend` still book with no cap check, so any call site left on
   `charge` bypasses the cap.

## (c) Conflicts between the branches

"Same path, different blob on the two heads" from `git rev-parse origin/<a>:<path>` on every path both diffs touch.
No trial merge was run (it would write objects), so textual conflict markers are predicted, not observed.

- `src/hadavin_sdk/store/protocol.py`, `store/memory.py`, `store/postgres.py`: three different versions (P4d-a2 head;
  the c31f336 copy in P4b1; that copy plus the P2a-1 kill switch in P4a). P4d-a2 vs P4b1 should resolve to P4d-a2
  (P4b1 did not edit them). P4d-a2 vs P4a is a real conflict in the kill switch area: P4a changes
  `get_kill_switch` / `set_kill_switch` return types to `StopState`, adds `reset_kill_switch`, reads the view
  `kill_switch_state`, while P4d-a2 rewrote the same region (`@_writes()` on `set_kill_switch`, removed
  `_kill_switch_row`, `_kill_on` in memory).
- `src/hadavin_sdk/store/migrations/0006_spend_reservations.sql`: P4d-a2 differs from the copy in P4b1 and P4a by
  three trigger lines (3.3). Whichever merges second must end with P4d-a2's text; a database that already ran the old
  0006 would need a new migration (forward-only), UNVERIFIED whether any did.
- `src/hadavin_sdk/store/migrate.py`: P4d-a2 and P4b1 identical; P4a differs (GRANTS for kill switch tables, `reset` /
  `stop` grant fields, the function templates).
- `src/hadavin_sdk/limits.py`: P4b1 (adds `hold`, `caps`, meter fields, keeps the 3-argument constructor) vs P4a
  (new constructor with required `environment=`, new `stop` / `reset`). Both edit the constructor and `charge`'s
  neighbourhood. P4d-a2 and T1-T2-tests do not touch it, but T1-T2's `tests/meter_support.py:98` and P4b1's tests
  call `Limits(store, audit, registry)` and will break against P4a's constructor.
- `src/hadavin_sdk/defaults.py`: all three append a different block at the end of the file (P4d-a2: money + purge;
  P4b1: money + meter; P4a: money + kill switch + usage + request counts). Keep all blocks.
- `src/hadavin_sdk/models.py`: `round_cost_up` has two texts (P4d-a2 newer, P4a/P4b1 older); P4a also adds `Usage`,
  `StopState`, `KillSwitch.version`, `Reply.usage`.
- `src/hadavin_sdk/llm/common.py` and `llm/fake.py`: P4d-a2 and P4b1 add `price_cost` and keep estimating; P4a removes
  the estimate and changes `reply()`'s signature, with no `price_cost`. Real conflict; P4a's intent (refuse) wins and
  `price_cost` callers must move to `pricing.cost_usd`.
- `src/hadavin_sdk/config.py`: the `Route._price` validator is the same text on all three; the import block and
  P4a's extra classes differ, and main changed config.py after each merge-base.
- `src/hadavin_sdk/backends/table.py`: P4d-a2 (lock_timeout_ms, call_budget_ms) vs P4a (P2a-1 settings such as
  `stop_credential_ref`; file not opened on P4a: UNVERIFIED).
- `tests/meter_support.py`: ADDED by both P4b1 (81 lines, scripted store) and T1-T2-tests (257 lines, Limits harness)
  with different content. Add/add conflict; one must be renamed.
- `tests/contracts/kinds/store_postgres.py`: different on all five heads.
- `tests/contracts/conftest.py`, `kinds/__init__.py`, `store_support.py`, `test_pg_driver.py`,
  `test_store_registry.py`, `test_store.py`: P4d (PR 66) differs from the copy carried by P4d-a2 / P4b1 / P4a (which
  agree with each other on conftest.py, kinds/__init__.py, store_support.py, test_pg_driver.py).
- `tests/contracts/test_store_reserve.py`, `test_store_reserve_pg.py`, `test_cost_rounding.py`, `test_store.py`,
  `tests/test_k5_fixes2.py`, `tests/test_p2_postgres.py`: P4d-a2 newer than the copies in P4b1 and P4a; P4a's copies
  also differ from P4b1's for the reserve tests. `test_store_money_edges.py` and `test_store_registry.py`: P4b1 = P4a,
  both differ from P4d-a2.
- Behaviour conflicts between test sets: P4d's `test_store_money_baseline.py` and T1-T2's two `test_pin_today_*` tests
  pin that bad amounts ARE booked; P4d-a2's validators refuse them. Those pins must go when P4d-a2 lands.
- `CHANGELOG.md`: changed by P4d, P4d-a2, P4b1, P4a and by main since.
- Drift against main (files main changed after the branch's merge-base that the branch also changes): P4d-a2:
  pyproject.toml, uv.lock, backends/table.py, config.py, models.py, tests/contracts/test_store.py. P4b1: config.py,
  defaults.py, models.py, store/postgres.py, tests/contracts/test_store.py. P4a: app.py, backends/table.py, config.py,
  defaults.py, models.py, runtime/agent_loop.py, store/postgres.py and nine test files. P4d and T1-T2: only
  CHANGELOG.md / test_store.py (P4d), nothing (T1-T2).

# Heads for three build tickets: audit drain (A), stop state with a reset identity (B), price constraint (C)

Read-only lookup. Nothing was run, no branch was switched. `S` = `src/hadavin_sdk`.

Refs read:
- main = `origin/main` = 51c9fc4fbb4a887274615dbc5f83087ff0ab4280. The working tree under `src/` and `tests/` equals it (`git diff --stat origin/main -- src tests` printed nothing). All plain `file:line` below are main.
- PR 76 = `origin/core/P2a-1` = 7f323491f91910ed3af03d6fae0cbabd1e23f6bc.
- PR 78 = `origin/core/P4a` = 4a0976ffdbda144f768ee7118b5d2ef65c757d47.
- Both branches fork from main at 1e4752f2211fb09a4d2487e568f73d113e371042 (`git merge-base`). Main has 12 commits after that point which neither branch holds (list in section B.9).

The three answers, short:
- A. Nothing in `src` ever calls `AuditSink.reconcile()`. So the `audit_outbox` table (and the `local_dir` outbox folder) and the in-memory `_pending` list are written but never drained outside tests. The tick step named `reconcile` is about approvals, not audit. Smallest fix: append one tick step (name free to choose, for example `audit_drain`) that calls `ctx.app.audit.reconcile()`. No migration and no grant change is needed.
- B. Yes. PR 76 separates stop from reset at the database-grant level (no role holds any right on `kill_switch`; stop and reset are two SECURITY DEFINER functions with separate EXECUTE grants; a trigger refuses on->off unless `session_user` is a member of the reset group). What is missing is not the design but the landing: it is unmerged, forked from an old main, and its head still uses the stage name `dev` that main no longer accepts.
- C. Partly. PR 78 refuses negative prices at config load (that validator comes from the P4d commit that PR 76 also carries) and refuses a zero price at config load unless the llm kind is `fake` (PR 78's own commit 781b8ba). It adds no price date: no such field exists in `Route` or anywhere under `src` on that branch.

---

# STEP A. Audit drain

## A.1 The chain sink: write_outcome, `_pending`, the outbox writes, reconcile

`src/hadavin_sdk/audit/chain.py` lines 140-260 (main 51c9fc4):
```
   140	        False  # the audit or its anchors could not be read: not checked, not "tampered"
   141	    )
   142	
   143	    @property
   144	    def ok(self) -> bool:
   145	        return not self.problems
   146	
   147	    @property
   148	    def unsigned_tail(self) -> int:
   149	        return self.rows - self.signed_through
   150	
   151	
   152	class ChainAudit:
   153	    """The AuditSink Protocol over the chain, plus `checkpoint()` (inline every N rows, and from `tick`) and
   154	    `verify()`. Keys returned by the writes are event ids."""
   155	
   156	    def __init__(
   157	        self,
   158	        db: _Db,
   159	        signer: Signer | None = None,
   160	        anchor: Any = None,
   161	        checkpoint_every: int = 100,
   162	    ) -> None:
   163	        self._db, self.signer, self.anchor = db, signer, anchor
   164	        # A custom anchor kind written before alg and key_label existed takes three arguments: it still works (its
   165	        # objects just lack the two fields) and is logged once, instead of failing every put with a TypeError.
   166	        self._anchor_takes_meta = not hasattr(anchor, "put") or _takes_meta(anchor.put)
   167	        if not self._anchor_takes_meta:
   168	            _LOG.warning(
   169	                "audit anchor put() takes no alg/key_label: its objects will not verify offline"
   170	            )
   171	        self.checkpoint_every = checkpoint_every
   172	        # Last resort when even the outbox table cannot be written (the database is down): drained by reconcile.
   173	        self._pending: list[AuditEvent] = []
   174	        # Checkpoints whose anchor put failed: retried by the next checkpoint() (ponytail: in-process only; a
   175	        # restart drops the list and `verify` then reports "never anchored", which is the truth).
   176	        self._unanchored: dict[int, tuple[str, str]] = {}
   177	
   178	    # --- AuditSink ----------------------------------------------------------------------------------
   179	
   180	    def _append(self, event: AuditEvent) -> str:
   181	        body = event.model_dump_json()
   182	        at = event.ts.astimezone(UTC).isoformat(timespec="microseconds")
   183	        kind = f"{event.domain}.{event.operation}"
   184	        with self._db.transaction() as q:
   185	            if q("SELECT 1 FROM audit_entries WHERE event_id = ?", (event.event_id,)):
   186	                raise DuplicateEvent(event.event_id)
   187	            last = q("SELECT seq, hash FROM audit_entries ORDER BY seq DESC LIMIT 1")
   188	            seq, prev = (last[0][0] + 1, last[0][1]) if last else (1, GENESIS)
   189	            q(
   190	                "INSERT INTO audit_entries (seq, at, run_id, kind, body, prev, hash, event_id) "
   191	                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
   192	                (
   193	                    seq,
   194	                    at,
   195	                    event.run_id,
   196	                    kind,
   197	                    body,
   198	                    prev,
   199	                    _hash(prev, seq, at, event.run_id, kind, body),
   200	                    event.event_id,
   201	                ),
   202	            )
   203	        if self.signer is not None and seq % self.checkpoint_every == 0:
   204	            self.checkpoint()
   205	        return event.event_id
   206	
   207	    def write_intent(self, event: AuditEvent) -> str:
   208	        try:
   209	            return self._append(event)
   210	        except DuplicateEvent:
   211	            raise
   212	        except Exception as exc:
   213	            raise AuditUnavailable(f"intent {event.event_id}: {exc.__class__.__name__}") from exc
   214	
   215	    def write_outcome(self, event: AuditEvent) -> str | None:
   216	        """Never raises: the chain, then the outbox table, then memory (all drained by reconcile)."""
   217	        try:
   218	            return self._append(event)
   219	        except DuplicateEvent:
   220	            return event.event_id
   221	        except Exception:  # noqa: BLE001 - the contract is "never raises"
   222	            try:
   223	                self._db.run(
   224	                    "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) "
   225	                    "ON CONFLICT (event_id) DO NOTHING",
   226	                    (event.event_id, event.model_dump_json()),
   227	                )
   228	            except Exception:  # noqa: BLE001
   229	                self._pending.append(event)
   230	            return None
   231	
   232	    def reconcile(self) -> int:
   233	        done = 0
   234	        for event in list(self._pending):
   235	            if self._drain(event):
   236	                self._pending.remove(event)
   237	                done += 1
   238	        try:
   239	            queued = self._db.run("SELECT event_id, body FROM audit_outbox ORDER BY event_id")
   240	        except Exception:  # noqa: BLE001 - the database is still down: retried next time
   241	            return done
   242	        for event_id, body in queued:
   243	            if self._drain(AuditEvent.model_validate_json(body)):
   244	                self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (event_id,))
   245	                done += 1
   246	        return done
   247	
   248	    def _drain(self, event: AuditEvent) -> bool:
   249	        try:
   250	            self._append(event)
   251	        except DuplicateEvent:
   252	            pass
   253	        except Exception:  # noqa: BLE001 - stays queued, retried next time
   254	            return False
   255	        return True
   256	
   257	    def verify_object(self, key: str) -> bool:
   258	        """The event's row holds its own content's hash and links to the row before it, which holds its own."""
   259	        found = self._db.run("SELECT seq FROM audit_entries WHERE event_id = ?", (key,))
   260	        if not found:
```

Facts from this block:
- `_pending` is a plain list on the sink object: `S/audit/chain.py:173`. The comment at `:172` says "drained by reconcile". It has no lock of its own (the `_Db.lock` at `S/audit/chain.py:98-99,111-113` covers database statements only).
- `write_outcome` (`S/audit/chain.py:215-230`) never raises. Order: chain append (`:218`), then `INSERT INTO audit_outbox ... ON CONFLICT (event_id) DO NOTHING` (`:223-227`), then `self._pending.append(event)` (`:229`). It returns `None` when the event was parked.
- `write_intent` (`S/audit/chain.py:207-213`) never parks: it raises `AuditUnavailable`.
- `reconcile` (`S/audit/chain.py:232-246`) is the ONLY drain. It drains `_pending` first (`:234-237`), then reads the whole outbox with no LIMIT (`:239`), appends each row through `_drain` (`:243`, `:248-255`) and deletes the outbox row (`:244`). It returns the number drained.
- There is nothing named `drain` (other than the private `_drain`), `flush` or a second reconcile in this file.
- Three weak points inside `reconcile` that a tick step will inherit:
  1. `AuditEvent.model_validate_json(body)` at `:243` is outside any `try`. One unreadable outbox row raises out of `reconcile` and blocks every row after it, on every tick. (The `local_dir` sink moves a corrupt file aside instead: `S/audit/local_dir.py:144-147`.)
  2. The `DELETE` at `:244` is outside any `try`. If it fails the row stays; the next pass hits `DuplicateEvent` in `_drain` (`:251-252`), which counts as done, and tries the delete again. So no double row in the chain, but the call raises.
  3. A drained event is appended with a NEW `seq` at drain time and keeps its original time `at` (`S/audit/chain.py:182`, `:187-188`). The chain order is then drain order, not event order. The test at `tests/warden_port/test_audit_chain.py:515` pins exactly this (`[later, first]`).

The SQLite twin of the outbox table (memory store): `S/audit/chain.py:55` (`CREATE TABLE audit_outbox (event_id TEXT PRIMARY KEY, body TEXT NOT NULL);`).

## A.2 The Protocol

`src/hadavin_sdk/audit/protocol.py` lines 18-35 (main 51c9fc4):
```
    18	class AuditSink(Protocol):
    19	    def write_intent(self, event: AuditEvent) -> str:
    20	        """Write before a side effect. Raises AuditUnavailable on any failure."""
    21	        ...
    22	
    23	    def write_outcome(self, event: AuditEvent) -> str | None:
    24	        """Write after a side effect. On failure the event goes to the outbox; never raises."""
    25	        ...
    26	
    27	    def reconcile(self) -> int:
    28	        """Drain the outbox. Returns how many events were written."""
    29	        ...
    30	
    31	    def verify_object(self, key: str) -> bool: ...
    32	
    33	    def events(self, run_id: str | None = None) -> list[AuditEvent]:
    34	        """Read back in write order, optionally for one run."""
    35	        ...
```

## A.3 The other sink (`local_dir`) has the same shape

`src/hadavin_sdk/audit/local_dir.py` lines 110-156 (main 51c9fc4):
```
   110	    def write_outcome(self, event: AuditEvent) -> str | None:
   111	        """Never raises: object store, then outbox, then memory (drained by reconcile)."""
   112	        try:
   113	            return self._write(event)
   114	        except DuplicateEvent:
   115	            return f"{event.event_id}.json"
   116	        except Exception:  # noqa: BLE001 - disk errors, a corrupt index line: the contract is "never raises"
   117	            try:
   118	                self.outbox.mkdir(parents=True, exist_ok=True)
   119	                tmp = self.outbox / f".tmp-{event.event_id}"
   120	                tmp.write_text(event.model_dump_json(), encoding="utf-8")
   121	                os.replace(tmp, self.outbox / f"{event.event_id}.json")  # never a half file
   122	            except Exception:  # noqa: BLE001
   123	                self._pending.append(event)
   124	            return None
   125	
   126	    def reconcile(self) -> int:
   127	        """Drain memory and the outbox. A corrupt outbox file is moved to ``outbox/corrupt/`` (kept for a
   128	        person, counted nowhere) so it can never block the files after it."""
   129	        done = 0
   130	        for event in list(self._pending):
   131	            try:
   132	                self._write(event)
   133	            except DuplicateEvent:
   134	                pass
   135	            except Exception:  # noqa: BLE001, S112 - safe to swallow: the event is still in memory, so nothing is lost; the next flush retries it and the audit chain only advances on a successful write
   136	                continue
   137	            self._pending.remove(event)
   138	            done += 1
   139	        if not self.outbox.exists():
   140	            return done
   141	        for path in sorted(self.outbox.glob("*.json")):
   142	            try:
   143	                event = AuditEvent.model_validate_json(path.read_text(encoding="utf-8"))
   144	            except ValueError:
   145	                (self.outbox / "corrupt").mkdir(exist_ok=True)
   146	                os.replace(path, self.outbox / "corrupt" / path.name)
   147	                continue
   148	            try:
   149	                self._write(event)
   150	            except DuplicateEvent:
   151	                pass
   152	            except Exception:  # noqa: BLE001, S112 - safe to swallow: the file is not unlinked, so nothing is lost; the next flush retries it and a duplicate is absorbed by DuplicateEvent
   153	                continue
   154	            path.unlink()
   155	            done += 1
   156	        return done
```
`_pending` there: `S/audit/local_dir.py:31-32`.

Only two classes define `reconcile`: `S/audit/chain.py:232` and `S/audit/local_dir.py:126` (grep `def reconcile` over `src`; the third hit, `S/runtime/tick.py:85`, is the tick step function, see A.5).

## A.4 Every caller (grep over `src`)

Callers of `write_outcome` in `src`:
- `S/k1b/audit_sink.py:39` (`self.sink.write_outcome(self._event(operation, run_id, fields))`)
- `S/runtime/tick.py:133` and `S/runtime/tick.py:162` (the `stuck` step, principal `system:tick`)
- `S/runtime/agent_loop.py:241` (`_note`)
- `S/limits.py:46` (the stop)
- `S/approvals/requests.py:82`

Callers of the audit `reconcile()` in `src`: NONE. `grep -rnE "\.reconcile\(" src tests tools demos` hits only tests:
- `tests/test_cuj.py:202`, `tests/warden_port/test_audit_chain.py:514,517,677`, `tests/test_s2_audit.py:51`, `tests/test_review_fixes.py:105`, `tests/contracts/test_capabilities.py:45,59`, `tests/test_review_pr3_round2.py:321`.

Readers or writers of `_pending` or `audit_outbox` outside the two sink files in `src`: none. The only other mentions are the DDL (`S/store/migrations/0002_audit_chain.sql:19`), its comment (`:3`), and the grant map (`S/store/migrate.py:43`, `:59`).

Words that claim a drain that does not happen:
- `S/audit/chain.py:172` "drained by reconcile", `S/audit/chain.py:216` "all drained by reconcile".
- `S/k1b/audit_sink.py:38` "on failure the sink keeps it for ``reconcile``".
- `S/store/migrations/0002_audit_chain.sql:3` and `S/store/migrate.py:43` "reconcile deletes an outbox row once it is in the chain".
- `S/cli.py:6-7` describes tick as "approvals sweep, reconcile, stuck runs, audit checkpoint": the word reconcile there is the approvals step.

## A.5 `S/runtime/tick.py`

`src/hadavin_sdk/runtime/tick.py` lines 1-18 (main 51c9fc4):
```
     1	"""`hadavin-sdk tick`: one idempotent pass of housekeeping steps, run every 30-60 s by any scheduler.
     2	
     3	Contract (design v5 kernel, section 4):
     4	* ``STEPS`` runs in order: sweep, reconcile, stuck, checkpoint, purge_evidence (by default daily). Later PRs only
     5	  **append** a ``TickStep``.
     6	* Each step runs in its own ``try``: a failure is logged as ``step=<name> error_kind=<type>
     7	  message=<redacted, <= 500 chars>`` and written to ``tick_state``; the other steps still run.
     8	* A step with ``every_s > 0`` runs only if ``now - tick_state.last_run_at >= every_s``.
     9	* The tick summary line (``heartbeat``) is not a step: it is logged after the steps, is never recorded in
    10	  ``tick_state`` and cannot change the exit code. The external heartbeat
    11	  (a ping sent by the CLI entrypoint for every exit code) is PENDING (K7): nothing sends it today.
    12	* Exit codes: 0 all ok; 1 a step failed (store still reachable); 2 config error, or the store answers but is
    13	  not ready (missing table or grant: run ``migrate``); 4 store unreachable (connection refused, dropped or
    14	  timed out), before any step or when it stops answering during the steps; 3 is the CLI wrapper's code for any
    15	  other uncaught error.
    16	
    17	Concurrent ticks are safe: every state change is a compare-and-set, and a loser (``StaleState``) skips.
    18	"""
```

`src/hadavin_sdk/runtime/tick.py` lines 43-61 (main 51c9fc4):
```
    43	@dataclass
    44	class TickContext:
    45	    app: App
    46	    now: datetime
    47	    results: dict[str, str] = field(default_factory=dict)  # step name -> ok / failed / skipped
    48	
    49	
    50	@dataclass(frozen=True)
    51	class TickStep:
    52	    name: str  # unique, [a-z_]+ (the tick_state CHECK)
    53	    every_s: int  # 0 = every tick
    54	    fn: Callable[[TickContext], None]
    55	    # Interval read from the config at run time (so it is not frozen at import); wins over `every_s`.
    56	    interval: Callable[[TickContext], int] | None = None
    57	
    58	    def __post_init__(self) -> None:
    59	        if not re.fullmatch(r"[a-z_]+", self.name) or self.every_s < 0:
    60	            raise ValueError(f"tick step name must be [a-z_]+ and every_s >= 0: {self.name!r}")
    61	
```

`src/hadavin_sdk/runtime/tick.py` lines 85-97 (main 51c9fc4):
```
    85	def reconcile(ctx: TickContext) -> None:
    86	    """Advance runs whose approval ended (APPROVED runs the plan). The receiver only records decisions."""
    87	    store, runtime = ctx.app.store, ctx.app.runtime
    88	    ended = store.list_approvals({"APPROVED", "REJECTED", "EXPIRED"})
    89	    # ponytail: scans every ended approval each tick; filter by a reconciled flag when the table grows.
    90	
    91	    def one(req) -> None:
    92	        if store.get_run(req.run_id).state is not S.WAITING_FOR_APPROVAL:
    93	            return
    94	        ctx.app.approvals.update_message(req)  # decisions arrive record-only: show the outcome now
    95	        runtime.on_decided(req.run_id, req.status, store.get_approval_decision(req.approval_id))
    96	
    97	    _each(ended, one, "reconcile")
```

`src/hadavin_sdk/runtime/tick.py` lines 177-181 (main 51c9fc4):
```
   177	def checkpoint(ctx: TickContext) -> None:
   178	    """Sign an audit checkpoint when the audit kind has them (`chain`); others have nothing to do."""
   179	    fn = getattr(ctx.app.audit, "checkpoint", None)
   180	    if fn is not None:
   181	        fn()
```

`src/hadavin_sdk/runtime/tick.py` lines 249-266 (main 51c9fc4):
```
   249	STEPS: list[TickStep] = [
   250	    TickStep("sweep", 0, sweep),
   251	    TickStep("reconcile", 0, reconcile),
   252	    TickStep("stuck", 0, stuck),
   253	    TickStep("checkpoint", 0, checkpoint),
   254	    TickStep(
   255	        "purge_evidence",
   256	        0,
   257	        purge_evidence,
   258	        interval=lambda ctx: ctx.app.config.retention.purge_every_s,
   259	    ),  # its own interval: Config.retention.purge_every_s
   260	    TickStep(
   261	        "reprobe_sources",
   262	        0,
   263	        reprobe_sources,
   264	        interval=lambda ctx: ctx.app.config.evidence.source_reprobe_s,
   265	    ),
   266	]
```

`src/hadavin_sdk/runtime/tick.py` lines 295-369 (main 51c9fc4):
```
   295	def _run_step(ctx: TickContext, step: TickStep) -> str:
   296	    store = ctx.app.store
   297	    prev, error = None, None
   298	    try:
   299	        prev = store.get_tick_state(step.name)
   300	        every = step.interval(ctx) if step.interval else step.every_s
   301	        if (
   302	            step.interval
   303	        ):  # a tick comes every 30-60 s: due a tick-period early, so the cadence does not drift
   304	            every = max(every - TICK_SLACK_S, every // 2)
   305	        # A step whose last run FAILED is due again at the next tick (a persistently raising hold hook must
   306	        # not push the 30-day purge a whole interval away each time).
   307	        if (
   308	            every
   309	            and prev
   310	            and prev.last_error is None
   311	            and (ctx.now - prev.last_run_at).total_seconds() < every
   312	        ):
   313	            return SKIPPED
   314	        step.fn(ctx)
   315	    except Exception as exc:  # noqa: BLE001 - one step never stops the others
   316	        error = f"{type(exc).__name__}: {_message(exc)}"
   317	        _LOG.error("step=%s error_kind=%s message=%s", step.name, type(exc).__name__, _message(exc))
   318	    try:
   319	        store.save_tick_state(
   320	            TickState(
   321	                step=step.name,
   322	                last_run_at=ctx.now,
   323	                last_ok_at=ctx.now if error is None else (prev.last_ok_at if prev else None),
   324	                last_error=error,
   325	            )
   326	        )
   327	    except Exception as exc:  # noqa: BLE001 - an unrecorded step counts as failed
   328	        _LOG.error(
   329	            "step=%s error_kind=%s message=tick_state not saved", step.name, type(exc).__name__
   330	        )
   331	        return FAILED
   332	    return OK if error is None else FAILED
   333	
   334	
   335	def run_tick(app: App, now: datetime | None = None, steps: list[TickStep] | None = None) -> int:
   336	    """One tick. Returns the exit code: 0 ok, 1 a step failed, 4 the store is unreachable, 2 the store answers but
   337	    is not ready (STORE_NOT_READY). A config that does not load is the caller's, before this runs."""
   338	    ctx = TickContext(app, now or app.approvals.clock())
   339	    try:
   340	        app.store.get_tick_state(_PROBE)  # the store answers, or nothing runs
   341	    except Exception as exc:  # noqa: BLE001 - any store failure: change nothing
   342	        if is_connectivity_error(exc):
   343	            _safe_log("step=- error_kind=%s message=store unreachable", type(exc).__name__)
   344	            return STORE_UNREACHABLE
   345	        _safe_log(
   346	            "step=- error_kind=%s message=store answers but is not ready: run hadavin-sdk migrate "
   347	            "and check the runtime role's grants",
   348	            type(exc).__name__,
   349	        )
   350	        return STORE_NOT_READY
   351	    for step in STEPS if steps is None else steps:
   352	        ctx.results[step.name] = _run_step(ctx, step)
   353	    try:
   354	        heartbeat(ctx)
   355	    except Exception as exc:  # noqa: BLE001 - a log line never changes the exit code
   356	        _safe_log("step=- error_kind=%s message=heartbeat line not written", type(exc).__name__)
   357	    if FAILED in ctx.results.values():
   358	        # A scheduler must tell "the store went away" (4) from "a step failed with the store up" (1).
   359	        try:
   360	            app.store.get_tick_state(_PROBE)
   361	        except Exception as exc:  # noqa: BLE001 - any store failure
   362	            if is_connectivity_error(exc):
   363	                _safe_log(
   364	                    "step=- error_kind=%s message=store unreachable after the steps",
   365	                    type(exc).__name__,
   366	                )
   367	                return STORE_UNREACHABLE
   368	            # answers but not ready: the step failures stand, exit 1
   369	    return 1 if FAILED in ctx.results.values() else 0
```

Facts:
- The step named `reconcile` (`S/runtime/tick.py:251`, function at `:85-97`) advances runs whose approval ended. It never touches `ctx.app.audit`. It is NOT the audit drain.
- The `getattr` guard is at `S/runtime/tick.py:179`: `fn = getattr(ctx.app.audit, "checkpoint", None)`, then `fn()` only when present (`:180-181`). It is how a step copes with an audit kind that lacks a method. It guards `checkpoint`, not `reconcile`.
- How a step is registered: one `TickStep(name, every_s, fn, interval=None)` entry in the module list `STEPS` (`S/runtime/tick.py:249-266`). The contract says later PRs only APPEND (`:4-5`). The name must match `[a-z_]+` (`:59`), and the database enforces the same (`S/store/migrations/0003_approvals_tick.sql:31`: `step TEXT PRIMARY KEY CHECK (step ~ '^[a-z_]+$')`).
- How a failure is handled: `_run_step` (`S/runtime/tick.py:295-332`). The step runs in its own `try` (`:298-317`); any exception becomes `error = "<Type>: <redacted message>"` (`:316`) and one log line `step=... error_kind=... message=...` (`:317`). Then `tick_state` is saved with `last_error` (`:319-326`); if that save fails the step counts as FAILED (`:327-331`). Other steps still run (`:351-352`). Exit code 1 when any step failed and the store still answers, 4 when the store is gone (`:357-369`).
- A step with an interval whose last run FAILED is due again at the next tick (`:305-313`).
- `tick_state` needs no new row or migration for a new step: `save_tick_state` upserts on `step` (`S/store/postgres.py:470-471`).

## A.6 `_note` and `_note_card` in `S/runtime/agent_loop.py`

`src/hadavin_sdk/runtime/agent_loop.py` lines 240-248 (main 51c9fc4):
```
   240	    def _note(self, run: Run, domain: str, operation: str, **kw: Any) -> None:
   241	        self.audit.write_outcome(self._event(run, domain, operation, **kw))
   242	
   243	    def _note_card(self, run: Run, operation: str, **kw: Any) -> None:
   244	        """Audit a card post. The card is already out, so a failing audit write is logged and never raised."""
   245	        try:
   246	            self._note(run, "card", operation, **kw)
   247	        except Exception:  # noqa: BLE001 - fail-safe: the run end state is unchanged
   248	            _LOG.warning("run %s: audit write for card %s failed", run.run_id, operation)
```
`_note_card` catches an exception that the two sinks never raise from `write_outcome` (`S/audit/chain.py:216`, `S/audit/local_dir.py:111`). The `except` at `S/runtime/agent_loop.py:247` can only fire for building the event (`_event`, `:230-238`) or for a custom sink that breaks the "never raises" contract.

## A.7 The outbox table DDL (migration 0002)

`src/hadavin_sdk/store/migrations/0002_audit_chain.sql` lines 1-35 (main 51c9fc4):
```
     1	-- The `chain` audit's tables in the store's database (slice 2 P3). Ported from WARDEN audit.py `_PG_SCHEMA`
     2	-- (main c78d7709): rows and checkpoints are append-only even to a role that could UPDATE, DELETE or TRUNCATE.
     3	-- The outbox is not: reconcile deletes a queued outcome once it is in the chain.
     4	CREATE TABLE IF NOT EXISTS audit_entries (
     5	    seq BIGINT PRIMARY KEY,
     6	    at TEXT NOT NULL,
     7	    run_id TEXT NOT NULL,
     8	    kind TEXT NOT NULL,
     9	    body TEXT NOT NULL,
    10	    prev TEXT NOT NULL,
    11	    hash TEXT NOT NULL,
    12	    event_id TEXT NOT NULL UNIQUE
    13	);
    14	CREATE TABLE IF NOT EXISTS audit_checkpoints (
    15	    seq BIGINT PRIMARY KEY,
    16	    hash TEXT NOT NULL,
    17	    signature TEXT NOT NULL
    18	);
    19	CREATE TABLE IF NOT EXISTS audit_outbox (
    20	    event_id TEXT PRIMARY KEY,
    21	    body TEXT NOT NULL
    22	);
    23	CREATE INDEX IF NOT EXISTS audit_entries_by_run ON audit_entries (run_id, seq);
    24	
    25	CREATE OR REPLACE FUNCTION hadavin_audit_append_only() RETURNS trigger LANGUAGE plpgsql AS
    26	$f$ BEGIN RAISE EXCEPTION 'the audit log is append-only'; END $f$;
    27	
    28	CREATE OR REPLACE TRIGGER audit_entries_append_only BEFORE UPDATE OR DELETE ON audit_entries
    29	    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
    30	CREATE OR REPLACE TRIGGER audit_checkpoints_append_only BEFORE UPDATE OR DELETE ON audit_checkpoints
    31	    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();
    32	CREATE OR REPLACE TRIGGER audit_entries_no_truncate BEFORE TRUNCATE ON audit_entries
    33	    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
    34	CREATE OR REPLACE TRIGGER audit_checkpoints_no_truncate BEFORE TRUNCATE ON audit_checkpoints
    35	    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();
```
- Table: `S/store/migrations/0002_audit_chain.sql:19-22`. Two columns: `event_id TEXT PRIMARY KEY`, `body TEXT NOT NULL`. No timestamp, no attempt count, no index beyond the key.
- The append-only triggers cover `audit_entries` and `audit_checkpoints` only (`:28-35`); the outbox has none, so DELETE works (`:3`).
- Migration 0004 (`0004_audit_checkpoint_meta.sql`) was not opened: UNVERIFIED whether it touches the outbox (its name and `tests/test_p2_postgres.py:276-294` say it adds `alg` and `key_label` to `audit_checkpoints`).

## A.8 GRANTS rows in `S/store/migrate.py`

`src/hadavin_sdk/store/migrate.py` lines 40-68 (main 51c9fc4):
```
    40	_RW = "SELECT, INSERT, UPDATE"
    41	_APPEND = "SELECT, INSERT"  # written once, never changed
    42	# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
    43	# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
    44	# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
    45	# `redaction_maps`, `events`, `tick_state.detail` or secrets.
    46	GRANTS: dict[str, Grant] = {
    47	    "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
    48	    "plans": Grant("table", _RW, portal=True),
    49	    "gate_decisions": Grant("table", _APPEND, portal=True),
    50	    "approval_requests": Grant("table", _RW, portal=True),
    51	    "approval_decisions": Grant("table", _APPEND, portal=True),
    52	    "dead_letters": Grant("table", _APPEND),
    53	    "spend": Grant("table", _RW),
    54	    "spend_month": Grant("table", _RW),
    55	    "kill_switch": Grant("table", _RW),
    56	    "tick_state": Grant("table", _RW),
    57	    "audit_entries": Grant("table", _APPEND, portal=True),
    58	    "audit_checkpoints": Grant("table", _APPEND, portal=True),
    59	    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    60	    # K5-core: append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
    61	    # The runtime role appends and reads evidence; only the purge role (its own identity) deletes it.
    62	    "tool_calls": Grant(
    63	        "table", _APPEND, purge="DELETE", purge_cols=("call_id", "run_id", "created_at")
    64	    ),
    65	    "redaction_maps": Grant("table", _RW, purge="DELETE", purge_cols=("run_id", "updated_at")),
    66	    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    67	    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
    68	}
```
- `"audit_outbox": Grant("table", "SELECT, INSERT, DELETE")` at `S/store/migrate.py:59`. So the runtime role already holds everything `reconcile` needs (SELECT `chain.py:239`, DELETE `chain.py:244`, INSERT `chain.py:224`). No `portal`, no `purge`.
- `audit_entries` is `_APPEND` = `SELECT, INSERT` (`:41`, `:57`), which is what `_drain` -> `_append` needs.

## A.9 How the tick process is started

`src/hadavin_sdk/cli.py` lines 132-135 (main 51c9fc4):
```
   132	    if args.config:
   133	        os.environ["HADAVIN_CONFIG_DIR"] = args.config
   134	    if args.cmd == "tick":
   135	        return _tick()
```

`src/hadavin_sdk/cli.py` lines 280-309 (main 51c9fc4):
```
   280	def _tick() -> int:
   281	    """Build the app with every qualified agent (an unqualified one must not stop approvals expiring)."""
   282	    from hadavin_sdk.app import build
   283	    from hadavin_sdk.runtime.agent_loop import Unqualified, assert_qualified
   284	    from hadavin_sdk.runtime.tick import run_tick
   285	
   286	    # The summary line and step errors go to stderr (the logger is otherwise silent below WARNING).
   287	    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
   288	    try:
   289	        reg = load_registry(load_config())
   290	        agents = []
   291	        for agent_id in reg.agents:
   292	            try:
   293	                assert_qualified(reg, agent_id)
   294	                agents.append(agent_id)
   295	            except Unqualified:
   296	                print(
   297	                    f"tick: {agent_id} is not qualified; its new runs are refused", file=sys.stderr
   298	                )
   299	        app = build(None, agents)
   300	    except StoreUnavailable as exc:
   301	        print(f"tick: {exc}", file=sys.stderr)
   302	        return 4
   303	    except ConfigError as exc:
   304	        print(f"tick: config error: {exc}", file=sys.stderr)
   305	        return 2
   306	    except Exception as exc:  # noqa: BLE001 - any other start-up failure is a config error, never "1"
   307	        print(f"tick: config error: {type(exc).__name__}", file=sys.stderr)
   308	        return 2
   309	    return run_tick(app)
```
- `hadavin-sdk tick` is one short process per pass: `S/cli.py:134-135` -> `_tick()` (`:280-309`) -> `build(None, agents)` (`:299`) -> `run_tick(app)` (`:309`). `S/runtime/tick.py:1` says a scheduler runs it every 30-60 s.
- `build` makes a NEW audit sink object for that process (`S/app.py:208`). So the tick process has its own empty `_pending`; it cannot see the runtime process's `_pending`, and anything the tick itself parks in memory (`S/runtime/tick.py:133`, `:162`) is gone when the process exits at `S/cli.py:309`.
- What the tick process CAN see is the outbox table, because on the postgres store the chain uses the store's own connection (`S/audit/chain.py:94-96`). How the chain `_Db` is built for postgres (the factory) was not opened: UNVERIFIED beyond that docstring.

## A.10 Existing tests that park an audit event or test the outbox

| Test | What it proves |
|---|---|
| `tests/warden_port/test_audit_chain.py:505-517` `test_an_outcome_that_cannot_be_appended_waits_in_the_outbox` | chain sink on in-memory SQLite: a failing `_append` puts the outcome in `audit_outbox` (`:511`); a manual `log.reconcile()` returns 1 (`:514`), the event lands AFTER a later intent (`:515`), the outbox is empty (`:516`), a second call returns 0 (`:517`). |
| `tests/warden_port/test_audit_chain.py:643-680` `test_the_runtime_role_writes_and_reads_the_chain_but_cannot_rewrite_it` | real Postgres, connected AS the runtime role (`:665`): a row inserted into `audit_outbox` (`:673-676`) is drained by `log.reconcile()` (`:677`, comment "SELECT + DELETE on the outbox"). This is the proof that the grants are enough. |
| `tests/contracts/test_capabilities.py:36-45` | every audit kind: `reconcile()` returns 0 with nothing parked. |
| `tests/contracts/test_capabilities.py:48-60` | every audit kind: with `AuditEvent.model_dump_json` broken, `write_outcome` returns None and does not raise (`:58`); this path lands in `_pending` because the outbox insert also needs the JSON; `reconcile()` then returns 1 (`:59`). This is the only test found that exercises the in-memory `_pending` of the chain kind. |
| `tests/test_s2_audit.py:44-53` | `local_dir`: failed write -> one file in the outbox folder -> `reconcile()` == 1 -> folder empty. |
| `tests/test_review_fixes.py:94-106` | `local_dir`: outbox folder unwritable -> event kept in `_pending` -> `reconcile()` == 1. |
| `tests/test_review_pr3_round2.py:310-324` | `local_dir`: a torn outbox file is moved to `outbox/corrupt/` and does not block `reconcile`. |
| `tests/test_cuj.py:192-203` | full run on `local_dir`: the `result` event fails, the run still ends SUCCEEDED (`:199`), one file sits in the outbox (`:200`), a MANUAL `app.audit.reconcile()` writes it (`:202-203`). |
| `tests/test_k2_migrations.py:101` | the portal role cannot read `audit_outbox`. |

Every one of these calls `reconcile()` by hand. No test runs a tick and then checks the outbox. The step list is pinned by name at `tests/test_p7_tick.py:82-89`:

`tests/test_p7_tick.py` lines 81-89 (main 51c9fc4):
```
    81	def test_steps_order_and_summary_line_is_not_a_step(app, caplog):
    82	    assert [s.name for s in tick.STEPS] == [
    83	        "sweep",
    84	        "reconcile",
    85	        "stuck",
    86	        "checkpoint",
    87	        "purge_evidence",
    88	        "reprobe_sources",
    89	    ]
```

## A.11 Answer

What is never drained today:
1. Rows in the `audit_outbox` table (postgres store, and the SQLite twin of the memory store), written at `S/audit/chain.py:223-227`. Nothing in `src` reads or deletes them: the only reader is `ChainAudit.reconcile` (`S/audit/chain.py:239-244`) and it has no caller in `src` (A.4).
2. Events in `ChainAudit._pending` (`S/audit/chain.py:173`, appended at `:229`). Same single drain, same missing caller. They also die with the process.
3. For the `local_dir` kind: files in the outbox folder (`S/audit/local_dir.py:118-121`) and its `_pending` (`:123`).
So an outcome event that could not be appended at the moment it happened (a stop: `S/limits.py:46`; a run state: `S/runtime/agent_loop.py:241`; a stuck run: `S/runtime/tick.py:133`) never reaches the chain, and nothing reports it.

Smallest change that drains the outbox table: append ONE entry to `STEPS` in `S/runtime/tick.py:249-266`, after `reprobe_sources`, for example

```python
def audit_drain(ctx: TickContext) -> None:
    """Move parked audit outcomes (the outbox) into the audit. A kind without `reconcile` has nothing to do."""
    fn = getattr(ctx.app.audit, "reconcile", None)
    if fn is not None:
        fn()

TickStep("audit_drain", 0, audit_drain),
```

- The name must be new and match `[a-z_]+` (`S/runtime/tick.py:59`). `reconcile` is taken (`:251`). `audit_drain` is a proposal, not an existing name.
- It calls `ctx.app.audit.reconcile()`, which is on the Protocol (`S/audit/protocol.py:27-29`), so the `getattr` guard copied from `S/runtime/tick.py:179` is belt and braces only.
- No migration (A.5 last point), no grant change (A.8), and the runtime-role test already proves the SQL works (A.10 second row).
- One test must change: `tests/test_p7_tick.py:82-89`. PR 76 appends `stop_guard_probe` to the same list (its `tests/test_p7_tick.py:82-90` and `S/runtime/tick.py` hunk, see B.7), so the two tickets collide on that line.
- The contract says "append" (`S/runtime/tick.py:4-5`), so the drain would run after `checkpoint` and drained rows are signed one tick later. Placing it before `checkpoint` would break the append rule; that is a ticket decision.
- Decisions the ticket must make, because `reconcile` gives only a count: (a) should the step FAIL when rows remain (today a still-failing append is silently skipped, `S/audit/chain.py:253-254`, so the step would report ok with a full outbox); (b) wrap `chain.py:243` so one bad row does not block the rest (A.1 weak point 1); (c) add a LIMIT at `chain.py:239`.

How the runtime process could drain its own `_pending` at the next write: the tick cannot do it (A.9). Inside `ChainAudit`, after a successful append in `write_outcome` (`S/audit/chain.py:218`) and `write_intent` (`:209`), run the first loop of `reconcile` when the list is not empty:

```python
if self._pending:
    for event in list(self._pending):   # the same loop as chain.py:234-237
        if self._drain(event):
            self._pending.remove(event)
```

- `_drain` calls `_append` directly (`S/audit/chain.py:250`), not `write_outcome`, so there is no recursion, and a duplicate is absorbed (`:251-252`).
- The check is one list truth test per write when nothing is parked.
- `_pending` has no lock (`S/audit/chain.py:173`); two threads writing at once could both try the same event. The second gets `DuplicateEvent` (counted as done) and then `list.remove` raises `ValueError` for the loser. A ticket that adds this must add a lock or tolerate the `ValueError`.
- This does not help a process that restarts before its next successful write: those events are lost. Only the outbox table survives a restart.
- The same change would be needed in `S/audit/local_dir.py:110-124` for that kind.

---

# STEP B. Stop state with a separate reset identity

## B.1 `kill_switch` DDL and seed row (main)

`src/hadavin_sdk/store/migrations/0001_core.sql` lines 94-100 (main 51c9fc4):
```
    94	CREATE TABLE kill_switch (
    95	    id             SMALLINT PRIMARY KEY CHECK (id = 1),
    96	    schema_version INTEGER NOT NULL,
    97	    "on"           BOOLEAN NOT NULL,
    98	    "by"           TEXT,
    99	    ts             TIMESTAMPTZ NOT NULL
   100	);
```

`src/hadavin_sdk/store/migrations/0003_approvals_tick.sql` lines 24-27 (main 51c9fc4):
```
    24	-- The kill switch row always exists; a missing row is read as "stopped" (fail closed).
    25	INSERT INTO kill_switch (id, schema_version, "on", "by", ts)
    26	VALUES (1, 1, FALSE, NULL, now())
    27	ON CONFLICT (id) DO NOTHING;
```

## B.2 Postgres store read and write (main)

`src/hadavin_sdk/store/postgres.py` lines 440-470 (main 51c9fc4):
```
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
   465	
   466	    def get_tick_state(self, step: str) -> TickState | None:
   467	        found = self._select(TickState, "tick_state", "step = %s", (step,))
   468	        return found[0] if found else None
   469	
   470	    def save_tick_state(self, state: TickState) -> None:
```
One method writes both directions: `set_kill_switch` (`S/store/postgres.py:453-464`) is an upsert that sets `"on"` to whatever it is given. The login needs INSERT and UPDATE on `kill_switch`.

## B.3 Memory store, Protocol, model (main)

`src/hadavin_sdk/store/memory.py` lines 218-224 (main 51c9fc4):
```
   218	    def get_kill_switch(self) -> KillSwitch:
   219	        with self._lock:
   220	            return self._kill.model_copy(deep=True)
   221	
   222	    def set_kill_switch(self, ks: KillSwitch) -> None:
   223	        with self._lock:
   224	            self._kill = ks.model_copy(deep=True)
```

`src/hadavin_sdk/store/protocol.py` lines 112-116 (main 51c9fc4):
```
   112	    def get_kill_switch(self) -> KillSwitch:
   113	        """A missing or unreadable switch row reads as ON (fail closed)."""
   114	        ...
   115	
   116	    def set_kill_switch(self, ks: KillSwitch) -> None: ...
```

`src/hadavin_sdk/models.py` lines 256-259 (main 51c9fc4):
```
   256	class KillSwitch(Shape):
   257	    on: bool = False
   258	    by: str | None = None
   259	    ts: datetime = Field(default_factory=now)
```
`self._kill = KillSwitch()` is set at `S/store/memory.py:39`.

## B.4 `S/limits.py` in full (main)

`src/hadavin_sdk/limits.py` lines 1-51 (main 51c9fc4):
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
On main `stop` and `reset` use the SAME store handle (`self.store`, `S/limits.py:45`, `:51`). `by` is the raw typed name, written to the row and to the audit event.

## B.5 `limits stop|reset` in `S/cli.py` (main)

`src/hadavin_sdk/cli.py` lines 93-95 (main 51c9fc4):
```
    93	    lim = sub.add_parser("limits", help="kill switch")
    94	    lim.add_argument("action", choices=["stop", "reset"])
    95	    lim.add_argument("--by", required=True)
```

`src/hadavin_sdk/cli.py` lines 166-209 (main 51c9fc4):
```
   166	    b = cfg.backends
   167	    if args.cmd == "audit" and b.audit.kind != "chain":
   168	        print(
   169	            "refused: audit verify reads a chain audit (backends.audit.kind: chain)",
   170	            file=sys.stderr,
   171	        )
   172	        return 2
   173	    if b.store.kind == "memory":
   174	        # The memory store lives inside one running process; a separate CLI process cannot reach it, so
   175	        # claiming "stopped" here would be a lie. Use App.limits.stop() in-process until Postgres arrives.
   176	        what = "audit verify" if args.cmd == "audit" else "the kill switch"
   177	        print(
   178	            f"refused: {what} needs a shared store (Postgres). With the memory store, "
   179	            "use the running process's app (app.limits, app.audit).",
   180	            file=sys.stderr,
   181	        )
   182	        return 2
   183	    try:
   184	        secrets = make("secrets", b.secrets)
   185	        # Same start-up probe as app.build: a missing DSN is a clean ConfigError, not a KeyError mid-build.
   186	        platform_secrets.check(secrets, [b.signer, b.anchor, b.store, b.audit], set())
   187	        signer = make("signer", b.signer, secrets)
   188	        anchor = make("anchor", b.anchor, secrets)
   189	        store = make("store", b.store, secrets)
   190	        audit = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
   191	    except StoreUnavailable:
   192	        if args.cmd == "audit":
   193	            print("could not verify: the store is unreachable", file=sys.stderr)
   194	            return 3
   195	        print(
   196	            f"kill switch NOT {'set' if args.action == 'stop' else 'reset'}: the store is unreachable. "
   197	            "Nothing was changed. Fix the store, then run the same command again.",
   198	            file=sys.stderr,
   199	        )
   200	        return 4
   201	    except ConfigError as exc:
   202	        if args.cmd != "audit":
   203	            raise
   204	        # An unreachable or un-migrated store is not evidence of tampering: never exit 1 for it.
   205	        print(f"could not verify: {exc}", file=sys.stderr)
   206	        return 3
   207	    if args.cmd == "audit":
   208	        return audit_verify(audit)
   209	    return kill_switch(Limits(store, audit, reg), args.action, args.by)
```

`src/hadavin_sdk/cli.py` lines 366-410 (main 51c9fc4):
```
   366	def _kill_switch_store_down(what: str, exc: BaseException) -> int:
   367	    """4 when the store cannot be reached; 2 when it answers but is not ready (missing table or grant)."""
   368	    if is_connectivity_error(exc):
   369	        print(
   370	            f"kill switch NOT {what}: the store is unreachable. Nothing was changed. "
   371	            "Fix the store, then run the same command again.",
   372	            file=sys.stderr,
   373	        )
   374	        return 4
   375	    print(
   376	        f"kill switch NOT {what}: the store answered with an error ({type(exc).__name__}); run "
   377	        "hadavin-sdk migrate and check the runtime role's grants. Nothing was changed.",
   378	        file=sys.stderr,
   379	    )
   380	    return 2
   381	
   382	
   383	def kill_switch(limits: Limits, action: str, by: str) -> int:
   384	    """Run stop/reset for a caller (the CLI once a shared store exists, or an in-process admin hook).
   385	
   386	    Exit codes: 0 done; 3 reset refused because the audit store is unavailable (the switch stays ON); 4 the
   387	    store is unreachable (the switch was NOT changed).
   388	    """
   389	    if action == "stop":
   390	        try:
   391	            limits.stop(by)
   392	        except AuditUnavailable:
   393	            raise
   394	        except Exception as exc:  # noqa: BLE001 - classified below
   395	            return _kill_switch_store_down("set", exc)
   396	        print(f"kill switch ON (by {by})")
   397	        return 0
   398	    try:
   399	        limits.reset(by)
   400	    except AuditUnavailable:
   401	        print(
   402	            "refused: the audit store is unavailable, so the reset cannot be recorded. "
   403	            "The kill switch stays ON. Fix the audit store, then try again.",
   404	            file=sys.stderr,
   405	        )
   406	        return 3
   407	    except Exception as exc:  # noqa: BLE001 - classified below
   408	        return _kill_switch_store_down("reset", exc)
   409	    print(f"kill switch OFF (by {by})")
   410	    return 0
```
One store is built from the one configured DSN (`S/cli.py:189`) and used for stop and reset alike (`:209`). Exit codes: 0 done, 2 not ready, 3 reset refused (audit down), 4 store unreachable (`:366-410`).

## B.6 `S/store/migrate.py` (main)

`src/hadavin_sdk/store/migrate.py` lines 20-70 (main 51c9fc4):
```
    20	MIGRATIONS = Path(__file__).parent / "migrations"
    21	
    22	
    23	@dataclass(frozen=True)
    24	class Grant:
    25	    """What the roles get on one relation. `runtime` is the privilege list for the runtime role; `portal` says the
    26	    read-only portal role may SELECT it. A relation not in `GRANTS` gets nothing, so `check_grants` (run by
    27	    `migrate` and by CI) refuses a migration that creates one."""
    28	
    29	    kind: Literal["table", "view", "sequence"]
    30	    runtime: str
    31	    portal: bool = False
    32	    purge: str = (
    33	        ""  # table-level privileges of the purge role (the evidence deleter) on this relation
    34	    )
    35	    # Columns the purge role may SELECT (a DELETE's WHERE needs them) and nothing else: it cannot read a stored
    36	    # original or a tool result.
    37	    purge_cols: tuple[str, ...] = ()
    38	
    39	
    40	_RW = "SELECT, INSERT, UPDATE"
    41	_APPEND = "SELECT, INSERT"  # written once, never changed
    42	# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
    43	# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
    44	# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
    45	# `redaction_maps`, `events`, `tick_state.detail` or secrets.
    46	GRANTS: dict[str, Grant] = {
    47	    "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
    48	    "plans": Grant("table", _RW, portal=True),
    49	    "gate_decisions": Grant("table", _APPEND, portal=True),
    50	    "approval_requests": Grant("table", _RW, portal=True),
    51	    "approval_decisions": Grant("table", _APPEND, portal=True),
    52	    "dead_letters": Grant("table", _APPEND),
    53	    "spend": Grant("table", _RW),
    54	    "spend_month": Grant("table", _RW),
    55	    "kill_switch": Grant("table", _RW),
    56	    "tick_state": Grant("table", _RW),
    57	    "audit_entries": Grant("table", _APPEND, portal=True),
    58	    "audit_checkpoints": Grant("table", _APPEND, portal=True),
    59	    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    60	    # K5-core: append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
    61	    # The runtime role appends and reads evidence; only the purge role (its own identity) deletes it.
    62	    "tool_calls": Grant(
    63	        "table", _APPEND, purge="DELETE", purge_cols=("call_id", "run_id", "created_at")
    64	    ),
    65	    "redaction_maps": Grant("table", _RW, purge="DELETE", purge_cols=("run_id", "updated_at")),
    66	    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    67	    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
    68	}
    69	_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1  # one fixed key for every migrate run
    70	_ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
```

`src/hadavin_sdk/store/migrate.py` lines 140-170 (main 51c9fc4):
```
   140	        ]
   141	        for m in _CREATE.finditer(text):
   142	            kind, name = m.group(1).lower(), m.group(2).lower()
   143	            found[name] = kind
   144	            if kind == "table":
   145	                for col in _SERIAL.findall(_table_body(text, m.end())):
   146	                    found[f"{name}_{col.lower()}_seq"] = "sequence"
   147	    return found, unread
   148	
   149	
   150	def check_grants(paths: list[Path]) -> list[str]:
   151	    """Problems between the migrations and `GRANTS`: a relation they create with no entry (it would get no grant
   152	    and fail at runtime), an entry for a relation no migration creates, or an entry of the wrong kind."""
   153	    created, problems = _scan(paths)
   154	    problems += [
   155	        f"{n} ({k}) is created by a migration but is not in GRANTS"
   156	        for n, k in sorted(created.items())
   157	        if n not in GRANTS
   158	    ]
   159	    for name, grant in sorted(GRANTS.items()):
   160	        if name not in created:
   161	            problems.append(f"GRANTS names {name}, which no migration creates")
   162	        elif created[name] != grant.kind:
   163	            problems.append(
   164	                f"GRANTS says {name} is a {grant.kind}; the migrations create a {created[name]}"
   165	            )
   166	    return problems
   167	
   168	
   169	def _apply_grants(db, role_name: str, privileges, columns=None) -> None:
   170	    """Reset the role's rights on every relation in `GRANTS`, then give back what `privileges(grant)` names."""
```

`src/hadavin_sdk/store/migrate.py` lines 280-360 (main 51c9fc4):
```
   280	    return extra
   281	
   282	
   283	def migrate(
   284	    dsn: str,
   285	    *,
   286	    runtime_role: str | None = None,
   287	    portal_role: str | None = None,
   288	    purge_role: str | None = None,
   289	    iam_auth: bool = False,
   290	    region: str | None = None,
   291	    sslmode: str | None = None,
   292	    sslrootcert: str | None = None,
   293	) -> list[str]:
   294	    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
   295	    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
   296	    relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
   297	    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database."""
   298	    for role in (runtime_role, portal_role, purge_role):
   299	        if role is not None and not _ROLE.fullmatch(role):
   300	            raise ConfigError(f"not a plain database role name: {role!r}")
   301	    named = [r for r in (runtime_role, portal_role, purge_role) if r is not None]
   302	    if len(set(named)) != len(named):
   303	        raise ConfigError("the runtime, portal and purge roles must be different roles")
   304	    files = _migration_files()
   305	    if problems := check_ledger(files) + check_grants(files):
   306	        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
   307	    applied = []
   308	    with (
   309	        connect(
   310	            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
   311	        ) as db,
   312	        db.transaction(),
   313	    ):
   314	        db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
   315	        db.execute(
   316	            "CREATE TABLE IF NOT EXISTS schema_migrations "
   317	            "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
   318	        )
   319	        done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
   320	        if gone := sorted(done - {p.stem for p in files}):
   321	            raise ConfigError(
   322	                f"applied migrations have no file in this release: {', '.join(gone)}. If a migration file was renamed "
   323	                "and its tables already exist, rename the ledger row by hand (change the version of that row in the "
   324	                "schema_migrations table to the new file name); if its content changed too, drop what it made and "
   325	                "run migrate again"
   326	            )
   327	        for path in files:
   328	            if path.stem in done:
   329	                continue
   330	            db.execute(path.read_text(encoding="utf-8"))  # a file shipped in this package
   331	            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
   332	            applied.append(path.stem)
   333	        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
   334	        for a in named:
   335	            for b in named:
   336	                if a != b and db.execute(q, (a, b)).fetchone()[0]:
   337	                    raise ConfigError(
   338	                        "the runtime, portal and purge roles must not be members of each other"
   339	                    )
   340	        if runtime_role:
   341	            _apply_grants(db, runtime_role, lambda g: g.runtime)
   342	            if bad := effective_problems(db, runtime_role, lambda g: g.runtime if g else ""):
   343	                raise ConfigError(
   344	                    "the runtime role holds more than the grant map: " + "; ".join(bad[:20])
   345	                )
   346	        if purge_role:
   347	            _apply_grants(db, purge_role, lambda g: g.purge, lambda g: g.purge_cols)
   348	            if bad := effective_problems(
   349	                db, purge_role, lambda g: g.purge if g else "", lambda g: g.purge_cols if g else ()
   350	            ):
   351	                raise ConfigError(
   352	                    "the purge role holds more than the grant map: " + "; ".join(bad[:20])
   353	                )
   354	        if portal_role:
   355	            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
   356	            if extra := _excess_privileges(db, portal_role):
   357	                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
   358	                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
   359	                )
   360	    return applied
```
Facts:
- `Grant` has three privilege slots: `runtime`, `portal` (bool), `purge` (+ `purge_cols`) (`S/store/migrate.py:23-37`). No reset or stop slot.
- `"kill_switch": Grant("table", _RW)` (`S/store/migrate.py:55`), `_RW = "SELECT, INSERT, UPDATE"` (`:40`). So the runtime role may UPDATE the row in both directions: it can stop AND reset. There is no separation at the grant level on main.
- `migrate()` keywords: `runtime_role`, `portal_role`, `purge_role`, `iam_auth`, `region`, `sslmode`, `sslrootcert` (`:283-293`). Role-name check `:298-300`, distinct-roles check `:301-303` (message "the runtime, portal and purge roles must be different roles"), membership check `:333-339` (message "... must not be members of each other"), then one grant loop per role: runtime `:340-345`, purge `:346-353`, portal `:354-359`.
- `check_grants` (`:150-166`) refuses a relation that a migration creates and `GRANTS` does not name, and the reverse. A new table or view for the stop state must get a `GRANTS` entry.
- The CLI passes the roles through `_migrate` (`S/cli.py:312-346`) from `--runtime-role`, `--purge-role`, `--portal-role` (`S/cli.py:98-105`).

## B.7 Every place the stop state is read (main, grep `kill_switch|KillSwitch|is_stopped|stopped` over `src`)

Reads of the state:
- `S/limits.py:22` `self.store.get_kill_switch().on` inside `Limits.blocked` (the one reader of the switch in the runtime).
- `S/runtime/agent_loop.py:250-253` `_limits_stop`: `"kill_switch" in blocked` -> run goes to STOPPED. Called at `S/runtime/agent_loop.py:404`, `:466`, `:505`.
- `S/runtime/agent_loop.py:817-818`: the recheck before execution, rule id `recheck.limits.kill_switch` -> STOPPED. The `_recheck` body that produces this id was not opened: UNVERIFIED how it reads the switch (the grep shows no second `get_kill_switch` call in `src`, so it most likely goes through `Limits.blocked`).
- Store implementations: `S/store/postgres.py:444-451` (missing row reads as ON, `:446-450`), `S/store/memory.py:218-220`, Protocol `S/store/protocol.py:112-114`.
Writes: `S/limits.py:45` (stop), `S/limits.py:51` (reset), implemented at `S/store/postgres.py:453-464` and `S/store/memory.py:222-224`.
CLI: `S/cli.py:209`, `:383-410`.
There is no `is_stopped` anywhere in `src`. The other `stopped` hits are audit `result="stopped"` strings in `agent_loop.py` (`:259`, `:400`, `:419`, `:429`, `:492`, `:509`, `:527`, `:549`) and two comments in `S/sources/kubernetes.py:296,301`; none reads the switch.

## B.8 Tests on main that pin role names, messages, migration lists

`tests/test_k2_migrations.py` lines 374-384 (main 51c9fc4):
```
   374	def test_migrate_refuses_roles_that_are_members_of_each_other(roles):
   375	    import psycopg
   376	    from psycopg import sql
   377	
   378	    dsn, runtime, portal = roles
   379	    with psycopg.connect(dsn, autocommit=True) as db:
   380	        db.execute(
   381	            sql.SQL("GRANT {} TO {}").format(sql.Identifier(runtime), sql.Identifier(portal))
   382	        )
   383	    with pytest.raises(ConfigError, match="members of each other"):
   384	        mig.migrate(dsn, runtime_role=runtime, portal_role=portal)
```

`tests/test_k5_round10_postgres.py` lines 153-158 (main 51c9fc4):
```
   153	def test_a_superuser_as_the_purge_role_is_refused():
   154	    for dsn, _schema, _rt, pu, run in _prepared():
   155	        with _connect(dsn) as db:
   156	            db.execute(f'ALTER ROLE "{pu}" SUPERUSER')
   157	        with pytest.raises(ConfigError, match="superuser|members of each other"):
   158	            run()
```

`tests/test_migration_numbers_guards.py` lines 356-363 (main 51c9fc4):
```
   356	def _sha(path: Path) -> str:
   357	    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
   358	
   359	
   360	def test_the_real_folder_matches_the_released_manifest(mn):
   361	    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
   362	    assert mn.released_problems(mn.MIGRATIONS, manifest) == []
   363	    assert len(manifest) == 5
```

`tests/test_p2_postgres.py` lines 276-294 (main 51c9fc4):
```
   276	def test_audit_checkpoints_migration_adds_alg_and_label_and_old_rows_get_defaults(fresh_dsn):
   277	    """Apply 0001-0003 only, insert a pre-upgrade checkpoint row, then migrate: the row loads with NULL (not recorded)."""
   278	    import psycopg
   279	
   280	    old = [p for p in sorted(MIGRATIONS.glob("*.sql")) if p.stem < "0004"]
   281	    with psycopg.connect(fresh_dsn, autocommit=True) as db:
   282	        for path in old:
   283	            db.execute(path.read_text(encoding="utf-8"))
   284	        db.execute(
   285	            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
   286	        )
   287	        for path in old:
   288	            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
   289	        db.execute("INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (1, 'h', 's')")
   290	    assert migrate(fresh_dsn) == ["0004_audit_checkpoint_meta", "0005_evidence"]
   291	    with psycopg.connect(fresh_dsn, autocommit=True) as db:
   292	        assert db.execute("SELECT seq, alg, key_label FROM audit_checkpoints").fetchall() == [
   293	            (1, None, None)
   294	        ]
```

`tests/fixtures/migrations_released.json` (main, whole file):
```json
{
  "0001_core": "d60b37ba5f929c7ae888f53920bd58c6c823b27a80d7ca82074aefdb42832374",
  "0002_audit_chain": "17325ed9f0a67cb276132d5cc0a42c6997d1191123122ba13491dd0413ac8dc3",
  "0003_approvals_tick": "f3e2a56cc11ee1b3c009f08dcd1aafc5bb52711dbd28368ad56ac8d06a2fe346",
  "0004_audit_checkpoint_meta": "1e0a67c9a9d22245dbeb54c65ff6b31e6392927f64c41deb955018595aef76a7",
  "0005_evidence": "d8a714926a61bc1a6ec45137a9563df20ca44a796f63f01f99d2028d87558ad9"
}
```

What these pin:
- `tests/test_k2_migrations.py:383` and `tests/test_k5_round10_postgres.py:157`: the text "members of each other". PR 76 changes the sentence to "the runtime, portal, purge, reset and stop roles must not be members of each other", which still holds that text.
- No test on main pins "must be different roles" (grep over `tests`: no hit).
- `tests/test_migration_numbers_guards.py:360-363`: the real folder matches the manifest and the manifest has exactly 5 entries. A new file numbered above the released ones is fine for `released_problems` (`tests/test_migration_numbers_guards.py:371-374`), so 0006 and 0007 pass as long as the manifest is not extended; when they are released the manifest and the `== 5` both change.
- `tests/test_p2_postgres.py:290`: `migrate(fresh_dsn) == ["0004_audit_checkpoint_meta", "0005_evidence"]`. Any new migration breaks this line; PR 76 rewrites it (B.9).
- `tests/test_k5_fixes2.py:307` also pins `rows == ["0005_evidence"]` (found by grep; the test around it was not opened: UNVERIFIED context).
- `tests/test_migration_numbers_guards.py` and `tests/fixtures/migrations_released.json` do NOT exist on PR 76 or PR 78 (they came to main after the fork point), so neither branch has been run against them.
- `S/store/migration_numbers.py` (main only) holds a lexer with a refusal list for migration files; its docstring says nothing calls it until a later change P3a-2 (`S/store/migration_numbers.py:5-6`). Whether 0007's statements (`UPDATE`, `ALTER TABLE ... ENABLE ALWAYS TRIGGER`, `CREATE VIEW`) pass that refusal list was not checked: UNVERIFIED.

## B.9 PR 76 (`origin/core/P2a-1`)

Head: 7f323491f91910ed3af03d6fae0cbabd1e23f6bc. Fork point from main: 1e4752f.

Commits (`git log --oneline origin/main..origin/core/P2a-1`):
```
7f32349 P2a-1 second pass: non-superuser migrator world, pilot tests name the real roles, mutants file, NOINHERIT owner check, loop/rollback/contract tests
d1855a9 P2a-1: stop probe, limits check, runbook, busy mapping, demo refused, pilot CLI fix, loop and rollback tests, PG16+17 matrix
e323ac7 P2a-1: tests that kill two surviving hand mutants (group check in the guard, version-only stale pair)
38a1f55 P2a-1: pilot and CLI tests learn the label key secret and the reset role
ca9b449 P2a-1: build the two kill-switch statements as whole literals (no string building)
63d272e P2a-1: CLI and config tests for the stop state
f0465df Merge origin/core/P4d-a2 into core/P2a-1
0b4ca7a WIP P2a-1: fix existing tests for the new API, add labelkey, memory and real-login Postgres tests
c31f336 P4d-a2-i and P4d-b: money validators, cost rounding, route price check, spend reservations (memory and Postgres, migration 0006)
77ace26 WIP P2a-1: stop-state requests, keyed labels, reset by (version, open) pair
1a885f3 P4d-a1: contract harness and test helpers (store_pair, pg_driver, require_backend, session-end check)
```
Note: this branch also carries P4d work (c31f336: money validators, route price check, spend reservations, migration 0006) and P4d-a1 (1a885f3). The stop-state work is the P2a-1 commits.

Diff stat against main (`git diff --stat origin/main...origin/core/P2a-1`):
```
 .github/workflows/ci.yml                           |  13 +-
 CHANGELOG.md                                       |   2 +
 docs/stop-state-runbook.md                         |  76 +++
 src/hadavin_sdk/app.py                             |  59 +-
 src/hadavin_sdk/audit/labelkey.py                  |  42 ++
 src/hadavin_sdk/backends/table.py                  |   5 +
 src/hadavin_sdk/cli.py                             | 247 ++++++++-
 src/hadavin_sdk/config.py                          |  73 ++-
 src/hadavin_sdk/defaults.py                        |  26 +
 src/hadavin_sdk/limits.py                          | 166 +++++-
 src/hadavin_sdk/llm/common.py                      |  22 +-
 src/hadavin_sdk/llm/fake.py                        |  13 +-
 src/hadavin_sdk/models.py                          |  75 ++-
 src/hadavin_sdk/runtime/agent_loop.py              |  11 +-
 src/hadavin_sdk/runtime/stop_state.py              |  47 ++
 src/hadavin_sdk/runtime/tick.py                    |  21 +
 src/hadavin_sdk/store/memory.py                    | 294 +++++++++-
 src/hadavin_sdk/store/migrate.py                   | 288 +++++++++-
 .../store/migrations/0006_spend_reservations.sql   |  67 +++
 .../store/migrations/0007_kill_switch_guard.sql    |  82 +++
 src/hadavin_sdk/store/postgres.py                  | 595 ++++++++++++++++++++-
 src/hadavin_sdk/store/protocol.py                  | 234 +++++++-
 tests/conftest.py                                  |  17 +
 tests/contracts/conftest.py                        | 107 +++-
 tests/contracts/kinds/__init__.py                  |  29 +
 tests/contracts/kinds/builtin.py                   |   7 +
 tests/contracts/kinds/store_postgres.py            | 249 ++++++++-
 tests/contracts/store_support.py                   | 136 +++++
 tests/contracts/test_cost_rounding.py              | 147 +++++
 tests/contracts/test_pg_driver.py                  | 151 ++++++
 tests/contracts/test_store.py                      | 132 ++++-
 tests/contracts/test_store_money_edges.py          | 207 +++++++
 tests/contracts/test_store_registry.py             | 322 +++++++++++
 tests/contracts/test_store_reserve.py              | 472 ++++++++++++++++
 tests/contracts/test_store_reserve_pg.py           | 145 +++++
 tests/k5_support.py                                |   2 +-
 tests/stop_state_helpers.py                        |  34 ++
 tests/stop_state_mutants.py                        | 114 ++++
 tests/test_cuj.py                                  |  23 +-
 tests/test_k2_migrations.py                        |  36 +-
 tests/test_k3_pilot.py                             |   2 +-
 tests/test_k3_pilot_env.py                         |  24 +-
 tests/test_k5_fixes2.py                            |  20 +-
 tests/test_k5_postgres.py                          |   2 +-
 tests/test_k5_round10_postgres.py                  |  11 +-
 tests/test_k5_round5.py                            |   2 +-
 tests/test_k5_round8_postgres.py                   |   4 +-
 tests/test_k5_tools.py                             |   4 +-
 tests/test_labelkey.py                             |  87 +++
 tests/test_p2_postgres.py                          |  25 +-
 tests/test_p3b_neutral_audit.py                    |   9 +-
 tests/test_p7_store.py                             |  15 +-
 tests/test_p7_tick.py                              |   3 +-
 tests/test_review_fixes.py                         |   6 +-
 tests/test_review_pr3_round2.py                    |  21 +-
 tests/test_route_prices.py                         |  59 ++
 tests/test_s5_runtime.py                           |  15 +-
 tests/test_stop_state_cli.py                       | 194 +++++++
 tests/test_stop_state_config.py                    |  53 ++
 tests/test_stop_state_db.py                        | 432 +++++++++++++++
 tests/test_stop_state_limits.py                    | 107 ++++
 tests/test_stop_state_loop.py                      |  39 ++
 tests/test_stop_state_memory.py                    | 147 +++++
 tests/test_stop_state_probe.py                     | 219 ++++++++
 tests/test_stop_state_rollback.py                  |  21 +
 tests/warden_port/test_audit_chain.py              |   3 +-
 66 files changed, 6128 insertions(+), 184 deletions(-)
```

Main commits the branch does not hold (`git log --oneline 1e4752f..origin/main`):
```
51c9fc4 tests: run the unit suite on 3 pytest-xdist workers (#99)
81a5aad tests: make the timing harness robust under load (growth ratio, CPU time) (#98)
ed96c75 P0a: guard test that pglast (GPL) never reaches src or a runtime dependency list (#71)
e5aa945 ci: treat wip/cloud-* builder branches like the handover lane in the security guard (#97)
a8b4d8e P6a-1: client-profile check (test objects refused in pilot/prod builds; dev config with a real model needs made_up_data_only) (#72)
2a8c2aa Fix flaky askdata copy-program test (child closed its pipe early) (#88)
453385a peel: run_id on Runtime.handle (#87)
2742c1b ci: gitleaks scans only the history reachable from the checked-out head (#90)
0dabf1f P3a-1: migration rule as pure functions (file numbers, late files, recipe, gone message, lexer, refusal list) (#68)
6bd2d83 ci: stage mutants step + pinned-Unicode env (S0 lead item) (#82)
13ebfaf gitleaks: ignore two fake test fixtures in core/P2d-1 history (temporary) (#81)
c709df3 P0t: stages are exactly demo, pilot, prod (R449); the old first stage name is refused (#67)
```
Files changed on BOTH sides since the fork (candidates for conflicts; no merge was tried):
```
.github/workflows/ci.yml
CHANGELOG.md
src/hadavin_sdk/app.py
src/hadavin_sdk/backends/table.py
src/hadavin_sdk/config.py
src/hadavin_sdk/defaults.py
src/hadavin_sdk/models.py
src/hadavin_sdk/runtime/agent_loop.py
src/hadavin_sdk/store/postgres.py
tests/contracts/test_store.py
tests/k5_support.py
tests/test_k3_pilot.py
tests/test_k3_pilot_env.py
tests/test_k5_round5.py
tests/test_k5_round8_postgres.py
tests/test_k5_tools.py
tests/test_p7_store.py
tests/test_p7_tick.py
tests/warden_port/test_audit_chain.py
```

### B.9.1 Migration 0007 in full

`src/hadavin_sdk/store/migrations/0007_kill_switch_guard.sql` lines 1-82 at origin/core/P2a-1:
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

### B.9.2 `S/store/migrate.py` diff in full (Grant slots, GRANTS, the three functions, roles, `migrate()` keywords)

`git diff origin/main...origin/core/P2a-1 -- src/hadavin_sdk/store/migrate.py`:
```diff
diff --git a/src/hadavin_sdk/store/migrate.py b/src/hadavin_sdk/store/migrate.py
index 668c5b8..5f049ff 100644
--- a/src/hadavin_sdk/store/migrate.py
+++ b/src/hadavin_sdk/store/migrate.py
@@ -12,10 +12,12 @@ from dataclasses import dataclass
 from pathlib import Path
 from typing import Literal
 
+from psycopg import errors as pg_errors
 from psycopg import sql
 
+from hadavin_sdk import defaults
 from hadavin_sdk.errors import ConfigError
-from hadavin_sdk.store.postgres import connect
+from hadavin_sdk.store.postgres import connect, table_privileges
 
 MIGRATIONS = Path(__file__).parent / "migrations"
 
@@ -35,6 +37,8 @@ class Grant:
     # Columns the purge role may SELECT (a DELETE's WHERE needs them) and nothing else: it cannot read a stored
     # original or a tool result.
     purge_cols: tuple[str, ...] = ()
+    reset: str = ""  # privilege list of the reset group (the only role that may clear a stop)
+    stop: str = ""  # privilege list of the stop login
 
 
 _RW = "SELECT, INSERT, UPDATE"
@@ -52,7 +56,14 @@ GRANTS: dict[str, Grant] = {
     "dead_letters": Grant("table", _APPEND),
     "spend": Grant("table", _RW),
     "spend_month": Grant("table", _RW),
-    "kill_switch": Grant("table", _RW),
+    "spend_reservations": Grant("table", _RW),  # no DELETE: v1 has no pruning (P4d-b)
+    # A stop is an INSERT through a function (the owner's rights); no role holds any right on these tables.
+    "kill_switch": Grant("table", ""),
+    "kill_switch_stop_requests": Grant("table", ""),
+    "kill_switch_stop_requests_id_seq": Grant("sequence", ""),
+    "kill_switch_login_labels": Grant("table", ""),
+    "kill_switch_resets": Grant("table", "SELECT"),
+    "kill_switch_state": Grant("view", "SELECT", reset="SELECT", stop="SELECT"),
     "tick_state": Grant("table", _RW),
     "audit_entries": Grant("table", _APPEND, portal=True),
     "audit_checkpoints": Grant("table", _APPEND, portal=True),
@@ -90,6 +101,191 @@ _UNREAD = re.compile(
 )
 
 
+# --- the three kill-switch functions, re-issued by `migrate()` on every run -----------------------------------------
+# `{S}` is the schema (an identifier), `{N}` the cap on open stop requests and `{GROUP}` the reset group (literals).
+# Every literal brace is doubled because the text goes through `sql.SQL(...).format`.
+_RETURNS = 'RETURNS TABLE ("on" boolean, "by" text, ts timestamptz, schema_version int, version bigint, open_requests int)'
+_LABEL_RE = "'^id:[A-Za-z0-9_-]{1,32}:[0-9a-f]{32}$'"  # passed as an argument, so its braces are not doubled
+_STOP_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_stop(p_by text) {RETURNS}
+LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
+DECLARE n int;
+BEGIN
+  IF p_by IS NULL OR p_by !~ {LABEL} THEN
+    RAISE EXCEPTION 'kill switch: stop label not accepted' USING ERRCODE = 'HD004'; END IF;
+  PERFORM 1 FROM {S}.kill_switch k WHERE k.id = 1;
+  SELECT count(*) INTO n FROM (SELECT 1 FROM {S}.kill_switch_stop_requests WHERE cleared_by IS NULL LIMIT {N}) q;
+  IF n < {N} THEN
+    INSERT INTO {S}.kill_switch_stop_requests ("by") VALUES (p_by);
+  END IF;
+  RETURN QUERY SELECT s."on", s."by", s.ts, s.schema_version, s.version, s.open_requests
+               FROM {S}.kill_switch_state s;
+  IF NOT FOUND THEN
+    RETURN QUERY SELECT true,
+                        coalesce((SELECT r."by" FROM {S}.kill_switch_stop_requests r
+                                  WHERE r.cleared_by IS NULL ORDER BY r.id LIMIT 1), p_by),
+                        now(), 1, 0::bigint,
+                        (SELECT count(*) FROM {S}.kill_switch_stop_requests WHERE cleared_by IS NULL)::int;
+  END IF;
+END $f$"""
+_RESET_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_reset(p_by text, p_expected_version bigint,
+  p_expected_open int) {RETURNS}
+LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
+DECLARE v bigint; was_on boolean; n int;
+BEGIN
+  IF p_by IS NULL OR p_by !~ {LABEL} THEN
+    RAISE EXCEPTION 'kill switch: name not accepted' USING ERRCODE = 'HD004'; END IF;
+  SELECT k.version, k."on" INTO v, was_on FROM {S}.kill_switch k WHERE k.id = 1 FOR UPDATE;
+  IF NOT FOUND THEN RAISE EXCEPTION 'kill switch: row missing' USING ERRCODE = 'HD005'; END IF;
+  IF p_expected_version IS NULL OR v <> p_expected_version THEN
+    RAISE EXCEPTION 'kill switch: the version changed' USING ERRCODE = 'HD003'; END IF;
+  UPDATE {S}.kill_switch_stop_requests r SET cleared_by = v + 1 WHERE r.cleared_by IS NULL;
+  GET DIAGNOSTICS n = ROW_COUNT;
+  IF p_expected_open IS NULL OR n <> p_expected_open OR (n = 0 AND NOT was_on) THEN
+    RAISE EXCEPTION 'kill switch: the open count changed' USING ERRCODE = 'HD003'; END IF;
+  IF NOT was_on THEN UPDATE {S}.kill_switch SET "on" = true WHERE id = 1; END IF;
+  UPDATE {S}.kill_switch SET "on" = false WHERE id = 1;
+  RETURN QUERY SELECT s."on", s."by", s.ts, s.schema_version, s.version, s.open_requests
+               FROM {S}.kill_switch_state s;
+END $f$"""
+_GUARD_FN = """CREATE OR REPLACE FUNCTION {S}.hadavin_kill_switch_guard() RETURNS trigger
+LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$
+DECLARE lbl text;
+BEGIN
+  IF OLD."on" AND NOT NEW."on" THEN
+    IF NOT pg_has_role(session_user, {GROUP}::text, 'MEMBER') THEN
+      RAISE EXCEPTION 'kill switch: only the reset role may clear it' USING ERRCODE = 'HD001'; END IF;
+    SELECT l.label INTO lbl FROM {S}.kill_switch_login_labels l WHERE l.login_name = session_user::text;
+    IF lbl IS NULL THEN RAISE EXCEPTION 'kill switch: login not registered' USING ERRCODE = 'HD001'; END IF;
+    INSERT INTO {S}.kill_switch_resets VALUES (OLD.version, now(), lbl,
+      CASE WHEN OLD."by" IS NULL OR OLD."by" = 'dba' OR OLD."by" ~ {LABEL}
+           THEN OLD."by" ELSE 'unlabelled' END);
+    NEW."by" := lbl; NEW.version := OLD.version + 1; NEW.ts := now();
+  ELSIF NEW."on" AND NOT OLD."on" THEN
+    IF NEW."by" IS NOT DISTINCT FROM OLD."by" THEN NEW."by" := NULL; END IF;
+    NEW.version := OLD.version; NEW.ts := now();
+  ELSE
+    NEW."on" := OLD."on"; NEW."by" := OLD."by"; NEW.ts := OLD.ts; NEW.version := OLD.version;
+  END IF;
+  NEW.id := OLD.id; RETURN NEW;
+END $f$"""
+_FORBIDDEN_ROLES = frozenset({"public", "none", "session_user", "current_user"})
+_GUARD_TRIGGERS = (  # (table, trigger): must stay ENABLE ALWAYS
+    ("kill_switch", "kill_switch_guard"),
+    ("kill_switch_stop_requests", "kill_switch_stop_requests_update"),
+    ("kill_switch_stop_requests", "kill_switch_stop_requests_delete"),
+    ("kill_switch_stop_requests", "kill_switch_stop_requests_no_truncate"),
+    ("kill_switch_resets", "kill_switch_resets_append_only"),
+    ("kill_switch_resets", "kill_switch_resets_no_truncate"),
+)
+_STOP_SIG = "hadavin_kill_switch_stop(text)"
+_RESET_SIG = "hadavin_kill_switch_reset(text, bigint, integer)"
+_GUARD_SIG = "hadavin_kill_switch_guard()"  # a trigger function: no role is meant to call it
+
+
+def _set_lock_timeout(db, ms: int) -> None:
+    """The one place the migration's own table-lock bound is set (transaction-local, milliseconds as text)."""
+    db.execute("SELECT set_config('lock_timeout', %s, true)", (str(ms),))
+
+
+def _install_kill_switch(db, schema: str, group: str, cap: int) -> None:
+    """Re-issue the three functions (the schema, the cap and the group are written into their text), take
+    EXECUTE from PUBLIC, and re-enable a guard trigger that someone disabled. `ENABLE ALWAYS` takes a table lock
+    that queues a stop, so it is issued only for a trigger that is not already ALWAYS."""
+    s = sql.Identifier(schema)
+    for text in (_STOP_FN, _RESET_FN, _GUARD_FN):
+        db.execute(
+            sql.SQL(text).format(
+                S=s,
+                N=sql.Literal(cap),
+                GROUP=sql.Literal(group),
+                RETURNS=sql.SQL(_RETURNS),
+                LABEL=sql.SQL(_LABEL_RE),
+            )
+        )
+    for sig in (_STOP_SIG, _RESET_SIG, _GUARD_SIG):
+        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {}.{} FROM PUBLIC").format(s, sql.SQL(sig)))
+    for table, trigger in _GUARD_TRIGGERS:
+        state = db.execute(
+            "SELECT t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
+            "JOIN pg_namespace n ON n.oid = c.relnamespace "
+            "WHERE n.nspname = %s AND c.relname = %s AND t.tgname = %s",
+            (schema, table, trigger),
+        ).fetchone()
+        if state is None:
+            raise ConfigError(f"the kill switch trigger {trigger} is missing")
+        if state[0] != "A":
+            db.execute(
+                sql.SQL("ALTER TABLE {}.{} ENABLE ALWAYS TRIGGER {}").format(
+                    s, sql.Identifier(table), sql.Identifier(trigger)
+                )
+            )
+
+
+def _grant_execute(db, schema: str, sig: str, role: str | None) -> None:
+    if role:
+        db.execute(
+            sql.SQL("GRANT EXECUTE ON FUNCTION {}.{} TO {}").format(
+                sql.Identifier(schema), sql.SQL(sig), sql.Identifier(role)
+            )
+        )
+
+
+def _check_kill_switch_roles(db, schema: str, named: list[str], reset_role: str) -> None:
+    owners = db.execute(
+        "SELECT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
+        "WHERE n.nspname = %s AND c.relname LIKE 'kill\\_switch%%' "
+        "UNION SELECT pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
+        "WHERE n.nspname = %s AND p.proname LIKE 'hadavin\\_kill\\_switch%%'",
+        (schema, schema),
+    ).fetchall()
+    if bad := sorted({r[0] for r in owners} & set(named)):
+        raise ConfigError(
+            f"a role named for migrate owns the kill switch objects: {', '.join(bad)}"
+        )
+    login = db.execute(
+        "SELECT rolcanlogin FROM pg_roles WHERE rolname = %s", (reset_role,)
+    ).fetchone()
+    if login is None:
+        raise ConfigError(f"the reset role {reset_role!r} does not exist; create it NOLOGIN first")
+    if login[0]:
+        raise ConfigError(f"the reset role {reset_role!r} must be a NOLOGIN group role")
+
+
+def _role_defaults(db, runtime_role, stop_role, settings: dict[str, int]) -> None:
+    """Role-level defaults for honest code (a session can undo them) and the connection limits."""
+    try:
+        for role, limit in (
+            (runtime_role, settings["runtime_connection_limit"]),
+            (stop_role, settings["stop_connection_limit"]),
+        ):
+            if not role:
+                continue
+            db.execute(
+                sql.SQL("ALTER ROLE {} CONNECTION LIMIT {}").format(
+                    sql.Identifier(role), sql.Literal(limit)
+                )
+            )
+            if role == runtime_role:
+                for name in (
+                    "statement_timeout",
+                    "lock_timeout",
+                    "idle_in_transaction_session_timeout",
+                ):
+                    db.execute(
+                        sql.SQL("ALTER ROLE {} IN DATABASE {} SET {} = {}").format(
+                            sql.Identifier(role),
+                            sql.Identifier(db.execute("SELECT current_database()").fetchone()[0]),
+                            sql.SQL(name),
+                            sql.Literal(str(settings[name])),
+                        )
+                    )
+    except pg_errors.InsufficientPrivilege as exc:
+        raise ConfigError(
+            "the migration role may not run ALTER ROLE for the runtime or stop role (needs CREATEROLE with "
+            "ADMIN on it, or a superuser); nothing was changed"
+        ) from exc
+
+
 def _migration_files(folder: Path = MIGRATIONS) -> list[Path]:
     return sorted(folder.glob("*.sql"))
 
@@ -208,6 +404,7 @@ def effective_problems(db, role: str, expected_table, expected_cols=None) -> lis
             f"{role}: is a superuser or can create roles or databases or bypass row security"
         )
     schema = db.execute("SELECT current_schema()").fetchone()[0]
+    privs = table_privileges(db)
     if db.execute("SELECT has_schema_privilege(%s, %s, 'CREATE')", (role, schema)).fetchone()[0]:
         problems.append(f"{role}: can CREATE in schema {schema}")
     rels = db.execute(
@@ -215,6 +412,10 @@ def effective_problems(db, role: str, expected_table, expected_cols=None) -> lis
         "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S')",
         (schema,),
     ).fetchall()
+    for owner in sorted({o for _, _, _, o in rels if o != role}):
+        # Membership, not inherited rights: a NOINHERIT member holds no rights today and can still SET ROLE to the owner.
+        if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
+            problems.append(f"{role}: is a member of {owner}, the owner of relations in {schema}")
     for oid, name, kind, owner in rels:
         if owner == role:
             problems.append(f"{role}: owns {name}")
@@ -238,7 +439,7 @@ def effective_problems(db, role: str, expected_table, expected_cols=None) -> lis
             {p.strip() for p in expected_table(grant).split(",") if p.strip()} if grant else set()
         )
         allowed_cols = set(expected_cols(grant)) if (grant and expected_cols) else set()
-        for p in _TABLE_PRIVS:
+        for p in privs:
             if (
                 p not in allowed
                 and db.execute("SELECT has_table_privilege(%s, %s, %s)", (role, oid, p)).fetchone()[
@@ -286,6 +487,16 @@ def migrate(
     runtime_role: str | None = None,
     portal_role: str | None = None,
     purge_role: str | None = None,
+    reset_role: str | None = None,
+    stop_role: str | None = None,
+    max_open_stop_requests: int = defaults.KILL_SWITCH_MAX_OPEN_STOP_REQUESTS,
+    lock_timeout_ms: int = defaults.KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS,
+    advisory_wait_ms: int = defaults.KILL_SWITCH_MIGRATE_ADVISORY_WAIT_MS,
+    role_statement_timeout_ms: int = defaults.KILL_SWITCH_ROLE_STATEMENT_TIMEOUT_MS,
+    role_lock_timeout_ms: int = defaults.KILL_SWITCH_ROLE_LOCK_TIMEOUT_MS,
+    role_idle_in_transaction_timeout_ms: int = defaults.KILL_SWITCH_ROLE_IDLE_IN_TRANSACTION_TIMEOUT_MS,
+    runtime_connection_limit: int = defaults.KILL_SWITCH_RUNTIME_CONNECTION_LIMIT,
+    stop_connection_limit: int = defaults.KILL_SWITCH_STOP_CONNECTION_LIMIT,
     iam_auth: bool = False,
     region: str | None = None,
     sslmode: str | None = None,
@@ -294,16 +505,35 @@ def migrate(
     """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
     privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
     relations marked `portal` and nothing else. The ledger and the grant map are checked first: a bad file name,
-    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database."""
-    for role in (runtime_role, portal_role, purge_role):
-        if role is not None and not _ROLE.fullmatch(role):
+    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database.
+
+    `reset_role` (REQUIRED: the guard function text names it) is the NOLOGIN group whose members may clear a stop;
+    `stop_role` is the optional login of the operator's stop. Both get EXECUTE on one function and SELECT on the
+    state view, nothing else. The stop and reset functions and the guard are re-issued on every run."""
+    for role in (runtime_role, portal_role, purge_role, reset_role, stop_role):
+        if role is not None and (not _ROLE.fullmatch(role) or role in _FORBIDDEN_ROLES):
             raise ConfigError(f"not a plain database role name: {role!r}")
-    named = [r for r in (runtime_role, portal_role, purge_role) if r is not None]
+    named = [
+        r for r in (runtime_role, portal_role, purge_role, reset_role, stop_role) if r is not None
+    ]
     if len(set(named)) != len(named):
-        raise ConfigError("the runtime, portal and purge roles must be different roles")
+        raise ConfigError(
+            "the runtime, portal, purge, reset and stop roles must be different roles"
+        )
+    for name, value in (
+        ("max_open_stop_requests", max_open_stop_requests),
+        ("lock_timeout_ms", lock_timeout_ms),
+        ("advisory_wait_ms", advisory_wait_ms),
+    ):
+        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
+            raise ConfigError(f"{name} must be an integer of at least 1 (0 means no timeout)")
     files = _migration_files()
     if problems := check_ledger(files) + check_grants(files):
         raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
+    if reset_role is None:
+        raise ConfigError(
+            "migrate needs reset_role: the NOLOGIN group whose members may reset the kill switch"
+        )
     applied = []
     with (
         connect(
@@ -311,7 +541,16 @@ def migrate(
         ) as db,
         db.transaction(),
     ):
-        db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
+        # Any login can take an advisory lock, so the wait for ours is bounded; then the (shorter) table-lock
+        # bound, set AFTER the advisory lock so a second honest `migrate` that waits for this one still goes through.
+        db.execute("SELECT set_config('lock_timeout', %s, true)", (str(advisory_wait_ms),))
+        try:
+            db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
+        except pg_errors.LockNotAvailable as exc:
+            raise ConfigError(
+                "another session holds the migration lock; see the runbook (pg_locks, locktype advisory)"
+            ) from exc
+        _set_lock_timeout(db, lock_timeout_ms)
         db.execute(
             "CREATE TABLE IF NOT EXISTS schema_migrations "
             "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
@@ -328,6 +567,9 @@ def migrate(
             if path.stem in done:
                 continue
             db.execute(path.read_text(encoding="utf-8"))  # a file shipped in this package
+            # A file may SET LOCAL its own (longer) lock_timeout, and that would stay for every later file and for
+            # the role and function steps. The configured bound is put back after every file.
+            _set_lock_timeout(db, lock_timeout_ms)
             db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
             applied.append(path.stem)
         q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
@@ -335,8 +577,34 @@ def migrate(
             for b in named:
                 if a != b and db.execute(q, (a, b)).fetchone()[0]:
                     raise ConfigError(
-                        "the runtime, portal and purge roles must not be members of each other"
+                        "the runtime, portal, purge, reset and stop roles must not be members of each other"
                     )
+        schema = db.execute("SELECT current_schema()").fetchone()[0]
+        _check_kill_switch_roles(db, schema, named, reset_role)
+        _install_kill_switch(db, schema, reset_role, max_open_stop_requests)
+        _grant_execute(db, schema, _STOP_SIG, runtime_role)
+        _grant_execute(db, schema, _STOP_SIG, stop_role)
+        _grant_execute(db, schema, _RESET_SIG, reset_role)
+        _role_defaults(
+            db,
+            runtime_role,
+            stop_role,
+            {
+                "statement_timeout": role_statement_timeout_ms,
+                "lock_timeout": role_lock_timeout_ms,
+                "idle_in_transaction_session_timeout": role_idle_in_transaction_timeout_ms,
+                "runtime_connection_limit": runtime_connection_limit,
+                "stop_connection_limit": stop_connection_limit,
+            },
+        )
+        for role, pick in ((reset_role, lambda g: g.reset), (stop_role, lambda g: g.stop)):
+            if role is None:
+                continue
+            _apply_grants(db, role, pick)
+            if bad := effective_problems(db, role, lambda g, pick=pick: pick(g) if g else ""):
+                raise ConfigError(
+                    f"the {role} role holds more than the grant map: " + "; ".join(bad[:20])
+                )
         if runtime_role:
             _apply_grants(db, runtime_role, lambda g: g.runtime)
             if bad := effective_problems(db, runtime_role, lambda g: g.runtime if g else ""):
```

### B.9.3 Store Protocol on PR 76

`src/hadavin_sdk/store/protocol.py` lines 176-206 at origin/core/P2a-1:
```
   176	        c.__name__ in ("OperationalError", "InterfaceError") and c.__module__.startswith("psycopg")
   177	        for c in type(exc).__mro__
   178	    )
   179	
   180	
   181	class ResetRefused(RuntimeError):
   182	    """The database refused a reset: the caller is not in the reset group or has no registered label (HD001)."""
   183	
   184	
   185	class StaleCount(RuntimeError):
   186	    """The version or the open-request count changed since the operator read it, or there was nothing to clear
   187	    (HD003)."""
   188	
   189	
   190	class LabelRefused(ValueError):
   191	    """A name that is not a keyed label (HD004). Raised by the memory store too."""
   192	
   193	
   194	class SwitchRowMissing(RuntimeError):
   195	    """The kill_switch row is missing (HD005): a database administrator must re-seed it."""
   196	
   197	
   198	class NotMigrated(RuntimeError):
   199	    """The stop or reset function does not exist (SQLSTATE 42883): the database is not migrated."""
   200	
   201	
   202	class StoreBusy(RuntimeError):
   203	    """The database answered "busy" (lock timeout 55P03, statement timeout 57014, deadlock victim 40P01, too many
   204	    connections for the role 53300): the call was NOT done and may be retried. Not a connectivity error: the
   205	    store is reachable (`is_connectivity_error` is false for it)."""
   206	
```

`src/hadavin_sdk/store/protocol.py` lines 318-346 at origin/core/P2a-1:
```
   318	    ) -> list[SpendReservation]:
   319	        """Open rows older than `older_than_s` (30 to 10**7) become `expired` (no counter moves)."""
   320	        ...
   321	
   322	    def get_kill_switch(self) -> StopState:
   323	        """A missing or unreadable switch row reads as ON (fail closed)."""
   324	        ...
   325	
   326	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
   327	        """A STOP: only `ks.on` true is accepted (anything else raises ValueError) and `ks.by` must be a keyed
   328	        label (`LabelRefused`). Each call is its own open stop request; nothing is overwritten."""
   329	        ...
   330	
   331	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
   332	        """Clear exactly the stops that the pair (version, open count) named when the operator read it.
   333	        `StaleCount` when either changed or there was nothing to clear."""
   334	        ...
   335	
   336	    def guard_report(
   337	        self, runtime_role: str | None, stop_role: str | None, reset_group: str | None
   338	    ) -> GuardReport:
   339	        """Catalog reads only (no writes, no locks that queue a stop) about the guard for the NAMED roles. A busy
   340	        database raises `StoreBusy`, which the probe treats as inconclusive."""
   341	        ...
   342	
   343	    def get_tick_state(self, step: str) -> TickState | None: ...
   344	    def save_tick_state(self, state: TickState) -> None: ...
   345	
   346	    # --- evidence (K5): read-tool calls and the run's redaction map ---------------------------------------------
```

### B.9.4 Postgres store on PR 76 (error map, guard report, the kill-switch methods)

`src/hadavin_sdk/store/postgres.py` lines 76-117 at origin/core/P2a-1:
```
    76	# SQLSTATE -> typed error for the two kill-switch functions. HD001 refused, HD003 stale, HD004 bad label, HD005
    77	# row missing (custom codes of the functions), 42883 function missing, 42704 the reset group role is missing.
    78	_SWITCH_ERRORS: dict[str, type[Exception]] = {
    79	    "HD001": ResetRefused,
    80	    "HD003": StaleCount,
    81	    "HD004": LabelRefused,
    82	    "HD005": SwitchRowMissing,
    83	    "42883": NotMigrated,
    84	    "42704": ResetRefused,
    85	}
    86	# "busy" answers: NOT done, retry later. 55P03 lock timeout, 57014 statement timeout, 40P01 deadlock victim,
    87	# 53300 too many connections for the role.
    88	_BUSY = frozenset({"55P03", "57014", "40P01", "53300"})
    89	_SWITCH_TEXT = {
    90	    "42883": "database not migrated; use the DBA stop recipe",
    91	    "42704": "reset group role missing",
    92	}
    93	
    94	
    95	_TABLE_PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
    96	_KS_RELATIONS = (
    97	    "kill_switch",
    98	    "kill_switch_stop_requests",
    99	    "kill_switch_resets",
   100	    "kill_switch_login_labels",
   101	)
   102	# The only direct table rights the grant map gives these roles on the guarded relations (migrate.GRANTS): the runtime
   103	# may read the reset history.
   104	_ALLOWED = {("runtime", "kill_switch_resets"): ("SELECT",)}
   105	_KS_FUNCTIONS = (
   106	    "hadavin_kill_switch_stop(text)",
   107	    "hadavin_kill_switch_reset(text, bigint, integer)",
   108	    "hadavin_kill_switch_guard()",
   109	)
   110	
   111	
   112	def table_privileges(db) -> tuple[str, ...]:
   113	    """Every table privilege this server knows. MAINTAIN exists from PostgreSQL 17; asking `has_table_privilege`
   114	    for it on 16 raises 22023, so the list comes from `server_version_num`. One list for the probe and for
   115	    `effective_problems`."""
   116	    n = int(db.execute("SHOW server_version_num").fetchone()[0])
   117	    return _TABLE_PRIVS + (("MAINTAIN",) if n >= 170000 else ())
```

`src/hadavin_sdk/store/postgres.py` lines 281-400 at origin/core/P2a-1:
```
   281	def _guard_report(db, runtime_role, stop_role, reset_group) -> GuardReport:
   282	    problems: list[str] = []
   283	    tolerated: list[str] = []
   284	    schema = db.execute("SELECT current_schema()").fetchone()[0]
   285	    privs = table_privileges(db)
   286	    table_owner = db.execute(
   287	        "SELECT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
   288	        "WHERE n.nspname = %s AND c.relname = 'kill_switch'",
   289	        (schema,),
   290	    ).fetchone()
   291	    if table_owner is None:
   292	        return GuardReport(
   293	            problems=("the kill_switch table does not exist: run hadavin-sdk migrate",)
   294	        )
   295	    for table, trigger in (
   296	        ("kill_switch", "kill_switch_guard"),
   297	        ("kill_switch_stop_requests", "kill_switch_stop_requests_update"),
   298	        ("kill_switch_stop_requests", "kill_switch_stop_requests_delete"),
   299	        ("kill_switch_stop_requests", "kill_switch_stop_requests_no_truncate"),
   300	        ("kill_switch_resets", "kill_switch_resets_append_only"),
   301	        ("kill_switch_resets", "kill_switch_resets_no_truncate"),
   302	    ):
   303	        row = db.execute(
   304	            "SELECT t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
   305	            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s AND t.tgname = %s",
   306	            (schema, table, trigger),
   307	        ).fetchone()
   308	        if row is None:
   309	            problems.append(f"trigger {trigger} is missing")
   310	        elif row[0] != "A":
   311	            problems.append(f"trigger {trigger} is not ENABLE ALWAYS")
   312	    for sig in _KS_FUNCTIONS:
   313	        row = db.execute(
   314	            "SELECT p.prosecdef, p.proconfig, pg_get_userbyid(p.proowner), "
   315	            "(SELECT rolsuper FROM pg_roles WHERE oid = p.proowner), p.prosrc "
   316	            "FROM pg_proc p WHERE p.oid = to_regprocedure(%s)",
   317	            (f"{schema}.{sig}",),
   318	        ).fetchone()
   319	        name = sig.split("(")[0]
   320	        if row is None:
   321	            problems.append(f"function {name} is missing")
   322	            continue
   323	        secdef, config, owner, owner_super, src = row
   324	        if not secdef:
   325	            problems.append(f"function {name} is not SECURITY DEFINER")
   326	        if not any(c.startswith("search_path=pg_catalog") for c in (config or [])):
   327	            problems.append(f"function {name} has no pinned search_path")
   328	        if owner != table_owner[0]:
   329	            problems.append(f"function {name} is owned by {owner}, not by the table owner")
   330	        if owner_super:
   331	            tolerated.append(f"function {name} is owned by a superuser")
   332	        if name.endswith("guard") and reset_group:
   333	            exact = db.execute(
   334	                "SELECT strpos(%s, quote_literal(%s) || '::text') > 0", (src, reset_group)
   335	            ).fetchone()[0]
   336	            if not exact:
   337	                problems.append("the guard function does not name the configured reset group")
   338	    group_exists = bool(
   339	        reset_group
   340	        and db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (reset_group,)).fetchone()
   341	    )
   342	    if reset_group and not group_exists:
   343	        problems.append("the reset group role does not exist")
   344	    for role, label in ((runtime_role, "runtime"), (stop_role, "stop")):
   345	        if not role:
   346	            continue
   347	        if db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone() is None:
   348	            problems.append(f"the {label} role does not exist")
   349	            continue
   350	        for rel in _KS_RELATIONS + ("kill_switch_stop_requests_id_seq",):
   351	            kind = "sequence" if rel.endswith("_seq") else "table"
   352	            held = (
   353	                [
   354	                    p
   355	                    for p in ("USAGE", "SELECT", "UPDATE")
   356	                    if db.execute(
   357	                        "SELECT has_sequence_privilege(%s, to_regclass(%s), %s)",
   358	                        (role, f"{schema}.{rel}", p),
   359	                    ).fetchone()[0]
   360	                ]
   361	                if kind == "sequence"
   362	                else [
   363	                    p
   364	                    for p in privs
   365	                    if (p in _ALLOWED.get((label, rel), ())) is False
   366	                    and db.execute(
   367	                        "SELECT has_table_privilege(%s, to_regclass(%s), %s)",
   368	                        (role, f"{schema}.{rel}", p),
   369	                    ).fetchone()[0]
   370	                ]
   371	            )
   372	            if held:
   373	                problems.append(f"the {label} role can {', '.join(held)} on {rel}")
   374	        if not db.execute(
   375	            "SELECT has_table_privilege(%s, to_regclass(%s), 'SELECT')",
   376	            (role, f"{schema}.kill_switch_state"),
   377	        ).fetchone()[0]:
   378	            problems.append(f"the {label} role cannot read kill_switch_state")
   379	        if not db.execute(
   380	            "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
   381	            (role, f"{schema}.{_KS_FUNCTIONS[0]}"),
   382	        ).fetchone()[0]:
   383	            problems.append(f"the {label} role cannot execute the stop function")
   384	        for fn in _KS_FUNCTIONS[1:]:
   385	            if db.execute(
   386	                "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
   387	                (role, f"{schema}.{fn}"),
   388	            ).fetchone()[0]:
   389	                problems.append(f"the {label} role can execute {fn.split('(')[0]}")
   390	        if (
   391	            reset_group
   392	            and group_exists
   393	            and db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, reset_group)).fetchone()[
   394	                0
   395	            ]
   396	        ):
   397	            problems.append(f"the {label} role is a member of the reset group")
   398	        if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, table_owner[0])).fetchone()[0]:
   399	            problems.append(f"the {label} role is a member of the table owner")
   400	    limits = {}
```

`src/hadavin_sdk/store/postgres.py` lines 945-1019 at origin/core/P2a-1:
```
   945	    def get_kill_switch(self) -> StopState:
   946	        found = self._select(StopState, "kill_switch_state", "true", ())
   947	        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
   948	            _LOG.error(
   949	                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
   950	            )
   951	            return StopState(on=True, by="system:kill_switch_row_missing")
   952	        return found[0]
   953	
   954	    # Two whole statements (no string building). The casts matter: a bigint argument does not resolve to the
   955	    # (text, bigint, integer) signature.
   956	    _STOP_QUERY = (
   957	        'SELECT "on", "by", ts, schema_version, version, open_requests '
   958	        "FROM hadavin_kill_switch_stop(%s)"
   959	    )
   960	    _RESET_QUERY = (
   961	        'SELECT "on", "by", ts, schema_version, version, open_requests '
   962	        "FROM hadavin_kill_switch_reset(%s, %s::bigint, %s::int)"
   963	    )
   964	
   965	    def _on_short(self, fn):
   966	        """Run `fn(db)` on a fresh short connection (closed after), or on the main one behind the lock."""
   967	        if self._short_connect is None:
   968	            with self._lock:
   969	                return fn(self._db)
   970	        db = self._short_connect()
   971	        try:
   972	            return fn(db)
   973	        finally:
   974	            db.close()
   975	
   976	    def _call_switch(self, query: str, params: tuple) -> StopState:
   977	        """Run one of the two kill-switch functions and map its SQLSTATE to a typed error (never by message
   978	        text). The functions run as their owner; the caller needs EXECUTE only. A busy answer (lock or statement
   979	        timeout, deadlock, connection limit) is `StoreBusy`: NOT done."""
   980	        try:
   981	            row = self._on_short(
   982	                lambda db: db.cursor(row_factory=dict_row).execute(query, params).fetchone()
   983	            )
   984	        except psycopg.Error as exc:
   985	            code = getattr(exc, "sqlstate", None) or ""
   986	            if code in _BUSY:
   987	                raise StoreBusy(f"the store is busy ({code}); the call was not done") from exc
   988	            mapped = _SWITCH_ERRORS.get(code)
   989	            if mapped is None:
   990	                raise
   991	            raise mapped(_SWITCH_TEXT.get(code, str(code))) from exc
   992	        return StopState.model_validate(row)
   993	
   994	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
   995	        """A stop: one INSERT through `hadavin_kill_switch_stop`. The runtime has no right on the tables."""
   996	        if ks.on is not True:
   997	            raise ValueError("set_kill_switch only stops; a reset goes through reset_kill_switch")
   998	        return self._call_switch(self._STOP_QUERY, (ks.by,))
   999	
  1000	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
  1001	        for n, top in ((expected_version, 2**63 - 1), (expected_open, 2**31 - 1)):
  1002	            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
  1003	                raise ValueError("reset: version and open count must be in range")
  1004	        return self._call_switch(self._RESET_QUERY, (by, expected_version, expected_open))
  1005	
  1006	    def guard_report(
  1007	        self, runtime_role: str | None, stop_role: str | None, reset_group: str | None
  1008	    ) -> GuardReport:
  1009	        """Catalog reads about the guard for the NAMED roles (never the connected one, so the runtime, the stop
  1010	        login and a reset login all see the same report). A busy answer is `StoreBusy`."""
  1011	        try:
  1012	            return self._on_short(
  1013	                lambda db: _guard_report(db, runtime_role, stop_role, reset_group)
  1014	            )
  1015	        except psycopg.Error as exc:
  1016	            code = getattr(exc, "sqlstate", None) or ""
  1017	            if code in _BUSY:
  1018	                raise StoreBusy(f"the store is busy ({code}); the probe is inconclusive") from exc
  1019	            raise
```

### B.9.5 Memory store on PR 76

`src/hadavin_sdk/store/memory.py` lines 436-490 at origin/core/P2a-1:
```
   436	                Decimal(0),
   437	            )
   438	            return self._spend.get((agent_id, day), Decimal(0)), month
   439	
   440	    def _state(self) -> StopState:
   441	        """The state view: ON when the flag is on or any request is open; `by`/`ts` from the flag, else from the
   442	        earliest open request."""
   443	        k, first = self._kill, (self._stops[0] if self._stops else None)
   444	        by, ts = (k.by, k.ts) if k.on or first is None else first
   445	        return StopState(
   446	            on=k.on or first is not None,
   447	            by=by,
   448	            ts=ts,
   449	            version=k.version,
   450	            open_requests=len(self._stops),
   451	        )
   452	
   453	    def get_kill_switch(self) -> StopState:
   454	        with self._lock:
   455	            return self._state()
   456	
   457	    def set_kill_switch(self, ks: KillSwitch) -> StopState:
   458	        if ks.on is not True:
   459	            raise ValueError("set_kill_switch only stops; a reset goes through reset_kill_switch")
   460	        if not is_label(ks.by):
   461	            raise LabelRefused("kill switch: stop label not accepted")
   462	        with self._lock:
   463	            self._stops.append((ks.by, now()))
   464	            return self._state()
   465	
   466	    def guard_report(
   467	        self, runtime_role: str | None, stop_role: str | None, reset_group: str | None
   468	    ) -> GuardReport:
   469	        """A memory store has no database guard; the report is empty (the probe reads that as nothing to flag)."""
   470	        return GuardReport()
   471	
   472	    def reset_kill_switch(self, by: str, expected_version: int, expected_open: int) -> StopState:
   473	        if not is_label(by):
   474	            raise LabelRefused("kill switch: name not accepted")
   475	        for n, top in ((expected_version, 2**63 - 1), (expected_open, 2**31 - 1)):
   476	            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
   477	                raise ValueError("reset: version and open count must be in range")
   478	        with self._lock:
   479	            if self._kill.version != expected_version:
   480	                raise StaleCount("kill switch: the version changed")
   481	            n = len(self._stops)
   482	            if n != expected_open or (n == 0 and not self._kill.on):
   483	                raise StaleCount("kill switch: the open count changed")
   484	            self._stops.clear()
   485	            self._kill = KillSwitch(on=False, by=by, version=self._kill.version + 1)
   486	            return self._state()
   487	
   488	    def get_tick_state(self, step: str) -> TickState | None:
   489	        with self._lock:
   490	            state = self._ticks.get(step)
```

### B.9.6 Models on PR 76

`src/hadavin_sdk/models.py` lines 272-292 at origin/core/P2a-1:
```
   272	
   273	
   274	class KillSwitch(Shape):
   275	    on: bool = False
   276	    by: str | None = None
   277	    ts: datetime = Field(default_factory=now)
   278	    version: int = 0  # raised by 1 on every reset; with `open_requests` it names the set of stops a reset clears
   279	
   280	
   281	class StopState(KillSwitch):
   282	    """What the stop and reset functions and the state view return: the switch plus the number of open stop
   283	    requests. `open_requests` is not a table column, so it is not on `KillSwitch`."""
   284	
   285	    open_requests: int = 0
   286	
   287	
   288	class GateRun(Shape):
   289	    agent_id: str
   290	    model_id: str
   291	    prompt_sha256: str
   292	    config_hash: str
```

`src/hadavin_sdk/models.py` lines 374-386 at origin/core/P2a-1:
```
   374	
   375	
   376	class GuardReport(BaseModel):
   377	    """What the catalog says about the kill switch guard, for the named roles (never the connected one). `problems`
   378	    fail the start-up probe in every stage; `dev_tolerated` fail it in pilot and prod only (for example a function
   379	    owned by a superuser, which is what a test database built as `postgres` has)."""
   380	
   381	    model_config = ConfigDict(extra="forbid", frozen=True)
   382	    problems: tuple[str, ...] = ()
   383	    dev_tolerated: tuple[str, ...] = ()
   384	    runtime_connection_limit: int | None = None
   385	    stop_connection_limit: int | None = None
```

### B.9.7 `S/limits.py` on PR 76, whole file

`src/hadavin_sdk/limits.py` lines 1-200 at origin/core/P2a-1:
```
     1	"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited.
     2	
     3	A stop is one new request row in the store (it cannot be refused for a naming problem and a compromised runtime
     4	cannot hold it up). A reset is allowed only through a separate store handle (`reset_store`, a different database
     5	login in the operator process) and names the exact set of stops it clears by (version, open count).
     6	"""
     7	
     8	from __future__ import annotations
     9	
    10	import logging
    11	import secrets
    12	from collections.abc import Iterable
    13	from decimal import Decimal
    14	
    15	from hadavin_sdk.audit.labelkey import (
    16	    NOKEY_LABEL,
    17	    mask_principal,
    18	    valid_key_id,
    19	)
    20	from hadavin_sdk.audit.protocol import AuditSink
    21	from hadavin_sdk.models import AuditEvent, KillSwitch, StopState, now
    22	from hadavin_sdk.registry import Registry
    23	from hadavin_sdk.store.memory import MemoryStore
    24	from hadavin_sdk.store.protocol import (
    25	    ResetRefused,
    26	    StaleCount,
    27	    Store,
    28	    StoreBusy,
    29	    SwitchRowMissing,
    30	)
    31	
    32	_LOG = logging.getLogger(__name__)
    33	MIN_KEY_BYTES = 16  # the same minimum as a restored audit key
    34	_STAGES = frozenset({"dev", "pilot", "prod"})  # exactly what Config.environment accepts; no alias
    35	_MISSING_ROW = "the kill_switch row is missing; a database administrator must re-seed it"
    36	
    37	
    38	class StopNotPermitted(RuntimeError):
    39	    """The caller may not do this: a reset by a name that is not listed, a process without a reset credential,
    40	    a database refusal, or a missing label key."""
    41	
    42	
    43	class SwitchChanged(RuntimeError):
    44	    """The reset did not happen because the switch changed since the operator read it (or its row is missing)."""
    45	
    46	
    47	class StopNotConfirmed(RuntimeError):
    48	    """A stop returned a row that does not read ON."""
    49	
    50	
    51	class Limits:
    52	    def __init__(
    53	        self,
    54	        store: Store,
    55	        audit: AuditSink,
    56	        registry: Registry,
    57	        *,
    58	        environment: str,
    59	        stop_store: Store | None = None,
    60	        reset_store: Store | None = None,
    61	        reset_names: Iterable[str] = frozenset(),
    62	        label_key: bytes | None = None,
    63	        key_id: str = "k1",
    64	    ) -> None:
    65	        if not valid_key_id(key_id):
    66	            raise ValueError("key_id must match [A-Za-z0-9_-]{1,32}")
    67	        if environment not in _STAGES:  # no alias: "demo" is not "dev" (Config.environment decides)
    68	            raise ValueError(f"environment must be one of {sorted(_STAGES)}, not {environment!r}")
    69	        dev = environment == "dev"
    70	        if not dev and isinstance(store, MemoryStore):
    71	            raise ValueError("a memory store is allowed only when environment is dev")
    72	        if label_key is None:
    73	            if not dev:
    74	                raise ValueError("a label key is required when environment is not dev")
    75	            label_key = secrets.token_bytes(32)
    76	            _LOG.warning(
    77	                "limits: no label key given; using a per-process random key (environment dev only)"
    78	            )
    79	        self.store, self.audit, self.registry = store, audit, registry
    80	        self.environment = environment
    81	        self.stop_store = stop_store if stop_store is not None else store
    82	        self.reset_store = reset_store
    83	        self.reset_names = frozenset(reset_names)
    84	        self._key, self._key_id = label_key, key_id
    85	
    86	    # --- the meter -----------------------------------------------------------------------------------------------
    87	
    88	    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
    89	        return self.store.add_spend(agent_id, now().date(), usd)
    90	
    91	    def blocked(self, agent_id: str) -> list[str]:
    92	        reasons = []
    93	        if self.store.get_kill_switch().on:
    94	            reasons.append("kill_switch")
    95	        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
    96	        budget = self.registry.agents[agent_id].budget_usd
    97	        if day >= budget.daily:
    98	            reasons.append("daily_budget")
    99	        if month >= budget.monthly:
   100	            reasons.append("monthly_budget")
   101	        return reasons
   102	
   103	    def status(self) -> StopState:
   104	        return self.store.get_kill_switch()
   105	
   106	    # --- labels --------------------------------------------------------------------------------------------------
   107	
   108	    def _key_usable(self) -> bool:
   109	        return len(self._key) >= MIN_KEY_BYTES
   110	
   111	    def label(self, name: object) -> str:
   112	        """The keyed label of a name (what `limits whois NAME` prints)."""
   113	        if not self._key_usable():
   114	            raise StopNotPermitted("the label key is unavailable or too short")
   115	        return mask_principal(name, self._key, self._key_id)
   116	
   117	    @staticmethod
   118	    def _event(on: bool, by: str, operation: str, object_ref: str | None = None) -> AuditEvent:
   119	        event = AuditEvent(
   120	            run_id="-",
   121	            domain="limits",
   122	            operation=operation,
   123	            principal=by,
   124	            source="cli",
   125	            result="on" if on else "off",
   126	        )
   127	        return event if object_ref is None else event.model_copy(update={"object_ref": object_ref})
   128	
   129	    # --- stop ----------------------------------------------------------------------------------------------------
   130	
   131	    def stop(self, by: object) -> StopState:
   132	        """An emergency stop works when the audit store is down and never fails for a label-key problem: switch
   133	        first, then audit (the outbox takes the row when the audit store is down)."""
   134	        if self._key_usable():
   135	            label = mask_principal(by, self._key, self._key_id)
   136	        else:
   137	            label = NOKEY_LABEL
   138	            _LOG.error(
   139	                "limits: label key unavailable; the stop is recorded as actor not identified"
   140	            )
   141	        try:
   142	            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
   143	        except StoreBusy:
   144	            # The busy call rolled back, so a second try cannot double a row. Once, on a fresh short connection.
   145	            _LOG.error("limits: the store was busy for the stop; trying once more")
   146	            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
   147	        if state.on is not True:
   148	            raise StopNotConfirmed("the stop returned a row that does not read ON")
   149	        self.audit.write_outcome(
   150	            self._event(True, label, "stop", f"kill_switch:open{state.open_requests}")
   151	        )
   152	        return state
   153	
   154	    # --- reset ---------------------------------------------------------------------------------------------------
   155	
   156	    def reset(self, by: str, *, expect_version: int, expect_open: int) -> StopState:
   157	        """Clear exactly the set of stops that (expect_version, expect_open) named when the operator read it."""
   158	        for n, top in ((expect_version, 2**63 - 1), (expect_open, 2**31 - 1)):
   159	            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
   160	                raise ValueError("expect_version and expect_open must be integers in range")
   161	        if not self._key_usable():
   162	            raise StopNotPermitted("the label key is unavailable or too short")
   163	        label = mask_principal(by, self._key, self._key_id)
   164	        if by not in self.reset_names:  # typo guard on the raw name; the real check is the database
   165	            self.audit.write_outcome(self._event(False, label, "reset_denied"))
   166	            raise StopNotPermitted("reset refused; the switch stays ON")
   167	        if self.reset_store is None:
   168	            raise StopNotPermitted("this process holds no reset credential")
   169	        self.audit.write_intent(self._event(False, label, "reset_attempted"))
   170	        try:
   171	            state = self.reset_store.reset_kill_switch(label, expect_version, expect_open)
   172	        except StaleCount as exc:
   173	            self.audit.write_outcome(self._event(False, label, "reset_refused"))
   174	            raise SwitchChanged(
   175	                "the stops changed since they were read; read the status again"
   176	            ) from exc
   177	        except ResetRefused as exc:
   178	            self.audit.write_outcome(self._event(False, label, "reset_denied"))
   179	            raise StopNotPermitted("reset refused; the switch stays ON") from exc
   180	        except SwitchRowMissing as exc:
   181	            self.audit.write_outcome(self._event(False, label, "reset_failed"))
   182	            raise SwitchChanged(_MISSING_ROW) from exc
   183	        except Exception:
   184	            self.audit.write_outcome(self._event(False, label, "reset_failed"))
   185	            raise
   186	        self.audit.write_outcome(
   187	            self._event(state.on, label, "reset", f"kill_switch:v{state.version}")
   188	        )
   189	        return state
```

### B.9.8 `S/runtime/stop_state.py` (new) and the tick hunk

`src/hadavin_sdk/runtime/stop_state.py` lines 1-47 at origin/core/P2a-1:
```
     1	"""The start-up and tick probe of the kill switch guard: it reads the database catalog and says whether the guard
     2	is in place for the NAMED roles. It never changes anything and never calls the stop or the reset.
     3	
     4	Three answers: OK, FAILED (the guard is wrong: a finding about grants, triggers or functions) and INCONCLUSIVE (the
     5	database was busy, so nothing is known; never reported as a finding about the grants)."""
     6	
     7	from __future__ import annotations
     8	
     9	from dataclasses import dataclass
    10	
    11	from hadavin_sdk.store.protocol import Store, StoreBusy
    12	
    13	OK, FAILED, INCONCLUSIVE = "ok", "failed", "inconclusive"
    14	LIVE_STAGES = frozenset({"pilot", "prod"})
    15	
    16	
    17	class ProbeInconclusive(RuntimeError):
    18	    """The database was busy, so the probe could not tell."""
    19	
    20	
    21	@dataclass(frozen=True)
    22	class ProbeResult:
    23	    status: str
    24	    problems: tuple[str, ...] = ()
    25	
    26	
    27	def probe(
    28	    store: Store,
    29	    *,
    30	    environment: str,
    31	    runtime_role: str | None,
    32	    stop_role: str | None,
    33	    reset_group: str | None,
    34	) -> ProbeResult:
    35	    """In pilot and prod the tolerated findings (a superuser-owned function) count as problems too."""
    36	    try:
    37	        report = store.guard_report(runtime_role, stop_role, reset_group)
    38	    except StoreBusy:
    39	        return ProbeResult(INCONCLUSIVE)
    40	    problems = report.problems + (report.dev_tolerated if environment in LIVE_STAGES else ())
    41	    if (
    42	        environment in LIVE_STAGES
    43	        and runtime_role
    44	        and report.runtime_connection_limit in (None, -1)
    45	    ):
    46	        problems += ("the runtime role has no connection limit",)
    47	    return ProbeResult(FAILED if problems else OK, problems)
```

`git diff origin/main...origin/core/P2a-1 -- src/hadavin_sdk/runtime/tick.py`:
```diff
diff --git a/src/hadavin_sdk/runtime/tick.py b/src/hadavin_sdk/runtime/tick.py
index b580c24..ea99a47 100644
--- a/src/hadavin_sdk/runtime/tick.py
+++ b/src/hadavin_sdk/runtime/tick.py
@@ -240,6 +240,26 @@ def reprobe_sources(ctx: TickContext) -> None:
         raise RuntimeError("source scope: " + "; ".join(found))
 
 
+def stop_guard_probe(ctx: TickContext) -> None:
+    """Re-check the kill switch guard for the configured roles. A finding fails the step (exit 1 of the tick); a busy
+    database is inconclusive and only logged: it says nothing about the grants."""
+    from hadavin_sdk.runtime.stop_state import FAILED as PROBE_FAILED
+    from hadavin_sdk.runtime.stop_state import INCONCLUSIVE, probe
+
+    cfg = ctx.app.config
+    result = probe(
+        ctx.app.store,
+        environment=cfg.environment,
+        runtime_role=cfg.limits.runtime_role,
+        stop_role=cfg.limits.stop_role,
+        reset_group=cfg.limits.reset_group,
+    )
+    if result.status == INCONCLUSIVE:
+        _LOG.warning("stop_guard_probe: the database was busy; nothing is known about the guard")
+    elif result.status == PROBE_FAILED:
+        raise RuntimeError("kill switch guard: " + "; ".join(result.problems[:10]))
+
+
 def heartbeat(ctx: TickContext) -> None:
     """After the steps (not a step): one line with this tick's outcome."""
     failed = sorted(n for n, r in ctx.results.items() if r == FAILED)
@@ -263,6 +283,7 @@ STEPS: list[TickStep] = [
         reprobe_sources,
         interval=lambda ctx: ctx.app.config.evidence.source_reprobe_s,
     ),
+    TickStep("stop_guard_probe", 0, stop_guard_probe),
 ]
 STORE_UNREACHABLE = 4
 STORE_NOT_READY = (
```

### B.9.9 `S/cli.py` diff in full

`git diff origin/main...origin/core/P2a-1 -- src/hadavin_sdk/cli.py`:
```diff
diff --git a/src/hadavin_sdk/cli.py b/src/hadavin_sdk/cli.py
index be3a33e..c7529db 100644
--- a/src/hadavin_sdk/cli.py
+++ b/src/hadavin_sdk/cli.py
@@ -40,10 +40,15 @@ from hadavin_sdk.backends.factory import make
 from hadavin_sdk.config import load_config
 from hadavin_sdk.errors import ConfigError
 from hadavin_sdk.guard.injection import combine
-from hadavin_sdk.limits import Limits
+from hadavin_sdk.limits import Limits, StopNotPermitted, SwitchChanged
 from hadavin_sdk.models import new_id
 from hadavin_sdk.registry import load_registry
-from hadavin_sdk.store.protocol import StoreUnavailable, is_connectivity_error
+from hadavin_sdk.store.protocol import (
+    NotMigrated,
+    StoreBusy,
+    StoreUnavailable,
+    is_connectivity_error,
+)
 
 
 def _num(x: float | None, places: int = 2) -> str:
@@ -91,8 +96,15 @@ def _main(argv: list[str] | None = None) -> int:
     g.add_argument("agent")
     g.add_argument("--k", type=_positive, default=1, help="runs per golden item (pass^k)")
     lim = sub.add_parser("limits", help="kill switch")
-    lim.add_argument("action", choices=["stop", "reset"])
-    lim.add_argument("--by", required=True)
+    lim.add_argument("action", choices=["stop", "reset", "status", "whois", "check"])
+    lim.add_argument("name", nargs="?", help="whois: the name to turn into its label")
+    lim.add_argument("--by", help="stop and reset: who is acting (stored only as a keyed label)")
+    lim.add_argument(
+        "--expect-version", type=int, help="reset: the version that `limits status` printed"
+    )
+    lim.add_argument(
+        "--expect-open", type=int, help="reset: the open_requests that `limits status` printed"
+    )
     sub.add_parser("tick", help="one pass of the housekeeping steps (run every 30-60 s)")
     mig = sub.add_parser("migrate", help="apply the postgres store schema (migration role)")
     mig.add_argument("--runtime-role", help="grant this database role what the runtime needs")
@@ -100,6 +112,14 @@ def _main(argv: list[str] | None = None) -> int:
         "--purge-role",
         help="grant this database role the evidence purge (DELETE on tool_calls and redaction_maps) and nothing else",
     )
+    mig.add_argument(
+        "--reset-role",
+        help="the NOLOGIN database role whose members may reset the kill switch (default: limits.reset_group)",
+    )
+    mig.add_argument(
+        "--stop-role",
+        help="the database login of the operator's stop (it may only call the stop function)",
+    )
     mig.add_argument(
         "--portal-role", help="grant this database role SELECT on the portal's relations only"
     )
@@ -133,9 +153,21 @@ def _main(argv: list[str] | None = None) -> int:
         os.environ["HADAVIN_CONFIG_DIR"] = args.config
     if args.cmd == "tick":
         return _tick()
+    if args.cmd == "limits":
+        if args.action in ("stop", "reset") and not args.by:
+            p.error(f"limits {args.action} needs --by")
+        if args.action == "whois" and not args.name:
+            p.error("limits whois needs a NAME")
     cfg = load_config()
     if args.cmd == "migrate":
-        return _migrate(cfg, args.runtime_role, args.portal_role, args.purge_role)
+        return _migrate(
+            cfg,
+            args.runtime_role,
+            args.portal_role,
+            args.purge_role,
+            reset_role=args.reset_role,
+            stop_role=args.stop_role,
+        )
     reg = load_registry(cfg)
     if args.cmd in (
         "replay",
@@ -206,7 +238,95 @@ def _main(argv: list[str] | None = None) -> int:
         return 3
     if args.cmd == "audit":
         return audit_verify(audit)
-    return kill_switch(Limits(store, audit, reg), args.action, args.by)
+    return _limits(cfg, reg, secrets, store, audit, args)
+
+
+def _limits(cfg, reg, secrets, store, audit, args) -> int:
+    """`limits stop|reset|status|whois`. The stop goes through the stopper login and the reset through the reset
+    login, each resolved here and nowhere else; the runtime never reads those two credential names."""
+    b, lim = cfg.backends, cfg.limits
+    label_key = None
+    if lim.label_key_secret_name:
+        try:
+            label_key = secrets.get(lim.label_key_secret_name).encode("utf-8")
+        except Exception:  # noqa: BLE001 - a stop must work without the key (it falls back to a fixed label)
+            label_key = b""
+    elif cfg.environment != "dev":
+        # No key name configured outside dev: the stop still works (fixed "actor not identified" label); reset and
+        # whois refuse because the key is unusable. `Limits` would otherwise raise here, outside the exit codes.
+        label_key = b""
+
+    def on_login(ref: str):
+        return make("store", b.store.model_copy(update={"dsn_secret_name": ref}), secrets)
+
+    stop_store = reset_store = None
+    try:
+        if args.action == "stop":
+            if b.store.stop_credential_ref:
+                stop_store = on_login(b.store.stop_credential_ref)
+            else:
+                print(
+                    "warning: store.stop_credential_ref is not set; stopping through the runtime login",
+                    file=sys.stderr,
+                )
+        elif args.action in ("reset", "check") and b.store.reset_credential_ref:
+            reset_store = on_login(b.store.reset_credential_ref)
+    except StoreUnavailable as exc:
+        return _kill_switch_store_down(args.action, exc)
+    limits = Limits(
+        store,
+        audit,
+        reg,
+        environment=cfg.environment,
+        stop_store=stop_store,
+        reset_store=reset_store,
+        reset_names=lim.reset_names,
+        label_key=label_key,
+        key_id=lim.key_id,
+    )
+    if args.action == "check":
+        return _limits_check(cfg, reset_store)
+    return kill_switch(
+        limits,
+        args.action,
+        args.by if args.action != "whois" else args.name,
+        expect_version=args.expect_version,
+        expect_open=args.expect_open,
+    )
+
+
+def _limits_check(cfg, store) -> int:
+    """`limits check`: the full guard report for the configured roles, read through the reset login. Exit 0 no
+    findings, 10 findings, 7 the database was busy (nothing known)."""
+    from hadavin_sdk.runtime import stop_state
+
+    if store is None:
+        print(
+            "check needs store.reset_credential_ref (the operator's reset login)", file=sys.stderr
+        )
+        return 2
+    lim = cfg.limits
+    result = stop_state.probe(
+        store,
+        environment=cfg.environment,
+        runtime_role=lim.runtime_role,
+        stop_role=lim.stop_role,
+        reset_group=lim.reset_group,
+    )
+    if result.status == stop_state.INCONCLUSIVE:
+        print(
+            "check inconclusive: the store is busy. Nothing is known; run it again.",
+            file=sys.stderr,
+        )
+        return 7
+    for problem in result.problems:
+        print(f"problem: {problem}")
+    print(
+        "guard OK"
+        if result.status == stop_state.OK
+        else f"guard FAILED: {len(result.problems)} problem(s)"
+    )
+    return 0 if result.status == stop_state.OK else 10
 
 
 def _k1b(cfg, reg, args) -> int:
@@ -310,7 +430,13 @@ def _tick() -> int:
 
 
 def _migrate(
-    cfg, runtime_role: str | None, portal_role: str | None = None, purge_role: str | None = None
+    cfg,
+    runtime_role: str | None,
+    portal_role: str | None = None,
+    purge_role: str | None = None,
+    *,
+    reset_role: str | None = None,
+    stop_role: str | None = None,
 ) -> int:
     store = cfg.backends.store
     if store.kind != "postgres":
@@ -319,6 +445,17 @@ def _migrate(
             file=sys.stderr,
         )
         return 2
+    group = cfg.limits.reset_group
+    if reset_role and group and reset_role != group:
+        print(
+            f"refused: --reset-role {reset_role!r} differs from limits.reset_group {group!r}; config is the one source",
+            file=sys.stderr,
+        )
+        return 2
+    reset_role = reset_role or group
+    if not reset_role:
+        print("refused: give --reset-role or set limits.reset_group", file=sys.stderr)
+        return 2
     dsn = os.environ.get("HADAVIN_MIGRATE_DSN")
     if not dsn:
         print("refused: set HADAVIN_MIGRATE_DSN to the migration role's DSN", file=sys.stderr)
@@ -332,6 +469,10 @@ def _migrate(
         runtime_role=runtime_role,
         portal_role=portal_role,
         purge_role=purge_role,
+        reset_role=reset_role,
+        stop_role=stop_role,
+        max_open_stop_requests=cfg.limits.max_open_stop_requests,
+        lock_timeout_ms=cfg.limits.migrate_lock_timeout_ms,
         iam_auth=store.iam_auth,
         region=store.region,
         sslmode=store.sslmode,
@@ -364,7 +505,17 @@ def audit_verify(audit) -> int:
 
 
 def _kill_switch_store_down(what: str, exc: BaseException) -> int:
-    """4 when the store cannot be reached; 2 when it answers but is not ready (missing table or grant)."""
+    """4 when the store cannot be reached; 7 when it is busy (NOT done, retry); 2 when it answers but is not ready
+    (missing table or grant)."""
+    if isinstance(exc, StoreBusy):
+        verb = {"set": "stop", "reset": "reset"}.get(what, what)
+        print(
+            f"{verb} NOT done: the store is busy (a lock or statement timeout, a deadlock or the connection limit). "
+            "Nothing was changed. Run the same command again; if it keeps failing, use the database "
+            "administrator recipe in docs/stop-state-runbook.md.",
+            file=sys.stderr,
+        )
+        return 7
     if is_connectivity_error(exc):
         print(
             f"kill switch NOT {what}: the store is unreachable. Nothing was changed. "
@@ -380,23 +531,64 @@ def _kill_switch_store_down(what: str, exc: BaseException) -> int:
     return 2
 
 
-def kill_switch(limits: Limits, action: str, by: str) -> int:
-    """Run stop/reset for a caller (the CLI once a shared store exists, or an in-process admin hook).
+def _print_status(state) -> None:
+    print(
+        f"kill switch {'ON' if state.on else 'OFF'} (by {state.by}) since {state.ts.isoformat()}; "
+        f"version {state.version}, open_requests {state.open_requests}"
+    )
+
 
-    Exit codes: 0 done; 3 reset refused because the audit store is unavailable (the switch stays ON); 4 the
-    store is unreachable (the switch was NOT changed).
+def kill_switch(
+    limits: Limits,
+    action: str,
+    by: str,
+    *,
+    expect_version: int | None = None,
+    expect_open: int | None = None,
+) -> int:
+    """Run stop/reset/status/whois for a caller (the CLI once a shared store exists, or an in-process admin hook).
+
+    Exit codes: 0 done; 2 usage; 3 reset refused because the audit store is unavailable (the switch stays ON);
+    4 the store is unreachable (the switch was NOT changed); 7 the store is busy (NOT done); 10 `check` found problems; 5 not permitted (the name, the credential or the
+    database refused); 6 the stops changed since they were read, or the switch row is missing; 9 the database is
+    not migrated.
     """
+    if action == "whois":
+        try:
+            print(limits.label(by))
+        except StopNotPermitted as exc:
+            print(f"refused: {exc}", file=sys.stderr)
+            return 5
+        return 0
+    if action == "status":
+        try:
+            _print_status(limits.status())
+        except Exception as exc:  # noqa: BLE001 - classified below
+            return _kill_switch_store_down("read", exc)
+        return 0
     if action == "stop":
         try:
-            limits.stop(by)
+            state = limits.stop(by)
         except AuditUnavailable:
             raise
+        except NotMigrated:
+            print(
+                "database not migrated; use the DBA stop recipe (docs/stop-state-runbook.md)",
+                file=sys.stderr,
+            )
+            return 9
         except Exception as exc:  # noqa: BLE001 - classified below
             return _kill_switch_store_down("set", exc)
-        print(f"kill switch ON (by {by})")
+        print(f"kill switch ON (by {state.by})")
         return 0
+    if expect_version is None or expect_open is None:
+        print(
+            "reset needs --expect-version and --expect-open (read them with `limits status`)",
+            file=sys.stderr,
+        )
+        return 2
     try:
-        limits.reset(by)
+        state = limits.reset(by, expect_version=expect_version, expect_open=expect_open)
     except AuditUnavailable:
         print(
             "refused: the audit store is unavailable, so the reset cannot be recorded. "
@@ -404,9 +596,32 @@ def kill_switch(limits: Limits, action: str, by: str) -> int:
             file=sys.stderr,
         )
         return 3
+    except StopNotPermitted as exc:
+        print(f"refused: {exc}", file=sys.stderr)
+        return 5
+    except SwitchChanged as exc:
+        print(f"reset NOT done: {exc}", file=sys.stderr)
+        return 6
+    except NotMigrated:
+        print(
+            "database not migrated; use the DBA stop recipe (docs/stop-state-runbook.md)",
+            file=sys.stderr,
+        )
+        return 9
     except Exception as exc:  # noqa: BLE001 - classified below
         return _kill_switch_store_down("reset", exc)
-    print(f"kill switch OFF (by {by})")
+    try:  # a stop can land while the reset commits: read once more and say so
+        now_state = limits.status()
+    except Exception:  # noqa: BLE001 - the reset happened; only the second read failed
+        print(f"reset done (version {state.version}); the status could not be read again")
+        return 0
+    if now_state.on:
+        print(
+            f"reset done (version {state.version}); the switch is still ON: "
+            f"{now_state.open_requests} stop request(s) arrived during the reset"
+        )
+    else:
+        print(f"kill switch OFF (version {state.version})")
     return 0
 
 
```

### B.9.10 Config, defaults, app wiring, agent loop, backend table (diffs in full)

`git diff origin/main...origin/core/P2a-1 -- src/hadavin_sdk/config.py src/hadavin_sdk/defaults.py src/hadavin_sdk/app.py src/hadavin_sdk/runtime/agent_loop.py src/hadavin_sdk/backends/table.py`:
```diff
diff --git a/src/hadavin_sdk/app.py b/src/hadavin_sdk/app.py
index 0a78ff9..6c7945a 100644
--- a/src/hadavin_sdk/app.py
+++ b/src/hadavin_sdk/app.py
@@ -59,6 +59,27 @@ class App:
     purge_store: Store | None = None
 
 
+def _check_stop_guard(store, cfg) -> None:
+    """Start-up probe of the kill switch guard: a finding refuses the start; a busy database is only logged."""
+    from hadavin_sdk.runtime import stop_state
+
+    result = stop_state.probe(
+        store,
+        environment=cfg.environment,
+        runtime_role=cfg.limits.runtime_role,
+        stop_role=cfg.limits.stop_role,
+        reset_group=cfg.limits.reset_group,
+    )
+    if result.status == stop_state.FAILED:
+        raise ConfigError(
+            "the kill switch guard is not in place: " + "; ".join(result.problems[:10])
+        )
+    if result.status == stop_state.INCONCLUSIVE:
+        _LOG.warning(
+            "kill switch guard probe: the database was busy; the tick probe will try again"
+        )
+
+
 def build(
     config_dir: Path | None,
     agents: list[str],
@@ -87,6 +108,14 @@ def build(
         # Only the purge role may DELETE evidence; without its DSN the purge fails every tick and the
         # redaction maps (plaintext originals) are kept for ever.
         raise ConfigError("backends.store.purge_dsn_secret_name is required in pilot and prod")
+    if live and not cfg.limits.label_key_secret_name:
+        raise ConfigError("limits.label_key_secret_name is required in pilot and prod")
+    postgres_live = live and getattr(b.store, "kind", "") == "postgres"
+    if postgres_live and not (cfg.limits.runtime_role and cfg.limits.reset_group):
+        raise ConfigError(
+            "limits.runtime_role and limits.reset_group are required in pilot and prod with a postgres store "
+            "(the start-up probe checks the kill switch guard for those roles)"
+        )
     if sources and live:
         # A source handed in as an object would replace a configured, probed one; live deployments use Config.sources.
         raise ConfigError("sources= is for tests; configure Config.sources in pilot and prod")
@@ -118,6 +147,7 @@ def build(
         }
         | {sc.token_secret_name for sc in cfg.sources.values() if sc.token_secret_name}
         | ({cfg.evidence.restored_hash_key_secret_name} - {None})
+        | ({cfg.limits.label_key_secret_name} - {None})
     )
     platform_secrets.check(secrets, [s for _, s in b.entries()], executor_names, extra_secret_names)
     # Design 6.6: every read source has a passing scope probe or a client-signed inventory; else no start. The
@@ -168,7 +198,22 @@ def build(
         # screens the document and tool output, where untrusted text enters (config refuses a judge alone).
         summary_detector = combine([m for m in members if m.backend != "llm_judge"])
     channel = channel or make("channel", b.channel, secrets, store=store)
-    limits = Limits(store, audit, reg)
+    label_key = (
+        _secret_key(secrets, cfg.limits.label_key_secret_name, "the limits label key")
+        if cfg.limits.label_key_secret_name
+        else None
+    )
+    # The runtime process holds neither the reset nor the stop credential: Limits has no reset_store and no stop_store.
+    limits = Limits(
+        store,
+        audit,
+        reg,
+        environment=cfg.environment,
+        label_key=label_key,
+        key_id=cfg.limits.key_id,
+    )
+    if postgres_live:
+        _check_stop_guard(store, cfg)
     executor = (
         None if live else Executor(reg, secrets, timeout_s=timeout_s or cfg.executor_timeout_s)
     )
@@ -387,15 +432,19 @@ def _unprobed_tools(cfg: Config, reg: Registry) -> list[str]:
 MIN_RESTORED_KEY_BYTES = 16
 
 
-def _restored_key(secrets: SecretProvider, name: str) -> bytes:
-    """The key that makes the audit's hash of the restored inputs unguessable. An empty or short one would put
-    brute-forceable plain hashes of IP addresses and short names back into the audit."""
+def _secret_key(secrets: SecretProvider, name: str, what: str) -> bytes:
     key = secrets.get(name).encode("utf-8")
     if len(key) < MIN_RESTORED_KEY_BYTES:
-        raise ConfigError(f"the restored-hash key must be at least {MIN_RESTORED_KEY_BYTES} bytes")
+        raise ConfigError(f"{what} must be at least {MIN_RESTORED_KEY_BYTES} bytes")
     return key
 
 
+def _restored_key(secrets: SecretProvider, name: str) -> bytes:
+    """The key that makes the audit's hash of the restored inputs unguessable. An empty or short one would put
+    brute-forceable plain hashes of IP addresses and short names back into the audit."""
+    return _secret_key(secrets, name, "the restored-hash key")
+
+
 def _switched_off(disabled: set[str] | None, source_hosts: dict[str, str]):
     """Why a tool may not run: a source it reads (named in `options.source`, or on one of its hosts) failed its
     scope re-probe and was switched off. The set is the app's own and the tick edits it."""
diff --git a/src/hadavin_sdk/backends/table.py b/src/hadavin_sdk/backends/table.py
index ad3b85b..13b983c 100644
--- a/src/hadavin_sdk/backends/table.py
+++ b/src/hadavin_sdk/backends/table.py
@@ -118,6 +118,11 @@ class PostgresSettings(KindSettings):
     # A second DSN (another database role) for the evidence purge, the only identity that may DELETE
     # `tool_calls` and `redaction_maps` (`hadavin-sdk migrate --purge-role`). None: the runtime's own DSN.
     purge_dsn_secret_name: str | None = None
+    # Names of secrets that hold the DSN of the kill switch's reset login and stop login. They do NOT end in
+    # `_secret_name` on purpose: the runtime reads every `*_secret_name` field at start-up, and it must never
+    # hold these. Only `hadavin-sdk limits reset|stop|check` resolve them.
+    reset_credential_ref: str | None = None
+    stop_credential_ref: str | None = None
     iam_auth: bool = (
         False  # RDS IAM login: no database password anywhere (needs the `aws` extra too)
     )
diff --git a/src/hadavin_sdk/config.py b/src/hadavin_sdk/config.py
index dfa135b..9d5ce2a 100644
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -12,10 +12,20 @@ from typing import Annotated, Any, Literal, get_args
 from urllib.parse import urlsplit
 
 import yaml
-from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator
+from pydantic import (
+    BaseModel,
+    BeforeValidator,
+    ConfigDict,
+    Field,
+    StrictInt,
+    ValidationError,
+    field_validator,
+    model_validator,
+)
 from pydantic_settings import BaseSettings, SettingsConfigDict
 
 from hadavin_sdk import defaults, deferred
+from hadavin_sdk.audit.labelkey import valid_key_id
 from hadavin_sdk.backends.table import DEFAULTS, DEV_ONLY, NOT_PROD, TABLE, KindSettings
 from hadavin_sdk.errors import ConfigError
 from hadavin_sdk.scrub_settings import ScrubSettings
@@ -26,6 +36,7 @@ __all__ = [
     "ConfigError",
     "EvidenceSettings",
     "K1bSettings",
+    "LimitsSettings",
     "Retention",
     "Route",
     "ScrubSettings",
@@ -58,6 +69,22 @@ class Route(_Strict):
     output_usd_per_mtok: Money
     max_tokens: int = Field(gt=0)
 
+    @field_validator("input_usd_per_mtok", "output_usd_per_mtok")
+    @classmethod
+    def _price(cls, v: Decimal) -> Decimal:
+        """Finite (pydantic already refuses non-finite Decimals; kept as a second line), not negative or minus zero,
+        at most `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK`, at most 6 decimals (checked last, so a huge exponent cannot
+        make `quantize` raise)."""
+        if not v.is_finite():
+            raise ValueError("a price must be a finite number")
+        if v.is_signed():
+            raise ValueError("a price must not be negative")
+        if v > defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:
+            raise ValueError(f"a price may be at most {defaults.MAX_ROUTE_PRICE_USD_PER_MTOK}")
+        if v != v.quantize(Decimal("1E-6")):
+            raise ValueError("a price may have at most 6 decimal places")
+        return v
+
 
 class Backends(_Strict):
     """One validated settings model per capability (built by `parse_backends`, never from raw YAML)."""
@@ -308,6 +335,42 @@ def _inventory_ref_ok(ref: str) -> bool:
     )
 
 
+class LimitsSettings(_Strict):
+    """The kill switch: who may reset, the label key and the stop-request cap. The label key is read by the
+    runtime at start-up (`_secret_name` on purpose); the stop and reset database credentials are NOT (see
+    `PostgresSettings.stop_credential_ref`)."""
+
+    reset_names: frozenset[str] = (
+        frozenset()
+    )  # raw login names allowed to run `limits reset` (a typo guard)
+    reset_group: str | None = None  # the NOLOGIN database role whose members may reset
+    label_key_secret_name: str | None = None
+    # The database roles the probe checks by NAME (never the connected one): the runtime login and the stop login.
+    runtime_role: str | None = None
+    stop_role: str | None = None
+    key_id: str = "k1"
+    max_open_stop_requests: StrictInt = Field(
+        default=defaults.KILL_SWITCH_MAX_OPEN_STOP_REQUESTS, ge=1
+    )
+    migrate_lock_timeout_ms: StrictInt = Field(
+        default=defaults.KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS, ge=1
+    )  # 0 would mean "no timeout" to PostgreSQL
+
+    @field_validator("runtime_role", "stop_role", "reset_group")
+    @classmethod
+    def _role(cls, v: str | None) -> str | None:
+        if v is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", v):
+            raise ValueError("a plain database role name: letters, digits, underscore")
+        return v
+
+    @field_validator("key_id")
+    @classmethod
+    def _key_id(cls, v: str) -> str:
+        if not valid_key_id(v):
+            raise ValueError("key_id must match [A-Za-z0-9_-]{1,32}")
+        return v
+
+
 class Settings(BaseSettings):
     model_config = SettingsConfigDict(env_prefix="HADAVIN_")
     config_dir: Path
@@ -333,6 +396,7 @@ class Config(_Strict):
     tool_timeout_s: float = Field(default=10.0, gt=0)
     retention: Retention = Retention()
     evidence: EvidenceSettings = EvidenceSettings()
+    limits: LimitsSettings = LimitsSettings()
     # design 6.6: a read source that cannot be probed names an operator-attested inventory instead (the reference
     # is format-checked and logged; its hash is NOT compared with the page and nobody is verified to have signed),
     # "<page>#<anchor> sha256:<64 hex>".
@@ -369,6 +433,13 @@ class Config(_Strict):
             ]
             refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []
         refused += _anchor_refusals(self.environment, self.backends)
+        store = self.backends.store
+        if (
+            self.environment != "dev"
+            and getattr(store, "kind", "") == "postgres"
+            and not store.stop_credential_ref
+        ):
+            refused.append("store postgres: stop_credential_ref is required")
         if refused:
             raise ValueError(f"environment {self.environment}: refused: {', '.join(refused)}")
         return self
diff --git a/src/hadavin_sdk/defaults.py b/src/hadavin_sdk/defaults.py
index de442d1..5f2282c 100644
--- a/src/hadavin_sdk/defaults.py
+++ b/src/hadavin_sdk/defaults.py
@@ -129,3 +129,29 @@ K8S_MAX_PAGES = 25  # pages followed per list; past that the answer says it is i
 K8S_JSON_CAP_BYTES = 1024 * 1024  # fetch cap for a JSON list reply
 K8S_LOG_SLACK_BYTES = 8192  # fetch-cap room over `log_bytes` for the line framing
 K8S_LOG_BYTES = 65536  # asked of the API as limitBytes
+
+# --- money (P4d-a2-i): one named block; `store/protocol.py`, `models.py` and `config.py` import these -------------------
+MAX_USD = 10**12  # the most one amount of money (one booking, one cost, one actual) may be, in USD
+# The most one model price may be, in USD per million tokens. 10**6 is one dollar per token, far above any list price
+# known to the author; it is not read from a provider's price list (UNVERIFIED), so a lead may lower it.
+MAX_ROUTE_PRICE_USD_PER_MTOK = 10**6
+
+# --- kill switch (stop state): the stop request table, the migration waits and the role-level settings -------------
+KILL_SWITCH_MAX_OPEN_STOP_REQUESTS = (
+    1000  # past this many open requests a stop adds no row; the switch reads ON
+)
+KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS = (
+    2000  # a migration that waits longer for a table lock aborts (a stop waits less)
+)
+KILL_SWITCH_MIGRATE_ADVISORY_WAIT_MS = 60000  # the wait for the migration lock itself
+KILL_SWITCH_ROLE_STATEMENT_TIMEOUT_MS = (
+    30000  # role defaults for honest code only; a session can undo them
+)
+KILL_SWITCH_ROLE_LOCK_TIMEOUT_MS = 10000
+KILL_SWITCH_ROLE_IDLE_IN_TRANSACTION_TIMEOUT_MS = 60000
+KILL_SWITCH_RUNTIME_CONNECTION_LIMIT = 20
+KILL_SWITCH_STOP_CONNECTION_LIMIT = 2
+KILL_SWITCH_CALL_BUDGET_MS = 5000  # statement_timeout of the stop and the probe's short connection
+KILL_SWITCH_CALL_LOCK_TIMEOUT_MS = (
+    1000  # lock_timeout of the same connection (a stop waits less than a migration)
+)
diff --git a/src/hadavin_sdk/runtime/agent_loop.py b/src/hadavin_sdk/runtime/agent_loop.py
index 59d7610..b05c54c 100644
--- a/src/hadavin_sdk/runtime/agent_loop.py
+++ b/src/hadavin_sdk/runtime/agent_loop.py
@@ -237,7 +237,10 @@ class Runtime:
             _LOG.warning("run %s: audit write for card %s failed", run.run_id, operation)
 
     def _limits_stop(self, run: Run, cited: list[str] | None = None) -> Run | None:
-        blocked = self.limits.blocked(run.agent_id)
+        try:  # limits unreadable: stop means stop, so the run goes to a person
+            blocked = self.limits.blocked(run.agent_id)
+        except Exception:  # noqa: BLE001
+            return self._to(run, S.NEEDS_PERSON, "limits_unavailable")
         if "kill_switch" in blocked:
             return self._to(run, S.STOPPED, "kill_switch")
         if blocked:
@@ -736,12 +739,16 @@ class Runtime:
             return "recheck.unknown_agent_or_action"
         if plan.hash() != decision.plan_hash:
             return "plan_changed"
+        try:
+            blocked_now = self.limits.blocked(agent.id)
+        except Exception:  # noqa: BLE001 - limits unreadable: stop means stop
+            return "recheck.limits_unavailable"
         now_d = authorize(
             self._principal(run),
             agent,
             contract,
             plan,
-            self.limits.blocked(agent.id),
+            blocked_now,
             self.inputs_view(run, plan),
         )
         if now_d.outcome == "deny":
```

### B.9.11 What PR 76 changes, in plain words

Line numbers here are PR 76 line numbers unless they say main.
1. A stop is no longer an UPDATE of the row. It is `SELECT ... FROM hadavin_kill_switch_stop(label)` (`S/store/postgres.py:956-959`, `:994-998`), a SECURITY DEFINER function that inserts one row into the new table `kill_switch_stop_requests` (function text `S/store/migrate.py` `_STOP_FN`, table `0007:13-18`). `set_kill_switch` refuses anything but `on=True` (`S/store/postgres.py:996-997`).
2. "Is it on" is read from one view, `kill_switch_state` = the flag OR at least one open request (`0007:34-43`); `get_kill_switch` reads the view (`S/store/postgres.py:945-952`).
3. A reset is a second function, `hadavin_kill_switch_reset(label, expected_version, expected_open)` (`_RESET_FN`), reached through a new store method `reset_kill_switch` (`S/store/postgres.py:1000-1004`). It clears the open requests and flips the flag off, and refuses when the version or the open count differs from what the operator read (SQLSTATE HD003).
4. A trigger on `kill_switch` (`0007:54-56`, real text `_GUARD_FN`, re-issued by every `migrate()` run) refuses on->off unless `pg_has_role(session_user, <reset group>, 'MEMBER')` and the login has a row in `kill_switch_login_labels` (HD001); it writes one row to the append-only table `kill_switch_resets`. `session_user` is the real login, so SECURITY DEFINER does not hide the caller.
5. Grants (`S/store/migrate.py` GRANTS hunk): `"kill_switch": Grant("table", "")`, `kill_switch_stop_requests` "", its sequence "", `kill_switch_login_labels` "", `kill_switch_resets` runtime `SELECT` only, `kill_switch_state` `SELECT` for runtime, reset and stop. `Grant` gains two slots, `reset` and `stop`. EXECUTE on all three functions is revoked from PUBLIC (`_install_kill_switch`), then granted: stop function to the runtime role and the stop role, reset function to the reset role only (`migrate()` hunk: `_grant_execute(db, schema, _STOP_SIG, runtime_role)`, `..., stop_role)`, `_grant_execute(db, schema, _RESET_SIG, reset_role)`).
6. `migrate()` gains `reset_role` (REQUIRED: `ConfigError` "migrate needs reset_role" when absent) and `stop_role`, plus timeouts and connection limits. The reset role must exist, be NOLOGIN, and none of the named roles may own the kill switch objects (`_check_kill_switch_roles`). `effective_problems` is run for the reset and stop roles too, and now also refuses a role that is a member of a relation owner.
7. `Limits` takes `stop_store` and `reset_store` (two more store handles on other logins), `reset_names` (a typo guard on the raw name), a label key and `environment` (`S/limits.py:52-84`). `reset` raises `StopNotPermitted` when the process holds no reset credential (`S/limits.py:167-168`). Names are stored only as keyed labels (`S/audit/labelkey.py`, new; not opened: UNVERIFIED content).
8. CLI: `limits stop|reset|status|whois|check`, `--expect-version`, `--expect-open`; `migrate --reset-role --stop-role`; the stop connects with `store.stop_credential_ref`, the reset with `store.reset_credential_ref` (`_limits` in the cli diff). New exit codes 5, 6, 7, 9, 10.
9. A probe (`S/runtime/stop_state.py`, `_guard_report` at `S/store/postgres.py:281-400`) reads the catalog for the NAMED roles: triggers ENABLE ALWAYS, functions SECURITY DEFINER with pinned `search_path` and owned by the table owner, the runtime and stop roles hold no table right on the guarded relations, can execute the stop function and can NOT execute the reset or guard function. It runs as a new tick step `stop_guard_probe` (tick hunk) and as `limits check`.
10. Config: `LimitsSettings` (reset_names, reset_group, label_key_secret_name, runtime_role, stop_role, key_id, max_open_stop_requests, migrate_lock_timeout_ms) and, outside `dev`, `store.stop_credential_ref` is required for postgres (config hunk in B.9.10).
11. Tests: `tests/test_stop_state_db.py` (432 lines), `_cli`, `_config`, `_limits`, `_loop`, `_memory`, `_probe`, `_rollback`, `tests/stop_state_mutants.py`, `docs/stop-state-runbook.md`. None of these was opened: UNVERIFIED what each proves.

## B.10 Answer

Does PR 76 already separate stop (the runtime role may set) from reset (only a reset role may clear) at the database-grant level? YES.
- The runtime role holds no privilege at all on `kill_switch` (`Grant("table", "")`), so it cannot UPDATE the flag. On main it holds `SELECT, INSERT, UPDATE` (main `S/store/migrate.py:55`).
- The runtime role (and the optional stop login) gets EXECUTE on the stop function only. The reset function's EXECUTE goes to the reset group only, after `REVOKE ALL ... FROM PUBLIC`.
- Even a caller that somehow reaches an UPDATE is stopped by the `ENABLE ALWAYS` trigger, which checks `session_user` membership in the reset group and a registered login label.
- The grants are verified after they are made (`effective_problems` for reset and stop roles) and re-checked at every tick by the probe.

What is missing (all about landing, plus items not verified here):
1. It is not on main. Main still has the single upsert (`S/store/postgres.py:453-464`), `_RW` on `kill_switch` (`S/store/migrate.py:55`) and one store handle for both directions (`S/limits.py:45,51`).
2. The branch forks from 1e4752f; main has 12 newer commits and 19 files changed on both sides (lists in B.9), among them `S/config.py`, `S/store/postgres.py`, `S/app.py`, `S/models.py`, `S/defaults.py`, `tests/test_p7_tick.py`.
3. Stage names. PR 76 head has `_STAGES = frozenset({"dev", "pilot", "prod"})` and refuses anything else (`S/limits.py:34`, `:67-68` on PR 76); its config check says `self.environment != "dev"` (config hunk) and its CLI `cfg.environment != "dev"`. Main's stages are `demo`, `pilot`, `prod` (main `S/config.py:341`; commit c709df3 "the old first stage name is refused"). As written, `Limits(environment="demo")` raises `ValueError` on a rebased tree. PR 78's merged copy of `limits.py` already changed this to `_DEMO_STAGES = {"dev", "demo"}` (shown in C.4), which is not on PR 76's head.
4. `migrate()` now fails without `reset_role`. Every caller on main that calls `migrate(dsn)` or `migrate(dsn, runtime_role=...)` must change; PR 76 updates the tests it knew (`tests/test_k2_migrations.py`, `tests/test_p2_postgres.py`, `tests/test_k5_*`), but tests added to main after the fork were never seen by it.
5. Migration ledger on main: `tests/test_p2_postgres.py:290` (PR 76 rewrites it to a glob), `tests/test_k5_fixes2.py:307`, the released manifest and `len(manifest) == 5` (`tests/test_migration_numbers_guards.py:363`), and the unchecked lexer refusal list (B.8).
6. The same branch also brings migration 0006 (spend reservations, P4d). 0007 cannot land without 0006 because the ledger allows no gap (main `S/store/migrate.py:105-106`).
7. Not verified in this lookup: whether the guard holds against the table owner or a superuser (it cannot: the owner can disable a trigger; the probe only reports it), the memory-store twin beyond the quoted lines, and every test file listed in B.9.11 point 11.

---

# STEP C. Price constraint

## C.1 `Money` and `Route` (main)

`src/hadavin_sdk/config.py` lines 57-76 (main 51c9fc4):
```
    57	def _money(v: object) -> object:
    58	    if isinstance(v, float):
    59	        # ValueError, not TypeError: pydantic turns only ValueError into a validation error.
    60	        raise ValueError("money must be a decimal string, not a float")  # noqa: TRY004
    61	    return v
    62	
    63	
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
On main a price is any Decimal that is not a float: zero and negative values load (`S/config.py:57-64`, `:72-76`). Only `max_tokens` has a bound (`:76`).

## C.2 `Config._cross_checks` (main)

`src/hadavin_sdk/config.py` lines 391-431 (main 51c9fc4):
```
   391	    @model_validator(mode="after")
   392	    def _cross_checks(self) -> Config:
   393	        for source, ref in self.scope_inventory.items():
   394	            if not _inventory_ref_ok(ref):
   395	                raise ValueError(
   396	                    f"scope_inventory {source}: expected '<page>#<anchor> sha256:<64 hex digits>'"
   397	                )
   398	        for d in self.backends.detector:  # llm_judge names a route
   399	            if getattr(d, "route", None) is not None and d.route not in self.routes:
   400	                raise ValueError(f"backends.detector {d.kind}: unknown route {d.route!r}")
   401	        for name, system in self.systems.items():
   402	            if not url_allowed(system.base_url, self.allow_insecure_loopback):
   403	                raise ValueError(
   404	                    f"system {name}: base_url must be https "
   405	                    f"(http only for loopback with allow_insecure_loopback): {system.base_url}"
   406	                )
   407	        refused = []  # environment table, design 4.6: every refusal at once, so one fix round is enough
   408	        live = is_live(self.environment)
   409	        if live:
   410	            refused = [
   411	                f"{c}: {s.kind}" for c, s in self.backends.entries() if (c, s.kind) in DEMO_ONLY
   412	            ]
   413	            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []
   414	        refused += (
   415	            ["made_up_data_only (for demo configs only)"] if live and self.made_up_data_only else []
   416	        )
   417	        sends_text_out = []
   418	        if not live and not self.made_up_data_only:
   419	            sends_text_out = _sends_text_out(self.backends)
   420	        refused += sends_text_out
   421	        refused += _anchor_refusals(self.environment, self.backends)
   422	        if refused:
   423	            tail = (
   424	                "; a demo config that names a real model, a vendor detector or a real approval channel "
   425	                "may send text to a service outside the process (a vendor, or a model you host): set "
   426	                "made_up_data_only: true only when every input is made up; client data runs only in pilot or prod"
   427	                if sends_text_out
   428	                else ""
   429	            )
   430	            raise ValueError(f"environment {self.environment}: refused: {', '.join(refused)}{tail}")
   431	        return self
```
No line in `_cross_checks` looks at `routes` prices. The only route check is that a detector's route name exists (`S/config.py:398-400`).

## C.3 `S/k1b/replay.py` (main)

`src/hadavin_sdk/k1b/replay.py` lines 80-127 (main 51c9fc4):
```
    80	    return sorted(
    81	        p.relative_to(out).as_posix() for d in out.glob("run*") for p in d.rglob("*") if p.is_file()
    82	    )
    83	
    84	
    85	def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: str) -> None:
    86	    route = registry.config.routes[registry.agents[agent_id].model_route]
    87	    zero = route.input_usd_per_mtok == 0 or route.output_usd_per_mtok == 0
    88	    if zero and llm_kind != "fake":
    89	        # A zero price makes every reply cost 0 and the --max-usd cap could never fire.
    90	        raise ConfigError("replay refuses a route with a zero input or output price")
    91	
    92	
    93	def _replay(
    94	    registry: Registry,
    95	    llm: LLM,
    96	    detector: Detector,
    97	    audit: K1bAudit,
    98	    *,
    99	    agent_id: str,
   100	    bundles_dir: Path,
   101	    cause_list_dir: Path,
   102	    k: int,
   103	    max_usd: Decimal,
   104	    out: Path,
   105	    llm_kind: str | None = None,
   106	    acknowledge_masked: bool = False,
   107	    clock: Callable[[], float] | None = None,
   108	) -> ReplayResult:
   109	    """Raises ``ConfigError`` for any refusal (nothing written), ``AuditUnavailable`` when an event cannot be
   110	    written. Aborts (non-transient provider error) and the USD cap return exit code 1."""
   111	    cfg = registry.config
   112	    if k < 1:
   113	        raise ConfigError("replay k must be at least 1")
   114	    if not max_usd.is_finite() or max_usd <= 0:
   115	        raise ConfigError("replay --max-usd must be above zero")
   116	    if agent_id not in registry.agents:
   117	        raise ConfigError(f"unknown agent {agent_id!r}")
   118	    _refuse_zero_price(registry, agent_id, llm_kind or cfg.backends.llm.kind)
   119	    if not cfg.k1b.redact and not acknowledge_masked:
   120	        raise ConfigError(
   121	            "k1b.redact is false: client data would go to the model unmasked. Pass "
   122	            "--i-know-data-is-already-masked only if the bundles are already masked"
   123	        )
   124	    out = Path(out)
   125	    if out.exists() and (not out.is_dir() or any(out.iterdir())):
   126	        raise ConfigError("replay output folder exists and is not empty")
   127	    cause = load_cause_list(cause_list_dir)
```
The only zero-price refusal on main is here: `_refuse_zero_price` (`S/k1b/replay.py:85-90`), called at `:118`. It covers the replay command only, one route (the agent's), zero only (a negative price passes), and it lets the `fake` kind through (`:88`).

## C.4 PR 78 (`origin/core/P4a`)

Head: 4a0976ffdbda144f768ee7118b5d2ef65c757d47 (a merge commit: "Merge origin/core/P2a-1 into core/P4a"). Fork point from main: 1e4752f.

Commits (`git log --oneline origin/main..origin/core/P4a`):
```
4a0976f Merge origin/core/P2a-1 into core/P4a
e323ac7 P2a-1: tests that kill two surviving hand mutants (group check in the guard, version-only stale pair)
c86e685 P4a-2: tests import on the base tree (local stub helper, cap stand-in)
8abe234 P4a-2: shim Usage so the fail-before run fails by assertion
f3227f2 P4a-2: tests for the cache classes, pricing words, request counts, k1b bookings, replay guards, zero prices
f349f0b P4a-2: ruff fixes (unused noqa)
781b8ba P4a-2: cache classes read and refused, pricing words, request_bound, k1b whole-call bookings, replay guards, zero-price load check
38a1f55 P2a-1: pilot and CLI tests learn the label key secret and the reset role
df80c12 P4a-1: refuse instead of estimate (Usage, UsageMissing, exact cost_usd, one upward rounding)
ca9b449 P2a-1: build the two kill-switch statements as whole literals (no string building)
63d272e P2a-1: CLI and config tests for the stop state
f0465df Merge origin/core/P4d-a2 into core/P2a-1
0b4ca7a WIP P2a-1: fix existing tests for the new API, add labelkey, memory and real-login Postgres tests
c31f336 P4d-a2-i and P4d-b: money validators, cost rounding, route price check, spend reservations (memory and Postgres, migration 0006)
77ace26 WIP P2a-1: stop-state requests, keyed labels, reset by (version, open) pair
1a885f3 P4d-a1: contract harness and test helpers (store_pair, pg_driver, require_backend, session-end check)
```
PR 78 contains PR 76 as it was at e323ac7 (not PR 76's two later commits d1855a9 and 7f32349) and the P4d commits. PR 78's own commits are df80c12, 781b8ba, f349f0b, f3227f2, 8abe234, c86e685.

Diff stat against main (`git diff --stat origin/main...origin/core/P4a`):
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
PR 78's own part under `src` (`git diff --stat e323ac7 origin/core/P4a -- src/hadavin_sdk`):
```
 src/hadavin_sdk/backends/table.py    |  4 +-
 src/hadavin_sdk/config.py            | 16 +++++++
 src/hadavin_sdk/defaults.py          | 19 ++++++++
 src/hadavin_sdk/k1b/loop.py          | 54 +++++++++++++++++----
 src/hadavin_sdk/k1b/replay.py        | 22 ++++++++-
 src/hadavin_sdk/llm/__init__.py      | 18 ++++++-
 src/hadavin_sdk/llm/anthropic.py     | 36 ++++++++++----
 src/hadavin_sdk/llm/bedrock.py       | 18 ++++---
 src/hadavin_sdk/llm/common.py        | 61 +++++++++++++----------
 src/hadavin_sdk/llm/fake.py          | 24 +++++++---
 src/hadavin_sdk/llm/gemini.py        | 47 +++++++++++++-----
 src/hadavin_sdk/llm/openai_compat.py | 46 +++++++++++++-----
 src/hadavin_sdk/llm/pricing.py       | 74 ++++++++++++++++++++++++++++
 src/hadavin_sdk/llm/protocol.py      | 93 +++++++++++++++++++++++++++++++++++-
 src/hadavin_sdk/models.py            | 31 ++++++++++++
 15 files changed, 478 insertions(+), 85 deletions(-)
```

### C.4.1 `S/config.py`: every changed hunk against main

`git diff origin/main...origin/core/P4a -- src/hadavin_sdk/config.py`:
```diff
diff --git a/src/hadavin_sdk/config.py b/src/hadavin_sdk/config.py
index dfa135b..4dbe471 100644
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -12,10 +12,20 @@ from typing import Annotated, Any, Literal, get_args
 from urllib.parse import urlsplit
 
 import yaml
-from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator
+from pydantic import (
+    BaseModel,
+    BeforeValidator,
+    ConfigDict,
+    Field,
+    StrictInt,
+    ValidationError,
+    field_validator,
+    model_validator,
+)
 from pydantic_settings import BaseSettings, SettingsConfigDict
 
 from hadavin_sdk import defaults, deferred
+from hadavin_sdk.audit.labelkey import valid_key_id
 from hadavin_sdk.backends.table import DEFAULTS, DEV_ONLY, NOT_PROD, TABLE, KindSettings
 from hadavin_sdk.errors import ConfigError
 from hadavin_sdk.scrub_settings import ScrubSettings
@@ -26,6 +36,7 @@ __all__ = [
     "ConfigError",
     "EvidenceSettings",
     "K1bSettings",
+    "LimitsSettings",
     "Retention",
     "Route",
     "ScrubSettings",
@@ -58,6 +69,22 @@ class Route(_Strict):
     output_usd_per_mtok: Money
     max_tokens: int = Field(gt=0)
 
+    @field_validator("input_usd_per_mtok", "output_usd_per_mtok")
+    @classmethod
+    def _price(cls, v: Decimal) -> Decimal:
+        """Finite (pydantic already refuses non-finite Decimals; kept as a second line), not negative or minus zero,
+        at most `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK`, at most 6 decimals (checked last, so a huge exponent cannot
+        make `quantize` raise)."""
+        if not v.is_finite():
+            raise ValueError("a price must be a finite number")
+        if v.is_signed():
+            raise ValueError("a price must not be negative")
+        if v > defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:
+            raise ValueError(f"a price may be at most {defaults.MAX_ROUTE_PRICE_USD_PER_MTOK}")
+        if v != v.quantize(Decimal("1E-6")):
+            raise ValueError("a price may have at most 6 decimal places")
+        return v
+
 
 class Backends(_Strict):
     """One validated settings model per capability (built by `parse_backends`, never from raw YAML)."""
@@ -308,6 +335,32 @@ def _inventory_ref_ok(ref: str) -> bool:
     )
 
 
+class LimitsSettings(_Strict):
+    """The kill switch: who may reset, the label key and the stop-request cap. The label key is read by the
+    runtime at start-up (`_secret_name` on purpose); the stop and reset database credentials are NOT (see
+    `PostgresSettings.stop_credential_ref`)."""
+
+    reset_names: frozenset[str] = (
+        frozenset()
+    )  # raw login names allowed to run `limits reset` (a typo guard)
+    reset_group: str | None = None  # the NOLOGIN database role whose members may reset
+    label_key_secret_name: str | None = None
+    key_id: str = "k1"
+    max_open_stop_requests: StrictInt = Field(
+        default=defaults.KILL_SWITCH_MAX_OPEN_STOP_REQUESTS, ge=1
+    )
+    migrate_lock_timeout_ms: StrictInt = Field(
+        default=defaults.KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS, ge=1
+    )  # 0 would mean "no timeout" to PostgreSQL
+
+    @field_validator("key_id")
+    @classmethod
+    def _key_id(cls, v: str) -> str:
+        if not valid_key_id(v):
+            raise ValueError("key_id must match [A-Za-z0-9_-]{1,32}")
+        return v
+
+
 class Settings(BaseSettings):
     model_config = SettingsConfigDict(env_prefix="HADAVIN_")
     config_dir: Path
@@ -333,6 +386,7 @@ class Config(_Strict):
     tool_timeout_s: float = Field(default=10.0, gt=0)
     retention: Retention = Retention()
     evidence: EvidenceSettings = EvidenceSettings()
+    limits: LimitsSettings = LimitsSettings()
     # design 6.6: a read source that cannot be probed names an operator-attested inventory instead (the reference
     # is format-checked and logged; its hash is NOT compared with the page and nobody is verified to have signed),
     # "<page>#<anchor> sha256:<64 hex>".
@@ -346,6 +400,22 @@ class Config(_Strict):
     )  # dev executor only
     root: Path
 
+    @model_validator(mode="after")
+    def _priced_routes_for_real_backends(self) -> Config:
+        """A zero price makes every reply cost 0, so no spend cap could fire. Only the fake llm kind may have one.
+        Names the routes only, never their prices."""
+        if self.backends.llm.kind != "fake":
+            zero = [
+                name
+                for name, r in self.routes.items()
+                if r.input_usd_per_mtok == 0 or r.output_usd_per_mtok == 0
+            ]
+            if zero:
+                raise ValueError(
+                    f"routes with a zero input or output price need the fake llm kind: {', '.join(sorted(zero))}"
+                )
+        return self
+
     @model_validator(mode="after")
     def _cross_checks(self) -> Config:
         for source, ref in self.scope_inventory.items():
@@ -369,6 +439,13 @@ class Config(_Strict):
             ]
             refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []
         refused += _anchor_refusals(self.environment, self.backends)
+        store = self.backends.store
+        if (
+            self.environment != "dev"
+            and getattr(store, "kind", "") == "postgres"
+            and not store.stop_credential_ref
+        ):
+            refused.append("store postgres: stop_credential_ref is required")
         if refused:
             raise ValueError(f"environment {self.environment}: refused: {', '.join(refused)}")
         return self
```

Which commit each price hunk comes from (`git log -S` on the branch):
- `Route._price` (the field validator: finite, not negative, at most `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK` = `10**6` at `S/defaults.py:137` on PR 78, at most 6 decimals): commit c31f336 (P4d). It is also on PR 76 (`S/config.py:74-83` there). It lets zero through: `Decimal("0").is_signed()` is false. It refuses minus zero.
- `Config._priced_routes_for_real_backends` (zero input or output price refused unless `backends.llm.kind == "fake"`): commit 781b8ba (P4a-2). PR 78's own. On PR 78 it is at `S/config.py:403-417`, just before `_cross_checks` (`:419-420`).
- The `LimitsSettings` and `stop_credential_ref` hunks are PR 76's, not price work.

PR 78's own change to `config.py` alone (`git diff e323ac7 origin/core/P4a -- S/config.py`):

`git diff e323ac7..origin/core/P4a -- src/hadavin_sdk/config.py`:
```diff
diff --git a/src/hadavin_sdk/config.py b/src/hadavin_sdk/config.py
index aadcb01..4dbe471 100644
--- a/src/hadavin_sdk/config.py
+++ b/src/hadavin_sdk/config.py
@@ -400,6 +400,22 @@ class Config(_Strict):
     )  # dev executor only
     root: Path
 
+    @model_validator(mode="after")
+    def _priced_routes_for_real_backends(self) -> Config:
+        """A zero price makes every reply cost 0, so no spend cap could fire. Only the fake llm kind may have one.
+        Names the routes only, never their prices."""
+        if self.backends.llm.kind != "fake":
+            zero = [
+                name
+                for name, r in self.routes.items()
+                if r.input_usd_per_mtok == 0 or r.output_usd_per_mtok == 0
+            ]
+            if zero:
+                raise ValueError(
+                    f"routes with a zero input or output price need the fake llm kind: {', '.join(sorted(zero))}"
+                )
+        return self
+
     @model_validator(mode="after")
     def _cross_checks(self) -> Config:
         for source, ref in self.scope_inventory.items():
```

### C.4.2 `S/limits.py`
PR 78's own commits do not touch `limits.py` (`git diff e323ac7 origin/core/P4a -- S/limits.py` is empty). Against main the file differs only by PR 76's work. Against PR 76's HEAD it differs because PR 76 moved on after the merge:

`git diff origin/core/P2a-1..origin/core/P4a -- src/hadavin_sdk/limits.py`:
```diff
diff --git a/src/hadavin_sdk/limits.py b/src/hadavin_sdk/limits.py
index 67a2b2a..f0a8724 100644
--- a/src/hadavin_sdk/limits.py
+++ b/src/hadavin_sdk/limits.py
@@ -25,13 +25,14 @@ from hadavin_sdk.store.protocol import (
     ResetRefused,
     StaleCount,
     Store,
-    StoreBusy,
     SwitchRowMissing,
 )
 
 _LOG = logging.getLogger(__name__)
 MIN_KEY_BYTES = 16  # the same minimum as a restored audit key
-_STAGES = frozenset({"dev", "pilot", "prod"})  # exactly what Config.environment accepts; no alias
+_DEMO_STAGES = frozenset(
+    {"dev", "demo"}
+)  # the only stage that may use a memory store or a random label key
 _MISSING_ROW = "the kill_switch row is missing; a database administrator must re-seed it"
 
 
@@ -64,17 +65,15 @@ class Limits:
     ) -> None:
         if not valid_key_id(key_id):
             raise ValueError("key_id must match [A-Za-z0-9_-]{1,32}")
-        if environment not in _STAGES:  # no alias: "demo" is not "dev" (Config.environment decides)
-            raise ValueError(f"environment must be one of {sorted(_STAGES)}, not {environment!r}")
-        dev = environment == "dev"
-        if not dev and isinstance(store, MemoryStore):
-            raise ValueError("a memory store is allowed only when environment is dev")
+        demo = environment in _DEMO_STAGES
+        if not demo and isinstance(store, MemoryStore):
+            raise ValueError("a memory store is allowed only in the demo stage")
         if label_key is None:
-            if not dev:
-                raise ValueError("a label key is required when environment is not dev")
+            if not demo:
+                raise ValueError("a label key is required outside the demo stage")
             label_key = secrets.token_bytes(32)
             _LOG.warning(
-                "limits: no label key given; using a per-process random key (environment dev only)"
+                "limits: no label key given; using a per-process random key (demo stage only)"
             )
         self.store, self.audit, self.registry = store, audit, registry
         self.environment = environment
@@ -138,12 +137,7 @@ class Limits:
             _LOG.error(
                 "limits: label key unavailable; the stop is recorded as actor not identified"
             )
-        try:
-            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
-        except StoreBusy:
-            # The busy call rolled back, so a second try cannot double a row. Once, on a fresh short connection.
-            _LOG.error("limits: the store was busy for the stop; trying once more")
-            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
+        state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
         if state.on is not True:
             raise StopNotConfirmed("the stop returned a row that does not read ON")
         self.audit.write_outcome(
```
Read this diff with care: `-` lines are PR 76's head, `+` lines are PR 78. PR 78 has the stage fix (`_DEMO_STAGES = {"dev", "demo"}`) and lacks PR 76's later `StoreBusy` retry. Which side is newer for the stage line was not traced commit by commit: UNVERIFIED.

### C.4.3 `S/llm/common.py`: PR 78's own change

`git diff e323ac7..origin/core/P4a -- src/hadavin_sdk/llm/common.py`:
```diff
diff --git a/src/hadavin_sdk/llm/common.py b/src/hadavin_sdk/llm/common.py
index 5f7f75d..6f016bd 100644
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -9,16 +9,17 @@ import json
 import re
 import time
 import urllib.request
-from collections.abc import Callable
-from dataclasses import dataclass
-from decimal import Decimal, InvalidOperation
+from collections.abc import Callable, Mapping
+from dataclasses import dataclass, field
+from types import MappingProxyType
 from typing import Any
 from urllib.parse import urlsplit
 
 from hadavin_sdk.errors import ConfigError
 from hadavin_sdk.guard import http as http_guard
+from hadavin_sdk.llm.pricing import check_facts, check_output_plausible, cost_usd
 from hadavin_sdk.llm.retry import with_retry
-from hadavin_sdk.models import Reply, ToolCall, round_cost_up
+from hadavin_sdk.models import Reply, ToolCall, Usage, round_cost_up
 
 # The forced tool an `output_schema` becomes: its input schema IS the schema, so the API enforces the shape.
 ANSWER_TOOL = "submit_answer"
@@ -57,8 +58,9 @@ def pinned(
 
 
 def estimate_tokens(text: str) -> int:
-    """For a provider that reports no usage. Deliberately pessimistic (3 chars a token, never 0): a budget fed
-    zeros never fires."""
+    """A guess at the tokens a text COULD use (3 chars a token, never 0). It bounds nothing: it estimates what a
+    call could use, never what it used. A provider reply without usage is refused (`UsageMissing`), not estimated
+    with this."""
     return max(1, len(text) // 3)
 
 
@@ -149,17 +151,20 @@ def stop_reason(raw: str | None, calls: list[ToolCall]) -> str:
     return "tool_use" if calls else "end_turn"
 
 
-def price_cost(route: Any, tokens_in: int, tokens_out: int) -> Decimal:
-    """The exact cost of a call from the route's prices, rounded UP to 8 decimals (`models.round_cost_up`).
-    A route that skipped validation (`model_copy(update=...)`) with a bad price gives `ValueError`."""
+_NO_FACTS: Mapping[str, object] = MappingProxyType({})
+
+
+def request_bound(llm: Any) -> int:
+    """The most requests one `chat` call sends, as the kind declares it (`REQUESTS_PER_CHAT`). Strict: an object
+    with no declaration is a `TypeError`; a declared value that is not an int of at least 1 (a bool is refused) is
+    a `ValueError`. It is NOT multiplied by `max_attempts`."""
     try:
-        cost = (
-            Decimal(tokens_in) * route.input_usd_per_mtok
-            + Decimal(tokens_out) * route.output_usd_per_mtok
-        ) / Decimal(1_000_000)
-    except InvalidOperation as exc:
-        raise ValueError("the route's price is not a usable number") from exc
-    return round_cost_up(cost)
+        n = llm.REQUESTS_PER_CHAT
+    except AttributeError:
+        raise TypeError(f"{type(llm).__name__} declares no REQUESTS_PER_CHAT") from None
+    if type(n) is not int or n < 1:
+        raise ValueError(f"{type(llm).__name__}.REQUESTS_PER_CHAT must be an int of at least 1")
+    return n
 
 
 def reply(
@@ -167,22 +172,25 @@ def reply(
     *,
     text: str,
     calls: list[ToolCall],
-    tokens: tuple[int | None, int | None],
+    usage: Usage,
     stop: str | None,
     started: float,
-    sent: str,
+    facts: Mapping[str, object] = _NO_FACTS,
 ) -> Reply:
-    """The Reply, priced from the route. Missing usage is estimated from what was sent and received. A cut-off
-    answer keeps its cost but loses its tool calls: their input may be incomplete."""
-    tokens_in = tokens[0] or estimate_tokens(sent)
-    tokens_out = tokens[1] or estimate_tokens(text + json.dumps([c.input for c in calls]))
-    cost = price_cost(route, tokens_in, tokens_out)
+    """The Reply, priced from the route and the counts the provider reported (never estimated). The provider's
+    pricing words (`facts`) are checked first (`pricing.check_facts`). A reported output of 0 on a reply that holds text or a tool call is refused (`UsageMissing("implausible_zero")`); `cost_usd`
+    refuses a cache count and a zero input on a priced route. The exact cost is rounded UP once, here
+    (`models.round_cost_up`). A cut-off answer keeps its cost but loses its tool calls: their input may be
+    incomplete."""
+    check_output_plausible(usage, text, calls)
+    check_facts(route, facts)
+    cost = round_cost_up(cost_usd(usage, route))
     stop = stop_reason(stop, calls)
     return Reply(
         text=text,
         tool_calls=[] if stop == "max_tokens" else calls,
-        input_tokens=tokens_in,
-        output_tokens=tokens_out,
+        input_tokens=usage.input_tokens,
+        output_tokens=usage.output_tokens,
         cost_usd=cost,
         model_id=route.model_id,
         stop_reason=stop,
@@ -196,8 +204,9 @@ class Answer:
 
     text: str
     calls: list[ToolCall]
-    tokens: tuple[int | None, int | None]
+    usage: Usage
     stop: str | None
+    facts: Mapping[str, object] = field(default_factory=lambda: _NO_FACTS)
 
 
 class NetworkLLM:
```
In words: `price_cost` is removed; `reply()` now takes a `Usage` object and optional provider `facts`, refuses a reply with no usable usage instead of estimating tokens, prices through `llm/pricing.py` `cost_usd` and rounds up once; `request_bound` is new. The whole diff against main for this file also holds the P4d part (`price_cost` with `round_cost_up`, added then removed):

`git diff origin/main...origin/core/P4a -- src/hadavin_sdk/llm/common.py`:
```diff
diff --git a/src/hadavin_sdk/llm/common.py b/src/hadavin_sdk/llm/common.py
index c5e1254..6f016bd 100644
--- a/src/hadavin_sdk/llm/common.py
+++ b/src/hadavin_sdk/llm/common.py
@@ -9,16 +9,17 @@ import json
 import re
 import time
 import urllib.request
-from collections.abc import Callable
-from dataclasses import dataclass
-from decimal import Decimal
+from collections.abc import Callable, Mapping
+from dataclasses import dataclass, field
+from types import MappingProxyType
 from typing import Any
 from urllib.parse import urlsplit
 
 from hadavin_sdk.errors import ConfigError
 from hadavin_sdk.guard import http as http_guard
+from hadavin_sdk.llm.pricing import check_facts, check_output_plausible, cost_usd
 from hadavin_sdk.llm.retry import with_retry
-from hadavin_sdk.models import Reply, ToolCall
+from hadavin_sdk.models import Reply, ToolCall, Usage, round_cost_up
 
 # The forced tool an `output_schema` becomes: its input schema IS the schema, so the API enforces the shape.
 ANSWER_TOOL = "submit_answer"
@@ -57,8 +58,9 @@ def pinned(
 
 
 def estimate_tokens(text: str) -> int:
-    """For a provider that reports no usage. Deliberately pessimistic (3 chars a token, never 0): a budget fed
-    zeros never fires."""
+    """A guess at the tokens a text COULD use (3 chars a token, never 0). It bounds nothing: it estimates what a
+    call could use, never what it used. A provider reply without usage is refused (`UsageMissing`), not estimated
+    with this."""
     return max(1, len(text) // 3)
 
 
@@ -149,30 +151,46 @@ def stop_reason(raw: str | None, calls: list[ToolCall]) -> str:
     return "tool_use" if calls else "end_turn"
 
 
+_NO_FACTS: Mapping[str, object] = MappingProxyType({})
+
+
+def request_bound(llm: Any) -> int:
+    """The most requests one `chat` call sends, as the kind declares it (`REQUESTS_PER_CHAT`). Strict: an object
+    with no declaration is a `TypeError`; a declared value that is not an int of at least 1 (a bool is refused) is
+    a `ValueError`. It is NOT multiplied by `max_attempts`."""
+    try:
+        n = llm.REQUESTS_PER_CHAT
+    except AttributeError:
+        raise TypeError(f"{type(llm).__name__} declares no REQUESTS_PER_CHAT") from None
+    if type(n) is not int or n < 1:
+        raise ValueError(f"{type(llm).__name__}.REQUESTS_PER_CHAT must be an int of at least 1")
+    return n
+
+
 def reply(
     route: Any,
     *,
     text: str,
     calls: list[ToolCall],
-    tokens: tuple[int | None, int | None],
+    usage: Usage,
     stop: str | None,
     started: float,
-    sent: str,
+    facts: Mapping[str, object] = _NO_FACTS,
 ) -> Reply:
-    """The Reply, priced from the route. Missing usage is estimated from what was sent and received. A cut-off
-    answer keeps its cost but loses its tool calls: their input may be incomplete."""
-    tokens_in = tokens[0] or estimate_tokens(sent)
-    tokens_out = tokens[1] or estimate_tokens(text + json.dumps([c.input for c in calls]))
-    cost = (
-        Decimal(tokens_in) * route.input_usd_per_mtok
-        + Decimal(tokens_out) * route.output_usd_per_mtok
-    ) / Decimal(1_000_000)
+    """The Reply, priced from the route and the counts the provider reported (never estimated). The provider's
+    pricing words (`facts`) are checked first (`pricing.check_facts`). A reported output of 0 on a reply that holds text or a tool call is refused (`UsageMissing("implausible_zero")`); `cost_usd`
+    refuses a cache count and a zero input on a priced route. The exact cost is rounded UP once, here
+    (`models.round_cost_up`). A cut-off answer keeps its cost but loses its tool calls: their input may be
+    incomplete."""
+    check_output_plausible(usage, text, calls)
+    check_facts(route, facts)
+    cost = round_cost_up(cost_usd(usage, route))
     stop = stop_reason(stop, calls)
     return Reply(
         text=text,
         tool_calls=[] if stop == "max_tokens" else calls,
-        input_tokens=tokens_in,
-        output_tokens=tokens_out,
+        input_tokens=usage.input_tokens,
+        output_tokens=usage.output_tokens,
         cost_usd=cost,
         model_id=route.model_id,
         stop_reason=stop,
@@ -186,8 +204,9 @@ class Answer:
 
     text: str
     calls: list[ToolCall]
-    tokens: tuple[int | None, int | None]
+    usage: Usage
     stop: str | None
+    facts: Mapping[str, object] = field(default_factory=lambda: _NO_FACTS)
 
 
 class NetworkLLM:
```

`S/llm/pricing.py` (new, 74 lines) was not opened: UNVERIFIED what `check_facts`, `check_output_plausible` and `cost_usd` do beyond the docstring quoted in the hunk above.

### C.4.4 `S/k1b/replay.py`: PR 78's own change

`git diff e323ac7..origin/core/P4a -- src/hadavin_sdk/k1b/replay.py`:
```diff
diff --git a/src/hadavin_sdk/k1b/replay.py b/src/hadavin_sdk/k1b/replay.py
index d0e884c..fc8d52b 100644
--- a/src/hadavin_sdk/k1b/replay.py
+++ b/src/hadavin_sdk/k1b/replay.py
@@ -30,6 +30,7 @@ from hadavin_sdk.k1b.causelist import load_cause_list
 from hadavin_sdk.k1b.diagnosis import Diagnosis
 from hadavin_sdk.k1b.redaction import SCHEME, redact_bundle
 from hadavin_sdk.k1b.report import DISCLAIMER, render_replay_report
+from hadavin_sdk.llm.common import NetworkLLM
 from hadavin_sdk.llm.protocol import LLM
 from hadavin_sdk.models import new_id
 from hadavin_sdk.registry import Registry
@@ -61,7 +62,9 @@ class ReplayResult:
 
 
 def _sha(text: str) -> str:
-    return hashlib.sha256(text.encode("utf-8")).hexdigest()
+    # "surrogatepass": a model's tool name can hold a lone surrogate, which plain UTF-8 refuses (every valid string
+    # hashes as before).
+    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
 
 
 def _diagnosis_dict(d: Diagnosis) -> dict[str, Any]:
@@ -82,6 +85,10 @@ def outputs_files(out: Path) -> list[str]:
     )
 
 
+# An allowlist: a detector kind that calls a paid service is refused without an edit (PL62).
+_REPLAY_DETECTORS = frozenset({"regex", "llm_judge"})
+
+
 def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: str) -> None:
     route = registry.config.routes[registry.agents[agent_id].model_route]
     zero = route.input_usd_per_mtok == 0 or route.output_usd_per_mtok == 0
@@ -107,7 +114,8 @@ def _replay(
     clock: Callable[[], float] | None = None,
 ) -> ReplayResult:
     """Raises ``ConfigError`` for any refusal (nothing written), ``AuditUnavailable`` when an event cannot be
-    written. Aborts (non-transient provider error) and the USD cap return exit code 1."""
+    written. Aborts (non-transient provider error) and the USD cap return exit code 1. ``llm_kind`` is a label the
+    caller promises is true: the guard reads labels, plus one check that a real network kind object is refused."""
     cfg = registry.config
     if k < 1:
         raise ConfigError("replay k must be at least 1")
@@ -116,6 +124,16 @@ def _replay(
     if agent_id not in registry.agents:
         raise ConfigError(f"unknown agent {agent_id!r}")
     _refuse_zero_price(registry, agent_id, llm_kind or cfg.backends.llm.kind)
+    # The loop books only the answered attempt of an answered call and has no meter, so the hidden billed attempts of
+    # a real model have no owner here (PL55): v1 replays only the fake kind and the detectors that cost nothing.
+    if (llm_kind or cfg.backends.llm.kind) != "fake":
+        raise ConfigError("k1b replay runs only on the fake llm kind in v1")
+    if isinstance(
+        llm, NetworkLLM
+    ):  # a real network object under a "fake" label is refused too (PL66)
+        raise ConfigError("k1b replay runs only on the fake llm kind in v1")
+    if any(d.kind not in _REPLAY_DETECTORS for d in cfg.backends.detector):
+        raise ConfigError("k1b replay runs only the regex and llm_judge detector kinds in v1")
     if not cfg.k1b.redact and not acknowledge_masked:
         raise ConfigError(
             "k1b.redact is false: client data would go to the model unmasked. Pass "
```
`_refuse_zero_price` stays, and replay is now refused outright for any llm kind but `fake`.

### C.4.5 Price date
`git grep -nIiE "price_date|priced_at|prices_as_of|price_as_of|as_of|effective_from|valid_from|price.*date|date.*price" origin/core/P4a -- src` hits only `as_of` in `S/k1b/bundle.py`, `S/k1b/redaction.py`, `S/k1b/tools.py` (bundle timestamps, not prices). `Route` on PR 78 has the same four fields as main (`model_id`, `input_usd_per_mtok`, `output_usd_per_mtok`, `max_tokens`) plus the validator. There is no price date.

## C.5 Answer

Does PR 78 already refuse zero or negative prices at config load, or add a price date?
- Negative: YES at config load, by `Route._price` (`v.is_signed()` -> "a price must not be negative"). This is P4d work (c31f336) that PR 78 and PR 76 both carry; it is not on main.
- Zero: YES at config load, but only for a non-`fake` llm kind, by `Config._priced_routes_for_real_backends` (PR 78's own, 781b8ba). With `backends.llm.kind: fake` a zero price still loads on purpose. The check looks at every route in `routes`, not only the routes agents use. It reads `self.backends.llm.kind` only: a detector that names a zero-priced route is covered because it is in `routes`, but a second llm-like backend of another kind is not looked at (UNVERIFIED whether one exists).
- Price date: NO. Nothing on the branch adds one.
- On main today none of this exists: prices are unchecked at load (C.1, C.2) and only replay refuses zero (C.3).

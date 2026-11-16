# findings-B (lane B)
(Saved by the session: the builder's Write of this file was refused by the harness, so this is the builder's returned report extracted VERBATIM by script from its transcript, not edited. Verdicts are the builder's proposals; not yet spot-checked by a reviewer. Audited sha b4cce5b.)

# Lane B report (state and runtime). Audited sha b4cce5b (disk HEAD 1c50990 only adds handover/core-hardening files). Start 07:03 UTC (12:33 IST), end about 07:15 UTC (12:45 IST).

## What failed first
1. **Only two of the five files are on disk.** `parts/checkpoint-B.md` and `parts/map-B.md` were written (the map has 39 skeleton rows, 16 extra rows, and the mandatory section). The Write tool then refused `parts/findings-B.md` with "Subagents should return findings as text, not write report files". I did not work around it (no Bash redirect). `findings-B.md`, `claims-B.md` and `walk-B.md` do NOT exist; their full content is below. The lead or session must save them. The checkpoint file says this.
2. Nothing was run: no pytest, no repo code. A test "found" below is only found by grep, never shown to pass. Every Postgres claim is read from code.
3. **NOT-AUDITED or only partly read:**
 - `k1b/score.py`: lines 1-60 and greps only.
 - `k1b/report.py`: grep only.
 - `k1b/tools.py`: lines 1-130 and 217-244 only.
 - `k1b/diagnosis.py`: lines 1-50 only.
 - `sources/kubernetes.py`: read, except for a quick skim of `rules_problems`.
 - Not checkable from here: how the host app calls `Runtime.handle` and `tick`, and whether `tools.py`/`guard/http.py` blocks plain http for the Kubernetes token (lanes C and A).
4. **Two of my first hypotheses were wrong and I dropped them.** `restored_hash_key_secret_name` and `purge_dsn_secret_name` are both enforced in `app.py:84-89`. The stage-name finding B-11 and the waiver in B-06 were checked against README before I kept them.

Counts: **1 Blocker, 11 Major, 10 Nit (B-01 to B-22).** Own-token use: about 330k input tokens, no sub-agents, no model or network calls. R-numbers used from the preamble and rules: R214, R368, R449, rules 11, 18 and 21 of BRIEF-PREAMBLE.

## Findings (format: id | sev | class | evidence | what is wrong | fix | verdict | thing's own verdict | duplicate-of | guarantee / code / test | patch)
All patches: none (decision or session).

**B-01 | Blocker | UNVERIFIED-CLAIM.**
- Evidence: `runtime/tick.py:235 app.disabled_sources.add(key)`; `app.py:58 disabled_sources: set[str] = field(default_factory=set)`; `cli.py:299 (reviewer-corrected)` (`_tick` builds its own app with `build(None, agents)` and exits after one pass).
- Wrong: README.md:35 says a failed re-probe "switches off every tool that names the source ... until a probe passes". The switch is a Python set inside the tick process. Tick is documented as a separate scheduler job every 30-60 s (tick.py:1-3), so the set dies at exit and the agent-running process never sees it. Only tick exit code 1 and `tick_state.last_error` reach a person. It is a Blocker if tick runs as a separate process (the default). It is fine only if the host runs `run_tick` inside the runtime process; that is UNVERIFIED.
- Fix: store switched-off sources in the Store and read them in `_switched_off` (app.py:469); add a test with two app objects on one store.
- Verdict FIX-NEEDED; own NEEDED.
- Guarantee: README.md:35. Code: tick.py:221-240, app.py:58,104,469. Test: tests/test_k5_round9b.py:295-314 asserts only `app.disabled_sources == {"c"}` on one object; no test found by grep for two processes sharing the flag.

**B-02 | Major | SECURITY.**
- Evidence: `k1b/replay.py:162 o = loop.run_case(` is the first model call, per case. `replay.py:260 audit.emit("replay_run", ...)` is the only audit event of the run and comes after all calls. `cli.py replay_cmd` writes no event first.
- Wrong: masked client data goes to the model before any audit event exists. `K1bAudit.emit` says it must write "BEFORE its side effect" (audit_sink.py:32). A dead audit store is noticed only after all calls are paid. `score_cmd` does it right (intent `started` first).
- Fix: write a `replay_start` intent (agent, bundle-set hash, k, max_usd, redaction mode) before the first `run_case`.
- Verdict FIX-NEEDED; own NEEDED.
- Guarantee: audit_sink.py:1-5,32-35. Code: replay.py:143-174,260. Test: tests/test_k1b_replay.py; no test found by grep for an event before the first model call.

**B-03 | Major | SECURITY.**
- Evidence: `runtime/agent_loop.py:774-781` writes `write_intent(... "action","execute" ...)` before `agent_loop.py:831 run = self._to(run, S.EXECUTING)`. `runtime/runs.py` `ALLOWED` has no EXECUTING to EXECUTING.
- Wrong: `execute()` never checks run state first. Two paths call it for one approval: `approvals/requests.py:179` and tick `reconcile` (tick.py:95). The compare-and-set at line 831 stops a double side effect, but the loser has already put a second "execute" intent into the tamper-evident chain.
- Fix: return early unless the state is WAITING_FOR_APPROVAL or PLAN_READY, or write the intent only after claiming the state.
- Verdict FIX-NEEDED; own NEEDED.
- Guarantee: tick.py:22 "Concurrent ticks are safe". Test: tests/test_p7_tick.py:150 asserts `fake_system.creates == 1` and exit codes only; no test found by grep counting audit intents.

**B-04 | Major | SECURITY.**
- Evidence: `runtime/plan.py:19 idempotency_key=f"{run.run_id}:{contract.id}"`. `agent_loop.py:342-348` makes a new Run on every `handle`. `models.py:95 trigger_ref` is stored and never read (grep: only agent_loop.py:331,346 and models.py:95). `0001_core.sql:7-18` has no unique key on trigger.
- Wrong: the same event delivered twice gives two runs, two approvals and two actions, because the executor key differs per run. R368 (no double-applied messages) is not met in the core. An upstream dedupe may exist (outside the repo, UNVERIFIED).
- Fix: unique index on `(agent_id, trigger_kind, trigger_ref)` for `trigger_ref != "-"`; `handle` returns the existing run; key the executor idempotency on the trigger.
- Verdict FIX-NEEDED; own NEEDED.
- Test: no test found by grep for duplicate delivery.

**B-05 | Major | SECURITY (money).**
- Evidence: `agent_loop.py:239-250` `_limits_stop` reads spend; `:425` calls the model; `:440 self.limits.charge(agent_id, reply.cost_usd)` charges after. `limits.py:17-30`. grep `reserve` finds no spend reservation.
- Wrong: check, then spend, then charge. N runs at the budget edge all pass, and one call can overshoot the per-run cap by a full reply. BRIEF-PREAMBLE rule 18 and R214 say reserve before, reconcile after. `k1b/loop.py:41` documents the overshoot; the runtime does not.
- Fix: atomic reserve of the worst case (`worst_case_usd` exists at k1b/loop.py:115) before the call, reconcile after.
- Verdict FIX-NEEDED; own NEEDED.
- Test: none found for a parallel budget race.

**B-06 | Major | SECURITY (exception, owner only).**
- Evidence: `store/migrate.py:50 "approval_requests": Grant("table", _RW ...)`, `:51 "approval_decisions": ... _APPEND`, `:55 "kill_switch": Grant("table", _RW)`. `cli.py:189` builds the kill-switch and audit command store with the runtime DSN. README.md:33 holds the written waiver ("the runtime role also holds the approver-recording and kill-switch write rights ... separating them (R365) is K6/K8 work and the owner's to accept").
- Wrong: one database role runs the agent process, records approvals and flips the kill switch. A compromised runtime can UPDATE `approval_requests.status` to APPROVED and tick will run the plan, or turn the kill switch off. Preamble rule 11 requires one identity per function. The waiver has no date.
- Fix: add `approver` and `operator` roles to GRANTS (runtime gets SELECT only); give the receiver and the `limits` CLI their own DSN names; add negative tests.
- Verdict FIX-NEEDED, owner yes needed; own NEEDED.
- Test: tests/test_k2_migrations.py:230 covers only the audit log; none found for the runtime role being denied UPDATE on approvals or the kill switch.

**B-07 | Major | DUPLICATE.**
- Evidence: `k1b/loop.py:40-52 class Budget` (own spend meter); `loop.py:125 def run_case(` calls `llm.chat` directly at `:158`; no `Limits` or kill-switch use anywhere in k1b/ (grep).
- Wrong: K1b is a second agent loop and a second spend meter beside `Runtime.handle` and `Limits`. Its spend never reaches the agent's daily and monthly meters, and the kill switch does not stop it. The third loop is `evals.gate` (lane C).
- Fix: at least call `Limits.blocked` before each call and `Limits.charge` after; list the three loops in cross table T-duplicates.
- Verdict FIX-NEEDED; own NEEDED; duplicate-of `Runtime.handle`, `evals.gate`.
- Guarantee: loop.py:1-6 (the difference is stated). Test: none found for "kill_switch" in tests/test_k1b_*.py.

**B-08 | Major | DUPLICATE.**
- Evidence: the same five lines (`make("signer"...)`, anchor, store, audit) at `app.py:144-161`, `cli.py:184-190` and `k1b/audit_sink.py:67-71`.
- Wrong: three copies. app.py has the purge store and the missing-method check; the other two do not.
- Fix: one `build_audit_stack(cfg, secrets)` in `backends/factory.py`.
- Verdict FIX-NEEDED; own NEEDED; duplicate-of app.py.
- Test: tests/test_p2_postgres.py:199 covers only the cli copy.

**B-09 | Major | DEAD.**
- Evidence: `store/protocol.py:73 add_dead_letter`; table `dead_letters` in 0001_core.sql:77-85; `migrate.py:52` grant; `extract.py:64 return DeadLetter(...)` returned and never stored. grep: no caller of `add_dead_letter` outside store/. `save_approval_decision` is used only by tests (tests/contracts/test_store.py:131); `record_decision` is the real path.
- Wrong: a table, two store methods, a model and a grant for dead letters that nothing writes or reads. `extract.py` has zero src importers (evidence 2c).
- Fix: wire extract failures to `add_dead_letter`, or archive these (owner yes first).
- Verdict NOT-NEEDED (cut-list candidate).
- Test: store-level only (tests/test_p7_store.py).

**B-10 | Major | OPS.**
- Evidence: `store/postgres.py:193 # ponytail: one connection behind one lock per process` and `:194 # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.`
- Wrong: after a database restart or failover every call in that process fails until restart. A written deferral of a fixable problem. Tick is one-shot and unaffected; a long-running host is not.
- Fix: reconnect once on `OperationalError`/`InterfaceError`, or use `psycopg_pool`; add a connection-kill test.
- Verdict FIX-NEEDED; own NEEDED.
- Test: none found for "reconnect".

**B-11 | Major | INCONSISTENT (rule R449).**
- Evidence: `backends/table.py:589 kinds allowed only in `dev``; `:593 DEV_ONLY`; `config.py:317 environment: Literal["dev","pilot","prod"]` (lane C); `registry.py:44 None only in dev`; `agent_loop.py:553 slice-1 gate path (dev)`.
- Wrong: preamble rule 21 says stages are DEMO, PILOT, PROD, and core config must refuse "dev" with a message naming the rename. The code accepts "dev". This is a rename, not a behaviour bug (frozen "dev" text reads as "demo", P0t).
- Fix: rename to `demo`, refuse `dev`, rename `DEV_ONLY` to `DEMO_ONLY`, update tests.
- Verdict FIX-NEEDED.
- Cross-lane: config.py:317 is lane C.

**B-12 | Nit | INCONSISTENT.**
- Evidence: `migrations/0001_core.sql:3 the runtime role gets SELECT, INSERT, UPDATE` vs `migrate.py:49,51,52` (append-only grants).
- Fix: correct the comment (the ledger is by version, check first).

**B-13 | Nit | INCONSISTENT (stale or garbled text).**
- Evidence: `store/protocol.py:1 ...postgres when Portal v0 or S11 needs it`; `memory.py:1 Postgres comes with its trigger` (it exists); `k1b/redaction.py:173-177` says `tools.redact_layered`, but the code at `:188` calls `runmap.redact_untrusted` (same behaviour: tools.py:976-984).
- Wrong: the `LIMITS` sentence "does not mask the values of the values the patterns do not know" (redaction.py:41-46) is printed in the client report (report.py:70,84). That breaks the wording rule.
- Fix: correct the three texts.

**B-14 | Nit | OPS.**
- Evidence: `store/postgres.py:100 tempfile.mkstemp(prefix="hadavin-ca-", suffix=".pem")`; no `unlink` anywhere in store/ or backends/.
- Wrong: one leftover temp file per `build()`. It is public data, but a second copy of the CA sits outside the secrets kind.

**B-15 | Nit | UNVERIFIED-CLAIM.**
- Evidence: `k1b/atomic.py:1 A crash leaves a *.tmp, never a torn file`; `:12 tmp = path.with_name(path.name + ".tmp")`; `:13 errors="backslashreplace"`.
- Wrong: no directory fsync after `os.replace`. A fixed temp name is shared by two writers. `backslashreplace` silently rewrites characters. No crash test; tests/test_k1b_cli.py:207 only monkeypatches the function.
- Fix: fsync the folder, use `mkstemp`, drop `errors=`.

**B-16 | Nit | INCONSISTENT.**
- Evidence: `runtime/tick.py:109 return steps * getattr(llm,"call_timeout_s",60) * getattr(llm,"max_attempts",1) + 60`; `:116 S.EXECUTING: "outcome_unknown"`.
- Wrong: the "quiet too long" time for EXECUTING comes from the model's timeouts, not the executor's. A slow action with no heartbeat (older three-argument hooks, agent_loop.py:836) is marked outcome_unknown while it still runs. When it ends, `_to(VERIFYING)` raises `IllegalTransition`. Fail-safe, but the reason is wrong.

**B-17 | Nit | SECURITY.**
- Evidence: `k1b/bundle.py:214 hashlib.sha256((path / rel).read_bytes())...` is the hash check; the content is read again at `:112,137,259`.
- Wrong: a file swapped between the two reads passes. It needs write access to the bundle folder. There is no size or count limit (`rglob` `:199`).
- Fix: read once, hash and parse the same bytes; add a size cap.

**B-18 | Nit | STORE.**
- Evidence: `agent_loop.py:102 path = registry.config.root / "qualified.jsonl"`; `replay_records.py:24 FILE = "replay-records.jsonl"`.
- Wrong: gate and replay records are file stores outside the Store protocol. No written exception (reason, owner, removal trigger) was found by grep. A torn append is handled by the reader (agent_loop.py:107-115).

**B-19 | Nit | DUPLICATE candidate, UNVERIFIED.**
- Evidence: `k1b/redaction.py:88 SENSITIVE_KEY = re.compile(` and `:60 SCHEMA_WORDS`.
- Wrong: a second "this key names a credential" vocabulary beside `guard/redact.py`. Overlap not measured. Compare in cross table T4.

**B-20 | Nit | INCONSISTENT.**
- Evidence: `registry.py:351-354 if not c.steps ... if not s.approver_ids or s.timeout_s <= 0`.
- Wrong: chain approver ids are not checked against `principals.yaml`. A typo loads fine and nobody can approve; it fails safe.

**B-21 | Nit | UNVERIFIED-CLAIM.**
- Evidence: `runtime/evidence.py:186 if agent.tools_allowed and any(k not in declared ...)`; `agent_loop.py:452 call = reply.tool_calls[0]`.
- Wrong: undeclared inputs are rejected here only for tooled agents; the authorizer may catch the rest (lane A, not read). Only the first tool call of a reply is used, and the others are dropped silently.

**B-22 | Major | OPS.**
- Evidence: `runtime/tick.py:10-11 ... is PENDING (K7): nothing sends it today.`
- Wrong: tick is the only job that expires approvals, runs approved plans, moves stuck runs and purges personal data. If the scheduler stops, nothing in the repo notices. The scheduler is outside the repo (UNVERIFIED).
- Fix: send the external heartbeat ping (config name, no hard-coded host) or ship a dead-man check.
- Test: tests/test_p7_tick.py:368 covers exit codes only.

## Written exclusions (every hit of evidence sections 2, 3, 8, 11, 12 in lane B)
- **X-1** `backends/builtin.py` (2a, 3a, eight functions with zero references). Loaded by string `"hadavin_sdk.backends.builtin"` + `:fake_secrets` and so on in `backends/table.py:379,385-590`, and by `importlib` at `factory.py:44`. The runner's string-exclusion list does not name `table.py`. NEEDED.
- **X-2** `sources/__init__.py` interface classes and `sources/kinds.py register` (3b, tests only). Extension points under no-single-dependency. The only built kind, kubernetes, has a written outline and trigger "K5-ITO" (kinds.py:5-8). NEEDED.
- **X-3** `k1b/tools.py` vs `src/hadavin_sdk/tools.py` (candidate overlap). Different jobs, no shared bodies, different caps. Dismissed as a duplicate.
- **X-4** Sections 11 and 12 have no lane B hit. In section 8, `psycopg` and `boto3` are declared and imported only in `store/postgres.py:23` and `store/auth_aws.py:12`. `kubernetes` is not imported; it uses REST.
- **X-5** The skeleton's `environ@48` in `deferred.py` is `cfg.environment`, not an env read. The real env read is `postgres.py:56 PGHOST` (host name only).
- **X-6** Alternative kinds (store postgres/memory, audit local_dir/chain) have wiring in `backends/table.py:490-512`. NEEDED.

## Candidates the lead should know (cut list, owner yes, archive not delete)
- `dead_letters` table, `add_dead_letter`, `list_dead_letters`, `save_approval_decision` (B-09).
- Candidate duplicates for the cross pass:
- three backend-wiring copies (B-08);
- three agent loops: `Runtime.handle`, `k1b/loop.run_case`, `evals.gate` (B-07);
- the redaction vocabulary in `k1b/redaction.py` (B-19).
- k1b tools vs `tools.py`: no overlap found (X-3).
- Cross-repo question for the lead (UNVERIFIED): do the receiver and the n8n flow dedupe events before `Runtime.handle` (B-04)? Does the host run `tick` in the same process as the runtime (B-01)? Where does the tick scheduler's liveness get checked (B-22)?
- Smaller leads: CHANGELOG.md:11 mentions renaming a ledger row to `0006_evidence`, but only migrations 0001-0005 exist as files (UNVERIFIED which name is right). No retention purge was found for `approval_requests`, `approval_decisions`, `runs`; personal ids such as `requested_by` and `approver_id` stay (UNVERIFIED by running).

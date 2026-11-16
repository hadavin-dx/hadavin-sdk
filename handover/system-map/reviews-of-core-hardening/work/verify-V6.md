# verify-V6: independent second look at the five Blockers (A-01, A-02, B-01, C-01, D2-01)

Checkpoint (25 min): A-01, A-02, C-01 traced; B-01 and D2-01 traced next. Final state below.

## What I did NOT check
- I ran no product program and no test. Everything below is reading. A stdlib-only `python3 -I` one-liner on `decimal` (no product code) was the only interpreter use.
- I did not check Postgres-side behaviour (grants, outbox row access by the runtime role), nor whether `audit_outbox` has the INSERT/DELETE grants a tick step would need (`store/migrate.py:59` says `"audit_outbox": Grant("table", "SELECT, INSERT, DELETE")`; I did not check which role the tick runs as).
- I did not check the snapshot against the real git head; I read `/tmp/.../scratchpad/snap/` as given.
- I did not read other findings (X-02, X-03, X-16) except where they were cited next to these five.
- I did not check any production host outside this repo (a client service might run `run_tick` in-process; nothing in this repo does).
- I did not read any `verify-V*.md` file.

Snapshot root used below: `snap/` = `/tmp/claude-0/-home-user/d72bd15c-b484-516a-89e0-703eea3c1a47/scratchpad/snap/`.

---

## A-01 (audit events parked in the outbox are never written back)

1. Claim: when the audit write fails, `write_outcome` parks the event (outbox table, folder or memory), and nothing in production ever calls `reconcile()`, so the event never reaches the audit trail.

2. Quotes (verbatim):
- `src/hadavin_sdk/audit/chain.py:215-216`: `def write_outcome(self, event: AuditEvent) -> str | None:` / `"""Never raises: the chain, then the outbox table, then memory (all drained by reconcile)."""`
- `chain.py:221-229`: `except Exception:  # noqa: BLE001 - the contract is "never raises"` ... `"INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) "` ... `self._pending.append(event)` ... `return None`
- `audit/local_dir.py:110-124`: same shape (`self.outbox.mkdir(...)`, `os.replace(tmp, self.outbox / f"{event.event_id}.json")`, `self._pending.append(event)`, `return None`).
- `audit/protocol.py:27-28`: `def reconcile(self) -> int:` / `"""Drain the outbox. Returns how many events were written."""`
- `runtime/tick.py:249-253`: `TickStep("sweep", 0, sweep),` `TickStep("reconcile", 0, reconcile),` `TickStep("stuck", 0, stuck),` `TickStep("checkpoint", 0, checkpoint),` `TickStep("purge_evidence", ...` (6th is `reprobe_sources`). The `reconcile` there (tick.py:85) is `store.list_approvals({"APPROVED", ...})`, the approvals one, not audit.

3. Trace: I searched `reconcile|_drain|audit_outbox|_pending|flush|drain` over `src`, `demos`, `docs`, `tests`. The only `.reconcile()` calls on an audit object are `tests/test_cuj.py:202` (`assert app.audit.reconcile() == 1`) and `tests/warden_port/test_audit_chain.py:514`. `checkpoint` (tick.py:177-181) only does `getattr(ctx.app.audit, "checkpoint", None)`. `_append` in chain.py does not drain the outbox. `k1b/audit_sink.py:38` also says "keeps it for reconcile" and nobody calls it. No second path or guard exists. No log line in either fallback block (I read both; there is none). Callers that park results: `agent_loop.py:229-230` `_note` -> `self.audit.write_outcome(...)`, also `limits.py:46`, `approvals/requests.py:82`, `tick.py:133,162`. The test `test_cuj5_outcome_write_fails_then_reconcile` (test_cuj.py:188-205) proves the event is parked (outbox file) and that a manual `reconcile()` recovers it, so the parking itself works; only the caller is missing.
Extra detail the target missed: a tick step would drain only the DB table (chain) or outbox folder (local_dir), which are shared across processes. `_pending` (memory) is per-process, so a memory-parked event of the agent process is not visible to a separate tick process; the audit_reconcile step cannot recover those. The target's fix text implies it does.

4. Verdict: CONFIRMED.

5. Severity: AGREES (Blocker). A stated guarantee (chain.py:216, protocol.py:27) has no production code, and the lost events include the result of an executed action and approval decisions, silently, with no log. Condition: only on an audit write failure.

6. Fix: no patch file covers A-01 (the patch is C-01 and A-02 only). The proposed fix (new tick step calling `app.audit.reconcile()`) fits `STEPS`. Breakage risk: `tests/test_p7_tick.py:79-92` pins the exact list of step names (`["sweep","reconcile","stuck","checkpoint","purge_evidence","reprobe_sources"]`); adding a step needs that test updated. Also the step needs write rights on `audit_outbox` DELETE (grant exists in `migrate.py:59`, role not checked) and the memory-parked case needs a different answer (log at fallback; or write the event to the DB outbox only).

---

## A-02 (G5, the "independent last leak check", is not built)

1. Claim: `approvals/gate.py` and `guard/redact.py` describe an outbound leak check "G5" that blocks text; no code or test implements it.

2. Quotes:
- `approvals/gate.py:5-7`: `Not ported (WARDEN outbound policy): enforce, hedge,` / `leaked_kinds/data_leaks/assembled_kinds/where_withheld, for_terminal,` / `outbound_data, sanitise_data, GateResult. The original module notes follow.`
- `gate.py:42-44`: `- **G5, leaks.** If the final text still contains anything the redactor classes as secret (every` / `kind except the identifiers an operator may choose to show), the message is BLOCKED and a stub` / `goes out instead: a person reads the full report locally.`
- `gate.py:63`: `Verdicts: PASS (unchanged), REWRITE (G3 removed something), BLOCK (G5).`
- `guard/redact.py:15-17`: `the control; HIGHENTROPY is their backstop; the outbound gate's G5 re-runs them, independently, on` / `everything that leaves.`
- `tests/warden_port/test_gate.py:1`: `... Kept 4 tests; dropped 13 that need WARDEN-only modules or unported gate policy (listed in the PR).`

3. Trace: `grep "G5|G2|leaked_kinds|data_leaks|enforce("` over src, demos, README, docs, SECURITY, CLAUDE finds only the comments above. The real outbound path is `approvals/channel.py:19-43 clean()` (sanitise, withhold commands, one `redact_text`) and `slack_channel.py` (`runmap.redact_text` again at the card). Same redactor, so not independent. `guard/bedrock_guardrail.py` is an input prompt-attack filter, not an output leak check. No README, SECURITY.md or docs line states G5 as a guarantee; I searched for "independent|last check|second check|outbound" in README, SECURITY, docs, CHANGELOG and found nothing.
Mitigation the target understated: gate.py:1-7 says outright "Not ported ... leaked_kinds ... The original module notes follow", so lines 42-44 and 63 sit inside a block labelled as the upstream's old notes. The self-contradiction is therefore partly flagged in the file. The one unflagged statement is `redact.py:15-17`, written in present tense about this repo.

4. Verdict: CONFIRMED as to facts (no G5 code, no test, `redact.py:15-17` is false for this repo). The "gate.py contradicts itself" part is only half right (gate.py labels the text as the original's notes).

5. Severity: TOO HIGH. I think Major (misleading comment), not Blocker. The guarantee exists only in code comments, not in README, SECURITY or customer text; the primary control (patterns plus sweep, README "Redaction is pattern-based and bounded") is built and honestly described. A second pass by the same regexes would add little. If the lead holds that any false security sentence in the redaction path is a Blocker, the target is right under the brief's definition ("a stated guarantee with no code"); I note it as a judgement call, with my lean to Major.

6. Patch: the A-02 half of `patches/C-01-and-A-02.patch` edits only `redact.py:16-17` to read `An independent second check at the outbound gate (G5) is NOT built yet (approvals/gate.py says so).` It fits the file (lines match the snapshot). Problems: (a) it leaves `gate.py:42-44` and `:63` untouched, so `redact.py` now points to gate.py "says so" while gate.py lines 42-44 still say G5 blocks (only lines 5-7 say not ported, and they name `leaked_kinds`, not "G5"); (b) "NOT built yet" promises future work; (c) the comment line exceeds the usual line length and may fail `ruff format --check` or E501 (ruff config not read). No behaviour change, so low risk otherwise.

---

## B-01 (a failed re-probe "switches off" a source only inside the tick process)

1. Claim: `reprobe_sources` stores the switched-off sources in a Python set on the tick process's own `App`; the tick is a separate short-lived process, so the agent-running process never sees it, and README:35's "switches off every tool that names the source ... until a probe passes" is not delivered.

2. Quotes:
- `runtime/tick.py:233-238`: `if problems:  # fail CLOSED: tools stop reading this source until a probe passes again` / `app.disabled_sources.add(key)` ... `else:` / `app.disabled_sources.discard(key)`
- `app.py:58`: `disabled_sources: set[str] = field(default_factory=set)`; `app.py:104-106`: `disabled_sources: set[str] = (` `set()` `)  # sources switched off by a failed re-probe (tick `reprobe_sources`)`
- `app.py:399-401`: `def _switched_off(disabled: set[str] | None, source_hosts: dict[str, str]):` ... `The set is the app's own and the tick edits it.`
- `cli.py:280-309`: `_tick()` builds `app = build(None, agents)` then `return run_tick(app)`; exits.
- `README.md:35` (Re-probe bullet): `a failed re-probe switches off every tool that names the source (options.source) or lists its host, and the source's own reads, until a probe passes.`
- `tick.py:1`: `one idempotent pass of housekeeping steps, run every 30-60 s by any scheduler.`

3. Trace: the set is written only at tick.py:235/238 and read only through `_switched_off` (app.py:469 -> tools `disabled=`). `run_tick` is called only from `cli.py` (grep over src, demos, docs, README); no host in this repo runs it inside the runtime process. There is no `serve` command; the SDK's agent runtime is a library, so the "agent-running process" is the client's host. The only test (`tests/test_k5_round9b.py:295-314`) asserts `app.disabled_sources == {"c"}` on one object; `test_k5_round10.py` tests refusal given a set; nothing tests two apps on one store.
Two corrections to the target I found:
 (a) The target says the failure reaches a person via tick "exit code 1 and `tick_state.last_error`". But `app.build()` itself probes scope at start (`app.py:125-128`: `if problems := sources_mod.scope_problems(...): raise ConfigError("; ".join(problems))`), and `cli._tick` maps `ConfigError` to exit 2. So when a probe fails persistently, the next tick (and any new agent process) refuses to start with exit 2 before `reprobe_sources` even runs; `reprobe_sources` in the CLI path is nearly unreachable as a failing step. This is a mitigation the target missed: new processes fail closed at start.
 (b) A consequence the target missed: a failing probe therefore also stops sweep, reconcile (approvals) and stuck-run handling in the tick (exit 2), which is a loud but broad effect.
What remains true: a long-running agent process that started with a passing probe is never told when RBAC widens later, so "switched off ... until a probe passes" has no effect on it. That is the guarantee README:35 states.

4. Verdict: CONFIRMED in substance (set is process-local; README:35 overstated for the separate-tick deployment). The detail "exit code 1" is WRONG in the likely case (exit 2 at build). The target's own caveat (UNVERIFIED how the host runs tick) stays open.

5. Severity: TOO HIGH. I think Major. Tools are bound to their own `READ_OPERATIONS` (README:29: "a tool module declares its own READ_OPERATIONS"), so a widened credential does not by itself let a tool write; the re-probe is defence in depth with an hour of delay stated in the same bullet; and every fresh process refuses to start on a failing probe. Reviewers also propose Major. A Blocker call would rest on "a stated guarantee with only partial code".

6. Fix: no patch provided. Proposed fix (store the set in the Store, read in `_switched_off`) would need: a new Store method on `store/protocol.py`, `memory.py`, `postgres.py`; a migration and grant (`migrate.py` role map; runtime role vs a tick writer); a DB read on every tool call (cost, and what to do when the store is down; it must fail closed); and a two-app test. Larger than 20 lines; not a drop-in. Risk: `_switched_off` is a synchronous closure called per tool invocation; a store error there must refuse, not allow.

---

## C-01 (a model price of zero, below zero or NaN switches every spend limit off)

1. Claim: `Route.input_usd_per_mtok` / `output_usd_per_mtok` accept 0, negative and NaN; every reply then costs 0 or less, so the daily, monthly and run budgets never trip; only the replay command refuses a zero price.

2. Quotes:
- `config.py:47`: `Money = Annotated[Decimal, BeforeValidator(_money)]`; `_money` (lines 38-43) only raises `if isinstance(v, float):`.
- `config.py:57-59`: `input_usd_per_mtok: Money` / `output_usd_per_mtok: Money` / `max_tokens: int = Field(gt=0)`
- `llm/common.py:166-169`: `cost = (` `Decimal(tokens_in) * route.input_usd_per_mtok` `+ Decimal(tokens_out) * route.output_usd_per_mtok` `) / Decimal(1_000_000)`
- `limits.py:17-18`: `def charge(...)`: `return self.store.add_spend(agent_id, now().date(), usd)`; `limits.py:26-28`: `if day >= budget.daily:` / `reasons.append("daily_budget")` / `if month >= budget.monthly:` ...
- `k1b/replay.py:87-90`: `zero = route.input_usd_per_mtok == 0 or route.output_usd_per_mtok == 0` / `if zero and llm_kind != "fake":` ... `raise ConfigError("replay refuses a route with a zero input or output price")`
- Note: the finding's cited `limits.py:206-209` does not exist (file has 51 lines); the real lines are 20-29 (X-13 already says so). Facts hold.

3. Trace: `add_spend` (memory.py:196-198 `self._spend[(agent_id, day)] += usd`; postgres.py:416-431 `usd = spend.usd + EXCLUDED.usd`) does no sign check, so a negative cost lowers the total. Charge sites: `agent_loop.py:440` and `:314`. A grep for `usd_per_mtok` across src/tests/demos shows the replay as the only non-model-math check. No other guard (no `gt=0` on Money, no cross-check in `Config._cross_checks` lines 350-374). Zero price is also a legitimate thing for a self-hosted model (`openai_compat` with Ollama, `tests/warden_port/test_providers.py:62-64,196`), where the cap is then meaningless by design.
Test evidence: `tests/test_k1b_replay.py:382` builds a zero-price route with `model_copy(update=...)`, which skips validation, so the new config check would not affect it.

4. Verdict: CONFIRMED.

5. Severity: AGREES (Blocker), with a caveat: it needs an operator to write a wrong price (a config mistake, not an attacker), but the effect is a silent loss of all spend limits, a money rule. The reviewers also propose Blocker.

6. Patch (`patches/C-01-and-A-02.patch`, C-01 half): adds in `Config._cross_checks`, after the `systems` loop:
`if self.backends.llm.kind != "fake":` ... `if min(r.input_usd_per_mtok, r.output_usd_per_mtok) <= 0` ... `raise ValueError(f"routes with a zero or negative price: {free}")`.
Fits the snapshot: the surrounding lines (359-365 and `refused = []`) match; `self.backends.llm.kind` and `self.routes` exist (used the same way at lines 356-358). Problems found:
 - NaN: I checked `min(Decimal('NaN'), Decimal(1)) <= 0` with stdlib: it raises `decimal.InvalidOperation` (an ArithmeticError, not a ValueError), so pydantic will not turn it into a validation error; the load crashes with a raw exception instead of a clean ConfigError (still fails closed, but the target's claim "patch covers NaN" is only half true). The finite check on `Money` that the finding itself proposes is not in the patch.
 - Infinity passes (`min(Decimal('Infinity'), 1) <= 0` is False): `Decimal(0) * Infinity` is NaN at runtime. Not guarded.
 - `openai_compat` with a local model and a real 0 price (Ollama) is now refused in every environment; that is a behaviour change the decision log marks as "not yet approved".
 - `max_tokens` still has no upper bound (not in patch; the finding says X-02 needs it).
 - No test is included in the patch (the target's own rule needs a test that fails on old code).
 - The replay's own check (`replay.py:87-90`) is left in place; harmless.

---

## D2-01 (demo `ask` skips kill switch, meter, audit and ledger)

1. Claim: `python -m askdata ask` validates the SQL and calls `source.run` directly; it never goes through `Pipeline`, so kill switch, meter, audit intent/outcome and ledger do not apply, although the README and policy present them as controls.

2. Quotes:
- `demos/ask-your-data/askdata/cli.py:87-108` (`cmd_ask`): `ok = validate(sql)` ... `result: RunResult = source.run(ok.canonical_sql, sql_sha256=ok.sha256)`
- `cli.py:262-284` (`main`): `if code := gate(source): return code` / `return cmd_ask(source, sql, who=ScriptedModel.name, question=args.question)` where `sql = ScriptedModel().complete(args.question)`. `gate` (cli.py:70-84) only runs `source.verify_readonly()`.
- `askdata/pipeline.py:106-107` `if self.kill.is_on(): return "kill_switch"`; `:141-143` the same in the loop. `Pipeline(` is built in `evalcli.py:87` and tests only.
- `README.md:51`: "`ask` first runs the read-only checks and refuses to start (exit 4) when one is red. Exit codes (spike, provisional)". `README.md:1`: "# Ask your data (spike)" and "calls **no model over the network**: the model is a scripted stand-in".
- `README.md:69-70`: `**Pipeline** (askdata/pipeline.py): gates, generate, validate, audit intent, execute, ledger.`

3. Trace: facts of the bypass are right (`cmd_ask` -> `source.run`; no kill-switch read, no meter, no audit, no ledger in that path). But the "README presents them as controls" part is not found: README:69-75 describes the Pipeline and the operator commands, not `ask`; README:1-3 and :51 label `ask` a spike with a scripted model; nothing says `ask` honours `killswitch on`. The inconsistency the target found is real in effect, though: `python -m askdata killswitch on` (opscli.py:170-173, prints "the tool is switched off") does not stop `ask`. Impact is limited: no paid call (scripted model), a read-only database login (`verify_readonly` gate runs first, `roles.sql`), validator before the database, row/byte caps, watchdog.

4. Verdict: CONFIRMED for the code facts; the label UNVERIFIED-CLAIM is WRONG for the README (no README claim that `ask` has these controls was found); at most the word "tool is switched off" in `killswitch status` output is a misleading claim.

5. Severity: TOO HIGH. Minor to Major (reviewers say Major at most). It is a demo, labelled a spike, no money path, read-only login. It is not a lost-data, leak or money case.

6. Fix: no patch. Either option the target gives (route `ask` through `Pipeline`, or say in the README that the controls are eval-path only) fits; the README sentence is the cheap one. Routing through `Pipeline` would change the exit codes pinned in `tests/demo_askdata/test_cli.py` (lines 33-104 call `cmd_ask` and `main` with those codes) and `README.md:51-54`.

---

## Summary table

| Finding | Verdict | Target severity | My severity check |
|---|---|---|---|
| A-01 | CONFIRMED | Blocker | AGREES |
| A-02 | CONFIRMED (facts); "self-contradiction" only half right | Blocker | TOO HIGH (Major; judgement call) |
| B-01 | CONFIRMED in substance; "exit code 1" wrong (build probe exits 2 first) | Blocker | TOO HIGH (Major) |
| C-01 | CONFIRMED | Blocker | AGREES (patch misses NaN/Infinity and has no test) |
| D2-01 | CONFIRMED (code); README claim not found | Blocker | TOO HIGH (Minor to Major) |

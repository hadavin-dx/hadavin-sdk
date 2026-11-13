# Draft of the pull-request text for Q8a-1 (branch core/q8a-1-live-override-refusals)

Title: Refuse test-only build() and tick keywords and the static Vault token in pilot and prod (Q8a-1)

## What this change does, in plain words
The core has three stages: demo, pilot and prod. Tests may hand the core ready-made stand-in objects (a made-up secret store, a made-up message channel, a scripted model, a fixed clock). That is right in demo. In pilot and prod it must never happen by accident, because the process would then run on stand-ins while everyone believes it runs on the configured, real parts.

After this change, outside demo (pilot, prod, and any stage value that is not exactly `demo`):
1. `app.build` refuses the six keyword arguments that exist for tests: `secrets=`, `channel=`, `detector=`, `llm=`, `clock=`, `timeout_s=`. `sources=` and `tools=` were already refused; they now count as given when they are not None (an empty mapping is refused too).
2. `runtime.tick.run_tick` refuses `now=` (a time of the caller's choice) and `steps=` (a step list of the caller's choice), and refuses to run when a built-in housekeeping step is missing from the list `runtime.tick.STEPS`. Without this a tick could report success while the clean-up of stored evidence or the handling of waiting approvals never ran. The same refusal sits where the time enters the housekeeping steps: the tick context (`TickContext`) refuses a time handed to it, so one step called by hand cannot work with a time of the caller's choice either (before this, `purge_evidence(TickContext(app, today + 500 days))` deleted every stored tool call and redaction map of a pilot app).
3. Every process that calls `app.build` refuses a Vault sign-in with a static token (`auth: token`, which is the default). A static token would sit in the environment of that process. The config file itself still loads, so the one-off commands (among them the kill switch, `limits stop`) keep working for a person with a short-lived token of their own.

The demo executor's timeout has one rule on both routes (the `timeout_s=` keyword of `build` and the config field `executor_timeout_s`): an int or float, not True or False, from 0.001 to 3600 seconds. In demo an object that is falsy is used as given and no longer silently replaced.

Every refusal is a `ConfigError` with a sentence that names the keyword and what to do instead. Upgrade steps are in CHANGELOG.md, section Unreleased.

## Rung table (from the ticket; "rung 1" means reuse of what the core already has)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| refusal of test objects outside demo | a pilot or prod process must not be built with a made-up secret store, channel, model, detector or clock by accident | rung 1 reuse: the two existing refusals in `app.build` for `sources=` and `tools=` (read 2026-11-11) | same function, same error type | a start-up refusal inside our own `build()` and `run_tick()` | KEEP-CODE (one check each; two build() calls in positive tests change their seam; new tests) |
| static Vault token refused outside demo | no static Vault token in the environment of a process that calls `app.build` | rung 1 reuse: the live refusals at the top of `app.build` (moved there from the config loader after review, decision D-012) | same function, same message shape | start-up refusal | KEEP-CODE (one helper + tests) |

No new dependency. No vendor SDK import outside its kind module (`app.py` imports only the settings class `backends.table.VaultConnection`).

## Honest limits
- The refusals stop a test object that reaches a pilot or prod process BY ACCIDENT. They do not stop hostile code inside the same process.
- Covered: the six keywords of `build`; `sources=` and `tools=`; `now=` and `steps=` of `run_tick`; a `runtime.tick.STEPS` that lacks a built-in step; a `runtime.tick.STEPS` with a name used twice; a time handed to a `TickContext`; and, outside demo, any object that is not exactly a `TickContext` handed to a step (a plain stand-in, a `Mock(spec=TickContext)`; the class cannot be subclassed).
- NOT covered (each is named in the build docstring and the CHANGELOG): constructing `App`, `Runtime` or `Approvals` directly (a hand-built `Approvals(clock=...)` among them); assigning attributes after build; a kind added to the table; a direct call of `backends.factory.make`; a leftover patch of `app.make` or `app.now`; a changed or patched `runtime.tick.STEPS` that still holds every built-in step name once (reordering; replacing a step's function under the same name, for example a `purge_evidence` that does nothing; a huge `every_s` or `interval` on a built-in name; a rebound `_BUILT_IN`); a real `TickContext` altered with `object.__setattr__`, built without its constructor, or given a wrapper app that reports `demo` (frozen stops ordinary assignment only); a clock that tells the wrong time (`app.approvals.clock` replaced after build); the store's own methods that delete by a cut-off date handed to them (`purge_tool_calls(before)`, `purge_redaction_maps(before)`: the store knows no stage; independent evidence: on a pilot or prod app, called directly with a time 500 days ahead, they deleted all 3 planted rows with no refusal; open question Q-2026-11-11-Q8a1-direct-store-purge); the time parameters of `Approvals.sweep(at=)` and `Approvals.resend_unsent(at=)` (`at=` is the tick's own parameter). A tick step called by hand with `TickContext(app)` (the app's clock) is not refused; it is not a supported entry point, and there is no supported way today to run only some steps outside demo.
- Static Vault token: only processes that call `app.build` are covered; of the commands that is `hadavin-sdk tick`. The commands `limits stop`, `limits reset`, `audit verify`, `gate`, `migrate`, `replay` and `score` load the config without `build`, so a static token is not refused there. Nothing checks how long a person's token lives, and a scheduled job that runs one of these commands with a static token in its environment is not refused either.
- `auth: approle` is allowed. Its secret id is also read from the environment; how long it lives is set on the Vault side and this code cannot check that.
- The Vault check finds a kind by its settings TYPE (`VaultConnection`). A guard test fails if a kind in the table brings its own sign-in field (`auth`, `token_env`, `secret_id_env`, `role_id`, `jwt_path`) without that type. Checked 2026-11-11: only the two Vault kinds have any of these fields.

## Deviations from the first ticket text (recorded in the ticket's errata rev 3 to rev 7)
1. `backends/factory.py`: `provider or FakeSecretProvider({})` became an `is None` test (a falsy secret provider is no longer swapped for an empty one; in every stage).
2. `app.build(clock=...)`: the default is `None`, not the real clock function; with no `clock=` the real clock is still used; `clock=models.now` handed in by a caller is refused outside demo like any given clock.
3. The static-token refusal sits in `app.build`, not in the config loader (decision D-012: in the loader it also stopped the kill switch for a person with a short-lived token).
4. `_VaultConnection` in `backends/table.py` is now the public name `VaultConnection`.
5. `sources={}` and `tools={}` (empty mappings) are refused outside demo. Both keywords take a mapping; a list of pairs works in demo only because the value is copied with `dict()`, which is not a contract.
6. `run_tick` refuses `now=`, `steps=` and a step list without a built-in step; these three RAISE `ConfigError` (the function otherwise returns an exit code).
7. `timeout_s=` in demo and the config field `executor_timeout_s`: one rule (`config.executor_timeout_ok`), an int or float, not True or False, from 0.001 to 3600 (`defaults.EXECUTOR_TIMEOUT_MIN_S`, `defaults.EXECUTOR_TIMEOUT_MAX_S`). The message is "... must be an int or float between 0.001 and 3600"; this replaces the wording of errata R5 ("between 0 (not included) and 3600"). Why one millisecond: no network call finishes in less, so a smaller value acts like 0. The config field no longer reads `true` as 1.0 or `'5'` as 5.0.
9. `runtime.tick.TickContext` is frozen, its time is optional (`TickContext(app)` takes the app's clock), and outside demo a context that is given a time is refused. Two existing tests changed for this: `tests/test_k5_round8_postgres.py` builds `TickContext(app)` for its pilot app, and the stand-in app of `tests/test_k5_round9b.py::test_a_failed_reprobe_switches_the_source_off_until_a_probe_passes` now says `environment="demo"`.
8. `Approvals.sweep` and `Approvals.resend_unsent`: `at = at or self.clock()` became an `is None` test (no change for a real time value).

## Questions for the owner (none blocks this pull request; each needs a decision and a date)
1. approle lifetime. `auth: approle` stays allowed in pilot and prod; its secret id sits in the environment like the static token and lives as long as the Vault role says. Keep it allowed with the written advice "set a short secret id lifetime on the Vault side", or refuse it too and allow only `auth: kubernetes`?
2. Sign-in of a person (or a scheduled job) for the one-off commands. These commands still work with `auth: token`. Is a person's own short-lived token the wanted route for the kill switch, or should the commands get a sign-in that reads no token from the environment (a new feature)? One middle option: refuse the static token also for `gate`, `replay` and `score` (they call the model and are not emergency tools) and leave `limits`, `audit verify` and `migrate` open.
3. Signer in pilot. A pilot config may keep the audit signing key as a file on disk, and may run with no signer and no anchor; only prod refuses these. Should pilot refuse the key file too? Two sibling cases from the same review, for the ledger: the Azure default credential with a client secret in the environment, and the AWS default credential chain with access keys in the environment.
4. Second factor for the approver. Today the person who approves is "the verified Slack user"; there is no second check such as a passkey, and that step-up is planned for a later phase. Is that acceptable for a first pilot, or must the passkey check come first? (Recorded in handover/questions-for-lead.md; not part of this change.)

Also recorded for ticket Q8a-2 and the ledger, not built here: the time parameters of the approvals object (`sweep(at=<future>)` escalates or expires early and fails closed; `resend_unsent(at=<future>)` sends a duplicate card; a hand-built `Approvals(clock=<fixed past>)` takes a decision after its expiry); a neutral hook such as `KindSettings.live_refusals()` so `app.py` names no product; an upper bound for `tool_timeout_s` (used in pilot and prod, today only "greater than 0").

## Tests and mutants (numbers from the builder's own runs; the independent evidence run is the one that counts)
- tests/test_q8a_live_overrides.py (new): 198 tests, no database needed.
- tests/test_stage_names.py: 103 tests, of which 6 are new killer tests for this change (test object, sources and tools, timeout range, static Vault token, time or step list handed to the tick, step list without a built-in step). They run without conftest fixtures and without a database.
- The two existing positive pilot tests (they need Postgres) now plant their test objects through one seam, `plant_test_backends`, and assert what `build` asks the factory for: the settings, the secret provider, and that the store handed to the audit and to the channel is the runtime store, not the purge store.
- tests/stage_mutants.py: 71 mutants, all killed (34 of them for this change: M12a-c, six "dropped keyword", M12f-r, M13a-j, M9d-f).
- Full suite at the final head: see the builder's report and the evidence folder of the final head.

## Evidence folders (independent evidence runner), under handover/evidence/Q8a-1/
- `464dee1/` (first build): RESULTS.md, fail-before-per-test.md, mutant-rows.txt, probes.py, probes.txt
- `f6fad26/` (fix batch 1): RESULTS.md, fail-before-groups.txt, fail-before-per-test.md, mutant-rows.txt, probes.py, probes.txt
- `fcd77a6/` (fix batch 2): RESULTS.md, fail-before-per-test.md, fail-before-failures.txt, fail-before-groups.txt, probes.py, probes.txt, timeout-three-versions.txt and helper scripts. Its full suite and mutant run were NOT run (stopped because fix batch 3 replaced the head). Its probes found the two facts that fix batch 3 closes (a hand-made time through the tick context; the config field of the executor timeout).
- the folder for the final head of fix batch 3: to be added by the evidence runner
Builder's own raw logs (not independent): /home/user/build/B-Q8a1-evidence/

## Proof note
The fail-before runs of tests/test_q8a_live_overrides.py against the first head (464dee14) needed one added line in the old `backends/table.py` (`VaultConnection = _VaultConnection`), because the test file imports the new public name. The killer tests in tests/test_stage_names.py need no alias and were run on untouched origin/main. On untouched origin/main the file tests/test_q8a_live_overrides.py cannot be collected at all (it imports the name `VaultConnection` from `backends/table.py`, which main does not have: `ImportError`), so main proves nothing for its tests; their fail-before proof is against the previous heads of this branch.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac

## Fix batch 4 (round-4 delta review, 1 Major and 6 Minor)
- M1: `type(ctx) is TickContext` replaces `isinstance` in the one helper every step reads the time through; `TickContext.__init_subclass__` raises. Tests: `Mock(spec=...)`, an object with a `__class__` property, a subclass (new mutants M13k, M13l).
- m2: duplicate step names refused outside demo (M13m, M13n); the limit texts name the huge-interval and same-name-no-op cases as not covered.
- m3: ticket errata rev 7. m4: config errors no longer show the refused value. m5: CHANGELOG says YAML 1.1 and the Decimal/config difference. m6: limit texts list what frozen and the exact-type check do not cover.
- Direct store purge: no small fix; open question written to handover/questions-for-lead.md.

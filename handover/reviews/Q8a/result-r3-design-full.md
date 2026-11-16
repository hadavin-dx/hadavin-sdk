<!-- full hand-back report of sub-agent a5f0e2c7, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review round 3, Q8a-1, head fcd77a68 (design critic, read-only, fresh reviewer, nothing executed)

## Failures and gaps first

- **No evidence exists for this head.** `/home/user/hadavin-sdk/handover/evidence/Q8a-1/` holds only `464dee1/` and `f6fad26/`. Every "passes" for fcd77a6 is unproven: the full suite, the two Postgres positive tests, the 61 mutants, the fail-before runs of the new and renamed tests, ruff, format, bandit and the guard tests.
- **Two regressions only a run can rule out.** An existing test outside the snapshot that calls `run_tick(app, steps=...)` on an app whose stage is not demo, or `build(..., timeout_s=<over 3600>)` in demo, now fails. I could not grep the repo tests under the read rule.
- **I ran nothing.** Everything below is from reading; the pydantic and socket behaviours in N2 are from knowledge, not a run.
- **Ledger not read.** Every "owner question logged" or "recorded against Q8a-2" claim is unverified.
- **By reading: no Blocker, no Major.** Five Minor findings and one nit.

## Findings

**N1. Minor: the documented extension point (`runtime.tick.STEPS`) is an unnamed live-stage route with the same silent outcome as `steps=`, and it has no test.**
- Where: `/home/user/build/snap/q8a1-fcd77a6/src/hadavin_sdk/runtime/tick.py:255, 371`; limit texts at `tick.py:353-354` and `/home/user/build/snap/q8a1-fcd77a6/src/hadavin_sdk/app.py:104-110`; `/home/user/build/snap/q8a1-fcd77a6/CHANGELOG.md` Unreleased, first bullet (upgrade sentence and "Limit, stated plainly").
- Scenario: a pilot wrapper runs `tick.STEPS[:] = [s for s in tick.STEPS if s.name != "purge_evidence"]`, or `STEPS.clear()`, or a `setattr(tick, "STEPS", [...])` patch is left over; then `run_tick(app)`.
- Wrong outcome: exit code 0 with no sweep or no purge, exactly what the `steps=` refusal exists to stop. Line 371 reads the module list at call time.
- Class: in-process change of module state, the same as "a kind added to the table" and "a leftover patch of `app.make`", which are accepted and named. So I judge it accepted, not a Major. But it is the one such route the CHANGELOG sends deployments to, and none of the three limit texts names it.
- Untested claim: the CHANGELOG sentence "a deployment that needs another step appends a `TickStep` to `runtime.tick.STEPS`" turns a source convention (`tick.py:4-5`, "Later PRs only append") into a runtime extension point. It works by reading; no test appends a step and runs a tick outside demo.
- Embedder gap: there is now no supported way to run a subset of steps outside demo, for example a purge-only job under the purge identity. The only way left is the by-hand call `purge_evidence(TickContext(app, ...))`, which the same docs list as "not covered".
- Fix:
  - Minimum: name "removing or replacing entries of `runtime.tick.STEPS`" in all three limit texts.
  - Add a test that an appended step runs with `run_tick(app)` in pilot.
  - Better, about three lines: keep `_BUILT_IN = tuple(STEPS)` at import; outside demo raise `ConfigError` when a built-in step is missing from `STEPS`; add a mutant.
  - Say in the docstring whether the by-hand step call is supported for a split purge job or merely not refused.

**N2. Minor: one setting, two rules. The keyword is capped at 3600 and int/float only; the config field is `gt=0` only. Errata R5 does not hold the cap.**
- Where: `app.py:157-162, 334-342`; `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/config.py:360-362` (`executor_timeout_s: float = Field(default=..., gt=0)`, untouched by the branch); `/home/user/build/snap/q8a1-fcd77a6/TICKET.md:42` (R5: "a finite number greater than 0, not a bool").
- Scenario (demo): `executor_timeout_s: 100000` or `.inf` in the config loads (pydantic allows infinity by default; not run). `build(timeout_s=100000)` is refused. With `.inf` the executor call would fail at the socket, the outcome the keyword check was added to stop.
- Pilot and prod: not a real problem. `app.py:242` builds no executor when live, so `executor_timeout_s` is never used there. The mismatch is demo only.
- The comment at `app.py:158` ("the config field is > 0 too") is true but reads as if the two agree.
- Ticket drift: `timeout_s=3601` and `Decimal("2.5")` are allowed by R5 and refused by the code. The stricter rule is reasonable (round-2 F6 asked for it), but the errata, which "win", do not say it.
- Fix: put `le=defaults.EXECUTOR_TIMEOUT_MAX_S, allow_inf_nan=False` on the config field with one test, and one errata line (R5: "int or float, at most 3600").
- Sibling outside this ticket, for the ledger: `tool_timeout_s` (`config.py:349`, `gt=0` only) IS used in pilot and prod (`tools.py:495, 1127`). Not introduced here.

**N3. Minor: no evidence for the newest commit.**
- See the first section. Needed before any "done":
  - an EVIDENCE RUNNER pass on fcd77a6: full suite with Postgres, the two positive tests non-skipped, `tests/stage_mutants.py` showing 61 of 61;
  - fail-before for the tests new or renamed in this commit: `test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick`, `test_pilot_and_prod_refuse_sources_and_tools_handed_to_build`, `test_demo_refuses_a_timeout_that_is_out_of_range`, the `steps=` tests and the new timeout cases;
  - a probe that repeats row (f) of the previous `RESULTS.md` (pilot `steps=[]` returned 0 at f6fad26) and now shows the `ConfigError`.

**N4. Minor (low): the seam records the NAMES of the handed-on objects, not which objects.**
- Where: `/home/user/build/snap/q8a1-fcd77a6/tests/test_k3_pilot_env.py:216-217, 243-262`.
- Scenario: a regression hands the audit or the channel `store=purge_store` (the deleting identity) instead of `store`. `available` is still `("anchor", "signer", "store")`, so `assert_asked_as_configured` stays green. The Postgres test checks `app.store` and `app.purge_store`, not the store inside the audit or the channel.
- Fix: keep `available` as a dict in `Call`, and assert that the `store` handed to audit and channel is the object returned by the first store call.

**N5. Minor: residuals are honest in the CHANGELOG, thinner elsewhere; the owner-question trail is unverified.**
- The scheduled-job residual is stated only in the CHANGELOG ("a scheduled job that runs one of these commands with a static token in its environment is accepted as well"). The build docstring (`app.py:100-102`) still speaks only of "a person".
  - Fix: add the scheduled-job sentence there, and write "is not refused" instead of "is accepted"; "accepted" reads as approval.
- The fix-don't-defer rule, exception 2(b), needs the owner told and a dated next step in the handoff. I could not confirm either for the one-off-command sign-in or the approle secret-id lifetime.
- The `Approvals` time parameters are named in the build docstring and the CHANGELOG. They are not named where their caller reads: the docstrings of `Approvals.sweep` and `Approvals.resend_unsent` (`approvals/requests.py:131-134, 191-193` on main) are unchanged. One clause there would do.

**Nit.** `approvals/requests.py:134, 193` still use `at = at or self.clock()`, the truthiness form this branch replaced in `tick.py:358`. Harmless for a real datetime.

## Answers by area

**(2) `steps=` refusal.**
- Placement is correct: first statement of `run_tick` (`tick.py:355-357`), before `TickContext` and the store probe.
- `is not None` is correct: an empty list is refused (tested, mutant M13d).
- The combined check is correct: with nothing given `app.config` is never read; with both given `now=` is named (tested and documented).
- Embedder and bypass question: see N1. Appending works by reading and is untested; mutation is the accepted in-process class but unnamed.

**(3) Timeout rule.**
- Acceptable as a keyword rule.
- No lower bound above 0 is a defensible, documented and tested choice (`1e-9`, `5e-324`).
- Config agreement: no, see N2. Demo-only effect; not a problem in pilot or prod.

**(4) Residuals.**
- One-off commands with a static token: honestly stated in the CHANGELOG and legitimately an owner decision. It would block operators, the kill switch among them, if refused blind. "Recorded" is acceptable if the dated ledger entry exists (unverified, N5).
- `sweep(at=)` and `resend_unsent(at=)`: "recorded" is right, and stronger than the builder's own reason. `at=` is the production parameter: the tick's own sweep step calls `approvals.sweep(ctx.now)` (`tick.py:87-88`). A refusal outside demo would break the tick. This is not a test seam left open.
- Hand-built `Approvals(clock=...)`: needs direct construction, which the limit text names. Acceptable.
- None of them is severe enough to block.

**(5) Wording.**
- Read against the code, the build docstring, the tick docstring and the CHANGELOG match: messages, order of the five checks, "before any backend is built", and the covered and not-covered command lists. `cli.py:299` is the only `build` call; `make` is called directly at `cli.py:150, 184-190, 215-222, 329`.
- Missing: the `STEPS` route (N1) and the scheduled-job sentence in the docstring (N5).
- One unclear sentence, `tick.py:349`: "RAISES a ConfigError before anything runs: the time then comes from the app's clock and the steps are `STEPS`". "Then" means a tick without the keywords; say so.
- Nothing over-claimed.

**(6) Tests.**
- Stand-in in `_build_refusal` (`test_stage_names.py:359-364`): nothing found. It is reached only when the Vault refusal did not fire. The build then stops at the empty secrets (a `ConfigError` that is not the wanted text), so every Vault mutant is still killed. `made == []` catches a moved check.
- `Call` and `assert_asked_as_configured`: sound; one residual (N4).
- Mutants: by reading, each `old` string occurs once in its file and each `expect` fragment matches its killer's message. The count is 61. No important guard is without a mutant.
- Optional additions, not findings:
  - the Vault check or the six-keyword check applied in demo too (killed today only by the q8a file and the wider suite, not by a stage mutant);
  - `0 < value` changed to `0 <= value`;
  - the order "`now=` named first".
- Unrun.

**(7) Coherence.**
- The branch matches errata rev 4, except the R5 wording (N2).
- Scope has grown beyond the original ticket (timeout range, falsy objects in `factory.make`, `sources=`/`tools=` semantics, the public `VaultConnection`), but each is covered by R4-R6.
- Nothing needs splitting out.

## Round-2 resolution table

| Finding | Status | Where |
|---|---|---|
| Design MJ1 `steps=` open | Resolved | `tick.py:355-357`; M13c, M13d; tests at `test_q8a_live_overrides.py:415-447`, `test_stage_names.py:531-580` |
| mn1 ticket has no erratum | Resolved; small new drift on R5 (N2); fail-before for this commit unproven | `TICKET.md:37-43` |
| mn2 scheduled jobs with a static token | Partly: stated in the CHANGELOG; owner item unverified; docstring thinner (N5) | CHANGELOG "What it does not cover"; `app.py:100-102` |
| mn3 limit wording omits siblings | Resolved; one new omission (N1) | `app.py:99-110`; CHANGELOG "Limit, stated plainly" |
| mn4 `sweep(at=)`, `resend_unsent(at=)`, `Approvals(clock=)` | Resolved as recorded and named; ledger unverified | `app.py:105-109` |
| mn5 raise versus exit code | Resolved | `tick.py:16-19, 349` |
| mn6 timeout message and config | Partly: message resolved; config mismatch remains (N2) | `app.py:157-162` |
| mn7 seam records too little | Resolved; identities not recorded (N4) | `test_k3_pilot_env.py:189-281`; `test_k5_round8_postgres.py` store DSN assertions |
| mn8 missing mutants | Resolved | M12k-o, M12j, six "dropped" mutants |
| mn9 class convention not enforced | Resolved | `test_q8a_live_overrides.py:558-597` |
| Codebase F1 killer reads `VAULT_TOKEN` | Resolved | `test_stage_names.py:350-351, 359-364`; `test_q8a_live_overrides.py:70-75` |
| F2 no kind-name revert mutant | Resolved | M12h, M12i, M12j; third-kind case at `test_stage_names.py:501-515` |
| F3 tick.py as fourth "live" site | Resolved | M9d; CHANGELOG stage bullet names `runtime/tick.py` |
| F4 `steps=` and by-hand step | Resolved | `tick.py:353-357` |
| F5 convention; Vault logic in core wiring | Partly: guard test added; `isinstance(s, VaultConnection)` stays in `app.py` (accepted by R6) | `app.py:330` |
| F6 timeout types and bounds | Resolved | `app.py:334-342`; `defaults.py` `EXECUTOR_TIMEOUT_MAX_S` |
| F7 fail-before on a modified base | Resolved for f6fad26 (previous `RESULTS.md` section 3 labels the alias); open for fcd77a6 (N3) | evidence folder |
| F8 ticket contradiction | Resolved (R1, R2, R6); the D-012 sentence not checked | `TICKET.md:37-43` |
| F9 `asked()` records too little | Resolved | as mn7 |
| F10 joined text not pinned | Resolved | `test_q8a_live_overrides.py:522-531` |
| F11 `AttributeError` without a config | Resolved (docstring) | `tick.py:350-351` |
| Nits: factory in every stage; "outside demo" wording; parameter type; `dict()` of pairs | All resolved | CHANGELOG; `app.py:322, 88-90` |

## Verdict

CLEAN by reading (no Blocker, no Major; 5 Minor, 1 nit); not proven, because no evidence run exists for fcd77a6 (N3).

## Not checked

- Any test, mutant, lint, format, bandit or guard run for this head.
- Repo tests, demos and docs outside the snapshot, for callers of `run_tick(steps=)`, `STEPS` mutation, or `timeout_s` over 3600.
- `handover/ledger.md` and D-012.
- `tools/mutation_runner.py` (the exactly-once and first-failing-line rules are taken from the `stage_mutants.py` docstring).
- pydantic's handling of `.inf` for `gt=0` fields and the socket's handling of an infinite timeout (from knowledge, not a run).
- `DIFF-vs-main.patch` beyond its file list; the head files were read instead.
- `backends/table.py`, `factory.py` and `builtin.py` beyond a grep of the changed lines.
- CI, SonarCloud, CodeQL, CodeRabbit.

<!-- full hand-back report of sub-agent a3703391, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review round 3, Q8a-1, head fcd77a68 (codebase-details reviewer, read-only, nothing executed)

## Failures and gaps first

- **No evidence for this head.** `/home/user/hadavin-sdk/handover/evidence/Q8a-1/fcd77a6/` does not exist (only `464dee1/` and `f6fad26/`). Every "passes" below is a reading, not a run: the full suite, the 61 mutants, lint, format and bandit are unproven for fcd77a68.
- **Trees used for unchanged code:** `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk` for source, and `/home/user/build/EV-P89-db0d9eb/tests` for other tests. The tests tree is commit db0d9eb, close to main but not main.
- **No Blocker and no Major found.** 5 Minor findings and 4 nits.

## Findings

**F1. Minor: the 3600 limit applies to the keyword only; the config field has none.**
- Where: `/home/user/build/snap/q8a1-fcd77a6/src/hadavin_sdk/app.py:157-162, 240-242, 334-342`; `defaults.py:101-102`; main `config.py:360-362` (`executor_timeout_s: float = Field(default=..., gt=0)`).
- Input: a demo config with `executor_timeout_s: 7200` (or `.inf`, which I believe pydantic accepts by default; not checked) loads and reaches `Executor(timeout_s=...)` unchecked.
- `build(dir, agents, timeout_s=7200)` is refused, and so is `build(..., timeout_s=load_config(dir).executor_timeout_s)` for that config.
- The comment at `app.py:158` ("the config field is > 0 too") and the name `EXECUTOR_TIMEOUT_MAX_S` suggest one limit for the executor; there are two different rules.
- Fix: either add `le=defaults.EXECUTOR_TIMEOUT_MAX_S` to the config field (a CHANGELOG line for demo), or say in the `defaults.py` comment and CHANGELOG line 8 that `executor_timeout_s` in the config has no upper limit.

**F2. Minor: the ticket's errata rev 4 does not cover what this round built for `timeout_s`.**
- Where: `/home/user/build/snap/q8a1-fcd77a6/TICKET.md:42` (R5) against `app.py:157-162, 340-342`.
- R5 says "a finite number greater than 0, not a bool, in every stage" and gives no message text.
- The code refuses `3601`, `3600.1`, `Decimal("2.5")` and `Fraction(5, 2)`, all of which are finite numbers greater than 0.
- The value check is reached in demo only; outside demo the keyword is refused first, with a different message.
- The message "timeout_s= must be an int or float between 0 (not included) and 3600" and the constant have no line in the errata.
- Fix: one errata line for the int-or-float rule, the 3600 limit, the message and "demo only".

**F3. Minor: `runtime.tick.STEPS` is an unnamed sibling of `steps=`.**
- Where: `tick.py:255, 371`; `CHANGELOG.md` lines 6 and 10; `app.py:104-110`.
- Sequence: in a pilot process, `tick.STEPS.clear()`, `tick.STEPS[:] = [...]` or a leftover `monkeypatch.setattr(tick, "STEPS", [])`, then `run_tick(app)`. It returns 0 with no sweep and no purge, the outcome the `steps=` refusal exists to stop.
- The CHANGELOG tells deployments to append to this list, so it is a supported mutable global. The limit list names "a leftover patch of `app.make` or `app.now`" but not this one.
- Fix: add "a changed or patched `runtime.tick.STEPS`" to the limit list in the CHANGELOG and both docstrings.

**F4. Minor: the last assertion of the tick killer proves less than its message says.**
- Where: `tests/test_stage_names.py:577-580`.
- `all(after.values())` is already true from the demo run at line 553, which saved all six steps.
- `after != before` is satisfied by one step. `purge_evidence` and `reprobe_sources` are skipped by their intervals in that final tick, so only four steps change.
- A regression where a live `run_tick(app)` runs only `sweep` passes this line. `test_run_tick_refuses_a_given_step_list_outside_demo` in the q8a file does catch it (fresh app, all `None`, then all set), but the mutation runner does not run that file.
- Fix: build a fresh app for the final check, or assert the four every-tick steps each changed.

**F5. Minor: `assert_asked_as_configured` compares the handed-on objects by name only.**
- Where: `tests/test_k3_pilot_env.py:217, 261-263`.
- Settings are compared with pydantic `==` (field values and type, not identity); the detector uses `in`, which is the same equality.
- `available` is `tuple(sorted(available))`, keyword names only. Changing `app.py:227` to `store=purge_store`, or `app.py:238` to `store=purge_store`, stays green.
- The docstring says "by name", so this is a stated limit, not a false claim.
- Fix: record the objects and assert `audit` and `channel` got the object the first store call returned.

**Nits**
- `CHANGELOG.md` line 9: "An object that is falsy is used as given ... for the six keywords of `build`" is not true for `timeout_s=0` or `0.0`, which are refused (line 8 says so). Say "five" or exclude `timeout_s`.
- `defaults.py:1-8, 101-102`: the module docstring says every value is the default of a validated field. `EXECUTOR_TIMEOUT_MAX_S` is a cap on a keyword and no field reads it. It also sits under the "tools (manifest and Config.evidence)" header.
- `tick.py:348-349`: "RAISES a ConfigError before anything runs: the time then comes from the app's clock and the steps are `STEPS`" reads as if that happens after the raise. It describes a tick with neither keyword.
- `tests/test_q8a_live_overrides.py:558`: `SIGN_IN_FIELDS` is `auth` and `token_env` only. A kind that signs in with only `secret_id_env`, `role_id` or `jwt_path` under its own class is not found. The number 3600 is also repeated in `app.py:88, 336`.

## Checked line by line: nothing found

**`runtime/tick.py`**
- `given` at 355 lists `now` then `steps`, tested with `is not None`; `given[0]` names `now` when both are given.
- The refusal at 356-357 comes before `TickContext`, `app.approvals.clock()` and any store access.
- `live` is read from `app.config.environment` at call time; `given and ...` short-circuits, so `app.config` is not read when neither keyword is given. The `AttributeError` sentence in the docstring is true.
- Later uses: `now` at 358 (`is None`), `steps` at 371 (`STEPS if steps is None else steps`). Line 371 is unchanged from main, so a tuple or generator in demo behaves as before; outside demo a generator is refused without being consumed.
- Module docstring lines 16-19 are true: `cli.py:309` is `run_tick(app)`; an uncaught error exits Python with 1.
- All 22 `run_tick(..., now=/steps=)` calls in the EV-P89 tests use apps built from `make_cfg` (demo).

**`app.py`**
- `_timeout_in_range`: bool is refused first; `Decimal`, `Fraction`, text and list fail `isinstance(value, int | float)`.
- NaN and infinity fail `0 < value <= 3600`; `10**400` is compared as an int, with no overflow; `3600` and `3600.0` pass.
- The message is built from `EXECUTOR_TIMEOUT_MAX_S` (an int, so "3600").
- The check sits after the live refusal at 147-156. The fix-2 hunks in `build` are imports, docstring, this check and the `Backends` annotation; no order changed.
- The docstring's "five checks, in this order" matches lines 127-146.

**`defaults.py` and other src hunks**
- The constant is defined once and documented.
- `backends/factory.py:51`, `builtin.py:17` and the `table.py` rename match the CHANGELOG.

**Tests, can each fail**
- Timeout refused (15 cases) and accepted (7 cases): yes, on the exact message or the stored value. The parametrize ids are unique.
- The builder's "12 only changed message text" holds. The previous `_positive_number` (bool or not int/float, then `0 < v < inf`) refused the first 12 of `TIMEOUT_REFUSED`; `10**400`, `3601` and `3600.1` are new refusals.
- Step-list tests: fail on no raise, a wrong name, a step that ran, or `STEPS` not all run afterwards.
- Autouse `_no_vault_credentials`: function scope, this module only, undone by `monkeypatch`, cannot leak. No test in the module needs the variables: every Vault backend is planted or refused before it is built.
- A broken check with real `make` stops at `_env` ("environment variable ... is not set"), before any network call (`secrets_vault.py:145-149, 165-168`).
- `_build_refusal`: removes both variables inside its own `MonkeyPatch.context`. `hasattr(settings, "token_env")` returns an empty `FakeSecretProvider` instead of building.
- A mutant that lets the build continue (M12b, M12f, M12g) still ends at `platform_secrets.check`, which wraps any provider error as `ConfigError`. The first failing assertion is `got == want`, with the right message.
- Purge test: `first, second` unpack needs exactly two store calls; `second.dsn_secret_name == purge name != first` holds ("pg-purge" vs "pg-dsn").
- Guard test: fields are found through `entry.settings.model_fields` (inherited ones included); the planted `_SignsInByItself` is reported; `held` pins the two real Vault kinds.
- Two-token test: exact, anchored; the order secrets then signer follows `Backends.entries()` (the `TABLE` order).

**Mutants: 61 counted**

Each `old` occurs exactly once in its head file, each killer exists, and the first failing assertion carries `expect`:

| Mutant | First failure under the mutant |
|---|---|
| dropped secrets, detector, llm, clock, timeout_s | six-keyword loop, "a live build took the keyword <name>=" |
| dropped channel | first loop, "a live build took a test object" |
| M12h | third-kind assertion |
| M12i | approle iteration; kubernetes passes first |
| M12j | `made == []`; the message assertion passes first |
| M12k, M12l | pilot, `_FalsyDict` case |
| M12m | value 0 |
| M12n | inf; 0 and -1 are still refused |
| M12o | True, the last value |
| M13c | pilot, `steps=[step]` |
| M13d | pilot, `steps=[]` |
| M9d | first non-stage value, "the tick treated" |

No killer passes under its mutant, by reading.

**Suppressions**
- No added line in `DIFF-vs-main.patch` holds `noqa`, `nosec`, `type: ignore`, `pragma: no cover` or `NOSONAR`.

**CHANGELOG**
- Lines 6-14 were checked sentence by sentence against the code. Everything matches except F1, F3 and the first nit: messages, order, "outside demo", the command lists against `cli.py` (only `_tick` calls `build`; gate, limits, audit verify, migrate, replay and score call `make`), `sweep(at=)` and `resend_unsent(at=)` (they exist on main), and `tick.py` named among the `is_live` callers.

## Verdict

CLEAN (no Blocker, no Major), by reading only; no run evidence exists for fcd77a68.

## Not checked

- Any test, mutant, ruff, format, bandit or gitleaks run for this head.
- `tools/mutation_runner.py` (the exactly-once and first-failing-line rules are taken from the `stage_mutants.py` docstring).
- Whether pydantic accepts `.inf` for `executor_timeout_s`.
- `docs/`, `demos/`, README and `.github` for callers of `run_tick(steps=)` or `build(timeout_s=)` above 3600.
- `tests/test_repo_rules.py` and `test_no_hardcoded_values.py` against the new `defaults` import in `app.py` and the repeated 3600.
- The stage-word scanner on the new text, beyond a reading of the patterns.
- `handover/ledger.md` and decision D-012.

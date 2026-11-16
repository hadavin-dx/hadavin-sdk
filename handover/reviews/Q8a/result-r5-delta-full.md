<!-- full hand-back report of sub-agent a360a436, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW Q8a-1 round 5 (delta), head ecd5dba1. Reading only: nothing was run. The evidence folder /home/user/hadavin-sdk/handover/evidence/Q8a-1/ecd5dba/ does not exist yet. Every run-dependent claim is unproven at this head: suite, mutant count, lint, bandit, and the "3 rows planted, all 3 deleted" figure in the CHANGELOG. That figure comes from the 0b97d55 probes.

## Verdict: no Blocker. 1 Major (a documentation overclaim, no code defect), 5 Minor, 2 Nit. All six round-4 items are closed in the code. One of them (the config error text) is closed in code but overstated in the text.

## (a) Round-4 items, by reading

| Item | Status |
|---|---|
| M1 exact-type check | Closed. `type(ctx) is not TickContext` is at tick.py:96. `__init_subclass__` raises TypeError (tick.py:75-78). Tests at test_q8a_live_overrides.py:698-722 use a `Mock(spec=...)`, an object with a `__class__` property, and a subclass. Mutants M13k and M13l cover them. |
| m2 duplicate step names | Closed. `_repeated_step_names` is at tick.py:331 and the refusal at tick.py:450-451, after the missing-step check. Test at line 726 and mutants M13m and M13n. |
| m3 errata | Closed. Ticket rev 6 and rev 7 record the 0.001 bound, the frozen and optional-time `TickContext`, the exact type and the duplicate-name refusal. Rev 7 line 58 carries the overclaim in M1 below. |
| m4 config error without the value | Code closed, claim overstated. `_value_free_text` is at config.py:491-498. See the answer to (d) and finding M1. |
| m5 YAML 1.1 note | Closed. CHANGELOG line 8 says `0x10` means 16 and `1:30` means 90. This matches PyYAML's resolver, which I know from reading about it and did not run. |
| m6 honest limit texts | Closed apart from the small gaps in (e). |

## Findings

### M1. Major: "A config error never shows the value that was refused" is false as written
- Where: CHANGELOG.md line 8 (last sentences) and ticket errata rev 7 line 58 ("a config error never shows the refused value").
- Why it is false:
  - `Config` and the backend models use `hide_input_in_errors=True` (config.py:61, backends/table.py:24). So round 4's premise that `input_value=` was echoed did not hold for `Config`. `_value_free_text` really only removes the documentation link and the `ctx` block.
  - Custom validators still put values into `msg`, and `_value_free_text` prints `msg`:
    - config.py:410-413 prints the whole `base_url` of a system. A URL such as `https://user:pw@host` can carry a credential.
    - config.py:407 prints the detector route, and 283-297 print the lists `case_insensitive_targets`, `stored_kinds`, `cluster_suffixes` and the ports.
    - config.py:136 builds `f"backends.{cap} ({kind}): {exc}"`, which is the raw pydantic text with the link.
    - config.py:540 uses `str(exc)` for any ValueError, TypeError or YAMLError. A YAML error text quotes the offending line.
    - config.py:457 echoes a duplicate key. config.py:115 echoes an unknown kind. config.py:481 echoes the path.
    - registry.py:224-225 uses `str(exc)` for agent and contract files.
    - `SourceConfig._kind_checks` (config.py:324) calls `KubernetesSettings`, which has no `hide_input_in_errors` (sources/kubernetes.py:58). The exact error text depends on how pydantic converts a ValidationError raised inside a validator. I did not check that.
  - The `__cause__` chain is kept (`from exc`, config.py:538), so a traceback printed outside the CLI shows the chained ValidationError text and link. Only the `msg` leak above applies, because of `hide_input`.
- Failure scenario: a person puts a URL with a password into `systems.x.base_url` using http. The error repeats the whole URL, and the CHANGELOG says this never happens.
- Fix: narrow the sentence to "the executor-timeout error and the pydantic field errors of `Config` do not repeat the value". Or make the custom messages value-free.
- Severity note: I rate this Major because the timeout path itself is fine. Under the persona rule "document contradicts the code", the lead may treat it as a Blocker.

### m1. Minor: tick.py module docstring says "Three refusals do NOT come back as an exit code" (tick.py:16-20)
It lists `now=`, `steps=` and a missing built-in step. The duplicate-name refusal raises a ConfigError too, so it is a fourth. The `run_tick` docstring and the CHANGELOG do list it. Fix: say four, or drop the count.

### m2. Minor: `dataclasses.replace(ctx, ...)` on a live context is refused with a wrong-sounding message
`replace` passes every field, including `now`, which is never None after construction. So `replace(ctx, results={})` on a pilot app raises "now= is for tests; it is refused in pilot and prod". The test only pins `replace(ctx, now=...)` (line 763). A person copying a context is told they handed a time. Either name this in the TickContext docstring or accept it as intended.

### m3. Minor: the subclass ban is a breaking change in every stage (demo included) and is not in the upgrade steps
CHANGELOG line 6 gives upgrade advice only for assigning `ctx.now` and for `TickContext(app, <time>)`. "The class can no longer be subclassed" appears only in the limit bullet (line 10). Test code in a client's own suite that does `class FakeCtx(TickContext)` will raise TypeError at import. Add one sentence to the upgrade steps.

### m4. Minor: no mutant for `_value_free_text`, and its test passes without it
`test_a_config_error_never_shows_the_value...` (line 745) checks that the value is absent. That holds even with plain `str(exc)`, because `Config` already hides inputs. Only the `"errors.pydantic" not in text` assertion would fail. There is no mutant in stage_mutants.py for `_value_free_text`, `include_url=False` or `include_context=False`. A test with a nested or custom-validator error would pin the real behaviour.

### m5. Minor: wording for a non-technical reader
CHANGELOG lines 6 and 10 are each one bullet of roughly 400-700 words. They use terms such as "stand-in", "frozen", "built without its constructor", "crafted pickle", "Mock(spec=...)" and "`object.__setattr__`" with no plain gloss. The plain sentence "these refusals stop a test object that arrives by accident, not hostile code in the same process" is present and good, but sits at the very end. Move it first and split the bullets into the headings: keywords, tick steps, timeout, limits.

### n1. Nit: an in-place edit of `STEPS` between the checks and the loop is not named
`run_tick` reads `STEPS` for the two checks (tick.py:448-451) and again for the loop (tick.py:465). Another thread could change the list in between. This was raised in round 4 as low severity and is still unnamed. One clause ("or a list changed by another thread during the tick") would close it.

### n2. Nit: the CHANGELOG states the direct-purge figure ("3 rows planted, all 3 went") as fact
It comes from a run on 0b97d55 (questions-for-lead.md line 1757) and has not been re-run at ecd5dba. Re-check it against the new evidence when it arrives.

## (b) Is the exact-type check at the real choke point?
- Yes for time. Everything that decides by age goes through `_now`: `sweep` (tick.py:132-133), `stuck` (178-199), `purge_evidence` (248-269) and `_run_step` (388-400).
- Direct callers of `purge_tool_calls`, `purge_redaction_maps` and `sweep` in src are only these steps. `list_due_approvals` is called only from `sweep`.
- No other `isinstance`, `getattr` or `.now` decision on a context exists in src. A grep outside tick.py found none.
- The other `getattr` uses in tick.py (`checkpoint`, `stuck_after_s`) are not about time or stage.
- Residual routes are the ones the docs already name. They are all hostile and in-process: `object.__setattr__`, `__new__` or pickle, a wrapped demo app, and a replaced `TickContext` or `NO_GIVEN_TIME` name in the module.
- A stand-in with no `app` gets an AttributeError, not a ConfigError. That still refuses, so it fails closed.
- `is_live` is `environment != "demo"`. A hostile str subclass with a custom `__ne__` would pass. That is hostile.

## (c) Duplicate-name refusal: bypasses
- Name case, whitespace and unicode lookalikes are stopped upstream by `TickStep.__post_init__` (tick.py:110). It uses `re.fullmatch(r"[a-z_]+")` with no IGNORECASE, so uppercase, a trailing newline, and characters like Kelvin or long-s are refused before they reach STEPS.
- No config route sets a step name, so "name given through config" does not exist.
- What remains is hostile:
  - A `TickStep` whose name was changed with `object.__setattr__`.
  - An object in STEPS that is not a `TickStep` and has a lying `.name`, for example a str subclass with a custom `__eq__` or `__hash__`.
  - A bypass that is not hostile: the check runs only outside demo. That matches the design.
- The check compares names only. Reordering and same-name replacement are not duplicates and are named as not covered.

## (d) `_value_free_text`
- It uses `exc.errors(include_url=False, include_input=False, include_context=False)`. It prints `loc` and `msg` only, so nested errors and list input are covered at that level. For `executor_timeout_s: [1]` the value is not printed. The `loc` can include list indices and dict keys, which are key names and not values. That was already so.
- The `__cause__` chain is still attached. Its text is value-free for `Config` because of `hide_input`, apart from the link and whatever `msg` holds.
- The rename-sentence path (config.py:501-517) prints only `msg` and the `_RenamedStage` text, so it is fine.
- Remaining echo routes are listed in M1.
- Not checked: `errors(include_input=...)` needs a recent pydantic. pyproject.toml is not in the snapshot, so I could not see the pin.

## (e) Limit texts (CHANGELOG line 10, app.py:114-128, tick.py:70-73 and 437-443)
- True and present: `object.__setattr__`, built without its constructor or by pickle, a wrapped app, reordered STEPS, same-name no-op, huge `every_s` or `interval`, `_BUILT_IN`, a replaced clock, direct store purge (with the numbers), and `Approvals.sweep(at=)` and `resend_unsent(at=)`.
- The code matches: requests.py:137 and 199 use `is None`.
- Direct store purge: the limit texts are complete. The open question is correctly kept out of the text as a decision for the lead (questions-for-lead.md:1756-1760). The limit is stated plainly, and the CHANGELOG, `build`, `run_tick` and ticket rev 7 all agree.
- Not named: n1, m2 (`replace` on a context). Also stale: m1.

## (f) Wording
- The message texts are plain: "now= is for tests; it is refused in pilot and prod", "a built-in tick step is missing: <names>", "a tick step name is used twice: <names>", and the timeout sentence.
- The CHANGELOG paragraphs are hard for a non-technical reader (m5).
- The `_now` docstring (tick.py:91-95) is clear and true.

## (g) Weakened or removed tests
- Only src exists in /home/user/build/q8a2-dryrun/main-2a8c2aa/, so I could not diff tests against main. I did not see the 0b97d55-to-ecd5dba1 diff.
- In the snapshot, the stand-in tests (lines 669-717) are present and wider than before: stand-in, a spec'd Mock, and `__class__` lying. Demo behaviour is still pinned at line 782. The mutant list grew with M13k-n.
- I found no sign of weakening in what I read. I cannot assert it for tests I did not open: the changed hunks of test_stage_names.py and the two earlier-changed K5 tests (test_k5_round8_postgres.py and test_k5_round9b.py), which round 4 cleared.

## (h) Single dependency and least privilege
- No new dependency or import beyond the leaf `stages` and `errors` modules. `_value_free_text` uses only pydantic's public API and `yaml` is already imported.
- `TickContext` reads only `app.config.environment` and `app.approvals.clock`. Nothing gained a broader grant. `purge_store` is still the deleting identity.
- The pydantic version pin is unchecked (see above).

## Not checked
- Any run: tests, mutants, ruff, format, bandit, gitleaks, and the Postgres tests.
- The diff against 0b97d55a. I read the final files whole. I did not read pyproject.toml, tools/, or CHANGELOG.md lines 322-403, which I only grepped for matches (older entries).
- How pydantic converts a ValidationError raised inside a validator (`SourceConfig`).
- PyYAML behaviour, taken from knowledge and not run.
- The test bodies other than lines 625-790 and the grep hits of test_q8a_live_overrides.py and test_stage_names.py.
- The ledger and the owner-question trail beyond questions-for-lead.md lines 1756-1760.

Files: /home/user/build/snap/q8a1-ecd5dba1/src/hadavin_sdk/runtime/tick.py, config.py, app.py; /home/user/build/snap/q8a1-ecd5dba1/CHANGELOG.md; /home/user/build/snap/q8a1-ecd5dba1/tests/test_q8a_live_overrides.py, stage_mutants.py; /home/user/hadavin-sdk/handover/tickets/Q8a-live-override-refusals.md.

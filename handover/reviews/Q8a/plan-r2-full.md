<!-- full hand-back report of sub-agent a62ab99a, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Mode: REVIEW. Target: /home/user/hadavin-sdk/handover/tickets/Q8a-live-override-refusals.md (rev 2). Read-only; nothing was run. All standards and the target were read.

VERDICT: NOT READY (1 blocker, 5 majors). The design is sound and every cited line number is correct; the gaps are a wrong literal code line and unstated test mechanics.

## Blocker

**B1. The literal `given` line is wrong for `clock`, and the ticket leaves the fix to the builder.**
- /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/app.py:73 has `clock: Callable[[], datetime] = now`. The other five default to `None` (lines 66-69, 74).
- With `v is not None` as written in Behaviour 1, `clock` is always "given". Every live build would be refused with "clock= is for tests", including the production caller `build(None, agents)` at /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/cli.py:299.
- The parenthesis "use each parameter's real default sentinel ... state what you found" contradicts the code line and hands the builder a design choice.
- Without Postgres nothing catches this: both positive pilot tests skip without HADAVIN_TEST_PG_DSN.
- Ticket text, pick one:
  - (a) "`clock` is the only parameter whose default is not None (app.py:73, `= now`). Change the signature to `clock: Callable[[], datetime] | None = None`, use `is not None` for all six, and after the refusal write `clock = now if clock is None else clock`."
  - (b) "Keep the signature; `clock` counts as given when `clock is not now` (the `now` imported at app.py:32); the other five use `is not None`."
  - I recommend (a): one uniform rule, and it does not depend on the module global `now`.
- Also add: "Add a test that needs no Postgres and proves a live build with NO override gets past the new check."

## Majors

**M1. The secrets backend is built at app.py:82 before the new check, so most refusal tests hit a different error first.**
- For `channel=`, `detector=`, `llm=`, `clock=` or `timeout_s=` given alone, line 82 runs `make("secrets", b.secrets)`.
- `pilot_cfg` (/home/user/build/EV-P89-db0d9eb/tests/test_k3_pilot_env.py:53) sets `mounted_file` with dir `secrets` and never creates that folder.
- /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/actions/secrets_file.py:70-71 then raises `ConfigError("secrets mounted_file: ... is not a folder")`. Ten of the twelve refusal tests, and the falsy-object test unless its override is `secrets=`, fail for the wrong reason.
- Ticket text: "The refusal tests create `<root>/secrets/` (empty) after `pilot_cfg`. `mounted_file` reads nothing until `get`, and nothing reads a secret between app.py:82 and the new check. The falsy-override test uses a falsy `channel=` object (a class whose `__bool__` returns False)."
- Alternative: move the `given` raise above line 82 and re-order the existing refusals. That changes the "four negative tests untouched" analysis, so the folder is the simpler fix.

**M2. No recipe for a prod config or a non-stage config.**
- `pilot_cfg(env="prod")` does not load. /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/config.py:420-424 refuses `anchor: none` and `signer ed25519_local with a key file`.
- A non-stage value never loads (`Literal` at config.py:333).
- The only existing prod helper (/home/user/build/EV-P89-db0d9eb/tests/test_p3b_neutral_audit.py:248) is built to be refused.
- Ticket text for Behaviour 1: "Prod and non-stage cases follow the precedent at tests/test_stage_names.py:302-311. Load the pilot config, `copy = cfg.model_copy(update={'environment': stage})`, and `monkeypatch.setattr(app_mod, 'load_config', lambda _d: copy)`; patch `load_registry` the same way with the registry loaded from the pilot config. Do NOT start from the demo fixture: it has no restored-hash key, so app.py:84 raises first."
- Ticket text for Behaviour 2 (exact-message match needs a config with nothing else refused): "Pilot: `pilot_cfg` with `backends.secrets = {kind: vault, address: https://vault.example}`, or `backends.signer = {kind: vault_transit, address: https://vault.example, key_name: k, key_version: 1}`. Prod: the same plus `anchor: {kind: s3_object_lock, bucket: b, region: r, retention_ack: true}`, and for the `vault` case `signer: {kind: ed25519_local, private_key_secret_name: audit-key}`. Assert with `load_config` only."

**M3. tests/stage_mutants.py can take the two mutants only under constraints the ticket does not state.**
- The `mutant()` helper (/home/user/build/EV-P89-db0d9eb/tests/stage_mutants.py:40-43) hardcodes `test_file` and `pinned` to tests/test_stage_names.py.
- The runner is called with `[TEST]` only (line 154). /home/user/build/EV-P89-db0d9eb/tools/mutation_runner.py:1118-1122 raises `ValueError` for any `test_file` not in that list.
- It runs with `--noconftest` and passes no HADAVIN_TEST_PG_DSN (no `pass_env`).
- So both killer tests must be in tests/test_stage_names.py, use no conftest fixture, and need no Postgres. That is feasible: both refusals fire before the store is built.
- The runner replaces every occurrence of `old`. `if is_live(self.environment):` (mutants M4a, M4d) and `live = is_live(cfg.environment)` (M4g, M9c) must each stay a single occurrence in its file.
- Ticket text: "Put the new tests, or at least the two killers, in tests/test_stage_names.py, with no conftest fixtures and no Postgres. Mutants: (APP) replace the new `if live and given:` with `if False:`, killer `<test name>`; (CFG) replace the Vault kind set or `== "token"` so the rule never matches, killer `<test name>`. Give each killer assertion its own message and use a fragment of it as `expect`, as the existing mutants do. Do not add a second occurrence of the two strings above."
- Without an own assertion message the first failing line will be pytest's "Regex pattern did not match" or "DID NOT RAISE" depending on what the mutated build raises next; the builder would have to guess.

**M4. The seam for the two positive pilot tests is offered as "A or B", and option A has a trap.**
- Both options work mechanically. `build()` calls the module global `make` (app.py:82, 162, 170), so `monkeypatch.setattr(app_mod, "make", wrapper)` takes effect. `TABLE` is consulted at config load (config.py:111) and in `make`, so `setitem` works too.
- The trap in `setitem`: test_k3_pilot_env.py:194-200 asserts the resolved names include `slack-sign` and `slack-token`. Those come from `platform_secrets.check` reading `*_secret_name` fields of the channel SETTINGS (/home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/backends/platform_secrets.py:18-20, 58-61). A planted channel kind with plain `KindSettings` drops them and the assertion fails.
- Table factories are `"module:function"` strings, so the per-iteration DSN, the spy, the `FakeChannel` instance (asserted at line 204) and the `ScriptedLLM` would need module-level state.
- Ticket text: "Use one seam: `monkeypatch.setattr(app_mod, 'make', wrapper)`, where `wrapper(cap, settings, *a, **kw)` returns the test's spy, FakeChannel or ScriptedLLM for `secrets`, `channel`, `llm` and calls the real `make` otherwise. The config keeps `slack` and `openai_compat`, so every assertion stays as written. Add the `monkeypatch` parameter to both tests; test_k5_round8_postgres.py does the same."

**M5. The regression guard "`hold_run_ids=` accepted when live" has no stated mechanism.**
- It needs a complete live build, which needs Postgres or a `make` that is patched for every capability.
- Ticket text: "Assert it inside `test_k3_pilot_app_has_no_executor` by passing `hold_run_ids=lambda: frozenset()` (Postgres run, output pasted). The no-Postgres proof for B1 is: with `make` patched for every capability, a pilot build with no override and with `hold_run_ids=` does not raise the override refusal."

## Stated facts checked and found true

- **Four negative tests untouched.** Each expected error is raised before the new check:
  - tests/test_stage_names.py:313-317 expects the restored-key error (app.py:84-85).
  - tests/test_k5_round10.py:80 expects `purge_dsn_secret_name` (app.py:86-89).
  - tests/test_k5_round9b.py:370 expects the restored-key error (app.py:84-85).
  - tests/test_k5_round5.py:226 expects "plain callables" (app.py:93-98).
- **No other caller passes `clock=` or `timeout_s=` to a live build.** tests/test_cuj.py:53-54, tests/test_p7_tick.py:46, tests/test_review_pr3_round2.py:49 and tests/test_k5_round5.py:748 all use demo fixture configs. The only production caller is cli.py:299, with no overrides. demos/, docs/, tools/ and .github/ have no `app.build` call.
- **Live builds with overrides** are exactly the two positive tests, the four negative tests and `_live_by_site`.
- **`Config._cross_checks`** has the assumed structure (config.py:393-401, message `environment <stage>: refused: ...`).
- **`Backends.entries()`** exists and returns `list[(capability, settings)]` (config.py:83-85).
- **Vault settings.** `_VaultConnection.auth` defaults to `"token"` (/home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/backends/table.py:255), so the omitted-auth case is caught. Kinds are `vault` (capability `secrets`) and `vault_transit` (capability `signer`).
- **No existing test loads a live config with Vault token auth.**
- **Other citations.** The precedent at tests/test_p1b_backends.py:127-131 and CHANGELOG.md:70 are as described.

## Minors

- The Vault message contains parentheses. Say "`match=re.escape(<message>)`", or `pytest.raises(match=...)` will not match the exact text.
- "six test call sites changed" in the rung table is unclear: it is two `build()` calls with three override keywords each. Reword.
- `app.py:82`, `162`, `170` and `173` use `x or make(...)`, so a falsy override object is silently dropped in demo. State whether that stays out of scope, or switch those lines to `is None` in this ticket.
- With several overrides given, only `given[0]` is named, in tuple order. Say this is intended, or name them all.
- The comment at /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/backends/builtin.py:17 ("Tests pass their own provider to app.build(secrets=)") should gain "(demo only)".
- "before anything else is built" is not literally true: the secrets provider is already built at line 82. Reword to "before any backend other than secrets is built".
- State where the shared `make` wrapper lives, since test_k5_round8_postgres.py imports helpers from tests/test_k3_pilot_env.py.

## Not checked

- No test, mutant or gate was run.
- pytest's exact first-line wording for a `match` miss.
- Whether `load_registry` accepts a pilot-loaded config copied to `environment="prod"` (M2 suggests patching it, as the precedent does).
- tools/mutation_runner.py lines 852-1097 and 1128-1278 were only grepped.
- reviews/Q8/deps-audit.md, reviews/Q8a/plan-r1-summary.md, handover/STUDIO-RULES.md, .github/workflows/ci.yml beyond line 94, and tests/test_k3_pilot.py (ScriptedLLM) were not read.
- Whether `approle` staying allowed satisfies the least-privilege rule's "short-lived credentials only". The ticket logs it as an owner question; I did not judge it.

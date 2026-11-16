<!-- full hand-back report of sub-agent a06b79ad, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review round 1, Q8a-1, head 464dee14 (snapshot /home/user/build/snap/q8a1-464dee1/)

## Outcome

No Blocker and no Major found by static reading. Six Minor/Nit findings below. Nothing was executed (read-only), so every "passes" below is a reading, not a run.

Independent evidence: /home/user/hadavin-sdk/handover/evidence/Q8a-1/464dee1/RESULTS.md is NOT present (the directory /home/user/hadavin-sdk/handover/evidence/Q8a-1 does not exist). The two Postgres-only positive tests, the fail-on-main proofs, the mutant run and the gates therefore have no evidence I could read.

## Findings

**1. Minor: a second seam helper duplicates the shared one; E1's "patch make for every capability" is met only in part.**
- Where: tests/test_q8a_live_overrides.py:87-96 (`plant`) versus tests/test_k3_pilot_env.py:175-186 (`plant_test_backends`).
- Both wrap `app_mod.make` the same way; `plant` adds a special case for `store` (`made() if callable(made) and capability == "store" else made`).
- `test_a_live_build_with_no_test_keyword_is_not_refused` (line 179) plants only secrets, store, channel and llm. signer (ed25519_local from the generated key file), anchor (none), audit (chain) and detector (regex) go through the real factory.
- No network is touched, and running the real path is arguably the stronger test, but it departs from E1's wording and from E5's "ONE seam".
- Fix: extend `plant_test_backends` to take `**objects` and an optional store factory, and use it in both files; or record the deviation in the PR.

**2. Minor: the same truthiness slip remains for `sources=` and `tools=`.**
- Where: src/hadavin_sdk/app.py:114, 117, 161, 250, 285 (`if sources and live`, `if tools and live`, `sources or {}`, `tools or {}`).
- Repro: `class M(dict): __bool__ = lambda self: False`, then `build(demo_dir, [...], sources=M(k8s=bad_source))`. The object is silently dropped and its scope probe never runs.
- In pilot the same object skips the `sources=` refusal, but it is also dropped, so no test object gets in.
- This is outside E7's four lines, so it is not a ticket failure. The CHANGELOG sentence "an object that is falsy is now used as given" is true only for the six keywords.
- Fix: switch to `is not None` / `is None` in a follow-up, or narrow the CHANGELOG sentence to the six keywords.

**3. Minor: the Vault rule keys on kind strings, not on the settings type.**
- Where: src/hadavin_sdk/config.py:168 and 404-408.
- `_VAULT_KINDS = {"vault", "vault_transit"}` matches the ticket and is correct today: `auth` exists only on `_VaultConnection` (table.py:250-265), and only those two table entries use it (table.py:399, 457).
- A later kind that reuses `_VaultConnection` under another name would pass with a static token. Repro: plant a kind `openbao` with `VaultSettings`.
- `getattr(s, "kind", "")` is needlessly defensive; line 398 already reads `s.kind` directly.
- Fix: test `isinstance(s, _VaultConnection)` (exported from table.py), or add a test that every TABLE settings class with an `auth` field is in `_VAULT_KINDS`.

**4. Nit: `timeout_s=` is not validated in demo.**
- Where: src/hadavin_sdk/app.py:209-211.
- Repro: `build(demo_dir, [...], timeout_s=-1)` or `timeout_s=True` reaches `Executor`, while `executor_timeout_s` is `gt=0` in the config.
- The CHANGELOG states the 0 case honestly and tests/test_q8a_live_overrides.py:241 pins it. No main test relied on 0 meaning "use the default".
- Fix: none required; optionally refuse `<= 0`.

**5. Nit: the docstring understates what runs before the refusal.**
- Where: src/hadavin_sdk/app.py:82-83.
- It says the refusal comes "after the `sources=` and `tools=` refusals". Two more checks precede it: the restored-hash key (line 108) and the purge DSN (line 110). tests/test_k5_round9b.py:370 and tests/test_k5_round10.py:80 depend on that order.
- Fix: name them in the docstring.

**6. Nit: formatter artefacts and one docstring claim in the new tests.**
- Formatter artefacts from trailing comments: tests/test_stage_names.py:340-343 (`( root / "secrets" ).mkdir()  # ...`) and 391-393; tests/test_q8a_live_overrides.py:215-217.
- Fix: move each comment to its own line.
- `vault_dir`'s docstring says "the Vault rule is the only refusal", but the refusal test uses an unanchored `re.escape` search. The proof is the companion test `test_the_other_vault_sign_ins_are_accepted_in_pilot_and_prod`, which is fine but was not run by me.

## Checked and found correct

**`given` list and refusal (app.py:93-133)**
- Order is secrets, channel, detector, llm, clock, timeout_s, and `given[0]` is named; no off-by-one.
- All six use `is not None`.
- `given` is computed before `secrets` is rebound at line 105, so a factory-built provider does not count as given.
- Message text equals the ticket strings exactly, for both the `backends.<name>` form and the clock/timeout_s form.
- The refusal sits after the `tools=` refusal; only the secrets backend is built before it (E2).
- `clock = now if clock is None else clock` is at line 133. The only use of `clock` in `build()` is line 219 (`Approvals(...)`); there is no earlier use.
- The signature default is `None` (E1).

**`x or make(...)` sites**
- app.py:105, 197, 206, 209 and factory.py:51 are all `is None`.
- No truthiness test remains on any of the six overrides in app.py or backends/factory.py.
- Remaining truthiness in those files: `sources`/`tools` (finding 2), `executor.execute if executor else None` (a built object, not an override), `disabled`, `ca_file`, and the `missing` import name.
- Elsewhere in src, `clock or ...` in audit/anchor_s3.py:41 and anchor_azure.py:40, and `if clock` in k1b/replay.py:139, are unrelated to `build()`.

**Vault rule (config.py:401-408)**
- It is inside the existing `if is_live(...)` block and appends to the same `refused` list, so the message shape is `environment <stage>: refused: ...`.
- Settings without `auth` give `None` via getattr; detector tuple entries are covered by `entries()`.
- `auth` is a `Literal` str with default `"token"`, so the omitted case matches.
- A non-stage environment cannot reach the validator through `load_config`: the `Literal` field fails first and the after-validator is skipped.
- Demo is unchanged.

**CHANGELOG**
- Both entries match the code: messages, order, the falsy rule, the `clock` default, the `factory.make` note, the `role` / `role_id` field names (table.py:258-260, 277), and both honest limits.
- The Vault message appears inside pydantic's wrapper text, as the existing refusals do.

**Mutants**
- `if live and given:` occurs once in app.py; `getattr(s, "auth", None) == "token"` occurs once in config.py.
- `live = is_live(cfg.environment)` and `if is_live(self.environment):` each still occur once (E4).
- Both killers have their own message, and `expect` is a fragment of it.
- Under M12a the pilot build goes on to `platform_secrets.check` and raises a different ConfigError, so `got != want` fails with the expected message.

**Tests**
- Exact-message matches use `^` + `re.escape` + `$`; the Vault matches use `re.escape`.
- I found no test that cannot fail, and no order dependence.
- No network: mounted_file is local, and slack/openai are planted or never reached.
- `FakeSecretProvider`, `FakeChannel` and `ScriptedLLM` define no `__bool__` or `__len__`, so the Falsy subclasses are needed and effective.
- `plant_test_backends` uses the test's `monkeypatch`, so it is undone at teardown; repeated calls inside the `pg_schema` loop stack and unwind, and it does not leak. It is not collected (no `test` prefix).
- `test_the_factory_hands_a_falsy_secret_provider_to_the_backend` uses `MonkeyPatch.context()`, so the TABLE entry and the `seen` attribute are restored.
- The stage-word scanner (test_stage_names.py POSITIONS) has no hit in the new or changed scanned files, as far as I can read the patterns.

**Other callers on main**
- The only src caller is cli.py:299, `build(None, agents)`, with no override.
- Live-config `build()` calls with overrides in main tests:
  - tests/test_k5_round10.py:80, test_k5_round9b.py:370, test_k5_round5.py:226 and test_stage_names.py:315 all expect an earlier refusal and keep it.
  - tests/test_k3_pilot_env.py and test_k5_round8_postgres.py are converted in this branch.
  - tests/test_k5_tools.py:1246 uses a pilot config but calls `_toolbox`, not `build`.
- No `FakeSecretProvider({})` passed as an override, no `timeout_s=0`, no `clock=None`, and no falsy override anywhere in main tests.
- tests/test_k5_round5.py:742-750 (`timeout_s=1.5` in demo) is unaffected.

## Not checked

- No test, mutant, ruff, format or bandit run; the fail-on-main proofs were not reproduced.
- The two Postgres positive tests (test_k3_pilot_env.py:189, test_k5_round8_postgres.py:21) were read only.
- tools/mutation_runner.py was outside the allowed read set, so its exactly-once and baseline rules are assumed from the stage_mutants.py docstring.
- docs/, demos/, README and .github were not read, for callers of `build(clock=...)` or prose describing the overrides.
- Whether the Vault provider contacts Vault at construction (before the refusal, when `secrets=` is not given) was read only from grep; sign-in looks lazy.
- Whether chain audit on `MemoryStore` builds in `test_a_live_build_with_no_test_keyword_is_not_refused` was not confirmed.
- The ticket's rung-table wording change (E7) is not in the snapshot diff.

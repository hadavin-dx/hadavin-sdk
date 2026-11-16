<!-- full hand-back report of sub-agent a2a30519, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, Q8a-1 round 1, head 464dee14 (design critic, read-only)

## Failures and gaps first

- **Evidence was not available.** `/home/user/hadavin-sdk/handover/evidence/Q8a-1/` does not exist. Every "passes" is unproven: the fail-on-main runs, the two non-skipped Postgres runs, the four untouched negative tests, both mutant kills, and the ruff, bandit and guard gates.
- **I ran nothing.** All findings come from reading the diff, the changed files and the main export.
- **One read outside my stated scope.** I ran a single search of `/home/user/hadavin-sdk/handover/ledger.md` to look for the approle owner question. I did not use its statuses as evidence.
- **Verdict: not clean.** No Blocker found in the code as written; 3 Major and 8 Minor findings.

## Major

**M1. The Vault rule also disables operator commands, which nobody states.**
- Where: `/home/user/build/snap/q8a1-464dee1/src/hadavin_sdk/config.py:401-408`; `CHANGELOG.md` line 10.
- Scenario: the rule sits in `Config._cross_checks`, so it fires for every `load_config` caller, not only `app.build`. In main `cli.py` that covers `stop`/`reset` (kill switch, 184-209), `audit verify`, `gate` (150), `migrate` (329) and `replay`/`score` (215). A prod config has `secrets: {kind: vault, auth: kubernetes}`. An operator on a bastion has no service-account JWT, so they keep a config copy with `auth: token` and a short-lived personal token from `vault login`. That copy is now refused at load, so the kill switch cannot be run from outside the cluster.
- Wrong outcome: the only remaining route for a human is `approle`, a shared secret id in an environment variable. That is worse than a personal short-lived token under the least-privilege rule (one identity per function, no shared keys, short-lived only). The premise "token = static" is false for that operator token.
- Fix: put the operator consequence in the CHANGELOG upgrade step now. Raise an owner decision on either scoping the refusal to the long-running build or adding a non-environment token source for operator commands. The ticket forbids touching the Vault connection code, so the second option needs an erratum.

**M2. The refusal steers users to `approle`, which is the same class of credential.**
- Where: `config.py:405` (message text) and `CHANGELOG.md` line 10.
- Scenario: a pilot user hits "set auth: kubernetes or auth: approle" and picks approle. `secrets_vault.py:172` reads `VAULT_SECRET_ID` from the environment. From memory, not checked live, a Vault AppRole secret id does not expire unless the role sets `secret_id_ttl`.
- Wrong outcome: a static credential still sits in the live process environment, and the refusal reports the problem as solved. The CHANGELOG's reason ("A static token would sit in the environment of a live process") applies word for word to the allowed option.
- The limit is stated honestly. But the rule's exception 2(b) needs a recorded owner question with a next step and date; my ledger search for "approle" and "owner question" found no such row.
- Fix: record the owner question in the ledger with a date. Until it is answered, make the CHANGELOG name kubernetes as the recommended sign-in and say approle needs a short `secret_id_ttl` and use limit set on the Vault side. Changing the message text needs a ticket erratum, since the wording is frozen.

**M3. A sibling of the fake-clock route is left open: `run_tick(app, now=...)`.**
- Where: main `runtime/tick.py:335-338` (`ctx = TickContext(app, now or app.approvals.clock())`).
- Scenario: a pilot scheduler wrapper copied from a test calls `run_tick(app, now=<fixed or future datetime>)`. Approval sweep (81-82), stuck-run detection (127-148) and the evidence purge (198-216) all compute against that value.
- Wrong outcome: a future `now` deletes tool calls and redaction maps before retention; a fixed one stops approvals expiring. This is the same accident `clock=` is now refused for, one call later, and `class-level-fixes.md` requires the sibling search.
- Fix: refuse `now=` in `run_tick` when `is_live(app.config.environment)`, with a test and a mutant. Otherwise log it as a ledger Major against Q8a-2 with the reason it is not in this PR.

## Minor

**m1. Reject as built: demo `timeout_s=0` is passed through.**
- Where: `app.py:209-211`; pinned by `tests/test_q8a_live_overrides.py::test_demo_uses_a_zero_timeout_as_given`.
- Scenario: `build(demo_dir, [...], timeout_s=0)` gives `Executor(timeout_s=0)`. `actions/executor.py:80` hands that to `urllib` as `timeout=0`, which means a non-blocking socket, so every execute, verify and rollback call fails at connect. `False` and negative values pass the same way.
- The config's own field refuses this value (`executor_timeout_s: Field(gt=0)`, `config.py:362`). Old behaviour silently replaced 0; new behaviour installs a broken executor and a test pins it.
- Not silently replacing is right. Fix: validate the override like the config field, `ConfigError("timeout_s= must be greater than 0")` when given and not `> 0`, and change the pinning test to expect that.

**m2. Accept: `backends/factory.py:51` (`is None` instead of truthiness).**
- Old code swapped any falsy provider for an empty `FakeSecretProvider`, so a real provider would have been replaced by one that knows nothing. That is the same slip as in `build`, at the choke point every caller uses (`app.py`, `cli.py`, `k1b/audit_sink.py`).
- No shipped provider defines `__bool__` or `__len__` (searched `src/hadavin_sdk`), so nothing changes for existing kinds. It is tested and stated in the CHANGELOG.
- It goes beyond the lines E7 lists; record it as a ticket deviation.

**m3. Accept with two notes: `clock` default `None`.**
- No caller in `src` passes `clock` (`cli.py:299` is `build(None, agents)`), and `Approvals` keeps its own default.
- Note (a): `build(..., clock=hadavin_sdk.models.now)` in pilot is now refused although it equals the default. Say so in the CHANGELOG or exempt `clock is now`.
- Note (b): `now` is now looked up at call time (`app.py:133`), so a leftover patch of `hadavin_sdk.app.now` reaches a live build without any keyword. On main the default was bound at definition. I did not check whether any test patches it.

**m4. `_VAULT_KINDS` is a list of names, not the class.**
- Where: `config.py:168, 407`.
- Today nothing is missed: only `VaultSettings` and `VaultTransitSettings` subclass `_VaultConnection` (`table.py:250-302`), and the two `azure_key_vault*` kinds have no `auth` field.
- Scenario: a third kind built on `_VaultConnection` (a Vault anchor, or a client kind added to `TABLE`) loads in prod with the default token and no refusal.
- Fix: match `isinstance(s, _VaultConnection)`, or add a test that every `TABLE` entry whose settings subclass it is in `_VAULT_KINDS`.

**m5. The honest-limit wording understates the open routes.**
- Where: `app.py:88-89`, `CHANGELOG.md` line 9, and the module docstring of `tests/test_q8a_live_overrides.py` ("is never built with a test object by accident").
- Routes that need no hostility:
  - constructing `App`, `Runtime` or `Approvals` directly;
  - assigning `app.approvals.channel` or `app.runtime.llm` after build;
  - `run_tick(now=)`;
  - a leftover patch of `app.make` or `app.now`;
  - a kind added to `TABLE` or `sources.kinds.register` and named in config, since `DEMO_ONLY` is a deny-list.
- Fix: say "refuses the six keywords of `build`; any route that does not pass through those keywords is not covered", and correct the test docstring.

**m6. Sibling static credentials in a live environment are untouched.**
- Not in ticket scope; for the ledger.
- `DefaultAzureCredential()` (`secrets_azure.py:47`, `signer_azure.py:57`, `anchor_azure.py:75`) accepts an environment client secret. The AWS kinds use the SDK default chain, which I did not read. `ed25519_local` with a key file is allowed in pilot.

**m7. The test seam does not check what `build` asks the factory for.**
- Where: `tests/test_k3_pilot_env.py:175-186`.
- Against main it masks nothing new: with the old keywords, `make` was never called for secrets, channel or llm either.
- It does ignore `settings` and the arguments, so a regression that passes the wrong settings or drops the provider when building channel or llm would stay green.
- Fix: record the calls and assert kinds `mounted_file`, `slack`, `openai_compat`, and that the provider argument is the spy.
- `tests/test_q8a_live_overrides.py:87-96` defines a second wrapper (`plant`); E5 asked for one shared seam.
- Both positive tests skip without `HADAVIN_TEST_PG_DSN`, so they are unproven until the evidence run.

**m8. The mutants are valid but only on/off.**
- Where: `tests/stage_mutants.py` M12a, M12b. Each target string occurs once, each killer has its own message, and the M12a killer covers pilot, prod and four non-stage values.
- No mutant covers `is not None` reverting to truthiness, a name dropped from the six, `vault_transit` dropped from `_VAULT_KINDS`, or the `"token"` default path alone.
- Tests in `test_q8a_live_overrides.py` would catch these, but the runner is pinned to `test_stage_names.py`. Add at least the truthiness and dropped-kind mutants with killers there.

## Checked and found sound

- **Completeness inside `build`:** the six parameters are keyword-only, so there is no positional route; `**kwargs`, `functools.partial` and wrappers all pass through the check. `given` is computed before `secrets` is replaced (`app.py:93-106`), so a normal start is not refused. No environment variable feeds any of the six.
- **Non-stage case:** `is_live` treats anything not exactly `demo` as live, and the tests cover `staging`, `Demo`, `demo `, empty and `None`.
- **Ordering:** the new check sits after the restored-key, purge-DSN, `sources=` and `tools=` refusals and before any backend other than secrets. The Vault secrets kind signs in lazily (`secrets_vault.py:99`), so no network call precedes the refusal for it.
- **`sources=` / `tools=` truthiness:** still used at `app.py:114, 117`, but safe, because a falsy object is also dropped at use (`sources or {}`, `tools or {}`). Inconsistent with the new rule, not a hole.
- **Vault rule placement:** in the shared loader, so the default (`auth` omitted) and the written form are both caught; demo is unchanged; the message shape matches the ticket.
- **`hold_run_ids=`:** allowed and documented as the ticket requires.

## Not checked

- Any test run, mutation run or gate.
- Unchanged tests outside the snapshot, including the four negative tests and whether any test patches `hadavin_sdk.app.now`.
- `tools/mutation_runner.py` behaviour.
- The AWS and GCP kind modules' credential chains.
- Live Vault documentation for the `secret_id_ttl` default.
- `reviews/Q8/deps-audit.md` and the plan reviews.
- Whether `demo ` or `None` stage values can reach `build` other than through the test's `model_copy`.

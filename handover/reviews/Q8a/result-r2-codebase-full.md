<!-- full hand-back report of sub-agent ac32ad6b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review round 2, Q8a-1, head f6fad26f (codebase-details reviewer, read-only, nothing executed)

## Failures and gaps first

- **No evidence for this head.** `/home/user/hadavin-sdk/handover/evidence/Q8a-1/f6fad26/RESULTS.md` does not exist (nor does the directory). Every "passes" below is a reading, not a run. Unproven: the fail-before runs, the two Postgres positive tests, the four untouched negative tests, the mutant run, ruff, format, bandit and the guard tests.
- **Tests folder used for unchanged tests:** `/home/user/build/EV-P89-db0d9eb/tests`, because `/home/user/build/EV-P3a2-main-2a8c2aa/tests` does not exist. That tree is commit db0d9eb, not main 2a8c2aa, so it may differ from main.
- **Verdict:** no Blocker and no Major found by reading. 11 Minor findings and a few nits. The three round-1 Majors (M1, M2, M3) are addressed in the code as D-012 describes.

## Findings

**F1. Minor: a broken Vault check makes the killer tests read `VAULT_TOKEN` and try the network.**
- Where: `/home/user/build/snap/q8a1-f6fad26/tests/test_stage_names.py:335-355` (`_build_refusal`) and `:407-431`; also `tests/test_q8a_live_overrides.py` `test_a_build_refuses_a_static_vault_token_...`.
- Sequence: export `VAULT_TOKEN=x`, then run mutant M12b or M12g, or the fail-before run on main. The build constructs a real `VaultProvider`; `platform_secrets.check` calls `get("pg-dsn")`; `secrets_vault.connect` reads the token from the environment and sends an HTTPS request to `vault.example`.
- With `VAULT_TOKEN` unset the path is deterministic (`_env` raises `ConfigError`). With it set, the result depends on DNS or the proxy. `platform_secrets.py:60-63` wraps any failure as `ConfigError`, so the verdict stays "killed", but the run touches the network with a real token in hand.
- Fix: `monkeypatch.delenv("VAULT_TOKEN", raising=False)` (and `VAULT_SECRET_ID`) in `_build_refusal` and in `vault_dir`.

**F2. Minor: no mutant reverts the round-1 fix itself (type match back to kind names).**
- Where: `tests/stage_mutants.py:129-143`.
- M12f narrows the check to `VaultSettings`. A mutant `s.kind in {"vault", "vault_transit"} and s.auth == "token"` passes every killer in `test_stage_names.py`; only `test_a_new_kind_built_on_the_vault_settings_class_is_refused_too` (not run by the runner) would catch it.
- Three more new guards have no mutant either:
  - the position of the Vault check (moved after `make("secrets", ...)`); only `calls == []` in the q8a file catches it;
  - `s.auth == "token"` widened to `!= "kubernetes"`;
  - `_positive_number` and the two `is not None` tests for `sources=` and `tools=`.
- Fix: add M12h (kind-name revert) with a third-kind case in `test_pilot_and_prod_refuse_a_static_vault_token`, and one mutant for the check's position.

**F3. Minor: `runtime/tick.py` is a fourth place that decides "live", outside the class coverage.**
- Where: `src/hadavin_sdk/runtime/tick.py:344`; `tests/test_stage_names.py:296-323` (`_live_by_site`, "each of the three places"); mutants M9a-c.
- The killer test does cover non-stage values for the tick, so behaviour is tested. But there is no allowlist mutant (`app.config.environment in ("pilot", "prod")`) for tick.py.
- The older CHANGELOG entry in the same Unreleased section still lists only `deferred.py`, `registry.py`, `app.py` as the callers of `is_live`.
- Fix: add M9d for tick.py and name tick.py in that CHANGELOG sentence.

**F4. Minor: sibling of `now=` left open and undocumented: `run_tick(app, steps=...)`.**
- Where: `tick.py:337, 359`.
- Sequence: a pilot wrapper copied from `tests/test_p7_tick.py:132` calls `run_tick(app, steps=[...])` or `steps=[]`. The approval sweep and the evidence purge never run, so approvals do not expire and redaction maps are kept for ever.
- The docstring does not say whether `steps=` is a test keyword or a production hook. The CHANGELOG limit covers it only by the general "any route" sentence.
- A second route of the same kind is used by a test on a pilot app: `tick_mod.purge_evidence(TickContext(app, <any time>))` (`tests/test_k5_round8_postgres.py:58-59`).
- Fix: record a decision. Either refuse `steps=` when live, or say in the docstring that it is a production hook; add both routes to the listed limits.

**F5. Minor: "a new kind that signs in to Vault must be built on this class" is not enforced.**
- Where: `src/hadavin_sdk/backends/table.py:251-253`; `app.py:313-322`.
- Sequence: a new kind with its own `auth` / `token_env` fields that calls `secrets_vault.connect` (duck-typed) loads and builds in prod with a static token.
- Also, `app.py` now holds product-specific logic (`isinstance(s, VaultConnection)`) in the core wiring. The lock-in guard does not flag it, because "vault" is not in its patterns.
- Fix: a guard test that every `TABLE` settings class with an `auth` or `token_env` field subclasses `VaultConnection`. Or a neutral hook, for example `KindSettings.live_refusals() -> list[str]` overridden in `VaultConnection`, so `build` asks every backend and names no product.

**F6. Minor: the `timeout_s` message and CHANGELOG sentence are wrong for some numbers.**
- Where: `app.py:151-153, 325-329`; `CHANGELOG.md:8`.
- Inputs refused with "timeout_s= must be greater than 0" although they are numbers greater than 0: `Decimal("2.5")`, `fractions.Fraction(5, 2)`, `numpy.float32(2.5)`, `numpy.int64(3)`. (`numpy.float64(2.5)` is accepted, as a float subclass.) The CHANGELOG calls these "a value that is not a number".
- Inputs accepted that still break the executor: `5e-324` or `1e-9` (the socket times out at once), and `10**400` (passes the comparison, then `OverflowError` at the socket).
- All of this is demo only. Position is correct: after the live refusal, so pilot `timeout_s=0` gets the "is for tests" message (tested).
- Fix: message "timeout_s= must be an int or float greater than 0", the same wording in the CHANGELOG, and optionally an upper bound.

**F7. Minor: the fail-before run was made on a modified base (`VaultConnection = _VaultConnection`).**
- I could not read the evidence, so this is what the evidence must show.
- The alias adds no behaviour. Without it every test in `test_q8a_live_overrides.py` fails at import, which is a wrong-reason failure, so the alias is the more honest route.
- It does mean "fails on origin/main" is really "fails on origin/main plus one line". The evidence should include the alias diff and say so.
- `tests/test_stage_names.py` does not import the name. `test_pilot_and_prod_refuse_a_static_vault_token` and `test_pilot_and_prod_refuse_a_time_handed_to_the_tick` are therefore alias-free fail-before proofs on pristine main and should be pasted as such.
- On 464dee14 the "config still loads" tests fail at the bare `load_config(root)` line, not inside `pytest.raises`. That is the right reason for M1 but should be named.

**F8. Minor: TICKET.md now contradicts the code and has no erratum.**
- Where: `/home/user/build/snap/q8a1-f6fad26/TICKET.md` lines 8, 18, 24 and E3 (line 31).
- It still says: the rule lives in `Config._cross_checks`; "No change to the Vault connection code"; "assert with `load_config` only"; and the old message text without "(recommended)".
- D-012 records the decision, but it does not name the public rename `_VaultConnection` to `VaultConnection`. Its minors line has a hole: "sources=/tools= switched to , docstring order".
- Fix: add errata rev 4 pointing at D-012, name the rename, and repair the sentence.

**F9. Minor: `asked()` records less than a regression could change.**
- Where: `tests/test_k3_pilot_env.py:199-220`.
- It records `(capability, settings.kind, provider)` only, not the settings object and not the `available` keywords (`store=`, `signer=`, `anchor=`, `routes=`, `llm=`).
- A build that hands the purge store the unswapped DSN settings, or drops `store=` for the channel, stays green.
- `VAULT_CASES[capability]["kind"] in asked(...)[capability]` only proves the build reached that call, since the kind comes from the config the test wrote.
- `store=` takes a factory while every other capability takes an object, and `store=None` means "not planted" while `signer=None` plants None. Passing an instance fails loudly with `TypeError`.
- Fix: also record `settings` and `sorted(available)`; assert `dsn_secret_name == "pg-purge"` on the second store call in `test_k5_round8_postgres.py`.

**F10. Minor: `test_both_static_vault_tokens_are_named_in_one_refusal` does not pin the joined text.**
- Where: `tests/test_q8a_live_overrides.py` (the test after the non-stage Vault test).
- It checks two substrings only, so the `", "` join, the `environment pilot: refused: ` prefix and the order are not pinned.
- Fix: `match=exactly(...)` with the full two-item message.

**F11. Minor: `run_tick` with `now=` and an app-like object without `config` raises `AttributeError`.**
- Where: `tick.py:344`.
- With `now=None` the attribute is never read. With `now` given and `app.config` missing or None, the error is `AttributeError`, not `ConfigError`. That is fail-closed and no test in the EV-P89 tree does it (all 32 `run_tick(` calls use built demo apps).
- Fix: none needed; one docstring clause would do.

**Nits**
- `CHANGELOG.md:8`: "In demo an object that is falsy is now used as given ...; this also holds for a secret provider handed to `backends.factory.make`". The `factory.py:51` change applies in every stage (the command line's `gate`, `limits` and k1b call `make`).
- `CHANGELOG.md:10`: "stop in pilot and prod" also holds for any non-stage value.
- `app.py:313`: `_static_vault_tokens(backends)` has no type on its parameter.
- `app.py:155`: `dict(sources)` now also accepts an iterable of pairs.

## Checked line by line and found correct

**`_static_vault_tokens()` (`app.py:313-322`)**
- Iterates `backends.entries()` (`config.py:83-85` on main): every capability once, plus one item per detector in the tuple.
- `isinstance(s, VaultConnection)` short-circuits before `s.auth`, so settings without `auth` (including detector entries) cannot raise.
- `auth` is a `Literal` with default `"token"`, so the left-out form matches.
- Item text is `"{c}: {s.kind} auth token (the default; set auth: kubernetes (recommended) or auth: approle)"`, joined with `", "` under `environment {cfg.environment}: refused: `. For a None stage this reads "environment None: refused: ...", which is tested.

**Position in `build` (`app.py:120-125`)**
- `live` is at line 120; the Vault check at 121-123 comes before the first `make` at 125. Only `load_config`, `load_registry` and the `given` list precede it.
- The comment and docstring claim "before any backend is built" is true; the test's `calls == []` assertion can fail if the check moves.
- Order after it matches the docstring: restored-hash key (126), purge DSN (128), `sources=` (132), `tools=` (135), the six keywords (141), `timeout_s` value (151).
- `live = is_live(cfg.environment)` and `if live and given:` each occur once.

**`run_tick` (`tick.py:337-346`)**
- `live` comes from `app.config.environment` at call time, not from the build.
- The `now or clock()` to `is None` change is the only use of the parameter; a datetime is always truthy, so behaviour is unchanged.
- No test in the EV-P89 tree passes `now=` to a live app.

**`sources` / `tools`**
- All six sites are `is None` / `is not None` (`app.py:132, 135, 155, 183, 272, 307`); no truthiness test remains.
- No code path receives an empty mapping it did not get before: `{}` gave `{}` before and after. The only new input is a falsy mapping with entries, which is now used.
- New refusal of `sources={}` / `tools={}` when live: the only src caller is `cli.py:299` (`build(None, agents)`). No EV-P89 test passes an empty mapping to a live build.

**`VaultConnection` rename**
- `table.py:250, 272, 284, 294`, `app.py:28, 321`, tests and mutants are all updated.
- No `_VaultConnection` remains in the snapshot outside the round-1 reports, and none in the EV-P89 tests.
- `table.py` has no `__all__`.
- Lock-in guard: `_TABLE_VENDOR_NAME` (`test_lockin_guard.py:516`, EV-P89 copy) has no "vault", so neither the old nor the new name was ever in the skip set. No pinned name set mentions it.

**Removal from `Config._cross_checks`**
- `DIFF-vs-main.patch` has no `config.py` hunk, so the net change is zero: `_VAULT_KINDS`, the comment and the rule are gone.
- No snapshot test still expects the loader to refuse; the killer and the q8a tests assert that the loader accepts.

**cli.py**
- `load_config` only: `gate` (136, 146-164), `limits stop|reset`, `audit verify` (166-209), `migrate` (137-138, 312-346), `replay` and `score` (`_k1b`, 212-223). All of these call `make` directly.
- `build`: `tick` only (`_tick`, 280-309), which prints "tick: config error: ..." and exits 2 on the refusal.
- The CHANGELOG lists match.

**Tests**
- Every new test can fail.
- Exact matches use `"^" + re.escape + "$"`; the remaining unanchored ones (`"plain callables"`, `re.escape("sources= is for tests")`) are adequate.
- No order dependence found: `TABLE` entries, `_reading_channel.seen`, `HADAVIN_CONFIG_DIR` and the `make` patches all go through `monkeypatch`. Repeated `plant_test_backends` calls stack and unwind, and each wrapper calls the real factory.
- No real Vault, and no network in the passing path. Wall-clock use is benign: a date 500 days ahead, and `run_tick(app)` on the real clock with no time-sensitive assertion.
- The kill-switch test runs the real `cli_mod._main(["limits", action, "--by", "ops"])`, not a stub: real `load_config`, `load_registry`, `platform_secrets.check`, chain audit, `Limits` and `kill_switch`. Only secrets, store, signer and anchor are planted. It asserts `("secrets", "vault", None) in calls`, and then that `app.build` refuses the same config.

**Mutants M12a-g, M13a-b**
- Each `old` string occurs exactly once in its head file (`app.py:141, 321, 118, 115, 116, 321, 121`; `tick.py:344`).
- Each killer's first failure carries the `expect` text:
  - M12c fails only at the falsy assertion.
  - M12f fails first at pilot/signer.
  - M12g fails first at pilot/secrets.
  - M13b fails at the `raise AssertionError("demo refused ...")` line.
- No killer passes under its mutant.

**Suppressions**
- No `noqa`, `nosec`, `type: ignore`, `pragma: no cover` or `NOSONAR` is added anywhere in the whole-branch diff. The one `noqa: BLE001` added in round 1 (`test_stage_names.py`) is removed by this fix.

**CHANGELOG**
- Sentence by sentence against the code, everything matches except the items in F3, F6 and the nits: messages, order, the `clock` default, the `run_tick` text, the empty-mapping change, `role` / `role_id`, and the covered and not-covered command lists.

## Not checked

- No test, mutant, lint, format or bandit run.
- `docs/`, `demos/`, README and `.github` for `_VaultConnection`, Vault config examples with `auth` left out, or `run_tick(now=)` / `build(clock=)` callers; they are outside the allowed read set.
- `tools/mutation_runner.py` (exactly-once and first-failing-line rules are taken from the `stage_mutants.py` docstring).
- Whether chain audit builds with `signer=None` / `anchor=None` on `MemoryStore` in prod, and whether `Limits.reset` succeeds on a never-stopped switch; both are needed by the new tests.
- `load_registry` side effects before the Vault check.
- `tests/test_repo_rules.py` import rules for the two new imports in `runtime/tick.py` (`errors`, `stages`; both look like leaf modules).
- The stage-word scanner (`POSITIONS`) against the new test text.
- `k1b/audit_sink.py` beyond the grep showing it calls `make`, not `build`.
- The ledger, for the owner questions D-012 says were logged.

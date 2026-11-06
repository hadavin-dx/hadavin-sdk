# Package ticket P6a: the client-profile check, in two pull requests. P6a-1: a pilot or production app cannot start with test objects handed in by code, and a dev config that names a real model must say it holds only made-up data. P6a-2: a CI test catches code in `src/` that reaches the model by a side door. DRAFT revision 3

**Revision line.** DRAFT revision 3, written 2026-11-06 from about 03:30 UTC (09:00 IST; IST = UTC+5:30) by a ticket-author agent, under lead order 20 item 6 (ticket only: no code, no pull request, no suite run, no sub-agent). It applies every decision of `handover/reviews/P6a-round2-resolve.md`: 22 decision rows over 27 finding ids (R2-ADV-1 to 14, R2-COR-1 to 12, and the resolve's own Major N4), plus the 5 order-22 rows of that resolve. It also carries three corrections I found while re-reading (CHANGELOG, N5 to N7). Revision 2 was written 2026-11-06 at about 03:00 UTC (08:30 IST). **This revision is the input of ticket review round 3**, the last ticket round: two fresh reviewers (correctness and adversarial), then one resolve. Cap (order 20 item 6): 3 ticket rounds counting from round 1. The "one more round" exception there covers money and redaction packages only, not security.

Plan row: plan-v3 section 6, row P6a, step S4. Split by lead order 22 item 24.

**Where the cites come from.** I re-read every `file:line` cite below myself in this session, in the checkout under `src/` and `tests/` and in `handover/tickets/`. The disk tree is core commit ce70eb5 plus later edits. The resolve reports, and I did not re-run, that `git diff --stat 124258b 397ec97 -- src tests` names no file this ticket cites, and that `tools.py:389` and `:407` read the same at `397ec97` (origin/main as P5c revision 2 reports it). So the cites hold at `397ec97` as far as the resolve checked. Anything I did not read is marked UNVERIFIED. "PENDING LEAD" means my recommendation, taken and acted on, which the lead may overrule (list at the end).

**Path class: SECURITY.** This package decides whether a client deployment can start with a test-only part, and whether a dev config may send text to a real model. Extended review: yes, Tier A (plan rule 3 names "client-profile gates"). Ticket review: the cap above. Result review of the built code: two fresh reviewers per round (correctness and adversarial) and the two-clean-rounds stop rule (plan rule 4; order 16 keeps it for built code).

**Scope rule (orders 7(3) and 8(1)):** where a finding can be closed by deleting surface instead of adding design, it is deleted. This revision deletes T2 (d), T2 (d2), T5 (a), T5 (d), T5 (e), T6 (f), the first-statement keyword record, the helper `make_llm_callers`, and the instruction to change P5c's T3-07. Each cut has its reason in the CHANGELOG. The one new design (S6) is ordered by the lead (order 22 item 28(b)).

## Words used in this ticket (one meaning each)
- **client profile**: a configuration whose `environment` is `pilot` or `prod`. `Config.environment` is `Literal["dev", "pilot", "prod"]` (`config.py:317`) and `deferred.LIVE = ("pilot", "prod")` (`deferred.py:33`). "Live" means the same thing. P6a adds no new profile object.
- **dev-only kind**: a `(capability, kind)` pair in `DEV_ONLY` (`backends/table.py:593-602`): `llm/fake`, `channel/fake`, `secrets/fake`, `secrets/env`, `store/memory`, `audit/local_dir`.
- **pair**: one `(capability, kind)` entry of `TABLE` (`backends/table.py:386`). Settings never make extra pairs: `llm/fake` with `recorded_dir` is still the one pair `llm/fake`.
- **masking wrapper**: the object P5c builds that masks text before the model sees it: `MaskedLLM` in `llm/masked.py` (`tickets/P5c.md:67`, `:161`, `:214-215`).
- **test double**: an object a test passes into `app.build` in place of a configured part (`ScriptedLLM`, `FakeChannel`, a spy secrets provider, a fixed clock).
- **build keyword**: any keyword-only parameter of `app.build`: today `secrets`, `channel`, `detector`, `llm`, `tools`, `sources`, `hold_run_ids`, `clock`, `timeout_s` (`app.py:62-75`), plus any added later.
- **live hook**: a build keyword that a production operator needs and that replaces no configured part: `hold_run_ids` (the purge hold, `runtime/tick.py:189-208`, held at `runtime/agent_loop.py:175-178`) and `timeout_s` (feeds only the executor, which is `None` when live, `app.py:172-174`). They are listed in one tuple `_LIVE_HOOKS`.
- **made-up data only**: a dev config that says, in the new field `made_up_data_only: true`, that every input it will see is made up. It is the operator's own word, not something the code can check.
- **model-call site**: in `src/`, a read of the attribute `chat` or `apply_guardrail` (a call or not), or a call of `getattr`, `operator.attrgetter` or `operator.methodcaller` whose name argument is one of those two names written as a string constant. It is NOT every possible way to reach the model (limits under Security notes (c)). A `.chat` read on an object that is not a model (for example a chat client of a messaging service) is a false alarm, not a hole: it is fixed by adding the site to the reviewed set with a reason.
- **PL61**: P4a's pending-lead item 61, confirmed by order 16 item 3: k1b replay is dev-only in v1.
- **pin (test row)**: a row that already passes on the base, because main already behaves that way. It guards against a later regression; it is not a fail-before row.
- **base**: the commit just before the sub-package, on which the fail-before runs.

## What is already true on main (read in code)
1. **Dev-only kinds are already refused outside dev.** `Config._cross_checks` (`config.py:350`) builds one refusal list `refused` (`:365`). When `self.environment != "dev"` it holds every `(capability, kind)` of `self.backends.entries()` that is in `DEV_ONLY` (`:366-369`) and `allow_insecure_loopback` (`:370`). It then adds the anchor rules (`:371`; `_anchor_refusals` at `:377`, which in prod adds the `NOT_PROD` pairs at `:392`). It raises ONE `ValueError` with `', '.join(refused)` (`:372-373`). `load_config` turns it into `ConfigError` (`config.py:453-454`). Capabilities left out of a config get `DEFAULTS` (`table.py:582-589`), and those defaults are refused the same way, because `entries()` lists every capability (`config.py:74-76`).
2. **That check is pinned by a test.** `tests/test_p1b_backends.py:89-102` runs in pilot and prod and asserts one error holding `llm: fake`, `store: memory`, `audit: local_dir`, `secrets: fake`, `channel: fake` and `allow_insecure_loopback`. It does NOT cover `secrets: env`. PL61's `llm: fake` row is that test.
3. **The llm kind has no default.** `Backends.llm` has no default (`config.py:70`) and `DEFAULTS` has no `llm` entry. P5c revision 2 adds the `redactor` capability (default `regex`, no `DEV_ONLY` pair, `tickets/P5c.md:66`, `:259`) and pins "pilot and prod must name the redactor" with T1-12 (`:378`). P5c-3 makes `app.py:162` and `build(llm=raw)` wrap the model with `MaskedLLM.of` (`:282`); its mutant M30 "`app.build(llm=raw)` not wrapped" is killed by T3-06 and T3-01 (`:509`).
4. **The hole on main: `app.build` takes test doubles in a client profile.** `app.build` accepts the build keywords (`app.py:62-75`) and uses `secrets`, `llm`, `detector` and `channel` in place of the configured kinds (`:82`, `:162`, `:163-169`, `:170`). `hold_run_ids` goes to the hooks (`:225`) and `clock` to `Approvals` (`:182`). In pilot and prod `build` refuses only `sources=` (`:90-92`) and `tools=` (`:93-98`). So a pilot app can run with a `FakeChannel` and a scripted model while its config names a real channel and a real model. The repository's own test does this: `tests/test_k3_pilot_env.py:185`. The only `src/` caller of `build` is `cli.py:299` (`build(None, agents)`, no keywords). `demos/` has no call of `app.build`.
5. **Order inside `build`.** `cfg = load_config(config_dir)` is `app.py:79`, then `load_registry` (`:80`). `secrets = secrets or make("secrets", b.secrets)` at `:82` REBINDS `secrets`, then `live` is computed (`:83`). Then the evidence-key check (`:84-85`), the purge-DSN check (`:86-89`), `sources=` (`:90-92`), `tools=` (`:93-98`), `platform_secrets.check` (`:122`), then `make("signer")` (`:144`) and the store (`:146`). `app.py` imports `make` at `:28` and `platform_secrets` at `:27` as module names, so a test can monkeypatch both.
6. **Revision 2's live-build rows fail for the wrong reason (N4).** `pilot_cfg` sets `secrets: {kind: mounted_file, dir: secrets}` (`tests/test_k3_pilot_env.py:53`) and creates only `actions`, `prompts`, `golden`, `inputs` (`:38-39`). Relative paths are relative to the config folder (`config.py:112`). `secrets_file.build` raises `ConfigError("secrets mounted_file: ... is not a folder")` when the folder is missing (`actions/secrets_file.py:69-71`), and `app.py:82` builds it before revision 2's check. So every revision-2 T5 row that passed no `secrets=` raised that error first. Revision 3 places the check before `:82` and patches `app.make` (S2 and the fixture below).
7. **Vault secrets construction does no network call** (`actions/secrets_vault.py:162-195`: the login is a closure called later). It does read the CA file (`ssl.create_default_context(cafile=...)`, `:186`), a local file read. With the check before `:82`, that read no longer happens before a refusal.
8. **Existing model-call scan is call-only.** `tests/test_k5_producers.py:22` sets `SINK_METHODS = {"chat", "apply_guardrail"}`. `_sink_callers` (`:78-95`) scans the roots `(ROOT, "")` and `(REPO / "demos", "demos/")` (`:80`), skips `llm/` (`:86`), and counts a module only for an `ast.Call` whose function is an `ast.Attribute` with that name (`:89-94`). `getattr(llm, "chat")(...)`, `f = llm.chat; f(...)` and `functools.partial(llm.chat)` are not counted. P5c revision 2 has no other call-site scanner: its cut 8 removed "the second module list of T3-07" (`tickets/P5c.md:32`), and T3-07 now has parts (b), (c), (d) only (`:426`).
9. **What an AST walk finds today** (revision 2's read-only walk, `python3 -I`, over `src/hadavin_sdk`; both round-2 reviewers recounted it):
   - Model-call sites outside `llm/`, as `(module, enclosing function)`: `evals.py` `gate`, `extract.py` `extract`, `guard/bedrock_guardrail.py` `GuardrailDetector.check` (the only `apply_guardrail`), `guard/judge.py` `JudgeDetector.check`, `k1b/loop.py` `_chat_bounded.work`, `runtime/agent_loop.py` `Runtime.handle`. `MODEL_CALLERS` (`guard/producers.py:55-65`) lists the same six modules plus `demos/ask-your-data/askdata/pipeline.py`. These are TODAY's sites; P6a-2's base is after P5c-3, which may move some (T6 (a)).
   - Calls of `make` with first argument `"llm"`: `app.py:162`, `cli.py:150`, `cli.py:221`.
   - Calls of `getattr` with a NON-constant name: 12 call sites in 11 functions (listed in T6 (g)). No `attrgetter` or `methodcaller` in `src/`.
   - `exec(` appears once in `src/hadavin_sdk`: `tools.py:389`, the loader of pinned tool-module bytes (grep this session).
10. **`TABLE` today** (AST of `backends/table.py`, `python3 -I`, this session): 8 capabilities, 31 pairs. `secrets` 7, `signer` 6, `anchor` 4, `store` 2, `audit` 2, `llm` 5, `detector` 3, `channel` 2. `DEV_ONLY` holds 6, so 25 pairs need a `CLIENT_REVIEWED` line.
11. **A new `Config` field does not move qualification hashes.** `Registry.config_hash` (`registry.py:131-155`) hashes named keys only. `Config` forbids unknown keys (`_Strict`, `config.py:52`, `extra="forbid"`), so on the base a config with `made_up_data_only` fails to load.
12. **Live builds with doubles in today's tests** (read by hand, a floor): `tests/test_k3_pilot_env.py:185` and `tests/test_k5_round8_postgres.py:40` (both Postgres-gated: `pg_schema()` skips without `HADAVIN_TEST_PG_DSN`, `tests/contracts/kinds/store_postgres.py:22-24`; round8 also has its own skip at `:22-23`); `tests/test_k5_round5.py:226` (passes `secrets=` and `tools=`), `tests/test_k5_round9b.py:370` and `tests/test_k5_round10.py:80` (pass `secrets=` and `llm=`). With the check before `:82`, all 5 need `allow_test_doubles=True`. Test files outside `test_k3*`/`test_k5*` that call `build(` are UNVERIFIED; the recount script covers them.
13. **Dev configs with a real llm kind in today's tests** (grep, a floor): `tests/test_p5_llm.py:38-46`, `tests/test_p5p6_followups.py:82` and `:392`. `tests/test_p1a_fixes.py:117` uses `model_copy`, which skips validators, so it is not affected (UNVERIFIED by run). `tests/fixtures/config/config.yaml:13` uses `llm: {kind: fake, ...}`. No demo YAML holds an `environment` key (grep, resolve).

## What P6a does
### P6a-1 (lands early: after P4c-2 on `app.py`, before P5c-3)
- **S1. Make the dev-only list complete, and pin the one pair no test covers.** No code change for the config path (item 1). Rows: `secrets/env` refused in pilot and prod, a pilot config that omits `store` is refused (default `memory`), and a completeness check: every pair of `TABLE` is in exactly one of `DEV_ONLY` and a test-local list `CLIENT_REVIEWED`, each `CLIENT_REVIEWED` entry with a one-line reason. A pair added later with no decision fails CI. `CLIENT_REVIEWED` today (25 pairs; the builder writes one reason per line):
  - `secrets`: `aws_secrets_manager`, `vault`, `azure_key_vault`, `gcp_secret_manager`, `mounted_file`;
  - `signer`: `none`, `ed25519_local`, `aws_kms`, `azure_key_vault_key`, `gcp_kms`, `vault_transit`;
  - `anchor`: `none`, `s3_object_lock`, `azure_immutable_blob`, `gcs_retention_lock`;
  - `store`: `postgres`; `audit`: `chain`;
  - `llm`: `anthropic`, `bedrock`, `openai_compat`, `gemini`;
  - `detector`: `regex`, `llm_judge`, `bedrock_guardrail`; `channel`: `slack`.
  - Rule for `NOT_PROD` (`table.py:604`): `signer/none` and `anchor/none` go in `CLIENT_REVIEWED` with the reason "allowed in pilot, refused in prod by `NOT_PROD`".
  - A later package that adds a pair adds it to one of the two sets in its own diff (relays). `CLIENT_REVIEWED` is not a copy of `NULL_KINDS`/`EXCEPTIONS` in `tests/test_lockin_guard.py`: those answer "does each capability have a neutral non-dev kind" (`coverage_problems`, `:406-430`); this list answers "is each pair decided for client use".
- **S2. One rule for the build keywords in a client profile.**
  - In a live profile, `app.build` refuses every build keyword whose value `is not` its signature default, unless the caller also passes `allow_test_doubles=True`.
  - The names come from `inspect.signature(build)`, minus `allow_test_doubles`, `sources` and `tools` (they keep their own refusals), and minus `_LIVE_HOOKS = ("hold_run_ids", "timeout_s")`. So today the rule covers `secrets`, `channel`, `detector`, `llm` and `clock`. A keyword added later is refused by default (fail closed) until a reviewed change adds it to `_LIVE_HOOKS` (PENDING LEAD 13).
  - **Where it runs:** right after `cfg = load_config(config_dir)` (`app.py:79`), before `load_registry` and before `secrets = secrets or make(...)` (`:82`). `live` needs only `cfg`. So no backend is built before a refusal: no secrets provider, no Vault client, no CA file read, no `mounted_file` folder check. The given keyword values are read directly, because nothing has rebound them yet.
  - The new check now runs BEFORE the `sources=` and `tools=` checks. Those two keep their messages because they are not in the rule. A call that passes `sources=` or `tools=` together with a refused keyword gets the new message first.
  - **Honest limit, in plain words: this is an accident guard (a named switch), not a boundary.** Code that builds the app in Python is the operator's own code. It can pass the switch, change the app after `build` (for example `app.runtime.hooks.hold_run_ids = ...`, as `tests/test_k5_tools.py:756` does in a test), or build `Runtime` directly. S2 stops a test fixture or a copied snippet from reaching a pilot by accident. It does not stop an operator who means to do it.
- **S6. A dev config that names a real model must say it holds only made-up data (order 22 items 28(b) and 31 option b; PENDING LEAD 14 = NEEDS LEAD 50, pending; I proceed on the recommendation).**
  - A config is taken to hold client data unless it says otherwise. Pilot and prod always hold client data (and already need P6b1's no-training statement).
  - New `Config` field `made_up_data_only: bool = False`.
  - In `Config._cross_checks`, when `environment == "dev"` and `made_up_data_only` is not `true`, each of these is added to the existing `refused` list: the `llm` kind, when it is not in `DEV_ONLY` (as `llm: <kind>`); and each `detector` of kind `bedrock_guardrail` (as `detector: bedrock_guardrail`; it sends text to a vendor service outside the llm kind). An `llm_judge` detector uses the llm kind, so the llm item covers it.
  - The one `ValueError` of `config.py:372-373` stays the only error. When any S6 item is in the list, the message ends with one sentence: "a dev config that names a real model or a vendor detector sends text out: set made_up_data_only: true only when every input is made up; client data runs only in pilot or prod".
  - Because it sits in `Config`, it runs at build (`app.py:79`) AND on the two command-line paths that build a model without `app.build`: `hadavin gate` (`cli.py:150`) and `replay`/`score` (`cli.py:221`).
  - In pilot and prod the field has no effect (stated; T0 and T5 (m) are the rows that would break if it had one).
  - The check does not look at the model's address: a real llm kind pointed at a model on the developer's own machine (for example `openai_compat` on loopback) is refused in dev without the field too. This is on purpose (no address rule to review).
  - Honest limit (Security notes (g), owner-visible): the field is the operator's own word. A dev config with client data and `made_up_data_only: true` is not refused. The rule turns a silent default into a false statement written in the config file.

### P6a-2 (after P5c, all four PRs; must not merge before P5c, order 22 item 24)
- **S4. One model-call scanner.** A test helper finds every model-call site and reports `(module, enclosing function)`. `test_k5_producers._sink_callers` switches to it. By fact, P5c revision 2 has no other call-site scanner, so the repository then has one. P6a-2's rows assert that:
  - the sites outside `llm/` are EXACTLY the set the builder finds at P6a-2's base and writes down, naming for each difference from today's six (item 9) the P5c-3 hunk that caused it;
  - `apply_guardrail` appears only in `guard/bedrock_guardrail.py`;
  - every non-constant `getattr`/`attrgetter`/`methodcaller` sits in a reviewed list.

  Scope is `src/` for these rows, as the plan row says. `demos/` stays in `_sink_callers`, so the registry check keeps covering the demo. Whether the demo pipeline imports a raw llm kind module is P5c's T3-07 (d) (an import-graph question), not P6a's (a call-site question); they share no scanner.

### Cut
S3 (redactor-named refusal; P5c T1-12 builds it), S5 (strict Unicode pin; order 22 item 24: warning only in v1, V6), a per-`Entry` `dev_only` field (V1), scanning `demos/` with the wrapper test (V2), a signed audit record of the profile (V3), a named profile object (V5), revision 2's T2 (d)/(d2) redactor-suite rows (P5c cut that suite), T5 (a), (d), (e), T6 (f).

## Template fields, in the template's order

- **Package id and name:** P6a, client-profile check, two pull requests: **P6a-1** (S1, S2, S6; rows T0, T1, T2, T5, T7; 42 rows, 35 mutants) and **P6a-2** (S4; rows T6; 13 rows, 10 mutants).
- **Path class:** security. Extended review: yes, Tier A (header).
- **Depends on (merged first):**
  - **P6a-1:** the merge chain of order 20 item 4 (P1m, P1a, P1b, P3a and the P4d chain, P2a-1, P2d-1, P2d-2, P4a); P4c-2 (it edits `app.py` before P6a-1, `tickets/P4c.md:40`, `:307`); P4b1 and P4b2 only as text (P4b1 says "P6a refuses it in a client profile" for the memory store, `tickets/P4b1.md:107`; P4b2 says the same at `tickets/P4b2.md:255`; both are already true by item 1). P6a-1 does NOT depend on P5c, P6b1 or P6b2.
  - **P6a-2:** P5c, all four PRs (T1-12 green at its base, P5c-3's T3-17 edit of `tests/test_k5_producers.py`, `tickets/P5c.md:289`, `:437`), and P6a-1. It must not merge before P5c (order 22 item 24).
  - A9 F6's "P6a depends on P6b1, P6b2, P4b1, P5c" reads, after the split: "P6a-2 depends on P5c; P6a-1 depends on the order-20 chain, P4b1/P4b2 text and P4c-2". The lead records this as an amendment (lead's step).
  - Ticket states, as read today (each file's own revision line): P1 revision 16 FROZEN; P2a revision 10 FROZEN; P4a revision 12 FROZEN; P4b1 revision 3; P4b2 revision 4; P4c revision 3; P5b1 revision 2; P5b2 revision 3; P5b3 revision 1; P5b4 revision 2; P5b5 revision 2; P5c revision 2; P6b1 revision 3; P6b2 revision 2. The non-frozen ones are drafts, so P6a "depends on" those revisions, not on clean ones.
  - **Hot files** (rule 10, A4, A9 F6):
    - `app.py`: P2a-1, P4b2-b (`tickets/P4b2.md:228`), P4c-2, **P6a-1**, P5c-3 (`tickets/P5c.md:282`), P6b2-a (its N11 refusal of `migrate_credential_ref`, `tickets/P6b2.md:139`, accepted by order 22 item 25). P6a-2 does not edit `app.py`. P6b1 does not (`tickets/P6b1.md:251`).
    - `config.py`: **P6a-1 early** (one field, one check in `_cross_checks`); P4b1, P5b3, P5c, P6b1, P6b2 rebase on it. Today's P6b2 text (`tickets/P6b2.md:138`) says "P6a is last on `config.py`"; relay below.
    - `tests/test_k5_producers.py`: P5c-3 (T3-17), then **P6a-2**.
    - `tests/test_k3_pilot_env.py`: **P6a-1** owns the `:185` edit. That P5c-3 does not also edit it is UNVERIFIED: P5c's grep pattern `\b(Runtime|gate|extract|JudgeDetector)\(` does not match `app_mod.build(`, and P5c-3 wraps `build(llm=raw)` itself, but its list is a floor.
    - `CHANGELOG.md`: append only. `defaults.py`: no constant (order 20 item 5).
    - `cli.py`, `backends/table.py`, `tests/test_lockin_guard.py`: P6a takes no slot.
  - Merge position: P6a-1 early (above); P6a-2 after P5c, before P8a (plan section 7 step 7).
- **Problem in plain words:** A client deployment must never run with a part that exists only for testing: a fake model, a fake approval channel, secrets read from the environment, an in-memory store, a frozen clock. The configuration check for test-only kinds already exists and is tested. But a program that builds the app in Python can still hand in test objects in a pilot or production configuration, and nothing stops it. P6a-1 adds a refusal for that case, as a guard against accidents (a copied test fixture), not as a lock against the operator's own code. Second, a config labelled `dev` can today send real text to a real model. P6a-1 refuses that unless the config says, in one field, that it holds only made-up data. The field is the operator's word, not a lock. P6a-2 replaces the test that looks for code in `src/` calling the model directly, so that alias forms like `getattr(llm, "chat")` are found too. The real lock on the model path is P5c's: the core only accepts the masking wrapper.
- **Source of the code and what is NOT taken:** nothing is promoted from another repository. Design sources: plan-v3 row P6a, rule 9(g), note 6; A6, A9 F6; order 22 items 24, 28, 31; P5c revision 2; memo-6. NOT taken: plan-v2's per-kind flag list; any change to `DEV_ONLY`'s members; a new profile object; a claim that the executor is a kind (A6); a WARNING log line, an `app.test_doubles` attribute and a `cli` refusal for S2 (`cli.py:299` passes no keyword, so a `cli` refusal could never fire); a renamed switch (PENDING LEAD 13 (b)); an address rule for "local" models in S6.
- **Target module and path in `src/hadavin_sdk/`:** `app.py` (S2) and `config.py` (S6), both in P6a-1. Everything else is in `tests/`.
- **Interface (names, argument and return types, errors):**
  - `app.build(config_dir, agents, *, secrets=..., ..., timeout_s=None, allow_test_doubles: bool = False) -> App`: a new keyword-only argument, default `False`.
  - `app._LIVE_HOOKS: tuple[str, ...] = ("hold_run_ids", "timeout_s")`, module level.
  - Private pure helper `app._test_doubles_given(params: Mapping[str, inspect.Parameter], given: Mapping[str, object]) -> list[str]`. It returns, in `params` order, every keyword-only name except `allow_test_doubles`, `sources`, `tools` and the names in `_LIVE_HOOKS`, whose value in `given` `is not` that parameter's default. It compares by identity, never by truth value. `build` calls it with `inspect.signature(build).parameters` (computed once at module level) and its own keyword values.
  - **What it raises.** When `live` and not `allow_test_doubles` and the list is non-empty: `ConfigError(f"{names} replace configured parts and are for tests; in pilot and prod pass allow_test_doubles=True only from a test")`, where `names` is every listed keyword as `name=`, joined by `", "`, all at once. In dev `allow_test_doubles` has no effect.
  - `Config.made_up_data_only: bool = False` (`config.py`, P6a-1). The S6 items join the existing `refused` list; one `ValueError`, turned into `ConfigError` by `load_config` as today.
  - Test helper `tests/_model_calls.py` (P6a-2): `model_call_sites(roots: list[tuple[Path, str]]) -> set[tuple[str, str]]` returns `(prefix + module path relative to its root as posix, dotted enclosing function or "<module>")` for every model-call site. Aliases of `attrgetter`/`methodcaller` are resolved within the module (`from operator import attrgetter as g`). A syntax error in a scanned file fails the scan, never skips it. Sibling `dynamic_attr_sites(roots)` returns the same tuple shape for calls of `getattr`/`attrgetter`/`methodcaller` whose name argument is not a constant. Pure function `unexpected_sites(found: set[tuple[str, str]], allowed: set[tuple[str, str]]) -> set[tuple[str, str]]` returns `found - allowed`, compared as full `(module, function)` pairs; T6 (a), (b) and the planted rows use it as the oracle.
  - `_sink_callers` becomes `{m for m, _ in model_call_sites([(ROOT, ""), (REPO / "demos", "demos/")]) if not m.startswith("llm/")}`. It keeps its signature (no argument) and the demos root.
- **Neutral default / working alternative:** not a kind. Default behaviour: refuse. There is no alternative to write. The outline for a different profile mechanism (a named profile object) is V5.
- **Files to create, change, delete (each with the reason):**
  - **P6a-1:**
    - Create `tests/test_client_profile.py`: rows T0, T1, T2, T5, T7 (the plan section 9 test file). **Import rule (R2-ADV-1):** module-level imports name only things that exist on P6a-1's base: the `app` module, `ConfigError`, `load_config`, `pilot_cfg`, `ScriptedLLM`, `FakeChannel`, `TABLE`, `DEV_ONLY`. Names that exist only after P6a-1 (`_test_doubles_given`, `_LIVE_HOOKS`) are read inside the row body with `getattr(app_mod, "<name>")`, so on the base that row fails alone. The keyword `allow_test_doubles=` and the config key `made_up_data_only` appear only inside row bodies. No P5c name is used.
    - Change `src/hadavin_sdk/app.py`: `import inspect`; `_LIVE_HOOKS`; `_test_doubles_given`; the new keyword; the check right after `:79` (S2). The docstring line "The keyword overrides replace one configured backend (tests)" (`app.py:76-77`) gains "and, except the live hooks, are refused in pilot and prod unless allow_test_doubles=True".
    - Change `src/hadavin_sdk/config.py`: the field `made_up_data_only` and the S6 items in `_cross_checks` (S6).
    - Change 5 tests to pass `allow_test_doubles=True` (item 12): `tests/test_k3_pilot_env.py:185`, `tests/test_k5_round8_postgres.py:40`, `tests/test_k5_round5.py:226`, `tests/test_k5_round9b.py:370`, `tests/test_k5_round10.py:80`. Each of the last three then still reaches its own refusal, so each pins "the switch lets the build through" with no Postgres.
    - Change at least 3 dev test configs to set `made_up_data_only: true` (item 13): `tests/test_p5_llm.py:38-46`, `tests/test_p5p6_followups.py:82`, `:392`. Final list by the recount script. Never by loosening a check.
    - Change `CHANGELOG.md`: one entry. Two behaviour changes: (1) a live build that passes `secrets=`, `channel=`, `detector=`, `llm=` or `clock=` needs `allow_test_doubles=True`; (2) a dev config that names a real llm kind or the `bedrock_guardrail` detector needs `made_up_data_only: true`. Also the two plain-words limits (S2, S6).
  - **P6a-2:**
    - Create `tests/_model_calls.py`: the one scanner (S4).
    - Append rows T6 to `tests/test_client_profile.py` (they may import `tests._model_calls` at module level; P6a-2's rows are not copied to a base).
    - Change `tests/test_k5_producers.py`: `_sink_callers` (`:78-95`) uses `model_call_sites`, rebased on P5c-3's T3-17 edit.
    - Change `CHANGELOG.md`: one entry (the alias-proof scan).
- **Existing core code reused (what I checked):**
  - Reused: `Config._cross_checks` and `_anchor_refusals` (`config.py:350-397`); `DEV_ONLY`, `NOT_PROD`, `DEFAULTS`, `TABLE` (`backends/table.py:593`, `:604`, `:582`, `:386`); `deferred.LIVE` (`deferred.py:33`); the `sources=`/`tools=` refusal pattern (`app.py:90-98`); `tests/test_p1b_backends.py:89-102` (pin and mutant killer); `pilot_cfg` (`tests/test_k3_pilot_env.py:35`), already imported by other tests as `from tests.test_k3_pilot_env import pilot_cfg` (`tests/test_k5_round5.py:222`); `SINK_METHODS`/`_sink_callers` (`tests/test_k5_producers.py:22`, `:78-95`) and `MODEL_CALLERS` (`guard/producers.py:55-65`).
  - Checked and not duplicated: `coverage_problems` (`tests/test_lockin_guard.py:406-430`; a different question, S1).
  - Checked and not needed: `hashing.py`, `k1b/atomic.py`, `k1b/redaction.py`, `stats.py`, `evals.py`, `store/memory.py`, the suites in `tests/contracts/`. Contract suite for P6a: none (not a kind).
  - **`prod_cfg` fixture**, test-local: `pilot_cfg(tmp_path, env="prod")`, then edit its `config.yaml` so that `backends.signer` = `{kind: ed25519_local, private_key_secret_name: audit-key}` and `backends.anchor` = `{kind: s3_object_lock, bucket: <made-up bucket>, region: <made-up region>, retention_ack: true}`. The audit kind is already `chain` (`tests/test_k3_pilot_env.py:59`), which the anchor needs (`config.py:383-384`). The builder fills the placeholders with obviously made-up words. Row T0 proves it loads. NOT run-checked by me.
  - **`made` fixture (R2-ADV-7), test-local, used by every T5 row in pilot or prod:** it monkeypatches `app.make` (module name, `app.py:28`) with a function that appends the capability to a list `record`; for `"secrets"` it returns a made-up secrets provider that answers every secret name with a made-up value built from parts (never a key-like literal), so `platform_secrets.check` (`app.py:122`) passes; for any other capability it raises a test-local exception `_Reached` (not a `ConfigError`). So no row, on the base or on P6a-1, builds a signer, a store or a channel, and none touches a network, a folder of secrets or Postgres. Rows that expect a refusal use `pytest.raises(ConfigError, match="allow_test_doubles")`, so `_Reached` on the base is a FAIL by assertion. Rows that expect "the check lets the build through" assert `_Reached` is raised and `record` starts with `"secrets"`.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):** P6a adds no role, grant, credential, network call or secret read. All checks run in the process at start-up, and no backend is built before an S2 refusal. It changes no member of `DEV_ONLY`. Refusal messages name keywords and kind names only, never a value. What P6a does NOT give, in plain words:
  - (a) It checks configuration and the `app.build` arguments. A client's own code that calls a model directly, outside `app.build` and outside `src/`, is not checked.
  - (b) `allow_test_doubles=True` is a named switch, not a lock. A client's code can pass it. The T5 (g) row keeps it out of `src/` and `demos/` only, and the T5 (g) tripwire does not follow an aliased `build` (`b = app.build; b(**opts)`, `getattr(app, "build")`).
  - (b') Code can change the app after `build` (for example replace `app.runtime.hooks.hold_run_ids`) or build `Runtime` itself. P6a does not see that. P5c-3's `isinstance` check in `Runtime.__init__` still refuses a raw model there (`tickets/P5c.md:425`).
  - (b'') `hold_run_ids=` and `timeout_s=` are accepted in pilot and prod without the switch (`_LIVE_HOOKS`). `hold_run_ids` decides which runs keep their tool calls and redaction maps past the ordinary purge, up to the 400-day ceilings (`runtime/tick.py:189-208`); it replaces no configured part.
  - (c) The scanner finds the two attribute names and the constant-name forms only. A name built at run time is not followed (`getattr(llm, "ch" + "at")`, a variable); instead every non-constant `getattr` must sit on a reviewed list (T6 (g)). T6 (g) is keyed by `(module, function)`: a second non-constant `getattr` inside a listed function is not reported. `vars(x)["chat"]` and `x.__getattribute__("chat")` are not found. `exec`/`compile`/`importlib` are not followed: today there is one `exec`, the pinned tool-module loader (`tools.py:389`). The real guard is P5c's `isinstance` check and import-graph test.
  - (d) Selecting the redactor does not mean every value is masked. The owner-visible limits of order 19 B stand: secrets of 8 to 11 characters (common passwords) are caught only as plain copies (order 15); other-case and re-broken copies of stored names and addresses are sent; copies hidden as base64, hex or invisible characters are caught only where the existing tool-secret forms cover them; copies with extra inserted characters are sent.
  - (e) The demo `demos/ask-your-data/askdata/pipeline.py` calls the model directly and is outside P6a's wrapper rows (V2). The registry check still lists it; P5c's T3-07 (d) owns the question whether it imports a raw llm kind module.
  - (f) `guard/bedrock_guardrail.py` sends text to a vendor service outside the llm kind. P6a-2 only pins that it is the one `apply_guardrail` site; P6a-1's S6 refuses it in a dev config without `made_up_data_only: true`. Whether its input is masked is P5c's.
  - (g) **Client data in a `dev` config (owner-visible; the lead shows it to the owner).** P6a-1's `made_up_data_only` rule is the first line: a dev config that names a real model or the vendor detector is refused unless it says it holds only made-up data. The field is the operator's own word and is not a lock: a dev config with client data and `made_up_data_only: true` is not refused. P6b1's plain-words `dev` label sentence (`tickets/P6b1.md:120`, `:244`) stays as the second line. Binding the no-training statement to route model ids and gateway upstreams is v1.1 row V8.
- **Tests** ("pin" as defined above; prod rows use `prod_cfg`; every pilot or prod T5 row uses the `made` fixture; refusal rows use `pytest.raises(ConfigError, match=...)` on the new text):
  - **P6a-1, `tests/test_client_profile.py`, 42 rows:**
    - **T0 prod fixture (1).** `load_config(prod_cfg(tmp_path))` loads. No Postgres.
    - **T1 dev-only rows not covered elsewhere (3).** (a) A `pilot_cfg`-based config with `secrets: {kind: env}` is refused in pilot and in prod, with `environment <env>: refused` and `secrets: env` in the message (2). (d) A pilot config whose `backends` omits `store` is refused, with `store: memory` in the message (1). Every other pair, the all-at-once message and PL61's `llm: fake` row are pinned by `tests/test_p1b_backends.py:89-102`.
    - **T2 completeness (5).** (a) `DEV_ONLY` equals the 6 pairs exactly, plus any pair a later package adds there in its own diff (1). (b) Every pair of `TABLE` is in exactly one of `DEV_ONLY` and `CLIENT_REVIEWED`, and each `CLIENT_REVIEWED` entry has a non-empty reason (1). (c) Three planted rows: the check function, called with a `TABLE` copy holding an extra kind in neither set, a pair planted in both sets, and a `CLIENT_REVIEWED` entry with an empty reason, reports each (3).
    - **T5 build keywords in a client profile (26).**
      - (b) Parametrised over the refused keywords read from the signature: today `secrets`, `channel`, `detector`, `llm`, `clock`, each given alone, refused in pilot and in prod; the message names `<keyword>=` and `allow_test_doubles` (5 x 2 = 10).
      - (c) All five at once in pilot: one message naming all five in signature order (1).
      - (f) `sources=` alone in pilot: the `sources=` message (`app.py:92`), so `sources` is not in the new rule (1).
      - (g) AST over `src/hadavin_sdk/` and `demos/`: it fails on any `ast.keyword` with `arg == "allow_test_doubles"` in ANY call (this covers `functools.partial(build, ...)`), and on any `**` expansion (`keyword.arg is None`) in a call whose function name is `build`. One real-tree row, plus three planted modules in a `tmp_path` tree, each reported: a direct keyword, `partial(build, allow_test_doubles=True)`, and `build(**opts)` (4).
      - (h) `tools=` alone in pilot: the `tools=` message, so `tools` is not in the new rule (1).
      - (i) Falsy double: a channel stub whose `__len__` returns 0, in pilot: refused (1).
      - (j) Placement: a refused `llm=` in pilot leaves `record` EMPTY (nothing built before the refusal) (1).
      - (l) Planted keyword: `getattr(app_mod, "_test_doubles_given")` called with the signature of a stub function that has one extra keyword, given a non-default value: the extra name is reported (1).
      - (m) No override at all, in pilot and in prod: the build passes the check (`_Reached`, `record` starts with `"secrets"`) (2).
      - (n) Pilot, `llm=` plus `allow_test_doubles=True`: the build passes the check (`_Reached`, `record` holds `"secrets"`, no `ConfigError` naming `allow_test_doubles`). No Postgres (1).
      - (o) `hold_run_ids=` and `timeout_s=`, each alone in pilot, no switch: NOT refused (`_Reached`) (2).
      - (p) `getattr(app_mod, "_LIVE_HOOKS")` equals exactly `{"hold_run_ids", "timeout_s"}` as a set, and each is a parameter of `build` (1).
      - The Postgres positive path is `tests/test_k3_pilot_env.py:185` itself, once it carries the switch (named as the pin; the evidence says whether it ran or skipped). The dev path ("overrides in dev build unchanged") is pinned by every dev test that passes overrides, for example `tests/test_k5_tools.py:1031`.
    - **T7 client-data rule (7).**
      - (a) One row per llm kind outside `DEV_ONLY`, read from `TABLE` (4 today: `anthropic`, `bedrock`, `openai_compat`, `gemini`): a dev config naming it, without `made_up_data_only`, is refused with `llm: <kind>` and `made_up_data_only` in the message. The builder writes one minimal made-up settings dict per kind; a kind added later with no settings dict fails the row, so it gets decided (4).
      - (a2) Dev, `llm: fake`, one `bedrock_guardrail` detector, no field: refused with `detector: bedrock_guardrail` (1).
      - (b) Dev, a real llm kind plus `made_up_data_only: true`: loads (1).
      - (d) Dev, a real llm kind, a `bedrock_guardrail` detector AND an anchor in `COMPLIANCE` mode (a refusal today's code already gives outside prod, `config.py:385-390`): ONE `ConfigError` whose message names all three (1).
  - **P6a-1 fail-before** (copy `tests/test_client_profile.py` into a scratch worktree of P6a-1's base):
    - Step 0: `pytest --collect-only -q tests/test_client_profile.py` must print 42 items; the evidence holds that output.
    - Expected FAIL (19): T5 (b) 10, (c), (i), (j); T7 (a) 4, (a2), (d). Each fails because the refusal does not happen (`_Reached`, a different error, or a message without the new items). None is a pass.
    - Not counted (4): T5 (l) and (p) (name missing); T5 (n) (unknown keyword `allow_test_doubles`); T7 (b) (unknown config key, refused by `extra="forbid"`).
    - Expected PASS, pins (19): T0, T1 (3), T2 (5), T5 (f), (g) (4), (h), (m) (2), (o) (2). T5 (g) passes because nothing passes the switch yet; its killers are its planted rows and mutants 23 to 25.
    - 19 + 4 + 19 = 42. The table (row, expected on base, seen) goes into the evidence file.
  - **P6a-2, appended to `tests/test_client_profile.py`, 13 rows (T6):**
    - (a) Real tree at P6a-2's base: `unexpected_sites` of the sites outside `llm/` against the written set is empty, and so is the reverse difference. Any new site outside `llm/` is added with a reason and reviewed (1).
    - (b) `apply_guardrail` sites equal `{("guard/bedrock_guardrail.py", "GuardrailDetector.check")}` (1).
    - (c) Seven planted rows, each a `tmp_path` tree scanned with `model_call_sites` and checked with `unexpected_sites` against a planted allowed set; each planted site is reported: `getattr(llm, "chat")(...)`; `f = llm.chat` then `f(...)`; `functools.partial(llm.chat)`; `operator.methodcaller("chat")`; `from operator import attrgetter as g; g("chat")`; a module `m.py` with `allowed_fn` and `other_fn` both reading `.chat`, allowed `{("m.py", "allowed_fn")}`, so `("m.py", "other_fn")` is reported; `apply_guardrail` in another module, allowed = the T6 (b) set (7).
    - (d) A file with a syntax error makes the scan fail (1).
    - (e) `"demos/ask-your-data/askdata/pipeline.py" in _sink_callers()` (the demos root is kept). The existing `test_every_module_that_calls_a_model_is_registered` (`tests/test_k5_producers.py:98`) stays green unchanged (1).
    - (g) `dynamic_attr_sites([(src, "")])` equals a reviewed list of 11 `(module, function)` pairs, each with a one-line reason: `actions/executor.py` `resolve`; `backends/factory.py` `make`; `backends/table.py` `AnthropicSettings._platform_fields` and `_VaultConnection._checks`; `config.py` `Backends.entries` and `EvidenceSettings._checks`; `k1b/tools.py` `Snapshot.call`; `models.py` `Plan.hash`; `registry.py` `Registry.config_hash` (2 sites); `store/protocol.py` `missing_methods`; `tools.py` `resolve_function`. The builder re-runs it at P6a-2's base and writes what it finds. A new one fails (1). (g2) Planted: a module with `getattr(x, name)` is reported (1).
  - **P6a-2 fail-before (the alias-proof scan, no helper copied).** For each of the 5 alias forms of T6 (c) (getattr, `f = llm.chat`, `partial`, `methodcaller`, `attrgetter as g`), plant one module `src/hadavin_sdk/_p6a_planted.py` holding that form, once in a scratch worktree of P6a-2's BASE and once in one of the P6a-2 commit, and in each run `tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered`. Expected on base: PASS (the old scan misses the planted module; that is the defect). Expected on the P6a-2 commit: FAIL, naming `_p6a_planted.py`. Ten runs. `_sink_callers` keeps its signature, so the base run cannot fail by `TypeError`. P6a-2's 13 rows are rows of a new helper and have no copy-to-base table. All 13 pass at head; T6 (e) and the unchanged registry test are the registry pins.
  - **Hostile inputs:** the T6 (c) and (g2) planted forms; the three T5 (g) planted forms (including `**opts`); the T5 (i) falsy double; the T2 (c) planted kinds; T7 (d) (three refusals at once).
  - **Race/process tests:** none (no state, no money).
  - **Contract suite:** not a kind; none.
- **Mutation plan.** Each mutant is one hunk with a named killer that exists in this ticket or on main. Mutants are cited by code text, not line numbers, because other packages edit `config.py` and `app.py` first. They run under P1m's mutation runner; its command line is UNVERIFIED until P1m merges, and whether it can mutate files under `tests/` (mutants 23 to 28 and 36 to 45) is UNVERIFIED too. A mutant found equivalent at build time is reported to the lead with its diff, never dropped silently (P4a PL65 rule).
  - **P6a-1 (35):**
    1. `("llm", "fake")` removed from `DEV_ONLY`: `test_p1b_backends.py:89` (`llm: fake`), T2 (a).
    2. `("channel", "fake")` removed: `test_p1b_backends.py:89`, T2 (a).
    3. `("secrets", "fake")` removed: `test_p1b_backends.py:89`, T2 (a).
    4. `("secrets", "env")` removed: T1 (a), T2 (a).
    5. `("store", "memory")` removed: `test_p1b_backends.py:89`, T1 (d), T2 (a).
    6. `("audit", "local_dir")` removed: `test_p1b_backends.py:89`, T2 (a).
    7. In `_cross_checks`, `if self.environment != "dev"` becomes `== "prod"`: T1 (a) pilot row, T1 (d), `test_p1b_backends.py:89` pilot row.
    8. `', '.join(refused)` keeps only the first refusal: `test_p1b_backends.py:89`, T7 (d).
    9. The S2 check deleted: T5 (b) `llm` rows.
    10. The check looks only at `llm`: T5 (b) rows for `secrets`, `channel`, `detector`, `clock`.
    11. `allow_test_doubles` default `True`: T5 (b).
    12. The check uses `cfg.environment == "prod"`: T5 (b) pilot rows.
    13. `sources` not excluded from the rule: T5 (f).
    14. `tools` not excluded from the rule: T5 (h).
    15. The helper compares by truth value instead of `is not` the default: T5 (i).
    16. The check placed after `secrets = secrets or make(...)`: T5 (j) (`record` holds `"secrets"`), T5 (m) (the rebound provider is never the default, so every live build is refused).
    17. The check placed after `platform_secrets.check`: T5 (j).
    18. The names taken from a fixed list of the original four (`secrets`, `channel`, `detector`, `llm`) instead of the signature: T5 (b) `clock` rows; T5 (l).
    19. The message names only the first keyword: T5 (c).
    20. Switch ignored (`and not allow_test_doubles` dropped): T5 (n), `tests/test_k5_round9b.py:370`, `tests/test_k5_round10.py:80` (both carry the switch after this ticket, need no Postgres, and assert a later refusal).
    21. `_LIVE_HOOKS` gains `llm`: T5 (b) `llm` rows, T5 (p).
    22. `_LIVE_HOOKS` ignored (the hooks refused too): T5 (o).
    23. T5 (g) checker: the `allow_test_doubles` keyword branch deleted: T5 (g) direct-keyword planted row.
    24. T5 (g) checker: keywords checked only in calls named `build`: T5 (g) `partial` planted row.
    25. T5 (g) checker: the `**` branch deleted: T5 (g) `**opts` planted row.
    26. T2 check: a pair in both sets not reported: T2 (c) both-sets row.
    27. T2 check: the empty-reason rule removed: T2 (c) empty-reason row.
    28. T2 check: a kind in neither set not reported: T2 (c) neither row.
    29. The S6 items deleted: T7 (a).
    30. The S6 items run in every environment (not only dev): T0 (`prod_cfg` names `openai_compat`), T5 (m), T5 (n).
    31. `made_up_data_only` default `True`: T7 (a).
    32. The S6 llm item checks one fixed kind name (for example only `anthropic`): T7 (a) rows for the other three kinds.
    33. The `bedrock_guardrail` detector item dropped: T7 (a2), T7 (d).
    34. The field ignored (refused even with `made_up_data_only: true`): T7 (b).
    35. The S6 items raised as their own error, not joined into the one `refused` message: T7 (d) (the anchor refusal or the S6 items go missing from the one message).
  - **P6a-2 (10):**
    36. Scanner: the `getattr` branch deleted: T6 (c) getattr row.
    37. Scanner: the `attrgetter` branch deleted: T6 (c) `attrgetter as g` row.
    38. Scanner: the `methodcaller` branch deleted: T6 (c) methodcaller row.
    39. Scanner: alias resolution deleted (only the literal name `attrgetter` matched): T6 (c) `attrgetter as g` row.
    40. Scanner: only `ast.Call` function attributes counted (today's shape): T6 (c) `f = llm.chat` and `partial` rows.
    41. `unexpected_sites` compares modules only, not `(module, function)`: T6 (c) second-function row.
    42. Scanner: `apply_guardrail` dropped from the names: T6 (b), T6 (c) apply_guardrail row.
    43. Scanner: a syntax error skips the file: T6 (d).
    44. `_sink_callers` drops the demos root: T6 (e).
    45. `dynamic_attr_sites`: the non-constant branch deleted: T6 (g2).

  Count: 45 mutants (P6a-1 35, P6a-2 10; revision 2 had 37). Recounted by script (CHANGELOG).
- **Evidence commands (exact).** `<handover>` is the absolute path of the handover checkout, so runs in a scratch worktree write outside that tree. Every command has the form `<command> > <file> 2>&1; echo rc=$? >> <file>` (repo rule `verify-tests-and-evals`; P5c's form), so the exit code is the command's, never a pipe's. Raw output under `<handover>/evidence/P6a/`, summary in `evidence-p6a.md`.
  - P6a-1: `uv run --all-extras --group test pytest tests/test_client_profile.py -q -rA > <handover>/evidence/P6a/p6a1-client-profile.txt 2>&1; echo rc=$? >> <handover>/evidence/P6a/p6a1-client-profile.txt`.
  - P6a-1 fail-before: (1) `git worktree add <scratch>/p6a1-base <P6a-1 base commit>`; (2) copy `tests/test_client_profile.py` into it; (3) in it, `uv run --all-extras --group test pytest --collect-only -q tests/test_client_profile.py > <handover>/evidence/P6a/p6a1-collect.txt 2>&1; echo rc=$? >> <handover>/evidence/P6a/p6a1-collect.txt` (must show 42 items); (4) `uv run --all-extras --group test pytest tests/test_client_profile.py -q -rA > <handover>/evidence/P6a/p6a1-failbefore.txt 2>&1; echo rc=$? >> <handover>/evidence/P6a/p6a1-failbefore.txt`; (5) `git worktree remove <scratch>/p6a1-base`.
  - The Postgres positive path: `uv run --all-extras --group test pytest tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py -q -rA > <handover>/evidence/P6a/p6a1-pg.txt 2>&1; echo rc=$? >> <handover>/evidence/P6a/p6a1-pg.txt`, with the Postgres service as CI (`.github/workflows/ci.yml:86`); the evidence says whether each row ran or skipped.
  - The recount script (`python3 -I`, read-only) lists (1) every test call of `build(` with a live config and a non-default refused keyword, and (2) every dev test config with a real llm kind or a `bedrock_guardrail` detector, into `<handover>/evidence/P6a/p6a1-recount.txt`. It runs at P6a-1's base.
  - P6a-2: the same client-profile run into `p6a2-client-profile.txt`. Fail-before: worktrees `<scratch>/p6a2-base` (P6a-2 base) and `<scratch>/p6a2-head` (P6a-2 commit); for each of the 5 forms write `src/hadavin_sdk/_p6a_planted.py` in both and run `uv run --all-extras --group test pytest "tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered" -q -rA >> <handover>/evidence/P6a/p6a2-failbefore.txt 2>&1; echo rc=$? >> <handover>/evidence/P6a/p6a2-failbefore.txt` in each; remove both worktrees. The planted file is never committed.
  - For each sub-package: `uv run --all-extras --group test pytest -q > <handover>/evidence/P6a/<sub>-full-suite.txt 2>&1; echo rc=$? >> ...` (Python 3.13, as CI, `ci.yml:73`, `:109`); `ruff check src tests demos` and `ruff format --check src tests demos` into `<sub>-lint.txt`; `bandit -q -r src demos -ll` (`ci.yml:119`) into `<sub>-bandit.txt`; each with `echo rc=$?`.
  - Whether `tests/` ships in the wheel: `build-backend = "uv_build"` (`pyproject.toml:58`); that only `src/hadavin_sdk` is packed is UNVERIFIED. The builder runs `uv build` and lists the wheel's files into `wheel-files.txt`.
  - Mutants: the P1m runner over the entries above into `<sub>-mutants.txt`; every row read: KILLED with its killer named.
- **Reviewers:** correctness + adversarial, fresh agents, per sub-package; they get the diff, this ticket and the evidence only. The adversarial reviewer is asked: to find a side door to the model that T6 misses and that P5c's `isinstance` check does not catch; to find a way a copied test fixture starts a pilot app with a test object that T5 misses; to find a dev config that sends text out past S6 without stating `made_up_data_only: true`.
- **Done =** plan rule 4 (two clean rounds in a row at the final commit, evidence green at that commit) and all gates green: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit; plan section 9 row "Client profile": `uv run --all-extras --group test pytest tests/test_client_profile.py` passes. Per sub-package.
- **Rollback:** tags `pre-P6a-1` and `pre-P6a-2` (the lead only). No migration, no stored data. Two behaviour changes, both revertible by reverting the merge and listed in CHANGELOG: a live build that passes a refused keyword needs `allow_test_doubles=True`; a dev config with a real llm kind or the vendor detector needs `made_up_data_only: true`. Nothing non-revertible.

## Couplings (relays for the lead to pass on)
- **To P5c:**
  - P6a-1 lands BEFORE P5c-3 on `app.py` and before P5c-1 on `config.py`; P5c rebases on it. P5c's hot-file lists (`tickets/P5c.md:117-122`) should say: P6a-1 on `app.py` and `config.py` (early); P6a on no `cli.py`, `backends/table.py` or `tests/test_lockin_guard.py` slot (`:119`, `:120` list P6a there today); P6a-2 on `tests/test_k5_producers.py` after P5c-3.
  - P5c-1 adds `("redactor", "regex")` to `CLIENT_REVIEWED` in `tests/test_client_profile.py` with the reason "masking kind; its rows are P5c-1's `tests/test_p5c1_redactor.py`", or T2 (b) fails.
  - Any test P5c-3 adds or changes that calls `app.build` in pilot or prod with `llm=`, `secrets=`, `channel=`, `detector=` or `clock=` passes `allow_test_doubles=True`; any dev test config with a real llm kind sets `made_up_data_only: true`.
  - `app.build_llm` is named only in T3-07 (b) (`tickets/P5c.md:426`); P5c-3's `app.py` line (`:282`) does not create it. P5c should add it to its Files list or re-word T3-07 (b) to the function that holds `make("llm", ...)` after P5c-3.
  - P6a no longer asks T3-07 to use `model_call_sites` (no part (a) exists).
- **To P6b2:**
  - `tickets/P6b2.md:139`: the `app.py` order is "P2a-1, P4b2-b, P4c-2, P6a-1, P5c-3, P6b2-a"; P6a-2 does not edit `app.py`. P6b2-a's `migrate_credential_ref` refusal rebases on P6a-1's check, which sits right after `load_config`.
  - `tickets/P6b2.md:138`: P6a-1 is early on `config.py`, not last; P6b2-a's N2 edit rebases on it. Its cite `tickets/P6a.md:37` is stale.
  - `tickets/P6b2.md:137`: drop "then P6a" from the `table.py` and `cli.py` lists (P6a edits neither).
  - If P6b2 adds a `TABLE` pair, it adds it to `DEV_ONLY` or `CLIENT_REVIEWED` in its own diff.
- **To P4c and P4b1:**
  - `tickets/P4c.md:40` and `:307`: `app.py` order as in the P6b2 relay; P6a-1 sits after P4c-2.
  - `tickets/P4b1.md:270` (the resolve placed it at `P4c.md:270`; see N5): reword "P6a's check 'no path calls the llm kind except through the masking wrapper'" to "P5c's T3-06 and T3-07"; P6a's scanner is only a tripwire.
  - `tickets/P4b1.md:115` ("P6a/P4c decide where" a `Caps` of three `None`s is refused): P6a does NOT refuse it. Recommend P4c owns that refusal in pilot and prod; if neither ticket takes it, it is an unowned money-path hole and goes to the lead.
- **To P6b1:** item 10 (`tickets/P6b1.md:532`) is answered by S6 (first line); its `dev` label sentence stays as the second line; PL11 is P6a's V8 row with a trigger.
- **To the lead (amendment):** P1 is FROZEN; the answer "warning only in v1" to `tickets/P1.md:47` (order 22 item 24) is recorded as an amendment by the lead. A9 F6's P6a dependency line after the split (Depends on).

## Later and v1.1 rows (nothing is silently lost)
| Id | What | Trigger |
|---|---|---|
| V1 | Per-`Entry` `dev_only` field instead of the `DEV_ONLY` set (plan rule 9(g)'s literal wording) | a kind needs a per-settings decision (dev-only for some settings only) |
| V2 | Scan `demos/` with the wrapper rows; the ask-your-data pipeline calls the model directly | a demo is run with client data, or P8a re-pins that demo, or P5c T3-07 (d) writes the demo's exclusion |
| V3 | Signed audit record of the profile (environment, kinds, no-training statement) at start-up (P6b1 item 6) | a client or auditor asks for start-up evidence in the audit trail |
| V5 | A named profile object with its own refusal table | a client needs a third live environment beside pilot and prod |
| V6 | Strict Unicode-data pin in live (`app.build` or `Config`), the `cli` paths that do not call `app.build` (`gate`, `replay`), and a skip on Pythons whose data differs from the pin | a client asks for the strict Unicode-data pin in live, or a pilot runs on a Python whose Unicode data differs from the pin |
| V8 | Bind the no-training statement to route model ids and to a gateway's upstream providers (P6b1 PL11; owner: P6b1's statement code) | a pilot routes through a gateway that fronts more than one provider, or a route's model id moves to another provider |

V7 (a "holds client data" marker) is no longer a v1.1 row: it is built in v1 as S6 (order 22 items 28 and 31). Open rows: 6.

## PENDING LEAD (my recommendation first)
PENDING LEAD items 1-14: items 2, 3, 4, 8, 9, 10, 11, 12 closed or answered (by cut, by fact or by order 22); 1, 5, 6, 7 kept; 13-14 new.
1. **Build keywords in a client profile (S2).** (a) RECOMMENDED, taken: one rule over the build keywords from the signature, refused in pilot and prod unless `allow_test_doubles=True`, with the two live hooks exempt (item 13) and the check right after `load_config`. Worded as an accident guard. On today's tree 5 tests add the switch, 2 of them Postgres-gated; the recount script gives the final number. (b) Refuse them outright, like `sources=`/`tools=`: live-path tests then cannot run without network; not workable. (c) State the hole only. Confidence 75 percent; reversible.
2. CLOSED (S5 cut; V6).
3. Answered by fact: P5c revision 2 builds the redactor refusal (T1-12, `tickets/P5c.md:378`). Applies to P6a-2's base.
4. Answered by fact: P5c revision 2 has no call-site scanner (cut 8, `tickets/P5c.md:32`), so `_sink_callers` is the one other user of `model_call_sites`.
5. "Client profile" = `environment` in `deferred.LIVE`; no new profile object. RECOMMENDED: yes (V5).
6. `demos/` out of P6a's wrapper rows, kept in `_sink_callers`. RECOMMENDED: yes; P5c's T3-07 (d) owns the demo's import question; V2.
7. Completeness list in the test file, not in `src/`. RECOMMENDED: yes (A6: build on `DEV_ONLY`); V1.
8. CLOSED by order 22 item 24 (split into P6a-1 and P6a-2, as written above).
9. CLOSED by order 22 item 24 (strict pin: warning only in v1; V6).
10. Answered by order 22 item 24, and CHANGED by item 28(b): P6a-1 now takes an early `config.py` slot (one field, one check). `cli.py`, `backends/table.py` and `tests/test_lockin_guard.py` stay free. Carried by item 14.
11. CLOSED by order 22 items 28 and 31 (option b): built as S6.
12. Answered by fact: P5c revision 2's T3-07 (b) asserts the `make("llm", ...)` callers (`tickets/P5c.md:426`); T6 (f), its mutant and `make_llm_callers` are cut.
13. **NEW. Two production hooks exempt from the test-double switch (R2-ADV-3).** (a) RECOMMENDED, taken: `_LIVE_HOOKS = ("hold_run_ids", "timeout_s")`, test-checked (T5 (o), (p)); everything else from the signature is refused in live without the switch; a later keyword is refused until added to the list. Why not exempt `secrets`/`clock` for an embedding operator: a different secrets store is a new secrets kind (the no-single-dependency rule), and a replaced approval clock in a client deployment is exactly what the guard is for. (b) Keep every keyword under the switch and rename it (for example `allow_overrides`): the purge-hold hook in production code then carries the switch, which erodes the guard. (c) Revision 2 as written. Not an owner decision (no money, secret, live call or client data). Confidence 80 percent; reversible.
14. **NEW. Meaning and place of the client-data refusal (order 22 item 28(b)). NEEDS LEAD 50, pending: I proceed on (a) and mark it here.** The literal words "refuse a real llm kind in any config that holds client data" would refuse every real model in pilot and prod, which cannot be meant. My reading, taken: a config is treated as holding client data unless it is `dev` AND says `made_up_data_only: true`; only then may `dev` name a real llm kind or the `bedrock_guardrail` detector. (a) RECOMMENDED, taken: the field and the check in `Config._cross_checks`, the choke point for `app.build` and both `cli` model paths; `config.py` joins P6a-1 (a hot file: P4b1, P5b3, P5c, P6b1, P6b2 rebase on one added field). (b) The check in `app.build` only: no `config.py` edit, but `hadavin gate`, `replay` and `score` in `dev` stay open (`cli.py:150`, `:221`). (c) Refuse every real llm kind in `dev` with no marker (P6b1's option (b)): breaks developer runs with real models on made-up data. Owner-visible limit for the lead to show the owner: the marker is the operator's own word and is not a lock. Confidence 70 percent; reversible until P6a-1 merges.

## UNVERIFIED (I did not read or could not run it)
- Nothing in this ticket was run as a test or against built code. What I ran this session: `sed` and `grep` reads of every cite, one read-only AST listing of `TABLE` (`python3 -I`), `git rev-parse` and `git log -1`, and the count script of the CHANGELOG. I did not re-run the resolve's `git diff --stat 124258b 397ec97` or `git show 397ec97:...`.
- That `prod_cfg` loads (T0), and that `pilot_cfg`/`prod_cfg` still pass P6b1's no-training refusal once P6b1 is built.
- That the `made` fixture's provider passes `platform_secrets.check` for every name `pilot_cfg` and `prod_cfg` need (I read where it is called, `app.py:122`, not its body).
- That `test_p5_llm.py`'s `_llm` helper and `test_p5p6_followups.py`'s `_hash` load the config through `load_config` (and so need `made_up_data_only: true`); that `test_p1a_fixes.py:117` is not affected.
- The final count of tests that need `allow_test_doubles=True` and of dev configs that need `made_up_data_only: true` (recount script).
- That P5c-3 does not edit `tests/test_k3_pilot_env.py:185`.
- Whether P5b2 and P5b3 edit `app.py` (their tickets mention it; I did not read the lines).
- The dotted function names of the model-call sites and of T6 (g) (from revision 2's walk and the reviewers' recount; I did not re-run the walk this session).
- The P1m mutation runner's command line, and whether it mutates files under `tests/`.
- That the wheel holds no `tests/` files.

## CHANGELOG
**Revision 3 (2026-11-06, about 03:30 UTC / 09:00 IST), from `reviews/P6a-round2-resolve.md`.**

**Removed in this revision, and why:**
| Removed | Why | Where it went |
|---|---|---|
| T2 (d), T2 (d2), mutant 37, the "Reused: P5c's redactor contract suite" bullet, the T2 (d) words in "Contract suite" and "Hostile inputs" | P5c revision 2 cut that suite (`tickets/P5c.md:27`); re-aiming at P5c's own test file declined (more coupling for what T2 (b) already forces) | relay: P5c-1 adds `("redactor", "regex")` to `CLIENT_REVIEWED`; P5c's V3 owns the suite |
| T5 (d) and its `MaskedLLM` assertion | Postgres-only positive path; the assertion duplicates P5c's M30 killers T3-06, T3-01 (`tickets/P5c.md:509`) | `tests/test_k3_pilot_env.py:185` named as the Postgres pin; new T5 (n) without Postgres |
| T5 (a) | duplicate of the T5 (b) `llm` rows | T5 (b) |
| T5 (e) | every dev test that passes overrides is the pin (for example `tests/test_k5_tools.py:1031`) | named under T5 |
| The T5 (b) rows for `hold_run_ids` and `timeout_s` | both are now live hooks | T5 (o), (p) |
| T6 (f), mutant 33, helper `make_llm_callers` | P5c revision 2's T3-07 (b) asserts the same (`tickets/P5c.md:426`); also removes a wrong expected set | PENDING LEAD 12 answered by fact |
| The first-statement keyword record, its basis in old T5 (m), old mutant 17 (correction N1's trick) | the check now runs before `app.py:82`, so nothing is rebound | S2 placement |
| The file entry "change P5c's T3-07 part (a)" | revision 2 of P5c has no part (a) | none |
| v1.1 row V7 | built in v1 as S6 | S6 |

**Added or changed, one row per finding id (27):**
| Finding id | What revision 3 does |
|---|---|
| R2-ADV-1 | Import rule for `tests/test_client_profile.py` (base names only at module level; `getattr(app_mod, ...)` inside rows); fail-before step 0, collection must print 42. |
| R2-ADV-2 | Merged with R2-COR-9. T5 (d) cut; new T5 (n) (switch lets the build through, no Postgres); new mutant 20 "switch ignored", killers T5 (n), `test_k5_round9b.py:370`, `test_k5_round10.py:80`. |
| R2-ADV-3 | `_LIVE_HOOKS = ("hold_run_ids", "timeout_s")` exempt; switch name kept; T5 (b) now 10 rows; new T5 (o), (p); mutants 21, 22; Security notes (b''); PENDING LEAD 13. |
| R2-ADV-4 | Merged with R2-COR-2. All P5c cites re-read against revision 2; "Ticket states" re-read; the T3-07 part (a) instruction dropped; "live contradiction" contested (T3-07 (d) is an import-graph question, P6a's a call-site one; owner of the demo question: P5c T3-07 (d)); V2 trigger extended. |
| R2-ADV-5 | T5 (j) asserts `record` is EMPTY; mutants 16 ("after `secrets = secrets or make(...)`") and 17 ("after `platform_secrets.check`"), killer T5 (j). |
| R2-ADV-6 | Every evidence command `> <file> 2>&1; echo rc=$?`; absolute `<handover>/evidence/P6a/...` paths. |
| R2-ADV-7 | Shared `made` fixture: `app.make` patched, made-up secrets provider, `_Reached` for any other capability; refusal rows match `allow_test_doubles`. |
| R2-ADV-8 | The 31 `TABLE` pairs and their sets listed (S1); pair rule; `NOT_PROD` rule; later packages add their pairs. |
| R2-ADV-9 | Merged with R2-COR-1 and R2-COR-12. T2 (d), (d2), mutant 37 cut (table above). |
| R2-ADV-10 | Counts per sub-package; owners: P6a-1 owns `test_k3_pilot_env.py:185`, the 4 other switch tests and the `made_up_data_only` edits; P6a-2 owns `_sink_callers` after P5c-3's T3-17. Part contested: P5c-3 editing `:185` is UNVERIFIED, not assumed. |
| R2-ADV-11 | Security notes (b): the T5 (g) tripwire does not follow an aliased `build`. Planted alias row declined (order 8). |
| R2-ADV-12 | Merged with R2-COR-11. The check moved to right after `cfg = load_config(config_dir)` (`app.py:79`); "no backend is built before this refusal"; the 3 earlier-refusal tests take the switch. |
| R2-ADV-13 | PENDING LEAD summary line reworded (item numbers, not counts). |
| R2-ADV-14 | Security notes (c): T6 (g) is keyed by `(module, function)`; a second non-constant `getattr` in a listed function is not reported. |
| R2-COR-1 | Merged into R2-ADV-9. |
| R2-COR-2 | Merged into R2-ADV-4. |
| R2-COR-3 | `app.py` hot-file order "P2a-1, P4b2-b, P4c-2, P6a-1, P5c-3, P6b2-a", cite `tickets/P6b2.md:139` (not `:173`); `config.py` P6a-1 early; relay to P6b2. |
| R2-COR-4 | T6 (f), mutant 33 and `make_llm_callers` cut; T6 (a)'s set is written at P6a-2's base, naming the P5c-3 hunk for each change. |
| R2-COR-5 | Re-cited `tickets/P4b1.md:107` and `tickets/P4c.md:40`, `:307`. |
| R2-COR-6 | Oracle stated: `unexpected_sites(found, allowed)`; planted rows use a planted allowed set (T6 (c)). |
| R2-COR-7 | Item 12: 5 tests read by hand need the switch; other `build(` callers UNVERIFIED, covered by the recount script, which also lists dev configs with a real llm kind; round8's own skip named. |
| R2-COR-8 | Contested "not reproducible": the repository root is a git work tree (`git rev-parse` this session). `397ec97` named as the base the resolve read; the `ce70eb5` sentence kept for the disk tree. |
| R2-COR-9 | Merged into R2-ADV-2. |
| R2-COR-10 | Word list: a `.chat` read on a non-model object is a false alarm, fixed by adding the site with a reason. |
| R2-COR-11 | Merged into R2-ADV-12. |
| R2-COR-12 | Merged into R2-ADV-9 ("Contract suite: none" is now consistent). |
| N4 (resolve, Major) | Defect of revision 2: its T5 rows hit the missing `mounted_file` folder at `app.py:82` before the check (item 6). Closed by the placement (R2-ADV-12) and the fixture (R2-ADV-7). |

**Order 22 items applied:** item 24 (split; strict pin warning only, PENDING LEAD 8 and 9 closed, V6 trigger); items 28(b) and 31 option b (S6, field `made_up_data_only`, rows T7, mutants 29-35; PENDING LEAD 14 = NEEDS LEAD 50, pending); item 28 PL11 (v1.1 row V8); item 28 P6b1 `dev` label as the second line (Security notes (g)).

**Corrections I found while re-reading (not in the resolve):**
- N5: the resolve's relay cites `P4c.md:270` for "P6a's check 'no path calls the llm kind except through the masking wrapper'". That sentence is at `tickets/P4b1.md:270`; `P4c.md:270` is the rollback line. Relay fixed.
- N6: revision 2 cited `tickets/P4b2.md:238` for P4b2's P6a line. P4b2 is now revision 4; `:238` is about the reservation clock, and the P6a line is `:255`. Re-cited.
- N7: two row definitions the resolve kept but that its placement change breaks. (1) T5 (f) and (h) were "`sources=`/`tools=` AND `llm=`: the old message"; with the check now first, that pair gets the new message. They become `sources=`/`tools=` alone (still pins), and the old mutants "placed before the `sources=`/`tools=` check" become 13/14 "`sources`/`tools` not excluded from the rule". (2) Mutant 35 ("S6 items not joined into the one message") could not fail with the resolve's T7 (d) (real llm plus vendor detector only: both names land in one message either way). T7 (d) now also holds an anchor refusal that today's code gives in dev (`config.py:385-390`). Same row and mutant counts.

**Counts, recounted by script (`python3 -I` over this file):** test rows 55 (P6a-1 42: T0 1, T1 3, T2 5, T5 26, T7 7; P6a-2 13); mutants 45 (P6a-1 35, P6a-2 10), each with a named killer; fail-before P6a-1: 19 FAIL, 4 not counted, 19 PASS; P6a-2: 10 planted runs; PENDING LEAD 14 items (13, 14 new); v1.1 open rows 6 (V1, V2, V3, V5, V6, V8). Revision 2: 54 rows, 37 mutants.

**Revision 2 (2026-11-06, about 03:00 UTC / 08:30 IST):** from `reviews/P6a-round1-resolve.md`; 54 rows, 37 mutants, 12 PENDING LEAD items.

**Revision 1 (2026-11-06, about 02:45 UTC / 08:15 IST):** first draft; 70 test rows, 16 mutants, 7 PENDING LEAD items.

# Package ticket P6a: the client-profile check (a pilot or production app cannot start with test-only parts or test objects handed in by code, and a CI test catches code in `src/` that reaches the model by a side door). REVISION 2, DRAFT

**Revision line.** Revision 2, written 2026-11-06 from about 03:00 UTC (08:30 IST; IST = UTC+5:30) by a ticket-author agent, under lead order 20 item 6 (ticket only: no code, no pull request, no suite run). It applies every decision of `handover/reviews/P6a-round1-resolve.md` (18 decision rows over 25 round-1 findings) and three corrections I found while re-reading the code (CHANGELOG, items N1 to N3). Revision 1 was written 2026-11-06 at about 02:45 UTC (08:15 IST). **Next step: review round 2** (two fresh reviewers, correctness and adversarial, then one resolve). Cap (order 20 item 6): at most 3 ticket rounds counting from round 1. The "one more round" exception there covers money and redaction packages only, not security, so round 3 is the last ticket round.

Plan row: plan-v3 section 6, row P6a, step S4. **Where the cites come from.** Every `file:line` cite below I re-read myself in the checkout under `/home/user/hadavin-sdk-handover/src` and `tests/`. Those files were last changed by core commit ce70eb5. `git diff --stat 124258b HEAD -- src tests` lists only `guard/http.py`, `guard/runmap.py`, `tools.py` and two test files. Of these, this ticket cites only `tools.py:389` and `:407`, and I checked those two lines in `git show 124258b:src/hadavin_sdk/tools.py`: same text, same line numbers. So the cites also hold on core main 124258b. Anything I did not read in code is marked UNVERIFIED. "PENDING LEAD" means my recommendation, which the lead decides (list at the end). "PENDING P5c" means the item waits for the P5c ticket. **P5c revision 1 exists** (DRAFT, round 1 reviewed, revision 2 being written), so its names below can still change.

**Path class: SECURITY.** This package decides whether a client deployment can start with a test-only part. Extended review: yes, Tier A (plan rule 3 names "client-profile gates"). Ticket review: the cap above. Result review of the built code: two fresh reviewers per round (correctness and adversarial) and the two-clean-rounds stop rule (plan rule 4; order 16 keeps it for built code).

**Scope rule used in this revision (orders 7(3) and 8(1)):** where a finding can be closed by deleting surface instead of adding design, it is deleted. Four items were cut this way (S3, S5, T3/T4, most of T1). Each cut has its reason in the CHANGELOG and, where it is a feature, a v1.1 row.

## Words used in this ticket (one meaning each)
- **client profile**: a configuration whose `environment` is `pilot` or `prod`. There is no other profile object. `Config.environment` is `Literal["dev", "pilot", "prod"]` (`config.py:317`) and `deferred.LIVE = ("pilot", "prod")` (`deferred.py:33`). "Live" below means the same thing. P6a adds no new profile concept (PENDING LEAD 5).
- **dev-only kind**: a `(capability, kind)` pair in `DEV_ONLY` (`backends/table.py:593-602`): `llm/fake`, `channel/fake`, `secrets/fake`, `secrets/env`, `store/memory`, `audit/local_dir`.
- **masking wrapper**: the object P5c builds that masks text before the model sees it. P5c revision 1 calls it `MaskedLLM` in `llm/masked.py` (`tickets/P5c.md:13`, `:34`). Final names are PENDING P5c.
- **test double**: an object a test passes into `app.build` in place of a configured part (`ScriptedLLM`, `FakeChannel`, a spy secret provider, a fixed clock).
- **build keyword**: any keyword-only parameter of `app.build` (today `secrets`, `channel`, `detector`, `llm`, `tools`, `sources`, `hold_run_ids`, `clock`, `timeout_s`; `app.py:62-75`), plus any added later.
- **model-call site**: in `src/`, a read of the attribute `chat` or `apply_guardrail` (a call or not), or a call of `getattr`, `operator.attrgetter` or `operator.methodcaller` whose name argument is one of those two names written as a string constant. It is NOT "every possible way to reach the model": names built at run time, `vars()[...]`, `__getattribute__` and `exec` are not found (stated as limits under Security notes). The real guard is P5c's (the `isinstance` check and the import-graph test); the scanner is a tripwire against accidental side doors.
- **PL61**: P4a's pending-lead item 61, confirmed by order 16 item 3: k1b replay is dev-only in v1.
- **pin (test row)**: a row that already passes before P6a, because main or P5c already behaves that way. It guards against a later regression; it is not a fail-before row.

## What is already true on main (read in code)
1. **Dev-only kinds are already refused outside dev.** `Config._cross_checks` builds a refusal list when `self.environment != "dev"` from every `(capability, kind)` of `self.backends.entries()` that is in `DEV_ONLY` (`config.py:365-369`). It adds `allow_insecure_loopback` (`:370`) and the anchor rules (`:371`, `_anchor_refusals` at `:377`, which adds the `NOT_PROD` pairs in prod at `:391-392`), and raises ONE `ValueError` joining them with `', '.join(refused)` (`:372-373`). `load_config` turns it into `ConfigError` (`config.py:453-454`). Capabilities left out of a config get `DEFAULTS` (`table.py:582-589`: secrets `fake`, store `memory`, channel `fake`, ...), and those defaults are refused the same way, because `entries()` lists every capability (`config.py:74-76`). So for the configuration path, the plan's "turn on the check" is a check that exists today (memo-6, row "rule 9(g)"; A6: "P6a builds on it").
2. **That check is already pinned by a test.** `tests/test_p1b_backends.py:89-102` runs in pilot and prod and asserts one error holding `llm: fake`, `store: memory`, `audit: local_dir`, `secrets: fake`, `channel: fake` and `allow_insecure_loopback`. It does NOT cover `secrets: env`. PL61's `llm: fake` row is that test; P4a relies on it, not on P6a.
3. **The llm kind has no default, and P5c builds the redactor rule.** `Backends.llm` has no default (`config.py:70`) and `DEFAULTS` has no `llm` entry. P5c revision 1 adds the `redactor` capability with one kind, `regex` (`DEFAULTS["redactor"] = "regex"`, no `DEV_ONLY` pair, `tickets/P5c.md:64`), makes `Config` refuse a missing explicit `redactor` outside dev (`:64`, `:71`), and pins it with T1-12 `test_pilot_and_prod_config_without_explicit_redactor_refused` (`:78`). P5c-3 makes `Runtime.__init__`, `evals.gate`, `extract.extract` and `JudgeDetector.__init__` refuse a raw model (`:66`; row T3-06, `:81`).
4. **The hole on main: `app.build` takes test doubles in a client profile.** `app.build` accepts the build keywords (`app.py:62-75`) and uses `secrets`, `llm`, `detector` and `channel` instead of the configured kinds (`app.py:82`, `:162`, `:163-169`, `:170`). `hold_run_ids` goes to the hooks (`:225`) and `clock` to `Approvals` (`:182`). In pilot and prod `build` refuses only `sources=` (`app.py:90-92`) and `tools=` (`:93-98`). So a pilot app can run with a `FakeChannel` and a scripted model while its config names Slack and a real model. The repository's own test does exactly this: `tests/test_k3_pilot_env.py:184-191`. The only `src/` caller of `build` is `cli.py:299` (`build(None, agents)`, in `_tick`, no keywords). `demos/` has no call of `app.build` (its `build` names are other functions: `demos/ask-your-data/db/lumen.py:481`, `db/build_verify.py:32`, `askdata/fixtures.py:109`). So the hole is reachable only by a client's own Python code, not by configuration.
5. **Order inside `build` (it matters for S2).** `secrets = secrets or make("secrets", b.secrets)` at `app.py:82` REBINDS `secrets` before `live` is computed (`:83`). Then come the evidence-key check (`:84-85`), the purge-DSN check (`:86-89`), `sources=` (`:90-92`) and `tools=` (`:93-98`). The configured sources are built at `:107-110` and secret names are checked at `:122`. The first `make` other than secrets is `make("signer", ...)` at `:144`, then the store at `:146`.
6. **The existing model-call scan is call-only.** `tests/test_k5_producers.py:22` sets `SINK_METHODS = {"chat", "apply_guardrail"}`. `_sink_callers` (`:78-95`) takes no argument, scans the roots `(ROOT, "")` and `(REPO / "demos", "demos/")` (`:80`), skips `llm/` (`:86`), and counts a module only for an `ast.Call` whose function is an `ast.Attribute` with that name (`:89-94`). `getattr(llm, "chat")(...)`, `f = llm.chat; f(...)` and `functools.partial(llm.chat)` are not counted. P5c's choke-point test T3-07 `test_raw_llm_import_graph_ast` is written in the same call-only shape ("the set of modules holding an `X.chat(` call", `tickets/P5c.md:81`).
7. **What my AST walk finds today** (read-only, `python3 -I`, over `src/hadavin_sdk`, run 2026-11-06 about 03:00 UTC):
   - Model-call sites outside `llm/`, as `(module, enclosing function)`: `evals.py` `gate` (`:73`), `extract.py` `extract` (`:47`), `guard/bedrock_guardrail.py` `GuardrailDetector.check` (`:101`, the only `apply_guardrail`), `guard/judge.py` `JudgeDetector.check` (`:72`), `k1b/loop.py` `_chat_bounded.work` (`:94`), `runtime/agent_loop.py` `Runtime.handle` (`:425`). `MODEL_CALLERS` (`guard/producers.py:55-65`) lists the same six plus `demos/ask-your-data/askdata/pipeline.py`.
   - Calls of `make` with first argument `"llm"`: `app.py` `build` (`:162`), `cli.py` `_main` (`:150`), `cli.py` `_k1b` (`:221`).
   - Calls of `getattr` with a NON-constant name (no `attrgetter` or `methodcaller` is used): 12 call sites in 11 functions: `actions/executor.py:37` `resolve`; `backends/factory.py:54` `make`; `backends/table.py:59` `AnthropicSettings._platform_fields`; `backends/table.py:278` `_VaultConnection._checks`; `config.py:75` `Backends.entries`; `config.py:271` `EvidenceSettings._checks`; `k1b/tools.py:100` `Snapshot.call`; `models.py:139` `Plan.hash`; `registry.py:139` and `:148` `Registry.config_hash`; `store/protocol.py:159` `missing_methods`; `tools.py:407` `resolve_function`.
   - `exec` appears once: `tools.py:389`, the loader of pinned tool-module bytes.
8. **A prod-valid test config does not exist.** `pilot_cfg` (`tests/test_k3_pilot_env.py:35-74`) sets no anchor (default `none`, in `NOT_PROD`, `table.py:604`) and a signer with `private_key_path` (refused in prod, `config.py:395-396`). Its `config=` argument replaces top-level keys, so `backends` would be replaced whole. No test calls `pilot_cfg(..., env="prod")` (grep of `tests/` finds none).
9. **The live builds in today's tests that get past `app.py:98` with test doubles are two**, both Postgres-gated through `pg_schema()` (`tests/contracts/kinds/store_postgres.py:22-24` skips without `HADAVIN_TEST_PG_DSN`; CI sets it, `.github/workflows/ci.yml:86`, `:93`): `tests/test_k3_pilot_env.py:185` and `tests/test_k5_round8_postgres.py:40`. Three other live builds with doubles stop at an earlier refusal and need no change: `tests/test_k5_round9b.py:370` (evidence key, `app.py:84`), `tests/test_k5_round10.py:80` (purge DSN, `:86`), `tests/test_k5_round5.py:226` (`tools=`, `:93`). `tests/test_k5_tools.py:1031` and `:1033` are dev builds (`k5_cfg`), so revision 1 listed them wrongly.

## What P6a does (after the cuts)
- **S1. Make the dev-only list complete, and pin the one pair no test covers.** No code change for the config path (item 1). Test rows: `secrets/env` refused in pilot and prod (item 2's gap), a pilot config that omits `store` is refused (default `memory`), and a completeness check. The completeness check says every `(capability, kind)` in `TABLE` is in exactly one of `DEV_ONLY` and a test-local list `CLIENT_REVIEWED`, each `CLIENT_REVIEWED` entry with a one-line reason. A kind added later with no decision fails CI. `CLIENT_REVIEWED` is not a copy of `NULL_KINDS` or `EXCEPTIONS` in `tests/test_lockin_guard.py`. Those answer "does each capability have a neutral non-dev kind" (`coverage_problems`, `tests/test_lockin_guard.py:406-430`). This list answers "is each kind decided for client use". It lives in P6a's own test file because `tests/test_lockin_guard.py` is a hot file for four packages (PENDING LEAD 7).
- **S2. One rule for every build keyword in a client profile.** In a live profile, `app.build` refuses every build keyword whose value `is not` its signature default, unless the caller also passes `allow_test_doubles=True`. The names come from `inspect.signature(build)`, so a keyword added later is covered with no list to maintain. This covers `clock`, `hold_run_ids` and `timeout_s` too (`timeout_s` is harmless in live, `app.py:172-174`, but refusing it costs nothing). `sources=` and `tools=` keep their own earlier messages. **Honest limit, in plain words: this is an accident guard (a named switch), not a boundary.** Code that builds the app in Python is the operator's own code. It can pass the switch, change the app after `build` (for example `app.runtime.hooks.hold_run_ids = ...`, as `tests/test_k5_tools.py:756` does in a test), or build `Runtime` directly. S2 stops a test fixture or a copied snippet from reaching a pilot by accident. It does not stop an operator who means to do it. PENDING LEAD 1.
- **S3. CUT** (was: P6a pins or builds the "redactor must be named" refusal). P5c revision 1 builds it and pins it in pilot and prod (item 3, T1-12). P6a keeps one Depends-on line: "P5c's T1-12 is green at P6a's base". If a later P5c revision drops T1-12, PENDING LEAD 3 reopens.
- **S4. One model-call scanner, used by every test that needs it.** A test helper finds every model-call site (as defined above) and reports `(module, enclosing function)`. `test_k5_producers._sink_callers` and P5c's T3-07 part (a) switch to it, so the repository has one scanner, not three (PENDING LEAD 4). P6a's rows assert that:
  - the sites outside `llm/` are EXACTLY the six of item 7;
  - `apply_guardrail` appears only in `guard/bedrock_guardrail.py`;
  - the `make("llm", ...)` callers are a fixed set;
  - every non-constant `getattr`/`attrgetter`/`methodcaller` sits in a reviewed list.

  Scope is `src/` for P6a's rows, as the plan row says. `demos/` stays in `_sink_callers`, so the registry check keeps covering the demo (PENDING LEAD 6, v1.1 row V2).
- **S5. CUT** (was: P6a wires P1's strict Unicode-data pin check). It is not in the plan row, it rests on an unanswered P1 item (`tickets/P1.md:47`: "Pilot and prod call it with `strict=True` (author proposal, PENDING ...)"), and it would turn every live-app test red on Python 3.12. Moved to v1.1 row V6, PENDING LEAD 9.

Also cut, each with a v1.1 row: a per-`Entry` `dev_only` field (V1); scanning `demos/` with the wrapper test (V2); a signed audit record of the profile at start-up (V3; P6b1 item 6 points here); a named profile object (V5); the pin check (V6); a "holds client data" marker (V7, PENDING LEAD 11). Revision 1's V4 (pin check on the `cli` paths) is folded into V6.

## Template fields, in the template's order

- **Package id and name:** P6a, client-profile check. One pull request, or two if PENDING LEAD 8 (a) is taken: P6a-1 = S1, S2 (rows T0, T1, T2 (a)-(c), T5 without its `MaskedLLM` assertion); P6a-2 = S4 plus T2 (d), (d2) and the `MaskedLLM` assertion of T5 (d), all of which need P5c.
- **Path class:** security. Extended review: yes, Tier A (see the header for the round rules that apply now).
- **Depends on (merged first):**
  - The merge chain of order 20 item 4 (P1m, P1a, P1b, P3a and the P4d chain, P2a-1, P2d-1, P2d-2, P4a). P1a is no longer needed by P6a itself (S5 cut).
  - P4b1 and P4b2: their memory-store text relays the refusal P6a pins (`tickets/P4b1.md:82` "P6a refuses it in a client profile", `tickets/P4b2.md:238`).
  - P4c: P4c-2 edits `app.py` before P6a (`tickets/P4c.md:19`).
  - P5b1 to P5b5 (they lie on the path to P5c).
  - P5c, all 4 PRs: the redactor kind and its T1-12 (green at P6a's base), the masking wrapper, the choke-point test T3-07, and the `isinstance` rows T3-06.
  - P6b1: its no-training refusal must still accept `pilot_cfg` and `prod_cfg`.
  - P6b2: A9 F6 says "P6a depends on P6b1, P6b2, P4b1, P5c".
  - Ticket states, as read today: P1 revision 16 FROZEN; P2a revision 10 FROZEN; P4a revision 12 FROZEN; P4b1 revision 2, P4b2 revision 3, P4c revision 2, P5b1 revision 2, P5b2 revision 3, P5b3 revision 1, P5b4 revision 1, P5b5 revision 1, P5c revision 1, P6b1 revision 3, P6b2 revision 1. All of these are drafts in review, so P6a "depends on" those revisions, not on clean ones.
  - Merge position: last v1 package before P8a (plan section 7 step 7: "P5c, then P6a"), unless PENDING LEAD 8 (a) moves P6a-1 earlier.
  - **Hot files** (rule 10, A4, A9 F6):
    - `app.py`: P2a-1, P4b2-b, P4c-2, P5c-3 (P5c also edits it, `tickets/P5c.md:46`), then **P6a last**. A9 F6 puts P6b2 on `app.py` too, but P6b2 revision 1 lists `app.py` as NOT changed (`tickets/P6b2.md:173`). So on this file P6a waits for no P6b2 edit.
    - `tests/test_k5_producers.py`: after P5c.
    - `CHANGELOG.md`: append only.
    - A9 F6 also lists P6a on `config.py`, `cli.py`, `backends/table.py` and `tests/test_lockin_guard.py`. P6a revision 2 edits none of them, so it takes no slot there and blocks no one (PENDING LEAD 10, an INFORM).
    - `defaults.py`: P6a adds no constant (order 20 item 5).
- **Problem in plain words:** A client deployment must never run with a part that exists only for testing: a fake model, a fake approval channel, secrets read from the environment, an in-memory store, a frozen clock. The configuration check for test-only kinds already exists and is tested. But a program that builds the app in Python can still hand in test objects in a pilot or production configuration, and nothing stops it. This package adds a refusal for that case, as a guard against accidents (a copied test fixture), not as a lock against the operator's own code. It also replaces the test that looks for code in `src/` calling the model directly, so that alias forms like `getattr(llm, "chat")` are found too. The real lock on the model path is P5c's: the core only accepts the masking wrapper.
- **Source of the code and what is NOT taken:** nothing is promoted from another repository. The work extends core main after P5c. Design sources: plan-v3 row P6a, rule 9(g), note 6; A6, A9 F6; P5c revision 1 (`tickets/P5c.md`); memo-6 (rule 9(g) row). NOT taken: plan-v2's per-kind flag list (it named `hmac_v0`, a v1.1 kind; review-plan-2 M14); any change to `DEV_ONLY`'s members; a new profile object; a claim that the executor is a kind (A6: it is not; in pilot and prod `app.build` builds no executor, `app.py:172-174`); the round-1 proposals of a WARNING log line, an `app.test_doubles` attribute and a `cli` refusal (resolve row ADV-6: `cli.py:299` passes no keyword, so a `cli` refusal could never fire, and the log line and attribute protect nothing against the operator's own code).
- **Target module and path in `src/hadavin_sdk/`:** `app.py` only (S2). Everything else is in `tests/`.
- **Interface (names, argument and return types, errors):**
  - `app.build(config_dir, agents, *, secrets=..., ..., timeout_s=None, allow_test_doubles: bool = False) -> App`: a new keyword-only argument, default `False`.
  - Module-level, computed once from `inspect.signature(build)`: the tuple of build keywords, i.e. every keyword-only parameter except `allow_test_doubles`, in signature order.
  - Private pure helper `_test_doubles_given(params: Mapping[str, inspect.Parameter], given: Mapping[str, object]) -> list[str]`. It returns, in `params` order, the names whose value in `given` `is not` that parameter's default. It compares by identity, never by truth value.
  - **Where it runs.** The first statement of the `build` body records the given keyword values, BEFORE `app.py:82` rebinds `secrets` (item 5; correction N1). The check itself runs right after the `tools=` check (`app.py:93-98`), so the four existing refusals keep their messages and their order. It runs before the configured sources are built (`:107-110`) and before any backend other than the secrets provider (`:82`).
  - **What it raises.** When `live` and not `allow_test_doubles` and the helper's list is non-empty: `ConfigError(f"{names} replace configured parts and are for tests; in pilot and prod pass allow_test_doubles=True only from a test")`. `names` is every given keyword as `name=`, joined by `", "`, all at once (the rule of `config.py:365`). In dev the keyword has no effect.
  - Test helper `tests/_model_calls.py`: `model_call_sites(roots: list[tuple[Path, str]]) -> set[tuple[str, str]]` returns `(prefix + module path relative to its root, as posix, dotted enclosing function or "<module>")` for every model-call site (definition above). Aliases of `attrgetter`/`methodcaller` are resolved within the module (`from operator import attrgetter as g`). A syntax error in a scanned file fails the scan, never skips it. Two sibling functions in the same file: `make_llm_callers(roots)` (calls of `make` whose first argument is the constant `"llm"`) and `dynamic_attr_sites(roots)` (calls of `getattr`/`attrgetter`/`methodcaller` whose name argument is not a constant). Both return the same tuple shape.
  - `_sink_callers` becomes `{m for m, _ in model_call_sites([(ROOT, ""), (REPO / "demos", "demos/")]) if not m.startswith("llm/")}`. It keeps its signature (no argument) and the demos root.
- **Neutral default / working alternative:** not a kind. Default behaviour: refuse. There is no alternative to write. The outline for a different profile mechanism (a named profile object with its own refusal table) is not needed until a client needs more than `pilot` and `prod` (V5).
- **Files to create, change, delete (each with the reason):**
  - Create `tests/test_client_profile.py`: rows T0, T1, T2, T5, T6 (the plan section 9 test file).
  - Create `tests/_model_calls.py`: the one scanner (S4).
  - Change `src/hadavin_sdk/app.py`:
    - the keyword record and the check (S2);
    - the docstring line "The keyword overrides replace one configured backend (tests)" (`app.py:76-77`) gains "and are refused in pilot and prod unless allow_test_doubles=True".
  - Change `tests/test_k5_producers.py`: `_sink_callers` (`:78-95`) uses `model_call_sites` as above. Behaviour: it now also counts alias forms. On today's tree the result is unchanged (item 7).
  - Change P5c's T3-07 `test_raw_llm_import_graph_ast` (file PENDING P5c): its part (a) uses `model_call_sites`.
  - Change `tests/test_k3_pilot_env.py:185` and `tests/test_k5_round8_postgres.py:40`: add `allow_test_doubles=True` (item 9).
    - The builder recounts after P5c with a script that loads each test config's `environment`. P5c changes how tests build the model (`tickets/P5c.md`, P5c-3), and the S2 rule also catches live builds that pass `clock=`, `hold_run_ids=` or `timeout_s=`.
    - The builder lists each changed test with the reason. Never by loosening the check.
  - Change `CHANGELOG.md`: one entry. Behaviour change: a live build with any build keyword needs `allow_test_doubles=True`. Also the plain-words limit of S2.
- **Existing core code reused (what I checked):**
  - Reused:
    - `Config._cross_checks` and `_anchor_refusals` (`config.py:350-397`);
    - `DEV_ONLY`, `NOT_PROD`, `DEFAULTS`, `TABLE` (`backends/table.py:593`, `:604`, `:582`, `:386`);
    - `deferred.LIVE` (`deferred.py:33`);
    - the `sources=`/`tools=` refusal pattern (`app.py:90-98`);
    - `tests/test_p1b_backends.py:89-102` (named as the pin and as a mutant killer);
    - `pilot_cfg` (`tests/test_k3_pilot_env.py:35`), already imported by other tests as `from tests.test_k3_pilot_env import pilot_cfg` (`tests/test_k5_round5.py:222`);
    - `SINK_METHODS`/`_sink_callers` (`tests/test_k5_producers.py:22`, `:78-95`) and `MODEL_CALLERS` (`guard/producers.py:55-65`);
    - P5c's redactor contract suite `tests/contracts/kinds/redactor.py` (`tickets/P5c.md:85`, PENDING P5c).
  - Checked and not duplicated: `coverage_problems` (`tests/test_lockin_guard.py:406-430`; a different question, see S1).
  - Checked and not needed: `hashing.py`, `k1b/atomic.py`, `k1b/redaction.py`, `stats.py`, `evals.py`, `store/memory.py`, the other suites in `tests/contracts/`.
  - **`prod_cfg` fixture (resolve row COR-2), test-local in `tests/test_client_profile.py`:** call `pilot_cfg(tmp_path, env="prod")`, then edit its `config.yaml` so that:
    - `backends.signer` = `{kind: ed25519_local, private_key_secret_name: audit-key}`;
    - `backends.anchor` = `{kind: s3_object_lock, bucket: <made-up bucket>, region: <made-up region>, retention_ack: true}`.

    The audit kind is already `chain` (`tests/test_k3_pilot_env.py:59`), which the anchor needs (`config.py:383-384`). Settings fields: `table.py:156`, `:162-164`, `:217-218`. The builder fills the two `<made-up ...>` placeholders with obviously made-up words, never real-looking names. Row T0 proves it loads. NOT run-checked by me.
- **Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):** P6a adds no role, grant, credential, network call or secret read. All checks run in the process at start-up. It changes no member of `DEV_ONLY`. It holds no personal data: refusal messages name keywords and kind names only, never a value. What P6a does NOT give, in plain words:
  - (a) It checks configuration and the `app.build` arguments. A client's own code that calls a model directly, outside `app.build` and outside `src/`, is not checked.
  - (b) `allow_test_doubles=True` is a named switch, not a lock. A client's code can pass it. The AST row keeps it out of `src/` and `demos/` only.
  - (b') Code can change the app after `build` (for example replace `app.runtime.hooks.hold_run_ids`) or build `Runtime` itself. P6a does not see that. P5c-3's `isinstance` check in `Runtime.__init__` still refuses a raw model there (`tickets/P5c.md:66`).
  - (c) The scanner finds the two attribute names and the constant-name forms only. A name built at run time is not followed (`getattr(llm, "ch" + "at")`, a variable). Instead, every non-constant `getattr` must sit on a reviewed list (T6 (g)). `vars(x)["chat"]` and `x.__getattribute__("chat")` are not found. `exec`/`compile`/`importlib` are not followed: today there is one `exec`, the pinned tool-module loader (`tools.py:389`). The real guard is P5c's `isinstance` check and import-graph test.
  - (d) Selecting the redactor does not mean every value is masked. The owner-visible limits of order 19 B stand:
    - secrets of 8 to 11 characters (common passwords) are caught only as plain copies (order 15);
    - other-case and re-broken copies of stored names and addresses are sent;
    - copies hidden as base64, hex or invisible characters are caught only where the existing tool-secret forms cover them;
    - copies with extra inserted characters are sent.
  - (e) The demo `demos/ask-your-data/askdata/pipeline.py:155` calls the model directly and is outside the wrapper test (V2). The registry check still lists it.
  - (f) `guard/bedrock_guardrail.py` sends text to a vendor service outside the llm kind. P6a only pins that it is the one `apply_guardrail` site. Whether its input is masked is P5c's.
  - (g) The check keys on `environment` only. A config labelled `dev` that holds client data is not refused (PENDING LEAD 11; this needs the owner).
- **Tests** (all in `tests/test_client_profile.py`; "pin" as defined above; prod rows use `prod_cfg`; refusal rows use `pytest.raises(ConfigError, match=...)` on the new text, so on the base a different error later in the build cannot make them pass):
  - **T0 prod fixture (1 row).** `load_config(prod_cfg(tmp_path))` loads. No Postgres needed.
  - **T1 dev-only rows not covered elsewhere (3 rows).** (a) A `pilot_cfg`-based config with `secrets: {kind: env}` is refused in pilot and in prod, with `environment <env>: refused` and `secrets: env` in the message (2 rows). (d) A pilot config whose `backends` omits `store` is refused, with `store: memory` in the message (1 row). Every other pair, the all-at-once message and PL61's `llm: fake` row are pinned by `tests/test_p1b_backends.py:89-102`, named here, not repeated.
  - **T2 completeness (7 rows).**
    - (a) `DEV_ONLY` equals the expected set exactly: the 6 pairs, plus any pair a v1 package adds, which that package writes into this row.
    - (b) Every pair of `TABLE` is in exactly one of `DEV_ONLY` and `CLIENT_REVIEWED`, and each `CLIENT_REVIEWED` entry has a non-empty reason.
    - (c) Three planted rows. The check function is called with a `TABLE` copy holding an extra kind in neither set: reported. A pair planted in both sets: reported. A `CLIENT_REVIEWED` entry with an empty reason: reported.
    - (d) Every `TABLE["redactor"]` kind not in `DEV_ONLY` is in the backend list of P5c's `tests/contracts/kinds/redactor.py` suite, so it must pass the masking rows. How the list is read is PENDING P5c. A pass-through kind put in `CLIENT_REVIEWED` without being in that suite fails here.
    - (d2) Planted: a `TABLE` copy with a redactor kind missing from that list is reported.
  - **T5 build keywords in a client profile (29 rows).**
    - (a) Pilot `pilot_cfg` plus `llm=ScriptedLLM(...)`, no switch: refused, message names `llm=` and `allow_test_doubles` (1).
    - (b) Parametrised over the build keywords read from the signature, minus `sources` and `tools` (they have their own messages). Today that is `secrets`, `channel`, `detector`, `llm`, `hold_run_ids`, `clock`, `timeout_s`, each refused alone in pilot and in prod (7 x 2 = 14). The `clock=` rows are the resolve's "clock row".
    - (c) All seven at once: one message naming all seven in signature order (1).
    - (d) Postgres-gated, skips without `HADAVIN_TEST_PG_DSN`, runs in CI. With `allow_test_doubles=True`, the build of `tests/test_k3_pilot_env.py:185` succeeds, and `type(app.runtime.llm) is MaskedLLM` (name PENDING P5c) (1).
    - (e) Dev (`k5_cfg`) with overrides and no switch: builds, unchanged (1).
    - (f) `sources=` AND `llm=` in pilot: the `sources=` message (`app.py:92`), so the new check comes after it (1).
    - (g) AST over `src/hadavin_sdk/` and `demos/`. It fails on any `ast.keyword` with `arg == "allow_test_doubles"` in ANY call (this covers `functools.partial(build, ...)`), and on any `**` expansion (`keyword.arg is None`) in a call whose function name is `build`. One real-tree row, plus three planted modules in a `tmp_path` tree, each reported: a direct keyword, `partial(build, allow_test_doubles=True)`, and `build(**opts)` (4).
    - (h) `tools=` AND `llm=` in pilot: the `tools=` message, so the new check comes after it. `tests/test_k5_round5.py:226` is the existing pin (1).
    - (i) Falsy double: a channel stub whose `__len__` returns 0, in pilot: refused (1).
    - (j) Placement: monkeypatch `app.make` to record each capability it builds. A refused override leaves the record within `{"secrets"}` (1).
    - (l) Planted keyword: `_test_doubles_given` called with the signature of a stub function that has one extra keyword, given a non-default value: the extra name is reported (1).
    - (m) No override at all, in pilot and in prod: monkeypatch `app.platform_secrets.check` (`app.py:122`) to raise a sentinel. The sentinel is reached, so the new check let the build through (2; correction N1).
  - **T6 scanner (14 rows).**
    - (a) Real tree: `{s for s in model_call_sites([(src, "")]) if not s[0].startswith("llm/")}` equals exactly the six sites of item 7. P5c adds `llm/masked.py` inside `llm/`. Any new site outside `llm/` is added here with a reason and reviewed (1).
    - (b) `apply_guardrail` sites equal `{("guard/bedrock_guardrail.py", "GuardrailDetector.check")}` (1).
    - (c) Seven planted rows, each in a `tmp_path` tree with one planted module, each reported:
      - `getattr(llm, "chat")(...)`;
      - `f = llm.chat` then `f(...)`;
      - `functools.partial(llm.chat)`;
      - `operator.methodcaller("chat")`;
      - `from operator import attrgetter as g; g("chat")`;
      - a second function in an allowed module reading `.chat`;
      - `apply_guardrail` in another module.
    - (d) A file with a syntax error makes the scan fail (1).
    - (e) `"demos/ask-your-data/askdata/pipeline.py" in _sink_callers()` (the demos root is kept). The existing `test_every_module_that_calls_a_model_is_registered` (`tests/test_k5_producers.py:98`) stays green unchanged (1).
    - (f) `make_llm_callers([(src, "")])` equals a fixed set. Today that is `{("app.py", "build"), ("cli.py", "_main"), ("cli.py", "_k1b")}`. P5c-3 moves the `app.py` one into `app.build_llm` and re-pins it here. This overlaps P5c's T3-07 (b) (`tickets/P5c.md:81`): PENDING LEAD 12 (1).
    - (g) `dynamic_attr_sites([(src, "")])` equals a reviewed list of 11 `(module, function)` pairs (item 7; 12 call sites), each with a one-line reason in the test file. A new one fails. (g2) Planted: a module with `getattr(x, name)` is reported (2).
  - **Row total for `tests/test_client_profile.py`: 54** (T0 1, T1 3, T2 7, T5 29, T6 14). It is 53 if PENDING LEAD 12 (a) drops T6 (f). Revision 1 had 70 rows.
  - **Fail-before, part 1: the build keywords (S2).**
    - Run: copy `tests/test_client_profile.py` and `tests/_model_calls.py` into a scratch worktree of the base, i.e. the commit just before P6a, after P5c is merged. Run the file there.
    - Expected FAIL (18 rows): T5 (a), (b) (14), (c), (i), (j). Each fails because the refusal does not happen: either no error, or a different error later in the build. Neither is a pass.
    - Not fail-before rows (2): T5 (d) fails with `TypeError` (unknown keyword `allow_test_doubles`); T5 (l) fails because `_test_doubles_given` does not exist. Both count for nothing.
    - Expected PASS, pins (34): T0, T1, T2, T5 (e), (f), (g) (4), (h), (m) (2), all of T6. T6's planted rows test the new helper, which is copied, so they have no fail-before by design. T5 (g) passes because nothing passes the switch yet; its killers are its planted rows and mutants 20 to 22.
    - Revision 1's table expected T5 (f) to fail on the base. It passes there: the `sources=` refusal already exists (correction N2).
    - The table (row, expected on base, seen) goes into the evidence file.
  - **Fail-before, part 2: the alias-proof scan (S4).** This shows the defect of today's call-only scan with no new helper copied. For each of the 5 alias forms of T6 (c) (getattr, `f = llm.chat`, `partial`, `methodcaller`, `attrgetter as g`), plant one module `src/hadavin_sdk/_p6a_planted.py` holding that form. Plant it once in a scratch worktree of the BASE and once in a scratch worktree of the P6a commit. In each, run `tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered`.
    - Expected on base: PASS. The old scan misses the planted module; that is the defect.
    - Expected on the P6a commit: FAIL, naming `_p6a_planted.py`.
    - Total: ten runs, raw output in `failbefore-s4.txt`. `_sink_callers` keeps its signature, so the base run cannot fail by `TypeError`.
  - **Hostile inputs:** the T6 (c) and (g2) planted forms; the three T5 (g) planted forms (including `**opts`); the T5 (i) falsy double; the T2 (c) and (d2) planted kinds.
  - **Race/process tests:** none (no state, no money).
  - **Contract suite:** not a kind; none. T2 (d) reads P5c's redactor suite.
- **Mutation plan.** Each mutant is one hunk and has a named killer. Mutants are cited by code text, not line numbers, because P4b1, P5c and P6b1 edit `config.py` first. They run under P1m's mutation runner; its invocation is UNVERIFIED until P1m merges, and whether it can mutate files under `tests/` (mutants 20 to 37) is UNVERIFIED too.
  1. `("llm", "fake")` removed from `DEV_ONLY`: `test_p1b_backends.py:89` (`llm: fake`), T2 (a).
  2. `("channel", "fake")` removed: `test_p1b_backends.py:89`, T2 (a).
  3. `("secrets", "fake")` removed: `test_p1b_backends.py:89`, T2 (a).
  4. `("secrets", "env")` removed: T1 (a), T2 (a).
  5. `("store", "memory")` removed: `test_p1b_backends.py:89`, T1 (d), T2 (a).
  6. `("audit", "local_dir")` removed: `test_p1b_backends.py:89`, T2 (a).
  7. In `_cross_checks`, `if self.environment != "dev"` becomes `== "prod"`: T1 (a) pilot row, T1 (d), `test_p1b_backends.py:89` pilot row.
  8. `', '.join(refused)` keeps only the first refusal: `test_p1b_backends.py:89` (it asserts all items in one message).
  9. The new check deleted: T5 (a).
  10. The check looks only at `llm`: T5 (b) rows for the other six keywords.
  11. `allow_test_doubles` default `True`: T5 (a).
  12. The check uses `cfg.environment == "prod"`: T5 (b) pilot rows.
  13. The check placed before the `sources=` check: T5 (f).
  14. The check placed before the `tools=` check: T5 (h).
  15. The helper compares by truth value instead of `is not` the default: T5 (i).
  16. The check placed after `make("store", ...)`: T5 (j).
  17. The keyword record taken after `secrets = secrets or make(...)`: T5 (m) (the rebound provider is never the default, so every live build would be refused).
  18. The names taken from a fixed list of the original four instead of the signature: T5 (b) `hold_run_ids`, `clock`, `timeout_s` rows; T5 (l).
  19. The message names only the first keyword: T5 (c).
  20. T5 (g) checker: the `allow_test_doubles` keyword branch deleted: T5 (g) direct-keyword planted row.
  21. T5 (g) checker: keywords checked only in calls named `build`: T5 (g) `partial` planted row.
  22. T5 (g) checker: the `**` branch deleted: T5 (g) `**opts` planted row.
  23. Scanner: the `getattr` branch deleted: T6 (c) getattr row.
  24. Scanner: the `attrgetter` branch deleted: T6 (c) `attrgetter as g` row.
  25. Scanner: the `methodcaller` branch deleted: T6 (c) methodcaller row.
  26. Scanner: alias resolution deleted (only the literal name `attrgetter` matched): T6 (c) `attrgetter as g` row.
  27. Scanner: only `ast.Call` function attributes counted (today's shape): T6 (c) `f = llm.chat` and `partial` rows.
  28. Scanner: compares modules only, not functions: T6 (c) second-function row.
  29. Scanner: `apply_guardrail` dropped from the names: T6 (b), T6 (c) apply_guardrail row.
  30. Scanner: a syntax error skips the file: T6 (d).
  31. `_sink_callers` drops the demos root: T6 (e).
  32. `dynamic_attr_sites`: the non-constant branch deleted: T6 (g2).
  33. `make_llm_callers` matches only `make` by bare name, not as an attribute, or returns nothing: T6 (f) real-tree row.
  34. T2 check: a pair in both sets not reported: T2 (c) both-sets row.
  35. T2 check: the empty-reason rule removed: T2 (c) empty-reason row.
  36. T2 check: a kind in neither set not reported: T2 (c) neither row.
  37. T2 (d) check: the redactor suite's backend list not read: T2 (d2).

  Count: 37 mutants (revision 1 had 16). If PENDING LEAD 12 (a) drops T6 (f), mutant 33 goes with it (36). A mutant found equivalent at build time is reported to the lead with its diff, never dropped silently (P4a PL65 rule).
- **Evidence commands (exact), raw output saved under `handover/evidence/P6a/`, summary in `evidence-p6a.md`:**
  - `uv run --all-extras --group test pytest tests/test_client_profile.py -q -rA 2>&1 | tee handover/evidence/P6a/client-profile.txt` (with the Postgres service, as CI, so T5 (d) runs; the evidence says whether it ran or skipped).
  - Fail-before part 1:
    1. `git worktree add <scratch>/p6a-base <base commit>`;
    2. copy `tests/test_client_profile.py` and `tests/_model_calls.py` into it;
    3. `uv run --all-extras --group test pytest tests/test_client_profile.py -q -rA 2>&1 | tee handover/evidence/P6a/failbefore.txt`;
    4. `git worktree remove <scratch>/p6a-base`.
  - Fail-before part 2:
    1. worktrees `<scratch>/p6a-base` (base) and `<scratch>/p6a-head` (P6a commit);
    2. for each of the 5 forms, write `src/hadavin_sdk/_p6a_planted.py` in both;
    3. run `uv run --all-extras --group test pytest "tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered" -q -rA` in each;
    4. append all ten outputs to `handover/evidence/P6a/failbefore-s4.txt`;
    5. remove both worktrees. The planted file is never committed.
  - `uv run --all-extras --group test pytest -q 2>&1 | tee handover/evidence/P6a/full-suite.txt` (Python 3.13, as CI, `.github/workflows/ci.yml:73`, `:109`).
  - `ruff check src tests demos` and `ruff format --check src tests demos` (CI's lint steps) into `handover/evidence/P6a/lint.txt`; `bandit -q -r src demos -ll` (`ci.yml:119`) into `bandit.txt`.
  - The recount of live builds that need the switch (script reading each test config's `environment`) into `live-builds.txt`.
  - Whether `tests/` ships in the wheel: `build-backend = "uv_build"` (`pyproject.toml:58`) and grep finds no include setting. That only `src/hadavin_sdk` is packed is my knowledge of the default, UNVERIFIED. The builder runs `uv build` and lists the wheel's files into `wheel-files.txt`.
  - Mutants: the P1m runner over the 37 entries above into `mutants.txt`; every row read: KILLED with its killer named.
- **Reviewers:** correctness + adversarial, fresh agents; they get the diff, this ticket and the evidence only. The adversarial reviewer is asked:
  - to find a side door to the model that T6 misses and that P5c's `isinstance` check does not catch;
  - to find a way a copied test fixture starts a pilot app with a test object that T5 misses.
- **Done =** plan rule 4 (two clean rounds in a row at the final commit, evidence green at that commit) and all gates green: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit; plan section 9 row "Client profile": `uv run --all-extras --group test pytest tests/test_client_profile.py` passes.
- **Rollback:** tag `pre-P6a` (the lead only). No migration, no stored data. One behaviour change, revertible by reverting the merge and listed in CHANGELOG: a live build that passes any build keyword needs `allow_test_doubles=True`. Nothing non-revertible.

## Later and v1.1 rows (nothing is silently lost)
| Id | What | Trigger |
|---|---|---|
| V1 | Per-`Entry` `dev_only` field instead of the `DEV_ONLY` set (plan rule 9(g)'s literal wording) | a kind needs a per-settings decision (dev-only for some settings only) |
| V2 | Scan `demos/` with the wrapper test; the ask-your-data pipeline calls the model directly (`pipeline.py:155`) | a demo is run with client data, or P8a re-pins that demo |
| V3 | Signed audit record of the profile (environment, kinds, no-training statement) at start-up (P6b1 item 6) | a client or auditor asks for start-up evidence in the audit trail |
| V5 | A named profile object with its own refusal table | a client needs a third live environment beside pilot and prod |
| V6 | Strict Unicode-data pin in live (`app.build` or `Config`), its owner, the `cli` paths that do not call `app.build` (`gate`, `replay`; was V4), and a skip on Pythons whose data differs (3.12 ships older data than the 15.1.0 pin; the 3.12 value is from reviewers' knowledge, not run here) | the lead answers `tickets/P1.md:47` (PENDING LEAD 9) |
| V7 | A "holds client data" marker that refuses a real model kind whatever `environment` says (P6b1 item 10 (a)) | the owner decides PENDING LEAD 11 for a marker |

## PENDING LEAD (my recommendation first)
1. **Build keywords in a client profile (S2).** (a) RECOMMENDED: one rule over every build keyword with a non-default value, refused in pilot and prod unless `allow_test_doubles=True`. It is worded as an accident guard. On today's tree 2 tests add the switch, both Postgres-gated; the builder recounts after P5c. (b) Refuse them outright, like `sources=`/`tools=`: then live-path tests cannot run without network (rule 9(d)); not workable. (c) State the hole only: zero code, but "dev-only parts refused" stays false for apps built in code. Confidence 75 percent; reversible.
2. CLOSED by the cut of S5 (moved to V6 and item 9).
3. **Redactor refusal owner.** Answered by fact, not by the lead: P5c revision 1 builds it (T1-12). P6a builds nothing for it and pins nothing extra. It reopens only if a later P5c revision drops T1-12. The P5c author should be told this line exists.
4. **One scanner (S4).** (a) RECOMMENDED: one helper `tests/_model_calls.py`, with the `roots` signature, used by P5c's T3-07, `test_k5_producers` and P6a. (b) P6a writes its own and leaves the two call-only scanners as they are: three scanners, two with the alias hole.
5. **"Client profile" = `environment` in `deferred.LIVE`; no new profile object.** RECOMMENDED: yes (cut; V5 keeps the idea).
6. **`demos/` out of the wrapper test (T6 (a)), kept in the registry check (`_sink_callers`).** RECOMMENDED: yes, as the plan row says `src/`; V2 with its trigger.
7. **Completeness list in the test file, not in `src/`.** RECOMMENDED: yes (A6: build on `DEV_ONLY`, no parallel flag); V1 keeps the per-kind field idea.
8. **Split P6a.** (a) RECOMMENDED: P6a-1 (S1, S2: T0, T1, T2 (a)-(c), T5 without the `MaskedLLM` assertion; on `app.py` after P4c-2, and P5c-3 then rebases on it) and P6a-2 (S4, T2 (d), (d2), the T5 (d) `MaskedLLM` assertion; after P5c-3). This needs A9 F6's "P6a depends on P6b1, P6b2, P4b1, P5c" to read "P6a-2 depends on those; P6a-1 depends on P4c-2". Reason: the hole for apps built in code closes many packages earlier, and each review is smaller. Cost: one more security-path pull request and result review. (b) Keep one pull request, last before P8a. Confidence 60 percent; reversible until P6a-1 merges.
9. **Strict Unicode pin wiring.** This answers `tickets/P1.md:47`'s "author proposal". (a) RECOMMENDED: warning only in v1 (P1a's default); strict-in-live becomes V6 with a 3.12 skip, built when a client asks. (b) A small separate ticket now, strict in `app.build` when live. (c) Strict in `Config` (covers the `cli` paths; every pilot config load fails on 3.12). P1 is FROZEN, so the lead records the answer as an amendment. Confidence 65 percent; reversible.
10. **INFORM.** P6a revision 2 edits only these files:
    - `src/hadavin_sdk/app.py`;
    - `tests/test_client_profile.py`, `tests/_model_calls.py`, `tests/test_k5_producers.py`;
    - P5c's T3-07 test;
    - `tests/test_k3_pilot_env.py`, `tests/test_k5_round8_postgres.py`;
    - `CHANGELOG.md`.

    Its A9 F6 slots on `config.py`, `cli.py`, `backends/table.py` and `tests/test_lockin_guard.py` are free. No answer is needed unless the lead disagrees.
11. **NEW. P6b1 item 10 asks P6a to refuse a real model kind in a config "marked as holding client data", whatever its `environment`** (`tickets/P6b1.md:532`, its recommended option (a)). No such marker exists in `Config`. Adding one is new design, against orders 7(3) and 8(1). Options:
    - (a) RECOMMENDED: P6a does not carry it. P6a states the limit in plain words (Security notes (g)), and V7 keeps the idea.
    - (b) P6a adds the marker and the refusal (a new `Config` field, so `config.py` joins P6a's files, last after P5c).

    Either way, the remaining risk is a client-data risk: a `dev`-labelled config with client data and a real model. P6b1's own text says that accepting it "needs the OWNER". So this item goes to NEEDS LEAD for the owner, and is not decided by me. Confidence 70 percent in (a); reversible.
12. **NEW. T6 (f) overlaps P5c's T3-07 (b)** ("every `make("llm", ...)` is inside `app.build_llm` or `cli.py`'s two named builders", `tickets/P5c.md:81`). The resolve asked for T6 (f) before it was seen that P5c already has this row. (a) RECOMMENDED: if T3-07 (b) is at P6a's base with the same assertion, the builder drops T6 (f) and mutant 33 and names T3-07 (b) as the pin. This is the same rule that cut T4. T3-07 (b) then uses `make_llm_callers`. (b) Keep both. Confidence 70 percent; reversible.

## UNVERIFIED (I did not read or could not run it)
- Every P5c name and file: `MaskedLLM`, `llm/masked.py`, `app.build_llm`, T1-12, T3-06, T3-07 and its file, `tests/contracts/kinds/redactor.py` and how its backend list is read. They come from P5c revision 1, a draft whose revision 2 is being written.
- That `prod_cfg` loads (row T0), and that `pilot_cfg`/`prod_cfg` still pass P6b1's no-training refusal once P6b1 is built.
- That constructing the `mounted_file` secrets provider at `app.py:82` works in a `tmp_path` config without a secrets folder. T5 (m) and the prod refusal rows need it; if it fails, the builder adds the folder in the fixture.
- Whether the other tickets that mention `app.py` (P4b1, P5b2, P5b3, P6b1) edit it. I checked only P2a, P4b2, P4c, P5c and P6b2.
- The final count of tests that need `allow_test_doubles=True` after P5c.
- The P1m mutation runner's command line, and whether it mutates files under `tests/`.
- That the wheel holds no `tests/` files (default of `uv_build`, from my knowledge).
- Python 3.12's Unicode data version (only relevant to V6).
- Nothing in this ticket was run as a test or against built code. The only things I ran are a read-only AST walk over `src/hadavin_sdk`, greps, and `git show`/`git diff --stat` on the read-only tree.

## CHANGELOG
**Revision 2 (2026-11-06, about 03:00 UTC / 08:30 IST), from `reviews/P6a-round1-resolve.md`.**

**Removed in this revision, and why** (so a reader sees exactly what is gone):
| Removed | Why | Where it went |
|---|---|---|
| S3 (P6a pins or builds the "redactor must be named" refusal) and its test T3 (4 rows) | P5c revision 1 builds the refusal and pins it in pilot and prod (T1-12); T3 duplicated it (ADV-3) | Depends-on line "P5c's T1-12 green at P6a's base"; PENDING LEAD 3 answered by fact |
| T4 (wrapper reached, dev only, 3 rows) | P5c-3's `isinstance` check in `Runtime.__init__`, `evals.gate`, `extract.extract`, `JudgeDetector.__init__` (T3-06) and mutant M30 (killer T3-06) already cover it (ADV-3) | one assertion `type(app.runtime.llm) is MaskedLLM` in T5 (d), in pilot |
| S5 (strict Unicode-data pin in live), T7 (4 rows), mutants 14 and 15, PENDING LEAD 2, v1.1 row V4, the P1a dependency, the CHANGELOG line about the pin | not in the plan row; rests on the unanswered `tickets/P1.md:47` "author proposal"; would break every live-app test on 3.12 (ADV-8 = COR-9 = COR-11) | v1.1 row V6; PENDING LEAD 9 |
| T1's 12 per-pair rows, 6 dev-load rows and T1c (two kinds at once) | duplicates of `tests/test_p1b_backends.py:89-102`, which already pins them all at once (ADV-10) | that test is named as the pin and as the killer of mutants 1-3, 5-8 |
| Mutant 16 (redactor check limited to pilot) | went with S3 | P5c's own mutants |
| The fixed list of four refused keywords | replaced by one rule over every build keyword (ADV-2) | S2 |
| `tests/test_k5_tools.py:1031`, `:1033` from the "tests to change" list | they are dev builds (ADV-5 = COR-3) | item 9 |
| "in any form" in the model-call definition | overclaimed (ADV-4 = COR-6) | narrowed definition; limits in Security notes (c) |
| The claim "P4a relies on P6a's PL61 rows" | P4a relies on `test_p1b_backends.py:89-102`, already on main (ADV-9) | item 2 |
| Five "no P5c ticket exists" statements | false: P5c revision 1 exists | P5c names used, PENDING P5c |

**Added or changed, by finding:**
- ADV-1 = COR-1 (Blocker): fail-before rebuilt in two parts. S4 uses planted modules in base and head worktrees, run against the existing `test_k5_producers` test. T5 (g) is now a pin with planted killers. T5 (d) and (l) are marked as not fail-before rows. Refusal rows match the new text.
- ADV-2: one keyword rule from the signature; T5 (b) covers 7 keywords x 2 environments; planted-keyword row T5 (l).
- ADV-3: T2 (d), (d2) (redactor kinds must be in P5c's contract suite); the T5 (d) `MaskedLLM` assertion.
- ADV-4 = COR-6: narrowed wording; T6 (f) (`make("llm"` callers); T6 (g), (g2) (non-constant `getattr` list, 11 functions, 12 sites, not 1 as ADV-4 said). Per-call-site counting declined, as the resolve contests: a second `.chat` in a listed function reads the same `self.llm`, which P5c-3 forces to be `MaskedLLM`.
- ADV-5 = COR-3: the list of tests to change is 2, both Postgres-gated; recount by script.
- ADV-6: "accident guard" wording in Problem, S2 and Security notes (b'). The WARNING log, `app.test_doubles` and the `cli` refusal are not added (cited reason under Source).
- ADV-7 = COR-5: T5 (f) with `sources=` plus `llm=`; T5 (h) with `tools=`; scanner mutants split per branch (23-29); all six pair mutants (1-6); falsy-double row T5 (i) and mutant 15; placement row T5 (j) and mutant 16; T2 mutants 34-36.
- ADV-9: PL61 sentence fixed; PENDING LEAD 8 (split).
- ADV-10: one line on why `CLIENT_REVIEWED` is not `NULL_KINDS`/`EXCEPTIONS`. The resolve contests that `audit/local_dir` is uncovered: it is covered (`tests/test_p1b_backends.py:97`).
- ADV-11: T5 (g) checks every call for the keyword, and `**` into `build`; 3 planted forms; wheel check in the evidence.
- ADV-12 = COR-4: `model_call_sites(roots)` signature; `_sink_callers` keeps the demos root; T6 (e).
- ADV-13: PL61 explained in the word list.
- COR-2: `prod_cfg` fixture, row T0, prod rows use it.
- COR-7: "before any backend other than the secrets provider".
- COR-8: A9 F6 slots stated free; PENDING LEAD 10.
- COR-10: mutants cite code text.
- COR-12: row total (54).

**Corrections found by me while re-reading (not in round 1):**
- N1: revision 1 (and the resolve's COR-7 wording) said the order of `app.py:82` and the check "does not matter". It does. `secrets = secrets or make(...)` rebinds the name, so a check placed after `:98` would always see a provider and refuse every live build. Fix: record the keyword values as the first statement of `build`. New row T5 (m) and mutant 17.
- N2: the resolve's fail-before table lists T5 (f) as FAIL on the base. It passes there, because the `sources=` refusal already exists. T5 (f) and (h) are pins whose killers are mutants 13 and 14.
- N3: the resolve cites the refusal join as `"; ".join`. The code is `', '.join(refused)` (`config.py:373`); mutant 8 uses the code text.
- Cite drift since revision 1: `tickets/P4b1.md:74` is now `:82`, `tickets/P4b2.md:240` is `:238`, `tickets/P4c.md:17` is `:19`. The `app.py` docstring line is `:76-77`, `Backends.llm` is `config.py:70`, `entries()` is `config.py:74-76`, and the prod signer rule is `config.py:395-396`.
- New couplings found: P6b1 revision 3 item 10 (PENDING LEAD 11, owner), and P5c's T3-07 (b) overlap (PENDING LEAD 12). P6b2 revision 1 does not edit `app.py` (hot-file line).

**Counts, re-derived:** test rows 54 (revision 1: 70); mutants 37 (revision 1: 16); fail-before part 1: 18 FAIL, 2 not counted, 34 PASS (54); fail-before part 2: 10 planted runs (5 forms x 2 sides); PENDING LEAD items 12 (2 closed, 3 answered by fact, 8 to 10 from the resolve, 11 and 12 new); v1.1 rows V1, V2, V3, V5, V6, V7 (V4 folded into V6).

**Revision 1 (2026-11-06, about 02:45 UTC / 08:15 IST):** first draft; 70 test rows, 16 mutants, 7 PENDING LEAD items.

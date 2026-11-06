# P6a round 3, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

TICKET REVIEW ROUND 3, CORRECTNESS: handover/tickets/P6a.md revision 3 (364 lines)
Read-only. I did not read handover/reviews/ or handover/evidence/. I ran no code and no git (no shell tool was available).

VERDICT: 0 Blocker, 0 Major, 5 Minor, 3 Nit. Every count you asked about is true. No code cite fails. The Minors are gaps in tracing or relays, not false statements.

## Findings (Blockers and Majors first, then Minors, then Nits)
id | severity | ticket line | problem | fix
--- | --- | --- | --- | ---
(none) | Blocker | - | none found | -
(none) | Major | - | none found | -
R3-COR-1 | Minor | 249-250, 296 | P5c-1 (T1-12, P5c.md:378) makes pilot and prod configs without an explicit `redactor` fail. P6a-1 lands first, and its rows T0, T1 and T5 use `pilot_cfg`/`prod_cfg` with no `redactor` key. After P5c-1 they go red unless someone adds the key. The relay lists only the `CLIENT_REVIEWED` line. `grep pilot_cfg\|test_k3_pilot_env\|test_client_profile` in P5c.md gives no match, so P5c does not plan this. | Add one relay sentence: P5c-1 gives `pilot_cfg` the explicit `redactor` key (as P4c's `alert_to` and P6b1's statement already require), so `prod_cfg` inherits it and T0/T5 stay green. Add "no redactor key in the fixture" to the UNVERIFIED list.
R3-COR-2 | Minor | 148, 167-168 | Step 0 says collect-only must print 42 on the base. T5 (b) is "parametrised over the refused keywords read from the signature". On the base the signature has no `allow_test_doubles` and no `_LIVE_HOOKS` (the import rule at line 115 bans module-level use of them). The ticket does not say how the five names are derived at collection time. A derivation that reads the P6a-1 signature, or that picks up `tools`, `sources`, `hold_run_ids` or `timeout_s`, would not give 10 items on the base. | State that T5 (b) builds its list at module level from `inspect.signature(app.build)` minus the literal names `tools`, `sources`, `hold_run_ids`, `timeout_s`, `allow_test_doubles`. Without that, the "42 on base" check can fail for the wrong reason.
R3-COR-3 | Minor | 156, 296-297 | T5 (m) in PROD is claimed to reach `_Reached` at `make("signer")` (`app.py:144`) and to PASS on the base. That needs `load_registry(cfg)` (`app.py:80`), `_toolbox`, `scope_problems` and `_unprobed_tools` to pass for a prod config. The UNVERIFIED list covers only T0 loading and the `made` provider. If prod fails earlier, T5 (m) prod would not PASS on the base and the 19 PASS count would be wrong. | Add "T5 (m) prod reaches the signer" to UNVERIFIED, or have the builder confirm it in the base run.
R3-COR-4 | Minor | 142, 197-198, 150, 152 | Line 142 says refusal rows match "the new text". T5 (f) and (h) must match the OLD messages (`configure Config.sources`, `plain callables`). The new message also contains `sources=`/`tools=`, so a loose match leaves mutants 13 and 14 alive. | In T5 (f) and (h), require a match on the old distinctive text and a non-match on `allow_test_doubles`.
R3-COR-5 | Minor | 41, 48-55, 257 | The 31 pairs, 25 `CLIENT_REVIEWED` entries, 5 refused keywords and 42 rows are all "today". Several packages merge before P6a-1 (P4a, P4d, P5b*, P6b1 and others). Only P5c and P6b2 get a relay about adding pairs. A pair added earlier makes T2 (b) fail at P6a-1's base, and the 42-item count would be off if T5/T7 are derived from `TABLE`. | Add: "the builder recounts TABLE at P6a-1's base and writes any extra pair into one of the two sets with a reason; row counts are fixed by the explicit lists, not by TABLE".
R3-COR-6 | Nit | 236 | `.github/workflows/ci.yml:86` is the `HADAVIN_TEST_PG_DSN` env line of the test step. The Postgres service is defined at `:39-40`. | Cite `:39-40` and `:84-88`.
R3-COR-7 | Nit | 20, 136 | `agent_loop.py:175-178` holds the `Hooks.hold_run_ids` field and a comment (the field is at `:178`). The hold is applied at `runtime/tick.py:203-205`. | Cite `tick.py:203-205` for "held".
R3-COR-8 | Nit | 87 vs template line 4 | The template reads "Extended review (no round cap): yes/no". The ticket says "yes, Tier A" and also says a 3-round cap applies. Orders 17 and 20 make the cap true, so the template label and the ticket disagree. | Write "Extended review: yes; ticket rounds capped at 3 by order 20 item 6".

## Counts: every one checked and true
- Rows 55 = 42 + 13.
  - P6a-1: T0 1, T1 3 (2 + 1), T2 5 (1 + 1 + 3), T5 26, T7 7 (4 + 1 + 1 + 1) = 42.
  - T5: (b) 10, (c) 1, (f) 1, (g) 4, (h) 1, (i) 1, (j) 1, (l) 1, (m) 2, (n) 1, (o) 2, (p) 1 = 26.
  - P6a-2 T6: (a) 1, (b) 1, (c) 7, (d) 1, (e) 1, (g) 1, (g2) 1 = 13.
- Mutants 45 = 35 + 10. Entries 1-35 and 36-45 are contiguous. Each has a named killer that is plausible, and none is obviously equivalent.
- Fail-before for P6a-1:
  - 19 FAIL = T5 (b) 10 + (c), (i), (j) 3 + T7 (a) 4, (a2), (d) 2.
  - 4 not counted = T5 (l), (p), (n) and T7 (b).
  - 19 PASS = T0 1, T1 3, T2 5, T5 (f) 1, (g) 4, (h) 1, (m) 2, (o) 2.
  - 19 + 4 + 19 = 42.
- Other counts that match:
  - Pairs: 31 (7, 6, 4, 2, 2, 5, 3, 2) and `DEV_ONLY` 6, so 25 in `CLIENT_REVIEWED`. The listed 25 entries are correct.
  - Finding ids: 27 = 14 + 12 + 1.
  - PENDING LEAD: 14 items, with 8 closed and 4 kept.
  - Open v1.1 rows: 6.
  - Template: all 17 fields are present, in the template's order.

## Verified (read this session)
- **`app.py`**
  - Keywords at `:62-75`, docstring at `:76-78`, `load_config` at `:79`, `reg` at `:80`, secrets rebind at `:82`, `live` at `:83`.
  - Evidence-key check at `:84-85`, purge-DSN check at `:86-89`, `sources=` at `:90-92`, `tools=` at `:93-98`.
  - `platform_secrets.check` at `:122`, signer/store at `:144`/`:146`, `llm` at `:162`, detector at `:163-169`, channel at `:170`.
  - Executor `None` when live at `:172-174`, `clock` at `:182`, `hold_run_ids` at `:225`, imports at `:27-28`.
- **`config.py`**
  - `_Strict` at `:52`, `Backends.llm` with no default at `:70`, `entries()` at `:74-76`, `environment` at `:317`.
  - `_cross_checks` at `:350`, `refused` at `:365-373`, `_anchor_refusals` at `:377`, `NOT_PROD` use at `:392`, COMPLIANCE refusal at `:385-390`.
  - `load_config` conversion at `:453-454`, relative paths at `:112`.
- **Other `src/`**
  - `table.py`: `TABLE` at `:386`, `DEFAULTS` at `:582-589`, `DEV_ONLY` at `:593-602`, `NOT_PROD` at `:604`.
  - `deferred.py:33`; `cli.py:150`, `:221`, `:299`.
  - `secrets_file.py:69-71`, `secrets_vault.py:162-195` and `:186`.
  - `tick.py:189-208`, `guard/producers.py:55-65`, `registry.py:131-155`, `tools.py:389` and `:407`.
- **Tests**
  - `test_p1b_backends.py:89-102`: the `secrets: env` item is absent from the asserted list.
  - `test_k3_pilot_env.py`: `:35`, `:38-39`, `:53`, `:59`, `:185`.
  - `test_k5_producers.py`: `:22`, `:78-95`, `:98`.
  - The five live-build callers: `round8:40`, `round5:226`, `round9b:370`, `round10:80`, `k3_pilot_env:185`. Round5 passes `secrets=` and `tools=`.
  - `test_k5_tools.py:756` and `:1031`, `round8:22-23`, `store_postgres.py:22-24`.
  - `test_p5_llm.py:38-46`, `test_p5p6_followups.py:82` and `:392`, `test_p1a_fixes.py:117` (`model_copy`), `fixtures/config/config.yaml:13` (`llm` fake).
  - `test_lockin_guard.py:406-430`, `pyproject.toml:58`, `ci.yml:73`, `:109`, `:119`.
  - `demos/` has no `app.build` call, and the only YAML with an `environment` key is the tests fixture.
- **Grep facts**
  - `make("llm"` occurs in `src/` exactly at `app.py:162`, `cli.py:150`, `cli.py:221`.
  - `exec(` occurs once in `src/` (`tools.py:389`), and `attrgetter`/`methodcaller` do not occur in `src/`.
  - Non-constant `getattr` is 12 sites in 11 functions, matching the T6 (g) list (`config.py:75`, `:271`; `table.py:59`, `:278`; `factory.py:54`; `registry.py:139`, `:148`; `models.py:139`; `protocol.py:159`; `k1b/tools.py:100`; `executor.py:37`; `tools.py:407`).
  - Model-call sites outside `llm/`: `judge.py:72`, `bedrock_guardrail.py:101` (the only `apply_guardrail`), `extract.py:47`, `agent_loop.py:425` (inside `Runtime.handle`, `:325-541`), `evals.py:73`, `k1b/loop.py:94`, and the demo at `pipeline.py:155`.
- **Pydantic settings**: `S3ObjectLockSettings` has `bucket`/`region`, `retention_ack` is on `_AnchorSettings`, and `Ed25519LocalSettings` has an exactly-one rule. The `prod_cfg` recipe is consistent with them.
- **Ticket cites**
  - `P5c.md`: `:27`, `:32`, `:66-67`, `:117-122`, `:161`, `:214-215`, `:259`, `:282`, `:289`, `:378`, `:425-426`, `:437`, `:509`. P5c has no other call-site scanner.
  - `P4c.md:40`, `:270` (the rollback line), `:307`; `P4b1.md:107`, `:115`, `:270`.
  - `P4b2.md:228`, `:255`; `P6b2.md:137-139`; `P6b1.md:120`, `:244`, `:251`, `:532`; `P1.md:47`.
- **Orders**
  - The lead orders I could read confirm the ticket's use of them: order 20 item 6 (cap and exception), orders 7(3) and 8(1), 15, 16 (two clean rounds kept for built code), 19 B, 22 items 24, 25 and 28/31 (option b).
  - The order text says P6a-1 is "app.py check, early". The ticket adds `config.py` under item 28(b) and flags this as PL14.
- **amendments**: A6 (executor is not a kind) and A9 F6 (the P6a dependency line) match the ticket's use of them.
- **Hypotheticals**: for a mutant or row that cannot be run here, I traced the code path by hand. The traced rows are T5 (b), (c), (f), (h), (i), (j), (m) and T7 (a), (d), plus mutants 7, 12, 15, 16, 20, 30 and 35. They behave as the ticket says, subject to R3-COR-3.

## Not checked (UNVERIFIED)
- The statements about `git diff --stat 124258b 397ec97`, commit `397ec97` and core commit `ce70eb5`. There is no git or shell here.
- The "22 decision rows", "5 order-22 rows" and "revision 2: 54 rows, 37 mutants" statements. They need `handover/reviews/`, which I may not read.
- The `NEEDS LEAD 50` / PENDING LEAD 14 wording against `questions-for-lead.md`.
- Plan-v3 section 6, section 9 and rule 4. I did not read the plan file.
- The "Ticket states" revision numbers at line 92. My grep output was too noisy to confirm them (P4c revision 3 and P5c revision 2 headers did match).
- Whether `prod_cfg` loads, and the full prod `load_registry` path (see R3-COR-3).
- That P5b2/P5b3 do not edit `app.py` or `test_k3_pilot_env.py`.
- The dotted names `k1b/loop.py _chat_bounded.work`, `evals.gate` and `extract.extract`. Only the lines and the `Runtime.handle`/`GuardrailDetector.check` names were checked.
- A complete list of tests that call `build(` in a live profile or load a dev config with a real llm kind or `bedrock_guardrail`. The ticket says "floor"; my greps found nothing extra. I did not read `tests/warden_port/test_providers.py` or `test_bedrock_provider_r16.py` beyond match counts.
- The P1m runner and whether it can mutate files under `tests/`.
- Whether the wheel excludes `tests/`.
- Whether `Backends` parsing of the pilot-with-no-store case gives exactly `store: memory` in the message. I confirmed `DEFAULTS["store"] = "memory"` and the refusal rule, not the final text.

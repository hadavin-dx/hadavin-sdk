# P6a round 3 resolve report (egm:egm-resolve, auto mode)

Status: resolved (categorised). The ticket is NOT edited here. This is the last ticket round (order 20 item 6; P6a is a security package, and the extra round of that item covers only money and redaction). So the fixes are build notes BN-1 to BN-13, not a revision 4. No round 4.
Target: `handover/tickets/P6a.md` revision 3 (364 lines, full file read; path class SECURITY, Tier A).
Inputs: `P6a-round3-adversarial.md` (R3-ADV-1..14: 0 Blocker, 2 Major, 8 Minor, 4 Nit; its verdict line says "7 Minors", but its table has 8, ADV-3 to ADV-10) and `P6a-round3-correctness.md` (R3-COR-1..8: 0 Blocker, 0 Major, 5 Minor, 3 Nit). 22 finding ids. Severity is counted by the tables and is never changed here.
Gate: the skill's "wait for the user" step is skipped (auto mode, per the brief). This file replaces the skill's default file name `goldfish_review_report.md`. Nothing is escalated to the owner. New PENDING LEAD items continue the ticket's numbering from 15. Each has a recommendation, and the build note states the default the builder takes meanwhile.

## Honest note (what I did NOT check, first)
- I ran no pytest, no mutant, no `uv`, no git write, no install and no network call. I ran one read-only probe script with the repository's existing virtual environment interpreter (`python -I`, in a scratch folder, `HADAVIN_TEST_PG_DSN` unset). It imported `tests.test_k3_pilot_env.pilot_cfg`, built the ticket's `prod_cfg`, called `load_config`, and called `app.build` with `app.make` patched as the ticket's `made` fixture describes. Results are in Facts. The probe is not evidence. The builder's base run is.
- I read the code on disk (core commit `ce70eb5` plus later edits, as the ticket says). I did not re-check the cites at `397ec97` or at P6a-1's real base, which does not exist yet.
- I read P2a, P4b2, P4c, P5b3, P4b1, P6b2 and P5c revision 3 only by grep, for new `build` keywords and `app.py` lines. "No new `build` keyword" (BN-3) is a grep fact, not a full read.
- I did not read the P1m runner, so whether it can mutate files under `tests/` is still UNVERIFIED. BN-4 gives the fallback.
- I did not check whether the Slack channel's masking is complete. I read `slack_channel.py:67-81` (the approval summary is redacted again through `runmap.redact_text`) and `runtime/agent_loop.py:278-284` (plan inputs are put back only for the approver's command, never into a card body). The masking limits of order 19 B apply to card text as to model text. BN-1 does not rely on the masking being complete.
- R3-ADV-1's decision (Slack in dev) is a lead decision (PENDING LEAD 15). I took the recommendation as the builder's default.

## Facts I checked myself (read on disk, unless marked "probe")
- **Slack is a real channel kind that sends text to a vendor.** `backends/table.py:558-565`: `channel` has `fake` (in `DEV_ONLY`, `:597`) and `slack` (`SlackChannel`, `hosts` = the API host). `SlackChannel.send`/`update` post the approval summary (`slack_channel.py:67-81`, `:123-135`, `:180-192`), `post_card` posts shadow and abstain cards (`:161-178`), and `notify` posts free text (`:194-198`). The shadow card body holds `canonical_json(plan.inputs)` and the diagnosis (`approvals/cards.py:66-96`). Plan inputs stay masked there (`agent_loop.py:278-284`).
- **Probe: a dev config with `channel: slack` and `llm: fake` loads today.** `pilot_cfg(..., env="dev")` with `llm: {kind: fake, recorded_dir: inputs}` loaded, with channel kind `slack`. S6 as written in revision 3 would not refuse it. So R3-ADV-1 is TRUE.
- **No existing test loads a dev config with Slack.** I grepped `tests/` and `demos/` for `kind: slack`, `"kind": "slack"` and `kind="slack"`. The 3 hits are `test_p7_tick.py:347` and `test_p5p6_followups.py:429` (both `SlackSettings(...)` objects, no `Config`) and `test_k3_pilot_env.py:64` (`pilot_cfg`). None of the 16 `pilot_cfg(` calls passes `env="dev"`. The one dev fixture, `tests/fixtures/config/config.yaml:15`, has `channel: fake`. This is a floor; the recount script (BN-1) is the final list.
- **Probe: T0 and T5 (m) on today's tree.** `load_config(prod_cfg)` loads, with environment `prod`. For the values, see BN-8. `app.build` in pilot and in prod, with no override and the `made` patch, raised `_Reached` at `make("signer")`, with `record == ["secrets", "signer"]`. So `load_registry` (`app.py:80`), the evidence-key and purge-DSN checks, `platform_secrets.check`, `scope_problems`, `_unprobed_tools` and `_toolbox` all pass for both fixtures on today's tree. This closes the UNVERIFIED notes behind R3-COR-3 and R3-ADV-9.
- **Probe: the build keywords today.** The keyword-only parameters of `app.build` are `secrets, channel, detector, llm, tools, sources, hold_run_ids, clock, timeout_s`. Minus the five literal names, the refused set is `secrets, channel, detector, llm, clock`, as the ticket says (`app.py:60-72`).
- **No new `build` keyword in the early `app.py` packages (grep).** P4c-2 wraps the model after `app.py:162` and adds an `App` field (`tickets/P4c.md:177`, `:192`). P4b2-b adds `App.maintenance_store` (`tickets/P4b2.md:228`). P6b2-a adds a config refusal (`tickets/P6b2.md:248`). P5c-3 wraps `build(llm=raw)` (`tickets/P5c.md:341`). None adds a keyword-only parameter to `build`. P2a's `environment` keyword (`tickets/P2a.md:84`) is on `Limits`, not on `build`.
- **The merge order (R3-ADV-2 is TRUE).** Order 20 item 4 (`LEAD-ORDERS.md:78`) names P1m, P1a, P1b, the P3a/P4d chain, P2a-1, P2d-1, P2d-2, P4a. P4c-2 and P4b2-b are not in it. Order 21 item 17 (`LEAD-ORDERS.md:88`) says "I will merge in dependency order". The ticket says P4c-2 is merged first, and P4b1/P4b2 are "text only" (line 89). Its `app.py` hot-file order puts P4b2-b before P6a-1 (line 94).
- **What S2 and S6 need from those packages: nothing.** S2 reads only `cfg` and the given keyword values, right after `load_config` (`app.py:79`). S6 sits in `Config._cross_checks`. P4c-2's edits come after `:162`, and P4b2-b's come at the store (`:146`). Both are below the S2 check.
- **P5c is now revision 3** (`tickets/P5c.md:1`, written from 03:44 UTC). P6a revision 3 cites P5c revision 2 line numbers, and those have moved. By name: `MaskedLLM.of` `:268`; the `Runtime` check `:273`, `:334` (it now also requires the inner model to be a `MeteredLLM`); the `app.py` wrap `:341`; T1-12 `:442`; T3-06 `:492`; T3-07 (b) `:490` (it still names `app.build_llm`); T3-17 `:504`; M30 `:573`. P5c revision 3 `:330` adds a pilot/prod fixture sweep for the explicit-`redactor` rule. It counts fixtures at `124258b`, so `tests/test_client_profile.py` (created by P6a-1) is not in that count.
- **PENDING LEAD 14 is answered.** Order 27 item 50 (`LEAD-ORDERS.md:146`): "P6a PL14: accept the `made_up_data_only` field; config.py belongs to P6a-1. I show this limit to the owner (it goes into handover/owner-visible-limits.md)." The ticket still marks it pending.
- **R3-ADV-10's line is not a config.** `tests/test_p5p6_followups.py:111-131` is a test parametrised over settings classes (`RegexSettings`, `JudgeSettings`, `GuardrailSettings`). It calls `model(**extra, threshold=0)` and expects `ValidationError`. It runs no `load_config` and has no `environment`. The recount script already lists `bedrock_guardrail` dev configs (ticket line 237, item (2)).
- **The scanner counts any read of `.chat`** (ticket line 22: "a read of the attribute `chat` ... (a call or not)"). So `ft.partial(llm.chat)` is found whatever `functools` is imported as.
- **Cites in the Nits.** `ci.yml:38-40` is the Postgres service, and `:84-88` is the test step with `HADAVIN_TEST_PG_DSN` at `:86`. The hold is applied at `runtime/tick.py:203-205`.

## Banner for the ticket (placed under the status line, word for word)
> **Build notes win.** Revision 3 is frozen text. Where a build note BN-1 to BN-13 (from `handover/reviews/P6a-round3-resolve.md`, copied into the section "Build notes (round 3)" at the end of this ticket) differs from the revision 3 text, the build note wins. The CHANGELOG sections are history, not instructions. Line cites into `tickets/P5c.md` were written against P5c revision 2: find each by its name (BN-12), not by its line number.

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX (lead decision PENDING LEAD 15; default taken) | TRUE (Facts, probe). Slack in dev is refused without `made_up_data_only: true`, the same rule as a real model. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX (cut a dependency; lead places the order, PENDING LEAD 16) | TRUE. P6a-1 does not depend on P4c-2 or P4b2-b. The `app.py` list is a rebase order, not a merge gate. **BN-2.** |
| R3-ADV-3 (Minor) | PROPOSE FIX | TRUE as a risk. The grep finds no new keyword today. The builder re-reads the signature at the base and reports any change. **BN-3.** |
| R3-ADV-4 (Minor) | PROPOSE FIX | TRUE. T5 (b) gets a sample table, and a keyword that has no sample and is not exempt fails collection by name. **BN-3.** |
| R3-ADV-5 (Minor) | PROPOSE FIX | TRUE. Fallback for mutants under `tests/`. **BN-4.** |
| R3-ADV-6 (Minor) | PROPOSE FIX (the `functools` part CONTESTED: the scanner counts any `.chat` read, ticket line 22) | TRUE for `operator`. One resolver for both names and all import forms, one planted row, one mutant. **BN-5.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | TRUE. Evidence table for T6 (a). **BN-6.** |
| R3-ADV-8 (Minor) | PROPOSE FIX (wording only; a second allowed set is DECLINED, order 8) | TRUE that `llm/` is exempt by prefix. State it and name the P5c rows that cover it. **BN-7.** |
| R3-ADV-9 (Minor) | PROPOSE FIX (the "add `load_registry` to T0" part CONTESTED: T5 (m) prod already runs it, and the probe shows it passes) | Exact made-up values given, and the builder confirms them at the base. **BN-8.** |
| R3-ADV-10 (Minor) | CONTEST | `test_p5p6_followups.py:111-131` builds settings classes directly (no `load_config`, no `environment`), so S6 never sees it. The recount script already lists `bedrock_guardrail` dev configs (ticket line 237). No build note. |
| R3-ADV-11 (Nit) | DECLINE | The sentence is about where an `environment` key appears, not about whether the key is optional. Changing it changes no builder action. |
| R3-ADV-12 (Nit) | DECLINE | Frozen text. Trimming the problem field changes no builder action. |
| R3-ADV-13 (Nit) | DECLINE | The ticket already says it: line 56 ("A later package that adds a pair adds it to one of the two sets in its own diff") and line 146 (T2 (a) "plus any pair a later package adds there in its own diff"). The redactor pair does not exist at P6a-1's base, so P6a-1 cannot test it. |
| R3-ADV-14 (Nit) | DECLINE | The reviewer says "None needed". |
| R3-COR-1 (Minor) | PROPOSE FIX | TRUE. P5c revision 3 `:330` plans a fixture sweep, but its count is at `124258b` and it does not name `pilot_cfg` or the P6a-1 rows. Relay sentence. **BN-9.** |
| R3-COR-2 (Minor) | PROPOSE FIX | TRUE. The derivation is stated: at module level, from the signature minus five literal names. On today's tree that gives 5 names (probe). **BN-3.** |
| R3-COR-3 (Minor) | PROPOSE FIX | The UNVERIFIED gap is closed for today's tree by the probe (`_Reached` at `make("signer")` in prod). The builder re-confirms at the base. **BN-8.** |
| R3-COR-4 (Minor) | PROPOSE FIX | TRUE. T5 (f) and (h) match the old distinctive text and assert that `allow_test_doubles` is absent. **BN-10.** |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE. Base recount rule. Rows derived from `TABLE` (T2 (b), T7 (a), T7 (a3)) may move the count, and the builder reports it. **BN-3.** |
| R3-COR-6 (Nit) | PROPOSE FIX | The evidence command points the builder at a line, so the cite is fixed: `ci.yml:38-40` (service) and `:84-88` (test step). **BN-11.** |
| R3-COR-7 (Nit) | DECLINE | The word-list cite is a definition, not a build step. The hold is at `runtime/tick.py:203-205` (Facts), for whoever needs it. |
| R3-COR-8 (Nit) | DECLINE | The ticket states the 3-round cap and its source in its header (line 3). The template label does not change what is built. |
| (resolve, own) N1 | PROPOSE FIX | P5c revision 3 moved every P5c line cite. **BN-12.** |
| (order 27 item 50) | lead answer | PENDING LEAD 14 is CLOSED. **BN-13.** |

## Build notes (round 3) - to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. A real approval channel in a dev config needs `made_up_data_only: true` (R3-ADV-1; PENDING LEAD 15, default taken).**
- S6 gains a third item. In `Config._cross_checks`, when `environment == "dev"` and `made_up_data_only` is not `true`, the `channel` kind is added to the one `refused` list (as `channel: <kind>`) when it is not in `DEV_ONLY`. Today that means `channel: slack`.
- Why: a real channel kind sends text built from case data to a vendor service (the approval summary, the shadow and abstain cards, the notices). That text is masked, with the order 19 B limits. This is the same reason S6 gives for the vendor detector.
- The rule is written as "not in `DEV_ONLY`", so it fails closed: a later channel kind (for example email, A6) is refused in dev too, until its package decides otherwise in its own diff.
- What S6 does NOT add, and why. Each of these kinds sends no case text out:
  - the `secrets` kinds send secret names and receive values;
  - the `signer` and `anchor` kinds send digests;
  - the `store` and `audit` kinds hold data in the operator's own database or folder, and do not send it to a vendor.
  - If a later kind sends case text out, its package adds it to S6.
- The one message's closing sentence becomes: "a dev config that names a real model, a vendor detector or a real approval channel sends text out: set made_up_data_only: true only when every input is made up; client data runs only in pilot or prod".
- New row **T7 (a3)**: one row per `channel` kind outside `DEV_ONLY`, read from `TABLE` (1 today: `slack`). A dev config with `llm: fake` (with `recorded_dir`), that channel and no field is refused, with `channel: slack` and `made_up_data_only` in the message. On the base it FAILS by assertion: the probe shows the config loads.
- New mutant **46**: "the S6 channel item dropped". Killer: T7 (a3).
- So that each T7 row proves one item, the other T7 rows (a), (a2), (b) and (d) use `channel: fake`.
- The recount script also lists every dev test config whose channel kind is not in `DEV_ONLY`. Grep finds none today (Facts). Each one found gets `made_up_data_only: true`; the check is never loosened.
- The CHANGELOG entry's change (2) reads "a dev config that names a real llm kind, the `bedrock_guardrail` detector or a real channel kind needs `made_up_data_only: true`".
- Security notes (f) and (g) read "a real model, the vendor detector or a real approval channel" wherever they say "a real model or the vendor detector".
- If the lead answers PENDING LEAD 15 with (b): drop the channel item, T7 (a3) and mutant 46, and add one sentence to Security notes (g): "a real approval channel in dev is allowed without the field, because its text is masked (`slack_channel.py:67-81`); the masking limits of order 19 B apply to it". The counts then go back.

**BN-2. P6a-1's merge gate (R3-ADV-2; PENDING LEAD 16).**
- "Depends on (merged first)" for P6a-1 reads: "the merge chain of order 20 item 4". P4c-2 is removed from it.
- P4c-2, P4b2-b and P2a-1 are NOT merge gates of P6a-1. S2 reads only `cfg` and the given keyword values, right after `load_config`. S6 sits in `Config._cross_checks`. Neither uses anything those packages add (Facts).
- The `app.py` hot-file line "P2a-1, P4b2-b, P4c-2, P6a-1, P5c-3, P6b2-a" is the preferred REBASE order, not a gate. Whichever of P2a-1, P4b2-b or P4c-2 has merged when P6a-1 starts, P6a-1 rebases on current main before its review (order 20 item 5 rule), and the later ones rebase on P6a-1.
- At that rebase, the builder runs BN-3 again.
- The P4b1/P4b2 "text only" sentence stands.
- The relays to P6b2 (`:139`) and P4c (`:40`, `:307`) say "preferred rebase order" instead of a fixed order.

**BN-3. Base recount and the T5 (b) list (R3-ADV-3, R3-ADV-4, R3-COR-2, R3-COR-5).**
- At module level, `tests/test_client_profile.py` computes `REFUSED = [n for n, p in inspect.signature(app_mod.build).parameters.items() if p.kind is p.KEYWORD_ONLY and n not in {"tools", "sources", "hold_run_ids", "timeout_s", "allow_test_doubles"}]`. These are literal names, not `_LIVE_HOOKS`, which does not exist on the base (the import rule). On today's tree this gives `secrets, channel, detector, llm, clock` (probe), so T5 (b) has 10 items on the base AND at head.
- T5 (b) and (c) take each keyword's non-default value from one test-local table `SAMPLES`:
  - `secrets`: the `made` provider;
  - `channel`: `FakeChannel()`;
  - `detector`: a stub detector;
  - `llm`: a `ScriptedLLM`;
  - `clock`: a lambda returning a fixed made-up time.
- At module level, `assert set(REFUSED) <= set(SAMPLES), f"build keywords with no sample: {sorted(set(REFUSED) - set(SAMPLES))}"`. A new keyword then fails collection with its name, and so it gets decided: either a sample (it is refused) or a reviewed `_LIVE_HOOKS` entry. That is the T7 (a) "fails so it gets decided" rule, at collection time.
- Base recount step, before step 0 of the fail-before:
  - The builder prints `inspect.signature(build)` and the `TABLE` pairs at P6a-1's base into `<handover>/evidence/P6a/p6a1-base-recount.txt`.
  - It classifies each keyword or pair that is not in this ticket's lists: keyword refused or `_LIVE_HOOKS`; pair `DEV_ONLY` or `CLIENT_REVIEWED`, with a reason.
  - The fixed counts (42 rows, now 43 with BN-1; 19 FAIL, now 20) are for today's tree. If the base moves them, the builder writes the new numbers and the reason in that file and in the PR body, and the step 0 collection count follows that file.
  - Rows from explicit lists never move. Rows read from `TABLE` (T2 (b), T7 (a), T7 (a3)) or from the signature (T5 (b)) may move, and each moved row is named.

**BN-4. Mutants under `tests/` (R3-ADV-5).** If the P1m runner cannot mutate files under `tests/` (mutants 23-28, 36-45 and 47), the builder runs them by hand:
- each mutant is one hunk, applied with `git apply` in the scratch worktree;
- the named killer rows are run there with the evidence command form;
- the patch text, the command, its output and `rc=` are appended to `<sub>-mutants.txt`;
- `git checkout -- tests` restores the tree, and `git status` is shown clean after each mutant.

The evidence says which mutants ran by hand. KILLED still means "the named killer failed".

**BN-5. `operator` forms the scanner must resolve (R3-ADV-6).** `model_call_sites` and `dynamic_attr_sites` use ONE resolver for the two names `attrgetter` and `methodcaller`. It accepts:
- (i) `operator.<name>`, where `operator` is the module imported under any name (`import operator` or `import operator as op`);
- (ii) `from operator import <name>`, with or without `as <alias>`.

Other ways to reach these names are not followed: a module object passed around, or `importlib`. Security notes (c) gains one sentence saying so. `functools` needs no rule: `partial(llm.chat)` is found by the `.chat` read whatever `functools` is called (ticket line 22).

New planted row **T6 (c) 8th**: `import operator as op; op.attrgetter("chat")`. It is reported. New mutant **47**: "the resolver matches only `from operator import ...` (the attribute form dropped)". Killer: the new row. The existing `methodcaller` row (attribute form) and `attrgetter as g` row (import form) now kill a resolver that handles one name only, because both names go through the one resolver. The P6a-2 fail-before keeps its 5 forms (the new row is a row of the new helper, ticket line 179).

**BN-6. T6 (a) evidence table (R3-ADV-7).** `<handover>/evidence/P6a/p6a2-sites.md` holds one row per site outside `llm/` at P6a-2's base, with these columns:
- `(module, function)`;
- in today's six (item 9): yes or no;
- for a "no" row, or for one of today's six that is gone, the P5c commit and the hunk (`file:line` in the P5c diff) that caused it.

The reviewer rejects a difference that has no hunk. T6 (a)'s written set is that table's first column.

**BN-7. The `llm/` exemption, stated (R3-ADV-8).** Security notes (c) gains this text: "The scan skips every file under `llm/` by prefix, as `_sink_callers` does today (`tests/test_k5_producers.py:86`). A new non-adapter file inside `llm/` that calls `.chat` is not seen by P6a-2. What covers it is P5c: T3-07 (b) keeps every `make("llm", ...)` in the named builders, T3-07 (c) keeps raw llm kind imports inside `llm/`, `backends/builtin.py` and `app.py`, and T3-06 plus `Runtime`'s `isinstance` check refuse a model object that is not the wrapper (P5c revision 3, by name). P6a-2 is a tripwire, not the guard." No second allowed set (order 8: the sentence closes the finding, and a second set would add surface to a tripwire).

**BN-8. `prod_cfg` values and the prod build path (R3-ADV-9, R3-COR-3).**
- `prod_cfg` is `pilot_cfg(tmp_path, env="prod")`, then its `config.yaml` is edited:
  - `backends.signer = {kind: ed25519_local, private_key_secret_name: audit-key}`;
  - `backends.anchor = {kind: s3_object_lock, bucket: madeup-bucket, region: madeup-region-1, retention_ack: true}`.
- Probe on today's tree: `load_config` loads it, and `app.build` with the `made` patch reaches `make("signer")` in pilot and in prod, with `record == ["secrets", "signer"]`.
- T0 stays `load_config` only. T5 (m) prod is the row that runs `load_registry` and the other start-up checks.
- The builder confirms both at the base in the fail-before table (T0 PASS, T5 (m) pilot and prod PASS). If either fails at the base, the builder fixes the fixture, never the row, and names the cause in the evidence.

**BN-9. Relay to P5c: the redactor key in P6a's fixtures (R3-COR-1).** Add to the P5c couplings: "P5c-1's sweep of pilot and prod fixtures for the explicit-`redactor` rule (`tickets/P5c.md:330`) includes `pilot_cfg` (`tests/test_k3_pilot_env.py:35`) and every fixture in `tests/test_client_profile.py`. `prod_cfg` derives from `pilot_cfg`, so one key there covers T0, T1 and T5. Without it, T0 and T5 (m), (n), (o) go red at P5c-1." Add to the UNVERIFIED list: "`pilot_cfg` has no `redactor` key today; after P5c-1 it needs one".

**BN-10. T5 (f) and (h) match the old text (R3-COR-4).** T5 (f) requires `match="configure Config.sources"` and asserts `"allow_test_doubles" not in str(err.value)`. T5 (h) requires `match="plain callables"` and the same absence. The "new text" rule of the Tests field applies to refusal rows of the new rule only. With this, mutants 13 and 14 fail on the absence check.

**BN-11. Postgres cite (R3-COR-6).** In the Postgres evidence command, read "the Postgres service as CI (`.github/workflows/ci.yml:38-40`, test step `:84-88`)".

**BN-12. P5c cites by name (own finding N1).** P5c is now revision 3 (`tickets/P5c.md:1`).
- Every `tickets/P5c.md:<line>` in P6a revision 3 was written against P5c revision 2. The builder finds each by its name:
  - `MaskedLLM` / `MaskedLLM.of`;
  - the `Runtime` check;
  - the `app.py` wrap;
  - T1-12, T3-06, T3-07 (b), (c), (d), T3-17, M30;
  - the hot-file list.
- Today these are at `:268`, `:273`/`:334`, `:341`, `:442`, `:492`, `:490`, `:504`, `:573` and `:156-164` (read now).
- "Ticket states" reads "P5c revision 3".
- P5c revision 3's `Runtime` check also requires `MeteredLLM` inside the wrapper (`:334`). This does not touch P6a's rows: every T5 row stops at `make("signer")` (BN-8), before `Runtime`.

**BN-13. PENDING LEAD 14 closed (order 27 item 50).** PENDING LEAD 14 reads "CLOSED by order 27 item 50: the field accepted, `config.py` belongs to P6a-1; the lead puts the limit in `handover/owner-visible-limits.md`". S6's "PENDING LEAD 14 = NEEDS LEAD 50, pending" wording is void.

## Positions
- **BN-1 adds design to a security path, on purpose.** Order 8 says cut surface. Here the cut would be the other option, (b): state that Slack in dev is allowed. That leaves a vendor receiving case-derived text from a config that never said its data is made up. It is the exact case the lead's option (b) of order 22 item 28/31 was chosen to close for the model. The added surface is one list item, one row and one mutant, and it breaks no test today (grep).
- **BN-2 removes a dependency instead of adding one.** P6a-1 is "early" (order 22 item 24). Gating it on two packages that are not in the lead's merge chain would make that impossible to plan. The functional fact (S2 and S6 use nothing from them) is checked.
- **BN-3 keeps the hard counts but makes them base-relative.** Today's numbers stay as the expected values. Only rows read from `TABLE` or the signature may move, and each move is written down. That is the fail-closed rule the ticket already uses for T7 (a).
- **BN-5 adds one row and one mutant, not four.** The resolver is one function. One planted row of the missing form, plus the two rows already there, kill every one-branch mutant of it.
- **BN-7 and R3-ADV-10 are wording or contest only.** Both findings are closed by a fact that is already true elsewhere (P5c's rows; a settings-class test).
- **The Slack masking was not judged here.** BN-1 does not depend on it. Whether card text is masked completely is P5c's question (redaction path) and is covered by the order 19 B owner-visible limits.

## Couplings
- BN-1 and BN-3: T7 (a3) is read from `TABLE`, so a channel kind added before P6a-1's base moves its count (BN-3 rule).
- BN-1 and BN-9: T7 (a3) is a dev config, so P5c-1's pilot/prod redactor rule does not touch it.
- BN-1 and PENDING LEAD 15: if the lead chooses (b), BN-1's reverse text applies, and the counts go back to 42 / 19 FAIL / 35 mutants for P6a-1.
- BN-2 and the relays to P6b2 (`:139`) and P4c (`:40`, `:307`): those tickets' fixed `app.py` order becomes a preferred rebase order. The lead passes this on with PENDING LEAD 16.
- BN-3 and BN-2: the recount runs again after every rebase of P6a-1.
- BN-4 and BN-5: mutant 47 sits in `tests/_model_calls.py`, under `tests/`, so BN-4's fallback may apply to it.
- BN-8 and BN-9: `prod_cfg` inherits P5c-1's redactor key from `pilot_cfg`.
- BN-12: the relays in the ticket's "To P5c" block cite P5c revision 2 lines too (for example `:117-122`, `:282`, `:426`). Read them by name: the hot-file list is `:156-164` and T3-07 (b) is `:490` in revision 3.
- To the kit (order 27 item 63): AK-G22 later puts Slack cards under a recipient gate. BN-1 is the v1 first line in dev and does not wait for it.

## PENDING LEAD (continuing the ticket's numbering after 14)
- **14: CLOSED** by order 27 item 50 (BN-13).
- **15. NEW. A real approval channel in a `dev` config (R3-ADV-1).** The builder's default meanwhile is (a).
  - (a) RECOMMENDED: refuse a `channel` kind that is not in `DEV_ONLY` in dev without `made_up_data_only: true`, as for a real model and the vendor detector. It costs one list item, T7 (a3) and mutant 46, and no existing test changes (grep). Reason: a vendor receives text built from case data, masked with the order 19 B limits, from a config that never said its data is made up.
  - (b) Allow it, with one sentence in Security notes (g) giving the reason (the card text is masked). This is smaller, but it leaves the same kind of outbound path open that S6 closes for the model.
  - Not an owner item: no money, secret, live call, or GitHub setting, and it reduces client-data risk. Confidence 80 percent. Reversible until P6a-1 merges.
- **16. NEW. INFORM: where P4c-2 and P4b2-b sit in the merge chain (R3-ADV-2).** The builder's default meanwhile: P6a-1 merges when the order-20 chain is merged, and does not wait for P4c-2 or P4b2-b.
  - Recommend: the lead places P4c-2 and P4b2-b in the order-20 chain, as order 21 item 17 says ("dependency order").
  - P6a-1 has no merge gate on them (BN-2). Whichever lands first, the others rebase, as order 20 item 5 says for `defaults.py`.
  - Reversible.

## Counts
- Finding ids 22 (ADV 14, COR 8). Majors 2 (ADV-1, ADV-2). No Blocker.
- PROPOSE FIX 15 (ADV-1 to ADV-9; COR-1 to COR-6), in build notes BN-1 to BN-11. CONTEST 1 (ADV-10). DECLINE 6 (ADV-11, 12, 13, 14; COR-7, 8). ESCALATE 0.
- Partial contests inside a PROPOSE FIX row: 2 (ADV-6, the `functools` part; ADV-9, `load_registry` in T0). Partial decline: 1 (ADV-8, the second allowed set).
- Own finding 1 (N1, BN-12). Lead answer 1 (BN-13).
- Ticket numbers after the build notes, if PENDING LEAD 15 stays (a):
  - P6a-1: 43 rows (T7 8). Fail-before on the base: 20 FAIL, 4 not counted, 19 PASS. 36 mutants (1-35 and 46).
  - P6a-2: 14 rows (T6 (c) 8). 11 mutants (36-45 and 47). 10 planted fail-before runs, unchanged.
  - Totals: 57 rows and 47 mutants (revision 3: 55 and 45).
- PENDING LEAD: 2 new (15, 16), 1 closed (14).
- Fixes applied to the ticket in this step: 0 (they are build notes). Remaining unaddressed findings: 0.

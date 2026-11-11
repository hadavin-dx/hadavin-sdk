<!-- full hand-back report of sub-agent a5ec89be, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

IMPLEMENTATION READINESS REVIEW, round 1 (Mode: REVIEW). Target: /home/user/hadavin-sdk/handover/tickets/Q8a-live-override-refusals.md

Verdict: NOT ready to build. A builder would have to make at least four design decisions the ticket leaves open (3 Blockers, 7 Majors, 4 Minors). Everything below was established by reading files only; nothing was executed (I have no run tools). See "Not checked" at the end.

Files read in full: the ticket; /home/user/hadavin-sdk/CLAUDE.md; the three named rule files; app.py, approvals/receiver.py, sources/kinds.py, tests/test_lockin_guard.py. Read in part: config.py 376-445, backends/table.py (grep), the six affected test sites, tests/stage_mutants.py 1-70.

---------------------------------------------------------------
BLOCKERS
---------------------------------------------------------------

B1. Behaviour 1 makes two existing positive-path pilot tests impossible, and the ticket only covers error-path tests.
Where: ticket line 13 ("updated to reach their intended error another way"); 
- /home/user/build/EV-P89-db0d9eb/tests/test_k3_pilot_env.py:185-191 (`test_k3_pilot_app_has_no_executor`: pilot build with `secrets=spy, channel=FakeChannel(), llm=ScriptedLLM(...)`)
- /home/user/build/EV-P89-db0d9eb/tests/test_k5_round8_postgres.py:40-42 (`test_the_app_deletes_evidence_only_through_the_purge_identity`: pilot build with `secrets=, channel=FakeChannel(), llm=ScriptedLLM()`)
Gap: these two have no "intended error". They prove security properties of a successfully built pilot App (no executor; exactly five secret names resolved, recorded by a spy provider; purge identity separate). After the change a pilot build can only use configured kinds (`mounted_file` secrets, `slack` channel, `openai_compat` model at https://llm.example/v1), which means no spy, a real Slack call on `post_card`, and a real model call. The ticket forbids weakening or deleting them and gives no test seam. Both tests need `HADAVIN_TEST_PG_DSN`, so a local gate will most likely not show the breakage and CI will go red after the PR is opened.
Text to add to the ticket (owner or lead must choose one; I recommend (a)):
"Positive-path pilot tests (tests/test_k3_pilot_env.py::test_k3_pilot_app_has_no_executor, tests/test_k5_round8_postgres.py::test_the_app_deletes_evidence_only_through_the_purge_identity) keep every assertion. They stop passing override objects and instead (a) monkeypatch `hadavin_sdk.app.make` in the test so that the capabilities `secrets`, `channel` and `llm` return the spy provider, FakeChannel and ScriptedLLM, all other capabilities going to the real `make`. No new production parameter, environment variable or flag may re-open the override in pilot or prod. Both tests run only with HADAVIN_TEST_PG_DSN: the evidence runner must run them against the CI postgres service and paste the output."
If (a) is rejected, the ticket must name the alternative seam exactly; a builder must not invent one on a security path.

B2. Behaviour 1: the position of the new check in `build()` is not given, and it decides which existing tests break.
Where: /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/app.py:82-98.
Facts: line 82 is `secrets = secrets or make("secrets", b.secrets)`, which overwrites the argument, so the check must read the argument before line 82 (or line 82 must move). `live` is computed at line 83. Existing refusals follow at 84-85 (restored-hash key), 86-89 (purge DSN), 90-92 (`sources=`), 93-98 (`tools=`). Four existing tests pass override objects to a live build and expect one of those later errors:
1. tests/test_stage_names.py:313-317 (`_live_by_site`, called at lines 77, 90, 328; expects "restored_hash_key_secret_name is required in pilot and prod"; passes `secrets=`). Note line 77 calls it with "demo", where the override must stay.
2. tests/test_k5_round10.py:80 (expects "purge_dsn_secret_name"; passes `secrets=`, `llm=`).
3. tests/test_k5_round9b.py:370 (expects "restored_hash_key_secret_name"; passes `secrets=`, `llm=`).
4. tests/test_k5_round5.py:226 (expects "plain callables"; passes `secrets=` and `tools=`).
If the new check is first, all four get the new error. If it is placed after line 98, 1-3 still pass untouched but 4 still changes, and a live process with a fake provider still gets as far as `make("secrets", ...)`. Also, 2-4 use `pilot_cfg`, whose secrets kind is `mounted_file` with dir "secrets"; `secrets_file.build` refuses a missing directory (src/hadavin_sdk/actions/secrets_file.py:70) and `pilot_cfg` (tests/test_k3_pilot_env.py:35-86) does not create it, so "drop the override" is not enough for those tests.
Also undefined: "pilot or prod" versus "not exactly demo". `is_live` treats any non-stage value as live (tests/test_stage_names.py:324-330 pins this), and "passing as an object" versus truthiness (the existing checks use `if sources and live`; an override object that is falsy would slip through).
Text to add:
"Placement: in app.build, immediately after `cfg = load_config(config_dir)` and before `secrets = secrets or make(...)` (app.py:82); compute `live = is_live(cfg.environment)` first. The check is `is not None` for each of the four arguments, never truthiness, and uses `is_live` (so any value that is not exactly `demo` is refused, as for the other guards). Order: secrets, channel, detector, llm; the first one present raises. Existing tests that change (exactly six call sites, list them in the PR): test_stage_names.py:313 (pass `secrets=` only when `stage == 'demo'`), test_k5_round10.py:80, test_k5_round9b.py:370, test_k5_round5.py:226 (drop the override objects, create `<root>/secrets/` so the mounted_file kind builds, assert the same message as today), plus the two in B1. Add one case to the `_live_by_site` family proving a non-stage value is refused by the new check."

B3. Behaviour 3 (receiver) is a design, not an instruction, and contradicts Behaviour 4.
Where: ticket line 15; /home/user/build/EV-P89-db0d9eb/src/hadavin_sdk/approvals/receiver.py:18,22,41,47,54; approvals/channel.py:69-83 (the `Channel` Protocol has no path attribute); approvals/slack_channel.py:33-36; tests/test_p7_tick.py:18,259,263,265,273,290,537.
Open decisions:
(a) "path taken from the channel object where one is defined": no attribute name, no statement whether it joins the `Channel` Protocol or is read with `getattr`, and no value for `FakeChannel`.
(b) Which paths does `serve()` answer? tests/test_p7_tick.py:290 posts to `/slack/actions` on an app built with `FakeChannel(SIG)` (line 45). If the alias is "owned by the Slack channel module", that request returns 404 with a FakeChannel unless `serve()` always accepts both paths, in which case receiver.py must hold or import the Slack path.
(c) "keep `handle_slack_action` working ... so no caller breaks": the only caller is `from hadavin_sdk.approvals.receiver import MAX_BODY, handle_slack_action, serve` (tests/test_p7_tick.py:18, used 4 times). If the name stays importable from receiver.py, a vendor-named identifier remains in a neutral module, which Behaviour 4 ("identifier part in neutral modules") is meant to catch. If it moves to slack_channel.py, that import breaks and the test file changes (5 lines), and slack_channel.py must import receiver.py (check for an import cycle: receiver imports approvals.requests only, so it is safe in that direction).
(d) `post_json`: receiver.py does not use `post_json` at all. It is imported at approvals/slack_channel.py:23 from `hadavin_sdk.llm.common`. The sentence is attached to the wrong file, names no target module, and "pure move" and "record" (where?) are undefined.
Text to add (one consistent option; adjust if the lead prefers another):
"receiver.py: `PATH = '/channel/actions'`; rename `handle_slack_action` to `handle_action` (same signature and behaviour). `Channel` Protocol gains no member. `serve()` answers `PATH` and, if present, `getattr(approvals.channel, 'callback_path', None)`; any other path is 404. `SlackChannel.callback_path = '/slack/actions'` and `FakeChannel.callback_path = None`. slack_channel.py defines `handle_slack_action = receiver.handle_action` with a one-line docstring 'documented alias'. receiver.py contains no vendor name in code, constants or docstrings. tests/test_p7_tick.py changes: line 18 imports `handle_action` from receiver (4 call sites renamed; reason: neutral name), line 290 posts to `/channel/actions`; add a second server test with a SlackChannel-like channel (callback_path set) proving `/slack/actions` returns the same status, and one proving `/slack/actions` is 404 when the channel defines no callback_path. docs/slack-app-manifest.yaml:5,30 and docs/slack-app.md:14 keep `/slack/actions` (it is the Slack channel's path; tests/test_p7_tick.py:537 pins the manifest). `post_json`: out of scope for this ticket; add a ledger line 'F6 remainder: slack_channel imports post_json from llm.common' with a trigger."

---------------------------------------------------------------
MAJORS
---------------------------------------------------------------

M1. Behaviour 4, vendor-name pattern: no regex, no definition of "path segment" or "identifier part", unbounded fallout.
Where: ticket line 16; tests/test_lockin_guard.py:519-536 (PATTERNS), 592-622 (`literal_problems` scans string/bytes constants, `+` joins and f-strings only; it skips docstrings and never looks at identifiers).
Gap: "identifier part" could mean a string that looks like an identifier (`"handle_slack_action"`) or real Python names (FunctionDef, Name, Attribute, keyword arguments), which needs a new AST scan. A grep of src for a vendor word next to `/ _ . "` finds matches in neutral modules besides receiver.py: approvals/gate.py (6 lines), guard/judge.py, guard/producers.py, store/postgres.py, defaults.py, config.py, audit/local_dir.py, sources/kubernetes.py, runtime/tick.py, llm/protocol.py, llm/common.py, llm/openai_compat.py, backends/table.py. I did not separate comments and docstrings from code constants, so the number of real new findings is unknown. Each one needs either a fix or a LITERAL_OK entry, and the ticket does not say which.
Text to add: "Add one PATTERNS entry, label 'vendor path segment', regex `(^|[/_.-])(slack|teams|aws|azure|gcp|github|gitlab|bedrock|anthropic|vertex|gemini|openai|kms|s3|foundry)([/_.:-]|$)`, applied to the same folded constants as today. Scope of 'identifier': also scan the names of top-level and nested `def`/`class` and module-level assignment targets in neutral modules with the same regex (new function `identifier_problems`), not arbitrary Name nodes. Before coding, the builder runs the new scan on main and pastes the full list of findings; each finding is fixed, or gets a LITERAL_OK entry with a reason, and the list is reviewed before the build continues. If more than 10 findings appear, stop and report." (The regex is my proposal; the lead must confirm the word list equals the 'bare vendor name' list at line 520-521.)

M2. Behaviour 4, `sources.kinds.KINDS` "joins the coverage check": the data shapes do not fit and the entry text is missing.
Where: tests/test_lockin_guard.py:406-426 (`coverage_problems` expects `{capability: {kind: entry with .neutral}}`, and reports "exception names no capability" for an EXCEPTIONS key not in the table); src/hadavin_sdk/sources/kinds.py:24-47 (`SourceKind` has no `neutral` field; one kind, `kubernetes`).
Gap: capability key name (`source`? `sources`?), how neutrality is decided for a SourceKind, whether KINDS is merged into the table passed at line 430 or checked by a second call, and the full ExceptionEntry (status, reason, decided, review_by; only the trigger "K5-ITO" is given).
Text to add: "In tests/test_lockin_guard.py build `COVERED = {**TABLE, 'sources': {name: _E(neutral=False) for name in KINDS}}` and pass COVERED at line 430. No change to SourceKind. Add `EXCEPTIONS['sources'] = ExceptionEntry('pending', 'Kubernetes is the only built read-source kind; the registry in sources/kinds.py is the seam', 'K5-ITO: first client that needs a second source kind', date(2026, 11, 11), date(<review date chosen by lead>))`. New test: with the 'sources' entry removed, coverage_problems names 'sources'."

M3. Behaviour 4, "none" trigger: rule and replacement text missing.
Where: tests/test_lockin_guard.py:389-395 (`EXCEPTIONS['audit']` trigger "none"), 422-423 (only an empty trigger is refused).
Gap: exact comparison (case, surrounding spaces, "n/a", "-"), the message, and the "real named trigger" for the audit entry, which is a product statement the builder cannot invent.
Text to add: "coverage_problems: `ex.trigger.strip().lower() in {'', 'none', 'n/a', '-'}` gives `'<name>: exception needs a named trigger (not none)'`. The audit entry's trigger becomes: '<text supplied by lead>'." The lead must supply that text.

M4. Behaviour 2 (Vault token): place, message, wording and default are not pinned.
Where: ticket line 14; src/hadavin_sdk/config.py:393-401; src/hadavin_sdk/backends/table.py:255 (`auth: Literal["token","approle","kubernetes"] = "token"`), 283, 293.
Gaps: (1) the ticket rung table cites "config.py 394-397" as refusing `env` secrets; that block refuses every DEMO_ONLY pair, and the new rule is a per-setting check, not a kind check, so it cannot reuse DEMO_ONLY. (2) Refusals there are collected into one list and raised as `environment <stage>: refused: a, b`; the item text is not given. (3) `token` is the default, so a pilot config that never wrote `auth` is refused; the message must say so. (4) "naming the allowed kinds (kubernetes, approle)": these are sign-in methods, and "kind" already means a backend kind in this codebase (wording rule: one word, one meaning). (5) Same `is_live` question as B2.
Text to add: "In Config._cross_checks, inside the `if is_live(self.environment):` block (config.py:394-398), append for each `(c, s)` in `self.backends.entries()` where `getattr(s, 'kind', '') in {'vault', 'vault_transit'}` and `s.auth == 'token'`: `f'{c}: {s.kind} auth token (the default; set auth: kubernetes or auth: approle)'`. No change to _VaultConnection. Tests: `load_config` on a pilot and a prod config for each of the two kinds matches `environment <stage>: refused: ` and contains that item, both with `auth: token` written and with `auth` omitted; the same four configs with `environment: demo` load."
For the report the ticket asks for ("if a live deployment path in docs/tests relies on token auth, say so"): I found none. No file under docs/ or demos/ names Vault; no test loads a pilot or prod config with a Vault kind (Vault tests build `VaultSettings`/`VaultTransitSettings` directly or call `make`, which the Config validator does not see: tests/test_p4b_secrets.py:40,46,159; tests/test_p5p6_followups.py:437; tests/test_p3b_neutral_audit.py:105). So Behaviour 2 changes zero existing tests, by reading.

M5. "Each must fail on origin/main" cannot hold for several listed tests.
Where: ticket lines 18-22.
These pass on main by nature: "demo still accepts" (4 overrides), "accepted in demo" (Vault, 2 kinds), "alias works" (`/slack/actions` and `handle_slack_action` work today). A builder following the line literally must either drop them or fake a failure.
Text to add: "Tests marked (regression guard) are expected to pass on origin/main and are exempt from the fail-on-main proof: demo accepts each override; demo accepts Vault token auth; the Slack path still answers. Every other listed test must fail on origin/main; paste the failing run for each." For the override negatives, also state the expected failure on main ("DID NOT RAISE" or a non-matching error), because on main a pilot build with a fake provider goes on to open the postgres store and may fail with an unrelated error, which is a failure for the wrong reason: require `pytest.raises(ConfigError, match=<exact message>)`.

M6. Exact messages for Behaviour 1 are a template, not text.
Where: ticket line 13; app.py:92 and 96-98 (the two existing messages differ from each other).
Text to add: "Messages, exactly: `secrets= is for tests; configure backends.secrets in pilot and prod`, and the same sentence with `channel`, `detector`, `llm`. Tests match the full string. Update the `build` docstring (app.py:76-78) to say the keyword overrides are refused outside demo."

M7. No CHANGELOG, upgrade or docs instructions.
Where: /home/user/build/EV-P89-db0d9eb/CHANGELOG.md:3 ("## Unreleased"; the file has an "Upgrade steps" convention, cited by app.py:149), CHANGELOG.md:321 (documents `auth: token|approle|kubernetes` with no stage limit); docs/slack-app.md:14; docs/slack-app-manifest.yaml:5,30.
Both Behaviour 1 and 2 turn configurations and call patterns that start today into start-up refusals. 
Text to add: "CHANGELOG 'Unreleased': (1) Changed, breaking for pilot and prod: `app.build` refuses `secrets=`, `channel=`, `detector=`, `llm=` objects outside demo. (2) Changed, breaking: Vault `auth: token` (the default) is refused in pilot and prod; Upgrade steps: set `auth: kubernetes` with `role`, or `auth: approle` with `role_id`. (3) Added: neutral callback path `/channel/actions` and `handle_action`; `/slack/actions` stays for the Slack channel. docs/slack-app.md line 14: add one sentence naming the neutral path. No change to docs/slack-app-manifest.yaml."

---------------------------------------------------------------
MINORS
---------------------------------------------------------------

m1. Ticket line 13 gives one example of an affected test ("for example tests/test_stage_names.py around 313-317") and leaves the search to the builder. Count by grep of tests for `secrets=|channel=|detector=|llm=` followed by an object: 82 matching lines in 29 files; six call sites are live builds (the four in B2 and the two in B1). All other sites use demo configs (`make_cfg`, `live_cfg_dir` at tests/conftest.py:105-106 which is a demo config despite its name, `k5_cfg`, `demo_cfg`) or are not `app.build` calls. Put the six in the ticket. The only production caller, src/hadavin_sdk/cli.py:299 `build(None, agents)`, passes no override and is unaffected.

m2. Mutation proof not requested. tests/stage_mutants.py holds one mutant per live guard (CFG, REGISTRY, DEFERRED, APP entries). The class-level-fixes rule asks for proof that tests fail on old code; the ticket should say: "add one mutant per new guard to tests/stage_mutants.py (four override checks in app.py, one Vault rule in config.py), each killed by its named test", or state that the evidence runner does this.

m3. Class-level sibling search (class-level-fixes.md) not instructed for Behaviour 1: `build()` has three more test-only keyword arguments that stay accepted when live: `hold_run_ids`, `clock`, `timeout_s` (app.py:72-74). `clock=` in particular changes approval expiry. The ticket should state the decision: "siblings reviewed: hold_run_ids, clock, timeout_s stay allowed because <reason>" or add them.

m4. Rung table row 2 says the reused validator "already refuse[s] `env` secrets when live (config.py 394-397)"; accurate only via DEMO_ONLY membership. Row 3 cites "compatibility alias" without saying who owns it. Row 4 says "test only", but Behaviour 3 moves production code to satisfy it. Correct the three cells so the evidence matches the code.

---------------------------------------------------------------
PER-BEHAVIOUR SUMMARY (the five questions asked)
---------------------------------------------------------------
1. Overrides: function known (app.build), line NOT fixed (B2); error type given (ConfigError), message a template (M6); existing tests changing: six call sites, two with no stated path (B1, B2, m1); ambiguous words: "pilot or prod", "as an object", "another way"; fail-on-main: achievable for the 8 negatives, not for "demo still accepts" (M5).
2. Vault token: function not named (should be Config._cross_checks, config.py:394-398), message not given, "kinds" misused, default not addressed (M4); existing tests changing: none found; fail-on-main: achievable for live refusals, not for demo acceptance (M5).
3. Receiver: not buildable as written (B3); existing test changes depend on the missing decision (up to 6 lines in tests/test_p7_tick.py); fail-on-main: "neutral path works" yes (404 on main), "alias works" no (M5), planted-segment meta test yes ("/slack/actions" is not matched by any pattern at test_lockin_guard.py:519-536 today).
4. Guard: regex, scan scope, capability name, entry fields and the audit trigger text all missing (M1, M2, M3); fail-on-main: achievable for the "none" test and the sources-coverage test once M2/M3 are fixed.
Migration notes: CHANGELOG and docs instructions absent (M7); no demo config uses Vault token auth (none found under docs/ or demos/ by grep of the build tree).

---------------------------------------------------------------
NOT CHECKED
---------------------------------------------------------------
- Nothing was run: no pytest, ruff, bandit, no proof that any test fails or passes on origin/main. All "would break" statements come from reading code.
- I treated /home/user/build/EV-P89-db0d9eb as main, as instructed; I did not compare it with origin/main.
- The new vendor-pattern fallout (M1): I counted grep line matches per file but did not determine which are code constants versus comments or docstrings, so the true number of new guard findings is unknown.
- Whether `make("llm", openai_compat)` and `make("channel", slack)` build without network in pilot_cfg once overrides are dropped (matters for B2 tests 2-4 only if the new check is not placed first; with the placement proposed they never reach those lines).
- Whether `pg_schema()` yields nothing or skips without HADAVIN_TEST_PG_DSN in tests/test_k3_pilot_env.py:178 (I did not read tests/contracts/kinds/store_postgres.py).
- handover/reviews/Q8/deps-audit.md: only the lines for F1, F5, F6, F8, F11 were read. handover/ledger.md, handover/README.md, STUDIO-RULES.md and STATUS.md were not read (not supplied as review context).
- demos/ in the working repository at /home/user/hadavin-sdk were not searched; the search for Vault and `/slack/actions` covered /home/user/build/EV-P89-db0d9eb only.
- Only the three named rule files under .claude/rules/ were read, not the other 36.
- tests/stage_mutants.py beyond line 70 and tools/mutation_runner.py were not read.
- AppRole reads its secret id from an environment variable (table.py:259); whether that meets "short-lived credentials" is a security-design question I did not assess.

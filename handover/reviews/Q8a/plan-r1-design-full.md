<!-- full hand-back report of sub-agent a126a1f8, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

DESIGN REVIEW, round 1 - ticket /home/user/hadavin-sdk/handover/tickets/Q8a-live-override-refusals.md
Verdict: not ready to build. 1 Blocker, 7 Major, 6 Minor. Read-only review; nothing was run (see "Not checked").

## BLOCKER

**B1. Item 1 breaks the only positive pilot build tests, and the plan has no replacement for them. A local "full pytest" will not show it.**
- Evidence:
  - /home/user/build/EV-P89-db0d9eb/tests/test_k3_pilot_env.py:185-191 builds a pilot app with `secrets=spy, channel=FakeChannel(), llm=ScriptedLLM(...)`. It then asserts the pilot guarantees: no executor, exactly five secrets resolved, shadow and abstain cards.
  - /home/user/build/EV-P89-db0d9eb/tests/test_k5_round8_postgres.py:40-42 does the same for the purge-identity guarantee.
  - Both skip without `HADAVIN_TEST_PG_DSN` (tests/contracts/kinds/store_postgres.py:22-24; test_k5_round8_postgres.py:22-23).
- Scenario: the builder adds the refusal, runs pytest on a machine with no Postgres, sees green, and opens the PR. With Postgres, both tests now die with "secrets= is for tests". The ticket's only instruction ("reach their intended error another way") fits negative tests; these two are positive, so the only moves left are deleting or weakening them, which CLAUDE.md forbids.
- Other live-stage callers that pass overrides (the ticket names one "for example"):
  - tests/test_k5_round10.py:80 (expects the `purge_dsn_secret_name` error)
  - tests/test_k5_round9b.py:370 (expects the `restored_hash_key` error)
  - tests/test_k5_round5.py:226 (expects "plain callables")
  - tests/test_stage_names.py:313-317
- Proposed change to the ticket:
  1. List all six call sites, marked positive or negative.
  2. Name the test seam for a live build: plant test kinds in `TABLE` with `monkeypatch.setitem` (precedent: tests/test_p1b_backends.py:127-131), and use the `mounted_file` secrets directory that `pilot_cfg` already declares (test_k3_pilot_env.py:53) with a spy wrapper. This exercises the real factory and `platform_secrets.check`, which the override path skips today.
  3. State the honest limit: the refusal stops an accidental fake in a live process, not hostile in-process code, since `TABLE` and `make` can still be patched.
  4. Require the EVIDENCE RUNNER to run with `HADAVIN_TEST_PG_DSN` set and paste the non-skipped results of both tests.

## MAJOR

**M1. Where the check sits in `build()` is unspecified, and two placements are wrong.**
- Evidence: app.py:82 `secrets = secrets or make("secrets", b.secrets)` rebinds the name, so any check after it cannot tell an override from the configured provider. app.py:162 and :170 do the same with `llm or` and `channel or`.
- Truthiness: `if secrets and live` (copying app.py:90 and :93) misses a falsy object, and line 82 would silently swap such an object for the configured one.
- Ordering: a refusal placed before app.py:84-98 changes which error the four negative tests in B1 see.
- Proposed: record `given = {name for name, v in (...) if v is not None}` at the top of `build()`, and raise after line 98. The four negative tests then keep their intended error with no edit. Add a test with a falsy override object.

**M2. Same class, missing: the `clock=` parameter (app.py:73).**
- Evidence: the clock feeds callback freshness (approvals/requests.py:76 passes `self.clock().timestamp()` to `parse_decision`) and approval expiry (requests.py:103, :154).
- Scenario: a frozen or skewed clock object in a live process means approvals never expire and stale signed callbacks stay fresh. That is as much a test-only object as a fake channel.
- Proposed: refuse a non-default `clock` when live, or write the reason for leaving it.
- Related: `timeout_s=` is silently ignored when live (app.py:172-174); refuse it or document it. `hold_run_ids=` is a real production hook (CHANGELOG.md:70) and stays; say so, so the next reviewer does not re-raise it.

**M3. Vault rule: the rung-table claim is not honest, and the choke point is one more special case.**
- Claimed need: "no long-lived credential in a live process". The allowed `approle` mode reads its secret id from an environment variable (table.py:259, actions/secrets_vault.py:172). That is a static credential in the environment, the reason `secrets: env` is demo-only (table.py:598). Its lifetime is set on the Vault side and we cannot check it.
- Scenario: an operator moves `VAULT_TOKEN` to `VAULT_SECRET_ID` with no expiry and passes the new check; nothing got shorter-lived.
- `kubernetes` is then the only truly short-lived mode, so a client on plain VMs has none. That is a no-single-dependency gap needing a second mode or a written outline with a trigger.
- Choke point: config.py:393-401 works on `(capability, kind)` pairs. A Vault rule there must name two kinds or test `s.auth == "token"` by duck typing, next to the hand-written `ed25519_local` rule at config.py:423-424.
- `auth` defaults to `"token"` (table.py:255), so a pilot config that omits `auth` is refused for a value the operator never wrote.
- Proposed:
  1. Add a `live_refusals()` hook on `KindSettings` that `_cross_checks` calls for every entry. `_VaultConnection` implements it, and the key-file rule can move there later.
  2. Reword the need to "no static Vault token; approle allowed only with a secret id that expires, which we cannot verify" and warn at start-up.
  3. Decide whether prod allows `approle` at all (owner decision).
  4. Make the error say "auth defaults to token".
  5. Log a trigger for a JWT/OIDC or certificate mode.
- Good news: no pilot or prod config in docs or tests uses token auth. The uses build settings directly (tests/test_p4b_secrets.py:47, tests/test_p3b_neutral_audit.py:103, tests/contracts/kinds/secrets_neutral.py:45), so a Config-level rule leaves them alone.

**M4. Receiver: the alias plan contradicts itself, and one reading keeps the lock-in.**
- Contradiction: "aliases owned by the Slack channel module so no caller breaks". The only caller imports `handle_slack_action` from `receiver` (tests/test_p7_tick.py:18). To keep that import, the neutral receiver must re-export from `slack_channel`: a neutral module importing a vendor module and carrying a vendor identifier, which item 4's new pattern must then exempt. That keeps the lock-in.
- Unspecified wiring:
  - `Channel` has no path attribute (approvals/channel.py:69-82).
  - `serve()` receives only `Approvals` (receiver.py:40).
  - Nothing says which paths answer for which configured channel. If `/slack/actions` answers while the channel is `fake` or a future kind, the Slack route is still global.
- The repo's own precedent is no shims: config.py:95 "no clients yet, so no migration shim".
- Proposed:
  1. Add `callback_path` to the channel objects, read with a neutral default so planted test channels do not break.
  2. The receiver serves exactly the configured channel's path and holds no vendor string.
  3. Drop the `handle_slack_action` alias and update the import in test_p7_tick.py:18 (a rename, not a weakening).
  4. For the URL, confirm whether any Slack app is registered with `/slack/actions`.
     - If none: change docs/slack-app-manifest.yaml:30, docs/slack-app.md:14 and test_p7_tick.py:290 and :537 to the neutral path, with no alias.
     - If one exists: `/slack/actions` becomes the Slack kind's own `callback_path` and is served only when the kind is `slack`.
  5. Write the path-by-kind matrix into the ticket.

**M5. Guard pattern (item 4a) is unspecified and its blast radius is unknown.**
- Evidence: `literal_problems` scans only string constants (tests/test_lockin_guard.py:605-610). "Identifier part" therefore needs a new scan of function, class and attribute names; it is not a pattern tweak.
- Certain hit: `OpenAICompatSettings` (table.py:71) is not covered by `_TABLE_VENDOR_NAME` (test_lockin_guard.py:516-518), and `llm.openai_compat` is not in `VENDOR_MODULES`.
- Likely hits: a rough grep finds vendor tokens as segments on lines in about ten neutral modules (approvals/gate.py, config.py, guard/runmap.py, guard/producers.py, store/postgres.py, audit/protocol.py, llm/protocol.py, llm/common.py). This is an upper bound that includes comments and docstrings.
- Scenario: the builder meets 15 or more hits and adds a pile of `LITERAL_OK` entries or narrows the pattern until main passes. The guard then looks stronger than it is.
- Proposed: put the exact regex and the tokenising rule (snake and camel parts) in the ticket; do a dry run on main first and paste the hit list, each marked fix or allow with a reason. Ship the path-segment rule with the rename; make the identifier scan a separate step if the list is long.

**M6. "KINDS joins the coverage check" is not "test only".**
- Evidence: `coverage_problems` reads `e.neutral` (test_lockin_guard.py:412). `SourceKind` has no such field (sources/kinds.py:24-36). An `EXCEPTIONS` key not in the table is itself an error (test_lockin_guard.py:420-421).
- So the plan needs either a `neutral` field on `SourceKind` (a source change) or a merged table with an adapter in the test. The rung table says "KEEP-CODE (test only)" with evidence "file read by reviewer", which is not evidence.
- Proposed: choose one, name the merged key, give the `review_by` date (the ticket leaves it blank), and correct the rung row.

**M7. Scope: split into two pull requests.**
- Items 1-2 are least-privilege (security path, uncapped rounds). Items 3-4 are lock-in (two fix batches at most, per CLAUDE.md). Bundled, the rename and the open-ended guard work ride on an uncapped loop and can hold up the security fix.
- Q8a-1: override refusals including `clock`, the Vault rule through the hook, and the test seam from B1.
- Q8a-2: receiver `callback_path`, the path-segment guard with its meta test, `KINDS` coverage, and the "none" trigger. The rename and its guard must land together, or the guard fails on main.

## MINOR

- **m1.** Refusing only the string "none" is a one-word denylist; "None ", "n/a", "tbd" and "-" pass. Normalise with strip and casefold, refuse a small set, and add plant tests.
- **m2.** The new trigger for the `audit` exception (test_lockin_guard.py:389-395) is a commitment about what ends it. The ticket should give the text or mark it an owner decision, not leave the builder to invent one.
- **m3.** "Each test must fail on origin/main" cannot hold for "alias works" and "demo still accepts"; both pass today. Mark them regression guards.
- **m4.** The `post_json` clause is scope creep. approvals/slack_channel.py:23 imports it from `llm.common`; llm/openai_compat.py:26 and llm/gemini.py:17 also use it, so a move touches three modules. Drop it from this ticket and log it.
- **m5.** Rung row 1 says "about 10 lines + tests". With six call sites and a new seam, that understates the work.
- **m6.** Siblings to log in the ledger, not fix here:
  - AWS kinds use the default credential chain (actions/secrets_aws.py:42), so long-lived access keys in the environment are accepted when live.
  - `ed25519_local` with a key file is allowed in pilot (config.py:423 refuses it in prod only).
  - Postgres with a password DSN and `iam_auth` off.
  - The vendor-name lists (test_lockin_guard.py:520-521) contain no entry for Vault, although both Vault kinds are marked neutral.

## Answers to your direct questions
- **Choke points:** `build()` is right for item 1; `cli.py:299` is the only production caller and passes no overrides. `Config._cross_checks` is the right layer for item 2, but through a per-kind hook (M3).
- **Legitimate callers that break:** six test call sites (B1). No demo imports `hadavin_sdk.app`. No live config uses `auth: token`.
- **Alias:** unsound as written (M4).
- **Rung table:** rows 1, 2 and 4 overstate or understate (m5, M3, M6).

## Not checked
- Nothing was executed: no pytest, no dry run of any pattern. Hit counts in M5 are grep estimates.
- reviews/Q8/deps-audit.md (F1-F11), handover/ledger.md, STATUS.md and the plan notes were not supplied, so I did not confirm the ticket matches its source findings or that the out-of-scope items are logged.
- tests/test_k5_tools.py:1232 and tests/test_k5_round5.py:883 use `pilot_cfg`; I did not read whether they pass overrides to `build`. Other test files may build live configs by other helpers.
- Whether `make("secrets", mounted_file)` fails on a missing directory at build time or lazily. This decides whether the negative tests could simply drop `secrets=`.
- The Azure and GCP credential paths, and `backends/hosts.py`.
- Whether any real Slack app is registered against `/slack/actions`.
- The `demos/` grep covered Python files plus docs for `build(` and receiver use, not YAML configs under `demos/`.

# P6b2 round 3 resolve report (egm:egm-resolve, auto mode)

Status: resolved (categorised). The ticket is NOT edited here. This is the last ticket round: order 20 item 6 caps review at 3 rounds, and its extra round is for money or redaction packages only. P6b2 is a security package, and this round had 5 Majors. So every fix is a build note, BN-1 to BN-15, and there is no revision 4 and no round 4.
Target: `handover/tickets/P6b2.md` revision 3 (905 lines, full file read; path class SECURITY, Tier A; commit `d66fcfb`, pushed 2026-11-06 03:50 UTC / 09:20 IST).
Inputs (20 finding ids; severity is counted from the tables and never changed here):
- `P6b2-round3-adversarial.md`, R3-ADV-1..9: 0 Blocker, 2 Major, 5 Minor, 2 Nit.
- `P6b2-round3-correctness.md`, R3-COR-1..11: 0 Blocker, 3 Major, 5 Minor, 3 Nit.

Gate: the skill's "wait for the user" step is skipped (auto mode, per the brief). This file replaces the skill's default file name `goldfish_review_report.md`.
- Nothing is escalated to the owner.
- New PENDING LEAD items continue the ticket's numbering from 16. Each has a recommendation, and its build note states the default the builder takes meanwhile.
- PENDING LEAD 16 is a NEEDS LEAD (least privilege). The others are INFORM.

## Honest note (what I did NOT check, first)
- I ran no pytest, no mutant, no `uv`, no ruff, no gitleaks or secret scan, no install and no network call. I wrote no git state.
- I ran two read-only probe scripts with the repository's existing virtual-environment interpreter (`python -I`, in a scratch folder outside the repo, `HADAVIN_TEST_PG_DSN` unset). They copy the test fixtures, then call `load_config`, `load_registry` and `app.build` with `make` patched. The results are in Facts. A probe is not evidence; the builder's base run is.
- **The R3-ADV-6 contest rests on two things.**
  - The code passes the password to `psycopg.connect` explicitly (`store/postgres.py:138-146`).
  - libpq prefers an explicit password over `PGPASSWORD` and the password file. That precedence is from memory: UNVERIFIED. If it is wrong, R3-ADV-6 becomes a PROPOSE FIX (limit 3 wording).
- **The SDK facts come from the INSTALLED packages only**: anthropic 2.1.0 (also the `uv.lock` pin), azure-identity and botocore in `<repo>/.venv`. That platforms (EKS, ECS, AKS) deliver short-lived role credentials through token-file or container variables is from memory: UNVERIFIED.
- **Fact 23 for `AZURE_PASSWORD` (BN-12), partly checked.** I checked the name against four guard patterns by script: bare vendor name, the SQL literal, key, and long-secret shape. I checked the other `PATTERNS` by eye. The repo's gitleaks rules were not run. The builder runs evidence commands 3 and 7.
- **Not probed:** `deferred.check` on an empty registry in PILOT; only dev was probed. This matters for the operator folder of `limits` (Couplings).
- P2a-1's final code (the `stop_credential_ref`/`reset_credential_ref` fields and the `limits` path) does not exist yet. BN-7's C10 (f) depends on it, as revision 3 already did.
- Revision 3 facts that both reviewers marked verified and that no finding touches were not re-checked by me. These are facts 3, 6, 10-13, 21 and 25 (AST counts), and the 13 L4 call lines.

## Facts I checked myself (read on disk or by probe)
- **The tree on disk vs `397ec97`.** `src` and `tests` are at `ce70eb5`, an ancestor of `397ec97` (`git merge-base --is-ancestor`). `git diff --stat 397ec97 -- src tests` shows 22 files:
  - in `src`: `approvals/gate.py`, `guard/http.py`, `guard/redact.py`, `guard/runmap.py` and `tools.py`;
  - in `tests`: renames and two deleted test files.
  - None of these is a file this ticket cites, except `tools.py`. There the change is in the partial-escape code only. The fact-21 site `tools.py:407` and the constant sites `:323`, `:375` and `:423` are on the same lines at `397ec97`.
  - So the ticket's cites hold at `397ec97`. This closes the "tree equals `397ec97`" UNVERIFIED in the ticket and in both reports. The reviewers' "not a git checkout" was wrong: the handover folder is inside the checkout `<repo>`.
- **Probe 1 (R3-ADV-1, R3-COR-1 are TRUE).** I copied the fixture config and deleted `agents.yaml`, `principals.yaml`, `chains.yaml`, `actions/` and `tools/`. Then `load_config` and `load_registry` succeed (0 agents). With `agents.yaml` = `- not: an agent`, `load_registry` raises `ConfigError` ("9 validation errors for AgentRecord"). So C8 (f) as worded does not kill Ma37, and the invalid-`agents.yaml` form does.
- **`tests/test_p2_postgres.py:96-103`** (`test_migrate_does_not_need_a_valid_registry`) uses that invalid `agents.yaml`. It is one of the four tests of fact 8. The others are `test_migrate_needs_the_migration_dsn` (`:106`), `test_p7_tick.py::test_cli_migrate_warns_when_new_tables_get_no_grants` (`:497`) and `test_k2_migrations.py::test_cli_migrate_passes_the_portal_role` (`:128`).
- **R3-ADV-2 is TRUE.** `cli._main` calls `load_config()` at `cli.py:136` for every command except `tick` (which reaches it through `app.build`, `cli.py:299`). It dispatches `migrate` at `:137-138` and calls `load_registry` at `:139` for every other command, `limits` and `audit verify` included. So N2, which sits in `Config._cross_checks`, runs for `migrate`, `limits stop/reset` and `audit verify` with a pilot or prod config. `migrate` with `iam_auth` signs in through `store/auth_aws.py:16` (`boto3.client`, ambient), so the operator's AWS identity is used there.
- **`app.build` order** (`app.py:79-146`): `load_config` `:79`, `load_registry` `:80`, `make("secrets")` `:82`, `platform_secrets.check` `:122`, `make("signer")` `:144`, `make("store")` `:146`. `store/postgres.py:build` connects (`:152-163`). `pilot_cfg` uses a postgres store (`tests/test_k3_pilot_env.py:54-58`), and the module docstring says the App test needs `HADAVIN_TEST_PG_DSN` (`:1`).
- **Probe 2 (R3-COR-3, and own finding N1 on C7).** I took a dev `cfg_dir` with `store` = postgres, a recording provider passed as `secrets=`, and `app.make` patched to raise at the first call. `app.build` reached `make("signer")` with no Postgres, after `check` had asked for `fixture-token` and `pg-dsn`. So a row that stops at `make("signer")` runs without a database. A row that runs past `make("store")` does not.
- **R3-ADV-6 (CONTEST).** In `store/postgres.py:138-146`, with `iam_auth` and no password in the DSN, `connect` passes `password=<IAM token>` to `psycopg.connect`. With a DSN password, that password is used. N10 needs a non-empty password or `iam_auth` in pilot and prod. So in pilot and prod libpq always gets an explicit password, and `PGPASSWORD`/`PGPASSFILE` do not decide the login (libpq precedence: see the Honest note). Dev keeps password-less DSNs on purpose (fact 18b), and owner-visible line 3 already says that libpq fills what the secret leaves out.
- **R3-ADV-3.** `grep` of `tests/` for `must be https`, `base_url must` and `http only for loopback` finds only `tests/warden_port/test_audit_chain.py:362` (`endpoint_url`, unrelated). One existing test matches the https refusal: `tests/test_review_fixes.py:120-126` (`test_base_url_scheme`, `match="https"`). U's new text keeps the words "base_url must be https", so that test stays green.
- **R3-ADV-4.** `tests/warden_port/fakes.py:16-17` defines Python constants NAMED like the AWS variables. They are redaction canaries, built from parts. `tests/warden_port/test_redaction.py` imports them (`:7-8`, `:61`, `:182`). Neither file calls `load_config` or `build`, or names pilot or prod. They are not environment uses and need no `delenv`.
- **R3-COR-2 is TRUE.** P5c is "DRAFT revision 3" (`tickets/P5c.md:1`). `:259` is a table row and `:323` is `- CHANGELOG.md.`. By name, the `TABLE["redactor"] = {"regex": Entry(KindSettings, ...)}` line is at `:317`, and the sentence "The redactor kind has `identity="none"` and `rights=()`. It is pure and in-process" is at `:387`.
- **R3-COR-6 is TRUE.** The `backends/table.py` hot-file list in `tickets/P6b1.md` is line `:137`, not `:136` (`:136` is the `config.py` list). `:137` lists P5b3 and P6a as editors, and P6b1 only in its trailing sentence.
- **R3-COR-7 (time part CONTESTED).** Order 20 (`LEAD-ORDERS.md:74`) says "the push times in git are the truth". `git log` shows orders 25, 26 and 27 pushed at 03:35, 03:40 and 03:42 UTC (09:05, 09:10 and 09:12 IST), and ticket revision 3 at 03:50 UTC. The "~04:10Z/04:25Z" stamps inside the orders carry the lead's known wrong hour. So "applies orders 6 to 26" is consistent in time. Order 27 is not mentioned, which is TRUE.
- **R3-COR-9 is TRUE.** `(f"{PKG}.config", "slack")` is at `tests/test_lockin_guard.py:509`.
- **R3-COR-8, which variables the installed SDKs read.**
  - `azure/identity/_credentials/environment.py:81-85` signs in as a USER when `AZURE_CLIENT_ID`, `AZURE_USERNAME` and `AZURE_PASSWORD` are all set (deprecated, but present).
  - `AZURE_CLIENT_CERTIFICATE_PASSWORD` is used only together with `AZURE_CLIENT_CERTIFICATE_PATH` (`:75`), which N2 refuses already.
  - `botocore/credentials.py:1199-1204`: `AWS_SECURITY_TOKEN`/`AWS_SESSION_TOKEN` are tokens read beside the access-key pair, which N2 refuses already.
- **PENDING LEAD 14's SDK question, own finding N2.** In anthropic 2.1.0 (`anthropic/_client.py:227-232`), an explicit `api_key=` means environment variables are not consulted. `key=None` falls back to `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_PROFILE`, federation variables or a profile on disk (`:199-214`). `llm/anthropic.py:81-84` passes `None` only for `vertex`, and `AnthropicSettings._platform_fields` makes `api_key_secret_name` required for `api` and `foundry` (`table.py:53-61`). So the explicit key always wins on the installed SDK.
- **R3-COR-11.** `grep` finds no `runpy` or `pkgutil` import and no `resolve_name` anywhere in `src/hadavin_sdk` (fact 14 holds), so no file needs the `backends/` exemption.

## Banner for the ticket (placed under the status line, word for word)
> **Build notes win.** Revision 3 is frozen text. Where a build note BN-1 to BN-15 differs from the revision 3 text, the build note wins. The notes come from `handover/reviews/P6b2-round3-resolve.md` and are copied into the section "Build notes (round 3)" at the end of this ticket. The CHANGELOG sections are history, not instructions. Counts after the build notes: 35 rows, 60 mutants, 13 `ALLOW` entries, and seven N2 variables. Line cites into `tickets/P5c.md` were written against P5c revision 2: find each by its name (BN-6), not by its line number.

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major), R3-COR-1 (Major) | PROPOSE FIX | TRUE (probe 1). Ma37 is KEPT and gets an observable killer: C8 (f) uses an invalid `agents.yaml` and must exit 0 with `migrate` called. The count stays 59 before BN-5. COR-1's "this existing test also kills Ma37" holds only for a mutant that loads the registry before step 2: stated. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX (NEEDS LEAD 16; default taken) | TRUE. Decided in text: N2 applies to EVERY command that loads a pilot or prod config, the operator commands included. One cli sub-case is added to A1, plus the owner-visible line and the Rollback note. **BN-2.** |
| R3-ADV-3 (Minor) | PROPOSE FIX | TRUE as a gap in the text. The checked line goes in: one existing test matches `"https"` and stays green. **BN-3.** |
| R3-ADV-4 (Minor) | PROPOSE FIX (the warden_port part CONTESTED: those hits are constants, not environment uses; Facts) | The list is closed by the full suite, and the final changed-test list is written to evidence. Fact 26 gains the warden_port sentence. **BN-4.** |
| R3-ADV-5 (Minor) | PROPOSE FIX (INFORM 19) | TRUE. Fixed at the choke point: a shape pattern on `migrate_credential_ref`, so a DSN pasted into the ref is refused at load and never echoed. New C3 case and mutant Ma38. **BN-5.** |
| R3-ADV-6 (Minor) | CONTEST | `store/postgres.py:138-146` always passes an explicit password in the `iam_auth` path. N10 forces an explicit password otherwise in pilot and prod. Dev's password-less DSN is intended and is covered by owner-visible line 3 (Facts; libpq precedence from memory, Honest note). No build note. |
| R3-ADV-7 (Minor) | CONTEST | The ticket already explains the gap: line 692, "Rows (b) and (c) are cut with the registry load". The reviewer itself says the count is consistent. Renumbering frozen ids would break the R2 trace. No build note. |
| R3-ADV-8 (Nit) | PROPOSE FIX | The four test functions are named (Facts). **BN-13.** |
| R3-ADV-9 (Nit) | DECLINE | Frozen text. The banner tells the builder that the CHANGELOG is history. Moving it changes no builder action (round 2 declined ADV-12 for the same reason). |
| R3-COR-2 (Major) | PROPOSE FIX | TRUE. P5c cites by name, at P5c revision 3 `:317` and `:387`. The (`redactor`, `regex`) -> {`none`} row is "as P5c revision 3 states; re-read at P5c-1 merge". **BN-6.** |
| R3-COR-3 (Major) | PROPOSE FIX (with own finding N1: C7 has the same defect) | TRUE (probe 2). N11's place is pinned: after `load_config`, before `load_registry`. Every `app.build` row in this ticket stops before any backend, with no Postgres. **BN-7.** |
| R3-COR-4 (Minor) | PROPOSE FIX (INFORM 17) | TRUE. F5's "pass credentials explicitly" is applied to the API-key constructors only (L5). The 13 cloud sites stay ambient and pinned, for the stated least-privilege reason. **BN-8.** |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE. N10's password rule is relabelled "ticket addition, INFORM", inside PENDING LEAD 15. **BN-9.** |
| R3-COR-6 (Minor) | PROPOSE FIX | TRUE. The cite is fixed, and the P5b3/P6a `table.py` disagreement is relayed (PENDING LEAD 4). **BN-10.** |
| R3-COR-7 (Minor) | PROPOSE FIX (the time-stamp part CONTESTED: git push times, Facts) | One line on order 27: nothing in it changes P6b2. **BN-11.** |
| R3-COR-8 (Minor) | PROPOSE FIX (INFORM 18) | TRUE. A reason is given for each name left out. `AZURE_PASSWORD` is ADDED: a long-lived user password that the installed SDK signs in with. **BN-12.** |
| R3-COR-9 (Nit) | PROPOSE FIX | Cite `:509`. **BN-13.** |
| R3-COR-10 (Nit) | PROPOSE FIX | The four Google plants are listed. **BN-13.** |
| R3-COR-11 (Nit) | PROPOSE FIX (surface cut) | The `backends/` exemption is removed. `pkgutil.resolve_name` and `runpy` are flagged everywhere (fact 14: no use anywhere). **BN-14.** |
| (resolve, own) N2 | PROPOSE FIX | PENDING LEAD 14's SDK question is settled for the installed anthropic 2.1.0. **BN-15.** |
| (resolve, own) N3 | fact only | Ticket cites hold at `397ec97` (Facts). The UNVERIFIED line "handover tree equals `397ec97`" is closed. No builder action. |

## Build notes (round 3) - to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. Ma37 gets an observable killer (R3-ADV-1, R3-COR-1).**
- C8 (f) is replaced by this row. Set up a dev `cfg_dir` as follows:
  - `store` = postgres with `migrate_credential_ref: migrate-dsn`, the `env` secrets kind, and `HADAVIN_SECRET_MIGRATE_DSN` set to a made-up password-less DSN (dev, N10 allows it);
  - `agents.yaml` overwritten with `- not: an agent\n`, exactly as `tests/test_p2_postgres.py:96-103` does;
  - `store.migrate.migrate` patched.
- `cli.main(["--config", ..., "migrate"])` must return 0, and the patched `migrate` must be called once.
- With Ma37, `load_registry` raises `ConfigError` (probe 1: "validation errors for AgentRecord"), so the run returns 2 and the row fails. On the base the row cannot run, because it needs the new field: "new feature; proven by Ma37".
- The words "no agents, contracts or tools folder" in C8 (f) and in `_migrate` step 3 read "an `agents.yaml` that does not load". Probe 1 shows an empty folder loads, so the old wording proved nothing.
- C6: the rewritten `test_migrate_does_not_need_a_valid_registry` KEEPS its invalid `agents.yaml`. It sets NO ref and asserts exit 2 with `migrate_credential_ref` in stderr: it reaches step 2, not the registry. It kills Ma37 only when the mutant loads the registry before step 2. C8 (f) kills it wherever the load is put.
- Ma37's killer reads "C8 (f) (and C6's `test_migrate_does_not_need_a_valid_registry` for a load before step 2)".

**BN-2. N2 applies to the operator commands too (R3-ADV-2; PENDING LEAD 16, default (a) taken).**
- **Decided in text:** N2 stays in `Config._cross_checks`, so it runs in `load_config` for EVERY command with a pilot or prod config. That covers the runtime, `tick`, `migrate`, `limits stop/reset`, `audit verify`, `gate`, `replay` and `score` (`cli.py:136`; `tick` through `app.build`). It is not scoped to `app.build`.
- **Why:**
  - the operator commands hold the higher rights: the migration role and the reset of a stop;
  - the least-privilege rule wants short-lived credentials there most of all;
  - a long-lived key exported in an operator shell is exactly what N2 refuses for the runtime.
- **The way out for an operator:** a sign-in that does not use the seven variables. Examples are a named profile or SSO login (files, not checked, V1), or the machine's own role. `migrate` with `iam_auth` then signs in through `store/auth_aws.py:16` with that identity.
- **A1 gains one cli sub-case**, not a new row:
  - take a pilot operator folder (`pilot_cfg` with `migrate_credential_ref` set and no runtime-only problem);
  - remove the conftest pair, then set `AWS_ACCESS_KEY_ID` alone;
  - `cli.main(["--config", <folder>, "migrate"])` returns 2, stderr names `AWS_ACCESS_KEY_ID`, and the patched `migrate` is never called.
  - A mutant that moves N2 into `app.build` is already killed by A1's `load_config` cases, so there is no new mutant.
- **Owner-visible line 4 (new, for the lead to copy):** "In pilot and production, the operator commands (database migration, kill-switch reset, audit check) also refuse to start when a cloud key is set in the shell. The operator signs in with a profile, a single sign-on login or the machine's own role instead."
- **Rollback note:** "reverting N2 also lifts this refusal for the operator commands".
- **CHANGELOG N2 line:** add "(every command, the operator commands included)".
- **If the lead answers (b), scope N2 to the runtime:**
  - N2 moves into `app.build`, right after `load_config`, as a `ConfigError` with the same text;
  - A1 calls `app.build` with `app.load_registry` patched to raise `_Reached` (BN-7 shape);
  - the cli sub-case flips: `migrate` is NOT refused;
  - `ALLOW` 7-13 move from `config.py` to `app.py`, and A3 patches `app.os`.

**BN-3. The old base_url text in existing tests (R3-ADV-3).** Add to U: "grep of `tests/` for the old text (`must be https`, `base_url must`, `http only for loopback`) finds only `tests/warden_port/test_audit_chain.py:362` (`endpoint_url`, unrelated). One existing test matches the https refusal, `tests/test_review_fixes.py:120-126` (`test_base_url_scheme`, `match="https"`). It stays green because the new text keeps the words `base_url must be https` (checked in the round 3 resolve)". The builder re-runs the grep at the base.

**BN-4. The tests changed for N2 (R3-ADV-4).**
- The rule stays: the full suite at the P6b2-a base, with N2 in place, decides which pilot or prod tests need `delenv`.
- Evidence command 2's file lists every changed test as `file::function`, each with the failing line it had before the `delenv`, as "the oracle". A test that needed the conftest AWS pair for a cloud kind gets `monkeypatch.delenv` plus a FakeEnv only where that kind is not built. If a test needs the pair AND a pilot or prod config, the builder stops and asks the lead (`questions-for-lead.md`). Such a test would prove that N2 blocks a real flow.
- Fact 26 gains: "`tests/warden_port/fakes.py:16-17` and `tests/warden_port/test_redaction.py` hold Python constants named like the AWS variables (redaction canaries). They are not environment uses and need no `delenv` (checked in the round 3 resolve)".

**BN-5. The ref's shape is checked at load (R3-ADV-5; INFORM 19).**
- F1 becomes `migrate_credential_ref: str | None = Field(default=None, min_length=1, max_length=256, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/@+-]*$")`.
- A URL-form DSN (`://`), a keyword DSN (`=`, spaces), a newline or a control character can therefore never be a ref. `hide_input_in_errors` (`table.py` `KindSettings`) keeps the value out of the pydantic error. So every later `<ref>` echo in `_migrate`'s texts is a checked name.
- Why at the choke point: the realistic mistake is an operator pasting the DSN itself into the ref field. Without the pattern, step 5's "cannot be read" text would print it.
- C3 gains a seventh case: a ref built from parts at run time as `postgresql://u:<canary>@h/d` is refused at load, and the canary is absent from the text. The C3 count reads "Seven rows".
- New mutant **Ma38**: "the ref pattern is dropped". Killer: C3, the DSN-shaped case. That makes 60 mutants.
- Relay to P2a's build-start review: `reset_credential_ref` and `stop_credential_ref` are echoed the same way and would take the same pattern. That is P2a's text.

**BN-6. P5c cites by name (R3-COR-2).**
- Facts 19 and "Relays" read:
  - "P5c-1 adds (`redactor`, `regex`): the `TABLE["redactor"]` line in P5c's Files field (`tickets/P5c.md:317` in P5c revision 3)";
  - "P5c states the kind is pure and in-process, `identity="none"` (P5c's security notes, `:387` in revision 3)".
- The (`redactor`, `regex`) -> {`none`} row reads "as P5c revision 3 states; the builder re-reads it from P5c-1's merged `table.py` and P5c's final notes before adding the row (D6)".
- The cites `P5c.md:259` and `:323` are void.

**BN-7. Every `app.build` row stops before any backend; N11's place is pinned (R3-COR-3; own finding N1 on C7).**
- **N11's place:** in `app.build`, right after `load_config` (after P6a-1's S2 check once that has merged) and BEFORE `load_registry` (`app.py:80`) and every `make`.
- **C10 shape:** every C10 row patches `app_mod.load_registry` with a stub that raises a test-local `_Reached`.
  - (a), (b), (d), (e): `ConfigError` naming the field, and the stub is never called. That proves N11 raises before the registry and before any backend.
  - (c) dev, and (f) pilot with `stop_credential_ref` set and neither other ref: `_Reached` is raised. That is no `ConfigError`, so N11 let the config through.
  - No Postgres and no network. The Tests header "no Postgres" now holds.
  - Mp11d (stop ref refused too) fails (f), because the run raises `ConfigError` before `_Reached`.
- **C7 shape (own finding N1):** C7's config must have a postgres store, because the field exists only on `PostgresSettings`. As written, `app.build` would connect at `make("store")` (`app.py:146`, `store/postgres.py:152-163`).
  - C7 passes a recording provider as `secrets=`, and patches `app_mod.make` to raise `_Reached` at its first call, `make("signer")` (`app.py:144`).
  - Probe 2 shows a dev postgres `cfg_dir` reaches that point with no database, after `platform_secrets.check` (`:122`) has asked for its names.
  - Assert `_Reached`, and that the recorded names do not include the ref. Ma15 still fails C7, because `check` would ask for a `*_secret_name` field.
- C10 (f) needs P2a-1's `stop_credential_ref` field (fact 24), as before.

**BN-8. F5's explicit-credential check, as built (R3-COR-4; INFORM 17).** Add under D1:
- "A9 F5 says the lint checks that the llm and cloud backends pass credentials explicitly. v1 builds that check for the API-key constructors (L5, E8).
- The 13 cloud sites stay ambient, and they are pinned (L4, E7), not rewritten. For the clouds, the least-privilege rule prefers the platform's short-lived role over an explicit long-lived key. Forcing an explicit credential there would push operators towards stored keys.
- The implicit chain's environment half is closed by N2, and its file half is V1."

**BN-9. N10's password rule is a ticket addition (R3-COR-5).** N10's label reads "DECIDED, order 22 item 25 (`passfile`/`service` refusal); the pilot/prod password rule and the `sslcert` cut are ticket additions, INFORM (PENDING LEAD 15)". PENDING LEAD 15 covers both.

**BN-10. The P6b1 hot-file cite (R3-COR-6).**
- The `table.py` hot-file line reads "(`tickets/P6b1.md:137` also lists P5b3 and P6a as `table.py` editors, and P6b1 in its trailing sentence)".
- The disagreement stays open. P5b3 revision 2 (`P5b3.md:83`) and P6a revision 3 (`P6a.md:256`) say they do not edit `table.py`. P6b2 keeps fact 19 and relays this through PENDING LEAD 4 (item 4d).
- Builder rule: whichever packages have merged at the rebase are the truth (D6 rebase check).

**BN-11. Order 27 (R3-COR-7).** Header line 5 reads "LEAD-ORDERS 6 to 27. Orders 25 and 26 are about P1m. Order 27 item 50 gives `config.py` to P6a-1, which this ticket already orders first (P6a-1 early). Item 46 allows a throwaway PostgreSQL 17 for builders. No item of order 27 changes P6b2". The time stamp stands: git push times are the truth (order 20).

**BN-12. N2's variable list: seven names, and why the rest are out (R3-COR-8; INFORM 18).**
- **Added:** `AZURE_PASSWORD`. Installed azure-identity signs in as a user with `AZURE_CLIENT_ID` + `AZURE_USERNAME` + `AZURE_PASSWORD` (`_credentials/environment.py:81-85`). That is a long-lived password, the same class as `AZURE_CLIENT_SECRET`.
- **Counts:** `ALLOW` 7-13 (13 entries); A1 has 14 cases plus BN-2's cli case; fact 1's sum reads 9 - 1 + 7 = 15 = `ALLOW` 13 + `EXEMPT` 2. Also "six" reads "seven" in D1, N2, the CHANGELOG and A2.
- The builder re-runs fact 23's guard script on the seven names at the base. The round 3 resolve checked four of the patterns by script and the rest by eye (Honest note).
- **Out, with the reason** (one sentence each in N2):
  - `AWS_PROFILE` and `AWS_DEFAULT_PROFILE` choose a profile in a credentials FILE. Files are V1, and refusing only the selector would be half a check.
  - `AWS_WEB_IDENTITY_TOKEN_FILE`, `AWS_ROLE_ARN`, `AWS_CONTAINER_CREDENTIALS_*` and `AZURE_FEDERATED_TOKEN_FILE` are how platforms deliver SHORT-LIVED role credentials (from memory, UNVERIFIED), the path the least-privilege rule prefers. Refusing them would block the safe path.
  - `AWS_SECURITY_TOKEN` and `AWS_SESSION_TOKEN` are read only beside the access-key pair, which is refused. `AWS_SESSION_TOKEN` stays in the list as before.
  - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` and `AZURE_USERNAME` are identifiers and need a secret variable to sign in.
  - `AZURE_CLIENT_CERTIFICATE_PASSWORD` is used only with `AZURE_CLIENT_CERTIFICATE_PATH`, which is refused.
  - `AWS_ENDPOINT_URL*` redirects calls and is not a credential. `tests/conftest.py` isolates it for test safety only.
  - `ANTHROPIC_*`: BN-15.

**BN-13. Small cites and wording (R3-ADV-8, R3-COR-9, R3-COR-10).**
- "the four tests of fact 8" are:
  - `tests/test_p2_postgres.py::test_migrate_does_not_need_a_valid_registry` (`:96`);
  - `tests/test_p2_postgres.py::test_migrate_needs_the_migration_dsn` (`:106`);
  - `tests/test_p7_tick.py::test_cli_migrate_warns_when_new_tables_get_no_grants` (`:497`);
  - `tests/test_k2_migrations.py::test_cli_migrate_passes_the_portal_role` (`:128`).
- Fact 22: `LITERAL_OK` `(config, "slack")` is at `test_lockin_guard.py:509`.
- E7 "the four Google forms of L4" are four plants, each found:
  - (i) `from google.cloud import storage; storage.Client()`;
  - (ii) `from google.cloud import kms as k; k.KeyManagementServiceClient()`;
  - (iii) `import google.cloud.storage; google.cloud.storage.Client()`;
  - (iv) `from google.cloud.storage import Client; Client()`.
  - Plus `from other import x; x.YClient()` NOT found, as written. Ma25 (imported name only) misses (i), (ii) and (iii).

**BN-14. `pkgutil.resolve_name` and `runpy` are flagged everywhere (R3-COR-11; surface cut).**
- H1's "outside `backends/`" is deleted for these two. Fact 14 shows no use anywhere in `src`, and the dynamic import that `backends/factory.py` needs goes through `import_module`, which `import_problems` pins (fact 10).
- S6 gains one plant in a file named `backends/factory.py`, which is flagged. Ma28 is unchanged.
- H2's `make(<not a constant>)` exemption for `backends/` stays, because `backends/factory.py` defines `make`.

**BN-15. PENDING LEAD 14's SDK question is settled for the installed SDK (own finding N2).**
- PENDING LEAD 14 and the UNVERIFIED list read: "anthropic 2.1.0 (the `uv.lock` pin) reads no credential variable when `api_key=` is passed (`anthropic/_client.py:227-232`). `llm/anthropic.py` passes `None` only for `vertex`, and `api_key_secret_name` is required for `api` and `foundry` (`table.py:53-61`)."
- The SDK's fallback for `key=None` (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, profiles, federation) is therefore never reached by our kind, so `ANTHROPIC_*` stays off the N2 list.
- E8's rule (`api_key` passed and not the literal `None`) is the static half. The settings validator is the runtime half.
- The builder re-reads `_client.py` if the pin moves.

## Positions
- **BN-1 keeps the mutant instead of dropping it.** Dropping Ma37 would leave "migrate needs no valid registry" unguarded. That behaviour is why step 3 was rewritten in revision 3, so the mutant guards a real choice. The fix costs no row: one fixture line, copied from an existing test.
- **BN-2 takes the stricter reading.** Scoping N2 to the runtime (b) would leave long-lived keys usable exactly where the rights are highest (migration, reset). The cost (a clean shell for operator commands) is stated to the owner. It is a NEEDS LEAD because it touches the owner's least-privilege rule and the operator's daily flow.
- **BN-5 and BN-12 add surface on a security path, on purpose.** Order 7(3) says "a found defect is never dropped". Each is a one-line rule at an existing choke point with one test case, and BN-5 has one mutant. BN-14 removes an exemption, so it is a cut.
- **BN-7 changes no row count.** It makes three rows (C7, C10 (c) and (f)) runnable as the Tests header already promised.
- **R3-ADV-6 and R3-ADV-7 are contested on facts a reader can check** (`store/postgres.py:138-146`; ticket line 692). The R3-ADV-6 contest depends on libpq precedence from memory, which the Honest note flags.

## Couplings
- BN-2 and C9: the pilot C9 rows already remove the conftest pair. BN-2's cli case is the only migrate row that sets a variable.
- BN-2 and N11: the operator folder for `limits` passes `load_config` (with N2) AND `load_registry` (`cli.py:139`). Probe 1 shows an empty registry loads in dev. Whether `deferred.check` accepts an empty registry in pilot or prod is UNVERIFIED: a relay to P2a's build-start review, because `limits` is P2a's path.
- BN-5 and P2a: the same pattern is recommended for P2a's two refs (relay). Until P2a adopts it, F1's disjointness rule still compares raw strings.
- BN-7 and P6a-1: N11 sits after P6a-1's S2 check. A C10 row that would also trip S2 must use a config S2 accepts. Revision 3's `pilot_cfg` does, per P6a's round 3 probe.
- BN-7 and BN-1: both use test-local `_Reached`/patched `migrate` stubs. Neither needs `HADAVIN_TEST_PG_DSN`.
- BN-12 and A3: `FakeEnv` holds seven canaries. A3's namespace still needs only `environ`.
- BN-12, BN-15 and PENDING LEAD 13: V6 and owner-visible line 2 are unchanged.
- BN-10 and PENDING LEAD 4: the `table.py` order is settled at rebase by what has merged.

## PENDING LEAD (continuing the ticket's numbering after 15)
- **4 (extended, BN-10):** item 4d. Relay to the lead: `tickets/P6b1.md:137` lists P5b3 and P6a on `backends/table.py`, while `P5b3.md:83` and `P6a.md:256` say they do not edit it. Recommend: the lead tells P6b1's builder to drop the two from its list.
- **14 (updated, BN-15):** the SDK question is settled for anthropic 2.1.0. The INFORM stands.
- **15 (widened, BN-9):** INFORM covers both ticket additions to N10, the pilot/prod password rule and the `sslcert` cut. Recommend: accept.
- **16. NEW, NEEDS LEAD (least privilege). Does N2 apply to the operator commands (R3-ADV-2)?** The builder's default meanwhile is (a).
  - (a) RECOMMENDED: yes, every command that loads a pilot or prod config, `migrate`, `limits` and `audit verify` included. The operator signs in by profile, SSO or the machine role (BN-2). Cost: an operator who exports cloud keys in the shell must unset them. Owner-visible line 4.
  - (b) N2 only in `app.build` (the runtime). This is smaller for operators, but long-lived keys stay usable for the migration and reset commands.
  - Confidence 75 percent. Reversible until P6b2-a merges, and after that by one edit. It touches the owner's least-privilege rule, so the lead may want the owner to see line 4.
- **17. NEW, INFORM. F5's explicit-credential check (R3-COR-4, BN-8).** Recommend: accept. The API-key constructors only; the 13 cloud sites stay ambient and pinned; files are V1.
- **18. NEW, INFORM. `AZURE_PASSWORD` added to N2 (R3-COR-8, BN-12).** Recommend: accept. Counts: 7 names, 13 `ALLOW` entries, 14 A1 cases. Reversible.
- **19. NEW, INFORM. Shape pattern on `migrate_credential_ref` (R3-ADV-5, BN-5).** Recommend: accept, and relay the same rule to P2a's refs. Reversible. A valid secret name with `=`, `:` or a space would be refused; I know of none in the secrets kinds used here (UNVERIFIED for every client store).

## Counts
- Finding ids: 20 (ADV 9, COR 11). Majors 5 (ADV-1, ADV-2, COR-1, COR-2, COR-3). Minors 10. Nits 5. No Blocker. No severity changed.
- PROPOSE FIX 17:
  - ADV-1, 2, 3, 4, 5 and 8;
  - COR-1 to COR-11.
  - They are in build notes BN-1 to BN-14.
- CONTEST 2 (ADV-6, ADV-7). DECLINE 1 (ADV-9). ESCALATE 0.
- Partial contests inside a PROPOSE FIX row: 2 (ADV-4, the warden_port hits; COR-7, the time stamp). Partial limit: COR-1, where the existing test kills Ma37 only for a load before step 2.
- Own findings: 3. N1 (C7 needs Postgres as written, in BN-7), N2 (BN-15), N3 (cites hold at `397ec97`, fact only).
- Ticket numbers after the build notes:
  - 35 rows (unchanged; sub-cases added to A1, C3, S6 and E7);
  - FAIL-BEFORE rows E1, C1, U1 (unchanged);
  - 60 mutants (Ma1-Ma38 = 38; Mb 8; Mp2 2; Mp10 6; Mp11 4; Mu 2);
  - 13 `ALLOW` entries, 2 `EXEMPT` entries, and 7 N2 variables;
  - 31 identity declarations (unchanged).
- PENDING LEAD: 4 new (16 NEEDS LEAD; 17, 18, 19 INFORM), 3 updated (4, 14, 15).
- Fixes applied to the ticket in this step: 0 (they are build notes). Remaining unaddressed findings: 0.
- One new owner-visible line for the lead to copy (BN-2, line 4).

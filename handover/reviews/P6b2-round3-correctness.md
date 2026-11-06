# P6b2 round 3, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

R3-COR report: P6b2 revision 3 (`handover/tickets/P6b2.md`). Persona: correctness. No Blocker found. 3 Majors, 5 Minors, 3 Nits.

I read the ticket completely, the template, LEAD-ORDERS (all of it), amendments A9 F5/F6, and the cited source and tests under `<repo>/hadavin-sdk-handover/src` and `<repo>/hadavin-sdk-handover/tests`. I did not open `reviews/` or `evidence/`. I could not run anything: I had no shell tool, only Read, Grep and Glob. Every count below was done by hand on grep and read output. The tree is not a git checkout, so "current main differs from `397ec97`" is UNVERIFIED either way. One visible drift: `cli._migrate` and the `migrate` parser already have `--purge-role` (`cli.py:98-102, 312-314`) and `app.py:86-89` already requires `purge_dsn_secret_name` in pilot and prod. The ticket never mentions either. Neither breaks a cite.

## Findings
| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 676-691, 778 (Ma37, C8 f) | Ma37 ("`_migrate` loads the registry") names C8 (f) as its killer. C8 (f) runs `migrate` on a folder with no agents, contracts or tools folder. That folder loads fine today: `registry.py:179-180` (`_yaml` returns None for a missing file), `:186` (`_by_id` accepts None) and `:243` (`folder.is_dir()` guard) all tolerate it. So the mutant survives C8 (f). The 59-with-named-killer claim fails for this one. Whether `deferred.check` (`registry.py:230`) rejects an empty registry I did not read: UNVERIFIED. | Make C8 (f) write an invalid `agents.yaml` (`- not: an agent`), as `tests/test_p2_postgres.py:96-103` does. A registry load then raises, and `migrate` must still reach the new refusal. Say that this existing test also kills Ma37. |
| R3-COR-2 | Major | 188, 290 (and 19, 252) | Cites `P5c.md:259` ("TABLE line") and `P5c.md:323` ("identity sentence") do not hold. Line 259 is a table row `\| a/c \| with or without \| yes \|`. Line 323 is `- CHANGELOG.md.`. The file now says "DRAFT revision 3" (line 1). `redactor` appears at lines 38, 64, 103; "identity" at 348, 386, 387, 723. The CHANGELOG line 70 says these were re-anchored (COR-7), so the re-anchoring did not match the file as it stands. | Re-cite by symbol and the right lines, or drop the line numbers. Mark the (`redactor`, `regex`) -> {`none`} row UNVERIFIED until P5c freezes. |
| R3-COR-3 | Major | 448, 668-670 vs 604 | C10 (f) and mutant Mp11d say "a pilot config with `stop_credential_ref` set ... builds". `app.build` goes on to `make("store")`, `load_registry` and `platform_secrets.check`. For a postgres store that means a real database; `test_k3_pilot_env.py:1` says the App test needs `HADAVIN_TEST_PG_DSN`. The Tests header says "no Postgres, no network". The row cannot run as worded, and Mp11d would have no executable killer. Also, N11 (a)/(b) only prove "raises before backends" if N11 sits before `load_registry` and `make`; the ticket pins the position only as "right after `load_config`" via P6a-1 (`P6a.md:254`). | Reword (f) as "N11 raises no ConfigError naming `stop_credential_ref`". Run it with `make`/`load_registry` patched, or assert only that the error text is absent. State where the N11 line sits in `app.build`. |
| R3-COR-4 | Minor | 16, 24, 428-449 vs `amendments.md` F5 | The header says it "Applies A9 F5". F5 says the lint "checks that the llm and cloud backends pass credentials explicitly (no implicit environment chains)". The ticket pins 13 ambient-identity sites (D1) and defers narrowing to V1. That is a partial application of a DECIDED amendment. It is not listed as a PENDING LEAD or a departure, unlike PL12. | Add one line under D1 or a PENDING LEAD: "F5's explicit-credential check is built for the API-key constructors only (L5). Cloud kinds stay ambient, V1." |
| R3-COR-5 | Minor | 450-460, 857 | N10 is labelled "DECIDED, order 22 item 25". The order (LEAD-ORDERS line 99) says only "narrow libpq passfile/service refusal in `_migrate`". The "no or empty password refused in pilot/prod unless `iam_auth`" rule goes beyond it. PL15 informs the lead only about the `sslcert` cut. | Mark the password rule as "ticket addition, INFORM", as PL12 does. |
| R3-COR-6 | Minor | 277 | "`tickets/P6b1.md:136` lists P6b1 there too" is wrong. Line 136 lists P4d, P2a-1, P4b2-b, P4c, P4a, P5b3, P5b4, P5c, P6b2, P6a. P6b1 appears only in the trailing sentence. That list also puts P5b3 and P6a on `table.py`, while fact 19 and line 277 say they do not edit it. | Fix the cite wording, and relay the P5b3/P6a disagreement to the lead or P6b1. |
| R3-COR-7 | Minor | 3, 5, 94 vs LEAD-ORDERS | The ticket is stamped 03:45 UTC. It says it applies orders 6 to 26, but order 25 is stamped ~04:10Z and order 26 ~04:25Z. Order 27 (~04:30Z) item 50 (P6a PL14 `made_up_data_only`, `config.py` belongs to P6a-1) is not mentioned. | Fix the time stamp. Add a line that order 27 item 50 does not change the `config.py` order. |
| R3-COR-8 | Minor | 429, 449 | The N2 variable list covers `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AZURE_CLIENT_SECRET`, `AZURE_CLIENT_CERTIFICATE_PATH` and `GOOGLE_APPLICATION_CREDENTIALS`. `tests/conftest.py:14-29` isolates a wider set: `AWS_PROFILE`, `AWS_DEFAULT_PROFILE`, `AWS_WEB_IDENTITY_TOKEN_FILE`, `AWS_CONTAINER_CREDENTIALS_*`, any `AZURE_*`. The ticket does not say why six is enough (e.g. Azure username/password variables). The stated limit covers credential files only. | Add one sentence on why the other names are out (UNVERIFIED SDK behaviour), or add them. If you add any, check the ALLOW count of twelve, E1 and A1's twelve cases. |
| R3-COR-9 | Nit | 215 | `LITERAL_OK` `(config, "slack")` is at `test_lockin_guard.py:509`, not `:508`. | Fix the cite. |
| R3-COR-10 | Nit | 648 (E7) | "the four Google forms of L4" is not defined. L4 gives one Google rule (the import form is "under any alias") and no list of four. | List the four plants. |
| R3-COR-11 | Nit | 408 | `runpy`/`pkgutil.resolve_name` are flagged "outside `backends/`" with no reason why `backends/` is exempt (it imports neither today, fact 14). | Say why, or flag everywhere. |

## Verified (read, with result)
- **Rows: 35.** E 9 (E1-E8, E10), S 5 (S1-S3, S5, S6), C 10, I 7, A 3, U 1; 9+5+10+7+3+1 = 35. Row ids and sub-rows are consistent.
- **Mutants: 59.** Ma1-Ma37 = 37; Mb1, Mb3-Mb9 = 8; Mp2a-b = 2; Mp10a-f = 6; Mp11a-d = 4; Mu1-2 = 2. Sum 59.
  - Each has a named killer in the text.
  - I checked the killers by reading. Plausible killers: Ma3, Ma4, Ma14, Ma15, Ma19, Ma20, Ma25 (10 vs 13 sites) and Mb3/Mb4.
  - Ma37 is not killed as worded (R3-COR-1).
- **Sub-PRs: 2** (P6b2-a, P6b2-b). The ticket's "six parts" bullets match the Problem field.
- **PENDING LEAD.**
  - Open: 1, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15 (11 items; 14 and 15 are INFORM).
  - Decided: 2, 9, 10, 11.
  - The changelog saying PL5-7 stay open matches order 22 item 26 (it answers P8b's PL5-7).
- **Template.** All 17 fields are present: id, path class, depends, problem, source, target, interface, neutral default, files, reuse, security, tests, mutation, evidence, reviewers, done, rollback. Fields hold concrete content.
- **Security of the text.** No real-looking secrets; canaries are "built from parts". The `postgresql://unused` strings are made-up.
- **Environment reads (fact 1).**
  - Matches: `cli.py:81`, `:133`, `:322`; `signer.py:123, 127`; `store/postgres.py:54, 56`; `secrets_env.py:17-18, 24`; `secrets_vault.py:146`; `audit_sink.py:54`; `config.py:311, 439`.
  - No reads in `secrets_aws.py`, `secrets_azure.py`, `secrets_gcp.py`, `secrets_file.py`.
  - Count: 9 reads today, minus the migrate DSN, plus 6 N2 presence tests, gives 14 = ALLOW 12 + EXEMPT 2.
  - `config.py` has no `import os` today (imports at lines 6-21; `urlsplit` at 12).
- **Fact 3.**
  - 9 holder pairs from 6 files: `app.py:21, 22, 27`; `builtin.py:8`; `factory.py:11, 12`; `cli.py:38`; `audit_sink.py:14`; `signer_vault.py:21`. A repo-wide grep found no others.
  - 25 `make(` calls with a string-constant first argument: app 9, cli 11, audit_sink 5.
  - `make("secrets")` sites: `app.py:82`; `cli.py:150, 184, 215, 329`.
- **Fact 21.** Non-constant `getattr` sites: 12, with the listed file and line pairs. `factory.py:56` is a constant name and so correctly not counted.
- **Facts 14 and 25.** No `subprocess`, `ctypes`, `runpy`, `pkgutil`, `os.system`, `os.popen`, `dotenv` or `/proc/` in `src`. The only hits are the strings at `tools.py:284, 291`, which the lint would not flag.
- **L4 sites.**
  - All 13 call lines match, and all 10 import lines match (`secrets_aws:14`, `signer_aws:13`, `anchor_s3:21`, `auth_aws:12`, `bedrock_guardrail:18`, `bedrock:15`; Azure 17/19/18; `anthropic:17`).
  - Google import lines are 17/19/17.
  - `llm/anthropic.py:42` is `AnthropicVertex`; `:49` (Foundry) and `:54` pass `api_key=key`.
- **TABLE.** 8 capabilities and 31 kinds (7, 6, 4, 2, 2, 5, 3, 2).
  - `TABLE` is at `table.py:386`, with `"secrets"` at `:387`.
  - The 8 builtin factory lines (388, 428, 468, 493, 503, 513, 544, 559) match.
  - `ALLOWED` is at `:570`, `DEV_ONLY` at `:593`, `extra="forbid"` at `:24`, `PostgresSettings` at `:116-138` (`purge_dsn_secret_name` at 120, `_checks` at 133).
  - Seven models have a `*_secret_name` field.
  - Identity table counts: workload 13, bootstrap 4, platform_secret 7, delegated 2, none 5.
- **platform_secrets.** `secret_names` at `:18-20`, `bound` at `:23-33`, `check` at `:36-63`; `app.py:122` and `cli.py:186` call `check`. The `app.py:100-122` name collection matches fact 16.
- **cli.py.**
  - `:74-76` (writer `:75`), `:77-83`, `:137-138` (migrate before `load_registry` at `:139`), `:299`, docstring `:9-10`, and `_migrate` at `:312-346` all match. `limits` builds `make("secrets")` directly at `:184`.
  - There is no `app.build` call in the `limits` path; the only `build(` call is in `_tick` (`:299`).
- **Guards.**
  - `test_lockin_guard.py`: `SRC:21`, `DYNAMIC_IMPORT_OK:80-84`, `_dynamic_target:96`, `import_problems:108`, test `:189`, `VENDOR_MODULES:493-501`, `literal_problems:592`, `_skipped_table_nodes:552`, test `:638-639`.
  - N2 name check: `aws` followed by `_` does not match the `(:|$)` pattern. The six names match nothing in either `PATTERNS` set (`test_lockin_guard.py:519-536`, `test_no_hardcoded_values.py:22-39`).
  - The Fact 22 explanation is correct: `bedrock` and `anthropic` strings in `config.py` would fail `test_core_logic_names_no_vendor`.
- **Test cites.**
  - `conftest.py:30-36` (AWS pair set at `:34-35`) and `cfg_dir` at `:74`.
  - `test_k3_pilot_env.py:35` (`pilot_cfg`).
  - `ci.yml:86, 93` DSN has no password.
  - The `HADAVIN_MIGRATE_DSN` test cites (`p7_tick:504`; `p2_postgres:99, 103, 108, 110`; `k2_migrations:135`) match, plus `CHANGELOG.md:238` and the `cli.py` docstring.
  - Fact 26: 13 test files contain a quoted `"pilot"` or `"prod"`.
- **Other tickets.**
  - `P2a.md:102` (mut-K5 requires `stop_credential_ref` in pilot and prod) holds; `P2a.md:115` has `migrate` requiring `reset_role`.
  - `P6a.md:94-95` and `:254, 256` match the cites.
  - `P5a.md:88`, `P2d.md:106`, `P5b3.md:83, 96, 123` hold.
- **Orders.**
  - 20 item 6 (3-round cap, extra round only for money or redaction packages), 21 item 17, 22 item 25 (PL2, PL9, PL10, PL11), 24 items 33 and 39 match the ticket's reading.
  - Orders 25 and 26 are about P1m.
  - A9 F6 split matches (P6b2 depends on P5c and P5b4).

## Not checked (UNVERIFIED)
- The ticket's own AST-script claims (fact 13's file count of 102, fact 3's 9 pairs as a scan result, fact 21 as an AST result). I confirmed them by grep only; the 12 `getattr` sites and 25 `make(` calls match.
- Whether the widened L4/L5 rules give exactly 13 sites on the real tree. I checked by reading call and import lines only.
- `conninfo_to_dict` behaviour (`passfile`, `service`, empty `password`, error text). Evidence command 0 settles it.
- Which existing pilot/prod tests need `delenv` under N2, and whether any (e.g. tests combining `"prod"` with moto AWS kinds, `warden_port/test_audit_chain.py`) depend on the AWS pair being present. Fact 26 admits the count is unsettled.
- The runtime behaviour of `deferred.check` on an empty registry (R3-COR-1).
- P2a-1, P5b3, P5b4, P6a-1 final code and the `refused:` writer. I read P2a, P5b3, P6a, P6b1 and P5c only at the cited lines.
- Fact 9 (demos), `getpass.getuser` variables, SDK credential-chain order, Lambda behaviour, libpq reads, Python 3.12.
- Fact 18 (a): the `store/postgres.py:70` TLS-default cite. I saw the `:79` use, not `:70`.
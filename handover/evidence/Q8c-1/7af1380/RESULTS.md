# Q8c PR 1: independent raw evidence, branch head 7af1380

EVIDENCE RUNNER record. I ran and recorded; I did not judge, review or fix anything. Model: Fable 5.2.

- Branch `core/q8c-1-policy-vault-kubernetes`, head `7af1380963ed2303d53499b6edef762268c48f58`.
- Compared with `origin/main` = `2a8c2aac89f83dd0a45af0412563b59ff4fe5632`.
- Run on 2026-11-11, about 15:20 to 15:40 UTC (20:50 to 21:10 IST). Python 3.13.18, PostgreSQL 16.15 (my own cluster, port 56180).
- I did not read the builder's report, checkpoint or proofs folder.
- Every test command ran with the nine cloud and token variables removed from the environment (`env -u AWS_ACCESS_KEY_ID ... -u VAULT_SECRET_ID`), as the brief lists them. No value was printed.

## 0. What was NOT run, and what failed (read this first)

1. **The Vault refusal tests have NOT been run against any real server by me.** No Vault or OpenBao server exists on this machine and I was told not to download one. The 11 tests in `tests/test_policy_engine.py` that need a real Vault-compatible server were SKIPPED (11 of 13 tests in that file). Nothing in this folder shows that a real Vault server refuses or allows anything. The two plants that the ticket says must make a refusal test fail (policy widened to the whole mount; admin token in place of the runtime token) are among those 11 and were NOT RUN.
2. **One test failed in the full suite on the branch head**: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (`AssertionError: a quadratic function must be flagged`). The branch does not change that file. Rerun of that file alone: clean `origin/main` 133 passed, exit code 0; branch head 133 passed, exit code 0. The machine load was 15.2 when the full run started and 4.8 when it ended. I state no cause.
3. **Two plants were NOT reported by the guard** (all 82 guard tests passed, the direct calls returned 0 problems, `--check` exit code 0):
   - P09a: in the Kubernetes module, an added request with `?watch=true` in its path, sent under the declared operation id `k8s.list_events`.
   - P04b (an extra plant, not in my brief): in the Vault secrets module, an ADDED `LIST` request sent through `getattr(self, "authed")(...)` with a literal name.
4. Not run: the stale-allowlist plant of the ticket (errata E9) was not in my brief's list, so I did not plant it myself. The branch's own test for it (`test_plant_a_stale_allowlist_line_is_caught`) passed in the full run, and its mutant row is KILLED (section 3).
5. Not run: CodeQL, SonarCloud, CodeRabbit and CI (they run on the pull request, not here). Kubernetes: no cluster was used by any test or probe.
6. Source hashes (section 7): the hash shows the file at that commit has the stated bytes today. I did not check that the permission names are in those files.

## 1. Engine tests (`tests/test_policy_engine.py`)

Full text: `engine-tests.txt`. Raw logs and XML: `/home/user/build/evidence-raw/Q8c1-7af1380/engine-*.{log,xml}`.

| Run | Command (after the `env -u ...` prefix) | Exit code | Result | Duration |
|---|---|---|---|---|
| no Vault address | `uv run --all-extras --group test pytest tests/test_policy_engine.py -v -rs -p no:cacheprovider` | 0 | 2 passed, 11 skipped | 2.12 s |
| no address, `HADAVIN_REQUIRE_VAULT_ENGINE=1` | the same | 1 | 2 passed, 11 errors | 1.57 s |

`HADAVIN_TEST_VAULT_ADDR` and `VAULT_ADDR` were not set in my environment (checked: 0 matching names).

Per test, run without the address:

| Test | Result |
|---|---|
| test_the_engine_tests_run_skip_or_fail_by_the_environment | PASSED |
| test_ci_requires_the_engine_tests_in_both_jobs_that_have_a_vault_service | PASSED |
| test_vault_secrets_the_allowed_read_works_with_only_the_generated_policy | SKIPPED |
| test_vault_secrets_the_read_is_refused_when_its_grant_is_removed | SKIPPED |
| test_vault_secrets_the_never_list_requests_are_refused_and_the_admin_control_is_not | SKIPPED |
| test_plant_a_vault_policy_widened_to_the_whole_mount_fails_the_refusal_check | SKIPPED |
| test_plant_the_admin_token_in_place_of_the_runtime_token_fails_the_refusal_check | SKIPPED |
| test_vault_transit_signing_and_the_public_key_work_with_only_the_generated_policy | SKIPPED |
| test_vault_transit_a_request_is_refused_when_its_grant_is_removed[R18] | SKIPPED |
| test_vault_transit_a_request_is_refused_when_its_grant_is_removed[R19] | SKIPPED |
| test_vault_transit_the_never_list_requests_are_refused_and_the_admin_control_is_not | SKIPPED |
| test_plant_a_transit_policy_widened_to_every_key_fails_the_refusal_check | SKIPPED |
| test_plant_the_admin_token_in_place_of_the_transit_runtime_token_fails_the_refusal_check | SKIPPED |

Skip reason, the same text for all 11: "needs a real Vault server (HADAVIN_TEST_VAULT_ADDR is not set): the local fake enforces no policy, so a refusal there would show nothing. CI runs these against its Vault service and requires them."

With `HADAVIN_REQUIRE_VAULT_ENGINE=1`: the same 2 tests PASSED; each of the 11 others was an ERROR at setup with "Failed: HADAVIN_REQUIRE_VAULT_ENGINE=1 but HADAVIN_TEST_VAULT_ADDR is not set: the Vault engine tests must run here".

## 2. Full suite on the branch head, with Postgres, without a Vault address

Command: `/home/user/build/heavy.sh env -u ... PGHOST=127.0.0.1 PGPORT=56180 PGUSER=postgres HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56180/postgres uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=.../full.xml -rs`

- pytest exit code: **1**. pytest's last line: `1 failed, 10635 passed, 12 skipped in 382.01s (0:06:22)`.
- Counted from the XML `testcase` elements: 10648 tests = 10635 passed, 1 failure, 0 errors, 12 skipped. The `testsuite` attributes say the same.
- Slot wait 270 s, run 385 s. Load (1 minute): 13.3 when queued, 15.2 at start, 4.8 at end. 4 cores.
- Failure (1): `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`: `AssertionError: a quadratic function must be flagged` (line 836).
  - Rerun of the file alone on a clean `origin/main` worktree (through heavy.sh, slot wait about 60 s): `133 passed in 3.29s`, exit code 0, load before 4.9.
  - Rerun of the file alone on the branch head: `133 passed in 3.33s`, exit code 0, load before 5.4.
- Skips (12): the 11 engine tests of section 1 with the reason quoted there, and `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]`: "Stubber refuses a malformed Converse shape before the kind sees it".
- List and log excerpt: `full-suite-failures-and-skips.txt`. Raw: `/home/user/build/evidence-raw/Q8c1-7af1380/full.{log,xml}`, `rerun-migration-{main,branch}.{log,xml}`.

## 3. Lint, scans, page check, mutants

Output: `gates-output.txt`, `mutant-rows.txt`.

| Command (after the `env -u ...` prefix, in the branch worktree) | Exit code | Output | Duration |
|---|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | `All checks passed!` | 1 s |
| `uv run --all-extras --group test ruff format --check` | 0 | `327 files already formatted` | under 1 s |
| `uv run --with bandit bandit -ll -r src tools` | 0 | `No issues identified.` at the level shown by `-ll`; totals by severity: Low 12, Medium 0, High 0; 17115 lines scanned | 2 s |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | no output | 1 s |
| `uv run --all-extras --group test python tools/policy_page.py --check` | 0 | no output | under 1 s |
| `/home/user/build/heavy.sh ... uv run --all-extras --group test python tests/policy_mutants.py` | 0 | `14 of 14 good; problems: []` | slot wait 200 s, run 11 s |

Mutant rows (all 14, as printed):

```
ok  KILLED       A1 a request with no grant is no longer reported  [test_plant_a_new_request_with_no_grant_is_caught]
ok  KILLED       A1 a grant whose request is gone is no longer reported  [test_plant_a_grant_whose_request_was_deleted_is_caught]
ok  KILLED       A1 a stale allowlist entry is no longer reported  [test_plant_a_stale_allowlist_line_is_caught]
ok  KILLED       Kinds: a kind on no list is no longer reported  [test_plant_a_new_kind_on_no_list_is_caught]
ok  KILLED       A4 an unverified grant with no pending entry is no longer reported  [test_plant_an_unverified_grant_with_no_pending_entry_is_caug]
ok  KILLED       A4 a source id that does not resolve is no longer reported  [test_plant_a_source_id_that_does_not_resolve_is_caught]
ok  KILLED       D1 a wildcard in a permission name is accepted  [test_plant_d1_a_wildcard_in_a_permission_name_is_caught]
ok  KILLED       D1 a wildcard resource with no bound is accepted  [test_plant_d1_a_wildcard_resource_with_no_bound_is_caught]
ok  KILLED       D3 an empty reason is accepted  [test_plant_d3_an_empty_reason_is_caught]
ok  KILLED       D5 a never action that a kind needs is accepted  [test_plant_d5_a_never_action_that_another_kind_needs_is_caug]
ok  KILLED       D6 a long-lived credential with no exception is accepted  [test_plant_d6_a_long_lived_credential_with_no_exception_is_c]
ok  KILLED       D7 an unknown key is accepted  [test_plant_d7_unknown_keys_platform_and_never_type_are_refus]
ok  KILLED       E2 copy-ready text is offered for a kind with an unchecked grant  [test_plant_no_copy_ready_text_for_a_kind_with_an_unverified_]
ok  KILLED       E5 a value that does not match its grammar is put into the text  [test_an_empty_vault_prefix_is_refused_and_the_page_says_so_f]
```

The mutant script has no mutant for the Vault engine tests (its own header says so). `git status` of the worktree was clean after the mutant run.

## 4. Fail-before on clean origin/main

Tree: `git archive origin/main` into a temp folder, then ONLY these five branch files copied over it: `tests/policy_mutants.py`, `tests/test_policy_engine.py`, `tests/test_policy_guard.py`, `tests/fixtures/policy_sources_2026-11-11.txt`, `tools/policy_page.py`. The three `src` files and `docs/` are origin/main's.

Command: `python -m pytest tests/test_policy_guard.py -v -p no:cacheprovider --tb=short` with `PYTHONPATH=<temp tree>/src`. Exit code 1. `65 failed, 17 passed in 2.15s` (82 tests).

Per-test table with the first assertion line: `fail-before-main.txt`. A marker column, set by a text match in code:

- 52 failures: the first assertion line names missing data (`no POLICY in ...`, or `docs/least-privilege-policies.md is missing`).
- 13 failures: the failure text also contains `no POLICY`, but the first line is shortened by pytest or compares a reported list with an expected one. These are: `test_every_kind_is_declared_pending_or_holds_no_identity` (`assert ['kind secret... dated entry'] == []`), the three `test_the_calls_written_in_the_module_equal_the_declared_list[...]`, `test_plant_a_new_request_with_no_grant_is_caught`, `test_plant_a_grant_whose_request_was_deleted_is_caught`, `test_plant_a_request_that_is_not_a_literal_is_caught`, `test_plant_a_path_built_by_a_call_is_not_foldable_and_is_caught` (`assert (2 == 1)`), `test_plant_a_sink_taken_as_a_value_is_caught`, `test_plant_a_raw_http_request_outside_the_one_sender_is_caught`, `test_plant_a_stale_allowlist_line_is_caught` (`assert (3 == 6)`), `test_a_request_named_only_in_a_docstring_changes_nothing`, `test_plant_a_new_kubernetes_operation_is_caught`.
- 0 failures with no such text.
- 17 passed on main (named in the table): among them the kind-list plants, `test_the_extracted_requests_are_the_ones_the_ticket_lists`, the five banned-indirect-call plants, `test_template_folds_only_names_and_attributes`, the three "not a pure literal" plants and `test_each_grammar_is_the_settings_own_pattern`.

In this run no test failed on main for a reason other than the missing POLICY literals or the missing page, by that text match.

## 5. Plants (temp copies of the branch tree, outside the repository)

Full verbatim record: `plants.txt` (each plant: the exact edit, the guard test file's exit code, failed tests and assertion lines, the output of the guard's own functions called directly, and `tools/policy_page.py --check`). Each plant ran on a fresh copy made with `git archive 7af1380`; the copy's own `src` was imported (the record prints the import path each time). Raw pytest logs: `/home/user/build/evidence-raw/Q8c1-7af1380/plant-P*.log`.

| Plant | Guard tests (82) | What the guard's own function reported (first line) | `--check` exit |
|---|---|---|---|
| P00 control, nothing changed | 82 passed, exit 0 | 0 problems | 0 |
| P01 Vault secrets: new undeclared request (POST to the data path) | 7 failed, exit 1 | `secrets_vault.py:115: request ('POST', '{mount}/data/{path_prefix}{name}') has no grant and no free entry in POLICY` | 0 |
| P02 Vault secrets: the declared request's call deleted | 7 failed | `POLICY declares request ('GET', '{mount}/data/{path_prefix}{name}') but the module makes no such call` | 0 |
| P03 Vault secrets: request path made a variable | 7 failed | `secrets_vault.py:116: call to .authed whose request is not a literal, outside the allowlisted lines: it cannot be compared with the declared list` (and the P02 line) | 0 |
| P04 Vault secrets: sink called through getattr with a variable name | 7 failed | `secrets_vault.py:116: banned getattr with a name that is not a literal` (and the P02 line) | 0 |
| P04b (extra) added request through getattr with a LITERAL name | **82 passed, exit 0** | **0 problems** | 0 |
| P05 Vault secrets: DELETE added on the path declared for read | 7 failed | `secrets_vault.py:116: request ('DELETE', '{mount}/data/{path_prefix}{name}') has no grant and no free entry in POLICY` | 0 |
| P06 Transit: call to `keys/<name>/rotate` added | 5 failed | `signer_vault.py:52: request ('POST', '{mount}/keys/{key_name}/rotate') has no grant and no free entry in POLICY` | 0 |
| P07 Transit: call to `export/...` added | 5 failed | `signer_vault.py:52: request ('GET', '{mount}/export/signing-key/{key_name}') has no grant and no free entry in POLICY` | 0 |
| P08 Kubernetes: operation not in READ_OPERATIONS (`k8s.list_secrets`) | 4 failed | `kubernetes.py:247: request ('k8s.list_secrets',) has no grant and no free entry in POLICY` | 0 |
| P09a Kubernetes: `?watch=true` request under the declared id `k8s.list_events` | **82 passed, exit 0** | **0 problems** | 0 |
| P09b Kubernetes: a grant with verb `watch` added (R23) | 3 failed: `test_each_kubernetes_grant_is_the_verb_and_resource_of_its_path`, `test_pr1_grants_are_all_verified_with_no_unverified_claim`, `test_the_committed_page_equals_what_the_data_gives` | the five direct functions: 0 problems (the report comes from the three tests) | 1 |
| P09c Kubernetes: verb of R21 changed from `list` to `watch` | 2 failed: `test_each_kubernetes_grant_is_the_verb_and_resource_of_its_path`, `test_the_committed_page_equals_what_the_data_gives` | the five direct functions: 0 problems | 1 |
| P10a fourth kind module with no POLICY added to the tool's `KIND_MODULES` | 45 failed | see `plants.txt`; `--check` prints `policy page: no POLICY in src/hadavin_sdk/actions/secrets_env.py` | 1 |
| P10b new kind added to the backends table, on no list | 3 failed | `kind secrets/new_cloud has no POLICY and is on no list: declare it or add a dated entry` | 0 |
| P11 `verified` of R17 set to a URL | 57 failed | `secrets/vault: grant R17: verified source 'https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2' is not a source id (a URL or host is never written here)` | 1 |
| P12 `verified` of R17 set to None, no pending entry | 6 failed | `secrets/vault R17: the name is not found in a vendor source (verified is None) and has no PENDING_NAMES entry` | 1 |
| P13a R17 unverified with a pending entry dated yesterday (2026-11-10) | 6 failed | `PENDING_NAMES ('secrets/vault', 'R17') is overdue (review_by 2026-11-10): plant` | 1 |
| P13b the seven existing "PR 2" pending-kind entries dated yesterday | 4 failed | seven lines `PENDING_KINDS <kind> is overdue (review_by 2026-11-10): Q8c PR 2` | 0 |
| P14 docs page changed by one character | 1 failed: `test_the_committed_page_equals_what_the_data_gives` | 0 problems | 1, prints `policy page: docs/least-privilege-policies.md differs from the data; run --write and commit` |

Notes on how I read two brief items (so the reader can check my reading):
- "add a `watch` verb" in the Kubernetes module: I planted three forms (P09a a request, P09b a new grant, P09c a changed grant).
- "add a fourth kind module with no POLICY to the table": I planted both tables (P10a the tool's table, P10b the backends table).
- "set a pending entry's date to yesterday": the branch's `PENDING_NAMES` is empty, so P13a adds one entry together with an unverified grant; P13b changes the existing pending-kinds entries.

## 6. Renderer probes

Full verbatim record: `renderer-probes.txt` (136 cases: the values given, then the exception text or the rendered text, then a check made by code).

- 22 cases rendered text, 114 raised `ValueError`. No other exception type occurred.
- Page mode (`values=None`), 3 cases: rendered; placeholders stay as written.
- Plain values, 4 cases: rendered.
- Hostile values, one field at a time, for all 8 fields (`mount`, `path_prefix`, `transit_mount`, `key_name`, `namespaces`, `ROLE_NAME`, `SERVICE_ACCOUNT`, `SERVICE_ACCOUNT_NAMESPACE`): `*`, `?`, `{x}`, empty string, `../`, a newline inside, a newline at the end, a double quote, a single quote, `"} path "sys/*" {capabilities=["sudo"]`: every one raised `ValueError` ("does not match its grammar", or for the empty prefix "is empty: an empty prefix means the whole mount, and no policy text is produced for that").
- A 300-character value of allowed characters: RENDERED for `mount`, `transit_mount`, `key_name`, `namespaces`, `ROLE_NAME`, `SERVICE_ACCOUNT`, `SERVICE_ACCOUNT_NAMESPACE`, and for a 300-character valid `path_prefix` (299 letters and a slash). The plain 300-letter `path_prefix` with no slash raised.
- Namespace lists `shop,,payments`, `shop,`, `,shop`, `shop, payments`, `shop,*`: raised. `kube-system`, `shop,kube-system`, `shop,shop` (the same name twice: two Roles and two RoleBindings with the same name and namespace): RENDERED. `SERVICE_ACCOUNT_NAMESPACE = kube-system`, `ROLE_NAME = cluster-admin`, `SERVICE_ACCOUNT = default`: RENDERED.
- Prefix `hadavin/*` (already ends with `*`), `hadavin/*/`, `*`, `+/`, `hadavin/acme` (no trailing slash), `/`, `/hadavin/`, `hadavin/../`, `./`, `hadavin//`: raised.
- Mount `secret*`, `secret/../sys`, `+`, `secret/`: raised. Mount `sys`: RENDERED as `path "sys/data/hadavin/acme/*"` with `["read"]`.
- Key name `audit*`, `audit/config`, `.`, `..`: raised.
- Missing key, unused key, `None`, a list, bytes: raised. A renderer given the other platform's policy: raised.

Check by code on every rendered text (does it hold any path or rule other than the declared ones?):
- Vault, 9 rendered texts: the `path` blocks found equal the blocks expected from the POLICY literal in all 9; lines outside the expected blocks: none in all 9.
- Kubernetes, 13 rendered texts: parsed as YAML; kinds other than Role and RoleBinding: none; every Role's rules equal the three declared rules in all 13; 3 rules per Role; unexpected top-level keys: none.

## 7. Source hashes (`tests/fixtures/policy_sources_2026-11-11.txt`)

Each stated file was fetched with curl as plain data at the stated commit (the `github.com/.../blob/<commit>/...` rows through the raw form of the same address) and hashed; nothing was executed and nothing about this project was sent. Fetched on 2026-11-11 at about 15:21 UTC. Per row: `source-hashes.txt`.

| Id | Result |
|---|---|
| V-POL, V-TOK, V-KV, V-TR, V-API, V-APPROLE, V-K8S (commit 82e7167) | MATCH, all 7 |
| B-POL, B-KV, B-TR, B-API (commit 0d706a0) | MATCH, all 4 |
| K-SSRR, K-KUBELET (commit 18f8e9f) | MATCH, both |
| K-RBAC, K-AUTHZ (branch `main`, and commit 18f8e9f) | MATCH at the branch address and MATCH at the commit, both rows |
| K-SRC (branch `master`, and commit dd21ea9) | MATCH at the branch address and MATCH at the commit |

16 rows, 19 fetches: 19 match, 0 mismatch, 0 not reachable. No host was refused by the network.

## 8. gitleaks

| Command | Exit code | Output |
|---|---|---|
| `/home/user/build/bin/gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..7af13809" /home/user/build/EV-Q8c1-7af1380` | 0 | `1 commits scanned.` `no leaks found` |
| `/home/user/build/bin/gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8c-1/7af1380` | 0 | `no leaks found`; run a second time after this row was written: exit code 0, `no leaks found` |

## 9. Set-up and clean-up

- Worktrees: `/home/user/build/EV-Q8c1-7af1380` (branch head, detached) and `/home/user/build/EV-Q8c1-main` (origin/main, detached). Virtual environment `/home/user/build/venv-evq8c1` (`uv sync --all-extras --group test`, exit code 0).
- Postgres: my own 16 cluster, `initdb -E UTF8 --locale=C.UTF-8`, trust authentication, port 56180 on 127.0.0.1, socket folder `/tmp`, started and stopped by me as the `postgres` user.
- Heavy slot waits: full suite 270 s, mutants 200 s, rerun on main about 60 s, rerun on the branch 0 s.
- No commit, no push, no sub-agent, no download of any program, no paid call.
- Raw files kept: `/home/user/build/evidence-raw/Q8c1-7af1380/`.

## Files in this folder

`RESULTS.md`, `engine-tests.txt`, `full-suite-failures-and-skips.txt`, `gates-output.txt`, `mutant-rows.txt`, `fail-before-main.txt`, `plants.txt`, `renderer-probes.txt`, `source-hashes.txt`.

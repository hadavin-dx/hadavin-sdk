<!-- full hand-back report of sub-agent a1693872, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW Q8c-1, round 1, design critic, read-only. Head 7af13809, snapshot /home/user/build/snap/q8c1-7af1380/. Nothing was run by me.

## Read this first: evidence state

- `/home/user/hadavin-sdk/handover/evidence/Q8c-1/7af1380/RESULTS.md` is NOT present. The folder appeared during my review and holds three raw files only: `plants.txt`, `source-hashes.txt`, `fail-before-main.txt`. I read all of `source-hashes.txt`, the first 80 lines of `fail-before-main.txt`, and `plants.txt` lines 1-591 plus a header/result grep of the rest.
- What those files do show: the 82 tests of `tests/test_policy_guard.py` pass on the branch tree and `policy_page.py --check` exits 0 (plants.txt P00); all 17 fixture hashes match on re-fetch, including the three branch rows at their stated commits (source-hashes.txt); on main with only the tool and tests overlaid, 65 tests fail for lack of data and 17 pass (fail-before-main.txt).
- What has no output anywhere: the 11 Vault server tests in `tests/test_policy_engine.py`, the full suite, `ruff`, `bandit`, `tests/test_no_hardcoded_values.py`, `tools/scan_repo.py`, `python tests/policy_mutants.py`, any CI run. Every "passes" for those is unproven.

## Findings, failures first

### Major 1. The Vault refusal tests have no recorded run, yet the page and CHANGELOG state the refusal as fact
- Where: `docs/least-privilege-policies.md:14-15, :58, :102`; `CHANGELOG.md:219-220`; `tools/policy_page.py:61-79, :662-664`.
- Scenario: the 11 server tests (5 secrets, 6 transit) skip on any machine without `HADAVIN_TEST_VAULT_ADDR`. If the fixture `transit_key()` or the `auth/token/create` answer differs from what the test expects, CI goes red after merge of a page that already says "are also refused by a real Vault server".
- My reading of the test logic found no defect (statuses, ordering with delete last, error-message regexes all match the kind code), but that is a reading, not a run.
- Fix: one CI run at this head with `-rs` output saved by the evidence runner, showing the 11 tests as passed and not skipped, before any verdict of clean.

### Major 2. R17 grants more than any call the code can make
- Where: `src/hadavin_sdk/actions/secrets_vault.py:228` (`{mount}/data/{path_prefix}*`), against `:34` and `:108-115` (the name is one path segment, no `/`).
- Scenario: `path_prefix: "hadavin/acme/"`. The code can read only `secret/data/hadavin/acme/<one name>`. The rendered policy also admits `secret/data/hadavin/acme/other-team/db/password` and everything deeper. The single-segment limit is enforced only by the client-side `_NAME` check; remove that check and the policy does not stop the wider read.
- Fix: `{mount}/data/{path_prefix}+` (Vault's one-segment wildcard). This is from my own knowledge, not a fetched source; the evidence runner must find the `+` rule in V-POL and B-POL before it is marked verified. Add a server refusal test "read two levels below the prefix", and let data rule D1 and the renderer treat `+` like `*`.
- Note: the ticket's row R17 specified the `*` form, so this is a ticket-level over-breadth the builder followed.

### Major 3. Two false negatives of the guard's central rule, both shown by the independent plants
- (a) Literal `getattr`. `tests/test_policy_guard.py:322-329` bans `getattr` only with a non-literal name. Plant P04b adds `getattr(self, "authed")("LIST", f"{self.mount}/metadata/{self.path_prefix}")` inside `_fetch`: 82 passed, 0 problems. Fix: refuse `getattr` whose literal name is a sink or a banned name (the existing `getattr(exc, "too_large", False)` at kubernetes.py:180 stays legal); add the plant.
- (b) Kubernetes verb changed by the query string. The guard reads only the operation id (`test_policy_guard.py:374, :392, :419-420`), and the run-time binding checks only the path, not the query (`/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/tools.py:567`). Plant P09a adds `self._get(f".../events?watch=true", "k8s.list_events")`: 82 passed. That request needs the verb `watch`, which the Role lacks, so a client cluster answers 403 at run time while every test is green; the start-up probe does not report `watch` either. It fails towards less privilege, but the declared set no longer equals the calls.
- Fix for (b): fold the path argument of literal Kubernetes calls, require it to fit the id's pattern in `READ_OPERATIONS`, and refuse a query the wrapper did not build (or have `fetch` refuse `watch` on a list binding, which is a behaviour change and a separate ticket).

### Minor 4. Other guard bypasses, not caught, by class
- Another module imports the client: `from hadavin_sdk.actions.secrets_vault import connect` then `connect(s).authed("LIST", ...)`. Today only `audit/signer_vault.py:21` imports it (checked by search on main). The page states this bound (`docs/...:19`). Cheap fix: a test that only modules in `KIND_MODULES` import `actions.secrets_vault`.
- A subclass of `VaultProvider` in another module: same class, same fix.
- `_template` folds `{self.mount}` and a bare local `{mount}` to the same text (`test_policy_guard.py:243-246`), so a path built from local variables named like settings equals the declared template. Fix: keep `self.` in the folded form.
- `self._opener.open("https://...")` with a URL string in any function: `open` is not in `RAW_HTTP` (`:219`).
- A new HTTP library import (`httpx`, `socket`) in a kind module is not seen. Fix: an import allowlist per kind module.
- Stored bound method and string concatenation: both fail closed (plants exist). The six allowlisted lines (secrets_vault 101, 104; signer_vault 40; kubernetes 168, 184, 203) are each a true pass-through; I checked them against the code.

### Minor 5. For Vault, the guard binds the `operations` label, not the rendered `resource` and capability
- Where: `test_policy_guard.py:431-443`; `tools/policy_page.py:190-192`.
- Scenario: R19 `resource` changed to `{transit_mount}/keys/*` with a `bound` sentence. A1, D1, D2 stay green; no server test reads another key. Only the literal pin at `test_policy_guard.py:1089-1097` and the page diff fail, and both are edited by the same author in the same change.
- Kubernetes has the derivation (`:690-695`); Vault has none. Fix: derive capability from the verb (GET read, POST update) and require `resource` to equal the operation template with the settings-name map and a final `{name}` replaced by the wildcard. Also refuse two grants claiming the same operation.

### Minor 6. Never-list gaps and one contradiction
- Vault secrets (`secrets_vault.py:252-284`): missing `{mount}/delete/*`, `{mount}/undelete/*`, `{mount}/subkeys/*`, and the capability `patch` on the data path. The evidence file verified `delete/*` and `patch` (LIVE-VERIFICATION.md:231, :235).
- Transit (`signer_vault.py:149-187`): missing `{transit_mount}/restore/*` (replaces the signing key), `keys/{key_name}/rotate`, `keys/{key_name}/trim`; all three verified in LIVE-VERIFICATION.md:253, :255, :258.
- Kubernetes: the never-list says verb `create` without exception (`kubernetes.py:453-457`), while the free entry says a hardened cluster "must grant `create` on `selfsubjectrulesreviews`" (`:426-429`), and every default identity already holds it. Fix: word the entry "create, other than on the self-review resources".
- Every existing never entry is something the code really never does (checked against the three modules).

### Minor 7. Coverage of requests against the code (item 1 of the brief)
- Vault secrets: GET data (R17), POST login (free). No token renewal, lookup, health or version call exists. A 403 signs in again through the same login. Covered.
- Transit: POST sign (R18, exact path, so the `/hash_algorithm` suffix is not admitted), GET keys (R19, exposes key settings and public keys, no private material). The start-up probe uses only these two. Covered. `key_version` in the body is not limited by the policy; `allowed_parameters` could pin it (not verified by me).
- Kubernetes: list deployments, list events, get pods/log, one rules review per namespace. No `pods` list (the pod name comes from the caller), no `replicasets`, no `watch`. Covered.
- Latent gap: a future request that needs a grant inside the shared client (`_login_with`, `authed`) would be declared only under `secrets/vault`; a process running only `vault_transit` would not get it in its text.

### Minor 8. Renderer
- `tools/policy_page.py:478` and `:521` write `reason` into an HCL or YAML comment unescaped; `_grant_problems` allows a newline in `reason`. A reason holding `\npath "sys/*" {...}` renders a second policy block. Needs a hostile commit to the literal, so low; fix by refusing control characters in every text field.
- Values mode is used only by tests (no command renders with values), so the grammar protects no operator. An operator hand-replaces `{path_prefix}`; with the default empty setting the result is `secret/data/*`. The "Read first" line warns; unedited page-mode text matches nothing in Vault and is invalid in Kubernetes, which fails safe.
- No value passing the grammars can add a wildcard: `*`, `+`, `$`, `{`, space, newline, `.`/`..` segments are all refused; text is written through `json.dumps`. A mount value such as `sys` is accepted, but it is the operator's own setting and the code calls the same path.

### Minor 9. Refusal-test design
- Control (`tests/test_policy_engine.py:159-166`): "admin gets anything but 403" also passes on a 404 from a mistyped path, and the runtime token gets 403 for any path at all. Fix: require 200 or 204 from the admin.
- A token with only the rendered policy does not represent production sign-in: AppRole and Kubernetes roles add `default` unless `token_no_default_policy` is set, and identity-group policies can add more. The note says the first; nothing says the second. The role field name is supported by V-TOKF in the evidence file, but V-TOKF is not in the fixture and the note carries no source id.
- Not shown by these tests: OpenBao, namespaces, nested mounts, depth below the prefix, LIST on metadata, completeness of the never-list.

### Minor 10. Honesty of claims
- Page title and file name say "Least-privilege policies" (`docs/least-privilege-policies.md:1`); errata E8 bans "smallest", and Major 2 shows the set is not minimal. README calls it "Declared permissions"; use that.
- `kubernetes.py:366-372` prints on the operator page "From the builder's memory, not checked ... No ticket removes this yet". Rule D6 wants the ticket that removes the exception. Fix: have it checked, or cut the sentence and open a ledger row.
- Vault credential text (`secrets_vault.py:205-216`) does not name the AppRole secret id in an environment variable, which is the long-lived credential for that sign-in.
- Three Kubernetes role names are `verified: None` (`kubernetes.py:433-451`) with no dated entry; the one rule covers grants only, so they can stay "not yet checked" for ever. Fix: put them in `PENDING_NAMES` or verify them from K-SRC.
- Fixture rows K-RBAC, K-AUTHZ, K-SRC point at moving branches (`policy_sources_2026-11-11.txt:21, :22, :25`), and all three Kubernetes grants rest on them. The independent re-fetch matched the hashes at commits 18f8e9f and dd21ea9, so pin the URLs to those commits. Commit ids are 7 characters; use the full ids. No test compares a hash with anything and no text is saved.
- `COVERAGE` (`policy_page.py:61-92`) is hand-written prose about what the server tests refuse; nothing ties it to the tests.
- Module comments say the guard "fails when it differs from the calls written above" (`secrets_vault.py:199`); the true claim is narrower (listed call shapes).

### Minor 11. Pending list
- Visible enough: last section of the page, README line 43, CHANGELOG. Total is consistent: 32 kinds = 3 declared + 16 pending + 13 no-identity (counted from `backends/table.py` and `sources/kinds.py`).
- It cannot go overdue silently (plants P13b: 7 problems). It can be silenced by moving a date forward without limit, or by moving a kind to `NO_IDENTITY` with one sentence. Fix: cap `review_by` at a fixed distance from `decided`.
- On 2026-12-12 the main branch goes red for every pull request until PR 2 lands or the dates move.

### Minor 12. Scope and lock-in
- `python tests/policy_mutants.py` is not a CI step (`ci.yml:94-95` runs only the stage mutants); ticket section 7 names "one mutant step". The 14 mutants match exact source lines and will go stale unnoticed. No mutants for D2, D4, the raw-HTTP and banned rules, or the Kubernetes equalities.
- Leftovers of PR 2 in the guard: `_make_api_call`, `get_waiter`, `.meta.client` bans and their plants (`test_policy_guard.py:218, :565-566`). Harmless.
- Builder additions I judge acceptable: `POLICY` at the end of each module (keeps the allowlisted line numbers stable), the raw-HTTP and sink-as-value rules, `_items` as a sink, never type `resource`, `notes`, `note`, `capabilities`.
- Lock-in: no tie of the core. `src/` gains data only, the tool is standard library in `tools/`, both modules were already vendor adapters. The engine evidence exists only for the BSL-licensed Vault image; OpenBao names were found in its own sources but it was never run, and question L3 is still open. Under the no-single-dependency rule this needs a ledger row with a trigger or an OpenBao service in CI.

## Errata checklist
- E1 done. Three kinds, 16 pending, nothing of PR 2 except the leftover bans.
- E2 done for grants; partly for never entries (three undated unverified names).
- E3 partly. Ids resolve and no URL is in `src/` (plant P11). Hashes were computed by the builder, since the evidence file holds none (disclosed in the fixture header); three rows unpinned. The two required runs of `test_no_hardcoded_values.py` have no output.
- E4 done. `id` unique (rule and plant), `no_wire` refused, `rides_on` absent. "Say so" is in a report I do not have.
- E5 done in code. The pasted literal `resource` strings are in a report I do not have.
- E6 done. Tuple allowlist, stale case, `_template`, Kubernetes equalities, never-list comparison, Transit sign-in note.
- E7 done in code, unproven in execution (Major 1). Both CI jobs carry the variable and a test checks it.
- E8 done in CHANGELOG, README and page body; partly for the page title and module comments.
- E9 partly. F1 and F2 fail for lack of data as labelled (fail-before-main.txt). Plants exist for most rules; none for "one Vault path, one grant", the Kubernetes verb derivation or the never-list equality inside the test file (the independent P09c does show the derivation firing).
- E10 partly. Decision taken (the tool is mutated through `extra_dirs`), mutants not run by anyone on record, not in CI, real-clock report not seen.

## Verdict
NOT CLEAN: 0 Blockers, 3 Majors (unproven Vault server tests; R17 wider than the code; two proven guard false negatives), 9 Minors.

## Not checked
- No test, tool or network call was run by me. Vault's `+` rule, `allowed_parameters` and identity-group policies are from my knowledge, not from a fetched source.
- `tests/test_lockin_guard.py` (`TODAY`, `Pending`), `tests/contracts/kinds/*` (`vault_target`, `transit_key`), `tools/mutation_runner.py`, `tests/test_no_hardcoded_values.py`, `tools/scan_repo.py` and `pyproject.toml` are outside the supplied set and were not read; whether the scanners accept the fixture's hashes and vendor names, and whether line 93 of `signer_vault.py` (about 170 characters) passes lint, is unknown.
- `plants.txt` lines 592-1136 were read only as headers and result lines.
- Whether identities exist outside the two kind tables (tool modules with their own `READ_OPERATIONS` under the same ServiceAccount token, telemetry exporters) and so escape the pending list.
- The builder's report, the ledger and `handover/` status files were not supplied and not read.
- DIFF.patch was read for the CI, CHANGELOG and README hunks and searched for removed lines (none); the other hunks were read as the head files.

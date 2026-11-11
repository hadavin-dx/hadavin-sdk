<!-- full hand-back report of sub-agent ae5f9e8d, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW, round 1 (design critic) - ticket /home/user/hadavin-sdk/handover/tickets/Q8c-least-privilege-policy-per-kind.md

Verdict: not ready to build. 3 Blockers, 12 Majors, 9 Minors. The per-kind call lists are complete for all 19 kinds; the problems are in the never-lists, the guard rules, the enforcer wiring and the rendering.

READ FIRST: what I could not check as asked
- /home/user/build/q8a2-dryrun/main-2a8c2aa/tests holds only `__init__.py` and `test_lockin_guard.py`. There is no `tests/contracts/` and no `.github/` in that checkout.
- I read the contract fakes, kind fixtures and ci.yml from /home/user/build/EV-P89-db0d9eb instead. The ticket says the 22 kind source files there equal main; it says nothing about tests, and I did not prove the tests equal origin/main. Every "T/" citation below carries that caveat.
- No vendor documentation was consulted (read-only, no network). Every statement about how AWS, Azure, Google Cloud or Vault behave is from memory and marked UNVERIFIED.
- Nothing was run.

Abbreviations: S/ = /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/ ; T/ = /home/user/build/EV-P89-db0d9eb/tests/ ; LG = /home/user/build/q8a2-dryrun/main-2a8c2aa/tests/test_lockin_guard.py

---------------------------------------------------------------
BLOCKERS

B1. K6 never-list forbids a call the code makes (ticket section 6, K6, line 138)
- Evidence: S/app.py:151-160 builds the purge store in the same process from the same settings (`model_copy`, so `iam_auth` carries over). S/store/postgres.py:158-161 refuses a DSN with a password when `iam_auth` is on. S/store/postgres.py:138-145 then calls the token helper with `parts["user"]`, which is the purge user. S/app.py:86-89 makes the purge DSN mandatory in pilot and prod.
- Scenario: a client with `iam_auth: true` in pilot applies the page, which says `rds-db:connect` "for any other database user (the purge user ... above all)" must never be granted. The purge sign-in is refused every tick, and redaction maps (plaintext originals, app.py:87-88) are kept for ever.
- Change:
  - K6 gets two grant rows today: runtime database user and purge database user, both held by the one process identity.
  - Add a section 11 note that separating them needs audit F2 (a code change).
  - The never entry becomes "any database user other than the two named".
  - The migration user (S/cli.py:335) is a third, operator-run identity and gets its own row.

B2. The AWS explicit Deny block is unspecified and contradicts itself across kinds (section 3.1 `never`, section 7 line 248, section 8 line 257)
- `never` is `(name, why)` with no resource, and section 7 renders it as "one explicit Deny statement". Section 8 also asserts the rendered block holds no `"Resource": "*"`. A Deny with no resource can only be `*`, or needs a resource the type does not carry.
- Conflicts across kinds:
  - K2 NEVER lists `kms:Decrypt`; K1 G02 grants `kms:Decrypt`.
  - K5 NEVER lists `bedrock:InvokeModel`; K4 G09 grants it.
- Scenario: identity split is out of scope (section 10), so one task role gets several kinds' blocks. A client using `llm: bedrock` plus `detector: bedrock_guardrail` loses every model call. A client using Secrets Manager with its own key plus `aws_kms` loses every secret read. An explicit Deny wins over any Allow.
- Change:
  - Make `never` structured: (name, resource template, why, kind of entry: action / role / path / prose, wire operation or None).
  - Scope every rendered Deny to that kind's own resource (Decrypt denied on the signing key only), or drop Deny rendering and list the never entries as text.
  - Add a guard rule: across all kinds of one platform, no never entry may cover an action plus resource that another kind grants.
  - G4 currently checks "both granted and never" only within one kind.

B3. Code-to-policy binding (G6, G7) is not achievable as written for 8 of 19 kinds (section 3.3)
Each case below either fails on main's own unchanged code or passes vacuously.
- G6, K5: the method list comes from "each `boto3.client("<service>")` literal". S/guard/bedrock_guardrail.py:28-29 calls `boto3.client(service, ...)` with a variable; the literals sit at :63 and :66 as arguments to `_client(...)`. No literal means no method list, so a new `control.delete_guardrail(...)` passes.
- G6, K3: `get_paginator` is allowlisted as "sends nothing". The operation is the string argument at S/audit/anchor_s3.py:73, and `.paginate()` sends it. G6 scans method calls only, so `get_paginator("list_object_versions")` needs no grant.
- G6, Google kinds: the list is "public methods of the client classes the module imports".
  - S/audit/anchor_gcs.py:17 imports the module `storage`, not a class.
  - The calls run on `Bucket` and `Blob` objects (`reload` :71, `upload_from_string` :43, `download_as_bytes` :47 and :53), which are never imported.
  - Three of K12's four calls are invisible; a new `blob.delete()` passes.
  - Same shape at S/audit/signer_gcp.py:19, S/actions/secrets_gcp.py:17, S/audit/signer_azure.py:16 (`azure_keys.KeyClient` by attribute).
  - On Azure, `ContainerClient.get_blob_client(...)` would need allowlisting, and everything on the returned client (delete, set or delete immutability policy) escapes.
- G6/G7, K13: anthropic (`messages.create`, S/llm/anthropic.py:122) is in neither the G6 list (AWS, Azure, Google) nor the G7 list. No binding exists, although the allowlist mentions `with_options`.
- G7, K14 and K15: the path argument is not foldable.
  - S/llm/gemini.py:88 passes the name `url`.
  - S/llm/openai_compat.py:120 passes `self.url`; the path is built at :88, outside any `post_json` call.
- G7, K19: the pod-log request goes through `self._call(path, "k8s.pod_log", ...)` at S/sources/kubernetes.py:285 with `path` a variable (:281-284). The ticket names only `_get`/`_items` as the request functions.
- G7, K17 and K18: the request functions are called with plain variables inside the client itself (S/actions/secrets_vault.py:101, :104; S/audit/signer_vault.py:40 folds to `{}/{}`). The rule fails on main unless unfoldable arguments are exempted, and that exemption is the hole: `p = f"keys/{n}/rotate"; self._call("POST", p)`.
- G7 matches "path or method-name argument", not the HTTP verb. `authed("DELETE", f"{self.mount}/data/{self.path_prefix}{name}")` folds to the same path as the read at secrets_vault.py:115 and passes. In Vault that is the difference between `read` and `delete`.
- "Matched by" is undefined. Under prefix or substring matching, `keys/{}` covers `keys/{}/rotate`.
- Change: replace G5, G6 and G7 with one rule per module: the extracted set of (verb, operation) must EQUAL the declared set. Per kind:
  - AWS: require a literal service name in every `boto3.client` call (K5 needs the variable handled); treat the string argument of `get_paginator` as a call; ban `get_waiter`, `generate_presigned_url`/`_post`, `_make_api_call`, `boto3.resource`, `.meta.client`.
  - Any attribute REFERENCE (not only a call) whose name is an API method counts.
  - `getattr` with a non-constant name on a client is refused in kind modules.
  - Unfoldable arguments fail closed, with a named per-line allowlist for the passthroughs (secrets_vault.py:101, :104; signer_vault.py:40).
  - Kubernetes: bind on the constant `operation` argument and require the policy's operations to equal `READ_OPERATIONS` (S/sources/kubernetes.py:27-32).
  - Azure and Google: name the classes per module in the test (Bucket, Blob, ContainerClient, StorageStreamDownloader, and so on), not "what the module imports".
  - State plainly that the enforcer (N1) is the real backstop and covers only paths the tests exercise.

---------------------------------------------------------------
MAJORS

M1. The S3 anchor has no enforcer choke point, and the moto claim is false (section 2 row 3, section 3.4 table)
- The ticket says the repo "already chose not to use moto".
- T/contracts/kinds/audit_neutral.py:16 and :78-88 build the `s3_object_lock` contract fixture on `moto.mock_aws`. pyproject.toml:52 (EV-P89) pins `moto[s3,kms,secretsmanager]==5.2.5`.
- K3 is the kind with G05-G08, N5 (outside `anchors/`) and N7 (identity split), and the AWS row of the 3.4 table names no hook for it.
- Change: specify one `enforce(client, enforcer)` that registers `before-call.<service>.*` on any boto3 client (moto-backed, Stubber-backed, or stub_client). Re-do the rung-4 verdict for moto's IAM enforcement, since moto is already a dependency for three of the six AWS services.

M2. Other choke points are misnamed or missing (section 3.4 table, section 4 Files)
- Slack, Gemini, OpenAI-compatible: there is no "fake behind `post_json`". They are real loopback HTTP servers in `tests/fixtures/`, which section 4 does not list: T/fixtures/fake_slack.py:8-37 (used at T/contracts/kinds/channel_slack.py:12) and `Replay` in T/fixtures/http_fake.py (used at T/contracts/kinds/llm_wire.py:17, :26).
- Kubernetes: T/contracts/sources.py holds no fake fetch (`ks(fetch, ...)` at :141-150 takes one). The fake is `FakeApi` at T/contracts/test_sources.py:55-73, plus several ad-hoc lambdas (:238, :251, :277).
- K5 start-up: `get_guardrail` has no contract fake. T/contracts/kinds/detectors.py:89-92 builds `GuardrailDetector` directly; `GuardrailClient` (:55-86) is a wrapper with one method, not a boto3 client. The `get_guardrail` tests live in T/test_p5p6_followups.py:172-239 on Stubber. G10's N2 needs a new start-up path.
- Vault: the contract fixtures use ONE admin-token client for both setup and the kind under test.
  - T/contracts/kinds/secrets_neutral.py:49-66 seeds through `provider.call(..., token=token)`.
  - T/contracts/kinds/audit_neutral.py:43-57 mounts transit and creates the key with the same client it hands to the signer.
  - Running the suite with a policy-only token means splitting every fixture into admin and runtime clients, and rendering a policy per test (random `path_prefix` at secrets_neutral.py:55, random key name at audit_neutral.py:48).
- What does hold: `stub_client.respond` receives `model.name` (T/contracts/aws_stub.py:40-45), `FakeAdapter.send` exists (T/contracts/http_fake.py:24), and `kms_stub` is hand-written (T/contracts/kinds/audit_chain.py:29-74).
- Change: rewrite the 3.4 table against these files, add `tests/fixtures/*` to section 4, and correct "fixture change, no new suite".

M3. Four grants have no wire operation of their own, so N2 and N3 cannot hold for them (section 3.4)
- G12 (`rds-db:connect`): the token is signed locally (S/store/auth_aws.py:19). The only test monkeypatches a class (T/test_p3b_neutral_audit.py:267-273), and nothing reaches a fake.
- G02 (`kms:Decrypt`): done by Secrets Manager on the server side.
- G06 (`s3:PutObjectRetention`): the same PutObject request as G05.
- G18: the same Put Blob request as G17.
- `allow` is "any grant lists the operation". Removing G06 or G18 still passes through G05 or G17, so N3 ("one grant removed, one test fails") is false for them. N2 ("every grant's operation is in seen") is false for G12 and G02.
- Change: add a field such as `rides_on` (the grant that carries the request) or `no_wire=True` with a reason. The enforcer requires ALL grants bound to an operation when its trigger is present (lock headers, immutability header). N2/N3 exempt `no_wire` grants by name, and the page says these are proven only on a live account.

M4. `condition: str` is prose, so G2 is vacuous and the IAM block cannot be rendered (sections 3.1, 3.3 G2, 7)
- G2 accepts `Resource: "*"` with `condition="see docs"`.
- G05's "condition" is "recorded bound: fixed name prefix".
- G03 needs two `StringEquals` keys. G06 needs one `StringEquals` and one numeric operator. G02 needs a region-templated value.
- Section 7 promises "one Allow statement per grant with its condition".
- Change: `conditions: tuple[(operator, key, value-template), ...]` plus a separate `bound: str` for prose. G2 requires a structured condition or a non-wildcard prefix. `?` is regulated like `*` (G01 uses `-??????` on purpose, so allow it only in a declared suffix).

M5. The verifier identity cannot start with only its "V" grants (K2, K8, K11, K18 tags; N7)
- Every signer factory signs a probe at build: S/audit/signer_aws.py:55 with S/audit/signer.py:79-90, and the same in signer_azure.py:63, signer_gcp.py:61, signer_vault.py:81.
- `verify()` is only reached from the CLI (S/cli.py:352, S/audit/chain.py:342-353).
- An `audit verify` identity therefore needs `kms:Sign` (G03, tagged S, R), not just G04.
- The Azure and Google anchors also probe at build (S/audit/anchor_azure.py:85, S/audit/anchor_gcs.py:71).
- Change: define the verifier as `start_up + verify`. Record in section 11 that the auditor identity can sign today, which is a least-privilege finding needing a code change (skip the sign probe in verify mode). Have N7 test the real pair. I did not read how cli.py builds the audit object for `audit verify`.

M6. G5 is a substring search and passes stale grants (section 3.3 G5)
- "A method call of that name or inside a string constant" is satisfied by unrelated text.
- `sign` appears in `"signer aws_kms"` (S/audit/signer_aws.py:55).
- `chat.update` appears in the module docstring (S/approvals/slack_channel.py:1).
- Deleting the real call leaves G03 or G34 green.
- Change: fold into the set-equality rule of B3 and exclude docstrings (helper exists at LG:542-549).

M7. Never-lists are untyped, so G4, N4 and the renderer cannot act on them (section 6)
- Entries mix real action names, role names ("role `Key Vault Secrets Officer`"), paths, and prose ("any verb on `secrets`", "an unrestricted API key", "`{transit_mount}/sign/*` for another key").
- N4 runs "for each entry that names a wire operation", but no field says which.
- The count of "169 unverified names" includes non-names.
- Change: the structured `never` of B2. G4 then checks typed entries only, and N4's coverage is stated as a number per kind.

M8. S3 anchor rows are likely too narrow in two cases and risky in one (K3) - UNVERIFIED, from memory
- Missing rows for a bucket with default SSE-KMS encryption: `kms:GenerateDataKey` for the put (S/audit/anchor_s3.py:55) and `kms:Decrypt` for the gets (:67, :78). K1 has the equivalent row (G02); K3 does not.
- G06 condition "remaining retention days at least `{retain_days}`": the code sends exactly `clock() + retain` (anchor_s3.py:60). By the time S3 evaluates, the remainder is fractionally under `retain_days`, and a whole-day comparison could refuse every put. Use `retain_days - 1`, or drop the condition until the live check.
- Change: add the two conditional rows with `when` prose, and fix the boundary.

M9. Name-prefix conditions probably break the list calls on Google Cloud and Azure (K12 G27, K9 G20) - UNVERIFIED, from memory
- A Google IAM condition on the object name does not match `storage.objects.list`, which is evaluated against the bucket. The verifier's `list_blobs` (S/audit/anchor_gcs.py:52) would be refused. `storage.buckets.get` (G24) has the same issue if the condition is on the same binding.
- Azure role-assignment conditions use a different attribute for List Blobs than for blob read or write, so "same" in G20 is not safe.
- Change: separate bindings. List and bucket-get are unconditioned or conditioned on the list prefix attribute; create and get are conditioned on the name prefix. Note that Google conditions need uniform bucket-level access.

M10. Vault negative tests are unsound unless the default policy is excluded (N4 on the real server; K17/K18 never `sys/*`) - UNVERIFIED, from memory
- A token made with `auth/token/create` also gets Vault's `default` policy unless `no_default_policy` is set. That policy allows several `sys/` and `auth/token/` self paths.
- "A token holding only that policy" is therefore not what the test creates. Depending on the path probed, N4 either fails or the page claims a refusal that the real identity does not have.
- Change: create the test token with `no_default_policy: true`. The page tells operators to set `token_no_default_policy` on the AppRole or Kubernetes role, or lists what `default` adds.

M11. Rendering trusts settings that have no grammar (section 8 hostile inputs)
- The renderer refuses only `*` and `{`. In IAM, `?` is also a wildcard.
- Unconstrained `str` fields: `bucket` and `region` (S/backends/table.py:163-164), `key_id` and `region` (:229-230), `region` (:146), `guardrail_id` (:102).
- A `key_id` or `guardrail_id` that is already an ARN or alias produces a malformed or wrong ARN (the ticket notes the alias case for K2 only).
- Change: per `.claude/rules/class-level-fixes.md`, use an allowlist grammar per field at the renderer choke point (bucket name grammar, region grammar, key id as UUID / ARN / alias with ARN pass-through). Do not use a deny list.

M12. The G9 library choice leaves nothing behind when it fails (section 2 row 2, section 11) - licences and maintenance UNVERIFIED, from memory
- Licences as I recall them: `parliament` BSD-3-Clause, `policy_sentry` MIT, `moto` Apache-2.0, `iamlive` MIT. None is copyleft. All are test-group only, so there is no distribution risk to the proprietary package (pyproject.toml:7), provided the test group never ships.
- Risks:
  - `parliament` has had little maintenance. A stale bundled list rejects valid newer names (Ed25519 KMS condition values, `bedrock:ApplyGuardrail`, newer Bedrock actions), which pressures the builder to drop G9.
  - `policy_sentry` brings a sizeable transitive tree into CI.
  - The fallback is "G9 is dropped", meaning no check at all. That is a single dependency with no second source.
- Change: make the fallback a second source, not nothing. Vendor a dated snapshot of the action lists for the six AWS services used (from AWS's published service authorization reference), with fetch date and source recorded. The library, if it passes R450, is the cross-check.
- Not a new single dependency: `iamlive` and `moto` are not adopted by the ticket.

---------------------------------------------------------------
MINORS

m1. Ticket line 243 is false for two entries. S/sources/kubernetes.py does not refuse verb `watch` (`_READ_VERBS` at :39 includes it; it is only consulted for secrets at :123) nor "any ClusterRoleBinding". Reword it. G8 through `rules_problems` would pass a policy granting `watch`, so also assert that the rendered rules equal what `READ_OPERATIONS` implies.

m2. `backends/policy.py` is declared neutral but must dispatch on platform names. The literal `"slack"` matches `PATTERNS["bare vendor name"]` (LG:520-521) and fails `test_core_logic_names_no_vendor`. Rename the platform ids (for example `slack_scopes`), or keep each renderer beside its vendor. Do not add the module to `VENDOR_MODULES`.

m3. Fail-on-main proofs F2-F4 would fail with `ModuleNotFoundError` for `hadavin_sdk.backends.policy` or `tests.contracts.policy_enforcer`, not with the expected messages. By the ticket's own standard that is a failure for the wrong reason. State which new files are overlaid on main for that run.

m4. API-key rows (G29-G32) and the Slack bot token are long-lived credentials. `credential` is free text and G4 only requires it non-empty. Add a structured lifetime and require a written exception line for anything long-lived (rule item 2). Also say what `action` holds for `platform="api_key"`.

m5. K17 with the default `path_prefix=""` (S/backends/table.py:285) renders `{mount}/data/*`, the whole mount. "The page must warn" is weaker than the rule. Have `for_config` refuse or flag an empty prefix in pilot and prod, or render one path per configured secret name.

m6. G11 `{key_version}` "the key part of" needs a derivation, not a template fill. Specify the helper or use `<KEY>`.

m7. Token-endpoint and metadata requests made by `DefaultAzureCredential`, Google default credentials and the AWS credential chain are not declared as free calls. The fakes bypass them (T/contracts/http_fake.py:43-47; `AnonymousCredentials` at :84), so nothing forces this. List them on the page.

m8. Single-dependency note: the strongest negative evidence (N4 on a real server) runs only on `hashicorp/vault:2.2.0` (T/../.github/workflows/ci.yml:54, BSL). The kind modules say OpenBao has not been run by the studio. Add an OpenBao service run, or record a trigger.

m9. The estimate of four 60-minute boxes does not fit, given M2 (every Vault fixture split, a new start-up fake for K5, the moto hook) and B3.

---------------------------------------------------------------
ANSWERS TO THE TICKET'S OPEN QUESTIONS (section 11, items 1-4)
1. Reference plus literal in the kind module: agree. Rule c skips vendor modules (LG:601). The four kind modules outside `VENDOR_MODULES` (secrets_vault, signer_vault, openai_compat, sources.kubernetes) hold no pattern-matching words in their rows as drafted.
2. Target level: keep it, but only after its grammar is defined (one string cannot express bucket plus key prefix). Otherwise remove the N5 claims from the page.
3. Split: yes. AWS, Vault, Slack and Kubernetes first. Azure and Google Cloud carry all three L rows, M9, and the weakest G6.
4. MinIO in CI: worth it only if the UNVERIFIED condition support is checked first. It does not replace M1.

---------------------------------------------------------------
WHAT I VERIFIED
Kind modules opened, with every call site and line number in section 6 compared against the code - all 19:
- K1 secrets_aws, K2 signer_aws, K3 anchor_s3, K4 bedrock, K5 bedrock_guardrail, K6 auth_aws + postgres.py:100-175
- K7 secrets_azure, K8 signer_azure, K9 anchor_azure
- K10 secrets_gcp, K11 signer_gcp, K12 anchor_gcs
- K13 anthropic, K14 gemini, K15 openai_compat (+ llm/common.py `post_json`)
- K16 slack_channel, K17 secrets_vault, K18 signer_vault, K19 sources/kubernetes + sources/kinds.py

Results:
- No SDK or HTTP call in any of the 19 modules is missing from the ticket's tables, and no listed call is absent from the code. All cited line numbers are correct.
- G1's selection yields exactly 19 kinds (18 TABLE entries plus kubernetes).
- G3 field names all exist on the settings models, except the derivation in m6.
- N7's "list is verify-only" holds (`anchor.all()` only at S/audit/chain.py:353).

Also read: S/backends/table.py and factory.py in full, S/audit/signer.py, S/audit/anchors.py, LG in full, the three rule files, CLAUDE.md, and the test files cited above.

WHAT I DID NOT CHECK
- Any permission name, condition key, role content or ARN format against a vendor page: all 209 items stay unverified. M8, M9, M10 and the licences in M12 are from memory.
- Whether the tests in EV-P89-db0d9eb equal origin/main 2a8c2aac.
- Not read: `tests/fixtures/http_fake.py` (`Replay`); `test_p4_secrets.py`; `tests/contracts/conftest.py`; `test_anchor.py`, `test_signer.py`, `test_secrets.py`, `test_llm.py`, `test_capabilities.py`; T/contracts/test_sources.py outside lines 225-284 (`FakeApi` located by search only); `docs/slack-app-manifest.yaml` beyond the scopes lines; ci.yml beyond the Vault lines.
- Not read: `store/migrate.py`, `store/migrations/*`, the `ToolContext.fetch` binding in `tools.py`, `approvals/slack.py` and `receiver.py`, `config.py`, and cli.py beyond the two search hits. The claim that Slack sends nothing beyond `chat.postMessage` and `chat.update` rests on a search for `post_json(` in the package, which found a single caller (slack_channel.py:51).
- SDK-internal requests (Azure `CryptographyClient` key fetch, upload chunking, retries) were not traced in the SDK sources.
- Whether moto's IAM enforcement or botocore event hooks behave as M1 assumes.
- Section 9 gates and the egm process steps.

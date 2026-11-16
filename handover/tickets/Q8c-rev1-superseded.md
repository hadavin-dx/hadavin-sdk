> SUPERSEDED 2026-11-11 by revision 2 (`Q8c-least-privilege-policy-per-kind.md`) after plan review round 1 (reviews/Q8c/plan-r1-zoomout.md, plan-r1-design.md; decision D-010). Kept for the record only: do NOT build from this text. Statements in it that the reviewers found false are listed in revision 2, section 0.

# Ticket Q8c (rev 1, draft, NOT yet reviewed): every cloud kind ships its minimum permission policy, a reason per permission, and a negative test
Source: reviews/Q8/deps-audit.md F3; rule `.claude/rules/least-privilege-hard-rule.md` item 5 (bible R365); code read at origin/main 2a8c2aac (the 22 kind files were compared byte for byte with `/home/user/build/EV-P89-db0d9eb/src`, all the same, 2026-11-11). Branch: NEW `core/q8c-policy-per-kind` from origin/main; draft PR against main; never merged by the builder. Path class: security (least privilege): result-review rounds uncapped. Depends on: nothing merged first; Q8a-1 touches only app.py, config.py and CHANGELOG (CHANGELOG is the one shared file). This ticket is longer than 250 lines because section 6 is the per-kind policy table for 19 kinds, which the builder copies from.

Words used here, one meaning each. A "kind" is one backend choice in `backends/table.py` (for example `aws_kms`). A "policy" is the declared smallest set of permissions one kind needs. A "grant" is one permission in that set. The "never-list" is the permissions that identity must not be given. An "operation" is one request the kind's code sends, as a test fake sees it.

## 0. What is not known (read first)
- **Every permission name in section 6 is UNVERIFIED-NEEDS-LIVE-CHECK.** The author had no network documentation access and checked none against a live vendor page today. Counts: 40 grant rows and 19 never-lists holding 169 entries, so 209 unverified items (counted by script, end of section 6). Each row carries the author's confidence (H, M, L); L rows are listed again in section 11. The builder or lead checks each name against the vendor's own page, writes the page and the date beside it, and corrects the table BEFORE the build starts.
- No test was run and no code was written for this ticket.
- A fake that enforces our own declared policy proves two things only: the code makes no request the policy lacks, and the policy holds no permission the tests never use. It does NOT prove that the real cloud accepts these names or that they are enough. That proof needs a real account (section 9, owner step).
- Not read: `store/postgres.py` beyond lines 100-125, `backends/factory.py` beyond `hosts`, `audit/chain.py` beyond lines 320-360, the contract fakes beyond their first lines and function lists.

## 1. Problem in plain words
The core can sign in to AWS, Azure, Google Cloud, Vault, Slack and Kubernetes. For none of these does the repository say which exact permissions the code needs. An operator who sets up a client's cloud has to guess, and a guess usually ends as a broad built-in role. The studio's rule says every kind ships three things: the policy text, one reason per permission, and a test showing the identity is refused what it must not do. Today all three are missing for all 19 kinds (the one partial exception: Slack's scope is in `docs/slack-app-manifest.yaml` and tested at tests/test_p7_tick.py:536).

## 2. Rung table (CODE-LAST v1; scale of 2026-11-06: 1 no-code tools, 2 our own core modules, 3 existing free tools, 4 free libraries, 5 our own new code)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| the policy text per kind | the exact permissions each kind's code needs, in the repository, before any cloud exists | 3: AWS IAM Access Analyzer policy generation (builds a policy from recorded account activity); Google Cloud role recommendations; no Azure tool known for data-level permissions | UNVERIFIED (author's memory, no live page 2026-11-11). They need a real account with weeks of real traffic, cover one cloud each (AWS: 6 of 19 kinds), and cannot fail a pull request | the list exists on day one, for all six platforms, and is tied to our code | KEEP, as DATA (a literal in each kind module, no logic). Access Analyzer becomes the cross-check at the first live run (section 9) |
| are the AWS permission names real | catch a misspelt or invented name without a cloud account | 4: an offline AWS permission database: `parliament` or `policy_sentry` (open source, bundle the AWS permission list); botocore's own data (installed) lists API operations, not permission names | UNVERIFIED: licence, last release date and whether both still ship current data must be checked live by the builder (R450) | nothing | CUT-TO-CONFIG+GLUE: one test-group dependency and about 15 test lines (guard G9). If the live check fails: no dependency; the lead's dated check against the AWS page stands instead and G9 is dropped |
| refusing a request in tests with no cloud | a new API call with no grant must fail a test | 4: `moto` has an option that enforces IAM policies (AWS only; UNVERIFIED whether it covers Ed25519 signing, Object Lock headers and Converse; the repo already chose not to use moto, tests/contracts/aws_stub.py:1-2). 3: a real Vault server already runs in CI (.github/workflows/ci.yml:50-61). 2: our fakes already sit on every request (tests/contracts/aws_stub.py `respond`, http_fake.py `FakeAdapter`, vault_fake.py) | files read 2026-11-11 | one check for all six platforms at choke points that exist | Vault kinds: CUT-TO-CONFIG+GLUE (apply the generated policy to the real CI Vault server). Others: KEEP-CODE, test code only, one wrapper (about 120 lines) |
| binding the code's calls to the policy | a policy line no code uses, or a call no line covers, fails CI | 3: `iamlive` (records the AWS calls a program sends and writes a policy; AWS only, needs real requests). 2: tests/test_lockin_guard.py already has the syntax-tree helpers (`_fold`, `module_name`, `_source_docstring` :215-221) and sources/kubernetes.py:27-32 already binds operation ids to method and path | UNVERIFIED for iamlive; files read 2026-11-11 | the only thing that knows which calls OUR modules make | KEEP-CODE (guard test, reuses those helpers) |
| the page operators copy | one page per release with every kind's policy | 2: generated from the same data; Slack's manifest file already exists | docs/slack-app-manifest.yaml read 2026-11-11 | stays equal to the code because a test regenerates and compares | KEEP thin glue. SCOPE CUT: copy-ready native text only where we can test the format offline (AWS IAM JSON, Vault policy, Kubernetes Role). Azure, Google Cloud and API keys are shown as a table of permissions; no native file is generated for them |
| proof on a real cloud | the real service accepts the policy and refuses the never-list | 3: AWS policy simulator and Access Analyzer validation, `kubectl auth can-i`, Google policy troubleshooter | UNVERIFIED; all need accounts, some cost money | nothing | NOT BUILT HERE: owner step at the first live run (section 9) |
Why a static declared policy is still needed although cloud tools exist: every cloud tool above works after the fact, on one cloud, on a real account. Rule item 5 asks for the policy to ship WITH the change. Honest limit of what we build: it keeps code and declared policy equal; it cannot tell whether the declaration is right for the real service.

## 3. Design
### 3.1 Types (in `backends/table.py`; plain dataclasses, no vendor word, no new import)
```python
@dataclass(frozen=True)
class Grant:
    action: str                 # the platform's own permission name, exact; never holds '*'
    resource: str               # template: {field} is this kind's setting, <NAME> is filled in by the operator
    reason: str                 # one plain sentence: which behaviour of the kind needs it
    calls: tuple[str, ...]      # how the call is written in the kind module (3.3)
    operations: tuple[str, ...] # the same call as a test fake sees it (3.4)
    used_by: tuple[str, ...]    # any of "start_up", "runtime", "verify"
    when: tuple[str, Any] | None = None  # (setting, value): the grant applies only then
    condition: str = ""         # the recorded bound; required when `resource` holds '*'
    target: str = ""            # what the request may name, as the fake sees it; "" = any (operation level only)

@dataclass(frozen=True)
class FreeCall:                 # a request that needs no permission (a sign-in, a self-check)
    calls: tuple[str, ...]; operations: tuple[str, ...]; reason: str

@dataclass(frozen=True)
class Policy:
    platform: str               # "aws_iam" | "azure_rbac" | "gcp_iam" | "vault" | "slack" | "kubernetes_rbac" | "api_key"
    grants: tuple[Grant, ...]
    never: tuple[tuple[str, str], ...]   # (permission name, why it must not be granted)
    credential: str             # how the identity signs in and how long the credential lives
    free: tuple[FreeCall, ...] = ()
```
`Entry` gains `policy: str | None = None`, a `"module:NAME"` reference in the same style as `factory`. `sources/kinds.py` `SourceKind` gains the same field (the Kubernetes source is not in TABLE).
### 3.2 Where the policy data lives (a deviation from the audit's wording, stated)
The audit says "a `policy` field on Entry holding" the data. Proposed instead: the field holds a REFERENCE; the data is a module-level literal `POLICY = {...}` (plain dict, list, tuple and string literals only) in the kind module that makes the calls. Reasons: (1) tests/test_lockin_guard.py rule c refuses vendor words in neutral modules (`PATTERNS` "bare vendor name" matches a string starting `kms:` or `s3:`, "ARN" matches `arn:aws`); kind modules are where vendor words are allowed; (2) a pull request that adds an API call and its grant touches one file. Alternative for the reviewers: write the data inline in TABLE (the guard skips TABLE nodes, test_lockin_guard.py `_skipped_table_nodes`); cost: about 250 more lines in table.py. The author recommends the reference.
New neutral module `backends/policy.py` (standard library only): `load(reference) -> Policy` reads the module's SOURCE FILE and evaluates only the `POLICY` literal with `ast.literal_eval` (no import, so no optional extra is needed and no code runs; precedent `_source_docstring`); `for_config(entries) -> list[tuple[str, str, Policy]]` (twin of `factory.hosts`) keeps the grants whose `when` matches the settings and fills `{field}`; `render(...)` (section 7). The postgres kind's reference points at `store/auth_aws.py` (the only AWS call of the store).
### 3.3 Guard test (new `tests/test_policy_guard.py`; each rule has a plant test in the repo's `test_plant_*` style)
- G1 needs a policy: every TABLE kind with `hosts is not None` or `extra in {"aws", "azure", "gcp", "anthropic"}`, every `sources.kinds.KINDS` entry, and `store/postgres` (named explicitly: its AWS path is a setting). Read with `getattr(entry, "policy", None)` so that on main it fails with the list of 19 kind names, not with an AttributeError.
- G2 no wildcard: `*` or `?` never in `action`; `*` in `resource` only with a non-empty `condition`.
- G3 fields are real: every `{field}` in `resource` and `target`, and every `when` field, exists on the kind's settings model.
- G4 nothing empty: `reason`, `credential`, each never-list reason; the never-list has at least one entry; no name is both granted and on the never-list.
- G5 policy to code: every `calls` entry is found in the policy's module, either as a method call of that name or inside a string constant (folded with `_fold`). A grant no code uses fails.
- G6 code to policy, SDK kinds: every method call in the module whose name is an API method of the SDK client it builds must be in some grant's or free call's `calls`. AWS: the method list comes from botocore's own service data for each `boto3.client("<service>")` literal (offline, no credentials; precedent aws_stub.py REGION), plus `generate_db_auth_token`. Azure and Google: the public methods of the client classes the module imports (needs the extras: skipped on a default install, and CI must fail if it was skipped). A short allowlist names methods that send nothing (`blob`, `bucket`, `with_options`, `get_paginator`), each with a reason; a stale allowlist entry fails.
- G7 code to policy, plain-HTTP kinds (vault, vault_transit, slack, gemini, openai_compat, kubernetes): every call to the module's one request function (named in the test per module: `_call`, `authed`/`call`, `post_json`, `_get`/`_items`) must have its folded path or method-name argument matched by a `calls` entry.
- G8 cross-checks with code that exists: the Slack policy's scopes equal the bot scopes in docs/slack-app-manifest.yaml; the Kubernetes policy, rendered as RBAC rules, makes `sources.kubernetes.rules_problems` return an empty list (the policy passes the code's own read-only check).
- G9 (only if the rung-4 library passes its live check) every `aws_iam` action exists in the offline permission database.
- G10 the committed page equals `render` output (section 7).
### 3.4 Negative tests with no cloud: a fake that enforces the declared policy
New `tests/contracts/policy_enforcer.py`: `Enforcer(policy, settings, used_by)` with `allow(operation, target) -> bool` (deny by default; allow only when a grant or free call lists the operation, its `when` matches, its `used_by` is included and `target` matches) and `seen` (the operations asked). `operations` grammar: AWS `"<service>:<ApiOperationName>"` exactly as aws_stub.py's `respond` receives `model.name`; every other platform `"METHOD path-regex"` in the READ_OPERATIONS style, matched against the request path. It is wired in at the choke points that already exist, not per test:
| platform | choke point (exists) | what a refusal looks like (the platform's own shape, so the kind's real error handling runs) |
|---|---|---|
| AWS | tests/contracts/aws_stub.py `stub_client` (new optional `enforce=`); the hand-written `kms_stub` (contracts/kinds/audit_chain.py:29), `GuardrailClient` (contracts/kinds/detectors.py:55) and `BedrockWire` (contracts/kinds/llm_wire.py:144) move onto `stub_client` or take the same hook | `ClientError`, code `AccessDeniedException` (`AccessDenied` for S3), HTTP 403 |
| Azure, Google Cloud | tests/contracts/http_fake.py `FakeAdapter.send` | HTTP 403 with the service's error body; the SDK raises its own error |
| Vault | CI: the REAL server. The test renders the policy (section 7), writes it with the root token, creates a token holding only that policy, and runs the kind's contract suite with it. Laptop: vault_fake.py takes the same hook | HTTP 403 |
| Slack, Gemini, OpenAI-compatible | the fake behind `llm.common.post_json` that each kind's contract fixture already uses | Slack: `{"ok": false, "error": "missing_scope"}`; others HTTP 403 |
| Kubernetes | the fake `fetch` in tests/contracts/sources.py | HTTP 403 Status |
Each kind's existing contract suite runs through the enforcer (fixture change in tests/contracts/kinds/*, no new suite). Then:
- N1 a call without a grant fails: the kind's contract tests pass only if every request was allowed.
- N2 no unused grant: after the kind's suite plus one start-up and one verify run, every grant's operation is in `seen`.
- N3 one grant removed, one test fails: a parametrised test removes each grant in turn and expects the kind's smoke path to be refused with the platform's refusal (one case per grant, in-process, no mutation run needed).
- N4 the never-list is refused: for each never-list entry that names a wire operation, a raw client behind the enforcer is refused (AWS examples: `PutSecretValue`, `ScheduleKeyDeletion`, `DeleteObject`). On Vault in CI this runs against the real server: write to the secret path, read another prefix, rotate and export the Transit key are each answered 403.
- N5 wrong target refused (kinds whose target comes from settings): signing with another key, writing an anchor outside `anchors/`, reading a Vault path outside `path_prefix`, a Kubernetes namespace not configured.
- N6 a refusal message never holds the secret value, the token or the request body.
- N7 identity split: with `used_by=("runtime",)` the anchor's list call is refused; with `used_by=("verify",)` the anchor's write is refused.

## 4. Files
Create: `src/hadavin_sdk/backends/policy.py`; `tests/test_policy_guard.py`; `tests/contracts/policy_enforcer.py`; `tests/contracts/test_policy.py` (N1-N7); `docs/least-privilege-policies.md` (generated). Change: `backends/table.py` (three dataclasses, `Entry.policy`, 18 references; its docstring line "imports no other Hadavin module" stays true); `sources/kinds.py` (field + reference); one `POLICY` literal in each of the 19 modules of section 6; `tests/contracts/aws_stub.py`, `http_fake.py`, `vault_fake.py`, `contracts/kinds/*.py` (the `enforce` hook); `tests/test_lockin_guard.py` only if `backends/policy.py` needs listing; CHANGELOG; README link. Delete: none. No production behaviour changes: no kind sends a different request after this ticket.

## 5. Reuse checked
tests/test_lockin_guard.py (`_fold`, `module_name`, `_source_docstring`, plant-test style); tests/contracts/aws_stub.py, http_fake.py, vault_fake.py; sources/kubernetes.py `READ_OPERATIONS`, `rules_problems`, `_WRITE_VERBS`, `_SHELL_RESOURCES`; `backends/factory.hosts` (the model for `for_config`); docs/slack-app-manifest.yaml. Not found in the repository: any existing policy text, IaC, or permission list besides the Slack manifest and three mentions (`rds-db:connect` store/auth_aws.py:4, `bedrock:GetGuardrail` guard/bedrock_guardrail.py:9 and CHANGELOG.md:213, `chat:write`).

## 6. Per-kind policy table (derived from the code; ALL names UNVERIFIED-NEEDS-LIVE-CHECK; conf = author's confidence)
Line numbers are in `src/hadavin_sdk/`. `<NAME>` is filled in by the operator; `{field}` is the kind's setting. "S" = start-up, "R" = runtime, "V" = audit verify.

**K1 secrets / aws_secrets_manager** (AWS; actions/secrets_aws.py; client built :42)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G01 | `get_secret_value(SecretId=name)` :29 (R) | `secretsmanager:GetSecretValue` | `arn:aws:secretsmanager:{region}:<ACCOUNT_ID>:secret:<SECRET_NAME>-??????` one line per secret the config names (the six characters are the suffix AWS adds) | reads one named secret when a caller asks | H |
| G02 | same call, only when the secret uses the client's own encryption key | `kms:Decrypt` | that key's ARN; condition `kms:ViaService` = the Secrets Manager service of `{region}` | Secrets Manager decrypts with that key on the caller's behalf | M |
NEVER K1: `secretsmanager:PutSecretValue`; `secretsmanager:UpdateSecret`; `secretsmanager:CreateSecret`; `secretsmanager:DeleteSecret`; `secretsmanager:RestoreSecret`; `secretsmanager:PutResourcePolicy`; `secretsmanager:ListSecrets`; `secretsmanager:DescribeSecret`; `secretsmanager:BatchGetSecretValue`; `secretsmanager:RotateSecret`

**K2 signer / aws_kms** (AWS; audit/signer_aws.py; client built :54; both calls also run once at start-up through `audit/signer.py` `probe` :79-90)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G03 | `sign(KeyId, Message, MessageType="RAW", SigningAlgorithm="ED25519_SHA_512")` :32-37 (S, R) | `kms:Sign` | `arn:aws:kms:{region}:<ACCOUNT_ID>:key/<KEY_ID>`; conditions `kms:SigningAlgorithm` = `ED25519_SHA_512`, `kms:MessageType` = `RAW` | signs each audit checkpoint | H (conditions M) |
| G04 | `get_public_key(KeyId)` :41 (S, V; once per process) | `kms:GetPublicKey` | same key | checks the key type and verifies signatures locally | H |
NEVER K2: `kms:ScheduleKeyDeletion`; `kms:DisableKey`; `kms:PutKeyPolicy`; `kms:CreateGrant`; `kms:UpdateKeyDescription`; `kms:UpdateAlias`; `kms:DeleteAlias`; `kms:ImportKeyMaterial`; `kms:DeleteImportedKeyMaterial`; `kms:Decrypt`; `kms:Encrypt`; `kms:Verify`; `kms:TagResource`
Note: an IAM policy must name the key ARN; if `key_id` is an alias the operator still writes the key ARN. The key's own key policy must let IAM policies apply.

**K3 anchor / s3_object_lock** (AWS S3, MinIO, Ceph; audit/anchor_s3.py; client built :89; object names start `anchors/`, audit/anchors.py:9)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G05 | `put_object(..., ObjectLockMode, ObjectLockRetainUntilDate, IfNoneMatch="*")` :55-63 (R) | `s3:PutObject` | `arn:aws:s3:::{bucket}/anchors/*` (recorded bound: fixed name prefix) | writes one new anchor object, never over an existing one | H |
| G06 | same call (it sets the lock in the same request) | `s3:PutObjectRetention` | same; conditions `s3:object-lock-mode` = `{mode}` and `s3:object-lock-remaining-retention-days` at least `{retain_days}` | S3 asks for this permission when a put carries lock headers | M (conditions L) |
| G07 | `get_object(Bucket, Key)` :67 (R, only after a refused double write) and :78 (V) | `s3:GetObject` | `arn:aws:s3:::{bucket}/anchors/*` | compares an anchor that already exists; reads anchors when verifying | H |
| G08 | `get_paginator("list_objects_v2").paginate(Bucket, Prefix)` :73-75 (V only) | `s3:ListBucket` | `arn:aws:s3:::{bucket}`; condition `s3:prefix` like `anchors/*` | lists the anchors when verifying | H |
NEVER K3: `s3:DeleteObject`; `s3:DeleteObjectVersion`; `s3:BypassGovernanceRetention`; `s3:PutObjectLegalHold`; `s3:PutBucketObjectLockConfiguration`; `s3:PutLifecycleConfiguration`; `s3:PutBucketPolicy`; `s3:PutBucketVersioning`; `s3:PutObjectAcl`; `s3:PutBucketAcl`; `s3:DeleteBucket`
Two identities: the writer (runtime) gets G05-G07; the verifier gets G07-G08 only. `s3:BypassGovernanceRetention` is the permission that lets a caller shorten or remove a GOVERNANCE lock, so it is first on the never-list. On MinIO and Ceph the same names are used in their own policy files (UNVERIFIED which of the conditions they support).

**K4 llm / bedrock** (AWS; llm/bedrock.py; client built :43-55)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G09 | `converse(**request)` :156 (R) | `bedrock:InvokeModel` | one line per route: `arn:aws:bedrock:{region}::foundation-model/<MODEL_ID>`, or `arn:aws:bedrock:{region}:<ACCOUNT_ID>:inference-profile/<PROFILE_ID>` plus the foundation-model ARN in each region that profile sends to | Converse is authorised by the invoke permission | H (profile resources M) |
NEVER K4: `bedrock:InvokeModelWithResponseStream`; `bedrock:CreateModelInvocationJob`; `bedrock:PutModelInvocationLoggingConfiguration`; `bedrock:DeleteModelInvocationLoggingConfiguration`; `bedrock:CreateProvisionedModelThroughput`; `bedrock:CreateModelCustomizationJob`; `bedrock:PutFoundationModelEntitlement`; `aws-marketplace:Subscribe`
Note: model ids come from the routes, not from this kind's settings, so the page shows `<MODEL_ID>` per route.

**K5 detector / bedrock_guardrail** (AWS; guard/bedrock_guardrail.py; clients built :28-40, two services)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G10 | `get_guardrail(guardrailIdentifier, guardrailVersion)` :47 (S) | `bedrock:GetGuardrail` | `arn:aws:bedrock:{region}:<ACCOUNT_ID>:guardrail/{guardrail_id}` | start-up refuses a guardrail whose prompt-attack filter is off | H (ARN M) |
| G11 | `apply_guardrail(..., source="INPUT", content)` :101-106 (R) | `bedrock:ApplyGuardrail` | same | screens one text | H |
NEVER K5: `bedrock:UpdateGuardrail`; `bedrock:DeleteGuardrail`; `bedrock:CreateGuardrail`; `bedrock:CreateGuardrailVersion`; `bedrock:ListGuardrails`; `bedrock:InvokeModel`

**K6 store / postgres with `iam_auth: true`** (AWS RDS; store/auth_aws.py; client built :16; called from store/postgres.py:122)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G12 | `generate_db_auth_token(DBHostname, Port, DBUsername)` :19 (R). It sends nothing: the token is signed locally and the database checks it at sign-in | `rds-db:connect` | `arn:aws:rds-db:{region}:<ACCOUNT_ID>:dbuser:<DB_RESOURCE_ID>/<DB_USER>` | signs in to the database with no stored password | H |
NEVER K6: `rds-db:connect` for any other database user (the purge user and the migration user above all); `rds:ModifyDBInstance`; `rds:DeleteDBInstance`; `rds:ModifyDBCluster`; `rds:CreateDBSnapshot`; `rds:RestoreDBInstanceFromDBSnapshot`; `rds:DescribeDBInstances`
`when=("iam_auth", True)`. With `iam_auth: false` the kind needs no cloud permission (the password is in the DSN secret).

**K7 secrets / azure_key_vault** (Azure; actions/secrets_azure.py; client built :45-51, `DefaultAzureCredential`)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G13 | `get_secret(name)` :37 (R) | data action `Microsoft.KeyVault/vaults/secrets/getSecret/action` (smallest built-in role that holds it: Key Vault Secrets User, which also allows reading secret metadata) | scope: the single secret `.../vaults/<VAULT>/secrets/<SECRET_NAME>`, one assignment per secret | reads one named secret | H |
NEVER K7: `Microsoft.KeyVault/vaults/secrets/setSecret/action`; `Microsoft.KeyVault/vaults/secrets/delete`; `Microsoft.KeyVault/vaults/secrets/backup/action`; `Microsoft.KeyVault/vaults/secrets/purge/action`; `Microsoft.KeyVault/vaults/secrets/readMetadata/action`; `Microsoft.KeyVault/vaults/write`; `Microsoft.KeyVault/vaults/accessPolicies/write`; role `Key Vault Secrets Officer`; role `Key Vault Administrator`; role `Contributor`
Note: assumes the vault uses Azure role-based access. With the older vault access policies the equivalent is secret permission Get only.

**K8 signer / azure_key_vault_key** (Azure; audit/signer_azure.py; clients built :57-62)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G14 | `CryptographyClient.sign(es256, digest)` :38 (S, R) | data action `Microsoft.KeyVault/vaults/keys/sign/action` | scope: the single key `.../vaults/<VAULT>/keys/<KEY_NAME>` | signs each audit checkpoint | H |
| G15 | `KeyClient.get_key(name, version)` :43 (S, V); the SDK's crypto client may also read the key before its first operation | data action `Microsoft.KeyVault/vaults/keys/read` | same key | reads the public half and checks the key type | H |
NEVER K8: `Microsoft.KeyVault/vaults/keys/delete`; `Microsoft.KeyVault/vaults/keys/update/action`; `Microsoft.KeyVault/vaults/keys/rotate/action`; `Microsoft.KeyVault/vaults/keys/create/action`; `Microsoft.KeyVault/vaults/keys/import/action`; `Microsoft.KeyVault/vaults/keys/backup/action`; `Microsoft.KeyVault/vaults/keys/purge/action`; `Microsoft.KeyVault/vaults/keys/release/action`; `Microsoft.KeyVault/vaults/keys/decrypt/action`; `Microsoft.KeyVault/vaults/keys/unwrap/action`; role `Key Vault Crypto Officer`
Note: the built-in role Key Vault Crypto User also allows encrypt, decrypt, wrap and unwrap, so a custom role with G14 and G15 is the minimum. A Managed HSM has its own role system with its own names (not derived here; section 11).

**K9 anchor / azure_immutable_blob** (Azure; audit/anchor_azure.py; client built :72-79)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G16 | `get_container_properties()` :85 (S) | `Microsoft.Storage/storageAccounts/blobServices/containers/read` | scope: the container `{container}` | start-up refuses a container without version-level immutability | M |
| G17 | `upload_blob(name, data, overwrite=False, immutability_policy=...)` :57 (R) | data action `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/add/action` (creates, cannot replace); if the service asks for it instead: `.../blobs/write` | same container; a role-assignment condition on the blob name prefix `anchors/` | writes one new anchor blob | L |
| G18 | same call (it sets the blob's immutability policy in the same request) | data action `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/immutableStorage/runAsSuperUser/action` | same | Azure asks for this to set a retention policy on a blob version | L |
| G19 | `download_blob(name).readall()` :59 (R, after a refused double write), :65 (V) | data action `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read` | same | compares an existing anchor; reads anchors when verifying | H |
| G20 | `list_blobs(name_starts_with="anchors/")` :64 (V only) | same data action as G19 (listing blobs) | same | lists the anchors when verifying | M |
NEVER K9: `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete`; `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/deleteBlobVersion/action`; `Microsoft.Storage/storageAccounts/blobServices/containers/blobs/permanentDelete/action`; `Microsoft.Storage/storageAccounts/blobServices/containers/delete`; `Microsoft.Storage/storageAccounts/blobServices/containers/write`; `Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies/delete`; `Microsoft.Storage/storageAccounts/blobServices/containers/immutabilityPolicies/write`; `Microsoft.Storage/storageAccounts/listKeys/action`; `Microsoft.Storage/storageAccounts/regenerateKey/action`; `Microsoft.Storage/storageAccounts/blobServices/generateUserDelegationKey/action`; role `Storage Blob Data Owner`; role `Storage Account Contributor`
Unresolved (section 11): G18 may be the same permission that lets a caller shorten or delete an Unlocked policy. If so, in GOVERNANCE mode the Azure writer can undo its own lock, and only COMPLIANCE (Locked) holds against the writer.

**K10 secrets / gcp_secret_manager** (Google Cloud; actions/secrets_gcp.py; client built :50)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G21 | `access_secret_version(name="projects/{project_id}/secrets/<name>/versions/latest")` :42 (R) | `secretmanager.versions.access` (role `roles/secretmanager.secretAccessor` holds only this) | bound on the single secret `projects/{project_id}/secrets/<SECRET_NAME>`, never on the project | reads the newest version of one named secret | H |
NEVER K10: `secretmanager.versions.add`; `secretmanager.versions.destroy`; `secretmanager.versions.disable`; `secretmanager.secrets.delete`; `secretmanager.secrets.update`; `secretmanager.secrets.setIamPolicy`; `secretmanager.secrets.list`; role `roles/secretmanager.admin`

**K11 signer / gcp_kms** (Google Cloud; audit/signer_gcp.py; client built :55)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G22 | `asymmetric_sign(request={"name", "data"})` :41 (S, R) | `cloudkms.cryptoKeyVersions.useToSign` | bound on the one key (the lowest level a binding can sit): the key part of `{key_version}` | signs each audit checkpoint | H |
| G23 | `get_public_key(request={"name"})` :45 (S, V) | `cloudkms.cryptoKeyVersions.viewPublicKey` | same key | reads the public half and checks the algorithm | H |
NEVER K11: `cloudkms.cryptoKeyVersions.destroy`; `cloudkms.cryptoKeyVersions.update`; `cloudkms.cryptoKeyVersions.create`; `cloudkms.cryptoKeys.update`; `cloudkms.cryptoKeys.setIamPolicy`; `cloudkms.cryptoKeyVersions.useToDecrypt`; `cloudkms.cryptoKeyVersions.restore`; role `roles/cloudkms.admin`
Note: role `roles/cloudkms.signerVerifier` holds G22, G23 and a verify permission the code does not use; a custom role with the two is the minimum.

**K12 anchor / gcs_retention_lock** (Google Cloud; audit/anchor_gcs.py; client built :61)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G24 | `bucket.reload()` :71 (S) | `storage.buckets.get` | bucket `{bucket}` | start-up checks the retention period and, for COMPLIANCE, that it is locked | H |
| G25 | `blob.upload_from_string(..., if_generation_match=0)` :43-45 (R) | `storage.objects.create` | bucket `{bucket}`; condition: object name starts `anchors/` | writes one new anchor object | H |
| G26 | `download_as_bytes()` :47 (R, after a refused double write), :53 (V) | `storage.objects.get` | same | compares an existing anchor; reads anchors when verifying | H |
| G27 | `list_blobs(prefix="anchors/")` :52 (V only) | `storage.objects.list` | same | lists the anchors when verifying | H |
NEVER K12: `storage.objects.delete`; `storage.objects.update`; `storage.objects.setRetention`; `storage.objects.overrideUnlockedRetention`; `storage.buckets.update`; `storage.buckets.delete`; `storage.buckets.setIamPolicy`; `storage.hmacKeys.create`; role `roles/storage.objectAdmin`; role `roles/storage.admin`
Note: `storage.buckets.update` lets a caller shorten or remove an unlocked retention policy, so it leads the never-list with `storage.objects.delete`. A custom role with G24-G27 is the minimum.

**K13 llm / anthropic** (llm/anthropic.py; one request: `messages.create(**request)` :122; three platforms, chosen by `platform`)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G28 | `platform: vertex`: `AnthropicVertex(...)` :42-47, then :122. Sign-in: Google Application Default Credentials | `aiplatform.endpoints.predict` | project `{project_id}`; a narrower bound to one publisher model: not established | sends one model request through Vertex AI | M |
| G29 | `platform: api`: `Anthropic(api_key=...)` :54, then :122 | no cloud permission: an API key of ONE workspace made for this deployment, with that workspace's spend limit | workspace `<WORKSPACE>` | sends one model request | M |
| G30 | `platform: foundry`: `AnthropicFoundry(api_key=...)` :49-53, then :122 | no role: the resource's API key, which allows every data request on that resource | resource `{resource}` | sends one model request | M |
NEVER K13: `aiplatform.models.upload`; `aiplatform.endpoints.deploy`; `aiplatform.endpoints.create`; `aiplatform.tuningJobs.create`; `aiplatform.datasets.create`; role `roles/aiplatform.user`; role `roles/aiplatform.admin`; an organisation admin API key on `platform: api`; an Azure role on the Foundry resource that can list or regenerate its keys
Unresolved (section 11): the Foundry key cannot be narrowed below the whole resource.

**K14 llm / gemini** (llm/gemini.py; plain HTTP, key in the `x-goog-api-key` header)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G31 | `post_json(".../v1beta/models/<model>:generateContent", ...)` :84-90 (R) | no role: an API key restricted to the Generative Language API only | a project made for this deployment | sends one model request | M |
NEVER K14: an unrestricted API key; a key shared with another deployment; a key from a project that holds other data

**K15 llm / openai_compat** (llm/openai_compat.py; plain HTTP)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G32 | `post_json("<base_url>/chat/completions", ...)` :88, :120 (R) | no role: where the provider offers restricted keys, a key allowed chat completions only; a self-hosted server needs none | one project or one server | sends one model request | L |
NEVER K15: an organisation admin key; a key allowed to manage files, fine-tunes or other keys

**K16 channel / slack** (approvals/slack_channel.py; plain HTTP, bot token)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G33 | `chat.postMessage` :125, :167, :196 (R) | bot scope `chat:write` | the client's own internal app; the bot is invited to the one channel `{channel_id}` | posts the approval message, cards and notices | H |
| G34 | `chat.update` :185 (R) | the same scope (a bot may update only its own messages) | same | replaces the buttons with the decision | H |
NEVER K16: `chat:write.public`; `chat:write.customize`; `channels:read`; `channels:history`; `groups:history`; `users:read`; `users:read.email`; `files:write`; `admin`; any user token scope; `incoming-webhook`
Already in docs/slack-app-manifest.yaml; guard G8 keeps the two equal. Inbound clicks are checked with the signing secret and need no scope.

**K17 secrets / vault** (Vault or OpenBao; actions/secrets_vault.py)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G35 | `authed("GET", "{mount}/data/{path_prefix}<name>")` :115 (R) | capability `read` | path `{mount}/data/{path_prefix}*` (recorded bound: this deployment's prefix; an empty `path_prefix` gives the whole mount and the page must warn) | reads one named secret | H |
| free | `call("POST", "auth/<auth_mount>/login", ...)` :138 (auth approle :172-173, kubernetes :183-184); auth token sends no sign-in request | none (the sign-in path takes no token) | n/a | signs in | H |
NEVER K17: capability `create`, `update`, `patch`, `delete` or `list` on `{mount}/data/*`; any capability on `{mount}/metadata/*`; `{mount}/delete/*`; `{mount}/destroy/*`; `sys/*`; `auth/token/create`; `auth/*` beyond the sign-in; capability `sudo`; the `root` policy

**K18 signer / vault_transit** (Vault or OpenBao; audit/signer_vault.py; signs in through `secrets_vault.connect` :79)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G36 | `authed("POST", "{transit_mount}/sign/{key_name}", ...)` :52 via :40 (S, R) | capability `update` | path `{transit_mount}/sign/{key_name}` | signs each audit checkpoint | H |
| G37 | `authed("GET", "{transit_mount}/keys/{key_name}")` :62 via :40 (S, V) | capability `read` | path `{transit_mount}/keys/{key_name}` | reads the pinned version's public key and the key type | H |
| free | the sign-in request, as in K17 | none | n/a | signs in | H |
NEVER K18: capability `update`, `create` or `delete` on `{transit_mount}/keys/{key_name}`; `{transit_mount}/keys/{key_name}/rotate`; `{transit_mount}/keys/{key_name}/config`; `{transit_mount}/keys/{key_name}/trim`; `{transit_mount}/export/*`; `{transit_mount}/backup/*`; `{transit_mount}/restore/*`; `{transit_mount}/sign/*` for another key; `sys/*`; capability `sudo`

**K19 source / kubernetes** (sources/kubernetes.py; registry sources/kinds.py:39-47; one namespaced Role and RoleBinding per configured namespace, never a ClusterRole)
| id | code call | permission | resource | reason | conf |
|---|---|---|---|---|---|
| G38 | `GET /apis/apps/v1/namespaces/<ns>/deployments?limit=...` :232-234 (R) | verb `list` | `deployments`, API group `apps`, in each of `{namespaces}` | reads deployments, their rollout revision and images | H |
| G39 | `GET /api/v1/namespaces/<ns>/events?limit=...` :247 (R) | verb `list` | `events`, core API group, same namespaces | reads events in the time window | H |
| G40 | `GET /api/v1/namespaces/<ns>/pods/<pod>/log?...` :281-287 (R) | verb `get` | `pods/log`, core API group, same namespaces | reads one pod's log lines | H |
| free | `POST /apis/authorization.k8s.io/v1/selfsubjectrulesreviews` :328-337 (S) | none in a default cluster (every signed-in identity may ask what it may do); if the cluster removed that default, verb `create` on `selfsubjectrulesreviews` | cluster | start-up proves the credential is read-only | H |
NEVER K19: verbs `create`, `update`, `patch`, `delete`, `deletecollection`, `escalate`, `bind`, `impersonate`; verb `watch`; verb `*`; `pods/exec`; `pods/attach`; `pods/portforward`; `pods/proxy`; `nodes/proxy`; `services/proxy`; any verb on `secrets`; any ClusterRoleBinding
The never-list is the list the code already refuses at start-up (kubernetes.py:36-49, :100-125).

Count (script over this file, 2026-11-11: `grep -cE '^\| G[0-9]{2} '` and the `; `-separated items of the `NEVER` lines): 19 kinds; 40 grant rows (author's confidence: 29 H, 8 M, 3 L); 3 calls that need no permission; 19 never-lists holding 169 entries. None verified live. The builder will write more than 40 `Grant` literals, because a row used by two identities (G07, G19, G26) or with two resource forms (G09) becomes one literal per identity or form; those extra literals add no new permission name.

## 7. Docs output
`docs/least-privilege-policies.md`, generated by `python -m hadavin_sdk.backends.policy` and committed; guard G10 fails when it is stale. For each kind: one plain sentence saying what the kind does; the identity or identities (runtime, verifier); a table (permission, on what, why, when it is used); the never-list with reasons; how the identity signs in and how long the credential lives; then a copy-ready block for AWS (IAM policy JSON: one Allow statement per grant with its condition, one explicit Deny statement for the never-list), Vault (policy text) and Kubernetes (Role and RoleBinding). Azure, Google Cloud and API-key kinds show the table and name the nearest built-in role with what it allows beyond the minimum. Placeholders stay as `<NAME>`: no account id, region, key id or ARN of a real account is written anywhere. The page opens with the honest limit: these policies are derived from the code and are kept equal to it by tests; each was (or was not yet) confirmed on a real account on a stated date. `for_config(entries)` gives the same for one config with the settings filled in; a command-line subcommand for it is NOT in this ticket (section 10).

## 8. Tests
Must FAIL on origin/main (the builder pastes each failing run against main's `src/`, with the expected message, so a failure for a wrong reason does not count):
- F1 guard G1 lists all 19 kinds as "no policy" (exact names asserted).
- F2 N1 for each of the 19 kinds: the contract fixture cannot load a policy (message names the kind).
- F3 G10: the page does not exist.
- F4 G8: the Slack policy and the Kubernetes policy do not exist to compare.
Regression guards (pass once built; exempt from the fail-on-main proof, each proved by its own plant): plants for G2 (a `*` action; a `*` resource with no condition), G3 (an unknown `{field}`), G4 (empty reason; a name both granted and never), G5 (a grant whose call is not in the module), G6 (a kind module calling `list_secrets` with no grant; a stale allowlist entry), G7 (a new Slack method string with no grant; a new Vault path with no grant), G9 (an invented AWS action), G10 (a stale page); N2-N7 of section 3.4; the enforcer's own tests (deny by default; an unknown operation refused; `when` and `used_by` honoured; refusal shapes per platform).
Hostile inputs: a `POLICY` that is not a pure literal (a call, an f-string, an import) is refused by `load` and never executed; a `POLICY` with an unknown key or platform is refused; a settings value holding `*` or `{` cannot widen a rendered resource (the renderer refuses it); a rendered AWS block parses as JSON and holds no `"Action": "*"`, no `"Resource": "*"`.
Mutants: one per guard rule G1-G10 and one for the enforcer's default deny, each killed by a named test, added to the repository's mutant list (tests/stage_mutants.py is the Q8a precedent; the builder says which file it used).

## 9. Evidence, gates, review
Gates: `uv run --all-extras --group test pytest` with HADAVIN_TEST_PG_DSN and HADAVIN_TEST_VAULT_ADDR set (own throwaway Postgres and Vault dev server; the Vault tests must show as NOT skipped), `ruff check`, `ruff format --check`, `bandit -ll`, the guard tests. One full run at the final head through one heavy slot. Then a separate EVIDENCE RUNNER and the egm:* result reviewers (they get the diff, this ticket and the evidence). Estimate at agent speed: build about 4 hours of real clock in four 60-minute boxes (types, loader and guard; 19 policies; enforcer wiring; page and renderers), plus evidence and review rounds.
Live proof, NOT in this ticket (needs the owner: accounts, and a yes with numbers where anything costs money): at the first live run of each kind, attach the page's policy to the test identity, run the kind's contract suite, attempt each never-list operation, and record the result and date on the page; for AWS also run the policy simulator and Access Analyzer validation.

## 10. Out of scope (each with where it goes)
- Splitting one process's identities (runtime, purge, signer, channel): audit F2, its own ticket. This ticket only labels each grant with `used_by` so that split has its input.
- Step-up sign-in for approvers (F4); Vault static token (F5, ticket Q8a-1); RDS-only passwordless sign-in (F7).
- Database roles and GRANT statements: they live in the migrations (`store/migrations/0001_core.sql`, `hadavin-sdk migrate`), which this author did not read; whether they meet item 5 is NOT established here and needs its own audit line.
- Infrastructure code (Terraform or similar), permission boundaries, organisation-level deny policies, CI deploy, break-glass and human identities: client delivery work, not core.
- Any change to what a kind sends. Findings from reading the code that would need one are in section 11, not fixed here.
- A `hadavin-sdk policy` command; native Azure and Google Cloud role files.
- Network egress (the `hosts` list and the network policy prerequisite) is separate and unchanged.

## 11. Open questions and items not established
For the plan reviewers:
1. Reference plus literal in the kind module (3.2), or data inline in TABLE?
2. Is target-level enforcement (`Grant.target`, N5) worth its size in this ticket, or operation level first?
3. One pull request for all 19 kinds, or AWS, Vault, Slack and Kubernetes first and Azure and Google Cloud second? The author sees no technical need to split.
4. Should CI gain a MinIO service so the S3 anchor policy is enforced by a real S3-compatible server, as Vault is? Zero money; one more CI container.
For the owner (each needs a decision only he can make):
5. Azure anchor in GOVERNANCE mode: if G18 is confirmed to be the same permission that removes an Unlocked policy, should pilot and prod refuse `azure_immutable_blob` with `mode: GOVERNANCE`, or accept it in writing per client?
6. Anthropic on Azure AI Foundry signs in with a resource-wide key. Accept with "one Foundry resource per deployment" written on the page, or order a follow-up ticket for identity-based sign-in (a code change)?
7. Live proof (section 9): which accounts, and when.
Not established (lowest confidence first; the live check must settle each before build):
- G17, G18 (Azure blob create and immutability permissions) and whether listing needs more than G19/G20.
- G06 conditions (`s3:object-lock-mode`, `s3:object-lock-remaining-retention-days`) and whether MinIO and Ceph honour them.
- G32 (restricted keys differ per OpenAI-compatible provider).
- G28: whether one publisher model can be the resource; G09 resources for cross-region inference profiles.
- G03 condition values for Ed25519; G16; K8 on Managed HSM (different permission names, not derived).
- Whether `parliament` or `policy_sentry` is maintained and licence-clean today.
- G02 applies only with a client-managed key; the page must say so.

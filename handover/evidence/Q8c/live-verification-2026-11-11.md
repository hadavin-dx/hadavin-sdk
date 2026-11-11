# Q8c live verification of permission names, 2026-11-11

EVIDENCE RUNNER record. It records what vendor sources say. It does not judge the ticket design. Model: Fable 5.2 (`claude-fable-5-2`). Fetches made 2026-11-11 between about 14:02 and 14:20 UTC (19:32 to 19:50 IST).

Input read: `handover/tickets/Q8c-least-privilege-policy-per-kind.md` section 6 (rev 1 text, read 2026-11-11 about 14:02 UTC, before the rewrite; the same text is now kept as `handover/tickets/Q8c-rev1-superseded.md`). Kinds checked: K1 to K6 and K16 to K19. K7 to K15 were not in this task and were not checked.

## Read this first: what failed and what was not checked

1. **The human-readable vendor pages could not be opened from this session.** `docs.aws.amazon.com`, `docs.slack.dev`, `developer.hashicorp.com`, `openbao.org`, `kubernetes.io` and `docs.getmoto.org` are outside this session's allowed network hosts (curl: "CONNECT tunnel failed, response 403"; page fetch tool: "getaddrinfo ENOTFOUND"). No environment change was requested. Every row that needed one of those pages and had no other vendor-owned source is marked PAGE NOT REACHABLE and is NOT VERIFIED.
2. **What was used instead, all vendor-owned and fetched today:** (a) the AWS Service Reference JSON files at `servicereference.us-east-1.amazonaws.com` (AWS's machine-readable form of the Service Authorization Reference: actions, resource ARN formats, condition keys with types, and which actions authorise each API operation; each file reports "Version": "v1.5"); (b) the AWS API models in `boto/botocore` branch `develop` (version string 1.44.0), which carry the API Reference text of each operation; (c) the documentation source files of Vault (`hashicorp/web-unified-docs`, commit 82e7167 of 2026-11-11, folder `content/vault/v2.x`), OpenBao (`openbao/openbao`, commit 0d706a0 of 2026-11-10, folder `website/content/docs`) and Kubernetes (`kubernetes/website`, commit 18f8e9f of 2026-11-11), plus the built-in policy source files of Vault, OpenBao and Kubernetes. These are the files the public pages are built from, not the rendered pages themselves.
3. **Slack: nothing was verified.** Slack publishes no current machine-readable scope list that this session could reach. All 14 Slack rows are PAGE NOT REACHABLE. Two weaker hints are written beside them and are not proof: web-search result summaries of the official pages (a search engine's summary, not a page read), and Slack's own archived API spec last changed 2021-09-07, which predates today's scope names.
4. **Old AWS user-guide copies.** AWS's archived `awsdocs/*` GitHub copies (last commit 2023-06-15) were read for prose that the JSON and API models do not hold. They are more than three years old and are quoted only as a labelled hint beside a PAGE NOT REACHABLE row, never as verification.
5. **Not checked at all:** MinIO and Ceph policy support (K3 note); the Aurora and RDS Proxy variants of the database resource id beyond the archived hint; whether a real AWS account accepts these policies; any Azure or Google kind.
6. A VERIFIED mark on a never-list entry means only "this name exists with this spelling in the vendor source". It says nothing about whether the never-list is complete.
7. Quotes are copied from the fetched files. JSON fragments are shortened with "..." where a list is long. Markdown link and escape markup inside a quote was removed; no words were changed.

Status words: VERIFIED = found in a vendor-owned source fetched today, spelled exactly so. WRONG = the vendor source shows a different name. NOT FOUND = vendor sources were read and do not contain it. PAGE NOT REACHABLE = the page that would answer it is blocked; NOT VERIFIED.

## Sources (exact URLs; the tables cite them by short id)

| id | URL |
|---|---|
| SM | https://servicereference.us-east-1.amazonaws.com/v1/secretsmanager/secretsmanager.json |
| KMS | https://servicereference.us-east-1.amazonaws.com/v1/kms/kms.json |
| S3 | https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json |
| BR | https://servicereference.us-east-1.amazonaws.com/v1/bedrock/bedrock.json |
| RDSDB | https://servicereference.us-east-1.amazonaws.com/v1/rds-db/rds-db.json |
| RDS | https://servicereference.us-east-1.amazonaws.com/v1/rds/rds.json |
| MP | https://servicereference.us-east-1.amazonaws.com/v1/aws-marketplace/aws-marketplace.json |
| BC-SM | https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/secretsmanager/2017-10-17/service-2.json |
| BC-KMS | https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/kms/2014-11-01/service-2.json |
| BC-S3 | https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/s3/2006-03-01/service-2.json |
| BC-BRT | https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/bedrock-runtime/2023-09-30/service-2.json |
| BC-BR | https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/bedrock/2023-04-20/service-2.json |
| V-POL | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/docs/concepts/policies.mdx |
| V-TOK | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/auth/token.mdx |
| V-KV | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/secret/kv/kv-v2.mdx |
| V-TR | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/secret/transit.mdx |
| V-API | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/index.mdx |
| V-APPROLE | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/auth/approle.mdx |
| V-K8S | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/api-docs/auth/kubernetes.mdx |
| V-TOKF | https://github.com/hashicorp/web-unified-docs/blob/82e7167/content/vault/v2.x/content/partials/tokenstorefields.mdx |
| V-SRC | https://raw.githubusercontent.com/hashicorp/vault/main/vault/policy_store.go |
| B-POL | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/concepts/policies.mdx |
| B-TOK | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/api/auth/token.mdx |
| B-KV | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/api/secret/kv/kv-v2.mdx |
| B-KVD | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/secrets/kv/kv-v2.mdx |
| B-TR | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/api/secret/transit.mdx |
| B-API | https://github.com/openbao/openbao/blob/0d706a0/website/content/docs/api/index.mdx |
| B-SRC | https://github.com/openbao/openbao/blob/0d706a0/internal/vault/policy/policy_store.go |
| K-RBAC | https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/reference/access-authn-authz/rbac.md |
| K-AUTHZ | https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/reference/access-authn-authz/authorization.md |
| K-SSRR | https://github.com/kubernetes/website/blob/18f8e9f/content/en/docs/reference/kubernetes-api/definitions/self-subject-rules-review-v1-authorization.md |
| K-KUBELET | https://github.com/kubernetes/website/blob/18f8e9f/content/en/docs/reference/access-authn-authz/kubelet-authn-authz.md |
| K-SRC | https://raw.githubusercontent.com/kubernetes/kubernetes/master/plugin/pkg/auth/authorizer/rbac/bootstrappolicy/policy.go |
| SL-POST | https://docs.slack.dev/reference/methods/chat.postMessage |
| SL-UPD | https://docs.slack.dev/reference/methods/chat.update |
| SL-SC | https://docs.slack.dev/reference/scopes |
| SL-OLD | https://raw.githubusercontent.com/slackapi/slack-api-specs/master/web-api/slack_web_openapi_v2.json |
| AWS-S3OL | https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html |
| AWS-S3KMS | https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html |
| AWS-KMSCOND | https://docs.aws.amazon.com/kms/latest/developerguide/conditions-kms.html |
| AWS-KMSKP | https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html |
| AWS-SMENC | https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html |
| AWS-SMPOL | https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_iam-policies.html |
| AWS-BRIP | https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html |
| AWS-RDSIAM | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.IAMPolicy.html |
| AWS-IAMCHK | https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-reference-policy-checks.html |
| AWS-IAMVAL | https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_policy-validator.html |
| AWS-IAMOP | https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html |
| ARCH-S3OL | https://raw.githubusercontent.com/awsdocs/amazon-s3-userguide/main/doc_source/object-lock-managing.md |
| ARCH-S3OLO | https://raw.githubusercontent.com/awsdocs/amazon-s3-userguide/main/doc_source/object-lock-overview.md |
| ARCH-S3KMS | https://raw.githubusercontent.com/awsdocs/amazon-s3-userguide/main/doc_source/UsingKMSEncryption.md |
| ARCH-SMENC | https://raw.githubusercontent.com/awsdocs/aws-secrets-manager-docs/master/doc_source/security-encryption.md |
| ARCH-RDS | https://raw.githubusercontent.com/awsdocs/amazon-rds-user-guide/main/doc_source/UsingWithRDS.IAMDBAuth.IAMPolicy.md |
| ARCH-IAMVAL | https://raw.githubusercontent.com/awsdocs/iam-user-guide/main/doc_source/access_policies_policy-validator.md |
| ARCH-IAMCHK | https://raw.githubusercontent.com/awsdocs/iam-user-guide/main/doc_source/access-analyzer-reference-policy-checks.md |
| ARCH-IAMOP | https://raw.githubusercontent.com/awsdocs/iam-user-guide/main/doc_source/reference_policies_elements_condition_operators.md |
| ARCH-KMSKP | https://raw.githubusercontent.com/awsdocs/aws-kms-developer-guide/master/doc_source/key-policy-default.md |

Ids starting `AWS-` and `SL-` are the pages that could NOT be reached. Ids starting `ARCH-` are archived 2023-06-15 copies. `SL-OLD` is Slack's archived spec of 2021-09-07.

## K1 secrets / aws_secrets_manager

| item | status | source | quote or note |
|---|---|---|---|
| G01 `secretsmanager:GetSecretValue` (action for `get_secret_value`) | VERIFIED | SM, BC-SM | JSON `Operations`: GetSecretValue -> AuthorizedActions [secretsmanager:GetSecretValue]. API model: "Required permissions: secretsmanager:GetSecretValue." |
| G01 resource ARN form `arn:aws:secretsmanager:{region}:<ACCOUNT_ID>:secret:...` | VERIFIED | SM | Resource "Secret": "arn:${Partition}:secretsmanager:${Region}:${Account}:secret:${SecretId}" |
| G01 the `-??????` suffix pattern (six characters AWS adds) | PAGE NOT REACHABLE | AWS-SMPOL | docs.aws.amazon.com blocked from this session. NOT VERIFIED. A web-search summary of that page (not a page read) says the `??????` pattern matches the six random characters and warns against `*` there. |
| G02 `kms:Decrypt` (only for a customer-managed key) | VERIFIED | BC-SM, KMS | API model GetSecretValue: "If the secret is encrypted using a customer-managed key ... then you also need kms:Decrypt permissions for that key." |
| G02 condition key `kms:ViaService` (exists, valid on kms:Decrypt, type String) | VERIFIED | KMS | JSON: Decrypt `ActionConditionKeys` includes "kms:ViaService"; `ConditionKeys`: {"Name":"kms:ViaService","Types":["String"]} |
| G02 value form of `kms:ViaService` for Secrets Manager (`secretsmanager.<region>.amazonaws.com`) | PAGE NOT REACHABLE | AWS-SMENC, AWS-KMSCOND | Live pages blocked. NOT VERIFIED live. Archived copy of 2023-06-15 (ARCH-SMENC): "kms:ViaService condition key with the `secretsmanager.<Region>.amazonaws.com` value". |
| `secretsmanager:PutSecretValue` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "PutSecretValue" |
| `secretsmanager:UpdateSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "UpdateSecret" |
| `secretsmanager:CreateSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "CreateSecret" |
| `secretsmanager:DeleteSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "DeleteSecret" |
| `secretsmanager:RestoreSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "RestoreSecret" |
| `secretsmanager:PutResourcePolicy` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "PutResourcePolicy" |
| `secretsmanager:ListSecrets` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "ListSecrets"; no resource type listed (cannot be scoped to one secret) |
| `secretsmanager:DescribeSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "DescribeSecret" |
| `secretsmanager:BatchGetSecretValue` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "BatchGetSecretValue"; no resource type listed |
| `secretsmanager:RotateSecret` | VERIFIED | SM | service reference JSON `Actions[].Name` holds exactly "RotateSecret" |

## K2 signer / aws_kms

| item | status | source | quote or note |
|---|---|---|---|
| G03 `kms:Sign` (action for `Sign`) | VERIFIED | KMS, BC-KMS | JSON `Operations`: Sign -> [kms:Sign]. API model: "Required permissions : kms:Sign (key policy)" |
| G03 resource ARN `arn:aws:kms:{region}:<ACCOUNT_ID>:key/<KEY_ID>` | VERIFIED | KMS | Resource "key": "arn:${Partition}:kms:${Region}:${Account}:key/${KeyId}". Sign lists resource type `key` only (no `alias`). |
| G03 condition key `kms:SigningAlgorithm` (exists, valid on Sign, type String) | VERIFIED | KMS, BC-KMS | Sign `ActionConditionKeys` includes "kms:SigningAlgorithm"; Types ["String"]. API model enum SigningAlgorithmSpec contains "ED25519_SHA_512". |
| G03 condition key `kms:MessageType` (exists, valid on Sign, type String) | VERIFIED | KMS, BC-KMS | Sign `ActionConditionKeys` includes "kms:MessageType"; Types ["String"]. API model enum MessageType: ["RAW","DIGEST","EXTERNAL_MU"]. |
| G04 `kms:GetPublicKey` (action for `GetPublicKey`), same key resource | VERIFIED | KMS, BC-KMS | JSON `Operations`: GetPublicKey -> [kms:GetPublicKey]; resource `key`. API model: "Required permissions : kms:GetPublicKey (key policy)" |
| K2 note: `kms:Verify` authorises `Verify`; `kms:DescribeKey` authorises `DescribeKey` (asked in the brief) | VERIFIED | KMS, BC-KMS | API model: "Required permissions : kms:Verify (key policy)"; "Required permissions : kms:DescribeKey (key policy)" |
| K2 note: "The key's own key policy must let IAM policies apply" | PAGE NOT REACHABLE | AWS-KMSKP | Live page blocked. NOT VERIFIED live. Archived copy of 2023-06-15 (ARCH-KMSKP) has the heading "Allows access to the AWS account and enables IAM policies". |
| `kms:ScheduleKeyDeletion` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "ScheduleKeyDeletion" |
| `kms:DisableKey` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "DisableKey" |
| `kms:PutKeyPolicy` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "PutKeyPolicy" |
| `kms:CreateGrant` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "CreateGrant" |
| `kms:UpdateKeyDescription` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "UpdateKeyDescription" |
| `kms:UpdateAlias` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "UpdateAlias"; resource types alias and key |
| `kms:DeleteAlias` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "DeleteAlias"; resource types alias and key |
| `kms:ImportKeyMaterial` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "ImportKeyMaterial" |
| `kms:DeleteImportedKeyMaterial` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "DeleteImportedKeyMaterial" |
| `kms:Decrypt` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "Decrypt" |
| `kms:Encrypt` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "Encrypt" |
| `kms:Verify` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "Verify" |
| `kms:TagResource` | VERIFIED | KMS | service reference JSON `Actions[].Name` holds exactly "TagResource" |

## K3 anchor / s3_object_lock

| item | status | source | quote or note |
|---|---|---|---|
| G05 `s3:PutObject` (action for `PutObject`) | VERIFIED | S3, BC-S3 | API model PutObject: "you must always have the s3:PutObject permission on a bucket to add an object to it." |
| G05 resource ARN `arn:aws:s3:::{bucket}/anchors/*` | VERIFIED | S3 | Resource "object": "arn:${Partition}:s3:::${BucketName}/${ObjectName}" |
| G06 `s3:PutObjectRetention` exists; it is listed as an action that authorises the `PutObject` call | VERIFIED | S3 | JSON `Operations`: PutObject -> AuthorizedActions [PutObject, PutObjectAcl, PutObjectLegalHold, PutObjectRetention, PutObjectTagging, ...]. This is a mapping, not a sentence. |
| G06 the sentence "S3 asks for this permission when a put carries lock headers" | NOT FOUND | BC-S3, S3 | No such sentence in the PutObject API model: its permission list names only s3:PutObject, s3:PutObjectAcl, s3:PutObjectTagging. Only the JSON mapping above supports it. Live user-guide pages blocked. |
| G06 condition key `s3:object-lock-mode` (exists, type String, valid on PutObject and PutObjectRetention) | VERIFIED | S3 | {"Name":"s3:object-lock-mode","Types":["String"]}; in `ActionConditionKeys` of both PutObject and PutObjectRetention. |
| G06 condition key `s3:object-lock-remaining-retention-days` (exists, type Numeric, valid on PutObject and PutObjectRetention) | VERIFIED | S3 | {"Name":"s3:object-lock-remaining-retention-days","Types":["Numeric"]}; in `ActionConditionKeys` of both actions. |
| G06 operator for "at least {retain_days}" (`NumericGreaterThanEquals`) | PAGE NOT REACHABLE | AWS-IAMOP | Live IAM operator page blocked. NOT VERIFIED live. Archived 2023-06-15 copy (ARCH-IAMOP): "`NumericGreaterThanEquals` \| \"Greater than or equals\" matching". |
| G07 `s3:GetObject` (action for `GetObject` without a version id) | VERIFIED | BC-S3, S3 | API model GetObject: "If you request the current version of an object without a specific versionId ... only the s3:GetObject permission is required." |
| G08 `s3:ListBucket` (action for `ListObjectsV2`), bucket ARN `arn:aws:s3:::{bucket}` | VERIFIED | BC-S3, S3 | API model ListObjectsV2: "You must have permission to perform the s3:ListBucket action." Resource "bucket": "arn:${Partition}:s3:::${BucketName}" |
| G08 condition key `s3:prefix` (exists, type String, valid on ListBucket) | VERIFIED | S3 | {"Name":"s3:prefix","Types":["String"]}; ListBucket `ActionConditionKeys` includes "s3:prefix". |
| Brief item: `GetObjectRetention` is authorised by `s3:GetObjectRetention` | VERIFIED | S3 | JSON `Operations`: GetObjectRetention -> [s3:GetObjectRetention]. (GetObject also lists it as an extra authorised action.) |
| Brief item: `ListObjectVersions` is authorised by `s3:ListBucketVersions` (not by s3:ListBucket) | VERIFIED | BC-S3, S3 | API model: "you must have permission to perform the s3:ListBucketVersions action. Be aware of the name difference." |
| `s3:DeleteObject` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "DeleteObject" |
| `s3:DeleteObjectVersion` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "DeleteObjectVersion" |
| `s3:BypassGovernanceRetention` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "BypassGovernanceRetention"; API model PutObjectRetention: "Bypassing a Governance Retention configuration requires the s3:BypassGovernanceRetention permission." |
| `s3:PutObjectLegalHold` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutObjectLegalHold" |
| `s3:PutBucketObjectLockConfiguration` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutBucketObjectLockConfiguration" |
| `s3:PutLifecycleConfiguration` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutLifecycleConfiguration" |
| `s3:PutBucketPolicy` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutBucketPolicy" |
| `s3:PutBucketVersioning` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutBucketVersioning" |
| `s3:PutObjectAcl` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutObjectAcl" |
| `s3:PutBucketAcl` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "PutBucketAcl" |
| `s3:DeleteBucket` | VERIFIED | S3 | service reference JSON `Actions[].Name` holds exactly "DeleteBucket" |

## K4 llm / bedrock

| item | status | source | quote or note |
|---|---|---|---|
| G09 `bedrock:InvokeModel` authorises `Converse` (there is no `bedrock:Converse` action) | VERIFIED | BC-BRT, BR | API model Converse: "This operation requires permission for the bedrock:InvokeModel action." JSON has no action named Converse. |
| G09 resource ARN `arn:aws:bedrock:{region}::foundation-model/<MODEL_ID>` | VERIFIED | BR | Resource "foundation-model": "arn:${Partition}:bedrock:${Region}::foundation-model/${ResourceId}" |
| G09 resource ARN `arn:aws:bedrock:{region}:<ACCOUNT_ID>:inference-profile/<PROFILE_ID>` | VERIFIED | BR | Resource "inference-profile": "arn:${Partition}:bedrock:${Region}:${Account}:inference-profile/${ResourceId}"; InvokeModel lists it as a resource type. |
| G09 "plus the foundation-model ARN in each region that profile sends to" | PAGE NOT REACHABLE | AWS-BRIP | Live page blocked. NOT VERIFIED. A web-search summary of that page (not a page read) says the foundation model must be listed for each Region of the profile. |
| `bedrock:InvokeModelWithResponseStream` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "InvokeModelWithResponseStream"; JSON `Operations`: ConverseStream -> InvokeModelWithResponseStream |
| `bedrock:CreateModelInvocationJob` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "CreateModelInvocationJob" |
| `bedrock:PutModelInvocationLoggingConfiguration` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "PutModelInvocationLoggingConfiguration" |
| `bedrock:DeleteModelInvocationLoggingConfiguration` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "DeleteModelInvocationLoggingConfiguration" |
| `bedrock:CreateProvisionedModelThroughput` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "CreateProvisionedModelThroughput" |
| `bedrock:CreateModelCustomizationJob` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "CreateModelCustomizationJob" |
| `bedrock:PutFoundationModelEntitlement` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "PutFoundationModelEntitlement" |
| `aws-marketplace:Subscribe` | VERIFIED | MP | service reference JSON `Actions[].Name` holds exactly "Subscribe" |

## K5 detector / bedrock_guardrail

| item | status | source | quote or note |
|---|---|---|---|
| G10 `bedrock:GetGuardrail` (action for `GetGuardrail`) | VERIFIED | BR | JSON `Operations`: GetGuardrail -> AuthorizedActions [bedrock:GetGuardrail, bedrock:CallWithBearerToken]; resource type `guardrail`. |
| G10/G11 resource ARN `arn:aws:bedrock:{region}:<ACCOUNT_ID>:guardrail/{guardrail_id}` | VERIFIED | BR | Resource "guardrail": "arn:${Partition}:bedrock:${Region}:${Account}:guardrail/${GuardrailId}" |
| G11 `bedrock:ApplyGuardrail` (action for `ApplyGuardrail`) | VERIFIED | BR | JSON `Operations`: ApplyGuardrail -> AuthorizedActions [bedrock:ApplyGuardrail, ...]; resource types `guardrail` and `guardrail-profile`. |
| `bedrock:UpdateGuardrail` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "UpdateGuardrail" |
| `bedrock:DeleteGuardrail` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "DeleteGuardrail" |
| `bedrock:CreateGuardrail` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "CreateGuardrail" |
| `bedrock:CreateGuardrailVersion` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "CreateGuardrailVersion" |
| `bedrock:ListGuardrails` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "ListGuardrails" |
| `bedrock:InvokeModel` | VERIFIED | BR | service reference JSON `Actions[].Name` holds exactly "InvokeModel" |

## K6 store / postgres with iam_auth (RDS IAM database sign-in)

| item | status | source | quote or note |
|---|---|---|---|
| G12 `rds-db:connect` (lower-case `connect`) | VERIFIED | RDSDB | JSON service "RDS IAM Authentication": `Actions[].Name` = "connect"; resource type `db-user`. |
| G12 resource ARN `arn:aws:rds-db:{region}:<ACCOUNT_ID>:dbuser:<DB_RESOURCE_ID>/<DB_USER>` | VERIFIED | RDSDB | Resource "db-user": "arn:${Partition}:rds-db:${Region}:${Account}:dbuser:${DbiResourceId}/${DbUserName}" |
| G12 "It sends nothing: the token is signed locally" and which id goes in `<DB_RESOURCE_ID>` (instance, cluster or proxy) | PAGE NOT REACHABLE | AWS-RDSIAM | Live page blocked. NOT VERIFIED live. Archived 2023-06-15 copy (ARCH-RDS): "If you are using Amazon Aurora, specify a `DbClusterResourceId` instead of a `DbiResourceId`." |
| NEVER `rds-db:connect` for any other database user | VERIFIED | RDSDB | Same action and ARN form as G12; the user name is the last ARN part "${DbUserName}", so one ARN names one user. |
| `rds:ModifyDBInstance` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "ModifyDBInstance" |
| `rds:DeleteDBInstance` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "DeleteDBInstance" |
| `rds:ModifyDBCluster` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "ModifyDBCluster" |
| `rds:CreateDBSnapshot` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "CreateDBSnapshot" |
| `rds:RestoreDBInstanceFromDBSnapshot` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "RestoreDBInstanceFromDBSnapshot" |
| `rds:DescribeDBInstances` | VERIFIED | RDS | service reference JSON `Actions[].Name` holds exactly "DescribeDBInstances" |

## K16 channel / slack

| item | status | source | quote or note |
|---|---|---|---|
| G33 bot scope `chat:write` for `chat.postMessage` | PAGE NOT REACHABLE | SL-POST | docs.slack.dev blocked from this session. NOT VERIFIED. A web-search summary of that page (not a page read) lists "Bot tokens chat:write". The 2021 archived Slack spec (SL-OLD) lists only the older `chat:write:bot` / `chat:write:user`. |
| G34 bot scope `chat:write` for `chat.update` | PAGE NOT REACHABLE | SL-UPD | docs.slack.dev blocked from this session. NOT VERIFIED. A web-search summary of that page lists "Bot tokens chat:write". |
| G34 "a bot may update only its own messages" | PAGE NOT REACHABLE | SL-UPD | docs.slack.dev blocked from this session. NOT VERIFIED. The web-search summary did not confirm this sentence either. |
| NEVER `chat:write.public` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Web-search summary: scope page exists; lets an app post in public channels it has not joined; needs chat:write too. |
| NEVER `chat:write.customize` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Web-search summary: scope page exists; custom username and avatar; needs chat:write too. |
| NEVER `channels:read` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Present in the 2021 archived Slack spec (SL-OLD) scope list; not read on today's page. |
| NEVER `channels:history` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Present in the 2021 archived Slack spec scope list; not read on today's page. |
| NEVER `groups:history` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Present in the 2021 archived Slack spec scope list; not read on today's page. |
| NEVER `users:read` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Present in the 2021 archived Slack spec scope list; not read on today's page. |
| NEVER `users:read.email` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Present in the 2021 archived spec; web-search summary: scope page exists, "must be requested at the same time as users:read". |
| NEVER `files:write` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Web-search summary: files:write exists and replaces `files:write:user`. The 2021 archived spec has only `files:write:user`. |
| NEVER `admin` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Conflicting hints: the 2021 archived spec lists a scope named `admin`; today's web-search summary found only the `admin.*` family, no plain `admin`. Needs a page read. |
| NEVER any user token scope | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. A class, not one name; nothing to spell-check. |
| NEVER `incoming-webhook` | PAGE NOT REACHABLE | SL-SC | docs.slack.dev blocked from this session. NOT VERIFIED. Web-search summary: scope page docs.slack.dev/reference/scopes/incoming-webhook exists ("Post messages to specific channels"). |

## K17 secrets / vault (Vault and OpenBao)

| item | status | source | quote or note |
|---|---|---|---|
| G35 capability `read` for `GET {mount}/data/<path>` (KV version 2) | VERIFIED | V-KV, V-POL, B-KV, B-POL | Vault KV v2 API: "\| `GET` \| `/:secret-mount-path/data/:path?version=:version` \|". Policies: "`read` (`GET`) - Allows reading the data at the given path." OpenBao: same two lines. |
| G35 path form `{mount}/data/{path_prefix}*` (a `*` at the end means prefix match) | VERIFIED | V-POL, B-POL | Vault: glob "is only supported **as the last character of the path**". OpenBao: same sentence. OpenBao KV doc: "Writing and reading versions are prefixed with the `data/` path." |
| free: sign-in `POST auth/<mount>/login` needs no token (approle, kubernetes) | VERIFIED | V-API, V-APPROLE, V-K8S, B-API | Vault API index: "Each auth method has one or more unauthenticated login endpoints." Tables: "`POST` \| `/auth/approle/login`", "`POST` \| `/auth/kubernetes/login`". OpenBao index: same sentence. |
| NEVER capability `create` on `{mount}/data/*` | VERIFIED | V-POL, V-KV | "`create` (`POST/PUT`) - Allows creating data at the given path."; KV v2: "`POST` \| `/:secret-mount-path/data/:path`" |
| NEVER capability `update` on `{mount}/data/*` | VERIFIED | V-POL | "`update` (`POST/PUT`) - Allows changing the data at the given path." |
| NEVER capability `patch` on `{mount}/data/*` | VERIFIED | V-POL, V-KV | "`patch` (`PATCH`) - Allows partial updates to the data at a given path."; KV v2: "`PATCH` \| `/:secret-mount-path/data/:path`" |
| NEVER capability `delete` on `{mount}/data/*` | VERIFIED | V-POL, V-KV | "`delete` (`DELETE`) - Allows deleting the data at the given path."; KV v2: "`DELETE` \| `/:secret-mount-path/data/:path`" |
| NEVER capability `list` on `{mount}/data/*` | VERIFIED | V-POL, V-KV | "`list` (`LIST`) - Allows listing values at the given path." Observed: the KV v2 API documents LIST on `metadata/:path` only, none on `data/`. |
| NEVER any capability on `{mount}/metadata/*` | VERIFIED | V-KV, B-KV | KV v2 tables: LIST, GET, POST, PATCH, DELETE on "/:secret-mount-path/metadata/:path". OpenBao adds "`LIST` \| `/:secret-mount-path/detailed-metadata/:path`". |
| NEVER `{mount}/delete/*` | VERIFIED | V-KV, B-KV | "`POST` \| `/:secret-mount-path/delete/:path`" (both docs). Observed, not on the ticket list: `undelete/:path` and `subkeys/:path` also exist. |
| NEVER `{mount}/destroy/*` | VERIFIED | V-KV, B-KV | "`PUT` \| `/:secret-mount-path/destroy/:path`" (both docs) |
| NEVER `sys/*` | VERIFIED | V-POL | Root-protected table lists paths such as "sys/audit", "sys/auth/:path"; the `sys/` prefix is real. |
| NEVER `auth/token/create` | VERIFIED | V-TOK, V-POL | Root-protected table: "auth/token/create \| POST \| Create a periodic or an orphan token"; token API documents `POST /auth/token/create`. |
| NEVER `auth/*` beyond the sign-in | VERIFIED | V-API | A class, not one name; the `auth/` prefix is real ("/auth/approle/login"). |
| NEVER capability `sudo` | VERIFIED | V-POL, B-POL | "`sudo` - Allows access to paths that are _root-protected_." (both docs) |
| NEVER the `root` policy | VERIFIED | V-POL | "The `root` policy is a built-in Vault policy that cannot be modified or removed." |

## K18 signer / vault_transit (Vault and OpenBao)

| item | status | source | quote or note |
|---|---|---|---|
| G36 capability `update` for `POST {transit_mount}/sign/{key_name}` | VERIFIED | V-TR, B-TR, V-POL | "`POST` \| `/transit/sign/:name(/:hash_algorithm)`" (both docs). Policies: "`update` (`POST/PUT`)". Note the optional `/:hash_algorithm` path part. |
| G37 capability `read` for `GET {transit_mount}/keys/{key_name}` | VERIFIED | V-TR, B-TR | "`GET` \| `/transit/keys/:name`" (both docs). Observed: Vault v2.x also documents "`GET` \| `/transit/keys/:name/:version`". |
| free: the sign-in request | VERIFIED | V-API | Same evidence as K17: "unauthenticated login endpoints". |
| NEVER capability `update` on `{transit_mount}/keys/{key_name}` | VERIFIED | V-TR | "`POST` \| `/transit/keys/:name`" (create key) is the POST on that path. |
| NEVER capability `create` on `{transit_mount}/keys/{key_name}` | VERIFIED | V-TR, V-POL | Same path; "most operations require both `create` and `update` capabilities." |
| NEVER capability `delete` on `{transit_mount}/keys/{key_name}` | VERIFIED | V-TR, B-TR | "`DELETE` \| `/transit/keys/:name`". OpenBao also has "`DELETE` \| `/transit/keys/:name/soft-delete`". |
| NEVER `{transit_mount}/keys/{key_name}/rotate` | VERIFIED | V-TR, B-TR | "`POST` \| `/transit/keys/:name/rotate`" (both docs) |
| NEVER `{transit_mount}/keys/{key_name}/config` | VERIFIED | V-TR, B-TR | "`POST` \| `/transit/keys/:name/config`" (both docs) |
| NEVER `{transit_mount}/keys/{key_name}/trim` | VERIFIED | V-TR, B-TR | "`POST` \| `/transit/keys/:name/trim`" (both docs) |
| NEVER `{transit_mount}/export/*` | VERIFIED | V-TR, B-TR | "`GET` \| `/transit/export/:key_type/:name(/:version)`". Observed, not on the ticket list: "`GET` \| `/transit/byok-export/:destination/:source(/:version)`". |
| NEVER `{transit_mount}/backup/*` | VERIFIED | V-TR, B-TR | "`GET` \| `/transit/backup/:name`" (both docs) |
| NEVER `{transit_mount}/restore/*` | VERIFIED | V-TR, B-TR | "`POST` \| `/transit/restore(/:name)`": the name part is optional, so the bare path `restore` also exists; `restore/*` is a prefix match on `restore/`. |
| NEVER `{transit_mount}/sign/*` for another key | VERIFIED | V-TR | Same endpoint as G36 with another `:name`. |
| NEVER `sys/*` | VERIFIED | V-POL | As K17. |
| NEVER capability `sudo` | VERIFIED | V-POL | As K17. |

## K19 source / kubernetes

| item | status | source | quote or note |
|---|---|---|---|
| G38 verb `list` on `deployments`, API group `apps` | VERIFIED | K-AUTHZ, K-SRC | authorization.md: "`GET`, `HEAD` \| **get** (for individual resources), **list** (for collections ...)". Source: Groups(appsGroup).Resources(... "deployments" ...). |
| G39 verb `list` on `events`, core API group | VERIFIED | K-AUTHZ, K-SRC | Source: NewRule(Read...).Groups(legacyGroup, eventsGroup).Resources("events"). Observed: `events` exists in the core group and in `events.k8s.io`. |
| G40 verb `get` on `pods/log`, core API group | VERIFIED | K-RBAC, K-SRC | rbac.md: "use a slash (`/`) to delimit the resource and subresource"; example `resources: ["pods", "pods/log"]`. |
| free: `POST selfsubjectrulesreviews` needs no extra grant in a default cluster; otherwise verb `create` | VERIFIED | K-RBAC, K-SRC, K-SSRR | rbac.md: system:basic-user is bound to the "system:authenticated group". Source: NewRule("create").Groups(authorizationGroup).Resources("selfsubjectaccessreviews", "selfsubjectrulesreviews"). |
| free: SelfSubjectRulesReview caveat recorded from the vendor text | VERIFIED | K-SSRR | "The returned list of actions may be incomplete depending on the server's authorization mode, and any errors experienced during the evaluation." |
| NEVER verb `create` | VERIFIED | K-AUTHZ | "API verbs like `get`, `list`, `create`, `update`, `patch`, `watch`, `delete`, and `deletecollection` are used for resource requests." |
| NEVER verb `update` | VERIFIED | K-AUTHZ | "API verbs like `get`, `list`, `create`, `update`, `patch`, `watch`, `delete`, and `deletecollection` are used for resource requests." |
| NEVER verb `patch` | VERIFIED | K-AUTHZ | "API verbs like `get`, `list`, `create`, `update`, `patch`, `watch`, `delete`, and `deletecollection` are used for resource requests." |
| NEVER verb `delete` | VERIFIED | K-AUTHZ | "API verbs like `get`, `list`, `create`, `update`, `patch`, `watch`, `delete`, and `deletecollection` are used for resource requests." |
| NEVER verb `deletecollection` | VERIFIED | K-AUTHZ | "API verbs like `get`, `list`, `create`, `update`, `patch`, `watch`, `delete`, and `deletecollection` are used for resource requests." |
| NEVER verb `escalate` | VERIFIED | K-AUTHZ | "**bind** and **escalate** verbs on `roles` and `clusterroles` resources in the `rbac.authorization.k8s.io` API group." |
| NEVER verb `bind` | VERIFIED | K-AUTHZ | Same sentence as `escalate`. |
| NEVER verb `impersonate` | VERIFIED | K-AUTHZ | "**impersonate** verb on `users`, `groups`, and `serviceaccounts` in the core API group" |
| NEVER verb `watch` | VERIFIED | K-AUTHZ | "The **get**, **list** and **watch** verbs can all return the full details of a resource." |
| NEVER verb `*` | VERIFIED | K-RBAC | Example `verbs: ["*"]`; "Using wildcards in resource and verb entries could result in overly permissive access being granted". |
| NEVER `pods/exec` | VERIFIED | K-RBAC, K-SRC | rbac.md: "you can use the `resourceNames` field with `pods/exec`". Source lists "pods/attach", "pods/proxy", "pods/exec", "pods/portforward". |
| NEVER `pods/attach` | VERIFIED | K-SRC | Source: Resources("pods", "pods/attach", "pods/proxy", "pods/exec", "pods/portforward") |
| NEVER `pods/portforward` | VERIFIED | K-SRC | Same source line. |
| NEVER `pods/proxy` | VERIFIED | K-SRC | Same source line. |
| NEVER `nodes/proxy` | VERIFIED | K-KUBELET | "**get** permission on `nodes/proxy` is not a read-only permission, and authorizes executing commands in any container running on the node." |
| NEVER `services/proxy` | VERIFIED | K-SRC | Source: Resources("pods/attach", "pods/proxy", "pods/exec", "pods/portforward", "secrets", "services/proxy") |
| NEVER any verb on `secrets` | VERIFIED | K-AUTHZ | "**list** on `secrets` will reveal the **data** attributes of any returned resources." |
| NEVER any ClusterRoleBinding | VERIFIED | K-RBAC | Kind name `ClusterRoleBinding` is used throughout rbac.md (a class, not one permission name). |

## Answers to the reviewers' doubts

**D1 Does a bucket with default SSE-KMS need `kms:GenerateDataKey` for PutObject and `kms:Decrypt` for GetObject?**

Status: PAGE NOT REACHABLE. Sources: AWS-S3KMS, BC-S3, ARCH-S3KMS.

The live user-guide page is blocked, so this is NOT VERIFIED on today's page. What was read: (1) today's S3 API model, PutObject and GetObject: "If the object is encrypted with SSE-KMS, you must also have the kms:GenerateDataKey and kms:Decrypt permissions in IAM identity-based policies and KMS key policies for the KMS key." In the model this sentence sits at the end of the "Directory bucket permissions" paragraph, so it is not clear from the text alone that it also covers general purpose buckets. (2) Archived user guide of 2023-06-15: "To upload an object encrypted with an AWS KMS key to Amazon S3, you need `kms:GenerateDataKey` permissions on the key. To download an object encrypted with an AWS KMS key, you need `kms:Decrypt` permissions." (3) A web-search summary of today's page (not a page read) says the same as (2). Nothing read today says a bucket-default key removes the need. Both action names exist (KMS service reference JSON).

**D2 How is `s3:object-lock-remaining-retention-days` computed (whole days? would `NumericGreaterThanEquals` on exactly the configured days refuse a put with retain-until = now + days)?**

Status: NOT FOUND. Sources: S3, ARCH-S3OL, AWS-S3OL.

No vendor text read today states how the number is computed, rounded or truncated. The service reference JSON gives only the type: "Types":["Numeric"]. The archived 2023-06-15 user guide shows one example only (a Deny with "NumericGreaterThan": {"s3:object-lock-remaining-retention-days": "10"} described as "a maximum retention period of 10 days") and no rounding rule. The live page is blocked; a web-search summary of it also found no formula. The boundary case therefore stays open and needs a real-account test. Also observed in the JSON: a sibling key "s3:object-lock-retain-until-date" (type Date) is valid on PutObject and PutObjectRetention.

**D3 Does a Vault token made via `auth/token/create` get the `default` policy unless `no_default_policy` is set, and what does `default` allow?**

Status: VERIFIED. Sources: V-TOK, V-POL, V-TOKF, V-SRC, B-TOK, B-POL, B-SRC.

Yes, per the vendor docs. Vault token API: "`no_default_policy` `(bool: false)` - If true the `default` policy will not be contained in this token's policy set." Vault policies doc: "By default, it is attached to all tokens, but may be explicitly excluded at token creation time". OpenBao: the same two sentences. What `default` allows (Vault source, main branch, today): read `auth/token/lookup-self`; update `auth/token/renew-self`, `auth/token/revoke-self`, `sys/capabilities-self`, `sys/renew`, `sys/leases/renew`, `sys/leases/lookup`, `sys/wrapping/wrap`, `sys/wrapping/lookup`, `sys/wrapping/unwrap`, `sys/tools/hash`, `sys/tools/hash/*`, `sys/control-group/request`; read own `identity/entity/id/...` and `identity/entity/name/...`; read `sys/internal/ui/resultant-acl`; create, read, update, delete, list on `cubbyhole/*`; read, update on `identity/oidc/provider/+/authorize`. OpenBao source lists the same paths except `sys/renew` and `sys/control-group/request` (not seen in its list). The docs also say the policy "can be modified", so a given server may differ. Note for K17/K18, which sign in through approle or kubernetes and not through `auth/token/create`: both auth-method API docs (V-APPROLE, V-K8S) pull in a shared field list (V-TOKF, through the include `tokenfields.mdx`) that holds the role field `token_no_default_policy` `(bool: false)`: "If set, the `default` policy will not be set on generated tokens; otherwise it will be added to the policies set in `token_policies`."

**D4 Does IAM reject a policy that contains an unknown action name?**

Status: NOT FOUND. Sources: AWS-IAMVAL, AWS-IAMCHK, ARCH-IAMVAL, ARCH-IAMCHK.

No vendor text read today says that the IAM API refuses to save such a policy. Live IAM pages are blocked. Archived 2023-06-15 copies: the validator page says "AWS checks JSON policy syntax and grammar. It also verifies that your ARNs are formatted properly and action names and condition keys are correct." and that this happens "when you create a JSON policy or edit an existing policy in the AWS Management Console"; the Access Analyzer check list has "Error - Invalid action ... The action {{action}} does not exist." A web-search summary of today's check page (not a page read) adds that AWS managed policies can contain invalid actions which "do not affect the permissions granted". So: the console and Access Analyzer flag an unknown action; whether `CreatePolicy` / `PutRolePolicy` reject it is not established here.

**D5 Which IAM action authorises each named API call (summary of the rows above)**

All from the AWS service reference JSON `Operations` lists and the API model text, fetched today: `Converse` -> `bedrock:InvokeModel`; `ApplyGuardrail` -> `bedrock:ApplyGuardrail`; `GetGuardrail` -> `bedrock:GetGuardrail`; connecting with a `generate_db_auth_token` token -> `rds-db:connect`; `PutObject` -> `s3:PutObject` (with `s3:PutObjectRetention` listed as a further authorised action, see G06); `GetObjectRetention` -> `s3:GetObjectRetention`; `ListObjectVersions` -> `s3:ListBucketVersions`; KMS `Sign`, `Verify`, `GetPublicKey`, `DescribeKey` -> the action of the same name. These are counted in the kind tables, not again here.

## Other facts seen in the vendor sources (recorded, not judged)

- S3 JSON: `PutObject` and `PutObjectRetention` now also list the condition keys `s3:object-lock-event-hold` and `s3:object-lock-event-hold-duration-days`. A web-search result title mentions "Amazon S3 Object Lock now supports variable retention with event holds" (aws.amazon.com, 2026/09); the page was not read.
- S3 JSON: `PutObject` lists the condition key `s3:if-none-match` (type String).
- S3 JSON: the `PutObjectRetention` operation lists `s3:BypassGovernanceRetention` as a further authorised action.
- S3 API model, GetObject: "If you include a versionId in your request header, you must have the s3:GetObjectVersion permission".
- Bedrock JSON: the `Converse` operation lists four authorised actions: `bedrock:InvokeModel`, `bedrock:ApplyGuardrail`, `bedrock:CallWithBearerToken`, `bedrock:InvokeTool`. `bedrock:InvokeModel` lists the condition keys `bedrock:InferenceProfileArn`, `bedrock:GuardrailIdentifier`, `bedrock:ModelArn` and others.
- Bedrock JSON: `bedrock:ApplyGuardrail` lists two resource types, `guardrail` and `guardrail-profile` (ARN `arn:${Partition}:bedrock:${Region}:${Account}:guardrail-profile/${ResourceId}`).
- Bedrock JSON: a separate resource type `application-inference-profile` exists beside `inference-profile`.
- KMS JSON: `kms:Sign` and `kms:GetPublicKey` also list the condition key `kms:RequestAlias`.
- Secrets Manager JSON: `GetSecretValue` lists the condition keys `secretsmanager:SecretId` (type ARN), `secretsmanager:VersionId`, `secretsmanager:VersionStage`.
- RDS JSON: the `rds-db` service file reports for `connect`: "IAM Access Analyzer Policy Generation": false, "IAM Action Last Accessed": false.
- Vault policies doc lists capabilities `subscribe` and `recover`; OpenBao lists `scan`. None of the three is in the ticket's lists.

## Library facts (PyPI JSON API and GitHub, fetched 2026-11-11)

| library | latest release on PyPI | release date (upload time, UTC) | licence | sources |
|---|---|---|---|---|
| moto | 5.2.5 | 2026-10-27 | Apache-2.0 (PyPI `license` field; LICENSE file in repo: "Apache License Version 2.0") | https://pypi.org/pypi/moto/json ; https://raw.githubusercontent.com/getmoto/moto/master/LICENSE ; last repo commit seen 2026-11-09 |
| parliament | 1.6.4 | 2025-04-25 | BSD 3 (PyPI `license` field "BSD 3", classifier "OSI Approved :: BSD License"; LICENSE file starts "Copyright 2019 Duo Security") | https://pypi.org/pypi/parliament/json ; https://github.com/duo-labs/parliament ; last repo commit seen 2025-04-25 (no commit since then) |
| policy_sentry (PyPI name `policy-sentry`) | 0.15.2 | 2026-04-14 | MIT (PyPI `license_expression` "MIT"; LICENSE file starts "Copyright 2019 Salesforce.com" with the MIT permission text) | https://pypi.org/pypi/policy-sentry/json ; https://github.com/salesforce/policy_sentry ; last repo commit seen 2026-11-10 |

**Does moto document IAM policy enforcement?** Yes, read from moto's own documentation source file (https://raw.githubusercontent.com/getmoto/moto/master/docs/docs/iam.rst ; the rendered site docs.getmoto.org is blocked). Setting name: environment variable `INITIAL_NO_AUTH_ACTION_COUNT`, or the decorator `set_initial_no_auth_action_count`. Quote: "If it is not set, it defaults to infinity, thus moto will never perform any authentication at all." Quote on coverage: "Note that the current implementation is very basic". What it covers, from the header of the source file the doc points to (https://raw.githubusercontent.com/getmoto/moto/master/moto/iam/access_control.py): "This implementation is NOT complete"; "TODO add support for the Resource and Condition parts of IAM policies"; "TODO add support for resource-based policies"; "TODO add support for more principals, apart from IAM users and assumed IAM roles". A second doc file (`docs/docs/configuration/environment_variables.rst`) lists the variable with type int and default 0, which differs from the "defaults to infinity" sentence; both are recorded as written.

## Counts

| kind | items | verified | wrong | not found | page not reachable |
|---|---|---|---|---|---|
| K1 secrets / aws_secrets_manager | 16 | 14 | 0 | 0 | 2 |
| K2 signer / aws_kms | 20 | 19 | 0 | 0 | 1 |
| K3 anchor / s3_object_lock | 23 | 21 | 0 | 1 | 1 |
| K4 llm / bedrock | 12 | 11 | 0 | 0 | 1 |
| K5 detector / bedrock_guardrail | 9 | 9 | 0 | 0 | 0 |
| K6 store / postgres with iam_auth (RDS IAM database sign-in) | 10 | 9 | 0 | 0 | 1 |
| K16 channel / slack | 14 | 0 | 0 | 0 | 14 |
| K17 secrets / vault (Vault and OpenBao) | 16 | 16 | 0 | 0 | 0 |
| K18 signer / vault_transit (Vault and OpenBao) | 15 | 15 | 0 | 0 | 0 |
| K19 source / kubernetes | 23 | 23 | 0 | 0 | 0 |
| reviewer doubts D1 to D4 | 4 | 1 | 0 | 2 | 1 |
| **total** | **162** | **138** | **0** | **3** | **21** |

Counted by the script that wrote this file (one row = one item). Library facts are not in the count.

WRONG items: none found in the sources that could be read. That is not a clean result: 24 items are not verified (21 page not reachable, 3 not found).

## What is needed to finish

Needs the owner (network setting of this cloud session): allow `docs.aws.amazon.com`, `docs.slack.dev`, `developer.hashicorp.com`, `openbao.org`, `kubernetes.io` and `docs.getmoto.org`, then re-run the PAGE NOT REACHABLE rows. Needs a real AWS account (owner step, already named in the ticket's section 9): D2 (the boundary case of the remaining-retention-days condition), D4 (whether the IAM API refuses an unknown action) and the G06 sentence (whether a put with lock headers is refused without `s3:PutObjectRetention`).

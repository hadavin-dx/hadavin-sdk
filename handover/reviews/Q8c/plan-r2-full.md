<!-- full hand-back report of sub-agent ac13fdc7, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW Q8c rev 2 (slice 1), round 2, implementation-readiness, read-only. Nothing was run; every code fact below is from opening the file.

Target: /home/user/hadavin-sdk/handover/tickets/Q8c-least-privilege-policy-per-kind.md
The tests folder /home/user/build/EV-P3a2-main-2a8c2aa/tests exists and was used (no fallback needed).
The live check file /home/user/hadavin-sdk/handover/evidence/Q8c/live-verification-2026-11-11.md appeared during the review and was read in full. It checked the rev-1 text (ids K1-K19, G01-G40), not rev 2.

## BLOCKERS

### B1. Sections 4.5 and 7 step 0: what ships when a name stays unverified is undefined, and the live result makes that the actual case
- 4.5 states two rules that cannot both be a test: "merge gate: zero grants with `verified = None` (a test)" and "until then a name sits in `PENDING_NAMES`". A test cannot know "at merge". Step 3's exit "A green" is impossible while the gate test exists and any grant is `None`.
- `verified` is defined as "set only from the evidence runner's saved page text". The runner could not open any rendered vendor page (evidence file line 9). It used the AWS Service Reference JSON, botocore API models, and the documentation source files of Vault, OpenBao and Kubernetes. By the ticket's own wording, nothing is verified.
- "A kind with ANY grant or condition not verified" (4.5) has no data field behind it: the 4.1 schema has no `verified` on a condition, a resource form or a `bound`.
- Ticket rows the evidence file contradicts or leaves unsupported:
  - **R16 (Slack `chat:write`) and the Slack never entries**: all 14 Slack rows PAGE NOT REACHABLE (evidence lines 207-220). With the gate as written, slice 1 cannot merge.
  - **R06**: the reason "S3 asks for it when a put sets a lock" is NOT FOUND (line 136). Only the mapping "PutObject may be authorised by PutObjectRetention" exists. V1 is unanswered; the retention-days rule is NOT FOUND (D2). Both need a real account.
  - **R01**: the bound `-??????` is not verified (line 89).
  - **R02**: the `kms:ViaService` value form is not verified live (line 92, archived 2023 copy only).
  - **R09, R10**: PAGE NOT REACHABLE (D1). Today's API model names both `kms:GenerateDataKey` and `kms:Decrypt` in one sentence, placed in the directory-bucket paragraph.
  - **R11**: the action is verified. "The model ARN in each region it sends to" is not (line 164). The inference-profile ARN carries an account id (line 163), which the row does not spell.
  - **R13**: `bedrock:ApplyGuardrail` has two resource types, `guardrail` and `guardrail-profile` (lines 180, 328). The row grants the guardrail ARN only.
  - **R14, R15**: name and ARN form are verified. Which id goes in `<DB_RESOURCE_ID>` is not (line 194; for Aurora it is the cluster resource id per the archived copy).
  - **"Free" line for `k8s.rules_review`**: true only in a default cluster (line 270). Otherwise it needs `create` on a cluster-scoped resource, which the ticket's "never a ClusterRole" cannot grant.
  - **Section 3, moto row**: moto's own source header says "TODO add support for the Resource and Condition parts" (line 343). The ticket's "S3 honours action and resource" rests on the author's run alone.
  - **Not in the evidence file at all**: the AWS managed-policy names in the never table, Kubernetes `cluster-admin`/`admin`/`edit`, the Vault admin path `sys/policies/acl/<name>`, and the guardrail id grammar.
- Fully supported: R03, R04, R05, R07, R08 (including the `s3:prefix` key), R12, R17, R18, R19, R20-R22, and all AWS action-type never names.
- V5 is answered: `kms:Sign` lists resource type `key` only, so the alias refusal in 4.6 is right.
- V3 is answered for names (`kms:SigningAlgorithm` = `ED25519_SHA_512`, `kms:MessageType` = `RAW`), but the ticket does not say whether those conditions now go into R03.

Exact text to add to 4.5 (the lead must pick; this is the smallest consistent version):
> "`verified` means: the permission NAME and the resource ARN/path FORM were found, spelled exactly so, in a vendor-owned source fetched by the evidence runner. Accepted sources: the rendered page, the vendor's documentation source repository at a pinned commit, the AWS Service Reference JSON, the botocore API model. Each grant also carries `claims_unverified: ("...",)` for anything else the row asserts (a bound, a condition value, why a `rides_on` row is needed). One test, no time dimension: a grant with `verified = None` fails unless `(kind, id)` is in `PENDING_NAMES`. Copy-ready block: only for a kind with no pending grant and empty `claims_unverified` on every grant. Slice 1 may merge with pending grants; each is listed on the page as 'not yet checked'. Expected at merge from the 2026-11-11 run: copy-ready for aws_kms, bedrock_guardrail (pending the R13 decision), vault, vault_transit, kubernetes; table only for aws_secrets_manager, s3_object_lock, bedrock, postgres iam_auth; slack R16 pending."

And to step 0:
> "Id map from the evidence file: G01,G02 = R01,R02; G03,G04 = R03,R04; G05-G08 = R05-R08; G09 = R11; G10,G11 = R12,R13; G12 = R14 and R15; G33,G34 = R16; G35 = R17; G36,G37 = R18,R19; G38-G40 = R20-R22; R09,R10 = doubt D1. Decisions fixed here, not by the builder: R03 conditions [add / do not add]; R13 guardrail-profile resource [add / state out of scope]; `k8s.rules_review` free entry gets the note 'default clusters only'."

### B2. Section 4.1 `verified = ("date", "https://...")` inside `src/` breaks an existing guard test, and the fix is not in the files list
- /home/user/build/EV-P3a2-main-2a8c2aa/tests/test_no_hardcoded_values.py:33 (`url`) and :34-38 (`host`) scan every string constant in `src/`.
- The `ALLOWED` table (:42-61) permits `url` only in `approvals/slack_channel.py`, `llm/anthropic.py`, `llm/gemini.py` and `backends/table.py`. `sources/kubernetes.py` has `host` only.
- A vendor URL in `verified` therefore fails in nine of the ten modules as soon as step 0 fills it. Section 0 says "the builder runs it after the first literal", but with `verified = None` the first literal passes and the failure arrives later.
- Adding nine `ALLOWED` entries would weaken that guard for whole modules (the repo gate says no weakened tests), and that file is not in section 7's change list.

Exact text to add to 4.1:
> "`verified` holds `("2026-11-11", "<source id>")`, never a URL. The source id is a key of the header table in `tests/fixtures/policy_sources_<date>.txt` (id, URL, commit or version, SHA-256 of the saved text). A test asserts every source id resolves. No URL or host name is added to any kind module; `tests/test_no_hardcoded_values.py` is not changed."

Also check R02's condition value `secretsmanager.{region}.amazonaws.com`. By my reading of the `host` regex it does not match, because `{` breaks the label. I did not run it; the builder runs that test after R02.

## MAJORS

### M1. Sections 4.2, 4.6 and 5: the renderer has no defined input, and several `resource` values are prose
- `for_config` is cut (section 2), yet 4.6 says "a value put into a template must fully match its grammar". Nothing says who supplies values, or the signatures of `render_aws`, `render_vault` and `render_kubernetes`.
- The page cannot hit the "empty prefix" or "alias" refusals, because R17 and R03 use operator placeholders (`<PATH_PREFIX>`, `<KEY_ID>`).
- Section 5's "on what" column is not a literal for these rows:
  - R02: "that key's ARN".
  - R09, R10: "the bucket key's ARN".
  - R11: two alternatives, "per route".
  - R16: prose.
  - R01: "one line per secret".
  - R20-R22: "each of `{namespaces}`", a tuple.
- The builder would invent security-relevant strings.

Add to 4.2:
> "`render_aws(policy: Policy, values: Mapping[str, str] | None = None) -> str` (same shape for vault and kubernetes). `values=None` is page mode: `{field}` and `<NAME>` stay as written. With `values`, every `{field}` and `<NAME>` must be present and `fullmatch` its 4.6 grammar, else `ValueError` naming the key. Only tests B and the grammar plants pass `values`. `{namespaces}` takes a comma-joined list and yields one Role and one RoleBinding per namespace."

Add to section 5 the literal `resource` string for every row, for example:
- R02: `arn:aws:kms:{region}:<ACCOUNT_ID>:key/<SECRET_KEY_ID>`.
- R11: two grants or a tuple of resources; say which and change the schema accordingly.

### M2. Sections 4.3 and 4.4 D4: the extracted pair ("local", "generate_db_auth_token") has no place in the declared set
- R14 and R15 are `no_wire`, and D4 allows exactly one of `operations`, `rides_on`, `no_wire`. So they declare no operation.
- `free` is defined as "requests that need no permission", and this is not a request.
- As written, A1 fails on store/auth_aws.py:19.

Add:
> "R14 and R15 carry `operations = (("local", "generate_db_auth_token"),)`; `no_wire` is removed from the schema and from D4; the B2 exempt list becomes R02, R06, R09, R10 plus every grant whose operations are all `local`."

### M3. Section 4.3: allowlist semantics are undefined for three of the eight lines, and `_fold` does not do what the table needs
I confirmed all eight lines exist as described:
- guard/bedrock_guardrail.py:28-29
- actions/secrets_vault.py:101, :104
- audit/signer_vault.py:40
- approvals/slack_channel.py:51
- sources/kubernetes.py:168, :184, :203

Three of them are not calls the stated rule for that module reads:
- signer_vault.py:40 is `.authed(`, but the module reads `._call(`.
- slack_channel.py:51 is `post_json(`, with the f-string on :52.
- kubernetes.py:168 is `self._fetch(`.

So "a stale entry fails" has no meaning for them.

Add:
> "An allowlist entry is (module, enclosing function, line, sink call name) and asserts: at that line, inside that function, there is a call to that sink whose operation argument is a parameter of the enclosing function. The entry is stale when no such call exists there. Sinks per module: `boto3.client`; `.call`; `.authed`; `post_json`; `._fetch`, `._call`, `._get`. A call to a sink outside an allowlisted wrapper fails."

Also, tests/test_lockin_guard.py:565-589 `_fold` returns `{}` for every formatted value, not `{mount}`. Add:
> "A new `_template(node)` in tests/test_policy_guard.py: a formatted `self.X` or `obj.X` becomes `{X}`, a bare name becomes `{name}`, anything else is not foldable. `_fold` is not reused for paths."

### M4. Sections 4.1 and 6.1: B2 exempts grants "BY ID", but the schema has no id
Add `"id": "R05"` to the 4.1 literal, unique across the ten modules (a D-rule), used by `PENDING_NAMES`, the exempt list and the page.

### M5. Section 6.1 B4 and 6.4: some controls cannot succeed, and the B plants are not defined
- B4 says the same request with the admin token "succeeds". On Vault Transit this is not true for all of them:
  - `export` on a non-exportable key is refused for admin too.
  - `DELETE keys/<name>` needs `deletion_allowed` set first.
  - Deleting or reconfiguring the fixture key breaks later tests.
- 6.4 lists "B2-B4" as "proved by its own plant" but names no plant.
- F3 fails with "no POLICY", the same reason as F1. It shows nothing about the engine.

Add:
> "B4 control = the admin token gets any status other than 403 for the same request. For export, config and delete, the fixture makes a second throwaway key with `exportable` and `deletion_allowed` set, used only by B3/B4. Plants for B: (1) policy text widened to `{mount}/data/*` makes 'read outside the prefix is refused' fail; (2) the runtime token replaced by the admin token makes every B3 test fail; (3) S3 JSON with `Resource` widened to `arn:aws:s3:::{bucket}/*` makes 'put outside anchors/ is refused' fail. F3 is dropped from the must-fail list or labelled 'fails for lack of data only'. If the build machine has no Vault server, the Vault plants are shown in CI output and the report says so."

### M6. Sections 3 and 6.3: moto facts are partly inexact, and a simpler mechanism exists in the installed source
- `set_initial_no_auth_action_count` is a decorator, not a context manager (/home/user/build/venv-p89/lib/python3.13/site-packages/moto/core/authorization.py:82-126). The ticket's "inside `mock_aws()` ... with `set_initial_no_auth_action_count(n)`" reads as a `with` block.
- `moto.core.enable_iam_authentication()` IS a context manager (authorization.py:129-141, exported at moto/core/__init__.py:5). It sets the count to 0, so set-up can run before the `with` and enforcement starts at the first call inside. That removes the call-counting and the off-by-one class. Not run by me.
- "For every non-S3 service moto compares Resource with `*`" is too wide. responses.py:436-439 is as cited, but `_determine_resource` exists for iam, sqs and sts. It is true for secretsmanager and kms.
- access_control.py:571-575 `_match` is as cited, and the `?` error is plausible from the code.
- The named evidence /tmp/claude-0/-home-user-hadavin-sdk/3c7954a2-a1b2-5867-97dd-d4d94c9e06fd/scratchpad/spike-out.txt line 3 reads "ALLOW get one-exactarn". Section 3 says the resource-scoped Secrets Manager policy "refused even the allowed read". Either the file is the uncorrected first run or the sentence is wrong. Step 1 must settle it; until then 6.2's "NONE (moto cannot evaluate...)" is unproven.
- Lines 18 and 28 of that file show "ALLOW put retention bypass" under the full policy. That agrees with 6.2 listing the lock-bypass entry as not covered.

Add to 6.3:
> "Set-up (bucket, user, policy, access key) runs inside `mock_aws()` before `with enable_iam_authentication():`; all checked calls run inside it. The control test stays."

### M7. Sentences that still claim more than the tests prove
- Title: "ten backend kinds ship their smallest permission set ... and an honest negative test". Only two kinds get an engine negative test, and no test shows "smallest". Suggested: "ten backend kinds ship a declared permission set tied to the calls their code makes; two are refused by a real engine, one partly by an emulator".
- CHANGELOG (section 10): "Each kind module now carries the smallest permission set its code needs". Change to "the permission set declared for the calls its code makes; the names for [list] are not yet checked".
- 4.3: "it proves the list of CALLS is complete". It proves the calls written in that module by the listed call shapes are all declared. For vault_transit the sign-in call lives in the imported actions/secrets_vault.py and is not in that kind's list.
- 4.3 and 3: "prototype by the author ran on all ten modules". No output file for it was found in the first 100 scratchpad entries; treat as unevidenced until step 2.
- Section 5, R06 reason: delete "S3 asks for it when a put sets a lock" (NOT FOUND, see B1).
- 6.2 kubernetes column B: "in production the code asks the real cluster" belongs in the notes column. It checks read-only, not the policy.

### M8. Size and estimate
- The slice couples a mechanism (tool, guard, Vault engine tests, page) with 15 AWS rows whose verification is incomplete and one Slack row that cannot be verified from this network. Under any strict gate, the AWS and Slack rows hold the mechanism hostage.
- Recommended split:
  - PR 1: `tools/policy_page.py`, guard family A, B on Vault, the CI variable, and the literals for vault, vault_transit and kubernetes (all verified today).
  - PR 2: the six AWS kinds, the moto fixture, the action list, and slack.
- Estimate: "steps 2-5 about 4 hours" covers a loader, three renderers, a grammar table, a CLI, six extraction shapes, about 30 plants, about 12 mutants, two engine fixtures and a page. The Vault engine tests can only be proven in CI, so it also needs at least one push-and-wait cycle (job timeout 30 minutes). Round 1 already found 3 Blockers and 18 Majors. 14 to 18 hours for the whole slice is more honest; about 7 to 9 for PR 1 alone.
- L2 is partly met already: the Service Reference JSON files are saved under the scratchpad `dl/` folder (`sr-*.json`). Say so.

## MINORS
1. 6.3 CI: say whether `HADAVIN_REQUIRE_VAULT_ENGINE=1` also goes into the `tests-py312` job (ci.yml:150-153). It should, or that job silently skips.
2. 4.4 D2: give the module-to-settings-class map (ten rows). `KubernetesSettings` is in sources/kubernetes.py:53, the rest in backends/table.py. Without it the builder designs the lookup.
3. Section 5, kubernetes never-list: "exactly the lists the code refuses" needs a test that the literal equals `_WRITE_VERBS` and `_SHELL_RESOURCES` (kubernetes.py:36-49). The literal cannot import them.
4. 4.5 last bullet: say the action-list test applies to `aws_iam` policies only. Slack's `chat:write.public` is also type `action`.
5. Section 8 finding 3: `AwsSecretsManagerSettings.region` (table.py:146) also has no pattern. Add it.
6. 4.3 Kubernetes path-to-verb derivation: say how the test recognises a subresource in the regex path (suggested: last path segment after a `{_NS}` segment is the subresource, else the collection).
7. 6.4 mutants: decide now whether `tools/policy_page.py` goes into `extra_dirs` (tools/mutation_runner.py:370 copies `src`, tests and `extra_dirs` only).
8. R18: Vault documents an optional `/:hash_algorithm` path part on sign (evidence line 247). The exact path grant is correct for the code at signer_vault.py:52; note it on the page.

## Code facts checked and found TRUE
- Per-kind sets and lines, all ten modules opened:
  - actions/secrets_aws.py:29
  - audit/signer_aws.py:32, :41
  - audit/anchor_s3.py:55, :67, :73, :78
  - llm/bedrock.py:156
  - guard/bedrock_guardrail.py:47, :101, `_client` :28-29 with call sites :63, :66
  - actions/secrets_vault.py:115, :138 (token auth sends no login, :165-168)
  - audit/signer_vault.py:52, :62
  - approvals/slack_channel.py:124, :166, :184, :195
  - sources/kubernetes.py:232, :247, :285, :328; `READ_OPERATIONS` :27-32; `_READ_VERBS` :39; secrets check :123
  - store/auth_aws.py:19
- Vault admin/runtime split fixtures: tests/contracts/kinds/secrets_neutral.py:42-67 and audit_neutral.py:43-60 use one admin token; the S3 fixture is at :78-88.
- Other fixture lines: fake_slack.py:8, channel_slack.py:10-12, test_sources.py:55, detectors.py:55 (no `get_guardrail` in it), test_p4_secrets.py:11, warden_port/test_audit_chain.py:27, test_p7_tick.py:530-538.
- Settings and core lines: backends/table.py:247, :285, :298, :229-230, :163-164, :102; audit/signer.py:79-90; cli.py:187; app.py:86-89 and :151-160; store/postgres.py:138-146; audit/anchors.py:9.
- Guard and tooling lines: test_lockin_guard.py:27-34, :89, :336-352, :40-45, :499, :565; ci.yml:51-64 and :90-91; pyproject.toml:52; moto is 5.2.5; `tools/__init__.py` exists, so the overlay imports work.

## Resolution table sample (16 rows)
Real resolution:
- zoom-out B2, B3, M1 (with the M6 corrections above), M5, M6
- design B1 (apart from M2 above), M2, M4, M10
- design M9 is honestly marked not resolved

Mention or partial only:
- zoom-out B1: 6.1 and 6.2 are honest, but the title and CHANGELOG are not (M7).
- zoom-out M4: contradictory gate, no field for conditions, URL in `src/` (B1, B2).
- design B3: one rule, but allowlist semantics are missing (M3).
- design M3: `no_wire` collides with A1 (M2).
- design M11: the grammar table has no entry point and four grammars are "author, UNVERIFIED" (M1).
- design M12: fixture named, but source and order are open; the files already exist in the scratchpad (M8).

## Must-fail-on-main
- F1 fails by assertion for lack of data. Acceptable.
- F2 fails because a file is absent. Weak but true.
- F3 is the same reason as F1 and is skipped without a Vault server. It is not an engine proof (M5).

## Build order
Step 0 is executable now that the evidence file exists, but only after B1 defines what `verified` accepts and what happens to R16, R06, R09 and R10. As the ticket reads today, the answer to "what ships if a name stays unverified" is nothing: the gate forbids merge and no exit is given.

VERDICT: NOT READY (2 Blockers, 8 Majors, 8 Minors).

## Not checked
- No test, script or moto call was run.
- `extract.py` and `spike.py` were not opened.
- The moto S3 action mapping for PutObjectRetention and the condition handling were not traced.
- No vendor page was read; evidence-file quotes were taken as written.
- `tools.py` `fetch`, `tools/mutation_runner.py` beyond the grep at :370, `tests/stage_mutants.py` and `tools/scan_repo.py` (whether it accepts the new page and fixture) were not read.
- docs/slack-app-manifest.yaml and the Slack settings model field `channel_id` were not opened.
- The Bedrock settings model was not checked for `region`.
- The count of never entries was not checked.
- Of the rules, `least-privilege-hard-rule.md`, `class-level-fixes.md`, `verify-tests-and-evals.md`, `honest-tamper-evidence-claims.md`, `tool-ladder-before-code.md` and CLAUDE.md were read; the rung table was checked for presence only, not re-argued.

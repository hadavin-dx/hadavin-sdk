<!-- full hand-back report of sub-agent aac974fb, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

ZOOM-OUT PLAN REVIEW, round 1: ticket Q8c (rev 1 draft), read-only

Verdict in one line: do not build as written. Cut to a first slice (below). The idea (policy data beside the code, plus a guard that keeps the two equal) is sound and is the smallest thing that satisfies rule item 5 mechanically; about half of the ticket's machinery proves less than it appears to, and three statements in the ticket are contradicted by the code.

All supplied standards and rules were read, the ticket in full, the audit, test_lockin_guard.py in full. One path gap: `/home/user/build/q8a2-dryrun/main-2a8c2aa/tests/contracts/` does not exist (that tree holds only `tests/__init__.py` and `tests/test_lockin_guard.py`, and no pyproject.toml). I read the contract fakes and pyproject from `/home/user/build/EV-P3a2-main-2a8c2aa/` instead (same commit hash in its name; I could not diff the two trees, so treat that as unconfirmed).

---

## PROBLEMS

### B1. Blocker. The permission NAME is never exercised by any test on 5 of 7 platforms; the ticket's own section 0 says so, but sections 3.4, 7 and 8 then build 7 negative-test families that read as proof
Section: 0 (line 9), 3.3, 3.4 (N1-N7), 8.
What the guard and enforcer really prove: (a) every SDK or HTTP call name in a kind module is listed under some grant, and every grant lists a call that exists (G5-G7); (b) the fake refuses operations the declaration omits. Both bind `calls`/`operations` strings to code. Neither touches `action`.
What they only appear to prove: that the identity is refused what it must not do, and that the listed permission is the one the cloud checks for that call.
Scenario: replace `cloudkms.cryptoKeyVersions.useToSign` with any invented string, or map `converse` to `bedrock:Converse` instead of `bedrock:InvokeModel`. G1-G8, G10 and N1-N7 all stay green. Only G9 could notice, only on AWS, only for existence (not for "right name for this call"), and G9 is conditional on a library nobody has checked.
N4 is tautological: the enforcer is deny-by-default, so every never-list entry is refused whether or not it is on the list. It tests default deny 169 times.
Change: (1) rename the test families honestly in the ticket: "code-to-declaration equality" (G5-G7, N1-N2) and "real-engine checks" (Vault CI server, `rules_problems`, Slack manifest, moto IAM where it works, G9). (2) Drop N4 against the home-made enforcer; keep it only where a real engine answers (Vault). (3) State per platform, in the generated page and the PR text, which of the two classes of proof each kind has. Rule item 5's "negative test (the identity is denied)" is met by this ticket only for Vault; say so and record the others as open until the live run.

### B2. Blocker. The verifier/writer identity split the ticket describes cannot work with today's code, and the ticket forbids the code change that would make it work
Section: K2 (lines 102-108), K3 line 118, 3.4 N7, 10 (line 265, 269).
Evidence: `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/cli.py:184-190`: `audit verify` calls `make("signer", ...)`; `audit/signer_aws.py:55` wraps the signer in `probe`; `audit/signer.py:79-90` `probe` SIGNS a test message. So the verify process needs `kms:Sign` at start-up. Same shape for the anchor probes (`anchor_azure.py:83-85` container read at build).
Scenario: an operator follows the page, gives the verifier G04 plus G07-G08 only. `hadavin-sdk audit verify` exits "could not verify: signer aws_kms: cannot sign at start-up". The operator's fix is to grant Sign to the verifier, which is an identity that can then forge checkpoints: the opposite of the rule. N7 in the fake will either fail or be wired around `probe`, and then it proves a split the product does not have.
Change: remove N7, the "two identities" sentence and the `used_by` enforcement from this ticket. Keep `used_by` only as a descriptive label if at all. Record "audit verify signs at start-up, so a sign-free verifier is impossible today" as a finding for the F2 ticket (it needs a code change, which section 10 rules out here). The page must say one identity per process is what the code supports today.

### B3. Blocker. Copy-ready AWS JSON with an explicit Deny per kind breaks deployments, because never-lists are per kind while identities are per process (audit F2)
Section: 7 (line 248), K1/K2, K4/K5, 3.3 G4.
Scenario 1: one process, one role, config uses `llm: bedrock` and `detector: bedrock_guardrail`. K5's never-list holds `bedrock:InvokeModel`; K4 grants it. Paste both blocks: explicit Deny wins, every model call fails. Scenario 2: `kms:Decrypt` is on K2's never-list and is grant G02 of K1. Scenario 3, inside one policy: K6 grants `rds-db:connect` and K6's never-list holds "`rds-db:connect` for any other database user", so G4 ("no name is both granted and on the never-list") fails on the ticket's own data.
Also under-specified: the hostile-input rule says a rendered block holds no `"Resource": "*"`, so what resource does the Deny statement carry?
Change: no Deny statement in rendered output in this slice. The never-list is page text only. If a Deny block is wanted later it must be computed per identity from the union of that identity's kinds, which depends on F2.

### M1. Major. The rung table's moto row is wrong, and so is the AWS choke-point row; an existing dependency that evaluates real IAM policy text was dismissed
Section: 2 (line 20), 3.4 table (line 72), 5.
Evidence: `/home/user/build/EV-P3a2-main-2a8c2aa/pyproject.toml:52` pins `moto[s3,kms,secretsmanager]==5.2.5` in the test group. It is used by the contract suite for the S3 anchor (`tests/contracts/kinds/audit_neutral.py:16,80`) and for Secrets Manager (`tests/test_p4_secrets.py:11,32`). `aws_stub.py:1-2` says only that contract kinds must not patch botocore globally; it does not say "the repo chose not to use moto".
Two consequences: (a) the `enforce=` hook on `stub_client` does not sit on the S3 anchor or the boto3 Secrets Manager path, so K3 (4 grants and the highest-stakes never-list) would run un-enforced unless those fixtures are rewritten, which the files list does not mention; (b) moto's IAM enforcement mode, if it works for these calls, evaluates the real policy JSON with the real action names for K1 and K3 (G01, G05-G08). That is a real-engine check of exactly the artefact the operator copies, on a library already installed. UNVERIFIED by me: whether moto 5.2.5's enforcement covers Object Lock headers, conditions and `IfNoneMatch` (no network, no shell).
Change: correct the row. First box of the build: a 30-minute spike that applies the rendered K1 and K3 JSON to moto with IAM enforcement on. If it holds, use it for those kinds and do not write an enforcer hook for them.

### M2. Major. The "one grant, one operation" model fails for the rows the author is least sure of, so N2 and N3 cannot hold as written
Section: 3.4 N2, N3; rows G02, G06, G12, G18, G20, G29-G32, G34.
- G12 `rds-db:connect`: the ticket itself says `generate_db_auth_token` sends nothing. The enforcer never sees an operation; removing the grant fails no test.
- G02 `kms:Decrypt`: Secrets Manager calls KMS on the caller's behalf; our code sends no such request.
- G06 and G18: a second permission on the SAME request as G05/G17. Removing G06 while G05 stays leaves the operation allowed.
- G20/G19 and G34/G33: same permission, two operations (fine for N3, but N2's "no unused grant" then counts rows, not permissions).
- G29-G32: no permission at all.
Of the 11 M and L rows, 9 are in this list. The tests are strongest where the names are safest and silent where they are not.
Change: add to the ticket a column "testable by enforcer: yes / no, why". Rows marked no are exempt from N2/N3 by name and carry a mandatory verified date and URL before merge instead.

### M3. Major. Scope: 19 kinds, 10 guard rules, a 7-family enforcer, three renderers and four new types in one pull request, with 209 unverified items, on an uncapped-review security path
Section: whole ticket; 11 question 3; 9 estimate.
YAGNI items with no consumer in this ticket:
- `for_config(entries)`: its command is out of scope (line 248, 270). Nothing calls it.
- `Grant.target` and N5: the author himself asks whether it is worth its size (11.2). Operation level first.
- `used_by` enforcement and N7 (see B2).
- `Entry.policy` plus `SourceKind.policy` plus three dataclasses in `backends/table.py`: production types that no production code reads ("No production behaviour changes"). The reference is derivable (the factory module, with `store/auth_aws` as the one named exception that `VENDOR_HELPERS` already records at test_lockin_guard.py:86).
- K13-K15 (anthropic api/foundry, gemini, openai_compat): 5 rows that say "no role", never-lists that are prose advice. Forcing them through `Grant(action=...)` invents a schema for something that is a paragraph.
- 169 never-list entries: under deny-by-default a never-list adds no protection. Its real use is naming the built-in roles and the two or three permissions that undo the kind's guarantee (for example `s3:BypassGovernanceRetention`, `storage.buckets.update`). At 9 per kind it is mostly a verification burden.
Change: see the slice in the recommendation.

### M4. Major. Shipping unverified names: the ticket has no mechanism, only an instruction
Section: 0 line 7, 6, 11.
"The builder or lead checks each name ... BEFORE the build starts" leaves no trace the reviewer can audit, and the author's first draft already contained invented counts.
Change, to be written into the ticket:
1. Who: a separate verifier agent with network access (not the author, not the builder), briefed like an evidence runner: it fetches and saves raw page text, it does not judge. The lead reads the result.
2. Against which pages (vendor's own only, named by type because I could not open any): AWS Service Authorization Reference page per service (actions, resource types, condition keys: these three are separate columns to check, the 9 or so condition keys in section 6 are not counted in the 209); Azure resource-provider operations page and built-in roles page; Google Cloud IAM permissions reference and the role pages; Vault/OpenBao policy and Transit API docs; Slack scopes reference; Kubernetes RBAC reference.
3. How a name is marked: each grant and each never entry carries `verified = (date, url)` or `None`, in the data, not in the ticket prose. In the ticket table add two columns, "verified on" and "page".
4. What the guard does with `None`: reuse the `Pending` pattern already in test_lockin_guard.py:26-33 (reason, fix_ref, decided, review_by; stale and overdue entries fail). An unverified name (a) is listed in a dated pending list or the guard fails, (b) is never rendered into a copy-ready block, (c) appears on the page under a line "NOT CONFIRMED against vendor documentation". A kind with any unverified grant gets no copy-ready block at all.
5. Merge rule: zero unverified GRANT names at merge for the kinds in the slice. L rows (G17, G18, G32) and the Azure GOVERNANCE question (line 165) are settled before their kinds enter any slice.
6. "Verified against documentation" and "confirmed on a real account" are two different states with two different fields; the page shows both.

### M5. Major. Reference-plus-`ast.literal_eval` versus inline TABLE: the stated reason holds, but a simpler third option was not considered, and `backends/policy.py` itself will trip the lock-in guard
Section: 3.2.
Checked: the claim is true. `PATTERNS["bare vendor name"]` (test_lockin_guard.py:520-521) matches strings starting `kms:`, `s3:`, `bedrock:`; "ARN" matches `arn:aws`; kind modules for AWS, Azure, Google, Slack, Gemini are in `VENDOR_MODULES` and are skipped. Inline in TABLE also passes (`_skipped_table_nodes`, :552-562) but adds about 250 lines to a 605-line module that config imports. So literal-in-kind-module beats inline. Agreed.
Not considered: (a) `secrets_vault`, `signer_vault`, `openai_compat` and `sources/kubernetes` are NOT in `VENDOR_MODULES`, so their `POLICY` literals are scanned by rule c. I see no pattern they would hit today, but the ticket should say it checked. (b) `backends/policy.py` is declared neutral, yet it must hold the platform set including the exact string `"slack"`, which matches `^(slack|...)(:|$)`, and it holds an AWS IAM JSON renderer, a Vault policy renderer and a Kubernetes Role renderer. That is vendor-specific logic in a neutral module; the ticket's "only if backends/policy.py needs listing" quietly anticipates adding it to `VENDOR_MODULES`, which would switch rule c off for the whole module. (c) If the loader, renderer and types have no production reader, they belong under `tests/` or a docs script, where rule c does not scan, and no `src` module changes besides the 10-19 `POLICY` literals.
Change: keep `POLICY` literals in kind modules. Move load/render/types out of `src/` (or justify a production reader). Do not add a renderer module to `VENDOR_MODULES`.

### M6. Major. G6 is name-based and install-dependent
Section: 3.3 G6.
"Every method call whose name is an API method of the SDK client" matches on attribute name, not on receiver. `sign`, `get_key`, `reload` are common names; a call made through a helper, `getattr`, or a paginator string (`get_paginator("list_objects_v2")`, anchor_s3.py:73, which is on the proposed allowlist of "methods that send nothing" although it is the list call) is outside it. For Azure and Google it needs the extras and "CI must fail if skipped", which is a new CI contract not in the files list.
Change: state the bound in the ticket ("G6 catches a new direct SDK method call by name in the kind module; it does not catch indirect calls"). Treat `get_paginator` by its string argument, not as allowlisted.

### m1. Minor. Over-stated claims (question 6), each with the fix
- Title and line 13 "a negative test": true only for Vault in CI (B1).
- K3 line 118 and K9: "the writer cannot delete". G06/G18 are the retention-setting permissions; line 165 admits G18 may also remove an Unlocked policy. Until settled the page must not claim the writer cannot undo its own lock on Azure GOVERNANCE (`anchor_azure.py:4-5` already says a privileged admin can shorten it). Per honest-tamper-evidence-claims: name the bound.
- Line 243 "The never-list is the list the code already refuses at start-up": `watch` is in `_READ_VERBS` and is not refused (kubernetes.py:39, 116-124), and "any ClusterRoleBinding" cannot be seen by a namespaced rules review. Two of 11 entries are not refused by code.
- G2 "`*` in resource only with a non-empty condition": `condition` is free text, so G2 proves a sentence exists, not that a bound exists. G35 with empty `path_prefix` is the whole mount with a sentence beside it. Rename to "a recorded reason", and for G35 make the renderer refuse an empty prefix outside demo or print the warning as the first line.
- G13: "one assignment per secret" and G21 "bound on the single secret": the code reads any name the caller asks for (secrets_aws.py:29 shape); the narrowness is the operator's work, not something the kind achieves.
- G30/K13 Foundry: a resource-wide key is not least privilege; the row must say "not least privilege, accepted or not by the owner (11.6)", not sit in a table of minimum policies.
- Line 24 "it keeps code and declared policy equal": equal at call-name level only (B1, M6).
- Line 20 "the repo already chose not to use moto": false (M1).

### m2. Minor. Fail-on-main proofs F1-F4 are attribute-missing failures; they prove the feature is absent, nothing about the guard. Fine as a formality; the plants carry the weight. Say so.

### m3. Minor. Altitude. Sections 3.1 and 3.4 fix field names, refusal payloads and helper names before the two structural questions (where the types live; whether a real engine can replace the enforcer) are answered. Move those to the build after the spike in M1.

---

## Question 5: recount (by hand over the ticket text, using the ticket's own rule; I have no shell, so no command was run)
- Grant rows matching `^\| G[0-9]{2} `: G01 to G40, no gaps, no duplicates = 40. HOLDS.
- Confidence: H 29, M 8 (G02, G06, G16, G20, G28, G29, G30, G31), L 3 (G17, G18, G32). HOLDS.
- "free" rows: 3 (K17, K18, K19). HOLDS.
- `NEVER` lines: 19. `; `-separated items per kind K1..K19: 10, 13, 11, 8, 6, 7, 10, 11, 12, 8, 8, 10, 9, 3, 2, 11, 9, 10, 11 = 169. HOLDS. 40 + 169 = 209. HOLDS.
- What the number is not: it is not 209 permission names. About 17 never items are prose rules with no vendor name (all of K14 and K15, K6's first, K13's last two, K16 "any user token scope", K17 "the root policy" and "auth/* beyond the sign-in", K19's last two). Three items bundle several names (K17 item 1: 5 capabilities; K18 item 1: 3; K19 item 1: 8 verbs). Four grant rows carry no permission (G29-G32). G20 repeats G19 and G34 repeats G33. Not counted at all and equally unverified: about 9 condition keys, every ARN and scope format, and about 8 built-in role names in rows and notes. Line 7 says "items", which is accurate; any sentence saying "209 permission names" is not.

## Questions 1-4 in short
1. Code or document: data plus a small guard, yes; a reviewed document alone drifts on the first new API call and cannot fail a pull request. The custom enforcer mostly no (B1, M1, M2).
2. Scope: cut (M3).
3. Literal in kind module: yes over inline TABLE; but keep loader/renderer/types out of `src/` (M5).
4. Process: M4.

---

## RECOMMENDATION: cut to slice 1, then decide slice 2 on evidence
Before any build: the live verification pass (M4) for the slice-1 kinds, and the moto IAM spike (M1).

Slice 1 (10 kinds, 20 grant rows, 96 never items before trimming): Vault secrets and Vault Transit (K17, K18), Kubernetes (K19), Slack (K16), the six AWS kinds (K1-K6).
Why these: each has a check that is not our own fake agreeing with itself. Vault: the real server in CI enforces the real policy text. Kubernetes: `rules_problems` already exists. Slack: the manifest already exists. AWS: an offline action list may exist (G9), moto is installed, Access Analyzer exists for the live run; it is also 12 of the 40 rows and the only platform with a testable native format.
Contents: `POLICY` literal per kind module; guard G1 (with a dated pending list naming the 9 kinds not yet done, so it cannot linger), G2-G5, G7, G6 for AWS only, G8, G9 if the library passes, G10; the verified/pending mechanism; the page with copy-ready blocks only for fully verified kinds and no Deny statements; never-lists trimmed to the built-in roles and the few permissions that undo the kind's guarantee.
Not in slice 1: `target`/N5, `used_by` enforcement/N7, N4 on fakes, `for_config`, `Entry.policy` and types in `table.py`, the enforcer hooks in `http_fake.py`, Azure and Google kinds.
Slice 2: Azure and Google (K7-K12, 15 rows, all three L-or-unresolved Azure blob questions), only after their names are verified and owner question 11.5 is answered. K13-K15: a short page section of key-hygiene rules, not `Grant` data.

## NOT CHECKED
- No permission name, condition key, ARN format or role name was checked against any vendor page (no network tool). I make no claim that any name in section 6 is right or wrong.
- Counts were done by hand, not by running the ticket's grep.
- Not run: any test. Not verified: that moto's IAM enforcement covers the S3 Object Lock or Secrets Manager calls used here; that `parliament` or `policy_sentry` is maintained.
- `tests/contracts/` at the supplied path does not exist; I read `aws_stub.py` in full and only the function list of `http_fake.py` from `/home/user/build/EV-P3a2-main-2a8c2aa/`, and did not read `vault_fake.py`, `sources.py`, `kinds/*.py`, `conftest.py` or `.github/workflows/ci.yml`. The ticket's choke-point claims for Azure, Google, Vault, Slack and Kubernetes are therefore unchecked.
- Kind modules read in full: `signer_aws.py`, `anchor_s3.py`, `secrets_aws.py`, `anchor_azure.py`, `signer.py`; partly: `bedrock.py`, `kubernetes.py` (to line 130), `cli.py` (168-207), `table.py` and `sources/kinds.py` in full. Line references in section 6 were spot-checked for K1, K2, K3, K9 and K19 only (all matched). Not read: the Google, Azure secrets/signer, Vault, Slack, Gemini, OpenAI-compatible, guardrail, `auth_aws`, `postgres` and `anthropic` modules, `factory.py`, `chain.py` beyond a grep, the migrations.
- `handover/README.md`, `STUDIO-RULES.md`, `STATUS.md`, the ledger and bible rules R365/R447/R450 were not supplied and not read.
- Whether IAM rejects a policy containing an unknown action name: not established.

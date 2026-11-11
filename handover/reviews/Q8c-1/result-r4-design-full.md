Q8c-1 | head be5313711305f417021a374465acc967b01f68e7 | round 4 (delta of fix batch 3, snapshot q8c1f3-be531371) | persona: design critic (least privilege)
Static read only. I ran no test, mutant or plant. I read the ticket, the r3 resolve report, both r3 result reports, the builder b2 report, and the snapshot (the three kind modules, policy_page.py, the test files, the mutants, the page, the fixture header).

VERDICT: no Blocker, no Major. Five minor findings, one open evidence gate. All seven batch-3 items are present in the snapshot and do what the report says. Three grants are broader than their stated reason and the page does not say so (finding 1).

## Batch 3, item by item
1. Builder-only marks. DONE.
   - `_checked_cell` (tools/policy_page.py:925-931) appends "(builder only)" to V-ACL, V-PARSE and B-ACL.
   - It serves grants, free entries and never entries (:953, :960, :973).
   - The docs page :88 shows the marks, and the page head explains them (:44).
   - The test at test_policy_guard.py:1583-1594 checks the whole generated page with a negative-lookahead regex, and a mutant covers it (policy_mutants.py:466-473).
   - Weakness: the three ids are a hand-written constant (policy_page.py:922). Nothing ties it to the fixture header, which lists what the builder alone read (fixture :26-36). See finding 3.
2. Dated claim entries R17, R18, R20, R21, R22, review by 2026-12-11. DONE.
   - PENDING_CLAIMS (test_policy_guard.py:119-125) holds exactly those five.
   - `claim_problems` (:1512-1522) fails on a claim with no entry, on a stale entry, and when overdue.
   - Tests at :1525-1543 and the mutant at policy_mutants.py:474-481 pin it.
   - The three unverified never paths (undelete, subkeys, byok-export) also have dated entries (:99-106).
   - The 92-day cap (:40, :145) is enforced inside the same test file where DECIDED is a constant. A person can move both. It is a reminder, not a gate. Nit only.
3. Never-versus-grant check and its mutants. DONE for the shapes in use.
   - Rule: `never_covers_grant_problems` (policy_page.py:714-740), called from `cross_problems` (:693).
   - Vault: a path overlap counts only when the never line's capabilities include the grant's capability (a line with none counts as all).
   - Kubernetes: a never `resource` that a grant names.
   - I redid the manual cross-check from r3 against the data. R17 `read` on `data/{prefix}+` against never `data/*` with create, update, patch and delete: no clash. R19 `read` against never `keys/{key}` with `delete` only: no clash. No other overlap.
   - Plants at test_policy_guard.py:2862-2928 include a narrower never path, a wider one, no capabilities, and a differing capability. The mutants at policy_mutants.py:416-457 drop each half of the overlap test, the capability filter, the Kubernetes clause and the call from `cross_problems`. Each has its own killer, and the killers use plain asserts with their own messages, not the weak `same()`.
   - Limits, see finding 4.
4. "Page equals data". Present and correct as a test (:1769-1775 plus :1797-1803). It is self-referential by design: the page is generated from the data and compared with the committed file. It cannot say the data is right. The head's "What the tests show" section says so honestly (docs page :30-35, :60-61).
   - I compared the committed docs/declared-permissions.md head and the R17 and R18 sections with `_HEAD` and `_kind_section`. They match.
   - I could not run `--check`.
5. R18 and Kubernetes claims added to claims_unverified. DONE.
   - R18: signer_vault.py:147-152. Kubernetes R20 to R22: kubernetes.py:405-435.
   - A new NOTE_CLASSES test (test_policy_guard.py:2936-3043) forces every note to be code, sources or claim, and a claim note must match a `claims_unverified` text. Three mutants cover it (policy_mutants.py:482-507).
   - Consequence: none of the three kinds gets copy-ready text. `copy_ready` is {False, False, False} (:1560-1567, policy_page.py:908-913). This is the honest result.
6. Credential text of the Kubernetes source. Fixed (kubernetes.py:363-368). It now says what the code does: a bearer token from the secret named by `token_secret_name`, only when that setting is set.
7. Page head and CHANGELOG on abbreviated ids, and the row count. Fixed.
   - Head :32-34 (docs) says seven abbreviated ids and the OpenBao release not looked up. A test checks the head against the fixture (test_policy_guard.py:2774-2784).
   - The brittle `== 19` is replaced by a comparison with the fixture header count and its listed rows (:2744-2771).
   - The allowlist hint now says to move the line in SHAPES, with a mutant (policy_mutants.py:508-516).

## Findings

### [F1] Minor - three Kubernetes grants and R17 are broader than their stated reason, and the "what limits a wildcard" column says "no wildcard"
Where: kubernetes.py:394-436 (R20 to R22); docs page lines 169-171; policy_page.py:951.
What: the stated reasons are narrower than what Kubernetes RBAC grants.
- R22 says "reads one pod's log lines". `get` on `pods/log` covers every pod in every configured namespace. Pod logs often hold secrets.
- R21 says "reads events in the time window". RBAC cannot restrict time, so it is all events in the namespace.
- R20 says "rollout revision and images". `list deployments` returns whole Deployment objects, including any env values in the pod template.
- The bound column prints "no wildcard" for all three, which reads as "exactly what the reason says".
- R17 is stated honestly (a one-segment bound), but it also reads every version of the secret (the `?version=` read is covered by `read` on the data path). The reason says "one named secret".
Why it matters: an operator sees "one pod's log lines" and "no wildcard" and approves it, but the identity can read every pod's log in the namespace. The page says "least privilege" for these rows, so the gap sits in the one column an approver reads.
Suggested fix: put the breadth in the `bound` text (for example "every pod's log in each namespace; RBAC cannot narrow this by time or by pod; the code asks for one"), and say that the log and event content is outside this kind's control. Keep the claim text unchanged.

### [F2] Minor - the R18 hash-suffix claim has no engine test that could ever settle it
Where: signer_vault.py:117-121 and :147-152; tests/test_policy_engine.py (B3 requests, around :380-440).
What: the claim is that the exact path `{transit_mount}/sign/{key_name}` does not also allow the longer `sign/{key}/<hash>` path. Once the Vault engine tests run, they still never send `sign/{key}/sha2-256`. grep finds no `sha2` or `hash` in the engine tests. The claim therefore stays "nobody has checked" even after a green CI run. The fixture header (:35-36) says an evidence runner should read it, but a read of the docs is weaker than one refused request.
Suggested fix: add `sign/{key}/sha2-256` as a B3 request (expect 403) with the admin control. Then the claim can be removed with a tested reason.

### [F3] Minor - builder-only marking is a hand list, and V-POL, B-POL, V-KV, B-KV, V-TR, B-TR are not marked
Where: policy_page.py:922; fixture header :29-39; docs page :88 and :128.
What: the fixture header says parts of V-POL and B-POL (the `+` passage), V-KV and B-KV (undelete, subkeys) and V-TR and B-TR (the hash-suffix claim) were read by the builder only. The cell for R17 lists V-POL and B-POL unmarked, and the R18 cell lists V-TR and B-TR unmarked. The claims column carries the unchecked statements, so nothing false is shown as checked. But a reader of the "found in a vendor source" cell alone sees seven or four clean ids. Nothing ties BUILDER_ONLY_SOURCES to the fixture header, so a new builder-only id would show unmarked with no test failure.
Suggested fix: either cell-level wording ("partly builder only: see claims") or a test that reads the fixture header list. Low priority because copy-ready text is withheld.

### [F4] Minor - the never-versus-grant check can miss an overlap, and it is per kind only
Where: policy_page.py:697-740.
What:
- The overlap test uses one sample path per side, so it can miss an overlap when both sides hold a wildcard in different places. Example: never `{mount}/+/{path_prefix}foo` against R17 `{mount}/data/{path_prefix}+`. Neither sample matches the other pattern, yet `data/<prefix>foo` is covered by both. No such never line exists now, so there is no live defect.
- The check is per kind. `_vault_form` turns `{mount}` and `{transit_mount}` into different tokens, so a deployment that runs both Vault kinds on one mount name is not compared. This matches the ticket's "one process holds several kinds" concern only partly.
Suggested fix: write the limit into the docstring (it says "checked both ways with one sample path each"). Optionally add a plant that documents the miss, or compare by real overlap of the two glob patterns.

### [F5] Nit - a Kubernetes never entry carries an unchecked claim in its own reason, with `verified` set
Where: kubernetes.py:471-482 (`create` never entry); the NOTE_CLASSES test covers notes and free notes only.
What: the reason text says "That these three requests write nothing was not found in a vendor source". That is honest, but the row's cell shows "2026-11-11, sources K-AUTHZ" and nothing in the data marks it as a claim.
Suggested fix: move it to a note classed "claim", or extend the note test to never reasons.

## Checked and found fine
- R17 `+` claim: unverified, withheld from copy-ready, dated, and visible in the claims column (docs page :88).
- Vault never-paths against R17, R18 and R19, and the Kubernetes never lists against R20 to R22: no overlap, by my own reading.
- Copy-ready decision for all three kinds: off while any claim is unchecked. A plant covers each way it could come on (test_policy_guard.py:1643-1663).
- Pending dates: the 16 pending kinds, the 3 builder-only never paths, the 3 role names and the 5 claims all go red after 2026-12-11. The overdue plant asserts 7 for kinds because the other 9 run to 2027-01-31 (:44-65, :233).
- No new permission was added. Grants R17 to R22 are unchanged in name and resource form in this batch.
- CI: HADAVIN_REQUIRE_VAULT_ENGINE=1 beside the address in both Vault jobs is tested (test_policy_engine.py:86-100).
- The engine tests would exercise the R17 depth limit (a read two levels below the prefix is a refusal request, :217, :236).

## Vault engine tests: what stays unverified (not run here, no binary)
- No request was ever seen refused or allowed by a real Vault server. ENGINE_RUN is None and the page says "have not run yet".
- The admin-control status codes were written from documentation (test_policy_engine.py:16). The fixture calls (`sys/policies/acl`, `auth/token/create` with `no_default_policy`) are unseen.
- Unproven until a run: R17 `+` matches exactly one part and nothing deeper; the generated HCL parses; `no_default_policy` removes the default policy; the transit never-requests (export, config, key delete) are refused.
- R18's hash-suffix claim stays unverified even after a run (F2). Policy text from a sign-in role (AppRole or Kubernetes) is not exercised at all.
- OpenBao is never run. Hashes for V-ACL, V-PARSE and B-ACL come from one fetch by one builder.
- Gate unchanged from r3: one CI run on the final head with `-rs` showing 12 passed, 0 skipped. After that, set ENGINE_RUN and edit the pinned page test in the same commit, then have an evidence runner re-read the listed sources.

## Not checked
- Whether the committed page is byte-equal to `--check` (not run).
- Mutant counts and weak-killer counts at this head.
- The full policy_page.py and test_policy_guard.py outside the ranges quoted. I did not read tests/test_policy_docs.py or the CHANGELOG batch-3 text.
- No vendor source was re-fetched.
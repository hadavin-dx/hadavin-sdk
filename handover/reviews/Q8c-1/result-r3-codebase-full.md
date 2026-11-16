<!-- full hand-back report of sub-agent a052087c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW round 3 (delta), Q8c-1, head 6bdfadc1. Static read only; I could not run anything (no shell tool). Snapshot: /home/user/build/snap/q8c1-6bdfadc1/

VERDICT: READY at review level. 0 Blocker, 0 new Major, 1 carried Major that is a process gate, 8 minor.
The carried Major is round-2 Major 1: the 12 Vault server tests have still never been seen to run. I did not re-open it as a code defect. It must stay a merge gate: one CI run on the final head that shows 12 passed and 0 skipped.

Evidence for this head: /home/user/hadavin-sdk/handover/evidence/Q8c-1/6bdfadc1/ does not exist yet. The newest evidence is a77fab7, so nothing run at 6bdfadc1 is on record. Mutant counts, gates and plants at this head are unconfirmed by me. The CI step for the policy mutants and HADAVIN_REQUIRE_VAULT_ENGINE=1 are in both Vault jobs (.github/workflows/ci.yml:91, :97, :156).

## Round-2 findings, checked in the code

- **Design Major 2 / codebase Major 1 (R17 `+` claim shown as verified): CLOSED.**
  - src/hadavin_sdk/actions/secrets_vault.py:256 sets `claims_unverified = ("the + matches exactly one whole path part, nothing deeper",)`.
  - tools/policy_page.py:853-858 `copy_ready` requires `verified` set and no claims on every grant.
  - tools/policy_page.py:923-942 prints "No copy-ready text" instead of the block.
  - tools/policy_page.py:882 and :891 render the claims column, with "none" when empty.
  - The page head (:984-988) and the CHANGELOG (:231-238) say it.
  - The three builder-only never-paths (`undelete`, `subkeys`, `byok-export`) have `verified = None` (secrets_vault.py:300, :306; signer_vault.py:198) and dated `_BUILDER_ONLY` entries (test_policy_guard.py:100-102). The page shows "not yet checked" for them.
  - The claim reaches the only rendering paths: the table row and the copy-ready decision. There is no other renderer.
  - Tests: test_policy_guard.py:1490-1518 checks the page section has no fence, shows the claim cell, and `copy_ready` is {False, True, True}. :1567-1584 plants a claim and an unverified grant on the transit kind.
  - Mutant "E2 copy-ready text is offered…" (policy_mutants.py:192-199) is killed by that plant. The killer has a hand-written assertion message and no `same()`, so it is not weak.
- **Round-2 minors, by reading:**
  - Secret-name characters: closed. A parametrized test now covers `% ? # + * space \n %2F`, `+` and `*` (:2343-2357).
  - Bare Kubernetes `watch` in the query: closed. `QUERY_NAME` is `[?&]([A-Za-z_]\w*)(?==|&|$)` (:362), with a test at :2096 and a mutant.
  - Second send in `call`, and `.call` in other modules: closed. These have plants and mutants (:2187, :2226; policy_mutants.py:64, :88).
  - The setting-to-attribute map through `build`: closed (:2169, :2180).
  - "first part is" wording: closed (policy_page.py:996).
  - A plain-words sentence on `update` for signing: closed (signer_vault.py:122, page head :1013).
  - Ledger rows BL-core-q8c1-lifetime and BL-core-q8c1-openbao exist (handover/ledger.md:2680-2681).
  - `page(root=None)` is fixed (policy_page.py:1021).
  - Allowlist hint: the message at test_policy_guard.py:909 still does not say to move the line in SHAPES. That is the old Minor 5, unchanged.

## Your specific questions

1. **Are the named mutant killers real, or only via a weak `same()`?**
   - `same()` (test_policy_guard.py:161) is a full `==` assertion, so the tests do fail when the guarded behaviour is removed.
   - Only the mutant runner's "first failing line holds `expect`" check is weak for killers that call `same()`. The `expect` string is a fragment of the expected text, so any failing `same()` in that test counts as killed.
   - policy_mutants.py:10-14 and :455-458 say this honestly, and the run prints how many mutants are weak.
   - Examples of weak killers: the A1 "no grant", "request gone" and "stale allowlist" mutants; the A4 unverified-grant and source-id mutants; the D1, D2, D3, D5, D6 and D7 mutants.
   - Examples with their own message, so not weak: the E2 copy-ready mutant, the Vault-capability mutant (killer at :2811 uses `same`, so it is weak despite the name), and the E5 grammar mutant killed only through the empty-prefix test (`DID NOT RAISE`).
   - Two mutants share the killer `test_plant_p09a_…` (policy_mutants.py:277, :285).
   - Minor: a partial revert of the E2 line (dropping only `not g.claims_unverified`) is not itself a mutant. The plant loop at :1570 would still catch it.
2. **Do `claims_unverified` entries reach every rendered page and copy-ready block?** Yes, as above. Only R17 carries one, and test :1496 pins that.
3. **Siblings of the round-2 bug class (a claim shown as verified with no source and date), all minor:**
   - Kubernetes grants R20-R22 carry a date plus sources (K-AUTHZ, K-SRC, K-RBAC), so they are not the same defect.
   - R18 note, signer_vault.py:118-120: "R18 is the exact path without [the hash suffix], so that longer form is not allowed". This is a Vault ACL matching claim with no `claims_unverified` and no source for it. R18's `verified` (V-TR, B-TR, V-POL) is documentation only, not the matching code (V-ACL). It is the same kind of claim as `+`, but R18 still gets a copy-ready block. The refusal test is among the unrun engine tests. Suggested fix: add it to R18's `claims_unverified`, or cite the source.
   - Kubernetes note, kubernetes.py:385-389: "None of them [limit, continue, timestamps, sinceTime, limitBytes] changes the verb the request needs". There is no source and no `claims_unverified`, and it sits on a kind that gets a copy-ready block. Fix: add it to the unverified claims.
   - kubernetes.py:464-469: "`create` on the self-review resources writes nothing". The entry cites only K-AUTHZ, not K-SSRR.
   - Kubernetes credential text, kubernetes.py:363-365: "The ServiceAccount token that the tool's fetch attaches". The token is attached at src/hadavin_sdk/app.py:340, only when `token_secret_name` is set, and it comes from the secrets backend as any named secret. Nothing says it is a ServiceAccount token, and with no token the request goes unauthenticated. The wording says more than the code does. Also `fetch` is in app.py, not tools.py.
   - The R17 page cell still lists V-ACL, V-PARSE and B-ACL under "name and form found in a vendor source" (`_checked_cell`, policy_page.py:865-868). Those three rows are builder-only. The adjacent "claims not checked" column mitigates this, but the head's "name and form found" and R17's `+` form contradict each other.
   - `copy_ready` ignores unverified `free` and `never` entries. This follows the ticket's E2, which speaks only of grants. The Kubernetes block is offered while three role names are unverified; the block does not contain them. This is acceptable.
   - No other kind's policy data was checked, because PR 1 declares only three kinds.
4. **The 7-character source ids in the 7 Vault documentation rows.**
   - They are honestly marked in the fixture header (policy_sources_2026-11-11.txt:18-21): the 40-character id could not be looked up and was not guessed.
   - `source_ids` accepts `[0-9a-f]{7,40}` with the id present in the URL (policy_page.py:626).
   - The test at test_policy_guard.py:2664-2668 only checks `/blob/{commit}/` is in the URL and that there are 19 rows. No test or tool re-hashes anything (header :37). The hashes are a record for a person.
   - Whether each 7-character id resolves on GitHub, and whether the hashes match, I did not verify.
   - The page head (policy_page.py:981-982) and the CHANGELOG (:244-245) say "every row pinned to a commit" and do not mention the 7 abbreviated ids or the unpinned OpenBao release. That is slightly overstated in the operator-facing text. Add one sentence to the page head.
   - The 3 hashes for V-ACL, V-PARSE and B-ACL were produced by one builder only (header :16-17).
   - `len(rows) == 19` at :2666 breaks on any new source row.
5. **Tautologies, where a test pins the same literal as the code (all minor, mostly deliberate pins):**
   - test_policy_guard.py:1487-1496: `R17_CLAIM` repeats the data string. It guards against relabelling, but changing both together passes silently.
   - :1504 hard-codes the `copy_ready` dict per kind, and :1702 pins `count("```hcl") == 1`. These are state pins, not behaviour tests. The behaviour tests are the plants at :1567 and :1499-1518.
   - :1214 and :1200-1206 compare the never-list and operations with the code's own `_WRITE_VERBS`, `_SHELL_RESOURCES` and `READ_OPERATIONS`. This is intended and is not a tautology.

## Other minors
- Carried and unchanged: the suite goes red by date on 2026-12-12 (`PENDING_KINDS` and `_BUILDER_ONLY` / `_ROLE_NAMES` review_by dates). This is stated in the CHANGELOG (:249-251).
- `ENGINE_RUN` is a hand-set constant that nothing ties to a real run. test_policy_docs.py asserts it is `None`, so recording the first run means editing the test in the same commit.
- Engine-test admin-control statuses and fixture signatures are still unseen (test_policy_engine.py header). This is the same risk as the carried Major.

## Not checked
I did not run any test, mutant or plant. I did not read tests/test_policy_engine.py in full, tests/test_no_hardcoded_values.py, or Vault's actual `+` semantics. I did not re-fetch any vendor source. I did not check the builder's summaries, as instructed.

Merge gate: keep the 12-engine-test CI run as a required step before ENGINE_RUN is set. Before the evidence runner finishes, add the R18 hash-suffix claim and the Kubernetes query-parameter claim to `claims_unverified` (or cite a source), and soften the Kubernetes credential wording.

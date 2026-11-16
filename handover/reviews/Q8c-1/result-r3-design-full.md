<!-- full hand-back report of sub-agent aec2bc5f, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW Q8c-1, round 3 (delta), head 6bdfadc1. Design critic. Read-only; I ran nothing. Static reading of the snapshot /home/user/build/snap/q8c1-6bdfadc1/.

VERDICT: READY on the code and docs delta (0 Blocker, 0 Major from this delta, 5 minor). One carried gate stays open: there is still no run of the 12 Vault server tests on record (carried round-2 item; see "Evidence state" below).

Evidence state: /home/user/hadavin-sdk/handover/evidence/Q8c-1/6bdfadc1/ does not exist, so there is no EVIDENCE-REPORT.md for this head. I reviewed the code and docs alone. The newest evidence on disk is a77fab7. I can't confirm from any run that the tests pass at this head, that the mutants are green, or that the generated page is byte-equal to `--check` output. I read the page against `tools/policy_page.py`, and its generated parts match `_HEAD` and `_kind_section`.

## Round-2 findings: closed or not

- **Round-2 Major, R17 `+` claim shown as verified: CLOSED.**
  - `secrets_vault.py:256` now sets `claims_unverified = ("the + matches exactly one whole path part, nothing deeper",)`.
  - `copy_ready` (`tools/policy_page.py:853-858`) requires `verified is not None` and no `claims_unverified` on every grant. So the Vault secrets kind gets no block.
  - The page (`docs/declared-permissions.md:80`, `:105`) shows the claim in the "claims not checked" column. It prints "No copy-ready text" and has no code fence in that section.
  - Tests pin this. `test_policy_guard.py:1490-1496` pins R17's claim and requires every other grant to carry none. `:1499-1518` pins `copy_ready` per kind (vault False, transit True, kubernetes True), the absence of a fence in the vault section, and the claim text in the table. `:1567-1584` plants a block that appears for a kind with an unchecked grant or claim.
  - I found no other route that shows R17 text. `main` (`policy_page.py:1043`) only has `--write` and `--check`. `render_vault(values)` is callable but only the engine tests call it.
  - Page head (`:34-38`, generated from `policy_page.py:984-988`), CHANGELOG (`:231-238`) and the fixture header (`policy_sources...txt:8-10`, `:26-37`) all say it plainly.
- **Round-2 design Minor 6 (reserved-value wording): closed.** The page now says "first part is ... (so `sysdata` is accepted)".
- **Round-2 design Minor 7 (plain words): closed.** There is a legend (`page:55-62`), a sentence that `update` for signing stores nothing (`:63-65`, and the transit note), and a note that verify needs R18 (`:66-67`).
- **Round-2 design Minors 4 and 5 (the setting-to-request link, and the body of `call`): closed as disclosure.** Both are now stated on the page (`:39-44`).
- **Not re-checked by me:** codebase round-2 Minors 1-3 and 5-10 (the `_items` query-name regex, `.call` callers, fixture hashes, allowlist hint, date-red, test_policy_docs brittleness, mutant vacuity, U+00A0 in a test literal, the `root` default argument). They are outside this delta's question. I did not verify them as closed or open.

## Questions asked

**1. Could any shown copy-ready text grant more than the per-action reason?** No. Three kinds have a copy-ready decision.
- vault secrets: no block, as above.
- vault_transit (page `:151-161`):
  - `update` on exactly `{transit_mount}/sign/{key_name}` and `read` on exactly `{transit_mount}/keys/{key_name}`.
  - No `+` and no `*` in either path. Grammars are fullmatch, there are no wildcard characters, and `..` is refused.
  - Capability matches HTTP verb (POST is update, GET is read, as `binding_problems` derives it).
  - Both match the two request sites at `signer_vault.py:52` and `:62`.
  - R18 is the exact path, so the optional hash-algorithm suffix is not granted. That is the safe direction.
- kubernetes (page `:212-245`): `list` on `apps/deployments`, `list` on core `events`, `get` on core `pods/log`. There is a namespaced Role per namespace and no ClusterRole. The page shows the placeholder `{namespaces}`. In values mode `kubernetes_rules` fullmatches `<group>/<resource> in {namespaces}`. That matches `READ_OPERATIONS` and `kubernetes.py:232, :247, :285`. It holds no wildcard verb, no `secrets` and no shell subresource.

**2. Could an unverified claim still look verified?** Only in one cosmetic way: see minor 1. Otherwise no. Every grant row has a "claims not checked" column. A policy's block is withheld on any non-empty claim.

**3. Wildcard, path and segment rules exact?**
- `path_prefix` grammar is `([A-Za-z0-9_.-]+/)+` (`policy_page.py:178`). It is non-empty and always ends in `/`. So `{path_prefix}+` makes the `+` a whole segment. `ENDS_IN_SLASH` and `_vault_path_problems` (`:338-358`) enforce that, and refuse `+*` and a mid-path `*`.
- The `..` and `.` segment check applies to every part (`:731`).
- The `_fetch` name check (`secrets_vault.py:108-114`) keeps the secret name to one part. `_NAME` and the `.`/`..` guard are unchanged.
- An empty prefix is refused in values mode and the page's first line says it reads the whole mount.
- The `+` semantics themselves are still a single reading (see Evidence state).

**4. Vault never-paths against grants (I did the cross-check; the builder did not).** `cross_problems` (`policy_page.py:676-693`) only compares `type == "action"` names within a platform. It never compares a never `path` with a grant. I compared by hand:
- `vault` kind:
  - Grant R17 is `read` on `{mount}/data/{prefix}+`.
  - Never `{mount}/data/*` lists create, update, patch and delete, not `read`. So there is no overlap.
  - `{mount}/delete/*`, `undelete/*`, `subkeys/*`, `metadata/*` and `destroy/*` are different path trees from `data/`. `root` and `sys/*` are not granted.
- `vault_transit` kind:
  - R18 is `update` on `.../sign/{key}` and R19 is `read` on `.../keys/{key}`.
  - Never `keys/{key}` is listed with `delete` only, so no clash with R19's `read` on the same path.
  - `config`, `rotate`, `trim` and `restore` are other paths. The same goes for `restore/*`, `export/*`, `byok-export/*` and `backup/*`. `sys/*` and `root` are not granted.
- One process with both Vault kinds: the never `{mount}/data/*` with `update` and R18's `update` sit on different mounts, so the union has no clash.
- Kubernetes: grants are `list` and `get` on three resources. Never actions (the write verbs, `escalate`, `bind`, `impersonate`) and never resources (shell subresources, `secrets`) do not intersect them. The `create` exception is limited to the self-review resources, which no grant uses.
- Result: consistent today. It is a manual finding only, not a test; see minor 3.

**5. Lock-in / single dependency.** There is no new runtime dependency. `tools/policy_page.py` is standard library, and PyYAML is an existing test dependency. The engine tests rest on one source-available image, `hashicorp/vault:2.2.0` (BSL 1.1). The page names this and the OpenBao trigger and review date 2026-12-11 (ledger row BL-core-q8c1-openbao). OpenBao is not run. That is honest and acceptable. I did not read the real ledger.

## Findings

**Minor 1. R17's "verified" cell lists the builder-only sources.**
- Where: `secrets_vault.py:245-254`; page `:80`.
- Failure: the column "name and form found in a vendor source" shows `2026-11-11, sources V-KV, V-POL, V-ACL, V-PARSE, B-KV, B-POL, B-ACL`. V-ACL, V-PARSE and B-ACL (and the `+` reading of V-POL and B-POL) were read by the fix builder only. A reader skimming that column sees seven sources for R17, and the next-column disclaimer is in a different column. The same row's "what limits a wildcard" cell also says "nothing deeper is covered" as fact.
- Fix: move the builder-only source ids out of `verified` into the claim text. Or add "(builder only)" beside those ids. No copy-ready text can come out of this today, so this is cosmetic.

**Minor 2. The unverified `+` claim and the builder-only never-paths have no deadline in different ways.**
- Where: `test_policy_guard.py:99-106`.
- The three builder-only never-paths (`undelete`, `subkeys`, `byok-export`) have `PENDING_NAMES` entries with review-by 2026-12-11, so the suite goes red then. R17's `claims_unverified` has no pending entry. Nothing ever fails for it, so it could sit for ever. The consequence is safe (the Vault secrets kind simply has no block), but there is no pressure to re-read the sources. Consider a dated entry for the claim.
- Also, the fixture header is internally contradictory. Lines 6-7 say 16 rows were read by the evidence runner, but lines 26-27 say "nothing below has been checked by anyone but the builder of a fix". The following list names only the builder-only items, so the intent is clear, but reword it.

**Minor 3. No automated Vault never-path versus grant cross-check.**
- Where: `policy_page.py:676-693`.
- Failure scenario: a later edit gives a grant a capability, such as `update` on a path under `{mount}/data/{prefix}+` or a read of `{mount}/metadata/*`. The page would list that same path as never-given, and no test would notice. For R17 and R18/R19, `binding_problems` ties each grant to its code request, so drift is caught there. The never side is untied.
- Fix: before PR 2 adds more Vault grants, add a test that no never `path` (with its capabilities, or all if none) covers a grant's resource and capability.

**Minor 4. Two builder-read claims sit in shown copy-ready rows without being flagged.**
- Where: transit note "so that longer form is not allowed by this policy" (`signer_vault.py:118-120`); Kubernetes note "None of them changes the verb the request needs" (`kubernetes.py:385-389`).
- Both stay in the safe direction (narrower, not wider) and rest on documentation the evidence runner read (V-TR; K-AUTHZ). The exact-path non-match rests on the builder-only V-ACL. No change is needed for safety. I mention it so the reader of the page does not treat them as machine-checked.

**Minor 5. Engine claims in the shown transit block.**
- The transit block is copy-ready while the page says its server tests have not run. That wording is honest and test-pinned (`test_policy_docs.py:27-34`). The block's content is from vendor documentation only.

## Evidence state / what remains before a final CLEAN
- The 12 Vault server tests have never run (`ENGINE_RUN` is None; pinned by `test_policy_docs.py:28`). That is round-2 Major 1 (design), still open as evidence. The code and docs are honest about it. It needs one CI run on the final head with `-rs` output saved by the evidence runner: 12 passed, 0 skipped, with `HADAVIN_REQUIRE_VAULT_ENGINE=1` in both Vault-service jobs. Only then set `ENGINE_RUN` and edit `test_m1` together.
- The `+` reading of R17 (V-POL, B-POL, V-ACL, V-PARSE, B-ACL) still needs an evidence-runner re-read and re-fetch of the three hashes. After that, set R17 `claims_unverified` back to `()` and update the three pending names (the fixture header says how).

Please treat the READY verdict as limited to the delta in the code and docs. The merge itself should wait for the two evidence items above.

Files read (snapshot /home/user/build/snap/q8c1-6bdfadc1/): `src/hadavin_sdk/actions/secrets_vault.py`, `src/hadavin_sdk/audit/signer_vault.py`, `src/hadavin_sdk/sources/kubernetes.py`, `tools/policy_page.py` (lines 140-440, 660-1000), `docs/declared-permissions.md`, `tests/test_policy_guard.py` (lines 70-140, 1440-1590), `tests/test_policy_docs.py`, `tests/fixtures/policy_sources_2026-11-11.txt`, `CHANGELOG.md` (212-252), `README.md` (line 43). Also the ticket and both round-2 reports under /home/user/hadavin-sdk/handover/.

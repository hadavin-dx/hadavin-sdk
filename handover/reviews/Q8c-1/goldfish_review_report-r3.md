Status: resolved (by egm:egm-resolve, autonomous mode, recommended option for every item; no person was available or asked)

# Goldfish Annotated Review Report

**Target:** Q8c-1 at head 6bdfadc1 (security path: declared least-privilege sets for the Vault and Kubernetes kinds); ticket handover/tickets/Q8c-least-privilege-policy-per-kind.md
**Findings from:** handover/reviews/Q8c-1/result-r3-design-full.md and result-r3-codebase-full.md. **Evidence:** handover/evidence/Q8c-1/6bdfadc1/EVIDENCE-REPORT.md (all gates exit 0; policy mutants 45/45; stage 37/37; plants 32/32; 12 Vault engine tests NOT RUN).

## ESCALATE first
### [Issue E1] [design + codebase] carried Major (evidence gate)
*   **Scope:** 12 Vault server tests (tests/test_policy_engine.py); `ENGINE_RUN` is None; R17 `+` reading rests on a single builder reading (V-POL, B-POL, V-ACL, V-PARSE, B-ACL, three hashes).
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** the evidence is outside everything the reviewers or this session can reach: no vault/bao binary and no docs hosts here. Not a code defect; a merge gate. Next step: one CI run with HADAVIN_REQUIRE_VAULT_ENGINE=1 and `-rs` showing 12 passed, 0 skipped on the final head; then set ENGINE_RUN and edit test_m1 in the same commit; then an evidence runner re-reads the five sources and re-fetches the three hashes, after which R17 `claims_unverified` goes back to `()`. Ledger: Q8c-1-r3-d-OPEN (OWNER-ONLY). Already in questions-for-lead.md.

## Prioritized Findings
### [Issue 1] design m1 - minor: R17 "verified" cell lists the builder-only sources (secrets_vault.py:245-254; page :80)
*   ***AI Suggestion:*** PROPOSE FIX. Move V-ACL, V-PARSE, B-ACL (and the `+` reading of V-POL/B-POL) out of `verified` into the claim text, or mark "(builder only)" in the cell. Cosmetic but it is the round-2 bug class; fix it at `_checked_cell` so any builder-only id is marked everywhere.
### [Issue 2] design m2 - minor: R17 `claims_unverified` has no dated pending entry; fixture header contradicts itself (test_policy_guard.py:99-106; fixture lines 6-7 vs 26-27)
*   ***AI Suggestion:*** PROPOSE FIX. Add a dated pending entry (review by 2026-12-11) so the suite goes red if the claim is never re-read; reword the header.
### [Issue 3] design m3 - minor: no automated Vault never-path vs grant cross-check (policy_page.py:676-693)
*   ***AI Suggestion:*** PROPOSE FIX. Security path and the manual check was consistent: add a test (and a mutant) that no never `path` with its capabilities covers a grant's resource and capability; derive the grant and never path forms the same way as the page does.
### [Issue 4] codebase m1 - minor: R18 hash-suffix claim (signer_vault.py:118-120) and Kubernetes "None of them changes the verb" (kubernetes.py:385-389) sit in copy-ready rows without `claims_unverified` or a source
*   ***AI Suggestion:*** PROPOSE FIX. Same bug class as the round-2 Major. Fix at the shared point: a test that every sentence in a copy-ready note that asserts server or API behaviour has either a source id or is listed in `claims_unverified`. Concretely: keep the safe-direction wording but add both claims to `claims_unverified` (consequence: the transit and Kubernetes copy-ready blocks are withheld until sources are checked; this is the honest result) OR cite the sources the builder actually read. Recommended: add to `claims_unverified`.
### [Issue 5] codebase m2 - minor: Kubernetes credential text says "ServiceAccount token that the tool's fetch attaches" (kubernetes.py:363-365); code attaches any named secret only if token_secret_name is set (app.py:340); `fetch` is in app.py
*   ***AI Suggestion:*** PROPOSE FIX. Reword to what the code does.
### [Issue 6] codebase m3 - minor: page head/CHANGELOG say every row is pinned to a commit; seven abbreviated ids and the unpinned OpenBao release are not mentioned; `len(rows) == 19` brittle (test_policy_guard.py:2666)
*   ***AI Suggestion:*** PROPOSE FIX. Add one sentence to the page head and the CHANGELOG; replace the count by a check against the fixture list.
### [Issue 7] codebase m4 - minor: allowlist hint (test_policy_guard.py:909) does not say to move the line in SHAPES; partial revert of the E2 line is not a mutant; K `create` on self-review resources cites only K-AUTHZ
*   ***AI Suggestion:*** PROPOSE FIX for all three (hint text, one mutant dropping only `not g.claims_unverified`, add K-SSRR or mark unverified).
### [Issue 8] codebase tautology pins (:1487-1496 R17_CLAIM, :1504 dict, :1702 count) and design m4/m5 (engine claims in the shown transit block)
*   ***AI Suggestion:*** DECLINE. Deliberate state pins; the behaviour tests are the plants at :1499-1518 and :1567-1584; the transit-engine wording is test-pinned (test_policy_docs.py:27-34). Recorded.

## Handoff
Accepted fixes: 7 (issues 1-7). Contested: 0. Escalated: 1 (engine run, owner-only). Declined: 1. Unaddressed: 0. Gate: one fix batch (security path: a fresh delta review of the batch follows, uncapped), then delta evidence.

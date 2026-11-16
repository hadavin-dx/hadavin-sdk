Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 5)

**Target:** branch `core/q8c-1-policy-vault-kubernetes`, head `fbc837b4`, snapshot `/home/user/build/snap/q8c1b4-fbc837b4`. Least-privilege page and guard path (security path, no round cap). No person was available: recommended option for every item. Reviews: `handover/reviews/Q8c-1/r5-design-summary.md` (0 Blocker, 0 Major, 3 Minor, 2 Nit) and `/home/user/build/reports/q8c1-codebase-r5.md` (0 Blocker, 1 Major, 3 Minor, 3 Nit). Evidence runner a5832502 had not reported when this was written: Issue 7 (fail-before) of round 4 stays open until its RESULTS.md is read.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase`] C1 - Severity: Major
*   **Affected Scope:** `docs/declared-permissions.md` (text explaining the "partly builder only" mark), `tools/policy_page.py` (same head wording), `tests/fixtures/policy_sources_2026-11-11.txt:35-43`, `:52`.
*   **Discrepancy Description:** The page says the passage behind the claim "was read by the builder only". The fixture says nobody has read it for R18, R20-R22, free `rules_review` and never `create`; the builder read only the `+` passage (R17).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A claim shown as checked on the least-privilege page; same class as the round-2 and round-4 Majors.
*   ***Proposed Edit:*** Two marks, derived from the fixture header (one source): "builder read the passage" (R17 only) and "nobody has read the passage" (every other claim row). The page text and the drift test use the fixture's per-claim lines. Test: R18 shows the "nobody" mark, R17 the "builder" mark; mutant: swap them.

### [Issue 2] [`codebase` C3, `design` N1] - Severity: Minor (same finding)
*   **Affected Scope:** `tools/policy_page.py` `_kind_section` (`_checked_cell(f.verified)`, `_checked_cell(n.verified)` without `claim=`); page lines 183 and 212.
*   **Discrepancy Description:** Free and never rows with a claim list K-SSRR and K-AUTHZ as plain checked sources, while the same row says the claim is not in them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Pass `bool(claims_unverified)` for free and never rows. Page assertions for the `rules_review` line and the never `create` row; mutant.

### [Issue 3] [`codebase` C2, `design` N2, N5] - Severity: Minor
*   **Affected Scope:** `tools/policy_page.py:1073-1078` (`UNCHECKED_WORDING`), `_claims_problems`; `tests/test_policy_guard.py:2947-2948`; `secrets_vault.py:241-243`; docs `:82`.
*   **Discrepancy Description:** The round-4 class fix is a six-phrase list. Free, never and grant `reason` text is not note-classed, so "creates nothing" with no claim entry passes. The R17 "older versions" sentence has no source or claim entry.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A tripwire is not a closed class; round 4 required the class to be closed.
*   ***Proposed Edit:*** Add `NOTE_CLASSES` keys for free, never and grant `reason` (`code`, `sources` with ids in the entry's `verified`, or `claim`). A reason with no class fails. Give R17 "older versions" a claim entry or a source. Keep the phrase list only as an extra tripwire and say so in its comment. Test: a free reason "it only reads" with no class and no claim fails; mutant.

### [Issue 4] [`codebase` C4, `design` N3] - Severity: Minor (same finding)
*   **Affected Scope:** `tools/policy_page.py:1238` (head bullet), docs `:36-37` against `:82`; R17 `why`.
*   **Discrepancy Description:** The head says R17 reads "the one secret it names"; the cell says every secret directly under the prefix with every older version.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Head: "every secret directly under the prefix, each with every older version". Fix R17 `why` the same way, regenerate the page, and add a test that the head sentence and the R17 cell contain the same scope words.

### [Issue 5] [`codebase` C5] - Severity: Nit
*   **Affected Scope:** `tests/test_policy_guard.py` sources-suffix test (delta 926-946).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Assert note text immediately followed by the suffix as one string; match source lines exactly (`"- V-TOK: "`).

### [Issue 6] [`codebase` C6] - Severity: Nit
*   **Affected Scope:** `tests/test_policy_guard.py:3133`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** "78 patterns" becomes 65 (5 + 15 + 45); better, compute the count in the test.

### [Issue 7] [`codebase` C7, `design` N4] - Severity: Nit
*   **Affected Scope:** `tests/policy_mutants.py` (automaton mutants), `_both_take`, `_vault_form`; `BROADER_THAN_REASON` (hand list).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add mutants for the mirror branch of `_both_take`, the `(?!path_prefix\})` lookahead and the `+` edge; state in the comment that `BROADER_THAN_REASON` is a hand list pinned by a test against the page.

### [Issue 8] [`evidence`, round 4 Issue 6] Vault engine tests never run - Severity: Major (process gate)
*   ***AI Suggestion:*** unchanged, IMPOSSIBLE-NOW (no server binary here, none may be fetched); one CI run on the final head with 12 passed and 0 skipped is the merge gate; ledger row stays OPEN; the page keeps saying "have not run yet".

## Handoff counts
Accepted (PROPOSE FIX): 7. Contested: 0. Escalated: 0. Declined: 0. Open gate (not code): Vault engine run in CI; round-4 Issue 7 awaits evidence a5832502. Round 6 review needed after the fix batch (security path, no round cap).

Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 4)

**Target:** branch `core/q8c-1-policy-vault-kubernetes`, head `be531371`, snapshot `/home/user/build/snap/q8c1f3-be531371/files`. Least-privilege page and guard path (security path, no round cap). No person was available: recommended option for every item. Reviews: `/home/user/build/reports/q8c1-design.md` (no Blocker, no Major, 5 minor findings, 1 open evidence gate) and `q8c1-codebase.md` (0 Blocker, 1 Major, 4 Minor/Nit). Evidence: `q8c1-EV.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase`] F1 - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/sources/kubernetes.py:441` (free `reason`), `:449` (`verified` K-RBAC, K-SRC, K-SSRR), never entry `create` at `:474-480`; page `docs/declared-permissions.md:175` against `:184`.
*   **Discrepancy Description:** The page says `k8s.rules_review` "creates nothing" and shows it as checked against K-SSRR, while the never entry says that no vendor source says so.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Verified at the lines by the reviewer; same class as the round-2 R17 `+` Major (a claim shown as verified). The page is a trust signal on a least-privilege page; a wrong one must be fixed here.
*   ***Proposed Edit:*** Class-level: add `claims_unverified` to `free` entries (as grants have), show it on the page, give each a dated PENDING_CLAIMS entry, and extend the note-class test to cover free `reason` text. For this entry: reword the reason to what the code does ("treated as harmless by the start-up check; not found in a vendor source") and drop K-SSRR from `verified` for that claim. Test and mutant: a free `reason` that states a fact with no source or no claim entry fails.

### [Issue 2] [`codebase`] F2 - Severity: Minor
*   **Affected Scope:** `tools/policy_page.py:711` (`_vault_form`), `:703-705` (`_vault_sample`), `:730-732`; GRAMMAR `:178`, ENDS_IN_SLASH `:148`.
*   **Discrepancy Description:** `{path_prefix}` is treated as a literal token with no slash, so a two-part never path such as `{mount}/data/+/+` over R17 is missed by the cover check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Expand `{path_prefix}` to a sample that ends in `/` and holds two parts (for example `px/qx/`) and test both one-part and two-part samples; add a clean/caught pair for a two-part never path to the plant test (`test_policy_guard.py:2862`) and a mutant.

### [Issue 3] [`codebase`] F3 - Severity: Minor
*   **Affected Scope:** `tools/policy_page.py:141` (NEVER_TYPES global), `:440-441`, branches at `:721`, `:734`.
*   **Discrepancy Description:** A never entry with a type that does not fit the platform is skipped by the cover rule yet rendered on the page.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** In `_never_problems` allow per platform: Vault `role`, `path`; Kubernetes `role`, `action`, `resource`. Anything else is a problem. Plant: a Vault `resource` entry with a path name must be refused.

### [Issue 4] [`codebase`] F4 - Severity: Nit
*   **Affected Scope:** `tests/test_policy_guard.py:2990-2997`, `:2936-2964`.
*   **Discrepancy Description:** Class "sources" in the note-class test only checks that listed ids exist, not that a grant's `verified` lists them; V-TOK is named in two notes and printed nowhere on the page.
*   ***AI Suggestion:*** PROPOSE FIX (cheap; same page-trust class)
*   ***Proposed Edit:*** Print a "sources:" suffix on classed notes; the test checks each listed id appears in the same entry's `verified` or in the source list printed on the page.

### [Issue 5] [`design`] findings 1, 3, 4 and remaining minors (see `q8c1-design.md`)
*   **Affected Scope:** design finding 1 (three grants broader than their stated reason, and the page does not say so); finding 3 (builder-only ids are a hand-written constant at `policy_page.py:922`, not tied to the fixture header); finding 4 (cover-check limits); the rest of the design Minors and Nit (the 92-day cap lives in the same test file as the constant).
*   ***AI Suggestion:*** PROPOSE FIX for each (the builder reads each finding at its lines first; where a finding is already covered by Issues 1-4 it says so with the line)
*   ***Proposed Edit:*** Finding 1: the page states, next to each broader grant, what it allows beyond the stated reason and why it cannot be narrower. Finding 3: derive the builder-only ids from the fixture header (one source) with a drift test. Finding 4: state the limits on the page and add the two-part case from Issue 2. 92-day cap: the CI check reads the cap from one constant in the tool, not from the test file.

### [Issue 6] [`evidence` and both reviews] Vault engine tests never run - Severity: Major (process gate)
*   **Affected Scope:** 12 tests in `tests/test_policy_engine.py` (skipped: no vault or bao binary here, 13 skips in the full run, 12 errors with `HADAVIN_REQUIRE_VAULT_ENGINE=1`).
*   ***AI Suggestion:*** PROPOSE FIX where possible; otherwise classified IMPOSSIBLE-NOW with the next step.
*   ***Justification:*** No server binary exists here and none may be fetched in this session (the auto-mode classifier refused a download brief). Classified IMPOSSIBLE-NOW (c, third party: needs a CI run). The merge gate stays: one CI run on the final head with `-rs` showing 12 passed and 0 skipped; then set ENGINE_RUN and edit the pinned page test in the same commit.
*   ***Proposed Edit:*** No download attempt. The ledger row stays OPEN until a CI run exists. The page keeps saying "have not run yet".

### [Issue 7] [`evidence`] fail-before - Severity: Minor
*   **Affected Scope:** 8 of the new tests pass on the old src (builder_only_source_marked_wherever_listed, never_path_over_a_grant_refused_by_check_command, no_never_list_line_covers_a_grant, plant_a_kubernetes_never_resource, plant_a_new_note_with_no_class, plant_a_vault_never_path_over_a_grant, plant_the_check_across_kind and one more).
*   **Discrepancy Description:** Most of them are plants that test the new guard against supplied data, so they pass on old src by construction (the guard lives in `tools/`, which the runner copied in).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The builder says per test why it passes on old src (the guard is in the tool, not in src) and shows that each guard fails if its mutant is applied (the mutants are the fail-before for the tools). Any test that can pass on the old tool as well gets a mutant or is rewritten.

## Handoff counts
Accepted (PROPOSE FIX): 7. Contested: 0. Escalated: 0. Declined: 0. Open gate (not code): Vault engine run in CI. Remaining unaddressed: 0 until the fix batch. Round 5 review needed (security path, no round cap).

Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 6)

**Target:** branch `core/q8c-1-policy-vault-kubernetes`, head `5015c990`, snapshot `/home/user/build/snap/q8c1b5-5015c990`. Least-privilege page and guard path (security path, no round cap). No person was available: recommended option for every item. Reviews: `/home/user/build/reports/q8c1b5-design-r6.md` (0 Blocker, 2 Major, 3 Nit) and `q8c1b5-codebase-r6.md` (0 Blocker, 2 Major, 6 Nit); both read-only. Evidence: `handover/evidence/Q8c-1/5015c990/RESULTS.md` (full run 10857 passed, 13 skipped; `policy_mutants` 89 of 89; ruff, bandit, scan_repo, `policy_page --check`, gitleaks all exit 0).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1, `evidence` probe 1] - Severity: Major
*   **Affected Scope:** `tools/policy_page.py:1106` (`claim_mark`, `startswith`), `:1127`; fixture `tests/fixtures/policy_sources_2026-11-11.txt:61-62`.
*   **Discrepancy Description:** The "builder read the passage" mark is matched on the first part of a claim. A clause added to the R17 claim keeps the stronger mark (page prints it after an unread clause). Evidence: a mark swapped between R17 and R18 gives no problem; the page then shows the nobody mark on R17 and the builder mark on R18. Also accepted by the parsers: a start repeated under both marks, a trailing ` ;;` with no space as a start text; a zero-width character in a start gives "0 marks" plus "stale start" (reported, fine); a BOM is accepted by `claim_readers` but refused by `builder_marks` and `source_ids`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The mark is the only statement on the page that someone read the vendor text; a mark that can drift onto text nobody read claims more than the evidence shows. Same class as rounds 2, 4 and 5.
*   ***Proposed Edit:*** Fixture lines carry the full claim text; match by equality for both marks (a start-of-text match is allowed nowhere). A start under both marks is a problem. A builder-read mark on any claim other than the one the fixture names is a problem (the page's mark per claim is compared with the fixture one by one). One reader for all three parsers: strip a BOM once, refuse the same set of bad lines. Tests: append a clause to R17 (reported), swap R17 and R18 marks (reported), start under both marks, BOM in each parser, trailing ` ;;`. Mutants for each.

### [Issue 2] [`design` F2, `codebase` M2] - Severity: Major
*   **Affected Scope:** `tools/policy_page.py:1483-1485` (head), `docs/declared-permissions.md:30-31`, `:112`, `src/hadavin_sdk/actions/secrets_vault.py:249-250` (R17 `reason`, also written into the rendered Vault policy comment `# R17:`, tested at `tests/test_policy_guard.py:1708/1712`), `:3688-3700`.
*   **Discrepancy Description:** The head and the "why" column state flatly that R17 covers "each with every older version"; the claims cell marks the same statement "(nobody has read the passage)". A test asserts the flat wording.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Safe direction (overstates the breadth of the grant) but the page's rule is that no behaviour claim reads as established without a source or mark. Round 5 itself introduced this wording.
*   ***Proposed Edit:*** Head, `why` and `reason`: "every secret directly under the prefix; it may also cover every older version of each (not yet checked against the vendor, see the claims cell)". Update the `NOTE_CLASSES` key, the rendered `# R17:` comment, the docs, and the scope test to assert the hedged wording and that the flat form is absent. Remove the vacuous assertion at `:3698` (the phrase never appears in the head) or replace it with one that fails on the flat wording.

### [Issue 3] [`codebase` M1] - Severity: Major
*   **Affected Scope:** `tools/policy_page.py:14-23` (docstring), `data_problems` `:703-726`, `tests/test_policy_guard.py:100-107` (`PENDING_NAMES`), `:120-128` (`PENDING_CLAIMS`), `:1489`; CHANGELOG ("the rule runs in --check").
*   **Discrepancy Description:** The docstring says `--check` runs every data check the tests run; the dated-entry rules (names, claims) exist only in the tests. A grant with `"verified": None` or a new `claims_unverified` entry with no `PENDING_*` row exits 0 on `--check` and fails only in pytest.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A gate described as the whole data gate that is not; fixed in the choke point, not by words alone.
*   ***Proposed Edit:*** Move the dated-entry data (`PENDING_NAMES`, `PENDING_CLAIMS` and the review-by dates) into the tool (the page data already lives there) and run both rules in `data_problems`; the tests import them. Docstring and CHANGELOG list what `--check` runs, and anything left test-only by name. Test: `verified: None` with no pending row is reported by `--check`; mutant.

### [Issue 4] [`design` F3, `codebase` N1, N2, `design` F4] - Severity: Minor
*   **Affected Scope:** `tools/policy_page.py:1067` (`builder_marks(DATA_ROOT)`), `:1099` (`claim_readers(DATA_ROOT)`), `:1137-1140` (`_claim_text`, `_checked_cell`), `:723`, `main` `:1608-1621`; `NOTE_CLASSES` handling `:1315-1326`.
*   **Discrepancy Description:** Both mark tables are read at import, so a malformed sources head gives a traceback before `--check` can report it, and `page(root)` and `data_problems(root)` take marks from different places. A malformed `NOTE_CLASSES` entry (empty tuple, `("claim", 5)`, `("claim", "")`) crashes with ValueError/TypeError or passes any entry, against the CHANGELOG ("never a crash").
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Read the tables lazily and pass them down (one `Marks` value built from `root`, used by `data_problems`, `page` and the render helpers). `note_problems` validates the class shape first (non-empty tuple, kind in the allowed set, non-empty `str` fragment for `claim`, tuple of `str` for `sources`) and reports a problem line. Tests for a broken head via `root` and each bad class shape through the CLI path (one problem line, exit 1, no traceback); mutants.

### [Issue 5] [`design` F5, `codebase` N5, N6] - Severity: Nit (PROPOSE FIX, cheap)
*   **Affected Scope:** `tools/policy_page.py:1509-1516` and `secrets_vault.py` R17 `bound` ("the second claim in the claims cell"); fixture head `:26-28`; `builder_marks` docstring `:1041-1045`; CHANGELOG `:278-281`.
*   **Proposed Edit:** Derive the head prose about which claim has which mark from the fixture (or a test comparing them) and name the claim in its own words. Reword the fixture head and the docstring: only V-POL and B-POL have a builder-read passage; the other 7 are nobody-read. CHANGELOG: only the 7 `_PR2` kinds fail from 2026-12-12; the other 9 from 2027-02-01.

### [Issue 6] [`codebase` N4, N3] - Severity: Nit (PROPOSE FIX, mutant strength)
*   **Affected Scope:** `tests/policy_mutants.py:577-584` (B4 "second builder-only line", old text `if len(rows) != 1:` occurs twice, at `policy_page.py:1053` and `:1090`; the runner replaces every occurrence), `:632-641` (B5 "a `+` reads exactly one character", `expect="reported"`, which any failing `same()` satisfies); no mutants for `:1093`, `_class_keys` `not k[1].startswith("reason:")` `:1277`, stale-class filter `if k[0] in policies` `:1353`; `tests/test_policy_guard.py:3698`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Anchor each B4 mutant on text unique to its function; add the three missing mutants; give B5 an `expect` that only the intended failure produces; fix or remove the vacuous assertion (done in Issue 2).

### [Issue 7] [`evidence` fail-before] - Severity: Minor
*   **Affected Scope:** 12 new test functions; on `fbc837b4` src 4 fail and 8 pass; on `origin/main` src 11 fail and 1 passes; as given, the new tests do not even collect on either base.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** One line per passing-on-old test: why it passes (a control for a class fixed earlier, a plant against supplied data that lives in `tools/`), and the mutant that proves the guard is live; any test with neither a failing old case nor a mutant gets one. The guard test for `{path_prefix}` (passes on both) names its mutant.

### [Issue 8] [`evidence`, rounds 4-5 Issue 8] Vault engine tests never run - Severity: Major (process gate)
*   ***AI Suggestion:*** unchanged: IMPOSSIBLE-NOW (no server binary here and none may be fetched). 12 tests error with `HADAVIN_REQUIRE_VAULT_ENGINE=1` ("HADAVIN_TEST_VAULT_ADDR is not set"), skipped in the full run. Merge gate: one CI run on the final head with 12 passed and 0 skipped; then set `ENGINE_RUN` and edit the pinned page test in the same commit. Ledger row stays OPEN; the page keeps saying "have not run yet".

### Items recorded, no change (evidence)
*   Not run: the flaky timing test (heavy slots busy); Python 3.12 CI job; `uv sync --locked --no-build` fails here (used `--all-extras --group test`). Probes confirmed good: K-NOPE gives a problem and `PolicyError` from `page()`, never KeyError; none of the 45 reason entries lacks a class key; the `{mount}/data/{path_prefix}+/deeper/+` path does not overlap R17; controls overlap as expected.

## Handoff counts
Accepted (PROPOSE FIX): 7 (Issues 1-7). Contested: 0. Escalated: 0. Declined: 0. Open gate (not code): Issue 8, Vault engine run in CI. Round 7 review needed after the fix batch (security path, no round cap).

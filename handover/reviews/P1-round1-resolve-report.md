# Goldfish Annotated Review Report (resolve, round 1)

Status: findings categorised; fixes to be applied by the ticket author under the owner's standing instruction (see the note below)

**Target:** `handover/tickets/P1.md` (full file). Findings: `handover/reviews/P1-round1-adversarial.md`, `handover/reviews/P1-round1-correctness.md`. Decisions applied: `handover/studio-notes/amendments.md` A11, A12, A13.

Counts: PROPOSE FIX 43, ESCALATE 0, CONTEST 0, DECLINE 0. Nothing was contested: for every finding the reviewer cited a file and line that could be read, and the author re-checks it before editing. The skill's severity names are Blocker / Major / Nit; the review files say BLOCKER / MAJOR / MINOR (MINOR = Nit, and every Nit is also fixed because the fix is cheap).

Note on the gate (skill Step 4): the owner told the cloud session to run resolve and rewrite the tickets, and set the standing rule that only major decisions wait for the owner. So the "auto accept" path is taken for every PROPOSE FIX; ESCALATE items are NOT applied as decisions: the ticket carries the recommended position marked PENDING LEAD and the item is listed in `handover/questions-for-lead.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** P1b "Decided choices"; Interface; P1b gap 1 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The ticket contradicts itself on identity keys. It says `identity_key` is "the single stable key" and, in the same section, that the identity key "keeps BOTH readings (3 and z)" for Ze. A digest of one string cannot hold two readings. The key-set is never defined.
*   **Rationale:** evidence: Ticket lines 38-40, 69; memo 1 section 5 gap 1b; amendments F4 vs A2 ("one stable identity key").
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(4): one string for identity; Cyrillic Ze readings live only in the DENY key-set. The finding is valid: the reviewer cites evidence that can be read (Ticket lines 38-40, 69; memo 1 section 5 gap 1b; amendments F4 vs A2 ("one stable identity key").). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b "Decided choices"; Interface; P1b gap 1
    *   Change: Pick one. Identity = ONE string. Ze goes only into the scan/DENY key-set. Specify the set encoding (sorted, length-prefixed) and the match rule (non-empty intersection), and test that `same_person` is documented as non-transitive.

### [Issue 2] [`egm-design`] - Severity: Blocker (finding id A2, adversarial)
*   **Affected Scope:** P1b gap 1 and gap 5 ("extra case readings") of `handover/tickets/P1.md`
*   **Discrepancy Description:** The key-set size is unbounded or under-covered. "Extra case readings" for case-ambiguous letters is not defined. With a per-position cross product, n ambiguous letters give 2^n keys (a 20,000-character run of capital Eta). With only two global readings, a string that mixes Η meant as H and η meant as n is not covered, so the DENY scan misses it.
*   **Rationale:** evidence: Memo 1 gap 1b; ticket lines 68-69, 77. The existing redactor note in `defaults.py` lines 34-47 shows every extra view repeats a 1-7 s hostile cost at the cap.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(4): fixed size cap that fails closed. The finding is valid: the reviewer cites evidence that can be read (Memo 1 gap 1b; ticket lines 68-69, 77. The existing redactor note in `defaults.py` lines 34-47 shows every extra view repeats a 1-7 s hostile cost at the cap.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 1 and gap 5 ("extra case readings")
    *   Change: Define the construction. Either per-position readings with a hard cap K on keys, failing closed (raise a distinct error that means DENY) above K, or a proof that two readings suffice. Add a hostile test with 20,000 ambiguous letters and a time bound.

### [Issue 3] [`egm-design`] - Severity: Blocker (finding id A3, adversarial)
*   **Affected Scope:** P1a Errors; Length cap; stored keys of `handover/tickets/P1.md`
*   **Discrepancy Description:** Every new error is a `ValueError` subclass: `TextTooLong`, `FoldVersionMismatch`, `TextnormError`. A DENY caller that does `except ValueError:` (routine for parse errors) turns "cannot decide" into "no match". That is fail-open on a security choke point. The cap itself also becomes an evasion switch: padding to 20,001 characters either raises (a DoS if the caller blocks) or is swallowed (a bypass).
*   **Rationale:** evidence: Ticket lines 40-42; `defaults.py` line 38 (`MAX_REDACT_CHARS` = 262,144, so redaction at the existing cap will hit `TextTooLong` at 20,000).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(4): the new errors do not derive from ValueError. The finding is valid: the reviewer cites evidence that can be read (Ticket lines 40-42; `defaults.py` line 38 (`MAX_REDACT_CHARS` = 262,144, so redaction at the existing cap will hit `TextTooLong` at 20,000).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a Errors; Length cap; stored keys
    *   Change: Derive the errors from `Exception` (not `ValueError`). State in the docstring and tests that any `TextnormError` on a DENY path means "deny/refuse", with an example caller test. Either chunk with overlap instead of raising, or state the explicit rule that over-cap means refuse. Reconcile with `MAX_REDACT_CHARS`: the cap must come from the existing config, not a second 20,000.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A10, adversarial)
*   **Affected Scope:** P1a differential test of `handover/tickets/P1.md`
*   **Discrepancy Description:** The test has no independent oracle and its own rule contradicts itself. "Every pair any variant equates must be equal AND every pair any variant keeps apart must be different" cannot hold when variants disagree. Rows are included "because the PR50 head satisfies them", which is circular. The harvested literals are inputs, not pairs with expected relations (memo section 9). Behaviour from "any variant" includes Intake `_f` steps explicitly NOT taken (circled digits, Chinese numerals, bar-like letters).
*   **Rationale:** evidence: Ticket lines 11, 45; memo section 9 ("harvested fixtures supply inputs, not expected outputs").
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 11, 45; memo section 9 ("harvested fixtures supply inputs, not expected outputs").). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a differential test
    *   Change: Write the expected relation per row from a stated principle (DENY: look-alikes equal; ALLOW: exact), with the source cited. List the excluded variant behaviours as explicit `not_taken` rows. The lead decides the disagreement rows before building, not per row at build time.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A11, adversarial)
*   **Affected Scope:** P1a views; empty keys of `handover/tickets/P1.md`
*   **Discrepancy Description:** Empty and non-Latin keys are unspecified. `id_key` uses `[^A-Z0-9]` deletion, so every id in CJK, Arabic, Cyrillic-without-mapping, etc. becomes `""`. The identity key of an all-invisible string is also `""`. A blocklist entry that folds to `""` and uses substring scan matches everything; one that is guarded by `if key:` matches nothing.
*   **Rationale:** evidence: PR50 `textnorm.py` lines 48, 86; ticket line 45.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (PR50 `textnorm.py` lines 48, 86; ticket line 45.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a views; empty keys
    *   Change: Define the contract: views return `""` only for empty or fully-dropped input, and callers get `is_empty_key(...)`. `stored_key` refuses to store an empty view output (or marks it). Test the substring-scan hazard.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A12, adversarial)
*   **Affected Scope:** P1b Intake `_f` move; `id_key` loose of `handover/tickets/P1.md`
*   **Discrepancy Description:** `id_key(loose=True)` equates O/0, I/1/L, S/5, B/8, Z/2, G/6, Q/9. The ticket plans for Intake to move its "`_f` money-path comparison onto `line_view` and `id_key`". If `_f` gates payment (ALLOW semantics: "the invoice field equals the approved value"), this is exactly the fold-as-ALLOW hazard the module's own rule forbids. The ticket never classifies `_f` as DENY or ALLOW.
*   **Rationale:** evidence: Ticket lines 11, 39, 85; PR50 docstring lines 7-16; `_LOOSE` at line 49.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 11, 39, 85; PR50 docstring lines 7-16; `_LOOSE` at line 49.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b Intake `_f` move; `id_key` loose
    *   Change: Classify every `_f` call site as ALLOW or DENY before P1b is built. ALLOW sites use `allow_equal` only. State this in the ticket and the Intake note.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A13, adversarial)
*   **Affected Scope:** P1b gap 7, nested entities of `handover/tickets/P1.md`
*   **Discrepancy Description:** The 8-round limit is a fixed number that an attacker can exceed. After 8 rounds a still-changing string is silently used. `&amp;` x9 followed by `#65;` stays unresolved, so `line_view` differs from the plain text and the DENY scan misses it. The ticket copies Intake's `_unescape` limit, a known evasion. "Entities only shorten text, so the cap holds" is asserted, not tested; the cap check must also be on the RAW input before unescape.
*   **Rationale:** evidence: Ticket lines 11, 78, 82.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 11, 78, 82.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 7, nested entities
    *   Change: After the loop, if the string still changes, fail closed (raise the DENY error, or add a marked "unresolved-entity" key that the caller treats as a hit). Make the limit a `defaults.py` constant. Test depth 9 as a REFUSAL, not a pass.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A14, adversarial)
*   **Affected Scope:** P1b cache of `handover/tickets/P1.md`
*   **Discrepancy Description:** The cache design is a sentence. `lru_cache` cannot bound by bytes. How size is counted (`len`, `getsizeof`, UTF-8) is unspecified, and no default name or value is given in `defaults.py`. The cache keeps raw personal data (names, account numbers) alive in memory. The "8-thread run equals single-thread" test cannot fail: the table is immutable and deterministic. The real race is in the byte accounting and eviction.
*   **Rationale:** evidence: Ticket lines 44, 68; memo section 5 (roughly 1.3 GB for the dealdesk model).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 44, 68; memo section 5 (roughly 1.3 GB for the dealdesk model).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b cache
    *   Change: Either drop the cache from core (the dealdesk wrapper keeps its own) or specify the cache: the byte measure, the lock, the key (a digest of the text rather than the text), the `defaults.py` constant, and a test that hammers eviction with a tiny bound and asserts `total <= bound` at the end.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A15, adversarial)
*   **Affected Scope:** P1a length cap and time bound of `handover/tickets/P1.md`
*   **Discrepancy Description:** The cap does not bound time. Only `fold`, the views and `has_mixed_script` are listed; `names_equal` and `allow_equal` (which run `_canon` before the capped `same_person`) are not. A str subclass can lie about `len` or `__eq__` (`a == b` in `allow_equal` returns EQUAL for an overriding `__eq__`, which is an ALLOW fail-open). Reverse-ordered combining marks may make normalisation quadratic (to be measured; the ticket's 0.25 s for 1M marks is for easy ordering). The time-ratio test uses a benign 10x input and is flaky by the studio's own rule (timing tests run alone).
*   **Rationale:** evidence: Ticket lines 17, 42, 44; PR50 `textnorm.py` lines 118-133.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 17, 42, 44; PR50 `textnorm.py` lines 118-133.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a length cap and time bound
    *   Change: Require `type(raw) is str` (TypeError otherwise) in every public function. Cap every entry point, including `_canon` users. Add a hostile-structure time test run alone. Measure the worst case across views, and state the per-call time budget.

### [Issue 10] [`egm-design`] - Severity: Major (finding id A16, adversarial)
*   **Affected Scope:** P1a mutation runner and scope of `handover/tickets/P1.md`
*   **Discrepancy Description:** A "small pull request" it is not. P1a carries about 870 lines of module, generator (129), 13 moved tests, three new test files, 3 fixtures, a manifest, ~400 lines of mutation runner and the mutants. The runner's `testing/mutation.py` lives under `src/hadavin_sdk/`, which ships in the wheel. Its docstring says the runner is "not shipped", but the judge module is. P1a also takes on a stored-key API for an algorithm the ticket itself says is buggy (gaps 1-3 are P1b).
*   **Rationale:** evidence: Ticket lines 35, 47, 65; `testing/mutation.py` line 3; A4 hot-file order.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 35, 47, 65; `testing/mutation.py` line 3; A4 hot-file order.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a mutation runner and scope
    *   Change: Land the runner as its own tiny PR (Decision 3, second option). In P1a do not export `stored_key`/`check_stored` until P1b, or mark algorithm id `fold1` as unstable and make P2/P3 depend on P1b.

### [Issue 11] [`egm-design`] - Severity: Major (finding id A17, adversarial)
*   **Affected Scope:** P1a loud-failure test of `handover/tickets/P1.md`
*   **Discrepancy Description:** The test, as specified, is built from strings the test crafts itself. The P1a to P1b case ("a P1a-algorithm key read by P1b code raises") needs a frozen key literal in a fixture; otherwise it is computed by current code and cannot fail. The golden fingerprint covers `fold_key` over single code points only: not `id_key`, `scan_views`, `line_view`, tag decode, spaced view or multi-code-point sequences. The golden test skips on other interpreters, so if CI ever moves off 3.13 it never runs. The mutant "golden accepted on every interpreter" is not a real mutant.
*   **Rationale:** evidence: Ticket lines 38, 43, 44, 47, 85; `ci.yml` lines 73, 109.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 38, 43, 44, 47, 85; `ci.yml` lines 73, 109.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a loud-failure test
    *   Change: Freeze real keys from P1a as literals. Add one golden constant per view over a fixed multi-code-point corpus. Make the CI job fail if the pinned interpreter is absent. Derive or test that the algorithm id changes whenever any golden changes.

### [Issue 12] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** P1a `FOLD_VERSION`; Pinned Python; Decision 2 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The pin is not enforced where production runs. The memo says "checked at import against the pinned value"; the ticket drops this. The pin exists only as a golden constant in a test file. Production on any other build silently writes `ud=` keys that other pods reject.
*   **Rationale:** evidence: Ticket lines 38, 43; memo section 7 ("checked at import against the pinned value"); `pyproject.toml` has `requires-python >=3.12`, `ci.yml` only 3.13 (lines 73, 109).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 38, 43; memo section 7 ("checked at import against the pinned value"); `pyproject.toml` has `requires-python >=3.12`, `ci.yml` only 3.13 (lines 73,). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a `FOLD_VERSION`; Pinned Python; Decision 2
    *   Change: Put the pinned unidata version in config (one place), validated at startup in pilot/prod. The profile refuses a mismatch. Dev may warn.

### [Issue 13] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** P1a stored keys; F3 "goes to a person" of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Goes to a person" is not implementable in P1, and the stored form defeats the alternative. Keys are SHA-256 digests with no raw text kept, so there is no re-fold route. On a P1b bump (non-revertible, algorithm id changes) every stored key, including every blocklist entry, is refused with no re-key path. No queue, API or owner for "a person" exists in textnorm, and no later package is named.
*   **Rationale:** evidence: Ticket lines 40, 65, 85; F3.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 40, 65, 85; F3.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a stored keys; F3 "goes to a person"
    *   Change: Ship an explicit contract in P1a: stored records must also keep the raw text under the caller's own protection (or `rekey(stored, view, raw)`), or the callers' tickets (P2d, P3b) name the person-queue. State the churn cost to the lead.

### [Issue 14] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** P1a `parse_stored`/`check_stored` of `handover/tickets/P1.md`
*   **Discrepancy Description:** Malformed or attacker-controlled stored strings leak into error messages. The ticket claims `FoldVersionMismatch` "message: both version strings, which are not personal data". That holds only for well-formed keys. `parse_stored` of an arbitrary string yields junk as the "version". Argument order is `(s, view, text)`, three strings, easy to swap.
*   **Rationale:** evidence: Ticket lines 40-41, 44.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 40-41, 44.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a `parse_stored`/`check_stored`
    *   Change: `parse_stored` raises a distinct `MalformedStoredKey` with no content echoed. The version string in a message is truncated or hash-prefixed and is shown only if it matches the format `fold\d+\|...`. Make the arguments keyword-only. The no-leak test must feed a canary through every entry point, including `s=`, and check `args`, `__cause__`, `__context__` and `repr`.

### [Issue 15] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** P1b gap 1 fix of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Table, casefold, table again, to a fixed point" is incomplete and unbounded. `casefold` can reintroduce dropped categories or chars needing NFKC (U+0130 gives `i` + U+0307, a Mn mark; U+1E9E, U+FB03). The loop does not re-run the drop and NFKC. "To a fixed point" has no iteration bound or termination proof. This is double folding on a security path.
*   **Rationale:** evidence: Ticket line 73; PR50 `textnorm.py` lines 65-77 (casefold last, no re-drop).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket line 73; PR50 `textnorm.py` lines 65-77 (casefold last, no re-drop).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 1 fix
    *   Change: Loop the WHOLE pipeline (NFKD, drop, NFKC, digits, table, casefold) with a fixed small max (2-3 passes). Assert over all code points that the max pass count is under the bound and is reached by none, else raise.

### [Issue 16] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** P1b gap 2 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The order is ambiguous: "apply the table to a code point before the Cn drop". If the table is applied before the drop for every category, any table entry whose source is Mn/Cf/Cc/Co now maps a mark to a letter. That contradicts the ticket's own property `identity_key(x + mark) == identity_key(x)`. A builder can do either. Also, the generator now keeps 1,797 single-source entries instead of 677, so the table roughly doubles with no entry-by-entry review.
*   **Rationale:** evidence: Ticket lines 74, 80; PR50 line 71.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 74, 80; PR50 line 71.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 2
    *   Change: State exactly: the pre-drop table lookup applies only to categories Cn (and the listed fillers); every other category is dropped first. Add a test that no table source is in a dropped category other than Cn. Review the new entries as a diff.

### [Issue 17] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** P1a table integrity; Decision 1 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The 677 (later ~1,700) entry table is a security artifact with no CI integrity check. The data file is not committed, the generator test is "run by the evidence runner, pasted" (manual). `tbl=41740c11:677` in `FOLD_VERSION` is described as "sha prefix and entry count", but it is not said whether the sha is computed from the in-memory TABLE or copied from the header. The generator test "table header matches FOLD_VERSION" compares header to header. `LOOKALIKES`/`CONFUSABLES` are mutable module dicts.
*   **Rationale:** evidence: Ticket lines 35-36, 38; PR50 `textnorm.py` lines 46-47.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 35-36, 38; PR50 `textnorm.py` lines 46-47.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a table integrity; Decision 1
    *   Change: Compute the table digest at import from a canonical serialisation of TABLE and compare it to a constant in a CI test. Expose the table via `MappingProxyType`. Alternatively commit the pinned data file and run the generator in CI.

### [Issue 18] [`egm-codebase-details`] - Severity: Major (finding id C1, correctness)
*   **Affected Scope:** P1a Files; Done gates of `handover/tickets/P1.md`
*   **Discrepancy Description:** Moving `_confusables.py` into core turns the repo guard test red. The file's header holds `https://www.unicode.org/terms_of_use.html`. The guard scans every `src/` string constant for url/host, so P1a fails its own gate `test_no_hardcoded_values`. PR #50 added an ALLOWED entry for `guard/_confusables.py` ({"url"}, "Unicode License notice"). The ticket never lists `tests/test_no_hardcoded_values.py`. The same applies when the generator rewrites the header in P1b.
*   **Rationale:** evidence: `_confusables.py:4` (2e8a28c). The 2e8a28c copy of `tests/test_no_hardcoded_values.py` has the entry at lines 50-53; core ce70eb5 has none (lines 42-61). Core pattern at lines 33-38.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`_confusables.py:4` (2e8a28c). The 2e8a28c copy of `tests/test_no_hardcoded_values.py` has the entry at lines 50-53; core ce70eb5 has none (lines 42-61). Core p). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a Files; Done gates
    *   Change: Add `tests/test_no_hardcoded_values.py` (ALLOWED entry) to P1a "Change". Add it to the P1b gate check too.

### [Issue 19] [`egm-codebase-details`] - Severity: Major (finding id C10, correctness)
*   **Affected Scope:** Header and all sections: which PR #50 head of `handover/tickets/P1.md`
*   **Discrepancy Description:** The ticket says "PR50 head = 2e8a28c" but quotes numbers from the local head 748849c without saying so. The two heads differ outside `textnorm.py` and `_confusables.py` (those two have identical sha in both manifests). Per-head values: test_promoted_controls def lines: 2e8a28c 766/777/799/803/842/855/871/881/910/950/962 (1863 and 2068 same), vs 748849c 764/775/795/801/840/853/869/879/908/948/960 (ticket uses these). `promoted_mutants.py`: 1,425 lines at 2e8a28c vs 2,149 at 748849c; the ticket's ranges 371-448, 639-709, 1033-1047 and 1159 match 748849c (at 2e8a28c the same mutants start 358, 623, 1016 and 1142). `tools/mutation_runner.py`: 255 lines at 2e8a28c vs 295 at 748849c. `testing/mutation.py`: 95 vs 105. `textnorm_manifest.json`: 5 files at 2e8a28c vs 11 at 748849c (the ticket says 11). "Carry PR50's runner (about 400 lines)" is about 350 at 2e8a28c.
*   **Rationale:** evidence: Greps and Reads of both snapshots, as listed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(6): every number is measured against PR #50's LOCAL head 748849c; this replaces the earlier instruction to use 2e8a28c. The finding is valid: the reviewer cites evidence that can be read (Greps and Reads of both snapshots, as listed.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Header and all sections: which PR #50 head
    *   Change: Name the head for every number. Decide which head P1a takes the tests, runner and manifest from. Recompute the line numbers. Run fail-before on the same head that supplies the tests.

### [Issue 20] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** P1b gap 4 row and Interface ("`id_key` gains dash/slash/quote tidy-up") of `handover/tickets/P1.md`
*   **Discrepancy Description:** The `id_key` change is a no-op, and its fail-before row cannot fail. `id_key` is `squeeze(loose=True)`, and `squeeze` strips every non-`[A-Z0-9]` character. `id_key("INV-2026")` and `id_key("INV‐2026")` are already equal on PR #50. The ticket's own probe uses `fold_key` (the identity key), which is where the bug is. Memo-1 section 6 says the same inconsistent thing.
*   **Rationale:** evidence: `textnorm.py:48` (`_NON_ALNUM`) and `:86` (`squeeze`) on 2e8a28c. Memo-1 gap 4 says "squeeze hides this".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`textnorm.py:48` (`_NON_ALNUM`) and `:86` (`squeeze`) on 2e8a28c. Memo-1 gap 4 says "squeeze hides this".). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 4 row and Interface ("`id_key` gains dash/slash/quote tidy-up")
    *   Change: Say which view gets the dash/slash/quote map: `identity_key` and the scan views. Drop the `id_key` claim, or define an `id_key` that keeps punctuation. Make the fail-before rows call the function that actually changes. Add a typographic-quote row (the table only has U+2010/2013/2014/2212/2044/2215).

### [Issue 21] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** P1b "Decided choices" vs Interface of `handover/tickets/P1.md`
*   **Discrepancy Description:** The identity key contradicts itself. It is "ONE stable key" (F4, gap 1, `identity_key(raw) -> str`), yet "the identity key keeps BOTH readings (3 and z)" for Cyrillic Ze. A single `str` cannot hold both readings unless a combining rule is defined, and the ticket gives none. The gap table has no Ze row, so there is no fail-before test. The mutant "Ze keeps only one reading in the identity key" has no killer.
*   **Rationale:** evidence: Ticket lines 69 and 83. `_confusables.py:105,123` (U+0417 and U+0437 both map to "3"). A9 F4 line 20.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(4). The finding is valid: the reviewer cites evidence that can be read (Ticket lines 69 and 83. `_confusables.py:105,123` (U+0417 and U+0437 both map to "3"). A9 F4 line 20.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b "Decided choices" vs Interface
    *   Change: Define the exact encoding (for example a fixed-order joined string, or the identity key stays one string and Ze lives only in the key-set). Add the Ze row with a fail-before test. Say what `identity_key("з")` returns.

### [Issue 22] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** P1b "Fail-before (must fail on `2e8a28c`)" of `handover/tickets/P1.md`
*   **Discrepancy Description:** The P1b fail-before tests, as worded, call names that do not exist on 2e8a28c (`identity_key`, `scan_views`, `line_view`, `id_key`). They would fail with ImportError or AttributeError, not by the gap assertion. That proves nothing about gaps 1-5 and 7, and the ticket demands KILLED, not CRASH, elsewhere. The gap behaviour is only visible against P1a's head, where `identity_key = fold_key`. F4 names 2e8a28c, but P1b's baseline is P1a.
*   **Rationale:** evidence: `textnorm.py` on 2e8a28c has no such names. Ticket lines 46 (the P1a note) and 71-78.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`textnorm.py` on 2e8a28c has no such names. Ticket lines 46 (the P1a note) and 71-78.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b "Fail-before (must fail on `2e8a28c`)"
    *   Change: For P1b, run the old-code step on both 2e8a28c and the merged P1a head. The assertion-level failure must be shown on P1a head, or the tests must call `fold`/`fold_key` for the old side.

### [Issue 23] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** P1a Tests list (13 "textnorm-only" tests) of `handover/tickets/P1.md`
*   **Discrepancy Description:** Two of the 13 moved tests are not textnorm-only. `test_the_micro_and_ohm_signs...` calls `check_text(...)` from `guard.egress_text`. `test_a_newline_or_tab...` calls `egress_text.check_text(..., LeakPolicy.payments())`. `egress_text` is not in core (P2d). The test file imports `egress_text`, `LeakPolicy` and `tools.mutation_runner` at module level. The ticket does not say the two tests must be cut down.
*   **Rationale:** evidence: 748849c `tests/test_promoted_controls.py` lines 873 and 1869; imports at lines 22-28.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (748849c `tests/test_promoted_controls.py` lines 873 and 1869; imports at lines 22-28.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a Tests list (13 "textnorm-only" tests)
    *   Change: List the two tests as "edited: egress lines removed". Say the new test module imports only textnorm. Say whether the mutant "mixed: the micro sign is flagged" still has its killer after the edit.

### [Issue 24] [`egm-codebase-details`] - Severity: Major (finding id C6, correctness)
*   **Affected Scope:** P1a Tests / "Vendored Unicode data: NOT in P1a" of `handover/tickets/P1.md`
*   **Discrepancy Description:** The ticket moves the generator tests (879, 908, 2068) into P1a but does not vendor `tools/data/confusables.txt`. `test_the_generator_reproduces_the_checked_in_table_offline` does `(root/"tools"/"data"/"confusables.txt").read_bytes()` with no skip, so it raises FileNotFoundError in CI. The ticket says only "cannot run in CI" without saying what the moved test does. The mutant "table: the vendored data file differs from the pin" targets the missing file. Also the data file is in BOTH PR #50 heads, so "take it from `origin/handover-src/pr50-local-748849c`" is not needed.
*   **Rationale:** evidence: 748849c test lines 2068-2094; `tools/data/confusables.txt` exists in 2e8a28c and 748849c (9,862 lines, version 18.0.0, 2026-08-06, as the ticket says). Memo-5 line 28 lists the data file and `.gitattributes` in P1's files.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (748849c test lines 2068-2094; `tools/data/confusables.txt` exists in 2e8a28c and 748849c (9,862 lines, version 18.0.0, 2026-08-06, as the ticket says). Memo-5 l). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a Tests / "Vendored Unicode data: NOT in P1a"
    *   Change: State for each of tests 881/910/2068 and the three generator mutants: dropped, skipped with a visible reason, or run only by the evidence runner. If the data file is not committed, `.gitattributes` `-text` is not needed, but say so.

### [Issue 25] [`egm-codebase-details`] - Severity: Major (finding id C7, correctness)
*   **Affected Scope:** P1a Fail-before of `handover/tickets/P1.md`
*   **Discrepancy Description:** The claim "non-`str` input not a clear TypeError" is false for PR #50. `fold(123)` and `fold(None)` already raise TypeError from `unicodedata.normalize`, so a `pytest.raises(TypeError)` test passes on 2e8a28c and is not a fail-before test. Related hazards: `has_mixed_script(b"abc")` raises AttributeError (iterating bytes gives ints, then `.isspace()`), and `allow_equal(1, 1)` returns EQUAL because it compares `a == b` first. The ticket says "non-`str` raises TypeError" without saying which functions, so it is under-specified for ALLOW.
*   **Rationale:** evidence: `textnorm.py:67` (`normalize` raises TypeError), `:121` (`a == b`), `:159-162` (`isspace` on ints) on 2e8a28c.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`textnorm.py:67` (`normalize` raises TypeError), `:121` (`a == b`), `:159-162` (`isspace` on ints) on 2e8a28c.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a Fail-before
    *   Change: Drop that item from the fail-before list or test the message. Specify non-`str` handling for `allow_equal`, `same_person`, `names_equal` and `has_mixed_script`.

### [Issue 26] [`egm-codebase-details`] - Severity: Major (finding id C8, correctness)
*   **Affected Scope:** P1b Tests ("`line_view` never grows the text beyond the cap") and gap 7 Fix of `handover/tickets/P1.md`
*   **Discrepancy Description:** The property is false as written. NFKC (applied after the entity step) expands text: U+FDFA gives 18 characters, and `&#xFDFA;` is 8 characters before and 18 after. The ticket's own measurement notes the 18-fold expansion. "Entities only shorten text" holds only for the entity step. The cap is also on input length, not output.
*   **Rationale:** evidence: Ticket lines 17 and 78. Core `guard/runmap.py:139-156` already solves this (`_expanded_len`, `fits_after_nfkc` refuse before normalising).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 17 and 78. Core `guard/runmap.py:139-156` already solves this (`_expanded_len`, `fits_after_nfkc` refuse before normalising).). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b Tests ("`line_view` never grows the text beyond the cap") and gap 7 Fix
    *   Change: State which length the cap bounds (input or expanded output). Rewrite the property accordingly, or reuse the `_expanded_len` idea. Add hostile rows `&#xFDFA;` x 2,500 and entity + NFKC at the cap.

### [Issue 27] [`egm-codebase-details`] - Severity: Major (finding id C9, correctness)
*   **Affected Scope:** P1b Interface (`scan_views`) of `handover/tickets/P1.md`
*   **Discrepancy Description:** The key-set is undefined. "for case-ambiguous letters the extra case readings" can be read as 2^k keys for k ambiguous letters (20,000 "η" characters gives a blow-up). Memo-1 gap 1b means two keys (key of the text, key of the case-swapped text; any overlap is a hit). The ticket does not fix the number, order or maximum size of the tuple. The template requires exact interfaces. `line_view`'s errors and cap behaviour are also not stated.
*   **Rationale:** evidence: Ticket line 68 vs memo-1 line 59.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket line 68 vs memo-1 line 59.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b Interface (`scan_views`)
    *   Change: Specify `scan_views` exactly: the element list, a fixed order, no duplicates, a maximum length. Say the case readings are whole-text readings, not per-letter products. Add a hostile test for the maximum.

### [Issue 28] [`egm-design`] - Severity: Nit (finding id A18, adversarial)
*   **Affected Scope:** P1a privacy claim of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Stored keys are SHA-256 digests, never the folded text" is presented as personal-data protection. An unsalted digest of a name or an account number is dictionary-reversible, and equal inputs are linkable across tables. Comparisons use `==`.
*   **Rationale:** evidence: Ticket line 17, 40.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket line 17, 40.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a privacy claim
    *   Change: Say plainly it is a pseudonym, not protection. Use a keyed hash (HMAC, key through the secrets kind) if the storage claim matters, and `hmac.compare_digest`.

### [Issue 29] [`egm-design`] - Severity: Nit (finding id A19, adversarial)
*   **Affected Scope:** P1b gap 5 of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Dropped characters become a space" is ambiguous (one word, one meaning). NFKD runs first, so a precomposed "é" splits into `e` + a mark, and the mark becomes a space ("résumé" gives "re sume "). Whether Mn, Cn, Co, Cs count as "dropped" is not stated.
*   **Rationale:** evidence: Ticket line 77; PR50 line 71.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket line 77; PR50 line 71.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b gap 5
    *   Change: List the exact categories that split (suggest Cf, Cc, Zl, Zp, fillers, not Mn) and add a row for a decomposed accented word.

### [Issue 30] [`egm-design`] - Severity: Nit (finding id A20, adversarial)
*   **Affected Scope:** P1a/P1b hard-coded values of `handover/tickets/P1.md`
*   **Discrepancy Description:** The values 20,000, 8 rounds, the cache default, 3.13 and the golden are stated in several places. The cache default and the entity limit have no name in `defaults.py`; the ticket lists only one new line. There is an existing 262,144-character `MAX_REDACT_CHARS` that P2d will have to reconcile with 20,000, and `test_no_hardcoded_values` is not checked against the new constants.
*   **Rationale:** evidence: Ticket lines 35, 68, 78; `defaults.py` lines 31-40.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 35, 68, 78; `defaults.py` lines 31-40.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a/P1b hard-coded values
    *   Change: Declare all numeric constants now with names in `defaults.py`. Decide the fold cap's relation to `MAX_REDACT_CHARS` in this ticket.

### [Issue 31] [`egm-design`] - Severity: Nit (finding id A21, adversarial)
*   **Affected Scope:** P1a fail-before of `handover/tickets/P1.md`
*   **Discrepancy Description:** Copying the P1a tests into the PR50 worktree fails at import (`FOLD_VERSION`, `view`, `stored_key` do not exist), not at an assertion. That proves nothing about whether the assertions bite.
*   **Rationale:** evidence: Ticket lines 46-47.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 46-47.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a fail-before
    *   Change: Run each new assertion against a shim that has the names but the old behaviour.

### [Issue 32] [`egm-design`] - Severity: Nit (finding id A22, adversarial)
*   **Affected Scope:** P1a docs of `handover/tickets/P1.md`
*   **Discrepancy Description:** `has_mixed_script` uses a curated prefix list of script names (Runic, Tamil, Bopomofo, Ethiopic, Sinhala and others are absent). The ticket calls it the "fail-closed backstop" and moves it without a fix or a test for an unlisted script.
*   **Rationale:** evidence: PR50 lines 136-139, 154-158.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (PR50 lines 136-139, 154-158.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a docs
    *   Change: Add a hostile row for an unlisted script and state the limit in the ticket's honesty section.

### [Issue 33] [`egm-design`] - Severity: Nit (finding id A23, adversarial)
*   **Affected Scope:** Ticket wording of `handover/tickets/P1.md`
*   **Discrepancy Description:** Mixed terms: "scan view" (one key vs a tuple vs `scan_views`), "identity key" vs "identity view", "key" for both a string and a digest, "version" for `FOLD_VERSION`, the algorithm id and `ud=`. The probe claims "Python 3.13.18"; this ticket was not able to confirm that patch version.
*   **Rationale:** evidence: Ticket lines 38-40, 69, 80.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 38-40, 69, 80.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Ticket wording
    *   Change: Define key (folded text), digest (stored form) and view (a named function) once at the top.

### [Issue 34] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** P1a/P1b Files list of `handover/tickets/P1.md`
*   **Discrepancy Description:** The Files list is incomplete. It omits `tests/textnorm_mutants.py` (the evidence command runs it), the mutation runner and judge files (only mentioned under Decision 3), and the test-guard entry from C1. P1b's cache byte bound "default from `defaults.py`", but `defaults.py` is not in P1b's change list. The 8-round entity limit is a number in code, against studio rule 4. P1a says the manifest lists "its own four" files without naming them.
*   **Rationale:** evidence: Ticket lines 35, 47, 58, 67, 68.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (Ticket lines 35, 47, 58, 67, 68.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1a/P1b Files list
    *   Change: Complete the list and name the four manifest files. Put the bounds in `defaults.py`.

### [Issue 35] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** P1b Mutation plan of `handover/tickets/P1.md`
*   **Discrepancy Description:** The 27 reused mutants match exact source strings (for example `.translate(_DIGITS).translate(_TABLE)`, the `_DROP_CATEGORIES` set text). P1b rewrites that code (gap 1 order, gap 2 drop). Most "fold:" mutants will no longer apply (ERROR or NO_TESTS). Their `test_...` ids also point at the old test file. The plan only lists new mutants.
*   **Rationale:** evidence: 748849c `tests/promoted_mutants.py:371-398`, `:1159-1165`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (748849c `tests/promoted_mutants.py:371-398`, `:1159-1165`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: P1b Mutation plan
    *   Change: Add "re-point the 27 mutants to the P1b text and the new test ids" to P1b.

### [Issue 36] [`egm-codebase-details`] - Severity: Nit (finding id C13, correctness)
*   **Affected Scope:** Gap 7 source claims of `handover/tickets/P1.md`
*   **Discrepancy Description:** Line numbers are wrong. `_unescape` is at lines 447-454, not 431-438 (431-438 is inside the message table). `_f` is lines 465-481, not 465-486 (484+ is `_SEPLIKE`). Correct: `_BREAKS` at 342, `_WS` at 392, imports at 94-110, step order as listed, 8 rounds. "ten call sites": `_f(` appears on 10 lines (501, 757, 1008, 1040, 1060, 1180, 1181, 1340, 1345, 1363) but 13 calls.
*   **Rationale:** evidence: `intake-wp3/src/intake/invoicecheck.py`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`intake-wp3/src/intake/invoicecheck.py`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Gap 7 source claims
    *   Change: Fix the numbers.

### [Issue 37] [`egm-codebase-details`] - Severity: Nit (finding id C14, correctness)
*   **Affected Scope:** Template fields of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Extended review (no round cap): yes/no" is not stated (Tier A text only). The template's order is not kept at top level (Files, Tests, Mutation, Evidence live only in the sub-tickets; "Existing core code reused" comes before "Security"). Review files are named `reviews/P1a-round<n>.md`, but the folder uses `P1-round1-adversarial.md`, `P3a-round1-correctness.md`.
*   **Rationale:** evidence: `TICKET-TEMPLATE.md` line 4; `reviews/` listing.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`TICKET-TEMPLATE.md` line 4; `reviews/` listing.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Template fields
    *   Change: Add an explicit "Extended review: yes". Align the review file names with the folder convention.

### [Issue 38] [`egm-codebase-details`] - Severity: Nit (finding id C15, correctness)
*   **Affected Scope:** Mapping table (verified claim) of `handover/tickets/P1.md`
*   **Discrepancy Description:** "verified by reading both files": there is no PR #49 file on disk in any snapshot, so the PR #49 signatures and semantics cannot be checked. Memo-1 gives only the names and "5 scripts". Also, the `mixed_script` row says "more words are flagged", but the unit-symbol exemption and the newline/tab word break make some words not flagged (PR #50 code: `has_mixed_script` lines 141-143, 160). A9 F4 maps the three PR #49 functions to `allow_equal, fold_key, has_mixed_script`. The ticket maps `confusable_not_equal` to `allow_equal` and puts `fold_key` nowhere in the table.
*   **Rationale:** evidence: `textnorm.py:141-168` (2e8a28c). A9 F4 line 20.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`textnorm.py:141-168` (2e8a28c). A9 F4 line 20.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Mapping table (verified claim)
    *   Change: Reword "verified" to "from memo-1 and PR #50". Say both directions for the `mixed_script` row. Explain the `fold_key` deviation from F4.

### [Issue 39] [`egm-codebase-details`] - Severity: Nit (finding id C16, correctness)
*   **Affected Scope:** Interface (cap and TextTooLong) of `handover/tickets/P1.md`
*   **Discrepancy Description:** Cap coverage is unclear. The cap is stated for `fold`, the views and `has_mixed_script`. `allow_equal` runs `a == b`, then `_canon` (not capped), then `same_person` (via `fold`, which would raise). `names_equal` uses only `_canon`. So an ALLOW check can raise `TextTooLong` for two long different strings, or not, depending on the path. PR #50's docstring says the length is not bounded there.
*   **Rationale:** evidence: `textnorm.py:89-90,118-133`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`textnorm.py:89-90,118-133`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (cap and TextTooLong)
    *   Change: State the cap for `squeeze`, `same_person`, `allow_equal` and `names_equal`, and the exception contract for ALLOW (refuse).

### [Issue 40] [`egm-codebase-details`] - Severity: Nit (finding id C17, correctness)
*   **Affected Scope:** Interface (`FOLD_VERSION`, `stored_key`) of `handover/tickets/P1.md`
*   **Discrepancy Description:** `tbl=41740c11` is the sha of the generated `_confusables.py` file, not `DATA_SHA256` (6ed3ee96, the UTS #39 data). "Built at import" would need file access, which the ticket's "no file access at run time" forbids, so it must be a constant. `ucd=18.0.0` is `DATA_VERSION`. Also `stored_key` is an unsalted SHA-256 of low-entropy text (names, account numbers), so "digests, never the text" is not privacy protection.
*   **Rationale:** evidence: `_confusables.py:8-11`. Ticket lines 17 and 38-40.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`_confusables.py:8-11`. Ticket lines 17 and 38-40.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (`FOLD_VERSION`, `stored_key`)
    *   Change: Say which file the sha is of, and that it is a constant checked by a test. Do not describe the digest as protection, or use a keyed digest.

### [Issue 41] [`egm-codebase-details`] - Severity: Nit (finding id C18, correctness)
*   **Affected Scope:** Tests (P1a) of `handover/tickets/P1.md`
*   **Discrepancy Description:** The time-ratio and 8-thread tests are in `test_textnorm.py` with no `perf` marker. CI runs `-m "not live and not perf"` and a separate blocking perf step (`ci.yml:88-94`), and the review-loop rule says timing tests run alone.
*   **Rationale:** evidence: `.github/workflows/ci.yml:88-94`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`.github/workflows/ci.yml:88-94`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Tests (P1a)
    *   Change: Mark the timing test `perf`.

### [Issue 42] [`egm-codebase-details`] - Severity: Nit (finding id C19, correctness)
*   **Affected Scope:** Evidence commands of `handover/tickets/P1.md`
*   **Discrepancy Description:** They differ from CI: CI runs `ruff check src tests demos` and `bandit -q -r src demos -ll`; the ticket runs plain `ruff check` and `bandit -ll -r src`. CI has Python 3.13 only (`ci.yml:73,109`), so "reported on the other CI interpreter" (F3) never happens in CI; only the local 3.12 run shows it.
*   **Rationale:** evidence: `ci.yml:73,79,81,119`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`ci.yml:73,79,81,119`.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Evidence commands
    *   Change: Use CI's exact commands. State that the 3.12 side is local only.

### [Issue 43] [`egm-codebase-details`] - Severity: Nit (finding id C20, correctness)
*   **Affected Scope:** Hot files / Decision 6 of `handover/tickets/P1.md`
*   **Discrepancy Description:** "P2a and P2d also touch `textnorm_manifest.json`" is not in memo-5 (only P1 is listed for it, line 28). The ticket does not say whether P2a, P2d, P3b and P5a wait for P1a or P1b. P3b's mapping targets P1a names whose behaviour P1b changes (the key output). Rule 9(f)/(g) (`identity`/`rights`/`dev_only` for the textnorm kind) is deferred to "UNVERIFIED at ce70eb5". F3 says Python 3.14 is probed in P1; the ticket leaves it to the evidence runner.
*   **Rationale:** evidence: `memo-5-overlap.md:15,28,86`; plan-v3 rule 9.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`memo-5-overlap.md:15,28,86`; plan-v3 rule 9.). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hot files / Decision 6
    *   Change: Say which sub-ticket each downstream package depends on. Cite the source for the P2a/P2d claim or drop it. State who adds the `dev_only` flag for the textnorm kind.

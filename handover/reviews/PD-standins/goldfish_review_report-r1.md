Status: resolved

# Goldfish Annotated Review Report

**Target:** `wip/cloud-pd-standins` head 9c831f70 (promotion part 3: kind classification and loopback-only stand-ins), round 1, MODE-SAFETY path (no round cap).
**Reviews read:** `pdst9c831f70-design-r1.md` (0 Blocker, 6 Major, 4 Minor, 3 Nit) and `pdst9c831f70-codebase-r1.md` (0 Blocker, 2 Major, 5 Minor, 3 Nit). Snapshot `/home/user/build/snap/pd-standins-9c831f70`.
**Evidence state:** builder evidence only (unverified by me). No independent evidence exists yet. The batch-2 builder must re-run the gates at the final head; an independent EVIDENCE RUNNER follows before the confirming round.

## Classes first (8 Majors fall into 4 classes)
1. **Registry rules not enforced at the choke point** (D1, D2, D3, D4; codebase Minors 3, 4, 5; design Minors: empty host list, `entry.hosts` raising). The rules exist, but a name guess (`_HOST_LIKE`), a loader-only call (`_one`), tests-only enforcement and a NOT_PROD hole let a stand-in reach a non-loopback host or a pilot.
2. **Sibling loopback sets not consolidated** (D5, codebase M1). The part-2 helper `netguard` exists, nothing migrated; six inline copies remain; two definitions of "loopback".
3. **Weak mutation proof** (D6, codebase Minor 7, Minor 6). Two guards are not mutation-proven, no mutant flips `role`, none for an empty list, S6 pins statement text.
4. **Documentation claims that disagree with the code** (codebase M2 six versus seven stand-ins; D2 sentence "a pilot or prod config refuses it"; netguard docstring "can all ask here"; PR body "netguard merged unchanged").

## Prioritized Findings & AI Suggestions

### [Group 1] [`design` + `codebase-details`] - Severity: Major (D1, D2, D3, D4)
*   **Affected Scope:** `src/hadavin_sdk/backends/table.py` (`_HOST_LIKE`, `registry_problems`, `assert_registry_sound`), `src/hadavin_sdk/config.py` (`_one`, `stand_in_host_problem`, `Config._cross_checks`, DEMO_ONLY / NOT_PROD checks ~414-440).
*   **Discrepancy Description:** (D1) host detection by field name misses `api_base`, `base`, `dsn`, `uri`, `server`, `origin`, `domain`, `proxy`, `broker`, `target`, `remote` (the real Slack kind reads `s.api_base`); a stand-in with `hosts=None` passes. (D2) NOT_PROD is refused only in prod, so a stand-in listed only in NOT_PROD runs in a pilot with client data; PR body and CHANGELOG say a pilot refuses it. (D3) rules 2 and 3 run only in this repo's tests; a downstream user adding a kind gets no refusal. (D4) the host rule is called only from the loader `_one`; `Backends(...)` or `Config(...)` built directly skip it. Plus: an empty hosts list passes (`all([])`); `entry.hosts(settings)` can raise a bare `ValueError`.
*   ***AI Suggestion:*** PROPOSE FIX (all Majors valid; no contest).
*   ***Justification:*** each is a mode-safety hole in the same class: the rule is not where every caller routes. The recommended fix is at the one choke point.
*   ***Proposed Edit:***
    *   D1: invert rule 3. Every stand-in MUST declare `hosts` explicitly (`hosts=lambda s: []` is a deliberate, tested "none"); keep the name regex only as an extra net, widened with the words above, and add a type-based check where the settings model has URL/host typed fields. An empty list is accepted only when the kind has no host-like or URL-typed field. Plants: `api_base`, `dsn`, `proxy`.
    *   D2: stand-ins must be in DEMO_ONLY (refused in every live stage). NOT_PROD is allowed only for a stand-in that is also in a named, tested exception list (today: `signer/none`, `anchor/none`, which are in-process). Correct the CHANGELOG and PR body sentence to the exact rule.
    *   D3: enforce ALL of `registry_problems` at the first use, not only at import: call it from `parse_backends` and from a `Backends` model validator, so a downstream kind is checked the moment a config is built. Keep the import-time check for classification only. REASON: the builder measured that raising on every rule at import crashed 5 of the 37 stage mutants before their pinned test ran. Enforcing at first use keeps those mutants reaching their tests. Gate: `tests/stage_mutants.py` must still print 37 of 37 good and the new mutants must still pass.
    *   D4: put `stand_in_host_problem` in a `Backends` validator (or `Config._cross_checks` beside the DEMO_ONLY check), so every construction path hits it; `_one` keeps only the error wording. Plant that builds `Backends` directly. Wrap `entry.hosts(settings)` so a raise becomes the same fixed-sentence refusal. Confirm `KindSettings` hides input in errors (design Minor 3, `config.py:137` echoes `{exc}`): add a test with a canary value.

### [Group 2] [`design` + `codebase-details`] - Severity: Major (D5, M1)
*   **Affected Scope:** `src/hadavin_sdk/netguard.py` (part-2 helper, `LOOPBACK_LITERALS`, `is_loopback_literal`), inline sets at `backends/table.py:68`, `config.py:186` (`url_allowed`), `guard/http.py:21`, `llm/openai_compat.py:37`, `actions/secrets_vault.py:67`, `store/postgres.py:55/63`.
*   **Discrepancy Description:** the brief says "grep siblings, fix at the shared choke point, improve before replace". A sixth copy is effectively added; `is_loopback_literal` has no caller in src; the netguard docstring is false; the stand-in rule accepts 127/8 and mapped IPv6, the clients accept three literals.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** fix-dont-defer: a deferral is allowed only for impossible, owner-only or third-party items, and none applies. The class is "one word, one meaning" for loopback.
*   ***Proposed Edit:*** migrate the six sites to `netguard` (exact-literal check `is_loopback_literal` where clients must stay strict; `is_loopback_host` for the stand-in rule), and state in one place which of the two meanings each site needs and why (the 127/8 versus three-literal difference: align to the three exact literals plus `::1` unless a test needs more; document the choice). Grep for every sibling (`127.0.0.1`, `"localhost"`, `"::1"`, `ipaddress`) and list the result in the PR body. Add a test that fails when a new inline loopback set appears in src (a source scan with an allowlist of `netguard.py` only). Dependency: part 2's builder (agent a1429b44bc7851c5a, `wip/cloud-pd-bind`) is still working; batch 2 must be based on the part-2 head that is current when batch 2 starts and must say which sha.

### [Group 3] [`design` + `codebase-details`] - Severity: Major (D6; codebase Minors 6 and 7)
*   **Affected Scope:** `tests/standin_mutants.py`, `tests/test_kind_registry.py:579-590, :655, :683`, `tests/test_stand_in_hosts.py` (fuzz, `planted` fixture).
*   **Discrepancy Description:** the reason given for dropping two mutants does not fit the code (the import guard runs only `_unclassified`); no mutant flips an entry `role` from `stand_in` to `real` (the one mislabel that disables every rule); none for `all()` over an empty list, `re.IGNORECASE`, the `role != "stand_in"` skip or the `hosts is None` short-circuit; S6 is killed by an AST text test, not by behaviour; the 2000-host fuzz has no seen-true/seen-false assertion and hand-mutates the global TABLE.
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** one mutant per code item is the standing requirement; two guards without mutation proof are a gap.
*   ***Proposed Edit:*** after Group 1 moves enforcement to first use, re-try the two dropped mutants (they now reach their pinned tests); find the real cause of the earlier ERROR (do not repeat the unverified explanation); add mutants for role flip, empty list, `IGNORECASE`, the skip and the short-circuit; replace the S6 AST test with a behaviour test (reload `table.py` with a role-less entry, expect `RuntimeError`); add seen-true/seen-false to the fuzz and use `monkeypatch` instead of hand-mutating `TABLE`; one result per mutant with the killing test and the failure reason.

### [Group 4] [`codebase-details` + `design`] - Severity: Major (M2) with documentation items
*   **Affected Scope:** `CHANGELOG.md:22`, PR body `/home/user/build/PD-standins-PR-BODY.md`, `netguard.py:1-3` docstring.
*   **Discrepancy Description:** CHANGELOG lists six stand-ins, code and test have seven (`secrets/fake` missing); "a pilot or prod config refuses it" is false for NOT_PROD (Group 1 D2); the netguard docstring says other modules ask it (false until Group 2); the PR body says netguard was "merged unchanged" while the diff shows it as new files against main (credit belongs to part 2).
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** a document contradicting the code is a defect, and one word keeps one meaning (wording rule).
*   ***Proposed Edit:*** list all seven; state the exact stage rule once; fix the docstring after Group 2 (or word it as a fact of the code); PR body: say netguard comes from the part-2 package (cite its branch and sha) and that part 3 depends on it. Recompute every count in CHANGELOG and PR body at the final head.

### [Group 5] [`design`] - Severity: Minor
*   **Affected Scope:** `config.py:137` (echo of `{exc}`), `netguard.is_loopback_host` docstring, `config.py:411`.
*   **Discrepancy Description:** the "never echo" claim covers only the new path; loopback is by name and ignores the port (a proxy or forwarder on 127.0.0.1 can carry traffic off the computer); `config.py:411` echoes `system.base_url` (old).
*   ***AI Suggestion:*** PROPOSE FIX.
*   ***Justification:*** cheap, same file, same class (refusal text must not echo values).
*   ***Proposed Edit:*** canary test over the refusal paths of `_one`; if one echoes, route it through the fixed-sentence helper; one docstring line on the loopback limits (name not resolved, port ignored, no proxy awareness).

### [Group 6] [`design` + `codebase-details`] - Severity: Nit
*   **Affected Scope:** `registry_problems` (`n != "kind"`), `tests/test_stand_in_hosts.py:925-928`, `test_a_real_kind_may_name_any_host`, `hostname_hint`.
*   **AI Suggestion:** DECLINE as separate work; fix in the same push only where the line is touched anyway (dead `n != "kind"`, stray docstring, try/except). Recorded, no new review.

### [Group 7] LEAD ITEMS (not fixes)
*   Licence: part 3 copied no demo code (design only); the question of the evaluation-only demo licence remains with the lead (see part 2 question in `questions-for-lead.md`).
*   The lead opens the draft PR after the confirming round; PR body goes in `/home/user/build/PD-standins-PR-BODY.md`.

## Handoff
*   Accepted fixes (PROPOSE FIX): 5 groups (1, 2, 3, 4, 5), covering the 8 Majors and all 9 Minors; contested: 0; escalated: 0 (the licence question is a lead item, not a finding); declined: 1 group (Nits, fixed only where touched); remaining unaddressed issues: 0 findings, but D3 carries a known trap (see Who fixes it).
*   **Who fixes it:** one batch-2 builder, branch `core/promote-demo-standins` from 9c831f70 (rebased or merged onto the current part-2 head, sha stated), plain push to `wip/cloud-pd-standins`. Method: name the 4 classes first, fix at the shared choke point, grep siblings, new tests shown failing on 9c831f70, one mutant per fix, ONE full suite, `stage_mutants` (must stay 37 of 37), `standin_mutants`, ruff, format, bandit, scan_repo, gitleaks once at the final head via `/home/user/build/heavy.sh`; builder returns once. Then an independent EVIDENCE RUNNER on the final head, then the two reviewers once (ORDER 256 A: this is mode-safety code, so ONE confirming round, not more after a clean one), then READY.
*   **Recommendation:** after batch 2 run exactly one confirming round (design + codebase). If it shows 0 Blocker and 0 Major, fix the minors in one push without another review and mark the package READY; if it shows a Major, fix and repeat (mode-safety has no cap).

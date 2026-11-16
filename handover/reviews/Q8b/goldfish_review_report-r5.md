Status: resolved

# Goldfish Annotated Review Report (Q8b, round 5)

**Target:** branch `core/q8b-partial-mask-and-card-redaction`, head `999ed05b`. Partial-mask and card redaction (redaction path, no round cap). No person was available: recommended option for every item. Reviews (both read-only, nothing run; findings are hand traces): `handover/reviews/Q8b/q8bb4-design-r5.md` (1 Blocker, 4 Nit) and `q8bb4-codebase-r5.md` (1 Major, 5 Nit). Evidence (independent, head confirmed): `handover/evidence/Q8b/999ed05b/RESULTS.md` and `probe-table.md`: full pytest 10766 passed, 1 skipped, 16 xfailed; `q8b_mutants` 75 of 75; `mutation_runner_mutants` 64 of 64 as root and as non-root; `stage_mutants` 37 of 37; ruff, format, bandit, scan_repo, gitleaks exit 0; fail-before on `4091f8b1` 23 failed with 8 batch4 tests passing on old code; hostile probe: readable key cases main 94 of 168, head 8 of 168. The evidence runner did NOT probe the F1 cookie input, so Issue 1 is unconfirmed by running. The probe covers only `redact()` and `redact_text`, not the record walk or the cards. The timing test failed 6 of 6 on head and main (known flaky, fix on `core/fix-timing-harness-flake`). Not run: perf, semgrep, zizmor, CodeQL, Windows, Vault.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/guard/redact.py:117` and `:650-653` (`_COOKIE_ASSIGN_KEY`, lookbehind `(?<!session[_\-])`); generic key rule `:161`, `:238-240`.
*   **Discrepancy Description:** The delta adds a lookbehind to the cookie-assignment rule so that `session_cookie` is taken by the generic key rule. Main's cookie rule took the `;`-joined `name=value` pairs after the value as part of the secret (`session_cookie=abc; csrf=xyz; user=bob` fully masked). The generic rule stops at `;` + space or `;` + a key, so only `abc` is masked. Input `x session_cookie=Zq7xV; csrf=Kp9wT; user=Hn4bL y` gives `session_cookie=<SECRET_1>; csrf=Kp9wT; user=Hn4bL` (by reading, not run). The `:` header form is still safe. Neither the oracle (`tests/q8b_older_rule.py`, which holds only the two quoted rules and the unquoted rule) nor mutant M73 (killed by a space-only test) sees it. This is a regression against main and breaks the "superset" claim.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Redaction regression versus main, uncapped path. Fix at the choke point: the cookie jar pair tail.
*   ***Proposed Edit:*** (1) Reproduce by running the input on head and on `origin/main` (card, tool and log paths) and record both raw outputs. (2) Restore the whole-value masking: give the `session_cookie` form the cookie rule's pair tail `(?:;\s*[^\s;=]+=[^\s;]*)*` (drop the lookbehind and keep the cookie rule for it, or let the generic rule take the same tail for cookie keys). (3) Class check: search every other key the lookbehind or the generic rule now owns that main's cookie rule used to take (`auth_cookie`, `*_cookie`, `set_cookie`). (4) Add the cookie rule to the oracle; rows with `; ` and bare `;` separators and a `,` separator; a mutant that removes the pair tail; prove the new rows fail on `999ed05b`.

### [Issue 2] [`codebase` F1] - Severity: Major
*   **Affected Scope:** `tests/test_q8b_batch4.py:173-181` (`test_j1_every_key_the_older_rule_masked_is_still_masked`); `tests/q8b_older_rule.py:575-582`.
*   **Discrepancy Description:** The test fails only when the whole text the older rule captured is still a substring of the output. A head that masks only the first word of `key="Zq7xV Kp9wT Hn4bL"` leaves two words readable and passes. The 300-plus generated keys (`_generated_keys`) get only this weak check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A test that cannot fail on the class it was written for (the half-masked defect). It is the same hole that let Issue 1 through.
*   ***Proposed Edit:*** Also fail when any of the plain pieces (`P1`, `P2`, `P3`) is readable in the output (`readable_pieces(out)`); keep `part in out` as a second check. Add values that contain `;` and `,`; run the oracle on the log path and the record walk too; prove the strengthened test fails on a head that masks only the first word.

### [Issue 3] [`design` F2 = `codebase` F2] - Severity: Nit
*   **Affected Scope:** `tests/q8b_older_rule.py:1-2, 7, 17`; `tests/test_q8b_batch4.py:176-179`; `tests/test_q8b_batch4.py:173-181`.
*   **Discrepancy Description:** The oracle covers three of main's key-bearing rules; comment line numbers are wrong (`575-590`, `591-613`; main has 577-590 and 591-616); the docstring says "the key rules of the code before Q8b"; the cookie rule, the `"auth"` JSON rule, flag rules and hex-key rule are not in it; run on card and tool paths only; keys come from a fixed list (~600-key sample), not the superset claim.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, and it closes the gap behind Issue 1.
*   ***Proposed Edit:*** Fix the line numbers; say "the three key rules" in the docstring; add the cookie rule (Issue 1) and a flag-rule row; run the log path.

### [Issue 4] [`design` F3] - Severity: Nit
*   **Affected Scope:** `k1b/redaction.py:155-156`, `:234` (`ORDINARY_WORDS`).
*   **Discrepancy Description:** `oauth` is on the ordinary-word list, so a record walk `{"oauth": token}` leaves it readable while the card rule `auth(?=["']?\s*[:=])` masks `oauth=<value>` as text. Not a regression (main did not match), but `oauth` is the one entry that plausibly names a credential holder. The evidence probe shows `oauth` masked on head in `=`, `:` and JSON text styles, so the disagreement is walk versus text.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Safe direction is to mask.
*   ***Proposed Edit:*** Remove `oauth` from `ORDINARY_WORDS` (fail closed) and test the record walk; if kept, test and write the disagreement into LIMITS.

### [Issue 5] [`design` F4] - Severity: Nit
*   **Affected Scope:** `redact.py:238-240` (`;` and `,` look-aheads use `[\w.\-]+`); `_KEY_STOP` `:245`; CHANGELOG line 10 ("12:30 is not a key").
*   **Discrepancy Description:** The look-ahead accepts a digit start while `_KEY_STOP` needs a letter or `_`; `password=ab;12:30x` stops at the separator and leaves `;12:30x` readable. Main stopped at `;` too (not a regression).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Two characters per look-ahead and a test; fixes the disagreement with the written claim.
*   ***Proposed Edit:*** Use `[A-Za-z_][\w.\-]*` in both look-aheads; add rows with a digit-led word after `;` and `,`.

### [Issue 6] [`design` F5 = `codebase` F5] - Severity: Nit
*   **Affected Scope:** CHANGELOG delta lines 10 and 14; `redaction.py:62` (LIMITS); `redact.py:169` comment; `redact.py:171` (`authorization` in `QUOTED_KEY_WORDS`); `test_q8b_batch2/4` pins.
*   **Discrepancy Description:** Claims not kept exactly: the `;` rule also stops before `"`, `'`, `,`, `&` and `;`; the record rule tests every word, not the last one (`newpass_enabled` masked); `password=ab;http://x` leaves `;http://x` readable (designed stop, not told); the superset claim is pinned by a sample, not the cookie rule; `authorization="a b"` alone has no test and no killer for dropping `|authorization` alone; the `_URL` lookbehind change `(?<![\w+.\-])` has no CHANGELOG line (stops removing `-https:` and `.mailto:` no-`//` schemes, visible card change); over-masking named only in part (`"authorization_endpoint": "https://..."`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Documentation claims are held to the same bar as code.
*   ***Proposed Edit:*** Reword each sentence to what the code does; add the `_URL` line; add an `authorization="a b"` test and a mutant dropping only `|authorization`; D-032 note below.

### [Issue 7] [`codebase` F3] - Severity: Nit
*   **Affected Scope:** `tests/test_q8b_batch2.py:652-712` (drift scan); `tests/test_q8b_batch4.py:351-361` (self-test).
*   **Discrepancy Description:** The Tuple/List/Set branch lower-cases but does not strip non-letters (`api_key`, `pass_word`, `"password passwd pwd secret".split()` not found) while the `|` branch strips to letters; BinOp concatenation not caught; the self-test re-implements the scan on a sample; `src/` only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The scan guards "one list of key words"; a self-test of a copy cannot fail when the real scan regresses.
*   ***Proposed Edit:*** One shared detection function used by both tests; strip non-letters in both branches; say in the docstring that `tools/` and `demos/` are out of scope.

### [Issue 8] [`codebase` F4] - Severity: Nit
*   **Affected Scope:** `tests/test_q8b_batch4.py:205-209` (`code.count("QUOTED_KEY_WORDS") == 3`).
*   **Discrepancy Description:** A string count, the shape round-4 Issue 5 asked to drop; behaviour is covered by M67 and the corpus test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fails on a harmless rename.
*   ***Proposed Edit:*** Delete it, or keep only `QUOTED_KEY_WORDS.startswith(KEY_WORDS)`.

### [Issue 9] [`codebase` F6] - Severity: Nit (mutant strength)
*   **Affected Scope:** `tests/q8b_mutants.py` M69 (expect `readable`), M70 (expect `expected`); `tests/test_q8b_batch4.py:219-222`.
*   **Discrepancy Description:** Generic expect fragments; the second assert `"[link removed]" in clean(...) or "<EMAIL" in clean(...)` cannot detect a regression of the `mailto:` removal. M65 and M68 kill was not confirmed by reading (evidence shows 75 of 75 killed by running, which closes the doubt on the exit code, not on the reason).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A mutant killed for the wrong reason is not a mutant.
*   ***Proposed Edit:*** Use the full message prefix as the expect fragment; assert the exact output of the `mailto:` case; check M65 and M68 first failing line names their own assertion.

### [Issue 10] [`evidence`] - Severity: Major (verdict needed on the probe)
*   **Affected Scope:** `probe-table.md`: 8 of 168 key cases readable on the head, all in the `--KEY value` style for `newpass`, `oldpass`, `postgresauth`, `authorization`.
*   **Discrepancy Description:** Readable on head; the probe does not say whether main also left them readable. `=`, `:` and JSON styles are masked for every listed key.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A readable secret on the head must be explained: either main left it readable (not a regression, but fix-dont-defer says fix it) or it is a gap in the flag rules.
*   ***Proposed Edit:*** Fix builder records main's result for those 8 rows; add the four words to the flag rules (`_CRED_FLAG` / `FLAG_WORDS`) with rows for `--newpass`, `--oldpass`, `--postgresauth`, `--authorization`; benign words (`bypass`, `compass`, `oauth` in text styles) stay masked as on main (30 of 72 masked on both).

### [Issue 11] [`evidence`] - Severity: Minor
*   **Affected Scope:** Evidence fail-before: 8 batch4 tests pass on `4091f8b1` (j3 semicolon stop x2, j4 benign names, j4 scan of list or regex string, j5 tag-split card, j5 one list of secret kinds, j6 comma pin, j6 whole line after a bearer key).
*   **Discrepancy Description:** Eight new tests pass on old code.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Per class-level-fixes each new test needs a killer or a stated control reason.
*   ***Proposed Edit:*** One line each in the next evidence table: the mutant that fails it, or "control: behaviour kept from main". Probe the record walk and the cards in the next evidence run (the probe so far covered only the two text entry points).

### [Issue 12] [`evidence`] - Severity: Nit (recorded)
*   **Affected Scope:** Evidence: timing test failed 6 of 6; `uv sync --locked --no-build` failed.
*   **AI Suggestion:*** DECLINE
*   ***Justification:*** Not part of this diff (timing fix on `core/fix-timing-harness-flake`; `--no-build` is an environment limit).

## Record for DECISIONS.md (from the builder note)
D-032 removed from the shipped text; D1 and D2 done; the 28-prefix list at `handover/DECISIONS.md:468-473` is obsolete; `authorization` added to the quoted key words. The lead adds this to `handover/DECISIONS.md`.

## Handoff counts
Accepted (PROPOSE FIX): 11 (Issues 1-11). Declined: 1 (Issue 12). Contested: 0. Escalated: 0. Redaction path, no round cap: the Blocker (Issue 1) and Majors (Issues 2, 10) need a fix builder (b5) and a fresh round 6 on the fixed head. The builder reproduces Issue 1 by running it on head and on `origin/main` first. Ledger: Q8b round 5 Blocker and Majors OPEN until fixed and verified by independent evidence including the Issue 1 input on both trees.

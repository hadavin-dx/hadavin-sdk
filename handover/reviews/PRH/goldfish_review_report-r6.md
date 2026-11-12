Status: resolved

# Goldfish Annotated Review Report (PR H batch 6, round 6)

**Target:** branch `core/prh-strip-hidden-controls` (batch 6), head `c802cc0f4c5dc7e0ae7130f004b2460ce862c869` (code `931d7396`). REDACTION path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `prhb6-design-r6.md` (1 Blocker, 1 Major, 2 Minor, 1 Nit) and `prhb6-codebase-r6.md` (0 Blocker, 3 Major, 3 Nit). Independent evidence: `handover/evidence/PRH/c802cc0f/RESULTS.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; PR H mutants 81 of 81. Full pytest exit 1: 1 failed, 12962 passed, 1 skipped. The one failure is `tests/demo_askdata/test_validate_harm.py[dblink-connect]`: the runner's own database server does not listen on the fixed socket; the same single failure occurs on clean origin/main, and the file passes (253) on both trees in a private mount namespace. Not a head defect (Issue 13). Fail-before against `3db0d34d` src: 27 failed; 14 of 15 new test functions fail on old code; one test and the rows `[single]` and `[two_plain]` pass on old code (controls). **Not run by the runner:** the mutant runner as user `nobody`, the timing test 3x3, Python 3.12, CI steps outside the redaction package (Semgrep, zizmor, Trivy, pip-audit). The next evidence run must run the first two (they fit this machine); the last two are IMPOSSIBLE-NOW (one Python version here; no network).

**What the evidence changed.** Design F1 was a hand trace; the runner **confirmed it by probe** (Issue 1). The runner also found three things no reviewer saw: `InputTooLarge` on small input (Issue 2), readable key windows with no spelled-out escape in the input (Issue 4), and the direct `redact()` gaps with zero-width and bidirectional characters (Issue 8).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1, confirmed by evidence E1] - Severity: Blocker
*   **Scope:** `tools.py:726-731` (`_decoded_readings`), `:1054-1066` (`_scrub_layers`); `runmap.py:495-505` (decodes), `:218-233` (undo with `strip_hidden`); `hidden.py:212` (the Fe sequence takes an upper-case letter after ESC).
*   **Description:** A handed-out secret hides from the scrub when it is spelled as an encoded ESC followed by an encoded first letter. Probe: secret `Tr0ub4dor-3xyzQ`, text `x %1b%54r0ub4dor%2d3xyzQ y`. On the tool and error paths origin/main gives `x <ESC><SECRET_REDACTED> y`; `3db0d34d` and the head return the text as written, which one percent-decode turns into ESC plus the secret. The strip removes ESC and the capital letter, so no form is found. Same for the `\u001b` text and `&#27;&#84;` spellings in the design trace (the probe shows those two masked on the tool and error paths; the percent spelling is the live leak). A lower-case first letter is masked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A readable secret that main did not show is a regression, and the redaction path has no round cap.
*   ***Proposed Edit:*** Name the class: **a decoded reading in which a spelled-out escape is followed by a letter that the escape grammar consumes (the strip eats the first letter of the value).** Fix at the shared choke point: the decoded views must carry the character reading (as `add_readings` already does for pattern secrets, `runmap.py:878-881`), and `_scrub_layers` must search both the stripped and the unstripped decoded text. Add rows for every spelling (percent, entity, JSON escape, mixed) with an upper-case first letter, on the tool and error paths, as a generated property test over all escape spellings and all first-letter classes (upper, lower, digit, symbol). Prove the new tests fail on `c802cc0f`; add mutants for the character reading and for the unstripped search.

### [Issue 2] [`evidence` E2] - Severity: Major
*   **Scope:** `tools.prepare_output` raising `InputTooLarge`; first input about 130 characters in `fuzz-wt.txt` (`Qx7m<ESC>Lp-9vRtzKw2 AKIAIOSFODNN%1b7EXAMPLE ... <BEL>`).
*   **Description:** 7 of 3000 small fuzz texts raise `InputTooLarge` on the head and on `3db0d34d`; 0 on origin/main. A 130-character result is far below any size cap, so a budget or reading-count limit is being reported as a size error.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** New availability regression on a path that must always return text or a withheld note; a raised error in a tool result path can drop the whole run.
*   ***Proposed Edit:*** The builder traces the raise (which limit fires, which reading list grows), fixes the cause, and makes `prepare_output` and `error_reason` never raise for any text under the cap: when a limit fires it returns the withheld note (a visible flag). Add the 7 inputs as fixed rows and a seeded fuzz test (3000 texts, zero exceptions). Report the cause in the PR notes.

### [Issue 3] [`design` F2, probes E5 items 10 and 11] - Severity: Major
*   **Scope:** `tools.py:1027-1028` (`SCRUB_PIECE_MIN=6`, piece check).
*   **Description:** After every copy of a handed-out secret was masked, any 6-character window of any form of the secret that stands elsewhere makes the whole result `MARKER+TRUNCATED`. Probes on the head: secret `ProdCompany2024!` plus the word `Company` in coloured output gives MARKER+TRUNCATED (main and `3db0d34d` gave the masked text). A secret that contains `SECRET` matches the scrub's own marker text, so every result with a hidden item is withheld (item 11 rows). The same piece check is what raised the fuzz withheld share from 1.6 % (main) to 7.5 % (head).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Ordinary input loses all of its content; and the cause is a check that does not look at what the scrub already masked.
*   ***Proposed Edit:*** Run the piece check only on stretches the scrub did not mask (compare against the marker-substituted text, and strip the scrub's own marker before checking). Add rows: a word-like secret in coloured output; a secret containing `SECRET` and `REDACT`; an ordinary log line with one masked copy. Pin the expected output (masked text, not withheld). Re-measure the fuzz withheld share and give a table of the reasons (see Issue 10).

### [Issue 4] [`evidence` E6, probe fuzz] - Severity: Major
*   **Scope:** `tools.prepare_output` output on fuzz texts with no spelled-out escape (226 of the head's 548 outputs with a readable 8-character window); example output `... A(BKIAIOSFODNN7EXAMPLE`, window `KIAIOSFO`.
*   **Description:** A key cut by `ESC ( B` inside a longer text stays readable in the head's tool output. The probe's per-text results are not compared with main one by one (main shows 1408 windows in total), so whether each case is a regression is not established.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A readable credential on a redaction path is fixed in the same work even when it is not a proven regression.
*   ***Proposed Edit:*** The builder reproduces the 226 cases from `fuzz-wt.txt` with the fixed seed 20261112, classifies each by cause (pass limit reached, ambiguity between readings, a reading dropped), names the class, fixes at the choke point, and lists per-text results for head versus main so a regression is named as such. Zero readable windows of the allowed example key and of handed-out values in the fuzz output is the stop rule; texts that cannot be made safe return the withheld note.

### [Issue 5] [`codebase` C1, `design` F3b] - Severity: Major
*   **Scope:** `redact.py:955-959, 961-962, 971-975`; `hidden.py:154, 185-186`.
*   **Description:** Direct `redact()` withholds a known value only after an ESC. The same cut by the C1 introducer U+009B leaves the tail readable (`redact("\x9b"+HAND+" x", mapping=...)` returns `r0ub4dor-3xyzQ`). The CHANGELOG states the rule without the ESC condition. Not a regression (main is the same).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The claim is wider than the code and a credential is readable.
*   ***Proposed Edit:*** Gate on any opener (`hidden.ANY.search(text)`), not on ESC; add rows for U+009B, U+0090, U+009D, U+009E, U+009F; fix the docstring at `redact.py:885-888`.

### [Issue 6] [`codebase` C2, `design` F3a] - Severity: Major
*   **Scope:** `redact.py:966-970`; compare `runmap._consuming_wins`.
*   **Description:** Direct `redact()` picks the consuming reading's output by placeholder count only. An ESC plus a `eyJ...` token plus two keys cut by ESC ( B ESC [ m: the consuming output masks 2 values, the grammar output 1; the token is then `yJ...`, which the `eyJ` pattern cannot match. On a tie of counts, the grammar output keeps the key tail. Not reproduced by the reviewer; the lead's lesson from earlier rounds applies: reproduce before the fix.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same family as Issue 5; the stronger fix covers the tie too.
*   ***Proposed Edit:*** Reproduce first (script into the evidence folder). Then: when the two outputs mask different sets of values, or the counts tie, return `WITHHELD_NOTE`; share one decision function with `runmap._consuming_wins` so the two cannot drift. Rows for the JWT case, the tie case, and a mutant per branch.

### [Issue 7] [`codebase` C3, `design` F4 and F5] - Severity: Major (claim against code)
*   **Scope:** CHANGELOG sentence "no stretch of `SCRUB_PIECE_MIN` characters of a handed-out secret may stand in a result that held hidden items"; `tools.py:970-971` (returns raw when no reading changed), `:924-932` (`_has_piece` samples at a step), `:899-902` and `:1031` (case); `defaults.py` comment.
*   **Description:** (a) The claim holds on the chosen path only: when no reading changed the text, raw text is returned and a 9-character piece stands (pinned on purpose by a test; same on main). (b) `_has_piece` samples at `step = (len-w+1)//64`, so for a form over about 132 characters a 6-character stretch at an odd offset is missed (a 300-character form guarantees 9). (c) The compare is case-sensitive while the form test is not for hex; only the marker-count check catches it. (d) Secrets of 6 or fewer characters reduce to a whole-form check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A guarantee in the CHANGELOG that the code does not give is a false claim on a redaction path; (b) and (c) are real gaps, not only wording.
*   ***Proposed Edit:*** Replace sampling with an exact check (collect all windows of the form into a set; scan the text with a rolling window; cost is linear), lower-case both sides for hex forms, and cover forms of 136, 300 and 1,000 characters at every offset in a property test. Reword the CHANGELOG and the defaults comment to the exact guarantee (window width, which paths, which forms) and say the availability cost (Issue 3 fixed). State the raw-return case plainly.

### [Issue 8] [`evidence` E3, direct `redact()` gaps] - Severity: Major
*   **Scope:** public `redact()` (`redact.py`), rows X2, X3, X5, X7 (keys and capital hex cut by zero-width or bidirectional characters, readable in the last column, all trees), row d6 (key plus U+0301, readable), rows X8, X9, X13 (see Issue 9).
*   **Description:** On the head, direct `redact()` leaves keys cut by ZW, RLO, BOM and bidirectional isolates readable (`ENCRYPTION_KEY=9F3AC7B2E1D04<U+200B>A6B55C8F...`), exactly as main does. All production paths go through `runmap`, which handles them (evidence columns untrusted, tool, error, head show `-`). The package claims the hidden-character class is closed at the choke point, but a public function still exposes it. Existing gap, not a regression.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Public functions that return a readable credential for the very class this package closes are a trap for the next caller; fix, do not note.
*   ***Proposed Edit:*** The builder lists all callers of `redact()` and `redact_many()` (src, tools, demos, docs). Preferred fix: make the public function apply the same gap-tolerant view as `runmap` (one implementation) or withhold when its input holds any hidden item (consistent with Issues 5 and 6). If a caller needs the raw grammar, it uses a private name. Rows for ZW, bidi, BOM and U+0301 cuts; d6 decision written down (U+0301 is not a hidden item, the combining mark changes the character, so say so in docs and add the row as pinned behaviour only if the decision is to keep it). Mutants per branch.

### [Issue 9] [`evidence` rows X8, X9, X13: spaced-out characters] - Severity: Minor (product decision)
*   **Scope:** a key or handed-out value written as `A K I A ...` (a visible space between each character), with or without a ZW between.
*   **Description:** Readable after removing the spaces, on all trees including main. This is not a hidden control character; it is a visible spacing technique. Masking it would need a space-tolerant matcher that can over-mask ordinary text.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Outside the ticket's class (hidden controls) and a product choice (false-positive rate against what is withheld); the owner decides. Safe default: not masked, stated plainly in LIMITS and CHANGELOG with the three rows pinned, and a ledger row OWNER-ONLY.
*   ***Proposed Edit:*** The batch-7 builder adds the LIMITS sentence and pins the rows as documented behaviour (not a promise). Question added to `questions-for-lead.md` as `q-prh-spaced-secrets` with the default.

### [Issue 10] [`evidence` E4, withheld share] - Severity: Minor
*   **Scope:** fuzz: 47 of 3000 (1.6 %) main, 124 (4.1 %) `3db0d34d`, 226 (7.5 %) head; hidden-control CPU 2.74 to 4.40 times main; plain-text rows 0.97 to 1.04.
*   **Description:** The fuzz is built to collide readings, so a share above main is expected, but part of the rise is the Issue 3 over-withholding.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** After the fixes the rise must be explained by cause, not accepted by size.
*   ***Proposed Edit:*** After Issues 2, 3 and 4 the builder reports the withheld share with a table by cause (limit hit, ambiguity, piece check, other) and a clean-corpus run (ordinary coloured logs): withheld count must be 0 there. The cost judgement of the design reviewer (justified for hostile shapes, bounded by `MAX_REDACT_PASSES` 24 and the 6 s budget) stays; the independent runner re-measures once on the final head.

### [Issue 11] [`evidence` choke and `safe_head` rows with no handed-out list] - Severity: Nit
*   **Scope:** `runmap.redact_untrusted`, `safe_head` on plain, JSON-escape and raw-ESC inputs: a handed-out value reads readable (or without its first letter) on all trees.
*   **Description:** These two paths are given no handed-out list, so they cannot know the value; a plain copy is readable there too.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** By design (the list exists only where the tool or error text is built); the evidence file says so; identical on main; recorded.

### [Issue 12] [`codebase` C4, C5, C6] - Severity: Nit
*   **Scope:** `runmap.py:789` docstring "13 and 7" (worst is now 14: `defaults.py:57`, `CHANGELOG.md:6`, `test_prh_steps.py:247-249`); mutant 79 (`f[1:]` strip) killed only through a thin seeded draw; new setting `evidence.scrub.piece_min` (`scrub_settings.py:26`, 4..32, default 6) not in the settings list style of the CHANGELOG.
*   ***AI Suggestion:*** PROPOSE FIX (all three)
*   ***Proposed Edit:*** Correct the docstring to 14; add the fixed row `"x " + HAND + " y " + ESC + HAND[:6] + TRUNCATED` to the h2 test so mutant 79 dies by a fixed row; add one CHANGELOG clause naming the setting and its range.

### [Issue 13] [`evidence` not run and the one failing test] - Severity: Minor
*   **Scope:** runner items F1, F6.
*   **Description:** The `dblink-connect` failure is the runner's database-server socket, same on origin/main, passes in a private namespace (253 on both trees). Not run: mutant runner as `nobody`, timing 3x3, Python 3.12, CI steps outside the package.
*   ***AI Suggestion:*** DECLINE for the dblink failure (not a head defect, recorded; the next runner starts its own server with the environment set and re-runs that file alone in a private namespace as the common brief says). PROPOSE FIX for the not-run items that fit this machine.
*   ***Proposed Edit:*** The next evidence brief lists the mutant runner as `nobody` and the timing test 3x3 as required items; Python 3.12 and the CI-only jobs are named IMPOSSIBLE-NOW and stay on the CI list for the lead.

### [Issue 14] [`evidence` tests that pass on old code] - Severity: Minor
*   **Scope:** `test_b6_scrub_without_a_find_or_a_changed_reading_is_still_the_text_as_written`; rows `[single]` and `[two_plain]` of `test_b6_h1_every_copy_is_masked_or_nothing_is_shown`.
*   **Description:** A test that passes on old code is a control or cannot fail for the case it names. The code reviewer mapped them (a pinned behaviour; two trivial head-to-head controls).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** One line per test in the PR notes: control with reason, or the killing mutant. The new tests of this batch each list their fail-before output on `c802cc0f`.

## Handoff counts
Accepted (PROPOSE FIX): 11 (Issues 1 to 8, 10, 12, 14; Issue 13 partly). Escalated: 1 (Issue 9, `q-prh-spaced-secrets`, safe default stands). Declined: 2 (Issue 11 by design; Issue 13 dblink failure). Contested: 0. Remaining unaddressed: none beyond the escalated question and IMPOSSIBLE-NOW items (Python 3.12, CI-only jobs).

## Who fixes it
One batch-7 builder, redaction path with no round cap, then a fresh independent evidence run and two `egm:*` reviewers on the new head. Order inside the batch: Issue 2 first (an exception hides the other probes), then 1, 3, 4, then 5, 6, 8 together (one decision function for direct `redact()`), then 7, 10, 12, 14. Class fixes at the shared choke point with property and fuzz tests; every new test shown failing on `c802cc0f`. **Lines also touched by other packages:** `guard/redact.py:954-976` (Issues 5, 6, 8) sits near the key rules that the Q8b builder (batch 7, `wip/cloud-q8b-b7`) edits at about `:157-209`; different regions, but the merge order (Q8b before PR 77, PR H before PR 77) means the later one rebases, and the builder must not copy Q8b's rules. PR 77 rebases on this package afterwards.

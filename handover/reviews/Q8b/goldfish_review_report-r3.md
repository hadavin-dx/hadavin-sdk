Status: resolved

# Goldfish Annotated Review Report (Q8b, round 3)

**Target:** `core/q8b-partial-mask-and-card-redaction` head `13ea6b75`, snapshot `/home/user/build/snap/q8bb2-13ea6b75`. Redaction path: security, no round cap. No person was available: recommended option for every item. Nothing was DECLINEd where a secret stays readable.

Sources: `/home/user/build/reports/q8bb2-design-r3.md` (0 Blocker, 3 Major, 1 Nit), `q8bb2-codebase-r3.md` (0 Blocker, 1 Major, 5 Nit), evidence `handover/evidence/Q8b/13ea6b75/RESULTS.md` (full run 10714 passed, 1 skipped, 16 xfailed; 52/52 mutants only in a patched scratch copy). All reviewer findings come from reading; the evidence runner ran the probes.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design`] F1 - Severity: Major
*   **Affected Scope:** `redact.py:1032-1035` (`_mask`), tail rule `:206`, `:709`, sweep `:1311-1318`.
*   **Discrepancy Description:** The unquoted-value tail makes `password: not set` or `token: field required` capture several words. `_NOT_A_VALUE` only skips a value that is exactly one word, so the phrase is masked as a secret and `_sweep` then masks every other "not set" in the same text.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Text is lost across lines, not only after the value; the approver and the model lose evidence. Not a leak, but a regression in the delta.
*   ***Proposed Edit:*** In `_mask`, skip masking when the first word of the captured value (stripped of `.,;:)(<>`) is in `_NOT_A_VALUE`. Test table: `password: not set`, `--token not set`, `token: field required`, `secret: has expired`, `api_key: not provided`, plus an unrelated "not set" line that must stay readable; mutant that restores the whole-value check.

### [Issue 2] [`design` F2] - Severity: Major
*   **Affected Scope:** `redact.py:681`, `:688` (quoted-value rules).
*   **Discrepancy Description:** A third hand-kept key list; `access_key="abc;def ghi"`, `private_key="x&y"`, `account_key`, `key_data`, `cert_data`, `sessid`, `phpsessid`, `connect.sid`, `auth` leave the part after `;` or `&` readable.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as round-2 Issue 2 (one source of truth); a readable secret.
*   ***Proposed Edit:*** Build both prefixes from `KEY_ALTERNATIVES`. Drift test over every spelling written `key="a;b c"`, on card, walk and log paths, leaving neither `b` nor `c` readable. Mutant that drops one spelling from either rule. Grep `redact.py`, `channel.py`, `gate.py`, `k1b/redaction.py` for any other key list.

### [Issue 3] [`design` F3, `evidence` item 3] - Severity: Major (readable secret; D-028 superseded)
*   **Affected Scope:** `k1b/redaction.py:110`, `:135`, `:140`, `:203-229` (`sensitive`).
*   **Discrepancy Description:** Walk-path keys `dbpass`, `mycredential`, `usersession`, `userauth`, `dbaccess_key`, `dbapi_key` leave the value readable (evidence: 8 of 8 readable as dictionary keys, also on main); the same names as `key=value` text are masked on all paths (0 of 48 readable). The two paths disagree.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Two independent sources now rate it Major; D-028 waited for a measurement, and the measurement shows the disagreement. Fix measured, not guessed.
*   ***Proposed Edit:*** Builder builds a made-up corpus of benign keys (`bypass`, `compass`, `oauth`, `author`, `passenger`, `sessionAffinity`, `trespass`, `authority`, ...) and credential keys, and adopts: `credential(s)`, `passwd`, `password`, `secret`, `token` as glued endings; `pass`, `auth`, `session` as endings only after a listed prefix word (`db`, `user`, `admin`, `root`, `app`, `api`, `login`, `my`, `mysql`, `pg`) or after `_`/`-`/camelCase boundary; word pairs compare `before.endswith(q)`. Show the measured benign-key false-mask count and credential-key miss count before and after; list what stays unmasked in `LIMITS` with a pinning test. Supersedes D-028. Property test: every key that the card path masks as `key=value` is also masked as a walk key, on the corpus.

### [Issue 4] [`codebase` F1] - Severity: Major
*   **Affected Scope:** `approvals/channel.py:38`, `tests/q8b_mutants.py` (M22 deleted), `guard/runmap.py:439-441`.
*   **Discrepancy Description:** The only killer of the `**mapping` merge was deleted; `original.replace("\0seed", "")` has no mutant or named test. A regression dropping the first view's masks would pass every named test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Restore M22 with a killer input where tags split a key and value (`password%<i></i>3Dx`) and the joined view numbers a secret differently; add a mutant deleting the `.replace` with a test where a masked, encoded value contains a seeded placeholder. Show each mutant killed by the named test.

### [Issue 5] [`evidence`] item 1 - Severity: Major (process, CI step fails)
*   **Affected Scope:** `tests/q8b_mutants.py` (the new CI step), `tests/test_q8b_batch2.py::test_the_changelog_entry_is_the_same_text_as_limits`.
*   **Discrepancy Description:** The mutation runner copies `src`, `tests`, `tools`, `demos`, `docs` but not `CHANGELOG.md`; the unmutated copy fails, so the CI step exits 1 (52/52 good only in a scratch copy with that test skipped).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A CI step that cannot pass is a defect. Skipping the test would weaken it.
*   ***Proposed Edit:*** Copy `CHANGELOG.md` into the mutation copy (check the copy list in `q8b_mutants.py`; same for any other file a test reads from the repo root). A test asserts the copy list contains every root file the test files open. Evidence runner reruns `python tests/q8b_mutants.py` from the real checkout: exit 0.

### [Issue 6] [`evidence`] item 4 - Severity: Minor, to be classified
*   **Affected Scope:** walk-path second pass differs on 2055 of 3000 random texts (1622 on old and main); with the placeholder escape reversed 304 (194 old, 203 main).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Not investigated; a second pass that changes the output can double-mask or change numbering. It is mostly pre-existing (1622 on main) but the count rose and an unexplained difference on the redaction path may not stay unexplained.
*   ***Proposed Edit:*** Builder classifies each difference class (escape of placeholders, renumbering, something else) with raw examples; fixes any class that changes a masked value or leaves a secret readable; for the rest, a test that pins the exact relation (second pass equals first after placeholder normalisation) and says why. The 304 vs 203 rise is explained.

### [Issue 7] [`evidence` item 2] - Severity: Minor (named behaviour change)
*   **Affected Scope:** unquoted value tail: `token=<A> on the primary` becomes `token=<SECRET_1>`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Deliberate and judged acceptable by the design reviewer on a secret path; it must be stated where a user reads it.
*   ***Proposed Edit:*** CHANGELOG and docstring name the stops precisely (flag, `key=`, any word with `:` or `=`, quote, `;`, `,`, `&`) with the examples `password=correct -horse battery staple` and `password=correct 12:30 horse`, which leave the later words readable (codebase F4); decide per example whether to extend the tail (a leaked passphrase word is worse than lost prose) and test the decision.

### [Issue 8] [`codebase` F2, F3, F5, F6, `design` F4] - Severity: Nit
*   ***AI Suggestion:*** PROPOSE FIX (all; two touch redaction tests)
*   ***Proposed Edit:*** F2: derive drift-test fragments from the regex including `connect\.sid` and the three look-ahead keys; remove the vacuous assertions (`KEY_PREFIX_MAX` positive int, `or "<" in out`, no-second-list that passes on main); the "notice" path test calls the real Slack channel clean, not `FakeChannel`. F3: move `SECRET_KINDS` above `PATTERNS` and drop `_MASKED_KINDS`; derive `_ASSIGNMENT_KINDS`. F5: one test pinning `[link removed]token=<SECRET_1>&next=/admin/x`. F6: reflow the comment at `channel.py:26-28`. Design F4: one test row `--password hunter2 word` stays `--password <SECRET_1> word`.

### [Issue 9] [`evidence`] fail-before - Severity: Minor
*   **Affected Scope:** `test_q8b_batch2.py`: 15 fail and 4 pass on both old trees; 23 new or changed ids: 6 pass on `bcb2bfec`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** For each passing-on-old test (`link_alone`, `plain_bearer`, `control_character`, `changelog_same_as_limits`, `r1` perf ratio, `r6`) the builder says why it is a control that must pass before and after, or makes it fail on the old code.

## Handoff counts
Accepted (PROPOSE FIX): 9. Contested: 0. Escalated: 0. Declined: 0. Open: Issue 3 supersedes D-028. Round 4 review needed after the fix batch (redaction path, no round cap). PR77 merge order and card-target label meaning remain owner-needed (questions-for-lead).

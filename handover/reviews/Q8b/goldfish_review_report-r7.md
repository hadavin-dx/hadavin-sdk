Status: resolved

# Goldfish Annotated Review Report (Q8b batch 6, round 7)

**Target:** branch `wip/cloud-q8b-b6`, head `8e8ccbef` (code `915127a6`). REDACTION path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8bb6-design-r7.md` (0 Blocker, 2 Major, 3 Nit) and `q8bb6-codebase-r7.md` (0 Blocker, 0 Major, 4 Nit). Independent evidence: `handover/evidence/Q8b/8e8ccbef/RESULTS.md` and probe files.

Key evidence facts: ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37/37; `q8b_mutants` 92/92; `mutation_runner_mutants` as user nobody 64/64; full pytest 10786 passed, 1 skipped, 16 xfailed (first run). Fail-before vs `6f32f0a8`: 11 failed, 3 of 14 new tests pass on old code. Vs main: 139 test ids pass on old main code. Timing test is the known flake (fix on `core/fix-timing-harness-flake`, not touched). Probe (816 cells per version): readable on head but masked on main = 0, so no regression. Round 6 items F1, D6-1, F2, F3, D6-2 verified fixed by reading (both reviewers) and by probe (cookie `&` part now masked).

Still readable on head (all also readable on main): the record key `Cookie` alone (12 cells), `--flag first second` second word, `authorization=<x> second words`, digit-suffix and plural flag keys. Over-masked on head: `bypass`, `compass`, `obsession` in `=value` forms.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` M1] - Severity: Major
*   **Scope:** `guard/redact.py:157-158, 209`; `k1b/redaction.py:203`; pins `tests/test_q8b_batch6.py:531-550`.
*   **Description:** Digit-suffix credential keys `pass2`, `newpass2`, `session2`, `auth1`, `rootauth2`, `--pass2 <v>` stay readable on the card, flag and key= rules, although the record walk treats them as credential keys. `auth0`/`oauth2` exceptions are wider than the CHANGELOG says; `oauth` itself is masked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Redaction path: a readable credential value is a defect even if main had it. Class: "credential word plus glued suffix".
*   ***Proposed Edit:*** Allow `[0-9]{0,3}` after the bare ending in the flag rule and in the `key=` look-ahead; drop `auth0` and `oauth2` from the exception sets and update the pins at `:531-550`; add each digit form to the corpus with a mutant that kills a removed suffix; CHANGELOG names the class.

### [Issue 2] [`design` M2, `codebase` N1] - Severity: Major
*   **Scope:** `tests/test_q8b_batch6.py:195-217, 500-528`; `guard/redact.py:209`.
*   **Description:** The drift test skips every key whose last word is not sensitive alone (api_key, access_key, signing_key, session_id, client-key-data, ...). The `> 150` guard runs before the filter, so it does not show how many keys are compared. No plurals in the sample, so `--secrets`, `--passwords`, `--apikeys`, `--api_tokens`, `--access_tokens` stay readable as flags although the record walk masks them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The test is meant to prove the card and flag rules cover what the record walk masks; a filter that silently skips keys defeats that.
*   ***Proposed Edit:*** Flag rule accepts an optional trailing `s` and digits after the credential word. Skip only keys whose last word is in SETTING_WORDS or in a short documented list. Count compared keys after the filter and assert the number against a pinned floor. Add plurals to sample and corpus. CHANGELOG and LIMITS updated.

### [Issue 3] [`evidence` probe] - Severity: Major
*   **Scope:** record walk key `Cookie` (capital C alone), `k1b/redaction.py` and `guard/redact.py` record path; 12 probe cells.
*   **Description:** A record key named exactly `Cookie` leaves any value readable on head, main and `6f32f0a8`. A cookie header value is a session credential.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Readable credential on a redaction path; not a regression but a found leak must be fixed in the same work.
*   ***Proposed Edit:*** Treat `cookie` and `set-cookie` as credential keys case-insensitively in the record walk and the card `key=` rule; add probe rows for case variants (`Cookie`, `COOKIE`, `Set-Cookie`) in all five paths and a mutant.

### [Issue 4] [`evidence` probe, `design` N1] - Severity: Major
*   **Scope:** `authorization=<x> second words`; `--flag first second` (newpass, oldpass, postgresauth, authorization, dbpass, confirmpass, rootauth, oauth).
*   **Description:** After a credential flag or `authorization=` the second word of a two-word value stays readable. The design reviewer accepts this for flags (shell: second word is a separate argument; main showed both words for these four flags because they were not flags, so head is not a regression). But `authorization=Bearer <token>` and `Authorization: Basic <b64>` put the credential in the second word.
*   ***AI Suggestion:*** PROPOSE FIX (narrow)
*   ***Justification:*** Scheme-then-token is a real format, not a shell argument; the generic flag case stays a stated design choice.
*   ***Proposed Edit:*** For `authorization` (flag and `=`/`:` forms) mask a leading scheme word (`Bearer|Basic|Token|Digest|ApiKey`) and the token after it. Leave the generic second word as is, stated in LIMITS and CHANGELOG with the seven pinned flags. Add probe rows for both forms and a mutant.

### [Issue 5] [`evidence` probe] - Severity: Minor
*   **Scope:** `--bypass=x`, `compass=x`, `obsession=x` (d6 rule); `author` stays readable.
*   **Description:** Ordinary words ending in `pass`/`ss` are masked in `=value` forms (60 cells on head, 60 on `6f32f0a8`, 30 on main); space forms stay readable. Over-masking, not a leak; the brief says they should stay readable.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Does not destroy needed content (masked value, key kept), so Minor; but the ORDINARY_WORDS list exists for exactly this and the rule should be consistent across forms.
*   ***Proposed Edit:*** Apply ORDINARY_WORDS look-behind to the `=value` and card forms too; test `bypass`, `compass`, `obsession`, `author` in all forms; mutant on the look-behind. If a fix makes a real credential key readable, keep the key masked and record why.

### [Issue 6] [`design` N2] - Severity: Nit
*   **Scope:** `guard/redact.py:201`; CHANGELOG.
*   **Description:** Flag prefix groups bounded at two; `--db-root-user-password <v>` readable (same as main).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Third prefix group, with a test on the backtracking bound; otherwise a LIMITS sentence. Fixed in the same push.

### [Issue 7] [`codebase` N3] - Severity: Nit
*   **Scope:** `CHANGELOG.md:14`.
*   **Description:** "any letters or digits glued in front" omits the limit `[a-z0-9]{0,40}`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Write "up to 40 letters or digits glued in front".

### [Issue 8] [`codebase` N2] - Severity: Nit
*   **Scope:** `tests/test_q8b_batch6.py:185-189`.
*   **Description:** Comment says the card `key=value` form needs the credential word at the end; the generic rule allows `[\w.\-]{0,20}` after it, so `token_type=x` is masked; only the flag form has the end limit.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Correct the comment.

### [Issue 9] [`codebase` N4] - Severity: Nit
*   **Scope:** `k1b/redaction.py:148-153`.
*   **Description:** Stale comment says ORDINARY_WORDS/BARE_ENDINGS are defined below; they come from the import at `:36`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Say they are imported from `guard/redact.py`.

### [Issue 10] [`design` N3] - Severity: Nit
*   **Scope:** `test_k1_every_cookie_key...`.
*   **Description:** Depends on the `older.masked_parts` oracle, which the reviewer did not read; `readable_pieces` uses P1-P3 only.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** Not a defect found; the builder notes in the PR which oracle is used. The next evidence run reads it.

### [Issue 11] [`evidence` tests that pass on old code] - Severity: Minor
*   **Scope:** `test_d6_a_flag_with_an_ordinary_word_stays_readable`, `test_no_test_names_a_fixed_path_in_the_shared_temporary_folder`, `test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file`; 139 test ids that pass on old main code (`failbefore-main-passed-on-old.txt`).
*   **Description:** A test that passes on old code is either a control or cannot fail for the case it names.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class from Q8c-1 round 6 Issue 7.
*   ***Proposed Edit:*** Builder writes one line per test: control (guards behaviour that already holds, with reason) or the mutant that kills it. The first is a control of the ordinary-word rule (and becomes meaningful once Issue 5 changes it). The second and third guard the path hygiene: give each a mutant (reintroduce the fixed path) or rewrite so it fails on `6f32f0a8`. Any of the 139 with neither reason is rewritten.

### [Issue 12] [`evidence` flake and not-run items] - Severity: Nit
*   **Description:** Timing test flaked (1 of 3 passes on head and on main); not run: perf, Python 3.12 job, security job (no network), Vault tests, ticket appendix A1-A5 and X1-X9.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** Known flake (fix elsewhere, do not touch); the not-run items are stated in the evidence file. The next evidence run starts the ticket appendix items that fit the machine (A1-A5) and names the rest.

## Handoff counts
Accepted (PROPOSE FIX): 10 (Issues 1-9, 11). Declined: 2 (10, 12). Contested: 0. Escalated: 0. Remaining unaddressed: none. Because the path is redaction with no round cap, a batch-7 builder fixes Issues 1-9 and 11, then a fresh evidence run (all five paths, new probe rows for Issues 1-5) and two `egm:*` reviewers read the new head. New findings this round that no reviewer saw: Issue 3 (Cookie) and Issue 5 (over-masking) came from the evidence probe; Issue 4 was narrowed from the design review's accepted decision.

# Goldfish Annotated Review Report (resolve, round 2)

Status: findings categorised; the author applies them (ticket revision 4)

**Target:** `handover/tickets/P1.md` (revision 3). Findings: `handover/reviews/P1-round2-adversarial.md`, `handover/reviews/P1-round2-correctness.md`. Counts: 32 findings, all PROPOSE FIX (none contested, none escalated: the lead answered the open questions in `LEAD-ORDERS.md` order 5 / amendment A14).

## Lead decisions that apply (order 5)
Order 5 (d): DENY for ids uses `id_key(loose)` over the whole text as an explicit named view, plus a substring API `scan_contains`; NO 16-key look-alike set. (e): P1 does NOT move Intake's ALLOW checks; Intake keeps `_f` equality until an Intake ticket does (so the ALLOW/DENY table becomes documentation, with the raw-span rule stated for that later ticket). (c): items the ticket attributed to 'A13 decision N' that A13 does not contain stay marked PENDING LEAD as the author's proposals. (g): fix every blocker and major, or contest with evidence in the disposition file.

Note on the gate (skill Step 4): the owner told the cloud session to follow `LEAD-ORDERS.md` (allowed actions only) and to run the resolve step; the auto-accept path is taken for every PROPOSE FIX, as in round 1.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-codebase-details`] - Severity: Blocker (finding id C1, correctness)
*   **Affected Scope:** Interface, "DENY key-set" and "same_person in P1b is scan_match" of `handover/tickets/P1.md`
*   **Discrepancy Description:** Under the ticket's own rules, `same_person` stops over-matching. That is unsafe for the separation-of-duties DENY case. (a) Gap 3 appends the decoded tag text before the scan keys. So `same_person("alice"+TAG("x"), "alice")` shares no key and returns False. Today it returns True, because tags are Cf and are dropped. An attacker can hide tag characters in an approver name to look like a different person. (b) "Empty keys are left out of the set" makes `scan_match("","")` and `scan_match("​","")` False. Today both are True. `scan_match(x, x)` is therefore not reflexive. (c) Nothing keeps `identity_key(a)==identity_key(b)` implying a match.
*   **Rationale:** evidence: P1.md lines 35, 60 and 62; memo-1 line 61 ("append the decoded text"); 748849c `textnorm.py` lines 98-102 (`same_person` is `fold_key` equality); `fold` drops Cf at line 42 and line 71
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface, "DENY key-set" and "same_person in P1b is scan_match"
    *   Change: Define `same_person(a,b)` as `identity_key(a)==identity_key(b) or scan_match(a,b)`. Add a property test: identity-equal implies same_person. Add a test for `same_person(x,x)` including empty and invisible-only text. State what happens for empty keys: raise `EmptyKey`, or compare the raw empty strings as equal. Also state whether the key-set always contains a tag-free reading, and whether that counts against the cap of 8.

### [Issue 2] [`egm-design`] - Severity: Major (finding id A1, adversarial)
*   **Affected Scope:** Interface, "DENY key-set" and "Match rule" of `handover/tickets/P1.md`
*   **Discrepancy Description:** The only matching API is `scan_match(a, b)`, which is whole-key set intersection. A DENY use (blocklist entry inside a document of up to 262,144 characters) is a substring search. The ticket never says how a needle key-set is searched in a haystack key-set. It is also silent on the cost: 8 x 8 = 64 substring passes per needle, times blocklist size, over keys of up to 262k characters.
*   **Rationale:** evidence: Ticket "Match rule" paragraph. Its only named tests are "ΗηΗη in scan_keyset" and the whole-string "hnhn" match. Cap test and perf list cover the fold only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface, "DENY key-set" and "Match rule"
    *   Change: Add `scan_contains(needle_raw, hay_keys)` (substring, any needle key in any haystack key) as a named API with an explicit complexity bound, a refuse-on-error wrapper, and a perf row at the cap with a realistic blocklist size. State which view each downstream scan uses.

### [Issue 3] [`egm-design`] - Severity: Major (finding id A10, adversarial)
*   **Affected Scope:** Scope (P1a/P1b/P1m) of `handover/tickets/P1.md`
*   **Discrepancy Description:** P1b is five things in one Tier A PR: algorithm change (gaps 1-5), entity/line view, key-set, stored-key API with a crypto/format surface, cache, and a generator regeneration. P1a merges a known-weak `fold1` (tags dropped, idempotence bug, no key-set) as the module for P2d to start on, and `scan_views` returns one key "so callers already iterate".
*   **Rationale:** evidence: Ticket "Depends on" and "P1a views".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Scope (P1a/P1b/P1m)
    *   Change: Split the stored-key API into its own package (P1c) after P1b: the algorithm then stays revertible until something stores a key. In P1a mark `scan_views` provisional/experimental in its name or docstring and make P2d wait for P1b for any DENY decision, not only for storage.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A2, adversarial)
*   **Affected Scope:** "DENY key-set": does it cover mixed ambiguous letters of `handover/tickets/P1.md`
*   **Discrepancy Description:** Coverage is only 3 binary choices (case reading, Ze, split). Table values are one-to-one, with no I/l/1 or O/0 reading. `_confusables.py` has no ASCII sources (first entry 0x00A1, line 15). `fold("paypaI")` therefore gives `paypai`, not `paypal`, because Latin capital I casefolds to `i`. The key-set does nothing for this, yet the ticket presents it as the DENY answer for ambiguous letters. `id_key(loose)` is the only O/I/L reading, and it exists for ids only.
*   **Rationale:** evidence: `_confusables.py:15`. `textnorm.py:77` (casefold, no I/l mapping). Ticket "DENY key-set".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: "DENY key-set": does it cover mixed ambiguous letters
    *   Change: Decide explicitly. Either add a fourth binary choice (I-like glyphs read `l` or `i`, giving 16 keys), or state that DENY for numeric ids uses `id_key(loose)` over the whole text and name the view. Generate a table of every ambiguous class (all code points whose own-case and case-first readings differ, plus ASCII I/l/1/O/0) and make the ticket claim "complete over the table", with a test, instead of a hand-listed pair.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A3, adversarial)
*   **Affected Scope:** Gap 3, tag characters of `handover/tickets/P1.md`
*   **Discrepancy Description:** The fix says "decode ... and append the decoded text to the text before the scan view". Appending at the end of the whole text destroys adjacency.
*   **Rationale:** evidence: Ticket gap-3 row. `textnorm.py:42` drops Mn.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Gap 3, tag characters
    *   Change: Decode tags in place, as ASCII at the tag's own position. Add a spaced reading for them. Add a row for tags inside a word and for tags adjacent to a needle. Decide and test variation selectors.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** Gap 7, entity step of `handover/tickets/P1.md`
*   **Discrepancy Description:** `html.unescape` turns invalid numeric references (`&#0;`, `&#xD800;`, `&#x110000;`) into U+FFFD. U+FFFD is category So and is not dropped (`_DROP_CATEGORIES` line 42), and it is absent from the table. The new step therefore creates a visible splitter that the fold keeps. The spaced view only spaces Cf/Cc/Zl/Zp/Co/fillers.
*   **Rationale:** evidence: `textnorm.py:42`. Ticket gap 5 and 7 rows.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Gap 7, entity step
    *   Change: After unescape, treat U+FFFD like Cf/Cc: dropped in the glued key and a space in the spaced key. Add rows for `&#0;`, `&#xD800;`, `&#x110000;` and `&#x81;`. Note that `html.unescape` also resolves legacy no-semicolon entities (`&amp` without semicolon), which over-match (the safe side, but test them).

### [Issue 7] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** FOLD_VERSION, Golden test 2 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The "forced bump" is vacuous. Test 2 requires a different `alg` only if goldens differ from the file. A developer who changes behaviour regenerates the golden file in the same commit, so goldens and `alg` in the file agree with each other and nothing forces a bump. Separately, `TABLE_DIGEST` covers only the table. `FILLERS`, `_DROP_CATEGORIES`, the dash/quote maps, the entity rule, `html.entities.html5` and `_LOOSE` are not in `FOLD_VERSION`. Changing them with `alg=fold2` unchanged yields the same version string and different keys.
*   **Rationale:** evidence: Ticket "Golden test (A17)". `textnorm.py:42-49`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: FOLD_VERSION, Golden test 2
    *   Change: Keep an append-only `alg -> golden` history in the fixture and fail if an existing `alg` entry changes. Or take the previous goldens from the merge base. Put a digest of every behaviour constant (fillers, drop categories, maps, entity-table digest) into the `tbl=`/`alg` part.

### [Issue 8] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** P1b stored keys of `handover/tickets/P1.md`
*   **Discrepancy Description:** (a) `salt=None` is the default, so the easiest call stores an unsalted SHA-256 of a personal name. It is brute-forceable from any name list, it correlates across tenants and rows, and the digest is stable and comparable between customers. (b) A salted stored string does not record which salt or key id was used. After a key rotation, `stored_key_matches` returns `False`, not an error. On a DENY path a stored key that silently does not match means "not on the list", which is fail-open. (c) The key-set shape is undefined: `stored_key` "returns f-string ... for the key-set view: a tuple", while `parse_stored` and `stored_key_matches` take one `str`.
*   **Rationale:** evidence: Ticket "P1b stored keys" (the f-string and `stored_key_matches`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P1b stored keys
    *   Change: Salt required for views that may carry personal data (`name_key`, `identity_key`); unsalted only via an explicit `unsalted_pseudonym=True`. Add a key id to the stored string (`...#kid=...#digest`) and raise `SaltMismatch` on an unknown id. Define the key-set stored form (a canonical, single string, e.g. the sorted digests with count) and the match call for it.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Stored-key mismatch, "goes to a person" (F3) of `handover/tickets/P1.md`
*   **Discrepancy Description:** Not implementable from this ticket. Nothing here provides a hand-off, a queue or a re-fold path. It is pushed to P3b and P2a as "must name who decides". Per bump, every stored item becomes a human decision. With, say, 100,000 stored names this is unworkable, which creates pressure to disable `check_stored` or catch-and-continue. Rolling deploy: during a rollout, old nodes (`fold1`/`fold2`) and new nodes (`fold3`) each refuse the other's keys, so a mixed fleet refuses everything for the length of the deploy.
*   **Rationale:** evidence: Ticket "Stored keys" cost sentence (A5) and F3 text at amendments.md:19.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Stored-key mismatch, "goes to a person" (F3)
    *   Change: Require raw text escrow under a role-gated store as the default (re-fold is then automatic and migration is a job, not a person). Document "refuse" as the only behaviour and ship `plan_refold(stored_items)` batch tooling. Add a deploy rule: stored-key writers and readers upgrade together, or readers accept the previous `alg` for one release via a frozen old-fold function. State the number of human decisions the downstream packages must be able to absorb.

### [Issue 10] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** Error contract (fail-closed), item 3 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The contract "any TextnormError means REFUSE" lives in a docstring and in a `deny_scan` helper that exists only in the tests. Consumers can do `except Exception: return False` (False = not matched = allow) and nothing enforces it. `NotText` also derives from `TypeError`, so `except TypeError` can swallow it.
*   **Rationale:** evidence: Ticket "errors" bullet and the tests list (helper `deny_scan`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Error contract (fail-closed), item 3
    *   Change: Ship the refusing wrapper in the module: `scan_hit(needles, text) -> bool` returns True (refuse) on any `TextnormError`, and `allow_equal` already catches. Or give scan APIs a three-valued result like `AllowVerdict` (`MATCH`, `NO_MATCH`, `REFUSED`) with no `__bool__`. Drop the `TypeError` base from `NotText`.

### [Issue 11] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** Intake call-site table / "Intake move after P1b" of `handover/tickets/P1.md`
*   **Discrepancy Description:** The rule says ALLOW sites call `allow_equal(extracted candidate, on-file component)`. But Intake `_f` folds the sent text and extracts the candidate from the folded text (lines 1060, 1345 "folds the sent text ... to find candidates"). A candidate taken from folded text is already look-alike-equalised, so `allow_equal` on it is comparing a folded value to the on-file value. If the builder then folds the on-file side to make them agree, the ALLOW path goes through the fold.
*   **Rationale:** evidence: Ticket Intake table (rows 1060, 1345 marked "DENY scan; the later `c in comps` test is ALLOW").
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Intake call-site table / "Intake move after P1b"
    *   Change: The ticket must say that the ALLOW candidate is cut from RAW text (offsets mapped from the folded text, or extracted by a regex on raw text) and compared to the raw on-file value; a candidate that exists only in the folded text is a LOOKALIKE and is flagged. Add this as a P1b/Intake test row.

### [Issue 12] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Interface (match rule, `stored_key`, `stored_key_matches`) of `handover/tickets/P1.md`
*   **Discrepancy Description:** The match rule is incomplete. `scan_match` is only "share one whole key". Blocklists and leak scans are substring checks. The ticket itself says an empty needle matches every text in a substring scan. Nothing defines needle-in-haystack across 8 x 8 key pairs. The gap-3 test "scan keys contain `approved`" is ambiguous (equal to, or contains). The stored-key API is also inconsistent. `stored_key(...) -> str`, but for the key-set view it "returns a tuple, never a joined string". `stored_key_matches(stored, view, text)` takes one `stored` string. `keyset_encode` is defined but nothing uses it. A salted digest and an unsalted digest have the same stored format. A wrong-mode comparison therefore returns a quiet False.
*   **Rationale:** evidence: P1.md lines 34-36 and 60
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (match rule, `stored_key`, `stored_key_matches`)
    *   Change: Add a `scan_contains(needle_raw, haystack_raw)` rule, with the empty-needle refusal. Give the key-set view separate functions with explicit tuple types. Record `salted` in the stored format, or refuse mixed use. Remove `keyset_encode` or say who uses it.

### [Issue 13] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Several: lines 20, 33, 43, 49, 53, 86 of `handover/tickets/P1.md`
*   **Discrepancy Description:** The ticket cites lead decisions that do not exist in A13. A13 in `amendments.md` has only items (1)-(6). (3) is the P2a stop/reset identity, not the constants. (4) is the P1 identity key, not "fail-before against a shim". (6) is "measure against 748849c", not "strict=True in pilot/prod". There is no (7) or (8). The pending-lead rows (strict pin, downstream split, shim, Intake table) are therefore the author's proposals, presented as decided. The ticket also says "Golden test (A17)"; A17 is only a round-1 review-finding id. A12 says the plan table shows P1a and P1b, but `plan-v3.md` lines 95-98, 104 and 130 still say "P1". The ticket treats that correctly.
*   **Rationale:** evidence: `amendments.md` lines 33, 31 and 20; `questions-for-lead.md` Q4 items 1-6; `plan-v3.md` lines 95-98
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Several: lines 20, 33, 43, 49, 53, 86
    *   Change: Remove "A13 decision N" for N = 3, 4 (shim), 6 (strict), 7 and 8. Mark those items as proposals under PENDING LEAD. Rename "A17".

### [Issue 14] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** Tests (P1b), fail-before table of `handover/tickets/P1.md`
*   **Discrepancy Description:** The table says each row "must fail on an assertion (a) on the merged P1a head". Several rows use names that P1a does not have: `line_view` (gap 7), `scan_match` and `scan_keyset` (Ze row), and `check_stored`, `stored_key` and `parse_stored`. On a P1a head those fail with ImportError or AttributeError, not an assertion. That is exactly what A13(4)/the ticket's shim logic rejects. The ticket builds a shim only for P1a.
*   **Rationale:** evidence: P1.md lines 53 and 55-65; P1a interface lines 30-34
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests (P1b), fail-before table
    *   Change: Add a P1b shim step. It is the P1a head plus stubs for every P1b name with old behaviour, including the error classes. Or move the P1b names into P1a as stubs. Also state that the P1a shim must define `TextnormError`, `TextTooLong`, `NotText` and `check_pinned_unidata`, so those rows fail on `DID NOT RAISE` or an assertion.

### [Issue 15] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** Interface, `check_stored` message rule of `handover/tickets/P1.md`
*   **Discrepancy Description:** "The message shows a version only if it matches `^alg=fold[0-9]+\|` and then at most 80 characters". Only a prefix is checked. A stored string such as `alg=fold1|<canary text>` echoes up to 80 characters of untrusted stored text. That contradicts "never a stored string" in the security notes and fails the ticket's own canary test through `stored=`.
*   **Rationale:** evidence: P1.md lines 36, 45 and 65
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface, `check_stored` message rule
    *   Change: Echo the version only when the whole version part fully matches `^alg=fold[0-9]+\|tbl=[0-9a-f]{12}:[0-9]+\|ucd=[0-9.]+\|ud=[0-9.]+$`. Otherwise use a fixed text.

### [Issue 16] [`egm-codebase-details`] - Severity: Major (finding id C6, correctness)
*   **Affected Scope:** Evidence commands; unidata pin of `handover/tickets/P1.md`
*   **Discrepancy Description:** A9 F3 says "Python 3.14 is probed in P1 before relying on gap 2". The evidence loop is `for v in 3.12 3.13` only. The ticket admits 3.14 and 3.12 are not installed, and gives no plan or owner for the 3.14 probe. Gap 2 (apply the table before the Cn drop, so a code point assigned later still maps) is therefore unverified across interpreters.
*   **Rationale:** evidence: `amendments.md` line 19; P1.md lines 68-71
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Evidence commands; unidata pin
    *   Change: Add 3.14 to the runner loop. If it is unavailable, add a stop condition: P1b may not merge until the probe is pasted. Also test that none of the 56 Cn sources is Mn/Cf/Cc on 3.14.

### [Issue 17] [`egm-codebase-details`] - Severity: Major (finding id C7, correctness)
*   **Affected Scope:** Files: "Vendored data `tools/data/confusables.txt`: NOT in P1" of `handover/tickets/P1.md`
*   **Discrepancy Description:** The generator's only input is left out of core. memo-5 line 28 lists `tools/data/confusables.txt` and `.gitattributes` as P1 files. No copy exists anywhere under `/home/user/hadavin-sdk-handover` (Glob finds none). P1b regeneration depends on a PR #50 branch that this ticket cannot show is on origin. Core `.gitattributes` has only `* text=auto eol=lf` and lacks PR #50's `tools/data/confusables.txt -text`. The verbatim `gen_confusables.py` docstring says the file "is vendored in tools/data/confusables.txt". That is false in core. The skip text "data file not vendored: P7n" is mislabelled: P7n is vendored `unicodedata`, not the UTS #39 file (A9 F3). CI can no longer check that the table matches its source.
*   **Rationale:** evidence: 748849c `gen_confusables.py` lines 3-8; `.gitattributes` in both trees; memo-5 line 28; `amendments.md` line 19
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Files: "Vendored data `tools/data/confusables.txt`: NOT in P1"
    *   Change: Vendor the 763 KB file with the `-text` attribute, as memo-5 and memo-1 section 8 say. Or edit the generator docstring and skip text, name the permanent location of the pinned file, and give that copy's sha256 in the ticket.

### [Issue 18] [`egm-codebase-details`] - Severity: Major (finding id C8, correctness)
*   **Affected Scope:** Mutation plan: "re-point the 27 existing mutants ... each must end KILLED" of `handover/tickets/P1.md`
*   **Discrepancy Description:** One of the 27 has no killer among the 13 moved tests. "fold: loose map short" (748849c `promoted_mutants.py` line 435) is killed by `test_a_protected_number_is_found_through_junk_look_alikes_and_exempt_tokens`, an egress test that is not moved. The only moved `loose` assertion is `squeeze("O0Il1", loose=True)=="00111"` (test line 788). That input contains only O, I and L, and the mutant maps those three the same way. The mutant would SURVIVE. The "builder confirms" sentence covers only the micro-sign and newline mutants. The count 27 = 12 + 11 + 3 + 1 is correct.
*   **Rationale:** evidence: `promoted_mutants.py` lines 435-440; test file lines 775-792
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Mutation plan: "re-point the 27 existing mutants ... each must end KILLED"
    *   Change: Add a moved or new test that uses S, B, Z, G and Q with `loose=True`. Add a re-pointing table (mutant, new killer) to the ticket.

### [Issue 19] [`egm-codebase-details`] - Severity: Major (finding id C9, correctness)
*   **Affected Scope:** Intake `_f` call-site table, rule for the Intake move of `handover/tickets/P1.md`
*   **Discrepancy Description:** The line numbers and the 13-calls-on-10-lines count are correct. But the stated rule does not work as written. At every ALLOW site the candidate is extracted from `_f`-folded text (line 1060 `t, tc = _f(u), _f(_camel(u))`; the `c in comps` test at 1065), and the components are also built from `_f(on_file)` (lines 757, 1040, 1340). `allow_equal(candidate, component)` on two already-folded strings is just `==`. A look-alike candidate still equals the on-file value, so the "never fold for ALLOW" property is not delivered. The rule needs raw spans.
*   **Rationale:** evidence: `invoicecheck.py` lines 757, 1040, 1060-1065, 1340
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Intake `_f` call-site table, rule for the Intake move
    *   Change: State that the ALLOW move needs the raw substring of each candidate (the `_show` and `_raw_lines` path), compared to a raw on-file component. Or say that the Intake ALLOW check stays on `_f` equality and is not moved by P1.

### [Issue 20] [`egm-design`] - Severity: Nit (finding id A11, adversarial)
*   **Affected Scope:** Bidi controls of `handover/tickets/P1.md`
*   **Discrepancy Description:** Bidi controls are only dropped. An override (U+202E) reverses the displayed order but the stored key keeps logical order. Intake already treats the presence of a bidi control as a signal (`_bidi_lines`, row 1008) but P1 offers no equivalent.
*   **Rationale:** evidence: Ticket class list "bidi controls" rows are only `equal`; Intake table row 1008.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Bidi controls
    *   Change: Add `has_bidi_control(text)` as a fail-closed signal beside `has_mixed_script`, or a reversed-order key reading under RLO/RLE/LRO. Add the row.

### [Issue 21] [`egm-design`] - Severity: Nit (finding id A12, adversarial)
*   **Affected Scope:** Spaced view and empty keys of `handover/tickets/P1.md`
*   **Discrepancy Description:** "Empty keys are left out of the set" is stated for the key-set, but the spaced pipeline turns Cf/Cc into ONE space. Strip behaviour is not specified. If the spaced key of "​" is `" "`, it is non-empty and `is_empty_key` is False, so a one-space needle matches every text that contains a space.
*   **Rationale:** evidence: Ticket "P1a views" `require_key` and gap-5 row.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Spaced view and empty keys
    *   Change: Define the spaced key as stripped and collapsed. `is_empty_key` is True for whitespace-only. Add a row.

### [Issue 22] [`egm-design`] - Severity: Nit (finding id A13, adversarial)
*   **Affected Scope:** Cap and expansion of `handover/tickets/P1.md`
*   **Discrepancy Description:** The ticket calls the check "NFKC expansion", but `fold` starts with NFKD and `runmap._expanded_len` counts NFKD length (runmap.py:135-147). A builder who writes `len(normalize("NFKC", s))` runs the normalisation before the check, which is the cost `runmap` avoids (docstring lines 150-153). Table values can also be longer than one character (`AE`), and a 3-pass loop reruns on each result, so the key can exceed the cap. Entity expansion (`&#xFDFA;`) is handled only by "again after NFKC".
*   **Rationale:** evidence: Ticket "input rules"; runmap.py:135-156.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Cap and expansion
    *   Change: Specify the check as per-character NFKD length (cached), multiplied by max table value length, and check the output key length too. Add a concurrency/memory note or a semaphore.

### [Issue 23] [`egm-design`] - Severity: Nit (finding id A14, adversarial)
*   **Affected Scope:** Cache of `handover/tickets/P1.md`
*   **Discrepancy Description:** `TEXTNORM_CACHE_ENTRIES` patched to 4 cannot work if the cache is a `functools.lru_cache(maxsize=N)` built at import (maxsize is fixed at decoration time). The test would pass vacuously or need a module reload. The cache also keeps raw personal text in memory (up to 38 MB by the ticket's own estimate) for no measured need. The cache key must include `casefold`/`collapse_ws`, which the ticket does not say.
*   **Rationale:** evidence: Ticket "Other P1b tests", cache bullet; "Security" bullet.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Cache
    *   Change: Build the cache through a factory function that reads the constant, or test against the real size. Show a measured benefit or drop the cache (gap 5 only says "bounded cache").

### [Issue 24] [`egm-design`] - Severity: Nit (finding id A15, adversarial)
*   **Affected Scope:** Idempotence and convergence tests of `handover/tickets/P1.md`
*   **Discrepancy Description:** The idempotence claim and "pass count 2 or less" are tested over single code points only. Sequence effects are the real risk: dropping a filler or mark between two Hangul jamo or a base plus mark makes NFKC compose across the gap; a table value can then expose a new composable pair.
*   **Rationale:** evidence: Ticket gap-1 row.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Idempotence and convergence tests
    *   Change: Add exhaustive pairs over the drop/table/jamo/combining classes plus a seeded random-string fuzz asserting `identity_key(identity_key(x)) == identity_key(x)` and pass count.

### [Issue 25] [`egm-design`] - Severity: Nit (finding id A16, adversarial)
*   **Affected Scope:** Hard-coded values of `handover/tickets/P1.md`
*   **Discrepancy Description:** Not in `defaults.py`: the 80-character cap on a version in the `check_stored` message, the `^alg=fold[0-9]+\|` pattern, and the digit table bound `range(0x20000)` (`textnorm.py:56`, a future Nd above U+1FFFF would be missed).
*   **Rationale:** evidence: `textnorm.py:56`; ticket "Constants".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Hard-coded values
    *   Change: Name the 80 in `defaults.py`; build the digit table over `sys.maxunicode + 1` and keep the existing completeness test.

### [Issue 26] [`egm-design`] - Severity: Nit (finding id A17, adversarial)
*   **Affected Scope:** Tests tied to the environment of `handover/tickets/P1.md`
*   **Discrepancy Description:** Fail-before relies on a shim stub that the same author writes. It proves each test can fail but not that it fails for a realistic wrong implementation (that is what mutants are for). The differential rows depend on "364 literals plus a 274-pair corpus" from a laptop script (UNVERIFIED), so the corpus may not exist when the builder starts. The golden test 1 "pinned only" means CI on 3.13 is the sole enforcer.
*   **Rationale:** evidence: Ticket "Fail-before (P1a)", "Differential test".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests tied to the environment
    *   Change: Make the builder commit a self-contained hostile list and require a minimum row count per class in a meta-test.

### [Issue 27] [`egm-design`] - Severity: Nit (finding id A18, adversarial)
*   **Affected Scope:** P1m of `handover/tickets/P1.md`
*   **Discrepancy Description:** The mutation judge (KILLED / WRONG_REASON / CRASH) is what lets Tier A claim "every mutant ends KILLED", yet P1m is proposed as Tier B and was not read in depth (`testing/mutation.py` "reads a JUnit file path: UNVERIFIED"). The runner rewrites source files and a killed run leaves a mutated file (long-jobs-run-detached rule). It also ships in the wheel.
*   **Rationale:** evidence: Ticket "Mutation plan".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P1m
    *   Change: Review P1m with the same adversarial pass (at least the verdict rules), run it under a restore-on-exit wrapper, and verify the file-read claim before merging.

### [Issue 28] [`egm-design`] - Severity: Nit (finding id A19, adversarial)
*   **Affected Scope:** Wording of `handover/tickets/P1.md`
*   **Discrepancy Description:** "digest" is used both for the SHA-256 of a key and for `TABLE_DIGEST` (SHA-256 of the table), and `keyset_encode` "used only when one value for a whole set is needed" versus "stored form is one digest PER KEY" may be read as two storage formats. "view" means both the function and, in `stored_key`, a name string. "text folding" `fold` is also said to be unsafe for ALLOW but `LOOKALIKE` is derived from it.
*   **Rationale:** evidence: Words section, P1b stored keys.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Wording
    *   Change: State once: `table_digest` (of the table), `key_digest` (of a key); say which stored form the key-set view uses.

### [Issue 29] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** Fail-before row 2 (gap 2), table of `handover/tickets/P1.md`
*   **Discrepancy Description:** Wrong line cite. "gen_confusables.py `build`, lines 54-61". At 748849c `build` is lines 66-94. The two filter lines are 77-78 (`NFKC != ch` or category in DROPPED) and 87-89 (small-capital rule). Lines 54-61 are `_HEADER` text.
*   **Rationale:** evidence: 748849c `gen_confusables.py` lines 52-94
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Fail-before row 2 (gap 2), table
    *   Change: Correct the cite to 66-94 (filters 77-78 and 87-89).

### [Issue 30] [`egm-codebase-details`] - Severity: Nit (finding id C11, correctness)
*   **Affected Scope:** Gap 1 row; "Existing core code reused" of `handover/tickets/P1.md`
*   **Discrepancy Description:** False statement: "PR #50's table already maps U+0130". `0x0130` is absent from `_confusables.py` (Grep of 0x0397, 0x03B7, 0x0417, 0x0437 and 0x03C3 hits; 0x0130, 0x00D8, 0x00DE, 0x0110 and 0x03A3 do not). `fold_key("İ")` is `i` because NFKD gives I + U+0307 and the Mn is dropped. The O-stroke and Sigma examples are consistent with the table. The test at line 776 asserts `0x130 -> "I"`, which is also reached by decomposition.
*   **Rationale:** evidence: 748849c `_confusables.py` (no 0x0130 entry); `textnorm.py` lines 67-73
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Gap 1 row; "Existing core code reused"
    *   Change: Reword: İ folds through NFKD plus the Mn drop, not through the table.

### [Issue 31] [`egm-codebase-details`] - Severity: Nit (finding id C12, correctness)
*   **Affected Scope:** P1m and mutation plan of `handover/tickets/P1.md`
*   **Discrepancy Description:** (a) P1m lists two files. 748849c also has `src/hadavin_sdk/testing/__init__.py` (a docstring) and `tools/__init__.py` (empty). Core main has neither the `testing/` nor the `tools/` directory, so P1m must create both. (b) "`testing/mutation.py` ... no I/O except reading a JUnit file path it is given: UNVERIFIED" is wrong. The file imports only `re`, `xml.etree.ElementTree`, `Iterable` and `StrEnum`. `first_failure_junit(xml_text)` takes the XML text, so there is no file I/O.
*   **Rationale:** evidence: 748849c `testing/mutation.py` lines 19-26 and 80; file listing
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: P1m and mutation plan
    *   Change: Add both `__init__.py` files to P1m. Replace the I/O sentence with "stdlib only; no file or process I/O".

### [Issue 32] [`egm-codebase-details`] - Severity: Nit (finding id C13, correctness)
*   **Affected Scope:** Interface details of `handover/tickets/P1.md`
*   **Discrepancy Description:** (a) `check_pinned_unidata(expected, *, strict)` is required-positional, but the text says "the default `expected` is `defaults.TEXTNORM_PINNED_UNIDATA`". (b) `id_key(raw, *, loose=True)` is "= squeeze", but `squeeze` defaults to `loose=False`. (c) The `TABLE_DIGEST` serialisation "sorted `<hex cp>:<value>` lines" does not fix hex case or padding, and the digest is pinned by a literal in a test. (d) `clear_cache()` and the cache's cached object are not in the Interface list, though the security notes depend on them. (e) "Read-only" covers `LOOKALIKES` and `_TABLE` only. `_DIGITS`, `_LOOSE` and `_confusables.TABLE` stay mutable dicts. (f) The case-reading rule for "own case" does not say whether the 3-pass convergence loop also runs for that reading. "A key-set runs the pipeline twice" conflicts with 2 case readings x 2 splits. (g) The "262,144 U+FDFA = 1.66 s" worst case cannot occur after the expansion check. Under the check the worst case is about 14,563 U+FDFA, as in `defaults.py` lines 34-37.
*   **Rationale:** evidence: 748849c `textnorm.py` lines 46-49, 60-62, 80-86; `defaults.py` lines 34-37
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface details
    *   Change: Fix each in the same batch.

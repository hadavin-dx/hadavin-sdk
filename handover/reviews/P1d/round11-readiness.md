# P1d rev 11 plan review round 11, implementation readiness (sonnet), behaviour/spec gaps only (ORDER 191)
Verdict: 0 Blockers, 2 Majors, 6 Nits. Read-only; ran nothing. Clean: counts (55 rows / 58 mutants), merge order consistent, redact.py/runmap.py/gate.py/requests.py/app.py cites correct, test names exist. textnorm/P1b-dependent items unverified (not on branch).

MAJOR
- M1. P1d.md:183 `clean` step (2) calls redact_text(..., source="card_joined") in approvals/channel.py with no neutralise hook; existing tests/test_k5_round11.py:79-122 (every redact_text call feeding a card passes the hook, NO_HOOK_OK = runmap/judge/bedrock_guardrail/evidence) fails on it, and is not in "Tests to rewrite". Pick: (a) pass neutralise=_neutralise (double neutralise; say acceptable), (b) add channel.py to NO_HOOK_OK (weakens rule), (c) other. Add the test to the rewrite list; name AST tests at :136-150 and 238-250 for BS-0 confirmation.
- M2. P1d.md:161 put-back count test gives no single formula (sum/max/min over key of k x key of p); e(k) uses smallest over scan_keyset(O), M38 flips to largest. Give one formula (e.g. max over keys of non-overlapping occurrences) or drop the test and decide at BS-0 with an explicit rule.

NITS
- N1. P1d.md:127-129 step b1 order (tag deletion, backspace overstrike, ANSI/C1/lone-ESC): say binding or irrelevant (BS after ESC[0m).
- N2. Neutraliser description incomplete (P1d.md:19, D11 :39): gate.normalise also runs _INVISIBLE_IN_NAME (ZWSP, SHY) and _CONTROL_CHARS deletes bidi controls; list in the card-entry carrier list; changes raw-family assignment (H17).
- N3. `views=%d` (P1d.md:182) undefined: do skipped identity steps / duplicates count.
- N4. Builder must invent: apply_settings call site (app.py after :79), which post_card (app.build local closure :186-192 vs channel.post_card), whether the LookalikeCopy catch wraps both `summary` calls (app.py:195 and Approvals.request), time check inside _finish.
- N5. FakeChannel.send moves to card_text (no joined pass): state accepted.
- N6. P1d-learn: `views_of_r` undefined (= _healing_views(r)?), wrong cite redact.py:896 (is 897), say r = fits_after_nfkc(_clean(text)).
NOT CHECKED: textnorm items, probe results and hand-traced rows, _learn_aws regexes, the 23/24/25 pytest.raises mapping (tests/test_k5_round12_fuzz.py:149 not on rewrite list), other tests pinning clean/FakeChannel.sent/_blocks, tools.py/k1b/judge.py etc., BS numbers, LEAD-ORDERS, template compliance.

# Look-alike design, round 7, correctness review (draft 7)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Target: `designs/lookalike-leak.md` draft 7 (head `2c60222`). Reviewer: `egm:egm-codebase-details`. No shell, so every recount was done by hand. Did not open `reviews/`.

Verdict: no Blocker. Two Majors (COR-LK7-1, COR-LK7-2), both about test rows or mutant killers that cannot do what the text says. Ten findings in all (2 Major, 8 Nit).

## Findings

**COR-LK7-1 | Major | lines 96 (LK-PH-ENT), 121 (M6), 46**
- LK-PH-ENT builds a copy of V as "head ending `&#6`, a checked e-mail, tail starting `5;`" and expects the e-mail to become a placeholder that the restore form deletes, so the pieces join as `&#65;`.
- That e-mail cannot become a placeholder. The EMAIL pattern (redact.py 244-245) has a lookbehind that the `6` breaks, and ends with `\b`, which does not match between the TLD letter and the `5`. The sweep for a stored non-secret e-mail (`_replace_standalone`, redact.py 1516-1517) refuses a copy touched by an ASCII letter or digit on either side. So the e-mail stays in clear, no placeholder exists, and the row does not test deletion versus space. M6's first killer is this row, so that half of M6 has no working killer.
- LK-PH (line 95) has the same hazard whenever V's head or tail ends in an ASCII letter or digit next to the e-mail.
- Fix: use an already-issued token in model-written text (`&#6<EMAIL_1>5;` with `<EMAIL_1>` held in the map), or split the entity at `&` and `#65;`. State in LK-PH that the neighbours of the e-mail must be non-ASCII-alphanumeric.

**COR-LK7-2 | Major | lines 121 (M18b), 83 (LK-TAG)**
- M18b is "search stops at the first key of a multi-key text", killed by LK-TAG bare. P1 line 58 defines `scan_keyset(raw)` as "the set of the non-empty results", up to 8 keys. A set has no first key. With tag characters interleaved, T0 and T2 contain V's key and T1 and T3 do not, so a mutant that tests one key survives or dies depending on set order and hash seed. The return type (set, frozenset, tuple) is UNVERIFIED.
- Fix: define the mutant as "only `sorted(keys)[0]` is tested" and add two inputs, one whose hit is the smallest key and one whose hit is the largest; or substitute a key-ordering wrapper.

**COR-LK7-3 | Nit | lines 67-68, 73, 130**: P1.md line 67 (RES-1, one space per placeholder) and line 274 (PENDING LEAD 31) still say one space, but draft 7 replaced that with the restore form (PL-LK-37). P1's merge-order sentence (line 22) ends "P2d-2, P4d-a2-i", with no P2d-2b. Fix: add a P1 item to section 8.

**COR-LK7-4 | Nit | line 131**: the list of stale P2d lines is wrong. Line 22 has nothing about P1b. Lines that say P1b is not needed: 3, 30, 33, 34, 71, 264, 266, 315, 334. The design misses 71, 266, 315 and 334. (Note from the lead session: the round 10 P1 resolve gave a different list, 3, 30, 33, 34, 264, 266, 315, 334, 339, and called line 71 correct; the P2d author must grep, not trust either list.)

**COR-LK7-5 | Nit | lines 9(c), 43, 118, 167**: section 1(c) and PL-LK-36 say a value is covered when each of its scan keys has 8 or more characters. Item 1 and GOLD-1 drop short keys one by one, so a value stays covered through any key of 8 or more. They differ for a value that carries tag characters, because T3 is short. Fix: say "at least one key of 8 or more; shorter keys are dropped".

**COR-LK7-6 | Nit | lines 35, 119, 130**: LK-BE is "Cyrillic Be for b", a strict xfail. confusables.txt line 2289 maps capital Be U+0411 to `b` plus a combining macron; small Be U+0431 maps to `6` (line 1980). If LK-BE uses the capital, the strict xfail turns into an XPASS failure when P1 takes the rule. Fix: pin LK-BE to small Be U+0431.

**COR-LK7-7 | Nit | line 118 (GOLD-1)**: GOLD-1 holds "on every LK row" as `any(k in s ...)`, but LK-UNFOLD (line 107) and FR-9, FR-33, FR-35, FR-8 are refusals by exception, not by a key hit. Fix: restrict GOLD-1 to rows where `scan_keyset` succeeds and add the raise clause.

**COR-LK7-8 | Nit | lines 120 (FR-13), 46 (item 3)**: FR-13's seeded map is built only from placeholders in the text (channel.py 54), so the row needs `<IPV4_1>` in the card text as well as the lower-case `seed<ipv4_1>`. Rule (ii) puts back the original of a seed placeholder, the literal `"\0seed<IPV4_1>"`, which adds the letters `seedipv41` to the key of every card text that holds a genuine placeholder; this is not stated. Fix: say seed placeholders are deleted (or restored on purpose, with a row), and fix the FR-13 input.

**COR-LK7-9 | Nit | lines 54, 113 (LK-CARD)**: `requests.summary` returns a fallback card when the main text is refused, but the fallback is itself passed through `clean(...)` (requests.py 47-50) and holds `plan.agent_id`, `action_id`, `target.system`. If one holds `password=<V>` plus a copy, the second `clean` raises `LookalikeCopy`, uncaught (`TooDeep` can do the same today). Fix: state it or add a row.

**COR-LK7-10 | Nit | lines 51, 139**: `error_reason` redacting with `mapping` instead of `{}` (P2d-2b): `redact_text` ends with `mapping.clear(); mapping.update(current)` (runmap.py 526-527), so on a successful pass the exception message now adds values to the live run map. Growth of the map by error text, and the interplay with the map-size check at agent_loop 502, are not stated. Fix: one sentence and one row.

## Orders
- Order 11: (1) closed in v1; (2) options (a), (b), (c) compared, (b) picked, named rows for the table, percent-encoded plain letters is LK-PCT-PLAIN; (5) is section 9 with acceptance rows. The 12-or-more rule is narrowed by the key-length rule (PL-LK-36), a declared deviation, not a hidden one. Order 11(2) says to put the design in the P1 and P2d tickets; the design only supplies text for P2d rev 6, and P2d is still rev 5 (process note, same pattern as order 13(1)).
- Order 13: (1) in section 7 (P-1, IN/OUT outcomes, old middle step deleted) and in the P2d rev 6 text in section 8; (2) the retire-list line and the Warden ticket text are present.
- Order 8(5): placeholders only.

## Checked and correct (by hand)
- LK ids: 40 table lines (79-118) = 39 lines plus GOLD-1; lines 88 and 108 hold 3 ids each; 43 ids plus GOLD-1. Strict xfail rows: 8 always, 10 in outcome OUT. FR rows: 31. Mutant names: 50 numbers plus M9b and M18b = 52; deleted 20; live 32 (30 in P2d-2, 2 in P2d-2b: M41, M44). Constants: 2 (IN) or 3 (OUT). Timing arithmetic consistent (4,000 and 256,000 tests).
- Code citations confirmed in the snapshot: runmap.py (PLACEHOLDER, undo, canonical, escape_placeholders, redact_untrusted, redact_text 462-528, SAFE_HEAD_NOTE, redact_bounded, _redact_value), redact.py (redact signature 869-877, _Redactor.__init__, _over_budget, _aligned_fold, _withhold, sweep, _build, _sweep, redact_many 1527-1537, SECRET_KINDS, EMAIL, ACCOUNTID), tools.py (prepare_output, redact_layered, error_reason 987-1012, secret forms), agent_loop.py, requests.summary, channel.clean, k1b/redaction.py and replay.py, evals.py, judge.py, bedrock_guardrail.py, audit/capped.py, defaults.py, textnorm.py, _confusables.py (677 entries; U+0406 maps to `I`, U+0437 to `3`, U+03B7 to `n`). The "too large to show" assertions at test_k5_round8.py 203 and test_k5_round12_fuzz.py 200. `error_reason` call shapes are compatible with a trailing keyword-only `mapping`.
- P1 rev 11: `scan_keyset` has one parameter and no clock; keys keep `str.isalnum()` characters with `l` to `i` and `z` to `3`, at most 8 keys; entity step present (since cut in P1 rev 12 per order 14); `REFUSAL_HANDLERS` has three entries with `check_lookalike` first; `TextTooLong` and `NotText` raised as the design says.
- UTS rows U+0127, U+0126, U+0167, U+0180, U+01B6, U+0268 are MA entries of ASCII plus an overlay (table drops them); U+0289 not checked.

## Unverified or not reached
Counts of 177 MA entries and 148 letters; all timing figures, S_call and the "0 hits in 8,000" prototype; Python 3.13.18 and Unicode 15.1.0 version claims; behaviour of rows not traced (`_DIGITS` for LK-KIND-NUM beyond S4 in P1); P1 "Stated limits (11)" and PENDING LEAD 29, 34-37 beyond the lines read; the Warden and demo checkouts; plan-v3 and amendments citations; the approval console and what card-site callers do with a `RedactionError`; whether core main equals the snapshot; section 9 line numbers beyond the greps; `_scrub` 898-933; evidence.py 85-110 and 169-220; P2d.md lines beyond the grep; "no test pins today's bundle behaviour" (already marked UNVERIFIED in the design).

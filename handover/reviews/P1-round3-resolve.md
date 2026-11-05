# P1 round 3 resolve report (egm:egm-resolve, Opus 5.5)

Status: resolved (categorised; ticket NOT edited here; the author rewrites revision 5)
Target: `handover/tickets/P1.md` rev 4 (221513b). Inputs: `P1-round3-adversarial.md` (A1-A20), `P1-round3-correctness.md` (C1-C22). Auto mode: interactive gate skipped. CONTEST 0, ESCALATE 0.
Extra inputs from the lead and the P0a author (2026-11-05): (1) PENDING LEAD, recommended: drop P1c (stored keys) from v1 and make it a separate later ticket; until the lead answers, the author keeps P1c as a clearly separable section and fixes it; findings marked [P1c] become MOOT if the lead drops it. (2) The ticket must say that P1a adds `THIRD-PARTY-NOTICES.md` with the Unicode License v3 text for `tools/data/confusables.txt`, `_confusables.py` and the generator (found by the P0a author; the permission text is nowhere in the repository today).

| id | category | decision for revision 5 |
|---|---|---|
| A1 (blocker) | PROPOSE FIX | Remove the choice point from the DENY keys: in the scan view map the confusable classes (z/3/Ze) to ONE class on needle and haystack (over-match is the safe side); add a squashed key with ALL whitespace removed; scan tag-decoded text as a suffix reading; redo the key bound; hostile rows for the three bypasses and a test that every mixed-reading text matches. Subsumes C18. |
| A2 (blocker) | PROPOSE FIX | `scan_hit(..., refuse_hidden=True)` default: refuse when tag or variation-selector characters exist; `view="id"` also scans the tag-decoded reading; add FE00-FE0F and U+E0001 to `has_hidden_channel`. |
| A3 + C5 + A14 + C21 | PROPOSE FIX | Set `TEXTNORM_MAX_NEEDLES` and a total-needle-characters cap from a measurement at the real worst case on the final code (read-only tables, 3 passes, 16 x 16 keys); monotonic deadline inside `scan_hit` returning refuse; count with `islice(cap+1)`; perf row = worst case. |
| A4 | PROPOSE FIX | Make `scan_contains` private; publish `deny_hit` (True = refuse) catching `Exception`; AST lint banning `except` around textnorm calls outside textnorm; rule: any exception in `allow_equal` = not equal. |
| A5 + C1 | PROPOSE FIX | Compute the real maximum table value length (3 today, plus gap-2 entries) as a constant asserted by a test; define ONE size rule (sum over distinct characters of max(NFKD length, table length), ASCII shortcut) and state the consequence for the redactor invariant; rows at 131,073 ASCII characters and cap+1. |
| A6 | PROPOSE FIX | Drop `name_key` from VIEWS and `stored_key`, or label it "prose only"; one canonical name per view; test `VIEWS` equals the accepted view-name set. |
| A7 + C6 + C11 [P1c] | PROPOSE FIX | Require `key_id` when a salt is given; reject short or empty salts (constant in defaults); `key_id` grammar `[A-Za-z0-9._-]{1,32}`; key check value so a wrong salt under the same id raises `SaltMismatch`; HMAC over version, view and key; empty-key-set rule stated and tested; document or drop the `n=` leak. |
| A8 [P1c] | PROPOSE FIX | Separate version string per view; exclude `html5` from stored-identity `beh`; accepted read-set of versions during a deploy window; state the human-decision bound as a number or formula. |
| A9 | PROPOSE FIX | State the narrowing honestly (56 entries); differential test old-vs-new `same_person` with a named exception list; "reflexive for every x within the cap that converges". |
| A10 | PROPOSE FIX | Bounded entity step before `squeeze` in the id view (same 8 rounds, same refusal); id-view entity rows. |
| A11 | PROPOSE FIX | Introspection test: every module-level constant is in `beh` or an exclusion list; golden Test 2 fails (not skips) in CI when `GOLDEN_BASE_REF` is missing or `git show` fails; integer-arithmetic fuzz; revert procedure = new `alg`. See C15 for the lint-clean way to read the base file. |
| A12 + C17 | PROPOSE FIX | Define a P1c shim; `xfail(strict=True, raises=AssertionError)`; reword Done ("fails on the old behaviour" only for the named shim at the named head). |
| A13 | PROPOSE FIX | Validate blocklist entries at load (`require_key`, minimum key length constant); a bad entry is reported at load, not as refuse-all at scan time. |
| A15 | PROPOSE FIX | Document the `str` conversion callers must use for `StrEnum`; test it. |
| A16 + C9 | PROPOSE FIX | State "at most 2 changing passes plus 1 confirming pass"; test the boundary; give `scan_match` a signature and place in the public list. |
| A17 | PROPOSE FIX | Provisional `alg` string carries a marker (`fold1p`) that `check_stored` always refuses. |
| A18 | PROPOSE FIX | Rename the stored record `stored_form`; one default for `loose`; one canonical key-set form; tell P5a to map `TextnormError` by base class. |
| A19 + C7 + C22 | PROPOSE FIX | Raise P1m to Tier A (the runner copies trees and kills process groups); add a P1m Tests field with the moved runner and judge tests and their fail-before (list the 748849c test names); consider `tools/` placement for `testing/mutation.py`. |
| A20 | PROPOSE FIX | Version-dependent counts (677, 56, 670, 114, 15.1.0) asserted as properties on every interpreter; counts only in the golden/report. |
| C2 | PROPOSE FIX | Give each case reading as an explicit step order (A = table, casefold, loop; B = casefold, table, loop); state which one `identity_key` equals; rows for Eta, Nu, Upsilon, palochka, Sigma both ways. |
| C3 | PROPOSE FIX | `id_key` decodes U+E0020-E007E in place (memo 1 section 6); fail-before rows: IBAN in tags; invoice number in tags beside its prefix. Overlaps A2. |
| C4 | PROPOSE FIX | Move `keyset_encode` to P1a as a pure helper that P1c reuses; fix the P1b golden entry. |
| C8 | PROPOSE FIX | Decide: `fold_key` becomes an alias of `identity_key` (recommended); state which equality `allow_equal` LOOKALIKE uses; correct the "line 125" claim; Ze and tag rows. |
| C10 | PROPOSE FIX | `re.fullmatch`/`\Z` for the version echo; test a trailing newline. |
| C12 | PROPOSE FIX | List files per PR, including `textnorm.py`, the manifest, golden file, corpus and `THIRD-PARTY-NOTICES.md`. |
| C13 | PROPOSE FIX | Add the manifest test; say whether P1m files are pinned. |
| C14 | PROPOSE FIX | Hash only what exists in each PR (`beh`). |
| C15 | PROPOSE FIX | Read the base file through a lint-clean route (no `subprocess` S603/S607): a fixture path the lead supplies, or a git API call; no suppressions. |
| C16 | PROPOSE FIX | State that `testing/mutation.py` (95 vs 105 lines) and `promoted_mutants.py` (1,425 vs 2,149 lines) also differ at 2e8a28c. |
| C18 | PROPOSE FIX | Covered by A1; add the hostile row. |
| C19 | PROPOSE FIX | State that P5a depends on P1a and P1b; add P1m to the hot-file/overlap table; fix the memo-5 file list for P2a. |
| C20 | PROPOSE FIX | Correct the generator line cites (77-78; 82-90; 75). |

Counts: 42 finding ids (A1-A20, C1-C22); PROPOSE FIX 42; CONTEST 0; ESCALATE 0; DECLINE 0. PENDING LEAD: drop P1c from v1 (recommended yes); P1m tier raised to A (consistent with order 6(b), which does not list P1m as Tier B). Severity unchanged. Downstream: P2d waits for P1b with A1/A2/A4 fixed; P3b waits for P1c. Model: Opus 5.5 (resolve skill).

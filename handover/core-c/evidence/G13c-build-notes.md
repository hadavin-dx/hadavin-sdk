# G13c build notes (fix of the G13/G13b design review round 2: M-A, M-B, budget DoS, m1, m2, docstrings)

Branch wip-g13c on cloud/core-c. Code commit "code G: G13c ..." (src, tests). Measured on this box (shared, loaded), direct `_touching_piece` calls.

## M-B (CPU): head test before the slice
Value of 65,536 `q`, text of 16 keys with 65,535 `x` between (no head hit): before 1.74 s CPU, after 0.13 s (the rest is the regex scan).
Test G13c-1: a counting str subclass records every slice; the gap with no head hit cuts at most the two gap slices per key (mutants E19v left, E19w right).

## M-A (memory): `seen` keeps a digest of a long piece
Value `aaaac...` (16,384), text `aaaab`*3000 + distinct 5-digit tail before each of 16 keys: tracemalloc peak 367 MB before, 7.1 MB after (blake2b 16 bytes for a piece > 64 chars; shorter pieces kept as text so G13b-4 still sees ~275 chars).
Test G13c-2 (6 keys, peak < 40 MB, mutant E19x).

## Per-key cap
`_KEY_HITS_MAX = 4096` head hits around one key (both sides, repeated pieces included: the hash/cut of a repeated long piece is the CPU). Past it InputTooLarge -> `mask_budget_exceeded` (fail closed; permanent while the text stays in history; stated in the docstrings).
Corpus: 1,978 property inputs through redact_text -> snapshot -> held_in_views: 0 InputTooLarge at caps 4096, 256, 64, 16, 8, 4, 2, 1 (no input has more than 1 hit around a key), 0 held. Dense hostile (value `aaaa`+c*16380, 8 x (16,000 `a` + `b<HOST_1>`)): before 1,022,038 characters of budget (~16k lookups a key), 0.54 s CPU, accepted; after refused at the first key after 4,096 lookups (260,374 characters), 0.02 s.
Tests G13c-3 (boundary 4,096 / 4,097 each side, per key not per text; gate level in test_model_gate.py: mask_budget_exceeded; mutants E19y, z, za, zb).

## m2: separators-only values
Not the literal "whole piece in values": `longest - 1` limits the gap, and a whole value beside a key is already refused by the sweep (verified before and after: `!!!!!!!!<HOST_1>`, `x....----<HOST_1>` net True at HEAD). The real hole is a PIECE (4-7 characters) of an all-separator value. Rule: `_piece_index` keeps the values made only of separators in their own sorted lists (forward, reversed); a piece of only separators is looked up there (a piece of such a value is a piece however short), a piece with another character in the usual lists; separators that start `-----BEGIN KEY-----` stay exempt (G13b-1 unchanged). Test G13c-4, mutants E19zc (left), E19zd (right).

## m1: `_LEAD`
Auth words case-insensitive `(?i:...)`: Bearer, Basic, Token, Digest, OAuth, ApiKey, Negotiate, NTLM, AWS4-HMAC-SHA256, Bot, Key. Test G13c-5: 14 leads (two lengths, lower/upper case, a two-space lead): lead sent, lead + 1 secret character refused; a value that IS the lead sent. Mutants E19t (case), E19u (NTLM).

## Docstrings and the stated limit
`_touching_piece`, `_piece_index`, model_gate.py SECURITY text (permanent for the run; the cap; the word list). G13c-6 pins the CURRENT behaviour (`the quick brown fox` + `the <HOST_1>` refused, `held_value_left`), G13c-6b strict xfail for the desired no-refusal; mutant E19ze. The letter-only rule and a distinct refusal code were NOT built (lead decisions).

## Anchors
E19b, f, m, n, o, q re-anchored (lines changed). MIN_MUTANTS 128 -> 140 (12 new: E19t..E19ze).

## Pre-existing at cloud/core-c HEAD (verified in a clean worktree): E19g and E19i report BAD OTHER_TEST (another param of test_g13_10 fails first than the pinned `[full-width document]`).

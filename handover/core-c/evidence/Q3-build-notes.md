# Q3 build notes: G15 independent final net (P8 flow review item 6)

Branch wip/cloud-core-c/q3-g15-net (from origin/cloud/core-c d993b4eed). Defaults only; no lead-approved values.

## What was built
- `src/hadavin_sdk/guard/finalnet.py` (new): `FinalNet` (Aho-Corasick, own goto/fail/owner tables, no regex from client values, no `_Redactor`/trie/runmap checker), `secret_left(text, secrets) -> index|None` (never the value), `FinalNetTooLarge` (fixed text), `MAX_STATES = defaults.MAX_MAP_CHARS` (524,288 states, explicit cap).
  Views are PRODUCED by `runmap._clean`, `runmap._windows`, `runmap._views`, `runmap._b64_units`/`_b64_text`, `runmap.canonical/composed`; matching is only in this module.
- Wiring in `guard/model_gate.py`: `BoundGate._final_net_finds`, called at the end of `_enforced` on the final `sent` messages and `docs` (after every existing check). New `CODE_FINAL_NET = "final_net_refused"`, in `AUDIT_CODES`, exception `FinalNetRefused(UnmaskedInput)`, audited via `_note` like the other enforce refusals. `FinalNetTooLarge` also gives that code. Secret set = `MapSnapshot.secret_values` (same set and 4-character threshold as the existing net, not weakened). Automaton kept on the bound gate while the value set is equal; clean texts remembered by SHA-256 (bounded by `GATE_CACHE_MAX_ENTRIES`).
- Barriers (needed so the net does not refuse what the existing net passes): an exact key of the map; the fixed words of the trusted framing (`_fixed_spans`). A forged placeholder-shaped token is plain text.
- Docstring bullet in the model_gate SECURITY block with named tests (`F::` prefix added to the D8 test: it now reads tests/test_finalnet.py).

## Behaviour change (flag for lead)
`test_g13b_5_...` pinned "a base64 copy of a secret is sent". The lead asked for the base64 view, so that limit is closed: the call is now refused `final_net_refused`. The test was updated; the docstring line says so.

## Gap-style notes for the docs pass (root SECURITY.md not edited)
1. G15 reads only the views `runmap._views` makes plus ONE base64 level; ROT13, hex, reversed text, words not found.
2. A value spanning two chunks the gate enforced separately is not seen (as in the existing net); the final net reads each whole message, so only the framing-word barrier cuts a value.
3. Cost: views are made twice per text (existing net and final net); a text up to the cap with many views doubles that part of the cost. Not measured at the cap.
4. Cap: 524,288 states (value characters, plus folded spellings of non-ASCII values). A larger map refuses every call with `final_net_refused` (fixed text). The cap is a default for the lead to confirm. Memory at the cap is about 50 MB by estimate, NOT MEASURED.
5. A secret equal to an ordinary word that also occurs in clean text is refused permanently (same as the existing G13c stated limit, now also via this net: the plain substring has no word-boundary rule). This widens the false-positive surface compared to the sweep for values that are short common strings (4+ characters) which the map holds as SECRET kind but the sweep would have replaced anyway; after the sweep they are placeholders, so only unreplaced copies (decoded views) can trigger it.

## Tests
TESTED (this worktree, load about 3-4 from other builders):
- tests/test_finalnet.py: 22 passed.
- tests/test_model_gate.py + test_runmap_enforce_map.py + test_gate_install_callers.py + test_s3_gate.py: 388 passed, 7 xfailed (before the docstring/D8 edits); test_model_gate + test_finalnet after: 304 passed, 1 xfailed.
- Hostile tests: blind redactor (`_Redactor.sweep` and runmap net monkeypatched to nothing) still refused, with control showing the call IS sent when the final net is off; zero-width split; NUL split; UTF-16 as UTF-8; NFD vs NFC; base64; percent and backslash-u copies; overlapping and nested values and suffix links; 1 MB text with 2,000 values (fail steps <= text length, 60 s generous bound); periodic and repeated-prefix text (fail steps <= text length); clean text byte-identical (same object); state cap with fixed text; map key and framing words as barriers; net follows map growth.
- Mutants Q3a..Q3v (22) added to tests/gate_mutants.py (runner test list now includes tests/test_finalnet.py): first subset run 17 of 22 good, the 5 that crashed (an exception instead of an assertion) had their killers rewritten; rerun of those 5: 5 of 5 killed (so 22 of 22 Q3 mutants killed, TESTED). MIN_MUTANTS in tests/test_gate_mutants_picked_up.py set to 181 (159 + 22, measured by importing tests.gate_mutants).
- ruff check and format: clean for the files touched (a pre-existing SIM102 in k1b/bundle.py is not mine).

Final light batch (test_model_gate, test_runmap_enforce_map, test_gate_mutants_picked_up, test_gate_install_callers, test_s3_gate, test_finalnet): 413 passed, 1 skipped (the full-mutant test), 7 xfailed.

NOT RUN: the whole gate_mutants.py run (the other 159 mutants were not re-run against the new wiring; only the Q3 subset), the property corpus tests, the whole-suite run. The lead said load was over the cap and a redact_mutants run was active.

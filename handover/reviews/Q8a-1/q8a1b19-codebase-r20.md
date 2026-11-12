# q8a1b19-codebase-r20: Q8a-1 batch 19, head a24d98ae, round 20, persona codebase details

Source: hand-back of the codebase reviewer (agent a4e1c8b1a1e9bdb76), saved by the lead (condensed). SECURITY path (no round cap). Read-only; no independent evidence existed when read. 0 Blocker, 0 Major, 3 Minor (F1-F3), 2 Nit (F4-F5). Snapshot `/home/user/build/snap/q8a1b19-a24d98ae`. Verdict: r19 Blocker (non-dict and invalid-JSON bypass) closed at the choke point for every entry shape traced (27 shapes, three class-method overrides, chain walked); Issues 2-8 and 11 fixed or honestly narrowed.

## Minor
- **F1** `config._rebuilt` (config.py:665-667, used by `_pairs` 670-678 and `_value_free_text` 696) decides "already rebuilt" by every problem input equal to the literal `<hidden>`: forgeable marker. A plain (non-HiddenInputModel) error whose refused values are all that text skips the rebuild, so `error_where(cleaned=True)` can show a word-like key. Fix: mark the rebuilt error positively (private subclass or attribute set only in `without_input`), or always rebuild (`without_input` is idempotent, pinned) keeping field names.
- **F2** `_text_keys_only` (hidden_input.py:203-204, 222-223) reads `args[0]` only: `model_validate(obj={1: x})`, `model_validate_strings(obj=...)` skip it and raise a bare TypeError (no refused text leaked, contract for `{1: x}` broken for the keyword spelling); a non-dict Mapping with non-text keys is not covered. No test or Z259-Z261 covers `obj=`. Fix: read `kwargs.get("obj")`, add a row.
- **F3** Known-receiver rule for `.count/.index/.find` (tests/_text_guard.py:1123-1124, `_string_names` 1129-1146) trusts ANY literal assignment to a bare name; `x = []` then `x = get_client()` then `log.warning('%d', x.count(name))` is dropped as a number (r18 Issue 6b shape for the name receiver). Fix: every binding must be a literal (as `env` does); plant plus mutant.

## Nit
- **F4** CHANGELOG:37 item 1 numbers with no stored proof (76 classes, 11 shapes, 532 to 0, 9.8 vs 1.55 microseconds; probe not committed; test uses 27 shapes and `> 40`); "76 plus the base = 77" not stated vs item 9 "pinned at 77". Fix: commit the probe and output, or soften.
- **F5** Mutant ids: Z264 does not exist (stated in CHANGELOG); brief range Z259-Z277.

## Checked and found fine
Issue 1 trace (raise outside `except`, `without_input`, `_without_chain`, `_all_text` walking str, repr, args, errors in all forms, json, ctx errors and the cause chain; 27 shapes per class; seeded fuzz; routing control; Z192-Z194 and Z259-Z263/Z265 anchors present each with a named killer). Issue 2 (no `strict=`/`context=`/`from_attributes=` in src; AST test exists). Issue 3 receivers fixed. Issue 4 Z163 to Z258, Z159 restored. Issue 5 STORE_READS 14 + STORE_WRITES 18 = 32 = protocol 32. Issue 6 named in CHANGELOG as not seen. Issue 7 bundle `_listed_names`. Issue 8 R17t/u renamed, R19h-j plants. MRO of Settings correct. Issue 10 OWNER-ONLY.

## Not checked
Ran nothing; no independent evidence for a24d98ae; the 433 vs 445 mutant count (own grep, inconclusive); Issue 9 sub-items (a)-(g) seen only in the CHANGELOG; Z269-Z277 kill reasons; pydantic-core behaviour for a non-dict Mapping; builder environment not stated in notes.

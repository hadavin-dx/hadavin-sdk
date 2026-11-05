# P2d round 2, adversarial (egm:egm-design), head d6be4de. Condensed by orchestrator. Verdict: NOT CLEAN. 0 Blocker, 1 Major, 9 Minor/Nit. Nothing run by the reviewer; probe figures and U-labels UNVERIFIED.
| id | sev | problem | fix |
|---|---|---|---|
| R2-1 | MAJOR | Storing the written spelling in the map breaks `sweep`/`_build` (redact.py 1256-1333): a secret found by context (`password=hunt<ZWSP>er2`) used to be stored folded, so later clear copies were swept; with the written slice stored the clear copy is not swept (leak regression). `runmap._decoded_masks` (424-450) also scans non-ASCII originals with no budget check. "No new exposure" unsupported. | Keep a second sweep-only record of the folded spelling, or prove by test the sweep still catches clear copies; add row (ZWSP secret then clear copy on another line), HOSTILE-1 timing row for `_decoded_masks`, sweep mutant. |
| R2-2 | MINOR | "ASCII-only LINE takes the old path" false in mixed texts: `bank_near` set by any bank word in the folded text widens ordinary BANKACCT masking on ASCII lines (over-masking). | Reword to "ASCII-only TEXT"; state widening in CHANGELOG; add row. |
| R2-3 | MINOR | Moved test 17 is in no placement list (31 of 32 placed). | Add to `test_redact_fold.py`. |
| R2-4 | MINOR | Deadline "at every loop level" / "budget plus one pass" overclaims: unchecked work in `_fold_scan` per-line fold, `_line_hits`, 1182-1183, ordinary loop, `sweep`. | State the bound is measured; list unchecked segments. |
| R2-5 | MINOR | `RedactionResult.restore` (redact.py 862) is a second restore path; `_folded_line` docstring says restore gives folded value. L5 has no trigger. | Cover in same decision; fix docstring; L5 trigger "P5c ticket cites this section". |
| R2-6 | MINOR | `_mask_ex` registers placeholders before the look-alike check and round discard: orphan map entries, double numbering on withheld lines. | Register only after commit; test no orphans. |
| R2-7 | MINOR | Edit (a) rewrites what existing mutants 18, 19 and N1 target; only some marked rewrite-snippet; 18 and N1 near-duplicates. | Mark; merge. |
| R2-8 | MINOR | `_char_class` lru_cache cleared only before patching `fold`. | cache_clear after the patch too. |
| R2-9 | MINOR | Done not gated on L1, L4, L6; step-2 file names collide with the other package. | Add to Done; rename files `P2d-1-step2-*`. |
| R2-10 | NIT | Disposition ADV-F5 omits that accented e-mail placeholders stay unrestored. | One sentence in disposition and L1. |
Checked fine: D1 premise, V5/V8 cites, cap = NFKD sum (`runmap._expanded_len` 139), counts 66/21/32. Not clean: round 3 required after fixes.

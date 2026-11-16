# Look-alike design round 2: correctness review (draft 2)

Reviewer: fresh Sonnet reviewer (a49936f805448cf9c), read-only, no code run. Saved by the lead session; condensed from the hand-back. UNVERIFIED by execution: leak-table rows, prototype figures (0 hits in 8,000 keys, 0.25 s), timings; whether `scan_keyset` has an entity step.

| id | sev | problem | fix |
|---|---|---|---|
| COR-LK2-1 | MAJOR | Sentinel assumes U+FFFD survives `scan_keyset`; P1.md lines 61 and 116 say it is dropped; segments join, LK-PH/M6 break. (Matches RES-1 of P1 round 7 resolve.) | Per-segment `scan_keyset`, no join; section 13 "unverified" becomes "contradicted by P1.md:116". |
| COR-LK2-2 | MAJOR | Section 7 says email/host/IP mask case variants; LK-KIND/FR-7/M8 expect an all-caps email to be refused; EMAIL pattern (redact.py 244-246) and `_mask_ex` (1236-1237) mask it. | Build LK-KIND/FR-7/M8 on a variant the pattern cannot read. |
| COR-LK2-3 | MAJOR | Section 9 false: `ACCOUNTID` (360) and `PHONE` (479-484) mask plain digit runs; IBAN (253-260) has no check-digit validation; HIGHENTROPY minimum 40 chars (647-648) not stated. | Rewrite section 9 and ACC-1 by length; fix IBAN description. |
| COR-LK2-4 | MINOR | agent_loop cites 469/495/649 are the except lines; calls at 470/496/650; line 377 missing. | Cite 377, 470, 496, 650. |
| COR-LK2-5 | MINOR | `capped.py:71`, `safe_head`, `tools.py:1005` pass `{}`; K empty; `guard/__init__.py:3` re-export not mentioned. | State which callers get protection. |
| COR-LK2-6 | MINOR | NAME/ADDRESS/TENANT have patterns; NAME/ADDRESS case-sensitive, TENANT `(?i)`. | Reword. |
| COR-LK2-7 | MINOR | "Four cases where the sweep leaves a plain copy": only the glued-identifier case produces refusals. | Reduce item 1. |
| COR-LK2-8 | MINOR | Section 8 says P1 lines 19/196/198 say P2d-2 follows P1b; they say the opposite (changed by order 11 and P1 round 7 resolve). | Correct. |
| COR-LK2-9 | MINOR | COR-R5-3/R5-4 are P4a findings; no P2d round-5 correctness report; same slip in lookalike-round1-resolve.md:47. | Drop them. |
| COR-LK2-10 | MINOR | FR-6 is both xfail and killer of M9; xfail cannot kill a mutant. | Strict xfail or make LK-SHORT the killer. |
| COR-LK2-11 | MINOR | PIN rows have no mutant (stage 1/2 without `_lookalike=False`); LK-CM/CN/TAG/ENT/ORDER/SPLIT no named killer. | Add mutant and killers. |
| COR-LK2-12 | MINOR | GOLD-1 writes `deny_hit([v])`; real signature differs and `refuse_hidden=True` refuses without a match. (Moot after P1 PL27 cut: GOLD-1 gets a plain-`in` oracle.) | New oracle. |
| COR-LK2-13 | NIT | `_sweep` 1485-1500, int/float return 598-600. | Fix cites. |
| COR-LK2-14 | NIT | `LK-` prefix used for rows and lead items. | Rename lead items `PL-LK-n`. |
| COR-LK2-15 | NIT | "2.3 s of its 2.0 s budget" garbled. | Reword (moot after the cut). |
| COR-LK2-16 | NIT | `REDACT_BUDGET_S` 6.0 s thread CPU not stated. | State it. |

Verified, no finding: constants and function cites in redact.py/runmap.py, cache equality key, `redact_text` flow and `RedactionError("LookalikeCopy")` wrap, bank-context cites, confusables entries, `fold` drop classes, id-collision check, section cross-references.

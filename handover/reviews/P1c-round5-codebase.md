# P1c ticket rev 6, Goldfish review round 5, codebase-details (egm:egm-codebase-details, Sonnet, read-only, ran nothing)

Saved by the lead's worker from the hand-back; wording condensed. No Blocker, no Major, 4 Minors, 3 Nits. All by reading; nothing was run (speed, prototype figures, licences UNVERIFIED).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R5-COD-1 | Minor | 52, 38 (item 6), 105 (B55) | Class-line cites wrong in runmap.py: RedactionError is :38 (not :36), InputTooLarge :42 (not :40; item 6 says :41), B55 cites escape_placeholders :327-331 but it is :322-327. TooDeep :98 is right. | Change to :38, :42, :42, :322-327. |
| R5-COD-2 | Minor | 38 (item 6) | "redact rebuilds its finders, redact.py:893-917" is imprecise: that range is _Redactor.__init__ (cache skip :915-917); the rebuild is _build :973-1009, called from sweep :1027-1028. | Cite :973-1009 and :1027-1028 for the rebuild; keep :893-917 for the map copy. |
| R5-COD-3 | Minor | 34 (item 3) | Glued-prefix example wrong: `blob_` is 5 characters, so grid offset 1, not 3. B32 is right (offset equals prefix length). | Use a 3-character prefix (e.g. `x-a`) or say `blob_` is offset 1. |
| R5-COD-4 | Minor | 114 vs 83-85 | "hostile, runs alone" -k list does not match the row tags: B34 tagged hostile but not listed; B33 and B35 listed but not tagged. | Make list and tags agree. |
| R5-COD-5 | Nit | 38 (item 6), 105 | redact._LABELS is private; runmap.py imports only public names and already imports PATTERNS. | Use `{label for label, _ in PATTERNS}` or name the import. |
| R5-COD-6 | Nit | 5 vs 37 | Summary says T = P + U; item 5 says T = P + newline + U. | Fix summary. |
| R5-COD-7 | Nit | 106 (H11, H2) | With a literal `<domain>`, H11's `db.local.<domain>.com` is masked (`.<` is not `.\w`). Test needs a made-up word label. | Add "written with a made-up word label, not the literal <domain>". |

## Verified by reading (summary)
runmap.py insertion points (redact_text :464, try :487, except :520-523, neutralise :489-490, scan gate :491-492, cache :493 is a real move, views loop :507-518, adoption test :517); agent_loop error codes (document_too_large :371-375, redaction_error :468-469/:547-549, TooDeep falls to redaction_error :376-377); redact.py HOSTNAME :387-393, _KEPT_HOST :809-811 end-anchored, cache equality semantics (use `cache` when not None, never `or {}`); defaults.py constants block (6 constants), line 12 is 118 columns; overlap 4*ceil(8192/3)+4 = 10,928 and stride 54,608 = 4*13,652, window starts keep the grid, offset-3 reasoning; short-run arithmetic (4 bytes 6 chars, 8 bytes 11, 9 bytes 12); counts 157 = 93+50+11+3, 155 pass + 2 xfail, 48 mutants each with an existing killer, 139 lines, 10,071 words.
## Not checked (UNVERIFIED)
CHANGELOG.md, tests/test_k5_fixes2.py:96, tools/mutation_runner.py, tests/mutation_runner_mutants.py, pyproject.toml (not in the snapshot); ticket cites to P5a.md:36, P5c.md:1030, P2d.md; licence and version claims; all prototype/base-run figures; H7 regex timing; whether P1b fold views reach escape_placeholders.

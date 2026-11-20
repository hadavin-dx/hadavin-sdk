# E9 (2) result review round 2 (design critic, fresh, sonnet) — 2026-11-20 ~10:50Z
Snapshot scratchpad/refs/e9r2 (HEAD 1bf4f11ba line). Read only. No Blocker, no Major, 5 Nits.
Leaks: none new. _OWN_OUTPUT (redact.py:889-892) used only in _decide (:1680), gated by label == SECRET plus fullmatch; glued, other-kind, cut-off, lowercase, non-ASCII-digit forms masked (own_output.py:93-116,:190-218; hardening.py:56-68,:123-168). No ReDoS. redact(), redact_many, redact_text/redact_untrusted and enforce_map agree; junk entries (option a) harmless and pinned (hardening.py:199-242; own_output.py:226-242).
- N1 stale docstrings: hardening.py:3-6, own_output.py:10-13 ("escaped lookalikes and genuine placeholders left alone"; "nothing added to a map ... restores to nothing" false for other kinds: they make a junk entry; `‹SECRET_1›<UUID_3>` is masked, own_output.py:190-195). Reword "SECRET tokens only; other kinds are masked and make a junk entry".
- N2 redact.py:870-885 comment: junk entry also from user-typed `password=‹JWT_1›`; HIGHENTROPY, URLCRED, PHONE kinds named but untested.
- N3 lowercase `<secret_1>` masked (safe, pinned hardening.py:64). No action.
- N4 test gap behind "harmless": no test puts a junk entry (`<EMA`, `<EMAIL_`, `‹JWT_1›`) in the run map and then runs enforce_map, redact_text or redact_many on a later text containing a real `<EMAIL_1>` or `x<EMA<IPV4_1>`; entries are secret kind, 4+ chars, swept in every copy, edge values held back (runmap.py:681). Add one test.
- N5 evidence figures not verifiable from the snapshot; tests/redact_mutants.py not opened.
Not read: redact.py 977-1559, 1790-2287; runmap.py 1-260, 400-530, 778-950; ESCALATIONS E9 vs code.
Resolution (core-c): N1, N2, N4 to be fixed in one small commit after the codebase reviewer reports; N3 none; N5 evidence recheck by the fixer.

# v12-CHANGES (revision 12 of LEAD-CHECKLIST-v5.md; builder, 2026-11-16)
Checklist sha256 (final): ede7e96e2f4d6737cb6baf59720bd3108dad346f5252f0d2fa8a476c8a844849. Fill list: NOT edited, sha256 still da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca (so no fingerprint to update). Backups: LEAD-CHECKLIST-v5.rev11.md, LEAD-FILL-list-v5.rev11.md.

## Not run / not verified (first)
- Only `bash -n` on all 45 bash blocks (0 errors) and my own greps. NO behaviour test of the changed blocks (D1, C4 fill, rows, C8, WSL-4/D2 order): none run in a harness, none in Git Bash, WSL, PowerShell.
- C4 string compare assumes each plan table row starts `| ID |` and quotes the strings.txt column-3 text verbatim (same row match the fill sed already uses). The plan file was not at hand to confirm; if the plan escapes characters in the table, the new check STOPs (fails closed) and the lead tells the builder.
- Register grep `(^|[^0-9:-])PID([^0-9:-]|$)` untested against a real register; it fails closed (STOP D1).
- Line numbers in the reviews were approximate; I located each place by text.

## Changes
| finding | change | where |
|---|---|---|
| F1 Major | D1 greps only `kill exit=3([^0-9]|$)`; STOP text, text above and below the block, and table row D1 say "after exit 3"; a normal GONE-FAIL still allows R2 (plan 13.1) | D1b, D1 text, table E row D1 |
| F2 Major | C4 fill: STOP unless rows.txt line 1 is `head=<PIN>`; each strings.txt column-3 string must be in the plan table row of its id (grep -F), else STOP and fill nothing | C4 fill block and its intro |
| readiness m1 | row C1 now: folder missing = do not make it, ask in channel; other name = fix WTN | table E |
| readiness m2 | section 0: a person in the channel (or L2 answered) is needed before starting; lists the STOPs and pins that depend on it | section 0 |
| readiness m3 | C8 grep -o patterns end in a letter, digit or underscore (no trailing . / -) in both places | C8 |
| adversarial m (line 136) | A5b4 text says the STOP gives the `aside` command (nothing deleted), not mv | A5b4 |
| adversarial m (WSL-4) | the three places with `< /proc/.../cmdline 2>/dev/null` now `2>/dev/null < file` (error silent when pid is gone) | WSL-4, D1a, D2 |
| adversarial m (D1 register) | grep -w replaced by a whole-number pattern that ignores digits next to `-` or `:` (dates) | D1b |
| adversarial m (rows rc) | rows returns non-zero and prints STOP when git grep exits above 1 (1 = no match stays an empty field) | rows helper |
| revision label | revision 12 in title, section 0, changes paragraph | top, end |

## Minors not fixed, and why
- Hand-typed P-4b-HIT control file still passes: it is the disclosed lead attestation; closing it needs a real WSL process proof (impossible without running WSL; owner/lead step).
- C9 "P-3a done" not bound to session: binding needs a runner-side token in the plan (plan edit, outside this file).
- c7check 7-char count weak: no concrete better check found without the plan text; left.
- The bash -n check of rows ran on text only (see above).

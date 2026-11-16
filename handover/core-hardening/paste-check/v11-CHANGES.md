# v11-CHANGES (revision 11 of LEAD-CHECKLIST-v5.md and LEAD-FILL-list-v5.md; builder, 2026-11-16)
Checklist sha256 (final): 67111574af9b9a3c7551939d6482b89508e360d60472721efb3786db1d69a759. Fill list sha256 da2635db2d7c329169eca1aba285e47fd17fd734908bce20dff3a55c122ee9ca.

## Failed, unverified or not done (first)
- Not run anywhere real: Git Bash, PowerShell, WSL, real n8n, Git for Windows patch. The positive WSL guard was not run (only the "not WSL" side).
- I did not re-verify each of the minor findings m5 to m14 (adversarial) and the stranger nits one by one after a context reset; they are covered by the grouped rows below and by the harness cases in evidence-c11.md, not by a line-by-line tick list. The independent reviewer should check them against the diff of rev10 to rev11.
- P1 (owner user names in plan paths, evidence-chain item 6): NOT edited (plan/inputs issue); listed in v11-OPEN-FOR-LEAD.md.
- PLAN-CHAIN.md has stale values (S1 in the open list); not mine to edit.
- During tests I found one real gap and fixed it: STOP B1 "unknown question" had no Next: line.
- The test tree needed /c and /mnt/c; both existed as dangling links to /tmp/c10ev/c from an earlier pass (I did not delete them: the removal was blocked; I made /tmp/c10ev/c point to my scratch instead and remove only that).

## Table (finding id: what changed, where, how checked)
| finding | what changed | where | how checked |
|---|---|---|---|
| stranger Blocker 1 (question 2 / L1) | open ruling made a step B2 with exact replacement words (outcome A/B/C), then accept 2; L1_RULED guard | section 1 variables, B2, fill list row 2 | B2 and accept 2 negative and positive in evidence-c11.md |
| stranger M2 (tell the builder dead end) | fallback: stay stopped, save lines in a note file, see L2 | section 0, v11-OPEN-FOR-LEAD L2 | read |
| stranger M3 (WT, W3, register unexplained) | explained in section 0 and 1 | section 0/1 | read |
| stranger M4 (spaces, backslashes) | values written between single quotes; norm converts C:\ form | section 1 | hbok cases |
| stranger M5 / adversarial m2 (C8 not real) | C8 compares plan guesses with your names | C8 | C8 ok run; guess names case |
| stranger M6 (autocrlf) | narrow -c way and printed restore command | 0b | block 1 syntax; read |
| stranger M7 / adversarial M7 (D2 unguarded) | WSL-only first line, exit codes, working folder and containers scanned | D2 blocks | non-WSL STOP run |
| stranger M8 (naming) | v5 meaning fixed in section 0 words | top of file | read |
| stranger M9 (A6 loop) | A6 names a state further than CHAIN and the way out (aside, restart) | A6 | CHAIN=2 on chain-3 plan |
| stranger nits | tool check moved to A0, clean minimum explained, labels explained, citations to v11-OPEN-FOR-LEAD.md, B1 Next added | A0, section 0, E | read; STOP/Next script |
| adversarial M1 (chain proof) | A6 and A8 check checksum and chain marks (S10-G1/G2, COPY_OK); C7 and C9 repeat it | A6, A8, c7check | M1 negative run |
| adversarial M2 (7-char, BR) | C7 checks 7-char pin form, BR in at least 3 lines; C2 refuses a second different pin | C2, C7 | wrong BR case |
| adversarial M3 (aside) | helper aside with mv -n and numbered suffix | section 1 | .old, .old2 run |
| adversarial M4 (hbok, quoting) | hbok refuses quote, dollar, backtick, relative, dot parts | section 1 | six hbok cases |
| adversarial M5 (D1 pid) | pid digits, at least 2, equals pid printed by D1a, in register, no GONE-FAIL/kill exit=3, no repeat | D1a, D1b | eight D1b cases |
| adversarial M6 (control file, exit codes, mktemp, cd) | WSL-3 tests exit code and mktemp, cd checked, WSL-4 needs HBW and control file | C2b | C2b run in Linux |
| adversarial M8 (accept 2) | accept 2 refuses while PF still says the owner decides | accept | accept 2 negative |
| adversarial M9 (fingerprints) | A2 checks full sha256 of every executed file and writes a proof file; A3 to A5b4 refuse without it | A2, chain_step, step4 | A2 missing-file case |
| adversarial m1, m3, m4 | rows exit code kept (rows.rc), mktemp checked, A1 simplified | C4, section 1, A1 | C4 run |
| adversarial m5 to m14 | grouped, see failed list above | various | not individually ticked |
| evidence citation 1, 2 (Q1/L2 references) | references point to the right ids in v11-OPEN-FOR-LEAD.md | checklist | grep |
| evidence citation 3 (stale v9 name) | v9 file name replaced | fill list | grep |
| evidence citation 4 (stray sha256sum line in A2) | A2 prints no stray line | A2 | missing-file run |
| evidence item 6 | not edited; OPEN P1 | v11-OPEN-FOR-LEAD.md | n/a |

## STOP ids whose text changed in revision 11 (all have a row in table E)
VARS, EV, CHAIN, A2, A3, A4, A5b, A5b4, A6, A8, A9, B1, B2, C2, C2b, C2c, C4, C5, C6, C7, C8, C8b, C9, D1, D2, ASIDE.

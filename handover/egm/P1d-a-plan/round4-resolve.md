# P1d-a plan, pass 3 (round 4 files), resolve (egm:egm-resolve, Opus 5.5 through the Skill tool)
Status: resolved. Ticket rev 6 -> rev 7. Inputs: round4-readiness.md (4B/5M/2N), round4-design.md (2B/5M/4N). 22 findings in 11 groups: all PROPOSE FIX, 0 CONTEST, 0 ESCALATE (lead questions stay NEEDS LEAD 1, 2, 3, 5), 0 DECLINE. Redaction path: UNCAPPED, a fresh pass follows. Admitted: rev 6 named the K41 fix without writing it and left A15/A44 unreconciled.
Probe P7 (handover/evidence/P1d-a/probes-r5/) ran the written grammar on 0dabf1f's src (model path): rows K41-K43, HL1, Q2-Q22b, H34a-b, SC1, PU1, F16, Q6, BTK1 as written; 100 KB hostile inputs 0.17-0.5 s. It caught one bug in my first draft (single `&` look-ahead took `&amp` of `&amp;next=`); fixed with `(?:amp;)?`. The gate (D1, D3, D4) is not probed.

| group | decision written into rev 7 |
|---|---|
| G1 K41 (blocker) | plain and query key prefix `[\w.\-]*` (lookbehind starts the run, so linear); suffix `{0,255}` in plain, query and both quoted entries; rows K41, K41q, K42a/c/q/d, K43a/b; base cells "same as input (P7)"; non-goal N8; mutants A45-A48, A50-A51 |
| G2 ReDoS | row HL1 (five 30,000-char inputs, 3 s each); A15 and A52 killed by time; NEEDS LEAD 4 closed (reopens only if they survive) |
| G3 AST choke point (blocker) | `test_every_card_exit_wraps_defang_text` defined on data flow in three parts; A44 row; BS-0 step 6 grep extended to card exits |
| G4 rebase and Depends | "the P1b branch"; no product dependency; default base 0dabf1f; re-run BS-0 on a moved main, lead writes the new sha; five files everywhere |
| G5 phases | every row and property in one phase; pb rows pass in every phase |
| G6 differential | one definition (frozen base sanitise_text for LIT and 2,000 G-TXT texts; WITHHELD line rule) |
| G7 fixture parts | all secret-looking literals in two parts; reword on a scanner hit, never suppress |
| G8 backtick swallow | row BTK1; defang_text is the post-redaction guard; scheme and mention removal not recomputed (N7); follow-up = NEEDS LEAD 5 (DEFAULT: ledger row P1d-learn) |
| G9 `=` in query value | look-ahead = field name IDF (letter or `_`, up to 20 name chars, `=`); rows Q18-Q22b; mutants A8, A14, A20, A21, A39, A24, A36, A40, A55, A56, A58; S7 split into S7a (reported) and S7b (gated, 25 samples); 660 total; NEEDS LEAD 1 carries the base S7b leak count |
| G10 wide dots | D4: `_wide_ascii` on prose parts when defang=False; rows D4a-c; A49; N5 limited to the model path |
| G11 Alternatives, Risks, nits | three alternatives and the prefix alternative added; risks ReDoS, over-masking, markdown-it (base dependency, pyproject line 15); counts by script (88 rows: fb 46, pb 39, ow 3; 60 mutants); N6 defined; R3 line numbers; round naming by resolve file |

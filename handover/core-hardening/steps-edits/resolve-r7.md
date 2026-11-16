# C4 resolve pass, round 7 (money, secret and delete paths: no round cap), 2026-11-16
Status: fixes applied by the builder by hand. The `egm:egm-resolve` skill was NOT used: it runs interactively (multiple-choice gates) and I did not run it headless; I did not try to start it. So this log is the builder's own resolve, not an EGM resolve; the studio lead decides whether to run `egm:egm-resolve` over it. Only `EDITS.md` changed (round 6 is kept as `EDITS.round6.md`, round 5 as `EDITS.round5.md`), plus this log, `resolve-r7-check-output.txt` and `checkpoint-r7.md`. `inputs/` untouched (file times 09:00 to 09:58 UTC). Nothing run except text checks by script; no code, network, spend or commit. The result of round 7 is NOT reviewed yet.

## Failures, gaps and open items first
- NEEDS-LEAD (not fixable from this folder): (1) EL-1 to EL-7 exist only in one paragraph (C4 brief not in the folder); next step: check against the brief, write result in `ANSWERS-c4.md`. (2) `review-codebase-1.md` is not in `inputs/`; E-31 (finding M-1) and E-40/E-44 (F-01) quote it; next step: read it. (3) D5 S9-5 and S9-12: the text of rules A, E, F, I is in no input, so no AGENT-SCOPE row was written (a guess would be worse); next step: supply the rule text, then write one MUST NOT row. (4) NOT DECIDED 8 (new): how the preparation enquiry reaches the accounts; AGENT-SCOPE row text for the second option is written inside ND8, not as a row. (5) NOT DECIDED 1 to 7 still open as before.
- Needs the owner: ND3 option b (one line), ND6 option B (a money yes with a number), ND7a/7b (key facts).
- Unproven and stated as such in the texts: Postgres design (planned, not yet proven), flow rehearsal cost (planned at US$0), no-paid-call path of the preparation enquiry, the pause prompt after the code change, what the row preview shows, where to revoke the model secret key.
- My own slip during this round: my first run of the E-37 replacement cut the row at the heading line inside the fenced block (a `## ` line), leaving a duplicate old fragment; I found it by grep, deleted the fragment and re-ran the full check. The same `## ` line inside a block exists in the round 6 file too (it is inside a fence, so it is text, but a simple line reader can mistake it for a heading; my script respects fences).
- Not checked: see the last bullet of "What I did not check" in `EDITS.md`.

## Findings -> fix -> check (design review, `review-c4-r6-design.md`)
| finding | fix | check |
|---|---|---|
| M-A E-03 Postgres as fact | E-03: "planned, not yet proven", first trial kept a simpler database; two tests "planned at US$0" | read E-03; text matches E-25 item 15, E-27, E-28 |
| M-B G1 not carried | E-12 fact 4 (end-of-take step no longer deletes; commit id, saved test output, reviewers' report named); E-37 paragraph (v3 steps 16 and 18 say "archived", today's code deletes, so no yes and no take until the message names the change); G1 paragraph and rule R6 | read E-12, E-37, G1, R6 |
| M-C E-48 conditional | E-48 applies always; the assistant asks at clean-up; revoke only on a clear yes; S9-3 stays; ND7 default and gate cell updated | status Apply now in header and index; counts |
| M-D E-11 path | E-11 owner text: the assistant tells the way and whether it counts against the 3 calls before sending; path is UNVERIFIED; NOT DECIDED 8 with both options and AGENT-SCOPE MAY and MUST NOT text for option B; contact added to E-12 as fact 5 | read E-11, ND8, E-12 |
| m1 E-09 old text | old text runs through the full stop; tail "(the lead gives the start command; you type the password)." replaced | script: old once on line 78 |
| m2 ND4 options | ND4: one allowed option (the app user); administrator, n8n's own user, counting user listed as NOT allowed | read ND4 |
| m3 ND1 | (b) and (c) say a secret-handling script change needs independent review with no round cap; "not on a command line" in (a), (b) and in E-09 | read ND1, E-09 |
| m4 E-25 item 15 source | "planned ... the studio lead's instruction of 2026-11-16, not proven" | read E-25 |
| m5 E-15 label | "test screenshot" label, who, when, pass, fail | read E-15 |
| m6 US$0 | "planned at US$0" in E-03, E-11, glossary | grep |
| m7 E-12 contact | fact 5 | read E-12 |
| m8 hedges | E-30 "planned ... expected"; E-48 "planned to be deleted" | read |
| m9 S9-5, S9-12 | new section "Decision D5": covered, not covered, NEEDS-LEAD with the exact missing input | read section |

## Findings -> fix -> check (naive review, `review-c4-r6-naive.md`)
| finding | fix | check |
|---|---|---|
| E-12 nobody answers no; circular | owner named as the one who answers no; assistant must state five facts with numbers and file names; owner repeats them; reviewers are separate programs named in their report; rule R6 for the studio lead | read E-12 |
| counts-check phrases | one phrase "the counting check" (a small program of ours, not part of n8n, counts mails, contacts and table rows; no read-only database user of its own) in E-15, E-18, E-31, E-36 (public wording "a small counting program of ours (not part of n8n)"); E-15 gives who, when, pass, fail | grep "different database user": none in owner texts |
| "key" three meanings | glossary in E-01: secret key (also "token"), lead key, password; owner texts use "secret key" | script scan: no bare "key" in owner NEW texts after two fixes |
| E-01 "lead" | E-01 defines assistant versus the sheet's "the lead", enquiry, contact, lead key; owner texts say "the assistant"; E-03, E-09, E-11 old "the lead" replaced | script scan |
| E-06 + E-07 dangling "there", codes | E-07 applied now with neutral words (not yet confirmed; assistant checks first); E-08 neutral; G2 only chooses a second wording | read scratch line 85 of OWNER-STEPS; scan: no WP6/WSL-label/UNVERIFIED in E-06/E-07 text (WSL explained) |
| E-11 pass/fail, hidden mechanism, preparation names | pass and fail; "preparation" and "enquiry" one word each; E-04 points to the paragraph by its first words | read |
| E-37 | which wins (the sentence about the deadline wins); step 8 prohibition explained; "app passwords saved in files; the assistant asks where"; heading kept as a heading line | read E-37 |
| gates, "the lead" vs assistant, EL-1..7 | this file now says "the studio lead"; EL-1..7: NEEDS-LEAD with next step (confirmation g) | grep |
| minors: E-03 length, "take/flows/model stage" | E-03 split into short parts; words defined in E-01 | read |
| E-02 full stop, fix vs review rounds, nesting | old text through the full stop; short sentences; branch explained | script |
| E-14 overrule, "saved runs" | stated in text; defined in E-01 | read |
| E-16 owner part of decision | "you may be asked one yes or no question" | read |
| E-19/20/21 jargon | "release number 2.46.6", item (2) in words, "secret-key test" | read E-20 |
| E-22/E-25 "missed" | defined in E-12, E-22, E-25 item 18 | read |
| E-24 count 17 / 1 to 18 | verified against v3 lines 178 to 193 (items 1 to 9 and 11 to 14 live = 13; +4 = 17; item 10 removed) | read |
| E-27 to E-31 jargon, file not in inputs | E-31 says the file is not in `inputs/` and the finding is UNVERIFIED; NEEDS-LEAD | read |
| E-36 W cannot be verified by the owner | Why: owner relies on E-12 fact 1; UNVERIFIED which counts the program makes (confirmation b) | read |
| E-48 UNVERIFIED path, step numbers | step 22 items named; place told by the assistant before clean-up | read |
| E-43/E-46/E-47 joins | the resulting sentences are written in the Why of E-43 and E-46 | read |
| ND1/ND4 pass/fail; "password" three things | pass or fail added; three passwords told apart (glossary, E-09) | read |
| rows not applicable without guessing | E-07, E-08 applied (neutral); E-13 Hold with the exact missing input; E-04, E-05, E-41, E-42 Hold with the exact missing input (G1 line and the evidence file's quote of the prompt); E-36 has both texts; E-39 per-answer texts; ND2 default; ND3 owner answer text; ND6 studio lead task for the figure; ND5 stated as the studio lead's reading | read |

## Your specific orders
1 E-03 done. 2 G1 in E-12 and E-37 done. 3 E-48 always applies, S9-3 kept. 4 E-11 UNVERIFIED path plus ND8; contact in E-12. 5 E-12 done. 6 one phrase done. 7 glossary done (E-01). 8 E-07 applied neutral. 9 E-09, ND4, ND1 done. 10 minors done as listed. 11 script re-run: below.

## Checks by script (raw output: `resolve-r7-check-output.txt`; script `verify7.py`, in the session scratchpad, parses `EDITS.md` itself)
46 rows parsed; 47 old texts each occur exactly once in their input file on the stated line (E-13 two); 0 failures; 0 overlaps; all 37 Apply-now rows applied to scratch copies of the inputs without conflict (E-36 with text W); the 8 Hold rows that have one text (E-39 option b counted; E-13 has none) also apply without conflict in a second scratch copy; old and new texts have no edge spaces; index table equals row headers; banned vendor strings: none (list read from the repo test at run time); secret-like patterns: none; no personal path copied. Counts: Apply now 37, Hold 9, Conditional 0 = 46; OWNER-STEPS 29, AGENT-SCOPE 13, DECISION-one-store 4; types STALE 15, UNCLEAR WORD 8, MISSING STEP 10, CONTRADICTION 12, DEFERRED 1. Word scans of the owner texts: "login": none; "Re-checked": none; "WP6": only E-03 (the runbook file name that was already in the old text); "UNVERIFIED": E-01 and E-24 (both name the list by its title).

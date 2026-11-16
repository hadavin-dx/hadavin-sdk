# Resolve, EDITS round 9 (builder notes; the egm:egm-resolve skill was not used; result not yet reviewed)

## Failures and gaps first
- Not checked: the code (whether the take program has a contact delete call is NOT SETTLED, Q23); nothing was run in n8n; the click paths (HubSpot website, model provider key list) and the latest start time (about 18:14 UTC = 23:44 IST, a reading of OWNER-STEPS line 171) are UNVERIFIED; no stranger has read the new owner texts; the model stage accepting a made-up key and a stand-in address in the flow rehearsal is UNVERIFIED (ND6).
- My own slips in this round, found by verify9 and fixed: E-12 lacked a definition of "on screen"; one verify8 check was stale (E-52 "preparation" word, E-11 text) and was updated; the apply-now id check had to ignore the bracketed status note of E-07 and E-08.
- Open by design (NOT DECIDED rows with a safe default): ND12 (when v4 is issued; default a) and ND13 (older words no row touches; default a).

## Finding -> fix -> row
| Finding | Fix | Rows |
|---|---|---|
| Brief 1 / design M1, naive B10: delete stated as fact | Q23 wording; G1 opens on route 1 (test fails on old code) or route 2 (saved grep plus test); R9 applies the rows together | E-04, E-05, E-12 (fact 4), E-37, E-40 to E-45, G1, R9 |
| Brief 2: deadline | every second ask and last revoke 18:19 UTC = 23:49 IST; 18:29 UTC = 23:59 IST only as window end | E-48, R7, ND7, E-12 |
| Brief 3 / design M3, naive B8: E-11 | structural control: stand-in address 127.0.0.1 plus own-folder key file, named, owner written reply | E-11, ND6 |
| Brief 4: consent | written reply `Yes, send the one enquiry on <day>`; G5 opens on ND8 and ND6 only | E-49, E-50, E-53, G5 |
| Brief 5: hold rows | `[HOLD Gx: DO NOT APPLY]` on every held NEW; apply-now id list; gate display of E-07/E-08 | all Hold rows, E-36 text N, counts, index |
| Brief 6 / naive B2: E-12 | no offer to show secret files; one yes example; crash-check exception consistent; N1/N2; "not run", "on screen", "window" defined; bullets; latest start time | E-12 |
| Brief 7 / naive A1, A5: apply now | meaning, what falls away in v4, ND12, needs column, key line, crash case names, five "lead" meanings | head, index, E-37, E-01, E-52, ND12 |
| Brief 8: E-09 | sub-steps a to f, placeholders pending ND1/ND4 | E-09 |
| Brief 9: naive B3-B16, design m1-m5 | fixed in the rows (E-14 to E-19, E-22, E-25, E-48, E-51, E-52, new E-54) or NOT DECIDED with default | see Why lines; ND12, ND13 |

## Counts (computed)
52 rows (E-01 to E-54 without E-10 and E-35): OWNER-STEPS 34, AGENT-SCOPE 14, DECISION-one-store 4. Apply now 40, Hold 12, Conditional 0. Types: STALE 15, UNCLEAR WORD 10, MISSING STEP 14, CONTRADICTION 12, DEFERRED 1. 53 old texts, each once on its stated line, 0 overlaps; apply-now copy applied 40 rows, apply-all copy 51 rows with text; the apply-now copy has no hold label or hold text. Command: `python3 verify9.py > resolve-r9-check-output.txt`, last line `FAILURES 0`.

# fix-rwct29: round 29 fix of RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)
Fixer: one agent, 2026-11-16. Edited only RW and CT. Not committed.

## Failures and uncertainty first
- EGM review of this result was NOT run by me (I cannot invoke the egm:* reviewers from here). Nothing here is independently reviewed; the lead runs that step.
- Nothing is filmable yet. Five facts are still missing and are written as NOT WRITTEN: LEAD FILLS (list below). I invented none of them.
- First checker run failed once: check_runsheet_paste.py rejected my new B-195 string because it held the banned words "one database". I reworded both copies (RW and CT) and re-ran; the raw output below is the passing run.
- Static reading only. The n8n flow facts (attempts column) come from reading mf-form.json and mf-recovery.json, not from a run. The desk repository is not in this checkout, so the SpendLedger half of B-158 was NOT re-checked (kept SUPPORTED on the earlier trace; stated in the row).
- The relayed numbers (12 of 20, 2 of 5, 12 of 12, 40 of 80, leases 20/45/120 s, V7) are still unconfirmed; raw files not seen.
- HubSpot id vs vid stays UNVERIFIED (untouched). The Q28 scoped sentence is unchanged.
- Verdict counts unchanged (330 = 102 + 64 + 84 + 15 + 65; 96 flagged ids). RW rows 195 -> 197 (PASTE 53 -> 55; section 3: 74 -> 76); updated in RW lines 12, 42, 47 and the coverage line.

## Questions I propose (QUESTIONS.md not edited)
- NQ-1 (owner typed answers): In which scene and step does the studio owner type y, the 6-digit challenge number and end on camera, and does the video show it?
- NQ-2 (second send proof): The attempts column does not change on a repeat send, so what on screen shows that the second send happened: the reply of POST 2 (repeat true), the n8n run list with two runs for the lead ID, or a narrower caption? Until answered A-016f stays HELD.
- NQ-3 (order): Does P4a move before the practice run (step 2c), so the real CRM is known to accept an all-digit id before the practice run sends?
- NQ-4 (V7 word): May the word measured be used for V7 numbers on anything shown, although the raw files are only on the lead's laptop?
- Existing items still carrying missing inputs: people for voice rows etc. Q31 item 100; P4a send command Q31 item 94; scene 4 stop timing Q31 item 105; rehearsal start Q31 item 101; practice start on NO-GO path Q31 items 6 and 85.

## Finding to result
| # | Reviewer finding | My check | Result |
|---|---|---|---|
| 1 | Steps nobody can carry out | Confirmed in text; RW 75, 92, 137, 146, 157, 160 already said UNANSWERED but without the missing input in one place | Each now says NOT WRITTEN: LEAD FILLS with the exact input and Q31 item or NQ-1; RW 75 lists all three extra gaps; CT 46 WL-1 said "ANSWERED (nothing is missing)", contradicting RW, now fixed to match RW |
| 2 | Proof does not show second send | Partly contested: the exclusion covers only the reply TIME of POST 2 and the 10 s line, not its content. Confirmed in flows: Claim writes attempts 1, repeat is ON CONFLICT DO NOTHING, only ClaimStuck adds 1 | Defined attempts in RW step 6(b), step 15, A-016f note, row (s); CT 497, 69, 527 updated; lead decision NQ-2; caption unchanged |
| 3 | N-12 not in step 15 gate | Confirmed | N-12 added to RW 31 and step 15; CT 69 |
| 4 | Relayed facts lack wording | Confirmed | CT A-009, A-050, A-091 carry "reported by another test session; we have not seen its raw files"; A-009 marked HELD for D2 in CT (no RW row exists, none added) |
| 5 | V7 provenance two ways | Confirmed (RW 216, 298, CT 164) | One rule: lead read laptop-only raw files, counted RELAYED here; RW 216, 298, CT 164 aligned; NQ-4 |
| 6 | Stage service evidence contradictory | Contested with evidence: stage_server.py is present (handover/demo/n8n-mainframe, 60 lines) and I read all of it | CT B-158, B-159, B-160, B-207, A-004, X-3 and RW A-004 now cite lines read; B-158 SpendLedger part rests on earlier desk trace (stated); verdicts unchanged |
| 7 | B-173 vs B-179 | Confirmed | B-179 keeps SUPPORTED with a second verdict (OVERSTATED for the words, not counted); new RW rows B-179 and B-179b with a paste string; counts updated |
| 8 | B-195 does not say what is counted | Confirmed | New string says variant a, what a clean burst is, reused vs fresh stack; RW 412 and CT 947 identical; gloss added to RW A-002 and A-016c |
| 9 | Schedule | Partly contested: step 3 has a 0.5 hour window (RUNBOOK row 19); steps 4 and 5 lack durations. Confirmed the NO-GO re-pin clash and step order | RW 172 and 91 now state the RUNBOOK fit (rehearsal not before 07:40Z = 13:10 IST), missing durations, the clash, NQ-3 |

## Raw outputs (final run)
```
### python3 -I tools/check_refs.py
PASS 5175 references
rc=0
### python3 -I tools/check_names.py
PASS 655 rows
rc=0
### python3 -I tools/check_secrets.py
PASS 0 hits in 2711 files
rc=0
### python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
paste strings in RW: 142 | found word for word in CT: 142
not found in CT: 0
rc=0
### python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
section '1': 55 rows
section '2': 20 rows
section '3': 76 rows
section '7': 46 rows
total rows: 197
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 96 | with no row here: []
claim ids marked UNTRACED there: 64 | with no row here: 53 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
rc=0
### python3 claims-count.py CLAIMS-TABLE.md
verdicts: {'UNSUPPORTED': 15, 'OVERSTATED': 84, 'UNTRACED': 65, 'SUPPORTED': 102, 'RELAYED-ONLY': 64} total 330
lanes (A, B incl. X): {'A': 100, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 330 unique: 330
rc=0
### ruff format --check .
859 files already formatted
rc=0
```

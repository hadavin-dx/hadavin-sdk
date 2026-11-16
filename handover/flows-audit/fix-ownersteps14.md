# fix-ownersteps14 (fixer log, static edit, nothing ran except the four checks)

Target: OWNER-STEPS-q16-rows.md, owner part only. Lead part byte-identical to the backup (cmp rc=0, compared from the "## For the lead" line on).
Source: round-12z-findings.md, section "OWNER-STEPS owner part stranger read r12" (unverified reviewer words, each checked against the file first; all were true).

| Finding | Check | Change |
|---|---|---|
| B1 no end to "wait for new times" | true | new chase "missing: new day" (table row 0c, cancelled-chases paragraph, When things happen, chase list): 08:00 UTC (13:30 IST) on the first morning after the cancelled day, then each morning, last Sun 22 Nov |
| B2 slip and chase days | true | chosen: the same chases run on the new take day at the same clock times, moved by the slip days, unless the lead names other times (planned by the audit, lead to confirm) |
| M3 row 6 vs "answer messages that came" | true | row 6 (3) and item 6 now say: no further "missing" reply about a message that has not come, but you still answer any message that has come |
| M4 08:30 route missing | true | five routes; 08:30 silence route added as route 3; pointers added to rows 1a, 2a, 3, items 1 to 3 and the chase list |
| M5 late take-prep and delete message 1 | true | chase is the later of 08:30 and 90 min after the take-prep message; message 1 about 30 min after it; reminder is 60 min after the message, not a fixed 08:00; "no 08:00 fallback" stated |
| M6 retake | true | Case A (new yes with numbers) and Case B (standing yes covers it under the ceiling); the lead's take-prep message says which; lead update applied: planned default B (ceiling for 4 sends), A if the lead keeps 3 |
| M7 hiding addresses | true | recording-ready message names editing tool and method; else reply "missing: editing method" |
| Nits | partly | late answer at 08:35 does not revive the day; Tuesday silence rules, NO-GO, take, slip, stopped take defined in the cancelled-chases paragraph and words; "money stop" and "the repository" removed; n8n, Postgres, HubSpot explained at first use; row order explained |

Lead update applied (message during the work): ceiling for 4 sends; HubSpot test from about 07:05 UTC after the take-prep message; take-prep message within 5 minutes after the safety test ends and only if T19 and T20 pass; two NO-GO clocks (the lead's 14:00 UTC check first, owner silence at 16:00 UTC second, GO needs both); "safety test" = T19 to T21; no new yes for the HubSpot test unless the lead says so. All marked "planned by the audit, lead to confirm".

Extraction (scratchpad os14/extract.py, output os14/out.txt): the "missing:" words are counted per section (table, items, chase list); every chase word appears in the table and chase list; "missing: new day" and "missing: editing method" are in table and chase list (no item, like the Tuesday ones except editing method which is in item 5).

Checks (from handover/flows-audit): check_secrets rc=0 (0 hits); check_refs rc=0 (5146 references); ruff check . rc=0; ruff format --check OWNER-STEPS-q16-rows.md rc=0.
Not checked: reading by a fresh person; the rest of QUESTIONS.md; the lead part consistency with the new owner wording (not edited).

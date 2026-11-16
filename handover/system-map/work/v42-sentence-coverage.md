# v4.2 sentence coverage (2026-11-16)
Status: DRAFT, UNVERIFIED. Method: grep -n -i on `inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md`, each hit read in context, compared with `work/RUNBOOK-V4.3-PATCH.md` (read in full for the rows named). I did not open any path in `work/OWNER-ONLY.txt`. v4.2 not edited.

## Words with 0 hits (plain)
`lslocks`: 0 hits. `N8N_TESTS_REQUIRED`: 0. `TESTS_REQUIRED`: 0. `no archive call`: 0 (the v4.2 words are "no HubSpot write, delete or archive call", line 453). `deletes the contacts`: 0. `contacts deleted`: 0. `studio head`: 0.
(Patch rows P87 and P89 already say the same about lslocks and TESTS_REQUIRED.)

## Hits
| v4.2 line | Quoted words | Patch row that edits it | Result |
|---|---|---|---|
| 100 | "the lead never deletes; the owner bulk-deletes once after the take" | P08, P82 (clean-up wording; P08 quotes this sentence) | COVERED |
| 127 | "never delete or recreate the take folder while n8n runs" | none | NOT LISTED, but about a folder, not HubSpot contacts: no edit needed, no row added |
| 140 | "The lead's own HubSpot identity stays read-only and the lead never deletes" | P83 edits this line ("Step D" word only); the quoted words stay true (lead's own search tool) | COVERED (line edited; quoted words need no change) |
| 183 | "never delete a `.used` file" | none | NOT LISTED, but about a marker file: no edit needed, no row added |
| 272 (G13) | "read-only searches and never delete" | none; P81 note says the lead's search tool (HS-14, G13) stays read-only | COVERED (note only, no edit needed) |
| 306 (HS-14) | "shows a read-only identity" | none; same P81 note (lead's search tool, not the take program) | COVERED (note only, no edit needed) |
| 435 | "shows a read-only identity" (`<HS_SEARCH>`) | none; same P81 note | COVERED (note only, no edit needed) |
| 453 | "no HubSpot write, delete or archive call and shows a read-only identity at start-up" | P35, P81 | COVERED |
| 507 | "only reads HubSpot, never deletes" | P35, P81 | COVERED |
| 514 | "the take identity stays read-only and the lead never deletes" | P08, P51, P53, P54, P82 list line 514; P82 keeps the order; sentence stays true | COVERED |
| 515 | "does not delete it" (owner's n8n folder) | none | NOT LISTED, but about a folder, not contacts: no edit needed, no row added |

## NOT LISTED hits and rows added
Three lines (127, 183, 515) are not in any patch row. None is about the HubSpot archive or delete sentence, and the batch 3 sentence cannot apply to a folder or marker file. So I added NO row (P95 and later are unused) and made no history copy, because the patch file is unchanged. If the lead wants a no-edit row for them, say so.

## Not checked
Only the listed search words were used; a synonym could exist. P-row texts were read, not re-verified against code.

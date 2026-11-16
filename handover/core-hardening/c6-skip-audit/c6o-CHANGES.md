# c6o changes (2026-11-16, UTC; IST = UTC + 5:30)

REPORT-c6o.md supersedes REPORT-c6n.md (kept unchanged). Built by evidence-c6o/build_c6o.py and sections_c6o.py from REPORT-c6n.md. Nothing in the audited files was applied.

## Counts
94 rows (c6n had 72): 49 ready, 40 apply on a default, 3 wait for a check (23, 58, 59), 2 NOT FILMABLE (13, 21) until L-LEASE is answered.

## What changed
- Repeat send (B1): the flow files refuse a second send at any gap while the contact row exists (mf-form.json:97, mf_leads.sql:5, mf.py:45). The 45 s lease only decides when the recovery flow may take over an unfinished contact (mf-recovery.json:26). This differs from the reading in ORDERS.md Q21.2. Rows 13 and 21 are NOT FILMABLE; question L-LEASE (1, 2 or none) has no default.
- Row 11: no total for the card. New questions L-CARDLEN and L-SCENES.
- New rows 73-94: split of rows 1, 33, 39 (always part and question part), residual lines (RS:57, 52, 47, 6; PG:144, 121, 132; ONE:26, 1), n=2 corrections (47, 77-80), generator edit (92), carve-outs for RS:32 (93, 94).
- Labels "sped up, real wait" and the 45 s carve-out added where the c6n rows named timings.
- Row 6: run-sheet items 11-16 (second leak scan; deletion of saved runs and saving switched off after the take). Row 8: every request line of the take script read; HubSpot key scope UNVERIFIED.
- Box: glossary, L-CARDLEN, L-SCENES, L-LEASE rows, reply form for every question, who sets the n8n values.
- Stale wave-1 numbers in the glossary fixed in the final build.

## Evidence (evidence-c6o/)
verify-c6o.py (exits 1 on any failure; 60 checks, 0 failed), neg_controls_c6o.py (control passes, 23 changed copies all fail), void-check.py, static-checks.sh and their outputs.

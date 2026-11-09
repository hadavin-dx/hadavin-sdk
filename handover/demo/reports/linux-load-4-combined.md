# Load matrix 4: fix-3 base + cloud patch fix4 (1933731) + server.py hook edits (scratch copy). Numbers only, Linux 4 cores.
Compare with linux-load-3-fix3.md (same script, fix-3 unpatched). Raw: linux-load-4-combined-raw.txt, ...-kill-raw.txt, linux-load-3-fix3-kill-raw.txt. Single runs; a builder was running tests at the same time.
| mode | scenario | status | 5xx | client errors | max s | received vs decided | open receipts | CRM rows | emails | follow-up states |
|---|---|---|---|---|---|---|---|---|---|---|
| keyed | same x500 | 1x201 499x200 | 0 | 0 | 1.26 | 500/500 | 0 | 1 | 1 | sent 1 |
| keyed | same x1000 | 1x201 999x200 | 0 | 0 | 2.18 | 1000/1000 | 0 | 1 | 1 | sent 1 |
| keyed | diff x500 | 500x201 | 0 | 0 | 2.92 | 500/500 | 0 | 500 | 500 | sent 500 |
| keyed | diff x1000 | 935x201 65x503 | 65 | 0 | 5.46 | 935/935 | 0 | 935 | 935 | sent 935 |
| blind | same x500 | 1x201 499x200 | 0 | 0 | 1.27 | 500/500 | 0 | 1 | 1 | sent 1 |
| blind | same x1000 | 1x201 999x200 | 0 | 0 | 2.31 | 1000/1000 | 0 | 1 | 1 | sent 1 |
| blind | diff x500 | 500x201 | 0 | 0 | 2.82 | 500/500 | 0 | 500 | 500 | sent 500 |
| blind | diff x1000 | 876x201 124x503 | 124 | 0 | 5.90 | 876/876 | 0 | 876 | 876 | sent 876 |
Versus fix-3 unpatched: open receipts 20 -> 0 (blind diff x1000); lost receipts 0 in both; 503 under 1000 different leads NOT fixed (keyed 6 -> 65, blind 109 -> 124; single runs, noisy). A 503 means the request got no receipt, so the client must retry; no data is lost. Cause: write-gate / database wait (BUSY_WAIT 5 s) exceeded when 1000 different leads arrive at once; the max latency 5.5-5.9 s matches. Open for the lead: raise the wait (and Retry-After on 503) or accept honest 503.
## kill -9 mid-burst (5 rounds per mode, 200 leads each, desk restarted on the same book)
| tree | mode | 5xx | open receipts | CRM rows (200 leads) | emails | follow-up states |
|---|---|---|---|---|---|---|
| fix-3 unpatched | keyed x5 | 0 | 0 | 200 each round | 200 | sent 200 |
| fix-3 unpatched | blind x5 | 0 | 0 | 200 each | 199-200 | sent 189-194, unknown 6-11 |
| combined | keyed x5 | 0 | 0 | 200 each | 200 | sent 200 |
| combined | blind x5 | 0 | 0 | 171-187 | 160-167 | sent 159-166, unknown 34-41 |
Combined blind rounds: more follow-ups end `unknown` (34-41 vs 6-11) and some leads have no CRM row yet (13-29 per round): the CRM intent mark treats a crash between the mark and the put as unconfirmed and hands it to a person. No lead has more than one CRM row or email in any round (max per lead 1). Safe and visible, but the person has no correct button for it until finding M4 (decision crm_present) lands (fix5, in progress).

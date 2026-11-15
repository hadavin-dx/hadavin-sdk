# GO-1 plan (written before the final runs; the first two runs were already done when this was saved, see RESULTS-GO1)
Problem: n8n killed during an alert send leaves a 12 min claim (alert_until in the future), so the alert comes about 13 min late (KS, measured 780 s, n=2).
Fix (smallest): recovery flow gets an "n8n started" trigger and one SQL: clear alert_until and alert_token for rows with alert_sent=false, alert_token not null, state unknown/failed.
Pass: KS on the fixed flows gives exactly 1 alert, 1 intake mail, alert_sent true, alert well under 12 min (target under 150 s after restart). Old flows must fail the same case (alert at about 780 s).
No-harm: B90 (hold 90 s, no kill) on the fixed flows still exactly 1 alert (no start event, so nothing is cleared).
Mutant: clearing SQL changed to match nothing useful => alert late again.
Not tested: two n8n instances at once (T11); a second alert channel (by order, open item).

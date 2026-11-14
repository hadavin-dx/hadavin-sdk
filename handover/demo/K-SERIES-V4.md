# What must be re-run on v4 before the take, and the cost (for the A-vs-B decision)
v4 differs from v3 ONLY in the recovery flow: AlertClaim (window 720 s instead of 60..300 s steps) and the new node AlertBackoff. Sub-workflow, form and hook flows are byte-identical to v3 (script diff). Minutes below are MY ESTIMATES from reading the test code at --lease 20, one test per runner run, including about 2 minutes per run for stack and n8n start; NOT MEASURED. The lead has the real V7 timings in the raw files: replace my numbers with them. Runs are sequential on one runner (shared ports); I have not checked whether two runners can share a machine.

## Tier 1: tests that touch the changed nodes (state unknown or failed, so the alert sweep runs). Must re-run on v4.
| Test (v3 in V7?) | Why it touches the change | Est. runner minutes |
|---|---|---|
| B90 (not in V7; new) | the lane3 case: alert answer held 90 s; v4 expects 1 alert, attempts 1 | 8 |
| AF1 (yes) | retry after a refused alert now goes through AlertBackoff | 10 |
| AF2 (not in V7; new) | hung alert connection for 300 s, measures the node wait | 13 |
| T8 (yes) | 3 failed leads, one alert each, one at a time | 8 |
| T15 (yes) | CRM refuses everything: failed, 1 alert each | 12 |
| K3, K3B (yes) | unknown leads (mail may have gone), alert counted | 10 each = 20 |
| T12 (not in V7) | SMTP drop: unknown, 1 alert (the doubtful scene on the take) | 5 |
Tier 1 total about 76 minutes.

## Tier 2: tests whose flows path does not use the changed nodes (leads end done). Strictly not required by the diff; required by the rule "the flows the take uses are the flows that were tested".
| Test (yes = in V7) | Est. minutes |
|---|---|
| T14 idle stack: 0 sweep sends, 0 alerts (touches AlertClaim every tick: worth running) | 4 |
| K1, K2 | 10 each = 20 |
| T10 (CRM hold and SMTP hold; the SMTP hold can end unknown, so partly Tier 1) | 12 |
| T11 two recovery copies (also checks no duplicate alerts: partly Tier 1) | 4 |
| T13 | 5 |
| K4, K5, T9, M0, M1 (not in V7; K4 and K5 not changed by v4) | 0 unless you want them |
Tier 2 total about 45 minutes.

## Options for your decision
- Minimal for v4: Tier 1 + T14 + T11 = about 84 minutes. Whole series on v4: about 2 hours (121 min).
- If you decide for v3 instead: add B90 and AF2 on v3 only (about 21 minutes) to publish the duplicate as measured, and keep the page wording "can send two alerts".
- A caveat on both: B90 and AF2 have never run; if either fails or shows something unexpected, a fix and a rerun cost more than the numbers above.
Nothing in this file is a result.

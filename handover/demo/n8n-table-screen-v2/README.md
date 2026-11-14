# Lead table screen v2

Status: built, sample rendered with node, NOT run in n8n. Version 1 (folder n8n-table-screen) was run live on n8n 2.46.6 and works; v2 keeps its four nodes, node types and versions, and the same placeholder credential id PG_CREDENTIAL_ID (credential name n8n-publish-pg).

## What changed vs v1 (the 5 rehearsal problems)
1. State badges with colour and text: done green, unknown amber, failed red, processing grey. The grey badge also covers the other in-progress states from mf_leads.sql (new, review) and any unexpected value, which shows its own text.
2. Dark mode: all colours are CSS variables, with a light palette and a real dark palette chosen by prefers-color-scheme.
3. Plain words instead of raw cells: mail: sent / mail: sent, confirmation missing (state unknown) / mail: not sent; alert sent / alert waiting (state unknown or failed, not yet sent) / a dash; attempts shown as tries 1. The alert_attempts column is no longer read.
4. updated_at shows as HH:MM:SS UTC, no milliseconds, no raw ISO text.
5. One title: the tab title and the heading both say Lead table.

Also new: summary strip with counts per state above the table, sticky header, centred card, monospace lead_key, tabular numbers, row hover, footer line "refreshes every 5 s; made-up data", larger text for a 1080p recording.

Unchanged: 5 s auto-refresh (meta tag), every value HTML-escaped, no name or e-mail read. The SELECT reads only lead_key, state, attempts, mail_sent, alert_sent, updated_at.

## Nodes (n8n 2.46.6, no Code node)
1. Receive: Webhook 2, GET, path demo-table-v2, Respond to Webhook mode.
2. ReadLeads: Postgres 2.5, one SELECT, newest 50 rows.
3. BuildHtml: Set 3.4, run once, the whole page is built in one expression, as in v1. It uses only arrow functions, map, filter, join and string replace, as v1 did; no template literals and no statements. The expression contains no closing double brace (CSS is written to avoid it), because that would end the n8n expression early.
4. ReplyHtml: Respond to Webhook 1.4, text, Content-Type text/html.

An n8n HTML node was deliberately not used: it was not proven live, whereas the Set-node expression was.

## Import steps (UI)
1. Workflows, Import from file, choose mf-table-screen-v2.json.
2. Open ReadLeads and select the Postgres credential n8n-publish-pg.
3. The table mf_leads must exist (DDL in n8n-flows-v4, file mf_leads.sql).
4. Save and activate.
5. Open the production webhook address of the instance with the path /webhook/demo-table-v2 (same machine: the LOOPBACK address plus the n8n port). For a test run use /webhook-test/demo-table-v2 after pressing Listen for test event.

## LAPTOP IMPORT COMMANDS
UI: steps above.

CLI (run where n8n is installed):

    n8n import:workflow --input=mf-table-screen-v2.json

Then set the credential on ReadLeads in the UI (the file holds only the placeholder id) and activate the workflow in the UI. After a CLI import, restart n8n if the webhook does not answer.

Coexisting with v1: v2 uses the path demo-table-v2 and v1 uses demo-table, so both can be active together. If you instead change v2 back to the path demo-table, deactivate v1 first, because two active workflows cannot share one webhook path.

## Validation done
- JSON loads with python3; all four connections resolve; node types and versions equal v1.
- The Set-node expression was extracted and evaluated with node against made-up rows (done, unknown, failed, processing, an unknown state value, a value with angle brackets and an ampersand, a null time, and an empty table). Output saved as sample-output.html.
- Checks passed: no name or e-mail column, angle brackets escaped, times as HH:MM:SS, no milliseconds, counts correct, empty table shows a "No leads yet" line.

## Unverified
- Never run in n8n: the real expression parser, the Postgres date type as n8n delivers it (the code accepts an ISO string or a date object), and rendering in a real browser (colours, sticky header, dark mode) are not checked.
- Shows at most 50 rows, newest first; no paging. The page is public to anyone who can reach the webhook; do not expose it beyond the demo.

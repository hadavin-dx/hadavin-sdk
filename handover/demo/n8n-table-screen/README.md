# Lead table screen (doubtful-case scene)

Status: NOT RUN. No n8n or Postgres can start in this sandbox (disk), so this workflow was never executed. Only the JSON structure was checked.

## What it shows
A browser page with one table of the newest 50 rows of the table mf_leads: lead_key, state, attempts, mail_sent, alert_sent, alert_attempts, updated_at. No name or e-mail columns are read. The page reloads itself every 5 seconds, so a doubtful case (state unknown or failed, then alert_sent turning true) can be watched live.

## Nodes (n8n 2.46.6, n8n nodes only, no Code node)
1. Receive: Webhook, GET, path demo-table, response mode: Respond to Webhook.
2. ReadLeads: Postgres 2.5, one SELECT, credential n8n-publish-pg.
3. BuildHtml: Set 3.4, run once, builds the whole HTML string from all rows (one expression, rows are HTML-escaped).
4. ReplyHtml: Respond to Webhook 1.4, text with Content-Type text/html.

## Import steps
1. In n8n choose Workflows, Import from file, pick mf-table-screen.json.
2. Open the ReadLeads node and select the Postgres credential n8n-publish-pg (the file holds the placeholder id PG_CREDENTIAL_ID, as in the other flows).
3. Make sure the table mf_leads exists (DDL in the n8n-flows-v4 folder, file mf_leads.sql).
4. Save and activate the workflow.
5. In the browser open the production webhook address of your n8n instance with the path /webhook/demo-table (on the same machine use the LOOPBACK address and the n8n port). For a test run use the path /webhook-test/demo-table after pressing Listen for test event.

## Honest limits
- Never executed; the expression syntax in BuildHtml and the header option of ReplyHtml are unverified against a live n8n.
- Empty table: the page shows only the header row.
- Shows at most 50 rows, newest first; no paging, no filter.
- The page is public to anyone who can reach the webhook; it shows lead_key values, so do not expose it beyond the demo.
- Auto-refresh is a plain meta tag; it re-runs the query each time.

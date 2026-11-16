# Rows for OWNER-STEPS version 4 (from answer Q16; the coordinator pastes these)
Written by the flows-audit fixer. Text only; nothing was run. Made-up data only.

1. Lead table definition: the take uses the file demo/n8n-flows-v4/mf_leads.sql (the table with the four alert columns alert_sent, alert_token, alert_until and alert_attempts). Copy it into the take folder. Reason: the recovery flow mf-recovery.json needs these four columns. With the older table file the alert step fails every 30 seconds and the failure is not shown, so no alert mail would ever be sent. The coordinator checks at re-pin that the copied file is this one.
2. Check before the first send (re-smoke gate): run a psql query that lists the lead table columns and confirm that alert_sent, alert_token, alert_until and alert_attempts all exist. If one is missing, stop: do not send any lead.
3. Address placeholders: the mail steps still hold the words FROM_ADDRESS_PLACEHOLDER (the sender address) and INTAKE_ADDRESS_PLACEHOLDER (the intake mailbox address). The coordinator fills both with the program fill_flows during take preparation, from the owner's settings. The owner types nothing. The coordinator checks at re-pin that no placeholder is left in the four real-v5 flow files.

All three rows: the coordinator verifies at re-pin.

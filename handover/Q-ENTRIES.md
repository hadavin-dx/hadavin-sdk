
## q (cloud, A3 round 2): rename or caveat two payload fields?
M2: `access.portal_read_only:true` only means the /api/ui read connection is read-only; the portal also has Retry and Mark as sent. Proposal: rename to `ui_reads_read_only` and add `portal_can_change:["retry","resolve"]`. M3: `never_receives` lists what the AI step is not passed, but a live step can look up name/phone/company/message by lead_id. Proposal: add note `can_look_up_with_lead_id`. Both change the frontend contract; need your yes. Report: handover/demo/reports/portal-A3-review-2-security.md

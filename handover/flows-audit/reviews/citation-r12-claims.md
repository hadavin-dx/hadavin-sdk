# Citation check r12: CLAIMS-TABLE.md Table 1 (rows 1 to 52 incl. sub-rows)

Head sha at start: 4cdfd4d3024d80d152bd3cee00f849a6d8361cd8. When I finished, HEAD was 72298f21d (another session committed in between). Between the two, CLAIMS-TABLE.md changed in one line only (row 33c); the 33c quote still matches its source. Static read; nothing run; no fix-*.md file used as evidence.

Rows covered: 1-40 (40), sub-rows 7b, 8b, 25b, 25c, 33b, 33c, 33d (7), rows 78, 79, 85, 86, 87 (5) = 52.

Source locations used: handover/demo (VIDEO-RUNSHEET.md, DOUBTFUL-SCENE.md, PLAN-4-NLITE-FROM-LEAD.md, n8n-owns-vs-desk-owns.md, n8n-flows/PAGE-STATEMENTS-V4.md, n8n-flows/N8N-START.md, n8n-flows-real-v5/*), handover/flows-audit/inputs (OWNER-STEPS-realrun-v3.md, DECISION-one-store.md, AGENT-SCOPE-DO-AND-DONT.md), flows-audit/ORDERS.md.

## Counts
| result | count |
|---|---|
| Cites checked (file + line + quoted words) | about 95 |
| MATCH | about 92 |
| SOFT MISMATCH | 2 |
| MISMATCH | 0 |
| CANNOT-CHECK | 1 |

Rows with "no existing sentence" (7b, 85, 86, 87, 78): the "none" claims hold (see below).

## SOFT MISMATCH
1. Row 18, cite DOUBTFUL-SCENE.md:13. The row's quoted words ("a one-time n8n database-node preview selecting only the seven safe columns") are word for word at VIDEO-RUNSHEET.md:39 (MATCH). At DOUBTFUL-SCENE.md:13 the words are: "a one-time database-node preview, seven safe columns, no name or address". Same meaning; no "n8n", no "selecting only".
2. Row 19, cites PAGE-STATEMENTS-V4.md:134 and :156. The row's quote "can be about 13 minutes late (780 s, RELAYED-INDEPENDENT ...); it is not lost" is word for word at VIDEO-RUNSHEET.md:82 (MATCH) and "Alert after a crash during the alert send: up to 13 min late (n=2)." at :90 (MATCH). The PAGE-STATEMENTS lines say "An alert can arrive up to about 13 minutes late ... it is not lost." (:134) and "up to 13 minutes late (KS n=2, 780 s), not lost" (:156). Same meaning, different words.

## CANNOT-CHECK
- Row 33 note cites AGENT-SCOPE-DO-AND-DONT.md:20 as a place where "the same wrong sentence stands". The file exists (flows-audit/inputs) and line 20 says the code archives HubSpot contacts "as a DELETE call"; that is the correct fact, not the "archives" wording, so the "same wrong sentence" statement is not borne out by that line. Treat as SOFT MISMATCH; the row's own parenthesis says the F-01 fix file is not in the checkout (true, not found).

## Other observations (all MATCH unless stated)
- Rows 1-6, 8-10: VIDEO-RUNSHEET.md lines 4, 8, 23, 30, 31, 32, 33, 35 hold the quoted sentences exactly (e.g. R:4 "real mail service and real CRM service in scenes 1 to 5 (made-up people only)"; R:23 "At 45 s the estimate is roughly 70 to 75 s: for planning the sped-up cut only, never a caption number."; R:33 "planning guess about 70 to 75 s").
- Row 2 other places: :31 "made-up person on example.test", :55 and :68 "no address except example.test", :87 header: all present. OWNER-STEPS-realrun-v3.md:107 says "(the code makes them with `example.com`, not `example.test`)": match.
- Rows 11-17: R:36 prohibition sentence, R:38 title and alert subject/text, R:50, :62, :88, :39 (second sentence), R:41 lines 2, 3, 5, 6 all present word for word (row 15 uses "..." for an elision, fine). PLAN-4 :57, :126, :194 each contain "about the lease plus 25 to 30 s".
- Rows 20-23: R:86, R:87 item (5) "the table screen shows lead keys only" and OWNER-STEPS-v3:107 "(5) the table screen: lead keys only"; R:90 caption and the K3B/K3 sentence; PAGE-STATEMENTS :150, :153 present.
- Rows 24-28: PAGE-STATEMENTS :33, :120, :134 (720 s claim window), :149, :159, :161 match.
- Rows 29-31: DOUBTFUL-SCENE :11, :12 match (subject written with <lead id>).
- Rows 32-33d: OWNER-STEPS-v3 :99, :103, :104, :95 quotes match exactly, including "the second wrong line also prints 'type exactly: end' and then the script goes ahead and archives anyway".
- Rows 34-35: n8n-owns-vs-desk-owns.md :5, :26, :29 match. Row 35 cites ":26-29": the quoted pieces are at :26 and :29.
- Rows 36-37: DECISION-one-store.md :14, :16 match (file is in flows-audit/inputs, not demo). Notes: same file :8 (CORRECTED SQLite) and :26 ("STATE vs AIM") match; N8N-START.md:4 ("SQLite inside n8n") and :41 (V5 T7b) match (file is demo/n8n-flows/N8N-START.md). The row says DECISION-one-store.md "also cites :23": line 23 does say "the decision is an AIM".
- Rows 38-40: PLAN-4 :50 (table row ends "KEEP-CODE (WP3b)"), :112, :154 match. PLAN-4 :111 (note of row 33) is the "archive_all" step: match.
- Row 79: OWNER-STEPS-v3:131 post text matches.
- Row 21 note: n8n-table-screen-v2/README.md:14 lists six columns (lead_key, state, attempts, mail_sent, alert_sent, updated_at): match.
- Row 33 note: flows-audit/ORDERS.md:82 says contacts stay for the owner to delete unless the F-01 fix lands: match (demo/ORDERS.md:82 is a different file and says something else; the row does not say which).
- Row 78: VIDEO-RUNSHEET.md has no sentence with "invalid" (grep empty): "none" holds. PAGE-STATEMENTS :33 lacks any review exception: as stated. mf-form.json:254 returns verdict 'review' (supports the note).
- Row 85: n8n-flows-real-v5 has no .sql file; run_all.sh line 43 copies n8n-flows/mf_leads.sql (which has 0 "alert" words); mf-recovery.json lines 124, 204, 228 use alert_until/alert_token/alert_attempts/alert_sent; n8n-flows-v4/mf_leads.sql lines 17-20 define all four. All match.
- Row 87: mf-recovery.json:177 and mf-sub-crm-mail.json:256-257 hold FROM_ADDRESS_PLACEHOLDER and INTAKE_ADDRESS_PLACEHOLDER; HS_CRED_PLACEHOLDER at mf-sub-crm-mail.json:103 and V5-README.md:11 (the "third placeholder" the row says it did not check is real). All match.
- Rows 7b, 86: "no sentence today" / "(none)" consistent with R:31-32 (no such sentence).

## Not checked
Claims about lane rows (A-/B- ids), RUNSHEET-WORDING.md strings and the "why" reasoning were not judged; only file:line cites and the quoted current sentences. Files cited as not in the checkout (F-01 fix file, take program) were not looked for beyond a filename search.

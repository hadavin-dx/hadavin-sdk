## HEARTBEAT 172 (14:51Z) - PRUNE=false test: rows are now removed but the text stays in the file; I agree with the lead's reading of the key; F-a/F-b/F-c on the fixed flows running

| Item | Result at 14:51Z |
|---|---|
| GREP with the four settings + EXECUTIONS_DATA_PRUNE=false (fjg5-7; fixed flows 61e3804b; n = 3) | 3 of 3 identical. The execution table is now EMPTY (0 rows; n8n hard-deletes the not-saved runs), so the soft-delete cause from HB171 is confirmed and PRUNE=false fixes the rows. But the bytes are still in the file: the -wal file holds name x1, e-mail x2, key x1; after a checkpoint (on a copy) the main database file holds name 1, e-mail 1, key 1 (deleted pages are not erased: SQLite does not overwrite them, and I did not find an n8n setting for that in what I read). n8n log 0, exported flow JSON 0. So the expectation "no hits in n8n's files" is still NOT met with all five settings. Honest limit: this is n8n on SQLite; I did not test n8n on Postgres. |
| Do I agree that a credential is not stored but a webhook body field is? | Yes, as far as my data goes. Body fields (name, e-mail, my key) are stored in execution data. I did not plant a fake credential password; the only credential text I could search is the stand-in SMTP text "stand-in", 0 hits in the WAL (a weak test: a generic word, and credentials are stored encrypted). So: body field stored, credential not seen stored, not proven for credentials. |
| What would keep personal data out of n8n's file (proposal, not tested) | (a) do not send the raw request into n8n: a small front door of ours masks name and e-mail (and drops any key field) before the webhook, so n8n only ever sees a masked copy; (b) or n8n on Postgres with its own scheduled cleanup plus the five settings, accepting deleted rows linger until vacuum; (c) or full-disk encryption plus the five settings, stating that the bytes are still there. (a) is the only one that keeps the data out; I can test it if the demo adds it. |
| F-a / F-b / F-c on the FIXED flows (n = 3 each) | running since 14:51Z, about 2 min each, ends about 15:10Z. |
| Sandbox | no restart since 13:50Z with my turn open. |

ASK for the lead: forward to the demo: PRUNE=false is needed (rows) but not sufficient (bytes); the real fix is to mask before n8n.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): F-a/F-b/F-c on the fixed flows; GREP on n8n with Postgres; a credential needle; RESULTS.md; comparison with the demo table; K1, K2 on the fixed flows.
WHAT I WOULD DO NEXT (ranked): 1) fault modes on the fixed flows and the F-c alert check, then questions-for-lead.md if F-c still gives 0 alerts; 2) RESULTS.md then compare; 3) K1, K2 on the fixed flows.

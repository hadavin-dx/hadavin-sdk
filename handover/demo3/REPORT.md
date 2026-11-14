## HEARTBEAT 170 (14:32Z) - GREP on the fixed flows WITHOUT n8n's environment settings: still in the WAL (name, e-mail, key); the same GREP WITH the four settings queued (n = 3); fault repeats running

| Item | Result at 14:32Z |
|---|---|
| GREP fjg1, fixed flows 61e3804b (same four flow files as 1ced4e1f), n = 1, n8n started with MY harness environment (none of the four settings from the demo's N8N-START.md) | Hits for fake name, e-mail AND key in n8n's database.sqlite-wal; n8n log 0; exported flow JSON 0; Postgres row: name 1, e-mail 1, key 0. So the flow files alone (saveData settings inside each workflow) do not keep the webhook body out of n8n's file; same as the 11:05Z flows (3 of 3). |
| Why this differs from the laptop result (name 3, e-mail 2, no key) | I cannot tell from here. Differences I know: (a) my harness does not set the four environment settings (EXECUTIONS_DATA_SAVE_ON_SUCCESS/ERROR=none, SAVE_ON_PROGRESS=false, SAVE_MANUAL=false) that N8N-START.md lists; the laptop run may have set them; (b) my key sits in the request body field api_key (HB164), theirs may sit elsewhere; (c) different n8n start (my runs read the WAL file right after the run, no checkpoint, no restart). To compare one thing at a time I now run the SAME needles with the four settings on (fjg2, fjg3, fjg4; runs about 100 s each; after the fault repeats, about 15:00Z). |
| Fault repeats on the 11:05Z flows | running (6 runs, F-a, F-b, F-c twice more), ends about 14:55Z. |
| Sandbox | no restart since 13:50Z with my turn open. |
| make_results.py | extended to all labels and to the flow set per row; ready to write RESULTS.md when the fault repeats and fjg2-4 are done. |

ASK for the lead: send me the exact place and size of the T7b key needle and the environment settings the laptop ran with, if you want the two runs compared line by line.
FAILURES AND RETRIES: none new.
NOT DONE / NOT CHECKED (my list, for the lead to decide): fjg2-4 (settings on); fault repeats; RESULTS.md; comparison with the demo table; K1, K2 and faults on the fixed flows (not ordered); whether a restart or checkpoint removes the WAL hits (not tested).
WHAT I WOULD DO NEXT (ranked): 1) fault repeats; 2) fjg2-4; 3) RESULTS.md then compare; 4) optional K1, K2, faults on the fixed flows.

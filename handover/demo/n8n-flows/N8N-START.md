# N8N-START (DRAFT, execution-saving part only; the rest comes with the real-node flows)

Versions the flows were built and tested against: n8n 2.46.6, Node.js 24.22.x, regular mode, SQLite inside n8n. Nothing here is a claim about other versions (n8n 2.47.7 redaction change: not checked yet).

## Execution saving: set ALL of these in n8n's environment (names read from the n8n 2.46.6 source, @n8n/config executions config)
```
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_ON_ERROR=none
EXECUTIONS_DATA_SAVE_ON_PROGRESS=false
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false
```
The flows in this folder also set saveDataSuccessExecution=none, saveDataErrorExecution=none and saveManualExecutions=false in every workflow's settings (so a workflow imported without the environment still saves nothing).

## Why (and what is NOT proven)
n8n keeps each execution's node inputs and outputs in its own database unless saving is off; anything a node handled (lead name, e-mail, a key in a header or body) is plaintext there. Credentials (HubSpot key, mail app password) are encrypted at rest by N8N_ENCRYPTION_KEY, but a copy in execution data would be plaintext.
Finding by lane3 (independent) on the 11:05Z flows: planted name, e-mail and fake key were present in n8n's SQLite write-ahead file (database.sqlite-wal) after a run. My workflow-level settings were already "none" then; the environment-level names above were NOT set in my harness. I have not yet found out WHICH table holds them (possibilities I cannot yet tell apart: the execution record that n8n writes when a run starts and deletes when it ends without saving, which stays in the write-ahead file until a checkpoint; or something else). Test T7b (mf.py) greps every file of the n8n data folder including -wal and -shm, the n8n log and the flow JSON after runs with the four variables set; the result decides. Until T7b has a result, do not state that these settings keep lead data out of n8n's files.
Rules that hold regardless: a key is never a node parameter, never in a node's output and never in a flow JSON: use n8n credentials only. The made-up lead payload may sit in the lead table and, until T7b says otherwise, in n8n's files.

# Run a second test series in parallel with V7 (H-PARAM). Built, NOT RUN (this machine has no disk and no usable docker).
Everything below is additive: with none of these variables set, behaviour and names are exactly the old ones (checked by n8n-tests/test_runcfg.py: PASS, it only compares configs, it starts nothing).
## Environment variable names (all optional; defaults in brackets)
RUN_ID [empty] -> Postgres container name n8n-publish-pg[-RUN_ID], label VALUE n8n-evidence.run=[1|RUN_ID], run_chain tag default RUN_ID. Allowed: lowercase letter first, then letters/digits, up to 12.
MF_STAGE_PORT [8770], MF_CRM_PORT [8771], DN1_DESK_PORT [8765], DN1_FAKE_PORT [8766], DN1_MODEL_PORT [48767], DN1_PROXY_PORT [8760], DN1_MAIL_PORT [8791], MF_N8N_PORT [5679], MF_N8N_BROKER_PORT [5780], MF_PG_PORT [55432], MF_RUN_PORT [8790].
Data dirs: each run already has its own --work-dir (run_chain: --work-root plus the tag); give the second run its own --out and --work-root. Cleanup (run_mf.py, end of run) removes only containers whose label value is THIS run's (docker filter label=n8n-evidence.run=<value>, exact match; the start check refuses only if a container with THIS run's label exists).
## Files changed (all additive, defaults unchanged): n8n-tests/runcfg.py (new), n8n-tests/test_runcfg.py (new), n8n-tests/dn1_common.py (5 fake ports + n8n port from runcfg), n8n-mainframe/mf.py (stage/CRM ports), n8n-mainframe/run_mf.py (PG name, label, ports, PG port mapping, KEEP_ENV), n8n-mainframe/run_chain.py (default tag). No flow and no test body changed.
## BLOCKER for a real parallel run: the harness lib.py hard-codes n8n 5679, broker 5780 and the stand-in server 8790; see LIB-PORT-PATCH.md (needs the lead's go, the rig is not mine). Until it is applied the second run can differ only in RUN_ID/label/PG name/PG port/the 5 fake ports/stage/CRM ports, and its n8n would still try port 5679 and be refused (port busy): it would NOT start while V7 runs.
## Launch recipe for the second run (after the lib patch), six lines
1. cd handover/demo/n8n-mainframe  (same commit as the first run)
2. export RUN_ID=p2 MF_N8N_PORT=15679 MF_N8N_BROKER_PORT=15780 MF_RUN_PORT=18790 MF_PG_PORT=65432
3. export MF_STAGE_PORT=18770 MF_CRM_PORT=18771 DN1_DESK_PORT=18765 DN1_FAKE_PORT=18766 DN1_MODEL_PORT=58767 DN1_PROXY_PORT=18760 DN1_MAIL_PORT=18791
4. python ../n8n-tests/test_runcfg.py   (must print PASS) ; check the ports are free
5. python run_chain.py --tests "AF2 T12 K4 K5" --reps 8 --lease 20 --out OUT-B --work-root WORK-B --node-dir NODEDIR --node-modules DIR_WITH_NPM_CI_OUTPUT   (add MF_V4 builds as in K-SERIES-V4.md)
6. Raw files land in OUT-B/<RUN_ID>-<TEST>-<time>/ exactly as for the first run.
## What the test proves and does not
test_runcfg.py proves only that the configured names and numbers are different. It does NOT prove two stacks run side by side (nobody has run that), and it does not look at lib.py.

Note 16:40Z: RUN_ID must start with a lowercase letter (runcfg refuses a digit first, e.g. 1 or 2); the laptop parallel run uses p2.

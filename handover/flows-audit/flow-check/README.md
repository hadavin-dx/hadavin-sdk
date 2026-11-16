# flow-check: read-only check of the exported n8n flow files

Nothing here starts n8n. The take uses the **real-v5** flows only (lead decision 2026-11-16): the folder `handover/demo/n8n-flows-real-v5`. The `film-v5` folder is **NOT FOR THE TAKE**; `run_all.sh` still runs it, in a separate block that never changes the exit status. Needs **Python 3.10 or newer** (the checker says so and stops with exit 3 on an older one).

Words used below: a **flow file** is one exported n8n workflow (a `.json` text file). A **step** is one box in a flow. A **web address flow** is a flow that starts when someone calls a web address (a webhook) or fills a form. A **run list** is the list of past runs that n8n shows; it is empty when saving of runs is switched off. The **take** is the filmed recording.

## Before the take: what a person must do (the script cannot)
1. **Put the right table in the database.** The take needs the table definition `handover/demo/n8n-flows-v4/mf_leads.sql` (lead decision, order Q16). The older table in `handover/demo/n8n-flows/mf_leads.sql` has no alert columns, so on it the alert steps fail on every run and no alert is ever sent. In psql, before the first send, run `select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');` It must list all four columns. No file check can see the database.
2. **Fill in every placeholder** in n8n: the mail addresses (sender and receiver) and the credential and sub-workflow ids. `take_check.sh` lists them. The checker cannot see what you type into n8n afterwards; it can only see the files.
3. **Decide the open points** below (no password on two web addresses; environment variables inside steps).
4. **Try one import into n8n.** Nothing here proves that n8n accepts these files.

## Open decisions (read first)
1. **Two web addresses have no password** (`mf-form`, `mf-hook`). Exit 0 does NOT mean a password was checked.
2. **Some steps read environment variables** (today: `AlertSend` in `mf-recovery`, `Qualify` in `mf-sub-crm-mail`; the checker prints the current list). If n8n on the filming machine blocks environment-variable access inside steps, they stop working. No file check can see that n8n setting. Add `--block-env-access` to see which steps depend on it (exit 1 expected today).
3. **Two yes/no steps lack their second branch** (`StuckRow`, `AlertRow` in `mf-recovery`). Recorded as an accepted decision with `--accept-if`, not hidden.
4. **Saving of runs is switched off in all four real-v5 files** (`saveDataSuccessExecution` and `saveDataErrorExecution` are `none`, `saveManualExecutions` is false). The run list in n8n stays empty, including for a run started with "Test workflow". The checker warns for every flow file and `take_check.sh` prints the three settings per file. The patch F-008 switches saving on for the two web address flows and the sub-workflow, but not for manual runs and not for the recovery flow. The two patches F-002 (checks that a lead key is well formed, answers a bad key, answers when the table write fails) and F-008 (saving of runs) are **not** in the committed real-v5 files; `take_check.sh` says per file whether the key check is present.

## Commands (from this folder)
- **The take check:** `bash take_check.sh`. It prints a top block first (the table check with counts, saving of runs per file, placeholders, the key check per file, open decisions, environment variables), then the full checker output, then one last line (`FINAL: ...`) that cannot be mistaken for a pass: *exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: N*. It runs `python3 -I check_flows.py demo/n8n-flows-real-v5 --ddl demo/n8n-flows-v4/mf_leads.sql --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token --quiet-info`. If the table file is missing it leaves out `--ddl`, says so loudly and exits 4. It looks for the table file at that one path only.
- **Everything at once:** `bash run_all.sh` (patches applied to a scratch copy, 9 checker runs, the take script and its three failure cases, the self-test). Its exit status and last line are about real-v5 only. Add `--strict` to make unreplaced credential ids a failure. It can exit 0 once the files are fixed and filled: the take script lines about placeholders, credential ids and environment variables are required only while the checker still reports them.
- **Self-test only:** `python3 -I selftest.py ../../demo/n8n-flows-real-v5 <patched real folder> ../../demo/n8n-flows-film-v5` (the last two arguments are optional). It does not run `take_check.sh`; `run_all.sh` does.

## What the exit codes mean

| Exit of `check_flows.py` | Meaning |
|---|---|
| 0 | No FAIL line. It does NOT mean the flows are ready, safe to import, or that a password is set on the web addresses. Read the closing block. |
| 1 | At least one FAIL line: a definite fault in a file (or an open decision you turned into a fault with an option below). |
| 2 | Wrong command line: unknown option, missing value, unknown patch name, bad `--expect`, `--expect-credential`, `--accept-if` or `--expect-json` value, a `--ddl` file that cannot be read (missing, or not valid UTF-8 text) or that holds no `CREATE TABLE`. |
| 3 | The checker itself broke, or could not write its `--diff-out` file. Never a verdict about the flows. |

`take_check.sh` uses the same 0 to 3 and adds **4**: the checker found no FAIL, but the table check did not happen or found a mismatch (table file missing, 0 query strings read, a column or table the file does not define, or a database step with no query text).

Line types: `FAIL` = fault. `WARN` = read it, exit stays 0. `WARN-LEAD-DECISION` = a decision for the lead or owner (no password on a web address, steps that read the environment); exit stays 0 on purpose.

## Options (what each really does)
- `--ddl FILE`: reads the `CREATE TABLE` definitions in FILE and compares **names** only. For each database step it reads the text of the `query` setting, takes the table names after `from`, `update`, `into`, `join` and the other plain words, and warns for a table or column the FILE does not define. It is a **WARN** (exit 0), and `take_check.sh` turns a column or table WARN into exit 4. What it does NOT do: it does not run SQL; it ignores words inside `{{ }}` and inside quotes, words directly before a `(`, and SQL words and type names it knows; it reads only `CREATE TABLE` (a column added later by `ALTER TABLE` looks missing); a table alias or an SQL word it does not know can give a false WARN; steps in table or column mode (no `query` text) are not compared and are counted and warned. It prints how many query strings it read; **0 read is said loudly** (`SQL COLUMNS NOT CHECKED`). Without `--ddl` it warns `no --ddl file was given`.
- `--accept-if FILE=NODE:OUT[,OUT]` (repeatable): records one decision: this yes/no step of this file is accepted to lack exactly these outputs. `OUT` is 0 or 1 (in n8n, 0 is the "yes" output and 1 the "no" output; that is from memory of n8n). More than one OUT may be given with commas, for example `mf-recovery.json=StuckRow:0,1`. It is a WARN, counted as a known open problem and listed in the closing block. Any other missing branch is a FAIL. It applies to every folder of the same run. An `--accept-if` that matches nothing is itself a WARN (`matched nothing`).
- `--baseline DIR`: a yes/no step that already lacks the same branch in DIR is only a WARN (and is not counted as a known open problem). If you point it at the folder you are checking, it excuses every missing branch there; do not do that. The take command does not use it.
- `--quiet-info`: hides the type table and the per-file line about placeholder words and environment variables. It does NOT hide the credential list per file, any WARN or FAIL, or the closing block (placeholders, credential ids, environment steps, SQL counts, open problems).
- `--require-webhook-auth`, `--block-env-access`, `--require-real-credential-ids`: each turns an open decision into a FAIL. `--require-real-credential-ids` also fails a placeholder in a node setting such as a mail address, not only credential ids.
- `--fail-unverified`: turns every rule tagged `n8n rule UNVERIFIED` into a FAIL. The rules are: the allowed webhook `authentication` values (webhook: none, basicAuth, headerAuth, jwtAuth; form trigger: none, basicAuth); the credential kind each needs; the credential kinds of postgres, smtp and hubspot steps; the position of the error output and "cannot tell which output is the error output"; the default `responseMode` and a webhook with none set; a webhook or form with no usable path; two webhooks with the same method and path or the same `webhookId` (compared across all folders of one run); the `onError` value list; the retry limits (`maxTries`, `waitBetweenTries`). The take check does NOT pass it, so these stay WARN there.

## The closing block of the checker (always printed, also with `--quiet-info`)
Open decisions count, accepted IF branches, placeholders in node settings, credential and sub-workflow ids that are still placeholders, steps that read environment variables, the SQL counts (`SQL columns compared ...`, `SQL WARNS: column WARNs=.. table WARNs=..`), the list of known open problems, and what is not proven.

What the placeholder scan can and cannot see: it looks at every node setting and at credential and sub-workflow ids, for these words: `PLACEHOLDER`, `PG_CREDENTIAL_ID`, `SMTP_CREDENTIAL_ID`, `SUB_WORKFLOW_ID`, `HS_CRED`, `HUBSPOT_CREDENTIAL_ID`, `CHANGE_ME`, `CHANGEME`, `REPLACE_ME`, `TODO`; and it flags a mail setting (`fromEmail`, `toEmail`, `ccEmail`, `bccEmail`, `replyTo`) that is not shaped like one address. A wrong but well-formed address, or a different placeholder word, passes. Anything you change inside n8n after import is invisible to it.

## Not known (said first)
- n8n was never started; import of these files is untested.
- Whether n8n blocks environment-variable access inside steps on the filming machine (and the name of that setting is itself from memory).
- Every rule tagged `n8n rule UNVERIFIED` above.
- Who calls a web address, whether a flow is active, test versus production web address.
- Whether the real database holds the v4 table (the psql step above).
- Python 3.10 itself was not run here (the version check is tested by a stand-in).

Details, numbers and raw outputs: `REPORT.md`, `raw/`. Latest fix log: `fix-f8-r6.md`.

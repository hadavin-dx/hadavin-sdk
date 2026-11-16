# evidence-r4 (EVIDENCE RUNNER, raw, no judgement). Run on a copy; scratch removed after.
## 1 run_all.sh rc=0 (6.6 s); take_check.sh rc=0
```
Known open problems: 4
exit=1
[patched-strict-film]
######## patched-strict film
RESULT: 4 FAIL, 16 WARN
Known open problems: 6
exit=1
[selftest exit=0] SELFTEST: 577 as expected, 0 not as expected, 58 skipped (not applicable)
run_all exit status (real-v5 default runs + self-test): 0
real-v5 placeholder ids: 4 file(s) warn in the committed flows (pass --strict to make that a failure)
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

real	0m6.566s
user	0m4.882s
sys	0m1.183s
```
```
  - /handover/flows-audit/flow-check/../../demo/n8n-flows-real-v5/mf-sub-crm-mail.json: node Qualify reads $env.DESK_TIMEOUT_MS, $env.DESK_URL; if the take blocks environment-variable access inside nodes (n8n setting, 
Not proven: that n8n accepts these files on import; what n8n really does when a step fails (F-002, tests T19 and T20); the SQL inside the postgres nodes; who calls a web address, whether the flow is active, and test versus production web address; expression syntax beyond node names; secrets in a sha
Passing this check does NOT mean the flows are ready to film.
take_check exit status: 0
```
## 2 selftest alone rc=0: SELFTEST: 577 as expected, 0 not as expected, 58 skipped; python3.11/3.12/3.13 identical; python3.10 not installed (not tested)
## 3 lint: repo config (/home/user/hadavin-sdk, line-length 100): ruff check rc=0, ruff format --check rc=0, bandit -ll rc=0 (1 Low, 0 Medium/High). On the COPY without pyproject: ruff format --check rc=1 (default line length 88) - config artefact only
## 4 grep noqa|nosec|type: ignore|pragma over 4 files: no matches
## 5 mutants (seed 20261116): 25 run, 5 syntax-error skipped, 13 killed, 12 survived
```
done 25 killed 13 survivors 12 syntax-skipped 5
SURV (117, '.append(', '.extend(', 'FAILS.append(f"{where}: {msg}")')
SURV (48, 'NUM', 13, 'sys.exit(3)')
SURV (418, ' in ', ' not in ', '"""Every path from a responseNode webhook must end in respondToWebhook. Walk is stopped at respond nodes."""')
SURV (1189, '.append(', '.extend(', 'out.append(f"== {tag} ==")')
SURV (33, 'NUM', 67, 'F-002 Claim is printed with a WARN (UNPROVEN until test T19): exit 0 does NOT clear F-002. A node with alwaysOutputData AND onError=continue')
SURV (62, ' in ', ' not in ', '}  # open lead decisions seen in this run (printed in the closing block)')
SURV (567, 'NUM', 54, 'f"node {nm} maxTries={mt!r} (2 to 5 is the n8n screen limit, not a proven import rule; {UNV})",')
SURV (317, 'NUM', 59, '("Slack token", re.compile(r"\\bxox[abprs]-[A-Za-z0-9-]{10,}")),')
SURV (1045, ' or ', ' and ', 'if all(isinstance(x, dict) and "name" in x for x in a + b) and (a or b):')
SURV (1, ' in ', ' not in ', '"""Read-only structural check of generated n8n flow JSON files. Nothing is run in n8n. Standard library only.')
SURV (353, 'NUM', 41, 'for b in blocks:  # a quoted text of 6+ characters inside the expression (other than a node or variable name in $(\'..\') or [".."]) is a lite')
SURV (502, ' or ', ' and ', 'or not c.get("type")')
```
Survivors on docstring/comment/message text (equivalent): lines 1, 33, 62, 353, 418, 567. Survivors on code: 48 (sys.exit(3) to 4, python<3.10 branch, unreachable on 3.11+), 117 (fail(): FAILS.append->extend), 317 (Slack token regex {10,} to {11,}), 502 (or not c.get(type) to and), 1045 (deep_diff: or to and), 1189 (diff header append->extend).
## 7 hostile inputs (each folder has only mf-form.json so missing-file FAILs are expected; rc=1 each, 0 tracebacks): empty file: FAIL parse failure JSONDecodeError; invalid JSON: same; 5.3 MB file with a 5.3M-char node name: FAILs, no crash; node with no name: FAIL node at index 0 lacks a text name or type; connection to missing node: FAIL dangling target 'Ghost'; same webhook method+path in two folders: WARN two webhooks share method+path (n8n rule UNVERIFIED), no traceback; nonexistent folder rc=1, no traceback.

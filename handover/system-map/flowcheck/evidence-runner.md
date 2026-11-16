# Evidence runner output (raw, no judgement)

Date: 2026-11-16T08:36:53Z. Branch: cloud/system-map @ d87f6f0b.
git status --short before: empty. After (before this file was written): empty.

## 1. bash handover/system-map/flowcheck/run_all.sh /tmp/fc-ev1
```
patching file handover/demo/n8n-mainframe/build_mainframe.py
patching file handover/demo/n8n-mainframe/build_mainframe.py
done
exit=0
```
### /tmp/fc-ev1/dry-run.txt
```
== F-001-one-ddl
checking file handover/demo/n8n-flows/mf_leads.sql
rc=0
== F-002-take-key-check-and-claim-error-path
checking file handover/demo/n8n-mainframe/build_mainframe.py
rc=0
== F-003-runsheet-claims
checking file handover/demo/VIDEO-RUNSHEET.md
rc=0
== F-004-page-statement-17
checking file handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
rc=0
== F-008-save-runs-for-the-take
checking file handover/demo/n8n-mainframe/build_mainframe.py
rc=0
patching file handover/demo/n8n-mainframe/build_mainframe.py
patching file handover/demo/n8n-mainframe/build_mainframe.py
Hunk #2 succeeded at 121 (offset 4 lines).
patching file handover/demo/n8n-mainframe/build_mainframe.py
patching file handover/demo/n8n-mainframe/build_mainframe.py
Hunk #1 succeeded at 79 (offset 3 lines).
Hunk #2 succeeded at 97 (offset 3 lines).
order F-002,F-008 and F-008,F-002 give the same file
```
### /tmp/fc-ev1/build.txt
```
pristine real-v5 rc=0
pristine film-v5 rc=0
f002 real-v5 rc=0
f002 film-v5 rc=0
f008 real-v5 rc=0
f008 film-v5 rc=0
both real-v5 rc=0
both film-v5 rc=0
pristine real-v5 flowcheck rc=1
pristine film-v5 flowcheck rc=1
f002 real-v5 flowcheck rc=1
f002 film-v5 flowcheck rc=1
f008 real-v5 flowcheck rc=1
f008 film-v5 flowcheck rc=1
both real-v5 flowcheck rc=1
both film-v5 flowcheck rc=1
```
### /tmp/fc-ev1/repro.txt
```
real-v5: rebuilt from the pristine generator is byte-identical to the committed folder
film-v5: rebuilt from the pristine generator is byte-identical to the committed folder
```
### /tmp/fc-ev1/selftest.txt
```
selftest ok
selftest rc=0
```
### /tmp/fc-ev1/changed-files.txt
```
== f002 vs pristine real-v5
Files built/pristine/real-v5/mf-form.json and built/f002/real-v5/mf-form.json differ
Files built/pristine/real-v5/mf-hook.json and built/f002/real-v5/mf-hook.json differ
== f002 vs pristine film-v5
Files built/pristine/film-v5/mf-form.json and built/f002/film-v5/mf-form.json differ
Files built/pristine/film-v5/mf-hook.json and built/f002/film-v5/mf-hook.json differ
== f008 vs pristine real-v5
Files built/pristine/real-v5/mf-form.json and built/f008/real-v5/mf-form.json differ
Files built/pristine/real-v5/mf-hook.json and built/f008/real-v5/mf-hook.json differ
Files built/pristine/real-v5/mf-sub-crm-mail.json and built/f008/real-v5/mf-sub-crm-mail.json differ
== f008 vs pristine film-v5
Files built/pristine/film-v5/mf-form.json and built/f008/film-v5/mf-form.json differ
Files built/pristine/film-v5/mf-hook.json and built/f008/film-v5/mf-hook.json differ
Files built/pristine/film-v5/mf-sub-crm-mail.json and built/f008/film-v5/mf-sub-crm-mail.json differ
== both vs pristine real-v5
Files built/pristine/real-v5/mf-form.json and built/both/real-v5/mf-form.json differ
Files built/pristine/real-v5/mf-hook.json and built/both/real-v5/mf-hook.json differ
Files built/pristine/real-v5/mf-sub-crm-mail.json and built/both/real-v5/mf-sub-crm-mail.json differ
== both vs pristine film-v5
Files built/pristine/film-v5/mf-form.json and built/both/film-v5/mf-form.json differ
Files built/pristine/film-v5/mf-hook.json and built/both/film-v5/mf-hook.json differ
Files built/pristine/film-v5/mf-sub-crm-mail.json and built/both/film-v5/mf-sub-crm-mail.json differ
```
## 2. Diff against builder copies (empty = identical)
### diff -r /tmp/fc-ev1/md handover/system-map/flowcheck/evidence/md
```
rc=0
```
### diff /tmp/fc-ev1/build.txt handover/system-map/flowcheck/evidence/build.txt
```
rc=0
```
### diff /tmp/fc-ev1/changed-files.txt handover/system-map/flowcheck/evidence/changed-files.txt
```
rc=0
```
### diff /tmp/fc-ev1/dry-run.txt handover/system-map/flowcheck/evidence/dry-run.txt
```
rc=0
```
### diff /tmp/fc-ev1/repro.txt handover/system-map/flowcheck/evidence/repro.txt
```
rc=0
```
### diff /tmp/fc-ev1/selftest.txt handover/system-map/flowcheck/evidence/selftest.txt
```
rc=0
```
## 3. Hostile inputs (files in /tmp/fc-ev1/hostile/)
### a.json
```
$ cat a.json
this is not json {
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/a.json
### /tmp/fc-ev1/hostile/a.json
- FAIL: does not parse: Expecting value: line 1 column 1 (char 0)

exit=1
```
### b.json
```
$ cat b.json
{}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/b.json
Traceback (most recent call last):
  File "/home/user/hadavin-sdk/handover/system-map/flowcheck/tools/flowcheck.py", line 120, in <module>
    R = check(w); print(md(p, w, R)); bad += bool(R["fail"])
                        ~~^^^^^^^^^
  File "/home/user/hadavin-sdk/handover/system-map/flowcheck/tools/flowcheck.py", line 95, in md
    o = ["### %s" % path, "- nodes: %d; connections: %d; triggers: %s" % (len(w.get("nodes", [])), sum(len(l or []) for o_ in w.get("connections", {}).values() for lst in o_.values() for l in lst), ", ".join(n["name"] for n in w["nodes"] if TRIG.search(n["type"])))]
                                                                                                                                                                                                                                   ~^^^^^^^^^
KeyError: 'nodes'
exit=1
```
### c.json
```
$ cat c.json
{"nodes":[{"name":"Hook","parameters":{}}],"connections":{}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/c.json
Traceback (most recent call last):
  File "/home/user/hadavin-sdk/handover/system-map/flowcheck/tools/flowcheck.py", line 120, in <module>
    R = check(w); print(md(p, w, R)); bad += bool(R["fail"])
  File "/home/user/hadavin-sdk/handover/system-map/flowcheck/tools/flowcheck.py", line 42, in check
    trig = [n["name"] for n in nodes if TRIG.search(n["type"])]
                                                    ~^^^^^^^^
KeyError: 'type'
exit=1
```
### d.json
```
$ cat d.json
{"nodes":[{"name":"Hook","type":"n8n-nodes-base.webhook","parameters":{"httpMethod":"POST","path":"x","authentication":"headerAuth"}}],"connections":{"Hook":{"main":[[{"node":"Missing","type":"main","index":0}]]}}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/d.json
### /tmp/fc-ev1/hostile/d.json
- nodes: 1; connections: 1; triggers: Hook
- FAIL: connection Hook[0] targets missing node: Missing
- save settings: saveDataSuccessExecution=None, saveDataErrorExecution=None, saveManualExecutions=None, executionOrder=None, errorWorkflow=None
- webhooks: Hook POST /x auth=headerAuth
- $env reads: none
- credentials: none

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Hook | webhook | (default: stop) | no | no | - |

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

exit=1
```
### e.json
```
$ cat e.json
{"nodes":[{"name":"Hook","type":"n8n-nodes-base.webhook","parameters":{"httpMethod":"POST","path":"x","authentication":"headerAuth"}},{"name":"S","type":"n8n-nodes-base.set","parameters":{}},{"name":"S","type":"n8n-nodes-base.set","parameters":{}}],"connections":{"Hook":{"main":[[{"node":"S","type":"main","index":0}]]}}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/e.json
### /tmp/fc-ev1/hostile/e.json
- nodes: 3; connections: 1; triggers: Hook
- FAIL: duplicate node names: S
- save settings: saveDataSuccessExecution=None, saveDataErrorExecution=None, saveManualExecutions=None, executionOrder=None, errorWorkflow=None
- webhooks: Hook POST /x auth=headerAuth
- $env reads: none
- credentials: none

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Hook | webhook | (default: stop) | no | no | - |
| S | set | (default: stop) | no | no | - |
| S | set | (default: stop) | no | no | - |

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

exit=1
```
### f.json
```
$ cat f.json
{"nodes":[{"name":"Hook","type":"n8n-nodes-base.webhook","parameters":{"httpMethod":"POST","path":"x","authentication":"headerAuth"}},{"name":"S","type":"n8n-nodes-base.set","parameters":{"v":"={{ $('Ghost').item.json.a }}"}}],"connections":{"Hook":{"main":[[{"node":"S","type":"main","index":0}]]}}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/f.json
### /tmp/fc-ev1/hostile/f.json
- nodes: 2; connections: 1; triggers: Hook
- FAIL: $('Name') names no node: S -> $('Ghost')
- save settings: saveDataSuccessExecution=None, saveDataErrorExecution=None, saveManualExecutions=None, executionOrder=None, errorWorkflow=None
- webhooks: Hook POST /x auth=headerAuth
- $env reads: none
- credentials: none

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Hook | webhook | (default: stop) | no | no | - |
| S | set | (default: stop) | no | no | - |

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

exit=1
```
### g.json
```
$ cat g.json
{"nodes":[{"name":"Hook","type":"n8n-nodes-base.webhook","parameters":{"httpMethod":"POST","path":"x","authentication":"headerAuth"}},{"name":"PG","type":"n8n-nodes-base.postgres","parameters":{"query":"select 1"},"alwaysOutputData":true,"onError":"continueErrorOutput"}],"connections":{"Hook":{"main":[[{"node":"PG","type":"main","index":0}]]}}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/g.json
### /tmp/fc-ev1/hostile/g.json
- nodes: 2; connections: 1; triggers: Hook
- FAIL: PG: alwaysOutputData together with continueErrorOutput (F-002 pattern) | PG: continueErrorOutput but output 1 (error) is not wired
- save settings: saveDataSuccessExecution=None, saveDataErrorExecution=None, saveManualExecutions=None, executionOrder=None, errorWorkflow=None
- webhooks: Hook POST /x auth=headerAuth
- $env reads: none
- credentials: none

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Hook | webhook | (default: stop) | no | no | - |
| PG | postgres | continueErrorOutput | no | yes | alwaysOutputData+continueErrorOutput; error output not wired |

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

exit=1
```
### h.json
```
$ cat h.json
{"nodes":[{"name":"Hook","type":"n8n-nodes-base.webhook","parameters":{"httpMethod":"POST","path":"x","authentication":"headerAuth"}},{"name":"S","type":"n8n-nodes-base.set","parameters":{}}],"connections":{"Hook":{"main":[[{"node":"S","type":"main","index":0}]]}}}
$ python3 -I handover/system-map/flowcheck/tools/flowcheck.py /tmp/fc-ev1/hostile/h.json
### /tmp/fc-ev1/hostile/h.json
- nodes: 2; connections: 1; triggers: Hook
- FAIL: none
- save settings: saveDataSuccessExecution=None, saveDataErrorExecution=None, saveManualExecutions=None, executionOrder=None, errorWorkflow=None
- webhooks: Hook POST /x auth=headerAuth
- $env reads: none
- credentials: none

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Hook | webhook | (default: stop) | no | no | - |
| S | set | (default: stop) | no | no | - |

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

exit=0
```
## 4. Mutation check (copies in /tmp/fc-ev1/mut/, original untouched)
Mutations: a = 'if dup:' -> 'if False and dup:'; b = missing-target check prefixed 'False and'; c = $('Name') check prefixed 'False and'; d = alwaysOutputData+continueErrorOutput check prefixed 'False and'.
### mutant a
```
$ python3 -I /tmp/fc-ev1/mut/flowcheck_a.py --selftest
  File "/tmp/fc-ev1/mut/flowcheck_a.py", line 110, in selftest
    for k in ("duplicate node names: A", "targets missing node: Nope", "orphan nodes", "Ghost", "alwaysOutputData together", "error) is not wired", "webhook without authentication"): assert k in t, (k, t)
                                                                                                                                                                                              ^^^^^^
AssertionError: ('duplicate node names: A', "connection T[0] targets missing node: Nope | orphan nodes (no way in, not a trigger): O | $('Name') names no node: A -> $('Ghost') | T: webhook without authentication | A: alwaysOutputData together with continueErrorOutput (F-002 pattern) | A: continueErrorOutput but output 1 (error) is not wired")
exit=1
```
### mutant b
```
$ python3 -I /tmp/fc-ev1/mut/flowcheck_b.py --selftest
  File "/tmp/fc-ev1/mut/flowcheck_b.py", line 110, in selftest
    for k in ("duplicate node names: A", "targets missing node: Nope", "orphan nodes", "Ghost", "alwaysOutputData together", "error) is not wired", "webhook without authentication"): assert k in t, (k, t)
                                                                                                                                                                                              ^^^^^^
AssertionError: ('targets missing node: Nope', "duplicate node names: A | orphan nodes (no way in, not a trigger): O | $('Name') names no node: A -> $('Ghost') | T: webhook without authentication | A: alwaysOutputData together with continueErrorOutput (F-002 pattern) | A: continueErrorOutput but output 1 (error) is not wired")
exit=1
```
### mutant c
```
$ python3 -I /tmp/fc-ev1/mut/flowcheck_c.py --selftest
  File "/tmp/fc-ev1/mut/flowcheck_c.py", line 110, in selftest
    for k in ("duplicate node names: A", "targets missing node: Nope", "orphan nodes", "Ghost", "alwaysOutputData together", "error) is not wired", "webhook without authentication"): assert k in t, (k, t)
                                                                                                                                                                                              ^^^^^^
AssertionError: ('Ghost', 'duplicate node names: A | connection T[0] targets missing node: Nope | orphan nodes (no way in, not a trigger): O | T: webhook without authentication | A: alwaysOutputData together with continueErrorOutput (F-002 pattern) | A: continueErrorOutput but output 1 (error) is not wired')
exit=1
```
### mutant d
```
$ python3 -I /tmp/fc-ev1/mut/flowcheck_d.py --selftest
  File "/tmp/fc-ev1/mut/flowcheck_d.py", line 110, in selftest
    for k in ("duplicate node names: A", "targets missing node: Nope", "orphan nodes", "Ghost", "alwaysOutputData together", "error) is not wired", "webhook without authentication"): assert k in t, (k, t)
                                                                                                                                                                                              ^^^^^^
AssertionError: ('alwaysOutputData together', "duplicate node names: A | connection T[0] targets missing node: Nope | orphan nodes (no way in, not a trigger): O | $('Name') names no node: A -> $('Ghost') | T: webhook without authentication | A: continueErrorOutput but output 1 (error) is not wired")
exit=1
```
Surviving mutants (self-test still passed): none of 4 (all 4 self-tests failed with AssertionError = mutant killed).
## 5. git status --short
```
?? handover/system-map/flowcheck/evidence-runner.md
```

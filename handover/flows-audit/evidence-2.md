EVIDENCE RUNNER output (round 2), Mon Nov 16 07:26:22 UTC 2026, BASE 3bf5ae299cebac78963780895af5c585cab8473c, head e9f18c808cf5bd574768e183d2042633d8b6f267

## (0)

Command: `date -u; git rev-parse HEAD; git status --porcelain`
Exit code: 0

```
Mon Nov 16 07:26:22 UTC 2026
e9f18c808cf5bd574768e183d2042633d8b6f267
?? handover/flows-audit/evidence-2.md
?? handover/flows-audit/tools/scratch/
```

## (a)

Command: `python3 handover/flows-audit/tools/check_counts.py`
Exit code: 0

```
PASS 52 files / 655 nodes
```

## (b)

Command: `python3 handover/flows-audit/tools/check_names.py`
Exit code: 0

```
PASS 655 rows
```

## (c)

Command: `python3 handover/flows-audit/tools/check_refs.py`
Exit code: 0

```
PASS 5105 references
```

## (d1)

Command: `sh handover/flows-audit/tools/check_patches.sh`
Exit code: 0

```
PASS 4 patches
```

## (d2)

Command: `git apply --check handover/flows-audit/patches/F-001-one-ddl.patch; echo $?`
Exit code: 0

```
0
```

## (d2)

Command: `git apply --check handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch; echo $?`
Exit code: 0

```
0
```

## (d2)

Command: `git apply --check handover/flows-audit/patches/F-003-runsheet-claims.patch; echo $?`
Exit code: 0

```
0
```

## (d2)

Command: `git apply --check handover/flows-audit/patches/F-004-page-statement-17.patch; echo $?`
Exit code: 0

```
0
```

## (e)

Command: `python3 handover/flows-audit/tools/check_secrets.py`
Exit code: 0

```
PASS 0 hits in 169 files
```

## (f1)

Command: `git status --porcelain`
Exit code: 0

```
?? handover/flows-audit/evidence-2.md
?? handover/flows-audit/tools/scratch/
```

## (f2)

Command: `git diff --stat 3bf5ae299cebac78963780895af5c585cab8473c HEAD -- . ':!handover/flows-audit'`
Exit code: 0

```
(empty)
```

## (g)

Command: `python3 handover/flows-audit/tools/test_dump_nodes.py`
Exit code: 0

```
PASS 8/8
```

## (h)

Command: `python3 handover/flows-audit/tools/dump_nodes.py counts handover/demo | tail -3`
Exit code: 0

```
4 n8n-table-screen-v2/mf-table-screen-v2.json
4 n8n-table-screen/mf-table-screen.json
TOTAL nodes 655
```

## (i)

Command: `for f in handover/demo/n8n-*/**/*.json (not n8n-tests): dump_nodes.py check <f>`
Exit code: 0

```
files checked: 52; failures: 0
```

## (j)

Command: `python (count rows, lane ids vs sources)`
Exit code: 0

```
FINDINGS.md rows (^| F-): 34
handover/flows-audit/lanes/L1.findings.md: 23
handover/flows-audit/lanes/L2a.findings.md: 17
handover/flows-audit/lanes/L2b-1-real.findings.md: 10
handover/flows-audit/lanes/L2b-2-film.findings.md: 9
handover/flows-audit/lanes/L2b-3-plain.findings.md: 17
handover/flows-audit/lanes/L3.findings.md: 22
lane findings rows total: 98
lane ids not in FINDINGS.md sources column: none
```

## (k)

Command: `python (sum counts.txt per folder) + grep claims`
Exit code: 0

```
counts.txt lines (files): 53
counts.txt folders: 13
counts.txt total nodes: 655
  n8n-flows: 122
  n8n-flows-film: 51
  n8n-flows-film-v3: 52
  n8n-flows-film-v4: 53
  n8n-flows-film-v5: 54
  n8n-flows-real: 51
  n8n-flows-real-v3: 52
  n8n-flows-real-v4: 53
  n8n-flows-real-v5: 54
  n8n-flows-v3: 52
  n8n-flows-v4: 53
  n8n-table-screen: 4
  n8n-table-screen-v2: 4
FINDINGS.md matching claims:
7:40 files in 11 older folders hold 525 of the 655 steps, so about fou
59:525 of 655 nodes.** The lane LIVE-REFERENCE tests found hits fo
```

## (m)

Command: `F-002 rebuild in scratch (patch -p1, build patched/unpatched real-v5/film-v5, compare)`
Exit code: 0

```
patch -p1 exit 0
patching file handover/demo/n8n-mainframe/build_mainframe.py

$ MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 handover/flows-audit/tools/scratch/rb2/patched/handover/demo/n8n-mainframe/build_mainframe.py handover/flows-audit/tools/scratch/rb2/out-patched-real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit 0
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json

files: ['mf-form.json', 'mf-hook.json', 'mf-recovery.json', 'mf-sub-crm-mail.json']
$ MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 handover/flows-audit/tools/scratch/rb2/patched/handover/demo/n8n-mainframe/build_mainframe.py handover/flows-audit/tools/scratch/rb2/out-patched-film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit 0
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json

files: ['mf-form.json', 'mf-hook.json', 'mf-recovery.json', 'mf-sub-crm-mail.json']
$ MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 handover/flows-audit/tools/scratch/rb2/unpatched/handover/demo/n8n-mainframe/build_mainframe.py handover/flows-audit/tools/scratch/rb2/out-unpatched-real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER
exit 0
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json

files: ['mf-form.json', 'mf-hook.json', 'mf-recovery.json', 'mf-sub-crm-mail.json']
$ MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 handover/flows-audit/tools/scratch/rb2/unpatched/handover/demo/n8n-mainframe/build_mainframe.py handover/flows-audit/tools/scratch/rb2/out-unpatched-film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45
exit 0
wrote mf-sub-crm-mail.json
wrote mf-form.json
wrote mf-hook.json
wrote mf-recovery.json

files: ['mf-form.json', 'mf-hook.json', 'mf-recovery.json', 'mf-sub-crm-mail.json']
--- real mf-form: patched files ['mf-form.json'], unpatched files ['mf-form.json']
mf-form.json: patched nodes 15, unpatched nodes 12
  added: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
  removed: []
  params changed: ['Valid']
  dangling patched: []
  dangling unpatched: []
--- real mf-hook: patched files ['mf-hook.json'], unpatched files ['mf-hook.json']
mf-hook.json: patched nodes 15, unpatched nodes 12
  added: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
  removed: []
  params changed: ['Valid']
  dangling patched: []
  dangling unpatched: []
--- real mf-recovery: patched files ['mf-recovery.json'], unpatched files ['mf-recovery.json']
mf-recovery.json: patched nodes 10, unpatched nodes 10
  added: []
  removed: []
  params changed: []
  dangling patched: []
  dangling unpatched: []
--- real mf-sub-crm-mail: patched files ['mf-sub-crm-mail.json'], unpatched files ['mf-sub-crm-mail.json']
mf-sub-crm-mail.json: patched nodes 20, unpatched nodes 20
  added: []
  removed: []
  params changed: []
  dangling patched: []
  dangling unpatched: []
--- unpatched real vs saved handover/demo/n8n-flows-real-v5 mf-form: gen ['mf-form.json'] saved ['mf-form.json']
  gen nodes 12, saved nodes 12; only in gen []; only in saved []
--- unpatched real vs saved handover/demo/n8n-flows-real-v5 mf-hook: gen ['mf-hook.json'] saved ['mf-hook.json']
  gen nodes 12, saved nodes 12; only in gen []; only in saved []
--- unpatched real vs saved handover/demo/n8n-flows-real-v5 mf-recovery: gen ['mf-recovery.json'] saved ['mf-recovery.json']
  gen nodes 10, saved nodes 10; only in gen []; only in saved []
--- unpatched real vs saved handover/demo/n8n-flows-real-v5 mf-sub-crm-mail: gen ['mf-sub-crm-mail.json'] saved ['mf-sub-crm-mail.json']
  gen nodes 20, saved nodes 20; only in gen []; only in saved []
--- film mf-form: patched files ['mf-form.json'], unpatched files ['mf-form.json']
mf-form.json: patched nodes 15, unpatched nodes 12
  added: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
  removed: []
  params changed: ['Valid']
  dangling patched: []
  dangling unpatched: []
--- film mf-hook: patched files ['mf-hook.json'], unpatched files ['mf-hook.json']
mf-hook.json: patched nodes 15, unpatched nodes 12
  added: ['KeyOk', 'ReplyBadKey', 'ReplyStoreFail']
  removed: []
  params changed: ['Valid']
  dangling patched: []
  dangling unpatched: []
--- film mf-recovery: patched files ['mf-recovery.json'], unpatched files ['mf-recovery.json']
mf-recovery.json: patched nodes 10, unpatched nodes 10
  added: []
  removed: []
  params changed: []
  dangling patched: []
  dangling unpatched: []
--- film mf-sub-crm-mail: patched files ['mf-sub-crm-mail.json'], unpatched files ['mf-sub-crm-mail.json']
mf-sub-crm-mail.json: patched nodes 20, unpatched nodes 20
  added: []
  removed: []
  params changed: []
  dangling patched: []
  dangling unpatched: []
--- unpatched film vs saved handover/demo/n8n-flows-film-v5 mf-form: gen ['mf-form.json'] saved ['mf-form.json']
  gen nodes 12, saved nodes 12; only in gen []; only in saved []
--- unpatched film vs saved handover/demo/n8n-flows-film-v5 mf-hook: gen ['mf-hook.json'] saved ['mf-hook.json']
  gen nodes 12, saved nodes 12; only in gen []; only in saved []
--- unpatched film vs saved handover/demo/n8n-flows-film-v5 mf-recovery: gen ['mf-recovery.json'] saved ['mf-recovery.json']
  gen nodes 10, saved nodes 10; only in gen []; only in saved []
--- unpatched film vs saved handover/demo/n8n-flows-film-v5 mf-sub-crm-mail: gen ['mf-sub-crm-mail.json'] saved ['mf-sub-crm-mail.json']
  gen nodes 20, saved nodes 20; only in gen []; only in saved []
```

## (n)

Command: `cmp pairs + grep counts`
Exit code: 0

```
cmp handover/demo/n8n-flows/mf_leads.sql handover/demo/n8n-flows-v3/mf_leads.sql: handover/demo/n8n-flows/mf_leads.sql handover/demo/n8n-flows-v3/mf_leads.sql differ: char 8, line 1
1
cmp handover/demo/n8n-flows/mf_leads.sql handover/demo/n8n-flows-v4/mf_leads.sql: handover/demo/n8n-flows/mf_leads.sql handover/demo/n8n-flows-v4/mf_leads.sql differ: char 8, line 1
1
cmp handover/demo/n8n-flows-v3/mf_leads.sql handover/demo/n8n-flows-v4/mf_leads.sql: 0
grep -c handover/demo/n8n-flows/mf_leads.sql: rc=1 count=0

grep -c handover/demo/n8n-flows-v3/mf_leads.sql: rc=0 count=5
16:  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
17:  alert_sent    boolean NOT NULL DEFAULT false,
18:  alert_token   text,
19:  alert_until   timestamptz,
20:  alert_attempts int NOT NULL DEFAULT 0);

grep -c handover/demo/n8n-flows-v4/mf_leads.sql: rc=0 count=5
16:  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
17:  alert_sent    boolean NOT NULL DEFAULT false,
18:  alert_token   text,
19:  alert_until   timestamptz,
20:  alert_attempts int NOT NULL DEFAULT 0);

grep -c handover/flows-audit/patches/F-001-one-ddl.patch: rc=0 count=6
5:+-- NOTE (current table, four alert columns at the end): matches the flows used in the take (n8n-flows-real-v5, n8n-flows-film-v5) and the older v3 and v4 flows. The flows in this folder (v2) ignore the extra columns, so this table also runs them. A table that already exists without the alert columns needs: ALTER TABLE mf_leads ADD COLUMN alert_sent boolean NOT NULL DEFAULT false, ADD COLUMN alert_token text, ADD COLUMN alert_until timestamptz, ADD COLUMN alert_attempts int NOT NULL DEFAULT 0;
16:+  -- v3: alert state. alert_sent is set only AFTER the alert mail was sent. The recovery sweep claims rows in unknown/failed with alert_sent=false (token + alert_until, backoff 60 s x (1 + attempts, max 5)).
17:+  alert_sent    boolean NOT NULL DEFAULT false,
18:+  alert_token   text,
19:+  alert_until   timestamptz,
20:+  alert_attempts int NOT NULL DEFAULT 0);
```

## (o)

Command: `git apply --stat handover/flows-audit/patches/F-001-one-ddl.patch`
Exit code: 0

```
 handover/demo/n8n-flows/mf_leads.sql |   10 ++++++++--
 1 file changed, 8 insertions(+), 2 deletions(-)
```

## (o)

Command: `git apply --stat handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch`
Exit code: 0

```
 handover/demo/n8n-mainframe/build_mainframe.py |   10 +++++++---
 1 file changed, 7 insertions(+), 3 deletions(-)
```

## (o)

Command: `git apply --stat handover/flows-audit/patches/F-003-runsheet-claims.patch`
Exit code: 0

```
 handover/demo/VIDEO-RUNSHEET.md |   22 +++++++++++-----------
 1 file changed, 11 insertions(+), 11 deletions(-)
```

## (o)

Command: `git apply --stat handover/flows-audit/patches/F-004-page-statement-17.patch`
Exit code: 0

```
 handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md |   12 ++++++------
 1 file changed, 6 insertions(+), 6 deletions(-)
```

## (p)

Command: `git status --porcelain`
Exit code: 0

```
?? handover/flows-audit/evidence-2.md
?? handover/flows-audit/tools/scratch/
```

## (p)

Command: `git diff --stat 3bf5ae299cebac78963780895af5c585cab8473c HEAD -- . ':!handover/flows-audit'`
Exit code: 0

```
(empty)
```

## Summary

check | exit code
--- | ---
(0) date -u; git rev-parse HEAD; git status --porcelain | 0
(a) python3 handover/flows-audit/tools/check_counts.py | 0
(b) python3 handover/flows-audit/tools/check_names.py | 0
(c) python3 handover/flows-audit/tools/check_refs.py | 0
(d1) sh handover/flows-audit/tools/check_patches.sh | 0
(d2) git apply --check handover/flows-audit/patches/F-001-one-ddl.patch; echo $? | 0
(d2) git apply --check handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch; echo $? | 0
(d2) git apply --check handover/flows-audit/patches/F-003-runsheet-claims.patch; echo $? | 0
(d2) git apply --check handover/flows-audit/patches/F-004-page-statement-17.patch; echo $? | 0
(e) python3 handover/flows-audit/tools/check_secrets.py | 0
(f1) git status --porcelain | 0
(f2) git diff --stat 3bf5ae299cebac78963780895af5c585cab8473c HEAD -- . ':!handover/flows-audit' | 0
(g) python3 handover/flows-audit/tools/test_dump_nodes.py | 0
(h) python3 handover/flows-audit/tools/dump_nodes.py counts handover/demo | tail -3 | 0
(i) for f in handover/demo/n8n-*/**/*.json (not n8n-tests): dump_nodes.py check <f> | 0
(j) python findings count | 0
(k) python counts | 0
(m) F-002 rebuild | 0
(n) cmp/grep | 0
(o) git apply --stat handover/flows-audit/patches/F-001-one-ddl.patch | 0
(o) git apply --stat handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch | 0
(o) git apply --stat handover/flows-audit/patches/F-003-runsheet-claims.patch | 0
(o) git apply --stat handover/flows-audit/patches/F-004-page-statement-17.patch | 0
(p) git status --porcelain | 0
(p) git diff --stat 3bf5ae299cebac78963780895af5c585cab8473c HEAD -- . ':!handover/flows-audit' | 0

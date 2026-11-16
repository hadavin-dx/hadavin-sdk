EVIDENCE RUNNER output, Mon Nov 16 07:15:21 UTC 2026, head 8b8ca98e3bd5e5ca6d56d4716bf49d1bf45b8fab

## (0)

Command: `date -u; git rev-parse HEAD; git status --porcelain`
Exit code: 0

```
Mon Nov 16 07:15:21 UTC 2026
8b8ca98e3bd5e5ca6d56d4716bf49d1bf45b8fab
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
PASS 5087 references
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
PASS 0 hits in 162 files
```

## (f1)

Command: `git status --porcelain`
Exit code: 0

```
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
FINDINGS.md rows (^| F-): 28
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
31:525 of 655 nodes.** The lane LIVE-REFERENCE tests found hits fo
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

# E1 patch check (raw)
Mon Nov 16 08:52:24 UTC 2026

## $ git apply --check -p1 F-001-one-ddl.patch (pristine copy)
files in headers:
b/handover/demo/n8n-flows/mf_leads.sql
exit=0

## $ git apply --check -p1 F-002-take-key-check-and-claim-error-path.patch (pristine copy)
files in headers:
b/handover/demo/n8n-mainframe/build_mainframe.py
exit=0

## $ git apply --check -p1 F-003-runsheet-claims.patch (pristine copy)
files in headers:
error: handover/demo/VIDEO-RUNSHEET.md: No such file or directory
exit=1

## $ git apply --check -p1 F-004-page-statement-17.patch (pristine copy)
files in headers:
b/handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
exit=0

## $ git apply --check -p1 F-008-save-runs-for-the-take.patch (pristine copy)
files in headers:
b/handover/demo/n8n-mainframe/build_mainframe.py
exit=0

## ALL FIVE applied in order on one copy
$ git apply -p1 F-001-one-ddl.patch
exit=0
$ git apply -p1 F-002-take-key-check-and-claim-error-path.patch
exit=0
$ git apply -p1 F-003-runsheet-claims.patch
error: handover/demo/VIDEO-RUNSHEET.md: No such file or directory
exit=1
$ git apply -p1 F-004-page-statement-17.patch
exit=0
$ git apply -p1 F-008-save-runs-for-the-take.patch
exit=0

## absent files named in headers
present handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
present handover/demo/n8n-flows/mf_leads.sql
present handover/demo/n8n-mainframe/build_mainframe.py

## check_patches.sh (needs git repo root; run from a pristine copy as is)
error: handover/demo/VIDEO-RUNSHEET.md: No such file or directory
FAIL apply-check handover/flows-audit/patches/F-003-runsheet-claims.patch
exit=1
## same, inside a throwaway git repo (git init in copy)
error: handover/demo/VIDEO-RUNSHEET.md: No such file or directory
FAIL apply-check handover/flows-audit/patches/F-003-runsheet-claims.patch
exit=1

## addendum: F-003 header lines (no 'diff --git' line, so the listing above is empty for it)
--- a/handover/demo/VIDEO-RUNSHEET.md
+++ b/handover/demo/VIDEO-RUNSHEET.md
@@ -1,7 +1,7 @@
 # Video run sheet: the ONE video (main flow plus the doubtful-case scene)
 
## all ---/+++ paths in all patches and presence in tree
ABSENT NOTE:
ABSENT handover/demo/VIDEO-RUNSHEET.md
present handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md
present handover/demo/n8n-flows/mf_leads.sql
present handover/demo/n8n-mainframe/build_mainframe.py
## find VIDEO-RUNSHEET anywhere in new/ and old/
new/handover/flows-audit/patches/F-003-runsheet-claims.patch
old/handover/flows-audit/patches/F-003-runsheet-claims.patch

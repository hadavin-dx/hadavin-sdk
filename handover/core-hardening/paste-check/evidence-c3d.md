# evidence-c3d (raw). Fresh copy of inputs/, patches applied in order, 2026-11-16
$ patch -p1 --dry-run < paste-check/plan-v5-fixes.patch
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
$ patch -p1 --dry-run < paste-check/plan-v5-repin.patch  (after fixes applied for real on the copy)
checking file inputs/plan-wp6-resmoke-v5.md
rc=0
patching file inputs/plan-wp6-resmoke-v5.md
apply rc=0
$ cmp patched copy vs the lead-side b/ tree the patch was built from
cmp rc=0
$ placeholder lines (expected: 2, 120, 235, 515 only)
2:**HEAD_PIN =
120:| code | (
235:$HEAD_PIN 
515:| ID | fil

## changed shell span: gone() (patched plan lines 150-153), no placeholders inside
$ bash -n
bash -n rc=0
$ dash -n
dash -n rc=0

## P-2 first line (PowerShell): not syntax-checked (no pwsh here); only quoting read

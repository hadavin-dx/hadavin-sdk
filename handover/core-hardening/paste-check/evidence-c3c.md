# evidence-c3c: patched plan (plan-v5-fixes.patch applied to a scratch copy), 2026-11-16
Commands: `patch -p1 --dry-run < plan-v5-fixes.patch` (output and rc in patch-dryrun.txt: rc=0); apply with `patch -p1 -s`; then the same extractor as C3b (extract_spans.py, with the line number of the S13 prefix changed from 409 to 411 because the patch adds lines) on the patched plan. Raw index: spans-index-patched.tsv; run log below.
161 spans

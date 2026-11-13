# RESULTS V4b (evidence runner; raw logs in this folder)
Note: RR/tree-V4bold did NOT exist. I built it as a copy of tree-V4b with out/F4b/fix.patch reverted (git apply -R) at RR/tmp-V4b/old (deleted after use); base 61ded9e + working-tree changes.
| run | tree | head | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|---|
| 1 old, DPLD_REQUIRE_COUNT=1, docs file | V4bold copy | 61ded9e+wt | 6 | 5 | 0 | 0 | 6s | no |
| 2 old, unset | V4bold copy | same | 6 | 5 | 0 | 0 | 7s | no |
| 3 V4b, REQ=1, docs file | tree-V4b | 61ded9e+wt | 11 | 0 | 0 | 0 | 4s | no |
| 4 V4b, unset | tree-V4b | same | 11 | 0 | 0 | 0 | 5s | no |
| 5 V4b, REQ=1, 20 doc-reading files (incl. hygiene) | tree-V4b | same | 1558 | 0 | 33 | 0 | 275s | no |
| 6 recipe once (unshare -n + lo_up) | copy of V4b | same | ALL 7 CHECKS HOLD, rc 0 | | | | | no |
Files of run 5: doc-readers.txt (20; the builder said 14). Skips: gitleaks absent (28), playwright absent (3), root-readable file (1), py3.13-only (1).

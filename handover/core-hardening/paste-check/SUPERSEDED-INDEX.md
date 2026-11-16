# SUPERSEDED-INDEX (2026-11-16; fixes finding 5 of `../cross-read/one-place-sweep-r2.md`)
What is old, what replaced it, and how it is marked. Patch files were not edited (their sha256 stay); for them this index is the only marker. A banner was written as text added to the END OF LINE 1 of a file, so line numbers cited elsewhere (for example `REPORT-runpy4.md:3`, `v2/README.md:109`) did not move. Not checked: I did not search every file for citations of the files below.

## Patches and files in `paste-check/` (the plan chain: see `PLAN-CHAIN.md`)
| Old file | Status | Replaced by | Marker |
|---|---|---|---|
| `plan-v5-repin.patch`, `-repin-v2`, `-repin-v3`, `-repin-v4`, `-repin-v5` | SUPERSEDED, do not apply (fail or give wrong counts) | `plan-v5-repin-v6.patch` (sha256 `8a83abaa...`) | this index only (patch files) |
| `REPORT-repin.md`, `-v2`, `-v3`, `-v4` | SUPERSEDED | `REPORT-repin-v6.md` | banner on line 1 (`REPORT-repin-v5.md` already had one) |
| `plan-v5-gate-rows.patch`, `plan-v5-gate-rows-v2.patch` | SUPERSEDED, do not apply | `plan-v5-gate-rows-v3.patch` (sha256 `498c1e5f...`) | this index only |
| `REPORT-c13-v2.md` | SUPERSEDED | `REPORT-c13-v3.md` | banner on line 1 |
| `GATE-ROWS-resmoke.md` | CURRENT, but its title says "version 4" (fix pass 4) while the patch it belongs to is `-v3`: two numbering schemes, not two versions of the patch | no change | this note |
| `plan-v5-real-v5-edits.md`, `plan-v6-...`, `plan-v7-...`, `plan-v8-...`, `plan-v9-real-v5-edits.md` | SUPERSEDED edit lists | `plan-v10-real-v5-edits.md` plus `plan-v10-corrections-after-chain.md` (needed when applied after the chain) | banner on line 1 |
| `apply-v6.py` to `apply-v9.py` | go with the superseded lists; not edited | `apply-v10.py` (original plan only) or `apply-v10-after-chain.py` (after the chain) | this index only |
| `REPORT-real-v5-edits.md`, `-v6`, `-v7`, `-v8`, `-v9` | SUPERSEDED builder reports | `REPORT-real-v5-edits-v10.md` | banner on line 1 |
| `LEAD-FILL-list.md` (v4) | SUPERSEDED | `LEAD-FILL-list-v5.md` | banner on line 1 |
| `plan-v10-real-v5-edits.md` | CURRENT text but its numbers are right only on the UNPATCHED plan (173 min); after the chain use `plan-v10-corrections-after-chain.md` | n/a | `PLAN-CHAIN.md` section 0 and 4 (old file not edited) |

## `patches-ready/` (kept scope is `v5/`: G5-wording, optional C-01-MINIMAL, dead-man note; decision 4 and Q18)
| Old item | Status | Marker |
|---|---|---|
| `A-01.patch`, `C-01.patch`, `G5-wording.patch` at the top level | SUPERSEDED first set; `A-01` and full `C-01` are not in the kept scope | this index only (patch files) |
| `DEAD-MAN-CHECK.md`, `unverified-claims-check.md` at the top level | SUPERSEDED (replaced by `v5/DEAD-MAN-CHECK.md` and `README.md`) | banner on line 1 |
| `v2/` | SUPERSEDED | banner on `v2/README.md` line 1 and new `v2/SUPERSEDED-NOTE.md` |
| `v3/` | SUPERSEDED but still cited by v5 for raw files and C7b evidence | banner on `v3/README.md` line 1 and new `v3/SUPERSEDED-NOTE.md` |
| `v4/` | SUPERSEDED | new `v4/SUPERSEDED-NOTE.md` only: `v4/SHA256SUMS.txt` lists `README.md` and `DEAD-MAN-CHECK.md`, a banner in them would break `sha256sum -c` (run after my changes: all OK). `v4/DEAD-MAN-CHECK.md` still has its v3 title, unedited text (`v5/README.md:32`) |
| `v5/DEFERRED-A-01.patch`, `v5/CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch` | DEFERRED / CUT, not superseded; named by their file names | no change |

## Reports of rounds that were replaced (not patches)
| File | What is stale | Marker |
|---|---|---|
| `../mutation-lane/REPORT.md` | "v2 rerun pending (C8c)" will not happen (Q18 stopped new C8 work); numbers are for the v1 patches | banner on line 1 |
| `../mutation-lane/REPORT-runpy3.md` | round 2; replaced by `REPORT-runpy4.md`; its "no precedent" wording about the S603 note differs from the evidence review (finding 6, not resolved here) | banner on line 1 |
| `../mutation-lane/REPORT-runpy4.md` | line 3 says "Not reviewed by anyone yet"; `review-runpy4-evidence.md` and `review-runpy4-security.md` exist | banner on line 1 (note, text not changed) |
| `../c6-skip-audit/REPORT.md` | lane3 "NOT READ" is replaced by `evidence-lane3-recompute.md`; claim text near line 20 lacks "inside the lease" (`REPORT-c6f.md:64`) | banner on line 1 |

## Not done
Finding 5 also lists the "v4/DEAD-MAN-CHECK.md title"; handled as above (not edited, hash-protected). I did not verify the claims in the banners beyond reading the cited lines (`REPORT-runpy4.md:3`, `c6-skip-audit/REPORT.md` lines 20 and 48, `REPORT-c6f.md:64`, `mutation-lane/REPORT.md:3`); I did not open `evidence-lane3-recompute.md` further than its first 5 lines.

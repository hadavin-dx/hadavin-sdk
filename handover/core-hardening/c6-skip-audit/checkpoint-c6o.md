# checkpoint-c6o (started 2026-11-16T15:34:53Z)
checkpoint-c6o: started 15:34Z; read all inputs; B1 settled from mf-form.json:97+270+298, mf-recovery.json:26; now writing build_c6o.py

## note 2 (15:52Z, 18 min in)
Design fixed: build_c6o.py reads REPORT-c6n.md (not c6m), patches rows (split 1, 33, 39; new rows 73+ for RS:6/30/32/47/52/57, PG:120/121/132/144/145, ONE:1/26, generator), adds questions L-CARDLEN, L-SCENES, makes rows 13/21 NOT FILMABLE (L-LEASE two readings). Next: write build_c6o.py part 1 (rows), then sections_c6o.py, verify-c6o.py (exits non-zero), neg controls.

## note 3 (15:53Z by the machine clock; 19 min in)
Done: build_c6o.py + sections_c6o.py build REPORT-c6o.md (94 rows; ready 49, defaults 40, check 3, NOT FILMABLE 2); verify-c6o.py (59 checks, exit 1 on any FAIL, 0 on the report); neg_controls_c6o.py: 24 copies (1 control + 23 changed), all 23 changed exit non-zero, control exits 0. Next: read the built report once for sense, CHANGES file, sha256, banned scan counts, final report.

## Note 4 (final)
Done: build, verify (60 checks, rc 0), 24 negative-control copies (0 wrong), CHANGES file. Fixed a stale wave-1 count in the glossary. Next: report via handback. Blockers: items labelled in the report (L-LEASE, n8n checks, HubSpot scope).

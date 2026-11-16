# C6 resolve round 1 log (builder), 2026-11-16

Wrong claims re-checked with grep first: run sheet :36 has K3/K3B (confirmed); nine lines have K3 (:24 :32 :36 :38 :39 :41 :47 :54 :90, confirmed); v1 recovery is every 30 s, lease 20 s (mf-recovery.json:2, :7-10, :15, confirmed). Plan v5 = flows-audit/inputs/plan-wp6-resmoke-v5.md (:125 saving all, :550 n8n DB owner).

| finding | status | how |
|---|---|---|
| Wrong claim :36 | fixed | Corrections section; F-007 row |
| Wrong claim K3 closing card only | fixed | nine lines listed; reach in F-007 |
| Wrong claim F-025 20 s | fixed | 30 s sweep, 20 s lease, cites |
| M1 | fixed (decision left open) | gate item 1: read and cite lane3 raw or drop the number; raw not read |
| M2 | fixed | T7b re-scope block, linked from F-011 |
| M3 | fixed | F-007 reach incl. :90 and mf.py:158; N4 folded |
| N2 | fixed | upgraded to Major, gate item 4 |
| F-006 decision | fixed | row and gate item 6 (run sheet :56, :78) |
| F-011 attribution | fixed | plan v5:550, EXCEPTIONS.md:5 |
| N5 | fixed | recommendation to cut or label v3 |
| m1 | fixed | N1 says parse was by hand, no saved output |
| m2, m4 | fixed | added to not-checked list |
| m3 | fixed | n=3 for K3 noted |
| N1 | fixed | importable sets named, one-active check, diff narrowed |
| N3 | fixed | split N3a/N3b |
| N6, F-020, F-022, F-023, F-025 | fixed | F-022 adds mf-form real-v5 :238-295 note; F-023 adds :3/:51 |
| F-003 wording, "allowed on closing card" | fixed | corrected in Corrections |
| PAGE-STATEMENTS path | note | file is under n8n-flows/, not demo/ root; cite updated |

Not re-verified: anything needing n8n or the lane3 raw.

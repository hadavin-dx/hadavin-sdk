# Committed patch bytes against recorded sha256 (checked 2026-11-14 05:26Z)

Columns: file | recorded hash | committed-bytes hash | result. A MISMATCH means git rewrote CRLF to LF; the true bytes are in the matching -crlf.patch.gz (checked: unpacks to the recorded hash).

```
RESULTS.md | a786ffb5114a | - | NOT COMMITTED (as .patch)
apply-matrix.txt | 89b7967febb4 | - | NOT COMMITTED (as .patch)
core-fix-on-frozen-r7b-lf.patch | 07091087654b | 07091087654b | match
core-fix-on-frozen-r7b.patch | 68a5e05cf615 | 07091087654b | MISMATCH; original found
core-fix-on-frozen-r7c-lf.patch | 7b46e0b8e51c | 7b46e0b8e51c | match
core-fix-on-frozen-r7c.patch | 6c58079b415c | c7bff839feea | MISMATCH; original found
core-fix-on-frozen-r7d-lf.patch | 133a19bab360 | 133a19bab360 | match
core-fix-on-frozen-r7d.patch | 151fac673ef8 | 133a19bab360 | MISMATCH; original found
core-fix-on-frozen-r7e-lf.patch | 89ca3a2ddeba | 89ca3a2ddeba | match
core-fix-on-frozen-r7e.patch | 508135cc44a6 | 89ca3a2ddeba | MISMATCH; original found
core-fix-on-frozen-r7f-lf.patch | 844c8407acf2 | 844c8407acf2 | match
core-fix-on-frozen-r7f.patch | 7041492f9555 | 844c8407acf2 | MISMATCH; original found
core-fix-on-frozen-r7g-lf.patch | 2e31f323fae6 | 2e31f323fae6 | match
core-fix-on-frozen-r7g.patch | d819e6a0fcce | 2e31f323fae6 | MISMATCH; original found
core-fix-r7-to-r7b-delta.patch | a3ff86c56f86 | c0d566694165 | MISMATCH; original found
core-fix-r7b-to-r7c-delta.patch | 1a7b88224002 | 2053bb67b55d | MISMATCH; original found
core-fix-r7c-to-r7d-delta.patch | 3b228fdf429f | 97199112a000 | MISMATCH; original found
core-fix-r7d-to-r7e-delta.patch | 29b429c00700 | 29b429c00700 | match
core-fix-r7e-to-r7f-delta.patch | 1a3adcc017af | 1a3adcc017af | match
core-fix-r7f-to-r7g-delta.patch | 08895dc78247 | 08895dc78247 | match
MISMATCH 9
```

Not checked: patches from r2 to r6, v1, v2, F*-fix, docs, f8 (no recorded hash file in this folder). Next: hash them in the build folder and compare, then add .gz where they differ.

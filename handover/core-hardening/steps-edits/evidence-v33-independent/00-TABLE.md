# Evidence v33 (independent runner; records, does not judge). Run 2026-11-16 about 18:45-18:58 UTC. Work copy /tmp/ev33 (originals untouched; sha256 of 25 v33 files before = copy, 01-sha-compare.txt).
| # | Item | Command | Result | File |
|---|---|---|---|---|
| 1 | sha256 of v33 files | sha256sum (25 files) | recorded; builder lists no hashes, so nothing to compare to; copy identical to originals | 00-sha-*.txt, 01 |
| 2 | rebuild from SOURCE | python3 -B build-v33.py /tmp/ev33/rb/ | 10 pages rebuilt; cmp: 10 of 10 byte-identical to delivered | 02, 03 |
| 3a | check-v33.py | python3 -B check-v33.py | 0 failures | 04 |
| 3b | v33-fail-proof.py | python3 -B -I v33-fail-proof.py | 32 checks (C228-C262); 11 fail on built v32; 0 on v33; exit 0 | 05 |
| 3c | gap-proof-v33.py | python3 -B gap-proof-v33.py | v32 checker misses 8 of 11 (3 anchors absent in v32); v33 checker catches 11 of 11 | 06 |
| 3d | mut33.py | python3 -B mut33.py | 283 plants: 282 caught by meant check, 0 missed, 0 anchor-not-found, negative control ok | 07 |
| 4 | 15 own plants X01-X15 | python3 -B myplants33.py | 11 caught, 4 MISSED (X03, X07, X08, X10) | 08 |
| 5 | words | wc -w | sheet A 6,286, sheet B 6,087 (cap 6,300); card 2,215/2,130; appendix 5,823/5,754; film 577; helper 821; note 13,615; open list 8,461 | 09 |
| 6 | banned / secret scan | scan.py | banned hits 0 (list of 10 read at run time, not written); secret-shaped hits 0; AKIAIOSFODNN7EXAMPLE occurs 0 times | 10 |
| 7 | UTC/IST pairs, weekdays | pairs.py | 238 pairs all +5:30; 0 lone UTC or IST times; 0 wrong weekdays; Mon 16, Wed 18, Sun 22, Mon 23, Wed 25 Nov all present and correct | 11 |

# cost, 200 kB hostile text, own script cost9.py; two sets of 3 runs each, median seconds per set. Machine load average was about 5 (other agents running), so absolute times are noisy.

| shape | head set1 | head set2 | main set1 | main set2 | ratio (mean head / mean main) |
|---|---|---|---|---|---|
| A letters only | 0.796 | 0.841 | 0.407 | 0.468 | 1.87 |
| B 40 letters + pass | 0.909 | 0.981 | 0.453 | 0.426 | 2.15 |
| C 40 letters + password= x | 0.609 | 0.602 | 0.225 | 0.216 | 2.75 |
| D glued digits + token:  | 0.514 | 0.514 | 0.236 | 0.232 | 2.20 |
| E --a*39 pass flag | 0.899 | 0.876 | 0.260 | 0.251 | 3.47 |
| F --a- runs | 1.200 | 1.181 | 0.802 | 0.814 | 1.47 |
| G --a_ runs | 0.776 | 0.835 | 0.435 | 0.559 | 1.62 |
| H pass + digit run | 0.783 | 0.847 | 0.453 | 0.493 | 1.72 |
| I Digest + spaces | 0.739 | 0.579 | 0.267 | 0.360 | 2.10 |
| J Digest + newlines | 0.601 | 0.612 | 0.249 | 0.260 | 2.38 |
| K authorization abc + spaces | 0.631 | 0.567 | 0.267 | 0.290 | 2.15 |
| L cookie prefixes | 1.101 | 1.012 | 0.391 | 0.421 | 2.60 |
| M glued plural tokens | 0.910 | 0.953 | 0.309 | 0.322 | 2.95 |
| N pass words | 0.714 | 0.747 | 0.337 | 0.300 | 2.29 |
| O hyphen words | 0.760 | 0.741 | 0.390 | 0.409 | 1.88 |
| P wrapped Basic | 0.640 | 0.677 | 0.245 | 0.255 | 2.63 |
| Q cookie + long run | 0.795 | 0.909 | 0.456 | 0.459 | 1.86 |
| R unclosed quote Digest | 0.432 | 0.420 | 0.467 | 0.461 | 0.92 |
| S --a-authorization | 0.935 | 0.939 | 0.309 | 0.307 | 3.04 |
| T cookie2 digits | 0.566 | 0.607 | 0.250 | 0.292 | 2.16 |

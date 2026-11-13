# Readable probes: key x 4 paths (card, tool, log, walk) x 4 value styles = 16 per key (a probe is READABLE when a piece of the made-up value is left in the output)

| key | main | head 4091f8b1 (before) | head after | note |
|---|---|---|---|---|
| passcode | 10/16 | 16/16 | 0/16 |  |
| passkey | 10/16 | 16/16 | 0/16 |  |
| pass_code | 6/16 | 12/16 | 0/16 |  |
| session_key | 10/16 | 12/16 | 0/16 |  |
| sessionkey | 10/16 | 16/16 | 0/16 |  |
| pass_value | 6/16 | 12/16 | 0/16 |  |
| PASS_value | 6/16 | 12/16 | 0/16 |  |
| Pass_value | 6/16 | 12/16 | 0/16 |  |
| session_value | 10/16 | 12/16 | 0/16 |  |
| SESSION_value | 10/16 | 12/16 | 0/16 |  |
| Session_value | 10/16 | 12/16 | 0/16 |  |
| auth_value | 16/16 | 12/16 | 0/16 |  |
| bearer_value | 12/16 | 12/16 | 0/16 |  |
| key-data | 14/16 | 6/16 | 0/16 |  |
| cert-data | 14/16 | 6/16 | 0/16 |  |
| certificate-data | 14/16 | 6/16 | 0/16 |  |
| session_cookie | 7/16 | 3/16 | 0/16 |  |
| authorization | not in corpus | | | |
| newpass | 7/16 | 7/16 | 0/16 |  |
| oldpass | 7/16 | 7/16 | 0/16 |  |
| confirmpass | 7/16 | 7/16 | 0/16 |  |
| defaultpass | 7/16 | 7/16 | 0/16 |  |
| postgresauth | 13/16 | 7/16 | 0/16 |  |
| jenkinssession | 7/16 | 7/16 | 0/16 |  |
| supersession | 7/16 | 3/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| bypass | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| compass | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| oauth | 13/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| obsession | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| possession | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| trespass | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |
| overpass | 7/16 | 7/16 | 4/16 | ordinary word, readable on the record walk by design (LIMITS) |

## Whole corpus (1140 keys x 16 = 18240 probes)

- main: 11416 readable of 18240
- head-before: 6780 readable of 18240
- head-after: 110 readable of 18240
- readable on head-before but masked on main (regression): 1338 probes; on head-after: 0

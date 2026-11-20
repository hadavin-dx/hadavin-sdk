# G8 v2: the glued-rest gap of IPv4, phone, IBAN and UUID (ORDER 016c item 15, K38 / L33, backlog 10)

Status: DRAFT v2 for plan review round 2, core-c drafter (opus tier), 2026-11-20. Nothing is built. Rewrites
G8-glued-rest-gap.md (v1) and answers every finding of G8-review-1.md (section 16 lists each one TAKEN or CONTESTED). A builder
with no other context builds from this file alone: every changed PATTERNS tuple is in section 4, the data file, the test file
and the mutant file are complete in appendices A to C, the source diff is appendix D. Path class: redaction. Lead rule: build
only a gap that a failing input proves (G4 v2 section 0).

## 0. Base, what was measured where, and what is NOT RE-MEASURED
- Measured base: cloud/core-c 3c11364 (gate round 4 b83accc, G7 rounds 3 and 4 da0f71f / 6783535, P1d-a rounds 2 and 3
  a2dea63 / 61ff6e7 merged). Every number of sections 2, 7 and 9 comes from clean `git archive` copies of 3c11364 in the
  drafter's scratchpad: `v2base` (HEAD as is), `v1proto` (v1's g8.patch), `v2proto` (this design), `v2base_g4c` and
  `v2proto_g4c` (the same with G4 v3's host regexes, section 5.4). The shared tree was not edited and no test was run in it.
- Current HEAD when this file was written: a5f55addc (G7 fix round 5, d1384342e, landed during the drafting). It changes
  redact.py only in the module docstring and the `_Redactor` settle / spelled-form code (hunks at 15, 875-2197); no PATTERNS
  line, no `_sweep` / `_replace_standalone` line, no runmap line G8 edits. The G8 v2 edit script applies to an archive of
  a5f55addc without a miss (appendix D is the diff against a5f55addc). The 80 rows, the must-keep rows and the test file were
  NOT RE-MEASURED on a5f55addc: the coordinator stopped new test and probe batches (box load 10.5 on 4 cores) right after the
  3c11364 runs. Phase 0 (section 8) re-runs them first; any difference from appendix A: STOP and report.
- Line numbers below are those of a5f55addc.
- G4 dependency: measured against G4 v3 (handover/core-c/tickets/G4-P1c-redactor-gaps-v3.md, blob e30443310b2f, commit
  aef96b6, section 5.2 and 5.3, compiled as written there and put in place of today's HOSTNAME entry). G4 v3 is NOT READY
  (G4-review-3); G4 v4 is being drafted and was not read. G8 does not wait for G4 (section 8, L-D7).
- Python: measured on 3.13.18 only (pyproject: `>=3.12`). The nested look-behind `(?<!(?<![A-Za-z])[vV])` is fixed width
  and compiles on 3.13.18; on 3.12 by reading only.

## 1. Goal
A value of kind IPV4, PHONE, IBAN or UUID glued straight to a letter, a digit or `_` (no word boundary) is masked in the first
`redact()` / `redact_many()` / `runmap.redact_text` call, as P1d-a did for EMAIL (`(?![A-Za-z])`). The glued text stays in the
output, outside the placeholder (`<IPV4_1>a`, `node_<IPV4_1>`). Shapes that cannot be told from a hash, a version or code are
stated limits, pinned by strict xfails. HOSTNAME gets no G8 code: its "glued before" rows (64, 71) are closed by G4c; its
"glued after the suffix" rows are limit L6.

## 2. Problem (what the probe shows on 3c11364)
Not a fixed-point problem: a second `redact()` on the output masks nothing more in any of the 80 rows. It is a boundary
problem in four pattern entries and one sweep rule:
- `IPV4` dotted (redact.py:377) and EC2 dashed (375) start and end with `\b`: a letter or `_` on either side refuses the match.
- `PHONE` (491-497) refuses a start after `\w . -` and an end before `\w .` (on purpose: hashes and identifiers, comment
  472-490). A formatted phone followed by a letter or `_` is not masked, or only in part (`<PHONE_1> 1234a`: the regex
  backtracks to the last separator and leaves the last group readable).
- `IBAN` (266-274) starts and ends with `\b`: `_x` after, or any letter, digit or `_` before, refuses it. A letter or digit after
  is absorbed into the BBAN (11 to 30 letters or digits), so rows 34 and 35 are masked today and stay so (the extra `a` / `9`
  goes into the placeholder: `pay <IBAN_1> now`, original `DE89...00a`).
- `UUID` (275-280) starts and ends with `\b`: anything glued refuses it; with a prefix glued, `ACCOUNTID` takes the last 12
  digits and 24 of 36 characters stay readable.
- The identifier sweep (`_replace_standalone`, redact.py:2167, called at 1980 for every `_STANDALONE` value of `_sweep`, 2146)
  refuses a copy that an ASCII letter or digit touches, so a clean copy of a contiguous phone number elsewhere in the text does
  not mask its letter-glued copy (row 31). IBAN is a SECRET kind (`_EVERY_COPY`): its glued copies are already swept (row 43).

### 2.1 Counts (80 probe rows: 75 glued shapes + 5 controls at rows 1, 17, 33, 46, 59)
| kind | rows | leak today | closed by G8 v2 | output changes, no leak either way | stated limit after G8 | closed by G4c (not G8) | unchanged, no leak |
|---|---|---|---|---|---|---|---|
| IPv4 | 19 | 17 | 15 | 0 | 2 (rows 10, 13) | 0 | 2 |
| phone | 17 | 13 | 11 | 2 (rows 21, 22: `x+<PHONE_1>` -> `x<PHONE_1>`) | 2 (25, 27) | 0 | 2 |
| IBAN | 14 | 10 | 8 | 0 | 2 (40, 76) | 0 | 4 |
| UUID | 14 | 13 | 13 | 0 | 0 | 0 | 1 |
| host name | 16 | 9 | 0 | 0 | 7 (67-70, 78-80) | 2 (64, 71) | 7 |
| total | 80 | 62 | 47 | 2 | 13 | 2 | 16 |
Rows: closed 47, left 15 (13 limits + 2 closed by G4c), limits 13. The v2 PHONE redesign (section 4, codebase M1) closes exactly
the rows v1 closed: the 80 outputs of `v2proto` are byte-identical to `v1proto`'s. What v2 changes is outside the 80 rows: it
removes v1's over-masks of letter-glued digit groups (section 2.3). `redact()`, `redact_many([text, "other line"])` and
`runmap.redact_text` give the same output in all 80 rows on the base and with v2; `redact_untrusted` equals `redact_text` and
a second `redact_text` with the same run map changes neither text nor map in all 80 rows with v2 (tests of section 7, run).

### 2.2 Probe rows (data: appendix A, `ROWS`; values: `V` there, all fake or documentation values built from parts)
Values: `{IP1}` 192.0.2.10, `{IP2}` 198.51.100.7, `{IP3}` 203.0.113.45 (RFC 5737), `{IPD}` 192-0-2-10; `{PHONE_P}`
+1 415-555-0132, `{PHONE_P2}` +1 415-555-0199, `{PHONE10}` 4155550132, `{PHONEUK}` +44 20 5550 1234 (555 numbers);
`{IBAN_DE}`, `{IBAN_GB}` (the published example IBANs); `{UUID}` (the RFC example), `{UUIDUP}` upper case, `{UUID2}` a second
one, `{UUIDHEAD}` its first 24 characters; host names `{HOST}` db-7.corp.internal, `{HOST2}` db01.prod.corp, `{HOST3}`
nas02.office.lan, `{HOST4}` printer7.local, `{HOST5}` a.b.c.internal (made up). Leak rule: `leak()` in appendix A (ipv4 7
characters of the value in a row, iban and uuid 8, phone 4 digits once spaces and hyphens are removed, host: any label other
than corp, internal, local, lan, intranet, prod, office, or 2 or more leading characters of one directly before a placeholder).
Row 6 (`{IP1}9`) is the address 192.0.2.109 masked as its own value (`<IPV4_1>` = 192.0.2.109), not a leak.
Column "after G8 with G4c": only where it differs (`same` otherwise).

| # | kind | shape | input | output on base | expected after G8 (G4c not merged) | after G8 with G4c | class |
|---|---|---|---|---|---|---|---|
| 1 | ipv4 | control: spaces | `from {IP1} ok` | `from <IPV4_1> ok` | `from <IPV4_1> ok` | same | unchanged |
| 2 | ipv4 | letter after | `from {IP1}a ok` | `from {IP1}a ok` | `from <IPV4_1>a ok` | same | closed |
| 3 | ipv4 | word after | `from {IP1}abc ok` | `from {IP1}abc ok` | `from <IPV4_1>abc ok` | same | closed |
| 4 | ipv4 | _x after | `from {IP1}_x ok` | `from {IP1}_x ok` | `from <IPV4_1>_x ok` | same | closed |
| 5 | ipv4 | _ after | `from {IP1}_ ok` | `from {IP1}_ ok` | `from <IPV4_1>_ ok` | same | closed |
| 6 | ipv4 | digit after | `from {IP1}9 ok` | `from <IPV4_1> ok` | `from <IPV4_1> ok` | same | unchanged |
| 7 | ipv4 | letter before | `from x{IP1} ok` | `from x{IP1} ok` | `from x<IPV4_1> ok` | same | closed |
| 8 | ipv4 | word before (ip) | `from ip{IP1} ok` | `from ip{IP1} ok` | `from ip<IPV4_1> ok` | same | closed |
| 9 | ipv4 | _ before | `from node_{IP1} ok` | `from node_{IP1} ok` | `from node_<IPV4_1> ok` | same | closed |
| 10 | ipv4 | digit before | `from 7{IP1} ok` | `from 7{IP1} ok` | `from 7{IP1} ok` | same | limit |
| 11 | ipv4 | both sides letters | `from x{IP1}y ok` | `from x{IP1}y ok` | `from x<IPV4_1>y ok` | same | closed |
| 12 | ipv4 | both sides _ | `from eth0_{IP1}_up ok` | `from eth0_{IP1}_up ok` | `from eth0_<IPV4_1>_up ok` | same | closed |
| 13 | ipv4 | two glued IPs | `from {IP1}{IP2} ok` | `from {IP1}{IP2} ok` | `from {IP1}{IP2} ok` | same | limit |
| 14 | ipv4 | glued to UUID | `from {UUID}{IP1} ok` | `from {UUID}{IP1} ok` | `from <UUID_1><IPV4_1> ok` | same | closed |
| 15 | ipv4 | letter after + clean copy | `from {IP1} and {IP1}a ok` | `from <IPV4_1> and {IP1}a ok` | `from <IPV4_1> and <IPV4_1>a ok` | same | closed |
| 16 | ipv4 | after = with letter | `src={IP3}x dst` | `src={IP3}x dst` | `src=<IPV4_1>x dst` | same | closed |
| 17 | phone | control: spaces | `call {PHONE_P} now` | `call <PHONE_1> now` | `call <PHONE_1> now` | same | unchanged |
| 18 | phone | letter after | `call {PHONE_P}a now` | `call {PHONE_P}a now` | `call <PHONE_1>a now` | same | closed |
| 19 | phone | _x after | `call {PHONE_P}_x now` | `call {PHONE_P}_x now` | `call <PHONE_1>_x now` | same | closed |
| 20 | phone | _ after | `call {PHONE_P}_ now` | `call {PHONE_P}_ now` | `call <PHONE_1>_ now` | same | closed |
| 21 | phone | letter before | `call x{PHONE_P} now` | `call x+<PHONE_1> now` | `call x<PHONE_1> now` | same | changed |
| 22 | phone | _ before | `call tel_{PHONE_P} now` | `call tel_+<PHONE_1> now` | `call tel_<PHONE_1> now` | same | changed |
| 23 | phone | both sides | `call x{PHONE_P}y now` | `call x{PHONE_P}y now` | `call x<PHONE_1>y now` | same | closed |
| 24 | phone | clean copy + glued copy | `call {PHONE_P} or {PHONE_P}a now` | `call <PHONE_1> or {PHONE_P}a now` | `call <PHONE_1> or <PHONE_1>a now` | same | closed |
| 25 | phone | contiguous, letter after | `call {PHONE10}a now` | `call {PHONE10}a now` | `call {PHONE10}a now` | same | limit |
| 26 | phone | contiguous, _x after | `call {PHONE10}_x now` | `call {PHONE10}_x now` | `call <PHONE_1>_x now` | same | closed |
| 27 | phone | contiguous, letter before | `call x{PHONE10} now` | `call x{PHONE10} now` | `call x{PHONE10} now` | same | limit |
| 28 | phone | contiguous, word before | `call tel{PHONE10} now` | `call tel{PHONE10} now` | `call tel<PHONE_1> now` | same | closed |
| 29 | phone | contiguous, _ before | `call tel_{PHONE10} now` | `call tel_{PHONE10} now` | `call tel_<PHONE_1> now` | same | closed |
| 30 | phone | contiguous, both _ | `call id_{PHONE10}_x now` | `call id_{PHONE10}_x now` | `call id_<PHONE_1>_x now` | same | closed |
| 31 | phone | contiguous, clean copy + glued | `phone={PHONE10} then x{PHONE10} now` | `phone=<PHONE_1> then x{PHONE10} now` | `phone=<PHONE_1> then x<PHONE_1> now` | same | closed |
| 32 | phone | spaced UK, letter after | `call {PHONEUK}a now` | `call <PHONE_1> 1234a now` | `call <PHONE_1>a now` | same | closed |
| 33 | iban | control | `pay {IBAN_DE} now` | `pay <IBAN_1> now` | `pay <IBAN_1> now` | same | unchanged |
| 34 | iban | letter after (absorbed: alnum BBAN) | `pay {IBAN_DE}a now` | `pay <IBAN_1> now` | `pay <IBAN_1> now` | same | unchanged |
| 35 | iban | digit after | `pay {IBAN_DE}9 now` | `pay <IBAN_1> now` | `pay <IBAN_1> now` | same | unchanged |
| 36 | iban | _x after | `pay {IBAN_DE}_x now` | `pay {IBAN_DE}_x now` | `pay <IBAN_1>_x now` | same | closed |
| 37 | iban | _ after | `pay {IBAN_DE}_ now` | `pay {IBAN_DE}_ now` | `pay <IBAN_1>_ now` | same | closed |
| 38 | iban | letter before | `pay x{IBAN_DE} now` | `pay x{IBAN_DE} now` | `pay x<IBAN_1> now` | same | closed |
| 39 | iban | word before | `pay iban{IBAN_DE} now` | `pay iban{IBAN_DE} now` | `pay iban<IBAN_1> now` | same | closed |
| 40 | iban | digit before | `pay 7{IBAN_DE} now` | `pay 7{IBAN_DE} now` | `pay 7{IBAN_DE} now` | same | limit |
| 41 | iban | _ before | `pay iban_{IBAN_DE} now` | `pay iban_{IBAN_DE} now` | `pay iban_<IBAN_1> now` | same | closed |
| 42 | iban | both _ | `pay to_{IBAN_DE}_x now` | `pay to_{IBAN_DE}_x now` | `pay to_<IBAN_1>_x now` | same | closed |
| 43 | iban | clean copy + _x copy | `pay {IBAN_DE} or {IBAN_DE}_x now` | `pay <IBAN_1> or <IBAN_1>_x now` | `pay <IBAN_1> or <IBAN_1>_x now` | same | unchanged |
| 44 | iban | GB, _x after | `pay {IBAN_GB}_x now` | `pay {IBAN_GB}_x now` | `pay <IBAN_1>_x now` | same | closed |
| 45 | iban | GB, letter before | `pay x{IBAN_GB} now` | `pay x{IBAN_GB} now` | `pay x<IBAN_1> now` | same | closed |
| 46 | uuid | control | `id {UUID} ok` | `id <UUID_1> ok` | `id <UUID_1> ok` | same | unchanged |
| 47 | uuid | digit after | `id {UUID}9 ok` | `id {UUID}9 ok` | `id <UUID_1>9 ok` | same | closed |
| 48 | uuid | hex letter after | `id {UUID}a ok` | `id {UUID}a ok` | `id <UUID_1>a ok` | same | closed |
| 49 | uuid | non-hex letter after | `id {UUID}x ok` | `id {UUID}x ok` | `id <UUID_1>x ok` | same | closed |
| 50 | uuid | _x after | `id {UUID}_x ok` | `id {UUID}_x ok` | `id <UUID_1>_x ok` | same | closed |
| 51 | uuid | _0 after (k8s) | `id _default_{UUID}_0 ok` | `id _default_{UUID}_0 ok` | `id _default_<UUID_1>_0 ok` | same | closed |
| 52 | uuid | letter before (non-hex) | `id x{UUID} ok` | `id x{UUIDHEAD}<ACCOUNTID_1> ok` | `id x<UUID_1> ok` | same | closed |
| 53 | uuid | hex letter before | `id a{UUID} ok` | `id a{UUIDHEAD}<ACCOUNTID_1> ok` | `id a<UUID_1> ok` | same | closed |
| 54 | uuid | digit before | `id 7{UUID} ok` | `id 7{UUIDHEAD}<ACCOUNTID_1> ok` | `id 7<UUID_1> ok` | same | closed |
| 55 | uuid | _ before | `id pod_{UUID} ok` | `id pod_{UUIDHEAD}<ACCOUNTID_1> ok` | `id pod_<UUID_1> ok` | same | closed |
| 56 | uuid | both letters | `id x{UUID}y ok` | `id x{UUID}y ok` | `id x<UUID_1>y ok` | same | closed |
| 57 | uuid | upper, _x after | `id {UUIDUP}_x ok` | `id {UUIDUP}_x ok` | `id <UUID_1>_x ok` | same | closed |
| 58 | uuid | clean copy + glued copy | `id {UUID} then {UUID}x ok` | `id <UUID_1> then {UUID}x ok` | `id <UUID_1> then <UUID_1>x ok` | same | closed |
| 59 | host | control | `x {HOST} y` | `x <HOSTNAME_1> y` | `x <HOSTNAME_1> y` | same | unchanged |
| 60 | host | digit after | `x {HOST}9 y` | `x <HOSTNAME_1>.internal9 y` | `x <HOSTNAME_1>.internal9 y` | `x <HOSTNAME_1> y` | unchanged |
| 61 | host | letter after | `x {HOST}a y` | `x <HOSTNAME_1>.internala y` | `x <HOSTNAME_1>.internala y` | `x <HOSTNAME_1> y` | unchanged |
| 62 | host | _x after | `x {HOST}_x y` | `x <HOSTNAME_1>.internal_x y` | `x <HOSTNAME_1>.internal_x y` | `x <HOSTNAME_1> y` | unchanged |
| 63 | host | letter before | `x z{HOST} y` | `x <HOSTNAME_1> y` | `x <HOSTNAME_1> y` | same | unchanged |
| 64 | host | _ before | `x svc_{HOST} y` | `x svc_db-<HOSTNAME_1> y` | `x svc_db-<HOSTNAME_1> y` | `x <HOSTNAME_1> y` | g4c |
| 65 | host | digit before | `x 9{HOST} y` | `x <HOSTNAME_1> y` | `x <HOSTNAME_1> y` | same | unchanged |
| 66 | host | clean copy + glued | `x {HOST} then {HOST}a y` | `x <HOSTNAME_1> then <HOSTNAME_2>.internala y` | `x <HOSTNAME_1> then <HOSTNAME_2>.internala y` | `x <HOSTNAME_1> then <HOSTNAME_2> y` | unchanged |
| 67 | host | ends at corp, letter after | `x {HOST2}a y` | `x {HOST2}a y` | `x {HOST2}a y` | same | limit |
| 68 | host | ends at corp, digit after | `x {HOST2}9 y` | `x {HOST2}9 y` | `x {HOST2}9 y` | same | limit |
| 69 | host | ends at corp, _x after | `x {HOST2}_x y` | `x {HOST2}_x y` | `x {HOST2}_x y` | same | limit |
| 70 | host | lan, letter after | `x {HOST3}x y` | `x {HOST3}x y` | `x {HOST3}x y` | same | limit |
| 71 | host | lan, _ before | `x vm_{HOST3} y` | `x vm_nas02.<HOSTNAME_1> y` | `x vm_nas02.<HOSTNAME_1> y` | `x <HOSTNAME_1> y` | g4c |
| 72 | ipv4 | dashed EC2 name, letter after | `node ip-{IPD}a ready` | `node ip-{IPD}a ready` | `node ip-<IPV4_1>a ready` | same | closed |
| 73 | ipv4 | dashed EC2 name, _x after | `node ip-{IPD}_x ready` | `node ip-{IPD}_x ready` | `node ip-<IPV4_1>_x ready` | same | closed |
| 74 | ipv4 | letter between two IPs | `from {IP1}x{IP2} ok` | `from {IP1}x{IP2} ok` | `from <IPV4_1>x<IPV4_2> ok` | same | closed |
| 75 | phone | two formatted phones glued | `call {PHONE_P}{PHONE_P2} now` | `call <PHONE_1>+<PHONE_2> now` | `call <PHONE_1>+<PHONE_2> now` | same | unchanged |
| 76 | iban | two IBANs glued | `pay {IBAN_DE}{IBAN_GB} now` | `pay {IBAN_DE}{IBAN_GB} now` | `pay {IBAN_DE}{IBAN_GB} now` | same | limit |
| 77 | uuid | two UUIDs glued | `id {UUID}{UUID2} ok` | `id {UUID}{UUID2} ok` | `id <UUID_1><UUID_2> ok` | same | closed |
| 78 | host | bare .local, digit after | `x {HOST4}9 y` | `x {HOST4}9 y` | `x {HOST4}9 y` | same | limit |
| 79 | host | bare .local, _x after | `x {HOST4}_x y` | `x {HOST4}_x y` | `x {HOST4}_x y` | same | limit |
| 80 | host | bare .internal, letter after | `x {HOST5}x y` | `x {HOST5}x y` | `x {HOST5}x y` | same | limit |

### 2.3 The reviewers' hand traces, run (`redact()`; `runmap.redact_text` gave the same text in every case)
Base = 3c11364; v1 = v1's g8.patch on 3c11364; v2 = this ticket on 3c11364. Map shown where it says something.
| input | base | v1 prototype | v2 | what is true |
|---|---|---|---|---|
| `eth0 1500 9000` | unchanged | `eth<PHONE_1>` (map `0 1500 9000`) | unchanged | codebase M1 right for v1; fixed |
| `rtt 120 118 131 125ms` | `rtt <PHONE_1> 125ms` (3 of 4 masked) | `rtt <PHONE_1>ms` | `rtt <PHONE_1>ms` | over-masked today already; v2 masks the 4th number too (12 digits pass the 10-digit rule): L-D9 |
| `PO12-3456-7890` | unchanged | `PO<PHONE_1>` | unchanged | fixed |
| `x4242 4242 4242 4242` | `x4242 <PHONE_1>` (`4242 4242 4242`) | `x<PHONE_1> 4242` (PHONE, stored) | `x4242 <PHONE_1>` | v2 = base; a card glued to a letter leaks one group today (not G8; limit L9) |
| `INV2026-0042-1234` | unchanged | `INV<PHONE_1>` | unchanged | fixed |
| `ISBN978-3-16-148410-0` | unchanged | `ISBN<PHONE_1>-0` | unchanged | fixed |
| `sha256-3851007894abcdef0123` | unchanged | `sha<PHONE_1>abcdef0123` | unchanged | fixed |
| `python3.11.4.1` | unchanged | `python<IPV4_1>` | `python<IPV4_1>` | over-mask, L-D8 |
| `nginx_1.18.0.1-1_amd64.deb` | unchanged | `nginx_<IPV4_1>-1_amd64.deb` | same as v1 | over-mask, L-D8 |
| `1.2.3.4rc1` | unchanged (NOT masked today) | `<IPV4_1>rc1` | `<IPV4_1>rc1` | v1 section 12 was FALSE (codebase M2): the end `\b` between `4` and `r` is no boundary; G8 newly masks it (L-D8) |
| `order_1234567890` | unchanged | `order_<PHONE_1>` | `order_<PHONE_1>` | over-mask, L-D10 |
| `<TENANT_4155550132>` | unchanged | `<TENANT_<PHONE_1>>` (placeholder broken) | unchanged | codebase N1 right; v2 entry 6 ends on no `>` |
| `password=hunter` + newline + `ref hunter123-45-6789` | `password=<SECRET_1>\nref <SECRET_1><SSN_1>` | `...ref <SECRET_1><PHONE_1>` (v1 ticket) | `password=<SECRET_1>\nref <SECRET_1><SSN_1>` | G7 boundary test stays byte-identical (section 3) |
| `ref hunter123-45-6789` (G7's `fresh`) | unchanged | `ref hunter<PHONE_1>` | unchanged | `"<SSN_1>" not in fresh` still shows the over-mask |
| `known 1.2.3.4 and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | `known <IPV4_1> and v<IPV4_1>` | same as base | v2 keeps IPV4 out of `_JOINS` (L-D1) |
| `backup_20-11-2026 done` | unchanged | `backup_<PHONE_1> done` | unchanged | fixed |
| `ts+1000000000` | `ts+<PHONE_1>` | `ts<PHONE_1>` | `ts<PHONE_1>` | masked today; only the `+` moves inside |
| `call 4155550132 or +1 415-555-0132` | `<PHONE_1> or <PHONE_2>` | `<PHONE_2> or <PHONE_1>` | `<PHONE_2> or <PHONE_1>` | numbering changes (entry 5 runs first), pinned K65 |
| `+123-45-6789x` | unchanged | `<PHONE_1>x` | `<PHONE_1>x` (PHONE, stored) | L-D11 |
| `call 415-555-0132x123` | unchanged | unchanged | `call <PHONE_1>x123` | newly closed by the 10-digit branch (L-D9) |
| `rev 2-3851007894abcdef` | unchanged | (not traced) | unchanged | a first v2 draft with only the 10-digit rule gave `rev <PHONE_1>abcdef`; the 5-digit-run guard keeps it |
| `call 415-555-0132.`, `call 4155550132.` | unchanged (not masked) | unchanged | unchanged | not glued; stated limit L7, pinned |

### 2.4 Must-keep rows (appendix A, `MUST_KEEP`: 74 rows; K1-K28 are v1's table, which held 28 texts, not 26)
Verdicts: kept (nothing masked, before and after) | same (masked today; G8 leaves it, or changes only what the note says) |
over-mask L-Dn (accepted, owned by that decision) | closed (a real value newly masked). Tokens: `{SHA}` a 64-hex digest
starting 3851007894, `{SHA16}` its first 16, `{CARD}` 4242 4242 4242 4242, `{SSN}` 123-45-6789, `{UUIDHEX}` the UUID without
dashes. Measured on 3c11364 (base column) and `v2proto` (after column); 74 of 74 as listed.

| id | text | output on base | expected after G8 | verdict |
|---|---|---|---|---|
| K1 | `release v1.2.3.4 shipped` | `release v1.2.3.4 shipped` | `release v1.2.3.4 shipped` | kept (L-D1) |
| K2 | `node-v18.19.1.2 build` | `node-v18.19.1.2 build` | `node-v18.19.1.2 build` | kept (L-D1) |
| K3 | `dotted date 2026.11.20.10 ok` | `dotted date 2026.11.20.10 ok` | `dotted date 2026.11.20.10 ok` | kept (L1) |
| K4 | `oid 1.3.6.1.4.1 ok` | `oid <IPV4_1>.4.1 ok` | `oid <IPV4_1>.4.1 ok` | same |
| K5 | `sha {SHA}` | `sha {SHA}` | `sha {SHA}` | kept |
| K6 | `commit {PHONE10}abcdef ok` | `commit {PHONE10}abcdef ok` | `commit {PHONE10}abcdef ok` | kept (L3) |
| K7 | `build{PHONE10} ok` | `build{PHONE10} ok` | `build{PHONE10} ok` | kept (L3) |
| K8 | `img sha256_{SHA16}` | `img sha256_{SHA16}` | `img sha256_{SHA16}` | kept |
| K9 | `wave2-2026-09-11T14:12:03Z` | `wave2-2026-09-11T14:12:03Z` | `wave2-2026-09-11T14:12:03Z` | kept |
| K10 | `orders-db-ro-1 up` | `orders-db-ro-1 up` | `orders-db-ro-1 up` | kept |
| K11 | `build-1234-5678-90 ok` | `build-1234-5678-90 ok` | `build-1234-5678-90 ok` | kept |
| K12 | `job-415-555-0132 ok` | `job-415-555-0132 ok` | `job-415-555-0132 ok` | kept |
| K13 | `pod web-5d8f9c7b6-x2x7q` | `pod web-5d8f9c7b6-x2x7q` | `pod web-5d8f9c7b6-x2x7q` | kept |
| K14 | `x86_64-linux-gnu` | `x86_64-linux-gnu` | `x86_64-linux-gnu` | kept |
| K15 | `eth0_up` | `eth0_up` | `eth0_up` | kept |
| K16 | `run_20261120101112_x ok` | `run_20261120101112_x ok` | `run_20261120101112_x ok` | kept |
| K17 | `self.local_cache = 1` | `self.local_cache = 1` | `self.local_cache = 1` | kept |
| K18 | `obj.internal_state` | `obj.internal_state` | `obj.internal_state` | kept |
| K19 | `nltk.corpus.reader` | `nltk.corpus.reader` | `nltk.corpus.reader` | kept |
| K20 | `acme.corporate.site` | `acme.corporate.site` | `acme.corporate.site` | kept |
| K21 | `ctx.local9` | `ctx.local9` | `ctx.local9` | kept |
| K22 | `vlan10.lan2 ok` | `vlan10.lan2 ok` | `vlan10.lan2 ok` | kept |
| K23 | `token AB12CDEFGHIJKLMNOPQ ok` | `token AB12CDEFGHIJKLMNOPQ ok` | `token AB12CDEFGHIJKLMNOPQ ok` | kept |
| K24 | `req ReqIdDE12345678901234 ok` | `req ReqIdDE12345678901234 ok` | `req ReqId<IBAN_1> ok` | over-mask L-D2 |
| K25 | `tag xDE00ABCDEFGHIJK ok` | `tag xDE00ABCDEFGHIJK ok` | `tag x<IBAN_1> ok` | over-mask L-D2 |
| K26 | `ts 1732095071000_x` | `ts 1732095071000_x` | `ts <PHONE_1>_x` | over-mask L-D10 |
| K27 | `uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe` | `uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe` | `uuid-ish <UUID_1>cafe` | over-mask L-D4 |
| K28 | `id {UUIDHEX} ok` | `id {UUIDHEX} ok` | `id {UUIDHEX} ok` | kept |
| K29 | `eth0 1500 9000` | `eth0 1500 9000` | `eth0 1500 9000` | kept |
| K30 | `ipv4 1500 1600` | `ipv4 1500 1600` | `ipv4 1500 1600` | kept |
| K31 | `vlan10 2001 2002` | `vlan10 2001 2002` | `vlan10 2001 2002` | kept |
| K32 | `node1 8080 9090` | `node1 8080 9090` | `node1 8080 9090` | kept |
| K33 | `PO12-3456-7890` | `PO12-3456-7890` | `PO12-3456-7890` | kept |
| K34 | `rtt 120 118 131 125ms` | `rtt <PHONE_1> 125ms` | `rtt <PHONE_1>ms` | over-mask L-D9 (3 of 4 masked today) |
| K35 | `backup_20-11-2026 done` | `backup_20-11-2026 done` | `backup_20-11-2026 done` | kept |
| K36 | `x{CARD}` | `x4242 <PHONE_1>` | `x4242 <PHONE_1>` | same (card glued: not G8) |
| K37 | `INV2026-0042-1234` | `INV2026-0042-1234` | `INV2026-0042-1234` | kept |
| K38 | `ISBN978-3-16-148410-0` | `ISBN978-3-16-148410-0` | `ISBN978-3-16-148410-0` | kept |
| K39 | `sha256-{SHA16}` | `sha256-{SHA16}` | `sha256-{SHA16}` | kept |
| K40 | `mac00-11-22-33-44-55` | `mac00-11-22-33-44-55` | `mac00-11-22-33-44-55` | kept |
| K41 | `ref hunter{SSN}` | `ref hunter{SSN}` | `ref hunter{SSN}` | kept (L-D11) |
| K42 | `password=hunter\nref hunter{SSN}` | `password=<SECRET_1>\nref <SECRET_1><SSN_1>` | `password=<SECRET_1>\nref <SECRET_1><SSN_1>` | same (the G7 boundary-class pin) |
| K43 | `python3.11.4.1` | `python3.11.4.1` | `python<IPV4_1>` | over-mask L-D8 |
| K44 | `python3.11.2.1` | `python3.11.2.1` | `python<IPV4_1>` | over-mask L-D8 |
| K45 | `jdk1.8.0.292` | `jdk1.8.0.292` | `jdk<IPV4_1>` | over-mask L-D8 |
| K46 | `node18.19.1.2` | `node18.19.1.2` | `node<IPV4_1>` | over-mask L-D8 |
| K47 | `libssl1.2.3.4` | `libssl1.2.3.4` | `libssl<IPV4_1>` | over-mask L-D8 |
| K48 | `rev1.2.3.4` | `rev1.2.3.4` | `rev<IPV4_1>` | over-mask L-D8 |
| K49 | `libc6_2.36.0.1_amd64.deb` | `libc6_2.36.0.1_amd64.deb` | `libc6_<IPV4_1>_amd64.deb` | over-mask L-D8 |
| K50 | `nginx_1.18.0.1-1_amd64.deb` | `nginx_1.18.0.1-1_amd64.deb` | `nginx_<IPV4_1>-1_amd64.deb` | over-mask L-D8 |
| K51 | `1.0.0.0a2` | `1.0.0.0a2` | `<IPV4_1>a2` | over-mask L-D8 |
| K52 | `2.0.1.0b3` | `2.0.1.0b3` | `<IPV4_1>b3` | over-mask L-D8 |
| K53 | `1.2.3.4rc1` | `1.2.3.4rc1` | `<IPV4_1>rc1` | over-mask L-D8 |
| K54 | `order_1234567890` | `order_1234567890` | `order_<PHONE_1>` | over-mask L-D10 |
| K55 | `user_1234567890` | `user_1234567890` | `user_<PHONE_1>` | over-mask L-D10 |
| K56 | `ts_1732095071` | `ts_1732095071` | `ts_<PHONE_1>` | over-mask L-D10 |
| K57 | `epoch_1732095071` | `epoch_1732095071` | `epoch_<PHONE_1>` | over-mask L-D10 |
| K58 | `trace_1732095071000` | `trace_1732095071000` | `trace_<PHONE_1>` | over-mask L-D10 |
| K59 | `snap_2026112010` | `snap_2026112010` | `snap_<PHONE_1>` | over-mask L-D10 |
| K60 | `b64url Zm9vYmFy_1234567890_YmF6` | `b64url Zm9vYmFy_1234567890_YmF6` | `b64url Zm9vYmFy_<PHONE_1>_YmF6` | over-mask L-D10 |
| K61 | `id_123456789012345678 ok` | `id_123456789012345678 ok` | `id_123456789012345678 ok` | kept |
| K62 | `ts+1000000000` | `ts+<PHONE_1>` | `ts<PHONE_1>` | same (the + moves inside) |
| K63 | `now+3600000000` | `now+<PHONE_1>` | `now<PHONE_1>` | same (the + moves inside) |
| K64 | `<TENANT_{PHONE10}>` | `<TENANT_{PHONE10}>` | `<TENANT_{PHONE10}>` | kept |
| K65 | `call {PHONE10} or {PHONE_P}` | `call <PHONE_1> or <PHONE_2>` | `call <PHONE_2> or <PHONE_1>` | same (numbering changes) |
| K66 | `blob aGVsbG8+aDE12abcdefghijk/x` | `blob aGVsbG8+aDE12abcdefghijk/x` | `blob aGVsbG8+a<IBAN_1>/x` | over-mask L-D2 |
| K67 | `known 1.2.3.4 and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | same (L-D1) |
| K68 | `rev 2-{SHA16}` | `rev 2-{SHA16}` | `rev 2-{SHA16}` | kept |
| K69 | `color #415555 and #0a0b0c` | `color #415555 and #0a0b0c` | `color #415555 and #0a0b0c` | kept |
| K70 | `sizes 1024 2048 4096ms` | `sizes 1024 2048 4096ms` | `sizes <PHONE_1>ms` | over-mask L-D9 |
| K71 | `took 100 200 300 400ms` | `took <PHONE_1> 400ms` | `took <PHONE_1>ms` | over-mask L-D9 (3 of 4 masked today) |
| K72 | `call 415-555-0132x123` | `call 415-555-0132x123` | `call <PHONE_1>x123` | closed (L-D9) |
| K73 | `ssn {SSN}a` | `ssn {SSN}a` | `ssn {SSN}a` | kept (L-D11: a stated limit, not a choice) |
| K74 | `card {CARD}x` | `card <PHONE_1> 4242x` | `card <PHONE_1> 4242x` | same (card glued: not G8) |

## 3. Files
Modify:
- `src/hadavin_sdk/guard/redact.py`: the IBAN, UUID, EC2-dashed and dotted IPV4 entries; three new PHONE entries (one directly
  before the main PHONE entry, two directly after it); a comment above each changed or new entry; one paragraph in the module
  docstring; `_JOINS` and `_joins()` beside `_ALNUM`; the `joins` parameter and docstring of `_replace_standalone`; the one call in
  `_Redactor.sweep` (1980). Exact text: section 4 and appendix D.
- `src/hadavin_sdk/guard/runmap.py` (codebase M3): import `_joins` (34, sorted after `_alias_keys`); `_sweep_held` (849) passes
  `_joins(placeholder)`; two sentences of the `enforce_map` docstring (699, 718). Decision: the held-back path follows the same
  rule as the first sweep, so one value never has two copy rules in one gate call. It is practically unreachable for a PHONE
  original (a held-back value is a piece of a placeholder name), so no test reaches it (stated, section 15).
- `tests/test_redact_idempotent_property.py:121` (codebase M3; it was :128 on 3c11364, :139 in the review): the oracle
  `raw_copies` calls `R._replace_standalone(free, original, "\x00", R._joins(placeholder))`, so it judges a copy by the rule
  production uses. Without it the oracle calls a letter-glued phone copy "not raw" while production replaces it, and could not
  see a regression of G8b.
- `tests/test_redact_g3_port.py:56-59` (codebase M5): re-pointed at a copy only the sweep can reach after G8 (exact text in
  appendix E): `redact("tenant_id=acme42 and x_acme42_0")` gives `tenant_id=<TENANT_1> and x_<TENANT_1>_0`, actions 2 (traced on
  3c11364 base, v2 and v2 + G4c: the same). The old UUID input still passes after G8 (2 actions) but both are pattern masks then.
- `SECURITY.md` (the stated-limits list) and `CHANGELOG.md` (Unreleased, one "Redaction: values glued to a word (G8)" item): the
  text of section 13, through the security wording review.
Create:
- `tests/g8_cases.py` (appendix A, complete): the 80 rows with their base, expected and G4c outputs, the leak rule `leak()`, the
  74 must-keep rows, the two full-stop rows, the `G4C_MERGED` flag, and the step-0 check (`python -m tests.g8_cases`).
- `tests/test_redact_glued_rest.py` (appendix B, complete): the tests of section 7.
- `tests/g8_mutants.py` (appendix C, complete): the 28 mutants, run by `tools/mutation_runner.py`.
- `handover/core-c/evidence/G8-1.md`: the raw output of every command of section 8 (step 0, fail-before, each phase, full
  suite, perf, mutants, ruff).
Where the step-0 outputs are stored: in `tests/g8_cases.py` itself (column `now` of `ROWS`, `now` of `MUST_KEEP`), recorded on
3c11364 by the drafter; phase 0 re-checks them on the build base with `python -m tests.g8_cases` (exit 0, "0 differ") and pastes
the output into evidence/G8-1.md. There is no separate fixture file and no hash: v1's `test_g8_rows_hash` is replaced by
`test_row_counts_are_pinned` plus the per-row literal expectations (a hash against a value that did not yet exist could not fail
before; the literals can).
Not changed (decided): the G7 test `tests/test_redact_settle_loop.py::test_boundary_class_is_over_masked_fail_safe_and_pinned`
(918-930) stays byte-identical (v1's "one test changes" section is gone: v2 does not mask `hunter123-45-6789` in pass 1;
measured, section 2.3, and green in the full run of section 9); the G7 ticket's "Boundary class" stated limit stays as written
(its example still over-masks); no G7 ticket edit. textnorm, defaults.py, `_countable` and the counters, `_LABELS`, `_sub_glued`
(EMAIL only), STORED_KINDS: unchanged (no new kind; new originals fit `runmap._GRAMMAR` IPV4 / PHONE; UUID and IBAN are never
stored).
Not added to the G7 / G4 property corpus: g8_cases.py is its own data; `EXPECTED_INPUTS` of tests/test_redact_idempotent_property.py
is unchanged. G4 v3 also edits that file (base64 rows); the two edits touch different lines (G8: line 121 only), so the merge is
textual only.

## 4. Design (exact; the regex text is copied from the measured prototype)
### 4.1 PATTERNS, in order (flags: none unless the pattern starts with `(?i)`; group count stated per entry)
Entry 1, IBAN (replaces redact.py:266-274). Preceded by the EMAIL tuple (ending `...\.[A-Za-z]{2,}(?![A-Za-z])"` / `),` /
`),`) and the IBAN comment, to which three lines are added; followed by the UUID entry. No group.
```python
    # evidence token like `AB12CDEF...` is NOT clobbered — only a genuine IBAN country prefix fires.
    # Glued (G8): not after an ASCII letter or digit, except a lower-case letter right before the country code (camelCase,
    # `_NOT_IN_WORD`), and not followed by a letter or digit (one would join the BBAN). So `iban_DE89...`, `xDE89...` and
    # `DE89..._x` are masked with the glued text outside; `7DE89...` and `XDE89...` are not (ticket G8, limit L4).
    (
        "IBAN",
        re.compile(
            _NOT_IN_WORD
            + r"(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
            r"|GI|GL|GR|GT|HN|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|LY|MC|MD|ME|MK|MN|MR|MT"
            r"|MU|NI|NL|NO|PK|PL|PS|PT|QA|RO|RS|RU|SA|SC|SD|SE|SI|SK|SM|SO|ST|SV|TL|TN|TR|UA|VA|VG|XK)"
            r"\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])"
        ),
    ),
```
`_NOT_IN_WORD` is the module's own (redact.py:68): `(?:(?<![A-Za-z0-9])|(?-i:(?<=[a-z])(?=[A-Z])))`.

Entry 2, UUID (replaces 275-280). Preceded by entry 1; followed by the "Bank details" comment and the BANKCODE tuple. No group.
`_UUID_SHAPE` (738) is taken from this entry and follows automatically (`_has_bank_word` now also removes a glued UUID).
```python
    # No word boundary (G8): the 8-4-4-4-12 run is found inside a longer token (`pod_<uuid>_0`, `x<uuid>`, `<uuid>9`) and
    # the glued text stays outside. An 8-4-4-4-16 hex id gives `<UUID_1>` and its last 4 hex digits (accepted, L-D4).
    (
        "UUID",
        re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        ),
    ),
```
Entries 3 and 4, IPV4 (replace 374-377). Preceded by `("ACCOUNTID", re.compile(r"\b\d{12}\b")),`; the pod-DNS entry between
them is unchanged; followed by the IPv6 comment block (`# IPv6 — we redact IPv4, ...`). EC2: one group (the dashed address),
as today; dotted: no group.
```python
    # An EC2 private DNS name carries the address with dashes: ip-10-0-3-22(.region.compute.internal).
    # A letter or `_` may follow the last group (`ip-10-0-3-22a`, G8); a digit may not.
    ("IPV4", re.compile(r"\b(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})(?![0-9])")),
    ("IPV4", re.compile(r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),  # k8s pod DNS
    # Dotted quad (G8): not inside a digit run (`7192.0.2.10`, `2026.11.20.10`: limit L1) and not after a lone `v` / `V`
    # (`v1.2.3.4` is a version, L-D1). A letter or `_` on either side is glued text, left outside (`node_<IPV4_1>`,
    # `<IPV4_1>a`); a four-part version glued to a word (`python3.11.4.1`) is masked too (L-D8).
    ("IPV4", re.compile(r"(?<![0-9])(?<!(?<![A-Za-z])[vV])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")),
```
Entries 5 to 7, PHONE. Preceded by `("CREDITCARD", re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")),` and the PHONE comment
block (472-490, unchanged, ending `#     still masked.`). Entry 5 is NEW and sits directly BEFORE the main PHONE tuple (491-497,
unchanged); entries 6 and 7 are NEW and sit directly AFTER it; the tuple after entry 7 is the SECRET `authorization` entry
(preceded by its comment `# password=..., secret: ...`). Entries 5 and 6: no group (the whole match is the value). Entry 7:
`(?i)`, group 1 is the value (the keyword stays in the text).
```python
    #     still masked.
    # (G8) Glued to a letter or `_`, BEFORE the main entry (which would leave `<PHONE_1> 1234a`): a number that starts
    # with `+` may follow a letter or `_` (`x+1 415-555-0132`); one without `+` starts where the main entry may, holds at
    # least 10 digits and no run of 5 (`415-555-0132x123`; not `rev 2-3851007894abcdef`, a hash). Either may END before a
    # letter or `_`, never before a digit or `.`. `eth0 1500 9000`, `PO12-3456-7890`, `hunter123-45-6789` stay as they were.
    (
        "PHONE",
        re.compile(
            r"(?:(?<![\w.\-])(?=(?:[ \-]?\d){10})(?![\d \-]{0,12}\d{5})|(?<![0-9.\-])(?=\+))(?!\d{4}-\d\d-\d\d)"
            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
            r"\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![0-9.])"
        ),
    ),
    (
        "PHONE",
        re.compile(
            r"(?<![\w.\-])(?!\d{4}-\d\d-\d\d)"
            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
            r"\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![\w.])"
        ),
    ),
    # (G8) A contiguous 10 to 16 digit number with `_` on one side and no letter or digit on the other (`tel_4155550132`,
    # `4155550132_x`); not a compact timestamp; `>` ends no phone (a placeholder `<TENANT_4155550132>`). `sha256_3851...ab`
    # stays (a letter after); `order_1234567890` is masked (L-D10). Then a number glued straight to a phone word.
    (
        "PHONE",
        re.compile(
            r"(?<![0-9A-Za-z.\-+])(?:(?<=_)|(?=\d{10,16}_))"
            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
            r"\d{10,16}(?![0-9A-Za-z.>])"
        ),
    ),
    ("PHONE", re.compile(r"(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\d{10,16})(?![0-9a-z.])")),
    # password=..., secret: ..., aws_secret_access_key="...": the value after a credential-ish key.
```
Entry 5 read in parts (codebase M1, taken, plus one guard): the start is EITHER branch A, the main entry's own start
`(?<![\w.\-])` (no letter, digit, `_`, `.` or `-` before) with at least 10 digits ahead (`(?=(?:[ \-]?\d){10})`, single separators)
and no run of 5 digits within the next 17 characters (`(?![\d \-]{0,12}\d{5})`: phone groups are 1 to 4 digits; a hash is not);
OR branch B, a `+` with no digit, `.` or `-` before (a letter or `_` may stand before a `+`-led number only). Then the main
entry's date guard, compact-timestamp guard and body, and the relaxed end `(?![0-9.])` (a letter or `_` may follow, a digit or
`.` may not). The 5-digit guard is the drafter's addition to M1: with the 10-digit rule alone, `rev 2-3851007894abcdef` became
`rev <PHONE_1>abcdef` (measured), the hash shape the PHONE comment's 2026-10-02 CI incident is about. v1's `(?=\+|\d{1,4}[ \-]\d)`
lookahead is gone (branch A's two rules imply a separator; branch B starts with `+`). No probe row needs branch A (every closed
phone row with a letter has a `+`): branch A closes `415-555-0132x123` and costs the rows of L-D9; the lead may drop it.
Cost bound: every repeat is bounded (`{10}`, `{0,12}`, `{8,14}`, `{10,16}`); the start guards allow at most one start per digit.

### 4.2 The sweep (G8b)
redact.py, replacing `_ALNUM` (2164) to the end of `_replace_standalone`'s signature and docstring first line (2167-2168), and the
test in its loop:
```python
_ALNUM = frozenset(string.ascii_letters + string.digits)
# The characters that make a touched copy part of a longer token, per kind (G8b). A PHONE value glued to a letter or `_`
# is the number with a word beside it (the patterns read it so); a digit beside it makes another number. Every other kind:
# `_ALNUM` (a host name, a tenant, an account id are made of letters and digits, so a letter beside one may be part of it).
_JOINS = {"PHONE": frozenset(string.digits)}


def _joins(placeholder: str) -> frozenset[str]:
    """The characters that, touching a copy of a known value, make it part of a longer token (ticket G8): a digit for
    a phone number (a letter or `_` beside it is a word glued on, as the patterns read it); a letter or digit for
    every other kind."""
    return _JOINS.get(_kind(placeholder), _ALNUM)


def _replace_standalone(segment: str, original: str, placeholder: str, joins: frozenset[str] = _ALNUM) -> str:
    """Replace `original` where no character of `joins` touches it (default `_ALNUM`: an ASCII letter or digit; callers
    pass `_joins(placeholder)`). A plain scan: a compiled pattern (or an
    ...                                    (rest of the docstring and body unchanged, except:)
        if before in joins or after in joins:
```
Callers: `_Redactor.sweep` (redact.py:1980) `segment = _replace_standalone(segment, original, placeholder, _joins(placeholder))`;
`runmap._sweep_held` (runmap.py:849) `parts[i] = _replace_standalone(segment, spelling, placeholder, _joins(placeholder))`; the
property oracle (section 3). `enforce_map` and the gate (`first.sweep`, runmap.py:758) inherit it through `_Redactor.sweep`:
a letter-glued copy of a known phone number in model-visible text is rewritten (intended; test in section 7).
Codebase M4 / readiness M4 taken: v1's `_JOINS` entries for IPV4 and UUID are dropped. After G8a no input reaches them: every
glued UUID is the pattern's own match, and the one IPv4 copy they changed was `v1.2.3.4` with `1.2.3.4` known (v1 gave
`v<IPV4_1>`, against L-D1). The 80 rows and the must-keep rows give the same output with or without them (measured: `v1proto`
had them, `v2proto` has not, 80 rows identical). The short / common value rule of `_sweep` is unchanged.

### 4.3 Module docstring (redact.py, a new paragraph after the "What this is not" paragraph, before the closing `"""`)
```
A value glued to a letter or `_` is masked with the glued text left outside the placeholder (`node_<IPV4_1>`, `<UUID_1>x`):
an e-mail address, an IPv4 address, an IBAN, a UUID, a phone number that starts with `+` or is written in groups with at
least 10 digits, and a contiguous one beside `_` or straight after a phone word (G8). A contiguous digit run glued to a
letter is not read as a phone number (hashes and identifiers), and a digit glued before an address or an IBAN is not read
as one. A copy of a known phone number is swept where a letter or `_` touches it (not a digit).
```
runmap.py `enforce_map` docstring: line 699 `where no ASCII letter or digit touches it.` becomes `where no ASCII letter or digit
touches it (a PHONE value: where no digit does; `redact._joins`, ticket G8).`; line 718 `... left where an ASCII letter or digit
touches it and` becomes `... left where an ASCII letter or digit (for a PHONE value: a digit) touches it and`.

### 4.4 What stays as it is
`_sub_glued` stays EMAIL only: the new boundaries are character classes, and the rows where two values touch (74, 75, 77) are
masked by plain `sub`; rows 13 and 76 (two values of one kind with no character between) cannot be split by any boundary rule
(L2, L5). The settle loop is untouched: G8 changes what pass 1 finds. Placeholders: entry 6 refuses `>` after and every new
start refuses a digit before, so a placeholder number is never re-masked (`<TENANT_4155550132>` kept, K64; `_countable` lets a
pre-seeded number reach 18 digits, which no new entry matches whole).

### 4.5 HOSTNAME under G4c (codebase M4, readiness B4; measured with G4 v3's regex through `redact()`)
G8 changes no host row, before or after G4c (v2base vs v2proto and v2base_g4c vs v2proto_g4c: identical host outputs). G4c changes
rows 60, 61, 62 and 66 (output only; no leak before or after: `x <HOSTNAME_1>.internal9 y` becomes `x <HOSTNAME_1> y`) and closes
rows 64 and 71; rows 67-70 and 78-80 stay leaks under G4c (limit L6). Hence appendix A's third column and the `G4C_MERGED` flag.
No G8 must-keep row changes under G4c (74 of 74 identical on v2proto and v2proto_g4c). The G8c variant of v1 (a digit or `_`
after a G4c tail suffix) is not re-measured and stays a fallback of L-D3.

## 5. Decisions made (drafter)
- The glued text stays outside the placeholder (as the e-mail fix): the map holds the value's own grammar, `runmap._GRAMMAR`
  accepts it, and `restore_text` gives back the input exactly (test `test_restore_round_trip_ipv4_and_phone`, 35 rows, green).
- No new kind; no change to `_LABELS`, counters, `_countable` or the stored kinds.
- HOSTNAME: no G8 code (section 4.5).
- A contiguous phone number glued to a letter stays unmasked in pass 1 (L3; the hash guard), but a copy of a known one is swept
  (G8b): it is the only fix for row 31 and the gate test of section 7.
- Letter-glued formatted digit groups without `+` (`INV2026-0042-1234`, `ISBN978-...`, `PO12-...`, `mac00-11-...`,
  `sha256-3851...`, `eth0 1500 9000`, `hunter123-45-6789`) are NOT masked: branch B needs a `+`, branch A no letter before
  (codebase M1). Kept rows K29-K33, K37-K41.

## 6. Decisions for the lead (build default first; each with fallback and consequence)
| id | question | default (built unless the lead says otherwise) | consequence of the default | fallback | consequence of the fallback |
|---|---|---|---|---|---|
| L-D1 | IPv4 after a lone `v` (`v1.2.3.4`) | not masked (a version) | `release v1.2.3.4` kept (K1, K2); a real address written `v192.0.2.10` is not masked, and with IPV4 out of `_JOINS` not even when the same address is known (K67: `known <IPV4_1> and v1.2.3.4`) | mask it (drop the `(?<!(?<![A-Za-z])[vV])` look-behind) | every `vN.N.N.N` becomes `v<IPV4_n>` (K1, K2 change; mutant V4 shows it) |
| L-D2 | IBAN with a letter glued before | `_` or a lower-case letter before the country code is masked (camelCase) | over-masks K24 `ReqId<IBAN_1>`, K25 `tag x<IBAN_1>`, K66 base64 `a<IBAN_1>`; an over-masked IBAN is a SECRET kind, so every copy of that token is swept in the call | start `(?<![A-Za-z0-9])` only | rows 38, 39, 45 become limits (`xDE89...`, `ibanDE89...`, `xGB82...`); K24, K25, K66 kept (by reading, not run) |
| L-D3 | a letter, digit or `_` glued AFTER a host's private suffix (rows 67-70, 78-80) | stated limit L6 | the labels of `db01.prod.corpa` stay readable | G8c after G4c is merged: `(?![^\W\d_]|-)` in place of G4c's tail `(?![\w-])` | closes 68, 69; masks code (`self.corp_id` -> `<H>_id`, `cfg.lan_mode`, `vlan10.lan2`, `data.corp_2026.csv`; v1's measurement, NOT RE-MEASURED with G4 v3) |
| L-D4 | UUID with hex glued after (`...174000a`, 8-4-4-4-16 ids) | masked, the extra hex left outside | K27 `uuid-ish <UUID_1>cafe` (an id that is not a UUID is masked in part; its last 4 hex stay) | end guard `(?![0-9A-Fa-f])` | rows 47, 48 become limits, and by reading rows 14 (`{UUID}{IP1}`: a digit follows) and 77 (two UUIDs glued) too; K27 kept (not run) |
| L-D5 | the G7 pinned "boundary class" test | nothing to decide any more: v2 leaves it byte-identical (measured, K42) | the G7 ticket's "Boundary class" limit and its example stay true | (v1's "builder picks" is gone) | none |
| L-D6 | PHONE keyword list (entry 7) | `tel`, `phone`, `mobile`, `cell`, `fax` | `tel4155550132` masked (row 28); `x4155550132` stays (L3) | cut entry 7 | row 28 becomes a limit |
| L-D7 | build order while G4 is NOT READY | G8a + G8b first; rows 64 and 71 are strict xfails naming G4c (`G4C_MERGED = False`) | G8 lands without waiting; the G4c builder flips `G4C_MERGED` in the G4c commit, which turns 64 / 71 into ordinary tests and switches rows 60-62 and 66 to the G4c column | G4c first, then G8 with `G4C_MERGED = True` from the start | G8 waits for G4 v4's readiness |
| L-D8 | four-part dotted versions and IPv4-shaped ids glued to a word or `_` (and letter-glued digit groups) | masked (fail safe): K43-K53 (`python<IPV4_1>`, `jdk<IPV4_1>`, `nginx_<IPV4_1>-1_amd64.deb`, `<IPV4_1>rc1`, `<IPV4_1>a2`); letter-glued digit groups (`INV2026-0042-1234`, ISBN, MAC, `PO12-...`) are KEPT by entry 5's design (K33, K37-K40) | version evidence is lost in logs that print `python3.11.4.1`-style strings; the original is stored as IPV4 and restorable | (a) a letter directly before refuses the dotted match (start `(?<![0-9A-Za-z])` plus the `v` rule) | (a) rows 7, 8, 11, 74 become limits (by reading, not run); K43-K48 kept; K49-K53 still masked (`_` before or a letter after) |
| L-D9 | a phone without `+`, in groups, with a letter or `_` after (entry 5 branch A) | masked when it has at least 10 digits and no run of 5 | closes K72 `call <PHONE_1>x123` (an extension); over-masks K70 `sizes <PHONE_1>ms` and grows K34 / K71 (`rtt <PHONE_1>ms`, `took <PHONE_1>ms`: 3 of 4 numbers were masked today) | drop branch A (entry 5 = `+`-led only) | K72 stays readable as today; K34, K70, K71 as today; the 80-row counts do not change (no probe row uses branch A; by reading, mutant P2 / P3 rows) |
| L-D10 | a contiguous 10-16 digit run glued to `_` (entry 6) | masked | closes rows 26, 29, 30; over-masks ids and epochs after a word and `_`: K26, K54-K60 (`order_<PHONE_1>`, `ts_<PHONE_1>`, `trace_<PHONE_1>`, a base64url `_<PHONE_1>_`); each is stored as PHONE and restorable | cut entry 6, and let entry 7 take `tel_` / `phone_` (`(?:tel|phone|mobile|cell|fax)_?`) | rows 26 and 30 become limits; row 29 stays closed by entry 7 (by reading, not run); K26, K54-K60 kept |
| L-D11 | an SSN-shaped value glued to a letter or `_` | v2 does NOT take it as PHONE (9 digits fail branch A; branch B needs `+`): `ssn 123-45-6789a`, `x123-45-6789`, `ssn_123-...` stay readable as today (limit L8, K73); `x+123-45-6789` is SSN (the SSN entry runs first); only `+123-45-6789x` becomes `<PHONE_1>x` and is stored as PHONE | an SSN-shaped `+` number glued to a letter is written to the run map at rest and restorable as PHONE (the map's policy says an SSN is never stored) | the SSN-safe lookahead `(?!\+?\d{3}-\d{2}-\d{4}(?!\d))` after entry 5's start group | `+123-45-6789x` stays readable as today (not run) |

## 7. Acceptance tests (appendix B; data appendix A; public names, plus `_has_bank_word` in one test)
| test | rows | asserts | red on the base (fail-before, measured on 3c11364) |
|---|---|---|---|
| `test_glued_rows_are_masked` | 49 (47 closed + rows 21, 22) | output == expected in `redact`, `redact_many(...)[0][0]`, `redact_text`; no leak | 49: row2 row3 row4 row5 row7 row8 row9 row11 row12 row14 row15 row16 row18 row19 row20 row21 row22 row23 row24 row26 row28 row29 row30 row31 row32 row36 row37 row38 row39 row41 row42 row44 row45 row47 row48 row49 row50 row51 row52 row53 row54 row55 row56 row57 row58 row72 row73 row74 row77 |
| `test_glued_character_stays_outside_the_placeholder` | 17: 2-5, 7-9, 18-20, 36-37, 47-51 | output == text with the value replaced by its own placeholder | 17: all of them |
| `test_controls_and_untouched_rows_keep_their_output` | 16 unchanged rows | output == expected and == `now` (host rows: `after_g4c` once `G4C_MERGED`) | 0 |
| `test_limit_rows_are_pinned` | 13: 10, 13, 25, 27, 40, 76, 67-70, 78-80 | the DESIRED behaviour (no leak), `xfail(strict=True)` with the limit id | 0 red; 13 xfailed (base and after) |
| `test_host_glued_before_is_closed_by_g4c` | 64, 71 | `x <HOSTNAME_1> y`; strict xfail naming G4c while `G4C_MERGED` is False | 0 red; 2 xfailed |
| `test_must_keep_rows` | 74 | output == `after`; a kept row has an empty map | 30: K24 K25 K26 K27 K34 K43 K44 K45 K46 K47 K48 K49 K50 K51 K52 K53 K54 K55 K56 K57 K58 K59 K60 K62 K63 K65 K66 K70 K71 K72 |
| `test_phone_before_a_full_stop_is_a_stated_limit` | F1, F2 | unchanged (L7) | 0 |
| `test_second_call_changes_nothing` | 80 | a second `redact_text` changes neither text nor map | 0 |
| `test_untrusted_matches_redact_text` | 80 | `redact_untrusted == redact_text` | 0 |
| `test_restore_round_trip_ipv4_and_phone` | 35 (IPv4 and phone rows without a UUID) | `restore_text(out, m) == text` | 0 (trivial on the base for the unmasked rows) |
| `test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only` | row 31; seeded `a x{PHONE10} and a{PHONE10}0b`; `known {IP1} and v{IP1}`; seeded `printer7` (HOSTNAME) and `acme42` (TENANT) copies glued to a letter | phone letter copy replaced, digit copy not; IPV4, HOSTNAME, TENANT letter copies not replaced | 1 (first line `SWEEP phone letter`) |
| `test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone` | `enforce_map("build" + PHONE10, {"<PHONE_1>": PHONE10})` == `build<PHONE_1>`; `x...` + `_` replaced; `7...` not; TENANT `acme42x` not | (codebase M3, the gate-level test) | 1 |
| `test_bank_word_check_ignores_a_glued_uuid` | `_has_bank_word("id x123e4567-e89b-12d3-a456-aba123456789")` (built from parts) is False | was True on the base | 1 |
| `test_row_counts_are_pinned` | 80 rows, 74 must-keep, 2 full-stop, class counts 47 / 16 / 13 / 2 / 2, limit ids | | 0 |
| `test_glued_patterns_are_linear` (perf) | 6 hostile texts | section 10 | not run on the base |
Fail-before total (measured: appendix A + B copied into the 3c11364 archive, `pytest -q -m "not perf" tests/test_redact_glued_rest.py`):
99 failed, 258 passed, 15 xfailed, 6 deselected. With v2: 357 passed, 15 xfailed, 6 deselected (measured on `v2proto`).
(The sweep and gate tests were run with an earlier wording of their assertion messages; the inputs and expected strings are
the ones in appendix B.)

## 8. Build order, phases and commands
Common prefix `uv run --all-extras --group test`; run from the repo root of the builder's worktree. "Green" = exactly the named
result. Dependency: G7 rounds 3 to 5 are merged (a5f55addc); a G7 round 6, if ordered, lands first (both edit redact.py; G8 edits
no G7 test). G4 (v3 / v4, NOT READY): independent (L-D7 default); textual overlap only in redact.py (G4 edits `_LABELS`,
HOSTNAME and the code near `_replace_standalone`) and tests/test_redact_idempotent_property.py; whichever lands second rebases.
G4 v3 says tests/test_redact_settle_loop.py must stay green unchanged: G8 v2 does not edit it, so there is no waiver to ask for.
Phase 0, no code. (a) Base sha recorded; `git archive <base> | tar -x -C /tmp/g8-base` (no worktree switch). (b) Copy appendix A
to /tmp/g8-base/tests/g8_cases.py; `cd /tmp/g8-base && uv run --all-extras --group test python -m tests.g8_cases`. Green: exit
0, last line `0 differ` (the step-0 record; paste the output). Any `BAD` line: STOP and report (the base moved). (c) Fail-before:
copy appendix B too; `uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not perf" tests/test_redact_glued_rest.py -rfEX`.
Green: `99 failed, 258 passed, 6 deselected, 15 xfailed`, the failing ids exactly those of section 7. (d) Full suite of the base
(`pytest -q -p no:cacheprovider -m "not perf and not live" -n 2 tests`), failures recorded.
Phase 1, G8a (redact.py PATTERNS and comments, section 4.1). Run `pytest -q -m "not perf" tests/test_redact_glued_rest.py`.
Expected red (by reading, not run): `test_glued_rows_are_masked[row31]`, `test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only`,
`test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone`; everything else as in the final state.
Phase 2, G8b (`_JOINS`, `_joins`, `_replace_standalone`, the sweep call, runmap.py, the property oracle, the g3 port re-point,
the docstrings of 4.3). Run `pytest -q -m "not perf" tests/test_redact_glued_rest.py tests/test_redact_g3_port.py
tests/test_redact_idempotent_property.py tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py
tests/warden_port -n 2`. Green: all pass; the G8 file `357 passed, 15 xfailed`.
Phase 3, checks. `ruff format` and `ruff check` on the changed files (appendix A-C were written to pass `ruff check`; `ruff format`
reflows four of them: run it, then re-run phase 2). Full suite: `pytest -q -p no:cacheprovider -m "not perf and not live" -n 2 tests`
(this covers the reviewers' list: the 73 files that name the redactor, `grep -rlE "guard\.redact|guard\.runmap|from hadavin_sdk\.guard import|redact_text" tests --include='test_*.py'`,
6 of them in tests/warden_port, and test_k1b_redaction.py, test_k1b_bundle.py, test_k1b_replay.py, test_s6_approvals.py,
test_s3_gate.py, test_executor.py, test_p1b_backends.py, test_p4_secrets.py, test_p4b_secrets.py, test_evidence_decomposed.py).
Green: the base's failures of phase 0 (d) and nothing else. Perf: `pytest -q -p no:cacheprovider -p no:xdist -m perf
tests/test_redact_glued_rest.py tests/test_k5_perf.py tests/test_redact_fold_budget.py`. Green: all pass.
Phase 4, mutants: `uv run --all-extras --group test python tests/g8_mutants.py` (runner: tools/mutation_runner.py, judge
src/hadavin_sdk/testing/mutation.py). Green: `28 of 28 good`. Then `python tests/redact_mutants.py`, `python tests/p1d_a_mutants.py`,
`python tests/gate_mutants.py`, `python tests/stage_mutants.py`, `python tests/textnorm_mutants.py`: no new BAD (their anchors are not
on G8 lines; codebase M5).
Phase 5, documents: SECURITY.md and CHANGELOG.md (section 13), evidence/G8-1.md with the raw output of phases 0-4.
Owner: core-c (guard/redact.py, guard/runmap.py). No core-a / core-b file, no SPINE file.

## 9. The drafter's runs (3c11364 unless said)
- Probe: the 80 rows on v2base (62 leak), v1proto (15 leak), v2proto (15 leak; outputs byte-identical to v1proto), with G4 v3's
  host regexes (section 4.5).
- Traces: section 2.3; must-keep 74 rows on v2base, v2proto and v2proto_g4c.
- The new test file: fail-before on v2base (99 failed) and green on v2proto (357 passed, 15 xfailed).
- Full suite of v2proto (G8a + G8b, without the comment, docstring, oracle and g3 edits; appendix A and B not in it):
  `pytest -q -p no:cacheprovider -m "not perf and not live" -n 2 tests`: 4 failed, 14,109 passed, 562 skipped, 10 xfailed
  (13 min 07 s). The four: `test_ci_gitleaks_scope.py::test_the_gitleaks_config_has_only_narrow_path_allowlists` and
  `test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` (fail on the base archive too, run alone),
  `test_repo_rules.py::test_licences_are_proprietary` (calls git; the archive has no `.git`),
  `test_runmap_enforce_map.py::test_m_new_1_enforce_map_has_the_redactors_time_budget` (passes alone and as its whole file on
  both base and v2 serially; failed under `-n 2` in v1's base run on 459d8da too: order-dependent, not G8's; to be confirmed by
  phase 0 (d)). Everything else is green: the G7 boundary test, the property test (old oracle), tests/test_redact_g3_port.py
  (old input, still 2 actions), tests/test_redact_fold_budget.py (`len(PATTERNS)` is read live, not pinned: no red, contrary to G4
  v3:631's wording), tests/warden_port, tests/test_text_parts_together.py, test_p1d_a_*.
- The base full suite was stopped at about 80 percent (coordinator: box load 10.5), so there is no base-vs-v2 diff of failure
  lists; the four failures above are classified one by one instead.
- NOT RUN: the 28 mutants of appendix C (their `expect` rows are the drafter's reading of the first failing row), the
  perf tests, the edited oracle and the re-pointed g3 test inside the suite (the g3 input was traced: 2 actions on base, v2, v2+G4c),
  `ruff format`, the G4 v3 property corpus with G8 (G4 is not built; codebase M5), the approval-card paths beyond the full suite.

## 10. Cost (NOT RE-MEASURED on 3c11364 or a5f55addc)
The coordinator stopped new batches (box load 10.5 on 4 cores; a timing on that box would be noise). v1's numbers stand as v1
measured them: on 0d93f20 (before G7 rounds 3 to 5), `redact()` only, CPU seconds by `time.thread_time` (the calling thread's
CPU clock), best of 3, 262,144 characters: `1.` 0.83-0.91 -> 0.92-0.93; `x1 2 3 ...` 0.60-0.76 -> 0.68-0.79; `_4155550132`
0.65-0.74 -> 0.60-0.72; `deadbeef-dead-beef-dead-` 0.69-0.77 -> 0.75-0.98; `aDE89` + 40 `A` 0.44-0.47 -> 0.45-0.52; 65,536 to
262,144 ratio 3.2-4.4. v2's entry 5 differs from v1's (two bounded lookaheads instead of one), so even these are not v2's.
Correction of v1 (readiness M5): FOUR entries change (IBAN, UUID, EC2 IPV4, dotted IPV4) and THREE PHONE entries are added
(PATTERNS grows from N to N+3); the sweep adds one dict lookup per swept copy.
To measure (phase 3, on a quiet box, results in evidence): the perf test of appendix B (`time.thread_time`, best of 3, six texts,
65,536 and 262,144 characters, both `redact()`); and once by hand the same six texts through `runmap.redact_text(t, RunMap())`
on the base and on G8, recorded side by side. Bounds in the test: ratio at most 6.0 (widened from v1's 5.0; 4x the text) and the
262,144-character call under 3.0 s; `REDACT_BUDGET_S` (defaults.py) is the hard stop above both. v1's "262,144 cap" sentence is
dropped (readiness N1).
Builder effort: half a day (the data, tests and mutants are given; most time is the runs).

## 11. Stated limits after G8 (each pinned by a strict xfail or a must-keep / full-stop row)
- L1 A digit glued before a dotted IPv4 (`7192.0.2.10`): row 10; `2026.11.20.10` must stay (K3).
- L2 Two dotted IPv4s glued with nothing between: row 13.
- L3 A contiguous phone number glued to a letter (`4155550132a`, `x4155550132`): rows 25, 27 (the hash guard; masked when a
  clean copy of the same number is in the call, or the number is a known value at the gate: G8b).
- L4 A digit or upper-case letter before an IBAN (`7DE89...`, `XDE89...`): row 40.
- L5 Two IBANs glued: row 76.
- L6 A letter, digit or `_` glued after a host's private suffix: rows 67-70, 78-80 (L-D3), also under G4c.
- L7 A phone number before a full stop (`call 415-555-0132.`): not glued, found on the way, unchanged; F1, F2.
- L8 An SSN-shaped value glued to a letter or `_` (`ssn 123-45-6789a`): readable as today (K73; L-D11).
- L9 A grouped card number glued to a letter (`x4242 4242 4242 4242`): one group readable, as today; the rest is PHONE (K36, K74).
- Over-masks accepted by decision (fail safe, evidence lost, not a leak): L-D2 (K24, K25, K66), L-D4 (K27), L-D8 (K43-K53),
  L-D9 (K34, K70, K71), L-D10 (K26, K54-K60).
- Unchanged from today: a 32-hex UUID without dashes is not a UUID shape (K28); the sweep's rule for short and common values.

## 12. Risks
- Over-masking classes are listed with their decisions (section 6); an over-masked IBAN-shaped token is swept in every copy.
- Label: a `+`-led SSN-shaped number glued to a letter is stored as PHONE (L-D11); a value masked as PHONE / IPV4 out of a version
  or an epoch is written to the run map at rest and restorable.
- Numbering: in a text with a contiguous and a `+`-led number, the `+`-led one is now `<PHONE_1>` (K65).
- The gate: a known phone number glued to a word in model-visible text is rewritten (`build<PHONE_1>`), intended.
- G4: rows 60-62 and 66 change under G4c (output only); the flag handles it. Textual conflicts in redact.py and the property test.
- Non-ASCII glue (a Cyrillic letter or a full-width digit beside an IP) goes through the fold scan first; not probed.

## 13. For SECURITY wording (proposed text for SECURITY.md's stated-limits list and the CHANGELOG item; through the security wording review)
"Values glued to other text. An IPv4 address, an IBAN, a UUID and a phone number are masked when a letter or an underscore is
glued to them (`node_10.0.0.1`, `id x<uuid>`), the glued text left in place. Not masked, by design: a phone number written as
one run of digits with a letter directly before or after it (`x4155550132`, `4155550132a`), because hashes and identifiers have
that shape (it is masked when the same number also appears on its own in the same text); an IPv4 address or an IBAN with a digit
glued directly before it; two addresses or two IBANs written together with nothing between; a host name with a letter, digit or
underscore glued after its private suffix (`db01.prod.corpa`); a US Social Security number with a letter glued to it; a phone
number directly followed by a full stop. To be safe, some things that only look like these values are masked: four-part version
numbers glued to a word (`python3.11.4.1`), long digit runs after an underscore (`order_1234567890`), spaced number groups
followed by a unit (`sizes 1024 2048 4096ms`), and short tokens that start with a country code and two digits (`ReqIdDE12...`).
Masked numbers and addresses are kept in the run's map and can be restored like any other masked value."

## 14. What is NOT verified
- Every row on a5f55addc (measured on 3c11364; PATTERNS and the sweep are textually identical, section 0).
- The cost (section 10), the mutants, the perf tests, `ruff format`, the edited oracle and g3 test inside a suite run.
- The fallbacks of section 6 marked "by reading" or "not run".
- G4 v4 (not read); G4 v3's regex measured through `redact()` in an archive, not on a G4-built tree; G4's property corpus with G8.
- A base-vs-v2 diff of full-suite failure lists (the base run was stopped); `test_m_new_1_enforce_map_has_the_redactors_time_budget` classified as order-dependent from v1's base run and serial runs, not from a base `-n 2` run of 3c11364.
- Non-ASCII glue; Windows; a quiet machine; approval-card text beyond what the full suite covers.

## 15. Notes on what cannot be tested
- `runmap._sweep_held` with `_joins`: no input known that holds a PHONE value back (a held-back value is a piece of a placeholder
  name, like `SECRET` or `UUID_1`); decided for consistency, no test, no mutant (appendix C says so).
- The property oracle edit: it makes the oracle agree with production; a mutant of `_joins` would be caught by appendix B, not by
  the property test (the corpus holds almost no glued shapes).

## 16. Findings of G8-review-1, one by one
Readiness reviewer:
- B1 TAKEN: every changed or new tuple pasted with neighbours and flags (4.1), sweep code (4.2), full diff (appendix D).
- B2 TAKEN: exact red ids per function, measured (section 7): 99 = 49 + 17 + 30 + 1 + 1 + 1.
- B3 TAKEN: `test_limit_rows_are_pinned` asserts the desired behaviour (no leak) under `xfail(strict=True)`; same for 64 / 71.
- B4 TAKEN: re-pointed to G4 v3 (blob e30443310b2f), default build order G8 first while G4 is NOT READY with the flag trigger
  (L-D7), host rows re-measured through `redact()` with two expected columns (4.5). CONTESTED in part: "tests/test_p1c_gaps.py
  must stay green under G8" cannot be measured (the file does not exist until G4 is built); phase 3 of G4 runs it.
- M1 TAKEN: 46 new must-keep rows (K29-K74) with exact outcomes; count pinned (74; v1 had 28, not 26). Underscore digits: L-D10;
  letter-glued formatted digits: kept by the M1 redesign; versions: L-D8 (default mask, fallback (a)). CONTESTED: "refuse when a
  word of letters precedes" as a default for IPv4 (it gives up rows 7, 8, 11, 74 for evidence only): offered as L-D8 fallback.
- M2 TAKEN: L-D8, L-D9, L-D10, L-D11 added; L-D5 closed (no builder pick: the test does not change); a consequence column for
  every decision.
- M3 TAKEN: `leak()`, the row builder and the step-0 check in appendix A (a file to create); step-0 storage stated (section 3);
  the hash test replaced by literal expectations and count pins.
- M4 TAKEN: `_JOINS` holds PHONE only; exact inputs for the HOSTNAME / TENANT / IPV4 / digit clauses (section 7) and mutants S3-S6.
- M5 TAKEN in part: clock named, ratio widened to 6.0, five-vs-four entries corrected, six texts named; NOT re-measured (coordinator
  stop), marked as such, with the commands.
- M6 TAKEN: the full suite was run on the prototype (section 9) and the command is given; the 79-file claim is replaced.
- M7 TAKEN: phases with commands and green states (section 8); the G7 test does not change, so no new assertion text is needed;
  mutant runner named; evidence/G8-1.md in the file list; no G7 ticket edit (section 3 says why).
- N1 TAKEN (cap sentence dropped). N2 TAKEN (2.2: the `a` / `9` joins the BBAN). N3 TAKEN (exact string, section 7). N4 TAKEN
  (G4 v3; Python 3.13.18 measured, 3.12 by reading). N5 TAKEN (row 6 = 192.0.2.109). N6 TAKEN (L7, test with F1, F2).
- Form: TAKEN (section 13).
Codebase reviewer:
- M1 TAKEN with one addition: start split and the 10-digit rule as proposed, plus the 5-digit-run guard (without it
  `rev 2-3851007894abcdef` is masked, measured). Measured: all 47 rows still close; `eth0`, `PO12-...`, the card, `INV...`,
  ISBN, `sha256-...`, MAC, `backup_20-11-2026`, `hunter123-45-6789` are back to the base output; the G7 test stays byte-identical.
  CONTESTED in part: "`rtt 120 118 131 125ms` regression disappears" is not true under the 10-digit rule (12 digits): it stays
  `rtt <PHONE_1>ms` (3 of 4 numbers were masked on the base already); owned by L-D9 with a `+`-only fallback.
- M2 TAKEN: the `1.2.3.4rc1` sentence was false (measured: not masked on the base); versions listed (K43-K53) under L-D8; L-D1
  states the sweep consequence (with IPV4 out of `_JOINS`, `v1.2.3.4` stays even when `1.2.3.4` is known, K67). The proposed
  heuristic (letter or `_` before AND a letter after) is CONTESTED as default: it would still mask `python3.11.4.1` (nothing after)
  and gives up row 11; the narrower fallback (a) is offered instead.
- M3 TAKEN: `_sweep_held` passes `_joins` (decided, section 3); the oracle at tests/test_redact_idempotent_property.py:121 updated;
  the gate-level test with `build4155550132`.
- M4 TAKEN: host rows re-measured with G4 v3 through `redact()`: 60, 61, 62, 66 change output under G4c, 64, 71 close, 67-70 and
  78-80 stay leaks; two expected columns and the `G4C_MERGED` flag.
- M5 TAKEN: the suite command is the full suite plus the grep (73 + 6 files) and the ten named files; the g3 port re-pointed at a
  TENANT copy; fold_budget:78 is live (green in the run); test_k5_perf: perf, not run; mutant scripts: no G8 anchor (phase 4 runs
  them); test_no_hardcoded_values.py green in the run; the G4 v3 property corpus with G8: NOT VERIFIED (G4 not built), relation stated.
- N1 TAKEN (`>` in entry 6's end guard; K64). N2 TAKEN (K65 pins the numbers). N3 TAKEN in part: `ts+1000000000`, `now+...`,
  `backup_20-11-2026 done`, `epoch_1732095071`, `snap_2026112010` and a base64 blob added (K35, K57, K59, K62, K63, K66); the
  "0.2 per 1,000 characters of base64" rate is not re-measured. N4 TAKEN (comments and docstring given; `frozenset[str]`).
  N5 TAKEN (28 must-keep in v1, cites updated to a5f55addc; "stored at rest" wording used in L-D10, L-D11, section 12).
- Design note (G4 v3 says tests/test_redact_settle_loop.py must stay unchanged while v1 edited it): resolved, v2 does not edit it.

## Appendix A: tests/g8_cases.py (create; complete)
```python
"""Ticket G8 (glued-rest gap): the 80 probe rows and the must-keep rows, as data. Not collected by pytest.

Every value is fake or a documentation value and is built from parts here (no literal of a full value elsewhere, as
tests/test_text_parts_together.py does). A row is
    (id, kind, shape, text, value, cls, now, after, after_g4c)
with `text`, `now`, `after` and `after_g4c` templates over `V` (`{IP1}` ...) that `case()` fills in:
    now       `redact(text).text` on the base commit (step 0, recorded on cloud/core-c 3c11364; `python -m tests.g8_cases`
              re-checks it and exits 1 on any difference)
    after     `redact(text).text` with G8a + G8b, G4c NOT merged
    after_g4c the same once G4c (ticket G4 v3 section 5.2, or its successor) is merged; None = same as `after`
    cls       closed (leaks now, not after) | changed (no leak either way, the output changes) | unchanged | limit (still
              leaks after G8: a stated limit) | g4c (closed by G4c, not by G8)
"""

from __future__ import annotations

import difflib
import re
import sys

J = "".join
V = {
    "IP1": J(["192.", "0.2", ".10"]),  # RFC 5737 TEST-NET-1
    "IP2": J(["198.", "51.100", ".7"]),
    "IP3": J(["203.", "0.113", ".45"]),
    "IPD": J(["192-", "0-2", "-10"]),
    "PHONE_P": J(["+1 415-", "555-", "0132"]),  # 555 numbers
    "PHONE_P2": J(["+1 415-", "555-", "0199"]),
    "PHONE10": J(["415", "555", "0132"]),
    "PHONEUK": J(["+44 20 ", "5550 ", "1234"]),
    "IBAN_DE": J(["DE89", "3704", "0044", "0532", "0130", "00"]),  # the published example IBANs
    "IBAN_GB": J(["GB82", "WEST", "1234", "5698", "7654", "32"]),
    "UUID": J(["123e4567-", "e89b-12d3-", "a456-426614174000"]),  # the RFC example
    "UUID2": J(["0f8fad5b-", "d9cb-469f-", "a165-70867728950e"]),
    "HOST": J(["db-7", ".corp", ".internal"]),  # made up
    "HOST2": J(["db01", ".prod", ".corp"]),
    "HOST3": J(["nas02", ".office", ".lan"]),
    "HOST4": J(["printer7", ".local"]),
    "HOST5": J(["a.b.c", ".internal"]),
}
V["UUIDUP"] = V["UUID"].upper()
V["UUIDHEAD"] = V["UUID"][:24]

# Is G4c merged into this tree? The G4c builder sets True in the G4c commit (ticket G8 v2, section 8). Until then the host
# rows are checked against `after` and rows 64 and 71 are strict xfails naming G4c.
G4C_MERGED = False

ROWS = [
    (1, 'ipv4', 'control: spaces', 'from {IP1} ok', 'IP1', 'unchanged', 'from <IPV4_1> ok', 'from <IPV4_1> ok', None),
    (2, 'ipv4', 'letter after', 'from {IP1}a ok', 'IP1', 'closed', 'from {IP1}a ok', 'from <IPV4_1>a ok', None),
    (3, 'ipv4', 'word after', 'from {IP1}abc ok', 'IP1', 'closed', 'from {IP1}abc ok', 'from <IPV4_1>abc ok', None),
    (4, 'ipv4', '_x after', 'from {IP1}_x ok', 'IP1', 'closed', 'from {IP1}_x ok', 'from <IPV4_1>_x ok', None),
    (5, 'ipv4', '_ after', 'from {IP1}_ ok', 'IP1', 'closed', 'from {IP1}_ ok', 'from <IPV4_1>_ ok', None),
    (6, 'ipv4', 'digit after', 'from {IP1}9 ok', 'IP1', 'unchanged', 'from <IPV4_1> ok', 'from <IPV4_1> ok', None),
    (7, 'ipv4', 'letter before', 'from x{IP1} ok', 'IP1', 'closed', 'from x{IP1} ok', 'from x<IPV4_1> ok', None),
    (8, 'ipv4', 'word before (ip)', 'from ip{IP1} ok', 'IP1', 'closed', 'from ip{IP1} ok', 'from ip<IPV4_1> ok', None),
    (9, 'ipv4', '_ before', 'from node_{IP1} ok', 'IP1', 'closed', 'from node_{IP1} ok', 'from node_<IPV4_1> ok', None),
    (10, 'ipv4', 'digit before', 'from 7{IP1} ok', 'IP1', 'limit', 'from 7{IP1} ok', 'from 7{IP1} ok', None),
    (11, 'ipv4', 'both sides letters', 'from x{IP1}y ok', 'IP1', 'closed', 'from x{IP1}y ok', 'from x<IPV4_1>y ok', None),
    (12, 'ipv4', 'both sides _', 'from eth0_{IP1}_up ok', 'IP1', 'closed', 'from eth0_{IP1}_up ok', 'from eth0_<IPV4_1>_up ok', None),
    (13, 'ipv4', 'two glued IPs', 'from {IP1}{IP2} ok', 'IP1', 'limit', 'from {IP1}{IP2} ok', 'from {IP1}{IP2} ok', None),
    (14, 'ipv4', 'glued to UUID', 'from {UUID}{IP1} ok', 'IP1', 'closed', 'from {UUID}{IP1} ok', 'from <UUID_1><IPV4_1> ok', None),
    (15, 'ipv4', 'letter after + clean copy', 'from {IP1} and {IP1}a ok', 'IP1', 'closed', 'from <IPV4_1> and {IP1}a ok', 'from <IPV4_1> and <IPV4_1>a ok', None),
    (16, 'ipv4', 'after = with letter', 'src={IP3}x dst', 'IP3', 'closed', 'src={IP3}x dst', 'src=<IPV4_1>x dst', None),
    (17, 'phone', 'control: spaces', 'call {PHONE_P} now', 'PHONE_P', 'unchanged', 'call <PHONE_1> now', 'call <PHONE_1> now', None),
    (18, 'phone', 'letter after', 'call {PHONE_P}a now', 'PHONE_P', 'closed', 'call {PHONE_P}a now', 'call <PHONE_1>a now', None),
    (19, 'phone', '_x after', 'call {PHONE_P}_x now', 'PHONE_P', 'closed', 'call {PHONE_P}_x now', 'call <PHONE_1>_x now', None),
    (20, 'phone', '_ after', 'call {PHONE_P}_ now', 'PHONE_P', 'closed', 'call {PHONE_P}_ now', 'call <PHONE_1>_ now', None),
    (21, 'phone', 'letter before', 'call x{PHONE_P} now', 'PHONE_P', 'changed', 'call x+<PHONE_1> now', 'call x<PHONE_1> now', None),
    (22, 'phone', '_ before', 'call tel_{PHONE_P} now', 'PHONE_P', 'changed', 'call tel_+<PHONE_1> now', 'call tel_<PHONE_1> now', None),
    (23, 'phone', 'both sides', 'call x{PHONE_P}y now', 'PHONE_P', 'closed', 'call x{PHONE_P}y now', 'call x<PHONE_1>y now', None),
    (24, 'phone', 'clean copy + glued copy', 'call {PHONE_P} or {PHONE_P}a now', 'PHONE_P', 'closed', 'call <PHONE_1> or {PHONE_P}a now', 'call <PHONE_1> or <PHONE_1>a now', None),
    (25, 'phone', 'contiguous, letter after', 'call {PHONE10}a now', 'PHONE10', 'limit', 'call {PHONE10}a now', 'call {PHONE10}a now', None),
    (26, 'phone', 'contiguous, _x after', 'call {PHONE10}_x now', 'PHONE10', 'closed', 'call {PHONE10}_x now', 'call <PHONE_1>_x now', None),
    (27, 'phone', 'contiguous, letter before', 'call x{PHONE10} now', 'PHONE10', 'limit', 'call x{PHONE10} now', 'call x{PHONE10} now', None),
    (28, 'phone', 'contiguous, word before', 'call tel{PHONE10} now', 'PHONE10', 'closed', 'call tel{PHONE10} now', 'call tel<PHONE_1> now', None),
    (29, 'phone', 'contiguous, _ before', 'call tel_{PHONE10} now', 'PHONE10', 'closed', 'call tel_{PHONE10} now', 'call tel_<PHONE_1> now', None),
    (30, 'phone', 'contiguous, both _', 'call id_{PHONE10}_x now', 'PHONE10', 'closed', 'call id_{PHONE10}_x now', 'call id_<PHONE_1>_x now', None),
    (31, 'phone', 'contiguous, clean copy + glued', 'phone={PHONE10} then x{PHONE10} now', 'PHONE10', 'closed', 'phone=<PHONE_1> then x{PHONE10} now', 'phone=<PHONE_1> then x<PHONE_1> now', None),
    (32, 'phone', 'spaced UK, letter after', 'call {PHONEUK}a now', 'PHONEUK', 'closed', 'call <PHONE_1> 1234a now', 'call <PHONE_1>a now', None),
    (33, 'iban', 'control', 'pay {IBAN_DE} now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (34, 'iban', 'letter after (absorbed: alnum BBAN)', 'pay {IBAN_DE}a now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (35, 'iban', 'digit after', 'pay {IBAN_DE}9 now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> now', 'pay <IBAN_1> now', None),
    (36, 'iban', '_x after', 'pay {IBAN_DE}_x now', 'IBAN_DE', 'closed', 'pay {IBAN_DE}_x now', 'pay <IBAN_1>_x now', None),
    (37, 'iban', '_ after', 'pay {IBAN_DE}_ now', 'IBAN_DE', 'closed', 'pay {IBAN_DE}_ now', 'pay <IBAN_1>_ now', None),
    (38, 'iban', 'letter before', 'pay x{IBAN_DE} now', 'IBAN_DE', 'closed', 'pay x{IBAN_DE} now', 'pay x<IBAN_1> now', None),
    (39, 'iban', 'word before', 'pay iban{IBAN_DE} now', 'IBAN_DE', 'closed', 'pay iban{IBAN_DE} now', 'pay iban<IBAN_1> now', None),
    (40, 'iban', 'digit before', 'pay 7{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay 7{IBAN_DE} now', 'pay 7{IBAN_DE} now', None),
    (41, 'iban', '_ before', 'pay iban_{IBAN_DE} now', 'IBAN_DE', 'closed', 'pay iban_{IBAN_DE} now', 'pay iban_<IBAN_1> now', None),
    (42, 'iban', 'both _', 'pay to_{IBAN_DE}_x now', 'IBAN_DE', 'closed', 'pay to_{IBAN_DE}_x now', 'pay to_<IBAN_1>_x now', None),
    (43, 'iban', 'clean copy + _x copy', 'pay {IBAN_DE} or {IBAN_DE}_x now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> or <IBAN_1>_x now', 'pay <IBAN_1> or <IBAN_1>_x now', None),
    (44, 'iban', 'GB, _x after', 'pay {IBAN_GB}_x now', 'IBAN_GB', 'closed', 'pay {IBAN_GB}_x now', 'pay <IBAN_1>_x now', None),
    (45, 'iban', 'GB, letter before', 'pay x{IBAN_GB} now', 'IBAN_GB', 'closed', 'pay x{IBAN_GB} now', 'pay x<IBAN_1> now', None),
    (46, 'uuid', 'control', 'id {UUID} ok', 'UUID', 'unchanged', 'id <UUID_1> ok', 'id <UUID_1> ok', None),
    (47, 'uuid', 'digit after', 'id {UUID}9 ok', 'UUID', 'closed', 'id {UUID}9 ok', 'id <UUID_1>9 ok', None),
    (48, 'uuid', 'hex letter after', 'id {UUID}a ok', 'UUID', 'closed', 'id {UUID}a ok', 'id <UUID_1>a ok', None),
    (49, 'uuid', 'non-hex letter after', 'id {UUID}x ok', 'UUID', 'closed', 'id {UUID}x ok', 'id <UUID_1>x ok', None),
    (50, 'uuid', '_x after', 'id {UUID}_x ok', 'UUID', 'closed', 'id {UUID}_x ok', 'id <UUID_1>_x ok', None),
    (51, 'uuid', '_0 after (k8s)', 'id _default_{UUID}_0 ok', 'UUID', 'closed', 'id _default_{UUID}_0 ok', 'id _default_<UUID_1>_0 ok', None),
    (52, 'uuid', 'letter before (non-hex)', 'id x{UUID} ok', 'UUID', 'closed', 'id x{UUIDHEAD}<ACCOUNTID_1> ok', 'id x<UUID_1> ok', None),
    (53, 'uuid', 'hex letter before', 'id a{UUID} ok', 'UUID', 'closed', 'id a{UUIDHEAD}<ACCOUNTID_1> ok', 'id a<UUID_1> ok', None),
    (54, 'uuid', 'digit before', 'id 7{UUID} ok', 'UUID', 'closed', 'id 7{UUIDHEAD}<ACCOUNTID_1> ok', 'id 7<UUID_1> ok', None),
    (55, 'uuid', '_ before', 'id pod_{UUID} ok', 'UUID', 'closed', 'id pod_{UUIDHEAD}<ACCOUNTID_1> ok', 'id pod_<UUID_1> ok', None),
    (56, 'uuid', 'both letters', 'id x{UUID}y ok', 'UUID', 'closed', 'id x{UUID}y ok', 'id x<UUID_1>y ok', None),
    (57, 'uuid', 'upper, _x after', 'id {UUIDUP}_x ok', 'UUIDUP', 'closed', 'id {UUIDUP}_x ok', 'id <UUID_1>_x ok', None),
    (58, 'uuid', 'clean copy + glued copy', 'id {UUID} then {UUID}x ok', 'UUID', 'closed', 'id <UUID_1> then {UUID}x ok', 'id <UUID_1> then <UUID_1>x ok', None),
    (59, 'host', 'control', 'x {HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (60, 'host', 'digit after', 'x {HOST}9 y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internal9 y', 'x <HOSTNAME_1>.internal9 y', 'x <HOSTNAME_1> y'),
    (61, 'host', 'letter after', 'x {HOST}a y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internala y', 'x <HOSTNAME_1>.internala y', 'x <HOSTNAME_1> y'),
    (62, 'host', '_x after', 'x {HOST}_x y', 'HOST', 'unchanged', 'x <HOSTNAME_1>.internal_x y', 'x <HOSTNAME_1>.internal_x y', 'x <HOSTNAME_1> y'),
    (63, 'host', 'letter before', 'x z{HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (64, 'host', '_ before', 'x svc_{HOST} y', 'HOST', 'g4c', 'x svc_db-<HOSTNAME_1> y', 'x svc_db-<HOSTNAME_1> y', 'x <HOSTNAME_1> y'),
    (65, 'host', 'digit before', 'x 9{HOST} y', 'HOST', 'unchanged', 'x <HOSTNAME_1> y', 'x <HOSTNAME_1> y', None),
    (66, 'host', 'clean copy + glued', 'x {HOST} then {HOST}a y', 'HOST', 'unchanged', 'x <HOSTNAME_1> then <HOSTNAME_2>.internala y', 'x <HOSTNAME_1> then <HOSTNAME_2>.internala y', 'x <HOSTNAME_1> then <HOSTNAME_2> y'),
    (67, 'host', 'ends at corp, letter after', 'x {HOST2}a y', 'HOST2', 'limit', 'x {HOST2}a y', 'x {HOST2}a y', None),
    (68, 'host', 'ends at corp, digit after', 'x {HOST2}9 y', 'HOST2', 'limit', 'x {HOST2}9 y', 'x {HOST2}9 y', None),
    (69, 'host', 'ends at corp, _x after', 'x {HOST2}_x y', 'HOST2', 'limit', 'x {HOST2}_x y', 'x {HOST2}_x y', None),
    (70, 'host', 'lan, letter after', 'x {HOST3}x y', 'HOST3', 'limit', 'x {HOST3}x y', 'x {HOST3}x y', None),
    (71, 'host', 'lan, _ before', 'x vm_{HOST3} y', 'HOST3', 'g4c', 'x vm_nas02.<HOSTNAME_1> y', 'x vm_nas02.<HOSTNAME_1> y', 'x <HOSTNAME_1> y'),
    (72, 'ipv4', 'dashed EC2 name, letter after', 'node ip-{IPD}a ready', 'IPD', 'closed', 'node ip-{IPD}a ready', 'node ip-<IPV4_1>a ready', None),
    (73, 'ipv4', 'dashed EC2 name, _x after', 'node ip-{IPD}_x ready', 'IPD', 'closed', 'node ip-{IPD}_x ready', 'node ip-<IPV4_1>_x ready', None),
    (74, 'ipv4', 'letter between two IPs', 'from {IP1}x{IP2} ok', 'IP1', 'closed', 'from {IP1}x{IP2} ok', 'from <IPV4_1>x<IPV4_2> ok', None),
    (75, 'phone', 'two formatted phones glued', 'call {PHONE_P}{PHONE_P2} now', 'PHONE_P', 'unchanged', 'call <PHONE_1>+<PHONE_2> now', 'call <PHONE_1>+<PHONE_2> now', None),
    (76, 'iban', 'two IBANs glued', 'pay {IBAN_DE}{IBAN_GB} now', 'IBAN_DE', 'limit', 'pay {IBAN_DE}{IBAN_GB} now', 'pay {IBAN_DE}{IBAN_GB} now', None),
    (77, 'uuid', 'two UUIDs glued', 'id {UUID}{UUID2} ok', 'UUID', 'closed', 'id {UUID}{UUID2} ok', 'id <UUID_1><UUID_2> ok', None),
    (78, 'host', 'bare .local, digit after', 'x {HOST4}9 y', 'HOST4', 'limit', 'x {HOST4}9 y', 'x {HOST4}9 y', None),
    (79, 'host', 'bare .local, _x after', 'x {HOST4}_x y', 'HOST4', 'limit', 'x {HOST4}_x y', 'x {HOST4}_x y', None),
    (80, 'host', 'bare .internal, letter after', 'x {HOST5}x y', 'HOST5', 'limit', 'x {HOST5}x y', 'x {HOST5}x y', None),
]

PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
HOST_SUFFIX_LABELS = ("corp", "internal", "local", "lan", "intranet", "prod", "office")
LEAK_RUN = {"ipv4": 7, "iban": 8, "uuid": 8}  # phone: 4 digits; host: see leak()


def fill(template: str | None) -> str | None:
    return None if template is None else template.format(**V)


def case(row: tuple) -> dict:
    rid, kind, shape, text, value, cls, now, after, after_g4c = row
    after = fill(after)
    return {
        "id": rid,
        "kind": kind,
        "shape": shape,
        "text": fill(text),
        "value": V[value],
        "cls": cls,
        "now": fill(now),
        "after": after,
        "expected": fill(after_g4c) if (G4C_MERGED and after_g4c) else after,
    }


CASES = [case(r) for r in ROWS]
BY_ID = {c["id"]: c for c in CASES}


def _lcs(a: str, b: str) -> int:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)).size


def _digits(s: str) -> str:
    return re.sub(r"[ \-]", "", s)


def leak(kind: str, value: str, out: str) -> bool:
    """The G8 leak rule: is `value` (of probe kind `kind`) still readable in `out` outside the placeholders?
    ipv4: 7 characters of the value in a row; iban, uuid: 8; phone: 4 digits in a row once spaces and hyphens are taken out
    of both (a leading `+` of the value ignored); host: any label of the name other than HOST_SUFFIX_LABELS, or 2 or more
    leading characters of such a label directly before a placeholder (`svc_db-<HOSTNAME_1>`)."""
    rest = PLACEHOLDER.sub("|", out)
    if kind == "host":
        labels = [x for x in value.lower().split(".") if x not in HOST_SUFFIX_LABELS]
        low = rest.lower()
        if any(x in low for x in labels):
            return True
        return any((x[:k] + "|") in low for x in labels for k in range(2, len(x)))
    if value in rest:
        return True
    if kind == "phone":
        return _lcs(_digits(value).lstrip("+"), _digits(rest)) >= 4
    return _lcs(value, rest) >= LEAK_RUN[kind]


SHA = J(["3851007894", "abcdef0123456789abcdef0123456789abcdef0123456789abcd"])
P10 = V["PHONE10"]
SSN = J(["123", "-45-", "6789"])
CARD = J(["4242 ", "4242 ", "4242 ", "4242"])
# (id, text, now, after, verdict); None = the text itself. verdict: kept (nothing masked, before and after) | same (masked
# today, G8 does not change it, or changes only what the note says) | over-mask L-Dn (accepted by that decision) | closed (a
# real value newly masked). K1-K28 are v1's table; K29-K74 the reviewers' examples and the drafter's v2 traces.
MUST_KEEP = [
    ("K1", "release v1.2.3.4 shipped", None, None, "kept (L-D1)"),
    ("K2", "node-v18.19.1.2 build", None, None, "kept (L-D1)"),
    ("K3", "dotted date 2026.11.20.10 ok", None, None, "kept (L1)"),
    ("K4", "oid 1.3.6.1.4.1 ok", "oid <IPV4_1>.4.1 ok", "oid <IPV4_1>.4.1 ok", "same"),
    ("K5", "sha " + SHA, None, None, "kept"),
    ("K6", "commit " + P10 + "abcdef ok", None, None, "kept (L3)"),
    ("K7", "build" + P10 + " ok", None, None, "kept (L3)"),
    ("K8", "img sha256_" + SHA[:16], None, None, "kept"),
    ("K9", "wave2-2026-09-11T14:12:03Z", None, None, "kept"),
    ("K10", "orders-db-ro-1 up", None, None, "kept"),
    ("K11", "build-1234-5678-90 ok", None, None, "kept"),
    ("K12", "job-415-555-0132 ok", None, None, "kept"),
    ("K13", "pod web-5d8f9c7b6-x2x7q", None, None, "kept"),
    ("K14", "x86_64-linux-gnu", None, None, "kept"),
    ("K15", "eth0_up", None, None, "kept"),
    ("K16", "run_20261120101112_x ok", None, None, "kept"),
    ("K17", "self.local_cache = 1", None, None, "kept"),
    ("K18", "obj.internal_state", None, None, "kept"),
    ("K19", "nltk.corpus.reader", None, None, "kept"),
    ("K20", "acme.corporate.site", None, None, "kept"),
    ("K21", "ctx.local9", None, None, "kept"),
    ("K22", "vlan10.lan2 ok", None, None, "kept"),
    ("K23", "token AB12CDEFGHIJKLMNOPQ ok", None, None, "kept"),
    ("K24", "req ReqIdDE12345678901234 ok", None, "req ReqId<IBAN_1> ok", "over-mask L-D2"),
    ("K25", "tag xDE00ABCDEFGHIJK ok", None, "tag x<IBAN_1> ok", "over-mask L-D2"),
    ("K26", "ts 1732095071000_x", None, "ts <PHONE_1>_x", "over-mask L-D10"),
    ("K27", "uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe", None, "uuid-ish <UUID_1>cafe", "over-mask L-D4"),
    ("K28", "id " + V["UUID"].replace("-", "") + " ok", None, None, "kept"),
    ("K29", "eth0 1500 9000", None, None, "kept"),
    ("K30", "ipv4 1500 1600", None, None, "kept"),
    ("K31", "vlan10 2001 2002", None, None, "kept"),
    ("K32", "node1 8080 9090", None, None, "kept"),
    ("K33", "PO12-3456-7890", None, None, "kept"),
    ("K34", "rtt 120 118 131 125ms", "rtt <PHONE_1> 125ms", "rtt <PHONE_1>ms", "over-mask L-D9 (3 of 4 masked today)"),
    ("K35", "backup_20-11-2026 done", None, None, "kept"),
    ("K36", "x" + CARD, "x4242 <PHONE_1>", "x4242 <PHONE_1>", "same (card glued: not G8)"),
    ("K37", "INV2026-0042-1234", None, None, "kept"),
    ("K38", "ISBN978-3-16-148410-0", None, None, "kept"),
    ("K39", "sha256-" + SHA[:16], None, None, "kept"),
    ("K40", "mac00-11-22-33-44-55", None, None, "kept"),
    ("K41", "ref hunter" + SSN, None, None, "kept (L-D11)"),
    (
        "K42",
        "password=hunter\nref hunter" + SSN,
        "password=<SECRET_1>\nref <SECRET_1><SSN_1>",
        "password=<SECRET_1>\nref <SECRET_1><SSN_1>",
        "same (the G7 boundary-class pin)",
    ),
    ("K43", "python3.11.4.1", None, "python<IPV4_1>", "over-mask L-D8"),
    ("K44", "python3.11.2.1", None, "python<IPV4_1>", "over-mask L-D8"),
    ("K45", "jdk1.8.0.292", None, "jdk<IPV4_1>", "over-mask L-D8"),
    ("K46", "node18.19.1.2", None, "node<IPV4_1>", "over-mask L-D8"),
    ("K47", "libssl1.2.3.4", None, "libssl<IPV4_1>", "over-mask L-D8"),
    ("K48", "rev1.2.3.4", None, "rev<IPV4_1>", "over-mask L-D8"),
    ("K49", "libc6_2.36.0.1_amd64.deb", None, "libc6_<IPV4_1>_amd64.deb", "over-mask L-D8"),
    ("K50", "nginx_1.18.0.1-1_amd64.deb", None, "nginx_<IPV4_1>-1_amd64.deb", "over-mask L-D8"),
    ("K51", "1.0.0.0a2", None, "<IPV4_1>a2", "over-mask L-D8"),
    ("K52", "2.0.1.0b3", None, "<IPV4_1>b3", "over-mask L-D8"),
    ("K53", "1.2.3.4rc1", None, "<IPV4_1>rc1", "over-mask L-D8"),
    ("K54", "order_1234567890", None, "order_<PHONE_1>", "over-mask L-D10"),
    ("K55", "user_1234567890", None, "user_<PHONE_1>", "over-mask L-D10"),
    ("K56", "ts_1732095071", None, "ts_<PHONE_1>", "over-mask L-D10"),
    ("K57", "epoch_1732095071", None, "epoch_<PHONE_1>", "over-mask L-D10"),
    ("K58", "trace_1732095071000", None, "trace_<PHONE_1>", "over-mask L-D10"),
    ("K59", "snap_2026112010", None, "snap_<PHONE_1>", "over-mask L-D10"),
    ("K60", "b64url Zm9vYmFy_1234567890_YmF6", None, "b64url Zm9vYmFy_<PHONE_1>_YmF6", "over-mask L-D10"),
    ("K61", "id_123456789012345678 ok", None, None, "kept"),
    ("K62", "ts+1000000000", "ts+<PHONE_1>", "ts<PHONE_1>", "same (the + moves inside)"),
    ("K63", "now+3600000000", "now+<PHONE_1>", "now<PHONE_1>", "same (the + moves inside)"),
    ("K64", "<TENANT_" + P10 + ">", None, None, "kept"),
    (
        "K65",
        "call " + P10 + " or " + V["PHONE_P"],
        "call <PHONE_1> or <PHONE_2>",
        "call <PHONE_2> or <PHONE_1>",
        "same (numbering changes)",
    ),
    ("K66", "blob aGVsbG8+aDE12abcdefghijk/x", None, "blob aGVsbG8+a<IBAN_1>/x", "over-mask L-D2"),
    ("K67", "known 1.2.3.4 and v1.2.3.4", "known <IPV4_1> and v1.2.3.4", "known <IPV4_1> and v1.2.3.4", "same (L-D1)"),
    ("K68", "rev 2-" + SHA[:16], None, None, "kept"),
    ("K69", "color #415555 and #0a0b0c", None, None, "kept"),
    ("K70", "sizes 1024 2048 4096ms", None, "sizes <PHONE_1>ms", "over-mask L-D9"),
    ("K71", "took 100 200 300 400ms", "took <PHONE_1> 400ms", "took <PHONE_1>ms", "over-mask L-D9 (3 of 4 masked today)"),
    ("K72", "call 415-555-0132x123", None, "call <PHONE_1>x123", "closed (L-D9)"),
    ("K73", "ssn " + SSN + "a", None, None, "kept (L-D11: a stated limit, not a choice)"),
    ("K74", "card " + CARD + "x", "card <PHONE_1> 4242x", "card <PHONE_1> 4242x", "same (card glued: not G8)"),
]
# Found on the way, NOT glued, unchanged by G8 (stated limit L7): a phone number before a full stop is not masked.
FULL_STOP = [("F1", "call 415-555-0132."), ("F2", "call " + P10 + ".")]


def keep_case(row: tuple) -> dict:
    kid, text, now, after, verdict = row
    return {
        "id": kid,
        "text": text,
        "now": text if now is None else now,
        "after": text if after is None else after,
        "verdict": verdict,
    }


KEEP = [keep_case(r) for r in MUST_KEEP]


if __name__ == "__main__":  # step 0: on the base commit every `now` must hold (exit 1 otherwise); the output is the record
    from hadavin_sdk.guard.redact import redact

    bad = 0
    for c in CASES:
        got = redact(c["text"]).text
        bad += got != c["now"]
        print(("ok  " if got == c["now"] else "BAD ") + f"row {c['id']}: {got!r}")
    for k in KEEP + [keep_case((f, t, None, None, "L7")) for f, t in FULL_STOP]:
        got = redact(k["text"]).text
        bad += got != k["now"]
        print(("ok  " if got == k["now"] else "BAD ") + f"{k['id']}: {got!r}")
    print(f"{bad} differ", file=sys.stderr)
    sys.exit(1 if bad else 0)
```

## Appendix B: tests/test_redact_glued_rest.py (create; complete)
```python
"""Ticket G8: a value of kind IPV4, PHONE, IBAN or UUID glued to a letter, a digit or `_` is masked in the first call, the
glued character left outside the placeholder; the shapes G8 does not take are pinned as stated limits (strict xfail, so a
later fix shows up). Data and the leak rule: tests/g8_cases.py. Public names only, except `_has_bank_word` (one test)."""

from __future__ import annotations

import importlib
import time

import pytest

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact, redact_many
from tests import g8_cases as G

R = importlib.import_module("hadavin_sdk.guard.redact")


def _rows(*classes: str) -> list:
    return [pytest.param(c, id=f"row{c['id']}") for c in G.CASES if c["cls"] in classes]


def _ids(*ids: int) -> list:
    return [pytest.param(G.BY_ID[i], id=f"row{i}") for i in ids]


GLUED_OUTSIDE = (2, 3, 4, 5, 7, 8, 9, 18, 19, 20, 36, 37, 47, 48, 49, 50, 51)
LIMITS = {10: "L1", 13: "L2", 25: "L3", 27: "L3", 40: "L4", 76: "L5"}
LIMITS.update({i: "L6" for i in (67, 68, 69, 70, 78, 79, 80)})


@pytest.mark.parametrize("c", _rows("closed", "changed"))
def test_glued_rows_are_masked(c):
    t = c["text"]
    many = redact_many([t, "other line"])[0][0]
    for where, out in (("redact", redact(t).text), ("redact_many", many), ("redact_text", runmap.redact_text(t, runmap.RunMap()))):
        assert out == c["expected"], f"ROW {c['id']} {where}: {out!r}"
        assert not G.leak(c["kind"], c["value"], out), f"ROW {c['id']} {where} leaks: {out!r}"


@pytest.mark.parametrize("c", _ids(*GLUED_OUTSIDE))
def test_glued_character_stays_outside_the_placeholder(c):
    r = redact(c["text"])
    ph = next(p for p, o in r.mapping.items() if o == c["value"])  # StopIteration (red) when the value is not masked whole
    i = c["text"].index(c["value"])
    before, after = c["text"][:i], c["text"][i + len(c["value"]) :]
    assert r.text == before + ph + after, f"ROW {c['id']} glued: {r.text!r}"


@pytest.mark.parametrize("c", _rows("unchanged"))
def test_controls_and_untouched_rows_keep_their_output(c):
    out = redact(c["text"]).text
    assert out == c["expected"], f"ROW {c['id']} unchanged: {out!r}"
    if not (G.G4C_MERGED and c["kind"] == "host"):
        assert out == c["now"], f"ROW {c['id']} differs from the base: {out!r}"


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(G.BY_ID[i], id=f"row{i}", marks=pytest.mark.xfail(strict=True, reason=f"stated limit {lim} (ticket G8)"))
        for i, lim in sorted(LIMITS.items())
    ],
)
def test_limit_rows_are_pinned(c):
    """Asserts the DESIRED behaviour; strict xfail, so the day a limit is fixed the suite turns red and the row is moved."""
    out = redact(c["text"]).text
    assert not G.leak(c["kind"], c["value"], out), f"ROW {c['id']} limit: {out!r}"


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(
            G.BY_ID[i],
            id=f"row{i}",
            marks=[] if G.G4C_MERGED else [pytest.mark.xfail(strict=True, reason="closed by G4c (ticket G4), not by G8")],
        )
        for i in (64, 71)
    ],
)
def test_host_glued_before_is_closed_by_g4c(c):
    out = redact(c["text"]).text
    assert out == "x <HOSTNAME_1> y", f"ROW {c['id']} g4c: {out!r}"


@pytest.mark.parametrize("k", [pytest.param(k, id=k["id"]) for k in G.KEEP])
def test_must_keep_rows(k):
    out = redact(k["text"])
    assert out.text == k["after"], f"ROW {k['id']} keep ({k['verdict']}): {out.text!r}"
    if k["after"] == k["text"]:
        assert out.mapping == {}, f"ROW {k['id']} keep: map {out.mapping!r}"


@pytest.mark.parametrize("fid,text", G.FULL_STOP)
def test_phone_before_a_full_stop_is_a_stated_limit(fid, text):
    """L7, found on the way (not glued, not changed by G8): PHONE's end guard refuses `.`. Pinned as it is today."""
    assert redact(text).text == text, f"ROW {fid} full stop"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_second_call_changes_nothing(c):
    m = runmap.RunMap()
    once = runmap.redact_text(c["text"], m)
    snap = dict(m)
    assert runmap.redact_text(once, m) == once and dict(m) == snap, f"ROW {c['id']} second call"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_untrusted_matches_redact_text(c):
    assert runmap.redact_untrusted(c["text"], runmap.RunMap()) == runmap.redact_text(c["text"], runmap.RunMap())


@pytest.mark.parametrize(
    "c", [pytest.param(c, id=f"row{c['id']}") for c in G.CASES if c["kind"] in ("ipv4", "phone") and "UUID" not in c["after"]]
)
def test_restore_round_trip_ipv4_and_phone(c):
    m = runmap.RunMap()
    out = runmap.redact_text(c["text"], m)
    assert runmap.restore_text(out, m) == c["text"], f"ROW {c['id']} restore"


def test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only():
    """G8b: a copy of a known PHONE value is replaced when a letter or `_` touches it, not when a digit does; every
    other kind keeps the old rule (no ASCII letter or digit beside the copy)."""
    p = G.P10
    out = redact(f"phone={p} then x{p} now").text  # row 31
    assert out == "phone=<PHONE_1> then x<PHONE_1> now", f"SWEEP phone letter: {out!r}"
    out = redact(f"a x{p} and a{p}0b", mapping={"<PHONE_1>": p}).text
    assert out == f"a x<PHONE_1> and a{p}0b", f"SWEEP phone digit: {out!r}"  # a digit beside it: another number
    ip = G.V["IP1"]
    out = redact(f"known {ip} and v{ip}").text
    assert out == f"known <IPV4_1> and v{ip}", f"SWEEP ipv4: {out!r}"  # IPV4 is not in _JOINS (L-D1)
    out = redact("on printer7 and xprinter7", mapping={"<HOSTNAME_1>": "printer7"}).text
    assert out == "on <HOSTNAME_1> and xprinter7", f"SWEEP host: {out!r}"
    out = redact("t acme42 and acme42x", mapping={"<TENANT_1>": "acme42"}).text
    assert out == "t <TENANT_1> and acme42x", f"SWEEP tenant: {out!r}"


def test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone():
    """The gate's own sweep (`runmap.enforce_map`, the model-visible text) inherits G8b: the very shape the PHONE hash guard
    keeps in pass 1 (`build4155550132`) is rewritten once the number is a known value of the run."""
    m = {"<PHONE_1>": G.P10}
    for text, want in (
        ("build" + G.P10, "build<PHONE_1>"),
        ("x" + G.P10 + "_", "x<PHONE_1>_"),
        ("7" + G.P10, "7" + G.P10),
    ):
        out = runmap.enforce_map(text, m)
        assert out == want, f"GATE phone: {out!r}"
    out = runmap.enforce_map("t acme42x", {"<TENANT_1>": "acme42"})
    assert out == "t acme42x", f"GATE tenant: {out!r}"


def test_bank_word_check_ignores_a_glued_uuid():
    glued = "id x" + G.J(["123e4567-", "e89b-12d3-", "a456-", "aba123456789"])
    assert R._has_bank_word(glued) is False, "BANK glued uuid"  # True before G8: the UUID's tail read as an ABA number


def test_row_counts_are_pinned():
    from collections import Counter

    assert len(G.CASES) == 80 and len(G.KEEP) == 74 and len(G.FULL_STOP) == 2
    assert Counter(c["cls"] for c in G.CASES) == {"closed": 47, "unchanged": 16, "limit": 13, "changed": 2, "g4c": 2}
    assert sorted(LIMITS) == sorted(c["id"] for c in G.CASES if c["cls"] == "limit")


HOSTILE = {
    "dots": "1.",
    "digits and spaces": "x1 2 3 4 5 6 7 8 9 ",
    "underscore digits": "_4155550132",
    "hex and dashes": "deadbeef-dead-beef-dead-",
    "iban-ish": "aDE89" + "A" * 40 + " ",
    "plus digits": "a+1 415-555-0132",
}


@pytest.mark.perf
@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_glued_patterns_are_linear(name):
    """CPU seconds (`time.thread_time`, best of 3) for 65,536 and 262,144 characters: the ratio is at most 6.0 (4x the text;
    G8 v2 measured at most 4.6 with the noise of a shared container) and the large text takes under 3.0 s."""

    def best(n: int) -> float:
        text = (HOSTILE[name] * (n // len(HOSTILE[name]) + 1))[:n]
        out = []
        for _ in range(3):
            t0 = time.thread_time()
            redact(text)
            out.append(time.thread_time() - t0)
        return min(out)

    small, large = best(65_536), best(262_144)
    assert large < 3.0, f"{name}: {large:.2f} s"
    assert large / max(small, 1e-3) <= 6.0, f"{name}: ratio {large / max(small, 1e-3):.2f}"
```

## Appendix C: tests/g8_mutants.py (create; complete). Not run by the drafter. `runmap._sweep_held` has no mutant (section 15).
```python
"""The mutants of ticket G8 (glued-rest gap), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must
hold ``expect`` (the ``ROW <id> ...`` or ``SWEEP ...`` start of the assertion message). Run from the repo root:

    python tests/g8_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g8_mutants.py G8-P       # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
RD = "src/hadavin_sdk/guard/redact.py"
TEST = "tests/test_redact_glued_rest.py"
PIN = "tests/test_redact_glued_rest::"
UU = r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
TS = r'(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))'
E5 = r'(?:(?<![\w.\-])(?=(?:[ \-]?\d){10})(?![\d \-]{0,12}\d{5})|(?<![0-9.\-])(?=\+))(?!\d{4}-\d\d-\d\d)'
E6 = r'(?<![0-9A-Za-z.\-+])(?:(?<=_)|(?=\d{10,16}_))'
MAIN_START = r'r"(?<![\w.\-])(?!\d{4}-\d\d-\d\d)"'
E5_TUPLE = (
    '    (\n        "PHONE",\n        re.compile(\n            r"' + E5 + '"\n            r"' + TS + '"\n'
    '            r"\\+?\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![0-9.])"\n        ),\n    ),\n'
)
MAIN_TUPLE = (
    '    (\n        "PHONE",\n        re.compile(\n            ' + MAIN_START + '\n            r"' + TS + '"\n'
    '            r"\\+?\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![\\w.])"\n        ),\n    ),\n'
)


def m(name, old, new, killer, expect, file=RD):
    return Mutant(name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer)


GR, KEEP, SW = "test_glued_rows_are_masked", "test_must_keep_rows", "test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only"
M = [
    m("G8-I1 IBAN end back to \\b", r'r"\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])"', r'r"\d{2}[A-Za-z0-9]{11,30}\b"', GR, "ROW 36 "),
    m("G8-I2 IBAN start back to \\b", '_NOT_IN_WORD\n            + r"(?:AD|AE', 'r"\\b(?:AD|AE', GR, "ROW 38 "),
    m("G8-I3 IBAN start without the camelCase part", '_NOT_IN_WORD\n            + r"(?:AD|AE', 'r"(?<![A-Za-z0-9])(?:AD|AE', GR, "ROW 38 "),
    m("G8-U1 UUID end \\b", UU + '"', UU + r'\b"', GR, "ROW 14 "),
    m("G8-U2 UUID start \\b", r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', r'r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', GR, "ROW 51 "),
    m("G8-V1 IPV4 dotted end \\b", r'(?:\d{1,3}\.){3}\d{1,3}(?![0-9])"', r'(?:\d{1,3}\.){3}\d{1,3}\b"', GR, "ROW 2 "),
    m("G8-V2 IPV4 dotted start \\b", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"\b(?<!(?<![A-Za-z])[vV])', GR, "ROW 7 "),
    m("G8-V3 IPV4 drop the digit look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<!(?<![A-Za-z])[vV])', KEEP, "ROW K2 "),
    m("G8-V4 IPV4 drop the lone-v look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<![0-9])', KEEP, "ROW K1 "),
    m("G8-V5 EC2 end \\b", r'(\d{1,3}(?:-\d{1,3}){3})(?![0-9])"', r'(\d{1,3}(?:-\d{1,3}){3})\b"', GR, "ROW 72 "),
    m("G8-P1 entry 5 after the main entry", E5_TUPLE + MAIN_TUPLE, MAIN_TUPLE + E5_TUPLE, GR, "ROW 32 "),
    m("G8-P2 entry 5 removed", E5_TUPLE, "", GR, "ROW 18 "),
    m("G8-P3 entry 5 refuses a letter before +", r'|(?<![0-9.\-])(?=\+))(?!\d{4}', r')(?!\d{4}', GR, "ROW 21 "),
    m("G8-P4 entry 5 lets a letter stand before any number", r'(?:(?<![\w.\-])(?=(?:[ \-]?\d){10})', r'(?:(?<![0-9.\-])(?=(?:[ \-]?\d){10})', KEEP, "ROW K31 "),
    m("G8-P5 entry 5 without the 10-digit rule", r'(?=(?:[ \-]?\d){10})(?![\d \-]{0,12}\d{5})', r'(?![\d \-]{0,12}\d{5})', KEEP, "ROW K73 "),
    m("G8-P6 entry 5 without the 5-digit group guard", r'(?![\d \-]{0,12}\d{5})|', r'|', KEEP, "ROW K68 "),
    m("G8-P7 entry 5 end back to the main guard", r'[\d \-]){8,14}\d(?![0-9.])"', r'[\d \-]){8,14}\d(?![\w.])"', GR, "ROW 18 "),
    m("G8-P8 entry 6 allows a letter after", r'r"\d{10,16}(?![0-9A-Za-z.>])"', r'r"\d{10,16}(?![0-9.>])"', KEEP, "ROW K8 "),
    m("G8-P9 entry 6 without the timestamp guard", '|(?=\\d{10,16}_))"\n            r"' + TS + '"\n', '|(?=\\d{10,16}_))"\n', KEEP, "ROW K16 "),
    m("G8-P10 entry 6 without the > guard", r'r"\d{10,16}(?![0-9A-Za-z.>])"', r'r"\d{10,16}(?![0-9A-Za-z.])"', KEEP, "ROW K64 "),
    m("G8-P11 entry 6 needs _ before", r'(?:(?<=_)|(?=\d{10,16}_))', r'(?<=_)', GR, "ROW 26 "),
    m("G8-P12 keyword entry removed", '    ("PHONE", re.compile(r"(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\\d{10,16})(?![0-9a-z.])")),\n', "", GR, "ROW 28 "),
    m("G8-S1 _JOINS empty", '_JOINS = {"PHONE": frozenset(string.digits)}', "_JOINS = {}", GR, "ROW 31 "),
    m("G8-S2 sweep call without joins", "_replace_standalone(segment, original, placeholder, _joins(placeholder))", "_replace_standalone(segment, original, placeholder)", GR, "ROW 31 "),
    m("G8-S3 HOSTNAME given digits", '_JOINS = {"PHONE": frozenset(string.digits)}', '_JOINS = {"PHONE": frozenset(string.digits), "HOSTNAME": frozenset(string.digits)}', SW, "SWEEP host"),
    m("G8-S4 IPV4 given digits", '_JOINS = {"PHONE": frozenset(string.digits)}', '_JOINS = {"PHONE": frozenset(string.digits), "IPV4": frozenset(string.digits)}', SW, "SWEEP ipv4"),
    m("G8-S5 TENANT given digits", '_JOINS = {"PHONE": frozenset(string.digits)}', '_JOINS = {"PHONE": frozenset(string.digits), "TENANT": frozenset(string.digits)}', SW, "SWEEP tenant"),
    m("G8-S6 PHONE copy beside a digit replaced too", '_JOINS = {"PHONE": frozenset(string.digits)}', '_JOINS = {"PHONE": frozenset()}', SW, "SWEEP phone digit"),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):
        name, v, test_id, good = row
        print(f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]", flush=True)
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    first_lines: dict[str, str] = {}
    res = run_mutants(
        ROOT,
        M,
        [TEST, "tests/g8_cases.py", "tests/__init__.py", "tests/conftest.py"],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
```

## Appendix D: the source diff against a5f55addc (redact.py and runmap.py; produced by applying section 4 to an archive of a5f55addc)
```diff
diff -ruN a/src/hadavin_sdk/guard/redact.py b/src/hadavin_sdk/guard/redact.py
--- a/src/hadavin_sdk/guard/redact.py	2026-11-20 09:05:34.000000000 +0000
+++ b/src/hadavin_sdk/guard/redact.py	2026-11-20 09:06:03.789983383 +0000
@@ -23,6 +23,12 @@
 model gate (`runmap.enforce_map`) replaces the values the run's map already holds (the redactor's own final sweep, with the
 gate's held-back values) and runs no pattern at all, so a value no pattern here matched and no map entry holds passes it.
 (A re-scan inside redact() used the sweep's own rule and could never fire, so it was removed - second review, 2026-09-30.)
+
+A value glued to a letter or `_` is masked with the glued text left outside the placeholder (`node_<IPV4_1>`, `<UUID_1>x`):
+an e-mail address, an IPv4 address, an IBAN, a UUID, a phone number that starts with `+` or is written in groups with at
+least 10 digits, and a contiguous one beside `_` or straight after a phone word (G8). A contiguous digit run glued to a
+letter is not read as a phone number (hashes and identifiers), and a digit glued before an address or an IBAN is not read
+as one. A copy of a known phone number is swept where a letter or `_` touches it (not a digit).
 """
 
 from __future__ import annotations
@@ -263,19 +269,25 @@
     # which would otherwise fragment its digit runs and leak the country+bank prefix. The prefix is
     # restricted to the SWIFT IBAN-registry country set (not any two letters) so an uppercase
     # evidence token like `AB12CDEF...` is NOT clobbered — only a genuine IBAN country prefix fires.
+    # Glued (G8): not after an ASCII letter or digit, except a lower-case letter right before the country code (camelCase,
+    # `_NOT_IN_WORD`), and not followed by a letter or digit (one would join the BBAN). So `iban_DE89...`, `xDE89...` and
+    # `DE89..._x` are masked with the glued text outside; `7DE89...` and `XDE89...` are not (ticket G8, limit L4).
     (
         "IBAN",
         re.compile(
-            r"\b(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
+            _NOT_IN_WORD
+            + r"(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
             r"|GI|GL|GR|GT|HN|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|LY|MC|MD|ME|MK|MN|MR|MT"
             r"|MU|NI|NL|NO|PK|PL|PS|PT|QA|RO|RS|RU|SA|SC|SD|SE|SI|SK|SM|SO|ST|SV|TL|TN|TR|UA|VA|VG|XK)"
-            r"\d{2}[A-Za-z0-9]{11,30}\b"
+            r"\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])"
         ),
     ),
+    # No word boundary (G8): the 8-4-4-4-12 run is found inside a longer token (`pod_<uuid>_0`, `x<uuid>`, `<uuid>9`) and
+    # the glued text stays outside. An 8-4-4-4-16 hex id gives `<UUID_1>` and its last 4 hex digits (accepted, L-D4).
     (
         "UUID",
         re.compile(
-            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
+            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
         ),
     ),
     # Bank details (owner, 2026-10-28): masked by shape beside their keyword, never by checksum. After UUID (a UUID
@@ -372,9 +384,13 @@
     # id on a non-AWS deployment) since WARDEN runs on any cloud.
     ("ACCOUNTID", re.compile(r"\b\d{12}\b")),
     # An EC2 private DNS name carries the address with dashes: ip-10-0-3-22(.region.compute.internal).
-    ("IPV4", re.compile(r"\b(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})\b")),
+    # A letter or `_` may follow the last group (`ip-10-0-3-22a`, G8); a digit may not.
+    ("IPV4", re.compile(r"\b(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})(?![0-9])")),
     ("IPV4", re.compile(r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),  # k8s pod DNS
-    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
+    # Dotted quad (G8): not inside a digit run (`7192.0.2.10`, `2026.11.20.10`: limit L1) and not after a lone `v` / `V`
+    # (`v1.2.3.4` is a version, L-D1). A letter or `_` on either side is glued text, left outside (`node_<IPV4_1>`,
+    # `<IPV4_1>a`); a four-part version glued to a word (`python3.11.4.1`) is masked too (L-D8).
+    ("IPV4", re.compile(r"(?<![0-9])(?<!(?<![A-Za-z])[vV])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")),
     # IPv6 — we redact IPv4, so an IPv6 address (common in dual-stack k8s pod logs) is the same
     # identifier and must be masked too. Deliberately matches ONLY real addresses: either a `::`
     # compression or a full 8 groups, so a `10:02:11` timestamp is left alone. (A MAC has its own
@@ -488,6 +504,18 @@
     #   - (hadavin-sdk edit) nor may it be a compact timestamp `YYYYMMDDhhmmss` (`20261030123456`): 14 digits
     #     with a valid month, day and time. Narrow on purpose: a phone written with `+` or of another length is
     #     still masked.
+    # (G8) Glued to a letter or `_`, BEFORE the main entry (which would leave `<PHONE_1> 1234a`): a number that starts
+    # with `+` may follow a letter or `_` (`x+1 415-555-0132`); one without `+` starts where the main entry may, holds at
+    # least 10 digits and no run of 5 (`415-555-0132x123`; not `rev 2-3851007894abcdef`, a hash). Either may END before a
+    # letter or `_`, never before a digit or `.`. `eth0 1500 9000`, `PO12-3456-7890`, `hunter123-45-6789` stay as they were.
+    (
+        "PHONE",
+        re.compile(
+            r"(?:(?<![\w.\-])(?=(?:[ \-]?\d){10})(?![\d \-]{0,12}\d{5})|(?<![0-9.\-])(?=\+))(?!\d{4}-\d\d-\d\d)"
+            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
+            r"\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![0-9.])"
+        ),
+    ),
     (
         "PHONE",
         re.compile(
@@ -496,6 +524,18 @@
             r"\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![\w.])"
         ),
     ),
+    # (G8) A contiguous 10 to 16 digit number with `_` on one side and no letter or digit on the other (`tel_4155550132`,
+    # `4155550132_x`); not a compact timestamp; `>` ends no phone (a placeholder `<TENANT_4155550132>`). `sha256_3851...ab`
+    # stays (a letter after); `order_1234567890` is masked (L-D10). Then a number glued straight to a phone word.
+    (
+        "PHONE",
+        re.compile(
+            r"(?<![0-9A-Za-z.\-+])(?:(?<=_)|(?=\d{10,16}_))"
+            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
+            r"\d{10,16}(?![0-9A-Za-z.>])"
+        ),
+    ),
+    ("PHONE", re.compile(r"(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\d{10,16})(?![0-9a-z.])")),
     # password=..., secret: ..., aws_secret_access_key="...": the value after a credential-ish key.
     # Runs LAST: a value already masked whole is left alone. The bounded [\w.\-] prefix/suffix lets the sensitive word sit INSIDE a
     # compound key (`aws_secret_access_key`, `db_password`), which a `\b`-anchored form missed — the
@@ -1977,7 +2017,7 @@
                 if rule is _EVERY_COPY:
                     segment = segment.replace(original, placeholder)
                 else:
-                    segment = _replace_standalone(segment, original, placeholder)
+                    segment = _replace_standalone(segment, original, placeholder, _joins(placeholder))
                 self.actions += segment.count(placeholder) - before  # one per copy replaced
             parts[i] = segment
         return "".join(parts)
@@ -2162,10 +2202,22 @@
 
 
 _ALNUM = frozenset(string.ascii_letters + string.digits)
-
-
-def _replace_standalone(segment: str, original: str, placeholder: str) -> str:
-    """Replace `original` where no ASCII letter or digit touches it. A plain scan: a compiled pattern (or an
+# The characters that make a touched copy part of a longer token, per kind (G8b). A PHONE value glued to a letter or `_`
+# is the number with a word beside it (the patterns read it so); a digit beside it makes another number. Every other kind:
+# `_ALNUM` (a host name, a tenant, an account id are made of letters and digits, so a letter beside one may be part of it).
+_JOINS = {"PHONE": frozenset(string.digits)}
+
+
+def _joins(placeholder: str) -> frozenset[str]:
+    """The characters that, touching a copy of a known value, make it part of a longer token (ticket G8): a digit for
+    a phone number (a letter or `_` beside it is a word glued on, as the patterns read it); a letter or digit for
+    every other kind."""
+    return _JOINS.get(_kind(placeholder), _ALNUM)
+
+
+def _replace_standalone(segment: str, original: str, placeholder: str, joins: frozenset[str] = _ALNUM) -> str:
+    """Replace `original` where no character of `joins` touches it (default `_ALNUM`: an ASCII letter or digit; callers
+    pass `_joins(placeholder)`). A plain scan: a compiled pattern (or an
     lru_cache of one) keyed by the identifier would keep one client's values in process memory, shared with every
     other client (R371), and `re` caches compiled patterns itself."""
     out: list[str] = []
@@ -2175,7 +2227,7 @@
         if j < 0:
             break
         before, after = segment[j - 1 : j], segment[j + n : j + n + 1]
-        if before in _ALNUM or after in _ALNUM:
+        if before in joins or after in joins:
             out.append(segment[i : j + 1])
             i = j + 1
             continue
diff -ruN a/src/hadavin_sdk/guard/runmap.py b/src/hadavin_sdk/guard/runmap.py
--- a/src/hadavin_sdk/guard/runmap.py	2026-11-20 09:05:34.000000000 +0000
+++ b/src/hadavin_sdk/guard/runmap.py	2026-11-20 09:06:03.790764226 +0000
@@ -29,6 +29,7 @@
     PATTERNS,
     SECRET_KINDS,
     _alias_keys,
+    _joins,
     _plain,
     _Redactor,
     _replace_standalone,
@@ -696,7 +697,7 @@
     the ones every producer's output already follows: longest originals first (a value that contains
     another is replaced whole); nothing is replaced inside a placeholder already in the text. Which copies
     (`redact._sweep`): a value of a secret kind of 4 characters or more, every copy; any other value, only
-    where no ASCII letter or digit touches it.
+    where no ASCII letter or digit touches it (a PHONE value: where no digit does; `redact._joins`, ticket G8).
 
     Two things are added to the sweep.
     1. Held-back values. Inside one stretch of text the sweep replaces value after value and does not look
@@ -715,7 +716,7 @@
     Limits, on purpose (each pinned by a test in tests/test_runmap_enforce_map.py):
     - NOT replaced at all: a value under 3 characters; and, unless it is a secret kind of 4 characters or
       more, a value that is all digits and under 6 characters or a common word (`redact._COMMON`).
-    - A value that is not a secret kind of 4 or more is left where an ASCII letter or digit touches it and
+    - A value that is not a secret kind of 4 or more is left where an ASCII letter or digit (for a PHONE value: a digit) touches it and
       keeps touching it after every other replacement.
     - Only the spelling held in the map is replaced (for a value that is not ASCII, also its folded NFKC spellings,
       which the redactor sweeps with it: each is its own held-back item when it is a piece of a placeholder). A copy hidden by full-width letters, a zero-width
@@ -846,7 +847,7 @@
             if rule is _EVERY_COPY:
                 parts[i] = segment.replace(spelling, placeholder)
             else:
-                parts[i] = _replace_standalone(segment, spelling, placeholder)
+                parts[i] = _replace_standalone(segment, spelling, placeholder, _joins(placeholder))
     return "".join(parts)
 
 
```

## Appendix E: the two edited test files (diff against a5f55addc)
```diff
diff -ruN a/tests/test_redact_g3_port.py b/tests/test_redact_g3_port.py
--- a/tests/test_redact_g3_port.py	2026-11-20 09:05:34.000000000 +0000
+++ b/tests/test_redact_g3_port.py	2026-11-20 09:06:03.791112791 +0000
@@ -53,10 +53,10 @@
 def test_actions_each_kind_of_change_is_counted():
     # a pattern mask: one per value masked
     assert redact("mail bob@example.com").actions == 1
-    # the sweep: one per copy replaced (the second copy touches `_`, which the pattern's word boundary does not accept)
-    uid = "123e4567-e89b-12d3-a456-426614174000"
-    swept = redact(f"uid {uid} and x_{uid}_0")
-    assert swept.text == "uid <UUID_1> and x_<UUID_1>_0" and swept.actions == 2
+    # the sweep: one per copy replaced (the second copy is not after the tenant key, so only the sweep reaches it; since
+    # G8 a UUID glued to `_` is the UUID pattern's own match and no longer shows the sweep)
+    swept = redact("tenant_id=acme42 and x_acme42_0")
+    assert swept.text == "tenant_id=<TENANT_1> and x_<TENANT_1>_0" and swept.actions == 2
     # a known value written in clear: every copy
     again = redact(f"mail {MAIL} and {MAIL}", mapping=dict(KNOWN))
     assert again.text == "mail <EMAIL_1> and <EMAIL_1>" and again.actions == 2
diff -ruN a/tests/test_redact_idempotent_property.py b/tests/test_redact_idempotent_property.py
--- a/tests/test_redact_idempotent_property.py	2026-11-20 09:05:34.000000000 +0000
+++ b/tests/test_redact_idempotent_property.py	2026-11-20 09:06:03.791002353 +0000
@@ -118,7 +118,7 @@
         rule = R._sweep(placeholder, original)
         if rule is None or original not in free:
             continue
-        if rule is R._EVERY_COPY or R._replace_standalone(free, original, "\x00") != free:
+        if rule is R._EVERY_COPY or R._replace_standalone(free, original, "\x00", R._joins(placeholder)) != free:
             found.append(placeholder)
     return found
 
```

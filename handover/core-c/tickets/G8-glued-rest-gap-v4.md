# G8 v4: the glued-rest gap of IPv4, phone, IBAN, UUID and card numbers (ORDER 016c item 15, K38 / L33, backlog 10)

Status: DRAFT v4 for plan review round 4, core-c drafter (opus tier), 2026-11-20. Nothing is built. v4 is v3
(G8-glued-rest-gap-v3.md) with every finding of G8-review-3-codebase.md resolved (M1-M5, N1-N6; section 18); every changed
paragraph, row or code line is marked "CHANGED in v4" (in code and data files: a `v4` comment); everything else is v3's text.
v3 took or contested every finding of G8-review-2.md (section 16) and kept what v2 resolved from G8-review-1.md (section 17). A
builder with no other context builds from this file alone: every changed PATTERNS tuple is in section 4, the data file, the
test file, the mutant file and the cost script are complete in appendices A, B, C and F, the source diff is appendix D and the
edits of four existing test files are appendix E. Path class: redaction. Lead rule: build only a gap that a failing input proves.

What changed from v3, in one list (CHANGED in v4; each with its finding; evidence labels: MEASURED = run by the v4 drafter on
`git archive 99787d5b3` copies in its scratch folder, read-only; BY READING; NOT RUN):
- M1 (IBAN `_` inside base64url tokens): MEASURED with the base64url and the standard base64 alphabets (2.4b). v3's claims "the
  base's behaviour in every class" and "0 tokens with an IBAN" were false: v3's own measurement drew only from the 62 letters and
  digits. v3's start/end let an IBAN start or end at `_` inside a token: per 80,000 random base64url tokens after `key`, 22 kept
  token text readable next to an `<IBAN_n>` (base 9; up to 39 characters), and the map split in 47 (base 17) under `key` and 48
  (base 21) under `Bearer`. Fix (default, decision L-D15): the IBAN start and end take `_` only in a short-word context
  (`_IBAN_START`, `_IBAN_END`, section 4.1); MEASURED equal to the base in readable text in all 16 random classes and in map
  splits in 15 of 16 (one more split in 20,000 Bearer tokens of 129-163 characters). Rows 36, 37, 41, 42, 44 stay closed; two new
  limit rows 87, 88 (L4); must-keep K83, K84; mutants I4, I5. The row-41 trade-off is offered to the lead (L-D15). Found on the
  way: the BASE already starts an IBAN after `-`, `+`, `/` inside a token (9 readable per 80,000 base64url, 26 per 80,000
  base64 `key` tokens): a pre-existing class, not G8's (L12, follow-up L-D16).
- M2 (`›` on the untrusted path): MEASURED: v3 turns `redact_untrusted("<TENANT_4155550132>")` into `‹TENANT_<PHONE_1>›` with a
  PHONE map entry. PHONE entry 7's end class gets `›` (`(?![0-9A-Za-z.>›])`); rows U1, U2 and
  `test_untrusted_placeholder_literal_keeps_its_number`; mutant P13.
- M3 (G4 v5 reconciled): G4 v5 is its own text (section 0.3, L23, L21), not a copy of v4; its HOSTNAME regex lines equal v4's
  (MEASURED as text); the differences (oracle line 141, PHONE entries 6-8, `g8_mutants.py` in G4's Phase 5, the `after_g4c` and
  K60/K66 rules, docstring placement) are reconciled in 8.1 (G4 v5's rules adopted where they are G4's). G4 v6 is being drafted.
- M4 (G9's read-back): whichever of G8 and G9 lands second changes G9's read-back standalone test from `_ALNUM` to
  `_joins(placeholder)` (8.1).
- M5: the phase 1+2 step 2 suite list gets nine more files (section 8).
- N1: L-D12's over-mask measured and pinned: AT7 `ORD1234-5678-9012-3456` -> `ORD<CREDITCARD_1>` (not storable).
- N2: the PHONE entries are 6 (`+`-led), 7 (beside `_`), 8 (phone word) everywhere; the main PHONE tuple has no number; the
  mutant file's constant is `E6`.
- N3: line numbers at a5247ac4a, 93c0d08ee and 99787d5b3 (section 0, cite table); model_gate.py's bullet is 12-14.
- N4: PHONE entry 6 gets the date guard right after `+` (`\+(?!\d{4}-\d\d-\d\d)\d...`): MEASURED, v3 masked
  `x+2026-11-20T10:00:00Z` as `x<PHONE_1>T10:00:00Z` and `t+2026-11-20 1012` as `t<PHONE_1>`; both kept now (K81, K82; mutant
  P14).
- N5: the two warden_port UUID-sweep docstrings and the property test's docstring (b) get a G8 sentence (appendix E).
- N6: non-ASCII glue probed (2.7, MEASURED): no leak class; a non-ASCII digit beside a value is not a guard (`[0-9]`) but can be
  taken into the value (`\d`), which makes the original non-storable (fail safe). Stated, no code change.
- Counts: 88 probe rows (+87, +88), 84 must-keep (+K81-K84), 7 at-rest (+AT7), 2 untrusted rows, 34 mutants (+I4, I5, P13,
  P14), 7 hostile cost texts (+`iban underscore`). Appendix D is now a diff against 99787d5b3 (it applies to a5247ac4a with
  offsets -31 / -42, no fuzz: MEASURED).

What changed from v2 (v3's list, kept as v3 wrote it except where marked):
- IBAN start: the fallback `(?<![A-Za-z0-9])` is now the default (F1, measured: the camelCase start left up to 39 characters of
  an opaque token readable; section 2.4). Rows 38, 39, 45 become limits (L4); K24, K25, K66 are kept.
- PHONE entry 6 (v3 said "entry 5" here; CHANGED in v4, N2): `+`-led numbers only (F6 / L-D9 flipped). K34, K70, K71, K72 are back to the base output; row 75 now changes
  (`<PHONE_1><PHONE_2>`, the `+` inside the second placeholder).
- IPv4 dashed forms glued before: the EC2 start is `(?<![A-Za-z0-9])` and the pod-DNS start `(?<![0-9])` (F4): rows 81-84
  closed, rows 85, 86 limit L10.
- CREDITCARD: start `(?<![0-9])`, end `(?![0-9])` (F6 / L9, measured: only K36 and K74 of v2's 156 data rows change; a new
  decision L-D12 with the old behaviour as fallback).
- Data: 86 rows (80 + 6), 80 must-keep rows (74 + 6), 3 full-stop rows, 6 at-rest rows (map and `storable()`).
- Mutants: 30, all run on the patched and `ruff format`ed tree before handoff (section 8 phase 4, section 9): every expect is the
  measured first failing line; the pinned ids carry the case (`[row36]`), which v2's file lacked (all 28 of v2's mutants would
  have been `BAD OTHER_TEST`).
- model_gate.py's guarantee docstring and its pinning test, the redact.py sweep comment (F3) are in the Modify list.
- Order with G4 stated both ways, with the exact edits the G4 builder makes (section 8.1); the G4c host column re-measured with
  G4 v4's HOSTNAME / HOSTKEY (identical to v2's G4 v3 column).
- Cost: a script (appendix F) and a phase 3 command that time the six texts through `redact()` and `runmap.redact_text` on the
  base and the build, with an acceptance rule and the action on failure (section 10).

## 0. Base, what was measured where, and what is NOT RE-MEASURED
- Measured base: cloud/core-c a5247ac4a (2026-11-20 09:45Z): G7 fix rounds 3 to 6 (round 6: 9d8bc580a), gate round 4, P1d-a
  rounds 2 and 3, the gate time-budget flake fix 833a86b and E9 (`_OWN_OUTPUT` restricted to SECRET tokens, e8ff6de2b, merged
  at 09:44Z) are all in it. Every number in this file comes from clean `git archive a5247ac4a` copies in the drafter's
  scratchpad (`base`, the base as is; `v3`, this design written by a script; `mut`, `v3` after `ruff format` with appendices A,
  B, C and F, from which appendix D and E are the diffs; `v3a`, G8a only; `v3camel`, `v3` with v2's camelCase IBAN start;
  `v2h`, v2's design on a5247ac4a; `base_g4` and `v3_g4`, `base` and `v3` with G4 v4's HOSTNAME and HOSTKEY entries). The
  shared tree was not edited and no test was run in it. Appendix D applies to an archive of a5247ac4a with `patch -p1` without
  fuzz (checked).
- v2's tables re-run on a5247ac4a (section 9): v2's `now` column (80 rows, 74 must-keep, 2 full-stop) holds on the base with 0
  differences, and v2's design (`v2h`) gives v2's `after` column with 0 differences. So G7 round 6 and E9 change nothing G8
  measures.
- Line numbers below are those of a5247ac4a.
- HEAD when this file was finished: 93c0d08ee (E9 fix round 1 c4d68c6ef, the Q9 tests and mutants 4fb0b5154 / 6e8bb9820). It
  changes redact.py only in the `_OWN_OUTPUT` comment (875-891: every redact.py line after 880 moves down 6: the sweep call is
  2047, `_ALNUM` 2231, `_replace_standalone` 2234, the `sweep` comment 1992) and appends Q9 tests to tests/test_redact_g3_port.py
  (G8's lines 56-59 move to 59-62). Run on an archive of 93c0d08ee (section 9): step 0 `0 differ`; fail-before `107 failed, 289
  passed, 12 deselected, 20 xfailed`; appendix D and E apply with `patch -p1` (offsets 6 and 3, no fuzz); then the G8 file
  `396 passed, 12 deselected, 20 xfailed`, the g3 port, property, enforce_map and model-gate files `2213 passed`, and the mutants
  `30 of 30 good`. The tables are unchanged on it.
- CHANGED in v4 (G8-review-3-codebase N3): HEAD when v4 was written: 99787d5b3 (adds G7 fix round 7, bff88a7a1, to 93c0d08ee).
  Measured by the v4 drafter on `git archive 99787d5b3` copies in its own scratch folder (`base4`; `v3h` = base4 + appendix D of
  v3; `v4` = v3h + the v4 changes of section 4.1, then `ruff format`): step 0 (`python -m tests.g8_cases`, v3's appendix A)
  `0 differ`; appendix D of v3 applies with `patch -p1`, no fuzz (redact.py hunks 7-8 offset 31, hunks 9-10 offset 42); appendix
  E with offset 3 (g3 port hunk); a scratch row check (not pytest: `check.py`, every probe, must-keep, full-stop and at-rest row
  through `redact`, `redact_many`, `redact_text`, a second `redact_text` and `redact_untrusted`) gives v3's `after` column on
  `v3h` with 0 differences. So G7 round 7 changes nothing G8 measures. Cite table, the same names at the three commits (by name
  first; a line is a hint; MEASURED with `git show <sha>:<file> | grep -n <name>`):

  | name | a5247ac4a | 93c0d08ee | 99787d5b3 |
  |---|---|---|---|
  | IBAN / UUID / EC2 / pod / dotted IPV4 / CREDITCARD entries | 266-274 / 275-280 / 375 / 376 / 377 / 471 | same | same |
  | PHONE comment block / main PHONE tuple | 472-490 / 491-498 | same | same |
  | `_Redactor.sweep` def / its comment / the `_replace_standalone` call | 1982 / 1983-1987 / 2041 | 1988 / 1989-1993 / 2047 | 2013 / 2014-2018 / 2072 |
  | `_ALNUM` / `_replace_standalone` def | 2225 / 2228 | 2231 / 2234 | 2267 / 2270 |
  | runmap.py: `_alias_keys` import / `enforce_map` docstring sentences / `_sweep_held` call | 31 / 699, 718 / 849 | same | same |
  | model_gate.py guarantee bullet (text / its `E::` pin line) | 12-13 / 14 | same | same |
  | tests/test_redact_idempotent_property.py `raw_copies` oracle line / docstring (b) | 141 / 5-7 | same | same |
  | tests/test_redact_g3_port.py re-pointed lines | 56-59 | 59-62 | 59-62 |
  | tests/test_runmap_enforce_map.py pinning test | 263-275 | same | same |
  | tests/warden_port/test_redaction.py UUID-sweep tests (N5) | 243-251, 375-379 | same | same |

  model_gate.py: the bullet G8 edits is lines 12-14 (two text lines and the `E::` pin line); v3's "12-13" named the text lines
  only (N3); appendix D's hunk is unchanged.
- Python: measured on 3.13 only (the repository's `.venv`; pyproject `>=3.12`). The nested look-behind
  `(?<!(?<![A-Za-z])[vV])` is fixed width; on 3.12 by reading only.
- Dependencies named (section 8.1): CHANGED in v4 (M3): G4 v5 (G4-P1c-redactor-gaps-v5.md, blob c96f9c01de99 at 99787d5b3) is
  NOT a copy of v4 as v3 said: it has its own section 0.3 "Order with G8", decision L23 and other new content (for example L21);
  its HOSTNAME regex lines (5.2, 5.3) are the same text as v4's, so v4's measurement stands; the differences that touch G8 are
  reconciled in 8.1. G4 v6 is being drafted (untracked draft read at 10:26Z). G9 (the spelled sweep to a fixed point, v1 and a v2
  draft; edits `_Redactor.sweep`'s loop and adds a read-back that copies the sweep's rule: 8.1, M4); G10 (textfold deadline,
  draft; no G8 line).

## 1. Goal
(CHANGED in v4: for IBAN, `_` counts as glue only in a short-word context, M1, section 4.1.)
A value of kind IPV4, PHONE, IBAN, UUID or CREDITCARD glued straight to a letter or `_` (and for IPV4 / UUID / PHONE in the
shapes of section 2, a digit) is masked in the first `redact()` / `redact_many()` / `runmap.redact_text` call, as P1d-a did for
EMAIL (`(?![A-Za-z])`). The glued text stays in the output, outside the placeholder (`<IPV4_1>a`, `node_<IPV4_1>`). Shapes
that cannot be told from a hash, a version, code or an opaque token are stated limits, pinned by strict xfails. HOSTNAME gets
no G8 code: its "glued before" rows (64, 71) are closed by G4c; its "glued after the suffix" rows are limit L6. Section 1 of v2
promised "IPV4 glued to a letter, a digit or `_`": v3 closes the dashed forms glued before too (F4), except a letter right
before `ip-` / `ec2-` and a digit before the pod-DNS address (L10).

## 2. Problem (what the probe shows on a5247ac4a)
Not a fixed-point problem: a second `redact()` on the output masks nothing more in any of the 86 rows. It is a boundary problem
in six pattern entries and one sweep rule:
- `IPV4` dotted (redact.py:377), EC2 dashed (375) and pod DNS (376) start and end with `\b`: a letter or `_` on either side
  refuses the match (`host_ip-192-0-2-10`, `my_ec2-...`, `pod_192-0-2-10.ns.pod` are not masked).
- `PHONE` (491-498) refuses a start after `\w . -` and an end before `\w .` (on purpose: hashes and identifiers, comment
  472-490). A formatted phone followed by a letter or `_` is not masked, or only in part (`<PHONE_1> 1234a`).
- `IBAN` (266-274) starts and ends with `\b`: `_x` after or `_` before refuses it. A letter or digit after is absorbed into the
  BBAN (rows 34, 35 are masked today and stay so).
- `UUID` (275-280) starts and ends with `\b`: anything glued refuses it; with a prefix glued, `ACCOUNTID` takes the last 12
  digits and 24 of 36 characters stay readable.
- `CREDITCARD` (471) starts and ends with `\b`: `x4242 4242 4242 4242` is masked by PHONE as `x4242 <PHONE_1>`: one group stays
  readable and 12 digits of a card go to the run map at rest as PHONE (K36, K74, F6 / L9).
- The identifier sweep (`_replace_standalone`, redact.py:2228, called at 2041 in `_Redactor.sweep` 1982 and at runmap.py:849 in
  `_sweep_held`) refuses a copy that an ASCII letter or digit touches, so a clean copy of a contiguous phone number does not
  mask its letter-glued copy (row 31). IBAN is a SECRET kind (`_EVERY_COPY`): its glued copies are already swept (row 43).

### 2.1 Counts (88 probe rows: 83 glued shapes + 5 controls at rows 1, 17, 33, 46, 59; CHANGED in v4: rows 87, 88 added)
| kind | rows | leak today | closed by G8 v4 | output changes, no leak either way | stated limit after G8 | closed by G4c (not G8) | unchanged, no leak |
|---|---|---|---|---|---|---|---|
| IPv4 | 25 | 23 | 19 | 0 | 4 (10, 13, 85, 86) | 0 | 2 |
| phone | 17 | 13 | 11 | 3 (21, 22: the `+` moves inside; 75: `<PHONE_1><PHONE_2>`) | 2 (25, 27) | 0 | 1 |
| IBAN | 16 (v4) | 12 (v4) | 5 | 0 | 7 (38, 39, 40, 45, 76, 87, 88; v4) | 0 | 4 |
| UUID | 14 | 13 | 13 | 0 | 0 | 0 | 1 |
| host name | 16 | 9 | 0 | 0 | 7 (67-70, 78-80) | 2 (64, 71) | 7 |
| total | 88 | 70 | 48 | 3 | 20 | 2 | 15 |
Rows: closed 48, left 22 (20 limits + 2 closed by G4c), limits 20. `redact()`, `redact_many([text, "other line"])` and
`runmap.redact_text` give the same output in all 86 rows on the base and with v3; `redact_untrusted` equals `redact_text` and a
second `redact_text` with the same run map changes neither text nor map in all 86 rows with v3 (tests of section 7, run).
CHANGED in v4: the same five properties hold in all 88 rows on `v4` at 99787d5b3 (MEASURED by the scratch row check, not by
pytest), and `redact_untrusted` of a placeholder-shaped literal is pinned separately (U1, U2: M2).
Card numbers are not a probe kind: the two card rows are must-keep rows K36, K74 (and K80), verdict "closed (L-D12)".

### 2.2 Probe rows (data: appendix A, `ROWS`; values: `V` there, all fake or documentation values built from parts)
Values: `{IP1}` 192.0.2.10, `{IP2}` 198.51.100.7, `{IP3}` 203.0.113.45 (RFC 5737), `{IPD}` 192-0-2-10; `{PHONE_P}`
+1 415-555-0132, `{PHONE_P2}` +1 415-555-0199, `{PHONE10}` 4155550132, `{PHONEUK}` +44 20 5550 1234 (555 numbers);
`{IBAN_DE}`, `{IBAN_GB}` (the published example IBANs); `{UUID}` (the RFC example), `{UUIDUP}` upper case, `{UUID2}` a second
one, `{UUIDHEAD}` its first 24 characters; host names `{HOST}` db-7.corp.internal, `{HOST2}` db01.prod.corp, `{HOST3}`
nas02.office.lan, `{HOST4}` printer7.local, `{HOST5}` a.b.c.internal (made up). Leak rule: `leak()` in appendix A (ipv4 7
characters of the value in a row, iban and uuid 8, phone 4 digits once spaces and hyphens are removed, host: any label other
than corp, internal, local, lan, intranet, prod, office, or 2 or more leading characters of one directly before a placeholder).
Row 6 (`{IP1}9`) is the address 192.0.2.109 masked as its own value, not a leak.
Column "after G8 with G4c": only where it differs (`same` otherwise); measured with G4 v4 sections 5.2 and 5.3 (section 4.5).
Rows that differ from v2 are marked (v3).

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
| 38 (v3) | iban | letter before | `pay x{IBAN_DE} now` | `pay x{IBAN_DE} now` | `pay x{IBAN_DE} now` | same | limit |
| 39 (v3) | iban | word before | `pay iban{IBAN_DE} now` | `pay iban{IBAN_DE} now` | `pay iban{IBAN_DE} now` | same | limit |
| 40 | iban | digit before | `pay 7{IBAN_DE} now` | `pay 7{IBAN_DE} now` | `pay 7{IBAN_DE} now` | same | limit |
| 41 | iban | _ before | `pay iban_{IBAN_DE} now` | `pay iban_{IBAN_DE} now` | `pay iban_<IBAN_1> now` | same | closed |
| 42 | iban | both _ | `pay to_{IBAN_DE}_x now` | `pay to_{IBAN_DE}_x now` | `pay to_<IBAN_1>_x now` | same | closed |
| 43 | iban | clean copy + _x copy | `pay {IBAN_DE} or {IBAN_DE}_x now` | `pay <IBAN_1> or <IBAN_1>_x now` | `pay <IBAN_1> or <IBAN_1>_x now` | same | unchanged |
| 44 | iban | GB, _x after | `pay {IBAN_GB}_x now` | `pay {IBAN_GB}_x now` | `pay <IBAN_1>_x now` | same | closed |
| 45 (v3) | iban | GB, letter before | `pay x{IBAN_GB} now` | `pay x{IBAN_GB} now` | `pay x{IBAN_GB} now` | same | limit |
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
| 75 (v3) | phone | two formatted phones glued | `call {PHONE_P}{PHONE_P2} now` | `call <PHONE_1>+<PHONE_2> now` | `call <PHONE_1><PHONE_2> now` | same | changed |
| 76 | iban | two IBANs glued | `pay {IBAN_DE}{IBAN_GB} now` | `pay {IBAN_DE}{IBAN_GB} now` | `pay {IBAN_DE}{IBAN_GB} now` | same | limit |
| 77 | uuid | two UUIDs glued | `id {UUID}{UUID2} ok` | `id {UUID}{UUID2} ok` | `id <UUID_1><UUID_2> ok` | same | closed |
| 78 | host | bare .local, digit after | `x {HOST4}9 y` | `x {HOST4}9 y` | `x {HOST4}9 y` | same | limit |
| 79 | host | bare .local, _x after | `x {HOST4}_x y` | `x {HOST4}_x y` | `x {HOST4}_x y` | same | limit |
| 80 | host | bare .internal, letter after | `x {HOST5}x y` | `x {HOST5}x y` | `x {HOST5}x y` | same | limit |
| 81 (v3) | ipv4 | dashed EC2 name, _ before | `node host_ip-{IPD} up` | `node host_ip-{IPD} up` | `node host_ip-<IPV4_1> up` | same | closed |
| 82 (v3) | ipv4 | dashed EC2 name (ec2), _ before | `node my_ec2-{IPD} up` | `node my_ec2-{IPD} up` | `node my_ec2-<IPV4_1> up` | same | closed |
| 83 (v3) | ipv4 | pod DNS, _ before | `pod_{IPD}.ns.pod up` | `pod_{IPD}.ns.pod up` | `pod_<IPV4_1>.ns.pod up` | same | closed |
| 84 (v3) | ipv4 | pod DNS, letter before | `x{IPD}.ns.pod up` | `x{IPD}.ns.pod up` | `x<IPV4_1>.ns.pod up` | same | closed |
| 85 (v3) | ipv4 | dashed EC2 name, letter before ip- | `node xip-{IPD} up` | `node xip-{IPD} up` | `node xip-{IPD} up` | same | limit |
| 86 (v3) | ipv4 | pod DNS, digit before | `7{IPD}.ns.pod up` | `7{IPD}.ns.pod up` | `7{IPD}.ns.pod up` | same | limit |
| 87 (v4) | iban | snake_case key, _ before | `pay acct_iban_{IBAN_DE} now` | `pay acct_iban_{IBAN_DE} now` | `pay acct_iban_{IBAN_DE} now` | same | limit (L4, M1: the word before `_` must start its token) |
| 88 (v4) | iban | _ + 9 letters after | `pay {IBAN_DE}_reference now` | `pay {IBAN_DE}_reference now` | `pay {IBAN_DE}_reference now` | same | limit (L4, M1: at most 8 characters after `_`) |

### 2.3 The reviewers' examples and v2's hand traces, run on a5247ac4a (`redact()`; `runmap.redact_text` gave the same text)
| input | base | v2 design on a5247ac4a | v3 | what is true |
|---|---|---|---|---|
| `eth0 1500 9000`, `PO12-3456-7890`, `INV2026-0042-1234`, `ISBN978-3-16-148410-0`, `sha256-3851007894abcdef0123`, `rev 2-3851007894abcdef`, `backup_20-11-2026 done`, `ref hunter123-45-6789`, `<TENANT_4155550132>`, `ssn 123-45-6789a` | unchanged | unchanged | unchanged | as the codebase reviewer traced |
| `rtt 120 118 131 125ms` | `rtt <PHONE_1> 125ms` | `rtt <PHONE_1>ms` | `rtt <PHONE_1> 125ms` (= base) | L-D9 flipped: entry 6 is `+`-led only (CHANGED in v4: numbered 6, N2) |
| `call 415-555-0132x123` | unchanged | `call <PHONE_1>x123` | unchanged (= base) | L-D9 flipped (K72) |
| `x4242 4242 4242 4242` | `x4242 <PHONE_1>` (map `4242 4242 4242`, storable) | same as base | `x<CREDITCARD_1>` (not storable) | L-D12 (K36) |
| `card 4242 4242 4242 4242x` | `card <PHONE_1> 4242x` | same as base | `card <CREDITCARD_1>x` | L-D12 (K74) |
| `python3.11.4.1`, `nginx_1.18.0.1-1_amd64.deb`, `1.2.3.4rc1` | unchanged | `python<IPV4_1>`, `nginx_<IPV4_1>-1_amd64.deb`, `<IPV4_1>rc1` | same as v2 | over-mask, L-D8 |
| `order_1234567890` | unchanged | `order_<PHONE_1>` | same as v2 | over-mask, L-D10 |
| `password=hunter` + newline + `ref hunter123-45-6789` | `password=<SECRET_1>\nref <SECRET_1><SSN_1>` | same | same | the G7 boundary test stays byte-identical (K42) |
| `known 1.2.3.4 and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | same | same | L-D1 (K67) |
| `ts+1000000000` | `ts+<PHONE_1>` | `ts<PHONE_1>` | `ts<PHONE_1>` | the `+` moves inside (K62) |
| `call 4155550132 or +1 415-555-0132` | `<PHONE_1> or <PHONE_2>` | `<PHONE_2> or <PHONE_1>` | same as v2 | numbering (K65) |
| `+123-45-6789x` | unchanged | `<PHONE_1>x` | `<PHONE_1>x` (stored as PHONE) | L-D11 (K78) |
| `x+123-45-6789` | `x+<SSN_1>` | same | same | the SSN entry runs first (K79) |
| `host_ip-192-0-2-10 up`, `my_ec2-192-0-2-10 up` | unchanged | unchanged | `host_ip-<IPV4_1> up`, `my_ec2-<IPV4_1> up` | F4 closed (rows 81, 82) |
| `xip-192-0-2-10 up`, `zip-192-0-2-10 up`, `7192-0-2-10.ns.pod up` | unchanged | unchanged | unchanged | L10 (rows 85, 86) |
| `host_ip-192-0-2-10.eu-west-1.compute.internal up` | `host_ip-<HOSTNAME_1> up` | same | `host_ip-<IPV4_1>.eu-west-1.compute.internal up` | IPV4 now runs first; the rest is a kept cloud suffix (`_KEPT_HOST`); no leak either way |
| `call 415-555-0132.`, `call 4155550132.`, `call +1 415-555-0132.` | unchanged | unchanged | unchanged | L7 (section 6, L-D13) |
| `call +1 415-555-0132+1 415-555-0199 now` | `<PHONE_1>+<PHONE_2>` | same as base | `<PHONE_1><PHONE_2>` | row 75 (v3): entry 6 masks the first number, the main entry then takes `+1 415-555-0199` after `>` (CHANGED in v4: numbered 6, N2) |

CHANGED in v4: the codebase reviewer's round 3 examples, run on 99787d5b3 (`base4`, `v3h`, `v4`; `redact()` unless named):
| input | base | v3 | v4 | what is true |
|---|---|---|---|---|
| `redact_untrusted("<TENANT_4155550132>")` | `‹TENANT_4155550132›`, map empty | `‹TENANT_<PHONE_1>›`, map `<PHONE_1>` = `4155550132` | `‹TENANT_4155550132›`, map empty | M2: the escape runs first; entry 7 now refuses `›` (U1) |
| `redact("‹TENANT_4155550132›")` | unchanged | `‹TENANT_<PHONE_1>›` | unchanged | M2 (U2) |
| `<TENANT_tel4155550132>` | unchanged | `<TENANT_tel<PHONE_1>>` | `<TENANT_tel<PHONE_1>>` | not placeholder-shaped (`n` is not digits): entry 8 masks a number after a phone word, as designed; no change |
| `x+2026-11-20T10:00:00Z` | unchanged | `x<PHONE_1>T10:00:00Z` (stored as PHONE) | unchanged | N4 (K81) |
| `t+2026-11-20 1012 ok` | unchanged | `t<PHONE_1> ok` | unchanged | N4 (K82) |
| `at +2026-11-20 10:00 ok` | `at <PHONE_1>:00 ok` | same | same | the MAIN entry's own behaviour on the base (its date guard sits before `\+?`): not G8's, unchanged |
| `ORD1234-5678-9012-3456` | unchanged, map empty | `ORD<CREDITCARD_1>` | `ORD<CREDITCARD_1>`, not storable | N1: L-D12's over-mask (AT7) |
| `INV_1234-5678-9012-3456_x` | unchanged | `INV_<CREDITCARD_1>_x` | same | L-D12 (as K80) |

### 2.4 F1 measured: an IBAN-shaped tail inside an opaque token (scratch script f1.py; base, v3 and v3camel)
Method: random tokens of the 62 ASCII letters and digits (seed 20261120), each written as `key <token> end` (HIGHENTROPY context)
and `Authorization: Bearer <token> end` (BEARER context); "readable" = the longest run of the token's characters left outside the
placeholders. Injected: the token ends `a` + `DE89` + 18 letters or digits. Run twice with the same seed: on archives of 2e3a081ae
(G7 round 6, before E9) and of a5247ac4a (`base`, `mut`, `v3camel`): identical numbers, shown below.
| tokens | context | n | base: tokens with readable text / IBAN in the map | v3 (`mut`, start `(?<![A-Za-z0-9])`) | v2 camelCase start (`v3camel`) |
|---|---|---|---|---|---|
| injected, 129-163 characters | key | 350 | 0 / 0 | 0 / 0 | 0 readable / 350 split (`<HIGHENTROPY_1><IBAN_1>`, two map entries) |
| injected, 129-163 | Bearer | 350 | 0 / 0 | 0 / 0 | 0 readable / 350 split (`<BEARER_2>` + `<IBAN_1>` in the map) |
| injected, 40-128 | key | 356 | 0 / 0 | 0 / 0 | 89 readable (10-39 characters each) / 356 |
| injected, 40-128 | Bearer | 356 | 0 / 0 | 0 / 0 | 0 readable / 356 split |
| random, 40-61 | key | 20,000 | 3 / 0 (the 3: no digit or no upper case, HIGHENTROPY's own rule; same on all trees) | 3 / 0 | 92 readable (up to 45) / 93 |
| random, 62-75 | key | 20,000 | 0 / 0 | 0 / 0 | 25 readable (30-39) / 103 |
| random, 129-163 | key | 20,000 | 0 / 0 | 0 / 0 | 0 readable / 94 split |
| random, 40-163 | Bearer | 20,000 each | 0 / 0 | 0 / 0 | 0 readable / 91-97 split |
What is true: the reviewer's mechanism is real, the length window is not. For 129-163 characters the head left before the IBAN
(95 or more characters) is still masked, by the 40+ HIGHENTROPY entry (redact.py:676-681), so nothing is readable; the cost there
is a credential split into two map entries. The leak is for tokens of about 40 to 75 characters, where the head is under 40
characters and no pattern takes it: 0.46 percent of random 40-61-character tokens and 0.13 percent of 62-75-character ones keep
up to 39 (measured maximum 45, counting the 3 base cases) characters readable. BEARER never leaks text (its match runs before and
takes the token whole) but its map holds the split pieces. The start `(?<![A-Za-z0-9])` gives the base's behaviour in every class
(0 tokens with an IBAN). Decision: L-D2 default is the fallback start (section 6). Rows K75 (60 characters), K76 (140), K77
(Bearer, 60) pin it, with `test_an_iban_never_starts_inside_an_opaque_token` asserting one map entry.
CHANGED in v4 (G8-review-3-codebase M1): the two sentences "gives the base's behaviour in every class" and "0 tokens with an
IBAN" are WITHDRAWN. They hold only for tokens of the 62 letters and digits, the alphabet v3 drew from. In base64url (`-`, `_`)
and standard base64 (`+`, `/`) tokens, v3's start and end take `_` as a break inside the token; the base itself takes `-`, `+`
and `/` (a `\b`). Measured in 2.4b; the v4 fix is in 4.1 (L-D15).

### 2.4b M1 measured: an IBAN shape at a separator inside a base64url / base64 token (CHANGED in v4; scratch m1.py; MEASURED)
Method: trees `base4` (99787d5b3), `v3h` (v3's appendix D on it), `A2` (v3h with the start `(?<![A-Za-z0-9_])` only), `E` (v3h
with the short-word context, without the `-`/`+`/`/` end guard), `v4` (the default of 4.1; measured as the variant `E3`, whose
IBAN regex is the same string, sha1 prefix 1e99398ea2e3, 693 characters). Random tokens (Python `random`, string seeds
`20261120|<class>|<ctx>`) of the base64url alphabet (A-Z a-z 0-9 `-` `_`) or the standard alphabet (A-Z a-z 0-9 `+` `/`), 20,000
per class, written `key <token> end` or `Authorization: Bearer <token> end`, through `redact()`. Injected: a random alphanumeric
head, then `_` or `-`, `DE89` + 18 letters or digits, then `_`, `-` or the token's end, then a random tail (1,000 per class).
"readable" = 8 or more token characters in a row outside the placeholders AND an `<IBAN_n>` in the map (a token without an IBAN
that HIGHENTROPY leaves readable is HIGHENTROPY's own rule, not counted); "split" = more than one map entry.

Random tokens, summed over the four length classes 40-61, 62-75, 76-128, 129-163 (80,000 tokens per row):
| alphabet / context | base4: readable / IBAN in map / split | v3h | A2 | E | v4 (E3) |
|---|---|---|---|---|---|
| base64url / key | 9 / 22 / 17 | 22 / 57 / 47 | 14 / 39 / 31 | 9 / 25 / 20 | 9 / 22 / 17 |
| base64url / Bearer | 0 / 20 / 21 | 0 / 47 / 48 | 0 / 29 / 30 | 0 / 22 / 23 | 0 / 21 / 22 |
| base64 (`+` `/`) / key | 26 / 57 / 45 | same | same | same | same |
| base64 (`+` `/`) / Bearer | 0 / 43 / 43 | same | same | same | same |
Per class (base64url, `key`; readable / IBAN in map, longest readable run): 40-61: base 4/4 (39), v3h 7/7 (39), v4 4/4 (39);
62-75: 1/5, 3/8, 1/5; 76-128: 1/7, 2/18, 1/7; 129-163: 3/6 (13), 10/24 (31), 3/6 (13). The one v4 difference from the base is
one more split (no readable text, BEARER takes the whole token first) in the 129-163 Bearer class: an IBAN after a word of
letters that starts the token (`ab_DE89...`), the context v4 accepts by design.

Injected (1,000 each; readable / IBAN in map, longest readable run):
| shape | length | base4 | v3h | A2 | E | v4 (E3) |
|---|---|---|---|---|---|---|
| `head_DE89..._tail` | 40-75 | 0 / 0 | 934 / 1000 (39) | 0 / 0 | 0 / 0 | 0 / 0 |
| `head_DE89..._tail` | 129-163 | 0 / 0 | 584 / 1000 (43) | 0 / 1 | 0 / 0 | 0 / 0 |
| `head_DE89...` (token end) | 40-75 | 0 / 0 | 702 / 1000 (39) | 0 / 0 | 18 / 120 (9) | 18 / 120 (9) |
| `head_DE89...` (token end) | 129-163 | 0 / 0 | 266 / 1000 (39) | 0 / 0 | 5 / 25 (9) | 5 / 25 (9) |
| `head-DE89..._tail` | 40-75 | 0 / 0 | 930 / 1000 (39) | 930 / 1000 (39) | 237 / 273 (39) | 0 / 0 |
| `head-DE89..._tail` | 129-163 | 0 / 1 | 520 / 1000 (39) | 520 / 1000 (39) | 17 / 57 (9) | 0 / 1 |
| `head-DE89...-tail` | 40-75 | 941 / 999 (39) | same | same | same | same |
| `head-DE89...-tail` | 129-163 | 510 / 1000 (39) | same | same | same | same |
| `head-DE89...` (token end) | 40-75 | 749 / 1000 (39) | same | same | same | same |
| `head-DE89...` (token end) | 129-163 | 259 / 1000 (39) | same | same | same | same |
Read:
- v3's leak is real and is the `_` share: v3 adds 13 readable tokens per 80,000 random base64url `key` tokens to the base's 9
  (about 1.6e-4 per token; the reviewer's estimate, about 1e-4 per `_` position, is the same order), and about 30 more split map
  entries under `key` and under `Bearer`. Up to 39 characters of a head stay readable (43 in one injected long token).
- v4 (E3) equals the base in readable text in all 16 random classes and in the injected `_` classes, except where the 2-8
  characters before `_` are letters that start the token (`head_DE89...` with a short all-letter head: 18 of 120 and 5 of 25 IBAN
  matches leave the head word readable, at most 9 characters, which is the word itself): that is the shape of row 41
  (`iban_DE89...`) and cannot be told apart from it by a pattern.
- `E` without the `-`/`+`/`/` end guard still leaks `head-DE89..._x` at a token end (237 of 1,000 short injected tokens): so
  both halves of `_IBAN_START` are needed.
- A2 (the one-character start fix) halves v3's extra but keeps the `_` END inside tokens (`-DE89..._`): 14 readable vs the base's
  9; it also turns rows 41, 42 into limits.
- The base itself splits an IBAN shape that starts after `-`, `+`, `/` (or at the token's start) and ends at `-`, `+`, `/` or the
  token's end: 9 readable per 80,000 base64url and 26 per 80,000 base64 `key` tokens; 941 of 999 injected short `-DE89...-`
  tokens. This is NOT a G8 change (v3h, A2, E and v4 give the same numbers): limit L12, follow-up L-D16.
- BEARER never leaves token text readable (it takes the token before IBAN runs); its map can hold the split pieces.
Wall time: 139-153 s per tree on a box with load 2.8-3.3; the numbers do not depend on time.

### 2.5 At rest and `storable()` (F6; `redact()` map and `runmap.storable(map)`; appendix A `AT_REST`)
| id | text | base: text / map / storable | v3 | what is true |
|---|---|---|---|---|
| AT1 | `password=hunter192.0.2.10x` | `password=<SECRET_1>` / SECRET only / none | same text; map adds `<IPV4_1>` = `192.0.2.10`; storable: `<IPV4_1>` | a piece of a password is stored at rest as IPV4 (limit L11) |
| AT2 | `password=hunter_4155550132` | SECRET only / none | map adds `<PHONE_1>` = `4155550132`; storable: it | the same, PHONE (L11) |
| AT3 | `token=x+14155550132y` | SECRET only / none | map adds `<PHONE_1>` = `+14155550132`; storable: it | the same (L11) |
| AT4 | `password=a-192.0.2.10-b` | `<IPV4_1>` in the map and storable already | same | the base does it today for a piece set off by `-` or `.`: G8 widens an existing class, it does not start it |
| AT5 | `arn:aws:s3:::bucket_DE89370400440532013000` | `<ARN_1>`, storable | `<ARN_1>`, NOT storable | IBAN is in `runmap._SECRET_PATTERNS` (runmap.py:256-258): an original holding `_DE89...` now fails `storable_original` (fail safe: not stored, so not restorable after the run) |
| AT6 | `tenant_id=acme_DE89370400440532013000` | `<TENANT_1>` = `acme_DE89...` | `tenant_id=<TENANT_1><IBAN_1>`, TENANT = `acme_` | the IBAN is masked first; the tenant value is cut (fail safe) |
| AT7 (v4, N1) | `ORD1234-5678-9012-3456` | unchanged / empty / none | `ORD<CREDITCARD_1>`; map `<CREDITCARD_1>` = `1234-5678-9012-3456`; storable: none | L-D12's over-mask: an order number in card groups glued to letters is masked as a card; CREDITCARD is a SECRET kind, so it is never stored and the evidence is not restorable after the run (fail safe; MEASURED on `v4`) |
With v2's camelCase start, `tenant_id=acmeDE89...` would be cut too; with v3's start it is not (measured: unchanged).
CHANGED in v4: AT5 and AT6 are unchanged by v4's IBAN context (`bucket_` and `acme_` are short words that start their token
after `:` / `=`): MEASURED on `v4`, the same three columns as v3.
Why G8 does not fix L11: the class exists on the base (AT4); a fix belongs in `runmap.storable` or in map pruning for every kind,
not in four patterns (L-D14 offers it as a follow-up ticket).

### 2.6 Must-keep rows (appendix A, `MUST_KEEP`: 84 rows; K1-K28 v1's table, K29-K74 v2's, K75-K80 v3's, K81-K84 v4's: CHANGED in v4)
Verdicts: kept (nothing masked, before and after) | same (masked today; G8 leaves it, or changes only what the note says) |
over-mask L-Dn (accepted, owned by that decision) | closed (a real value newly masked). Tokens: `{SHA}` a 64-hex digest
starting 3851007894, `{SHA16}` its first 16, `{CARD}` 4242 4242 4242 4242, `{SSN}` 123-45-6789, `{UUIDHEX}` the UUID without
dashes, `opaque(n)` n characters of `ALNUM[(7 * i + 3) % 62]`, `{F1}` `aDE89Xq7Lm2Pw9Rt4Ys6Vb3`. Measured on a5247ac4a (base
column) and `mut` (after column); 80 of 80 as listed. Rows that differ from v2 are marked (v3).

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
| K24 (v3) | `req ReqIdDE12345678901234 ok` | `req ReqIdDE12345678901234 ok` | `req ReqIdDE12345678901234 ok` | kept (L-D2) |
| K25 (v3) | `tag xDE00ABCDEFGHIJK ok` | `tag xDE00ABCDEFGHIJK ok` | `tag xDE00ABCDEFGHIJK ok` | kept (L-D2) |
| K26 | `ts 1732095071000_x` | `ts 1732095071000_x` | `ts <PHONE_1>_x` | over-mask L-D10 |
| K27 | `uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe` | `uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe` | `uuid-ish <UUID_1>cafe` | over-mask L-D4 |
| K28 | `id {UUIDHEX} ok` | `id {UUIDHEX} ok` | `id {UUIDHEX} ok` | kept |
| K29 | `eth0 1500 9000` | `eth0 1500 9000` | `eth0 1500 9000` | kept |
| K30 | `ipv4 1500 1600` | `ipv4 1500 1600` | `ipv4 1500 1600` | kept |
| K31 | `vlan10 2001 2002` | `vlan10 2001 2002` | `vlan10 2001 2002` | kept |
| K32 | `node1 8080 9090` | `node1 8080 9090` | `node1 8080 9090` | kept |
| K33 | `PO12-3456-7890` | `PO12-3456-7890` | `PO12-3456-7890` | kept |
| K34 (v3) | `rtt 120 118 131 125ms` | `rtt <PHONE_1> 125ms` | `rtt <PHONE_1> 125ms` | same (L-D9: 3 of 4 masked today) |
| K35 | `backup_20-11-2026 done` | `backup_20-11-2026 done` | `backup_20-11-2026 done` | kept |
| K36 (v3) | `x{CARD}` | `x4242 <PHONE_1>` | `x<CREDITCARD_1>` | closed (L-D12) |
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
| K66 (v3) | `blob aGVsbG8+aDE12abcdefghijk/x` | `blob aGVsbG8+aDE12abcdefghijk/x` | `blob aGVsbG8+aDE12abcdefghijk/x` | kept (L-D2) |
| K67 | `known 1.2.3.4 and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | `known <IPV4_1> and v1.2.3.4` | same (L-D1) |
| K68 | `rev 2-{SHA16}` | `rev 2-{SHA16}` | `rev 2-{SHA16}` | kept |
| K69 | `color #415555 and #0a0b0c` | `color #415555 and #0a0b0c` | `color #415555 and #0a0b0c` | kept |
| K70 (v3) | `sizes 1024 2048 4096ms` | `sizes 1024 2048 4096ms` | `sizes 1024 2048 4096ms` | kept (L-D9) |
| K71 (v3) | `took 100 200 300 400ms` | `took <PHONE_1> 400ms` | `took <PHONE_1> 400ms` | same (L-D9: 3 of 4 masked today) |
| K72 (v3) | `call 415-555-0132x123` | `call 415-555-0132x123` | `call 415-555-0132x123` | kept (L-D9: an extension glued to a number without + stays readable) |
| K73 | `ssn {SSN}a` | `ssn {SSN}a` | `ssn {SSN}a` | kept (L-D11: a stated limit, not a choice) |
| K74 (v3) | `card {CARD}x` | `card <PHONE_1> 4242x` | `card <CREDITCARD_1>x` | closed (L-D12) |
| K75 (v3) | `key opaque(37){F1} end` | `key <HIGHENTROPY_1> end` | `key <HIGHENTROPY_1> end` | same (L-D2: F1, 60 characters) |
| K76 (v3) | `key opaque(117){F1} end` | `key <HIGHENTROPY_1> end` | `key <HIGHENTROPY_1> end` | same (L-D2: F1, 140) |
| K77 (v3) | `Authorization: Bearer opaque(37){F1} end` | `Authorization: Bearer <BEARER_1> end` | `Authorization: Bearer <BEARER_1> end` | same (L-D2: F1, BEARER) |
| K78 (v3) | `+{SSN}x` | `+{SSN}x` | `<PHONE_1>x` | over-mask L-D11 (stored as PHONE) |
| K79 (v3) | `x+{SSN}` | `x+<SSN_1>` | `x+<SSN_1>` | same (the SSN entry runs first) |
| K80 (v3) | `card_{CARD with -}_x` | `card_{CARD with -}_x` | `card_<CREDITCARD_1>_x` | closed (L-D12) |
| K81 (v4) | `x+2026-11-20T10:00:00Z` | `x+2026-11-20T10:00:00Z` | `x+2026-11-20T10:00:00Z` | kept (N4; v3 gave `x<PHONE_1>T10:00:00Z`) |
| K82 (v4) | `t+2026-11-20 1012 ok` | `t+2026-11-20 1012 ok` | `t+2026-11-20 1012 ok` | kept (N4; v3 gave `t<PHONE_1> ok`) |
| K83 (v4) | `key opaque(20)_{F1_MID}-opaque(17) end` | `key <HIGHENTROPY_1> end` | `key <HIGHENTROPY_1> end` | same (L-D15, M1: `_` before, `-` after; v3 gave `key <head>_<IBAN_1>-<tail> end`) |
| K84 (v4) | `key opaque(20)-{F1_MID}_opaque(5) end` | `key <HIGHENTROPY_1> end` | `key <HIGHENTROPY_1> end` | same (L-D15, M1: `-` before, `_` after; v3 gave `key <head>-<IBAN_1>_<tail> end`) |
`{F1_MID}` is `DE89Xq7Lm2Pw9Rt4Ys6Vb3` (F1's tail without its `a`). K83 and K84 are also asserted with one map entry by
`test_an_iban_never_starts_inside_an_opaque_token` (OPAQUE ids K75, K76, K77, K83, K84). Base and after columns MEASURED on
`base4` and `v4` (84 of 84).

Full-stop rows (L7, unchanged): F1 `call 415-555-0132.`, F2 `call 4155550132.`, F3 `call +1 415-555-0132.` (v3).
Untrusted rows (CHANGED in v4, M2; appendix A `UNTRUSTED`): U1 `redact_untrusted("<TENANT_4155550132>")` ==
`‹TENANT_4155550132›` with an empty map; U2 `redact_text("‹TENANT_4155550132›")` unchanged with an empty map. Base: both hold;
v3h: both give `‹TENANT_<PHONE_1>›` and a PHONE entry; v4: both hold (MEASURED).

### 2.7 Non-ASCII glue (CHANGED in v4, G8-review-3-codebase N6; scratch probe.py, `redact()`; MEASURED on `base4`, `v3h`, `v4`)
The new guards are ASCII classes (`[0-9]`, `[A-Za-z0-9]`), the bodies use `\d` (Unicode digits in a `str` pattern), and the
fold scan reads folded views. v3h and v4 give the same outputs:
| input | base | v4 | what is true |
|---|---|---|---|
| `from х192.0.2.10 ok` (Cyrillic х before) | unchanged | `from х<IPV4_1> ok` | a non-ASCII letter is glued text, like an ASCII one |
| `from 192.0.2.10х ok` | unchanged | `from <IPV4_1>х ok` | the same after |
| `from ٧192.0.2.10 ok` (Arabic-Indic 7 before) | unchanged | `from ٧<IPV4_1> ok` | a non-ASCII digit is not a guard (`[0-9]`): masked (L1 holds for ASCII digits only) |
| `from ７192.0.2.10 ok` (full-width 7 before) | unchanged | `from ７<IPV4_1> ok` | the same |
| `from 192.0.2.10٩ ok` | `from <IPV4_1> ok`, original `192.0.2.10٩`, not storable | same | the BASE already takes a Unicode digit into the value (`\d`): not restorable after the run (fail safe) |
| `call tel_4155550132٧ now` | unchanged | `call tel_<PHONE_1> now`, original `4155550132٧`, not storable | entry 7 takes the Unicode digit into the value (`\d{10,16}`); fail safe |
| `call ١٢٣٤٥٦٧٨٩٠_x now` | unchanged | `call <PHONE_1>_x now`, not storable | entry 7 masks an Arabic-Indic digit run beside `_` |
| `call +1 415-555-0132а now` (Cyrillic а after) | unchanged | `call <PHONE_1>а now` | as an ASCII letter |
| `id х123e4567-...-426614174000 ok` | `id х123e4567-e89b-12d3-a456-<ACCOUNTID_1> ok` | `id х<UUID_1> ok` | closed, as row 52 |
| `pay хDE89370400440532013000 now` | unchanged | `pay х<IBAN_1> now` | a non-ASCII letter before an IBAN is not in `_IBAN_START`'s ASCII class: masked (L4 is for ASCII letters only; fail safe) |
| `pay DE89370400440532013000х now` | `[line withheld: look-alike text hid a protected value] <IBAN_1>` | same | the fold scan's own rule on the base; unchanged |
Read: no non-ASCII shape leaks more with G8 than on the base; non-ASCII glue is masked more, and a Unicode digit taken into a
value makes it non-storable. No code change (consistent fail-safe direction); stated in section 11 (L13).

## 3. Files
Modify:
- `src/hadavin_sdk/guard/redact.py`: CHANGED in v4: two module constants `_IBAN_START`, `_IBAN_END` directly after
  `_NOT_IN_WORD` (74) (M1); the IBAN (266-274), UUID (275-280), EC2 (375), pod-DNS (376), dotted IPV4 (377) and
  CREDITCARD (471) entries; three new PHONE entries (CHANGED in v4, N2: entry 6 directly before the main PHONE tuple 491-498,
  entries 7 and 8 directly after it; the main tuple itself is unchanged and has no number); a comment above each changed or new entry; one paragraph in the module docstring; the `sweep` comment (1983-1987,
  F3: the UUID `_0` copy is now the pattern's own match); `_JOINS` and `_joins()` after `_ALNUM` (2225); the `joins` parameter
  and docstring of `_replace_standalone` (2228-2244); the one call in `_Redactor.sweep` (2041). Exact text: section 4 and
  appendix D.
- `src/hadavin_sdk/guard/runmap.py`: import `_joins` at line 32 (after `_alias_keys`, 31; F6); `_sweep_held` (849) passes
  `_joins(placeholder)`; two sentences of the `enforce_map` docstring (699, 718).
- `src/hadavin_sdk/guard/model_gate.py:12-14` (F3; CHANGED in v4, N3: the bullet is lines 12-14, the hunk edits 13): the guarantee "replaced only where no ASCII letter or digit touches it" gets
  the PHONE sentence (a known `4155550132` in `build4155550132` reaches the model as `build<PHONE_1>`); its pinning test
  `E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept` (tests/test_runmap_enforce_map.py:263) gets the
  PHONE assertion and a docstring sentence (appendix E).
- `tests/test_redact_idempotent_property.py:141`: the oracle `raw_copies` calls `R._replace_standalone(free, original, "\x00",
  R._joins(placeholder))`, so it judges a copy by the rule production uses (v2: :121; G7 round 6 moved it).
- `tests/test_redact_g3_port.py:56-59`: re-pointed at a copy only the sweep can reach after G8: `redact("tenant_id=acme42 and
  x_acme42_0")` gives `tenant_id=<TENANT_1> and x_<TENANT_1>_0`, actions 2 (run: green on `mut`, section 9). Order with G4: 8.1.
- `tests/test_runmap_enforce_map.py:263-275`: the pinning test above (appendix E).
- CHANGED in v4 (N5): `tests/test_redact_idempotent_property.py` docstring (b), line 7: the copy rule names the PHONE case;
  `tests/warden_port/test_redaction.py` 243-251 and 375-379: the two UUID-sweep docstrings say that since G8 the UUID pattern
  takes the `_0` copy itself (the tests' assertions are unchanged and stay green: the copies are still masked). Docstrings
  only (appendix E).
- `SECURITY.md`: one bullet appended to the list under `## Stated limits of redaction (reviewed, not bugs)` (heading at line 9),
  after the second bullet ("A form-encoded `;` or `&` ...") and before the line "Control that does not depend on these limits".
  `CHANGELOG.md`: one bullet under `## Unreleased` / `### Upgrade steps` (line 5), in that list's form: `- **G8, values glued to
  a word.** ...` (a bold lead sentence, then plain text). Text: section 13, through the security wording review.
Create:
- `tests/g8_cases.py` (appendix A): the 88 rows, the leak rule, the 84 must-keep rows, the full-stop, at-rest (7) and untrusted
  (2) rows, the `G4C_MERGED` flag and the step-0 check (`python -m tests.g8_cases`) (CHANGED in v4: counts).
- `tests/test_redact_glued_rest.py` (appendix B): the tests of section 7.
- `tests/g8_mutants.py` (appendix C): the 34 mutants (CHANGED in v4: was 30), run by `tools/mutation_runner.py`.
- `tests/g8_cost.py` (appendix F): the cost script of section 10 (not collected by pytest).
- `handover/core-c/evidence/G8-1.md`: the raw output of every command of section 8.
Not changed (decided): the G7 test `tests/test_redact_settle_loop.py::test_boundary_class_is_over_masked_fail_safe_and_pinned`
(936) stays byte-identical (K42); textnorm, defaults.py, `_countable`, `_LABELS`, `_sub_glued` (EMAIL only), STORED_KINDS,
`_SECRET_PATTERNS`: unchanged (no new kind; new originals fit `runmap._GRAMMAR` IPV4 / PHONE, runmap.py:241-249; UUID, IBAN and
CREDITCARD are never stored; CHANGED in v4: an original holding a non-ASCII digit does not fit the grammar and is not stored,
2.7). `runmap.neutralise_untrusted` / `escape_placeholders` (the `‹ ›` escape): unchanged; G8 only stops entry 7 reading
inside the escaped literal (M2). `EXPECTED_INPUTS` of the property test is unchanged (g8_cases.py is its own data).

## 4. Design (exact; CHANGED in v4: the text is copied from `v4`, the formatted tree at 99787d5b3; appendix D is the same as a diff)
### 4.1 PATTERNS, in order (flags: none unless the pattern starts with `(?i)`; group count stated per entry)
Entry 0 (CHANGED in v4, M1, L-D15), two module constants directly after `_NOT_IN_WORD` (redact.py 74), before the
"# Key to value: ..." comment:
```python
_NOT_IN_WORD = r"(?:(?<![A-Za-z0-9])|(?-i:(?<=[a-z])(?=[A-Z])))"
# Where an IBAN may start and end beside `_` (ticket G8 v4, M1). `_` is a base64url character, so inside an opaque token
# `..._DE89..._...` is no IBAN (masking it there would cut the token and leave its head readable). `_` before counts as a
# break only after a word of 2 to 8 ASCII letters that starts its token (`iban_DE89...`, `to_DE89...`); `_` after only
# when at most 8 letters or digits follow it to the token's end (`DE89..._x`, `DE89..._`), and not when the IBAN starts
# after `-`, `+` or `/` (inside a token, as the base already reads `...-DE89...-...`).
_IBAN_START = (
    r"(?:(?<![A-Za-z0-9+/_\-])"
    r"|(?<=[+/\-])(?![A-Z]{2}\d{2}[A-Za-z0-9]{11,30}_)"
    + "".join(rf"|(?<=(?<![A-Za-z0-9+/_\-])[A-Za-z]{{{n}}}_)" for n in range(2, 9))
    + ")"
)
_IBAN_END = r"(?:(?![A-Za-z0-9_])|(?=_[A-Za-z0-9]{0,8}(?![A-Za-z0-9+/=_\-])))"
```
Read in parts. Start: (a) no token character before (`[A-Za-z0-9+/_-]`: the base's `\b` minus `_`, for ASCII); or (b) `-`,
`+` or `/` before, as the base allows, but then the IBAN may not end at `_` (the lookahead is bounded: 2 + 2 + 30 + 1
characters); or (c) `_` after a word of exactly n ASCII letters (n = 2 to 8) that has no token character before it (seven
fixed-width look-behinds, so Python `re` accepts them). End: no letter, digit or `_` after (the base's `\b` for ASCII); or `_`
and then at most 8 letters or digits up to a character that is not a token character (or the end of the text). Every repeat is
bounded; each look-around is at most 35 characters, so the cost per start position is constant (section 10 adds the
`iban underscore` text).

Entry 1, IBAN (replaces 266-274). Preceded by the EMAIL tuple and the IBAN comment, to which four lines are added; followed
by the UUID entry. No group.
```python
    # evidence token like `AB12CDEF...` is NOT clobbered — only a genuine IBAN country prefix fires.
    # Glued (G8): not after an ASCII letter or digit and not before one (one would join the BBAN); `_` only in the
    # short-word context of `_IBAN_START` / `_IBAN_END`, so `iban_DE89...` and `DE89..._x` are masked with the `_` text
    # outside; `xDE89...`, `7DE89...`, `acct_iban_DE89...` stay (limit L4: inside a token an IBAN-shaped piece would cut
    # a longer credential in two and leave its head readable, ticket G8 v3 F1 and v4 M1).
    (
        "IBAN",
        re.compile(
            _IBAN_START
            + r"(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
            r"|GI|GL|GR|GT|HN|HR|HU|IE|IL|IQ|IS|IT|JO|KW|KZ|LB|LC|LI|LT|LU|LV|LY|MC|MD|ME|MK|MN|MR|MT"
            r"|MU|NI|NL|NO|PK|PL|PS|PT|QA|RO|RS|RU|SA|SC|SD|SE|SI|SK|SM|SO|ST|SV|TL|TN|TR|UA|VA|VG|XK)"
            r"\d{2}[A-Za-z0-9]{11,30}" + _IBAN_END
        ),
    ),
```
(v3's entry 1 was `r"(?<![A-Za-z0-9])(?:AD|...|XK)" r"\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])"`; it is L-D15's "v3 as is" option.)
Entry 2, UUID (replaces 275-280; `ruff format` puts it on one line). No group. `_UUID_SHAPE` (738) follows automatically.
```python
    # No word boundary (G8): the 8-4-4-4-12 run is found inside a longer token (`pod_<uuid>_0`, `x<uuid>`, `<uuid>9`) and
    # the glued text stays outside. An 8-4-4-4-16 hex id gives `<UUID_1>` and its last 4 hex digits (accepted, L-D4).
    (
        "UUID",
        re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
    ),
```
Entries 3 and 4, IPV4 (replace 374-377; CHANGED in v4, N2: entry 3 is the pair of dashed tuples, EC2 then pod DNS, entry 4
the dotted quad). Preceded by `("ACCOUNTID", re.compile(r"\b\d{12}\b")),`; followed by the IPv6 comment.
EC2 and pod DNS: one group (the dashed address), as today; dotted: no group.
```python
    # An EC2 private DNS name carries the address with dashes: ip-10-0-3-22(.region.compute.internal).
    # G8: `_` may stand before `ip-` / `ec2-` (`host_ip-10-0-3-22`), a letter may not (`xip-...`, `zip-...`: limit L10);
    # a letter or `_` may follow the last group (`ip-10-0-3-22a`); a digit may not.
    ("IPV4", re.compile(r"(?<![A-Za-z0-9])(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})(?![0-9])")),
    # k8s pod DNS; G8: a letter or `_` may stand before the address (`pod_10-0-3-22.ns.pod`), a digit may not.
    ("IPV4", re.compile(r"(?<![0-9])(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),
    # Dotted quad (G8): not inside a digit run (`7192.0.2.10`, `2026.11.20.10`: limit L1) and not after a lone `v` / `V`
    # (`v1.2.3.4` is a version, L-D1). A letter or `_` on either side is glued text, left outside (`node_<IPV4_1>`,
    # `<IPV4_1>a`); a four-part version glued to a word (`python3.11.4.1`) is masked too (L-D8).
    ("IPV4", re.compile(r"(?<![0-9])(?<!(?<![A-Za-z])[vV])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")),
```
Entry 5, CREDITCARD (replaces 471; L-D12). No group. Preceded by the card comment (468-470, one line added), followed by the PHONE
comment block.
```python
    # contiguous 16-digit card is already caught by PHONE; this closes the spaced/dashed form.
    # Glued (G8): a letter or `_` may stand on either side (`x4242 4242 4242 4242`), a digit may not.
    ("CREDITCARD", re.compile(r"(?<![0-9])\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}(?![0-9])")),
```
Entries 6 to 8, PHONE. Preceded by the PHONE comment block (472-490, unchanged, ending `#     still masked.`). Entry 6 is NEW and
sits directly BEFORE the main PHONE tuple (491-498, unchanged); entries 7 and 8 are NEW and sit directly AFTER it; the tuple after
entry 8 is the SECRET entry preceded by `# password=..., secret: ...`. Entries 6 and 7: no group. Entry 8: `(?i)`, group 1 is the
value (the keyword stays in the text). CHANGED in v4: entry 6 gets `(?!\d{4}-\d\d-\d\d)` right after `\+` (N4) and a comment
line, and `ruff format` now wraps it into the three-line tuple form; entry 7's end class gets `›` (M2) and its comment says
why. The main PHONE tuple between them is unchanged and has no entry number.
```python
    #     still masked.
    # (G8) A number that starts with `+`, BEFORE the main entry (which would leave `<PHONE_1> 1234a`): a letter or `_` may
    # stand before the `+` (`x+1 415-555-0132`, `tel_+44 20 5550 1234`) and after the last digit (`+1 415-555-0132a`);
    # a digit or `.` may not. A number without `+` keeps the main entry's rules (`415-555-0132x123` is not masked).
    # No date right after the `+` either (`x+2026-11-20T10:00:00Z` stays).
    (
        "PHONE",
        re.compile(
            r"(?<![0-9.\-])\+(?!\d{4}-\d\d-\d\d)\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![0-9.])"
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
    # `4155550132_x`); not a compact timestamp; `>` and `›` end no phone (a placeholder `<TENANT_4155550132>`, and the
    # same literal as `redact_untrusted` escapes it, `‹TENANT_4155550132›`). `sha256_3851...ab` stays (a letter after);
    # `order_1234567890` is masked (L-D10). Then a number glued straight to a phone word.
    (
        "PHONE",
        re.compile(
            r"(?<![0-9A-Za-z.\-+])(?:(?<=_)|(?=\d{10,16}_))"
            r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"
            r"\d{10,16}(?![0-9A-Za-z.>›])"
        ),
    ),
    (
        "PHONE",
        re.compile(r"(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\d{10,16})(?![0-9a-z.])"),
    ),
    # password=..., secret: ..., aws_secret_access_key="...": the value after a credential-ish key.
```
Entry 6 read in parts: a `+` with no digit, `.` or `-` before (a letter or `_` may stand before it), then (CHANGED in v4, N4)
no ISO date right after the `+`, then the main entry's body with its date guard, and the end `(?![0-9.])` (a letter or `_` may
follow, a digit or `.` may not). Without the guard after `+`, v3 read `x+2026-11-20T10:00:00Z` as `x<PHONE_1>T10:00:00Z`
(the body's guard is checked only from the second digit on); the main entry has the same blind spot after `+` but refuses a
letter before it, so on the base only `at +2026-11-20 10:00` (a space before `+`) is masked, and that stays as it is (2.3).
Entry 7 (CHANGED in v4, M2): `›` joins `>` in the end class. `redact_untrusted` escapes a placeholder-shaped literal
`<TENANT_4155550132>` to `‹TENANT_4155550132›` BEFORE the patterns run (runmap.py `neutralise_untrusted`), so v3's `>` guard
never saw it there and entry 7 wrote `‹TENANT_<PHONE_1>›` and a PHONE map entry (MEASURED). `‹` before needs no guard: the
start of entry 7 is `_` or a digit run followed by `_`. It has no compact
timestamp guard: a 14-digit timestamp never starts with `+`. v2's branch A (10 digits, no run of 5, no `+`) is dropped (L-D9
flipped, F6): it closed none of the probe rows and only K72, and cost K34, K70, K71. Cost bound: every repeat is bounded
(`{8,14}`, `{10,16}`); the start guards allow at most one start per `+` or digit.

### 4.2 The sweep (G8b)
redact.py, after `_ALNUM` (2225), the signature and docstring first lines of `_replace_standalone` (2228-2229) and the test in its
loop (2239); `ruff format` wraps the signature and the call (as below; appendix D is formatted).
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


def _replace_standalone(
    segment: str, original: str, placeholder: str, joins: frozenset[str] = _ALNUM
) -> str:
    """Replace `original` where no character of `joins` touches it (default `_ALNUM`: an ASCII letter or digit; callers
    pass `_joins(placeholder)`). A plain scan: ...  (rest of the docstring and body unchanged, except:)
        if before in joins or after in joins:
```
Callers: `_Redactor.sweep` (2041) `segment = _replace_standalone(segment, original, placeholder, _joins(placeholder))` (wrapped
by `ruff format`); `runmap._sweep_held` (849) `parts[i] = _replace_standalone(segment, spelling, placeholder, _joins(placeholder))`;
the property oracle. `enforce_map` and the gate (`first.sweep`, runmap.py:758) inherit it through `_Redactor.sweep`: a known PHONE
value glued to a letter or `_` in model-visible text is rewritten, so THE MODEL SEES THE GATE'S REWRITTEN TEXT
(`build<PHONE_1>` for a known `4155550132` in `build4155550132`), including epoch-like digit runs stored by entry 7 (K54-K60); it
round-trips through `restore_text` and is idempotent (digit-only joins). Pinned by `test_gate_enforce_map_rewrites_...` (B) and
the edited E test (appendix E); stated in model_gate.py's docstring. `_JOINS` holds PHONE only (G8-review-1 M4).

### 4.3 Module docstring (redact.py, a new paragraph after the "(A re-scan inside redact() ...)" sentence, before the closing `"""`)
```
A value glued to a letter or `_` is masked with the glued text left outside the placeholder (`node_<IPV4_1>`, `<UUID_1>x`):
an e-mail address, an IPv4 address, a UUID, a phone number that starts with `+`, a contiguous one beside `_` or straight
after a phone word, and an IBAN beside `_` after a short word (`iban_DE89...`; not inside a longer token) (G8).
A contiguous digit run glued to a letter is not read as a phone number (hashes and identifiers), and a letter or digit
glued before an IBAN, or a digit before an address, is not read as one.
A copy of a known phone number is swept where a letter or `_` touches it (not a digit).
```
(CHANGED in v4: the IBAN clause, M1.)
CHANGED in v4 (M3): place, in G4 v5's words: after the "What this is not" paragraph (which ends with the "(A re-scan inside
redact() ...)" sentence, redact.py 21-25), before the closing `"""`. G4 v5 section 6 adds its bare-number paragraph and base64
sentence AFTER this G8 paragraph; under the default order (G8 first) the G4 builder places them (textual merge only). G4 v5's
paragraph has a PHONE sentence that its Phase 0 (b) re-derives once G8 is merged (G4 v5 section 6, "G8 entries 5-7", which is
entries 6-8 here). runmap.py `enforce_map` docstring 699 and 718, model_gate.py 12-13: appendix D.

### 4.4 What stays as it is
`_sub_glued` stays EMAIL only (rows 74, 75, 77 are masked by plain `sub`); rows 13 and 76 (two values of one kind with nothing
between) cannot be split by a boundary rule (L2, L5). The settle loop is untouched. Placeholders: entry 7 refuses `>` and
(CHANGED in v4, M2) `›` after, and every new start refuses a digit before, so a placeholder number is never re-masked, written
`<KIND_n>` (K64) or escaped `‹KIND_n›` by `redact_untrusted` (U1, U2).

### 4.5 HOSTNAME under G4c (re-measured with G4 v4 sections 5.2 and 5.3, blob a029802bd1f3; F5, readiness Major 1)
G4 v4's `_HOST_LABEL`, `_HOST_DOT`, `_HOST_BARE`, `_HOST_TAIL`, HOSTNAME and HOSTKEY, compiled as written there and put in place
of today's HOSTNAME entry (scratch mkg4v4.py), on `base` (`base_g4`) and on `v3` (`v3_g4`): `v3_g4` gives appendix A's
`after_g4c` column with 0 differences in all 86 rows, the 80 must-keep rows (all equal to `after`), the 3 full-stop rows and
the 6 at-rest rows. So the column v2 measured with G4 v3 holds with v4 unchanged: rows 60, 61, 62 and 66 change output only
(`x <HOSTNAME_1> y`), rows 64 and 71 close, rows 67-70 and 78-80 stay leaks (L6), rows 81-86 are not affected (no host in them).
G8 changes no host row with or without G4c. CHANGED in v4 (M3): G4 v5's 5.2 / 5.3 regex lines are the same text as v4's
(compared, 8.1), so the column holds for v5 (not re-run). The column is checked again by the G4 builder's run of the G8 test file
with `G4C_MERGED = True` (8.1 step G4-2; `python -m tests.g8_cases` checks only `now` and does not cover it). A red `after_g4c`
cell there follows G4 v5's rule (0.3 step 2, adopted here): the G4 builder writes the measured output into the cell, records old
and new in evidence/G4-1.md and reports it; a leak in the new output is a STOP. (v3 said "a finding to report, not an edit of the
column"; that is withdrawn in favour of G4 v5's rule.)
G4a / G4b (base64, ENCODED; readiness Major 2): not measured (they are not built and live in `runmap.redact_text`'s base64 view).
`test_must_keep_rows` calls `redact()`, which G4a does not change; K60 (`Zm9vYmFy_<PHONE_1>_YmF6`) and K66 (a base64 blob) are
the two rows that a base64 view could move through `redact_text`. Rule for whoever lands second: run the G8 file (8.1).
CHANGED in v4 (M3, G4 v5 0.3 adopted): a must-keep row that changes under G4a is recorded (old and new output); if the new output
masks a base64 blob that decodes to text holding a secret, it is intended and the row's cell is updated; otherwise STOP and report.
A changed probe row is a finding, reported, not edited away.

## 5. Decisions made (drafter)
- The glued text stays outside the placeholder (as the e-mail fix): `restore_text` gives back the input exactly (test
  `test_restore_round_trip_ipv4_and_phone`, 41 rows, green).
- No new kind; no change to `_LABELS`, counters, `_countable` or the stored kinds.
- HOSTNAME: no G8 code (4.5).
- A contiguous phone number glued to a letter stays unmasked in pass 1 (L3; the hash guard), but a copy of a known one is swept
  (G8b): row 31 and the gate test.
- Formatted digit groups without `+` keep the main entry's rules (L-D9 flipped): `INV2026-...`, ISBN, `PO12-...`, MAC,
  `sha256-3851...`, `eth0 1500 9000`, `hunter123-45-6789`, `415-555-0132x123` are not masked by G8.

## 6. Decisions for the lead (build default first; each with fallback and consequence)
| id | question | default (built unless the lead says otherwise) | consequence of the default | fallback | consequence of the fallback |
|---|---|---|---|---|---|
| L-D1 | IPv4 after a lone `v` (`v1.2.3.4`) | not masked (a version) | K1, K2 kept; a real address written `v192.0.2.10` is not masked, even when known (K67) | mask it (drop `(?<!(?<![A-Za-z])[vV])`) | every `vN.N.N.N` becomes `v<IPV4_n>` (mutant V4 shows K1) |
| L-D2 (v3: default flipped, F1 measured; CHANGED in v4: for `_` see L-D15, the v3 "no opaque token is split" holds only for letter-and-digit tokens) | IBAN with a letter glued before | start `(?<![A-Za-z0-9])`: `_` before is masked, a letter or digit before is not | rows 38, 39, 45 are limits (L4: `xDE89...`, `ibanDE89...`, `xGB82...` readable); K24, K25, K66, K75-K77 kept; no opaque token is split (2.4) | v2's camelCase start `_NOT_IN_WORD` | rows 38, 39, 45 closed; K24, K25, K66 over-masked; up to 39 characters of 0.46 percent of 40-61-character opaque tokens readable, and longer tokens split in the map (measured, 2.4; mutant I3) |
| L-D3 | a letter, digit or `_` glued AFTER a host's private suffix (rows 67-70, 78-80) | stated limit L6 | `db01.prod.corpa` stays readable | G8c after G4c: `(?![^\W\d_]|-)` in place of G4c's tail `(?![\w-])` | NOT RE-MEASURED with G4 v4 (v1's measurement: masks code such as `self.corp_id`) |
| L-D4 | UUID with hex glued after | masked, the extra hex left outside | K27 `uuid-ish <UUID_1>cafe` | end guard `(?![0-9A-Fa-f])` | rows 47, 48 limits, by reading 14 and 77 too (not run) |
| L-D6 | PHONE keyword list (entry 8) | `tel`, `phone`, `mobile`, `cell`, `fax` | row 28 closed | cut entry 8 | row 28 a limit |
| L-D7 | build order with G4 | G8 first with `G4C_MERGED = False` (8.1) | G8 lands without waiting for G4 v5's readiness; the G4 builder makes the four edits of 8.1 | G4 first, then G8 with `G4C_MERGED = True` and the G8 builder makes the same edits | G8 waits for G4 |
| L-D8 | four-part dotted versions glued to a word or `_` | masked (fail safe): K43-K53 | version evidence lost; stored as IPV4, restorable | (a) a letter directly before refuses the dotted match | rows 7, 8, 11, 74 become limits (not run); K43-K48 kept |
| L-D9 (v3: default flipped, F6) | a phone without `+`, in groups, with a letter or `_` after | NOT masked: entry 6 is `+`-led only | K72 `415-555-0132x123` readable as today; K34, K70, K71 as today; the probe counts do not change (no probe row needs it; measured: v2h vs v3camel differ only in K34, K70, K71, K72 and row 75) | v2's branch A (10 digits, no run of 5) | K72 closed; K34, K71 grow, K70 over-masked (measured on `v2h`) |
| L-D10 | a contiguous 10-16 digit run glued to `_` (entry 7) | masked | rows 26, 29, 30 closed; K26, K54-K60 over-masked, stored as PHONE | cut entry 7, let entry 8 take `tel_` | rows 26, 30 limits (not run) |
| L-D11 | an SSN-shaped value glued to a letter | not taken as PHONE, except `+123-45-6789x` (K78, stored as PHONE) | `ssn 123-45-6789a` readable as today (L8, K73) | SSN-safe lookahead `(?!\+?\d{3}-\d{2}-\d{4}(?!\d))` in entry 6 | K78 readable as today (not run) |
| L-D12 (new, F6 / L9) | a grouped card number glued to a letter or `_` | masked whole as CREDITCARD: start `(?<![0-9])`, end `(?![0-9])` | K36 `x<CREDITCARD_1>`, K74 `card <CREDITCARD_1>x`, K80 `card_<CREDITCARD_1>_x`; the 12 digits no longer go to the map at rest as PHONE (CREDITCARD is a SECRET kind, never stored); measured on a variant against v2's 156 data rows (80 + 74 + 2): only K36 and K74 change; K80 added in v3. CHANGED in v4 (N1): the over-mask is measured and pinned: AT7 `ORD1234-5678-9012-3456` -> `ORD<CREDITCARD_1>` (and `INV_1234-5678-9012-3456_x` -> `INV_<CREDITCARD_1>_x`, 2.3): an order or invoice number in four groups of four glued to letters is masked as a card and, CREDITCARD being a SECRET kind, is not storable (evidence lost after the run, no leak) | keep `\b` (L9 stays a limit) | one group of the card readable, 12 digits stored as PHONE (today's behaviour) |
| L-D13 (new, F6 / L7; ASK THE LEAD) | a phone number directly before a full stop (`call 415-555-0132.`) | unchanged: not masked (L7, F1-F3 pinned) | a phone at the end of a sentence leaks, as today | end guard `(?![0-9]|\.\d)` in entry 6 and the main entry | F1-F3 masked; measured over-masks: `build 1234567890.tar` -> `build <PHONE_1>.tar`, `pid 4155550132.log`, `at 1732095071. done` (an epoch); `ts 1732095071.123` and `v 415-555-0132.5` stay (variant `v3fs`; v2's 80 rows and 74 must-keep rows otherwise identical). The default is not G8's to change: not glued, and the fallback trades evidence for a common leak |
| L-D15 (NEW in v4, M1; ASK THE LEAD: the row-41 trade-off) | an IBAN beside `_` when `_` is also a base64url token character | `_IBAN_START` / `_IBAN_END` (4.1): `_` counts only after a 2-8-letter word that starts its token and before at most 8 letters or digits that end it; after `-`, `+`, `/` no `_` end | rows 36, 37, 41, 42, 44 closed; rows 87 (`acct_iban_DE89...`) and 88 (`DE89..._reference`) limits (L4); the measured in-token classes equal the base in readable text (16 of 16 random classes) and in map splits (15 of 16; one more split per 20,000 129-163-character Bearer tokens); a short all-letter head before `_` at a token's start (`ab_DE89...`) is read as `iban_DE89...` is (at most the 2-8-letter word readable; 2.4b); K83, K84 pin it; mutants I4, I5; the regex is longer (seven fixed-width look-behinds) | (a) the smallest text change: treat `_` as the base does, start `(?<![A-Za-z0-9_])`, end `(?![A-Za-z0-9_])` | rows 36, 37, 41, 42, 44 become limits (G8 closes no IBAN row; IBAN is then the base's for ASCII); AT5, AT6 back to the base (by reading; not run as such, A2 measured the start half). (b) A2, only the start: `(?<![A-Za-z0-9_])` | rows 41, 42 limits; rows 36, 37, 44 closed; in-token readable 14 per 80,000 base64url `key` tokens vs the base's 9 (MEASURED). (c) v3 as is, stated as a limit | 22 vs 9 readable, 47 vs 17 splits per 80,000 (MEASURED); not recommended |
| L-D16 (NEW in v4, M1; follow-up, not G8) | the BASE's own IBAN start after `-`, `+`, `/` (and at a token's start) inside a base64 / base64url token | not changed by G8 (limit L12) | 9 readable per 80,000 random base64url and 26 per 80,000 base64 `key` tokens on the base and after G8 (MEASURED, 2.4b) | a follow-up ticket (owner core-c): refuse an IBAN that a 40+-character token run holds on both sides, or run HIGHENTROPY's token test first | not designed, not measured; changing `-` would also change `ref-DE89...` (masked today) |
| L-D14 (new, F6 / L11) | a piece of a secret with a stored kind's shape (AT1-AT3) | not fixed in G8; pinned (AT1-AT4); a follow-up ticket (owner core-c) | a password like `hunter192.0.2.10x` leaves `192.0.2.10` in the map at rest (as `a-192.0.2.10-b` does today) | in G8: `runmap.storable` refuses an original that is a substring of a SECRET-kind original of the same map | AT1-AT4 storable empty; not built, not measured |

## 7. Acceptance tests (appendix B; data appendix A; public names, plus `_has_bank_word` in one test)
| test | rows | asserts | red on the base (measured on a5247ac4a) |
|---|---|---|---|
| `test_glued_rows_are_masked` | 51 (48 closed + rows 21, 22, 75) | output == expected in `redact`, `redact_many(...)[0][0]`, `redact_text`; no leak | 51: row2 row3 row4 row5 row7 row8 row9 row11 row12 row14 row15 row16 row18 row19 row20 row21 row22 row23 row24 row26 row28 row29 row30 row31 row32 row36 row37 row41 row42 row44 row47 row48 row49 row50 row51 row52 row53 row54 row55 row56 row57 row58 row72 row73 row74 row75 row77 row81 row82 row83 row84 |
| `test_glued_character_stays_outside_the_placeholder` | 21: 2-5, 7-9, 18-20, 36-37, 47-51, 81-84 | output == text with the value replaced by its own placeholder | 21: all of them |
| `test_controls_and_untouched_rows_keep_their_output` | 15 unchanged rows | output == expected and == `now` (host rows: `after_g4c` once `G4C_MERGED`) | 0 |
| `test_limit_rows_are_pinned` | 18: 10, 13, 25, 27, 38, 39, 40, 45, 76, 67-70, 78-80, 85, 86 | the DESIRED behaviour (no leak), `xfail(strict=True)` with the limit id | 0 red; 18 xfailed (base and after) |
| `test_host_glued_before_is_closed_by_g4c` | 64, 71 | `x <HOSTNAME_1> y`; strict xfail naming G4c while `G4C_MERGED` is False | 0 red; 2 xfailed |
| `test_must_keep_rows` | 80 | output == `after`; a kept row has an empty map | 27: K26 K27 K36 K43 K44 K45 K46 K47 K48 K49 K50 K51 K52 K53 K54 K55 K56 K57 K58 K59 K60 K62 K63 K65 K74 K78 K80 |
| `test_phone_before_a_full_stop_is_a_stated_limit` | F1-F3 | unchanged (L7) | 0 |
| `test_an_iban_never_starts_inside_an_opaque_token` (v3) | K75-K77 | output == `after` and one map entry | 0 (it pins the base; red under v2's start: mutant I3) |
| `test_at_rest_rows` (v3) | AT1-AT6 | (text, sorted map, sorted `storable(map)`) == `after` (or `now` when None) | 5: AT1 AT2 AT3 AT5 AT6 |
| `test_second_call_changes_nothing` | 86 | a second `redact_text` changes neither text nor map | 0 |
| `test_untrusted_matches_redact_text` | 86 | `redact_untrusted == redact_text` | 0 |
| `test_restore_round_trip_ipv4_and_phone` | 41 (IPv4 and phone rows without a UUID) | `restore_text(out, m) == text` | 0 |
| `test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only` | row 31; seeded copies (as v2) | phone letter copy replaced, digit copy not; IPV4, HOSTNAME, TENANT letter copies not replaced | 1 |
| `test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone` | as v2 | as v2 | 1 |
| `test_bank_word_check_ignores_a_glued_uuid` | as v2 | False | 1 |
| `test_row_counts_are_pinned` | 86 rows, 80 must-keep, 3 full-stop, 6 at-rest, classes 48 / 15 / 18 / 3 / 2, limit ids | | 0 |
| `test_glued_patterns_are_linear` (perf) | 6 hostile texts x (`redact`, `redact_text`) = 12 | section 10 | not run on the base |
Fail-before total (measured: appendices A and B copied into the a5247ac4a archive, `pytest -q -p no:cacheprovider -m "not perf"
tests/test_redact_glued_rest.py`): `107 failed, 289 passed, 12 deselected, 20 xfailed` (107 = 51 + 21 + 27 + 5 + 1 + 1 + 1).
With G8 (`mut`): `396 passed, 12 deselected, 20 xfailed`. G8a only (`v3a`): `3 failed, 393 passed, 12 deselected, 20 xfailed`,
the three ids of phase 1 (measured).

## 8. Build order, phases and commands
Common prefix `uv run --all-extras --group test`; run from the repo root of the builder's worktree. "Green" = exactly the named
result. Rule for every phase: ANY red id that the phase does not name: STOP and report.
How to apply the appendices: appendix D and E are unified diffs against a5247ac4a: save each as a file and run `patch -p1 <
file` from the repo root (a line offset is fine, as on 93c0d08ee; a hunk that needs fuzz or fails means the base moved: STOP,
re-measure). Appendices A, B, C
and F are whole files: copy the text between the ```python fence and the closing fence into the named path. All of them are
already `ruff format`ed (v2's reflowed four files on `ruff format`: redact.py, tests/test_redact_idempotent_property.py,
tests/test_redact_glued_rest.py and tests/g8_cases.py; v3's appendices are the formatted text, so `ruff format --check` on
the changed files says "already formatted"; the ROWS table is under `# fmt: off`).

### 8.1 Order with G4 (L-D7; readiness Major 1, F5; G4-review-4 Major 2)
CHANGED in v4 (G8-review-3-codebase M3): v3 said G4 v5 was "still a copy of v4". It is not: G4 v5 (blob c96f9c01de99 at
99787d5b3) has its own section 0.3 "Order with G8" and decision L23, and G4 v6 is being drafted (an untracked file in the shared
tree, read at 10:26Z while it was still being written: its header names this reconciliation, its section 0.3 then still read as
v5's). The table below is the reconciled text: where G4 v5 differs, the resolution column says which wording both tickets carry and
who edits. G4 v5's own rules are adopted where they are G4's to make (its regex, its builder's evidence).

| point | G4 v5 says (section) | G8 v3 said | resolution (both tickets) |
|---|---|---|---|
| order | G8 first, `G4C_MERGED = False`; fallback G4 first (0.3, L23) | the same (L-D7) | agreed, no edit |
| the property-test oracle line | "about line 121" (0.3) | 141 | 141 at a5247ac4a and at 99787d5b3 (MEASURED: `grep -n _replace_standalone tests/test_redact_idempotent_property.py`); the G4 v6 drafter writes 141, by name `raw_copies` |
| PHONE entry numbers | "G8 entries 5-7" (section 6) | mixed (5 and 6 for the `+` entry) | 6 (`+`-led, before the main tuple), 7 (contiguous beside `_`), 8 (phone word); the main tuple has no number (N2, section 4.1). G4 v6 writes "G8 entries 6-8" |
| G8 mutants in G4's runs | not listed: step 2 runs only the two G8 test files (0.3) | G4-2: `python tests/g8_mutants.py` in G4's phase 5 | kept: G4 phase 5 runs `python tests/g8_mutants.py`, expected `32 of 32 good` (CHANGED in v4: two mutants added, 8.2); G4 v6 adds the command to its Phase 5 list (its header names "30 of 30", which is v3's count) |
| a red `after_g4c` cell in the G4c commit | the G4 builder writes the measured output into the cell, records old and new in evidence/G4-1.md and reports; a LEAK in the new output is a STOP (0.3 step 2) | "a red host row is a finding to report, not an edit of the column" | G4 v5's rule is adopted (the regex is G4's; the cell is data G8 measured with an older G4 text). G8 v4 section 4.5 says the same |
| a changed must-keep row under G4a (K60, K66) | intended and the cell updated when the new output masks a base64 blob that decodes to text holding a secret; otherwise STOP (0.3) | "a changed row is a finding, reported, not edited away" | G4 v5's rule is adopted; G8 v4 section 4.5 says the same |
| docstring placement | G8's paragraph after the "What this is not" paragraph; G4's bare-number paragraph and base64 sentence after G8's, before the closing `"""` (0.3, section 6) | G8's paragraph after the "(A re-scan inside redact() ...)" sentence | the same place: that sentence is the last line of the "What this is not" paragraph (redact.py 21-25 at 99787d5b3, read). Wording to use in both: "after the 'What this is not' paragraph (it ends with the '(A re-scan inside redact() ...)' sentence)" |
| HOSTNAME regex | 5.2 / 5.3 | measured with G4 v4's | v5's 5.2 / 5.3 code lines equal v4's (MEASURED: the regex lines of the two sections compared as text, 14 lines, only a prose line differs); so the `after_g4c` column holds; NOT RE-RUN with v5 (same code) |
| who rebases | the second lander (G4 under the default) | the same | agreed |
| G4 v5's header | "G8 (ticket G8-glued-rest-gap-v2, v3 drafting)" | - | stale: the G8 ticket is this v4; G4 v6 names it |

The text G4 has to carry (passed by the coordinator to the G4 v6 drafter; G4 v5 already carries G4-1, the test-file half of G4-2,
G4-3 and G4-4):
- G4-1. The G4c commit (G4 phase 4) sets `G4C_MERGED = True` in tests/g8_cases.py. That turns rows 64 and 71 into ordinary tests
  (they would otherwise XPASS under strict xfail and go red) and switches rows 60-62 and 66 to the `after_g4c` column (section
  4.5, measured with G4 v4's regex).
- G4-2. G4's phase 4 step 1 run list gets `tests/test_redact_glued_rest.py`, and its phase 5 the mutant run `python
  tests/g8_mutants.py` (expected: 32 of 32 good; CHANGED in v4, was 30). Expected red: none. A red `after_g4c` host cell: G4 v5's
  rule (the table above: write the measured output, record, report; a leak is a STOP). Any other red row is a finding, reported.
- G4-3. Rebase of tests/test_redact_idempotent_property.py: owned by whoever lands second; the two edits do not overlap (G8: the
  `raw_copies` oracle line 141; G4: the `p1c-b64` group, `EXPECTED_INPUTS`, `P1C_B64`). The redact.py module docstring: G8 adds
  one paragraph (4.3), G4 another (its phase 5): the second lander puts its paragraph after the first's. Textual conflict in
  redact.py is limited to the PATTERNS region near HOSTNAME (G8 does not edit HOSTNAME) and the docstring.
- G4-4. The g3_port clause: G4 v4 section 11 lists tests/test_redact_g3_port.py under "must stay green UNCHANGED" while G8 edits
  lines 56-59 (appendix E). Resolution: when G8 lands first, the G4 v5 ticket lists tests/test_redact_g3_port.py as "must stay
  green, unchanged BY G4 (G8 re-pointed lines 56-59)"; the file is in G4's base, so G4's own rule (no G4 edit) still holds. When
  G4 lands first, G8 makes its edit as written (G8's appendix E applies to any base where lines 53-59 read as at a5247ac4a) and
  G4's "unchanged" applied to G4's commits only. Measured: tests/test_redact_g3_port.py passes on `v3_g4` (G8 + G4 v4's host patterns: `16 passed`).
Fallback (G4 first): G8 is built on the G4 head with `G4C_MERGED = True` from the start; phase 0 then expects the `after_g4c`
column for rows 60-62 and 66 in `now` too (the step-0 check prints them as BAD: compare them with 4.5 and go on; any other BAD:
STOP).
Other tickets: G7 round 6 is merged (a5247ac4a); E9 is merged; G7 fix round 7 (bff88a7a1) is merged after the measured base
(section 0: it moves lines only, the tables hold on 99787d5b3). G10 (textfold deadline, draft) touches no G8 line.
G9 (spelled sweep fixed point; v1, and v2 being drafted, G9-spelled-fixed-point-v2.md at 10:22Z) touches G8 in TWO places
(CHANGED in v4, G8-review-3-codebase M4):
- the literal-sweep call in `_Redactor.sweep` (2041 at a5247ac4a, 2072 at 99787d5b3), which G8 gives the `_joins(placeholder)`
  argument and which G9 moves into `_sweep_once` (same text). Whichever lands second applies its edit to the moved line, by name.
- G9's read-back (`_overlaps`; G9 v2 section 4.1, the `add()` helper: `E[at - 1:at] in _ALNUM or E[end:end + 1] in _ALNUM`)
  mirrors the sweep's standalone rule with `_ALNUM`. After G8 the sweep's rule is `_joins(placeholder)` (a digit only, for a PHONE
  value). The two must stay the same rule, or a PHONE copy glued to a letter, which G8's sweep replaces, is judged differently by
  the read-back (it would see a letter-glued known phone in E as "touched", not an occurrence). RULE: whichever of G8 and G9 lands
  SECOND changes G9's read-back test to `in _joins(placeholder)` for the occurrence's placeholder (the rule entry's placeholder,
  `rule[...]` in G9's `rules` map; G9's ticket names the field), in the same commit, and adds one G9 test: a map with
  `<PHONE_1>` = `4155550132` and a text where that number is glued to a letter beside another placeholder, read back as an
  occurrence. If G8 lands second, the G8 builder makes this edit (it is then a G9 file region: name it in evidence/G8-1.md); if
  G9 lands second, the G9 builder does. NOT MEASURED (G9 is not built); by reading of G9 v1 (section 4.2: "the same rule as
  `_replace_standalone`") and v2 (section 4.1, the `add()` code). The coordinator passes this paragraph to the G9 drafter.

Phase 0, no code. (a) Base sha recorded; `git archive <base> | tar -x -C /tmp/g8-base` (no worktree switch). (b) Copy appendix A to
/tmp/g8-base/tests/g8_cases.py; `cd /tmp/g8-base && uv run --all-extras --group test python -m tests.g8_cases`. Green: exit 0, last
line `0 differ`. Any `BAD` line: STOP and report (the base moved). (c) Fail-before: copy appendix B and F too; `uv run
--all-extras --group test pytest -q -p no:cacheprovider -m "not perf" tests/test_redact_glued_rest.py -rfEX`. Green: `107 failed,
289 passed, 12 deselected, 20 xfailed`, the failing ids exactly those of section 7. (d) Full suite of the base (`pytest -q -p
no:cacheprovider -m "not perf and not live" -n 3 tests`), failures recorded. (e) Cost on the base: `uv run --all-extras --group
test python -m tests.g8_cost run /tmp/g8-cost-base.json` (section 10), on a box with load under 2 (`uptime`); paste the table.
(f) Record at the base: `python tests/redact_mutants.py`, `python tests/p1d_a_mutants.py`, `python tests/gate_mutants.py`,
`python tests/stage_mutants.py`, `python tests/textnorm_mutants.py`, each verdict per mutant (phase 4 compares with it).
Phase 1+2, G8a and G8b in one commit (readiness Major 6: the prototype was run; phase 1 alone is red by design). Apply appendix
D and E, add appendices A, B, C, F.
1. `pytest -q -p no:cacheprovider -m "not perf" tests/test_redact_glued_rest.py`. Green: `396 passed, 12 deselected, 20 xfailed`
   (its own count, a separate run).
2. `pytest -q -p no:cacheprovider -m "not perf" -n 3 tests/test_redact_g3_port.py tests/test_redact_idempotent_property.py
   tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py tests/warden_port
   tests/test_redact_fold.py tests/test_redact_context_after_sweep.py tests/test_redact_own_output.py
   tests/test_redact_own_output_hardening.py tests/test_text_parts_together.py tests/test_k5_classes.py tests/test_s4_llm_guard.py
   tests/test_k5_round8.py tests/test_k5_round12_fuzz.py`. Green: all pass. (CHANGED in v4, G8-review-3-codebase M5: the
   last nine files are added; they hold redact / redact_untrusted / sweep / fold assertions a pattern or `_joins` change can turn.
   None is expected red: by the reviewer's reading and by this drafter's reading of their PHONE / IPV4 / IBAN / UUID / CARD
   literals, NOT RUN by the v4 drafter (box rule: no test suite), so a red id there is a finding, reported, not edited away.
   Their count is the builder's to record in evidence/G8-1.md; v3's `2679 passed, 3 skipped` covers the first six only.)
   (The enforce_map flake of v2 section 9, `test_m_new_1_enforce_map_has_the_redactors_time_budget`, is fixed by 833a86b: the test
   patches the redactor's clock too; a red there now is a finding.)
   If the builder prefers two commits (G8a, then G8b): after G8a alone, step 1 gives exactly `3 failed`:
   `test_glued_rows_are_masked[row31]`, `test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only`,
   `test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone` (measured on `v3a`); any other red id: STOP.
Phase 3, checks. `ruff format --check` and `ruff check` on the changed and new files: green ("already formatted", "All checks
passed"). Full suite: `pytest -q -p no:cacheprovider -m "not perf and not live" -n 3 tests`. Green: its failures are a SUBSET of
phase 0 (d)'s (the worktree has `.git`, the archive not, so `test_repo_rules.py::test_licences_are_proprietary` fails in the archive
only). Perf: `pytest -q -p no:cacheprovider -p no:xdist -m perf tests/test_redact_glued_rest.py tests/test_k5_perf.py
tests/test_redact_fold_budget.py`. Green: all pass. Cost: `python -m tests.g8_cost run /tmp/g8-cost-build.json` then `python -m
tests.g8_cost compare /tmp/g8-cost-base.json /tmp/g8-cost-build.json`, both runs on the same box with load under 2; paste both.
Green: exit 0 (`0 rows break the rule`). On a FAIL: re-run both (base and build) once; if a row still fails, STOP and report the
two tables to the lead (no bound is changed by the builder).
Phase 4, mutants: `uv run --all-extras --group test python tests/g8_mutants.py` (runner tools/mutation_runner.py, judge
src/hadavin_sdk/testing/mutation.py). Green: `30 of 30 good` (measured, section 9). Rules: a BAD caused ONLY by a wrong expect
(`WRONG_REASON` whose first line is a `ROW` / `OPAQUE` / `SWEEP` line of the same killer, or `OTHER_TEST` whose id is another
case of the same killer) is corrected to the actual first failing line and pinned case, and the correction is written in the
evidence; a SURVIVING mutant (`SURVIVED`, or any verdict where the killer passes) is a STOP. Then `python tests/redact_mutants.py`,
`python tests/p1d_a_mutants.py`, `python tests/gate_mutants.py`, `python tests/stage_mutants.py`, `python tests/textnorm_mutants.py`:
no new BAD against phase 0's base record (their anchors are not on G8 lines).
Phase 5, documents: SECURITY.md and CHANGELOG.md (section 13, the insertion points of section 3), evidence/G8-1.md with the raw
output of phases 0-4. Owner: core-c (guard/redact.py, guard/runmap.py, guard/model_gate.py). No core-a / core-b file, no SPINE file.

## 9. The drafter's runs (a5247ac4a)
- Step 0 (`python -m tests.g8_cases`, appendix A) on `base`: `0 differ` (86 rows, 80 must-keep, 3 full-stop, 6 at-rest).
- The scratch check of the `after` column on `mut` and of `after_g4c` on `v3_g4`: 0 differences each (all 86 + 80 + 3 + 6).
- v2's tables on a5247ac4a: `now` 0 differences on `base`, `after` 0 differences on `v2h`.
- The G8 test file: base `107 failed, 289 passed, 12 deselected, 20 xfailed`; `mut` `396 passed, 12 deselected, 20 xfailed`;
  `v3a` (G8a only) `3 failed, 393 passed, 12 deselected, 20 xfailed` (the three phase 1 ids).
- F1 (2.4), at rest (2.5), the card and full-stop variants (L-D12, L-D13), the reviewers' examples (2.3).
- Phase 1+2 step 2 list (`-n 3`, `-m "not perf"`: tests/test_redact_g3_port.py, test_redact_idempotent_property.py,
  test_redact_settle_loop.py, test_runmap_enforce_map.py, test_model_gate.py, tests/warden_port): `mut` (with the appendix E edits)
  `2679 passed, 3 skipped in 53.85s`; `base` `2679 passed, 3 skipped in 41.71s`. So the edited oracle, the re-pointed g3 test and
  the new enforce_map assertion run green inside their files, and the G7 boundary test is green.
- Mutants (phase 4 command, run in `mut`: the patched tree after `ruff format`, appendices A-C copied in; `python
  tests/g8_mutants.py` with the repository's `.venv` python; the runner sets the child's PYTHONPATH to its temp copy):
  - run 1 (v3's first expects): `4 of 30 good`: 24 `BAD OTHER_TEST` (the expect matched, the pinned id lacked the case
    `[row36]`, a v2 defect), 2 `BAD WRONG_REASON`: P1 (first line `ROW 21 redact: 'call x+<PHONE_1> now'`, expect was `ROW 18`)
    and P4 (`ROW K5 keep (kept): 'sha <PHONE_1>abcdef...'`, expect was `ROW K29`). Fixed by the phase 4 rule (the pinned case
    from the expect; the two expects set to the measured first lines). No mutant survived.
  - run 2 (the corrected expects and pins, before a rename of the P-mutants' names only): `30 of 30 good`. Raw tail:
    `ok  KILLED       G8-S5 TENANT given digits  [test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only]`
    `ok  KILLED       G8-S6 PHONE copy beside a digit replaced too  [test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only]`
    `30 of 30 good; problems: []`
    Killers by case: I1 row36, I2 row41, I3 K75 (OPAQUE), U1 row14, U2 row51, V1 row2, V2 row7, V3 K2, V4 K1, V5 row72, V6 row81,
    V7 row83, C1 K36, C2 K74, P1 row21, P2 row18, P3 row21, P4 K5, P5 row18, P8 K8, P9 K16, P10 K64, P11 row26, P12 row28, S1 row31,
    S2 row31, S3-S6 the sweep test.
  - run 3 (appendix C exactly as printed; 10:02Z, load 3.3): raw tail:
    `ok  KILLED       G8-S4 IPV4 given digits  [test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only]`
    `ok  KILLED       G8-S5 TENANT given digits  [test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only]`
    `ok  KILLED       G8-S6 PHONE copy beside a digit replaced too  [test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only]`
    `30 of 30 good; problems: []`
- `ruff format --check` on `src` and the eight changed or new test files of `mut`: `118 files already formatted`; `ruff check`:
  `All checks passed!` (ruff 0.17.1, the repository's `.venv`).
- On an archive of 93c0d08ee (HEAD when the file was finished): step 0 `0 differ`; the G8 file before the patch `107 failed, 289
  passed, 12 deselected, 20 xfailed`; `patch -p1` of appendix D and E (hunk offsets 6 and 3, no fuzz); after: the G8 file `396
  passed, 12 deselected, 20 xfailed`; tests/test_redact_g3_port.py, test_redact_idempotent_property.py, test_runmap_enforce_map.py,
  test_model_gate.py (`-n 3`) `2213 passed in 36.84s`; `python tests/g8_mutants.py` `30 of 30 good; problems: []`.
- Cost: section 10 (`base` vs `mut`, both calls, `0 rows break the rule`).
- F1 on 2e3a081ae and on a5247ac4a (2.4): identical.
- NOT RUN by the drafter (box rule): the whole suite (phase 0 (d) and 3 are the builder's); the perf tests under pytest (the cost
  script of appendix F ran instead); `redact_mutants.py`, `p1d_a_mutants.py`, `gate_mutants.py`, `stage_mutants.py`,
  `textnorm_mutants.py` (their anchors are not on G8 lines: checked by grep, not run); the approval-card and k1b suites.

## 10. Cost
Script: appendix F, `tests/g8_cost.py` (not collected by pytest). `run OUT.json` times the six hostile texts of appendix B (`dots`
`1.`, `digits and spaces` `x1 2 3 ...`, `underscore digits` `_4155550132`, `hex and dashes` `deadbeef-dead-beef-dead-`, `iban-ish`
`aDE89` + 40 `A`, `plus digits` `a+1 415-555-0132`) repeated to 65,536 and 262,144 characters, through `redact()` and through
`runmap.redact_text(t, RunMap())`, CPU seconds of the calling thread (`time.thread_time`), best of 3. `compare BASE.json BUILD.json`
prints both side by side and exits 1 when a row breaks the rule.
Acceptance rule (every text, both calls, on the build): the 262,144-character time is under 3.0 s; it is at most 6.0 times the
65,536-character time; and it is at most 1.5 times the base's 262,144-character time plus 0.05 s. Both runs on the same box, load
under 2 (`uptime`). Action on failure: re-run base and build once; a row that still fails is a STOP: both tables go to the lead,
and no bound is changed by the builder.
Drafter's run (2026-11-20 09:58-09:59Z, a5247ac4a, `base` vs `mut`, the repository's `.venv` Python 3.13, box load 3.1-4.3: so the
absolute numbers are noisy; the phase 3 run on a quiet box is the one that counts): `0 rows break the rule`.
| text / call | base 65,536 | base 262,144 | G8 65,536 | G8 262,144 | G8 4x ratio | G8 / base |
|---|---|---|---|---|---|---|
| digits and spaces / redact | 0.193 | 0.768 | 0.198 | 0.829 | 4.19 | 1.08 |
| digits and spaces / redact_text | 0.193 | 0.785 | 0.200 | 0.782 | 3.91 | 1.00 |
| dots / redact | 0.238 | 1.019 | 0.248 | 0.993 | 4.01 | 0.97 |
| dots / redact_text | 0.243 | 1.035 | 0.249 | 0.995 | 3.99 | 0.96 |
| hex and dashes / redact | 0.222 | 1.041 | 0.232 | 1.022 | 4.42 | 0.98 |
| hex and dashes / redact_text | 0.201 | 1.046 | 0.209 | 1.037 | 4.96 | 0.99 |
| iban-ish / redact | 0.123 | 0.509 | 0.133 | 0.538 | 4.04 | 1.06 |
| iban-ish / redact_text | 0.128 | 0.496 | 0.133 | 0.531 | 4.01 | 1.07 |
| plus digits / redact | 0.253 | 1.019 | 0.169 | 0.671 | 3.97 | 0.66 |
| plus digits / redact_text | 0.281 | 1.020 | 0.167 | 0.697 | 4.17 | 0.68 |
| underscore digits / redact | 0.160 | 0.798 | 0.192 | 0.798 | 4.15 | 1.00 |
| underscore digits / redact_text | 0.158 | 0.865 | 0.194 | 0.767 | 3.96 | 0.89 |
Read: G8 costs 0.66 to 1.08 times the base on these texts; `plus digits` is cheaper because the new `+` entry masks the number
first and the main entry then has less to scan. The base's own 4x ratio reached 5.46 (`underscore digits / redact_text`) under
this load, close to the 6.0 bound: that is why the rule needs a quiet box and allows one re-run. The perf test of appendix B
(`test_glued_patterns_are_linear`, 12 cases, the same 3.0 s and 6.0 bounds without the base) was NOT run by the drafter.
Relabelled earlier figures: v1's numbers (0d93f20, `redact()` only, ratio 3.2-4.4) and v2's "at most 4.6" (which had no v2 source)
are v1-era figures and are not used for any bound here.
Correction kept from v2: FOUR existing entries change their boundaries in v2 (IBAN, UUID, EC2, dotted IPV4); v3 adds the pod-DNS and
CREDITCARD entries (six change) and adds THREE PHONE entries (PATTERNS grows from N to N+3; `tests/test_redact_fold_budget.py:78`
reads `len(PATTERNS)` live); the sweep adds one dict lookup per swept copy.
Builder effort: half a day (the data, tests, mutants and cost script are given; most of the time is the runs).

## 11. Stated limits after G8 (each pinned by a strict xfail or a must-keep / full-stop / at-rest row)
- L1 A digit glued before a dotted IPv4 (`7192.0.2.10`): row 10; `2026.11.20.10` must stay (K3).
- L2 Two dotted IPv4s glued with nothing between: row 13.
- L3 A contiguous phone number glued to a letter (`4155550132a`, `x4155550132`): rows 25, 27 (masked when a clean copy of the same
  number is in the call, or the number is a known value at the gate: G8b).
- L4 (v3: widened) A letter or digit glued before an IBAN (`xDE89...`, `ibanDE89...`, `7DE89...`): rows 38, 39, 40, 45 (L-D2).
- L5 Two IBANs glued: row 76.
- L6 A letter, digit or `_` glued after a host's private suffix: rows 67-70, 78-80 (L-D3), also under G4c.
- L7 A phone number before a full stop: F1-F3 (L-D13: ask the lead).
- L8 An SSN-shaped value glued to a letter or `_` (`ssn 123-45-6789a`): K73 (L-D11).
- L9 (v3: closed by L-D12 by default; stays a limit only under its fallback).
- L10 (v3, new) A letter glued right before `ip-` / `ec2-` (`xip-10-0-3-22`, `zip-...`), a digit before a pod-DNS address
  (`710-0-3-22.ns.pod`): rows 85, 86.
- L11 (v3, new) A piece of a secret with the shape of a stored kind (an IPv4 address, a phone number) is registered under that kind
  and is storable: AT1-AT3 (and AT4 on the base already); L-D14.
- Over-masks accepted by decision (fail safe, evidence lost, not a leak): L-D4 (K27), L-D8 (K43-K53), L-D10 (K26, K54-K60),
  L-D11 (K78). AT5, AT6: a stored-kind original that holds `_` + an IBAN shape is not stored or is cut (fail safe).

## 12. Risks
- Over-masking classes are listed with their decisions (section 6).
- At rest: L11 (a piece of a secret stored as IPV4 or PHONE), now also for glued pieces.
- Label: `+123-45-6789x` is stored as PHONE (L-D11); a value masked as PHONE / IPV4 out of a version or an epoch is stored.
- Numbering: in a text with a contiguous and a `+`-led number, the `+`-led one is `<PHONE_1>` (K65).
- The gate: a known phone number glued to a word in model-visible text is rewritten (`build<PHONE_1>`); the model sees that text.
- G4: rows 60-62 and 66 change under G4c (the flag handles it); textual conflicts in redact.py and the property test (8.1).
- Non-ASCII glue (a Cyrillic letter or a full-width digit beside an IP) goes through the fold scan first; not probed.

## 13. For SECURITY wording (proposed text; through the security wording review)
SECURITY.md bullet (appended as section 3 says):
"- Values glued to other text. An IPv4 address, an IBAN, a UUID, a card number and a phone number written with `+` are masked
when an underscore, and for most of them a letter, is glued to them (`node_10.0.0.1`, `id x<uuid>`, `x4242 4242 4242 4242`), the
glued text left in place. Not masked, by design: a phone number written as one run of digits with a letter directly before or
after it (`x4155550132`), because hashes and identifiers have that shape (it is masked when the same number also appears on its
own in the same text); a phone number without `+` with a letter after it (`415-555-0132x123`); an IBAN with a letter or digit
glued directly before it (`xDE89...`), because the same shape appears inside long tokens and masking it there would cut a
credential in two; an IPv4 address with a digit glued before it, or a dashed EC2 name with a letter before `ip-`; two addresses
or two IBANs written together with nothing between; a host name with a letter, digit or underscore glued after its private
suffix (`db01.prod.corpa`); a US Social Security number with a letter glued to it; a phone number directly followed by a full
stop. A part of a password that looks like an address or a phone number (`hunter192.0.2.10x`) can be kept in the run's map as
that kind. To be safe, some things that only look like these values are masked: four-part version numbers glued to a word
(`python3.11.4.1`) and long digit runs after an underscore (`order_1234567890`). Masked numbers and addresses are kept in the
run's map and can be restored like any other masked value."
CHANGELOG.md bullet (`### Upgrade steps` of `## Unreleased`):
"- **G8, values glued to a word.** An IPv4 address, an IBAN, a UUID, a card number and a `+` phone number glued to a letter or an
underscore are now masked in the first pass, with the glued text left outside the placeholder. You may see placeholders inside
words where you saw text before (`python<IPV4_1>`, `order_<PHONE_1>`). A known phone number glued to a word is replaced in text
sent to a model too. The limits are listed in SECURITY.md."

## 14. What is NOT verified
- The whole test suite (box rule: not run by the drafter); section 9 lists the files run. A base-vs-G8 diff of full-suite failure
  lists is phase 0 (d) / phase 3's job.
- The perf tests of appendix B under pytest (the cost script ran instead, section 10); ratios on a quiet box.
- The fallbacks of section 6 marked "not run"; L-D3's G8c with G4 v4.
- G4 v5 (being drafted; v4 measured, its file at this base is still v4's text); G4a / G4b with the G8 rows (4.5); the G4 property
  corpus with G8; G9 with G8 (textual conflict only, by reading).
- Non-ASCII glue; Python 3.12; Windows; approval-card paths beyond the files of section 9.

## 15. Notes on what cannot be tested
- `runmap._sweep_held` with `_joins`: no input known that holds a PHONE value back; decided for consistency, no test, no mutant.
- The property oracle edit: it makes the oracle agree with production; a mutant of `_joins` is caught by appendix B.

## 16. Findings of G8-review-2, one by one
Readiness reviewer:
- Major 1 (G4 v4 not reconciled) TAKEN: section 8.1 states the order (G8 first, `G4C_MERGED = False`) and the fallback, the four
  edits the G4 ticket must carry (flip the flag in the G4c commit, which turns rows 64 / 71 into ordinary tests and switches rows
  60-62 / 66 to the G4c column; the G8 file in G4's phase 4 run list and the G8 mutants in its phase 5), who rebases the property
  test and the docstring (the second lander), and the g3_port clause (8.1 G4-4). The host column is re-measured with G4 v4's
  HOSTNAME and HOSTKEY (4.5): identical to v2's G4 v3 column. G4 v5 is being drafted (its file at a5247ac4a is still v4's text):
  named as a dependency; a G4 v5 regex change is caught by G4-2's run.
- Major 2 (G4a / G4b vs must-keep rows) TAKEN as a step, CONTESTED in part: G4a and G4b are not built and their code is a
  `runmap.redact_text` refactor, so nothing can be measured now; `test_must_keep_rows` uses `redact()`, which they do not change.
  K60 and K66 are named as the rows a base64 view could move through `redact_text`; the rule for the second lander is in 4.5 / 8.1
  (run the G8 file; a changed row is a finding). "Mark K60/K66 as expected to move" is not taken: no measurement says they move.
- Major 3 (cost not runnable) TAKEN: appendix F (tests/g8_cost.py) times the six texts through `redact()` and
  `runmap.redact_text` at 65,536 and 262,144 characters; phase 0 (e) runs it on the base archive, phase 3 on the build and
  compares; acceptance rule and action on failure in section 10. The perf test docstring no longer quotes "4.6"; v1's figures are
  labelled v1 (section 10).
- Major 4 (mutant expects never run) TAKEN: the 30 mutants were run on the formatted tree (section 9): 30 of 30 good after two
  expect corrections (P1 `ROW 21 `, P4 `ROW K5 `) and the pinned-case fix; the rule "a BAD caused only by a wrong expect is
  corrected to the actual first failing line; a surviving mutant is a stop" is in phase 4.
- Major 5 (phase 2 vs the flake note) TAKEN: the G8 file runs alone with its own count (phase 1+2 step 1); the flake note says
  833a86b fixed it and a red there is a finding.
- Major 6 (phase 1 red ids by reading) TAKEN both ways: the G8a-only prototype `v3a` was run (exactly the three ids); phases 1
  and 2 are merged into one commit by default, the two-commit variant names the three ids and "any other red id: STOP".
- Nits TAKEN: phase 3 is "a SUBSET of phase 0 (d)'s failures" (the `.git` difference named); SECURITY.md insertion point (line 9
  heading, after the second bullet) and the CHANGELOG form (`### Upgrade steps`, bold lead) named (section 3); the four files v2's
  `ruff format` reflowed are named and v3's appendices are pre-formatted (section 8); how to apply D / E (`patch -p1`, no fuzz) and
  A / B / C / F (copy the fenced block) is stated.
Codebase reviewer:
- F1 (IBAN camelCase start inside an opaque token) TAKEN, measured first (2.4), with one part CONTESTED: the stated scenario
  (140 characters, "about 110 characters readable") does not happen: the 40+ HIGHENTROPY entry masks the 95+ character head, so a
  129-163-character token loses nothing to the reader (measured: 0 of 350 injected, 0 of 20,000 random); its cost there is a split
  map entry. The real leak is for 40-75-character tokens (head under 40 characters): up to 39 characters readable in 89 of 356
  injected tokens and 0.46 / 0.13 percent of random ones. Decision L-D2: the fallback start `(?<![A-Za-z0-9])` is the default
  (identical to the base in every class); rows K75-K77 added; mutant I3 pins it.
- F2 (three wrong expects, S2 anchor) TAKEN and run: P1 = `ROW 21 ` (as the reviewer said); P3 = `ROW 21 ` for v3's `+`-only entry
  (the reviewer's `ROW 18 ` was right for v2's P3, which removed branch B; v3's P3 refuses a letter before `+`, and row 18 has a
  space there: measured `ROW 21`); P6 removed (v3 has no 5-digit guard: L-D9 flipped); P4 re-targeted (`+` made optional:
  `ROW K5 `, measured). S2's `old` is `original, placeholder, _joins(placeholder)` (one occurrence, unchanged by `ruff format`).
  One more defect found by running: every v2 mutant pinned the killer function without its case (`...::test_glued_rows_are_masked`),
  while the runner's id is `...::test_glued_rows_are_masked[row36]`, so all 28 would have been `BAD OTHER_TEST`; `m()` now adds
  the case from the expect.
- F3 (model_gate.py:12-14 and the redact.py sweep comment) TAKEN: both in section 3 Modify and appendix D; the pinning test gets
  the PHONE assertion (appendix E).
- F4 (dashed and pod-DNS IPv4 glued before) TAKEN: EC2 start `(?<![A-Za-z0-9])`, pod start `(?<![0-9])`; rows 81-84 closed, rows
  85 (`xip-...`) and 86 (`7...pod`) limit L10 with strict xfails; mutants V6, V7. A letter right before `ip-` stays a limit because
  `zip-`, `vip-`, `skip-` + four numbers would then be read as addresses.
- F5 (G4 v4 in S, citations) TAKEN: citations re-pointed to v4 (a029802bd1f3); the `after_g4c` column re-measured with v4's regex
  (4.5); the g3_port clause settled (8.1 G4-4); textual overlap stated (PATTERNS near HOSTNAME, the docstring, the property test).
- F6 nits and gaps:
  - at-rest storage of secret pieces TAKEN: measured rows AT1-AT6 with map and `storable()` (2.5, `test_at_rest_rows`); the class
    exists on the base (AT4); limit L11 and L-D14 (follow-up, not G8).
  - IBAN vs `_SECRET_PATTERNS` TAKEN: AT5 (an ARN holding `_DE89...` no longer storable) and AT6 (a tenant cut), fail safe, stated;
    the fallback IBAN start narrows it (a letter-glued IBAN shape no longer counts).
  - CREDITCARD glued (L9) TAKEN beyond the ask: measured and closed by default (L-D12; only K36, K74 change; K80 added; mutants C1,
    C2), with "keep L9" as the fallback.
  - phone before a full stop TAKEN as a question to the lead (L-D13) with the default "unchanged" and the measured fallback.
  - branch A of entry 6 (v2 called it entry 5; CHANGED in v4, N2) / L-D9 TAKEN: the default is flipped to `+`-led only (measured: K34, K70, K71, K72 back to the base; the
    probe counts unchanged; row 75 now changes).
  - import line TAKEN (`_joins` at runmap.py:32).
  - "the model sees the gate's rewritten text" TAKEN (4.2, the model_gate.py docstring, section 12).
  - the step-0 script compares the base `now` column: TAKEN as stated (phase 0 runs it on the base only; the G4-first fallback
    says which BAD lines are expected).
- Design attacks, citations, "tests that go red": checked against a5247ac4a; line numbers updated (G7 round 6 moved the oracle to
  :141, the sweep call to 2041, `_replace_standalone` to 2228); nothing further to take.

## 17. Findings of G8-review-1 (resolved in v2, kept)
B1 (exact regexes: 4.1, appendix D), B2 (exact red ids: section 7, re-measured), B3 (limit rows assert the desired behaviour under
strict xfail), B4 (order: 8.1; host rows re-measured with G4 v4), M1 (must-keep rows, now 80), M2 (decisions with consequences,
section 6), M3 (leak rule and data in appendix A), M4 (`_JOINS` PHONE only), M5 (cost: now with a script, section 10), M6 (suite
command; the full suite stays the builder's phase 0 (d) / 3), M7 (phases with commands), N1-N6, the "For SECURITY wording" form;
codebase M1 (the `+` entry redesign, v2's "entry 5", now entry 6 (CHANGED in v4, N2): v3 keeps only its `+` branch, L-D9), M2 (versions L-D8; `1.2.3.4rc1` not masked today), M3
(`_sweep_held`, the oracle, the gate test), M4 (host rows with two columns), M5 (suites, g3 re-point, fold_budget live), N1
(`>` guard, K64), N2 (K65), N3 (K35, K57, K59, K62, K63, K66), N4, N5: all kept as v2 resolved them, re-measured on a5247ac4a.

## Appendix A: tests/g8_cases.py (create; complete)
```python
"""Ticket G8 (glued-rest gap): the 86 probe rows, the must-keep rows, the full-stop rows and the at-rest rows, as data.
Not collected by pytest.

Every value is fake or a documentation value and is built from parts here (no literal of a full value elsewhere, as
tests/test_text_parts_together.py does). A row is
    (id, kind, shape, text, value, cls, now, after, after_g4c)
with `text`, `now`, `after` and `after_g4c` templates over `V` (`{IP1}` ...) that `case()` fills in:
    now       `redact(text).text` on the base commit (step 0, recorded on cloud/core-c a5247ac4a; `python -m tests.g8_cases`
              re-checks it and exits 1 on any difference)
    after     `redact(text).text` with G8a + G8b, G4c NOT merged
    after_g4c the same once G4c (ticket G4 v4 sections 5.2 and 5.3, blob a029802bd1f3) is merged; None = same as `after`
    cls       closed (leaks now, not after) | changed (no leak either way, the output changes) | unchanged | limit (still
              leaks after G8: a stated limit) | g4c (closed by G4c, not by G8)
"""

from __future__ import annotations

import difflib
import re
import string
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

# Is G4c merged into this tree? The G4c builder sets True in the G4c commit (ticket G8 v3, section 8.1). Until then the host
# rows are checked against `after` and rows 64 and 71 are strict xfails naming G4c.
G4C_MERGED = False

# fmt: off
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
    (38, 'iban', 'letter before', 'pay x{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay x{IBAN_DE} now', 'pay x{IBAN_DE} now', None),
    (39, 'iban', 'word before', 'pay iban{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay iban{IBAN_DE} now', 'pay iban{IBAN_DE} now', None),
    (40, 'iban', 'digit before', 'pay 7{IBAN_DE} now', 'IBAN_DE', 'limit', 'pay 7{IBAN_DE} now', 'pay 7{IBAN_DE} now', None),
    (41, 'iban', '_ before', 'pay iban_{IBAN_DE} now', 'IBAN_DE', 'closed', 'pay iban_{IBAN_DE} now', 'pay iban_<IBAN_1> now', None),
    (42, 'iban', 'both _', 'pay to_{IBAN_DE}_x now', 'IBAN_DE', 'closed', 'pay to_{IBAN_DE}_x now', 'pay to_<IBAN_1>_x now', None),
    (43, 'iban', 'clean copy + _x copy', 'pay {IBAN_DE} or {IBAN_DE}_x now', 'IBAN_DE', 'unchanged', 'pay <IBAN_1> or <IBAN_1>_x now', 'pay <IBAN_1> or <IBAN_1>_x now', None),
    (44, 'iban', 'GB, _x after', 'pay {IBAN_GB}_x now', 'IBAN_GB', 'closed', 'pay {IBAN_GB}_x now', 'pay <IBAN_1>_x now', None),
    (45, 'iban', 'GB, letter before', 'pay x{IBAN_GB} now', 'IBAN_GB', 'limit', 'pay x{IBAN_GB} now', 'pay x{IBAN_GB} now', None),
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
    (75, 'phone', 'two formatted phones glued', 'call {PHONE_P}{PHONE_P2} now', 'PHONE_P', 'changed', 'call <PHONE_1>+<PHONE_2> now', 'call <PHONE_1><PHONE_2> now', None),
    (76, 'iban', 'two IBANs glued', 'pay {IBAN_DE}{IBAN_GB} now', 'IBAN_DE', 'limit', 'pay {IBAN_DE}{IBAN_GB} now', 'pay {IBAN_DE}{IBAN_GB} now', None),
    (77, 'uuid', 'two UUIDs glued', 'id {UUID}{UUID2} ok', 'UUID', 'closed', 'id {UUID}{UUID2} ok', 'id <UUID_1><UUID_2> ok', None),
    (78, 'host', 'bare .local, digit after', 'x {HOST4}9 y', 'HOST4', 'limit', 'x {HOST4}9 y', 'x {HOST4}9 y', None),
    (79, 'host', 'bare .local, _x after', 'x {HOST4}_x y', 'HOST4', 'limit', 'x {HOST4}_x y', 'x {HOST4}_x y', None),
    (80, 'host', 'bare .internal, letter after', 'x {HOST5}x y', 'HOST5', 'limit', 'x {HOST5}x y', 'x {HOST5}x y', None),
    # v3 (G8-review-2 F4): the dashed forms glued BEFORE the address
    (81, 'ipv4', 'dashed EC2 name, _ before', 'node host_ip-{IPD} up', 'IPD', 'closed', 'node host_ip-{IPD} up', 'node host_ip-<IPV4_1> up', None),
    (82, 'ipv4', 'dashed EC2 name (ec2), _ before', 'node my_ec2-{IPD} up', 'IPD', 'closed', 'node my_ec2-{IPD} up', 'node my_ec2-<IPV4_1> up', None),
    (83, 'ipv4', 'pod DNS, _ before', 'pod_{IPD}.ns.pod up', 'IPD', 'closed', 'pod_{IPD}.ns.pod up', 'pod_<IPV4_1>.ns.pod up', None),
    (84, 'ipv4', 'pod DNS, letter before', 'x{IPD}.ns.pod up', 'IPD', 'closed', 'x{IPD}.ns.pod up', 'x<IPV4_1>.ns.pod up', None),
    (85, 'ipv4', 'dashed EC2 name, letter before ip-', 'node xip-{IPD} up', 'IPD', 'limit', 'node xip-{IPD} up', 'node xip-{IPD} up', None),
    (86, 'ipv4', 'pod DNS, digit before', '7{IPD}.ns.pod up', 'IPD', 'limit', '7{IPD}.ns.pod up', '7{IPD}.ns.pod up', None),
]
# fmt: on

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
    return (
        difflib.SequenceMatcher(None, a, b, autojunk=False)
        .find_longest_match(0, len(a), 0, len(b))
        .size
    )


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
ALNUM = string.ascii_uppercase + string.ascii_lowercase + string.digits
# G8-review-2 F1: an IBAN-shaped tail (`a` + `DE89` + 18 letters or digits) at the end of an opaque token.
F1_TAIL = J(["a", "DE89", "Xq7Lm2Pw9Rt4Ys6Vb3"])


def opaque(n: int) -> str:
    """n characters of a made-up token with upper case, lower case and digits (no IBAN or other shape inside)."""
    return J(ALNUM[(7 * i + 3) % 62] for i in range(n))


# (id, text, now, after, verdict); None = the text itself. verdict: kept (nothing masked, before and after) | same (masked
# today, G8 does not change it, or changes only what the note says) | over-mask L-Dn (accepted by that decision) | closed (a
# real value newly masked). K1-K28 are v1's table; K29-K74 the reviewers' examples and the drafter's v2 traces; K75-K80 v3's
# (G8-review-2 F1 and F6). The opaque tokens of K75-K77 are built here (`opaque()`), not written out.
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
    ("K24", "req ReqIdDE12345678901234 ok", None, None, "kept (L-D2)"),
    ("K25", "tag xDE00ABCDEFGHIJK ok", None, None, "kept (L-D2)"),
    ("K26", "ts 1732095071000_x", None, "ts <PHONE_1>_x", "over-mask L-D10"),
    (
        "K27",
        "uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe",
        None,
        "uuid-ish <UUID_1>cafe",
        "over-mask L-D4",
    ),
    ("K28", "id " + V["UUID"].replace("-", "") + " ok", None, None, "kept"),
    ("K29", "eth0 1500 9000", None, None, "kept"),
    ("K30", "ipv4 1500 1600", None, None, "kept"),
    ("K31", "vlan10 2001 2002", None, None, "kept"),
    ("K32", "node1 8080 9090", None, None, "kept"),
    ("K33", "PO12-3456-7890", None, None, "kept"),
    (
        "K34",
        "rtt 120 118 131 125ms",
        "rtt <PHONE_1> 125ms",
        "rtt <PHONE_1> 125ms",
        "same (L-D9: 3 of 4 masked today)",
    ),
    ("K35", "backup_20-11-2026 done", None, None, "kept"),
    ("K36", "x" + CARD, "x4242 <PHONE_1>", "x<CREDITCARD_1>", "closed (L-D12)"),
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
    (
        "K60",
        "b64url Zm9vYmFy_1234567890_YmF6",
        None,
        "b64url Zm9vYmFy_<PHONE_1>_YmF6",
        "over-mask L-D10",
    ),
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
    ("K66", "blob aGVsbG8+aDE12abcdefghijk/x", None, None, "kept (L-D2)"),
    (
        "K67",
        "known 1.2.3.4 and v1.2.3.4",
        "known <IPV4_1> and v1.2.3.4",
        "known <IPV4_1> and v1.2.3.4",
        "same (L-D1)",
    ),
    ("K68", "rev 2-" + SHA[:16], None, None, "kept"),
    ("K69", "color #415555 and #0a0b0c", None, None, "kept"),
    ("K70", "sizes 1024 2048 4096ms", None, None, "kept (L-D9)"),
    (
        "K71",
        "took 100 200 300 400ms",
        "took <PHONE_1> 400ms",
        "took <PHONE_1> 400ms",
        "same (L-D9: 3 of 4 masked today)",
    ),
    (
        "K72",
        "call 415-555-0132x123",
        None,
        None,
        "kept (L-D9: an extension glued to a number without + stays readable)",
    ),
    ("K73", "ssn " + SSN + "a", None, None, "kept (L-D11: a stated limit, not a choice)"),
    ("K74", "card " + CARD + "x", "card <PHONE_1> 4242x", "card <CREDITCARD_1>x", "closed (L-D12)"),
    (
        "K75",
        "key " + opaque(37) + F1_TAIL + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D2: F1, 60 characters)",
    ),
    (
        "K76",
        "key " + opaque(117) + F1_TAIL + " end",
        "key <HIGHENTROPY_1> end",
        "key <HIGHENTROPY_1> end",
        "same (L-D2: F1, 140)",
    ),
    (
        "K77",
        "Authorization: Bearer " + opaque(37) + F1_TAIL + " end",
        "Authorization: Bearer <BEARER_1> end",
        "Authorization: Bearer <BEARER_1> end",
        "same (L-D2: F1, BEARER)",
    ),
    ("K78", "+123-45-6789x", None, "<PHONE_1>x", "over-mask L-D11 (stored as PHONE)"),
    ("K79", "x+" + SSN, "x+<SSN_1>", "x+<SSN_1>", "same (the SSN entry runs first)"),
    (
        "K80",
        "card_" + CARD.replace(" ", "-") + "_x",
        None,
        "card_<CREDITCARD_1>_x",
        "closed (L-D12)",
    ),
]
# Found on the way, NOT glued, unchanged by G8 (stated limit L7): a phone number before a full stop is not masked.
FULL_STOP = [
    ("F1", "call 415-555-0132."),
    ("F2", "call " + P10 + "."),
    ("F3", "call " + V["PHONE_P"] + "."),
]
# At rest (G8-review-2 F6): (id, text, now, after): each side is (text, sorted map items, sorted storable items) of
# `redact(text)` and `runmap.storable(mapping)`. AT1-AT3: a piece of a secret with a stored kind's shape is registered under
# that kind and is storable (limit L11; AT4 shows the base does the same for a piece set off by `-`). AT5, AT6: IBAN in
# `runmap._SECRET_PATTERNS` (the start now accepts `_`): an ARN that holds `_DE89...` is no longer storable, a tenant is split.
IP1, IBAN = V["IP1"], V["IBAN_DE"]
AT_REST = [
    (
        "AT1",
        "password=hunter" + IP1 + "x",
        ("password=<SECRET_1>", [("<SECRET_1>", "hunter" + IP1 + "x")], []),
        (
            "password=<SECRET_1>",
            [("<IPV4_1>", IP1), ("<SECRET_1>", "hunter" + IP1 + "x")],
            [("<IPV4_1>", IP1)],
        ),
    ),
    (
        "AT2",
        "password=hunter_" + P10,
        ("password=<SECRET_1>", [("<SECRET_1>", "hunter_" + P10)], []),
        (
            "password=<SECRET_1>",
            [("<PHONE_1>", P10), ("<SECRET_1>", "hunter_" + P10)],
            [("<PHONE_1>", P10)],
        ),
    ),
    (
        "AT3",
        "token=x+1" + P10 + "y",
        ("token=<SECRET_1>", [("<SECRET_1>", "x+1" + P10 + "y")], []),
        (
            "token=<SECRET_1>",
            [("<PHONE_1>", "+1" + P10), ("<SECRET_1>", "x+1" + P10 + "y")],
            [("<PHONE_1>", "+1" + P10)],
        ),
    ),
    (
        "AT4",
        "password=a-" + IP1 + "-b",
        (
            "password=<SECRET_1>",
            [("<IPV4_1>", IP1), ("<SECRET_1>", "a-" + IP1 + "-b")],
            [("<IPV4_1>", IP1)],
        ),
        None,
    ),
    (
        "AT5",
        "arn:aws:s3:::bucket_" + IBAN,
        (
            "<ARN_1>",
            [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)],
            [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)],
        ),
        ("<ARN_1>", [("<ARN_1>", "arn:aws:s3:::bucket_" + IBAN)], []),
    ),
    (
        "AT6",
        "tenant_id=acme_" + IBAN,
        (
            "tenant_id=<TENANT_1>",
            [("<TENANT_1>", "acme_" + IBAN)],
            [("<TENANT_1>", "acme_" + IBAN)],
        ),
        (
            "tenant_id=<TENANT_1><IBAN_1>",
            [("<IBAN_1>", IBAN), ("<TENANT_1>", "acme_")],
            [("<TENANT_1>", "acme_")],
        ),
    ),
]


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


if (
    __name__ == "__main__"
):  # step 0: on the base commit every `now` must hold (exit 1 otherwise); the output is the record
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
    from hadavin_sdk.guard.runmap import storable

    for aid, text, now, _after in AT_REST:
        r = redact(text)
        got = (r.text, sorted(r.mapping.items()), sorted(storable(dict(r.mapping)).items()))
        bad += got != now
        print(("ok  " if got == now else "BAD ") + f"{aid}: {got!r}")
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


GLUED_OUTSIDE = (2, 3, 4, 5, 7, 8, 9, 18, 19, 20, 36, 37, 47, 48, 49, 50, 51, 81, 82, 83, 84)
LIMITS = {
    10: "L1",
    13: "L2",
    25: "L3",
    27: "L3",
    38: "L4",
    39: "L4",
    40: "L4",
    45: "L4",
    76: "L5",
    85: "L10",
    86: "L10",
}
LIMITS.update({i: "L6" for i in (67, 68, 69, 70, 78, 79, 80)})
OPAQUE = ("K75", "K76", "K77")


@pytest.mark.parametrize("c", _rows("closed", "changed"))
def test_glued_rows_are_masked(c):
    t = c["text"]
    many = redact_many([t, "other line"])[0][0]
    for where, out in (
        ("redact", redact(t).text),
        ("redact_many", many),
        ("redact_text", runmap.redact_text(t, runmap.RunMap())),
    ):
        assert out == c["expected"], f"ROW {c['id']} {where}: {out!r}"
        assert not G.leak(c["kind"], c["value"], out), f"ROW {c['id']} {where} leaks: {out!r}"


@pytest.mark.parametrize("c", _ids(*GLUED_OUTSIDE))
def test_glued_character_stays_outside_the_placeholder(c):
    r = redact(c["text"])
    ph = next(
        p for p, o in r.mapping.items() if o == c["value"]
    )  # StopIteration (red) when the value is not masked whole
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
        pytest.param(
            G.BY_ID[i],
            id=f"row{i}",
            marks=pytest.mark.xfail(strict=True, reason=f"stated limit {lim} (ticket G8)"),
        )
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
            marks=[]
            if G.G4C_MERGED
            else [pytest.mark.xfail(strict=True, reason="closed by G4c (ticket G4), not by G8")],
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


@pytest.mark.parametrize("k", [pytest.param(k, id=k["id"]) for k in G.KEEP if k["id"] in OPAQUE])
def test_an_iban_never_starts_inside_an_opaque_token(k):
    """G8-review-2 F1 (L-D2): an IBAN-shaped tail inside a long letter-and-digit token is not an IBAN; the token is masked
    whole as before and the map holds one entry (a camelCase start split it and left up to 39 characters readable)."""
    out = redact(k["text"])
    assert out.text == k["after"] and len(out.mapping) == 1, (
        f"OPAQUE {k['id']}: {out.text!r} {sorted(out.mapping)!r}"
    )


@pytest.mark.parametrize("aid,text,now,after", [pytest.param(*a, id=a[0]) for a in G.AT_REST])
def test_at_rest_rows(aid, text, now, after):
    """G8-review-2 F6: what `redact()` writes to the map and what `runmap.storable` keeps of it. AT1-AT3 pin limit L11 (a
    piece of a secret with a stored kind's shape is stored), AT5 and AT6 the IBAN start's effect on stored originals."""
    r = redact(text)
    got = (r.text, sorted(r.mapping.items()), sorted(runmap.storable(dict(r.mapping)).items()))
    assert got == (after or now), f"AT {aid}: {got!r}"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_second_call_changes_nothing(c):
    m = runmap.RunMap()
    once = runmap.redact_text(c["text"], m)
    snap = dict(m)
    assert runmap.redact_text(once, m) == once and dict(m) == snap, f"ROW {c['id']} second call"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_untrusted_matches_redact_text(c):
    assert runmap.redact_untrusted(c["text"], runmap.RunMap()) == runmap.redact_text(
        c["text"], runmap.RunMap()
    )


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(c, id=f"row{c['id']}")
        for c in G.CASES
        if c["kind"] in ("ipv4", "phone") and "UUID" not in c["after"]
    ],
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
    assert out == f"a x<PHONE_1> and a{p}0b", (
        f"SWEEP phone digit: {out!r}"
    )  # a digit beside it: another number
    ip = G.V["IP1"]
    out = redact(f"known {ip} and v{ip}").text
    assert out == f"known <IPV4_1> and v{ip}", (
        f"SWEEP ipv4: {out!r}"
    )  # IPV4 is not in _JOINS (L-D1)
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
    assert R._has_bank_word(glued) is False, (
        "BANK glued uuid"
    )  # True before G8: the UUID's tail read as an ABA number


def test_row_counts_are_pinned():
    from collections import Counter

    assert (
        len(G.CASES) == 86 and len(G.KEEP) == 80 and len(G.FULL_STOP) == 3 and len(G.AT_REST) == 6
    )
    assert Counter(c["cls"] for c in G.CASES) == {
        "closed": 48,
        "unchanged": 15,
        "limit": 18,
        "changed": 3,
        "g4c": 2,
    }
    assert sorted(LIMITS) == sorted(c["id"] for c in G.CASES if c["cls"] == "limit")


HOSTILE = {
    "dots": "1.",
    "digits and spaces": "x1 2 3 4 5 6 7 8 9 ",
    "underscore digits": "_4155550132",
    "hex and dashes": "deadbeef-dead-beef-dead-",
    "iban-ish": "aDE89" + "A" * 40 + " ",
    "plus digits": "a+1 415-555-0132",
}


CALLS = {
    "redact": lambda t: redact(t),
    "redact_text": lambda t: runmap.redact_text(t, runmap.RunMap()),
}


@pytest.mark.perf
@pytest.mark.parametrize("call", sorted(CALLS))
@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_glued_patterns_are_linear(name, call):
    """CPU seconds (`time.thread_time`, best of 3) for 65,536 and 262,144 characters, through `redact()` and through
    `runmap.redact_text`: the ratio is at most 6.0 (4x the text) and the large text takes under 3.0 s. The base-vs-G8
    comparison is tests/g8_cost.py (ticket G8 v3 section 10), not this test."""

    def best(n: int) -> float:
        text = (HOSTILE[name] * (n // len(HOSTILE[name]) + 1))[:n]
        out = []
        for _ in range(3):
            t0 = time.thread_time()
            CALLS[call](text)
            out.append(time.thread_time() - t0)
        return min(out)

    small, large = best(65_536), best(262_144)
    assert large < 3.0, f"{name} {call}: {large:.2f} s"
    assert large / max(small, 1e-3) <= 6.0, f"{name} {call}: ratio {large / max(small, 1e-3):.2f}"
```

## Appendix C: tests/g8_mutants.py (create; complete; run: 30 of 30 good, section 9)
```python
"""The mutants of ticket G8 (glued-rest gap), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must
hold ``expect`` (the ``ROW <id> ...``, ``OPAQUE ...`` or ``SWEEP ...`` start of the assertion message). Every ``old`` is a
fragment that ``ruff format`` leaves as it is (ticket G8 v3, section 8 phase 4). Run from the repo root:

    python tests/g8_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g8_mutants.py G8-P       # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
RD = "src/hadavin_sdk/guard/redact.py"
TEST = "tests/test_redact_glued_rest.py"
PIN = "tests/test_redact_glued_rest::"
UU = r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
E5 = '    ("PHONE", re.compile(r"(?<![0-9.\\-])\\+\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![0-9.])")),\n'
MAIN = (
    '    (\n        "PHONE",\n        re.compile(\n            r"(?<![\\w.\\-])(?!\\d{4}-\\d\\d-\\d\\d)"\n'
    '            r"(?!(?:19|20)\\d\\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01])(?:[01]\\d|2[0-3])[0-5]\\d[0-5]\\d(?!\\d))"\n'
    '            r"\\+?\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![\\w.])"\n        ),\n    ),\n'
)
TS = r'r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"'
J5 = '_JOINS = {"PHONE": frozenset(string.digits)}'


def m(name, old, new, killer, expect, file=RD):
    # the pinned id names the parametrized case the expect names: "ROW 36 " -> [row36], "ROW K2 " / "OPAQUE K75" -> [K2] / [K75]
    tag = expect.split()[1] if expect.startswith(("ROW ", "OPAQUE ")) else ""
    case = "" if not tag else f"[row{tag}]" if tag.isdigit() else f"[{tag}]"
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer + case
    )


GR, KEEP, SW = (
    "test_glued_rows_are_masked",
    "test_must_keep_rows",
    "test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only",
)
OPQ = "test_an_iban_never_starts_inside_an_opaque_token"
M = [
    m("G8-I1 IBAN end back to \\b", r'r"\d{2}[A-Za-z0-9]{11,30}(?![A-Za-z0-9])"', r'r"\d{2}[A-Za-z0-9]{11,30}\b"', GR, "ROW 36 "),
    m("G8-I2 IBAN start back to \\b", 'r"(?<![A-Za-z0-9])(?:AD|AE', 'r"\\b(?:AD|AE', GR, "ROW 41 "),
    m("G8-I3 IBAN start with the camelCase part (v2, F1)", 'r"(?<![A-Za-z0-9])(?:AD|AE', '_NOT_IN_WORD + r"(?:AD|AE', OPQ, "OPAQUE K75"),
    m("G8-U1 UUID end \\b", UU + '"', UU + r'\b"', GR, "ROW 14 "),
    m("G8-U2 UUID start \\b", r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', r'r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', GR, "ROW 51 "),
    m("G8-V1 IPV4 dotted end \\b", r'(?:\d{1,3}\.){3}\d{1,3}(?![0-9])"', r'(?:\d{1,3}\.){3}\d{1,3}\b"', GR, "ROW 2 "),
    m("G8-V2 IPV4 dotted start \\b", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"\b(?<!(?<![A-Za-z])[vV])', GR, "ROW 7 "),
    m("G8-V3 IPV4 drop the digit look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<!(?<![A-Za-z])[vV])', KEEP, "ROW K2 "),
    m("G8-V4 IPV4 drop the lone-v look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<![0-9])', KEEP, "ROW K1 "),
    m("G8-V5 EC2 end \\b", r'(\d{1,3}(?:-\d{1,3}){3})(?![0-9])"', r'(\d{1,3}(?:-\d{1,3}){3})\b"', GR, "ROW 72 "),
    m("G8-V6 EC2 start back to \\b", r'r"(?<![A-Za-z0-9])(?:ip|ec2)-', r'r"\b(?:ip|ec2)-', GR, "ROW 81 "),
    m("G8-V7 pod DNS start back to \\b", r'r"(?<![0-9])(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod', r'r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod', GR, "ROW 83 "),
    m("G8-C1 card start back to \\b", r'r"(?<![0-9])\d{4}[ \-]\d{4}', r'r"\b\d{4}[ \-]\d{4}', KEEP, "ROW K36 "),
    m("G8-C2 card end back to \\b", r'[ \-]\d{4}(?![0-9])"', r'[ \-]\d{4}\b"', KEEP, "ROW K74 "),
    m("G8-P1 the + entry after the main PHONE entry", E5 + MAIN, MAIN + E5, GR, "ROW 21 "),
    m("G8-P2 the + entry removed", E5, "", GR, "ROW 18 "),
    m("G8-P3 the + entry refuses a letter before +", r're.compile(r"(?<![0-9.\-])\+\d', r're.compile(r"(?<![\w.\-])\+\d', GR, "ROW 21 "),
    m("G8-P4 the + entry takes a number without +", r'r"(?<![0-9.\-])\+\d(?:', r'r"(?<![0-9.\-])\+?\d(?:', KEEP, "ROW K5 "),
    m("G8-P5 the + entry end back to the main guard", r'[\d \-]){8,14}\d(?![0-9.])"', r'[\d \-]){8,14}\d(?![\w.])"', GR, "ROW 18 "),
    m("G8-P8 the _ entry allows a letter after", r'r"\d{10,16}(?![0-9A-Za-z.>])"', r'r"\d{10,16}(?![0-9.>])"', KEEP, "ROW K8 "),
    m("G8-P9 the _ entry without the timestamp guard", '|(?=\\d{10,16}_))"\n            ' + TS + "\n", '|(?=\\d{10,16}_))"\n', KEEP, "ROW K16 "),
    m("G8-P10 the _ entry without the > guard", r'r"\d{10,16}(?![0-9A-Za-z.>])"', r'r"\d{10,16}(?![0-9A-Za-z.])"', KEEP, "ROW K64 "),
    m("G8-P11 the _ entry needs _ before", r'(?:(?<=_)|(?=\d{10,16}_))', r'(?<=_)', GR, "ROW 26 "),
    m("G8-P12 keyword entry without tel", "(?:tel|phone|mobile|cell|fax)", "(?:phone|mobile|cell|fax)", GR, "ROW 28 "),
    m("G8-S1 _JOINS empty", J5, "_JOINS = {}", GR, "ROW 31 "),
    m("G8-S2 sweep call without joins", "original, placeholder, _joins(placeholder)", "original, placeholder", GR, "ROW 31 "),
    m("G8-S3 HOSTNAME given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "HOSTNAME": frozenset(string.digits)}', SW, "SWEEP host"),
    m("G8-S4 IPV4 given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "IPV4": frozenset(string.digits)}', SW, "SWEEP ipv4"),
    m("G8-S5 TENANT given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "TENANT": frozenset(string.digits)}', SW, "SWEEP tenant"),
    m("G8-S6 PHONE copy beside a digit replaced too", J5, '_JOINS = {"PHONE": frozenset()}', SW, "SWEEP phone digit"),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
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

## Appendix D: the source diff against a5247ac4a (redact.py, runmap.py, model_gate.py; `patch -p1`)
```diff
--- a/src/hadavin_sdk/guard/redact.py
+++ b/src/hadavin_sdk/guard/redact.py
@@ -23,6 +23,12 @@
 model gate (`runmap.enforce_map`) replaces the values the run's map already holds (the redactor's own final sweep, with the
 gate's held-back values) and runs no pattern at all, so a value no pattern here matched and no map entry holds passes it.
 (A re-scan inside redact() used the sweep's own rule and could never fire, so it was removed - second review, 2026-09-30.)
+
+A value glued to a letter or `_` is masked with the glued text left outside the placeholder (`node_<IPV4_1>`, `<UUID_1>x`):
+an e-mail address, an IPv4 address, a UUID, a phone number that starts with `+`, a contiguous one beside `_` or straight
+after a phone word, and an IBAN beside `_` (G8). A contiguous digit run glued to a letter is not read as a phone number
+(hashes and identifiers), and a letter or digit glued before an IBAN, or a digit before an address, is not read as one.
+A copy of a known phone number is swept where a letter or `_` touches it (not a digit).
 """
 
 from __future__ import annotations
@@ -263,20 +269,23 @@
     # which would otherwise fragment its digit runs and leak the country+bank prefix. The prefix is
     # restricted to the SWIFT IBAN-registry country set (not any two letters) so an uppercase
     # evidence token like `AB12CDEF...` is NOT clobbered — only a genuine IBAN country prefix fires.
+    # Glued (G8): not after an ASCII letter or digit and not before one (one would join the BBAN), so `iban_DE89...`
+    # and `DE89..._x` are masked with the `_` text outside; `xDE89...`, `7DE89...` stay (limit L4: inside a token an
+    # IBAN-shaped tail would cut a longer credential in two and leave its head readable, ticket G8 v3 F1).
     (
         "IBAN",
         re.compile(
-            r"\b(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
+            r"(?<![A-Za-z0-9])(?:AD|AE|AL|AT|AZ|BA|BE|BG|BH|BI|BR|BY|CH|CR|CY|CZ|DE|DJ|DK|DO|EE|EG|ES|FI|FO|FR|GB|GE"
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
-        re.compile(
-            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
-        ),
+        re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
     ),
     # Bank details (owner, 2026-10-28): masked by shape beside their keyword, never by checksum. After UUID (a UUID
     # can end `-aba123456789`) and before ACCOUNTID, SSN, CREDITCARD and PHONE. Codes first: a masked code is the
@@ -372,9 +381,15 @@
     # id on a non-AWS deployment) since WARDEN runs on any cloud.
     ("ACCOUNTID", re.compile(r"\b\d{12}\b")),
     # An EC2 private DNS name carries the address with dashes: ip-10-0-3-22(.region.compute.internal).
-    ("IPV4", re.compile(r"\b(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})\b")),
-    ("IPV4", re.compile(r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),  # k8s pod DNS
-    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
+    # G8: `_` may stand before `ip-` / `ec2-` (`host_ip-10-0-3-22`), a letter may not (`xip-...`, `zip-...`: limit L10);
+    # a letter or `_` may follow the last group (`ip-10-0-3-22a`); a digit may not.
+    ("IPV4", re.compile(r"(?<![A-Za-z0-9])(?:ip|ec2)-(\d{1,3}(?:-\d{1,3}){3})(?![0-9])")),
+    # k8s pod DNS; G8: a letter or `_` may stand before the address (`pod_10-0-3-22.ns.pod`), a digit may not.
+    ("IPV4", re.compile(r"(?<![0-9])(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod\b")),
+    # Dotted quad (G8): not inside a digit run (`7192.0.2.10`, `2026.11.20.10`: limit L1) and not after a lone `v` / `V`
+    # (`v1.2.3.4` is a version, L-D1). A letter or `_` on either side is glued text, left outside (`node_<IPV4_1>`,
+    # `<IPV4_1>a`); a four-part version glued to a word (`python3.11.4.1`) is masked too (L-D8).
+    ("IPV4", re.compile(r"(?<![0-9])(?<!(?<![A-Za-z])[vV])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")),
     # IPv6 — we redact IPv4, so an IPv6 address (common in dual-stack k8s pod logs) is the same
     # identifier and must be masked too. Deliberately matches ONLY real addresses: either a `::`
     # compression or a full 8 groups, so a `10:02:11` timestamp is left alone. (A MAC has its own
@@ -468,7 +483,8 @@
     # A grouped payment-card number (4-4-4-4 with space or dash separators). Masked WHOLE and BEFORE
     # PHONE, which otherwise catches only the first 12-14 digits and leaks the final group. A
     # contiguous 16-digit card is already caught by PHONE; this closes the spaced/dashed form.
-    ("CREDITCARD", re.compile(r"\b\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}\b")),
+    # Glued (G8): a letter or `_` may stand on either side (`x4242 4242 4242 4242`), a digit may not.
+    ("CREDITCARD", re.compile(r"(?<![0-9])\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4}(?![0-9])")),
     # The negative lookahead stops an ISO-8601 date (YYYY-MM-DD, which every log line starts with)
     # being masked as a phone number — that was masking timestamps and losing evidence.
     #
@@ -488,6 +504,10 @@
     #   - (hadavin-sdk edit) nor may it be a compact timestamp `YYYYMMDDhhmmss` (`20261030123456`): 14 digits
     #     with a valid month, day and time. Narrow on purpose: a phone written with `+` or of another length is
     #     still masked.
+    # (G8) A number that starts with `+`, BEFORE the main entry (which would leave `<PHONE_1> 1234a`): a letter or `_` may
+    # stand before the `+` (`x+1 415-555-0132`, `tel_+44 20 5550 1234`) and after the last digit (`+1 415-555-0132a`);
+    # a digit or `.` may not. A number without `+` keeps the main entry's rules (`415-555-0132x123` is not masked).
+    ("PHONE", re.compile(r"(?<![0-9.\-])\+\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![0-9.])")),
     (
         "PHONE",
         re.compile(
@@ -496,6 +516,21 @@
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
+    (
+        "PHONE",
+        re.compile(r"(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\d{10,16})(?![0-9a-z.])"),
+    ),
     # password=..., secret: ..., aws_secret_access_key="...": the value after a credential-ish key.
     # Runs LAST: a value already masked whole is left alone. The bounded [\w.\-] prefix/suffix lets the sensitive word sit INSIDE a
     # compound key (`aws_secret_access_key`, `db_password`), which a `\b`-anchored form missed — the
@@ -1984,7 +2019,8 @@
         # by the rule in _sweep: every copy of a secret, every standalone copy of an identifier. Real
         # example from a live cluster: a Kubernetes "failed to reserve container name" event embeds the pod
         # UID inside `..._default_<uid>_0`, where the trailing `b_` is not a `\b` boundary, so the `(uid)`
-        # copy was masked and the `_0`-suffixed copy was not.
+        # copy was masked and the `_0`-suffixed copy was not. (Since G8 the UUID pattern itself takes that copy;
+        # the sweep still takes such copies of the kinds whose pattern keeps a boundary: a tenant, a host name.)
         #
         # ⛔ The sweep must NOT run inside placeholders already placed. If a TENANT value happens to be
         # the literal `UUID_1`, a naive sweep rewrites the neighbouring `<UUID_1>` to `<<TENANT_1>>` -
@@ -2038,7 +2074,9 @@
                 if rule is _EVERY_COPY:
                     segment = segment.replace(original, placeholder)
                 else:
-                    segment = _replace_standalone(segment, original, placeholder)
+                    segment = _replace_standalone(
+                        segment, original, placeholder, _joins(placeholder)
+                    )
                 self.actions += segment.count(placeholder) - before  # one per copy replaced
             parts[i] = segment
         return "".join(parts)
@@ -2223,10 +2261,24 @@
 
 
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
+def _replace_standalone(
+    segment: str, original: str, placeholder: str, joins: frozenset[str] = _ALNUM
+) -> str:
+    """Replace `original` where no character of `joins` touches it (default `_ALNUM`: an ASCII letter or digit; callers
+    pass `_joins(placeholder)`). A plain scan: a compiled pattern (or an
     lru_cache of one) keyed by the identifier would keep one client's values in process memory, shared with every
     other client (R371), and `re` caches compiled patterns itself."""
     out: list[str] = []
@@ -2236,7 +2288,7 @@
         if j < 0:
             break
         before, after = segment[j - 1 : j], segment[j + n : j + n + 1]
-        if before in _ALNUM or after in _ALNUM:
+        if before in joins or after in joins:
             out.append(segment[i : j + 1])
             i = j + 1
             continue
--- a/src/hadavin_sdk/guard/runmap.py
+++ b/src/hadavin_sdk/guard/runmap.py
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
@@ -715,7 +716,8 @@
     Limits, on purpose (each pinned by a test in tests/test_runmap_enforce_map.py):
     - NOT replaced at all: a value under 3 characters; and, unless it is a secret kind of 4 characters or
       more, a value that is all digits and under 6 characters or a common word (`redact._COMMON`).
-    - A value that is not a secret kind of 4 or more is left where an ASCII letter or digit touches it and
+    - A value that is not a secret kind of 4 or more is left where an ASCII letter or digit (for a PHONE value: a
+      digit) touches it and
       keeps touching it after every other replacement.
     - Only the spelling held in the map is replaced (for a value that is not ASCII, also its folded NFKC spellings,
       which the redactor sweeps with it: each is its own held-back item when it is a piece of a placeholder). A copy hidden by full-width letters, a zero-width
@@ -846,7 +848,7 @@
             if rule is _EVERY_COPY:
                 parts[i] = segment.replace(spelling, placeholder)
             else:
-                parts[i] = _replace_standalone(segment, spelling, placeholder)
+                parts[i] = _replace_standalone(segment, spelling, placeholder, _joins(placeholder))
     return "".join(parts)
 
 
--- a/src/hadavin_sdk/guard/model_gate.py
+++ b/src/hadavin_sdk/guard/model_gate.py
@@ -10,7 +10,8 @@
   characters or more (those are replaced in every copy).
   E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept
 - Any value that is not a secret kind of 4 or more (an identifier: tenant, host, address, id) is replaced only
-  where no ASCII letter or digit touches it: `abc123` inside `xabc1234` stays.
+  where no ASCII letter or digit touches it: `abc123` inside `xabc1234` stays. A PHONE value is replaced where no
+  digit touches it (ticket G8): a known `4155550132` in `build4155550132` is sent to the model as `build<PHONE_1>`.
   E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept
 - Only the spelling the map holds is replaced: a percent-, entity- or backslash-encoded copy, a full-width or
   other look-alike spelling and a copy split by a zero-width character pass as written. EXCEPTION (code review round
```

## Appendix E: the three edited test files (diff against a5247ac4a; `patch -p1`)
```diff
--- a/tests/test_redact_g3_port.py
+++ b/tests/test_redact_g3_port.py
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
--- a/tests/test_redact_idempotent_property.py
+++ b/tests/test_redact_idempotent_property.py
@@ -138,7 +138,10 @@
         rule = R._sweep(placeholder, original)
         if rule is None or original not in free:
             continue
-        if rule is R._EVERY_COPY or R._replace_standalone(free, original, "\x00") != free:
+        if (
+            rule is R._EVERY_COPY
+            or R._replace_standalone(free, original, "\x00", R._joins(placeholder)) != free
+        ):
             found.append(placeholder)
     return found
 
--- a/tests/test_runmap_enforce_map.py
+++ b/tests/test_runmap_enforce_map.py
@@ -262,7 +262,8 @@
 
 def test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept():
     """`redact._replace_standalone`: an identifier is replaced only where no ASCII letter or digit touches
-    it. An underscore, a dash, a dot or a letter outside ASCII beside it does not protect it."""
+    it. An underscore, a dash, a dot or a letter outside ASCII beside it does not protect it. A PHONE value: only
+    a digit beside it protects it (ticket G8, `redact._joins`)."""
     mapping = {"<TENANT_1>": "abc123"}
     assert _enforce("xabc123 abc1234 9abc123 abc123z", mapping) == "xabc123 abc1234 9abc123 abc123z"
     assert (
@@ -270,6 +271,11 @@
         == "<TENANT_1>_ -<TENANT_1>- .<TENANT_1>. \u00e9<TENANT_1>"
     )
     assert _enforce("x123456 1234567", {"<TENANT_1>": "123456"}) == "x123456 1234567"
+    phone = "415" + "555" + "0132"
+    assert (
+        _enforce(f"build{phone} x{phone}_ 7{phone}", {"<PHONE_1>": phone})
+        == f"build<PHONE_1> x<PHONE_1>_ 7{phone}"
+    )
     secret = {"<SECRET_1>": TOKEN}  # a secret is replaced in every copy
     assert _enforce(f"x{TOKEN}9", secret) == "x<SECRET_1>9"
 
```

## Appendix F: tests/g8_cost.py (create; complete)
```python
"""Ticket G8 cost check (section 10 of the ticket): times the six hostile texts of tests/test_redact_glued_rest.py through
`redact()` and `runmap.redact_text` on the tree it runs in. Not collected by pytest. Run from the repo root of each tree:

    python -m tests.g8_cost run OUT.json        # CPU seconds (`time.thread_time`), best of 3, 65,536 and 262,144 characters
    python -m tests.g8_cost compare BASE.json BUILD.json

`compare` prints both tables side by side and exits 1 when a row breaks the acceptance rule: on the build, for every text and
call, the 262,144-character time is under 3.0 s, at most 6.0 times the 65,536-character time, and at most 1.5 times the
base's time plus 0.05 s.
"""

from __future__ import annotations

import json
import sys
import time

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact
from tests.test_redact_glued_rest import HOSTILE

CALLS = {
    "redact": lambda t: redact(t),
    "redact_text": lambda t: runmap.redact_text(t, runmap.RunMap()),
}
SIZES = (65_536, 262_144)


def best(call: str, name: str, n: int) -> float:
    text = (HOSTILE[name] * (n // len(HOSTILE[name]) + 1))[:n]
    out = []
    for _ in range(3):
        t0 = time.thread_time()
        CALLS[call](text)
        out.append(time.thread_time() - t0)
    return min(out)


def run(path: str) -> None:
    res = {
        f"{name}|{call}": [best(call, name, n) for n in SIZES]
        for name in sorted(HOSTILE)
        for call in sorted(CALLS)
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    for key, (small, large) in res.items():
        print(f"{key:32} {small:7.3f} {large:7.3f}  x{large / max(small, 1e-3):.2f}")


def compare(base_path: str, build_path: str) -> int:
    with open(base_path, encoding="utf-8") as fh:
        base = json.load(fh)
    with open(build_path, encoding="utf-8") as fh:
        build = json.load(fh)
    bad = 0
    print(
        f"{'text|call':32} {'base 64K':>8} {'base 256K':>9} {'G8 64K':>8} {'G8 256K':>8} {'ratio':>6} {'G8/base':>7}"
    )
    for key in sorted(build):
        (b_small, b_large), (g_small, g_large) = base[key], build[key]
        ratio = g_large / max(g_small, 1e-3)
        ok = g_large < 3.0 and ratio <= 6.0 and g_large <= 1.5 * b_large + 0.05
        bad += not ok
        print(
            f"{key:32} {b_small:8.3f} {b_large:9.3f} {g_small:8.3f} {g_large:8.3f} {ratio:6.2f} "
            f"{g_large / max(b_large, 1e-3):7.2f} {'ok' if ok else 'FAIL'}"
        )
    print(f"{bad} rows break the rule")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(sys.argv[2])
    elif sys.argv[1:2] == ["compare"]:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    else:
        sys.exit("usage: python -m tests.g8_cost run OUT.json | compare BASE.json BUILD.json")
```


# G8: the glued-rest gap of IPv4, phone, IBAN, UUID and host name (ORDER 016c item 15, K38 / L33, backlog 10)

Status: DRAFT for plan review, written by the core-c drafter (opus tier), 2026-11-20. Nothing is built. A builder with no other
context builds from this file alone. Path class: redaction. Lead rule: build only a gap that a failing input proves (G4 v2 section 0).
Base read: cloud/core-c HEAD 459d8da (holds G7 fix round 3, da0f71f). Every number below was measured on a clean `git archive` of that
commit in the drafter's scratchpad (the shared tree was not edited and not run); the probe was also run on 0d93f20 (before G7 round 3)
and gave byte-identical tables.

## 1. Goal
A value of kind IPV4, PHONE, IBAN or UUID that is glued straight to a letter, a digit or `_` (no word boundary) is masked in the
first `redact()` / `redact_many()` / `runmap.redact_text` call, like the e-mail fix of P1d-a (`EMAIL` ends in `(?![A-Za-z])`, plus
`_sub_glued`). The glued character stays in the text, outside the placeholder (`<IPV4_1>a`), as the e-mail fix does. Shapes that
cannot be told from a hash, a version or code are written down as stated limits and pinned. HOSTNAME needs no G8 pattern change:
its "glued before" rows are closed by G4c (G4 v2 section 5.2); its "glued after the suffix" rows are a stated limit (decision L-D3).

## 2. Problem (what the probe shows)
Not a fixed-point problem: a second call on the output masks nothing more in any of the 80 rows (G7's settle loop cannot help). It is
a boundary problem in five pattern entries and one sweep rule:
- `IPV4` dotted (redact.py:375) and EC2 dashed (373) start and end with `\b`: a letter or `_` on either side refuses the match.
- `PHONE` (490) refuses a start after `\w . -` and an end before `\w .` (on purpose: hashes and identifiers, comment 472-487). So a
  FORMATTED phone (`+1 415-555-0132`) followed by a letter or `_` is not masked, or only in part (`<PHONE_1> 1234a`: the regex
  backtracks to the last separator and leaves the last group readable).
- `IBAN` (265) starts and ends with `\b`: `_x` after, or any letter, digit or `_` before, refuses it.
- `UUID` (274) starts and ends with `\b`: anything glued on either side refuses it; with a prefix glued, `ACCOUNTID` takes the last
  12 digits and 24 of 36 characters stay readable.
- The identifier sweep (`_replace_standalone`, redact.py:2001, rule `_STANDALONE` from `_sweep`, 1980) refuses a copy that an ASCII
  letter or digit touches, so a clean copy of the same IP, phone or UUID elsewhere in the text does not mask the glued copy. IBAN is a
  SECRET kind (`_EVERY_COPY`), so its glued copies are already swept once one clean copy is found (row 43).

### 2.1 Counts (80 probe rows: 75 glued shapes + 5 controls)
| kind | rows | leak today | closed by the G8 prototype | stated limit after G8 | closed by G4c (not G8) | unchanged, no leak |
|---|---|---|---|---|---|---|
| IPv4 | 19 | 17 | 15 | 2 | 0 | 2 |
| phone | 17 | 13 | 11 | 2 | 0 | 4 (2 change output: `x+<PHONE_1>` -> `x<PHONE_1>`) |
| IBAN | 14 | 10 | 8 | 2 | 0 | 4 |
| UUID | 14 | 13 | 13 | 0 | 0 | 1 |
| host name | 16 | 9 | 0 | 7 | 2 | 7 |
| total | 80 | 62 | 47 | 13 | 2 | 18 |
`redact()`, `redact_many([text, "other line"])` and `runmap.redact_text` gave the same leak verdict in all 80 rows, today and with the
prototype; `redact_untrusted` gave the same output as `redact_text` in all 80 rows with the prototype; a second `redact_text` with the
same run map changed neither text nor map in all 80 rows with the prototype.

### 2.2 Probe rows
Values (all fake or documentation values, built from parts in the probe): `{IP1}` 192.0.2.10, `{IP2}` 198.51.100.7, `{IP3}`
203.0.113.45 (RFC 5737 ranges); `{PHONE+}` +1 415-555-0132, `{PHONE10}` 4155550132, `{PHONEUK}` +44 20 5550 1234 (555 numbers);
`{IBAN_DE}` DE89370400440532013000 and `{IBAN_GB}` GB82WEST12345698765432 (the published example IBANs); `{UUID}`
123e4567-e89b-12d3-a456-426614174000 (the RFC example), `{UUIDUP}` the same in upper case; host names `db-7.corp.internal`,
`db01.prod.corp`, `nas02.office.lan`, `printer7.local`, `a.b.c.internal` (made up). Leak rule (the probe's, per kind): the value
readable outside placeholders; phone: 4 or more digits of the number in a row; IBAN / UUID: 8 or more characters; IPv4: 7 or more;
host: any non-suffix label, or 2 or more leading characters of one directly before a placeholder (`svc_db-<HOSTNAME_1>`).
"Expected" is the prototype's output (section 4) for a closed row, or the stated limit. Column "now" is HEAD 459d8da.

| # | kind | shape | input | output now | leak now | expected after G8 | result |
|---|---|---|---|---|---|---|---|
@@TABLE@@

Must-keep rows (outside the 80; output now -> with the prototype):
| text | now | with G8 | verdict |
|---|---|---|---|
| `release v1.2.3.4 shipped`, `node-v18.19.1.2 build` | unchanged | unchanged (the lone `v` rule, L-D1) | kept |
| `dotted date 2026.11.20.10 ok` | unchanged | unchanged (digit before: L1) | kept |
| `oid 1.3.6.1.4.1 ok` | `oid <IPV4_1>.4.1 ok` | same | unchanged (already over-masked today) |
| a SHA-256 `3851007894abcdef...`, `commit 4155550132abcdef`, `build4155550132`, `img sha256_3851007894abcdef` | unchanged | unchanged | kept (PHONE hash guard) |
| `wave2-2026-09-11T14:12:03Z`, `orders-db-ro-1 up`, `pod web-5d8f9c7b6-x2x7q`, `x86_64-linux-gnu`, `eth0_up` | unchanged | unchanged | kept |
| `run_20261120101112_x ok` | unchanged | unchanged (compact timestamp guard kept in the new entry) | kept |
| `self.local_cache = 1`, `obj.internal_state`, `nltk.corpus.reader`, `acme.corporate.site`, `ctx.local9`, `vlan10.lan2 ok` | unchanged | unchanged (no host change in G8) | kept |
| `token AB12CDEFGHIJKLMNOPQ ok` | unchanged | unchanged | kept |
| `req ReqIdDE12345678901234 ok` | unchanged | `req ReqId<IBAN_1> ok` | OVER-MASK, accepted (camel-case boundary, L-D2) |
| `tag xDE00ABCDEFGHIJK ok` | unchanged | `tag x<IBAN_1> ok` | OVER-MASK, accepted (the IBAN pattern is a shape, not a checksum, as today standalone) |
| `ts 1732095071000_x` | unchanged | `ts <PHONE_1>_x` | consistent: `ts 1732095071000` is `<PHONE_1>` today |
| `uuid-ish deadbeef-dead-beef-dead-beefdeadbeefcafe` | unchanged | `uuid-ish <UUID_1>cafe` | OVER-MASK, accepted (no end guard on UUID, L-D4) |
| `id 123e4567e89b12d3a456426614174000 ok` (no dashes) | unchanged | unchanged | not a UUID shape today either: out of scope |
Found on the way, NOT glued, NOT in G8: a phone written before a full stop (`call 415-555-0132.`, `call 4155550132.`) is not masked
today (PHONE's end guard refuses `.`). Reported for a later ticket; G8's new entry keeps the same `.` guard so it does not change this.

## 3. Files
Modify:
- `src/hadavin_sdk/guard/redact.py` only: the IBAN, UUID, the two IPV4 entries named below, one new PHONE entry before the main PHONE
  entry and two after it, `_JOINS` and the `joins` argument of `_replace_standalone`, the one call in `_Redactor.sweep`, the comments
  above each changed entry, one sentence in the module docstring.
Create:
- `tests/g8_cases.py`: the 80 rows of 2.2 as data (kind, shape, text built from parts, protected value, expected class) and the
  must-keep rows. Values built from parts (`"192." + "0.2.10"`), no literal of a full value, as tests/test_text_parts_together.py does.
- `tests/test_redact_glued_rest.py`: the acceptance tests of section 7.
Changed outcome, edited by the builder in the same commit (one assertion, recorded old and new in the evidence):
- `tests/test_redact_settle_loop.py::test_boundary_class_is_over_masked_fail_safe_and_pinned` (442-453 at HEAD). With the prototype
  `ref hunter123-45-6789` is masked by the new formatted-PHONE entry in pass 1 (a letter may now stand before a formatted number):
  old `password=<SECRET_1>\nref <SECRET_1><SSN_1>`, new `password=<SECRET_1>\nref <SECRET_1><PHONE_1>`; the map holds
  `123-45-6789` under PHONE, not SSN. The `fresh` call now ALSO masks it (`<PHONE_1>`), so the test's last assertion
  (`"<SSN_1>" not in fresh`) still holds but no longer shows over-masking. The builder rewrites the test to pin the new outputs and
  moves the "boundary class" example to a shape G8 does not touch, or the lead takes L-D5's fallback. This is the ONLY existing test
  that changed outcome in the drafter's run (section 9).
Not touched: runmap.py (grammars: every new original fits `_GRAMMAR` IPV4 / PHONE; UUID and IBAN are never stored), textnorm, defaults.py,
`_countable` and the counters (no new label: the new entries reuse PHONE, so `_LABELS` and `_countable` are unchanged), `_sub_glued`.

## 4. Design (exact; this is the prototype the numbers come from)
G8a, patterns (PATTERNS order unchanged except the three PHONE entries):
1. IBAN (redact.py:265-272): start `\b` -> `_NOT_IN_WORD` (the module's own helper, line 66: not after an ASCII letter or digit, or a
   lower-case letter directly before the upper-case country code); end `\b` -> `(?![A-Za-z0-9])`. So `_` on either side and
   `xDE89...`, `ibanDE89...` are masked; `7DE89...`, `XDE89...` stay (L4).
2. UUID (274-278): drop both `\b`: `[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}`. The leftmost
   search finds the 8-4-4-4-12 run inside a longer hex run; a glued character on either side stays outside. `_UUID_SHAPE` (736, used by
   `_has_bank_word`) follows automatically: a glued UUID is now also removed before the bank-word check (a UUID ending `-aba123456789`
   glued to a letter no longer counts as a routing number; more correct, not less).
3. IPV4 EC2 dashed (373): end `\b` -> `(?![0-9])`. The pod-DNS entry (374) is unchanged (not probed glued; not in G8).
4. IPV4 dotted (375): `(?<![0-9])(?<!(?<![A-Za-z])[vV])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])`. A letter or `_` may stand on either side;
   a digit may not (L1); a lone `v` / `V` (not inside a word) directly before is a version tag and refuses the match (L-D1).
5. PHONE, formatted, glued (NEW entry directly BEFORE the main PHONE entry at 490, so it wins the row-32 partial):
   `(?<![0-9.\-])(?!\d{4}-\d\d-\d\d)(?=\+|\d{1,4}[ \-]\d)` + the main entry's compact-timestamp guard +
   `\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![0-9.])`. Only a number that starts with `+` or has a separator within its first 5
   characters. Letters and `_` may touch it on either side; digits, `.` and `-` before, and digits and `.` after, may not (the
   identifier guards of the comment at 472-487: `ip-10-0-3-22`, `orders-db-ro-1`, `wave2-2026-...`, dates). `+` is allowed before so
   two phones glued (`...0132+1 415-...`) still give `<PHONE_1>+<PHONE_2>` (row 75; a first draft that refused `+` left `+1 ` readable).
6. PHONE, contiguous, underscore-glued (NEW, directly AFTER the main PHONE entry):
   `(?<![0-9A-Za-z.\-+])(?:(?<=_)|(?=\d{10,16}_))` + the compact-timestamp guard + `\d{10,16}(?![0-9A-Za-z.])`: 10 to 16 digits with
   `_` on at least one side and no letter or digit on the other. `sha256_3851007894abcdef` stays (letter after).
7. PHONE, keyword-glued (NEW, after 6): `(?i)(?<![a-z0-9])(?:tel|phone|mobile|cell|fax)(\d{10,16})(?![0-9a-z.])`, group 1 is the
   value. `tel4155550132` is masked; `x4155550132` and `4155550132a` stay (L3).
G8b, sweep (redact.py:1817 and 1998-2019):
8. `_JOINS = {"IPV4": frozenset(string.digits), "PHONE": frozenset(string.digits), "UUID": frozenset(string.hexdigits)}`;
   `_replace_standalone(segment, original, placeholder, joins: frozenset[str] = _ALNUM)` refuses a copy only when `before in joins or
   after in joins`; `sweep` passes `_JOINS.get(_kind(placeholder), _ALNUM)`. Every other kind keeps `_ALNUM` (HOSTNAME, EMAIL, TENANT,
   ACCOUNTID, ...: their values are made of letters and digits, so a letter beside one may be part of another value). The rule for
   short and common values (`_sweep`: under 3 characters, all-digit under 6, `_COMMON`) is unchanged.
9. Docstring (module, after the "What this is not" paragraph): "A value glued to a letter or `_` is masked with the glued character
   left outside the placeholder (IPv4, a formatted phone number, IBAN, UUID, e-mail); a contiguous digit run glued to a letter is not
   a phone number here (hashes and identifiers), and a digit glued before an address or IBAN is not read as one."
What stays as it is: `_sub_glued` is used for EMAIL only. Not needed for the new entries: their new boundaries are character classes,
and the rows where two values touch (75, 76-77 UUID, 74 IPs with a letter between) are masked by plain `sub`; the two rows with no
character between two values of the same kind (13 IPs, 76 IBANs) cannot be split by any boundary rule (L2, L5).
Settle loop: untouched. G8 changes what pass 1 finds; the loop then behaves as on any other text (a glued value in pass 1 means
fewer, not more, rounds: the G7 "boundary class" case is now found in pass 1).

## 5. Decisions made (drafter)
- The glued character stays outside the placeholder (as the e-mail fix): the original stored in the map is the value's own grammar,
  so `runmap._GRAMMAR` accepts it and restore gives back exactly the input (35 of 35 IPv4 / phone rows restore byte-identical; the one
  other row holds a UUID, which is never stored).
- No new kind, no change to `_LABELS`, counters, `_countable` or the stored kinds.
- HOSTNAME: no G8 code. The G4c pattern (G4 v2 5.2) closes rows 64 and 71 (`svc_db-7...`, `vm_nas02...`: `_` is a label character
  there). Measured in-process with G4 v2's regex. A G8c variant (G4c's tail suffix may be followed by `_` or a digit,
  `(?![^\W\d_]|-)` in place of `(?![\w-])`) closes rows 68, 69 (`corp9`, `corp_x`) but masks code: `self.corp_id` -> `<H>_id`,
  `cfg.lan_mode` -> `<H>_mode`, `vlan10.lan2` -> `<H>2`, `m.intranet2`, `data.corp_2026.csv`. Not proposed as default (L-D3).
- Contiguous phone digits glued to a letter stay unmasked (L3): the PHONE comment's hash and identifier guards are kept as they are.
- The sweep change (G8b) is kept in G8: it is the only fix for row-31-type text (a clean copy plus a letter-glued copy of a
  contiguous phone, which no pattern may take) and it is two lines.

## 6. Decisions for the lead (each with the build default)
| id | question | default (built unless the lead says otherwise) | fallback |
|---|---|---|---|
| L-D1 | IPv4 after a lone `v` (`v1.2.3.4`) | not masked: read as a version | mask it too (drop the second look-behind); every `vN.N.N.N` version becomes `v<IPV4_n>` |
| L-D2 | IBAN glued before | `_` or a lower-case letter before the country code (camelCase) is masked; `ReqIdDE12345678901234` over-masked, accepted | `_` only before (rows 38, 39, 45 become limits; no camelCase over-mask) |
| L-D3 | host name with a letter, digit or `_` glued AFTER its private suffix (rows 67-70, 78-80) | stated limit L6 (code and words: `self.local_cache`, `corporate`, `corpus`) | G8c: `_` or a digit after a G4c TAIL suffix (`corp`, `lan`, `intranet`, `intra`, `localdomain`, `home.arpa`) masked; closes 68, 69 and over-masks code attributes as listed in 5; only after G4c is merged |
| L-D4 | UUID with hex glued after (`...174000a`, `...-beefdeadbeefcafe`) | masked, the extra hex left outside (`<UUID_1>a`, `<UUID_1>cafe`) | end guard `(?![0-9A-Fa-f])`: rows 47, 48 become limits, no over-mask of 8-4-4-4-16 ids |
| L-D5 | the G7 pinned "boundary class" test (section 3) | rewrite it to the new outputs (PHONE in pass 1) and keep one over-mask example that G8 does not touch (the builder picks it from the G7 generator shapes and records it) | delete the test and drop the "boundary class" bullet from G7's Stated Limits, since its example no longer over-masks |
| L-D6 | PHONE keyword list (entry 7) | `tel`, `phone`, `mobile`, `cell`, `fax` | cut entry 7: row 28 becomes a limit |
| L-D7 | dependency order (section 8) | G7 round 3 (done, da0f71f) -> G4 (G4c) -> G8 | G8a + G8b before G4 (they touch no HOSTNAME line); then rows 64 and 71 are strict xfails naming G4c until G4 lands |

## 7. Acceptance tests (tests/test_redact_glued_rest.py; data from tests/g8_cases.py; public names only: `redact`, `redact_many`, `runmap.redact_text`, `runmap.redact_untrusted`, `runmap.restore_text`)
- `test_glued_rows_are_masked` (parametrised over the 47 closed rows): the protected value is not readable by the 2.2 leak rule in
  `redact()`, `redact_many([text, "other line"])[0][0]` and `redact_text`; the output equals the "expected" column exactly.
- `test_glued_character_stays_outside_the_placeholder`: for rows 2-5, 7-9, 18-20, 36-37, 47-51: the glued text (`a`, `_x`, `_`, `x`,
  `iban`, `9`) is in the output next to the placeholder, and the map original equals the bare value.
- `test_controls_and_untouched_rows_are_byte_identical` (rows 1, 6, 17, 32-35, 43, 46, 59-63, 65-66... every row whose result is
  "unchanged"): output and map equal the values recorded at step 0 on the base commit.
- `test_limit_rows_are_pinned` (rows 10, 13, 25, 27, 40, 76, 67-70, 78-80): output equals the base commit's; strict `xfail` with the
  limit id in the reason, so a later fix shows up.
- `test_host_glued_before_is_closed_by_g4c` (rows 64, 71): `x <HOSTNAME_1> y`. Ordinary test if G4c is merged first (L-D7 default);
  strict xfail naming G4c otherwise.
- `test_must_keep_rows` (2.2 must-keep table): each "kept" text is returned unchanged with an empty map; each accepted over-mask
  equals the table's output exactly (pinned, so a change is looked at).
- `test_second_call_changes_nothing`: for all 80 rows `redact_text(redact_text(t, m), m)` changes neither text nor map.
- `test_untrusted_matches_redact_text`: `redact_untrusted(t, RunMap()) == redact_text(t, RunMap())` for all 80 rows.
- `test_restore_round_trip_ipv4_and_phone`: for every IPv4 / phone row without another kind, `restore_text(out, m) == t`.
- `test_sweep_masks_a_letter_glued_copy_of_a_known_value` (G8b): `phone=<10 digits>` then `x<same digits>` -> both `<PHONE_1>`;
  the same for an IP and a UUID; a copy touched by a DIGIT is not replaced (`<IP>9` stays a different address: `192.0.2.109` with
  `192.0.2.10` known is masked by the pattern as its own value, never as `<IPV4_1>9`); HOSTNAME and TENANT copies glued to a letter
  are still NOT replaced (unchanged rule).
- `test_phone_hash_guard_kept`: `sha 3851007894abcdef...`, `commit 4155550132abcdef`, `img sha256_3851007894abcdef`,
  `run_20261120101112_x` unchanged.
- `test_two_glued_phones_leave_only_the_plus` (row 75): `call <PHONE_1>+<PHONE_2> now`.
- `test_bank_word_check_ignores_a_glued_uuid`: `_has_bank_word("id x<uuid ending -aba123456789>")` is False (was True before G8).
- `test_glued_patterns_are_linear` (perf mark): each of the five texts of section 10 at 65,536 and 262,144 characters; the ratio
  of CPU seconds is at most 5.0 (4x the text), and the 262,144-character time is under 2.0 s.
- `test_g8_rows_hash`: sha256 of the joined inputs of tests/g8_cases.py (`"\x00".join`, in order) equals the value in the evidence.
Mutants (each must be killed; raw result in evidence/G8-1.md):
| mutant | killed by |
|---|---|
| IBAN end back to `\b` | rows 36, 37, 42, 44 |
| IBAN start back to `\b` | rows 38, 39, 41, 45 |
| IBAN start without the camelCase part (`(?<![A-Za-z0-9])` only) | rows 38, 39, 45 |
| UUID end `\b` restored | rows 47-51, 77 |
| UUID start `\b` restored | rows 52-55 |
| IPV4 dotted end `\b` | rows 2-5, 11, 16 |
| IPV4 dotted start `\b` | rows 7-9 |
| IPV4 drop `(?<![0-9])` | must-keep `2026.11.20.10` |
| IPV4 drop the `v` look-behind | must-keep `v1.2.3.4` |
| EC2 end `\b` | rows 72, 73 |
| formatted PHONE entry moved after the main entry | row 32 (`<PHONE_1> 1234a`) |
| formatted PHONE without `(?=\+|\d{1,4}[ \-]\d)` | must-keep `build4155550132`... (contiguous run after a letter) |
| formatted PHONE allows `-` before | must-keep `orders-db-ro-1` style row and `ip-10-0-3-22` |
| underscore PHONE allows a letter after | must-keep `img sha256_3851007894abcdef` |
| underscore PHONE without the timestamp guard | must-keep `run_20261120101112_x` |
| keyword PHONE entry removed | row 28 |
| `_JOINS` removed (all `_ALNUM`) | rows 15, 24, 31, 58 |
| `_JOINS` given to HOSTNAME as digits | the HOSTNAME / TENANT part of the sweep test |

## 8. Build order and dependencies
1. G7 round 3 (settle is a real fixed point, `_SETTLE_ROUNDS` = 4, union `todo`): DONE in da0f71f; G8 builds on it. G8 needs no
   change to `settle`; the settle-loop tests are in the must-stay-green list. If a G7 round 4 is ordered, it lands first: both edit
   redact.py, and G8's one changed G7 test (section 3) must be rewritten against the final G7 text.
2. G4 v2 (G4a base64 in runmap, G4b ENCODED, G4c HOSTNAME + HOSTKEY in redact.py): lands before G8 (L-D7 default). G8 touches no
   HOSTNAME line, so the only coupling is rows 64 / 71 and the must-keep host rows, and G4's `tests/test_p1c_gaps.py` must stay green
   under G8 (none of its 229 rows holds a glued IPv4, IBAN or UUID by its builders; the 1b IPv4 rows decode to `10.20.30.40` in
   prose: re-measure).
3. G8 itself, in this order: step 0 (record the base outputs of all 80 rows and the must-keep rows on the base commit), tests/g8_cases.py
   and the tests (fail-before), G8a entries one at a time (IBAN, UUID, IPV4 x2, PHONE x3) re-running the redactor files after each,
   G8b, the docstring, the G7 test rewrite, mutants, evidence.
Owner: core-c (guard/redact.py). No file of core-a or core-b is touched; no SPINE file.

## 9. Fail-before and the drafter's run
- Fail-before: copy tests/g8_cases.py and tests/test_redact_glued_rest.py into a clean export of the base commit
  (`git archive <base> | tar -x -C /tmp/g8-base`, no worktree, no branch switch) and run them. Expected: exactly 47 failures in
  `test_glued_rows_are_masked`, plus `test_sweep_masks_...` and `test_bank_word_check_...`; the limit, control and must-keep tests
  pass. Record the ids.
- Drafter's run of the prototype (the patch of section 4 applied to a clean archive of 459d8da, every test file that names
  `guard.redact`, `guard.runmap`, `from hadavin_sdk.guard import` or `redact_text`: 79 files, `-m "not perf" -n 2`): see the batch line
  in the evidence; on 0d93f20 the same set gave base 18 failed / 10,410 passed / 1 error and prototype 19 failed / 10,409 passed /
  1 error; every failure but one is the same in both and is caused by the archive (no `.git`, no `.gitleaks.toml`, no `demos/`,
  unidata generator files); the one difference is `test_boundary_class_is_over_masked_fail_safe_and_pinned` (section 3).
  @@SUITE@@

## 10. Cost (CPU seconds, best of 3, `redact()` on this 4-core container, Python 3.13.18, measured while other jobs ran: noise about 20 percent)
| text (262,144 chars unless said) | before G8 | with G8 |
|---|---|---|
| `1.` repeated | 0.83-0.91 | 0.92-0.93 |
| `x1 2 3 4 5 6 7 8 9 ` repeated | 0.60-0.76 | 0.68-0.79 |
| `_4155550132` repeated | 0.65-0.74 | 0.60-0.72 |
| `deadbeef-dead-beef-dead-` repeated | 0.69-0.77 | 0.75-0.98 |
| `aDE89` + 40 `A` + space, repeated | 0.44-0.47 | 0.45-0.52 |
| 109,600 chars of log lines with glued values | 0.31-0.38 | 0.24-0.30 (fewer unmasked runs left for later patterns) |
Linear: with G8, 65,536 -> 262,144 characters gives a ratio of 3.2 to 4.4 for the five hostile texts (4.43 for the hex-dash text).
Worst seen: about 1.3x on the hex-dash text, inside the noise of the others. Under `REDACT_BUDGET_S` (6.0) with room. No new pass:
the five changed entries replace five entries, three PHONE entries are added; the sweep cost is unchanged (one set lookup per copy).
Builder effort estimate: half a day (regex edits are given; most time is the test data, step 0 fixtures and the mutants).

## 11. Stated limits (after G8; each pinned by a strict xfail or a must-keep row)
- L1 A digit glued before a dotted IPv4 (`7192.0.2.10`): not an address grammar (a 4-digit first group); a dotted date-like run
  (`2026.11.20.10`) must stay. Row 10.
- L2 Two dotted IPv4s glued with no character between (`192.0.2.10198.51.100.7`): no boundary can split them. Row 13.
- L3 A contiguous phone number glued to a letter on either side (`4155550132a`, `x4155550132`): kept unmasked like a hash or an
  identifier (the PHONE comment's guard). Masked if a clean copy of the same number is in the call (G8b). Rows 25, 27.
- L4 A digit or an upper-case letter glued before an IBAN (`7DE89...`, `XDE89...`): cannot be told from an upper-case evidence id.
  Row 40.
- L5 Two IBANs glued (`DE89...GB82...`): the 44-character run is longer than the 34 an IBAN may have; no per-country length table.
  Row 76.
- L6 A letter, digit or `_` glued AFTER a host name's private suffix (`db01.prod.corpa`, `corp9`, `corp_x`, `lanx`, `printer7.local9`,
  `.local_x`, `.internalx`): the name's labels stay readable; code and words share the shape. Rows 67-70, 78-80 (L-D3).
- Unchanged from today: a 32-hex UUID without dashes is not a UUID shape; a phone before a full stop (found on the way, section 2.2);
  the sweep's rule for short and common values.

## 12. Risks
- Over-masking (fail safe, evidence lost): versions without a `v` (`1.2.3.4rc1` is masked today when standalone, and now also glued),
  camelCase ids holding a country code and two digits (`ReqIdDE12...`), 8-4-4-4-16 hex ids, `vlan`-style host labels are NOT affected
  (no host change). An over-masked IBAN is a SECRET kind: every copy of that token is swept in the call.
- Label change: a 3-2-4 group glued to a letter is now PHONE (pass 1), not SSN (G7 boundary class); still masked, restore gives it
  back as PHONE is a stored kind (an SSN never was): an SSN-shaped value glued to a letter can now be stored and restored. If the lead
  wants SSN never stored, the formatted-PHONE entry must refuse exactly the 3-2-4 shape (`(?!\d{3}-\d{2}-\d{4}(?!\d))`); not built.
- Placeholder digits: the new look-behinds are character classes; a placeholder number (`<X_12>`) is never followed by a dotted
  quad in the probe, and the sweep never runs inside placeholders (unchanged split).
- G4c interaction: none measured on the integrated tree (G4 is not built); rows 64 / 71 depend on it.

## 13. What is NOT verified
- Only the 79 files that name the redactor were run (not the whole suite); perf-marked tests were not run; no mutant was run.
- The archive lacked `.git`, `.gitleaks.toml`, `demos/` and the unidata generator inputs: the 18 failures they cause hide what those
  tests would say about G8 (they do not call the redactor patterns, by their names; not opened one by one).
- Timing on a quiet machine, on Windows, and through `redact_text` with views at the 262,144 cap with glued values (only `redact()`).
- G4c on the integrated tree: host rows were measured with G4 v2's regex compiled alone, not through `redact()`.
- tests/warden_port corpora and the G7 property generator ran green under the prototype, but they hold almost no glued shapes; the
  must-keep list is the drafter's own (26 rows), not a corpus of real logs.
- Non-ASCII glue (a Cyrillic letter or a full-width digit glued to an IP) goes through the fold scan first; not probed.
- Whether any approval-card path (channel.clean, slack_channel) shows a different text: not run; they call `runmap.redact_text`.
